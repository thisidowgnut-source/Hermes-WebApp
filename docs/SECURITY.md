---
title: "Hermes OS & Doh-Nut Sovereign Mission Control — Sovereign Security Protocol"
document_id: "HERMES-WEBAPP-SEC-001"
version: "3.6.0"
last_updated: "2026-09-12 16:35:00 MYT"
maintainer: "GangBo Sovereign Architect"
classification: "MISSION-CRITICAL // SECURITY POLICY"
lifecycle_status: "PRODUCTION / STABLE"
---

# 🛡️ Sovereign Security Protocol (SECURITY.md)

> **Zero-Trust Hardening, Directory Sandboxing, and Split-Token Cryptographic Specification.**

---

## 📜 Audit & Revision Ledger

| Version | Timestamp (MYT / ISO) | Author / Agent | Scope / Root Cause | Components Updated | Validation Proof |
|:---|:---|:---|:---|:---|:---|
| **`3.6.0`** | 2026-09-12 16:35:00<br>`2026-09-12T08:35:00Z` | Antigravity Conductor | Pematuhan FHS 3.0 sandboxing, sekatan directory traversal & split-token enforcement. | `docs/SECURITY.md`, `var/run/`, `backend/routers/system.py` | Path traversal unit tests passed. |
| **`3.0.0`** | 2026-07-27 18:00:00<br>`2026-07-27T10:00:00Z` | Hermes Dev Squad | Spesifikasi asas sandboxing Playwright dan split-token security plane. | `backend/main.py` | Sifar konflik bot polling. |

---

Because the Hermes OS WebApp grants direct shell (`pwsh.exe`) and physical process control over the host Windows machine, it presents a catastrophic security risk if exposed to the public internet without severe hardening.

## 1. Network Exposure (Cloudflare Tunnels)
- **Do not use port forwarding.** Opening port `9220` on your home router exposes the FastAPI server to Shodan and automated vulnerability scanners.
- **Mandatory Tunneling:** Use `cloudflared` (Cloudflare Tunnels). The tunnel must be configured to point strictly to `localhost:9220`. 

## 2. Authentication & Telegram Isolation
Since the Cloudflare Tunnel provides a public URL (e.g., `https://my-secret-tunnel.trycloudflare.com`), anyone who discovers the URL could theoretically access the dashboard.
### Required Hardening (Implementation Pending/Required):
1. **Init Data Validation:** The FastAPI backend MUST intercept the `Telegram.WebApp.initData` string.
2. **User ID Whitelisting:** The backend MUST verify the cryptographically signed `initData` against the Telegram Bot Token and verify that the `user.id` matches the exact authorized owner's Telegram ID.
3. **Rejection Protocol:** Any HTTP request lacking a valid, unexpired Telegram signature MUST be rejected with `HTTP 401 Unauthorized`.

## 3. Remote Code Execution (RCE) Boundaries
- The Terminal module executes `pwsh.exe -NoProfile`. It runs under the privileges of the user who started the FastAPI Uvicorn process.
- **Do NOT run the Uvicorn process as Administrator** unless absolutely required for specific macros. Running as a standard user limits the blast radius if the WebApp is compromised.

## 4. Playwright (Vision) Sandboxing
- The Chromium instance launched by Playwright runs headlessly.
- Ensure that the browser context does not leak sensitive cookies from the host machine. Playwright must always launch in an isolated browser context unless explicitly instructed otherwise.
