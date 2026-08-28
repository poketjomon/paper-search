---
name: paper-search-local
description: Three-layer paper retrieval — (1) bundled local `journal/**` corpus + live arXiv API merge via script, (2) agent-native web search over GitHub awesome lists, blogs, and project pages reusing the same concept bundle, (3) cross-layer dedup and merge. Use for paper search, related-work lookup, topic survey, or venue/year/code/pdf filtering, including queries like "find papers about diffusion policy", "related work for multimodal reasoning", "search CORL 2024 papers with code", "找论文", "相关论文", or "某方向综述".
---

Accept one natural-language paper-search request, then run the three-layer workflow below. Layer 1 is always scripted and deterministic; Layer 2 uses your own web tools and is REQUIRED for exhaustive tasks; Layer 3 merges everything.

## Layer 1 — scripted retrieval (always run)

```bash
./scripts/run.sh "<user query>"
```

The script searches the local `journal/**` corpus, always augments with a live arXiv API search, dedups by title, gates out remote papers that match no domain concept, and merges results (local first, arXiv appended). Return its structured output (count, filters, local status, arXiv augmentation flag, papers, why each matched).

## Layer 2 — agent web search (required for exhaustive/survey tasks)

Trigger when the request is survey-style: "越多越好", related-work collection, 综述, benchmark/dataset enumeration, or a fast-moving field where preprints dominate. For a quick single-topic lookup, Layer 1 alone is fine.

1. Get the shared concept bundle so both layers search the same thing:
   ```bash
   ./scripts/run.sh "<user query>" --concepts
   ```
2. Use your available web tools (WebSearch, WebFetch, or web skills) with the non-generic concepts as query seeds. Sources the script CANNOT reach, in priority order:
   - GitHub awesome lists / paper lists for the topic (e.g. `awesome-<topic>-agents`)
   - arXiv listing pages filtered by announcement month, for papers newer than what Layer 1 surfaced
   - lab blogs, project pages, leaderboards, and survey papers' related-work sections
   - Google Scholar / Semantic Scholar pages for citation tracing
3. For each promising hit, capture title, venue/year, link, and abstract (fetch the page when the snippet is insufficient).

## Layer 3 — merge and report (always when Layer 2 ran)

- Dedup across layers by normalized title; on collision prefer the entry with verified venue metadata.
- Tag each paper's source: `local corpus` / `arXiv` / `web`.
- Keep Layer 1's structured fields (title, abstract, year, venue, link) as the output schema; Layer 2 hits must be normalized into the same schema.
- State coverage honestly: which layers ran, what source types were and were not covered.

## Behavior contract

- extract query fields dynamically from the user's request rather than relying on one fixed topic template
- build a small bundle of related local queries from those extracted concepts
- report when local coverage is weak instead of overstating generic matches
- always augment results with arXiv remote search: local corpus (curated venues) and arXiv (preprints) are complementary sources, not either/or; merge and deduplicate by title, keep strong local matches first, append remote-only papers (arXiv first when local is weak)
- remote queries should reuse the same extracted concepts (multiple composed queries, never the raw sentence once) and include compact semantic variants (for example, `llm` forms) to improve recall for acronym-heavy paper titles
- for exhaustive tasks, do not stop at Layer 1 output — Layer 2 web sources routinely contain the majority of relevant preprints, awesome-list entries, and benchmark pages that no API-only pipeline reaches

Do not assume multi-turn memory.

See `references/usage.md` for examples and scope.
