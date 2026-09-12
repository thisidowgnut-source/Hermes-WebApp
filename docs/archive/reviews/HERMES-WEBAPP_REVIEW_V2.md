# Hermes-WebApp Codebase Review V2
**Date:** 2026-07-27 19:00 UTC+8  
**Previous review:** 2026-07-27 (HERMES-WEBAPP_REVIEW.md — V1)  
**Scope:** Fresh re-review of all files after user updates

---

## What Changed Since V1

| Area | V1 (Jul 27 morning) | V2 (Jul 27 evening) | Delta |
|------|---------------------|---------------------|-------|
| **`backend/auth.py`** | ❌ Did not exist | ✅ Exists (89 lines) — `verify_telegram_init_data()` + `telegram_auth_guard()` dependency | **NEW** |
| **`backend/main.py`** | 67 lines, no auth | 67 lines, **still no auth wired** | **UNCHANGED** |
| **`backend/config.py`** | CORS `*`, no Telegram token env | **UNCHANGED** — CORS still `*` | **UNCHANGED** |
| **`static/index.html`** | 4088 lines | 4618 lines (+530) | **Grew** — new module overlays added |
| **`tests/test_auth.py`** | Did not exist | ✅ 134 lines, 10 tests — full HMAC-SHA256 verify | **NEW** |
| **`tests/test_ui_contracts.py`** | Did not exist | ✅ 221 lines, 6 tests — HTML structural validation | **NEW** |
| **`tests/test_bot_bridge.py`** | Did not exist | ✅ Exists (not deep-reviewed) | **NEW** |
| **`tests/test_empirical_stress.py`** | Did not exist | ✅ Exists (not deep-reviewed) | **NEW** |
| **`tests/test_websockets_e2e.py`** | 158 lines | 5370 bytes — likely expanded | **UPDATED** |
| **`scripts/hermes_watchdog.py`** | Did not exist | ✅ 106 lines — self-healing daemon | **NEW** |
| **`scripts/fix_tg.py`** | Did not exist | ✅ Exists | **NEW** |
| **`scripts/fix_terminal_id.py`** | Did not exist | ✅ Exists | **NEW** |
| **`scripts/cloudflare_webhook_updater.py`** | Existed | 4033 bytes (was smaller) | **UPDATED** |
| **`scripts/update_telegram_url.py`** | Did not exist | ✅ Exists | **NEW** |
| **`scripts/apply_*.py` (8 files)** | Did not exist | ✅ 8 UI patch scripts | **NEW** |
| **`scripts/revert_ugly_patches.py`** | Did not exist | ✅ Revert utility | **NEW** |
| **`scripts/remove_jitter.py`** | Did not exist | ✅ CSS cleanup | **NEW** |
| **`.queue/workflows.json`** | Did not exist | ✅ Workflow state persistence | **NEW** |
| **`docs/superpowers/`** | Did not exist | ✅ Plans + specs (8 files) | **NEW** |

---

## Updated Scores

| Dimension | V1 Score | V2 Score | Change | Evidence |
|-----------|----------|----------|--------|----------|
| **Security** | 3/10 | **5/10** | ⬆️ +2 | `backend/auth.py` EXISTS with proper HMAC-SHA256. `tests/test_auth.py` validates 10 scenarios. **BUT: auth NOT wired into `backend/main.py`** — middleware never applied, so all endpoints still open. CORS still `*`. |
| **Testing** | 5/10 | **7/10** | ⬆️ +2 | 10+ test files now. `test_auth.py` (10 tests), `test_ui_contracts.py` (6 HTML structural tests), `test_bot_bridge.py`, `test_empirical_stress.py`, `test_ui_contracts.py`. Auth has proper HMAC test vectors. |
| **Architecture** | 6/10 | **6/10** | — | Same. Auth module added but not integrated. |
| **Frontend/UX** | 7/10 | **7/10** | — | 4618 lines (+530). New module overlays added (all 15 operational per user). Still single-file monolith. |
| **Operations** | 5/10 | **7/10** | ⬆️ +2 | `hermes_watchdog.py` — self-healing daemon checks health + auto-restart + webhook sync. `fix_tg.py`, `fix_terminal_id.py`, `update_telegram_url.py` — operational tools. `cloudflare_webhook_updater.py` updated. |
| **Code Quality** | 6/10 | **7/10** | ⬆️ +1 | 8 UI patch scripts + revert utility = systematic patching approach. `remove_jitter.py` for CSS cleanup. |

**V2 OVERALL: 6.5 / 10** (up from 5.6/10)

---

## P0 Status (Critical Issues)

| # | Issue (V1) | V2 Status | Notes |
|---|-----------|-----------|-------|
| 1 | **No Telegram auth** | ⚠️ **PARTIALLY FIXED** | `backend/auth.py` written + tested. **BUT `backend/main.py` does NOT import or apply `telegram_auth_guard()` to any route.** Auth is ready but not connected. |
| 2 | **CORS `*`** | ❌ **UNFIXED** | `backend/config.py` still defaults to `CORS_ORIGINS="*"`. `.env.example` still shows `"*"`. |
| 3 | **Browser WS memory leak** | ❌ **UNFIXED** | `websockets/browser.py` unchanged — new Playwright per connection. |
| 4 | **Kill endpoint no auth** | ❌ **UNFIXED** (blocked by #1) | Will be fixed when auth is wired. |
| 5 | **Shell injection in macros** | ❌ **UNFIXED** | `system.py:183` still uses `os.system()` with string interpolation. |

---

## New Findings

### Positive

1. **Auth Module (90% complete)**: `backend/auth.py` is well-written:
   - Proper HMAC-SHA256 per Telegram docs
   - `hmac.compare_digest()` for constant-time comparison (timing-attack safe)
   - `telegram_auth_guard()` as FastAPI dependency — reads `X-Telegram-Init-Data` header
   - Dev mode bypass when `TELEGRAM_BOT_TOKEN` is empty (logs warning)
   - `test_auth.py` covers: valid sig, invalid token, tampered payload, missing hash, empty payload, no user param, guard with valid/missing token, dev mode bypass

2. **UI Contract Tests**: `test_ui_contracts.py` validates HTML structure without browser:
   - Module overlay CSS has proper hidden/visible states
   - All overlays have `role="dialog"`, `aria-modal="true"`, `aria-hidden="true"` initially
   - No `maximum-scale=1` or `user-scalable=no` in viewport
   - Form controls have programmatic labels
   - HTML IDs are unique and markup is balanced
   - No `removeAttribute('onclick')` anti-pattern

3. **Watchdog**: `hermes_watchdog.py` is solid:
   - Health check across port fallback chain (9230→9220→9225→9255→9290→8080)
   - Auto-restart server if down
   - Trigger Cloudflare webhook sync after restart
   - Structured logging to `logs/watchdog.log`

4. **UI Patch System**: 8 `apply_*.py` scripts + `revert_ugly_patches.py` = systematic CSS/JS patching with rollback capability.

### Concerning

1. **Auth Not Wired**: The biggest issue. Auth is written, tested, and ready — but `backend/main.py` line 53-59 never imports `telegram_auth_guard`. This is like having a lock but leaving the door open. One line to fix:
```python
# In backend/main.py, add dependency to routers:
app.include_router(system.router, dependencies=[Depends(telegram_auth_guard)])
```

2. **CORS Still Open**: Until `.env` has `CORS_ORIGINS="https://<tunnel-url>"`, any origin can access the API with credentials.

3. **`scripts/apply_*.py` × 8**: Lots of UI patches being layered on a single HTML file. Risk of patch conflicts and maintenance hell. Consider splitting `index.html` instead.

---

## Complete File Inventory

### Backend (18 files)
| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `backend/main.py` | 67 | FastAPI app + lifespan + CORS + routers | ⚠️ No auth wired |
| `backend/auth.py` | 89 | Telegram initData HMAC-SHA256 verification | ✅ Ready, not wired |
| `backend/config.py` | 23 | `.env` config | ⚠️ CORS default `*` |
| `backend/routers/system.py` | 843 | 32+ system endpoints | ✅ Working, needs auth |
| `backend/routers/swarm.py` | 61 | Swarm REST | ✅ Clean |
| `backend/routers/audio.py` | 107 | Audio REST | ✅ Clean |
| `backend/services/swarm_manager.py` | 268 | Agent lifecycle | ✅ Solid |
| `backend/services/audio_engine.py` | 250 | VAD + STEM + intent | ✅ Functional |
| `backend/websockets/terminal.py` | 65 | pwsh.exe WS | ⚠️ No auth |
| `backend/websockets/browser.py` | 128 | Playwright stream | 🔴 Memory leak |
| `backend/websockets/swarm.py` | 65 | Telemetry broadcast | ✅ Good |
| `backend/websockets/audio.py` | 75 | PCM audio WS | ✅ Good |
| `backend/__init__.py` | — | Package marker | ✅ |
| `backend/routers/__init__.py` | — | Package marker | ✅ |
| `backend/services/__init__.py` | — | Package marker | ✅ |
| `backend/websockets/__init__.py` | — | Package marker | ✅ |
| `backend/bot_bridge.py` | — | Telegram polling | ✅ |

### Tests (12 files)
| File | Lines | Coverage |
|------|-------|----------|
| `tests/test_auth.py` | 134 | 10 tests — HMAC verify, guard, dev mode |
| `tests/test_system_api.py` | 291 | 20+ tests — REST, SSE, queue CRUD, FIM, workflow, obsidian |
| `tests/test_swarm_api.py` | 189 | 6 tests — REST + WS + defensive load |
| `tests/test_ui_contracts.py` | 221 | 6 tests — HTML structural validation |
| `tests/test_audio_api.py` | — | Audio REST + WS |
| `tests/test_bot_bridge.py` | — | Bot bridge logic |
| `tests/test_websockets_e2e.py` | 158 | 5 WS contract tests |
| `tests/test_empirical_stress.py` | — | Stress testing |
| `tests/test_queue_manager.py` | — | Queue operations |
| `tests/stress_harness.py` | — | Stress test framework |
| `tests/test_bridge.py` | — | Legacy bridge test |
| `tests/validate_n8n_async.js` | — | n8n template validator |

### Scripts (18 files)
| File | Purpose |
|------|---------|
| `scripts/hermes_watchdog.py` | Self-healing daemon |
| `scripts/aiogram_bridge.py` | Telegram ↔ n8n bridge |
| `scripts/queue_manager.py` | JSON queue + git auto-commit |
| `scripts/cloudflare_webhook_updater.py` | Cloudflare webhook sync |
| `scripts/n8n_telegram_hitl.py` | n8n HITL workflow |
| `scripts/cleanup_tasks.py` | Zombie process cleanup |
| `scripts/fix_tg.py` | Telegram URL fix |
| `scripts/fix_terminal_id.py` | Terminal ID fix |
| `scripts/update_telegram_url.py` | Telegram URL updater |
| `scripts/debug_ui.py` | UI debug helper |
| `scripts/apply_colorful_patch.py` | UI: colorful theme |
| `scripts/apply_magicui_patch.py` | UI: magic UI effects |
| `scripts/apply_mobile_patch.py` | UI: mobile responsive |
| `scripts/apply_premium_topology.py` | UI: topology effects |
| `scripts/apply_solid_patch.py` | UI: solid design |
| `scripts/apply_terminal_org_patch.py` | UI: terminal organization |
| `scripts/apply_topology_patch.py` | UI: topology |
| `scripts/apply_ux_patch.py` | UI: UX improvements |
| `scripts/revert_ugly_patches.py` | Revert all UI patches |
| `scripts/remove_jitter.py` | Remove CSS jitter |

### Frontend
| File | Lines | Notes |
|------|-------|-------|
| `static/index.html` | 4618 | 15 module overlays, OLED bento-box, dock nav |

---

## Minimum Viable Fix (1 Line)

To activate auth on all endpoints, add ONE line to `backend/main.py`:

```python
from backend.auth import telegram_auth_guard

# After app creation (line 39), add global dependency:
app = FastAPI(title="Hermes WebApp Backend", lifespan=lifespan, dependencies=[Depends(telegram_auth_guard)])
```

Or per-router:
```python
app.include_router(system.router, dependencies=[Depends(telegram_auth_guard)])
```

This makes `X-Telegram-Init-Data` header required on all endpoints. In dev mode (no token set), it bypasses with warning — so local dev still works.

---

## Next Steps

1. **Wire auth** — 1 line in `backend/main.py` (see above)
2. **Fix CORS** — set `CORS_ORIGINS` in `.env` to tunnel URL
3. **Test auth flow** — hit endpoint without header → 401, with valid header → 200
4. **Fix browser WS leak** — singleton Playwright pool
5. **Consider splitting `index.html`** — 4618 lines in one file is unmaintainable
