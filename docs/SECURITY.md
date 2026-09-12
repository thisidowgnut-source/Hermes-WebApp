# Security Protocol (SECURITY.md)

**Classification:** STRICT CONFIDENTIAL / ROOT ACCESS
**Scope:** Hermes OS Telegram WebApp

Because the Hermes OS WebApp grants direct shell (`pwsh.exe`) and physical process control over the host Windows machine, it presents a catastrophic security risk if exposed to the public internet without severe hardening.

## 1. Network Exposure (Cloudflare Tunnels)
- **Do not use port forwarding.** Opening port `9220` on your home router exposes the FastAPI server to Shodan and automated vulnerability scanners.
- **Mandatory Tunneling:** Use `cloudflared` (Cloudflare Tunnels). The tunnel must be configured to point strictly to `localhost:9220`. 

## 2. Authentication & Telegram Isolation
Since the Cloudflare Tunnel provides a public URL (e.g., `https://my-secret-tunnel.trycloudflare.com`), anyone who discovers the URL could theoretically access the dashboard.
### Required Hardening (Implementation Pending/Required):
1. **Init Data Validation:** The FastAPI backend MUST intercept the `Telegram.WebApp.initData` string.
2. **User ID Whitelisting:** The backend MUST verify the cryptographically signed `initData` against the Telegram Bot Token and verify that the `user.id` matches the exact authorized owner's Telegram ID.
3. **Rejection Protocol:** Any HTTP request lacking a valid, unexpired Telegram signature MUST be rejected with `HTTP 401 Unauthorized`.

## 3. Remote Code Execution (RCE) Boundaries
- The Terminal module executes `pwsh.exe -NoProfile`. It runs under the privileges of the user who started the FastAPI Uvicorn process.
- **Do NOT run the Uvicorn process as Administrator** unless absolutely required for specific macros. Running as a standard user limits the blast radius if the WebApp is compromised.

## 4. Playwright (Vision) Sandboxing
- The Chromium instance launched by Playwright runs headlessly.
- Ensure that the browser context does not leak sensitive cookies from the host machine. Playwright must always launch in an isolated browser context unless explicitly instructed otherwise.
