#!/usr/bin/env python3
"""
Paper Reading Daemon - 后台论文阅读守护进程

功能：
1. 从 Zotero 获取指定分类的论文列表（递归子分类）
2. 调用可配置的 AI backend 逐篇处理
3. 遇到 rate limit 时自动等待并重试
4. 支持断点续传

用法：
    # 启动守护进程处理 VLA 分类
    screen -S paper-daemon
    python3 paper_daemon.py -c "VLA"

    # 查看进度
    python3 paper_daemon.py --status

AI backend 在 _shared/user-config.json 的 "ai_backend" 段配置，
支持 claude_code / generic_cli / openai_api 三种类型。
"""

import os
import sys
import json
import sqlite3
import shutil
import time
import argparse
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

_SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

_LIB_DIR = Path(__file__).resolve().parent / "lib"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from user_config import (
    concepts_dir,
    obsidian_vault_path,
    paper_notes_dir,
    zotero_db_path,
    zotero_storage_dir,
    temp_file_path,
    daemon_state_dir,
    ai_backend_type,
)
from ai_backend import AIBackend, RateLimitError, QuotaLimitError, BackendTimeoutError, AIBackendError, parse_reset_wait_seconds

# 配置
ZOTERO_DB = str(zotero_db_path())
ZOTERO_STORAGE = str(zotero_storage_dir())
OBSIDIAN_VAULT = str(obsidian_vault_path())
PAPER_NOTES_ROOT = str(paper_notes_dir())
CONCEPTS_ROOT = str(concepts_dir())
_DAEMON_STATE_DIR = str(daemon_state_dir())
PROGRESS_FILE = os.path.join(_DAEMON_STATE_DIR, "paper_daemon_progress.json")
LOG_FILE = os.path.join(_DAEMON_STATE_DIR, "paper_daemon.log")
PID_FILE = os.path.join(_DAEMON_STATE_DIR, "paper_daemon.pid")

# Rate limit 配置
INITIAL_WAIT = 60          # 初始等待时间（秒）
MAX_WAIT = 21600           # 最大等待时间（6小时）
WAIT_MULTIPLIER = 2        # 等待时间倍数
BETWEEN_PAPERS_WAIT = 5    # 论文之间的等待时间（秒）
QUOTA_WAIT_TIME = 1800     # 命中配额上限时的默认等待时间（30分钟）

# 设置日志
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

_SUBSCRIPT_TRANSLATION = str.maketrans("₀₁₂₃₄₅₆₇₈₉₊₋", "0123456789+-")
_GREEK_REPLACEMENTS = {
    "π": "pi",
    "ϕ": "phi",
    "φ": "phi",
    "α": "alpha",
    "β": "beta",
    "γ": "gamma",
}


def acquire_lock() -> bool:
    """获取进程锁，防止重复运行"""
    if os.path.exists(PID_FILE):
        with open(PID_FILE, 'r') as f:
            old_pid = f.read().strip()
        # 检查进程是否还在运行
        try:
            os.kill(int(old_pid), 0)
            return False  # 进程还在运行
        except (OSError, ValueError):
            pass  # 进程已结束，可以继续

    # 写入当前 PID
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    return True


def release_lock():
    """释放进程锁"""
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)


def wait_for_quota_reset(wait_seconds: Optional[int] = None):
    """等待配额重置或人工恢复后再继续。"""
    if wait_seconds is None:
        wait_seconds = QUOTA_WAIT_TIME
    wait_minutes = max(1, wait_seconds // 60)
    logger.info(f"⏳ 配额受限，等待 {wait_minutes} 分钟...")
    time.sleep(wait_seconds)


def copy_zotero_db() -> str:
    """复制 Zotero 数据库以避免锁定"""
    tmp_db = str(temp_file_path("zotero_readonly.sqlite"))
    shutil.copy(ZOTERO_DB, tmp_db)
    return tmp_db


def get_collection_id_and_path(db_path: str, collection_name: str) -> tuple[Optional[int], Optional[str]]:
    """根据分类名称获取 ID 和完整路径"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT collectionID, collectionName, parentCollectionID FROM collections")
    collections = {row[0]: {'name': row[1], 'parent': row[2]} for row in cursor.fetchall()}

    def get_path(cid):
        path_parts = []
        current = cid
        while current:
            if current in collections:
                path_parts.insert(0, collections[current]['name'])
                current = collections[current]['parent']
            else:
                break
        return '/'.join(path_parts)

    for cid, info in collections.items():
        if info['name'].lower() == collection_name.lower():
            conn.close()
            return cid, get_path(cid)
        if collection_name.lower() in info['name'].lower():
            conn.close()
            return cid, get_path(cid)

    conn.close()
    return None, None


def get_all_child_collections(db_path: str, collection_id: int) -> list[int]:
    """递归获取所有子分类ID（包含自身）"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT collectionID, parentCollectionID FROM collections")
    all_collections = cursor.fetchall()
    conn.close()

    children_map = {}
    for cid, parent_id in all_collections:
        if parent_id not in children_map:
            children_map[parent_id] = []
        children_map[parent_id].append(cid)

    result = [collection_id]
    def collect_children(cid):
        if cid in children_map:
            for child_id in children_map[cid]:
                result.append(child_id)
                collect_children(child_id)

    collect_children(collection_id)
    return result


def get_papers_in_collection(db_path: str, collection_id: int) -> list[dict]:
    """获取分类下的所有论文（递归包含子分类）"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    collection_ids = get_all_child_collections(db_path, collection_id)
    placeholders = ','.join('?' * len(collection_ids))
    query = f"""
        SELECT DISTINCT i.itemID, idv.value as title
        FROM items i
        JOIN collectionItems ci ON i.itemID = ci.itemID
        JOIN itemData id ON i.itemID = id.itemID
        JOIN itemDataValues idv ON id.valueID = idv.valueID
        JOIN fields f ON id.fieldID = f.fieldID
        WHERE ci.collectionID IN ({placeholders}) AND f.fieldName = 'title' AND i.itemTypeID != 14
    """
    cursor.execute(query, collection_ids)
    logger.info(f"递归查询，包含 {len(collection_ids)} 个分类")

    papers = [{'item_id': row[0], 'title': row[1]} for row in cursor.fetchall()]
    conn.close()
    return papers


def get_pdf_path(db_path: str, item_id: int) -> Optional[str]:
    """获取论文的 PDF 路径"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ia.path, items.key
        FROM itemAttachments ia
        JOIN items ON ia.itemID = items.itemID
        WHERE ia.parentItemID = ? AND ia.contentType = 'application/pdf'
    """, (item_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        path, key = row
        if path and path.startswith('storage:'):
            filename = path.replace('storage:', '')
            return os.path.join(ZOTERO_STORAGE, key, filename)
    return None


def get_paper_online_source(db_path: str, item_id: int) -> Optional[dict]:
    """
    获取论文的在线来源信息（arXiv ID、DOI、URL）
    用于处理没有 PDF 的论文
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取论文的各种字段
    cursor.execute("""
        SELECT f.fieldName, idv.value
        FROM itemData id
        JOIN fields f ON id.fieldID = f.fieldID
        JOIN itemDataValues idv ON id.valueID = idv.valueID
        WHERE id.itemID = ?
    """, (item_id,))

    fields = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()

    result = {}

    # 检查 arXiv ID (可能在 extra 字段或 archiveID)
    extra = fields.get('extra', '')
    if 'arXiv:' in extra:
        # 格式: arXiv:2401.12345
        match = re.search(r'arXiv[:\s]+(\d{4}\.\d{4,5})', extra, re.IGNORECASE)
        if match:
            result['arxiv_id'] = match.group(1)

    # 检查 DOI
    doi = fields.get('DOI', '')
    if doi:
        result['doi'] = doi

    # 检查 URL
    url = fields.get('url', '')
    if url:
        result['url'] = url
        # 尝试从 URL 提取 arXiv ID
        if 'arxiv.org' in url and 'arxiv_id' not in result:
            match = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})', url)
            if match:
                result['arxiv_id'] = match.group(1)

    return result if result else None


def get_existing_notes() -> dict[str, str]:
    """获取 Obsidian 中已有的笔记（返回 {方法名: 文件路径}）"""
    existing = {}
    notes_dir = Path(PAPER_NOTES_ROOT)
    if notes_dir.exists():
        for md_file in notes_dir.rglob("*.md"):
            name = md_file.stem
            relative_parts = md_file.relative_to(notes_dir).parts
            # 跳过 _待整理, _概念 等特殊目录和目录页
            if any(part.startswith("_") for part in relative_parts):
                continue
            if md_file.parent.name == name:
                continue

            for method_name in _extract_note_method_names(name):
                existing[method_name] = str(md_file)
    return existing


def title_matches_note(title: str, existing_notes: dict[str, str]) -> bool:
    """
    检查论文标题是否与已有笔记匹配
    只有精确匹配方法名时才返回 True
    """
    if not title:
        return False

    normalized_candidates = {
        _normalize_method_name(title.strip()),
        _normalize_method_name(title.split(':', 1)[0].strip()),
    }

    for method_normalized in normalized_candidates:
        if not method_normalized:
            continue
        for note_method in existing_notes.keys():
            # 完全相等
            if note_method == method_normalized:
                return True
            # 笔记方法名完全包含在标题方法名中（且长度相近）
            if note_method in method_normalized and len(note_method) > 3:
                # 确保不是太短的匹配（避免 "gs" 匹配 "3dgs"）
                if len(note_method) >= len(method_normalized) * 0.5:
                    return True

    return False


def _normalize_method_name(value: str) -> str:
    normalized = value.strip().lower().translate(_SUBSCRIPT_TRANSLATION)
    for source, target in _GREEK_REPLACEMENTS.items():
        normalized = normalized.replace(source, target)
    normalized = normalized.replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "", normalized)


def _extract_note_method_names(stem: str) -> set[str]:
    candidates = {stem}

    match = re.match(r"^(?:19|20)\d{2}_(.+)$", stem)
    if match:
        candidates.add(match.group(1))

    return {
        normalized
        for candidate in candidates
        if (normalized := _normalize_method_name(candidate))
    }


def load_progress() -> dict:
    """加载进度"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'completed': [], 'failed': [], 'current': None, 'started_at': None}


def save_progress(progress: dict):
    """保存进度"""
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


def build_analysis_prompt(source_info: str, no_pdf_instruction: str) -> str:
    return f"""请深读并分析这篇论文，输出结构化分析。

{source_info}
{no_pdf_instruction}

## 输出结构

1. **Decision summary**
   - 这篇论文解决什么问题
   - 核心方法是什么
   - 证据是否足够强
   - 是否值得继续深读
2. **Research analysis**
   - 问题设定
   - 方法拆解
   - 实验与结果
   - 局限性 / 风险 / 下一步值得检查什么

## 处理规则

- 默认只做分析，不要假设要保存到 Obsidian
- 默认不要创建概念笔记
- 默认不要移动 Zotero 分类
- 默认不要执行 git、索引刷新或归档动作
- 如果没有本地 PDF，按给定优先级获取在线内容
- 不要编造缺失的 benchmark 数字或实验细节
"""



def build_workflow_prompt(
    source_info: str,
    collection_path: str,
    item_id: int,
    no_pdf_instruction: str,
    notes_root: str,
    concepts_root: str,
) -> str:
    return f"""请读取并分析这篇论文，生成完整的结构化笔记。

{source_info}
Zotero 分类路径: {collection_path}
Zotero ItemID: {item_id}
{no_pdf_instruction}

## 质量要求（重要）

参考高质量笔记风格，必须包含：

1. **元信息表格**: 机构、日期、项目主页、对比基线
2. **内联概念链接**: 在正文中使用 `[[Flow Matching]]`、`[[DiT]]` 链接概念，不只是在文末
3. **公式格式**: 每个公式包含 "含义" + "符号说明" 小节
4. **图片格式**: `### Figure X: 英文标题 / 中文标题` + 在线URL + `**说明**:`
5. **批判性思考**: 优点、局限性、潜在改进方向、可复现性评估 checklist
6. **关联笔记分类**: 分为 "基于"、"对比"、"方法相关"、"硬件/数据相关"
7. **速查卡片**: ASCII 框格式的快速参考

## 处理规则

1. **图片优先在线链接**：先检查 arXiv HTML 版本 (arxiv.org/html/xxx)，有则用在线图片 URL

## 概念库更新（必须执行）

**每篇论文处理完后，必须为新遇到的技术概念创建笔记！**

### 概念库位置
{concepts_root}

### 需要创建概念笔记的情况
1. 论文中首次遇到的技术术语（如 Flow Matching、Action Chunking、DiT）
2. 论文提出的新方法名（如果是通用概念）
3. 在笔记中使用了 [[概念]] 链接但该概念笔记不存在

### 概念笔记格式
```markdown
---
type: concept
aliases: [别名1, 别名2]
---

# 概念名称

## 定义
一句话定义

## 数学形式（如有）
$$公式$$

## 核心要点
1. 要点1
2. 要点2

## 代表工作
- [[论文1]]: 说明
- [[论文2]]: 说明

## 相关概念
- [[相关概念1]]
```

### 概念目录结构（已存在的分类）
- 1-生成模型/: Diffusion Model, DiT, VAE, Flow Matching, EDM, Latent Diffusion 等
- 2-强化学习/: MDP, Policy, Value Function, PPO, GAIL, World Model 等
- 3-机器人策略/: Action Chunking, Inverse Dynamics Model, Sim-to-Real 等
- 4-足式运动/: CPG, Curriculum Learning, Privileged Learning 等
- 5-导航与定位/: VLN 等
- 如果是新领域，创建新的子目录（如 6-3D视觉/）

### 执行步骤
1. 分析完论文后，列出笔记中所有 [[概念]] 链接
2. 检查每个概念是否已存在：查看 `{concepts_root}` 下已有概念笔记
3. 对于不存在的概念，创建概念笔记文件
4. 将概念笔记写入对应文件

## 自动分类与 Zotero 同步（重要）

**不要依赖关键词匹配！** 你需要真正理解论文后自主判断分类。

### 分类判断原则
1. 理解论文的**核心贡献**是什么
2. 问自己：如果我要找这篇论文，我会去哪个分类找？
3. 按**主要贡献**分类，而不是使用的技术
   - 例：用 Diffusion 做机器人控制 → VLA，不是 Diffusion Model
   - 例：用 3DGS 做 SLAM → SLAM，不是 3DGS

### 分类操作
使用 zotero_helper.py 脚本：
- collections: 列出所有分类
- find-collection "名称": 查找分类ID
- move <item_id> <collection_id>: 移动论文

### 何时必须移动
- 当前在 "2025"、"杂项"、"feifeili" 等临时分类 → 必须移动
- 分类与论文内容明显不符 → 移动

## 保存位置

根据你对论文的理解，保存到对应的 Obsidian 目录：
- 基本结构：{notes_root}/对应分类路径/
- 不确定时：{notes_root}/_待整理/

请直接开始处理，不需要确认。提取所有公式、图片和表格。"""



def call_ai_backend(backend: AIBackend, paper_source: dict, collection_path: str, item_id: int, mode: str) -> tuple[bool, str]:
    """
    调用 AI backend 处理论文

    paper_source 可以包含:
    - pdf_path: 本地 PDF 路径
    - arxiv_id: arXiv ID (如 2401.12345)
    - doi: DOI
    - url: 论文 URL
    - title: 论文标题 (用于搜索)
    """

    arxiv_id = paper_source.get('arxiv_id', '')
    notes_root = PAPER_NOTES_ROOT
    concepts_root = CONCEPTS_ROOT

    # 构建来源信息
    source_lines = []
    if paper_source.get('pdf_path'):
        source_lines.append(f"PDF 路径: {paper_source['pdf_path']}")
    if arxiv_id:
        source_lines.append(f"arXiv ID: {arxiv_id}")
        source_lines.append(f"arXiv 页面: https://arxiv.org/abs/{arxiv_id}")
        source_lines.append(f"arXiv PDF: https://arxiv.org/pdf/{arxiv_id}.pdf")
        source_lines.append(f"arXiv HTML (图片): https://arxiv.org/html/{arxiv_id}")
    if paper_source.get('doi'):
        source_lines.append(f"DOI: {paper_source['doi']}")
        source_lines.append(f"DOI 链接: https://doi.org/{paper_source['doi']}")
    if paper_source.get('url'):
        source_lines.append(f"URL: {paper_source['url']}")
    if paper_source.get('title'):
        source_lines.append(f"论文标题: {paper_source['title']}")

    source_info = '\n'.join(source_lines)

    # 如果没有 PDF，添加特殊说明
    no_pdf_instruction = ""
    if not paper_source.get('pdf_path'):
        fallback_steps = []
        if arxiv_id:
            fallback_steps.extend(
                [
                    f"1. **arXiv HTML 版本**（推荐）: 读取 https://arxiv.org/html/{arxiv_id}，可直接获取图片 URL",
                    f"2. **arXiv 摘要页**: 读取 https://arxiv.org/abs/{arxiv_id}",
                    f"3. **arXiv PDF**: 下载 https://arxiv.org/pdf/{arxiv_id}.pdf 到本地后读取",
                ]
            )
        if paper_source.get('doi'):
            fallback_steps.append(f"{len(fallback_steps) + 1}. **DOI 页面**: 跳转到 https://doi.org/{paper_source['doi']} 读取")
        if paper_source.get('url'):
            fallback_steps.append(f"{len(fallback_steps) + 1}. **原始 URL**: 读取 {paper_source['url']}")
        if not fallback_steps:
            fallback_steps.append("1. 根据标题搜索在线来源，再优先读取可直接获取图片的 HTML 版本")

        no_pdf_instruction = f"""
## 无本地 PDF - 在线获取（重要）

这篇论文没有本地 PDF，请按以下优先级获取内容：

{chr(10).join(fallback_steps)}

优先使用 HTML 版本，因为可以直接获取在线图片链接！
"""

    prompt = (
        build_analysis_prompt(source_info, no_pdf_instruction)
        if mode == 'analysis'
        else build_workflow_prompt(
            source_info,
            collection_path,
            item_id,
            no_pdf_instruction,
            notes_root,
            concepts_root,
        )
    )

    try:
        backend.process(prompt, timeout=900)
        return True, ''
    except RateLimitError:
        return False, 'RATE_LIMIT'
    except QuotaLimitError as e:
        return False, f'QUOTA_LIMIT|{str(e)}'
    except BackendTimeoutError:
        return False, 'TIMEOUT'
    except AIBackendError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def process_collection(
    collection_name: str,
    resume: bool = True,
    mode: str = 'workflow',
    backend: Optional[AIBackend] = None,
):
    """处理整个分类的论文"""
    logger.info(f"=== 开始处理分类: {collection_name} ===")

    # 创建 AI backend 实例
    if backend is None:
        backend = AIBackend.from_config()
    logger.info(f"AI backend: {type(backend).__name__}")

    db_path = copy_zotero_db()

    collection_id, collection_path = get_collection_id_and_path(db_path, collection_name)
    if not collection_id:
        logger.error(f"找不到分类: {collection_name}")
        return

    logger.info(f"分类路径: {collection_path} (ID: {collection_id})")

    papers = get_papers_in_collection(db_path, collection_id)
    logger.info(f"分类下共有 {len(papers)} 篇论文")

    progress = load_progress() if resume else {'completed': [], 'failed': [], 'current': None, 'started_at': None}
    if not progress['started_at']:
        progress['started_at'] = datetime.now().isoformat()

    # 获取已有笔记
    existing_notes = get_existing_notes()
    logger.info(f"Obsidian 中已有 {len(existing_notes)} 篇笔记")

    # 过滤待处理论文
    pending = []
    skipped_existing = 0
    for paper in papers:
        item_id = paper['item_id']
        title = paper['title']

        if item_id in progress['completed']:
            continue

        # 检查是否已有笔记
        if title_matches_note(title, existing_notes):
            logger.info(f"跳过 (已有笔记): {title[:50]}")
            skipped_existing += 1
            progress['completed'].append(item_id)  # 标记为已完成
            continue

        pdf_path = get_pdf_path(db_path, item_id)
        paper_source = {'title': title}

        if pdf_path and os.path.exists(pdf_path):
            paper_source['pdf_path'] = pdf_path
        else:
            # 尝试获取在线来源
            online_source = get_paper_online_source(db_path, item_id)
            if online_source:
                paper_source.update(online_source)
                logger.info(f"无本地 PDF，使用在线来源: {list(online_source.keys())}")
            else:
                logger.warning(f"跳过 (无PDF且无在线来源): {title[:50]}")
                continue

        pending.append({**paper, 'source': paper_source})

    if skipped_existing > 0:
        logger.info(f"跳过已有笔记: {skipped_existing} 篇")
        save_progress(progress)

    logger.info(f"待处理: {len(pending)} 篇")

    wait_time = INITIAL_WAIT

    for i, paper in enumerate(pending):
        item_id = paper['item_id']
        title = paper['title']
        paper_source = paper['source']

        source_type = "PDF" if paper_source.get('pdf_path') else "在线"
        logger.info(f"\n[{i+1}/{len(pending)}] 处理 ({source_type}): {title[:60]}...")
        progress['current'] = {'item_id': item_id, 'title': title}
        save_progress(progress)

        success, error = call_ai_backend(backend, paper_source, collection_path, item_id, mode)

        if success:
            logger.info(f"✓ 完成: {title[:50]}")
            progress['completed'].append(item_id)
            progress['current'] = None
            save_progress(progress)
            wait_time = INITIAL_WAIT

            if i < len(pending) - 1:
                time.sleep(BETWEEN_PAPERS_WAIT)

        elif error == 'RATE_LIMIT':
            logger.warning(f"⏳ Rate limit, 等待 {wait_time} 秒...")
            time.sleep(wait_time)
            wait_time = min(wait_time * WAIT_MULTIPLIER, MAX_WAIT)
            pending.insert(i + 1, paper)  # 重新加入队列

        elif error.startswith('QUOTA_LIMIT'):
            reset_wait = parse_reset_wait_seconds(error)
            if reset_wait:
                logger.warning(f"⏳ 用量上限，等待到重置（约 {reset_wait // 60} 分钟）...")
                time.sleep(reset_wait)
            else:
                wait_for_quota_reset()
            pending.insert(i + 1, paper)  # 重新加入队列

        elif error == 'TIMEOUT':
            logger.error(f"✗ 超时: {title[:50]}")
            progress['failed'].append({'item_id': item_id, 'title': title, 'error': 'TIMEOUT'})
            save_progress(progress)

        else:
            logger.error(f"✗ 失败: {title[:50]} - {error[:100]}")
            progress['failed'].append({'item_id': item_id, 'title': title, 'error': error[:200]})
            save_progress(progress)

    progress['current'] = None
    progress['finished_at'] = datetime.now().isoformat()
    save_progress(progress)

    logger.info("\n=== 处理完成 ===")
    logger.info(f"成功: {len(progress['completed'])} 篇")
    logger.info(f"失败: {len(progress['failed'])} 篇")


def show_status():
    """显示当前进度"""
    progress = load_progress()
    print("\n=== Paper Daemon 状态 ===")
    print(f"开始时间: {progress.get('started_at', 'N/A')}")
    print(f"完成时间: {progress.get('finished_at', '进行中...')}")
    print(f"已完成: {len(progress.get('completed', []))} 篇")
    print(f"失败: {len(progress.get('failed', []))} 篇")

    current = progress.get('current')
    if current:
        print(f"当前处理: {current.get('title', 'N/A')[:60]}")

    if progress.get('failed'):
        print("\n失败的论文:")
        for item in progress['failed'][:5]:
            print(f"  - {item['title'][:50]}: {item['error'][:50]}")


def main():
    parser = argparse.ArgumentParser(
        description='Paper Reading Daemon',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
AI backend 选择（不需要改配置文件，命令行直接指定）:
  # 用 Claude Code（默认）
  python3 paper_daemon.py -c "VLA" --backend claude

  # 用 Codex CLI
  python3 paper_daemon.py -c "VLA" --backend codex

  # 用 OpenAI API
  python3 paper_daemon.py -c "VLA" --backend openai

  # 自定义 CLI 工具
  python3 paper_daemon.py -c "VLA" --backend codex \\
      --cli-args "exec,--sandbox,workspace-write,--skip-git-repo-check"

  # 用 OpenAI API + 自定义模型
  python3 paper_daemon.py -c "VLA" --backend openai \\
      --api-model gpt-4-turbo --api-key-env MY_OPENAI_KEY

不指定 --backend 时，从 _shared/user-config.json 的 ai_backend.type 读取。
        """.strip(),
    )
    parser.add_argument('--collection', '-c', type=str, help='Zotero 分类名称')
    parser.add_argument('--status', '-s', action='store_true', help='显示当前状态')
    parser.add_argument('--list', '-l', action='store_true', help='列出 Zotero 分类')
    parser.add_argument('--no-resume', action='store_true', help='不恢复之前的进度')
    parser.add_argument('--mode', choices=['analysis', 'workflow'], default='workflow', help='批处理模式：analysis 为默认结构化分析，workflow 为完整归档流程')

    # AI backend 参数
    parser.add_argument('--backend', choices=['claude', 'codex', 'openai'],
                        help='AI backend 预设（不指定则从配置文件读取）')
    parser.add_argument('--cli-command', help='覆盖 CLI 命令（如 codex, aider）')
    parser.add_argument('--cli-args', help='CLI 参数，逗号分隔（如 exec,--sandbox,workspace-write）')
    parser.add_argument('--cli-input-mode', choices=['stdin', 'arg'], help='CLI prompt 输入模式')
    parser.add_argument('--cli-prompt-arg', help='prompt 参数名（空字符串=位置参数，如 "" 或 -p）')
    parser.add_argument('--api-model', help='API 模型名（如 gpt-4o, claude-opus-4）')
    parser.add_argument('--api-key-env', help='API key 环境变量名（如 OPENAI_API_KEY）')
    parser.add_argument('--api-base-url', help='API base URL（OpenAI 兼容端点）')

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if args.list:
        db_path = copy_zotero_db()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.collectionName, COUNT(ci.itemID) as count
            FROM collections c
            LEFT JOIN collectionItems ci ON c.collectionID = ci.collectionID
            GROUP BY c.collectionID
            HAVING count > 0
            ORDER BY c.collectionName
        """)
        print("\n=== Zotero 分类 ===")
        for name, count in cursor.fetchall():
            print(f"  {name}: {count} 篇")
        conn.close()
        return

    if not args.collection:
        parser.print_help()
        return

    # 构建 AI backend
    backend = AIBackend.from_cli_args(
        preset=args.backend,
        cli_command=args.cli_command,
        cli_args=args.cli_args,
        cli_input_mode=args.cli_input_mode,
        cli_prompt_arg=args.cli_prompt_arg,
        api_model=args.api_model,
        api_key_env=args.api_key_env,
        api_base_url=args.api_base_url,
    )
    logger.info(f"AI backend: {type(backend).__name__}")

    # 检查是否已有进程在运行
    if not acquire_lock():
        logger.error(f"另一个 paper_daemon 进程正在运行！请先停止它或删除 {PID_FILE}")
        return

    try:
        process_collection(
            args.collection,
            resume=not args.no_resume,
            mode=args.mode,
            backend=backend,
        )
    finally:
        release_lock()


if __name__ == '__main__':
    main()
