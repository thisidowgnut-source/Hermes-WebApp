# Comprehensive Frontend Architecture & Integration Analysis: Hermes-WebApp

**Agent**: `explorer_2`  
**Location**: `C:\Users\megat\Hermes-WebApp\.agents\explorer_2`  
**Date**: 2026-07-23  
**Target Codebase**: `C:\Users\megat\Hermes-WebApp`  

---

## Executive Summary

This report provides a thorough, read-only architectural investigation of the frontend of `Hermes-WebApp`. `Hermes-WebApp` features a high-performance, single-page web interface (`static/index.html`) engineered strictly according to the **Anti-AI Slop OLED Bento-box Protocol**. It integrates real-time WebSockets, glassmorphic UI components, dynamic dot-field canvas physics, interactive Mac OS dock magnification, and full-screen module overlays.

This document details:
1. The exact layout and structure of the `static/` directory.
2. Complete documentation of UI themes, CSS rules, active widgets, and existing WebSocket clients (`/ws/terminal`, `/ws/browser`).
3. Concrete integration designs for:
   - **Swarm Control Panel UI Widget**: Multi-agent spawner, status indicators, live telemetry grid, and full-screen overlay matching the OLED Bento-box aesthetic.
   - **Voice Command Terminal UI & STEM Audio Visualizer**: WebAudio multi-stem frequency spectrum display, real-time speech transcript console, and bidirectional WebSocket client connected to `/ws/audio`.

---

## 1. Static Directory & Codebase Layout Audit

### 1.1 Directory Structure
The frontend is structured as a **single-file web application** located in `static/`:
```
C:\Users\megat\Hermes-WebApp\static\
└── index.html (70,838 bytes | 1,665 lines)
```

### 1.2 CDN Dependency Footprint
`static/index.html` leverages external CDNs for fonts, icons, terminal rendering, and Telegram integration:
- **Telegram WebApp SDK**: `<script src="https://telegram.org/js/telegram-web-app.js"></script>` (Line 7)
- **Typography**: `<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">` (Line 8)
- **Icons**: `<script src="https://unpkg.com/lucide@latest"></script>` (Line 9)
- **Terminal Emulator**: `<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.css" />` & `<script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.js"></script>` (Lines 10–11)

### 1.3 Backend Mounting & Routing
In `backend/main.py`:
- Static directory mounted: `app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")` (`backend/main.py:50`)
- Serves `static/index.html` as root route: `@app.get("/") -> FileResponse(os.path.join(config.STATIC_DIR, "index.html"))` (`backend/main.py:57-59`)

---

## 2. Current UI Architecture & Design System

### 2.1 Color Palette & OLED Theme
- **Base Background**: `#000` (Pure OLED Black) (`index.html:16`)
- **Text & Foreground**: `#e0e0e0` (Light Gray), `#fff` (Pure White Headers)
- **Glass Card Fill**: `rgba(255, 255, 255, 0.025)` (`index.html:61`)
- **Glass Border**: `1px solid rgba(255, 255, 255, 0.06)` (`index.html:64`)
- **Accent Colors**:
  - Purple Glow: `rgb(168, 85, 247)` / `#9333ea`
  - Active Green: `#4ade80` / `#50fa7b`
  - Warning/Amber: `#ffb86c`
  - Danger/Kill Red: `#ef4444` / `#ff5555`
  - Pink Accent: `#ff79c6`
  - Cyan Accent: `#8be9fd`

### 2.2 CSS Component Rules

#### A. Glassmorphic Bento Cards (`.glass`) (`index.html:60–104`)
```css
.glass {
    background: rgba(255, 255, 255, 0.025);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 1rem;
    position: relative;
    overflow: hidden; 
    transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease, border-color 0.3s ease;
    --glow-x: 50%; --glow-y: 50%; --glow-intensity: 0; --glow-radius: 200px; --glow-color: 168, 85, 247;
}
```
- **Spotlight & Border Gradient**: Radial pseudo-element `::after` (`index.html:85-104`) dynamically positioned via CSS variables `--glow-x` and `--glow-y`.
- **Interactive 3D Tilt & Magnetic Physics**: Handled by JavaScript class `MagicBento` (`index.html:1046-1139`), calculating cursor offset to tilt cards via `perspective(1000px) rotateX(...) rotateY(...) translate(...)`.
- **Particle System**: Spawns floating particles (`.bento-particle`) inside `.particle-container` on card hover.

#### B. Dot Field Background Canvas (`#dot-field-container`) (`index.html:31-56, 873-1041`)
- Renders an interactive 2D canvas particle grid with cursor bulge distortion physics (`bulgeStrength = 67`, `cursorRadius = 500`) and an SVG radial glow element (`#dot-glow`).

#### C. Mac OS-Style Bottom Dock (`.dock-outer`, `.dock-panel`, `.dock-item`) (`index.html:150-256, 1338-1379`)
- Floating glass navigation container (`background: rgba(18, 15, 23, 0.75)`, `backdrop-filter: blur(16px)`).
- Mouse distance-based magnification (`initDock()` JS function), smoothly expanding items from `48px` to up to `75px` in real time.
- Displays tooltips (`.dock-label`) and glowing active indicators (`.glow-indicator`).

#### D. Full-Screen Module Overlays (`.module-overlay`) (`index.html:387-417`)
```css
.module-overlay {
    position: fixed; inset: 0; background: #000; z-index: 50;
    transform: translateY(100%); transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
    display: flex; flex-direction: column;
}
.module-overlay.active { transform: translateY(0); }
```

---

### 2.3 Active Widgets & Sections

#### Main View Container (`<main>`) (`index.html:562-707`)
1. **Header Bar**:
   - `RotatingText` animation swapping titles ("GANGNIAGA", "SUPREME", "SOVEREIGN") (`index.html:567-570, 1144-1239`).
   - System Status Indicator Dot (`#status-dot`) & Text (`#status-text`).
   - Obsidian Context Badge (`#obsidian-badge`): Displays active note title fetched via `/api/system/obsidian-context`.
2. **System Metrics Ring Gauges**:
   - 3 SVG ring gauges (`#cpu-ring`, `#ram-ring`, `#disk-ring`) showing live CPU, RAM, and Disk C usage percentages fetched via `/api/stats` (`index.html:590-627, 1384-1402`).
3. **Service Topology Map**:
   - Interactive node graph representing 4 system services: API (Uvicorn), Tunnel (Cloudflare), Bot (Telegram), and n8n (`index.html:629-662`).
4. **Agent Stream Log**:
   - Live stream log box (`#agent-logs`) rendering transcript logs from `/api/logs` with safe HTML escaping (`index.html:664-678, 1407-1419`).
5. **Quick Actions Command Grid**:
   - 4 glass macro buttons triggering `/api/macro/{macro_name}`:
     - `clean_temp`: Deletes temporary files.
     - `lock_pc`: Locks Windows workstation.
     - `cleanup_zombies`: Executes `cleanup_tasks.py`.
     - `sync_webhook`: Executes `cloudflare_webhook_updater.py`.

#### Dock Navigation & Module Overlays (`index.html:709-847, 1257-1335`)
- **Dock Index 0 (Home)**: Resets active modules (`goHome()`).
- **Dock Index 1 (Monitor / `#mod-monitor`)**: Lists top system processes via `/api/processes` with PID kill action (`killProcess(pid)`). Integrates Telegram Native `MainButton`.
- **Dock Index 2 (Shell / `#mod-terminal`)**: Interactive root PowerShell shell connected to `/ws/terminal` rendered with `xterm.js`.
- **Dock Index 3 (Vision / `#mod-browser`)**: Remote browser viewport streaming Playwright JPEG frames via `/ws/browser` with manual interactive takeover mode.
- **Dock Index 4 (Kanban / `#mod-kanban`)**: Reads tasks from `kanban.db` via `/api/system/kanban`.
- **Dock Index 5 (Files / `#mod-files`)**: Filesystem browser via `/api/files?path=...`.

---

## 3. Frontend WebSocket Connections Audit

Currently implemented in `static/index.html`:

### 3.1 Terminal WebSocket Client (`/ws/terminal`)
- **Backend Route**: `backend/websockets/terminal.py`
- **Frontend Function**: `initTerm()` (`index.html:1497-1524`)
- **Behavior & Protocol**:
  - Connects using `wss://` (or `ws://`).
  - Initializes `xterm.js` instance into `#terminal-inner`.
  - Bidirectional communication: Sends keystrokes/commands + `\r\n`; receives terminal output string buffer.
  - Heartbeat: Handles `{"type": "ping"}` / `{"type": "pong"}` every 15 seconds.
  - Auto-reconnect: Triggers reconnect after 3 seconds on websocket closure (`termWs.onclose`).

### 3.2 Browser Vision WebSocket Client (`/ws/browser`)
- **Backend Route**: `backend/websockets/browser.py`
- **Frontend Function**: `initBrowser()` (`index.html:1541-1557`)
- **Behavior & Protocol**:
  - Receives screen frames: `{"type": "frame", "data": "<base64_jpeg>"}`.
  - Sends user interaction commands:
    - Navigation: `{"type": "goto", "url": "..."}`
    - Mouse Click: `{"type": "click", "x": <px>, "y": <px>}` (scaled to 1024x768)
    - Keyboard Type: `{"type": "type", "text": "..."}` / `{"type": "keydown", "key": "..."}`
  - Heartbeat & Auto-reconnect: Ping/pong every 15s; auto-reconnects every 3s.

---

## 4. Swarm Control Panel UI Integration Architecture

### 4.1 UI Design & Placement Strategy

#### A. Main View Bento Card (`#swarm-bento-card`)
Placed on the main dashboard (`<main>`) between Service Topology and Agent Stream Log:
```html
<!-- SWARM CONTROL PANEL BENTO CARD -->
<div class="glass" id="swarm-bento-card" style="padding: 16px; flex-shrink: 0;">
    <div class="glass-spotlight"></div>
    <div class="particle-container"></div>
    <div style="position: relative; z-index: 2; display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <div style="display: flex; align-items: center; gap: 6px;">
            <i data-lucide="bot" style="width: 12px; height: 12px; color: #8be9fd;"></i>
            <span style="font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: rgba(255,255,255,0.4);">Swarm Control Grid</span>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
            <span id="swarm-active-badge" style="background: rgba(80, 250, 123, 0.15); border: 1px solid rgba(80, 250, 123, 0.3); color: #50fa7b; font-size: 8px; font-weight: 700; padding: 2px 6px; border-radius: 4px;">0 Active</span>
            <button onclick="openModule('swarm', document.querySelector('.dock-item[data-idx=\'6\']'))" class="btn-action" style="padding: 4px 8px; font-size: 8px;">Open Panel</button>
        </div>
    </div>
    <!-- Mini Agent Grid Summary -->
    <div id="swarm-mini-grid" style="position: relative; z-index: 2; display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px;">
        <div style="text-align: center; color: rgba(255,255,255,0.25); font-size: 10px; padding: 12px;">No background agents running</div>
    </div>
</div>
```

#### B. Full-Screen Module Overlay (`#mod-swarm`)
Added as a dedicated overlay module (Dock index 6):
- **Left Column (Spawner Console)**:
  - Input: Task prompt textarea (`#swarm-prompt-input`).
  - Selector: Agent Archetype (`generalist`, `codebase_investigator`, `file_master`, `researcher`).
  - Target Directory: `C:\Users\megat\Hermes-WebApp`.
  - Button: `[⚡ SPAWN AGENT]` (`POST /api/swarm/spawn`).
- **Right Column (Live Agent Matrix)**:
  - Grid of active agent cards showing:
    - Agent ID, Archetype badge, Task summary.
    - Status indicators: `RUNNING` (glowing green dot), `IDLE` (yellow), `COMPLETED` (purple), `FAILED` (red).
    - Real-time task progress bar.
    - Live streaming log output drawer.
    - Control buttons: `Pause`, `Delegate Subtask`, `Kill Agent`.
- **Bottom Bar**: `[EMERGENCY STOP ALL SWARM AGENTS]`.

### 4.2 CSS Rules & Status Styling
```css
/* Swarm UI Extensions */
.swarm-agent-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.status-pill {
    font-size: 8px; font-weight: 800; text-transform: uppercase;
    letter-spacing: 0.08em; padding: 2px 6px; border-radius: 4px;
}
.status-pill.running { background: rgba(80, 250, 123, 0.2); color: #50fa7b; border: 1px solid rgba(80, 250, 123, 0.4); }
.status-pill.completed { background: rgba(189, 147, 249, 0.2); color: #bd93f9; border: 1px solid rgba(189, 147, 249, 0.4); }
.status-pill.failed { background: rgba(255, 85, 85, 0.2); color: #ff5555; border: 1px solid rgba(255, 85, 85, 0.4); }
```

### 4.3 WebSocket & REST Communication
- **REST Endpoints**:
  - `GET /api/swarm/agents`: Returns JSON list of all active/past swarm agents.
  - `POST /api/swarm/spawn`: Triggers background agent process.
  - `POST /api/swarm/kill/{agent_id}`: Kills specific agent process.
- **WebSocket Protocol (`/ws/swarm`)**:
  - Client connects via `initSwarmWs()`.
  - Inbound Server Messages:
    - `{"type": "agent_spawned", "agent": {"id": "agent-1", "archetype": "codebase_investigator", "status": "running"}}`
    - `{"type": "agent_status", "agent_id": "agent-1", "status": "completed", "progress": 100}`
    - `{"type": "agent_log", "agent_id": "agent-1", "log": "Completed analysis of static/index.html"}`

---

## 5. Voice Command Terminal & STEM Audio Visualizer Integration Architecture

### 5.1 UI Design & Placement Strategy

#### A. Header Voice Toggle Badge (`#voice-toggle-badge`)
Placed in the top right header area near `#obsidian-badge`:
```html
<button id="voice-toggle-badge" onclick="toggleVoiceListening()" class="btn-action" style="padding: 4px 10px; font-size: 8px; border-color: rgba(80, 250, 123, 0.3); background: rgba(80, 250, 123, 0.1); color: #50fa7b;">
    <i data-lucide="mic" id="voice-mic-icon" style="width: 10px; height: 10px;"></i>
    <span id="voice-status-text">Voice Idle</span>
</button>
```

#### B. Full-Screen Module Overlay (`#mod-audio`)
Dedicated audio module accessible via Dock (item index 7) or by clicking `#voice-toggle-badge`:
- **Top Section (STEM Audio Visualizer Canvas)**:
  - Multi-stem audio spectrum / waveform canvas (`#stem-audio-canvas`, `height: 220px`).
  - WebAudio API integration using `AudioContext` and 4 distinct `AnalyserNode` channels:
    1. **Master Stream** (Cyan `#00f3ff`): Total input audio.
    2. **Voice STEM** (Green `#50fa7b`): Filtered vocal frequency band (300Hz–3.4kHz).
    3. **Noise STEM** (Purple `#bd93f9`): High/Low ambient noise frequencies.
    4. **Output Synthesis STEM** (Amber `#ffb86c`): Agent voice response playback audio.
  - Visualizer modes: Frequency Spectrum Bars, Oscilloscope Waveform, Circular Neon Reactive Ring.
- **Middle Section (Voice Command Console)**:
  - Speech-to-Text Live Transcript Box (`#voice-transcript-box`): Displays streaming recognized speech text real-time.
  - Command Parsing Card: Displays matched Voice CLI command (e.g. `[MATCHED COMMAND] -> triggerMacro('clean_temp')`).
  - Auto-Execution Toggle Switch: "Execute Automatically" vs "Require Touch Confirmation".
- **Bottom Section (Audio Device & STEM Controls)**:
  - Microphone selector dropdown (`#audio-input-select`).
  - Sensitivity Gain Slider (`#audio-gain-slider`).
  - STEM Noise Suppression Toggle (`#stem-noise-toggle`).
  - Quick Mute Button (`#audio-mute-btn`).

### 5.2 Client Audio Capture & WebSocket (`/ws/audio`)

#### Client-Side WebAudio Capture Pipeline:
```javascript
let audioCtx = null, mediaStream = null, audioWs = null, analyserNodes = {};

async function startAudioCapture() {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    
    const source = audioCtx.createMediaStreamSource(mediaStream);
    
    // Create Analyser Nodes for STEM Visualization
    analyserNodes.master = audioCtx.createAnalyser();
    analyserNodes.master.fftSize = 256;
    source.connect(analyserNodes.master);

    // Initialize /ws/audio WebSocket
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    audioWs = new WebSocket(`${proto}://${location.host}/ws/audio`);
    audioWs.binaryType = 'arraybuffer';

    audioWs.onopen = () => {
        // Send initial handshake configuration
        audioWs.send(JSON.stringify({ type: 'start_stream', sampleRate: audioCtx.sampleRate }));
    };

    audioWs.onmessage = (e) => {
        if (typeof e.data === 'string') {
            const msg = JSON.parse(e.data);
            if (msg.type === 'transcript') {
                document.getElementById('voice-transcript-box').textContent = msg.text;
            } else if (msg.type === 'cmd_matched') {
                handleVoiceCommand(msg.command);
            }
        }
    };

    // ScriptProcessorNode / AudioWorklet for sending PCM chunks to /ws/audio
    const processor = audioCtx.createScriptProcessor(4096, 1, 1);
    source.connect(processor);
    processor.connect(audioCtx.destination);
    
    processor.onaudioprocess = (e) => {
        if (audioWs && audioWs.readyState === WebSocket.OPEN) {
            const inputData = e.inputBuffer.getChannelData(0);
            // Convert Float32 to Int16 PCM array buffer
            const pcm16 = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
                pcm16[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF;
            }
            audioWs.send(pcm16.buffer);
        }
    };

    // Start 60fps Visualizer Animation Loop
    renderStemVisualizer();
}
```

---

## 6. Comprehensive Implementation Guidelines for Implementers

When modifying `static/index.html` to add these integrations, implementers MUST follow these strict rules:

1. **Preserve Embedded Structure**:
   - Keep `static/index.html` self-contained unless a modular JS/CSS refactoring strategy is explicitly mandated by project leads.
   - Do NOT modify existing global canvas background scripts (`initDotField`), `MagicBento` tilt physics, or `RotatingText` rotator.

2. **Dock Index & Icon Sync**:
   - Increment dock item indices cleanly:
     - Index 0: Home
     - Index 1: Monitor (`#mod-monitor`)
     - Index 2: Shell (`#mod-terminal`)
     - Index 3: Vision (`#mod-browser`)
     - Index 4: Kanban (`#mod-kanban`)
     - Index 5: Files (`#mod-files`)
     - Index 6: Swarm (`#mod-swarm`) *(New)*
     - Index 7: Audio (`#mod-audio`) *(New)*
   - Ensure `lucide.createIcons()` is called after rendering new dynamic HTML cards or module overlays.

3. **WebSocket Error Handling & Heartbeat Hygiene**:
   - Implement `ping`/`pong` heartbeat loops every 15s in all new WebSocket connections (`/ws/swarm` and `/ws/audio`).
   - Implement graceful exponential backoff or 3-second auto-reconnection timeouts (`onclose`) matching `initTerm()` and `initBrowser()`.

4. **Telegram WebApp SDK Compatibility**:
   - Ensure `haptic('light')` / `haptic('medium')` / `haptic('heavy')` calls are triggered on user taps.
   - Update `tg.BackButton` and `tg.MainButton` handlers in `openModule()` for the new Swarm (`#mod-swarm`) and Audio (`#mod-audio`) modules.

---

## 7. Verification Method

To independently verify the frontend architecture findings:
1. Open `static/index.html` in any browser or Telegram WebApp test harness.
2. Inspect DOM element IDs: `#dot-canvas`, `#title-rotator`, `#obsidian-badge`, `#cpu-ring`, `#agent-logs`, `#mod-terminal`, `#mod-browser`.
3. Test WebSocket connection initialization in Browser DevTools Console:
   - `const wsTerm = new WebSocket('ws://localhost:9220/ws/terminal');`
   - `const wsBrowser = new WebSocket('ws://localhost:9220/ws/browser');`
4. Confirm styling rules against `PROJECT.md` and `C:\GEMINI.md` Anti-AI Slop OLED Bento-box specifications.

---
