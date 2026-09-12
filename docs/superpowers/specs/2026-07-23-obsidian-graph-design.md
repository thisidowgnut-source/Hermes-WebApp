# 🧠 Design Specification: Obsidian Knowledge Graph & Local Search Engine

**Project**: Hermes-WebApp (Sub-Project 3)  
**Date**: 2026-07-23  
**Status**: APPROVED  

---

## 1. Overview

The **Obsidian Knowledge Graph & Local Search Engine** (`mod-obs-graph`) provides interactive visualization of the 2,700+ wikilink note network in `C:\Users\megat\ObsidianVault\Hermes-Obsidian` and fast full-text semantic search over local Obsidian notes.

---

## 2. Architecture & Data Flow

```
[ Frontend: mod-obs-graph ] 
       │
       ├─► GET  /api/obsidian/graph       ─► Wikilink Network Parser (Cache: .ua/knowledge-graph.json)
       └─► POST /api/obsidian/search      ─► Local Vault Full-Text Search Engine
```

---

## 3. Component Specifications

### 3.1 Backend Endpoints (`backend/routers/system.py`)

1. **`GET /api/obsidian/graph`**: Returns nodes & links of Obsidian vault MOC hubs (`Hermes-Docs-MOC.md`, `Hermes-Features-MOC.md`, `Hermes-Skills-MOC.md`).
2. **`POST /api/obsidian/search`**: Searches vault note titles and contents for query keywords, returning scored note snippets.

---

## 4. User Interface Specification (`static/index.html`)

- **Dock Item**: **Graph** (Icon: `git-fork`, Data Index: 14).
- **Module ID**: `mod-obs-graph`.
- **Layout**: Bento-Box 2-subtab interface:
  1. **Knowledge Graph Canvas**: Visual node network representation.
  2. **Vault Vault FTS Search**: Instant note content search & preview.

---

## 5. Test Plan

- `test_obsidian_graph_endpoint()`
- `test_obsidian_search_endpoint()`
