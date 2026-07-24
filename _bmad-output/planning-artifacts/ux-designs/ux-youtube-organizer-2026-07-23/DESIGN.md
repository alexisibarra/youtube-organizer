---
name: YouTube Organizer
description: A personal curation library that wears YouTube's clothes with the machinery cut out. shadcn/ui on Next.js + Tailwind v3; this DESIGN.md specifies the delta only — and the delta is deliberately close to empty.
status: final
created: 2026-07-23
updated: 2026-07-23
sources:
  - ../../prds/prd-youtube-organizer-2026-07-20/prd.md
  - ../../../../Docs/FRONTEND-STACK.md
colors:
  # ── Inheritance ────────────────────────────────────────────────
  # shadcn `neutral` tokens inherited unchanged unless listed as an
  # override below: background, foreground, card, popover, muted,
  # secondary, input, destructive-foreground.
  background: '#FFFFFF'
  background-dark: '#09090B'
  surface: '#F4F4F5'
  surface-dark: '#18181B'
  foreground: '#18181B'
  foreground-dark: '#FAFAFA'
  muted-foreground: '#71717A'
  muted-foreground-dark: '#A1A1AA'
  destructive: '#DC2626'
  destructive-dark: '#EF4444'
  # ── Contrast-driven overrides on shadcn defaults ───────────────
  # Each replaces a shadcn default that failed a measured AA check.
  # See § Colors for the computed ratios and the reason for each.
  chip-foreground: '#52525B'          # was muted #71717A → 4.40:1 on surface. Now 7.06:1.
  chip-foreground-dark: '#D4D4D8'     # 11.42:1 on surface-dark.
  border: '#D4D4D8'                   # was #E4E4E7 → 1.27:1. Now 3.02:1 for UI boundaries.
  border-dark: '#3F3F46'              # 3.09:1 on background-dark.
  border-subtle: '#E4E4E7'            # shadcn's original — decorative separators ONLY, never a control edge.
  border-subtle-dark: '#27272A'
  destructive-foreground-dark: '#FFFFFF'  # white on #EF4444 = 4.55:1; shadcn's default computed 3.61:1.
  # ── Selection (achromatic — measured 17.72:1 / 19.06:1) ────────
  selection-ring: '#18181B'
  selection-ring-dark: '#FAFAFA'
  selection-check-bg: '#18181B'
  selection-check-bg-dark: '#FAFAFA'
  selection-check-fg: '#FFFFFF'
  selection-check-fg-dark: '#09090B'
  selection-check-edge: '#FFFFFF'      # 2px outer ring separating the checkbox from arbitrary imagery
  selection-check-edge-dark: '#09090B'
  # ── Focus (must NOT read as selection — see § Components) ──────
  focus-ring: '#18181B'
  focus-ring-dark: '#FAFAFA'
  # ── Status (scrim + icon; scrim alone is invisible — see § Colors)
  status-scrim: 'rgba(255,255,255,0.55)'
  status-scrim-dark: 'rgba(9,9,11,0.60)'
  status-badge-bg: 'rgba(0,0,0,0.82)'
  status-badge-fg: '#FFFFFF'
  thumb-placeholder: '#E4E4E7'
  thumb-placeholder-dark: '#27272A'
typography:
  # Geist Sans across every role, via next/font (self-hosted at build).
  page-title:
    fontFamily: 'Geist Sans'
    fontSize: 20px
    fontWeight: '650'
    lineHeight: '1.25'
    letterSpacing: -0.02em
  section-title:
    fontFamily: 'Geist Sans'
    fontSize: 15px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.011em
  card-title:
    fontFamily: 'Geist Sans'
    fontSize: 13.5px
    fontWeight: '600'
    lineHeight: '1.32'
    letterSpacing: -0.011em
  row-title:
    fontFamily: 'Geist Sans'
    fontSize: 12.5px
    fontWeight: '500'
    lineHeight: '1.35'
    letterSpacing: -0.011em
  body:
    fontFamily: 'Geist Sans'
    fontSize: 13px
    fontWeight: '400'
    lineHeight: '1.5'
  meta:
    fontFamily: 'Geist Sans'
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1.4'
  chip:
    fontFamily: 'Geist Sans'
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1.3'
    note: 'Raised from 10.5px — chip text is product-critical and must clear AA at its own size.'
  numeric:
    fontFamily: 'Geist Sans'
    fontSize: 11px
    fontWeight: '400'
    note: 'font-variant-numeric: tabular-nums — mandatory on every duration, count and date'
rounded:
  sm: 4px
  md: 6px
  lg: 8px
  thumbnail: 12px
  full: 9999px
spacing:
  grid-gutter: 16px
  card-gap: 16px
  row-padding-y: 6px
  row-padding-x: 9px
  sidebar-width: 240px
  sidebar-width-collapsed: 72px
  bottom-bar-height: 56px
  player-max-width: 1280px
  content-max-width: 1600px
  target-min: 24px
  scroll-margin: 96px
components:
  video-card:
    radius: '{rounded.thumbnail}'
    gap: '{spacing.card-gap}'
    title: '{typography.card-title}'
    channel: '{typography.meta}'
    channel-color: '{colors.muted-foreground}'
    border: 'none'
    background: 'transparent'
  thumbnail:
    radius: '{rounded.thumbnail}'
    aspect-ratio: '16 / 9'
    placeholder: '{colors.thumb-placeholder}'
  duration-badge:
    background: '{colors.status-badge-bg}'
    foreground: '{colors.status-badge-fg}'
    radius: '{rounded.sm}'
    typography: '{typography.numeric}'
    position: 'thumbnail bottom-right'
  status-badge:
    background: '{colors.status-badge-bg}'
    foreground: '{colors.status-badge-fg}'
    radius: '{rounded.sm}'
    min-height: '{spacing.target-min}'
    position: 'thumbnail bottom-left'
    note: 'Icon glyph. Always paired with {colors.status-scrim}; never scrim alone.'
  selection-checkbox:
    background: '{colors.selection-check-bg}'
    foreground: '{colors.selection-check-fg}'
    edge: '2px solid {colors.selection-check-edge}'
    radius: '{rounded.sm}'
    size: '{spacing.target-min}'
    position: 'thumbnail top-left'
  selection-outline:
    color: '{colors.selection-ring}'
    style: 'solid'
    width: 3px
    offset: 2px
    radius: '{rounded.thumbnail}'
  focus-indicator:
    color: '{colors.focus-ring}'
    style: 'dashed'
    width: 2px
    offset: 4px
    radius: '{rounded.thumbnail}'
    note: 'DASHED, wider offset — must never be confused with solid selection.'
  tag-chip:
    radius: '{rounded.full}'
    background: '{colors.surface}'
    foreground: '{colors.chip-foreground}'
    border: '1px solid {colors.border}'
    typography: '{typography.chip}'
    min-height: '{spacing.target-min}'
  filter-chip:
    radius: '{rounded.full}'
    background: '{colors.background}'
    foreground: '{colors.chip-foreground}'
    border: '1px solid {colors.border}'
    active-background: '{colors.foreground}'
    active-foreground: '{colors.background}'
    typography: '{typography.chip}'
    min-height: '{spacing.target-min}'
  triage-row:
    padding: '{spacing.row-padding-y} {spacing.row-padding-x}'
    title: '{typography.row-title}'
    separator: '1px solid {colors.border-subtle}'
    thumbnail-width: 44px
    min-height-touch: 44px
  bulk-action-bar:
    background: '{colors.foreground}'
    foreground: '{colors.background}'
    radius: '{rounded.lg}'
    position: 'sticky bottom, above bottom-bar on mobile'
  sidebar-nav-item:
    radius: '{rounded.md}'
    active-background: '{colors.surface}'
    active-edge: '3px solid {colors.foreground}'
    active-weight: '650'
    typography: '{typography.meta}'
    min-height: '{spacing.target-min}'
    note: 'Surface tint alone computes 1.10:1 — the edge bar carries the signal.'
  shelf-row:
    title: '{typography.section-title}'
    gap: '{spacing.grid-gutter}'
    note: 'Library hub row — horizontal strip of cards + count + View more.'
  inline-banner:
    radius: '{rounded.lg}'
    background: '{colors.surface}'
    foreground: '{colors.foreground}'
    border: '1px solid {colors.border}'
    typography: '{typography.meta}'
    note: 'shadcn Alert. Never modal, never blocking.'
  tag-popover:
    radius: '{rounded.lg}'
    background: '{colors.background}'
    border: '1px solid {colors.border}'
    note: 'shadcn Popover holding the full tag set behind +N.'
---

## Brand & Style

YouTube Organizer is a personal curation library for one person. Its design premise is unusual and worth stating plainly, because every rule below descends from it: **the app should look like YouTube on purpose.**

This is not laziness or a missing brand. Alexis loves YouTube. The familiarity is load-bearing — he wants to open this app and have his hands already know where things are, because it is the same content he was always going to watch. What he is escaping is not YouTube's *appearance*; it is YouTube's *machinery*. So the design strategy is **subtractive**: keep the visual language, cut the apparatus. Same shelf, no salesman.

That produces a discipline most products don't get to have. There is no brand color. There is no logo moment. There is no signature gesture. The identity of this product is defined almost entirely by **what is absent** — see `EXPERIENCE.md.Subtraction Contract`, which is the real brand statement and lives on the experience side because absence is behavioral before it is visual.

Two consequences follow, and they are the reason this document is short:

1. **Color does no brand work.** The palette is shadcn `neutral`, overridden only where a measured contrast check forced it. Red is reserved exclusively for destruction. There is no accent hue, at all, anywhere.
2. **Type does no brand work either.** Geist Sans is chosen for legibility in dense triage, not for character.

With both of those spent to zero, **structure carries the entire familiarity budget** — card proportions, the 16:9 thumbnail with its rounded corners, the grid/list duality, the sidebar, the bottom bar, the shape of the watch page. That is why the Layout, Shapes, and Components sections below are the substantive ones and the Colors section is mostly a list of things not to touch.

The register is restraint. When a decision is close, choose the smaller, more familiar option.

> **Visual references.** `mockups/key-library.html`, `mockups/key-triage.html`, `mockups/key-watch.html`, `mockups/key-mobile.html` illustrate the compositions described here. **This spine wins on conflict** — the mocks predate several remediation decisions and are directional, not normative.

## Colors

**The palette is shadcn `neutral`.** Overrides exist only where a token was *measured* and failed WCAG 2.2 AA. Nothing here is an aesthetic override; every one is a contrast fix.

- **Neutral surfaces** (`{colors.background}` / `{colors.surface}`) are the entire chromatic environment. Dark mode is deeper than YouTube's `#0F0F0F` because thumbnails are the only saturated objects on screen and a deeper ground makes them read as content rather than decoration.
- **`{colors.destructive}`** is the *only* chromatic token, and it means exactly one thing: **this destroys something.** Because it is the sole color in an otherwise neutral field it is impossible to miss — which is the entire reason it was ringfenced. In dark mode its foreground is overridden to pure white (`{colors.destructive-foreground-dark}`); shadcn's default computed **3.61:1** on `#EF4444` and failed.
- **There is no `primary` brand color and no `accent`.** This was considered explicitly and rejected. Do not introduce YouTube red, or any hue, as a brand accent.
- **Selection is achromatic, and this is an accessibility asset rather than a compromise.** `{colors.selection-ring}` measures **17.72:1** in light mode and **19.06:1** in dark — higher than any accent hue would have achieved. The 2px `{colors.selection-check-edge}` exists because the checkbox sits on arbitrary thumbnail imagery, where the checkbox otherwise collapsed to **1.19:1** over dark thumbnails and **1.04:1** in dark mode over bright ones.
- **Status is scrim *plus* icon — never scrim alone.** Dimming is a lightness change, which is still color, and it fails outright: watched over a light thumbnail computes to **1.00:1** (literally invisible), and watched-plus-unavailable stacked resolve to byte-identical values. `{colors.status-scrim}` is therefore a *reinforcement*, and `{components.status-badge}` carries the actual signal.
- **Two border tokens, and the distinction is load-bearing.** `{colors.border}` (3.02:1) is for anything that is a **control edge** — inputs, checkboxes, chips, buttons. `{colors.border-subtle}` is shadcn's original `#E4E4E7` (1.27:1) and is permitted **only** for decorative separators that convey no boundary a user must perceive. Never use `border-subtle` on a control.
- **`{colors.chip-foreground}`** replaces muted on chips. Muted computed **4.40:1** on `{colors.surface}` — a fail, on the tag row, which is the single element this product adds to YouTube's card.

## Typography

**Geist Sans** across every role, loaded through `next/font` (self-hosted at build time — no runtime request, no layout shift, no phantom dependency). **Geist Mono** is available but unused; do not reach for it without cause.

| Role | Size / weight | Where |
|---|---|---|
| `{typography.page-title}` | 20px / 650 | Surface headings |
| `{typography.section-title}` | 15px / 600 | Shelf-row titles, dialog titles, empty-state headlines |
| `{typography.card-title}` | 13.5px / 600 | Video title, grid view |
| `{typography.row-title}` | 12.5px / 500 | Video title, list view |
| `{typography.body}` | 13px / 400 | Descriptions, dialog body |
| `{typography.meta}` | 12px / 400 | Channel names, dates, counts |
| `{typography.chip}` | 12px / 500 | Tag and filter chips |
| `{typography.numeric}` | 11px, tabular | Durations, counts, dates |

Rules:

1. **Tabular numerals are mandatory** on every duration, count and date. Durations sit in a vertical stack during triage; proportional figures jitter as you scroll.
2. **Video titles clamp, never truncate mid-layout.** Two lines in grid, one line with ellipsis in list. Titles are user-uncontrolled and frequently absurd.
3. **No display face, no serif moment, no oversized hero type.** There is no marketing surface here, and empty states are not an opportunity for personality.

## Layout & Spacing

Tailwind's 4-based scale, inherited unchanged. The named tokens hold the proportions that do the familiarity work.

**Desktop.** Persistent left sidebar at `{spacing.sidebar-width}`, collapsing to `{spacing.sidebar-width-collapsed}` icons at `md`. Content capped at `{spacing.content-max-width}`. The grid is responsive by column count, not card width — cards grow to fill, which is how YouTube behaves.

**The grid.** `{spacing.grid-gutter}` both axes. Columns: 4 at `xl`, 3 at `lg`, 2 at `md`, 2 at `sm`, **2 below** — never 1. The reason that floor exists is in `EXPERIENCE.md § Responsive & Platform`.

**The list.** `{spacing.row-padding-y}` is deliberately tight; list view exists for volume. Rows land near 32px on pointer devices and **must relax to 44px on touch** to clear the target floor.

**Watch page.** Single column, centered, capped at `{spacing.player-max-width}`. **No right rail exists at any breakpoint** — absent from the layout, not collapsed.

**Mobile.** Bottom tab bar at `{spacing.bottom-bar-height}`, plus a drawer for overflow. Safe-area insets respected. The bulk action bar stacks *above* the tab bar; they never overlap.

**Scroll margin.** Every keyboard-focusable list item carries `scroll-margin-block: {spacing.scroll-margin}` so `j`/`k` navigation never parks focus underneath the sticky bulk action bar or the mobile tab bar (WCAG 2.4.11).

## Elevation & Depth

Almost none, and that is a decision.

- **Cards have no shadow, no border, and no background fill.** A video card is a thumbnail with text under it, floating on the page ground. This is YouTube's own treatment and why a YouTube grid reads as *content* rather than as containers. Do not put cards in boxes.
- **Elevation is reserved for genuine layering:** dialogs, popovers, dropdowns, toasts, the bulk action bar. These inherit shadcn's shadow tokens unchanged.
- **The bulk action bar** uses an inverted fill rather than a heavy shadow, which reads unambiguously in both modes.
- **No hover elevation on cards.** Hover reveals affordances; it does not lift.

## Shapes

Corner radii carry more familiarity load here than anywhere else, because color and type carry none.

- **`{rounded.thumbnail}` (12px)** on every thumbnail and card. The single most important number in this document — YouTube's own thumbnail radius, and the strongest cue that this is the same kind of object. Deliberately larger than shadcn's `lg`.
- **`{rounded.full}`** on tag chips, filter chips, avatars.
- **`{rounded.lg}` (8px)** for dialogs, popovers, banners, the bulk action bar.
- **`{rounded.md}` (6px)** for buttons and sidebar nav items.
- **`{rounded.sm}` (4px)** for inputs, checkboxes, duration and status badges.

Rule: **anything holding a thumbnail gets 12px; anything holding a word gets 4–8px; anything holding a tag gets a pill.**

## Components

Used **unchanged** from shadcn: `Button`, `Dialog`, `AlertDialog`, `DropdownMenu`, `Popover`, `Select`, `Sheet`, `Toast`, `Skeleton`, `Separator`, `Switch`, `Tabs`, `Input`, `Label`, `Checkbox`, `Calendar`, `Alert`. Do not customize these; generate via `npx shadcn@latest add`, never hand-edit `src/components/ui/`.

- **Video card** (`{components.video-card}`) — The atom of the product. Anatomy: 16:9 thumbnail at `{rounded.thumbnail}`, title (2-line clamp), channel in `{colors.muted-foreground}`, then the tag row. No border, fill, or shadow. **The tag row is the app's one addition to YouTube's card** and must never be crowded out by status.
- **Thumbnail status layer** — All status renders *on* the thumbnail. Duration bottom-right (always — duration is content). Selection top-left. Status badge bottom-left. **Silent unless abnormal:** nothing renders for the default state; freshness renders nothing until a perishable window has actually expired.
- **Status badge** (`{components.status-badge}`) — Icon glyph on `{colors.status-badge-bg}`, paired with `{colors.status-scrim}`. Icons: ✓ watched, ⚠ unavailable, ⏳ expired. When two apply, both render side by side — they must remain individually legible, which is why the badge is opaque rather than another scrim.
- **Selection treatment** (`{components.selection-outline}` + `{components.selection-checkbox}`) — Solid 3px outline at 2px offset, plus a 24px filled checkbox with a 2px contrasting edge. Both, always. Redundant by design.
- **Focus indicator** (`{components.focus-indicator}`) — **Dashed, 2px, 4px offset.** Deliberately different in *style* from selection, not merely in width. A solid ring differing by 1px was indistinguishable during keyboard triage across a mostly-selected grid.
- **Tag chip** (`{components.tag-chip}`) — Pill, `{typography.chip}`, 24px minimum height. Read-only in browse contexts (click filters); inline-editable on the watch page. **Overflow past three collapses to `+N`, which opens `{components.tag-popover}`** with the full set.
- **Filter chip** (`{components.filter-chip}`) — Pill, horizontally scrollable. **Tags only** — structured facets live behind a Filters panel. Active state inverts to a foreground fill, the same achromatic inversion used for selection.
- **Triage row** (`{components.triage-row}`) — Checkbox, 44px thumbnail, title (1-line ellipsis), channel, duration. Separator uses `{colors.border-subtle}`; the row is not a control, its checkbox is.
- **Bulk action bar** (`{components.bulk-action-bar}`) — Sticky, inverted fill, appears only when a selection is live. **Destructive actions live here, bound to the selection — never on individual cards.**
- **Sidebar nav item** (`{components.sidebar-nav-item}`) — Active state is a `{colors.surface}` pill **plus a 3px foreground edge bar**. The tint alone computes **1.10:1** and cannot carry the signal; no grey light enough to look like a tint clears 3:1.
- **Shelf row** (`{components.shelf-row}`) — The Library hub unit: a section title with count, a horizontal strip of cards, and a "View more →" link. One per organizational dimension.
- **Inline banner** (`{components.inline-banner}`) — shadcn `Alert`. Sync progress, partial failures, orphans, quota. Never modal, never blocking, never auto-dismissing when it reports a failure.

## Do's and Don'ts

| Do | Don't |
|---|---|
| Keep the palette shadcn `neutral`, overriding only for measured contrast | Introduce YouTube red — or any hue — as a brand or accent color |
| Reserve `{colors.destructive}` strictly for destruction | Use red for the logo, active states, badges, or emphasis |
| Signal selection with solid outline + filled checkbox | Signal selection with a colored fill or tint |
| Signal focus with a **dashed** ring at a wider offset | Make focus a solid ring that reads as selection |
| Pair every status scrim with a status badge | Convey watched, unavailable or expired by dimming alone |
| Use `{colors.border}` on any control edge | Use `{colors.border-subtle}` on anything a user must perceive |
| Use `{rounded.thumbnail}` (12px) on every thumbnail | Fall back to shadcn's 8px — the 12px *is* the familiarity |
| Let cards float — no border, fill, or shadow | Put video cards inside bordered or elevated containers |
| Two columns minimum on phones | Ship a single-column full-width feed (that shape *is* the doomscroll) |
| Keep the watch page single-column at every breakpoint | Add a right rail — for recommendations, queue, or anything else |
| Keep every interactive target ≥ `{spacing.target-min}` | Ship 17px checkboxes or 18px chips |
| Tabular numerals on every duration and count | Let proportional figures make the duration column jitter |
| Attach destructive actions to the selection | Put a delete affordance on individual cards |
| Reach for the smaller, more familiar option | Invent a novel pattern where a YouTube-shaped one exists |
