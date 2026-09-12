# Test Suite and Verification Environment Analysis

**Target Project**: Hermes-WebApp (`C:\Users\megat\Hermes-WebApp`)  
**Investigator**: `explorer_3`  
**Date**: 2026-07-23  

---

## 1. Executive Summary

A comprehensive, read-only investigation of the test suite, test configuration, Uvicorn server launcher, and WebSocket setup for **Hermes-WebApp** was conducted.

Key takeaways:
- **Baseline Test Execution**: Running `pytest -v` collected **32 test cases** across 5 test modules. The result was **31 PASSED, 0 FAILED, 1 ERROR**, with 2 cache warnings.
- **Root Cause of Setup Error**: `tests/test_system_api.py::test_get_obsidian_context_mocked` errored during fixture setup due to a Windows `PermissionError: [WinError 5] Access is denied` when pytest attempted to create a temp folder via the standard `tmp_path` fixture in `C:\Users\megat\AppData\Local\Temp\pytest-of-megat`.
- **Uvicorn Launch Configuration**: Hermes-WebApp defaults to `127.0.0.1:9220` configured via `backend/config.py` (`PORT = int(os.getenv("PORT", 9220))`). Both root `main.py` and `backend/main.py` support entry via Uvicorn.
- **WebSocket Route Audit**: `/ws/terminal` (pwsh sub-process) and `/ws/browser` (Playwright Chromium 5 FPS streaming) are fully implemented in `backend/websockets/`. `/ws/audio` is currently **unimplemented** (planned for Expansion Milestone 4 in `PROJECT.md`).
- **WebSocket Test Coverage Gap**: No unit or integration tests currently exist for any WebSocket endpoints (`/ws/terminal`, `/ws/browser`, `/ws/audio`).

---

## 2. Test Suite Infrastructure & Configuration

### 2.1 Directory Layout & Test Modules

| Test File | Target Module | Test Count | Scope |
| :--- | :--- | :---: | :--- |
| `tests/test_auth.py` | `backend/auth.py` | 9 | Telegram HMAC-SHA256 initData validation & auth guard |
| `tests/test_bot_bridge.py` | `backend/bot_bridge.py` | 7 | Aiogram bot bridge, polling lifecycle, loop prevention |
| `tests/test_bridge.py` | `scripts/aiogram_bridge.py` | 2 | Script bridge message handler & bot-to-bot loop check |
| `tests/test_queue_manager.py` | `scripts/queue_manager.py` | 4 | File-backed JSON task queue CRUD & corrupted backup recovery |
| `tests/test_system_api.py` | `backend/routers/system.py` | 10 | FastAPI REST system endpoints, stats, telemetry SSE, queue API |

### 2.2 `conftest.py` Setup
Located at `C:\Users\megat\Hermes-WebApp\conftest.py`:
```python
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
```
This minimal setup injects the root directory `C:\Users\megat\Hermes-WebApp` into Python's `sys.path`, allowing test files inside `tests/` to import `backend` and `scripts` directly without installation.

### 2.3 Fixtures & Utilities
- **FastAPI `TestClient`**: `tests/test_system_api.py` instantiates `TestClient(app)` to test HTTP GET/POST/DELETE routes and Server-Sent Events (`/api/stream/telemetry`).
- **Queue State Cleanup (`setup_teardown_queue`)**: `test_system_api.py` utilizes an `autouse=True` fixture that backs up `QUEUE_FILE` (`.queue/queue.json`), writes pre-defined test jobs, and restores original contents on teardown.
- **Custom Local Temp Directory (`tmp_path_local`)**: `test_queue_manager.py` defines a custom fixture pointing to `BASE_DIR/.pytest_tmp/queue_tests`. This design avoids host OS `%TEMP%` permission issues.

---

## 3. Baseline Pytest Run Analysis (`pytest -v`)

### 3.1 Test Results Inventory

```
tests/test_auth.py::test_verify_telegram_init_data_valid_signature PASSED
tests/test_auth.py::test_verify_telegram_init_data_invalid_bot_token PASSED
tests/test_auth.py::test_verify_telegram_init_data_tampered_payload PASSED
tests/test_auth.py::test_verify_telegram_init_data_missing_hash PASSED
tests/test_auth.py::test_verify_telegram_init_data_empty_payload PASSED
tests/test_auth.py::test_verify_telegram_init_data_no_user_param PASSED
tests/test_auth.py::test_telegram_auth_guard_with_valid_token PASSED
tests/test_auth.py::test_telegram_auth_guard_missing_header_when_token_configured PASSED
tests/test_auth.py::test_telegram_auth_guard_dev_mode_bypass PASSED
tests/test_bot_bridge.py::test_init_bot_bridge_success PASSED
tests/test_bot_bridge.py::test_init_bot_bridge_missing_token PASSED
tests/test_bot_bridge.py::test_cmd_start_bot_to_bot_loop_prevention PASSED
tests/test_bot_bridge.py::test_cmd_start_human_user_allowed PASSED
tests/test_bot_bridge.py::test_forward_to_n8n_loop_prevention PASSED
tests/test_bot_bridge.py::test_forward_to_n8n_human_allowed PASSED
tests/test_bot_bridge.py::test_start_and_stop_bot_polling PASSED
tests/test_bridge.py::test_bot_to_bot_loop_prevention PASSED
tests/test_bridge.py::test_human_allowed PASSED
tests/test_queue_manager.py::test_add_to_queue PASSED
tests/test_queue_manager.py::test_add_to_queue_append PASSED
tests/test_queue_manager.py::test_corrupted_queue_backup PASSED
tests/test_queue_manager.py::test_relative_paths PASSED
tests/test_system_api.py::test_get_stats PASSED
tests/test_system_api.py::test_get_queue PASSED
tests/test_system_api.py::test_delete_queue_item_by_id PASSED
tests/test_system_api.py::test_delete_queue_item_by_index PASSED
tests/test_system_api.py::test_delete_queue_item_not_found PASSED
tests/test_system_api.py::test_clear_queue PASSED
tests/test_system_api.py::test_stream_telemetry PASSED
tests/test_system_api.py::test_get_obsidian_context PASSED
tests/test_system_api.py::test_get_obsidian_context_mocked ERROR
tests/test_system_api.py::test_get_kanban_tasks PASSED
```

### 3.2 Failure / Error Analysis

#### 1. Setup ERROR: `test_get_obsidian_context_mocked`
- **Error Stack**:
  ```
  PermissionError: [WinError 5] Access is denied: 'C:\\Users\\megat\\AppData\\Local\\Temp\\pytest-of-megat'
  ```
- **Cause**: Pytest's standard built-in `tmp_path` fixture attempts to create a temporary directory inside `AppData\Local\Temp\pytest-of-megat`. Windows file lock / permission policies on the host environment block directory creation under `AppData\Local\Temp`.
- **Solution Recommendation**: Replace built-in `tmp_path` in `test_get_obsidian_context_mocked` with a project-local fixture (similar to `tmp_path_local` in `test_queue_manager.py`) located under `.pytest_tmp/`.

#### 2. Warnings: `PytestCacheWarning`
- **Warning Message**:
  ```
  PytestCacheWarning: could not create cache path C:\Users\megat\Hermes-WebApp\.pytest_cache\v\cache\nodeids: [WinError 5] Access is denied
  ```
- **Cause**: The root directory `.pytest_cache` folder permissions or file locking on Windows prevents pytest from updating `.pytest_cache/v/cache/nodeids` and `lastfailed`.
- **Solution Recommendation**: Pass `-p no:cacheprovider` or configure `cache_dir = .pytest_tmp/.pytest_cache` in `pytest.ini`.

---

## 4. Uvicorn Launch Configuration Analysis

### 4.1 Server Binding & Port Configuration
- Default Host: `127.0.0.1` (configurable via `HOST` env var)
- Default Port: `9220` (configurable via `PORT` env var)
- Code location: `backend/config.py`:
  ```python
  HOST: str = os.getenv("HOST", "127.0.0.1")
  PORT: int = int(os.getenv("PORT", 9220))
  ```

### 4.2 Application Entrypoints
1. **Root Entrypoint (`main.py`)**:
   ```python
   import uvicorn
   from backend.main import app
   from backend.config import config

   if __name__ == "__main__":
       uvicorn.run(app, host=config.HOST, port=config.PORT)
   ```
2. **Backend Entrypoint (`backend/main.py`)**:
   - Configures FastAPI app with `lifespan` context manager.
   - CORS middleware enabled (`allow_origins=config.CORS_ORIGINS`, `allow_credentials=True`).
   - Static files mounted at `/static`.
   - Routers mounted: `system.router`, `terminal.router`, `browser.router`.

---

## 5. WebSocket Setup & Test Verification

### 5.1 `/ws/terminal` Endpoint (`backend/websockets/terminal.py`)
- **Protocol**: Raw WebSocket bidirectional text.
- **Backend Mechanics**: Spawns asynchronous child process `pwsh.exe -NoProfile -NoLogo` with working directory `C:\Users\megat`.
- **Tasks**:
  - `read_stdout`: Reads process stdout chunks (1024 bytes) and forwards text to client.
  - `heartbeat`: Sends `{"type": "ping"}` every 15 seconds.
  - Stdin relay: Writes incoming client text + `\n` to process stdin.
  - Ping/Pong handling: Responds to client `"ping"` with `{"type": "pong"}`.
- **Teardown**: Gracefully terminates or kills `pwsh.exe` when client disconnects.

### 5.2 `/ws/browser` Endpoint (`backend/websockets/browser.py`)
- **Protocol**: JSON-formatted WebSocket messages.
- **Backend Mechanics**: Launches Playwright Chromium headless instance with viewport 1024x768.
- **Tasks**:
  - `stream_screen`: Captures JPEG screenshots (quality=40) every 0.2s (~5 FPS) and sends `{"type": "frame", "data": "<base64>"}`.
  - `heartbeat`: Sends `{"type": "ping"}` every 15 seconds.
  - Incoming command router:
    - `"click"`: `mouse.click(x, y)`
    - `"type"`: `keyboard.type(text)`
    - `"keydown"`: `keyboard.press(key)`
    - `"goto"`: `browser_page.goto(url)`

### 5.3 `/ws/audio` Endpoint Status
- **Current Codebase Status**: **NOT IMPLEMENTED**.
- **Roadmap Mapping**: Listed under Expansion Milestone 4 (Voice Terminal & STEM Audio (R2)) in `PROJECT.md`.
- **Planned Interface**: Bidirectional binary/JSON audio frame streaming for real-time speech CLI navigation and STEM audio processing.

### 5.4 Test Coverage Gap & Verification Plan
Currently, no test file in `tests/` exercises WebSocket endpoints. To achieve full R3 verification requirement:
1. Add `tests/test_websockets.py` utilizing `TestClient(app).websocket_connect("/ws/terminal")` and `/ws/browser`.
2. Mock Playwright browser interactions and process streams to verify connection acceptance, ping/pong frames, and disconnection lifecycle without requiring actual GUI browser launch in CI.

---

## 6. Verification Environment Summary & Recommendations

| Component | Status | Action Item |
| :--- | :--- | :--- |
| `tests/test_auth.py` | 9/9 PASS | Operational |
| `tests/test_bot_bridge.py` | 7/7 PASS | Operational |
| `tests/test_bridge.py` | 2/2 PASS | Operational |
| `tests/test_queue_manager.py` | 4/4 PASS | Operational |
| `tests/test_system_api.py` | 9/10 PASS (1 ERROR) | Fix `test_get_obsidian_context_mocked` fixture to use `.pytest_tmp` |
| Pytest Cache | 2 Warnings | Configure `pytest.ini` cache dir or disable cache provider on Windows |
| Uvicorn Port 9220 | Configured & Validated | Host `127.0.0.1`, Port `9220` ready |
| `/ws/terminal` | Implemented | Add unit test in `test_websockets.py` |
| `/ws/browser` | Implemented | Add unit test in `test_websockets.py` |
| `/ws/audio` | Unimplemented | Scope for Milestone 4 (R2 Expansion) |
