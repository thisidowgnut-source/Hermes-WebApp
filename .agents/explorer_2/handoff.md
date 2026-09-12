# Handoff Report — Frontend Architecture Investigation (`explorer_2`)

**Agent ID**: `explorer_2`  
**Folder**: `C:\Users\megat\Hermes-WebApp\.agents\explorer_2`  
**Target Project**: `C:\Users\megat\Hermes-WebApp`  
**Handoff Type**: Soft Handoff  
**Date**: 2026-07-23  

---

## 1. Observation

Direct observations from inspecting `C:\Users\megat\Hermes-WebApp`:
- **Static Directory Structure**: Contains a single self-contained application file: `static/index.html` (70,838 bytes, 1,665 lines).
- **Backend Entry Point & Routing**: `backend/main.py:50` mounts `/static` via `StaticFiles(directory=config.STATIC_DIR)`. `backend/main.py:57-59` serves `static/index.html` at root `/`.
- **UI Design System**:
  - Theme: Dark OLED aesthetic (`#000` background, `#120F17` gradients).
  - Cards: `.glass` class (`static/index.html:60–104`) with `backdrop-filter: blur(16px)`, `border: 1px solid rgba(255, 255, 255, 0.06)`, dynamic `--glow-x` / `--glow-y` spotlighting, 3D tilt, and floating particle simulation (`MagicBento` class at lines 1046–1139).
  - Background: Interactive particle dot canvas (`#dot-canvas`, `#dot-field-container`, lines 31–56 & 873–1041) with magnetic cursor bulge physics (`bulgeStrength = 67`).
  - Navigation: Mac OS-style bottom dock (`.dock-outer`, `.dock-panel`, `.dock-item`, lines 150–256 & 1338–1379`) with dynamic React-Bits-style mouse magnification (48px -> 75px radius).
- **Active Dashboard Widgets**:
  - Header with `RotatingText` rotator ("GANGNIAGA", "SUPREME", "SOVEREIGN"), system status dot (`#status-dot`), and Obsidian context badge (`#obsidian-badge`).
  - 3 SVG System Metrics Ring Gauges (`#cpu-ring`, `#ram-ring`, `#disk-ring`, lines 590–627).
  - Service Topology Map (`#topology-map`, lines 629–662) connecting Uvicorn, Cloudflare, Telegram, and n8n.
  - Agent Stream Log (`#agent-logs`, lines 664–678).
  - 4 Quick Macro Buttons (`clean_temp`, `lock_pc`, `cleanup_zombies`, `sync_webhook`, lines 680–706).
- **Active Module Overlays**:
  - `#mod-monitor`: Process manager table (`fetchProcesses()`, `/api/processes`, `/api/kill/{pid}`).
  - `#mod-terminal`: Root PowerShell shell connected to `/ws/terminal` using `xterm.js`.
  - `#mod-browser`: Remote Vision browser view streaming Playwright JPEG frames via `/ws/browser`.
  - `#mod-kanban`: Task board reading SQLite `kanban.db` via `/api/system/kanban`.
  - `#mod-files`: Interactive file manager connected to `/api/files?path=...`.
- **Active WebSocket Connections**:
  - `/ws/terminal`: Handled in `backend/websockets/terminal.py`. Client handler `initTerm()` (`static/index.html:1497-1524`).
  - `/ws/browser`: Handled in `backend/websockets/browser.py`. Client handler `initBrowser()` (`static/index.html:1541-1557`).

---

## 2. Logic Chain

1. **Premise**: The user requested a thorough read-only investigation of the frontend architecture of `Hermes-WebApp`, documentation of the current OLED Bento-box UI/themes/widgets/WebSockets, and integration plans for Swarm Control Panel UI and Voice Command Terminal & STEM Audio Visualizer UI.
2. **Analysis Step 1 (Static Inspection)**: `static/index.html` was verified as the sole frontend asset serving HTML, CSS, and JS. The CSS rules strictly implement dark OLED black (`#000`), glassmorphic backdrop blurs (`rgba(255,255,255,0.025)`), dynamic radial spotlights, 3D tilt magnetics, and bottom dock magnification.
3. **Analysis Step 2 (WebSocket & API Mapping)**: Active WebSockets `/ws/terminal` and `/ws/browser` use JSON message protocol with 15s ping/pong heartbeats and 3s auto-reconnect logic.
4. **Integration Synthesis (Swarm Control Panel)**:
   - Needs a main dashboard Bento Card (`#swarm-bento-card`) for high-level subagent metrics (active count, status indicators: `running`, `completed`, `failed`).
   - Needs a full-screen overlay module (`#mod-swarm`) (Dock index 6) containing a subagent spawner form (archetypes, prompt, target dir) and active agent matrix with sub-task progress and live streaming logs.
   - Communicates via `/ws/swarm` WebSocket and fallback `/api/swarm/*` REST routes.
5. **Integration Synthesis (Voice Terminal & STEM Audio)**:
   - Needs a header voice toggle badge (`#voice-toggle-badge`) with audio level meter.
   - Needs a full-screen overlay module (`#mod-audio`) (Dock index 7) featuring a WebAudio multi-stem spectrum/waveform canvas (`#stem-audio-canvas`), real-time speech transcript console (`#voice-transcript-box`), command auto-execute toggle, and audio controls.
   - Communicates via `/ws/audio` sending Int16 PCM audio buffers and receiving real-time STT transcripts and matched CLI commands.

---

## 3. Caveats

- **Read-Only Scope**: No backend or frontend code changes were made to `Hermes-WebApp` source files during this task.
- **Backend WebSocket Routes (`/ws/swarm`, `/ws/audio`)**: Backend handlers for `/ws/swarm` and `/ws/audio` are currently PLANNED in `PROJECT.md` and will need to be implemented by subsequent backend agents before full end-to-end WebSocket communication can be tested.
- **Microphone Permissions**: Voice Command audio streaming relies on browser `navigator.mediaDevices.getUserMedia({ audio: true })` API, which requires HTTPS or `localhost` context.

---

## 4. Conclusion

The frontend of `Hermes-WebApp` (`static/index.html`) is a sleek, highly responsive, single-page application built adhering strictly to the Anti-AI Slop OLED Bento-box specification. The architecture cleanly supports adding new Bento cards to `<main>` and new full-screen module overlays (`.module-overlay`) tied to the bottom dock (`.dock-panel`).

Integrating the **Swarm Control Panel UI** (`#swarm-bento-card` & `#mod-swarm`) and **Voice Command Terminal & STEM Audio Visualizer UI** (`#voice-toggle-badge` & `#mod-audio`) follows the established design patterns, WebAudio API standards, and WebSocket client initialization conventions.

Detailed findings, code structures, CSS rules, HTML snippets, and JavaScript integration scripts are documented in `C:\Users\megat\Hermes-WebApp\.agents\explorer_2\analysis.md`.

---

## 5. Verification Method

1. **Inspect Analysis Report**:
   - Read `C:\Users\megat\Hermes-WebApp\.agents\explorer_2\analysis.md`.
2. **Inspect Main Frontend File**:
   - View `C:\Users\megat\Hermes-WebApp\static\index.html`.
3. **Validate Element Selectors & Functions**:
   - Check lines 60–104 for `.glass` styling.
   - Check lines 150–256 for `.dock-panel` styling.
   - Check lines 1497–1524 for `initTerm()` and lines 1541–1557 for `initBrowser()`.
4. **Backend Route Inspection**:
   - Check `backend/main.py:50-59` and `backend/websockets/terminal.py` / `browser.py`.

---

## 6. Remaining Work (Soft Handoff Next Steps)

1. **Backend Integration (Implementer / Backend Agent)**:
   - Implement `backend/websockets/swarm.py` and router inclusion for `/ws/swarm`.
   - Implement `backend/websockets/audio.py` and STEM audio processing service for `/ws/audio`.
   - Implement REST endpoints `/api/swarm/agents`, `/api/swarm/spawn`, `/api/swarm/kill/{agent_id}` in `backend/routers/swarm.py`.
2. **Frontend Implementation (Implementer / Frontend Agent)**:
   - Insert `#swarm-bento-card` into `<main>` in `static/index.html`.
   - Add `#mod-swarm` full-screen module overlay and Dock item index 6 (`bot` icon).
   - Add `#voice-toggle-badge` to `<header>` in `static/index.html`.
   - Add `#mod-audio` full-screen module overlay and Dock item index 7 (`mic` icon).
   - Add WebAudio visualizer rendering loop `renderStemVisualizer()` and `/ws/audio` binary WebSocket handler.
3. **Testing & Verification (Tester Agent)**:
   - Run unit and integration tests using `pytest -v`.
   - Verify Uvicorn startup on port 9220.
