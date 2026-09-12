# 🛡️ Design Specification: System Hardening & Deep Forensic Suite

**Project**: Hermes-WebApp (Sub-Project 1)  
**Date**: 2026-07-23  
**Status**: APPROVED  

---

## 1. Overview

The **System Hardening & Deep Forensic Suite** (`mod-forensics`) is a native, zero-external-dependency security & auditing module for Hermes-WebApp. It provides real-time file integrity monitoring (FIM), Windows Firewall rule management, and security event log inspection natively through Python and Windows system interfaces.

---

## 2. Architecture & Data Flow

```
[ Frontend: mod-forensics ] 
       │
       ├─► GET  /api/forensics/fim/scan         ─► FIM SHA-256 Engine (.fim_baseline.json)
       ├─► POST /api/forensics/fim/baseline     ─► Hash Snapshot Generator
       ├─► GET  /api/forensics/firewall/rules   ─► netsh advfirewall / Get-NetFirewallRule
       ├─► POST /api/forensics/firewall/rule    ─► Add/Block/Remove Firewall Rules
       └─► GET  /api/forensics/event-logs       ─► Get-WinEvent (Security & System)
```

---

## 3. Detailed Component Specifications

### 3.1 Backend Endpoints (`backend/routers/system.py` or `backend/routers/forensics.py`)

#### A. File Integrity Monitor (FIM)
- **`GET /api/forensics/fim/scan`**
  - Scans specified directories (`C:\Users\megat\Hermes-WebApp\backend`, `C:\Users\megat\Hermes-WebApp\static`) against baseline `.fim_baseline.json`.
  - Returns modified, added, or deleted files with status `MODIFIED`, `ADDED`, or `DELETED`.
- **`POST /api/forensics/fim/baseline`**
  - Computes SHA-256 hashes for all target files and saves snapshot to `.fim_baseline.json`.

#### B. Firewall Rule Controller
- **`GET /api/forensics/firewall/rules`**
  - Executes PowerShell `Get-NetFirewallRule -Enabled True | Select-Object -First 30 Name, DisplayName, Action, Direction` and returns JSON rule set.
- **`POST /api/forensics/firewall/rule`**
  - Accepts JSON payload `{"name": "...", "action": "block"|"allow", "ip": "...", "direction": "in"|"out"}`.
  - Executes `netsh advfirewall firewall add rule ...` via subprocess.

#### C. Windows Security Event Viewer
- **`GET /api/forensics/event-logs`**
  - Executes PowerShell `Get-WinEvent -LogName Security -MaxEvents 20` to fetch recent login, privilege escalation, or process execution events.

---

## 4. User Interface Specification (`static/index.html`)

- **Dock Item**: **Forensics** (Icon: `shield-check`, Data Index: 12).
- **Module ID**: `mod-forensics`.
- **Layout**: Bento-box 3-subtab interface:
  1. **FIM Panel**: Visual diff list showing green for intact files, red for modified/tampered files.
  2. **Firewall Manager Panel**: Table of active firewall rules with quick "Block IP" action input.
  3. **Security Event Stream**: Highlighting security log severity badges.

---

## 5. Security & Risk Assessment

1. **Execution Risk**: Subprocess commands (`netsh`, `powershell`) use parameterized arrays to prevent command injection.
2. **Performance Impact**: FIM scans use `hashlib.sha256()` with 64KB chunk buffer for zero RAM spikes.
3. **No-Docker Guarantee**: Operates 100% natively on host OS.

---

## 6. Verification & Test Plan

- Unit tests added to `tests/test_system_api.py` or `tests/test_forensics_api.py`:
  - `test_fim_baseline_and_scan()`
  - `test_firewall_rules_endpoint()`
  - `test_event_logs_endpoint()`
- Required pass rate: 100%.
