<div align="center">

# papersearch

### Find papers, triage papers, deep-read papers, turn papers into your knowledge base — one suite for all four.

A paper-research skill suite for AI agents: **local-first search across 11 top venues**, a **30-second brief** to judge whether a paper is worth reading, **structured deep reading**, and **one-click archival** into Obsidian notes with formulas, figures, and concept links.

Works with Claude Code, Codex, Qoder — any agent framework that can read a `SKILL.md` and run shell commands — or standalone from the command line with no agent at all.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen?style=flat-square)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey?style=flat-square)
![Tests](https://img.shields.io/badge/tests-14%20passing-brightgreen?style=flat-square)
![Corpus](https://img.shields.io/badge/local_corpus-11%20top%20venues-orange?style=flat-square)
![AI backends](https://img.shields.io/badge/AI_backends-claude%20%7C%20codex%20%7C%20openai-blueviolet?style=flat-square)
![Zotero](https://img.shields.io/badge/Zotero-local%20API-CC2936?style=flat-square)
![Obsidian](https://img.shields.io/badge/Obsidian-vault%20ready-7C3AED?style=flat-square)

🌐 [简体中文](./README.zh-CN.md) · **English** · [繁體中文](./README.zh-TW.md)　|　[📥 Install](#-install) · [🎬 How to use](#-how-to-use) · [📊 What it looks like](#-what-it-looks-like) · [📚 Knowledge-base archival](#-build-your-paper-knowledge-base-zotero--obsidian) · [❓ FAQ](#-faq)

</div>

---

## ✨ What you get

- **Find papers in bulk** — search by topic / venue / year / has-code, with ranked results and per-paper match reasons; weak local coverage is **reported honestly** with an arXiv fallback — no filler results ([full example](./examples/agent_rl_papers_en.md))
- **30-second go / no-go verdict** — hand it an arXiv / alphaXiv link; sources and confidence levels are stated, gaps never invented
- **Download paper PDFs** — one sentence downloads one or a batch of arXiv papers locally (batch support, automatic rate-limiting)
- **Structured deep reading** — problem, method, experiments, limitations in one pass; default mode **never touches your files**
- **Archive into your knowledge base** — Obsidian notes with formulas, figures, and `[[concept]]` links, plus automatic concept-library maintenance and Zotero organization (only on explicit request)
- **Zero dependencies** — pure Python standard library; clone and run, nothing to pip install
- **Multi-agent-framework** — the batch daemon supports Claude Code / Codex / OpenAI API, switchable with one `--backend` flag, no config edits
- **Resumable batches** — rerun the same command after an interruption; finished papers are skipped automatically

## 🎯 Who it's for

| You are | What you can do with it |
| --- | --- |
| **A grad student writing related work** | One sentence retrieves years of top-venue papers in a direction, with match reasons and code links — no more crawling conference sites |
| **A researcher keeping up with new papers** | Drop an arXiv link in, get a worth-reading verdict in 30 seconds, then decide whether to deep-read |
| **A knowledge-base builder** | Batch-convert whole Zotero collections into Obsidian notes with formulas and figures, auto-building a linked concept library |
| **A Zotero power user** | BibTeX export, full-text search, safe collection moves (via Zotero's local API) |
| **A tool builder** | Every core feature is a CLI script — usable with no agent, embeddable in your own pipeline |

## 📥 Install

“Installing” a skill just means letting your agent framework discover its `SKILL.md` — one symlink does it:

```bash
# Claude Code
ln -s /path/to/papersearch ~/.claude/skills/papersearch

# Codex CLI
ln -s /path/to/papersearch ~/.codex/skills/papersearch
```

To scope it to one project, put it in that project's `.claude/skills/` instead. Other frameworks (Qoder / Cursor / custom agents): anything that can read the top-level `SKILL.md` and execute `./scripts/run.sh` works.

Verify by starting a new session and saying “Find ICLR papers about world model” — a paper list in the response means it's live.

## 🎬 How to use

Once installed, say any of these in your agent:

- “Find 2024 ICLR papers about diffusion policy, preferably with code and project links”
- “Create a related-work list for VLA from 2023-2025”
- “Is this paper worth reading: https://arxiv.org/abs/2303.04137”
- “Deeply analyze this paper's method, experiment design, and limitations”
- “Read this paper and archive it to my Obsidian vault”
- “Export the papers in my Zotero VLA collection to references.bib”
- “Download the PDF of arXiv 2303.04137 to my Downloads folder”
- 「帮我找 2024 ICLR 上 diffusion policy 的论文，要有代码」
- 「快速看一下这篇论文值不值得读：arXiv 2303.04137」

You don't need to remember the three subskills — the router picks the lightest way to answer (brief before deep read, local before remote).

### You say → you get (real output)

**Example 1: Find papers in bulk**

> You say: “Find ICLR papers about world model”

You get:

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

**Example 2: 30-second brief**

> You say: “Is this worth reading: https://arxiv.org/abs/2303.04137”

You get:

```text
Paper: Diffusion Policy: Visuomotor Policy Learning via Action Diffusion (2303.04137)
Takeaway: This paper introduces Diffusion Policy, a new way of generating robot
          behavior by representing a robot's visuomotor policy as a conditional
          denoising diffusion process.
Core method:
- To fully unlock the potential of diffusion models for visuomotor policy
  learning on physical robots, this paper presents a set of key technical
  contributions ...
Worth reading? Abstract-first; this brief relies on the arXiv fallback.
Source: arXiv abstract fallback. Confidence: basic (alphaXiv: http_error).
```

**Example 3: Export references (via Zotero local API)**

> You say: “Export my Zotero library to references.bib”

You get:

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

For archival scenarios (papers into notes, batch processing), see [📚 Build your paper knowledge base](#-build-your-paper-knowledge-base-zotero--obsidian).

<details>
<summary><b>Subskill details (filter syntax / output formats / CLI flags)</b></summary>

### search: bulk retrieval

Write filters straight into natural language — no special syntax:

| Filter | Examples |
|---|---|
| Venue | `ICLR`, `ICML`, `NeurIPS`, `AAAI`, `ACL`, `EMNLP`, `ICCV`, `IJCAI`, `KDD`, `WWW`, `CORL` |
| Year | `2024` or a range like `2023-2025` |
| Resources | `with code`, `with pdf` |

Local data covers 11 top venues (see `search/journal/`); CORL has no bundled data and falls back to arXiv, labeled `Fallback: arXiv`. Results are also saved to `search/outputs/latest_search_results.md`.

### lookup: one-paper brief + paper download

Accepted inputs: `2303.04137`, `1706.03762v7`, arXiv URLs, alphaXiv URLs.

```bash
./scripts/run.sh lookup "2303.04137" --format brief          # English brief
./scripts/run.sh lookup "2303.04137" --format brief-zh       # Chinese brief
./scripts/run.sh lookup --input-file papers.txt --format brief   # batch (one ID per line)

# Download paper PDFs (single or multiple, space- or comma-separated)
./scripts/run.sh lookup download "2303.04137" --out ~/Downloads/papers
./scripts/run.sh lookup download "2303.04137,2401.12345" --out ~/Downloads/papers
./scripts/run.sh lookup download --input-file papers.txt --out ~/Downloads/papers
```

Formats: `brief` / `brief-zh` / `markdown` / `text` / `json` / `json-compact`. Downloads keep a 3-second courtesy gap between papers; failures are reported with exact reasons (not found / rate-limited / not a PDF).

### reader: deep reading & batch

```bash
./scripts/run.sh reader -c "VLA"        # batch-process a Zotero collection (recursive)
./scripts/run.sh reader --status        # check progress
./scripts/run.sh reader --list          # list Zotero collections
```

Default mode only analyzes; the archival workflow activates only when you explicitly mention **save / archive / Obsidian / Zotero / batch**.

</details>

## 📊 What it looks like

### 1. search — find papers in bulk

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

How to read it: **Filters** shows what was parsed from your words (confirm it understood you); a weak **Local status** means results came from the arXiv fallback; **Why** lists each paper's match reasons so you can judge relevance.

### 2. lookup — 30-second brief

```bash
./scripts/run.sh lookup "2303.04137" --format brief
```

```text
Paper: Diffusion Policy: Visuomotor Policy Learning via Action Diffusion (2303.04137)
Takeaway: This paper introduces Diffusion Policy, a new way of generating robot
          behavior by representing a robot's visuomotor policy as a conditional
          denoising diffusion process.
Problem solved: We benchmark Diffusion Policy across 12 different tasks from 4
          different robot manipulation benchmarks ...
Core method:
- To fully unlock the potential of diffusion models for visuomotor policy
  learning on physical robots, this paper presents a set of key technical
  contributions ...
Worth reading? Abstract-first; this brief relies on the arXiv fallback.
Source: arXiv abstract fallback. Confidence: basic (alphaXiv: http_error).
```

The last two lines tell you where the information came from and how much to trust it — alphaXiv detailed reports > arXiv abstracts. The system never invents missing details.

## 📚 Build your paper knowledge base (Zotero × Obsidian)

The heaviest capability: turn papers into a cross-linked Obsidian knowledge base while organizing your Zotero library. **Only activates on explicit archival requests** — plain deep reading never touches your files.

### One-time setup

Create `_shared/user-config.local.json` (gitignored) to tell the suite where your vault and Zotero live:

```json
{
  "paths": {
    "obsidian_vault": "~/Documents/MyObsidianVault",
    "zotero_db": "~/Zotero/zotero.sqlite",
    "zotero_storage": "~/Zotero/storage"
  }
}
```

(Optional but recommended) Enable Zotero's local API: Settings > Advanced > check "Allow other applications on this computer to communicate with Zotero". Once enabled, collection moves go through the API (safer than writing the database directly), and BibTeX export plus full-text search are unlocked.

### Archive a single paper

State the archival intent explicitly in your agent:

- “Read this paper and generate an Obsidian note with key figures and formula explanations”
- “Archive this paper into the VLA collection in Zotero”

The workflow then: fetches content (local PDF first; otherwise arXiv HTML → PDF → DOI) → generates an archival-quality note → saves it under the matching collection folder → creates concept notes for new concepts → moves the paper to a sensible Zotero collection when needed (based on understanding the paper, not keyword matching; uncertain notes go to `_待整理/`).

Generated notes follow [`reader/assets/paper-note-template.md`](reader/assets/paper-note-template.md):

- **YAML frontmatter**: title, method name, authors, year, venue, tags, Zotero collection
- **Meta table**: affiliations, date, project page, baselines, links
- **One-line summary** + **core contributions**
- **Method breakdown**: per-module detail with inline `[[concept]]` links on every technical term
- **Key formulas**: each with a "meaning + symbol glossary" section
- **Key figures/tables**: `### Figure X: English title / 中文标题` + image source + explanation
- **Critical thinking**: strengths, limitations, improvement directions, reproducibility checklist
- **Related notes** + **quick-reference card** (Obsidian callout)

### Batch processing: a whole Zotero collection into notes

Say in your agent:

- “Batch-process the VLA collection in my Zotero into paper notes”
- “What collections do I have in Zotero?”
- “How is the batch processing going?”

The agent handles the rest: recursing into subcollections, skipping papers with existing notes, and resuming automatically after interruptions. Ask about your collections and it reports honestly, e.g.:

```text
=== Zotero 分类 ===
  GUI: 6 篇
  LLM: 3 篇
  PRML: 2 篇
  Value论文: 9 篇
  agent: 1 篇
```

<details>
<summary>CLI equivalents (when running without an agent)</summary>

```bash
./scripts/run.sh reader --list       # see your Zotero collections
./scripts/run.sh reader -c "VLA"     # batch-process (recursively includes subcollections)
./scripts/run.sh reader --status     # check progress from another terminal
```

</details>

Other smart behavior: papers without a local PDF fall back to online sources; rate limits trigger automatic backoff — no intervention needed.

### What ends up in your knowledge base

- `{vault}/论文笔记/` — one archival-quality note per paper, with formulas, figures, and concept links
- `{vault}/论文笔记/_概念/` — a concept library, auto-built and cross-linked with the notes
- MOC index pages — directory-level navigation pages, auto-generated (`_shared/generate_*_mocs.py`)
- Organized Zotero collections — papers moved from temporary folders to sensible homes

## 🔧 Switching AI backends

Batch processing needs an AI backend per paper. Claude Code is the default; one `--backend` flag switches it — **no config edits**:

```bash
./scripts/run.sh reader -c "VLA" --backend claude    # default
./scripts/run.sh reader -c "VLA" --backend codex     # Codex CLI
./scripts/run.sh reader -c "VLA" --backend openai    # OpenAI API (needs OPENAI_API_KEY)
```

| `--backend` | Actual invocation |
|---|---|
| `claude` | `claude -p "prompt" --model opus --permission-mode acceptEdits ...` |
| `codex` | `codex exec --sandbox workspace-write "prompt"` |
| `openai` | HTTP POST `{base_url}/chat/completions` |

Fine-grained overrides available (`--cli-command` / `--cli-args` / `--api-model` / `--api-key-env` / `--api-base-url`), and you can plug in any CLI tool directly:

```bash
./scripts/run.sh reader -c "VLA" --cli-command aider --cli-args "--model,gpt-4o" --cli-input-mode stdin
```

Full reference: `./scripts/run.sh reader --help`. Precedence: CLI flags > `user-config.local.json` > `user-config.json` > built-in defaults.

## 🗂️ Companion skills (ship with the repo, no separate install)

| Skill | Purpose | When it's used |
|---|---|---|
| `obsidian_skills/obsidian-markdown` | Obsidian syntax rules (wikilinks / callouts / embeds / frontmatter) | Automatically followed whenever vault notes are written |
| `obsidian_skills/obsidian-cli` | Vault search / operations via CLI | Concept deduplication, vault search (needs Obsidian CLI installed) |
| `obsidian_skills/obsidian-bases` | `.base` database views | When you want a filterable view over your paper library |
| `zotero_skills/zotero` | Zotero local API: safe collection moves, BibTeX export, full-text search | When Zotero Desktop runs with the local API enabled |

Division of labor: batch read-only queries with Zotero closed use the built-in SQLite approach (`reader/assets/zotero_helper.py`); write operations and API-only features (BibTeX / full-text search) use the local API.

## ⚙️ Configuration

All settings live in [`_shared/user-config.json`](_shared/user-config.json). For personal overrides, create `_shared/user-config.local.json` (gitignored) — it deep-merges, so write only what you change:

```json
{
  "paths": {
    "obsidian_vault": "~/Documents/MyVault",
    "zotero_db": "~/Zotero/zotero.sqlite"
  },
  "ai_backend": { "type": "openai_api" }
}
```

| Section | Contents | When to change |
|---|---|---|
| `paths` | Obsidian vault, notes folders, Zotero paths | Always, before the archival workflow |
| `daily_papers` | Keyword filters for daily arXiv ingestion | Customizing daily feeds |
| `automation` | Index refresh, git commit/push switches | Auto-committing note changes |
| `ai_backend` | AI backend type and parameters | Changing the default backend (or use `--backend` ad hoc) |
| `daemon` | Batch state directory (default `~/.papersearch/`) | Rarely |

Security: API keys always go through environment variables (config stores only the variable name), never into JSON.

## 🆚 How it differs from other tools

| Tool | Positioning | Difference |
| --- | --- | --- |
| Zotero itself | Reference management | No AI triage/deep reading, no knowledge-base notes |
| arXiv daily-paper tools | New-paper recommendations | Can't search existing venue corpora, no deep reading or archival |
| General AI chat + PDF | Ad-hoc paper reading | No local corpus, no match reasons, no knowledge-base workflow |
| **papersearch** | **Search → triage → deep read → archive, end to end** | **Local corpus + honest fallback + knowledge-base automation + multi-framework** |

In one line: **other tools cover one step; papersearch chains the entire paper-research pipeline — and every step also runs standalone without an agent.**

## ❓ FAQ

<details>
<summary><b>Do I have to pick search / lookup / reader manually?</b></summary>

No. State your goal and the router dispatches automatically, preferring the lightest option (brief before deep read). From the CLI, use the entrypoints above.

</details>

<details>
<summary><b>Which venues does the local corpus cover? Can I extend it?</b></summary>

AAAI / ACL / AI4X / EMNLP / ICCV / ICLR / ICML / IJCAI / KDD / NeurIPS / WWW — see `search/journal/`. Data lives as JSON files; drop additional same-format JSON into the right directory to extend. Weak local coverage always triggers the arXiv fallback and is reported explicitly.

</details>

<details>
<summary><b>Does lookup need an alphaXiv account?</b></summary>

No, it fetches public pages. When alphaXiv is unavailable or rate-limited it falls back to the arXiv abstract, stating the actual source and confidence.

</details>

<details>
<summary><b>Does the archival workflow modify my Zotero database?</b></summary>

Read-only queries copy the database first, so nothing gets locked. Collection moves only happen in the explicit archival flow (batch `workflow` mode); when Zotero is running with the local API enabled the API is preferred (safer), otherwise it falls back to SQLite; `--mode analysis` writes nothing.

</details>

<details>
<summary><b>What if a batch gets interrupted? Will it trip AI usage limits?</b></summary>

Progress lives in `~/.papersearch/`; rerunning the same command resumes automatically. `--no-resume` starts over; `--status` shows progress and failures. Rate-limit handling is built in: exponential backoff (60 s up to 6 h), quota-reset parsing that waits until the stated reset time, and a 5-second pause between papers — no intervention needed.

</details>

<details>
<summary><b>Do the companion Obsidian / Zotero skills need a separate install?</b></summary>

No, they ship with the repo. obsidian-markdown applies automatically whenever vault notes are written; obsidian-cli is only used if you have the Obsidian CLI installed; the zotero skill is only used when Zotero Desktop runs with the local API enabled (otherwise it falls back to the built-in SQLite approach).

</details>

<details>
<summary><b>Does it work on Windows?</b></summary>

Scripts are POSIX-shell based; macOS / Linux are recommended. On Windows, use WSL.

</details>

## 📁 Project structure

```text
papersearch/
├── SKILL.md                 # Top-level router: dispatches requests to subskills
├── scripts/run.sh           # Unified entrypoint
├── search/                  # Bulk search (local journal/** + arXiv fallback)
├── lookup/                  # One-paper brief (alphaXiv first, arXiv fallback)
├── reader/                  # Deep reading + archival workflow (batch daemon, AI backend abstraction)
├── _shared/                 # Config loading, MOC index generators
├── obsidian_skills/         # Companion Obsidian skills (markdown / cli / bases)
├── zotero_skills/           # Companion Zotero skill (local API)
└── examples/                # Sample search outputs
```

## 🌱 Requirements & tests

- Python 3.9+ (standard library only, no third-party dependencies)
- macOS / Linux
- (Optional) Zotero + Obsidian, only for the archival workflow; enabling Zotero's local API unlocks BibTeX export and more

```bash
python3 -m unittest search/tests/test_paper_search.py
```

---

<div align="center">

**Find it useful? A ⭐ is the best encouragement.**

[⬆ Back to top](#papersearch) · [🎬 How to use](#-how-to-use)

</div>
