# Hermes, AGY, and Doh-Nut Remote Operations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Deliver a secure mobile-first mission control surface that lets the operator run and resume the existing Doh-Nut AGY workflow remotely, records truthful execution state, and adds Hermes coordination only when it is explicitly selected.

**Architecture:** Hermes-WebApp owns a durable SQLite mission ledger, access control, UI event replay, approvals, cost records, and adapter contracts. AGY remains the default task executor and is run only through typed, project-scoped profiles with one writer per provider conversation. Hermes is a feature-flagged secondary adapter for plan, verification, and Kanban work; handoffs are bounded artifacts, never recursive executor calls. An Astra-aligned policy layer adds immutable planning packets, capability receipts, risk classifications, execution budgets, and evidence-based keep/revert/escalate decisions.

**Tech Stack:** Python 3, FastAPI, Pydantic v2, asyncio subprocesses, SQLite WAL, existing cryptography package, pytest, httpx/TestClient, existing static HTML/CSS/JavaScript, and AGY stream-json.

**Spec:** docs/PRD.md

## Global Constraints

- Preserve the existing AGY CLI workflow, current Doh-Nut workspace, and eight agent definition files. Do not clone, reinstall, reset, or replace them.
- Treat G:/Doh-Nut as a configured workspace path, not an assumed AGY provider project id.
- Use typed argv lists with shell=False for every new AGY/Hermes subprocess. The client must never submit raw commands, paths, or hidden flags.
- Keep port 9220 and the Telegram Mini App entry point stable. Do not hardcode a historic cloudflared PID as a success condition.
- Do not connect to or poll the existing terminal, browser, swarm, audio, or HITL WebSockets from engineering automation.
- Use SQLite WAL and short transactions. Persist only redacted events and approved artifacts under var/lib.
- Use Telegram server-side validation plus short-lived operator sessions. Development bypass must be opt-in and rejected through the public tunnel.
- No social post is "published" until a platform receipt or human-attested proof is stored. CAPTCHA and 2FA remain human-in-the-loop.
- Do not add a frontend framework or rewrite static/index.html. Add focused static assets and mount one new Mission Control view through existing navigation.
- Every new endpoint, state transition, and adapter must be covered by focused tests before it is wired into the UI.
- The worktree currently contains unrelated user changes. Do not stage, commit, revert, or reformat unrelated files. At each checkpoint, record the focused test output and inspect the scoped diff.
- A Hermes planning, verification, or Kanban run with more than one meaningful step requires a persisted planning packet before it can enter running.
- Capability selection is a registry lookup from a declared mission intent. Never derive authority from model output, arbitrary prompt text, a web page, or a returned artifact.
- High-risk intent must become a typed waiting-human state before any browser publish, external transmission, credential, financial, destructive, CAPTCHA, 2FA, or unknown-platform action.
- Historical Astra-Grade values of 25 iterations and 3 concurrent children are candidate defaults only. Read effective values from non-secret validated policy and prove them in a fresh controlled test before activation.
- A failed, stale, missing, or incomparable measurement is never success evidence. It must leave the mission in needs-verification, interrupted, unknown, or a typed failure state.

---

## Current File Map

| Path | Role after implementation |
| --- | --- |
| backend/config.py | Adds validated configuration for mission DB, project registry, auth allowlist, secure cookie policy, capacity limits, and feature flags. |
| backend/main.py | Registers auth and mission routers, lifespan recovery, and the authenticated mission WebSocket. |
| backend/auth.py | Retains Telegram HMAC verification and adds auth_date freshness checks; becomes the low-level validator only. |
| backend/models/mission.py | Pydantic request/response models, enums, and event schemas used by API, runner, UI, and tests. |
| backend/services/project_registry.py | Reads safe project/agent profile configuration and resolves allowlisted workspace paths. |
| backend/services/mission_store.py | SQLite WAL schema, transaction helpers, idempotency, events, approvals, artifacts, sessions, costs, and migration metadata. |
| backend/services/mission_policy.py | State transition, authorization, redaction, idempotency, and handoff-depth rules. |
| backend/services/session_auth.py | Server session, CSRF, one-time WebSocket ticket, allowlist, and in-memory rate limit services. |
| backend/services/agy_protocol.py | NDJSON parser and conversion from AGY events to normalized mission events. |
| backend/services/agy_session_manager.py | One-writer-per-run AGY subprocess lifecycle, input queue, stdout/stderr drain, cancellation, and recovery classification. |
| backend/services/mission_service.py | Coordinates repository, profile validation, AGY manager, Hermes adapter, and event fan-out. |
| backend/services/social_campaign_service.py | Campaign facts, immutable content hashes, approval validation, and publication state transitions. |
| backend/services/social_delivery.py | Capability-declared manual/WebBridge/API adapters and reconciliation behavior. |
| backend/services/hermes_adapter.py | Feature-flagged Hermes plan/verifier/Kanban adapter contract and one-hop handoff protection. |
| backend/services/orchestration_policy.py | Planning-packet validation, risk classification, budget enforcement, and one-hop policy shared by Hermes workflows. |
| backend/services/capability_registry.py | Versioned allowlist that maps declared mission intent to least-privilege Hermes capability profiles. |
| backend/services/evaluation_service.py | Baseline/measurement provenance and keep/revert/escalate decisions for change-oriented missions. |
| backend/services/capability_probe.py | Honest availability probes with timestamps for AGY, Hermes, tunnel, WebBridge, and database. |
| backend/routers/auth.py | Session establishment, CSRF bootstrap, and WebSocket ticket endpoints. |
| backend/routers/missions.py | Authenticated mission, turn, event, artifact, approval, and capability REST routes. |
| backend/websockets/missions.py | Authenticated one-time-ticket event stream with cursor replay. |
| backend/cli/migrate_legacy_social.py | Dry-run and verified import of legacy social data into the new ledger. |
| config/projects/doh-nut.json | Non-secret Doh-Nut project profile with workspace path, eight AGY role mappings, brand truth path, and approval policy. |
| config/orchestration/defaults.json | Non-secret candidate limits, risk classes, capability profiles, and evaluation policy; must be validated at startup. |
| static/mission-control.css | Focused responsive Mission Control styling. |
| static/mission-control.js | Client state, REST requests, event reconnect, cursor storage, approval UI, and accessibility behavior. |
| static/index.html | Adds minimal asset tags and one Mission Control mount point/navigation entry. |
| tests/fixtures/agy/*.ndjson | Sanitized documented AGY stream fixtures. |
| tests/test_*.py | Unit, repository, API, security, browser, adapter, recovery, and migration coverage described below. |
| docs/ASTRA-GRADE-ALIGNMENT.md | Provenance boundary and design mapping for the requested GPT-6 Astra direction. |

## Shared Interfaces

All tasks use these exact public shapes. Do not duplicate look-alike enums in routers, services, or JavaScript.

    class PrimaryExecutor(str, Enum):
        AGY = "agy"
        HERMES = "hermes"

    class MissionState(str, Enum):
        DRAFT = "draft"
        QUEUED = "queued"
        STARTING = "starting"
        RUNNING = "running"
        WAITING_HUMAN = "waiting_human"
        WAITING_APPROVAL = "waiting_approval"
        SUCCEEDED = "succeeded"
        NEEDS_VERIFICATION = "needs_verification"
        VERIFIED = "verified"
        FAILED_VERIFICATION = "failed_verification"
        INTERRUPTED = "interrupted"
        UNKNOWN = "unknown"
        CANCELLED = "cancelled"
        FAILED = "failed"
        TIMED_OUT = "timed_out"

    class CreateMissionRequest(BaseModel):
        project_slug: str
        title: str
        objective: str
        primary_executor: PrimaryExecutor
        agent_profile: str
        idempotency_key: UUID

    class CreateTurnRequest(BaseModel):
        message: str
        idempotency_key: UUID

    class OperatorContext(BaseModel):
        operator_id: int
        username: str | None
        session_id: UUID
        is_local_development: bool = False

    class ProjectProfile(BaseModel):
        slug: str
        workspace_path: Path
        agy_project_id: str | None
        brand_truth_path: Path
        agents: dict[str, AgentProfile]
        approval_policy: ApprovalPolicy

    class NormalizedAgyEvent(BaseModel):
        event_type: str
        provider_conversation_id: str | None
        state: str | None
        text_delta: str | None
        result_status: str | None
        usage: UsageRecord | None
        tool_name: str | None
        created_at: datetime

All datetime values are UTC ISO-8601. All identifiers exposed to clients are UUID strings. Store external provider ids separately from WebApp ids.

    class RiskClass(str, Enum):
        LOW = "low"
        REVIEW = "review"
        HUMAN_REQUIRED = "human_required"

    class PlanningPacket(BaseModel):
        mission_id: UUID
        objective: str
        constraints: list[str]
        evidence_artifact_ids: list[UUID]
        risk_class: RiskClass
        selected_capability_ids: list[str]
        policy_version: str
        iteration_budget: int
        child_concurrency_budget: int
        acceptance_checks: list[str]
        sha256: str

    class CapabilityReceipt(BaseModel):
        registry_version: str
        mission_intent: str
        selected_capability_ids: list[str]
        denied_capability_ids: list[str]
        selected_at: datetime

    class EvaluationDecision(str, Enum):
        KEEP = "keep"
        REVERT = "revert"
        ESCALATE = "escalate"
        NEEDS_VERIFICATION = "needs_verification"

    class MeasurementRecord(BaseModel):
        mission_id: UUID
        metric_name: str
        baseline_artifact_id: UUID
        observed_artifact_id: UUID | None
        method: str
        comparable: bool
        observed_at: datetime | None

No model response, user text, external content, or historical log can directly populate selected_capability_ids. Only the validated registry may do so.

---

### Task 1: Freeze the Baseline and Prove the AGY Protocol Contract

**Files:**

- Create: tests/fixtures/agy/stream_success.ndjson
- Create: tests/fixtures/agy/stream_error.ndjson
- Create: tests/fixtures/agy/stream_malformed.ndjson
- Create: backend/services/agy_protocol.py
- Create: tests/test_agy_protocol.py
- Modify: docs/API.md
- Modify: docs/ARCHITECTURE.md

**Interfaces:**

- Produces parse_agy_stream_line(line: str, now: datetime) -> NormalizedAgyEvent | None.
- Produces AgyProtocolError with code values malformed_json, unsupported_shape, missing_result, and invalid_usage.
- Consumes no live AGY account in unit tests.

- [ ] **Step 1: Capture a non-destructive baseline**

Record the installed AGY version, help text, remote-control status, configured WebApp endpoint, current Git status, and the existing eight agent filenames in a dated development log. Do not start or register the remote-control daemon. Do not use a real social account.

The AGY protocol fixture must model a documented init, step_update, and result sequence:

    {"event":"init","conversation_id":"11111111-1111-1111-1111-111111111111","init":{"cwd":"G:/Doh-Nut","permission_mode":"request-review"}}
    {"event":"step_update","step_update":{"conversation_id":"11111111-1111-1111-1111-111111111111","step_index":1,"state":"ACTIVE","step_type":"agent_response","text_delta":"Draft is being prepared."}}
    {"event":"result","result":{"conversation_id":"11111111-1111-1111-1111-111111111111","status":"SUCCESS","response":"Prepared draft.","duration_seconds":2.5,"num_turns":1,"usage":{"input_tokens":10,"output_tokens":5,"thinking_tokens":1,"cache_read_tokens":0,"total_tokens":16}}}

- [ ] **Step 2: Write failing parser tests**

    def test_result_event_preserves_conversation_and_usage():
        event = parse_agy_stream_line(RESULT_LINE, FIXED_NOW)
        assert event.event_type == "agy.result"
        assert event.provider_conversation_id == "11111111-1111-1111-1111-111111111111"
        assert event.result_status == "SUCCESS"
        assert event.usage.total_tokens == 16

    def test_malformed_json_raises_typed_error():
        with pytest.raises(AgyProtocolError, match="malformed_json"):
            parse_agy_stream_line("{not-json}", FIXED_NOW)

    def test_unknown_event_is_diagnostic_not_a_crash():
        assert parse_agy_stream_line('{"event":"future_event"}', FIXED_NOW) is None

- [ ] **Step 3: Run the focused test before implementation**

Run: pytest tests/test_agy_protocol.py -v

Expected: collection or import failure because the parser does not exist.

- [ ] **Step 4: Implement a strict, redaction-ready parser**

The parser must use json.loads, validate event/payload types, map init to agy.init, step_update to agy.step, result to agy.result, and reject JSON objects that claim to be known events but lack required dictionaries. It must not execute data from AGY output.

    def parse_agy_stream_line(line: str, now: datetime) -> NormalizedAgyEvent | None:
        payload = json.loads(line)
        event_name = payload.get("event")
        if event_name == "init":
            return _parse_init(payload["init"], payload.get("conversation_id"), now)
        if event_name == "step_update":
            return _parse_step(payload["step_update"], now)
        if event_name == "result":
            return _parse_result(payload["result"], now)
        return None

- [ ] **Step 5: Run parser tests and add one bounded live contract probe**

Run: pytest tests/test_agy_protocol.py -v

Expected: all parser tests pass.

Only after tests pass and only under an already authenticated AGY session, run one short plan-mode prompt in the Doh-Nut workspace with no tools, no writes, no browser access, and stream-json output. Save only a redacted fixture if the event shape differs. A missing login, quota, timeout, or empty response is a recorded baseline result, not a reason to alter AGY configuration.

- [ ] **Step 6: Correct legacy documentation claims**

Update API.md and ARCHITECTURE.md to mark the existing social "publish" route as browser assistance until receipt support is implemented, replace ConPTY claims with actual observed behavior, and link to PRD.md. Do not publish undocumented endpoints in the public API section.

- [ ] **Checkpoint**

Run: pytest tests/test_agy_protocol.py -v

Inspect: git diff -- docs/API.md docs/ARCHITECTURE.md backend/services/agy_protocol.py tests/fixtures/agy tests/test_agy_protocol.py

---

### Task 2: Define Project Profiles and the Eight Existing Doh-Nut Roles

**Files:**

- Create: config/projects/doh-nut.json
- Create: backend/services/project_registry.py
- Create: tests/test_project_registry.py
- Modify: backend/config.py
- Modify: backend/models/mission.py

**Interfaces:**

- Produces ProjectRegistry.get(slug: str) -> ProjectProfile.
- Produces ProjectRegistry.list_visible(operator: OperatorContext) -> list[ProjectProfile].
- The profile stores an optional AGY project id separately from workspace_path.

- [ ] **Step 1: Write a non-secret Doh-Nut profile**

Use only stable configuration. Do not place tokens, browser-profile credentials, or account cookies in this file.

    {
      "slug": "doh-nut",
      "display_name": "Doh-Nut",
      "workspace_path": "G:/Doh-Nut",
      "agy_project_id": null,
      "brand_truth_path": "G:/Doh-Nut/brand-system/01-brand-truth.md",
      "approval_policy": {
        "social_requires_human_confirmation": true,
        "approval_ttl_seconds": 900
      },
      "agents": {
        "dohnut-orchestrator": {"display_name":"Doh-Nut Orchestrator","execution":"agy"},
        "dohnut-frontend-artisan": {"display_name":"Doh-Nut Frontend Artisan","execution":"agy"},
        "dohnut-backend-architect": {"display_name":"Doh-Nut Backend Architect","execution":"agy"},
        "dohnut-realtime-ops": {"display_name":"Doh-Nut Realtime Ops","execution":"agy"},
        "dohnut-qa-guardian": {"display_name":"Doh-Nut QA Guardian","execution":"agy"},
        "dohnut-brand-guardian": {"display_name":"Doh-Nut Brand Guardian","execution":"agy"},
        "dohnut-viral-engine": {"display_name":"Doh-Nut Viral Engine","execution":"agy"},
        "dohnut-social-autopilot": {"display_name":"Doh-Nut Social Autopilot","execution":"agy"}
      }
    }

- [ ] **Step 2: Write failing registry tests**

    def test_dohnut_profile_resolves_existing_workspace_and_all_agents():
        profile = registry.get("doh-nut")
        assert profile.workspace_path == Path("G:/Doh-Nut")
        assert set(profile.agents) == EXPECTED_AGENT_KEYS
        assert profile.agy_project_id is None

    def test_unknown_project_and_agent_are_rejected():
        with pytest.raises(ProjectNotFound):
            registry.get("not-a-project")
        with pytest.raises(AgentProfileNotFound):
            registry.require_agent("doh-nut", "shell-injection")

    def test_workspace_must_stay_inside_allowlisted_project_root(tmp_path):
        invalid = write_profile(tmp_path, workspace_path="C:/Windows")
        with pytest.raises(ProjectProfileError, match="workspace_path"):
            ProjectRegistry.load(invalid)

- [ ] **Step 3: Implement profile validation**

Resolve each configured path and compare it to the explicit allowlisted workspace root. Verify the actual agent definition exists at G:/Doh-Nut/.gemini/agents/<agent>.md when loading Doh-Nut. Do not require an AGY project id: when absent, the bridge uses the workspace current directory and records the provider id after first result.

- [ ] **Step 4: Add config settings**

Add settings for HERMES_PROJECTS_DIR, HERMES_MISSION_DB_PATH, HERMES_ALLOW_LOCAL_DEVELOPMENT, HERMES_OPERATOR_ALLOWLIST, HERMES_MAX_ACTIVE_RUNS, HERMES_MAX_ACTIVE_AGY_PER_PROJECT, and HERMES_HERMES_ADAPTER_ENABLED. Validate paths and numeric limits at startup. Provide safe development defaults only when HERMES_ENV equals development.

- [ ] **Step 5: Verify**

Run: pytest tests/test_project_registry.py -v

Expected: all expected role, path, and invalid-profile tests pass.

- [ ] **Checkpoint**

Inspect: git diff -- config/projects/doh-nut.json backend/config.py backend/models/mission.py backend/services/project_registry.py tests/test_project_registry.py

---

### Task 3: Build the Durable Mission Ledger and State Machine

**Files:**

- Create: backend/models/mission.py
- Create: backend/services/mission_store.py
- Create: backend/services/mission_policy.py
- Create: tests/test_mission_store.py
- Create: tests/test_mission_policy.py
- Modify: backend/config.py

**Interfaces:**

- Produces MissionStore.initialize() -> None.
- Produces MissionStore.create_mission(request: CreateMissionRequest, operator: OperatorContext) -> MissionSnapshot.
- Produces MissionStore.enqueue_turn(mission_id: UUID, request: CreateTurnRequest, operator: OperatorContext) -> TurnRecord.
- Produces MissionStore.append_event(mission_id: UUID, type: str, payload: dict) -> MissionEvent.
- Produces assert_transition(from_state: MissionState, to_state: MissionState) -> None.
- Produces redact_payload(value: object) -> object.

- [ ] **Step 1: Write failing state and idempotency tests**

    def test_same_operator_and_idempotency_key_creates_one_mission(store, operator):
        first = store.create_mission(REQUEST, operator)
        second = store.create_mission(REQUEST, operator)
        assert second.mission_id == first.mission_id
        assert store.count_rows("missions") == 1

    def test_cannot_mark_unknown_run_as_verified():
        with pytest.raises(InvalidMissionTransition):
            assert_transition(MissionState.UNKNOWN, MissionState.VERIFIED)

    def test_event_sequence_is_monotonic_per_mission(store, operator):
        mission = store.create_mission(REQUEST, operator)
        first = store.append_event(mission.mission_id, "mission.created", {})
        second = store.append_event(mission.mission_id, "run.queued", {})
        assert (first.sequence, second.sequence) == (1, 2)

    def test_redaction_replaces_bearer_and_cookie_values():
        payload = {"authorization": "Bearer abcdefghijklmnopqrstuvwxyz", "cookie": "sid=secret"}
        assert "abcdefghijklmnopqrstuvwxyz" not in json.dumps(redact_payload(payload))

- [ ] **Step 2: Run red tests**

Run: pytest tests/test_mission_store.py tests/test_mission_policy.py -v

Expected: import failure before implementation.

- [ ] **Step 3: Implement SQLite schema and transaction boundaries**

Create tables for missions, mission_runs, mission_turns, mission_events, artifacts, approvals, publication_attempts, cost_records, operator_sessions, websocket_tickets, migration_manifests, and idempotency_keys. Turn on PRAGMA journal_mode=WAL, foreign_keys=ON, and busy_timeout. Open a short-lived connection per repository operation; begin IMMEDIATE only for operations that allocate a per-mission sequence or consume an idempotency key.

The idempotency table must be keyed by operator_id, operation, and idempotency_key. Store a canonical response reference, not raw request secrets.

- [ ] **Step 4: Implement the state transition policy**

Use an explicit adjacency map. It must reject arbitrary transitions, require a terminal AGY result before succeeded, require a verification artifact before verified, and disallow published without a receipt. Do not mutate history rows; append events for each transition.

- [ ] **Step 5: Verify repository behavior**

Run: pytest tests/test_mission_store.py tests/test_mission_policy.py -v

Expected: all state, event sequencing, transaction, idempotency, and redaction tests pass.

- [ ] **Checkpoint**

Inspect: git diff -- backend/models/mission.py backend/services/mission_store.py backend/services/mission_policy.py tests/test_mission_store.py tests/test_mission_policy.py

---

### Task 4: Secure Operator Sessions, CSRF, Rate Limits, and WebSocket Tickets

**Files:**

- Create: backend/services/session_auth.py
- Create: backend/routers/auth.py
- Create: tests/test_auth_sessions.py
- Create: tests/test_auth_boundaries.py
- Modify: backend/auth.py
- Modify: backend/main.py
- Modify: tests/conftest.py

**Interfaces:**

- Produces validate_telegram_init_data(init_data: str, now: datetime) -> TelegramIdentity.
- Produces SessionAuthService.create_session(identity: TelegramIdentity, request_origin: str) -> SessionBootstrap.
- Produces SessionAuthService.require_operator(request: Request) -> OperatorContext.
- Produces SessionAuthService.consume_websocket_ticket(ticket: str, origin: str) -> OperatorContext.
- Produces RateLimiter.check(scope: str, operator_id: int) -> None.

- [ ] **Step 1: Write failing security tests without the global test override**

    def test_expired_telegram_auth_date_is_rejected(client, signed_init_data):
        response = client.post("/api/auth/telegram-session", headers={
            "X-Telegram-Init-Data": signed_init_data(auth_date=EXPIRED_UNIX_TIME)
        })
        assert response.status_code == 401

    def test_unallowlisted_operator_cannot_create_session(client, signed_init_data):
        response = client.post("/api/auth/telegram-session", headers={
            "X-Telegram-Init-Data": signed_init_data(user_id=999999)
        })
        assert response.status_code == 403

    def test_state_change_requires_session_and_csrf(client, authenticated_session):
        response = client.post("/api/missions", json=MISSION_BODY)
        assert response.status_code == 403

    def test_websocket_ticket_is_one_time(websocket_client, authenticated_session):
        ticket = issue_ticket(authenticated_session)
        assert websocket_client.connect_with_ticket(ticket).operator_id == ALLOWED_USER_ID
        assert websocket_client.connect_with_ticket(ticket).close_code == 4401

- [ ] **Step 2: Implement low-level Telegram validation**

Retain constant-time HMAC comparison. Require hash, parse user safely, validate auth_date as an integer, and reject auth_date older than HERMES_TELEGRAM_MAX_AGE_SECONDS. Do not treat loopback as authenticated in production or tunnel mode.

- [ ] **Step 3: Implement opaque session and CSRF flow**

Generate a cryptographically random opaque session id and CSRF token. Store only SHA-256 hashes and expiry in the mission database. Set the session cookie with HttpOnly, Secure, SameSite=Strict, Path=/, and a bounded Max-Age in production. Return the CSRF token in the response body only once. Require X-CSRF-Token on every state-changing route.

The WebSocket ticket is a distinct random value with a short expiry and consumed_at timestamp. It is minted only by an authenticated CSRF-protected route and is invalid after its first successful use.

- [ ] **Step 4: Wire routes and remove unsafe test assumptions**

Register the auth router in main.py. Use dependency injection for protected routers. Replace the autouse auth override in tests/conftest.py with an explicit authenticated_session fixture so tests can intentionally exercise rejection paths.

- [ ] **Step 5: Implement in-memory limits**

Use a lock-protected sliding window keyed by scope and operator id. Configure separate limits for session creation, mission creation, turn submission, approval decision, ticket issue, and social dispatch. Exceeding a limit must raise HTTP 429 before creating a row or subprocess.

- [ ] **Step 6: Verify**

Run: pytest tests/test_auth_sessions.py tests/test_auth_boundaries.py -v

Expected: valid signature passes, invalid/expired/unauthorized requests fail closed, CSRF is required, tickets cannot replay, and rate-limited requests have no side effect.

- [ ] **Checkpoint**

Inspect: git diff -- backend/auth.py backend/main.py backend/services/session_auth.py backend/routers/auth.py tests/conftest.py tests/test_auth_sessions.py tests/test_auth_boundaries.py

---

### Task 5: Implement the AGY One-Writer Session Manager

**Files:**

- Create: backend/services/agy_session_manager.py
- Create: tests/test_agy_session_manager.py
- Modify: backend/services/agy_protocol.py
- Modify: backend/services/mission_store.py
- Modify: backend/services/project_registry.py

**Interfaces:**

- Produces AgySessionManager.start_run(run_id: UUID) -> None.
- Produces AgySessionManager.enqueue_turn(run_id: UUID, turn_id: UUID, message: str) -> None.
- Produces AgySessionManager.cancel_run(run_id: UUID) -> None.
- Produces AgySessionManager.reconcile_incomplete_runs() -> list[RunReconciliation].
- Uses _build_argv(profile: ProjectProfile, run: RunRecord) -> list[str].
- Uses one asyncio.Queue[QueuedTurn] per active AGY run.

- [ ] **Step 1: Write failing subprocess contract tests**

Use a fake executable fixture that reads NDJSON stdin and writes the saved stream fixture. Do not call real AGY from unit tests.

    async def test_turns_are_serialized_for_one_run(manager, running_run):
        first = await manager.enqueue_turn(running_run.id, UUID1, "first")
        second = await manager.enqueue_turn(running_run.id, UUID2, "second")
        await manager.wait_until_idle(running_run.id)
        assert fake_process.received_messages == ["first", "second"]

    async def test_exit_zero_without_result_becomes_interrupted(manager, running_run):
        fake_process.exit_without_result(0)
        await manager.wait_for_terminal(running_run.id)
        assert store.get_run(running_run.id).state == MissionState.INTERRUPTED

    async def test_cancel_is_idempotent_and_kills_process_tree_once(manager, running_run):
        await manager.cancel_run(running_run.id)
        await manager.cancel_run(running_run.id)
        assert fake_process.termination_calls == 1

- [ ] **Step 2: Implement typed argv construction**

Construct an argv list from the configured AGY executable, optional --project only when agy_project_id is configured, --agent for the configured agent profile, --input-format stream-json, and --output-format stream-json. Set cwd to ProjectProfile.workspace_path. Use shell=False, a sanitized environment allowlist, and Windows process-group creation flags required for bounded child cleanup.

Never append user strings as flags. The user message is written as an NDJSON stdin line after the process is running.

- [ ] **Step 3: Implement process and stream lifecycle**

Start stdout and stderr reader tasks immediately. stdout is parsed line by line through parse_agy_stream_line. stderr is redacted and stored as diagnostic events. A result event completes the active turn; only one turn may be sent after the prior result. Close stdin for graceful shutdown, wait with a timeout, then terminate the process group only if needed.

Persist the provider conversation id from init/result before accepting another turn. A successful result creates succeeded plus needs_verification unless a profile explicitly declares no verification requirement.

- [ ] **Step 4: Implement recovery classification**

At app startup, do not attempt to reconstruct a vanished stdin stream. For a stored running process, verify process identity includes pid, start timestamp, executable basename, and run id marker. If it cannot be proven alive with an active manager, mark interrupted. If a process appears alive but cannot be safely attached, mark unknown and expose an explicit resume option using the provider conversation id.

- [ ] **Step 5: Verify**

Run: pytest tests/test_agy_session_manager.py tests/test_agy_protocol.py -v

Expected: queue ordering, protocol parsing, graceful cancellation, no false success, and restart classification all pass.

- [ ] **Checkpoint**

Inspect: git diff -- backend/services/agy_session_manager.py backend/services/agy_protocol.py backend/services/mission_store.py tests/test_agy_session_manager.py

---

### Task 6: Expose Mission APIs, Durable Events, and Authenticated Event Streaming

**Files:**

- Create: backend/services/mission_service.py
- Create: backend/routers/missions.py
- Create: backend/websockets/missions.py
- Create: tests/test_mission_api.py
- Create: tests/test_mission_events.py
- Modify: backend/main.py
- Modify: docs/API.md

**Interfaces:**

- Produces POST /api/missions, GET /api/missions, GET /api/missions/{id}, POST /api/missions/{id}/turns, POST /api/missions/{id}/cancel, GET /api/missions/{id}/events, GET /api/capabilities.
- Produces POST /api/auth/websocket-ticket.
- Produces WebSocket /ws/missions/{mission_id}, authenticated by a one-time ticket in the first client message.
- Uses MissionService.create_mission, submit_turn, cancel_mission, get_events_after, and publish_event.

- [x] **Step 1: Write failing API tests**

    def test_create_mission_is_idempotent(authenticated_client):
        first = authenticated_client.post("/api/missions", json=MISSION_BODY, headers=CSRF_HEADERS)
        second = authenticated_client.post("/api/missions", json=MISSION_BODY, headers=CSRF_HEADERS)
        assert first.status_code == 201
        assert second.status_code == 200
        assert second.json()["mission_id"] == first.json()["mission_id"]

    def test_second_turn_is_queued_not_written_concurrently(authenticated_client, running_mission):
        response = authenticated_client.post(
            f"/api/missions/{running_mission}/turns",
            json=SECOND_TURN_BODY,
            headers=CSRF_HEADERS,
        )
        assert response.status_code == 202
        assert response.json()["state"] == "queued"

    def test_event_cursor_replays_only_new_events(authenticated_client, mission):
        first = get_events(mission.id, after_sequence=0)
        second = get_events(mission.id, after_sequence=first[-1]["sequence"])
        assert len(second) == 0

- [x] **Step 2: Implement service orchestration**

MissionService validates the profile, checks rate/concurrency policy, creates the mission and run atomically, emits mission.created and run.queued, and invokes the selected executor only after persistence succeeds. Every public response includes next_action and correlation_id.

A failed process start must transition the persisted run to failed and emit a typed event. A client disconnect does not call cancel.

- [x] **Step 3: Implement event replay and WebSocket flow**

REST event replay reads durable sequence rows. The WebSocket first accepts the connection, requires a JSON auth message containing its ticket, consumes the ticket, checks mission ownership, replays events after the requested cursor, then receives only server fan-out events. It does not accept arbitrary command messages.

On backpressure or client error, drop the connection only. Do not drop database events or the underlying mission.

- [x] **Step 4: Update API documentation from the Pydantic schema**

Document the exact request, response, error codes, cursor semantics, and WebSocket auth handshake. Remove claims that every endpoint always returns HTTP 200; document expected 201, 202, 401, 403, 409, 422, 429, 503, and 504 responses.

- [x] **Step 5: Verify**

Run: pytest tests/test_mission_api.py tests/test_mission_events.py -v

Expected: protected route, idempotency, cursor, queue, cancellation, and ticket behavior pass.

- [x] **Checkpoint**

Inspect: git diff -- backend/services/mission_service.py backend/routers/missions.py backend/websockets/missions.py backend/main.py docs/API.md tests/test_mission_api.py tests/test_mission_events.py

---

### Task 7: Add the Mobile Mission Control Experience Without Rewriting the Existing UI

**Files:**

- Create: static/mission-control.css
- Create: static/mission-control.js
- Modify: static/index.html
- Create: tests/test_mission_ui.py
- Create: tests/test_mission_ui_browser.py

**Interfaces:**

- Uses GET /api/missions, POST /api/missions, POST /api/missions/{id}/turns, GET /api/missions/{id}/events, and POST /api/auth/websocket-ticket.
- Exposes window.HermesMissionControl.mount(root: HTMLElement).
- Maintains client cursor per mission in sessionStorage under hermes.mission.<id>.sequence.
- Does not use terminal/browser/swarm WebSockets.

- [ ] **Step 1: Write failing DOM and browser tests**

    def test_mission_control_uses_semantic_controls_and_status_regions(page):
        page.goto(APP_URL)
        assert page.locator("[data-mission-control]").count() == 1
        assert page.locator("button[data-action='create-mission']").count() == 1
        assert page.locator("[aria-live='polite']").count() >= 1

    def test_mobile_flow_preserves_visible_send_and_approval_actions(page):
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(APP_URL)
        assert page.locator("[data-action='send-turn']").bounding_box()["y"] < 844

- [ ] **Step 2: Mount a focused view**

Add a single Mission Control mount in the Doh-Nut operational context and a route/open action through the existing drawer/navigation. Do not add a seventeenth always-visible dock control. The view contains:

- project and role selector;
- mission list with live source/time labels;
- conversation stream;
- turn input with queued/sending/blocked state;
- artifacts and verification badge;
- approval drawer with immutable summary;
- cost/capacity indicator;
- capability health panel;
- recovery action for interrupted/unknown runs.

- [ ] **Step 3: Implement robust client state**

The client sends CSRF headers, creates idempotency UUIDs with crypto.randomUUID, fetches durable events before opening the mission WebSocket, and saves only the event cursor to sessionStorage. It reconnects with exponential delay capped at 30 seconds. On reconnect it first uses the REST cursor endpoint, preventing UI gaps if a WebSocket event was missed.

Never render raw event HTML. Use textContent and safe URL allowlists for artifact links.

- [ ] **Step 4: Implement responsive/accessibility behavior**

Use dynamic viewport sizing, safe-area padding, contained scroll regions, 44 pixel minimum actions, visible focus, aria-live for event status, semantic form labels, and an explicit cancel confirmation. Long logs must not force the entire page into a fixed no-scroll viewport.

- [ ] **Step 5: Verify browser flows**

Run: pytest tests/test_mission_ui.py -v

Run the browser suite at 360 x 740, 390 x 844, 768 x 1024, and desktop. Verify create, send, queued turn, reconnect/replay, artifact opening, expired approval, keyboard focus, and no horizontal overflow.

- [ ] **Checkpoint**

Inspect: git diff -- static/index.html static/mission-control.css static/mission-control.js tests/test_mission_ui.py tests/test_mission_ui_browser.py

---

### Task 8: Replace Social Status Fiction With a Verifiable Campaign and Approval Ledger

**Files:**

- Create: backend/services/social_campaign_service.py
- Create: tests/test_social_campaign_service.py
- Modify: backend/routers/social.py
- Modify: backend/routers/dohnut.py
- Modify: backend/services/mission_store.py
- Modify: static/mission-control.js
- Modify: docs/API.md

**Interfaces:**

- Produces create_campaign(project_id, source_facts, drafts, assets) -> Campaign.
- Produces request_approval(campaign_id, platform, account_id, content_sha256, media_sha256) -> Approval.
- Produces decide_approval(approval_id, decision, operator) -> Approval.
- Produces assert_approval_valid_for_dispatch(approval_id, attempt) -> None.
- Uses PublicationState prepared, awaiting_confirmation, submitted, published, failed, unknown.

- [ ] **Step 1: Write failing social truthfulness tests**

    def test_local_approval_does_not_mark_post_published(service, approved_campaign):
        attempt = service.create_attempt(approved_campaign, platform="instagram")
        assert attempt.state == "prepared"
        assert attempt.remote_post_id is None
        assert attempt.published_at is None

    def test_content_change_invalidates_existing_approval(service, campaign):
        approval = service.request_approval(campaign.id, "x", ACCOUNT, HASH_A, [])
        with pytest.raises(ApprovalMismatch):
            service.assert_approval_valid_for_dispatch(approval.id, content_sha256=HASH_B, media_sha256=[])

    def test_unknown_dispatch_blocks_automatic_retry(service, submitted_attempt):
        service.mark_unknown(submitted_attempt.id, "network_lost_after_submit")
        with pytest.raises(ReconciliationRequired):
            service.retry(submitted_attempt.id)

- [ ] **Step 2: Model source facts and immutable content**

Create a campaign snapshot containing source references, brand truth hash, quote/claim validation result, content hash, media hash, platform, target account, draft version, and creator run id. Static/generated copy can be displayed as a draft but must be flagged when source facts are absent.

The legacy social endpoints must change their labels and response states to draft/prepared until the new campaign service is live. Do not write published_at on approval.

- [ ] **Step 3: Implement approval policy**

An approval expires at the project-configured TTL and is bound to one content/media/account/platform tuple. Store who requested it, who decided it, decision reason, and timestamp. Reject stale, changed, cross-platform, cross-account, and already-consumed approval requests.

- [ ] **Step 4: Verify**

Run: pytest tests/test_social_campaign_service.py tests/test_dohnut_api.py -v

Expected: approval, state transition, source warning, and legacy endpoint wording tests pass.

- [ ] **Checkpoint**

Inspect: git diff -- backend/services/social_campaign_service.py backend/routers/social.py backend/routers/dohnut.py backend/services/mission_store.py static/mission-control.js docs/API.md tests/test_social_campaign_service.py

---

### Task 9: Build Capability-Declared Social Delivery and Reconciliation

**Files:**

- Create: backend/services/social_delivery.py
- Create: tests/test_social_delivery.py
- Modify: backend/services/capability_probe.py
- Modify: backend/routers/dohnut.py
- Modify: backend/routers/missions.py
- Modify: config/projects/doh-nut.json

**Interfaces:**

- Produces SocialAdapter.capabilities() -> PlatformCapabilities.
- Produces SocialAdapter.prepare(attempt: PublicationAttempt) -> DeliveryResult.
- Produces SocialAdapter.submit(attempt: PublicationAttempt) -> DeliveryResult.
- Produces SocialAdapter.reconcile(attempt: PublicationAttempt) -> DeliveryResult.
- Uses adapters ManualConfirmationAdapter, WebBridgeAssistAdapter, and PlatformApiAdapter.

- [ ] **Step 1: Write failing adapter tests**

    def test_webbridge_navigation_is_prepared_not_published(adapter, approved_attempt):
        result = adapter.prepare(approved_attempt)
        assert result.state == "prepared"
        assert result.remote_post_id is None

    def test_receipt_is_required_before_published(adapter, approved_attempt):
        result = adapter.submit(approved_attempt)
        assert result.state == "submitted"
        with pytest.raises(MissingPublicationReceipt):
            adapter.mark_published(approved_attempt.id, receipt=None)

    def test_tiktok_defaults_to_human_confirmation(registry):
        assert registry.adapter_for("tiktok").capabilities().requires_human_confirmation is True

- [ ] **Step 2: Implement capabilities**

Every platform config declares draft, media_upload, publish, schedule, read_receipt, analytics, and requires_human_confirmation. The UI reads capability objects rather than assuming parity across TikTok, Instagram, Threads, Facebook, X, and YouTube.

WebBridgeAssistAdapter may health-check, navigate, and prefill only through its documented safe command shape. Its successful result is prepared or awaiting_confirmation. It must record an opaque browser action reference, not browser credentials or page contents.

- [ ] **Step 3: Implement receipts and reconciliation**

PlatformApiAdapter can be enabled only after OAuth, scopes, account mapping, webhook/polling contract, and platform policy are verified for that platform. It stores the remote post id and receipt metadata needed to reconcile. A network loss after submit becomes unknown. Only reconcile can resolve unknown to published, failed, or still_unknown.

- [ ] **Step 4: Lock down dangerous paths**

Remove any response wording that reports a navigation, draft insertion, or local database change as published/dispatched success. Existing direct social routes must require the same authenticated session, CSRF, approved attempt, and idempotency key as Mission Control.

- [ ] **Step 5: Verify**

Run: pytest tests/test_social_delivery.py tests/test_social_campaign_service.py -v

Expected: capability gates, receipt rules, unknown reconciliation, duplicate prevention, and safe legacy wording pass.

- [ ] **Checkpoint**

Inspect: git diff -- backend/services/social_delivery.py backend/services/capability_probe.py backend/routers/dohnut.py backend/routers/missions.py config/projects/doh-nut.json tests/test_social_delivery.py

---

### Task 10: Add Hermes as a Feature-Flagged Coordinator With One-Hop Handoffs

**Files:**

- Create: backend/services/hermes_adapter.py
- Create: tests/test_hermes_adapter.py
- Modify: backend/services/mission_service.py
- Modify: backend/services/mission_policy.py
- Modify: backend/services/capability_probe.py
- Modify: backend/routers/missions.py
- Modify: config/projects/doh-nut.json

**Interfaces:**

- Produces HermesAdapter.is_available() -> CapabilityResult.
- Produces HermesAdapter.submit(request: HermesTaskRequest) -> HermesTaskResult.
- Produces MissionService.propose_handoff(source_mission_id, request) -> HandoffProposal.
- Rejects handoff_depth greater than 1 and origin_mission_id already in ancestry.

- [ ] **Step 1: Write failing isolation tests**

    def test_hermes_disabled_does_not_break_agy_mission(service, agy_request):
        mission = service.create_mission(agy_request, OPERATOR)
        assert mission.primary_executor == PrimaryExecutor.AGY

    def test_handoff_cannot_return_to_ancestor_mission(service, agy_mission):
        handoff = service.propose_handoff(agy_mission.id, HERMES_PLAN_REQUEST)
        with pytest.raises(DelegationLoopError):
            service.propose_handoff(handoff.target_mission_id, AGY_RETURN_REQUEST)

    def test_hermes_plan_has_no_browser_or_social_permissions(adapter):
        result = adapter.submit(PLAN_REQUEST)
        assert result.status in {"succeeded", "unsupported"}
        assert "browser" not in result.granted_capabilities

- [ ] **Step 2: Implement the adapter boundary**

Use a Protocol interface so the first implementation can be a disabled adapter. Read Hermes availability from explicit configuration and a safe local capability probe. Do not scrape Hermes private databases or assume its config path. When enabled, submit only plan, verify, or Kanban profiles with source artifact ids and structured result parsing.

- [ ] **Step 3: Implement one-hop policy and external record linkage**

Store external_task_id, source artifact ids, ancestor mission ids, handoff depth, and result artifacts in the WebApp ledger. A returned Hermes proposal requires operator acceptance to create a new AGY mission. Never auto-spawn AGY from a Hermes result.

- [ ] **Step 4: Add optional Kanban mapping**

After a separate capability spike verifies the installed Hermes Kanban interface, add a mapping from mission id to external Kanban task id. Sync only summary status and artifact links. If the capability is absent or errors, retain the WebApp mission and display unsupported/degraded with a recovery action.

- [ ] **Step 5: Verify**

Run: pytest tests/test_hermes_adapter.py tests/test_mission_policy.py -v

Expected: disabled feature isolation, unsupported state, one-hop enforcement, and external-id persistence pass.

- [ ] **Checkpoint**

Inspect: git diff -- backend/services/hermes_adapter.py backend/services/mission_service.py backend/services/mission_policy.py backend/services/capability_probe.py tests/test_hermes_adapter.py

---

### Task 11: Implement the Astra-Aligned Orchestration Policy and Evaluation Loop

**Files:**

- Create: backend/services/orchestration_policy.py
- Create: backend/services/capability_registry.py
- Create: backend/services/evaluation_service.py
- Create: config/orchestration/defaults.json
- Create: tests/test_orchestration_policy.py
- Create: tests/test_capability_registry.py
- Create: tests/test_evaluation_service.py
- Modify: backend/models/mission.py
- Modify: backend/services/mission_store.py
- Modify: backend/services/mission_service.py
- Modify: backend/services/hermes_adapter.py
- Modify: backend/services/capability_probe.py
- Modify: docs/ASTRA-GRADE-ALIGNMENT.md

**Interfaces:**

- Produces OrchestrationPolicy.classify(request) -> RiskClass.
- Produces CapabilityRegistry.select(intent, project, executor) -> CapabilityReceipt.
- Produces PlanningPacketService.create_for_mission(mission, receipt, policy) -> PlanningPacket.
- Produces EvaluationService.decide(measurement) -> EvaluationDecision.
- Rejects a running Hermes coordinator mission without a complete packet, a registry receipt, and an in-budget execution policy.

- [ ] **Step 1: Write failing policy and containment tests**

    def test_multistep_hermes_mission_requires_complete_planning_packet(service):
        mission = service.create_hermes_plan(MULTISTEP_REQUEST)
        with pytest.raises(PlanningPacketRequired):
            service.start(mission.id)

    def test_external_text_cannot_grant_unregistered_capability(registry):
        receipt = registry.select("plan", DOH_NUT, HERMES)
        assert "shell" not in receipt.selected_capability_ids
        with pytest.raises(UnknownCapability):
            registry.resolve_requested_capability("browser_publish")

    def test_high_risk_intent_waits_for_narrow_human_approval(policy, request):
        assert policy.classify(request.with_browser_publish()) == RiskClass.HUMAN_REQUIRED
        assert policy.transition_for(request) == MissionState.WAITING_HUMAN

    def test_iteration_budget_exhaustion_stops_without_retry(service, packet):
        run = service.start_hermes_run(packet, iteration_budget=1)
        service.record_iteration(run.id)
        result = service.record_iteration(run.id)
        assert result.state == MissionState.NEEDS_VERIFICATION
        assert result.retry_scheduled is False

    def test_incomparable_measurement_cannot_verify_change(evaluations, record):
        decision = evaluations.decide(record.model_copy(update={"comparable": False}))
        assert decision == EvaluationDecision.NEEDS_VERIFICATION

- [ ] **Step 2: Define and validate the non-secret policy file**

Create config/orchestration/defaults.json with schema-validated risk classes, permitted mission intents, fixed capability profile ids, one-hop handoff limit, iteration budget, child-concurrency budget, elapsed-time budget, retry classes, and measurement rules. Use the local Astra-Grade values of 25 iterations and 3 children only as documented candidate defaults. A malformed, duplicate, unknown, or out-of-range policy must fail closed at startup and emit a safe diagnostic.

- [ ] **Step 3: Implement planning packets and risk gating**

Before a multi-step Hermes task can run, write a planning packet in the same transaction that allocates the run. The packet must reference only existing redacted artifacts, contain acceptance checks, hash its canonical content, and store a policy version. Classify dangerous, external, privileged, credential, CAPTCHA, 2FA, financial, browser-publish, and unknown-platform intent before adapter submission. Require a narrow approval that names the exact action, target, content hash where applicable, expiry, and operator identity.

- [ ] **Step 4: Implement a capability registry with least privilege**

The registry maps a declared intent such as plan, verify, kanban_sync, health_probe, code_index_read, or security_review to a fixed profile. Each profile lists allowed artifact types, maximum duration, network posture, and whether it can create a follow-up mission. Do not accept tool names, model names, executable paths, or profile ids from mission free text. Persist a capability receipt and a rejected-request diagnostic with sensitive text redacted.

- [ ] **Step 5: Implement the closed evaluation loop**

For a change-oriented mission, record a baseline artifact before one bounded action, collect a re-measurement with method and timestamp, compare only compatible metrics, then persist keep, revert, escalate, or needs-verification. Revert is a proposal until the operator accepts it; this policy must not silently mutate a repository, database, platform post, or runtime configuration.

- [ ] **Step 6: Add bounded read-only health adapters**

Expose Doctor, Skill Toolkit, Benchmark, code-index, and security-review integrations only through fixed capability profiles and bounded subprocess or API adapters. Apply timeouts, capture sanitized structured output, and report unavailable/degraded when the integration cannot be proven. These adapters never alter host configuration, credentials, provider routing, browser profile state, or social content.

- [ ] **Step 7: Verify**

Run:

    pytest tests/test_orchestration_policy.py tests/test_capability_registry.py tests/test_evaluation_service.py tests/test_hermes_adapter.py tests/test_mission_policy.py -v

Expected: packet completeness, registry containment, high-risk waiting-human gates, budget exhaustion, measurement truthfulness, disabled-Hermes isolation, and one-hop enforcement all pass.

- [ ] **Checkpoint**

Inspect: git diff -- backend/services/orchestration_policy.py backend/services/capability_registry.py backend/services/evaluation_service.py backend/models/mission.py backend/services/mission_store.py backend/services/mission_service.py backend/services/hermes_adapter.py backend/services/capability_probe.py config/orchestration/defaults.json tests/test_orchestration_policy.py tests/test_capability_registry.py tests/test_evaluation_service.py docs/ASTRA-GRADE-ALIGNMENT.md

---

### Task 12: Add Honest Capability Health, Cost Records, Restart Recovery, and Legacy Migration

**Files:**

- Create: backend/services/capability_probe.py
- Create: backend/cli/migrate_legacy_social.py
- Create: tests/test_capability_probe.py
- Create: tests/test_recovery.py
- Create: tests/test_legacy_social_migration.py
- Modify: backend/main.py
- Modify: backend/services/mission_store.py
- Modify: backend/services/mission_service.py
- Modify: docs/DEPLOYMENT.md
- Modify: docs/TROUBLESHOOTING.md

**Interfaces:**

- Produces CapabilityProbe.check_all() -> list[CapabilityResult].
- Produces MissionService.reconcile_startup() -> StartupReconciliation.
- Produces migrate_legacy_social(source: Path, destination: Path, dry_run: bool) -> MigrationReport.
- Produces record_cost(run_id: UUID, usage: UsageRecord | None, duration_seconds: float | None) -> CostRecord.

- [ ] **Step 1: Write failing operational truth tests**

    def test_file_existence_is_not_reported_as_online(probe, fake_agy_path):
        result = probe.check_agy()
        assert result.status in {"available", "degraded", "unavailable"}
        assert result.checked_at is not None
        assert result.evidence != "file_exists_only"

    def test_restart_without_terminal_result_is_interrupted(store, manager):
        run = store.create_running_run_without_result()
        reconciliation = manager.reconcile_incomplete_runs()
        assert reconciliation[0].new_state == MissionState.INTERRUPTED

    def test_dry_run_migration_changes_no_destination_data(tmp_path):
        report = migrate_legacy_social(SOURCE_DB, DESTINATION_DB, dry_run=True)
        assert report.written_rows == 0
        assert report.source_sha256

- [ ] **Step 2: Implement capability probes**

Probe executable availability, process health where safe, documented local health endpoints, database initialization, and tunnel accessibility separately. Every result has component, status, checked_at, evidence class, version when known, and recovery action. Do not expose raw endpoint headers, process command lines, secrets, or browser profile details.

- [ ] **Step 3: Implement startup reconciliation and cost summaries**

Call MissionService.reconcile_startup during lifespan after the store initializes. Persist a recovery event for every active run. Capture AGY usage from result events; record unavailable usage explicitly. The daily summary groups by project, executor, calendar day, and status. It must show zero only when a real zero is recorded.

- [ ] **Step 4: Implement dry-run migration**

Inventory legacy social databases and queues from explicitly configured paths. For SQLite, report row count, schema, primary key mapping, duplicates, invalid timestamps, and SHA-256. The real import uses a new target database, migration manifest, and transactional writes. Original source files remain unchanged.

- [ ] **Step 5: Verify**

Run: pytest tests/test_capability_probe.py tests/test_recovery.py tests/test_legacy_social_migration.py -v

Expected: health honesty, restart classification, usage missing state, dry run, duplicate detection, and source preservation pass.

- [ ] **Checkpoint**

Inspect: git diff -- backend/services/capability_probe.py backend/cli/migrate_legacy_social.py backend/main.py backend/services/mission_store.py docs/DEPLOYMENT.md docs/TROUBLESHOOTING.md tests/test_capability_probe.py tests/test_recovery.py tests/test_legacy_social_migration.py

---

### Task 13: Run the Full Security, API, UI, and Controlled AGY Acceptance Suite

**Files:**

- Modify: tests/test_empirical_stress.py
- Modify: tests/test_swarm_api.py
- Modify: tests/test_system_api.py
- Modify: tests/test_websockets_e2e.py
- Create: tests/test_mission_e2e.py
- Create: docs/release-checklists/remote-mission-control.md
- Modify: docs/PRD.md
- Modify: docs/README.md

**Interfaces:**

- Produces an acceptance report linked to exact test commands, sanitized AGY evidence, viewport screenshots, and capability snapshot.
- Does not change provider configuration, register a daemon, post social content, or kill host processes as part of the test suite.

- [ ] **Step 1: Harden existing tests around the new security boundary**

Update legacy API tests to create an explicit authenticated test session and CSRF token. Add negative tests proving old unauthenticated social, swarm, system, and WebSocket routes cannot obtain mission/sensitive operations through the new surface. Preserve tests for legacy endpoints whose documented behavior remains supported.

- [ ] **Step 2: Write end-to-end acceptance tests**

    def test_operator_can_create_resume_and_replay_a_doh_nut_agy_mission(app, fake_agy):
        mission = create_authenticated_mission(agent="dohnut-social-autopilot")
        send_turn(mission.id, "Prepare only. Do not publish.")
        wait_for_result(mission.id)
        reconnect_events = fetch_events(mission.id, after_sequence=0)
        assert has_event(reconnect_events, "agy.result")
        assert mission_detail(mission.id)["verification_state"] == "needs_verification"

    def test_social_action_requires_approval_receipt_and_reconciliation(app):
        attempt = create_prepared_attempt()
        assert approve(attempt).state == "prepared"
        assert cannot_mark_published_without_receipt(attempt)
        assert unknown_attempt_requires_reconciliation(attempt)

- [ ] **Step 3: Run the focused suites**

Run:

    pytest tests/test_agy_protocol.py tests/test_project_registry.py tests/test_mission_store.py tests/test_mission_policy.py -v
    pytest tests/test_auth_sessions.py tests/test_auth_boundaries.py tests/test_agy_session_manager.py -v
    pytest tests/test_mission_api.py tests/test_mission_events.py tests/test_social_campaign_service.py tests/test_social_delivery.py -v
    pytest tests/test_orchestration_policy.py tests/test_capability_registry.py tests/test_evaluation_service.py tests/test_hermes_adapter.py -v
    pytest tests/test_capability_probe.py tests/test_recovery.py tests/test_legacy_social_migration.py tests/test_mission_e2e.py -v

Expected: no failure, no hidden network dependency, no real social dispatch, and no unbounded subprocess left running.

- [ ] **Step 4: Run browser acceptance**

Use the existing browser automation path to verify Mission Control on desktop, 360 x 740, 390 x 844, and 768 x 1024. Capture evidence for:

- authenticated open;
- mission create;
- AGY stream event rendering through a fake process;
- reconnect/replay;
- keyboard focus;
- long log scrolling;
- expired approval;
- no horizontal overflow;
- no visible overlap;
- no console error on the critical flow.

- [ ] **Step 5: Conduct one controlled live AGY acceptance run**

Only after all fake-process and orchestration-policy tests pass, use an existing authenticated AGY session in G:/Doh-Nut. Select a planning/review role, submit a bounded read-only prompt that disallows files, browser, shell, and social publishing, and record the returned conversation id, result state, and redacted usage. The controlled run must include the saved planning packet, capability receipt, effective budget, and verification outcome. Then end the session cleanly. If credentials, quota, or provider behavior block this test, mark M2 blocked with the exact typed result; do not change provider auth or use dangerous permission flags.

- [ ] **Step 6: Publish the release checklist and update truth labels**

The release checklist must contain date, code revision, environment, config hash excluding secrets, tests, screenshots, capability snapshot, controlled AGY evidence, residual risks, and whether each milestone is accepted. Update PRD.md and docs/README.md only with verified implemented milestones, never planned ones.

- [ ] **Checkpoint**

Run: git diff --check

Run: git status --short

Review only the files touched by this plan. Do not stage or commit unrelated existing worktree changes.

---

## Requirement Traceability

| PRD requirement group | Tasks |
| --- | --- |
| REQ-MSN mission lifecycle, idempotency, replay, cancellation, resume | 3, 5, 6, 7, 11, 12, 13 |
| REQ-AGY protocol, workspace, profiles, result truth, errors, remote companion | 1, 2, 5, 6, 12, 13 |
| REQ-TEAM eight Doh-Nut roles | 2, 5, 7, 13 |
| REQ-HRM optional Hermes, packets, policy, Kanban, bounded handoffs | 10, 11, 12, 13 |
| REQ-SOC source truth, approval, adapters, receipts, reconciliation | 8, 9, 13 |
| REQ-SEC Telegram/session/CSRF/Origin/rate limits/redaction | 3, 4, 5, 6, 9, 11, 13 |
| REQ-UX mobile, accessible, source-aware status | 6, 7, 11, 13 |
| REQ-OPS capability truth, recovery, migration, cost | 3, 5, 11, 12, 13 |

## Completion Definition

The plan is complete only when M0 through the selected milestone have fresh evidence in the release checklist. A task is not complete because code exists, a test is skipped, a local process exits, a static UI card says ONLINE, a model claims confidence, or a route returns HTTP 200. The evidence must demonstrate the exact state the user will rely on, including planning-packet, capability, risk, budget, and evaluation evidence for every enabled Hermes coordinator profile.
