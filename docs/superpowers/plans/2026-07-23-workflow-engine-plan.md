# Advanced AI Autonomous Workflow Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement native task scheduling and Subagent DAG visualization in Hermes-WebApp (`mod-workflow`).

**Architecture:** Extend `backend/routers/system.py` with REST endpoints for workflow scheduling, cancellation, and DAG generation; add `mod-workflow` Bento-box overlay and Dock button in `static/index.html`; verify with pytest TDD.

**Tech Stack:** Python 3.11, FastAPI, HTML5/CSS3, Vanilla JS, Pytest.

## Global Constraints
- 100% Non-Docker native Python.
- Anti-AI Slop UI: Pure black `#000` background, sharp 1px borders, Lucide icons.

---

### Task 1: Backend Workflow & DAG REST Endpoints

**Files:**
- Modify: `backend/routers/system.py`
- Test: `tests/test_system_api.py`

- [ ] **Step 1: Write failing unit tests in `tests/test_system_api.py`**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement minimal backend endpoints in `backend/routers/system.py`**
- [ ] **Step 4: Run test to verify it passes**

---

### Task 2: Frontend Workflow Bento-Box Module UI (`mod-workflow`) & Dock Integration

**Files:**
- Modify: `static/index.html`

- [ ] **Step 1: Add Dock Button for Workflow (Icon: `workflow`, Index: 13)**
- [ ] **Step 2: Add `mod-workflow` Module Overlay HTML**
- [ ] **Step 3: Add `fetchWorkflowTasks()`, `scheduleWorkflowTask()`, and `fetchWorkflowDag()` JS handlers**
- [ ] **Step 4: Run full test suite & verify UI**
