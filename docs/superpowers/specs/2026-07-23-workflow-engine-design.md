# ⚙️ Design Specification: Advanced AI Autonomous Workflow Engine & Task Scheduler

**Project**: Hermes-WebApp (Sub-Project 2)  
**Date**: 2026-07-23  
**Status**: APPROVED  

---

## 1. Overview

The **Advanced AI Autonomous Workflow Engine & Task Scheduler** (`mod-workflow`) enables scheduling one-shot timers and recurring cron background tasks natively in Python, while rendering a real-time DAG (Directed Acyclic Graph) visualization of multi-agent tasks and dependencies.

---

## 2. Architecture & Data Flow

```
[ Frontend: mod-workflow ] 
       │
       ├─► GET  /api/workflow/tasks               ─► Scheduler Engine (JSON DB .queue/workflows.json)
       ├─► POST /api/workflow/task/schedule       ─► Cron & One-shot Task Launcher
       ├─► POST /api/workflow/task/{id}/cancel    ─► Process / Task Canceller
       └─► GET  /api/workflow/dag                 ─► Agent DAG Dependency Graph Generator
```

---

## 3. Component Specifications

### 3.1 Backend Endpoints (`backend/routers/system.py`)

1. **`GET /api/workflow/tasks`**: Returns list of scheduled cron and background workflow tasks.
2. **`POST /api/workflow/task/schedule`**: Accepts `name`, `cron_expr`, `command`, `interval_sec`.
3. **`POST /api/workflow/task/{task_id}/cancel`**: Cancels task by ID.
4. **`GET /api/workflow/dag`**: Generates multi-agent DAG execution node tree for UI rendering.

---

## 4. User Interface Specification (`static/index.html`)

- **Dock Item**: **Workflow** (Icon: `workflow`, Data Index: 13).
- **Module ID**: `mod-workflow`.
- **Layout**: Bento-Box 2-subtab interface:
  1. **Cron & Task Scheduler Panel**: Schedule task form + Active jobs table.
  2. **Subagent DAG Graph Panel**: Node graph representation of multi-agent workflows.

---

## 5. Test Plan

- `test_workflow_schedule_and_list()`
- `test_workflow_cancel()`
- `test_workflow_dag()`
