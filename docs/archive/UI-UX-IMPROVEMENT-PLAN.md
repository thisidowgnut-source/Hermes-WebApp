---
title: "Hermes-WebApp UI/UX Improvement Plan"
document_id: HERMES-UIUX-2026-001
version: 1.0.0
last_updated: "2026-09-12 17:22 MYT"
maintainer: "Antigravity Conductor (Opus 4.6)"
classification: INTERNAL
lifecycle_status: ACTIVE
---

# 🎨 HERMES-WEBAPP — UI/UX IMPROVEMENT PLAN
## `static/index.html` · 5,406 Lines · 291KB · 17 Modules

> **Objective**: Transform from ⭐⭐½ (5.4/10) MVP → ⭐⭐⭐⭐½ (9.0/10) Production-Grade
> **Method**: Full 360° audit by 4 parallel auditor agents, covering every line of HTML/CSS/JS
> **Estimated Total Effort**: ~17 hours across 4 sprints

---

## 📊 Current Health Scorecard

| Dimension | Score | Critical Issue |
|:---|:---:|:---|
| Mobile-First Layout | ⭐⭐⭐ | Single breakpoint (640px), no tablet |
| Touch Target Compliance | ⭐⭐ | 23+ elements below 48px |
| Typography & Readability | ⭐½ | Systemic 8px font plague |
| Accessibility (WCAG 2.1) | ⭐⭐½ | Missing tab roles, skip-nav, contrast |
| Visual Consistency | ⭐⭐⭐⭐ | Solid OLED theme, coherent |
| Component Architecture | ⭐⭐½ | Duplicate social modules, 17-item dock |
| JavaScript Robustness | ⭐⭐⭐ | Silent catches, race conditions |
| Performance & Memory | ⭐⭐½ | Phantom animation loops |

**42 Total Findings**: 13 Critical · 6 High · 16 Moderate · 7 Low

---

## 📱 Per-Module Status

| Module | Dock # | Touch ✋ | Font 🔤 | A11y ♿ | Loading ⏳ | Mobile 📱 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| Dashboard/Home | 0 | ❌ | ❌ | ⚠️ | ❌ | ⚠️ |
| Monitor | 1 | ✅ | ⚠️ | ⚠️ | ❌ | ✅ |
| Terminal | 2 | ❌ | ❌ | ⚠️ | ✅ | ⚠️ |
| Browser | 3 | ⚠️ | ⚠️ | ✅ | ❌ | ⚠️ |
| Kanban | 4 | ✅ | ⚠️ | ⚠️ | ❌ | ✅ |
| Files | 5 | ⚠️ | ⚠️ | ⚠️ | ❌ | ✅ |
| Swarm | 6 | ❌ | ❌ | ❌ | ❌ | ⚠️ |
| Audio/Voice | 7 | ⚠️ | ❌ | ⚠️ | ⚠️ | ⚠️ |
| NetScan | 8 | ⚠️ | ❌ | ⚠️ | ❌ | ✅ |
| Threat | 9 | ⚠️ | ❌ | ⚠️ | ❌ | ✅ |
| Editor | 10 | ⚠️ | ⚠️ | ⚠️ | ❌ | ❌ |
| Services | 11 | ✅ | ❌ | ⚠️ | ❌ | ✅ |
| Forensics | 12 | ❌ | ⚠️ | ❌ | ❌ | ⚠️ |
| Workflow | 13 | ⚠️ | ⚠️ | ⚠️ | ❌ | ❌ |
| Obsidian Graph | 14 | ⚠️ | ⚠️ | ⚠️ | ❌ | ❌ |
| Social Hub | 15 | ⚠️ | ⚠️ | ✅ | ❌ | ⚠️ |
| Doh-Nut HQ | 16 | ❌ | ⚠️ | ⚠️ | ❌ | ⚠️ |
| App Drawer | — | ❌ | ❌ | ❌ | — | ⚠️ |

---

## 🔴 CRITICAL FINDINGS (13)

### Architecture
1. **Two separate Social backends** — `social.py` (214 lines) and `dohnut.py` social section doing same job with different schemas
2. **Doh-Nut `DB_PATH` never used** — all campaign data lost on refresh
3. **"Approve & Broadcast" fake publish** — `social.py` updates SQLite status but never calls WebBridge
4. **1-Tap Post: zero confirmation** — `publishDohnutSocial()` instantly fires, 8px font, 1px padding
5. **Conflicting terminal listeners** — `keypress` + `keydown` on same input cause double command execution

### Typography
6. **Systemic 8px font plague** — 25+ locations using 8px, 15+ using 9px across ALL modules

### Touch Targets
7. **23+ elements below 48px minimum** — voice badge (17px), RUN button (21px), hacker keyboard (25px), 1-Tap Post (15px)

### Navigation
8. **17-item dock overflow** — requires scroll on mobile, only 5-6 items visible

### Accessibility
9. **Non-semantic interactive elements** — `<div onclick>` in App Drawer, AI Labs without keyboard access
10. **iOS auto-zoom** — inputs below 16px font-size cause Safari viewport zoom

### Contrast
11. **Contrast failures** — `rgba(255,255,255,0.2)` text used in 8+ empty states (1.5:1 ratio vs 4.5:1 required)

### Social Module
12. **X + YouTube cards missing in frontend** — backend generates 6 platforms, UI shows only 4
13. **Two different API response schemas** — flat strings vs nested objects, incompatible merge

---

## 📐 DESIGN SYSTEM

### Typography Scale

| Token | Size | Usage |
|:---|:---:|:---|
| `--text-2xs` | 11px | Badges, timestamps (MINIMUM) |
| `--text-xs` | 12px | Labels, captions |
| `--text-sm` | 13px | Body text, descriptions |
| `--text-base` | 14px | Default body |
| `--text-md` | 16px | Inputs (iOS-safe), subheadings |
| `--text-lg` | 18px | Card titles |
| `--text-xl` | 20px | KPI numbers |
| `--text-2xl` | 24px | Page titles |

### Spacing Scale

| Token | Size | Usage |
|:---|:---:|:---|
| `--space-1` | 4px | Micro gap |
| `--space-2` | 8px | Tight gap |
| `--space-3` | 12px | Standard |
| `--space-4` | 16px | Module padding |
| `--space-5` | 20px | Section gap |
| `--space-6` | 24px | Large gap |

### WCAG-Compliant Color Tokens

| Token | Value | Contrast vs #000 | Usage |
|:---|:---|:---:|:---|
| `--text-primary` | `#fafafa` | 21:1 ✅ | Headings, primary text |
| `--text-secondary` | `#a1a1aa` | 5.6:1 ✅ | Body text, labels |
| `--text-tertiary` | `#71717a` | 3.9:1 ✅ | Large text, empty states |
| `--text-muted` | `#52525b` | 2.8:1 ⚠️ | Decorative only |
| `--bg-surface` | `#09090b` | — | Cards |
| `--bg-elevated` | `#18181b` | — | Inputs, hover |
| `--border-subtle` | `#27272a` | — | Card borders |

### Button Hierarchy (4-Tier System)

| Tier | Class | Visual | Usage |
|:---|:---|:---|:---|
| **Primary** | `.btn-primary` | White solid, dark text | 1 per section — "Generate", "Save" |
| **Secondary** | `.btn-secondary` | Glass border | "Sync", "Refresh" |
| **Ghost** | `.btn-ghost` | Text-only, no border | "Cancel", "Close" |
| **Danger** | `.btn-danger` | Red-tinted | "Kill", "Block IP", "Delete" |

All buttons: `min-height: 48px`, `font-size: 12px+`, `touch-action: manipulation`

---

## 🧭 NAVIGATION REDESIGN

### Dock: 17 → 5+1 Pattern

```
BEFORE: 17 flat items with horizontal scroll
 [Home][Monitor][Shell][Vision][Kanban][Files][Swarm][Voice][Net][Threat]...

AFTER: 5 primary tabs + More drawer
 ┌──────┬──────┬──────┬──────┬──────┐
 │  🏠  │  🍩  │  💻  │  🤖  │  ⋯  │
 │ Home │DohNut│Shell │Swarm │ More │
 └──────┴──────┴──────┴──────┴──────┘
```

**Why these 5:**
1. **Home** — Most frequent entry point
2. **Doh-Nut** — Primary revenue tool (business-critical)
3. **Shell** — Power-user essential
4. **Swarm** — AI workflow management
5. **More** — Opens existing App Drawer (categorized catalog)

### App Drawer Enhancement

Add to existing `mod-appdrawer`:
- **Search bar** at top for quick module finding
- **Recently Used** section (3 items, JS `localStorage` tracked)
- Keep existing categories: Control & Shell, Agents & Automation, Security & Forensics, Knowledge & Tasks

---

## 📱 DASHBOARD RESTACK

### Mobile Viewport Budget (iPhone 14: 390×844px)

```
PROPOSED LAYOUT:
┌──────────────────────────┐
│ ⚡ Hermes V3    🎤 🛡️    │  50px
├──────────────────────────┤
│ ✨ [AI Command Bar.....] │  48px  (sticky)
├──────────────────────────┤
│ 🍩 Doh-Nut HQ            │
│ RM 1,420 · 8 Pipeline    │  80px
├──────────────────────────┤
│ 🤖 Swarm: 3 Active       │  70px
├──────────────────────────┤
│ ⚡ Actions (4×2 grid)     │
│ [Audit][Test][Kill][Sync] │
│ [Vault][Spawn][Temp][Lock]│ 100px
├──────────────────────────┤
│ 📊 Agent Stream ▼        │  40px  (collapsed)
├──────────────────────────┤
│ 🏠 │ 🍩 │ 💻 │ 🤖 │ ⋯  │  64px
└──────────────────────────┘
Total: ~452px ✅ (fits with room to spare)
```

**Actions:**
- Remove Quick Actions grid (L820–L846) — duplicates Kill Zombies + Sync Tunnel
- Merge "Clean Temp" + "Lock PC" into Action Launchers (6→8 items, 4×2 grid)
- Collapse Agent Stream by default (tap header to expand)
- Make AI Command Bar `position: sticky; top: 0;`

---

## 🔧 MODULE IMPROVEMENT SPECS

### Terminal — Hacker Keyboard

```
BEFORE: 10 keys in 1 row, 25px height, 8px font
┌───┬───┬───┬───┬────┬────┬───┬───┬───┬───┐
│ESC│TAB│C-C│C-Z│C-L │ ↑  │ ↓ │ ← │ → │CLR│
└───┴───┴───┴───┴────┴────┴───┴───┴───┴───┘

AFTER: 5 keys per row × 2 rows, 44px height, 12px font
┌──────┬──────┬──────┬──────┬──────┐
│ ESC  │ TAB  │Ctrl+C│  ↑   │ CLR  │
├──────┼──────┼──────┼──────┤      │
│ HOME │ END  │Ctrl+Z│← ↓ →│      │
└──────┴──────┴──────┴──────┴──────┘
```

### Social Command Center (Merge Two Modules)

**Frontend**: Remove `mod-social` (dock #15). Move all into `dohnut-tab-social` with:
- 6 platform tabs (TikTok, IG, FB, Threads, X, YouTube) — all rendered
- Pollinations HD thumbnail preview
- Editable caption textarea
- 3 actions: Reject / Schedule / Approve & Publish
- Draft history list (SQLite-backed)

**Backend**: Merge into single `social_unified.py`:
```
POST /api/social/generate        ← 6 platforms + thumbnail
POST /api/social/publish/{id}    ← WebBridge + confirmation
POST /api/social/action/{id}     ← Approve/Reject
GET  /api/social/drafts          ← History
GET  /api/social/accounts        ← Platform status
```

### Forensics — Confirmation on Destructive Actions

Add `confirm()` dialog before:
- `addFirewallBlockRule()` — "Block all traffic from {IP}?"
- `publishDohnutSocial()` — "Publish to {platform}? Cannot undo."
- `saveFileFromEditor()` — "Overwrite {filename}?"

### All Modules — Empty State Pattern

Replace all `rgba(255,255,255,0.2)` empty states with:
```html
<div class="empty-state">
    <i data-lucide="inbox" style="width: 32px; height: 32px;"></i>
    <p class="empty-state-title">No Data Yet</p>
    <p class="empty-state-desc">Tap the button below to get started</p>
</div>
```

### All Modules — Loading State Pattern

Wrap every fetch button with `withLoading()`:
```javascript
async function withLoading(btn, fn) {
    if (btn.disabled) return;
    btn.disabled = true;
    btn.classList.add('is-loading');
    try { await fn(); }
    catch(e) { showToast('Error: ' + e.message, 'error'); }
    finally { btn.disabled = false; btn.classList.remove('is-loading'); }
}
```

---

## ⚡ JAVASCRIPT FIXES

### Terminal Double-Listener (CRITICAL)

**Problem**: Two event listeners on same input — `keypress` (L3002) sends to WebSocket, `keydown` (L4944) runs local commands. Pressing Enter fires BOTH.

**Fix**: Single unified handler:
```javascript
termInput.addEventListener('keydown', function(e) {
    if (e.key !== 'Enter') return;
    e.preventDefault();
    const cmd = this.value.trim();
    if (!cmd) return;
    const LOCAL = ['help', 'clear', 'date', 'whoami'];
    if (LOCAL.includes(cmd.split(' ')[0])) handleLocalCommand(cmd);
    else sendCmd(cmd);
    this.value = '';
});
```

### Animation Lifecycle Manager

**Problem**: `setInterval`/`requestAnimationFrame` IDs not stored, never cancelled on module close.

**Fix**: Central manager that `pauseAll()` in `closeAllModules()`.

### Command Palette Guard

**Problem**: `Cmd+K` fires even when typing in Editor textarea or Terminal.

**Fix**: Early return if `e.target.tagName === 'INPUT' || 'TEXTAREA'`.

### Audio Memory Leak

**Problem**: `createScriptProcessor` deprecated, double-tap mic creates orphaned streams.

**Fix**: Migrate to `AudioWorkletNode`, add `isTogglingAudio` lock flag.

---

## ♿ ACCESSIBILITY CHECKLIST (WCAG 2.1 AA)

- [ ] Skip navigation link at top of page
- [ ] Focus trap in all `.module-overlay` dialogs
- [ ] `role="tablist"` + `role="tab"` + `aria-selected` on Forensics, Obsidian, Doh-Nut tabs
- [ ] Convert all `<div onclick>` to `<button>` (App Drawer, AI Labs)
- [ ] Color contrast minimum 4.5:1 for all text
- [ ] `outline: 2px solid` on `:focus-visible` for all interactive elements
- [ ] `aria-live="polite"` on dynamic content regions
- [ ] Full keyboard Tab navigation across all dock items and modules
- [ ] Touch targets minimum 48×48px on all interactive elements
- [ ] `prefers-reduced-motion` — already excellent ✅

---

## 🎨 MICRO-INTERACTION UPGRADES

### Module Transitions
```css
/* Current: translateY(100%) slide up */
/* Proposed: scale(0.96) + fade — more modern */
.module-overlay {
    transform: scale(0.96);
    opacity: 0;
    transition: transform 300ms cubic-bezier(0.16, 1, 0.3, 1),
                opacity 200ms ease-out;
}
.module-overlay.active {
    transform: scale(1);
    opacity: 1;
}
```

### Tab Underline Indicator
```css
.tab-btn.active::after {
    content: '';
    position: absolute;
    bottom: 0; left: 20%; right: 20%;
    height: 2px;
    background: var(--accent-purple);
    border-radius: 1px;
    animation: tabSlide 200ms ease-out;
}
```

### Solid Bento Patch Fix
Replace `!important` sledgehammer with scoped class:
```css
/* Instead of: .glass { box-shadow: none !important; } */
.theme-solid .glass { box-shadow: none; }
.theme-solid .glass:hover { box-shadow: 0 2px 8px rgba(255,255,255,0.05); }
```

---

## 🏎️ PERFORMANCE TARGETS

| Metric | Current | Target |
|:---|:---:|:---:|
| HTML Size | 291KB | < 150KB (extract JS/CSS) |
| First Contentful Paint | ~2.5s | < 1.5s |
| Animation FPS (mobile) | 30-45fps | 60fps |
| Memory (5min session) | Growing | Stable |
| Lighthouse Score | ~55 | > 85 |

---

## 📋 EXECUTION ROADMAP (4 Sprints)

### Sprint 1 — Foundation (~3.5 hours) → Score: 5.4 → 6.5
| # | Task | Effort | Impact |
|:---:|:---|:---:|:---:|
| 1 | Design system CSS variables | 30min | Foundation |
| 2 | Global font-size patch (8px/9px → 11px) | 20min | 🔴 Critical |
| 3 | Global touch target patch (min 48px) | 15min | 🔴 Critical |
| 4 | Contrast fix (text opacity → tokens) | 20min | 🟠 High |
| 5 | iOS input zoom fix (16px on mobile) | 10min | 🟠 High |
| 6 | Remove duplicate Quick Actions | 15min | 🟡 Moderate |
| 7 | Fix terminal double-listener | 15min | 🔴 Critical |
| 8 | Add confirmation dialogs | 15min | 🔴 Critical |

### Sprint 2 — Navigation (~3.5 hours) → Score: 6.5 → 7.5
| # | Task | Effort | Impact |
|:---:|:---|:---:|:---:|
| 9 | Dock 17→5+1 redesign | 45min | 🔴 Critical |
| 10 | App Drawer search + Recently Used | 30min | 🟡 Moderate |
| 11 | Dashboard restack | 30min | 🟠 High |
| 12 | Terminal keyboard upgrade | 20min | 🔴 Critical |
| 13 | `withLoading()` wrapper on all fetches | 30min | 🟡 Moderate |
| 14 | Empty state upgrade (8 modules) | 25min | 🟡 Moderate |
| 15 | Tablet breakpoint (768px) | 20min | 🟡 Moderate |

### Sprint 3 — Module Polish (~4.5 hours) → Score: 7.5 → 8.5
| # | Task | Effort | Impact |
|:---:|:---|:---:|:---:|
| 16 | Social Command Center (frontend) | 60min | 🔴 Critical |
| 17 | Social backend merge | 45min | 🔴 Critical |
| 18 | Render X + YouTube cards | 15min | 🟡 Moderate |
| 19 | Render Pollinations thumbnails | 15min | 🟡 Moderate |
| 20 | ARIA tab roles | 20min | 🟠 High |
| 21 | Semantic buttons (divs → buttons) | 20min | 🟠 High |
| 22 | Module transition upgrade | 15min | 🟡 Low |
| 23 | Tab underline animation | 15min | 🟡 Low |
| 24 | Scoped Solid Bento Patch | 20min | 🟡 Moderate |

### Sprint 4 — Architecture (~5.5 hours) → Score: 8.5 → 9.0
| # | Task | Effort | Impact |
|:---:|:---|:---:|:---:|
| 25 | Extract CSS to files | 60min | 🟠 High |
| 26 | Extract JS to modules | 90min | 🟠 High |
| 27 | AnimationManager lifecycle | 30min | 🟡 Moderate |
| 28 | AudioWorkletNode migration | 45min | 🟡 Moderate |
| 29 | Focus trap for modals | 20min | 🟠 High |
| 30 | Skip-nav + aria-live | 15min | 🟡 Moderate |

---

## 🏆 What's Already Excellent (Preserve)

1. OLED Pure Black theme (`#000`)
2. `touch-action: manipulation` on all buttons
3. `aria-label` on all 17 dock items
4. `env(safe-area-inset-bottom)` for iPhone notch
5. `prefers-reduced-motion` kills particles/canvas
6. `@media (hover: hover) and (pointer: fine)` hover detection
7. `history.pushState` popstate back gesture
8. `safeTg()` Telegram version checks
9. `event.stopPropagation()` on nested buttons
10. `escapeHtml()` + `DOMPurify.sanitize()` XSS protection
11. Native `<form onsubmit>` on Swarm spawn
12. Mobile scroll: `overflow-x: auto; scrollbar-width: none`

---

## Audit & Revision Ledger

| Version | Timestamp | Author | Why | How |
|:---|:---|:---|:---|:---|
| 1.0.0 | 2026-09-12 17:22 MYT | Antigravity Conductor (Opus 4.6) | Full 360° UI/UX audit requested by user | 4 parallel auditor subagents scanned all 5,406 lines; compiled 42 findings + 30-item roadmap |
