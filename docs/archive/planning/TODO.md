# Hermes-WebApp UI/UX TODO

Audit source: `static/index.html` dan UI runtime pada `http://127.0.0.1:9230/`  
Audit date: 2026-07-23  
Scope: UI, UX, responsive behavior, accessibility, interaction reliability, dan maintainability.

## Priority legend

- **P0 — Blocker:** UI utama atau navigation tidak boleh digunakan.
- **P1 — High:** Mengganggu usability, accessibility, atau keselamatan operasi.
- **P2 — Medium:** Peningkatan efficiency, performance, consistency, dan maintainability.

## Baseline findings

- [ ] Runtime audit: 64 buttons, 15 form controls, dan 14 module overlays dikesan.
- [ ] Semua 14 `.module-overlay` dilaporkan visible pada initial load.
- [ ] Mobile viewport 390px tidak menghasilkan horizontal body overflow.
- [ ] Telegram `requestFullscreen()` menghasilkan console error pada Telegram WebApp versi lama.
- [ ] Tiada source code diubah semasa audit.

## P0 — Restore core usability

### 1. Betulkan module overlay state

- [ ] Sembunyikan overlay inactive menggunakan `visibility`, `transform`, dan `pointer-events`.
- [ ] Pastikan hanya satu module boleh mempunyai `.active` pada satu masa.
- [ ] Tambah `aria-hidden="true"` pada inactive overlay dan `aria-hidden="false"` pada active overlay.
- [ ] Tambah `role="dialog"` dan `aria-modal="true"` pada module shell.
- [ ] Pastikan dock dan Home screen boleh digunakan selepas page load.
- Rujukan: `static/index.html:387-398`, `static/index.html:4050-4053`

### 2. Buang patch yang memadam event handlers

- [ ] Buang `btn.removeAttribute('onclick')` daripada DOMContentLoaded patch.
- [ ] Gantikan inline handlers dengan event delegation atau `data-action` yang explicit.
- [ ] Pastikan button tanpa icon tidak menyebabkan `querySelector('i').getAttribute(...)` error.
- [ ] Re-test: Close, Run, Go, Refresh, Spawn, Save, Search, dan semua tab buttons.
- Rujukan: `static/index.html:3994-4016`

### 3. Betulkan struktur HTML

- [ ] Buang closing `</div>` berlebihan dalam Services Manager.
- [ ] Buang closing `</div>` berlebihan dalam Workflow Engine.
- [ ] Jalankan HTML validation selepas pembetulan.
- Rujukan: `static/index.html:1160`, `static/index.html:1247`

## P1 — Accessibility dan mobile UX

### 4. Navigation information architecture

- [ ] Kurangkan primary dock kepada 5 item: Home, Monitor, Terminal, Swarm, More.
- [ ] Pindahkan Files, Browser, Kanban, Audio, Security, Workflow, dan Obsidian ke More drawer.
- [ ] Kekalkan Command Palette sebagai global search/action entry point.
- [ ] Tambah active module title dan breadcrumb/back affordance yang jelas.
- [ ] Pastikan navigation boleh digunakan tanpa hover.

### 5. Keyboard dan semantic controls

- [ ] Tukar semua `div onclick` kepada `<button>` atau `<a>` yang sesuai.
- [ ] Tambah keyboard support untuk card, file row, agent row, log filter, dan command palette item.
- [ ] Tambah visible `:focus-visible` state kepada semua interactive elements.
- [ ] Tambah `aria-hidden="true"` pada icon Lucide dekoratif.
- [ ] Tambah `aria-label` atau visible label pada voice badge dan icon-only controls.
- Rujukan: `static/index.html:577`, `static/index.html:678`, `static/index.html:1752`, `static/index.html:2232`, `static/index.html:3515`

### 6. Form usability

- [ ] Tambah `<label>` yang boleh diklik untuk setiap input.
- [ ] Tambah `name`, `autocomplete`, `inputmode`, dan `type` yang sesuai.
- [ ] Gantikan placeholder `...` dengan ellipsis typographic `…`.
- [ ] Tambah inline validation dan error message dengan langkah pembetulan.
- [ ] Fokuskan field pertama yang gagal selepas submit.
- Rujukan: `static/index.html:893-894`, `static/index.html:1024-1029`, `static/index.html:1193`, `static/index.html:1228-1232`, `static/index.html:1275`

### 7. Modal behavior

- [ ] Focus masuk ke module title atau primary control ketika module dibuka.
- [ ] `Escape` menutup module aktif.
- [ ] Focus trap tidak membenarkan keyboard focus keluar daripada dialog.
- [ ] Focus dikembalikan kepada button yang membuka module.
- [ ] Gunakan safe-area padding pada header dan footer module.

### 8. Mobile layout

- [ ] Buang `maximum-scale=1` dan `user-scalable=no` daripada viewport meta.
- [ ] Guna `100dvh` dengan fallback kepada `100vh`.
- [ ] Guna `env(safe-area-inset-top)` dan `env(safe-area-inset-bottom)`.
- [ ] Gantikan selector global `form, .glass > div` dengan class layout khusus.
- [ ] Uji 375px, 390px, 768px, 1024px, dan 1440px.
- Rujukan: `static/index.html:5`, `static/index.html:562`, `static/index.html:3691-3696`

## P1 — Operational UX

### 9. Loading, empty, error, dan connection states

- [ ] Standardkan loading state dengan spinner/progress indicator.
- [ ] Tambah `aria-live="polite"` pada toast, transcript, logs, dan status badges.
- [ ] Tambah retry button untuk API/WebSocket failures.
- [ ] Paparkan `last updated` pada metrics dan connection state.
- [ ] Jangan paparkan `WS Connected`, `Active`, atau `Sovereign Node Active` sebelum health check sebenar berjaya.
- [ ] Elakkan toast berulang daripada polling failures.

### 10. Destructive action safety

- [ ] Tambah confirmation modal atau undo window untuk Block IP.
- [ ] Tambah confirmation untuk Stop/Restart Service, Cleanup Zombies, dan Save File.
- [ ] Paparkan target, kesan, dan pilihan Cancel sebelum tindakan berisiko.
- [ ] Disable button ketika request sedang berjalan dan pulihkan state selepas response.

### 11. Telegram integration

- [ ] Semak Telegram WebApp version sebelum memanggil `requestFullscreen()`.
- [ ] Gunakan `expand()` sebagai fallback tanpa menghasilkan console error.
- [ ] Elakkan duplicate `BackButton.onClick()` registration setiap kali module dibuka.
- [ ] Elakkan duplicate `MainButton.onClick()` registration setiap kali Monitor dibuka.
- Rujukan: `static/index.html:1293`, `static/index.html:1710-1716`

## P2 — Performance dan maintainability

### 12. Motion dan visual effects

- [ ] Tambah `@media (prefers-reduced-motion: reduce)` untuk semua animation dan transition.
- [ ] Gantikan `transition: all` dengan property list yang explicit.
- [ ] Pause canvas animation, polling, dan WebSocket work ketika document hidden.
- [ ] Kurangkan particle/dot-field work pada device low-power.
- Rujukan: `static/index.html:577`, `static/index.html:1380`, `static/index.html:1596`, `static/index.html:2704-2706`

### 13. Pecahkan single-file UI

- [ ] Pindahkan CSS ke `static/css/`.
- [ ] Pindahkan navigation, modal shell, toast, command palette, dan accessibility helpers ke module JS berasingan.
- [ ] Pecahkan setiap feature module kepada fail atau component yang tersendiri.
- [ ] Buang patch CSS/JS berlapis yang menimpa rules sebelumnya.
- [ ] Tambah design tokens untuk warna, spacing, typography, border, dan state.

### 14. Selaraskan design system

- [ ] Pilih satu typography direction: Inter untuk application UI atau JetBrains Mono untuk terminal-oriented UI.
- [ ] Selaraskan `MASTER.md` dengan implementation sebenar.
- [ ] Buang emoji sebagai icon dan guna Lucide secara konsisten.
- [ ] Semak contrast minimum 4.5:1 untuk body text dan status labels.
- [ ] Pastikan hover tidak mengubah layout atau menyebabkan jitter.

### 15. Safer dynamic rendering

- [ ] Escape semua user/backend data sebelum dimasukkan ke `innerHTML`.
- [ ] Elakkan membina `onclick` string daripada path atau agent ID.
- [ ] Gunakan DOM APIs atau event delegation untuk dynamic rows.
- [ ] Tambah explicit `width` dan `height` pada browser stream image/canvas wrapper.

### 16. Asset dan offline resilience

- [ ] Self-host atau sediakan fallback untuk Inter, Lucide, xterm, dan DOMPurify.
- [ ] Tambah `font-display: swap` untuk font.
- [ ] Pertimbangkan CSP dan integrity pinning untuk external CDN assets.
- [ ] Paparkan offline/degraded mode yang jelas apabila CDN atau backend tidak tersedia.

## Definition of Done

- [ ] Initial load hanya memaparkan Home dashboard.
- [ ] Semua 14 module boleh dibuka dan ditutup menggunakan mouse, touch, keyboard, dan Telegram BackButton.
- [ ] Tiada console error semasa initial load dan basic navigation.
- [ ] Semua form mempunyai label, validation, loading, success, dan error state.
- [ ] Tiada horizontal overflow pada 375px dan 390px.
- [ ] Semua destructive actions mempunyai confirmation atau undo.
- [ ] Reduced-motion mode berfungsi.
- [ ] `pytest -v` selesai tanpa hang dan tanpa failure.
- [ ] Uvicorn/Watchdog port configuration diselaraskan kepada port yang dipersetujui.
- [ ] QA manual selesai pada 375px, 768px, 1024px, dan 1440px.

