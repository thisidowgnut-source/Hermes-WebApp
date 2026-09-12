# System Hardening & Deep Forensic Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a native, 0% Docker security & auditing module for Hermes-WebApp supporting File Integrity Monitoring (FIM SHA-256), Windows Firewall rule management, and Security EventLog inspection.

**Architecture:** Extend `backend/routers/system.py` (or dedicated router) with REST endpoints using native `hashlib`, `psutil`, `subprocess` (`netsh`/`powershell`), add a Bento-box `mod-forensics` overlay to `static/index.html` with Lucide icons and dock integration, and add full pytest coverage.

**Tech Stack:** Python 3.11, FastAPI, `psutil`, PowerShell/`netsh` CLI, HTML5/CSS3 Bento-Box, Vanilla JS, Pytest.

## Global Constraints

- 100% Non-Docker native implementation.
- Anti-AI Slop UI: Pure black background (`#000`), Lucide icons, sharp 1px borders.
- Zero breaking changes to existing 71 passing tests.

---

### Task 1: Backend FIM (File Integrity Monitor) & Firewall REST Endpoints

**Files:**
- Modify: `backend/routers/system.py`
- Test: `tests/test_system_api.py`

**Interfaces:**
- Consumes: `config.BASE_DIR`
- Produces: `GET /api/forensics/fim/scan`, `POST /api/forensics/fim/baseline`, `GET /api/forensics/firewall/rules`, `POST /api/forensics/firewall/rule`, `GET /api/forensics/event-logs`

- [ ] **Step 1: Write the failing tests**

Add unit tests to `tests/test_system_api.py`:
```python
def test_fim_baseline_and_scan(tmp_path):
    # Test FIM baseline creation and scan
    res_base = client.post("/api/forensics/fim/baseline", json={"dir": str(tmp_path)})
    assert res_base.status_code == 200
    assert res_base.json()["status"] == "success"

    # Scan clean
    res_scan = client.get(f"/api/forensics/fim/scan?dir={tmp_path}")
    assert res_scan.status_code == 200
    assert res_scan.json()["status"] == "success"
    assert res_scan.json()["tampered_count"] == 0

def test_firewall_rules_endpoint():
    res = client.get("/api/forensics/firewall/rules")
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert "rules" in res.json()

def test_event_logs_endpoint():
    res = client.get("/api/forensics/event-logs")
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert "logs" in res.json()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_system_api.py -k "test_fim_baseline_and_scan or test_firewall_rules_endpoint or test_event_logs_endpoint" -v`
Expected: FAIL with "404 Not Found"

- [ ] **Step 3: Implement minimal backend endpoints in `backend/routers/system.py`**

Add FIM SHA-256 hash calculator, baseline reader/writer, firewall rules query, and win-event logs reader functions to `backend/routers/system.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_system_api.py -k "test_fim_baseline_and_scan or test_firewall_rules_endpoint or test_event_logs_endpoint" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/routers/system.py tests/test_system_api.py
git commit -m "feat(forensics): add FIM SHA-256 and Firewall REST endpoints"
```

---

### Task 2: Frontend Forensics Bento-Box Module UI (`mod-forensics`) & Dock Integration

**Files:**
- Modify: `static/index.html`

**Interfaces:**
- Consumes: `/api/forensics/*` endpoints
- Produces: macOS Dock Item `Forensics` (Index 12) & `mod-forensics` overlay UI

- [ ] **Step 1: Add Dock Button for Forensics**

In `static/index.html` dock bar:
```html
<button class="dock-item" onclick="openModule('forensics', this)" aria-label="Forensics Suite" data-idx="12">
    <div class="dock-icon"><i data-lucide="shield-check"></i></div>
    <div class="dock-label">Forensics</div>
    <div class="glow-indicator"></div>
</button>
```

- [ ] **Step 2: Add `mod-forensics` Module Overlay HTML**

Insert Bento-box overlay HTML before `<script>` in `static/index.html` with FIM, Firewall, and Security Log subtabs.

- [ ] **Step 3: Add `fetchFimScan()`, `fetchFirewallRules()`, and `fetchSecurityLogs()` JS handlers**

Add client fetch logic, table rendering,Lucide icon re-creation, and Telegram haptic feedback.

- [ ] **Step 4: Run full test suite & verify UI**

Run: `pytest -v`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add static/index.html
git commit -m "feat(ui): add Forensics Bento-box module and dock button"
```
