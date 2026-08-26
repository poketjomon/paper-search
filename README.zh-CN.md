<div align="center">

# papersearch

### 找论文、速览论文、精读论文、把论文变成你的知识库笔记——四件事，一个套件搞定。

面向 AI Agent 的论文研究技能套件：**本地优先检索 11 个顶会**论文数据集、**30 秒速览**判断一篇论文值不值得读、**结构化深读**，还能把论文**一键归档**成带公式、图表、概念链接的 Obsidian 笔记。

支持 Claude Code、Codex、Qoder 等任何能读 `SKILL.md` 并执行 shell 命令的 agent 框架，也可以不装任何 agent、纯命令行直接使用。

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen?style=flat-square)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey?style=flat-square)

🌐 **简体中文** · [English](./README.md) · [繁體中文](./README.zh-TW.md)　|　[📥 30 秒装上](#-30-秒装上) · [🎬 怎么用](#-怎么用) · [📊 它长什么样](#-它长什么样) · [❓ FAQ](#-faq)

</div>

---

## ✨ 它能给你什么

- **找一批论文** — 按主题 / 会议 / 年份 / 有无代码检索，输出排序列表 + 每篇的匹配理由；本地覆盖弱时**如实报告**并回退 arXiv，不拿不相关结果糊弄你（[完整示例](./examples/agent_rl_papers.md)）
- **30 秒判断值不值得读** — 给一个 arXiv / alphaXiv 链接，输出结论 + 信息来源可信度，缺什么明说，绝不编造
- **结构化深读** — 问题、方法、实验、局限一次讲清；默认只分析，**不动你的任何文件**
- **归档进知识库** — 生成带公式、图表、`[[概念]]` 链接的 Obsidian 笔记，自动维护概念库、整理 Zotero 分类（只在你明确要求时启用）
- **完全零依赖** — 纯 Python 标准库，clone 下来就能跑，不需要 pip install 任何东西
- **多 agent 框架** — 批处理支持 Claude Code / Codex / OpenAI API，`--backend` 一个参数切换，不用改配置文件
- **断点续传** — 批量处理中断后重跑同一命令即可继续，自动跳过已完成的论文

## 🎯 谁会想用

| 你是 | 你能用它做什么 |
| --- | --- |
| **写 related work 的研究生** | 一句话检索某方向近几年的顶会论文，带匹配理由和代码链接，不用逐个会议官网翻 |
| **追新论文的研究者** | 刷到 arXiv 链接先扔进去速览 30 秒，值不值得读一目了然，再决定要不要精读 |
| **知识库建设者** | 把 Zotero 整个分类批量变成带公式图表的 Obsidian 笔记，自动建概念库和互链 |
| **Zotero 重度用户** | BibTeX 导出、全文搜索、安全移动分类（走 Zotero 本地 API） |
| **工具开发者** | 核心功能全是命令行脚本，不装 agent 也能用，可直接接进自己的 pipeline |

## ⚡ 30 秒装上

### 方式一：装进你的 agent 框架（推荐）

```bash
git clone https://github.com/<your-name>/papersearch.git

# Claude Code
ln -s "$PWD/papersearch" ~/.claude/skills/papersearch

# Codex
ln -s "$PWD/papersearch" ~/.codex/skills/papersearch
```

其他框架（Qoder / Cursor / 自建 agent）：核心要求只有两个——agent 能读到顶层 `SKILL.md`（路由契约），能执行 `./scripts/run.sh`。按各自框架的 skill 安装方式接入即可。

### 方式二：纯命令行（零安装）

不装任何 agent 也能用全部核心功能：

```bash
./scripts/run.sh <search|lookup|reader> [args...]
```

### 验证安装

```bash
./scripts/run.sh search "find iclr papers about world model"
```

看到论文表格输出就说明装好了。

## 🎬 怎么用

安装后在 agent 对话里说出以下任一句即可触发：

- 「帮我找 2024 ICLR 上 diffusion policy 的论文，最好有代码和项目链接」
- 「给我整理一份 2023-2025 年 VLA 方向的 related work 列表」
- 「快速看一下这篇论文值不值得读：https://arxiv.org/abs/2303.04137」
- 「深度分析这篇论文的方法、实验设计和局限」
- 「读这篇论文并归档到我的 Obsidian 笔记库」
- 「把 Zotero 里 VLA 分类的论文导出成 references.bib」
- "Find 2024 ICLR papers about diffusion policy, preferably with code"
- "Is this paper worth reading: https://arxiv.org/abs/2303.04137"

你不需要记住 search / lookup / reader 三个子技能——路由层会自动选最轻的方式完成（能速览就不深读，能本地查就不走网络）。

<details>
<summary><b>子技能详细用法（筛选语法 / 输出格式 / 命令行参数）</b></summary>

### search：批量检索

自然语言里直接写筛选条件，不需要学特殊语法：

| 筛选 | 写法示例 |
|---|---|
| 会议 | `ICLR`、`ICML`、`NeurIPS`、`AAAI`、`ACL`、`EMNLP`、`ICCV`、`IJCAI`、`KDD`、`WWW`、`CORL` |
| 年份 | `2024` 或范围 `2023-2025` |
| 资源 | `with code`、`with pdf` |

本地数据覆盖 11 个顶会（见 `search/journal/`）；CORL 无本地数据时自动走 arXiv 回退并明确标注 `Fallback: arXiv`。结果同时保存为 `search/outputs/latest_search_results.md`。

### lookup：单篇速览

支持的输入：`2303.04137`、`1706.03762v7`、arXiv 链接、alphaXiv 链接。

```bash
./scripts/run.sh lookup "2303.04137" --format brief-zh   # 中文简报
./scripts/run.sh lookup "2303.04137" --format brief      # 英文简报
./scripts/run.sh lookup --input-file papers.txt --format brief   # 批量（每行一个 ID）
```

格式选项：`brief` / `brief-zh` / `markdown` / `text` / `json` / `json-compact`。

### reader：深读与批处理

```bash
./scripts/run.sh reader -c "VLA"        # 批量处理 Zotero 分类（递归子分类）
./scripts/run.sh reader --status        # 查看进度
./scripts/run.sh reader --list          # 列出 Zotero 分类
```

默认只做结构化分析；只有明确提到**保存 / 归档 / Obsidian / Zotero / 批处理**时才进入归档工作流。

</details>

## 📊 它长什么样

### 1. search —— 找一批论文

```bash
./scripts/run.sh search "find iclr papers about world model"
```

```text
Found 5 papers for: world model

Filters: venue=ICLR

Local status: strong

| Year | Venue | Title                                        | Link   | Why                                        |
| ---- | ----- | -------------------------------------------- | ------ | ------------------------------------------ |
| 2025 | ICLR  | Dream to Manipulate: Compositional World ... | [link] | venue match, title match, keyword match ... |
| 2025 | ICLR  | Hierarchical World Models as Visual Whole... | [link] | venue match, title match, keyword match ... |
| 2025 | ICLR  | FLIP: Flow-Centric Generative Planning as... | [link] | venue match, title match, keyword match ... |

Saved markdown report: search/outputs/latest_search_results.md
```

怎么读：**Filters** 是系统从你话里解析出的条件（确认它理解对了）；**Local status** 弱时说明结果来自 arXiv 回退；**Why** 是每篇的命中理由，方便判断相关性。

### 2. lookup —— 30 秒速览

```bash
./scripts/run.sh lookup "2303.04137" --format brief-zh
```

```text
论文：Diffusion Policy: Visuomotor Policy Learning via Action Diffusion（2303.04137）
一句话结论：This paper introduces Diffusion Policy, a new way of generating robot
           behavior by representing a robot's visuomotor policy as a conditional
           denoising diffusion process.
解决什么问题：We benchmark Diffusion Policy across 12 different tasks from 4
           different robot manipulation benchmarks ...
核心方法：
- To fully unlock the potential of diffusion models for visuomotor policy
  learning on physical robots, this paper presents a set of key technical
  contributions ...
值不值得读：先看摘要即可；这版主要依赖 arXiv fallback。
来源：arXiv 摘要 fallback。可信度：基础（alphaXiv: http_error）。
```

最后两行告诉你信息从哪来、可信度多少——alphaXiv 详细报告 > arXiv 摘要，系统不会为了好看而编造。

### 3. 归档笔记 —— 论文变知识库

<details>
<summary><b>展开看生成的笔记包含什么</b></summary>

按 [`reader/assets/paper-note-template.md`](reader/assets/paper-note-template.md) 生成：

- **YAML frontmatter**：标题、方法名、作者、年份、会议、标签、Zotero 分类
- **元信息表格**：机构、日期、项目主页、对比基线、链接
- **一句话总结** + **核心贡献**
- **方法详解**：模块拆解，技术术语全部内联 `[[概念]]` 链接
- **关键公式**：每个公式都有"含义 + 符号说明"
- **关键图表**：`### Figure X: 英文标题 / 中文标题` + 图片来源 + 说明
- **实验**：数据集、实现细节、定性结果
- **批判性思考**：优点、局限、改进方向、可复现性 checklist
- **关联笔记**：按"基于 / 对比 / 方法相关 / 硬件数据"分类
- **速查卡片**：Obsidian callout 格式的快速参考

归档流程还会：为新概念自动建概念笔记、把论文移动到合理的 Zotero 分类（基于对论文的理解判断，不是关键词匹配）、拿不准的笔记放 `_待整理/`。

</details>

## 🔧 多 agent 框架切换

批处理需要调用 AI 逐篇处理论文。默认 Claude Code，`--backend` 一键切换，**不用改配置文件**：

```bash
./scripts/run.sh reader -c "VLA" --backend claude    # 默认
./scripts/run.sh reader -c "VLA" --backend codex     # Codex CLI
./scripts/run.sh reader -c "VLA" --backend openai    # OpenAI API（需 OPENAI_API_KEY）
```

| `--backend` | 实际调用 |
|---|---|
| `claude` | `claude -p "prompt" --model opus --permission-mode acceptEdits ...` |
| `codex` | `codex exec --sandbox workspace-write "prompt"` |
| `openai` | HTTP POST `{base_url}/chat/completions` |

还能细粒度覆盖（`--cli-command` / `--cli-args` / `--api-model` / `--api-key-env` / `--api-base-url`），甚至直接接入任意 CLI 工具：

```bash
./scripts/run.sh reader -c "VLA" --cli-command aider --cli-args "--model,gpt-4o" --cli-input-mode stdin
```

完整参数：`./scripts/run.sh reader --help`。优先级：命令行参数 > `user-config.local.json` > `user-config.json` > 内置默认值。

## 🗂️ 配套技能（随仓库附带，无需单独安装）

| 技能 | 干什么 | 什么时候被用到 |
|---|---|---|
| `obsidian_skills/obsidian-markdown` | Obsidian 语法规范（wikilinks / callouts / embeds / frontmatter） | 每次归档写笔记时自动遵循 |
| `obsidian_skills/obsidian-cli` | 通过 CLI 搜索 / 操作 vault | 概念查重、vault 搜索（需本机装 Obsidian CLI） |
| `obsidian_skills/obsidian-bases` | `.base` 数据库视图 | 你想要论文库的可筛选视图时 |
| `zotero_skills/zotero` | Zotero 本地 API：安全移动分类、BibTeX 导出、全文搜索 | Zotero 桌面版运行且开启本地 API 时 |

分工原则：Zotero 关闭时的批量只读查询走内置 SQLite 方案（`reader/assets/zotero_helper.py`）；写操作和 API 独有能力（BibTeX / 全文搜索）走本地 API。

## ⚙️ 配置

所有配置在 [`_shared/user-config.json`](_shared/user-config.json)。个人定制请新建 `_shared/user-config.local.json`（已 gitignore）做深度合并覆盖，只写要改的字段：

```json
{
  "paths": {
    "obsidian_vault": "~/Documents/MyVault",
    "zotero_db": "~/Zotero/zotero.sqlite"
  },
  "ai_backend": { "type": "openai_api" }
}
```

| 配置段 | 内容 | 什么时候要改 |
|---|---|---|
| `paths` | Obsidian vault、笔记目录、Zotero 路径 | 用归档工作流前必改 |
| `daily_papers` | arXiv 每日论文关键词过滤 | 定制每日推送时 |
| `automation` | 索引刷新、git commit/push 开关 | 想自动提交笔记时 |
| `ai_backend` | AI 后端类型及参数 | 改默认后端时（也可用 `--backend` 临时切换） |
| `daemon` | 批处理状态目录（默认 `~/.papersearch/`） | 一般不用改 |

安全约定：API key 一律走环境变量（配置里只写变量名），永远不进 JSON。

## 🆚 跟其他工具啥不同

| 工具 | 定位 | 差异 |
| --- | --- | --- |
| Zotero 本体 | 文献管理 | 不做 AI 速览/深读，不生成知识库笔记 |
| arXiv 每日论文工具 | 新论文推荐 | 不能检索已有会议论文，无深读和归档 |
| 通用 AI 对话读 PDF | 临时读一篇 | 无本地语料、无匹配理由、无知识库工作流 |
| **papersearch** | **检索 → 速览 → 深读 → 归档一站式** | **本地语料 + 诚实回退 + 知识库自动化 + 多框架** |

简单说：**别的工具做其中一个环节，papersearch 把论文研究的全链路串起来，而且每一步都能脱离 agent 独立跑。**

## ❓ FAQ

<details>
<summary><b>我需要手动选 search / lookup / reader 吗？</b></summary>

不需要。在 agent 里直接说目标，路由层自动分发，遵循"能轻不重"原则（能速览就不深读）。命令行场景按[上面的入口](#-怎么用)调用即可。

</details>

<details>
<summary><b>本地数据覆盖哪些会议？能扩充吗？</b></summary>

AAAI / ACL / AI4X / EMNLP / ICCV / ICLR / ICML / IJCAI / KDD / NeurIPS / WWW，见 `search/journal/`。数据就是 JSON 文件，往对应目录放同格式 JSON 即可扩充。本地覆盖弱时自动回退 arXiv 并明确告知。

</details>

<details>
<summary><b>lookup 需要注册 alphaXiv 账号吗？</b></summary>

不需要，直接抓公开页面。alphaXiv 不可用或被限流时自动回退 arXiv 摘要，输出里会标注实际来源和可信度。

</details>

<details>
<summary><b>归档工作流会动我的 Zotero 数据库吗？</b></summary>

只读查询会先复制数据库再操作，不会锁库。移动分类只在显式归档流程（批处理 workflow 模式）中发生；Zotero 开着且本地 API 启用时优先走 API（更安全），否则回退 SQLite；`--mode analysis` 不写任何东西。

</details>

<details>
<summary><b>批处理中断了怎么办？会不会触发 AI 用量限制？</b></summary>

进度存在 `~/.papersearch/`，重跑同一命令自动续传；`--no-resume` 从头开始；`--status` 看进度和失败原因。限速策略内置：rate limit 指数退避（60 秒起步、最长 6 小时），配额上限自动解析重置时间并等待，论文间默认间隔 5 秒，全程无需人工干预。

</details>

<details>
<summary><b>配套的 Obsidian / Zotero 技能需要单独安装吗？</b></summary>

不需要，随仓库附带。obsidian-markdown 在每次归档写笔记时自动生效；obsidian-cli 仅在本机装了 Obsidian CLI 时使用；zotero 技能仅在 Zotero 桌面版运行且开启本地 API 时使用（否则回退内置 SQLite 方案）。

</details>

<details>
<summary><b>支持 Windows 吗？</b></summary>

脚本基于 POSIX shell，推荐 macOS / Linux；Windows 请用 WSL。

</details>

## 📁 项目结构

```text
papersearch/
├── SKILL.md                 # 顶层路由：把请求分发给对应子技能
├── scripts/run.sh           # 统一入口
├── search/                  # 批量检索（本地 journal/** + arXiv 回退）
├── lookup/                  # 单篇速览（alphaXiv 优先，arXiv 兜底）
├── reader/                  # 深读 + 归档工作流（含批处理守护进程、AI backend 抽象层）
├── _shared/                 # 配置加载、MOC 索引生成
├── obsidian_skills/         # 配套 Obsidian 技能（markdown / cli / bases）
├── zotero_skills/           # 配套 Zotero 技能（本地 API）
└── examples/                # 搜索输出示例
```

## 🌱 环境要求与测试

- Python 3.9+（纯标准库，无第三方依赖）
- macOS / Linux
- （可选）Zotero + Obsidian，仅归档工作流需要；Zotero 开启本地 API 可解锁 BibTeX 导出等能力

```bash
python3 -m unittest search/tests/test_paper_search.py
```

---

<div align="center">

**用过觉得有用？给个 ⭐ 是对作者最大的鼓励。**

[⬆ 回到顶部](#papersearch) · [📥 装一个](#-30-秒装上) · [🎬 怎么用](#-怎么用)

</div>
