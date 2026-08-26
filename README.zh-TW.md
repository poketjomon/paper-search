# papersearch

🌐 [English](README.md) | [简体中文](README.zh-CN.md) | **繁體中文**

> 面向 AI Agent 的論文研究技能套件（Skill Suite）。
> 支援 Claude Code、Codex、Qoder 等任何能讀取 `SKILL.md` 並執行 shell 指令的 agent 框架，也可以不裝任何 agent、純命令列直接使用。

## 它能做什麼

| 子技能 | 用途 | 一句話範例 |
|---|---|---|
| **search** | 依主題 / 會議 / 年份批量找論文 | 「幫我找 2024 ICLR 上 diffusion policy 的論文，要有程式碼」 |
| **lookup** | 單篇論文 30 秒速覽，判斷值不值得讀 | 「快速看一下 arXiv 2303.04137」 |
| **reader** | 單篇論文深度分析 | 「深度分析這篇論文的方法和實驗設計」 |
| **歸檔工作流** | 產生 Obsidian 筆記、維護 Zotero 分類（需明確觸發） | 「讀這篇論文並歸檔到我的 Obsidian 筆記庫」 |

特點：

- **本地優先檢索**：內建 11 個頂級會議（AAAI / ACL / AI4X / EMNLP / ICCV / ICLR / ICML / IJCAI / KDD / NeurIPS / WWW）論文資料集，也識別 CORL 會議（無本地資料時自動回退 arXiv），本地覆蓋不足時如實回報
- **零依賴**：純 Python 標準函式庫，不需要 pip 安裝任何東西
- **多框架相容**：批處理守護進程支援 Claude Code / Codex / OpenAI API 等後端，命令列一鍵切換

## 安裝

### 方式一：裝進你的 Agent 框架（推薦）

把本倉庫放進 agent 的 skills 目錄即可，agent 會自動讀取 `SKILL.md` 完成路由：

```bash
# Claude Code
ln -s "$PWD" ~/.claude/skills/papersearch

# Codex
ln -s "$PWD" ~/.codex/skills/papersearch
```

其他框架（Qoder、Cursor 等）請參考各自的 skill / plugin 安裝方式，核心要求只有一個：agent 能讀到 `SKILL.md`，並能執行 `./scripts/run.sh`。

裝好後直接用自然語言提問：

```text
幫我找 2024 ICLR 上 diffusion policy 的論文，最好有程式碼和專案連結
快速看一下這篇論文值不值得讀：https://arxiv.org/abs/2303.04137
深度分析這篇論文的方法、實驗設計和局限
```

### 方式二：純命令列使用（零安裝）

不裝任何 agent 也能用，直接跑腳本：

```bash
./scripts/run.sh <search|lookup|reader> [args...]
```

## 功能展示（真實輸出）

### 1) search：找一批論文

```bash
./scripts/run.sh search "find iclr papers about world model"
```

輸出（節選）：

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

支援的篩選條件（自然語言裡直接寫就行）：

- 會議：`ICLR`、`ICML`、`NeurIPS`、`AAAI`、`ACL`、`EMNLP`、`ICCV`、`IJCAI`、`KDD`、`WWW`、`CORL`（CORL 無本地資料，自動走 arXiv 回退）
- 年份：`2024` 或範圍 `2023-2025`
- 資源：`with code`、`with pdf`

本地匹配較弱時會明確回報 `Local status: weak` 並自動用 arXiv API 補充，不會拿不相關的結果敷衍你。

完整範例：搜尋最近兩年 Agent RL 相關論文 → [examples/agent_rl_papers.md](./examples/agent_rl_papers.md)

### 2) lookup：單篇速覽

給一個 arXiv ID 或連結，30 秒判斷值不值得讀：

```bash
./scripts/run.sh lookup "2303.04137" --format brief-zh
```

輸出（節選）：

```text
論文：Diffusion Policy: Visuomotor Policy Learning via Action Diffusion（2303.04137）
一句話結論：This paper introduces Diffusion Policy, a new way of generating robot
           behavior by representing a robot's visuomotor policy as a conditional
           denoising diffusion process.
解決什麼問題：We benchmark Diffusion Policy across 12 different tasks from 4
           different robot manipulation benchmarks ...
核心方法：
- To fully unlock the potential of diffusion models for visuomotor policy
  learning on physical robots, this paper presents a set of key technical
  contributions ...
值不值得讀：先看摘要即可；這版主要依賴 arXiv fallback。
來源：arXiv 摘要 fallback。可信度：基礎（alphaXiv: http_error）。
```

可選格式：`--format brief`（英文簡報）| `brief-zh`（中文簡報）| `markdown` | `text` | `json`

支援的輸入：`2401.12345`、`https://arxiv.org/abs/2401.12345`、`https://www.alphaxiv.org/overview/2401.12345`

### 3) reader：深度閱讀

```bash
./scripts/run.sh reader -c "VLA"                # 批量處理 Zotero 的 VLA 分類
./scripts/run.sh reader --status                # 查看批處理進度
./scripts/run.sh reader --list                  # 列出 Zotero 所有分類
```

在 agent 裡則直接說：「幫我深讀這篇論文」「讀這篇論文並產生 Obsidian 歸檔筆記」。

預設只做結構化分析（問題、方法、實驗、局限）；只有你明確提到 **儲存 / 歸檔 / Obsidian / Zotero / 批處理** 時才會進入歸檔工作流（寫筆記、建概念庫、移動 Zotero 分類）。

## 多 Agent 框架支援

批量處理（`paper_daemon.py`）需要呼叫 AI 處理每篇論文。預設用 Claude Code，但可以透過 `--backend` 參數一鍵切換，**不需要改任何設定檔**：

```bash
# Claude Code（預設）
./scripts/run.sh reader -c "VLA" --backend claude

# OpenAI Codex CLI
./scripts/run.sh reader -c "VLA" --backend codex

# OpenAI API（需要 OPENAI_API_KEY 環境變數）
./scripts/run.sh reader -c "VLA" --backend openai

# 任意 CLI 工具（連預設都不用）
./scripts/run.sh reader -c "VLA" \
    --cli-command aider --cli-args "--model,gpt-4o" --cli-input-mode stdin
```

| `--backend` | 對應工具 | 實際呼叫 |
|---|---|---|
| `claude` | Claude Code CLI | `claude -p "prompt" --model opus ...` |
| `codex` | Codex CLI | `codex exec --sandbox workspace-write "prompt"` |
| `openai` | OpenAI 相容 API | HTTP POST `/chat/completions` |

更細的覆蓋參數（`--cli-command`、`--cli-args`、`--api-model`、`--api-key-env`、`--api-base-url` 等）見 `./scripts/run.sh reader --help`。

## 設定

所有設定在 [`_shared/user-config.json`](_shared/user-config.json)，主要分五段：

| 設定段 | 內容 |
|---|---|
| `paths` | Obsidian vault、論文筆記目錄、Zotero 資料庫路徑 |
| `daily_papers` | arXiv 每日論文的關鍵字過濾規則 |
| `automation` | 是否自動重新整理索引、是否 git commit/push |
| `ai_backend` | AI 後端類型及參數（`claude_code` / `generic_cli` / `openai_api`） |
| `daemon` | 批處理狀態目錄（進度、日誌、鎖檔） |

個人客製化不要直接改 `user-config.json`，而是新建 `_shared/user-config.local.json` 做覆蓋（已加入 `.gitignore`）：

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

命令列參數優先級高於設定檔：`--backend` 等參數 > `user-config.local.json` > `user-config.json` > 內建預設值。

## 專案結構

```text
papersearch/
├── SKILL.md                 # 頂層路由：把請求分發給對應子技能
├── scripts/run.sh           # 統一入口
├── search/                  # 批量檢索（本地 journal/** 資料集 + arXiv 回退）
│   ├── SKILL.md
│   ├── paper_search.py
│   └── journal/             # 11 個頂級會議的論文資料集
├── lookup/                  # 單篇速覽（alphaXiv 優先，arXiv 兜底）
│   ├── SKILL.md
│   └── scripts/alphaxiv_lookup.py
├── reader/                  # 深度閱讀 + 歸檔工作流
│   ├── SKILL.md
│   ├── paper_daemon.py      # 批處理守護進程（斷點續傳、限速重試）
│   ├── lib/ai_backend.py    # AI 後端抽象層
│   └── assets/              # 筆記範本、Zotero 輔助腳本
├── _shared/
│   ├── user_config.py       # 設定載入
│   └── user-config.json     # 預設設定
└── examples/                # 搜尋輸出範例
```

## 常見問題

**我需要手動選 search / lookup / reader 嗎？**
不需要。在 agent 裡直接說目標，路由層會自動分發；命令列場景按上面的入口呼叫即可。

**search 的本地資料覆蓋哪些會議？**
AAAI / ACL / AI4X / EMNLP / ICCV / ICLR / ICML / IJCAI / KDD / NeurIPS / WWW，見 `search/journal/`。CORL 會被識別為會議篩選條件，但無本地資料，會自動回退 arXiv API。本地覆蓋弱時也會自動回退並明確告知。

**歸檔工作流需要什麼前置條件？**
需要本機安裝 Zotero 和 Obsidian，並在 `_shared/user-config.local.json` 中設定好 vault 和 Zotero 資料庫路徑。search / lookup 不需要任何前置條件。

**批處理中斷了怎麼辦？**
進度儲存在狀態目錄（預設 `~/.papersearch/`），重新執行相同指令會自動斷點續傳；用 `--no-resume` 可強制從頭開始。

## 環境需求

- Python 3.9+（純標準函式庫，無第三方依賴）
- macOS / Linux
- （可選）Zotero + Obsidian，僅歸檔工作流需要

## 測試

```bash
python3 -m unittest search/tests/test_paper_search.py
```
