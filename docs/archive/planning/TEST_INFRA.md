# Test Infrastructure — Hermes OS WebApp

> **Philosophy**: Opaque-box, requirement-driven testing ensuring zero regression across all modules.  
> **Methodology**: Category-Partition + BVA + Pairwise + Workload Testing across 4 tiers.

---

## Feature Inventory & Test Coverage

| # | Feature | Module | Tier 1 (Unit) | Tier 2 (Edge) | Tier 3 (Integration) | Tier 4 (E2E) | Status |
|---|---------|--------|:-------------:|:-------------:|:--------------------:|:------------:|:------:|
| 1 | **Core System API** | `system.py` | 25+ | 15+ | ✓ | ✓ | ✅ |
| 2 | **Multi-Agent Swarm** | `swarm.py` + WS | 15+ | 10+ | ✓ | ✓ | ✅ |
| 3 | **Voice/STEM Audio** | `audio.py` + WS | 12+ | 8+ | ✓ | ✓ | ✅ |
| 4 | **HITL Protocol** | `hitl.py` + WS | 8+ | 5+ | ✓ | ✓ | ✅ |
| 5 | **Remote Terminal** | `terminal.py` WS | 6+ | 4+ | ✓ | ✓ | ✅ |
| 6 | **Hermes Vision** | `browser.py` WS | 6+ | 4+ | ✓ | ✓ | ✅ |
| 7 | **Security/Forensics** | `system.py` | 10+ | 6+ | ✓ | ✓ | ✅ |
| 8 | **Workflow Engine** | `system.py` | 8+ | 4+ | ✓ | — | ✅ |
| 9 | **Observability** | `observability.py` | 8+ | 4+ | ✓ | — | ✅ |
| 10 | **Health/Metrics** | `main.py` + `system.py` | 5+ | 3+ | ✓ | ✓ | ✅ |

**Total**: ~113 unit tests, ~63 edge tests, cross-feature integration, E2E workloads

---

## Test Architecture

### Runner
```bash
# All tests
pytest -v

# With coverage
pytest --cov=backend --cov-report=term-missing --cov-report=html

# Specific tiers
pytest -m "not e2e" -v           # Unit + edge (fast)
pytest -m e2e -v                 # E2E (requires running server)
pytest -m websocket -v           # WebSocket tests
```

### Test Files
| File | Scope |
|------|-------|
| `tests/test_system_api.py` | Core REST + SSE + Forensics + Workflow + Obsidian |
| `tests/test_swarm_api.py` | Swarm REST + WS telemetry + agent lifecycle |
| `tests/test_audio_api.py` | Audio REST + WS streaming + voice CLI |
| `tests/test_websockets_e2e.py` | Uvicorn startup + all 5 WS connectivity |

### WebSocket Verification
```python
# FastAPI TestClient for WS
with client.websocket_connect("/ws/swarm") as ws:
    ws.send_json({"type": "get_telemetry"})
    data = ws.receive_json()
    assert data["type"] in ("init", "telemetry")
```

### Uvicorn Verification (E2E)
```python
# tests/test_websockets_e2e.py
- Programmatic startup on port 9220
- Verify /ws/terminal handshake + echo
- Verify /ws/browser handshake + frame
- Verify /ws/swarm handshake + telemetry
- Verify /ws/audio handshake
- Verify /ws/hitl handshake + request/response
- Graceful shutdown
```

---

## Coverage Thresholds (Enforced in CI)

| Tier | Requirement | Target |
|------|-------------|--------|
| **Tier 1** | Feature coverage (REST + WS handshake) | ≥ 113 tests |
| **Tier 2** | Boundary/corner cases (invalid input, disconnects, timeouts) | ≥ 63 tests |
| **Tier 3** | Cross-feature (Swarm + Terminal + Audio simultaneous) | ≥ 12 tests |
| **Tier 4** | Real-world workloads (Voice CLI → Swarm spawn → Monitor → Teardown) | ≥ 3 scenarios |

**Overall line coverage**: ≥ 85% (backend/)
**Branch coverage**: ≥ 80%

---

## Test Categories (pytest markers)

```ini
# pytest.ini markers
e2e: End-to-end tests requiring running server
websocket: Tests requiring WebSocket connections
slow: Tests taking >5 seconds
integration: Integration tests with external services
unit: Pure unit tests (no external deps)
```

Usage:
```bash
pytest -m "unit" -v                    # Fast unit tests only
pytest -m "websocket and not e2e" -v   # WS unit tests (mocked)
pytest -m e2e -v                       # Full E2E suite
```

---

## CI Pipeline (GitHub Actions)

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - name: Install deps
        run: |
          pip install -r requirements.txt
          playwright install chromium
      - name: Run unit + edge tests
        run: pytest -m "not e2e" --cov=backend --cov-fail-under=85
      - name: Start server for E2E
        run: |
          python main.py &
          sleep 5
          curl -f http://127.0.0.1:9220/health
      - name: Run E2E tests
        run: pytest -m e2e -v
```

---

## Mock Strategy

| External Dependency | Mock Approach |
|---------------------|---------------|
| Telegram Bot API | `aiogram` mock + `urllib` mock in `test_system_api.py` |
| Playwright Chromium | Skip in unit; real in E2E |
| `psutil` system calls | Real (read-only, safe) |
| Obsidian Vault | Temp dir fixture + monkeypatch env |
| Kanban DB | Temp SQLite fixture |
| Cloudflare Tunnel | Not tested (external) |

---

## Test Data Management

```python
# Fixtures in conftest.py (or inline)
@pytest.fixture
def tmp_queue(tmp_path):
    # Isolated queue.json per test
    ...

@pytest.fixture
def mock_telegram_token(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    ...
```

---

## Regression Prevention

### Pre-commit Hooks (`.pre-commit-config.yaml`)
```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-changed
        name: pytest on changed files
        entry: pytest --co -q
        language: system
        types: [python]
```

### Flaky Test Quarantine
```bash
# Mark flaky tests
@pytest.mark.flaky(reruns=3, reruns_delay=1)
def test_flaky_websocket():
    ...
```

---

## Debugging Failed Tests

### Common Issues
| Symptom | Cause | Fix |
|---------|-------|-----|
| `WebSocketDisconnect` in test | Server not started | Check `test_websockets_e2e.py` startup |
| Port 9220 in use | Previous test didn't cleanup | `main.py` port fallback handles this |
| `psutil.AccessDenied` | Windows permissions | Run as Admin or skip sensitive tests |
| Telegram 409 Conflict | Two pollers | Split-token arch prevents this |

### Run Single Test with Debug
```bash
pytest tests/test_system_api.py::test_get_stats -v -s --tb=long
pytest tests/test_websockets_e2e.py -v -s --tb=long -k "terminal"
```

---

## Test Data Directories (gitignored)
```
.pytest_tmp/          # Temp test files
.pytest_cache/        # pytest cache
.queue/               # Shared-state queues (test isolation)
```

---

## Future Test Enhancements

| Enhancement | Priority |
|-------------|----------|
| Visual regression (Playwright screenshots) | Medium |
| Load testing (locust/k6) for WS endpoints | Medium |
| Chaos testing (network partition, process kill) | Low |
| Contract testing (Schemathesis for OpenAPI) | Low |

---

*Run `pytest -v` before every commit. CI must pass before merge.*