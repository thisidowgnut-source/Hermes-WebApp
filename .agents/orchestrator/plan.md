# Execution Plan: Hermes-WebApp Expansion Modules

## Architecture & Milestones Overview

### Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Exploration & Baseline Analysis | Inspect backend/frontend/tests, run baseline pytest, document existing API/WS routes | none | IN_PROGRESS |
| M2 | Dual-Track Architecture & Test Infra | Establish E2E test harness (`TEST_INFRA.md`) & define expansion module interface contracts | M1 | PLANNED |
| M3 | Multi-Agent Swarm Control Panel (R1) | Backend agent management/telemetry API + WebSocket updates + OLED Bento-box UI dashboard | M2 | PLANNED |
| M4 | Voice Command Terminal & STEM Audio Stream (R2) | Backend `/ws/audio` endpoint + voice navigation CLI parser + STEM audio processing + UI integration | M2 | PLANNED |
| M5 | Systems Health, E2E Test Suite & Audit (R3) | Comprehensive unit & E2E tests, Uvicorn server startup check, WS connectivity tests, forensic integrity audit | M3, M4 | PLANNED |

## Detailed Plan Steps

1. **Phase 1: Baseline Investigation**
   - Dispatch `teamwork_preview_explorer` to inspect existing code in `backend/`, `static/`, `main.py`, `tests/`, and verify current pytest suite.

2. **Phase 2: Project Specification (`PROJECT.md` & `TEST_INFRA.md`)**
   - Record exact architecture, module boundaries, endpoints, WS channels, UI Bento-box layouts, and test tier definitions.

3. **Phase 3: Parallel Milestone Execution**
   - Dispatch implementation subagents for M3 (Swarm Control Panel) and M4 (Voice Terminal & STEM Audio Stream).
   - Simultaneously dispatch E2E testing subagent for test suite generation (Tiers 1-4).

4. **Phase 4: Review, Challenger Testing & Integrity Audit**
   - Review code quality with `teamwork_preview_reviewer`.
   - Run stress/adversarial tests with `teamwork_preview_challenger`.
   - Perform forensic integrity audit with `teamwork_preview_auditor`.

5. **Phase 5: Final Synthesis & Human Reporting**
   - Confirm zero-regression integrity, verify all pytest tests pass, Uvicorn port 9220 launches cleanly, and all WebSockets connect.
