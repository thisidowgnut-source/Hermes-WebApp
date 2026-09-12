# REST & WebSocket API Contract (API.md)

This document outlines the API surface for the Hermes OS WebApp. Autonomous agents can hit these endpoints directly instead of parsing the UI.

## 1. REST Endpoints (Base: `http://127.0.0.1:9220`)

### `GET /api/stats`
Returns instantaneous system hardware telemetry.
**Response:**
```json
{
  "cpu": 12.5,
  "ram": 45.2,
  "disk": 29.7
}
```

### `GET /api/processes`
Returns a list of the top active processes sorted by memory consumption.
**Response:**
```json
[
  { "pid": 10424, "name": "chrome.exe", "memory_mb": 450.2 },
  { "pid": 532, "name": "pwsh.exe", "memory_mb": 120.1 }
]
```

### `POST /api/kill/{pid}`
Forcefully terminates a process by its ID.
**Response:** `{"status": "success", "message": "Process 10424 killed"}`

### `POST /api/macro/{macro_name}`
Executes predefined host shell scripts.
- Valid macros: `clean_temp`, `lock_pc`, `restart_explorer`
**Response:** `{"status": "success", "output": "..."}`

---

## 2. WebSocket Endpoints

### `WS /ws/terminal`
Provides raw bidirectional I/O to a `pwsh.exe` subprocess.
- **Client -> Server:** Raw string inputs (e.g., `"ls\r"`).
- **Server -> Client:** Raw stdout/stderr strings (includes ANSI color codes).

### `WS /ws/browser`
Streams Playwright frame data and accepts remote input events.
- **Server -> Client:**
  ```json
  {"frame": "data:image/jpeg;base64,...(base64 string)..."}
  ```
- **Client -> Server (Click Event):**
  ```json
  {"type": "click", "x": 512, "y": 384}
  ```
- **Client -> Server (Keyboard Event):**
  ```json
  {"type": "keypress", "key": "Enter"}
  ```
