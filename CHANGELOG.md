# Changelog (CHANGELOG.md)

All notable changes to this project will be documented in this file.

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
