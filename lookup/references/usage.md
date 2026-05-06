# AlphaXiv Lookup Usage

Run from inside this subskill:

```bash
./scripts/run.sh "2401.12345" --format brief
```

Other examples:

```bash
./scripts/run.sh "https://arxiv.org/abs/2401.12345" --format brief
./scripts/run.sh "https://www.alphaxiv.org/overview/2401.12345" --format brief-zh
./scripts/run.sh --input-file papers.txt --format json-compact
```

## What it returns

- paper title
- source used
- concise summary / takeaway
- problem solved
- core method
- worth-reading verdict
- warnings / fallback status when relevant

## Routing

- use this subskill for one-paper arXiv / alphaXiv lookup
- use `search/` for local topic, venue, year, or paper-list retrieval
- use `reader/` when a quick brief is not enough and full reading is needed

## Scope

- accepts arXiv ids, arXiv URLs, alphaXiv URLs
- can process single or batch inputs
- prefers alphaXiv overview when available
- falls back to arXiv abstract when needed
