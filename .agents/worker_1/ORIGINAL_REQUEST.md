## 2026-07-23T03:56:18Z
You are worker_1 in C:\Users\megat\Hermes-WebApp\.agents\worker_1.
Your task is to implement Requirement R1: Multi-Agent Swarm Control Panel for Hermes-WebApp in C:\Users\megat\Hermes-WebApp.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Key steps to execute:
1. Backend Service: Create `backend/services/swarm_manager.py` with `SwarmManager` singleton managing background agent processes, state persistence in `.queue/swarm_agents.json`, `psutil` metrics monitoring, agent spawning, status tracking (`running`, `completed`, `failed`), and process termination.
2. Backend Router: Create `backend/routers/swarm.py` with REST routes `GET /api/swarm/agents`, `POST /api/swarm/spawn`, `GET /api/swarm/agent/{id}`, `POST /api/swarm/agent/{id}/terminate`.
3. Backend WebSocket: Create `backend/websockets/swarm.py` for `/ws/swarm` broadcasting real-time agent telemetry and log updates.
4. Register `swarm.router` and `/ws/swarm` endpoint in `backend/main.py`.
5. Frontend UI: Edit `static/index.html` adhering strictly to Anti-AI Slop OLED dark aesthetic (`#000` dark background, `.glass` cards, Bento-box grid):
   - Add `#swarm-bento-card` into `<main>` grid showing active subagent count, status indicators, and quick spawn action.
   - Add `#mod-swarm` full-screen module overlay (Dock item index 6 with bot icon) containing subagent spawner form, active agents matrix with progress badges, and live log stream.
   - Add frontend JS connecting to `/ws/swarm` and `/api/swarm/*`.
6. Unit Tests: Create `tests/test_swarm_api.py` covering all REST endpoints and `/ws/swarm` WebSocket connection.
7. Run `pytest -v tests/test_swarm_api.py` to verify implementation.
8. Write detailed handoff report to `C:\Users\megat\Hermes-WebApp\.agents\worker_1\handoff.md` including exact commands executed and passing test logs.
9. Send completion message to parent.
