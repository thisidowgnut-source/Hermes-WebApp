---
title: "Hermes OS & Doh-Nut Sovereign Mission Control — UI/UX Design Specifications"
document_id: "HERMES-WEBAPP-DSG-001"
version: "3.6.0"
last_updated: "2026-09-12 16:35:00 MYT"
maintainer: "GangBo Sovereign Architect"
classification: "ENGINEERING DOCS // DESIGN SYSTEM"
lifecycle_status: "PRODUCTION / STABLE"
---

# UI/UX Design Specifications — Hermes OS WebApp

> **Anti-AI Slop Protocol & Emil Kowalski Craft Standard** — Strict design rules and mobile-first ergonomics for the Telegram Mini App and desktop PWA.  
> **Design Tokens**: See `design-system/hermes-webapp/MASTER.md` for canonical values.

---

## 📜 Audit & Revision Ledger

| Version | Timestamp (MYT / ISO) | Author / Agent | Scope / Root Cause | Components Updated | Validation Proof |
|:---|:---|:---|:---|:---|:---|
| **`3.6.0`** | 2026-09-12 16:35:00<br>`2026-09-12T08:35:00Z` | Antigravity Conductor | Kemasan Butang Emil Kowalski (Zero-Jitter) dan Arkitektur Mobile-First Sifar-Bertindih. | `docs/DESIGNS.md`, CSS Button Rules, Safe-Area Equation, Flex Guards | 0 jitter butang pada hover, 0 bertindih pada 390x844 & 360x740. |
| **`3.5.0`** | 2026-09-12 15:22:00<br>`2026-09-12T07:22:00Z` | Antigravity Conductor | Reka bentuk antaramuka Doh-Nut Sovereign HQ (#mod-dohnut) & 16-modul dock. | `docs/DESIGNS.md`, `static/index.html` | Chrome DevTools Desktop & Mobile verified. |
| **`3.0.0`** | 2026-07-27 18:00:00<br>`2026-07-27T10:00:00Z` | Hermes Dev Squad | Bento-Box Dashboard reka bentuk semula, Termux keyboard, CSS z-index fix. | `static/index.html` | Lulus 84/84 tests. |

---

## 1. Aesthetic Protocol (The "Anti-AI Slop" Rule)

This project enforces **high-fidelity, professional, serious aesthetics**. Generic "chat-bot" or "toy" designs are forbidden.

### ❌ Prohibited Elements
| Element | Reason |
|---------|--------|
| Gradients (linear/radial) | No functional purpose, looks cheap |
| Excessive glassmorphism blur | Muddies UI, kills contrast |
| Emoji icons (🤖, 🧹, ⚙️) | Unprofessional, inconsistent |
| Default browser styling | Generic, not branded |
| Blue/red primary colors | Not on-brand |
| Layout-shifting hover transforms | Janky on mobile |
| Placeholder text in production | Unfinished feel |

### ✅ Mandatory Elements
| Rule | Specification |
|------|---------------|
| **Background** | Pure Black `#000000` (OLED) |
| **Card Background** | Zinc `#020617` → `#1E293B` |
| **Primary Text** | White `#F8FAFC` |
| **Accent/CTA** | Green `#16A34A` (running/active) |
| **Destructive** | Red `#DC2626` (stop/kill) |
| **Border** | `#334155` (Zinc 700) |
| **Typography** | **JetBrains Mono** exclusively (headings + body) |
| **Icons** | Lucide Icons (SVG only, 1.5–2 stroke width) |
| **Glassmorphism** | Structural: `backdrop-filter: blur(16px)`, `border: 1px solid rgba(255,255,255,0.06)` |
| **Transitions** | 150–300ms on all interactive elements |
| **Focus States** | Visible ring for keyboard accessibility |

---

## 2. Layout Architecture

### 2.1 Bento-Box Grid
- Discrete, bordered rectangles (`rounded-xl`, `border border-zinc-800`)
- CSS Grid with fixed columns/rows — no masonry
- Cards: `background: #020617`, `box-shadow: var(--shadow-md)`

### 2.2 Scroll-Lock (`100vh`)
- `body`, `main` → `height: 100vh`, `overflow: hidden`
- Safe area insets: `padding-bottom: env(safe-area-inset-bottom)`
- **No internal scrolling** — use fullscreen slide-ups for dense content

### 2.3 Dock Navigation (Bottom)
- Fixed bottom bar (Mac OS Dock style)
- 16 subsystems modular launcher with snap points
- Z-index: 40 (above grid, below overlays)

### 2.4 Mobile-First Zero-Overlap Architecture
- **Safe-Area Bottom Clearance**:
  ```css
  main {
    padding-bottom: calc(140px + env(safe-area-inset-bottom, 28px)) !important;
  }
  ```
  Guarantees lowest interactive buttons maintain >20px clear buffer above `#bottom-dock`.
- **Flexbox Collapse Guard**:
  ```css
  #agent-stream-container {
    min-height: 180px !important;
    flex-shrink: 0 !important;
    max-height: 240px !important;
  }
  ```
  Prevents flex containers from collapsing to 0px on compact viewports (360x740 Android).
- **Responsive 3-Column Touch Matrix (<640px)**:
  ```css
  .action-launchers-grid {
    grid-template-columns: repeat(3, 1fr) !important;
  }
  ```
  Each button: `min-height: 52px`, `font-size: 10px`, `padding: 8px 4px` — 0 text truncation, 0 icon collision.
- **List Scroll Clearance**:
  All scrollable sub-panels (`.kanban-column-body`, catalog items, logs) feature `padding-bottom: 36px` to ensure the final item is never clipped.

---

## 3. Interaction Design

### 3.1 Fullscreen Slide-Up Overlays
| Module | Trigger | Transition |
|--------|---------|------------|
| Terminal | Dock item 2 | `translateY(100%)` → `translateY(0)` |
| Browser | Dock item 3 | `translateY(100%)` → `translateY(0)` |
| Swarm | Dock item 4 | `translateY(100%)` → `translateY(0)` |
| Audio | Voice badge | `translateY(100%)` → `translateY(0)` |
| Doh-Nut HQ | Dock item 16 | `translateY(100%)` → `translateY(0)` |

- Overlay obscures dock + header
- Prominent `(X)` close button (top-right)
- Spring-back animation on close

### 3.2 Feedback & Micro-animations
| Interaction | Feedback |
|-------------|----------|
| Button tap | `active:scale-[0.97]` + opacity |
| Card hover | `transform: translateY(-2px)`, `box-shadow: var(--shadow-lg)` |
| Dock item hover | Magnification + glow |
| WS connect/disconnect | Toast notification (top-center) |
| HITL request | Pulsing badge + sound/vibration |

### 3.3 HITL (Human-in-the-Loop) UI
- **Incoming request**: Fullscreen modal (z-index: 100)
- **Context display**: Screenshot, URL, agent name, reason badge
- **Actions**: `[Continue] [Abort] [Retry] [Custom...]`
- **Timeout**: Visual countdown bar (300s default)
- **Priority colors**: Low=Gray, Med=Amber, High=Green, Critical=Red

### 3.4 Emil Kowalski Zero-Jitter Button Standard (The Anti-Wobble Rule)
- **Root Cause Eliminated**: Button jitter was caused by interactive buttons inheriting the `.glass` class and being swept into the `MagicBento` pointer-tracking loop, triggering conflicting magnetic `translate()` offsets against CSS button transforms.
- **Class Hygiene**: Strictly stripped `.glass` from 52 interactive buttons, tabs, and switches.
- **Selector Guardrails**:
  ```javascript
  const bentoCards = document.querySelectorAll('.card:not(button):not(.btn)');
  ```
- **Instant Tactile Feedback**:
  ```css
  button:active, .btn:active, .tab-btn:active {
    transform: scale(0.97) !important;
    transition: transform 0.1s ease !important;
  }
  ```
- **Touch Hover Scoping**:
  Hover styles are wrapped in `@media (hover: hover) and (pointer: fine)` so mobile taps do not trigger persistent, sticky hover outlines.

---

## 4. Component Specifications

### 4.1 Bento Card (Base)
```css
.bento-card {
  background: var(--color-background-card);  /* #020617 */
  border: 1px solid var(--color-border);     /* #334155 */
  border-radius: var(--radius-xl);           /* 12px */
  padding: var(--space-md);                  /* 16px */
  box-shadow: var(--shadow-md);
  transition: transform 200ms, box-shadow 200ms, border-color 200ms;
}
.bento-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  border-color: var(--color-border-hover);   /* #475569 */
}
```

### 4.2 Primary Button (CTA)
```css
.btn-primary {
  background: var(--color-accent);           /* #16A34A */
  color: var(--color-on-primary);            /* #FFFFFF */
  padding: var(--space-sm) var(--space-lg);
  border-radius: var(--radius-lg);
  font-weight: 600;
  font-family: var(--font-mono);             /* JetBrains Mono */
  transition: opacity 150ms, transform 150ms;
}
.btn-primary:active {
  opacity: 0.9;
  transform: scale(0.97);
}
```

### 4.3 Terminal / Code Areas
```css
.terminal-area {
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.5;
  background: #000000;
  color: #E0E0E0;
}
```

### 4.4 Metric Display (Dashboard)
```css
.metric-value {
  font-family: var(--font-mono);
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: 500;
  letter-spacing: -0.02em;
}
.metric-label {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-muted);  /* #94A3B8 */
}
```

---

## 5. Color Tokens (Canonical)

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-background` | `#020617` | Page background |
| `--color-background-card` | `#020617` | Card background |
| `--color-foreground` | `#F8FAFC` | Primary text |
| `--color-muted` | `#94A3B8` | Labels, secondary text |
| `--color-border` | `#334155` | Card borders |
| `--color-accent` | `#16A34A` | Primary actions, running status |
| `--color-accent-hover` | `#15803D` | Button hover |
| `--color-destructive` | `#DC2626` | Kill, delete, critical |
| `--color-warning` | `#F59E0B` | Pending, medium priority |
| `--color-ring` | `#16A34A` | Focus rings |

---

## 6. Spacing & Shadow Tokens

| Token | Value |
|-------|-------|
| `--space-xs` | `4px` |
| `--space-sm` | `8px` |
| `--space-md` | `16px` |
| `--space-lg` | `24px` |
| `--space-xl` | `32px` |
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` |
| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.15)` |

---

## 7. Responsive Breakpoints

| Breakpoint | Target |
|------------|--------|
| `375px` | iPhone SE / Mini App narrow |
| `390px` | iPhone 12/13/14 standard |
| `414px` | iPhone Plus/Pro Max |
| `768px` | Tablet / Telegram Desktop sidebar |
| `1024px` | Desktop browser testing |

---

## 8. Accessibility Checklist

- [ ] `prefers-reduced-motion` respected (disable transitions)
- [ ] Focus visible on all interactive elements
- [ ] Color contrast ≥ 4.5:1 (WCAG AA)
- [ ] Touch targets ≥ 44×44px
- [ ] ARIA labels on icon-only buttons
- [ ] Semantic HTML structure
- [ ] No horizontal scroll on mobile

---

## 9. Implementation Reference

| File | Purpose |
|------|---------|
| `static/index.html` | Main SPA — all components inline |
| `design-system/hermes-webapp/MASTER.md` | Canonical design tokens |
| `design-system/hermes-webapp/pages/` | Page-specific overrides |

---

*All UI changes MUST comply with this spec. Agents modifying UI must re-read this document before editing.*