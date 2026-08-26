---
name: paper-search-reader
description: |
  Read one specific paper or PDF more deeply than `lookup/`. By default, return default structured analysis for the paper. Preserve Zotero/Obsidian archival workflows as an explicit advanced path when the user asks for notes, saving, syncing, or batch processing.
context: fork
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch, WebSearch
---

# 学术论文阅读助手 (Paper Reader)

专注单篇论文的深读与分析。

默认行为：先做 **default structured analysis**，只有在用户明确要求保存、归档或批量处理时，才进入 **advanced workflow mode**。

Run:
`./scripts/run.sh <reader arguments>`

This subskill is integrated from the dailypaper skills `paper-reader` workflow, with local suite routing plus shared `_shared/**` config.

## AI Backend 选择（重要）

paper_daemon 支持通过 `--backend` 参数直接指定 AI 框架，**不需要改配置文件**。

### 预设 backend

| `--backend` | 对应工具 | 说明 |
|---|---|---|
| `claude` | Claude Code CLI | 默认，`claude -p "prompt" --model opus` |
| `codex` | OpenAI Codex CLI | `codex exec --sandbox workspace-write "prompt"` |
| `openai` | OpenAI API | 通过 `OPENAI_API_KEY` 环境变量调用 |

用法示例:

```bash
# Claude Code（默认，不指定也是这个）
./scripts/run.sh reader -c "VLA" --backend claude

# Codex CLI
./scripts/run.sh reader -c "VLA" --backend codex

# OpenAI API
./scripts/run.sh reader -c "VLA" --backend openai
```

### 自定义覆盖参数

在预设基础上可以用额外参数覆盖:

```bash
# Codex + 额外参数
./scripts/run.sh reader -c "VLA" --backend codex \
    --cli-args "exec,--sandbox,workspace-write,--skip-git-repo-check"

# OpenAI + 自定义模型和 key
./scripts/run.sh reader -c "VLA" --backend openai \
    --api-model gpt-4-turbo --api-key-env MY_OPENAI_KEY

# 任意 CLI 工具（不使用预设）
./scripts/run.sh reader -c "VLA" \
    --cli-command aider --cli-args "--model,gpt-4o" --cli-input-mode stdin
```

### 完整参数列表

| 参数 | 说明 |
|---|---|
| `--backend` | 预设名称：`claude` / `codex` / `openai` |
| `--cli-command` | 覆盖 CLI 命令 |
| `--cli-args` | CLI 参数，逗号分隔 |
| `--cli-input-mode` | `stdin` 或 `arg` |
| `--cli-prompt-arg` | prompt 参数名（空字符串=位置参数） |
| `--api-model` | API 模型名 |
| `--api-key-env` | API key 环境变量名 |
| `--api-base-url` | API base URL（OpenAI 兼容端点） |

不指定 `--backend` 时，从 `_shared/user-config.json` 的 `ai_backend.type` 读取。

## What this subskill is for

Use `reader/` when the paper is already known and the user wants more than a quick brief.

Typical requests:
- `read this paper`
- `analyze this pdf`
- `帮我读一下这篇论文`
- `详细拆一下这篇方法`

Use `lookup/` instead when the user only wants a fast go / no-go brief for one arXiv paper.
Use `search/` instead when the user is still collecting papers by topic, venue, year, benchmark, or dataset.

## Default mode

For ordinary one-paper reading requests, return a medium-weight structured analysis.

Supported inputs:
- local PDF path
- arXiv URL
- alphaXiv URL
- known paper title or identifier
- other direct one-paper sources already provided by the user

Default output shape:
1. **Decision summary**
   - what problem the paper tackles
   - the core idea in plain language
   - whether the evidence is strong enough to care about
   - whether it is worth deeper reading
2. **Research analysis**
   - problem setup
   - method breakdown
   - experimental evidence
   - limitations / caveats / what to inspect next

Default mode should **not** assume note saving, concept-note creation, Zotero moves, Obsidian writes, git actions, or zero-omission extraction.

## Advanced workflow mode

Enter **advanced workflow mode** only on explicit user intent.

Trigger boundary:
- save / archive / sync / batch / Zotero / Obsidian / note intent
- requests to generate vault-ready notes
- requests to process Zotero collections recursively
- requests to maintain concept notes or paper indexes

When advanced workflow mode is active, preserve the existing heavy workflow capabilities:
- Obsidian-ready note generation with `assets/paper-note-template.md`
- zero-omission figure / formula / table extraction
- concept-library maintenance
- Zotero-aware classification or collection workflows
- optional index refresh and git flows
- batch processing through the collection daemon

## Advanced workflow prerequisites

Read `../_shared/user-config.json` first. If `../_shared/user-config.local.json` exists, use it to override defaults.

Use these shared variables consistently:
- `VAULT_PATH`
- `NOTES_PATH`
- `CONCEPTS_PATH`
- `ZOTERO_DB`
- `ZOTERO_STORAGE`
- `AUTO_REFRESH_INDEXES`
- `GIT_COMMIT_ENABLED`
- `GIT_PUSH_ENABLED`

Where:
- `NOTES_PATH = {VAULT_PATH}/{paper_notes_folder}`
- `CONCEPTS_PATH = {NOTES_PATH}/{concepts_folder}`
- `GIT_PUSH_ENABLED` can only be true when `GIT_COMMIT_ENABLED=true`

## Input handling

| Input type | Example | Preferred handling |
|-----------|---------|--------------------|
| PDF path | `/path/to/paper.pdf` | Read directly |
| arXiv URL | `https://arxiv.org/abs/xxxx` | Prefer HTML/abstract fetch |
| alphaXiv URL | `https://www.alphaxiv.org/...` | Fetch and cross-check |
| known paper title | `Diffusion Policy` | Resolve source, then read |
| Zotero collection | `VLA 分类的论文` | advanced workflow mode |
| Zotero title search | `Zotero 里的 π0.5` | advanced workflow mode |

If there is no local PDF, prefer this fallback order:
1. arXiv HTML
2. arXiv PDF
3. DOI page
4. user-provided URL
5. title-based web search

Use `references/zotero-guide.md` only when the task actually involves Zotero workflows.

## Advanced note-generation rules

These rules apply only in advanced workflow mode.

### Obsidian syntax

All vault notes (paper notes and concept notes) must follow Obsidian Flavored Markdown as specified in `../obsidian_skills/obsidian-markdown/SKILL.md` — wikilinks, embeds, callouts, and frontmatter properties. Read that skill before writing any vault note; consult its `references/` for callout, embed, and property details when needed.

### Template

Use `assets/paper-note-template.md` for vault-ready note generation. Do not treat it as the default output contract for ordinary analysis.

### Completeness rules

When the user explicitly asks for archival-quality notes:
1. include all required figures, formulas, and tables
2. use inline `[[概念]]` links where appropriate
3. avoid ASCII diagrams when structured Markdown plus math is clearer
4. keep formulas complete with meaning and symbol explanations
5. prefer online image sources before local extraction when possible

Detailed standards remain in:
- `references/quality-standards.md`
- `references/image-troubleshooting.md`
- `references/concept-categories.md`

## Save / vault behavior

These actions are advanced-only.

When the user explicitly asks to save or archive:
- choose method-name-based filenames
- save under the appropriate Zotero collection path when known
- when moving an item between Zotero collections, prefer the local API via `../zotero_skills/zotero/SKILL.md` if Zotero Desktop is running with the local API enabled; fall back to `assets/zotero_helper.py` otherwise
- use the existing YAML/frontmatter conventions
- refresh indexes only when `AUTO_REFRESH_INDEXES=true`
- run git steps only when enabled by config

## Concept-library behavior

These actions are advanced-only.

If workflow mode requires concept maintenance:
1. scan note content for `[[概念]]` links
2. check whether concept notes already exist (prefer `../obsidian_skills/obsidian-cli/` for fast vault search when the Obsidian CLI is available; otherwise list the concept directory)
3. create missing concept notes in the appropriate concept directory

## Batch behavior

Batch processing is advanced-only and currently runs through the daemon wrapper.
Use it for recursive Zotero collection processing, status checks, and resumable archival workflows.

## Follow-up behavior

After default analysis, useful follow-ups include:
- deeper explanation of one section
- comparison with another paper
- escalation into advanced workflow mode if the user wants notes or saving

## Reference files

Consult these only when needed:
- `../obsidian_skills/obsidian-markdown/SKILL.md` — Obsidian syntax rules for all vault notes (advanced mode)
- `../obsidian_skills/obsidian-cli/SKILL.md` — vault search / note operations via Obsidian CLI (advanced mode)
- `../obsidian_skills/obsidian-bases/SKILL.md` — `.base` views when the user wants a paper-library view (advanced mode)
- `../zotero_skills/zotero/SKILL.md` — Zotero local API: moving collections (write ops), BibTeX export, full-text search (advanced mode)
- `references/zotero-guide.md` — Zotero lookup, collection, and PDF-path workflows
- `references/image-troubleshooting.md` — image fallback and figure extraction edge cases
- `references/concept-categories.md` — concept-note categorization rules
- `references/quality-standards.md` — archival note quality requirements
