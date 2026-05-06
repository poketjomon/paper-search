# papersearch

这是一个 **Claude Code Skill 套件**，用于论文检索、快速摘要与深度阅读工作流，包含三个子 skill：`search` / `lookup` / `reader`。

## 这个项目怎么用（最重要）

你通常不会直接 import 代码，而是在 Claude Code 里调用这个 skill。

### 1) 作为顶层 skill 使用

当该 skill 已安装后，可直接让 Claude 执行类似请求：

- `帮我找 2024 ICLR 上 diffusion policy 的论文，最好有代码`
- `帮我快速看这篇 arXiv: 2401.12345`
- `深度分析这篇论文，并给出是否值得精读`

顶层路由规则见 [SKILL.md](SKILL.md)：

- 多论文检索/筛选 → `search`
- 单篇快速 brief（arXiv/alphaXiv）→ `lookup`
- 单篇深读或笔记归档流程 → `reader`

### 2) 本地命令行调试（开发者）

在仓库根目录可通过统一入口脚本验证行为：

```bash
./scripts/run.sh <search|lookup|reader> [args...]
```

例如：

```bash
./scripts/run.sh search "find 2024 iclr papers about diffusion policy with code"
./scripts/run.sh lookup "2401.12345" --format brief
./scripts/run.sh reader --status
```

### 3) Claude Code 最小示例对话（可直接照抄）

```text
你：帮我找 2024 ICLR 上 diffusion policy 的论文，最好有代码
Claude：<调用 papersearch 的 search 路由并返回论文列表>
```

```text
你：快速看这篇论文：https://arxiv.org/abs/2401.12345
Claude：<调用 lookup 路由并返回结构化 brief>
```

```text
你：深度分析这篇论文的方法与实验设计，给出是否值得精读
Claude：<调用 reader 路由并返回深度分析>
```

## 子 skill 说明

### search

- 入口脚本：`search/scripts/run.sh`
- skill 定义：`search/SKILL.md`
- 核心能力：本地 `journal/**` 语义检索、过滤（venue/year/code/pdf）、弱匹配检测、必要时 arXiv fallback

### lookup

- 入口脚本：`lookup/scripts/run.sh`
- skill 定义：`lookup/SKILL.md`
- 核心能力：对指定 arXiv/alphaXiv 论文快速生成结构化 brief

### reader

- 入口脚本：`reader/scripts/run.sh`
- skill 定义：`reader/SKILL.md`
- 核心能力：单篇论文深读；在显式要求时进入 Zotero/Obsidian 的高级归档流程

## 目录结构

```text
papersearch/
├── SKILL.md                   # 顶层 skill 路由
├── references/usage.md        # 套件使用说明
├── scripts/run.sh             # 统一入口（本地调试）
├── search/
│   ├── SKILL.md
│   ├── paper_search.py
│   ├── scripts/run.sh
│   └── journal/
├── lookup/
│   ├── SKILL.md
│   └── scripts/
│       ├── run.sh
│       └── alphaxiv_lookup.py
└── reader/
    ├── SKILL.md
    ├── paper_daemon.py
    └── scripts/run.sh
```

## 环境要求

- Python 3.10+
- macOS / Linux

## 测试（当前）

```bash
python3 -m unittest search/tests/test_paper_search.py
```

## 备注

- `reader` 依赖本机 Zotero 与 `_shared/user-config.json` 配置。
- 更详细的套件级说明见 [references/usage.md](references/usage.md)。
