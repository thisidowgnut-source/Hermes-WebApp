---
title: "Hermes OS & Doh-Nut Sovereign Mission Control — Sovereign Security Protocol"
document_id: "HERMES-WEBAPP-SEC-001"
version: "3.7.0"
last_updated: "2026-09-16 06:30:00 MYT"
maintainer: "GangBo Sovereign Architect"
classification: "MISSION-CRITICAL // SECURITY POLICY"
lifecycle_status: "PRODUCTION / ACTIVE"
---

# 🛡️ Sovereign Security Protocol (SECURITY.md)

> **Zero-Trust Hardening, Directory Sandboxing, HMAC-SHA256 Telegram Verification, and Shell Sanitization.**

---

## 📜 Audit & Revision Ledger

| Version | Timestamp (MYT / ISO) | Author / Agent | Scope / Root Cause | Components Updated | Validation Proof |
|:---|:---|:---|:---|:---|:---|
| **`3.7.0`** | 2026-09-16 06:30:00<br>`2026-09-15T22:30:00Z` | Antigravity Conductor | Penghapusan bypass auth, penguatkuasaan sekatan metacharacter shell pada spawn, dan pengasingan path sandbox. | `backend/auth.py`, `backend/routers/swarm.py`, `backend/routers/system.py`, `docs/SECURITY.md` | 9/9 auth tests passed, 89/89 full pytest passed, live HMAC validated. |
| **`3.6.0`** | 2026-09-12 16:35:00<br>`2026-09-12T08:35:00Z` | Antigravity Conductor | Pematuhan FHS 3.0 sandboxing, sekatan directory traversal & split-token enforcement. | `docs/SECURITY.md`, `var/run/`, `backend/routers/system.py` | Path traversal unit tests passed. |
| **`3.0.0`** | 2026-07-27 18:00:00<br>`2026-07-27T10:00:00Z` | Hermes Dev Squad | Spesifikasi asas sandboxing Playwright dan split-token security plane. | `backend/main.py` | Sifar konflik bot polling. |

---

Because the Hermes OS WebApp grants direct shell (`pwsh.exe`) and physical process control over the host Windows machine, it presents a critical security risk if exposed to the public internet without severe hardening.

## 1. Network Exposure (Cloudflare Tunnels)
- **Do not use port forwarding.** Opening port `9220` on your home router exposes the FastAPI server to Shodan and automated vulnerability scanners.
- **Mandatory Tunneling:** Use `cloudflared` (Cloudflare Tunnels). The tunnel is configured to forward directly to `localhost:9220` without interstitial warning pages.

## 2. Authentication & Telegram Isolation (IMPLEMENTED & ACTIVE)
Since the Cloudflare Tunnel provides a public URL (`*.trycloudflare.com`), multi-layer cryptographic authentication is enforced:
1. **Init Data HMAC-SHA256 Validation:** The FastAPI backend intercepts the `X-Telegram-Init-Data` header or `initData` query parameter and verifies it cryptographically against the secret key derived from `TELEGRAM_BOT_TOKEN`.
2. **User ID Verification:** The backend verifies that the signed payload contains an authenticated Telegram user ID.
3. **Rejection Protocol:** Any HTTP request arriving from an external network lacking a valid, unexpired Telegram signature is immediately rejected with `HTTP 401 Unauthorized`. Local loopback (`127.0.0.1`, `localhost`, `testclient`) is allowed for native desktop use and automated test suites.

## 3. Remote Code Execution (RCE) Boundaries & Shell Metacharacter Protection
- The Terminal module executes `pwsh.exe -NoProfile` under the least-privilege host user.
- **Shell Metacharacter Rejection (`backend/routers/swarm.py`):** Custom commands submitted to `/api/swarm/spawn` are strictly filtered. Any command containing `&`, `|`, `;`, `` ` ``, `$(`, `\n`, or `\r` is rejected with `HTTP 400 Bad Request` to prevent command chaining and injection.

## 4. Path Sandbox (`_is_path_allowed`)
- File operations via `/api/files/read` and `/api/files/write` are strictly constrained to allowlisted root paths:
  - `C:\Users\megat\Hermes-WebApp`
  - `C:\Users\megat\ObsidianVault`
  - `G:\Doh-Nut`
- Direct access to sensitive paths (`.env`, `.ssh`, `id_rsa`, `id_ed25519`, `credentials.json`, `*.key`) is blocked with `HTTP 403 Forbidden`.

## 5. Playwright (Vision) Sandboxing
- The Chromium instance launched by Playwright runs headlessly.
- Automatic detection locates system Chrome (`C:\Program Files\Google\Chrome\Application\chrome.exe`) and Microsoft Edge.
- Browser contexts remain ephemeral and isolate cookies from leaking outside the designated session.
