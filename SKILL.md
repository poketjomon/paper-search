---
name: paper-search
description: Route paper requests to the right progressively loaded Python-first subskill in this suite. Use `search/` for local-first bundled `journal/**` retrieval with dynamic query-field extraction, honest weak-coverage reporting, query-bundle local search, and arXiv fallback, `lookup/` for alphaXiv/arXiv paper briefs, and `reader/` for deeper one-paper analysis plus explicit advanced workflow mode copied from the reference skills.
---

This is a paper skill suite with multiple subskills.

See `references/usage.md` for suite-level usage and routing.

Choose the subskill that best matches the user request:

## `search/`
Use for local dataset search requests such as:
- find papers by topic / venue / year
- related work lookup
- queries like `find CORL 2024 diffusion policy papers with code`
- 中文检索：`找论文`、`相关论文`、`某方向综述`

Hard rule: if the user is searching, filtering, or collecting papers by topic, venue, year, benchmark, dataset, or paper list, route to `search/` first.
Even if the request mentions an arXiv URL, paper link, or preprint, still use `search/` first when the intent is multi-paper local retrieval rather than reading one specific paper.
Prefer the bundled local `journal/**` corpus before any remote lookup.
The local search path should dynamically extract useful query fields, try a small bundle of related local searches, and only fall back when those local results are still weak.
That same extracted concept bundle should drive remote fallback queries too, so fallback is planned retrieval rather than one raw sentence lookup.
If local matches are weak, the subskill should say so explicitly and then use arXiv fallback rather than pretending generic local matches are enough.

Run the `search/` subskill.

## `lookup/`
Use only when the user provides a specific arXiv id, arXiv URL, or alphaXiv URL and wants a fast paper brief for that one paper.
Examples:
- `summarize arXiv 2401.12345`
- `看看这篇 https://arxiv.org/abs/2401.12345`
- `这个 alphaXiv 链接值不值得读`

Do not use `lookup/` for bulk search, venue/year filtering, or topic-based paper collection.

Run the `lookup/` subskill.

## `reader/`
Use when the user wants deeper one-paper analysis, full paper reading, or an explicit note/workflow task from a specific paper/PDF.
Examples:
- `read this paper`
- `analyze this pdf`
- `帮我读一下这篇论文`
- `做论文笔记`

Default behavior: return deeper structured analysis for the specific paper.
Advanced workflow mode only applies on explicit save / archive / sync / batch / Zotero / Obsidian / note intent.

Run the `reader/` subskill.

If the request is ambiguous, choose the lightest subskill that still answers it:
- search before lookup
- lookup before reader
