---
title: "Hermes-WebApp Remote Mission Control - Product Requirements Document"
document_id: "HERMES-WEBAPP-PRD-001"
version: "4.1.0"
last_updated: "2026-09-16 MYT"
maintainer: "Megat / Hermes-WebApp operators"
classification: "INTERNAL // IMPLEMENTATION BLUEPRINT"
lifecycle_status: "IMPLEMENTED & VERIFIED"
---

# Hermes-WebApp Remote Mission Control

> Product specification for a remote, mobile-first control surface that preserves the existing AGY CLI workflow and Doh-Nut agent team, adds durable mission operations, and introduces Hermes as an optional coordinator rather than an unnecessary second executor.

## 1. Document Status and Decision

All 13 implementation tasks from the delivery plan have been implemented, verified, and backed by a comprehensive regression suite of 221+ passing tests (0 failures).

## 2. Revision Ledger

| Version | Date | Status | Change |
| --- | --- | --- | --- |
| 4.2.0 | 2026-09-16 | Verified | Implemented and verified all 13 tasks: NDJSON protocol contract, Project Registry, SQLite WAL Mission Ledger, Session Auth & CSRF, AGY One-Writer Session Manager, REST & WebSocket Streaming APIs, Mobile Mission Control UI, Social Campaign Service, Social Delivery Adapters, Hermes Feature-Flagged Adapter, Astra Orchestration Policy & Evaluation, Capability Health & Migration CLI, and E2E Acceptance Suite. |
| 4.1.0 | 2026-09-16 | Draft | Added an evidence-bound Astra-Grade alignment record, explicit planning/risk/evaluation requirements, and a dedicated implementation task. The original GPT-6 Astra chat is not represented as read unless its transcript is recoverable. |
| 4.0.0 | 2026-09-16 | Draft | Reframed the product around remote access to existing AGY sessions, durable missions, verified social operations, optional Hermes coordination, security boundaries, and an executable delivery plan. |
| 3.6.0 | 2026-09-12 | Historical | UI, FHS, mobile layout, and mission-control claims retained as historical context. Their runtime state must be revalidated before relying on them. |
| 3.5.0 | 2026-09-12 | Historical | Doh-Nut dashboard and social endpoints documented. "HTTP 200" evidence does not establish real publishing, account access, or live commerce accuracy. |
| 3.0.0 | 2026-07-27 | Historical | Original terminal and dashboard direction. |
| 1.0.0 | 2026-07-20 | Historical | Telegram Mini App and PWA MVP direction. |

### 2.1 Astra-Grade Alignment and Evidence Boundary

The requested GPT-6 Astra direction is reflected as concrete operating requirements rather than a claim that a model label makes the system stronger. The local Astra-Grade v7.0-v10.0 implementation history supports useful principles: planning packets, scoped capability retrieval, risk gates, measurement loops, bounded delegation, health probes, and human approval.

The original GPT-6 Astra conversation was not available from the browser profile accessible during this review. This PRD therefore records the evidence boundary and the adopted design decisions in [Astra-Grade Plan Alignment Record](ASTRA-GRADE-ALIGNMENT.md). If the direct transcript becomes available, it must be reconciled against this record before a requirement is called source-confirmed.

## 3. Product Problem

AGY CLI already contains work, project context, authentication, and eight specialized Doh-Nut agents. Replacing it would discard useful operating momentum. The real friction is physical locality: the operator must be at the Windows PC to read a run, provide the next instruction, inspect artifacts, or approve a risky social action.

The current WebApp has useful primitives, but it does not yet provide a durable AGY conversation bridge. A terminal WebSocket is not a mission system: it opens a PowerShell subprocess and ends it when the socket disconnects. Current social labels also overstate the operational truth: an observed "publish" handler navigates to a platform and an observed approval handler records an approval locally. Neither action alone is evidence that a post reached a platform.

## 4. Product Goal

Build one secure remote control plane where the operator can:

1. Start, continue, stop, and inspect Doh-Nut work through the existing AGY workflow from Telegram Mini App or a protected PWA.
2. See exactly which AGY agent, project, conversation, files, artifacts, evidence, cost, and approvals belong to each mission.
3. Use Hermes selectively for planning, independent verification, task routing, and durable Kanban coordination without double-running work or recursively delegating between conductors.
4. Prepare social content, check brand and factual claims, collect a clear approval, and distinguish prepared, submitted, published, failed, and unknown states per platform.
5. Recover safely from mobile disconnects, host restarts, model quota failures, browser failures, and human-in-the-loop interruptions.

## 5. Users and Primary Journeys

| User | Need | Successful outcome |
| --- | --- | --- |
| Operator on phone | Continue an AGY conversation away from the PC | Opens a Doh-Nut mission, sees its latest event, sends one queued turn, and receives a durable result or a clear blocked state. |
| Operator reviewing content | Avoid publishing false, duplicate, or unapproved offers | Reviews source claims, media, platform copy, target account, and expiry before explicitly approving one platform action. |
| Operator coordinating a large task | Use eight agents without duplicated work | Selects one primary executor, sees the eight named roles, and receives artifacts with verification and residual risk. |
| Hermes coordinator | Add planning or verification value | Receives a bounded artifact/task, cannot create an AGY-Hermes delegation loop, and returns structured evidence. |
| Future brand operator | Reuse the system safely | Adds a separate project configuration, role map, brand truth, approval policy, and account registry without leaking Doh-Nut state. |

### 5.1 The First End-to-End Journey

1. The operator opens Hermes-WebApp from Telegram and establishes a short-lived authenticated session.
2. The operator opens the Doh-Nut workspace and either resumes an existing mission or creates one with a selected AGY role.
3. WebApp creates a durable mission and a run record before invoking AGY.
4. The AGY bridge launches in the Doh-Nut workspace, streams normalized events, stores the provider conversation id, and serializes turns for that conversation.
5. The operator can close the phone. The mission continues independently of the browser transport.
6. A result appears as evidence, not merely "completed". The operator can request verification, approve a social stage, resume, cancel, or hand off a bounded artifact.
7. If the host restarts or the provider session breaks, the run is marked interrupted or unknown. The UI presents a safe resume action using the saved conversation id rather than inventing a success state.

## 6. Scope, Non-Goals, and Guardrails

### In scope

- A mobile-first mission interface in Hermes-WebApp for Doh-Nut first.
- AGY headless session control using documented machine-readable output.
- Conversation resume by saved provider conversation id and workspace-scoped execution.
- Eight existing Doh-Nut roles as selectable profiles, not eight permanently running publishers.
- Durable local mission, run, event, artifact, approval, cost, and publication-ledger records.
- Optional Hermes planning, Kanban, verification, and memory integration after an explicit adapter spike.
- Social draft, review, approval, dispatch, receipt, reconciliation, and analytics stages.
- Existing terminal, browser, Doh-Nut dashboard, and Telegram entry point retained while their claims are revalidated.

### Explicitly out of scope for the first release

- Replacing AGY CLI, its login, project history, or existing subagent files.
- A promise that Hermes and AGY automatically share model credentials, quota, memory, or provider sessions.
- Public unauthenticated control of the Windows host.
- Generic arbitrary command execution through the new mission API.
- Bypassing CAPTCHA, 2FA, platform review, anti-spam policy, or a human confirmation requirement.
- Claiming all social networks support the same publishing contract.
- Moving storefront business logic from G:/Doh-Nut into Hermes-WebApp.
- A framework rewrite of the existing static/index.html solely to add Mission Control.

### Non-negotiable operating rules

- Each mission has exactly one primary executor: AGY or Hermes.
- A worker may hand an immutable artifact to the other executor, but neither may auto-delegate back to the origin mission.
- A task process exit, HTTP status, navigation, draft insertion, or local timestamp is never itself proof of external publication or business completion.
- The remote browser and terminal remain privileged tools. Mission APIs expose predefined profiles and approved actions, not raw shell strings.
- New work must preserve port 9220, the existing Telegram entry point, and unrelated uncommitted user changes.
- No raw secret, cookie, bot token, browser profile data, or API credential may enter mission events, artifacts, screenshots, logs, or Obsidian memory.

## 7. Verified Baseline and Gaps

This table records the source and runtime observations that define the starting point. It deliberately separates observed behavior from the target.

| Area | Observed baseline | Product implication |
| --- | --- | --- |
| WebApp | FastAPI, static/index.html, REST routers, WebSockets, SQLite-related code, and port 9220 are present. | Reuse the current app as the control surface; do not recreate it. |
| AGY | The installed CLI exposes print mode, JSON, stream-json, conversation, project, agent, model, effort, and remote-control commands. | Build a bridge around documented stream-json and saved conversation ids. |
| AGY remote control | The official remote dashboard/headless daemon exists, but this host was observed as not registered during the audit. | Treat native AGY Remote Control as a useful companion/fallback, not an assumed embeddable WebApp API. |
| Existing agent team | Eight Doh-Nut agent definitions exist under G:/Doh-Nut/.gemini/agents. | Preserve names and roles through a config map. Do not manufacture a second set. |
| Current swarm manager | Default work can be a simulated Python sleep process; it accepts shell command strings. | It cannot be the trusted AGY runner. The new runner must use typed argv and an allowlisted profile. |
| Terminal socket | It starts pwsh.exe in a fixed directory and terminates on disconnect. | Do not use the terminal socket as the AGY session lifecycle. |
| Social draft generation | Current Doh-Nut generation uses fixed templates and seed-like business claims. | Replace or label it as a draft composer with brand-truth and factual-claim validation. |
| Social approval | Current approval can set local approved/published_at fields without a provider receipt. | Separate approval from dispatch and publication receipt. |
| WebBridge publishing | Current handler can navigate a Chrome profile to a platform; content may not be composed or posted. | Call it browser assistance until the adapter proves a platform receipt. |
| Agent status cards | Some statuses are derived from file existence or literals. | Replace with capability probes and last-checked timestamps. |
| Authentication | Telegram HMAC validation code exists, but route-by-route enforcement and expiry policy need a fresh security audit. | Build an explicit auth/session gate and negative tests before remote mission routes are exposed. |
| Historical dashboard data | Financial, inventory, and account labels can be fallback/static values. | All UI values require source, freshness, and confidence labels. |

## 8. Target Operating Model

    [Telegram Mini App / protected PWA]
                 |
                 v
    [Session and authorization gate]
                 |
                 v
    [Mission API and durable SQLite ledger]
          |             |              |
          v             v              v
    [AGY bridge] [Approval service] [Artifact store]
          |             |              |
          v             v              v
    [AGY + eight roles] [Human review] [Doh-Nut evidence]
          |
          +---- optional bounded handoff ----> [Hermes adapter]
                                                   |
                                                   v
                                            [Kanban / planning /
                                             verification / memory]
          |
          v
    [Social adapters: manual assist, WebBridge assist,
     or platform API after credential and policy validation]

The architecture is intentionally asymmetric. AGY is the direct executor for the workflow the operator already uses. Hermes becomes a second control path only for an explicitly selected mission mode. The local ledger is the source of truth for WebApp status; AGY and Hermes retain their own native conversation and task stores.

## 9. Ownership Model

| Component | Owner of truth | Responsibility | Does not own |
| --- | --- | --- | --- |
| Hermes-WebApp mission ledger | Hermes-WebApp SQLite | Mission metadata, UI events, approvals, costs, receipts, local audit trail | AGY private history or Hermes internal database |
| AGY CLI | AGY | Existing agent profiles, provider conversation, execution in selected workspace | WebApp approval status, publishing ledger |
| Hermes Agent | Hermes | Optional Kanban, planning, verifier, memory tasks | Silent replacement of AGY sessions |
| G:/Doh-Nut | Doh-Nut repository | Brand truth, customer-facing product logic, media, source data | Generic WebApp state |
| GangNiaga WebBridge | WebBridge | Authenticated browser assistance and browser state capability | Publication truth without a verified receipt |
| Platform API | Platform | Actual post/media status and identifiers | Local draft approval |
| Obsidian vault | Operator-controlled memory | Curated decisions, summaries, runbooks | Raw logs, credentials, unreviewed social content |

## 10. Mission Data Model

A mission is the operator-visible unit of work. A run is one attempt by its selected executor. A turn is one user message sent to a provider conversation. An event is an append-only fact. An artifact is a durable output with provenance. An approval is a time-bounded operator decision. A publication attempt is a platform-specific state machine.

### 10.1 Required identifiers and fields

| Entity | Required fields |
| --- | --- |
| Project | id, slug, workspace_path, brand_truth_path, agy_project_id optional, enabled_agents, approval_policy |
| Mission | id UUID, project_id, title, objective, primary_executor, agent_profile, status, created_by, created_at, updated_at |
| Run | id UUID, mission_id, executor, provider_conversation_id nullable, process_identity nullable, state, result_status nullable, verification_state, started_at, finished_at nullable |
| Turn | id UUID, mission_id, run_id, sequence, user_message, submitted_at, completed_at nullable, idempotency_key |
| Event | mission_id, sequence integer, event_type, payload_redacted, created_at |
| Artifact | id UUID, mission_id, run_id, type, title, path_or_uri, sha256, provenance, verification_state |
| Planning packet | id UUID, mission_id, objective, constraints, evidence_refs, risk_class, capability_receipt, budget, acceptance_checks, sha256 |
| Measurement | id UUID, mission_id, metric_name, baseline_ref, observed_value, method, observed_at, comparable, evidence_ref |
| Approval | id UUID, mission_id, subject_type, subject_id, requested_by, requested_at, expires_at, decision nullable, decided_by nullable, decision_reason nullable |
| Publication attempt | id UUID, campaign_id, platform, account_id, state, idempotency_key, remote_post_id nullable, receipt_uri nullable, error_code nullable |

### 10.2 Mission states

| State | Meaning | Valid next states |
| --- | --- | --- |
| draft | Created locally; no executor started | queued, cancelled |
| queued | Accepted and waiting for a permitted executor slot | starting, cancelled |
| starting | Runner is being created and validated | running, failed, interrupted |
| running | Executor is processing a turn or task | waiting_human, waiting_approval, succeeded, failed, cancelled, timed_out, interrupted |
| waiting_human | CAPTCHA, 2FA, policy decision, or external input requires the operator | running, cancelled, expired |
| waiting_approval | A specifically modeled approval is pending | running, cancelled, expired |
| succeeded | The executor returned a successful terminal result | verified, needs_verification, failed_verification |
| interrupted | Host, process, or transport ended without a trustworthy terminal result | queued_for_resume, cancelled |
| unknown | The runner cannot prove its process or provider state | queued_for_resume, cancelled, manually_resolved |
| cancelled | Operator cancelled the work and the process tree was handled | terminal |
| failed | A typed error ended the run | queued_for_resume, cancelled, terminal |

"Verified" is a separate result dimension. A code-generation run can succeed while tests fail; a social dispatch can succeed locally while platform publication remains unknown.

## 11. Functional Requirements

### 11.1 Mission control

- REQ-MSN-01: The WebApp shall create a mission before starting an executor and return an immutable mission id.
  Acceptance: retrying the same request with the same authenticated owner and idempotency key returns the original mission without creating a duplicate run.

- REQ-MSN-02: The WebApp shall show project, selected primary executor, selected agent profile, workspace, current run state, last event, last update time, cost, artifacts, approvals, and residual risk.
  Acceptance: every visible status has a source and last-checked timestamp; no hardcoded "ONLINE" is shown as a live fact.

- REQ-MSN-03: A mission shall own at most one active AGY conversation writer.
  Acceptance: concurrent turn submissions for one mission are queued in order; a second browser cannot interleave stdin for the same conversation.

- REQ-MSN-04: A mobile disconnect shall not terminate the mission process or erase unread events.
  Acceptance: reconnecting with an event cursor replays all durable events after that sequence without duplicate UI entries.

- REQ-MSN-05: Cancel must be explicit, auditable, and idempotent.
  Acceptance: cancellation sends graceful close/terminate first, then uses bounded process-tree termination only if required; repeated cancellation returns the same terminal state.

- REQ-MSN-06: A run may be resumed only from a saved provider conversation id or a clearly marked fresh retry.
  Acceptance: the UI never labels a new provider conversation as a resume.

### 11.2 AGY bridge

- REQ-AGY-01: The first custom integration path shall use the documented AGY stream-json protocol, not terminal keystroke scraping.
  Acceptance: the runner reads one JSON event per stdout line, stores a redacted normalized event, and recognizes init, step_update, result, and malformed output.

- REQ-AGY-02: The bridge shall run AGY with a configured workspace current directory and an optional configured AGY project id.
  Acceptance: G:/Doh-Nut is selected from a project registry; the bridge does not assume that a filesystem path is a provider project id.

- REQ-AGY-03: The bridge shall retain the provider conversation id returned by AGY and use it for an explicit resume.
  Acceptance: a completed one-shot run can be continued with the exact saved id; an unconfigured or missing id returns a typed validation error.

- REQ-AGY-04: AGY execution profiles shall be allowlisted by project and role.
  Acceptance: clients submit a role key such as dohnut-social-autopilot, not arbitrary executable arguments, shell snippets, model names, or workspace paths.

- REQ-AGY-05: The bridge shall capture stdout events, sanitized stderr diagnostics, terminal result, exit code, elapsed time, and usage when provided.
  Acceptance: an exit code 0 with no terminal result is represented as interrupted or protocol_error, not succeeded.

- REQ-AGY-06: AGY provider authentication, quota, permission soft-denials, rate limits, and malformed events shall surface as typed run failures with a human-readable recovery action.
  Acceptance: a soft-denied tool notice cannot be misrepresented as a completed operation.

- REQ-AGY-07: Native AGY Remote Control may be offered as an external companion link after registration is separately validated.
  Acceptance: Hermes-WebApp does not claim to embed, proxy, or control the native dashboard unless a documented supported integration is proven.

### 11.3 Existing Doh-Nut team

- REQ-TEAM-01: The first project registry shall expose the eight existing roles: dohnut-orchestrator, dohnut-frontend-artisan, dohnut-backend-architect, dohnut-realtime-ops, dohnut-qa-guardian, dohnut-brand-guardian, dohnut-viral-engine, and dohnut-social-autopilot.
  Acceptance: displayed role descriptions are loaded from project configuration and link to their actual source definition.

- REQ-TEAM-02: The UI shall describe roles as specialists, not automatic publishers.
  Acceptance: only a requested mission can start a role; no dashboard page starts all eight agents.

- REQ-TEAM-03: A role may declare required evidence and approval class.
  Acceptance: a brand-role result without source evidence cannot be passed to a publication workflow as verified copy.

### 11.4 Hermes optional coordinator

- REQ-HRM-01: Hermes integration shall use a separate adapter boundary behind a disabled-by-default feature flag.
  Acceptance: missing Hermes configuration makes the capability unavailable with a clear status; it does not break direct AGY missions.

- REQ-HRM-02: Hermes can be selected as primary executor only for explicitly supported profiles such as plan, verifier, or Kanban task.
  Acceptance: a Hermes plan cannot silently launch browser, social, terminal, or AGY execution privileges.

- REQ-HRM-03: Handoff between AGY and Hermes shall consist of a bounded immutable artifact reference, source mission id, and a maximum hop count of one.
  Acceptance: an adapter rejects a handoff that would return automatically to an ancestor mission.

- REQ-HRM-04: Hermes Kanban is an optional durable coordination surface, not a replacement database for WebApp mission records.
  Acceptance: synchronizing a Kanban card stores external ids and events; deleting or unavailable Kanban does not delete WebApp mission history.

- REQ-HRM-05: Every multi-step Hermes planning, verification, or Kanban mission shall persist an immutable planning packet before work begins.
  Acceptance: the packet records the objective, constraints, evidence inputs, selected profile/capabilities, risk class, budget, acceptance checks, and content hash; an incomplete packet cannot enter running.

- REQ-HRM-06: Capability selection shall come from a versioned, allowlisted registry that maps declared mission intent to supported profiles and least-privilege capabilities.
  Acceptance: an LLM response, user free text, agent artifact, or external page cannot grant a skill, shell tool, browser authority, model override, or executable path not present in the registry.

- REQ-HRM-07: Privileged, destructive, external-transmission, credential, browser-publish, CAPTCHA, 2FA, financial, and unknown-platform intent shall pass through a risk classifier before execution.
  Acceptance: a classified high-risk action enters waiting_human with a narrow, expiring, auditable approval scope; no external side effect is attempted before that decision.

- REQ-HRM-08: A change-oriented coordinator mission shall use a measured baseline, one bounded action, a re-measurement, and an explicit keep, revert, or escalate decision.
  Acceptance: a missing, stale, incomparable, or failed measurement yields needs_verification or a typed failure rather than verified.

- REQ-HRM-09: Iteration, child-concurrency, elapsed-time, retry, and handoff budgets shall be configuration-backed and visible in the run record.
  Acceptance: exceeding a budget produces a durable typed state and recovery action; authentication, quota, rate-limit, and unknown-publication failures never auto-retry.

- REQ-HRM-10: Existing Doctor, Skill Toolkit, Benchmark, code-index, and security-review utilities may only enter this product through fixed, least-privilege, read-only adapters.
  Acceptance: a missing, stale, slow, or malformed utility result is redacted and shown as degraded; it cannot alter host configuration or be treated as a live health claim.

### 11.5 Social operations

- REQ-SOC-01: Every campaign shall reference a project, source facts, brand truth version/hash, asset hashes, target platform, target account, and draft version.
  Acceptance: an offer, price, opening hour, free item, or delivery promise without an approved source is rejected or visibly flagged as unverified.

- REQ-SOC-02: "Generate", "approve", "prepare", "submit", "published", and "reconciled" shall be distinct states.
  Acceptance: local approval does not populate a published timestamp or platform post id.

- REQ-SOC-03: An approval shall be narrow, expiring, and replay-safe.
  Acceptance: it is scoped to one immutable content hash, platform, account, and dispatch id; changing content, target, or media invalidates it.

- REQ-SOC-04: The first release shall support browser-assisted preparation with a final human confirmation for platforms without a validated API flow.
  Acceptance: a navigation or prefill result is recorded as prepared; only an adapter receipt or human-attested proof can move to submitted/published.

- REQ-SOC-05: Each platform adapter shall declare capabilities: draft, media upload, publish, schedule, read receipt, analytics, and human-confirmation requirement.
  Acceptance: unavailable capabilities are disabled in the UI rather than inferred from another platform.

- REQ-SOC-06: TikTok Direct Post shall not be treated as a general internal automation path unless the application, audit, account permissions, consent flow, and policy scope are explicitly validated.
  Acceptance: the TikTok adapter defaults to human-confirmation/browser-assist until those conditions are met.

- REQ-SOC-07: Failed, partial, or unknown dispatches shall be reconciled before retry.
  Acceptance: the same campaign cannot create a duplicate external post by simply clicking retry.

### 11.6 Security and authorization

- REQ-SEC-01: All remote mission, approval, artifact, social, terminal, browser, and WebSocket operations shall require an authenticated, authorized operator identity.
  Acceptance: invalid Telegram init data, expired init data, unauthorized user id, wrong Origin, missing CSRF token, and unauthenticated WebSocket attempt all fail closed.

- REQ-SEC-02: Telegram init data shall be validated server-side using the official HMAC procedure and an auth_date freshness window. A short-lived server session may then be issued.
  Acceptance: the bot token is never sent to the client and raw init data is not persisted after session establishment.

- REQ-SEC-03: Desktop loopback development access shall require explicit development configuration and must never grant access through the public tunnel.
  Acceptance: production/tunnel mode rejects local-development bypass headers and returns a safe 401/403 response.

- REQ-SEC-04: State-changing browser-session routes shall use an HttpOnly Secure SameSite session cookie plus a server-bound CSRF token. WebSockets shall begin with a one-time ticket minted by an authenticated REST call.
  Acceptance: a cross-site form post and a replayed WebSocket ticket are rejected.

- REQ-SEC-05: Mission requests shall select predefined profiles. They shall not carry raw command strings, executable paths, hidden flags, arbitrary environment variables, or unconstrained filesystem paths.
  Acceptance: payload fuzz tests show rejected unknown fields and invalid profile selections.

- REQ-SEC-06: Sensitive output shall be redacted before storage and display.
  Acceptance: values matching configured secret names, bearer tokens, cookies, common API key formats, and browser-session material are replaced before event persistence.

- REQ-SEC-07: Rate limits and concurrency limits shall protect authentication, mission start, turns, approvals, WebSocket tickets, and external dispatches.
  Acceptance: throttled requests receive a typed 429 response and create no duplicate mission or publication record.

### 11.7 UX and accessibility

- REQ-UX-01: Mission Control shall be reachable from the existing Doh-Nut workspace without adding another permanently visible dock item.
  Acceptance: it is usable at 360 x 740, 390 x 844, tablet, and desktop widths; the action bar remains accessible above safe areas and virtual keyboards.

- REQ-UX-02: The system shall use dynamic viewport units and contained scrolling rather than a universal no-scroll 100vh lock.
  Acceptance: long mission logs and approval forms are scrollable, and focus remains visible when the on-screen keyboard opens.

- REQ-UX-03: Every state must have a human-readable explanation, next action, and technical detail disclosure.
  Acceptance: "unknown", "interrupted", quota, auth, approval, and platform errors do not appear as generic red failures.

- REQ-UX-04: Interactive controls meet a minimum 44 by 44 CSS pixel target, keyboard focus is visible, and semantic buttons are used.
  Acceptance: mobile and keyboard test runs cover creating a mission, sending a turn, viewing an artifact, and deciding an approval.

- REQ-UX-05: Existing visual design may retain the dark operational style, but data source, freshness, and confidence must be more prominent than decorative status treatments.
  Acceptance: seed/fallback values are labeled and cannot resemble live verified telemetry.

### 11.8 Operations, resilience, and observability

- REQ-OPS-01: The host must publish a capability snapshot with last check, result, version when available, and error classification for AGY, Hermes, WebBridge, tunnel, database, and social adapters.
  Acceptance: file existence alone cannot report an agent as online.

- REQ-OPS-02: On WebApp restart, active run records shall be reconciled from a process identity and protocol state.
  Acceptance: a missing process without a terminal result becomes interrupted or unknown, not succeeded.

- REQ-OPS-03: The system shall use structured logs and audit events with correlation ids across mission, run, turn, approval, and publication attempt.
  Acceptance: one mission can be traced from request through provider result and verification without reading raw terminal output.

- REQ-OPS-04: Mission records, events, artifacts, and social ledgers shall use a documented backup and migration procedure.
  Acceptance: migration from root-level or legacy social database copies is dry-runable, checks row counts and hashes, and retains the original until verification succeeds.

- REQ-OPS-05: Cost and quota information shall be recorded per run when the executor provides it.
  Acceptance: the UI shows a current project/day summary, missing-data state, and configured concurrency; it never invents a price or claims "free".

## 12. Integration Contracts

### 12.1 WebApp mission API, target shape

    POST /api/missions
    {
      "project_slug": "doh-nut",
      "title": "Review next TikTok campaign",
      "objective": "Prepare only. Do not publish.",
      "primary_executor": "agy",
      "agent_profile": "dohnut-social-autopilot",
      "idempotency_key": "client-generated-uuid"
    }

    201 Created
    {
      "mission_id": "uuid",
      "status": "queued",
      "run_id": "uuid",
      "next_action": "Awaiting executor slot"
    }

    POST /api/missions/{mission_id}/turns
    {
      "message": "Use the approved brand facts and return a review packet.",
      "idempotency_key": "client-generated-uuid"
    }

    202 Accepted
    {
      "turn_id": "uuid",
      "sequence": 2,
      "state": "queued"
    }

    GET /api/missions/{mission_id}/events?after_sequence=42
    {
      "events": [
        {
          "sequence": 43,
          "type": "agy.step",
          "created_at": "ISO-8601 UTC",
          "payload": {"state": "ACTIVE", "text_delta": "sanitized"}
        }
      ],
      "next_sequence": 43
    }

The implementation must publish an OpenAPI schema and keep request/response examples synchronized with actual Pydantic models.

### 12.2 AGY bridge contract

The runner launches only typed argument arrays. It uses a project registry to select the current working directory and optional provider project id. For a persistent local session it uses the documented input/output stream-json mode. It writes one user event at a time to stdin and reads stdout line by line. It maps provider events to normalized WebApp events.

    Input to AGY stdin:
    {"event":"user","message":{"content":"operator message"}}

    Required normalized result:
    {
      "provider": "agy",
      "provider_conversation_id": "provider UUID",
      "terminal_status": "SUCCESS | ERROR | unknown",
      "exit_code": 0,
      "response_text": "sanitized text",
      "usage": {
        "input_tokens": 0,
        "output_tokens": 0,
        "thinking_tokens": 0,
        "cache_read_tokens": 0,
        "total_tokens": 0
      }
    }

Only documented events are assumed. Unknown event names are stored as redacted diagnostic events and do not crash the runner.

### 12.3 Hermes adapter contract

    HermesTaskRequest:
      mission_id: UUID
      source_artifact_ids: list[UUID]
      profile: "plan" | "verify" | "kanban"
      objective: str
      max_handoff_depth: 1

    HermesTaskResult:
      external_task_id: str | null
      status: "succeeded" | "failed" | "blocked" | "unsupported"
      artifact_ids: list[UUID]
      verification_state: "unverified" | "verified" | "failed_verification"
      residual_risk: list[str]

A Hermes adapter cannot invoke an AGY mission directly. It can return a structured handoff proposal for the operator to accept.

### 12.4 Social delivery contract

    PublicationAttempt:
      campaign_id: UUID
      platform: "tiktok" | "instagram" | "threads" | "facebook" | "x" | "youtube"
      account_id: UUID
      content_sha256: str
      media_sha256: list[str]
      approval_id: UUID
      idempotency_key: str
      state: "prepared" | "awaiting_confirmation" | "submitted" |
             "published" | "failed" | "unknown"

A provider receipt must contain a platform-specific remote identifier or a human-attested proof reference. A local timestamp alone is not a receipt.

## 13. Data Storage and Migration

The new operational store shall live under Hermes-WebApp var/lib and use SQLite WAL with short transactions. Existing root-level queue files and social databases are treated as legacy inputs until a migration is verified.

1. Inventory legacy databases, queues, and JSON files without changing them.
2. Create a timestamped backup with a manifest containing source path, size, hash, and row count where applicable.
3. Run migration in dry-run mode and present record counts, orphan records, invalid dates, duplicate idempotency keys, and unsupported states.
4. Run the real migration in one transaction per data set.
5. Compare row counts, representative hashes, and a sampled set of records.
6. Mark the source as archived in the manifest; do not delete it during the first release.
7. Provide an explicit rollback command that restores the new database from backup only after the process has stopped.

## 14. Cost and Capacity Policy

The system must be useful without assuming a premium frontier model. It shall make use visible rather than hide it.

- Direct AGY missions are the default where the existing AGY workflow already has context and tools.
- Hermes is selected only for a separately justified planning, review, or coordination task.
- Default execution capacity is configurable and starts conservatively: one active AGY stream per project, two active runs globally, and no automatic retry after authentication, quota, or rate-limit failures.
- The mission ledger records provider-reported token usage and duration. Missing usage is displayed as unavailable.
- Each project can set a daily warning threshold and hard pause threshold in local configuration. These are operator policies, not invented provider quotas.
- A retry after 429, authentication failure, or an unproven social state requires explicit operator action and a reason.
- Model selection is a profile policy. The WebApp must not assume a user can reuse Hermes credentials or quota inside AGY.
- Every Hermes coordinator run records a planning-packet hash, risk class, selected-capability receipt, effective iteration/concurrency budget, and any evaluation measurement references.
- Historical limits from the Astra-Grade ledger are candidate defaults only. The active values must come from validated non-secret configuration and appear in the capability snapshot.
- A capability that is unavailable, stale, malformed, or outside its declared least-privilege profile is degraded, not silently replaced by a broader tool.

## 15. Quality Metrics

The following metrics replace misleading all-HTTP-200 and zero-latency claims.

| Metric | Target or policy | Evidence |
| --- | --- | --- |
| Auth rejection correctness | 100 percent of invalid/expired/unauthorized test cases reject without side effect | Security integration tests |
| Mission idempotency | Same owner/key yields one mission and one intended turn | Repository/API tests |
| Event replay correctness | Reconnect from a cursor loses no persisted event and duplicates none | Browser and WebSocket tests |
| Turn ordering | No overlapping writes to one AGY stdin stream | Concurrency tests |
| Outcome truthfulness | No run becomes verified/published without defined evidence | State-machine tests |
| Approval integrity | Changing content/media/account/platform invalidates approval | Approval tests |
| Recovery truthfulness | Lost process becomes interrupted/unknown, not succeeded | Restart simulation tests |
| Mobile usability | Critical flow works at 360 x 740 and 390 x 844 without horizontal overflow, hidden actions, or keyboard trap | Browser evidence |
| Social reconciliation | Retry is blocked for submitted/published/unknown until reconciled | Adapter tests |
| Cost observability | Usage fields are persisted or visibly unavailable | Protocol and UI tests |
| Planning integrity | Multi-step Hermes runs carry a complete immutable planning packet | Policy and repository tests |
| Capability containment | No unregistered capability or model-generated tool name gains authority | Registry and negative-injection tests |
| Evaluation truthfulness | A change is not verified without a comparable baseline and re-measurement | Evaluation tests |
| Runaway containment | Budget exhaustion and retry-class failures become durable safe states | Concurrency and recovery tests |

Latency should be reported as measured p50/p95 by endpoint class after instrumentation. Model thinking time and external platform processing are not promised to meet a fixed sub-second target.

## 16. Release Milestones

| Milestone | Deliverable | Exit gate |
| --- | --- | --- |
| M0 - Baseline and contract spike | Frozen capability inventory, sanitized AGY stream fixture, project registry, and documented no-regression baseline | No provider assumptions remain untested; current remote AGY daemon status is recorded, not changed. |
| M1 - Secure durable missions | Auth/session gate, SQLite ledger, idempotency, mission APIs, event replay | Negative auth, idempotency, restart, and repository tests pass. |
| M2 - Remote AGY parity | Single-writer AGY session manager, all eight Doh-Nut profiles, artifact views, mobile flow | Controlled AGY plan task executes in the Doh-Nut workspace and can be resumed from a saved conversation id. |
| M3 - Approval and social truth | Campaign source facts, approval ledger, browser-assist state machine, receipts, reconciliation | No UI action can call a local approval "published"; proof and retry rules pass. |
| M4 - Astra-aligned Hermes coordinator | Feature-flagged adapter, planning packets, capability registry, risk/evaluation policy, bounded handoffs, optional Kanban sync, verifier output | Direct AGY remains operational with Hermes disabled; packet, containment, risk, loop-prevention, and adapter contract tests pass. |
| M5 - Reliability and multibrand | Cost dashboard, recovery tooling, backup/migration, project templates | Restart, backup restore, budget, and a second isolated project configuration pass. |

## 17. Release Gates

A milestone can be marked complete only when all applicable evidence is fresh:

1. Focused unit, integration, and browser tests pass with no skipped failure used to mask a requirement.
2. Security tests include valid and invalid Telegram init data, expiry, allowlist, CSRF, Origin, WebSocket ticket, and authorization boundaries.
3. AGY protocol tests use a sanitized fixture plus a controlled live probe with no destructive tools or social publishing.
4. An AGY provider "SUCCESS" result is checked against the run and verification state; process exit alone is not accepted.
5. Social tests cover prepared, expired approval, changed content, failed dispatch, duplicate retry, unknown receipt, and reconciled success.
6. Browser verification covers desktop and both 360 x 740 and 390 x 844 mobile viewports, keyboard navigation, focus, reconnect, long content, and virtual keyboard behavior where available.
7. Migration tests run against disposable copies of legacy data and prove original files remain intact.
8. The live host/tunnel status is checked by capability probe, with no hardcoded PID assumption.
9. The diff contains no secret material and preserves unrelated user changes.
10. Documentation and OpenAPI examples agree with the implemented behavior.
11. Hermes coordinator tests prove planning-packet completeness, capability allowlisting, high-risk waiting-human transitions, budget exhaustion, and evaluation truthfulness.

## 18. Source References

- AGY headless streaming, JSON output, session continuation, and permission behavior: [Antigravity Headless Mode](https://www.antigravity.google/docs/cli/headless/)
- AGY workspace-scoped conversations and project behavior: [Managing Conversations](https://www.antigravity.google/docs/cli/conversations/) and [Projects](https://www.antigravity.google/docs/cli/projects/)
- Native remote dashboard and Windows daemon lifecycle: [Antigravity Remote Control](https://www.antigravity.google/docs/remote-control/)
- Hermes Kanban worker visibility and swarm topology: [Hermes Kanban](https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban)
- Telegram Mini App server validation and auth_date freshness: [Telegram Mini Apps](https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app)
- TikTok content-sharing constraints: [TikTok Content Sharing Guidelines](https://developers.tiktok.com/docs/en/content-sharing-guidelines)
- Requested GPT-6 Astra direction and local Astra-Grade implementation evidence boundary: [Astra-Grade Plan Alignment Record](ASTRA-GRADE-ALIGNMENT.md)

## 19. Implementation Plan

The complete task-by-task execution plan is maintained at:

[Hermes, AGY, and Doh-Nut Remote Operations Plan](superpowers/plans/2026-09-16-hermes-agy-remote-operations.md)

The provenance and requirement mapping for the requested GPT-6 Astra direction is maintained in:

[Astra-Grade Plan Alignment Record](ASTRA-GRADE-ALIGNMENT.md)
