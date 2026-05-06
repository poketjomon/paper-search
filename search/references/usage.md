# Paper Search Usage

Run from inside this subskill:

```bash
./scripts/run.sh "find 2024 diffusion policy papers from CORL with code"
```

Optional explicit dataset root:

```bash
./scripts/run.sh "robot manipulation papers with pdf" --journal-root ./journal
```

## Runtime

- Python entrypoint: `paper_search.py`
- shell wrapper: `scripts/run.sh`
- bundled local dataset: `journal/**`
- local-first retrieval with arXiv fallback when local coverage is weak

## What it returns

- found paper count
- applied filters
- local status (`strong` or `weak`)
- whether arXiv fallback was used
- top papers
- why each paper matched
- warnings when local coverage appears weak

## Retrieval behavior

- search the bundled local `journal/**` corpus first
- extract query fields dynamically from the user's request
- build a small deterministic query bundle from those extracted concepts for better local recall
- keep local/remote provenance explicit in the output
- prefer honest weak-coverage reporting over generic local false positives
- use arXiv fallback only when strong local matches are absent
- remote fallback reuses the extracted concepts and query bundles instead of sending the raw user sentence as a single remote query
- remote fallback also tries compact semantic variants (such as `llm`) to improve retrieval for acronym-dominant papers

## Routing

- use this subskill for local bundled `journal/**` retrieval
- use this subskill first even for niche topic discovery where local coverage may be sparse
- use `lookup/` when the user gives one specific arXiv / alphaXiv paper
- use `reader/` when the user wants full-paper analysis or note generation

## Scope

- single-turn only
- bundled local `journal/**` dataset first, then arXiv fallback if needed
- supports year / year range / venue / `with code` / `with pdf`
- does not preserve multi-turn context
