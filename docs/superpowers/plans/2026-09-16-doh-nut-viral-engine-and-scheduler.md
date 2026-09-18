# Doh-Nut Viral & FYP Engine + Durable Scheduler Implementation Plan

> **Goal:** Implement the Khairul Aming Proven Viral & FYP Certainty Engine, Platform Constraints Validator, and SQLite WAL Durable Delayed Job Scheduler for Hermes-WebApp and Doh-Nut Sovereign Operations.

- **Architecture Spec:** [`docs/superpowers/specs/2026-09-16-doh-nut-viral-engine-and-scheduler-design.md`](file:///C:/Users/megat/Hermes-WebApp/docs/superpowers/specs/2026-09-16-doh-nut-viral-engine-and-scheduler-design.md)
- **Primary Tech Stack:** Python 3.11, FastAPI, Pydantic v2, SQLite WAL (`missions.db`), Pure JS / HTML5
- **Test Runner:** `C:\Users\megat\AppData\Local\hermes\hermes-agent\venv\Scripts\pytest.exe`

---

## Proposed File Changes & Deliverables

```
Hermes-WebApp/
├── config/
│   └── viral_playbook.json                     # [CREATE] Khairul Aming proven viral hooks, sensory bank, and storytelling arcs
├── backend/
│   ├── services/
│   │   ├── viral_engine.py                     # [CREATE] ViralScore model, calculate_viral_score, generate_ka_campaign
│   │   ├── social_validator.py                 # [CREATE] PlatformValidator for TikTok, IG, Threads, X, FB, YouTube
│   │   └── durable_scheduler.py                # [CREATE] SQLite WAL scheduled_jobs worker & crash recovery
│   ├── routers/
│   │   └── social.py                           # [CREATE] REST endpoints for scoring, KA generation, validation & scheduling
│   └── main.py                                 # [MODIFY] Register social router and start scheduler worker in lifespan
├── static/
│   ├── index.html                              # [MODIFY] Add KA formula buttons, FYP gauge & scheduled queue to Doh-Nut tab
│   └── mission-control.js                      # [MODIFY] Add client logic for viral scoring and scheduled posts
└── tests/
    ├── test_viral_engine.py                    # [CREATE] Unit tests for viral scoring and KA playbook generation
    ├── test_social_validator.py                # [CREATE] Unit tests for platform constraints and auto-trimming
    ├── test_durable_scheduler.py               # [CREATE] Tests for SQLite WAL delayed queue and crash recovery
    └── test_social_api.py                      # [CREATE] API integration tests for social endpoints
```

---

## Tasks Decomposition

### Task 1: Khairul Aming Viral Playbook (`config/viral_playbook.json`)
- **Scope:** Pre-loaded knowledge bank of proven F&B viral hooks, sensory words, 4-phase script structures, and debate-loop CTAs.
- **Files to Create:** `config/viral_playbook.json`
- **Steps:**
  1. Define 4 Hook categories: `question_curiosity`, `shock_diet`, `behind_the_scenes_secret`, `asmr_crunch`.
  2. Define sensory keywords: `gebu`, `rangup berderap`, `leleh karamel`, `panas berasap`, `uli 48 jam`, `mentega asli`, `coklat pekat`, `tarik bertali`.
  3. Define 3 Storytelling arcs: `struggle_mastery`, `customer_craving`, `raw_kitchen_transparency`.
  4. Define comment loops: interactive debate questions for Malaysian F&B audience.
  5. Validate valid JSON parsing with python.

### Task 2: Viral Score Linter & Generator Service (`backend/services/viral_engine.py`)
- **Scope:** Real-time 0-100 viral evaluation engine with enforced 85/100 threshold for FYP Certified status.
- **Files to Create:** `backend/services/viral_engine.py`, `tests/test_viral_engine.py`
- **Steps:**
  1. Write failing test `tests/test_viral_engine.py` testing:
     - Generic boring corporate copy scores `< 60` and fails FYP threshold.
     - Khairul Aming structured copy scores `>= 85` and passes FYP threshold.
     - `generate_ka_campaign()` produces valid 4-phase campaign with high score.
  2. Implement `ViralScore` Pydantic v2 model:
     - `hook_score` (0-25), `sensory_score` (0-20), `pacing_score` (0-20), `engagement_score` (0-20), `scarcity_score` (0-15), `total_score` (0-100), `is_fyp_ready` (bool), `suggestions` (list[str]).
  3. Implement `calculate_viral_score(text: str) -> ViralScore`.
  4. Implement `generate_ka_campaign(product_name: str, key_feature: str, arc_type: str = "struggle_mastery") -> dict`.
  5. Run pytest and verify 100% green.

### Task 3: Platform Constraints Validator (`backend/services/social_validator.py`)
- **Scope:** Format, character, duration, and aspect ratio linting per social platform.
- **Files to Create:** `backend/services/social_validator.py`, `tests/test_social_validator.py`
- **Steps:**
  1. Write failing test `tests/test_social_validator.py` testing:
     - X text > 280 chars triggers auto-trim or error.
     - Threads text > 500 chars triggers warning / auto-thread.
     - TikTok / YouTube Shorts requires vertical video (9:16) and duration < 60s for Shorts.
     - Instagram max 30 hashtags.
  2. Implement `ValidationResult` Pydantic model (`valid: bool`, `errors: list[str]`, `warnings: list[str]`, `auto_trimmed_text: str | None`).
  3. Implement `SocialValidator.validate_post(platform: str, text: str, media_aspect_ratio: str | None, media_duration_seconds: float | None) -> ValidationResult`.
  4. Implement `SocialValidator.auto_trim(platform: str, text: str) -> str`.
  5. Run pytest and verify 100% green.

### Task 4: SQLite WAL Scheduled Jobs Ledger & Durable Scheduler (`backend/services/durable_scheduler.py`)
- **Scope:** Persistent delayed task queue polled every 5s on FastAPI lifespan with crash recovery.
- **Files to Create:** `backend/services/durable_scheduler.py`, `tests/test_durable_scheduler.py`
- **Steps:**
  1. Write failing test `tests/test_durable_scheduler.py` testing:
     - Table initialization `scheduled_jobs`.
     - `schedule_job()` inserts row with status `pending`.
     - `poll_and_execute_due_jobs()` executes jobs where `execute_at <= now`.
     - Interrupted jobs on restart are reverted to `pending` if `attempts < max_attempts`.
     - Cancel job updates status to `cancelled`.
  2. Implement `DurableSchedulerService`:
     - `initialize_table()`
     - `schedule_job(project_slug, platform, action, payload, execute_at)`
     - `list_jobs(status, platform, limit)`
     - `cancel_job(job_id)`
     - `reconcile_startup()`
     - `poll_and_execute_due_jobs()`
  3. Run pytest and verify 100% green.

### Task 5: Social API Router & Main Lifespan Integration (`backend/routers/social.py`)
- **Scope:** REST endpoints exposing viral scoring, KA generation, validation, scheduling, and background worker lifecycle.
- **Files to Create/Modify:** `backend/routers/social.py`, `backend/main.py`, `tests/test_social_api.py`
- **Steps:**
  1. Write failing test `tests/test_social_api.py` testing:
     - `POST /api/social/viral-score` returns score and suggestions.
     - `POST /api/social/generate-ka` returns generated draft.
     - `POST /api/social/validate` returns validation status.
     - `POST /api/social/schedule` enqueues job (requires auth/csrf).
     - `GET /api/social/scheduled` lists pending jobs.
     - `DELETE /api/social/scheduled/{id}` cancels job.
  2. Implement `backend/routers/social.py`.
  3. Register router in `backend/main.py` and start background scheduler worker in lifespan.
  4. Run pytest and verify 100% green.

### Task 6: Doh-Nut Social Hub UI & 1-Tap Formula Buttons (`static/index.html`, `static/mission-control.js`)
- **Scope:** Front-end interactive controls for viral generation, FYP gauge, and scheduled post view.
- **Files to Modify:** `static/index.html`, `static/mission-control.js`
- **Steps:**
  1. Add 3 1-tap KA buttons in `dohnut-tab-social`: `[ 🍳 KA Recipe Story ]`, `[ 🍩 ASMR Glaze Drip ]`, `[ 📦 Sold-Out FOMO ]`.
  2. Add Neon Green FYP Confidence Gauge: `🔥 VIRAL CONFIDENCE: 92% (KHAIRUL AMING CERTIFIED)`.
  3. Add Scheduled Posts queue card with 1-tap cancel buttons.
  4. Wire event listeners in `static/mission-control.js` / inline script to call `/api/social/...` endpoints.
  5. Verify UI rendering and responsive mobile layout.

### Task 7: Full Regression & Verification
- **Scope:** Run full test suite (`pytest tests/ -v`) to confirm 230+ tests passing (100% green, 0 failures).
