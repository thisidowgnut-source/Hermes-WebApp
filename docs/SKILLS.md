# Hermes OS Skills Directory

This document outlines the specialized skills deployed alongside the Hermes OS WebApp to enable autonomous AI agents to leverage the platform.

## 1. `hermes-ui-controller`

**Skill ID:** `hermes-ui-controller`
**Domain:** Human-in-the-Loop (HITL) & Remote Delegation
**Access Level:** Core System Capability

### 1.1 Purpose
The `hermes-ui-controller` skill teaches autonomous agents how to interact with the Hermes OS Telegram WebApp. It allows AI agents to monitor system health without invoking heavy terminal commands and provides a structured protocol for handing over control to a human operator when autonomous execution fails.

### 1.2 REST API Access (Agent Context)
Agents are instructed to use the FastAPI REST endpoints (`127.0.0.1:9220`) for lightweight data gathering:
- **Health Checks:** Hitting `/api/stats` to check if their own execution is causing CPU/RAM spikes.
- **Process Audits:** Hitting `/api/processes` to identify memory leaks.
- **Hostile Takeovers:** Hitting `/api/kill/{pid}` to terminate rogue processes they spawned.

### 1.3 The Vision Handover Protocol
When an agent is performing automated browser tasks (e.g., via Playwright or Chrome DevTools) and encounters an impassable barrier:
1. **Trigger Condition:** Captchas (Cloudflare Turnstile, reCAPTCHA, hCaptcha) or heavily obfuscated 2FA logins.
2. **Action:** The agent stops its script, prevents timeouts, and sends an alert to the user's Telegram.
3. **Message Format:** *"🚨 HUMAN HANDOVER REQUIRED 🚨 I have encountered a security block on `[URL]`. Please open your Telegram Mini App, navigate to the **Vision** tab, and click **REQUEST MANUAL CONTROL** to bypass the security check."*
4. **Resolution:** The agent waits for the user to reply "proceed" before continuing its autonomous loops.

## 2. Skill Management
Skills are managed globally in the `~/.gemini/config/plugins/GangNiaga-Elite-CyberSuite/skills/` directory. Modifications to UI interaction patterns must be updated in the `SKILL.md` file within that directory to propagate across all agent sessions.
