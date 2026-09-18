# 🧩 SERVERLESS GITOPS — Perbandingan & Rangka Kerja

**Status**: Proposal / Rangka (bukan perubahan struktur sedia ada)  
**Workspace**: `C:\Users\megat\Hermes-WebApp`  
**Referensi**: `SUGGESTI-FLOWISE-POSTIZ.md` (bahagian 3.2 — sintesis integrasi)

---

## Perbandingan: Monolith SaaS (Postiz/VPS) vs. Headless GitOps (GitHub Actions)

| Aspek | Monolith (Postiz / VPS / Docker) | Headless GitOps (GitHub Actions) |
|---|---|---|
| **Kos** | Perlu VPS / kad kredit / Docker host | RM0 (GitHub Actions 2,000 minit percuma) |
| **Database** | PostgreSQL (Prisma) — perlu penyelenggaraan | Tiada DB — `queue.json` dalam Git |
| **Worker / Queue** | Temporal / Redis — proses berterusan 24/7 | GitHub Actions cron (berjadual, bukan berterusan) |
| **State** | DB + file storage | Git commit log (`git push`) |
| **API Social** | SDK / OAuth (kompleks) | Panggilan langsung (`urllib` / `requests`) |
| **Deployment** | Docker compose, Cloudflare tunnel | Tiada server — `push` ke GitHub = deploy |
| **Akses Luar** | Perlu IP awam / firewall / tunnel | `outbound-only` — panggil API dari GitHub runner |
| **Beban CPU/RAM** | 2GB-4GB (berat) | Sifar (jalan di Microsoft server) |
| **Autonomi** | Bergantung pembekal awan | 100% milik sendiri (repo peribadi) |
| **Hermes-Kaitan** | Tambah modul `analytics` / `social` ke backend | Tidak merosakkan struktur sedia ada (`mod-swarm` kekal, `social` router kekal) |

---

## Komponen Rangka (Sudah Dibuat)

### 1. `.github/workflows/post_scheduler.yml`
- **Cron trigger**: Setiap 2 jam (`*/2`) dan harian 10:30 AM (`30 10 * * *`)
- **Manual trigger**: `workflow_dispatch`
- **Langkah**: Checkout → Load `queue.json` (`select_due_posts.py`) → Publish (`post_to_social.py`) → Commit status → Upload artifact log
- **Secrets**: `TELEGRAM_BOT_TOKEN`, `TIKTOK_SESSION_ID`, `INSTAGRAM_USER_ID`, `X_API_KEY`

### 2. `.github/scripts/post_to_social.py`
- **Fungsi**: Baca `queue.json`, panggil API platform, kemas kini status (`pending` → `published` / `failed`)
- **Tiada DB**: Semua state disimpan semula ke `queue.json` (GitOps)
- **Tiada server berat**: Hanya `urllib` (native Python) — tiada `requests`, tiada `redis`

### 3. `queue.json`
- **Format**: Array objek `{id, platform, content, schedule_at, status, created_at}`
- **Contoh**: 3 post (`post-001` Tiktok, `post-002` Instagram, `post-003` Threads) — semua `pending`
- **Update**: `post_to_social.py` akan tukar `status` ke `published` dan tambah `published_at`

---

## Bagaimana Ini Tidak Merosakkan Struktur Hermes Asal

| Struktur Asal Hermes | Status | Kaitan Serverless |
|---|---|---|
| `backend/main.py` (FastAPI, port 9220) | ✅ Utuh | Tiada perubahan — workflow hanya `outbound` panggil API |
| `static/index.html` (SPA, `.module-overlay`) | ✅ Utuh | Tiada perubahan — workflow adalah proses latar belakang |
| `.agents/` (agent lifecycle) | ✅ Utuh | Workflow `post_scheduler` boleh diintegrasi sebagai `agent` baru (tanpa ganggu yang sedia ada) |
| `var/lib/` (missions.db, SQLite WAL) | ✅ Utuh | `queue.json` simpan dalam root repo (bukan `var/lib`) — tiada konflik dengan `missions.db` |
| `deploy/` (Cloudflare tunnel, VBS, service) | ✅ Utuh | Workflow tidak ganti tunnel; ia adalah alternatif `social` module tanpa server |
| `tests/` (pytest 273 passed) | ✅ Utuh | Tiada perubahan pada file backend utama; hanya tambahan `.github/` dan `scripts/` |

---

## Langkah Seterusnya (Jika User Setuju)

1. **Isikan secrets** dalam repo GitHub (`TELEGRAM_BOT_TOKEN`, `TIKTOK_SESSION_ID`, dll)
2. **Ubah `queue.json`** mengikut kempen Doh-Nut sebenar (`post-001`, `post-002`, `post-003` sudah contoh)
3. **Aktifkan cron** — workflow akan berjalan secara automatik tanpa server
4. **Pantau artifact** (`social-publish-log`) untuk setiap eksekusi
5. **Integrasi dengan Hermes** (pilihan): Panggil endpoint `/api/social/generate-ka` dari `post_to_social.py` untuk jana kandungan AI sebelum hantar ke platform

Laporan ini (`SERVERLESS-DESIGN.md` + `.github/workflows/post_scheduler.yml` + `.github/scripts/post_to_social.py` + `queue.json`) disimpan dalam workspace sebagai rujukan — **struktur asal Hermes kekal utuh 100%**.
