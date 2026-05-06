# Paper Search Suite Usage

Use this package root when you want to route a paper request to the right bundled subskill.

Run from inside this suite:

```bash
./scripts/run.sh search "find 2024 diffusion policy papers from CORL with code"
./scripts/run.sh lookup "2401.12345" --format brief
./scripts/run.sh reader --status
```

## Routing

- use `search/` for local bundled `journal/**` retrieval, paper lists, topic search, venue/year filtering, and sparse-domain discovery
- `search/` is local-first: it should extract query fields dynamically, try a small bundle of related local searches, report weak local coverage honestly, and then use arXiv fallback when needed
- the same extracted bundle should also drive multiple remote fallback queries instead of sending one raw sentence remotely
- use `lookup/` for one-paper arXiv / alphaXiv briefs
- use `reader/` for deeper one-paper analysis and explicit advanced workflow mode
- use advanced workflow mode only when the user explicitly asks for saving, archiving, syncing, Zotero, Obsidian, notes, or batch processing
- default escalation order: `search/` before `lookup/`, `lookup/` before `reader/`

## Entrypoints

- suite wrapper: `./scripts/run.sh`
- search wrapper: `search/scripts/run.sh`
- lookup wrapper: `lookup/scripts/run.sh`
- reader wrapper: `reader/scripts/run.sh`

## Notes

- this suite is Python-first and wrapper-first
- subskills own their runtime details; this root layer only provides routing guidance
