---
name: hermes-webapp-master
description: Use when developing, modifying, testing, or auditing the Hermes OS WebApp, including backend FastAPI routes, PTY WebSocket terminal, Browser Vision node, Telegram Mini App integration, Bento-Box action HUD, and Cloudflare tunnel webhooks.
---

# 🦅 Hermes OS WebApp Master Development & Architecture Skill

This skill defines the authoritative software engineering standards, architecture blueprints, terminal protocols, and verification loops for the **Hermes OS WebApp & Telegram Command Center**.

---

## 🏗️ 1. Architecture Blueprint & System Topology

The Hermes OS WebApp operates as a zero-latency, full-stack AI Command Center:

```
[ Telegram WebApp / Mobile Browser ]
               │
               ▼  (Cloudflare Tunnel / HTTPS / WSS)
[ FastAPI Backend (Port 9230 / 9220) ] ──► [ Local Brain (n8n / Ollama / Python) ]
    │                  │
    ├─ Static Engine   ├─ WebSockets PTY Stream (/ws/terminal)
    │  (index.html)    ├─ Browser Vision Stream (/ws/browser)
    │                  ├─ Realtime Telemetry (/ws/telemetry)
    │                  └─ Swarm Dispatcher (/ws/swarm)
    └─ REST APIs (/api/stats, /api/queue, /api/services, /api/obsidian, /api/workflows)
```

### Key File Locations:
- **Frontend SPA**: [static/index.html](file:///C:/Users/megat/Hermes-WebApp/static/index.html)
- **FastAPI Main**: [backend/main.py](file:///C:/Users/megat/Hermes-WebApp/backend/main.py)
- **Terminal PTY Handler**: [backend/websockets/terminal.py](file:///C:/Users/megat/Hermes-WebApp/backend/websockets/terminal.py)
- **Browser Vision Handler**: [backend/websockets/browser.py](file:///C:/Users/megat/Hermes-WebApp/backend/websockets/browser.py)
- **Automated Webhook Sync**: [scripts/cloudflare_webhook_updater.py](file:///C:/Users/megat/Hermes-WebApp/scripts/cloudflare_webhook_updater.py)
- **Pytest Verification Suite**: [tests/](file:///C:/Users/megat/Hermes-WebApp/tests/)

---

## 🎨 2. The Anti-AI Slop UI/UX Protocol

When modifying or adding components to the WebApp UI:

1. **Color Palette**: Pure OLED Black (`#000000`), Dark Glass Card (`rgba(17,17,17,0.85)`), Hairline Zinc Borders (`1px solid rgba(255,255,255,0.06)`). Neon accents: Sky Blue (`#38bdf8`), Cyber Purple (`#a855f7`), Emerald (`#34d399`), Rose (`#f43f5e`).
2. **Iconography**: **ZERO EMOJIS IN ACTION BUTTONS**. Use **Lucide Icons** exclusively (e.g. `<i data-lucide="terminal"></i>`).
3. **Full-Screen Overlays**: Overlays MUST use `.module-overlay` with explicit hidden state:
   ```css
   .module-overlay {
       position: fixed;
       inset: 0;
       background: #000;
       z-index: 100;
       transform: translateY(100%);
       opacity: 0;
       pointer-events: none;
       transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.3s ease;
       visibility: hidden;
   }
   .module-overlay.active {
       transform: translateY(0);
       opacity: 1;
       pointer-events: auto;
       visibility: visible;
   }
   ```

---

## 📟 3. Terminal PTY & Termux Hacker's Keyboard Protocol

### A. PTY WebSocket Heartbeat Hygiene
- **Rule**: WebSockets serving terminal text streams **MUST NOT** send text JSON strings like `{"type": "ping"}` using `send_text()`.
- **Backend Fix**: Use binary ping frames `websocket.send_bytes(b"\x09")`.
- **Frontend Protection**:
  ```javascript
  termWs.onmessage = (e) => {
      if (typeof e.data === 'string' && (e.data.includes('"ping"') || e.data.includes('"pong"'))) return;
      xterm.write(e.data);
  };
  ```

### B. Termux Hacker's Keyboard Layout
Every terminal view MUST feature the 2-row Cyberpunk touch toolbar:
- **Row 1**: `ESC`, `TAB`, `CTRL+C`, `CTRL+Z`, `CTRL+L`, `▲ UP`, `▼ DOWN`, `◄ LEFT`, `► RIGHT`, `HOME`, `END`, `CLEAR`.
- **Row 2**: `|`, `/`, `-`, `~`, `\`, `&`, `>`, `$`, `*`, `"`.

### C. Dynamic Fit-Screen Auto-Scaling (`fitXtermContainer`)
Recalculate xterm columns and rows on module launch and window resize:
```javascript
function fitXtermContainer() {
    if (!xterm) return;
    const container = document.getElementById('terminal-inner');
    if (!container) return;
    const rect = container.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) return;
    const cols = Math.max(30, Math.floor((rect.width - 16) / 7.2));
    const rows = Math.max(10, Math.floor((rect.height - 12) / 15));
    try { xterm.resize(cols, rows); } catch(e) {}
}
```

---

## 📱 4. Mobile Back Swipe & Browser Popstate Integration

Modal overlays in Single Page Apps MUST register browser history states so mobile swipe-back gestures close active overlays cleanly:

```javascript
function openModule(modId) {
    closeAllModules();
    const el = document.getElementById('mod-' + modId);
    if (!el) return;
    el.classList.add('active');
    el.setAttribute('aria-hidden', 'false');
    history.pushState({ module: modId }, '', '#' + modId);
}

window.addEventListener('popstate', (e) => {
    const activeOverlays = document.querySelectorAll('.module-overlay.active');
    if (activeOverlays.length > 0) {
        closeAllModules();
    }
});
```

---

## 🌐 5. Vision Node (Browser Use) Standards

1. **Preset URL Quick Chips**: Provide 1-tap navigation buttons (`🌐 Google`, `🐙 GitHub`, `🦅 Hermes API`, `🤖 Ollama API`).
2. **Non-Blocking Control Overlay**: Use floating top pill badges (`● MANUAL CONTROL ACTIVE` with `pointer-events: none`) so the live browser image is never obscured.
3. **Mobile Touch Coordinate Mapping**:
   ```javascript
   function sendBrowserClick(clientX, clientY, targetEl) {
       if (!isHumanControlling) return;
       const rect = targetEl.getBoundingClientRect();
       const x = (clientX - rect.left) * (1024 / rect.width);
       const y = (clientY - rect.top) * (768 / rect.height);
       if (browserWs && browserWs.readyState === 1) {
           browserWs.send(JSON.stringify({ type: 'click', x, y }));
       }
   }
   ```

---

## 🧪 6. Empirical Verification Loop (Mandatory)

Before claiming any task or edit complete, execute the two-phase verification:

1. **Backend & Contract Test Suite**:
   ```powershell
   C:\Users\megat\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe -m pytest tests/
   ```
   *Requirement*: 100% Pass Rate (84/84 tests passed).

2. **Visual & UI DOM Verification**:
   Use `chrome-devtools` MCP to evaluate scripts (`openModule(...)`) and take screenshots in mobile viewport (390x844px) to ensure zero layout overflow.
