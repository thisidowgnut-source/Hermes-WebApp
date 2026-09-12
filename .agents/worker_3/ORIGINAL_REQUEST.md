## 2026-07-23T03:56:19Z
You are worker_3 in C:\Users\megat\Hermes-WebApp\.agents\worker_3.
Your task is to implement Requirement R3: Systems Health & Baseline Test Verification Suite for Hermes-WebApp in C:\Users\megat\Hermes-WebApp.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Key steps to execute:
1. Fix pre-existing baseline test error: In `tests/test_system_api.py::test_get_obsidian_context_mocked`, replace standard pytest `tmp_path` fixture (which causes WinError 5 PermissionError in Windows AppData/Temp) with a local project directory fixture pointing to `.pytest_tmp/` (similar to `test_queue_manager.py`).
2. Add End-to-End WebSocket Test Suite: Create `tests/test_websockets_e2e.py` testing FastAPI `TestClient.websocket_connect` for:
   - `/ws/terminal` (handshake, ping/pong, text command exchange, disconnect)
   - `/ws/browser` (handshake, ping/pong, frame receipt, disconnect)
   - `/ws/audio` (handshake, binary PCM audio send, JSON transcript/command frame receipt, disconnect)
   - `/ws/swarm` (handshake, telemetry/status broadcast, disconnect)
3. Uvicorn Launcher Check: Verify programmatically that `main.py` launches app cleanly on port 9220 without startup errors.
4. Run full test suite: Execute `pytest -v` across all test files in `tests/`. Verify that 100% of test cases PASS with 0 failures and 0 errors.
5. Write detailed handoff report to `C:\Users\megat\Hermes-WebApp\.agents\worker_3\handoff.md` including exact commands executed and full pytest output log.
6. Send completion message to parent.
