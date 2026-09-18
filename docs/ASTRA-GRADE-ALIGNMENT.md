---
title: "Astra-Grade Plan Alignment Record"
document_id: "HERMES-WEBAPP-ASTRA-001"
version: "1.0.0"
last_updated: "2026-09-16 MYT"
maintainer: "Megat / Hermes-WebApp operators"
classification: "INTERNAL // EVIDENCE-BOUND PLANNING"
lifecycle_status: "DRAFT - IMPLEMENTATION NOT STARTED"
---

# Astra-Grade Plan Alignment Record

## Purpose

This record turns the requested GPT-6 Astra direction into traceable Hermes-WebApp requirements. It keeps the useful operating principles from the local Astra-Grade v7.0-v10.0 history while refusing to convert historical claims, model names, or tool labels into unverified runtime facts.

The product remains a remote control plane for the existing Doh-Nut AGY workflow. It is not a second autonomous agent that silently replaces AGY, impersonates a platform user, or manufactures success from an exit code.

## Evidence Boundary

| Source | What it can establish | What it cannot establish |
| --- | --- | --- |
| Local Astra-Grade implementation ledger in C:/Users/megat/ObsidianVault/Hermes-Obsidian/04-Active/DOWGNUT/LOG-GANGBO.md | Historical intent and recorded v7.0-v10.0 practices: Planning with Files, dynamic skill retrieval, doubt-driven gates, feedback loops, bounded subagents, codebase memory, security review, and Doctor/Toolkit/Benchmark utilities. | That every listed component is still installed, enabled, healthy, or suitable for a remote WebApp integration today. |
| Current Obsidian context and session log | The intended Doh-Nut-first topology, existing AGY/Hermes roles, and previous operational decisions. | Live authentication, quota, account permissions, actual social publication, current PID ownership, or current model availability. |
| Official AGY, Hermes, Telegram, and platform documentation listed in PRD.md | Supported public contracts used by a future adapter. | A private embedding API, unadvertised capability, or automatic publishing permission. |
| Direct GPT-6 Astra conversation | The requested original plan, if its transcript is made available in this workspace or an accessible signed-in browser profile. | It is not currently recoverable from the browser profile available during this review; no statement in this document claims that the original chat transcript was read. |

## Design Decisions Adopted

| Astra-Grade principle | Hermes-WebApp decision | Proof required before activation |
| --- | --- | --- |
| Planning with Files | Every Hermes planning or verification mission gets an immutable planning packet with objective, constraints, evidence inputs, risk class, selected capabilities, budget, and acceptance checks. | Policy tests prove packets are required for multi-step coordinator work and remain linked to the mission. |
| Dynamic skill retrieval | Capability selection is an allowlisted registry lookup by mission intent and profile version. It records why a capability was selected. Model output, prompt text, or external page content cannot name arbitrary skills or executable tools. | Registry, schema, and negative-injection tests. |
| Doubt-Driven Development | Privileged, destructive, external-transmission, financial, credential, browser-publish, CAPTCHA, and 2FA intent are classified before execution. Unsafe intent moves to a typed waiting-human state with a narrow approval scope. | State-transition and authorization tests prove no side effect happens before approval. |
| Loopy feedback loops | A change-oriented mission uses a baseline, one bounded action, a re-measurement, and an explicit keep/revert/escalate decision. | Evaluation tests prove a missing or non-comparable measurement cannot become verified. |
| Subagent runaway guard | Iteration, concurrency, handoff depth, retry class, and elapsed-time budgets are configuration-backed and visible per run. Authentication, quota, and unknown external states never auto-retry. | Capacity and recovery tests with exhausted budgets and duplicate requests. |
| Codebase memory | A future read-only code index is an optional artifact source, not an authority or opaque memory store. Its index version and source revision are visible in a planning packet. | Index freshness and provenance tests; a stale or missing index produces a degraded result. |
| Doctor, skill toolkit, and model benchmarker | Existing local utilities may be surfaced through fixed, read-only capability probes. Their output becomes a sanitized health artifact, never an instruction channel or a claim of universal health. | Probe tests use fake tools and assert redaction, timeouts, and degraded handling. |
| Security and Mantis-style review | Security review is a bounded verifier profile with explicit scope and evidence. It cannot modify host settings, credentials, or provider configuration. | Permission-denial tests and a fixed-profile contract. |
| Human-in-the-loop social operation | Approval, preparation, submission, receipt, and reconciliation remain separate. CAPTCHA, 2FA, and final actions on unvalidated platforms remain human-controlled. | Campaign state-machine, receipt, and duplicate-prevention tests. |

## Orchestration Contract

1. A mission has one primary executor: AGY or Hermes.
2. Hermes may plan, verify, coordinate a Kanban task, or return an evidence artifact. It does not automatically launch AGY, browser, terminal, social, or platform actions.
3. AGY remains the direct executor for the existing Doh-Nut subagent workflow. One provider conversation has one writer.
4. A cross-executor handoff contains immutable artifact references, the source mission id, a declared target profile, and a maximum depth of one.
5. A mission is verified only when its declared acceptance checks and evidence threshold are met. A process exit, static status card, route response, local timestamp, or uncorroborated model assertion is insufficient.
6. A failed or uncertain measurement produces needs_verification, interrupted, unknown, or waiting_human; it never becomes a silent retry or a false success.

## Candidate Configuration Defaults

The local ledger records historical Hermes safeguards of 25 maximum iterations and 3 concurrent children. Hermes-WebApp will treat those as candidate defaults, not fixed truths. The implementation must read a validated non-secret policy file, display effective limits in the capability snapshot, and require a fresh controlled test before enabling a different limit.

The first release remains more conservative at the WebApp boundary: one active AGY stream per project, two active runs globally, one-hop handoffs, no implicit retries for authentication/quota/rate-limit/unknown-publication failures, and no raw command submission.

## Requirement Mapping

| Requirement group | Delivery task |
| --- | --- |
| Planning packets, risk classification, selected-capability receipt | Task 11 |
| AGY process, conversation, and one-writer rules | Tasks 1, 2, 5, 6 |
| Hermes adapter isolation and bounded handoff | Tasks 10, 11 |
| Capability health, cost, recovery, migration | Task 12 |
| Security, UI, social truth, and controlled live acceptance | Task 13 |

## Completion Standard

Alignment is complete only after the implemented behavior has fresh evidence. Historical Astra-Grade notes, a model label, an installed executable, or an optimistic dashboard badge are not completion evidence.
