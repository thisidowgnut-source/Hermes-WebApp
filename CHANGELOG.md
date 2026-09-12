# Changelog (CHANGELOG.md)

All notable changes to the **Hermes OS & Doh-Nut Sovereign Mission Control** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.6.0] - 2026-09-12

### Added
- **FHS 3.0 Runtime Separation (`var/` & `tools/mcp/`)**:
  - Structured runtime directories: `var/log/` (telemetry/audit logs), `var/run/` (PID/locks), `var/lib/` (persistent app states), `var/spool/` (queues).
  - Isolated MCP installation assets and guides under `tools/mcp/`.
  - Refactored project root directory from 36 cluttered files down to 13 clean, essential files.
- **Divio 4-Quadrant Documentation Architecture**:
  - Organized documentation into Tutorials (`README.md`), How-To Guides (`docs/DEPLOYMENT.md`, `docs/TROUBLESHOOTING.md`), Reference (`docs/ARCHITECTURE.md`, `docs/API.md`, `docs/DESIGNS.md`, `docs/SECURITY.md`), and Explanation (`docs/PRD.md`, `docs/AGENTS.md`, `docs/SKILLS.md`).
  - Created centralized index hub at `docs/README.md`.
- **Emil Kowalski Craft Standard — Zero-Jitter Button Engine**:
  - Stripped `.glass` class from 52 interactive buttons/controls to prevent style inheritance conflicts with the physics engine.
  - Constrained `MagicBento` pointer-tracking to static cards only (`.card:not(button):not(.btn)`), eliminating magnetic jitter on hover.
  - Added tactile feedback: `:active { transform: scale(0.97); }` with snappy `100ms ease` transition.
  - Scoped hover effects inside `@media (hover: hover) and (pointer: fine)` to eliminate sticky hover states on touch devices.
- **Mobile-First Zero-Overlap Architecture**:
  - Implemented safe-area bottom clearance on `main`: `padding-bottom: calc(140px + env(safe-area-inset-bottom, 28px))`, ensuring bottom actions never collide with `#bottom-dock`.
  - Hardened flex layouts against collapse: `min-height: 180px; flex-shrink: 0; max-height: 240px` on streaming and log containers.
  - Responsive 3-column action launcher grid on mobile screens (`< 640px`) with `min-height: 52px` and `font-size: 10px`.
  - Added `padding-bottom: 36px` to all scrolling list containers (`.kanban-column-body`, catalog items, logs).

### Changed
- Refactored `static/index.html` CSS and JavaScript event listeners for buttons and card hover physics.
- Reorganized `docs/` folder structure: moved historical review/planning artifacts into `docs/archive/` and n8n blueprints into `docs/n8n/`.

### Fixed
- Fixed button hover vibration/jitter caused by `MagicBento` magnetic `translate(magnetX, magnetY)` conflicting with CSS transforms.
- Fixed layout overlap where bottom action buttons collided with the persistent dock on mobile viewports (390x844 iPhone 14 and 360x740 Android).
- Fixed flexbox collapse where `Agent Stream` shrunk to 0px height on small screens.

---

## [3.5.0] - 2026-09-12

### Added
- **Doh-Nut Sovereign Mission Control (`#mod-dohnut`)**:
  - Integrated full bakery operations dashboard: Financial KPIs (RM 1,420.50 revenue), 4-stage Kanban baking pipeline (Preparing, Frying, Glazing, Dispatch), and signature stock counters.
  - Added Omnichannel Social Autopilot tab linked to Chrome User Profile 50 (`thisisdohnut@gmail.com`) for 6 platforms (TikTok, Instagram, Threads, Facebook, X, YouTube).
  - Added 10 Google AI Labs fast-launchers (Mixboard, Stitch, Putty, Jules, Opal, AI Studio, NotebookLM, Flow, ChatGPT Plus, Labs Hub).
- **Backend Router `backend/routers/dohnut.py`**:
  - `GET /api/dohnut/stats`: Baking orders, catering count, batch status, signature stock.
  - `POST /api/dohnut/orders`: Add/update orders in 4-stage pipeline.
  - `POST /api/dohnut/social/generate`: AI multi-platform promotional copy generator.
  - `POST /api/dohnut/social/publish-webbridge`: 1-tap direct dispatch to GangNiaga WebBridge (port 10087).
  - `GET /api/dohnut/agent-swarm/status`: Telemetry for 4-node swarm (Hermes Conductor, Antigravity, WebBridge, Open Design).
  - `POST /api/dohnut/ai-labs/launch`: Focus or launch specific Google AI Labs tabs.
- **Pytest Suite `tests/test_dohnut_api.py`**:
  - 5/5 automated test cases verifying all Doh-Nut endpoints.

### Changed
- Expanded bottom dock to 16 modules with Doh-Nut Sovereign HQ as flagship item (`data-idx="16"`).
- Registered `dohnut_router` in `backend/main.py`.

---

## [3.4.0] - 2026-09-12

### Added
- **Chrome User Profile 50 Verification**:
  - Verified active social media sessions for `thisisdohnut@gmail.com` across TikTok, Instagram, Threads, Facebook, X, and YouTube.
- **GangNiaga WebBridge Integration**:
  - Connected WebApp to port 10087 for seamless CDP browser automation and 1-tap posting.

---

## [3.0.0] - 2026-07-27

### Added
- **Action-Oriented AI Agent HUD**:
  - Replaced passive CPU/RAM gauges with 6 1-Tap Action Launchers (`Audit & Fix`, `Run Pytest`, `Kill Zombies`, `Sync Vault`, `Spawn Swarm`, `Sync Tunnel`).
  - Added Direct Hermes AI Command Bar with neon styling.
- **Termux Hacker's Keyboard**:
  - Integrated dual-row mobile control keys (`ESC`, `TAB`, `CTRL+C`, `CTRL+Z`, `CTRL+L`, `|`, `/`, `~`, `\`, `&`, `>`, `$`).
- **Dynamic Fit-Screen Terminal**:
  - Auto-resizing xterm container adapting to viewport orientation changes.
- **Mobile Swipe-Back Support**:
  - Connected `history.pushState` and `window.onpopstate` for native back-gesture handling.

### Fixed
- CSS `.module-overlay` stuck z-index bug preventing clicks on dashboard elements.
- PTY ping character leakage into xterm terminal display.

---

## [2.1.0] - 2026-07-21
### Added
- **Omnichannel Content Engine:** Implemented asynchronous media generation via n8n (Wait Node pattern).
- **GitHub Shared-State (Staging Queue):** Decoupled n8n from heavy processing by introducing `queue.json` managed by `queue_manager.py` with automated Git commits.
- **Bot-to-Bot Loop Prevention:** Intercept and prevent infinite bot feedback loops in `aiogram_bridge.py` (`message.from_user.is_bot = true`).

## [2.0.0] - 2026-07-21
### Added
- **Hermes Vision:** Integrated Microsoft Playwright to stream headless Chromium directly via WebSockets as MJPEG frames. Supports remote mouse clicks and keypress injection.
- **Fullscreen Slide-Ups:** Terminal and Browser modules now trigger a `translateY(100%)` full-screen takeover, hiding all navigation for maximum workspace.
- **Native PowerShell Integration:** Shifted Terminal backend to `pwsh.exe -NoProfile` to support full Windows commands (like `ls`) natively.

### Changed
- **Aesthetic Overhaul (Anti-AI Slop + MagicBento):** Migrated to a strictly professional OLED aesthetic utilizing Pure Black (`#000`), Zinc (`#111`), Inter font, and Lucide SVG icons. Upgraded with Glassmorphism UI elements within a lock-fit Bento-box grid.
- **Layout Architecture:** Migrated to a strict 100vh lock-fit Bento-box grid with Glassmorphism for the Home and Monitor tabs, completely eliminating page scrolling within Telegram.

### Fixed
- **Network Blocking:** Abandoned `localtunnel` due to "Click to Continue" interstitial warnings breaking Telegram Web Apps. Adopted `Cloudflare Tunnels` for seamless reverse proxying.
- **URL Navigation Crashes:** Fixed a backend bug in Playwright where missing `http://` schemes would crash the entire browser socket.

## [1.0.0] - Initial Implementation
- Basic FastAPI backend setup.
- Initial HTML/JS dashboard with basic `localtunnel` exposure.
- Standard process telemetry and `cmd.exe` websocket terminal (deprecated).
