# papersearch

🌐 [English](README.md) | [繁體中文](README.zh-TW.md)

面向 **Claude Code** 的論文研究 Skill 套件，涵蓋從多篇檢索、單篇速讀到深度閱讀的完整流程。

> 適用於快速找論文、篩選候選、生成結構化摘要，以及判斷是否值得精讀。

## 核心能力

- **search**：多篇論文檢索與篩選（venue/year/code/pdf 等）
- **lookup**：單篇論文快速摘要（arXiv / alphaXiv）
- **reader**：單篇深度閱讀，並可選擇筆記歸檔流程

## 快速開始

### 1) 在 Claude Code 中直接使用（推薦）

安裝後可直接提問：

- `幫我找 2024 ICLR 上 diffusion policy 的論文，最好有程式碼`
- `快速看這篇論文：arXiv 2401.12345`
- `深度分析這篇論文的方法與實驗，並判斷是否值得精讀`

頂層路由規則見 [SKILL.md](SKILL.md)：

- 多篇檢索/篩選 → `search`
- 單篇快速摘要 → `lookup`
- 單篇深度分析 → `reader`

### 2) 本地命令列調試（開發者）

在倉庫根目錄執行：

```bash
./scripts/run.sh <search|lookup|reader> [args...]
```

範例：

```bash
./scripts/run.sh search "find 2024 iclr papers about diffusion policy with code"
./scripts/run.sh lookup "2401.12345" --format brief
./scripts/run.sh reader --status
```

## 子 Skill 說明

### search

- 入口：`search/scripts/run.sh`
- 定義：`search/SKILL.md`
- 能力：本地 `journal/**` 語意檢索、條件過濾、弱匹配偵測，必要時進行 arXiv fallback

### lookup

- 入口：`lookup/scripts/run.sh`
- 定義：`lookup/SKILL.md`
- 能力：對指定 arXiv / alphaXiv 論文生成結構化速讀摘要

### reader

- 入口：`reader/scripts/run.sh`
- 定義：`reader/SKILL.md`
- 能力：單篇論文深度閱讀；在明確要求時可走 Zotero / Obsidian 歸檔流程

## 專案結構

```text
papersearch/
├── SKILL.md                   # 頂層路由
├── references/usage.md        # 套件級使用說明
├── scripts/run.sh             # 本地統一入口
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

## 環境需求

- Python 3.10+
- macOS / Linux

## 測試

```bash
python3 -m unittest search/tests/test_paper_search.py
```

## 注意事項

- `reader` 依賴本機 Zotero 與 `_shared/user-config.json`。
- 更完整說明見 [references/usage.md](references/usage.md)。
