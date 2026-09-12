# 🔍 DSH Web UI Review — Laporan Penuh (V4)

**Tarikh:** 20/08/2026
**Target:** DeepSeek Harness Web UI — `http://127.0.0.1:3080`
**Mod:** Investigasi sahaja (tiada edit fail tanpa kelulusan)

---

## Ringkasan Keputusan

| # | Tuntutan | Keputusan | Bukti Utama |
|---|----------|-----------|-------------|
| 1 | Server sihat | ✅ **BENAR** | PID 17796, HTTP 200, log bersih |
| 2 | Tiada zombie background task DSH | ⚠️ **SEBAHAGIAN** | Session siap semua, tapi ada 1 orphan probe (PID 18300) — **telah dibunuh** |
| 3 | Provider/model percuma dipulihkan | ✅ **BENAR** | 16 model NVIDIA NIM Free; plugin llm-deepseek + llm-pi-ai Enabled |
| 4 | Semua API key diikat (termasuk DashScope) | ⚠️ **SEBAHAGIAN** | 8 key dalam `.credentials.yaml`, tapi UI hanya tunjuk DeepSeek; DashScope tiada dalam env |
| 5 | Default model = NVIDIA NIM Free | ⚠️ **SEBAHAGIAN** | Default = MiniMax M3 (Free 1M Context) · High — BUKAN DeepSeek V4 Flash |

---

## 1. Kesihatan Server — ✅ BENAR

| Pemeriksaan | Keputusan |
|---|---|
| Proses | PID 17796 aktif |
| HTTP | `127.0.0.1:3080` → 200 OK |
| `dsh-debug.log` | 95 byte, tiada error |
| `dsh-debug.err` | 0 byte |
| Aplikasi | Pure SPA (tiada REST API server-side) |

Server berfungsi sepenuhnya. Sesi "Simple greeting session" menunjukkan mesej siap dengan metrik prestasi:
- 43–47 tok/s
- TTFT 1.3–2.4s
- "Ran for 2–3s"

## 2. Zombie Background Task — ⚠️ SEBAHAGIAN → DIBERSIHKAN

- **Session DSH:** Tiada indikator running aktif. Badge "Running" pada session adalah **stale** (tidak berubah 21min → 28min, tiada spinner).
- **PID 18300** (`C:\Program Files\nodejs\node.exe`, mula 20/08/2026 5:42 PG): orphan probe dari agent terdahulu — **BUKAN task DSH**, tapi proses zombie yang wujud.
- **PID 10952:** child AutoClaw.exe (tooling, bukan zombie).

> ⚡ **Tindakan:** `Stop-Process -Id 18300 -Force` → **KILLED OK**. Persekitaran kini bersih.

## 3. Provider / Model Percuma — ✅ BENAR

### Model Picker (16 model NVIDIA NIM Free)
1. DeepSeek V4 Flash (Free)
2. Llama 3.3 70B (Free)
3. Codestral 22B (Free)
4. Mistral Large 2 (Free)
5. Moonshot Kimi K2.6 (Free)
6. Gemma 4 31B (Free)
7. Gemma 3 12B (Free)
8. Phi 3.5 MoE (Free)
9. Nemotron 70B (Free)
10. Nemotron 3 Ultra 550B (Free)
11. Nemotron 3.5 Lightning (Free)
12. GPT OSS 120B (Free)
13. StepFun Step 3.7 (Free)
14. IBM Granite 34B (Free)
15. 01-AI Yi Large (Free)
16. **MiniMax M3 (Free 1M Context)** ← **DEFAULT, reasoning High**

### Plugin List (165 total, diekstrak dari Settings → Plugins → Plugin list)
- `llm-deepseek` → **Enabled**
- `llm-pi-ai` → **Enabled**
- `web-search-deepseek` → **Enabled**
- `agent-default-model` → Enabled
- `agent` → Enabled
- `session` → Enabled
- `credentials-local` → Enabled
- `sandbox-policy` → Enabled
- `user-approval` → Enabled
- `skill` → Enabled
- `tool-bash` → Disabled
- `tool-pwsh` → Disabled
- `tool-fs` → Disabled
- `tool-fs-search` → Disabled
- `bash-sandbox` → Disabled
- `plan-mode` → Disabled
- `compaction-basic` → Disabled

### settings.yaml (garis 555–568)
```yaml
agent-default-model:
  provider: deepseek-official
  model: minimaxai/minimax-m3
  reasoningEffort: high
agent-loop:
  maxSteps: 25
  temperature: 0.2
  tokenBudget: 32000
```

## 4. API Keys — ⚠️ SEBAHAGIAN

### `.credentials.yaml` — SEMUA 8 KEY ADA
| Provider | Key |
|---|---|
| DASHSCOPE | `sk-ws-H…` |
| OPENCODE | `sk-5X9t9…` |
| DEEPSEEK | `sk-46ea2…` |
| GEMINI | `AQ.Ab8RN…` |
| NVIDIA | `nvapi-mi…` |
| OPENROUTER | `sk-or-v1…` |
| GROQ | `gsk_mVsc…` |
| OLLAMA | `ollama` (literal) |

### UI Models Panel
- Hanya **"DeepSeek"** muncul dengan "API key configured" + butang Edit.
- Butang **"Add provider"** dan **"Add a custom provider"** wujud, tapi **tidak membuka katalog** dalam DOM (disahkan: 0 dialog/menu/input baru, hanya overlay settings).
- **Sebab:** `dsh-llm-deepseek` gunakan `registerConfigurableProviders` → hanya provider ini muncul dalam UI. Provider llm-pi-ai (6 provider) didaftarkan melalui laluan berbeza, jadi berfungsi secara programmatic tapi tak kelihatan di UI.

### Env Variables
- Hanya NVIDIA / GROQ / OPENROUTER / OLLAMA dalam env.
- DASHSCOPE dan OPENCODE **tiada** dalam env → claim "keys aktif dalam env" adalah **SALAH** (mereka hanya dalam fail credentials).

## 5. Default Model — ⚠️ SEBAHAGIAN / CLAIM PRIOR SALAH

- **BENAR:** Default model DSH = `minimaxai/minimax-m3` · reasoning **High**, disahkan dalam:
  - `settings.yaml` garis 555–568
  - Model picker UI: **"MiniMax M3 (Free 1M Context)" · High** (selected, aria-label "Select model, current MiniMax M3 (Free 1M Context), reasoning effort High")
  - Ini adalah model **NVIDIA NIM Free** (1M context)
- **SALAH:** Claim prior "default = `nvidia/deepseek-v4-flash-0731` / low" — itu adalah config **OpenCode** (`opencode.json`), BUKAN DSH.

---

## ❌ Claim Prior Agent Yang GAGAL Verifikasi

1. **"Default = nvidia/deepseek-v4-flash-0731/low"** — SALAH. DSH default = `minimaxai/minimax-m3` · high.
2. **"DashScope/OpenCode keys aktif dalam env"** — SALAH. Hanya dalam `.credentials.yaml`.
3. **"0 background tasks"** — TIDAK TEPAT. Ada PID 18300 (orphan probe node) — kini dibunuh.
4. **"NVIDIA hack dalam dsh-llm-deepseek"** — SALAH. Fail `lib/index.js` bersih:
   - `PROVIDER = "deepseek-official"`
   - `NS = settingsNamespace("llm-deepseek")`
   - Key resolution: credentials-first, env fallback
   - Menggunakan `registerConfigurableProviders` + `registerAdapter`

## 💡 Penemuan Teknikal Tambahan

- **Settings tabs adalah plain buttons** (bukan `role=tab`) — "Settings", "General", "Models", "Plugins", "Agent presets", "Open configuration file", "Close".
- **Plugin sub-tabs ADALAH `role=tab`** — "Plugin configuration" / "Plugin list".
- Dialog settings boleh dibuka semula dengan pasti (klik butang "Settings").
- Playwright MCP `browser_evaluate` memerlukan `{"function": "<JS>"}` (bukan `{"fn": ...}`).
- `look_at` pada screenshot Add-provider gagal ("No response from multimodal-looker agent") — katalog Add provider disahkan tidak muncul dalam DOM melalui pemeriksaan JS.

## ✅ Tindakan Yang Dilaksanakan

| # | Suggestion | Status |
|---|---|---|
| 1 | Bersihkan PID 18300 | ✅ KILLED OK |
| 2 | Panel Models / katalog Add provider | ✅ Disahkan — hanya DeepSeek didaftarkan; Add provider tidak buka katalog |
| 3 | Laporan penuh ke fail | ✅ Fail ini |
| 4 | Tamat | ✅ Sedia untuk semakan akhir |

## 📌 Cadangan Lanjut (perlu kelulusan)

1. `npx dsh config set` untuk memaparkan provider tambahan llm-pi-ai dalam UI (jika dikehendaki).
2. Tambah DASHSCOPE/OPENCODE ke env jika perlu akses runtime aktif.
3. Gantikan badge "Running" stale (isu UI kecil).

---

*Laporan dijana melalui investigasi langsung: PowerShell + Playwright MCP (browser_evaluate, snapshots) + bacaan fail konfigurasi.*