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
- use the existing YAML/frontmatter conventions
- refresh indexes only when `AUTO_REFRESH_INDEXES=true`
- run git steps only when enabled by config

## Concept-library behavior

These actions are advanced-only.

If workflow mode requires concept maintenance:
1. scan note content for `[[概念]]` links
2. check whether concept notes already exist
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
- `references/zotero-guide.md` — Zotero lookup, collection, and PDF-path workflows
- `references/image-troubleshooting.md` — image fallback and figure extraction edge cases
- `references/concept-categories.md` — concept-note categorization rules
- `references/quality-standards.md` — archival note quality requirements
