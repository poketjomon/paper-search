---
name: paper-search-local
description: Search the bundled `journal/**` paper dataset from one natural-language request and return local-first ranked papers with explicit match reasons, honest local coverage status, dynamic query-field extraction, query-bundle retrieval, and arXiv fallback when local matches are weak. Use for paper search, related-work lookup, topic survey, or venue/year/code/pdf filtering, including queries like "find papers about diffusion policy", "related work for multimodal reasoning", "search CORL 2024 papers with code", "找论文", "相关论文", or "某方向综述".
---

Accept one natural-language paper-search request.

Run:
`./scripts/run.sh "<user query>"`

Use the user's request as `<user query>`.

Return the command output directly.

Keep the response focused on:
- found paper count
- applied filters
- local status (`strong` or `weak`)
- whether arXiv fallback was used
- top papers
- why each paper matched

Behavior contract:
- search the bundled local `journal/**` corpus first
- extract query fields dynamically from the user's request rather than relying on one fixed topic template
- build a small bundle of related local queries from those extracted concepts
- report when local coverage is weak instead of overstating generic matches
- use arXiv fallback only when local matches are weak or absent
- remote fallback should reuse the same extracted concepts to compose multiple remote queries instead of sending the raw sentence once
- remote fallback should include compact semantic variants (for example, `llm` forms) to improve recall for acronym-heavy paper titles

Do not assume multi-turn memory.

See `references/usage.md` for examples and scope.
