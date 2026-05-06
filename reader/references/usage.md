# Paper Reader Usage

Use this subskill when the paper is already known and the user wants deeper one-paper analysis than `lookup/` provides.

Run from inside this subskill:

```bash
./scripts/run.sh "https://arxiv.org/abs/2401.12345"
./scripts/run.sh --status
./scripts/run.sh -c "VLA"
```

## default analysis examples

Use the default path for ordinary one-paper reading requests:

- local PDF path
- arXiv URL
- alphaXiv URL
- known paper title / identifier when the source is already known

Default result:
- decision summary
- problem / method / evidence
- limitations / what to inspect next

This path is for reading and analysis only. It should not assume note saving, concept maintenance, Zotero moves, or Obsidian writes.

## advanced workflow examples

Use the advanced path only on explicit workflow intent:

- `./scripts/run.sh -c "VLA"` for recursive Zotero collection processing
- `./scripts/run.sh --status` for daemon workflow status
- explicit requests to save notes, archive to Obsidian, sync with Zotero, or batch-process papers

Advanced workflow mode is for:
- vault-ready note generation
- Zotero-backed batch processing
- concept-note maintenance
- save / archive / sync flows

## Runtime

- Python entrypoint: `paper_daemon.py`
- shell wrapper: `scripts/run.sh`
- shared config: `../_shared/user-config.json`
- note/template assets: `assets/**`
- workflow references: `references/**`

## Output focus

Default analysis should emphasize:
- what problem the paper tackles
- how the method works
- what evidence/results matter
- what is missing or weak
- whether the paper is worth deeper reading

Advanced workflow output may additionally include:
- archival-quality notes
- figures / formulas / tables
- concept links and concept-note updates
- save / index / git workflow results

## Routing

- use `lookup/` for a fast arXiv/alphaXiv brief before deciding whether to read more
- use `search/` for local `journal/**` paper retrieval or topic/venue/year filtering
- use this subskill for deeper one-paper analysis
- use advanced workflow mode only on explicit save / archive / sync / batch / Zotero / Obsidian / note intent
