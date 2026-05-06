---
name: paper-search-lookup
description: Turn an arXiv paper id or arXiv/alphaXiv URL into a fast structured paper brief. Use when the user provides a specific paper and wants a quick overview before deciding whether to read more.
---

Use this subskill to turn an arXiv identifier or URL into a fast, structured paper brief.

Run:
`./scripts/run.sh "<paper-or-url>" --format brief`

Use `--format brief-zh` for Chinese output when appropriate.
Use `--format json` only when structured machine output is needed.

1. Normalize the input into one or more paper ids.
   - Accept plain ids like `2401.12345` or `1706.03762v7`
   - Accept arXiv URLs like `https://arxiv.org/abs/2401.12345`
   - Accept alphaXiv URLs like `https://www.alphaxiv.org/overview/2401.12345`
2. Run:
   - `python3 scripts/alphaxiv_lookup.py "<paper-or-url>" --format brief`
   - Use `--format brief-zh` for Chinese output when appropriate.
   - Use `--format json` only when structured machine output is needed.
3. Read returned fields in this priority order:
   - `best_summary`
   - `alphaxiv_report`
   - `alphaxiv_description`
   - `arxiv_abstract`
4. Write the answer in a fixed structure:
   - Paper title
   - What problem it solves
   - Core idea / method
   - Key findings
   - Limitations / caveats
   - Whether it is worth reading in full

Fallback rules:
- If alphaXiv is thin or unavailable, combine it with the arXiv abstract.
- Do not invent missing benchmark numbers.
- If the user needs equation-level detail, say the PDF should still be checked.

This subskill is integrated from the AlphaXiv Paper Lookup reference runner, with a local wrapper and suite-level routing.

See `references/usage.md` for examples.
