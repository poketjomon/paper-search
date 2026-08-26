# papersearch

🌐 [English](README.md) | **简体中文** | [繁體中文](README.zh-TW.md)

> 面向 AI Agent 的论文研究技能套件（Skill Suite）。
> 支持 Claude Code、Codex、Qoder 等任何能读 `SKILL.md` 并执行 shell 命令的 agent 框架，也可以不装任何 agent、纯命令行直接使用。

## 它能做什么

| 子技能 | 用途 | 一句话示例 |
|---|---|---|
| **search** | 按主题 / 会议 / 年份批量找论文 | “帮我找 2024 ICLR 上 diffusion policy 的论文，要有代码” |
| **lookup** | 单篇论文 30 秒速览，判断值不值得读 | “快速看一下 arXiv 2303.04137” |
| **reader** | 单篇论文深度分析 | “深度分析这篇论文的方法和实验设计” |
| **归档工作流** | 生成 Obsidian 笔记、维护 Zotero 分类（显式触发） | “读这篇论文并归档到我的 Obsidian 笔记库” |

特点：

- **本地优先检索**：内置 11 个顶会（AAAI / ACL / AI4X / EMNLP / ICCV / ICLR / ICML / IJCAI / KDD / NeurIPS / WWW）论文数据集，也识别 CORL 会议（无本地数据时自动回退 arXiv），本地覆盖不足时如实报告
- **零依赖**：纯 Python 标准库，不需要 pip 安装任何东西
- **多框架兼容**：批处理守护进程支持 Claude Code / Codex / OpenAI API 等后端，命令行一键切换

## 安装

### 方式一：装进你的 Agent 框架（推荐）

把本仓库放进 agent 的 skills 目录即可，agent 会自动读取 `SKILL.md` 完成路由：

```bash
# Claude Code
ln -s "$PWD" ~/.claude/skills/papersearch

# Codex
ln -s "$PWD" ~/.codex/skills/papersearch
```

其他框架（Qoder、Cursor 等）请参考各自的 skill / plugin 安装方式，核心要求只有一个：agent 能读到 `SKILL.md`，并能执行 `./scripts/run.sh`。

装好后直接用自然语言提问：

```text
帮我找 2024 ICLR 上 diffusion policy 的论文，最好有代码和项目链接
快速看一下这篇论文值不值得读：https://arxiv.org/abs/2303.04137
深度分析这篇论文的方法、实验设计和局限
```

### 方式二：纯命令行使用（零安装）

不装任何 agent 也能用，直接跑脚本：

```bash
./scripts/run.sh <search|lookup|reader> [args...]
```

## 功能演示（真实输出）

### 1) search：找一批论文

```bash
./scripts/run.sh search "find iclr papers about world model"
```

输出（节选）：

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

支持的筛选条件（自然语言里直接写就行）：

- 会议：`ICLR`、`ICML`、`NeurIPS`、`AAAI`、`ACL`、`EMNLP`、`ICCV`、`IJCAI`、`KDD`、`WWW`、`CORL`（CORL 无本地数据，自动走 arXiv 回退）
- 年份：`2024` 或范围 `2023-2025`
- 资源：`with code`、`with pdf`

本地匹配较弱时会明确报告 `Local status: weak` 并自动用 arXiv API 补充，不会拿不相关的结果糊弄你。

完整示例：搜索最近两年 Agent RL 相关论文 → [examples/agent_rl_papers.md](./examples/agent_rl_papers.md)

### 2) lookup：单篇速览

给一个 arXiv ID 或链接，30 秒判断值不值得读：

```bash
./scripts/run.sh lookup "2303.04137" --format brief-zh
```

输出（节选）：

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

可选格式：`--format brief`（英文简报）| `brief-zh`（中文简报）| `markdown` | `text` | `json`

支持的输入：`2401.12345`、`https://arxiv.org/abs/2401.12345`、`https://www.alphaxiv.org/overview/2401.12345`

### 3) reader：深度阅读

```bash
./scripts/run.sh reader -c "VLA"                # 批量处理 Zotero 的 VLA 分类
./scripts/run.sh reader --status                # 查看批处理进度
./scripts/run.sh reader --list                  # 列出 Zotero 所有分类
```

在 agent 里则直接说：“帮我深读这篇论文”“读这篇论文并生成 Obsidian 归档笔记”。

默认只做结构化分析（问题、方法、实验、局限）；只有你明确提到 **保存 / 归档 / Obsidian / Zotero / 批处理** 时才会进入归档工作流（写笔记、建概念库、移动 Zotero 分类）。

## 多 Agent 框架支持

批量处理（`paper_daemon.py`）需要调用 AI 处理每篇论文。默认用 Claude Code，但可以通过 `--backend` 参数一键切换，**不需要改任何配置文件**：

```bash
# Claude Code（默认）
./scripts/run.sh reader -c "VLA" --backend claude

# OpenAI Codex CLI
./scripts/run.sh reader -c "VLA" --backend codex

# OpenAI API（需要 OPENAI_API_KEY 环境变量）
./scripts/run.sh reader -c "VLA" --backend openai

# 任意 CLI 工具（连预设都不用）
./scripts/run.sh reader -c "VLA" \
    --cli-command aider --cli-args "--model,gpt-4o" --cli-input-mode stdin
```

| `--backend` | 对应工具 | 实际调用 |
|---|---|---|
| `claude` | Claude Code CLI | `claude -p "prompt" --model opus ...` |
| `codex` | Codex CLI | `codex exec --sandbox workspace-write "prompt"` |
| `openai` | OpenAI 兼容 API | HTTP POST `/chat/completions` |

更细的覆盖参数（`--cli-command`、`--cli-args`、`--api-model`、`--api-key-env`、`--api-base-url` 等）见 `./scripts/run.sh reader --help`。

## 配置

所有配置在 [`_shared/user-config.json`](_shared/user-config.json)，主要分五段：

| 配置段 | 内容 |
|---|---|
| `paths` | Obsidian vault、论文笔记目录、Zotero 数据库路径 |
| `daily_papers` | arXiv 每日论文的关键词过滤规则 |
| `automation` | 是否自动刷新索引、是否 git commit/push |
| `ai_backend` | AI 后端类型及参数（`claude_code` / `generic_cli` / `openai_api`） |
| `daemon` | 批处理状态目录（进度、日志、锁文件） |

个人定制不要直接改 `user-config.json`，而是新建 `_shared/user-config.local.json` 做覆盖（已加入 `.gitignore`）：

```json
{
  "paths": {
    "obsidian_vault": "~/Documents/MyVault"
  },
  "ai_backend": {
    "type": "openai_api"
  }
}
```

命令行参数优先级高于配置文件：`--backend` 等参数 > `user-config.local.json` > `user-config.json` > 内置默认值。

## 项目结构

```text
papersearch/
├── SKILL.md                 # 顶层路由：把请求分发给对应子技能
├── scripts/run.sh           # 统一入口
├── search/                  # 批量检索（本地 journal/** 数据集 + arXiv 回退）
│   ├── SKILL.md
│   ├── paper_search.py
│   └── journal/             # 11 个顶会的论文数据集
├── lookup/                  # 单篇速览（alphaXiv 优先，arXiv 兜底）
│   ├── SKILL.md
│   └── scripts/alphaxiv_lookup.py
├── reader/                  # 深度阅读 + 归档工作流
│   ├── SKILL.md
│   ├── paper_daemon.py      # 批处理守护进程（断点续传、限速重试）
│   ├── lib/ai_backend.py    # AI 后端抽象层
│   └── assets/              # 笔记模板、Zotero 辅助脚本
├── _shared/
│   ├── user_config.py       # 配置加载
│   └── user-config.json     # 默认配置
└── examples/                # 搜索输出示例
```

## 常见问题

**我需要手动选 search / lookup / reader 吗？**
不需要。在 agent 里直接说目标，路由层会自动分发；命令行场景按上面的入口调用即可。

**search 的本地数据覆盖哪些会议？**
AAAI / ACL / AI4X / EMNLP / ICCV / ICLR / ICML / IJCAI / KDD / NeurIPS / WWW，见 `search/journal/`。CORL 会被识别为会议筛选条件，但无本地数据，会自动回退 arXiv API。本地覆盖弱时也会自动回退并明确告知。

**归档工作流需要什么前置条件？**
需要本机安装 Zotero 和 Obsidian，并在 `_shared/user-config.local.json` 中配置好 vault 和 Zotero 数据库路径。search / lookup 不需要任何前置条件。

**批处理中断了怎么办？**
进度保存在状态目录（默认 `~/.papersearch/`），重新运行相同命令会自动断点续传；用 `--no-resume` 可强制从头开始。

## 环境要求

- Python 3.9+（纯标准库，无第三方依赖）
- macOS / Linux
- （可选）Zotero + Obsidian，仅归档工作流需要

## 测试

```bash
python3 -m unittest search/tests/test_paper_search.py
```
