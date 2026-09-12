# 🎼 Gemini Workspace Memory & Learned Rules (GEMINI.md)

Dokumen ini merekodkan peraturan yang dipelajari dan disahkan untuk projek **Hermes-WebApp** dan persekitaran kerja.

---

## 🛑 SOVEREIGN AUTONOMOUS EXECUTION PROTOCOL (NON-NEGOTIABLE)

1. **Sifar Penyerahan Manual (Zero Manual Hand-Off)**:
   - JANGAN SEKALI-KALI meminta pengguna menjalankan skrip `uvicorn`, pelancaran pelayan, atau pendaftaran Cloudflare Tunnel secara manual. Ejen **WAJIB** melancarkan skrip latar belakang (`run_command`) secara autonomi dan mengesahkan respons pelayan secara *real-time*.

2. **Kekangan Sifar Docker (100% Native OS Constraint)**:
   - Semua aplikasi, modul, dan servis MESTI dibina menggunakan Python 3.11 tempatan, PowerShell, `psutil`, dan SQLite secara terus di atas Windows OS tanpa kontena Docker.

3. **Pembersihan Berterusan (Resource & Task Hygiene)**:
   - Segera tamatkan sub-ejen yang selesai (`manage_subagents kill_all`) dan tugas zombie (`manage_task kill`) sebaik sahaja log disemak untuk mengelakkan RAM leak.

---

## 🚀 Omnichannel Social Media Autopilot (FB, IG, TikTok, YouTube) - 21 Ogos 2026
*   **Architecture Stack**: Hermes-Agent + HeyGen HyperFrames (`heygen-com/hyperframes`) + Edge-TTS + Pollinations.ai (Free-Tier RM0).
*   **Active Router**: `backend/routers/social.py` (Endpoint `/api/social/generate-omnichannel`, `/api/social/omnichannel-drafts`, `/api/social/omnichannel-action`).
*   **Database**: `social_autopilot.db` (SQLite local drafts persistence).
*   **Obsidian Link**: Terpaut ke Obsidian Vault di `07-Research/Social-Media-Autopilot-Omnichannel.md` dan `00-INDEX/DASHBOARD.md`.
