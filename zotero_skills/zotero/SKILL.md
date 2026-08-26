---
name: zotero
description: Operate the local Zotero Desktop library through its local HTTP API (localhost:23119) — search items, list collections, move items between collections, and export BibTeX. Use for Zotero write operations (moving collections) and BibTeX export. For read-only batch queries that must work while Zotero is closed, prefer the SQLite-based reader/assets/zotero_helper.py instead.
---

# Zotero (Local API)

Operate the user's local Zotero Desktop library through its local HTTP API.

## Division of labor with papersearch's built-in Zotero tools

This suite already has a SQLite-based helper at `../../reader/assets/zotero_helper.py` (read-only DB copy, works while Zotero is closed). Choose by scenario:

| Scenario | Use |
|---|---|
| Batch read-only queries (daemon, listing collections, finding PDFs) while Zotero may be closed | `reader/assets/zotero_helper.py` (SQLite) |
| **Write operations** (moving an item between collections) while Zotero is running | **This skill (local API)** — safer than writing the SQLite DB directly |
| BibTeX export (`references.bib`) | This skill (local API) — not available via SQLite |
| Full-text search | This skill (local API) — not available via SQLite |

## Connection Setup

Before any operation, ensure Zotero is running and the local API is enabled:

1. **Open Zotero Desktop** application
2. **Enable Local API**: Settings > Advanced > check "Allow other applications on this computer to communicate with Zotero" (serves http://localhost:23119/api/)
3. **Verify connection**:

```bash
curl -s -H "Zotero-API-Version: 3" "http://127.0.0.1:23119/api/users/0/collections"
```

If the connection fails:
- The local API preference is not yet enabled
- Close and reopen Zotero after checking the preference
- Or manually add to `prefs.js`: `user_pref("extensions.zotero.httpServer.localAPI.enabled", true);`

## Direct HTTP API Usage

When the Python helper script is unavailable or fails, use direct HTTP calls to the Zotero local API (port 23119).

### List collections (folders)
```bash
curl -s -H "Zotero-API-Version: 3" "http://127.0.0.1:23119/api/users/0/collections"
```
Response includes `key`, `name`, and `meta.numItems` for each collection.

### List items in a collection
```bash
# Top-level items only
curl -s -H "Zotero-API-Version: 3" "http://127.0.0.1:23119/api/users/0/collections/{collectionKey}/items/top?limit=25"

# All items (including attachments)
curl -s -H "Zotero-API-Version: 3" "http://127.0.0.1:23119/api/users/0/collections/{collectionKey}/items?limit=25"
```

### Search across library
```bash
curl -s -H "Zotero-API-Version: 3" "http://127.0.0.1:23119/api/users/0/items?q=transformer&limit=10"
```

### Export BibTeX
```bash
curl -s -H "Zotero-API-Version: 3" "http://127.0.0.1:23119/api/users/0/items?format=bibtex&limit=100"

# A single collection to a .bib file
curl -s -H "Zotero-API-Version: 3" "http://127.0.0.1:23119/api/users/0/collections/{key}/items?format=bibtex" > collection.bib
```

### Get item children (attachments)
```bash
curl -s -H "Zotero-API-Version: 3" "http://127.0.0.1:23119/api/users/0/items/{itemKey}/children"
```

### Get attachment file URL
```bash
curl -s -H "Zotero-API-Version: 3" "http://127.0.0.1:23119/api/users/0/items/{attachmentKey}/file/view/url"
```

## Reading PDFs from Zotero

Zotero stores attachments under `~/Zotero/storage/{attachmentKey}/` (configurable via `paths.zotero_storage` in `_shared/user-config.json`).

1. Get the attachment key from the item's children (response includes `links.attachment.href` and `data.filename`)
2. The PDF is at `~/Zotero/storage/{attachmentKey}/{filename}`
3. Read the PDF directly with the agent's PDF/file reading capability — do not install third-party parsing libraries

## Python Helper Script

The stdlib-only helper script provides convenience wrappers:

```bash
python3 <skill-root>/scripts/zotero.py <command>
```

### Fast starts

Check readiness:
```bash
python3 scripts/zotero.py status --json
```

Search and export:
```bash
python3 scripts/zotero.py search "transformer" --json
python3 scripts/zotero.py export-bibtex --out references.bib
```

## Workflow

1. **Verify Zotero is running** and local API is enabled.
2. **Choose connection method**:
   - Prefer direct HTTP API calls when the Python helper is unavailable
   - Use the helper script when available for convenience
3. **Read-only operations** (safe by default):
   - List collections/items via HTTP API
   - Search library
   - Export BibTeX
   - Locate PDFs in local storage
4. **Attachment/PDF access**: Only retrieve when explicitly requested
5. **Write operations** (e.g. moving items between collections): Confirm with user before import/save actions

## Common HTTP API Patterns

### Summarize a collection
```bash
# 1. Get collection key
curl -s -H "Zotero-API-Version: 3" "http://127.0.0.1:23119/api/users/0/collections"

# 2. Get items in collection (extract title, abstract, creators)
curl -s -H "Zotero-API-Version: 3" "http://127.0.0.1:23119/api/users/0/collections/{key}/items/top?limit=50"

# 3. For each item, get children to find PDF attachment key
curl -s -H "Zotero-API-Version: 3" "http://127.0.0.1:23119/api/users/0/items/{itemKey}/children"

# 4. Read PDF from ~/Zotero/storage/{attachmentKey}/
```

## Output standards

- For inventory/search, return title, creators, year, Zotero item key, and BibTeX key when available.
- For PDF reading, summarize key findings: research question, method, results, and conclusions.
- For `.bib` export, return the absolute output path and entry count.
- For blockers, name the exact gate: Zotero app missing, local API disabled, port closed, no matching item, or PDF not found.

## Route details

Read `references/local-api-routes.md` for complete endpoint documentation.
