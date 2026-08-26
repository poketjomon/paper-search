<div align="center">

# papersearch

### 找論文、速覽論文、精讀論文、把論文變成你的知識庫筆記——四件事，一個套件搞定。

面向 AI Agent 的論文研究技能套件：**本地優先檢索 11 個頂級會議**論文資料集、**30 秒速覽**判斷一篇論文值不值得讀、**結構化深讀**，還能把論文**一鍵歸檔**成帶公式、圖表、概念連結的 Obsidian 筆記。

支援 Claude Code、Codex、Qoder 等任何能讀取 `SKILL.md` 並執行 shell 指令的 agent 框架，也可以不裝任何 agent、純命令列直接使用。

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen?style=flat-square)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey?style=flat-square)

🌐 [简体中文](./README.zh-CN.md) · [English](./README.md) · **繁體中文**　|　[🎬 怎麼用](#-怎麼用) · [📊 它長什麼樣](#-它長什麼樣) · [📚 知識庫歸檔](#-打造你的論文知識庫zotero--obsidian) · [❓ FAQ](#-faq)

</div>

---

## ✨ 它能給你什麼

- **找一批論文** — 依主題 / 會議 / 年份 / 有無程式碼檢索，輸出排序列表 + 每篇的匹配理由；本地覆蓋弱時**如實回報**並回退 arXiv，不拿不相關結果敷衍你（[完整範例](./examples/agent_rl_papers.md)）
- **30 秒判斷值不值得讀** — 給一個 arXiv / alphaXiv 連結，輸出結論 + 資訊來源可信度，缺什麼明說，絕不編造
- **結構化深讀** — 問題、方法、實驗、局限一次講清；預設只分析，**不動你的任何檔案**
- **歸檔進知識庫** — 產生帶公式、圖表、`[[概念]]` 連結的 Obsidian 筆記，自動維護概念庫、整理 Zotero 分類（只在你明確要求時啟用）
- **完全零依賴** — 純 Python 標準函式庫，clone 下來就能跑，不需要 pip install 任何東西
- **多 agent 框架** — 批處理支援 Claude Code / Codex / OpenAI API，`--backend` 一個參數切換，不用改設定檔
- **斷點續傳** — 批量處理中斷後重跑同一指令即可繼續，自動跳過已完成的論文

## 🎯 誰會想用

| 你是 | 你能用它做什麼 |
| --- | --- |
| **寫 related work 的研究生** | 一句話檢索某方向近幾年的頂會論文，帶匹配理由和程式碼連結，不用逐個會議官網翻 |
| **追新論文的研究者** | 刷到 arXiv 連結先丟進去速覽 30 秒，值不值得讀一目了然，再決定要不要精讀 |
| **知識庫建設者** | 把 Zotero 整個分類批量變成帶公式圖表的 Obsidian 筆記，自動建概念庫和互鏈 |
| **Zotero 重度使用者** | BibTeX 匯出、全文搜尋、安全移動分類（走 Zotero 本地 API） |
| **工具開發者** | 核心功能全是命令列腳本，不裝 agent 也能用，可直接接進自己的 pipeline |

## 🎬 怎麼用

把本倉庫作為 skill 裝進你的 agent 框架（Claude Code / Codex / Qoder 等，按各自框架的方式載入即可），或者不裝任何 agent 直接跑命令列：`./scripts/run.sh <search|lookup|reader> [args...]`。

然後在 agent 對話裡說出以下任一句即可觸發：

- 「幫我找 2024 ICLR 上 diffusion policy 的論文，最好有程式碼和專案連結」
- 「給我整理一份 2023-2025 年 VLA 方向的 related work 列表」
- 「快速看一下這篇論文值不值得讀：https://arxiv.org/abs/2303.04137」
- 「深度分析這篇論文的方法、實驗設計和局限」
- 「讀這篇論文並歸檔到我的 Obsidian 筆記庫」
- 「把 Zotero 裡 VLA 分類的論文匯出成 references.bib」
- "Find 2024 ICLR papers about diffusion policy, preferably with code"
- "Is this paper worth reading: https://arxiv.org/abs/2303.04137"

你不需要記住 search / lookup / reader 三個子技能——路由層會自動選最輕的方式完成（能速覽就不深讀，能本地查就不走網路）。

### 你說 → 你得到（真實輸出）

**例 1：找一批論文**

> 你說：「找 ICLR 上 world model 的論文」

你得到：

```text
Found 5 papers for: world model

Filters: venue=ICLR

Local status: strong

| Year | Venue | Title                                        | Link   | Why                                        |
| ---- | ----- | -------------------------------------------- | ------ | ------------------------------------------ |
| 2025 | ICLR  | Dream to Manipulate: Compositional World ... | [link] | venue match, title match, keyword match ... |
| 2025 | ICLR  | Hierarchical World Models as Visual Whole... | [link] | venue match, title match, keyword match ... |
| 2025 | ICLR  | FLIP: Flow-Centric Generative Planning as... | [link] | venue match, title match, keyword match ... |
```

**例 2：30 秒速覽**

> 你說：「這篇值不值得讀：https://arxiv.org/abs/2303.04137」

你得到：

```text
論文：Diffusion Policy: Visuomotor Policy Learning via Action Diffusion（2303.04137）
一句話結論：This paper introduces Diffusion Policy, a new way of generating robot
           behavior by representing a robot's visuomotor policy as a conditional
           denoising diffusion process.
核心方法：
- To fully unlock the potential of diffusion models for visuomotor policy
  learning on physical robots, this paper presents a set of key technical
  contributions ...
值不值得讀：先看摘要即可；這版主要依賴 arXiv fallback。
來源：arXiv 摘要 fallback。可信度：基礎（alphaXiv: http_error）。
```

**例 3：匯出參考文獻（走 Zotero 本地 API）**

> 你說：「把我 Zotero 庫裡的論文匯出成 references.bib」

你得到：

```text
{
  "output": "/path/to/references.bib",
  "bytes": 873883,
  "bibtex_entries": 254
}
```

```bibtex
@misc{wuSurveyLargeLanguage2024,
    title = {A survey on large language models for recommendation},
    url = {http://arxiv.org/abs/2305.19860},
    author = {Wu, Likang and Zheng, Zhi and ...},
    year = {2024},
    note = {arXiv:2305.19860 [cs]}
}
```

更多歸檔場景（論文變筆記、批量處理）見 [📚 打造你的論文知識庫](#-打造你的論文知識庫zotero--obsidian)。

<details>
<summary><b>子技能詳細用法（篩選語法 / 輸出格式 / 命令列參數）</b></summary>

### search：批量檢索

自然語言裡直接寫篩選條件，不需要學特殊語法：

| 篩選 | 寫法範例 |
|---|---|
| 會議 | `ICLR`、`ICML`、`NeurIPS`、`AAAI`、`ACL`、`EMNLP`、`ICCV`、`IJCAI`、`KDD`、`WWW`、`CORL` |
| 年份 | `2024` 或範圍 `2023-2025` |
| 資源 | `with code`、`with pdf` |

本地資料覆蓋 11 個頂級會議（見 `search/journal/`）；CORL 無本地資料時自動走 arXiv 回退並明確標註 `Fallback: arXiv`。結果同時儲存為 `search/outputs/latest_search_results.md`。

### lookup：單篇速覽

支援的輸入：`2303.04137`、`1706.03762v7`、arXiv 連結、alphaXiv 連結。

```bash
./scripts/run.sh lookup "2303.04137" --format brief-zh   # 中文簡報
./scripts/run.sh lookup "2303.04137" --format brief      # 英文簡報
./scripts/run.sh lookup --input-file papers.txt --format brief   # 批量（每行一個 ID）
```

格式選項：`brief` / `brief-zh` / `markdown` / `text` / `json` / `json-compact`。

### reader：深讀與批處理

```bash
./scripts/run.sh reader -c "VLA"        # 批量處理 Zotero 分類（遞迴子分類）
./scripts/run.sh reader --status        # 查看進度
./scripts/run.sh reader --list          # 列出 Zotero 分類
```

預設只做結構化分析；只有明確提到**儲存 / 歸檔 / Obsidian / Zotero / 批處理**時才進入歸檔工作流。

</details>

## 📊 它長什麼樣

### 1. search —— 找一批論文

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

怎麼讀：**Filters** 是系統從你話裡解析出的條件（確認它理解對了）；**Local status** 弱時說明結果來自 arXiv 回退；**Why** 是每篇的命中理由，方便判斷相關性。

### 2. lookup —— 30 秒速覽

```bash
./scripts/run.sh lookup "2303.04137" --format brief-zh
```

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

最後兩行告訴你資訊從哪來、可信度多少——alphaXiv 詳細報告 > arXiv 摘要，系統不會為了好看而編造。

## 📚 打造你的論文知識庫（Zotero × Obsidian）

這是套件最重的能力：把論文變成互相連結的 Obsidian 知識庫，同時整理你的 Zotero 文獻庫。**只在你明確要求歸檔時啟用**，普通深讀永遠不碰你的檔案。

### 一次性設定

新建 `_shared/user-config.local.json`（不進 git），告訴套件你的 vault 和 Zotero 在哪：

```json
{
  "paths": {
    "obsidian_vault": "~/Documents/MyObsidianVault",
    "zotero_db": "~/Zotero/zotero.sqlite",
    "zotero_storage": "~/Zotero/storage"
  }
}
```

（可選但推薦）在 Zotero 裡開啟本地 API：設定 > 進階 > 勾選「允許本機其他應用與 Zotero 通信」。開啟後移動分類會走 API（比直寫資料庫更安全），並解鎖 BibTeX 匯出、全文搜尋。

### 歸檔單篇論文

在 agent 裡明確說出歸檔意圖：

- 「讀這篇論文並產生 Obsidian 筆記，包含關鍵圖表和公式說明」
- 「把這篇論文歸檔到 Zotero 的 VLA 分類」

工作流會依序：取得內容（本地 PDF 優先，否則 arXiv HTML → PDF → DOI）→ 產生歸檔級筆記 → 存入對應分類目錄 → 為新概念建立概念筆記 → 必要時把論文移到合理的 Zotero 分類（基於對論文的理解判斷，不是關鍵詞匹配；拿不準的筆記放 `_待整理/`）。

產生的筆記依 [`reader/assets/paper-note-template.md`](reader/assets/paper-note-template.md) 範本，包含：

- **YAML frontmatter**：標題、方法名、作者、年份、會議、標籤、Zotero 分類
- **元資訊表格**：機構、日期、專案主頁、對比基線、連結
- **一句話總結** + **核心貢獻**
- **方法詳解**：模組拆解，技術術語全部內嵌 `[[概念]]` 連結
- **關鍵公式**：每個公式都有「含義 + 符號說明」
- **關鍵圖表**：`### Figure X: 英文標題 / 中文標題` + 圖片來源 + 說明
- **批判性思考**：優點、局限、改進方向、可重現性 checklist
- **關聯筆記** + **速查卡片**（Obsidian callout）

### 批量處理：把 Zotero 整個分類變成筆記

```bash
./scripts/run.sh reader --list       # 看 Zotero 裡有哪些分類
./scripts/run.sh reader -c "VLA"     # 批量處理（遞迴包含子分類）
./scripts/run.sh reader --status     # 另開終端看進度
```

`--list` 真實輸出：

```text
=== Zotero 分類 ===
  GUI: 6 篇
  LLM: 3 篇
  PRML: 2 篇
  Value論文: 9 篇
  agent: 1 篇
```

智慧行為：已有筆記的論文自動跳過；沒有本地 PDF 的自動改用線上來源；中斷後重跑同一指令自動續傳；遇到 rate limit 自動退避等待，全程無需人工干預。

### 最終你的知識庫裡會多出什麼

- `{vault}/論文筆記/` —— 每篇論文一份歸檔級筆記，帶公式、圖表、概念連結
- `{vault}/論文筆記/_概念/` —— 概念庫，隨筆記自動建設並與筆記互鏈
- MOC 索引頁 —— 目錄級的導覽頁，可自動產生（`_shared/generate_*_mocs.py`）
- 整理過的 Zotero 分類 —— 論文從臨時分類移到合理位置

## 🔧 多 agent 框架切換

批處理需要呼叫 AI 逐篇處理論文。預設 Claude Code，`--backend` 一鍵切換，**不用改設定檔**：

```bash
./scripts/run.sh reader -c "VLA" --backend claude    # 預設
./scripts/run.sh reader -c "VLA" --backend codex     # Codex CLI
./scripts/run.sh reader -c "VLA" --backend openai    # OpenAI API（需 OPENAI_API_KEY）
```

| `--backend` | 實際呼叫 |
|---|---|
| `claude` | `claude -p "prompt" --model opus --permission-mode acceptEdits ...` |
| `codex` | `codex exec --sandbox workspace-write "prompt"` |
| `openai` | HTTP POST `{base_url}/chat/completions` |

還能細粒度覆蓋（`--cli-command` / `--cli-args` / `--api-model` / `--api-key-env` / `--api-base-url`），甚至直接接入任意 CLI 工具：

```bash
./scripts/run.sh reader -c "VLA" --cli-command aider --cli-args "--model,gpt-4o" --cli-input-mode stdin
```

完整參數：`./scripts/run.sh reader --help`。優先級：命令列參數 > `user-config.local.json` > `user-config.json` > 內建預設值。

## 🗂️ 配套技能（隨倉庫附帶，無需單獨安裝）

| 技能 | 幹什麼 | 什麼時候被用到 |
|---|---|---|
| `obsidian_skills/obsidian-markdown` | Obsidian 語法規範（wikilinks / callouts / embeds / frontmatter） | 每次歸檔寫筆記時自動遵循 |
| `obsidian_skills/obsidian-cli` | 透過 CLI 搜尋 / 操作 vault | 概念查重、vault 搜尋（需本機裝 Obsidian CLI） |
| `obsidian_skills/obsidian-bases` | `.base` 資料庫視圖 | 你想要論文庫的可篩選視圖時 |
| `zotero_skills/zotero` | Zotero 本地 API：安全移動分類、BibTeX 匯出、全文搜尋 | Zotero 桌面版執行且開啟本地 API 時 |

分工原則：Zotero 關閉時的批量唯讀查詢走內建 SQLite 方案（`reader/assets/zotero_helper.py`）；寫操作和 API 獨有能力（BibTeX / 全文搜尋）走本地 API。

## ⚙️ 設定

所有設定在 [`_shared/user-config.json`](_shared/user-config.json)。個人客製化請新建 `_shared/user-config.local.json`（已 gitignore）做深度合併覆蓋，只寫要改的欄位：

```json
{
  "paths": {
    "obsidian_vault": "~/Documents/MyVault",
    "zotero_db": "~/Zotero/zotero.sqlite"
  },
  "ai_backend": { "type": "openai_api" }
}
```

| 設定段 | 內容 | 什麼時候要改 |
|---|---|---|
| `paths` | Obsidian vault、筆記目錄、Zotero 路徑 | 用歸檔工作流前必改 |
| `daily_papers` | arXiv 每日論文關鍵詞過濾 | 客製化每日推送時 |
| `automation` | 索引重新整理、git commit/push 開關 | 想自動提交筆記時 |
| `ai_backend` | AI 後端類型及參數 | 改預設後端時（也可用 `--backend` 臨時切換） |
| `daemon` | 批處理狀態目錄（預設 `~/.papersearch/`） | 一般不用改 |

安全約定：API key 一律走環境變數（設定裡只寫變數名），永遠不進 JSON。

## 🆚 跟其他工具啥不同

| 工具 | 定位 | 差異 |
| --- | --- | --- |
| Zotero 本體 | 文獻管理 | 不做 AI 速覽/深讀，不產生知識庫筆記 |
| arXiv 每日論文工具 | 新論文推薦 | 不能檢索既有會議論文，無深讀和歸檔 |
| 通用 AI 對話讀 PDF | 臨時讀一篇 | 無本地語料、無匹配理由、無知識庫工作流 |
| **papersearch** | **檢索 → 速覽 → 深讀 → 歸檔一站式** | **本地語料 + 誠實回退 + 知識庫自動化 + 多框架** |

簡單說：**別的工具做其中一個環節，papersearch 把論文研究的全鏈路串起來，而且每一步都能脫離 agent 獨立跑。**

## ❓ FAQ

<details>
<summary><b>我需要手動選 search / lookup / reader 嗎？</b></summary>

不需要。在 agent 裡直接說目標，路由層自動分發，遵循「能輕不重」原則（能速覽就不深讀）。命令列場景按[上面的入口](#-怎麼用)呼叫即可。

</details>

<details>
<summary><b>本地資料覆蓋哪些會議？能擴充嗎？</b></summary>

AAAI / ACL / AI4X / EMNLP / ICCV / ICLR / ICML / IJCAI / KDD / NeurIPS / WWW，見 `search/journal/`。資料就是 JSON 檔案，往對應目錄放同格式 JSON 即可擴充。本地覆蓋弱時自動回退 arXiv 並明確告知。

</details>

<details>
<summary><b>lookup 需要註冊 alphaXiv 帳號嗎？</b></summary>

不需要，直接抓公開頁面。alphaXiv 不可用或被限流時自動回退 arXiv 摘要，輸出裡會標註實際來源和可信度。

</details>

<details>
<summary><b>歸檔工作流會動我的 Zotero 資料庫嗎？</b></summary>

唯讀查詢會先複製資料庫再操作，不會鎖庫。移動分類只在顯式歸檔流程（批處理 workflow 模式）中發生；Zotero 開著且本地 API 啟用時優先走 API（更安全），否則回退 SQLite；`--mode analysis` 不寫任何東西。

</details>

<details>
<summary><b>批處理中斷了怎麼辦？會不會觸發 AI 用量限制？</b></summary>

進度存在 `~/.papersearch/`，重跑同一指令自動續傳；`--no-resume` 從頭開始；`--status` 看進度和失敗原因。限速策略內建：rate limit 指數退避（60 秒起步、最長 6 小時），配額上限自動解析重置時間並等待，論文間預設間隔 5 秒，全程無需人工干預。

</details>

<details>
<summary><b>配套的 Obsidian / Zotero 技能需要單獨安裝嗎？</b></summary>

不需要，隨倉庫附帶。obsidian-markdown 在每次歸檔寫筆記時自動生效；obsidian-cli 僅在本機裝了 Obsidian CLI 時使用；zotero 技能僅在 Zotero 桌面版執行且開啟本地 API 時使用（否則回退內建 SQLite 方案）。

</details>

<details>
<summary><b>支援 Windows 嗎？</b></summary>

腳本基於 POSIX shell，推薦 macOS / Linux；Windows 請用 WSL。

</details>

## 📁 專案結構

```text
papersearch/
├── SKILL.md                 # 頂層路由：把請求分發給對應子技能
├── scripts/run.sh           # 統一入口
├── search/                  # 批量檢索（本地 journal/** + arXiv 回退）
├── lookup/                  # 單篇速覽（alphaXiv 優先，arXiv 兜底）
├── reader/                  # 深讀 + 歸檔工作流（含批處理守護進程、AI backend 抽象層）
├── _shared/                 # 設定載入、MOC 索引產生
├── obsidian_skills/         # 配套 Obsidian 技能（markdown / cli / bases）
├── zotero_skills/           # 配套 Zotero 技能（本地 API）
└── examples/                # 搜尋輸出範例
```

## 🌱 環境需求與測試

- Python 3.9+（純標準函式庫，無第三方依賴）
- macOS / Linux
- （可選）Zotero + Obsidian，僅歸檔工作流需要；Zotero 開啟本地 API 可解鎖 BibTeX 匯出等能力

```bash
python3 -m unittest search/tests/test_paper_search.py
```

---

<div align="center">

**用過覺得有用？給個 ⭐ 是對作者最大的鼓勵。**

[⬆ 回到頂部](#papersearch) · [🎬 怎麼用](#-怎麼用)

</div>
