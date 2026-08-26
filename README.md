# papersearch

🌐 **English** | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md)

> A paper-research skill suite for AI agents.
> Works with Claude Code, Codex, Qoder — any agent framework that can read a `SKILL.md` and run shell commands — or standalone from the command line with no agent at all.

## What it does

| Subskill | Purpose | Example request |
|---|---|---|
| **search** | Find papers in bulk by topic / venue / year | “Find 2024 ICLR papers about diffusion policy, preferably with code” |
| **lookup** | 30-second brief of one paper — is it worth reading? | “Quickly summarize arXiv 2303.04137” |
| **reader** | Deep analysis of one paper | “Deeply analyze this paper's method and experiments” |
| **archival workflow** | Obsidian notes + Zotero organization (explicit opt-in) | “Read this paper and archive it to my Obsidian vault” |

Highlights:

- **Local-first search**: bundled datasets for 11 top venues (AAAI / ACL / AI4X / EMNLP / ICCV / ICLR / ICML / IJCAI / KDD / NeurIPS / WWW); CORL is also recognized as a venue filter and falls back to arXiv since it has no bundled data; weak local coverage is reported honestly
- **Zero dependencies**: pure Python standard library, nothing to pip install
- **Multi-framework**: the batch daemon supports Claude Code / Codex / OpenAI API backends, switchable via one CLI flag

## Installation

### Option 1: Install into your agent framework (recommended)

Point your agent's skills directory at this repo; the agent reads `SKILL.md` and handles routing automatically:

```bash
# Claude Code
ln -s "$PWD" ~/.claude/skills/papersearch

# Codex
ln -s "$PWD" ~/.codex/skills/papersearch
```

For other frameworks (Qoder, Cursor, …), follow their skill/plugin installation docs. The only requirement: the agent can read `SKILL.md` and execute `./scripts/run.sh`.

Once installed, just ask in natural language:

```text
Find 2024 ICLR papers about diffusion policy, preferably with code and project links
Is this paper worth reading: https://arxiv.org/abs/2303.04137
Deeply analyze this paper's method, experiment design, and limitations
```

### Option 2: Standalone CLI (zero install)

Everything also works without any agent:

```bash
./scripts/run.sh <search|lookup|reader> [args...]
```

## Feature demos (real output)

### 1) search: find a list of papers

```bash
./scripts/run.sh search "find iclr papers about world model"
```

Output (truncated):

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

Filters you can write directly in natural language:

- Venue: `ICLR`, `ICML`, `NeurIPS`, `AAAI`, `ACL`, `EMNLP`, `ICCV`, `IJCAI`, `KDD`, `WWW`, `CORL` (CORL has no bundled data and automatically uses the arXiv fallback)
- Year: `2024` or a range like `2023-2025`
- Resources: `with code`, `with pdf`

When local matches are weak it reports `Local status: weak` and falls back to the arXiv API instead of pretending generic matches are good enough.

Full example: a two-year survey of Agent RL papers → [examples/agent_rl_papers_en.md](./examples/agent_rl_papers_en.md)

### 2) lookup: one-paper brief

Hand it an arXiv id or URL and get a go / no-go verdict in 30 seconds:

```bash
./scripts/run.sh lookup "2303.04137" --format brief
```

Output (truncated):

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

Formats: `--format brief` | `brief-zh` (Chinese) | `markdown` | `text` | `json`

Accepted inputs: `2401.12345`, `https://arxiv.org/abs/2401.12345`, `https://www.alphaxiv.org/overview/2401.12345`

### 3) reader: deep reading

```bash
./scripts/run.sh reader -c "VLA"                # batch-process a Zotero collection
./scripts/run.sh reader --status                # check batch progress
./scripts/run.sh reader --list                  # list all Zotero collections
```

Inside an agent, just say: “read this paper deeply” or “read this paper and generate an Obsidian note”.

By default it only produces a structured analysis (problem, method, experiments, limitations). The archival workflow (writing notes, maintaining the concept library, moving Zotero collections) activates only when you explicitly mention **save / archive / Obsidian / Zotero / batch**.

## Multi-agent-framework support

Batch processing (`paper_daemon.py`) needs an AI backend to process each paper. Claude Code is the default, but you can switch with one `--backend` flag — **no config file edits needed**:

```bash
# Claude Code (default)
./scripts/run.sh reader -c "VLA" --backend claude

# OpenAI Codex CLI
./scripts/run.sh reader -c "VLA" --backend codex

# OpenAI API (requires the OPENAI_API_KEY environment variable)
./scripts/run.sh reader -c "VLA" --backend openai

# Any CLI tool (no preset needed)
./scripts/run.sh reader -c "VLA" \
    --cli-command aider --cli-args "--model,gpt-4o" --cli-input-mode stdin
```

| `--backend` | Tool | Actual invocation |
|---|---|---|
| `claude` | Claude Code CLI | `claude -p "prompt" --model opus ...` |
| `codex` | Codex CLI | `codex exec --sandbox workspace-write "prompt"` |
| `openai` | OpenAI-compatible API | HTTP POST `/chat/completions` |

Override flags (`--cli-command`, `--cli-args`, `--api-model`, `--api-key-env`, `--api-base-url`, …) are documented in `./scripts/run.sh reader --help`.

## Configuration

All settings live in [`_shared/user-config.json`](_shared/user-config.json):

| Section | Contents |
|---|---|
| `paths` | Obsidian vault, paper-notes folder, Zotero DB paths |
| `daily_papers` | Keyword filters for daily arXiv ingestion |
| `automation` | Auto-refresh indexes, git commit/push switches |
| `ai_backend` | AI backend type and parameters (`claude_code` / `generic_cli` / `openai_api`) |
| `daemon` | Batch state directory (progress, logs, lock file) |

For personal overrides, create `_shared/user-config.local.json` (gitignored) instead of editing the tracked file:

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

Precedence: CLI flags > `user-config.local.json` > `user-config.json` > built-in defaults.

## Project structure

```text
papersearch/
├── SKILL.md                 # Top-level router: dispatches requests to subskills
├── scripts/run.sh           # Unified entrypoint
├── search/                  # Bulk search (local journal/** corpus + arXiv fallback)
│   ├── SKILL.md
│   ├── paper_search.py
│   └── journal/             # Paper datasets for 11 top venues
├── lookup/                  # One-paper brief (alphaXiv first, arXiv fallback)
│   ├── SKILL.md
│   └── scripts/alphaxiv_lookup.py
├── reader/                  # Deep reading + archival workflow
│   ├── SKILL.md
│   ├── paper_daemon.py      # Batch daemon (resume, rate-limit backoff)
│   ├── lib/ai_backend.py    # AI backend abstraction layer
│   └── assets/              # Note template, Zotero helper scripts
├── _shared/
│   ├── user_config.py       # Config loading
│   └── user-config.json     # Default configuration
└── examples/                # Sample search outputs
```

## FAQ

**Do I have to pick search / lookup / reader manually?**
No. In an agent, just state your goal and the router dispatches automatically; from the CLI, use the entrypoints above.

**Which venues does the local search corpus cover?**
AAAI / ACL / AI4X / EMNLP / ICCV / ICLR / ICML / IJCAI / KDD / NeurIPS / WWW — see `search/journal/`. CORL is recognized as a venue filter but has no bundled data, so it falls back to the arXiv API. Weak local coverage also triggers the fallback and is reported explicitly.

**What do I need for the archival workflow?**
Local Zotero and Obsidian installs, plus vault/Zotero paths configured in `_shared/user-config.local.json`. search and lookup need no prerequisites.

**What if a batch run gets interrupted?**
Progress is saved in the state directory (default `~/.papersearch/`); rerunning the same command resumes automatically. Use `--no-resume` to start over.

## Requirements

- Python 3.9+ (standard library only, no third-party dependencies)
- macOS / Linux
- (Optional) Zotero + Obsidian, only for the archival workflow

## Tests

```bash
python3 -m unittest search/tests/test_paper_search.py
```
