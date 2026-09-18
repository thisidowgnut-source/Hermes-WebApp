---
title: "Hermes OS & Doh-Nut Sovereign Mission Control — Documentation Hub & Index"
document_id: "HERMES-DOCS-INDEX-001"
version: "3.6.0"
last_updated: "2026-09-12 16:35:00 MYT"
maintainer: "GangBo Sovereign Architect"
classification: "ENGINEERING DOCS // DIVIO STANDARD"
lifecycle_status: "ACTIVE"
---

# 📚 Documentation Hub — Divio 4-Quadrant Architecture

> **Master index and navigation directory for all engineering, architectural, and operational documentation of Hermes OS & Doh-Nut Sovereign Mission Control, organized according to the Divio Documentation System.**

---

## 📜 Audit & Revision Ledger

| Version | Timestamp (MYT / ISO) | Author / Agent | Scope / Root Cause | Components Updated | Validation Proof |
|:---|:---|:---|:---|:---|:---|
| **`4.2.0`** | 2026-09-16 08:15:00<br>`2026-09-16T00:15:00Z` | Antigravity Conductor | Pelaksanaan penuh 13 tugasan Remote Mission Control, penyelarasan protokol NDJSON, perkhidmatan lejar SQLite WAL, dan modul UI Mobile Mission Control. | `docs/README.md`, `docs/PRD.md`, `docs/release-checklists/remote-mission-control.md`, `static/` | 221+ ujian melepasi (100% lulus, 0 ralat). |
| **`3.6.0`** | 2026-09-12 16:35:00<br>`2026-09-12T08:35:00Z` | Antigravity Conductor | Penstrukturan FHS 3.0, Kemasan Butang Emil Kowalski (Zero-Jitter), dan Arkitektur Mobile-First Sifar-Bertindih. | `docs/README.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/AGENTS.md`, `docs/DESIGNS.md`, `docs/API.md` | Divio 4-quadrant verified, 0 broken links, 100% doc alignment. |
| **`3.5.0`** | 2026-09-12 15:55:00<br>`2026-09-12T07:55:00Z` | GangBo Sovereign Architect | Penstrukturan semula dokumentasi berasaskan sistem 4-kuadran Divio & arkib dokumen lama. | `docs/` tree, `docs/README.md`, `docs/archive/` | 10 fail dokumentasi aktif disahkan selaras. |

---

## 🧭 Divio 4-Quadrant System Overview

```
                   PRACTICAL STEPS                    THEORETICAL KNOWLEDGE
          ┌──────────────────────────────┬──────────────────────────────┐
          │                              │                              │
          │         1. TUTORIALS         │        4. EXPLANATION        │
          │     (Learning-Oriented)      │    (Understanding-Oriented)  │
          │                              │                              │
          │  • README.md (Root Guide)    │  • docs/PRD.md               │
          │                              │  • docs/AGENTS.md            │
          │                              │  • docs/SKILLS.md            │
          │                              │                              │
ACQUISITION ├──────────────────────────────┼──────────────────────────────┤ APPLICATION
          │                              │                              │
          │        2. HOW-TO GUIDES      │         3. REFERENCE         │
          │       (Task-Oriented)        │    (Information-Oriented)    │
          │                              │                              │
          │  • docs/DEPLOYMENT.md        │  • docs/ARCHITECTURE.md      │
          │  • docs/TROUBLESHOOTING.md   │  • docs/API.md               │
          │                              │  • docs/DESIGNS.md           │
          │                              │  • docs/SECURITY.md          │
          │                              │                              │
          └──────────────────────────────┴──────────────────────────────┘
```

---

## 📑 Complete Document Directory

### 1. Tutorials (Learning-Oriented)
- [`../README.md`](file:///C:/Users/megat/Hermes-WebApp/README.md) — **Master System Guide & Quickstart**: Orientasi komprehensif, setup asas, dan pengenalan kepada 16 modul teras.

### 2. How-To Guides (Task-Oriented)
- [`DEPLOYMENT.md`](file:///C:/Users/megat/Hermes-WebApp/docs/DEPLOYMENT.md) — **Production Deployment Guide**: Langkah penggunaan Windows Service (NSSM), Linux/WSL2 systemd, dan persediaan terowong Cloudflare.
- [`TROUBLESHOOTING.md`](file:///C:/Users/megat/Hermes-WebApp/docs/TROUBLESHOOTING.md) — **Runtime Troubleshooting Runbook**: Penyelesaian ralat WebSocket, konflik port 9220, dan pemulihan subprocess.

### 3. Reference (Information-Oriented)
- [`ARCHITECTURE.md`](file:///C:/Users/megat/Hermes-WebApp/docs/ARCHITECTURE.md) — **System Architecture Specification**: Rajah topologi Mermaid, penghalaan FastAPI REST, 5 hab WebSocket, dan integrasi WebBridge port 10087.
- [`API.md`](file:///C:/Users/megat/Hermes-WebApp/docs/API.md) — **API Contract Reference**: Rujukan lengkap parameter dan skema respons untuk setiap endpoint.
- [`DESIGNS.md`](file:///C:/Users/megat/Hermes-WebApp/docs/DESIGNS.md) — **UI/UX Design Specification**: Garis panduan Anti-AI Slop, OLED palette, dan transisi modul skrin penuh.
- [`SECURITY.md`](file:///C:/Users/megat/Hermes-WebApp/docs/SECURITY.md) — **Sovereign Security Protocol**: Pengasingan sandbox, pemantauan integriti fail (FIM), dan arkitektur split-token.

### 4. Explanation (Understanding-Oriented)
- [`PRD.md`](file:///C:/Users/megat/Hermes-WebApp/docs/PRD.md) — **Product Requirements Document**: Penyata masalah, visi produk, dan spesifikasi fungsian Doh-Nut Sovereign HQ.
- [`AGENTS.md`](file:///C:/Users/megat/Hermes-WebApp/docs/AGENTS.md) — **Autonomous Agent Operational Handbook**: Protokol operasi ejen AI berasaskan Mesin Status 5-Fasa dan gerbang HITL.
- [`SKILLS.md`](file:///C:/Users/megat/Hermes-WebApp/docs/SKILLS.md) — **Specialized Skills Registry**: Pemetaan kemahiran autonomi yang boleh diaktifkan.

---

## 🗄️ Sub-Directories & Repositories

- **[`n8n/`](file:///C:/Users/megat/Hermes-WebApp/docs/n8n/)**: Koleksi fail blueprint alur kerja JSON n8n (async media generation, telegram HITL, subworkflows).
- **[`superpowers/`](file:///C:/Users/megat/Hermes-WebApp/docs/superpowers/)**: Pelan arkitektur, spesifikasi reka bentuk, dan trajektori pelaksanaan terdahulu.
- **[`archive/`](file:///C:/Users/megat/Hermes-WebApp/docs/archive/)**:
  - `reviews/`: Laporan semakan audit terdahulu (GLM, Opus, DSH, Review v1..v3).
  - `planning/`: Dokumen perancangan bersejarah (PROJECT, TODO, IMPROVEMENT_PLAN).
  - `patches/`: Artefak kod lama dan sandaran ujian.
