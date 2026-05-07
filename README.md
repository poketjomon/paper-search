# papersearch

🌐 [English](README.md) | [简体中文](README.zh-CN.md)

papersearch is a Claude Code skill for paper research.

It can:
- find papers by topic, venue, or year
- quickly judge whether one paper is worth reading
- deeply analyze one paper
- generate Obsidian / Zotero-ready notes

## How to use it

Use natural language. Describe what you want, and Claude will route the request.

### 1) Find a list of papers

Say:

- `Find 2024 ICLR papers about diffusion policy, preferably with code and project links`
- `Create a related-work list for VLA from 2023-2025`

You will get a ranked paper list, match reasons, applied filters, and weak/strong coverage status.

### 2) Get a quick brief for one paper

Say:

- `Quickly summarize this paper: arXiv 2401.12345`
- `Is this alphaXiv paper worth reading: https://www.alphaxiv.org/...`

You will get the problem, core method, key results, limitations, and a reading recommendation.

### 3) Deeply research one paper

Say:

- `Deeply analyze this paper's method, experiment design, and limitations`
- `Compare this paper against XXX baseline and give me a conclusion`

You will get a structured deep analysis and follow-up points worth checking.

### 4) Generate archive-ready notes

To trigger the advanced workflow, explicitly mention `save`, `archive`, `Obsidian`, `Zotero`, or `batch`.

Say:

- `Read this paper and generate an Obsidian note with key figures and formula explanations`
- `Process this Zotero collection and batch-generate archived paper notes`

You will get archive-ready notes, workflow output, and batch status.

## FAQ

### Is this skill only for paper search?
No. It also supports single-paper briefs, deep research, and archive-ready note generation.

### Do I need to manually pick search/lookup/reader?
No. Just describe your goal in natural language.

## Local debugging

```bash
./scripts/run.sh <search|lookup|reader> [args...]
```

Examples:

```bash
./scripts/run.sh search "find 2024 iclr papers about diffusion policy with code"
./scripts/run.sh lookup "2401.12345" --format brief
./scripts/run.sh reader --status
```

## Requirements

- Python 3.10+
- macOS / Linux
