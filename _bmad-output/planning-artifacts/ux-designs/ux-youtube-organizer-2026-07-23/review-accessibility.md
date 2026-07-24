---
name: YouTube Organizer — Accessibility Review
type: review
standard: WCAG 2.2 Level AA
reviewed: DESIGN.md, EXPERIENCE.md
date: 2026-07-23
status: draft
---

# Accessibility Review — YouTube Organizer UX Spine

Audited against **WCAG 2.2 Level AA**, both modes (light + dark), both surfaces (desktop + mobile web).
All contrast ratios below were computed from the stated hex values using the WCAG 2.x relative-luminance formula, not estimated.

---

## Overall Verdict

The achromatic thesis is, for the most part, **an accessibility asset rather than a liability**: the selection outline and the inverted bulk-action bar land at 17.7:1 / 19.1:1, which no accent hue would have beaten, and the "outline plus filled checkbox" redundancy satisfies 1.4.1 by construction. Three things break it. First, **status-by-scrim is dimming-only**, and dimming is a lightness change — i.e. still colour — so watched / unavailable / expired currently fail 1.4.1 outright, and two stacked scrims resolve to a 1.20–1.51:1 difference from one scrim, making the combined state unreadable by anyone. Second, the **focus indicator and the selection indicator are the same visual object** (a foreground-coloured outline on the thumbnail), so during keyboard triage — the product's core loop — a user cannot see where focus is inside a selection. Third, the **entire keyboard map is single-character with no modifier, no off-switch and no focus scoping**, which is a direct, unambiguous 2.1.4 failure that the spine currently states as a *virtue*.

Secondary but pervasive: the spine's claim that "shadcn `neutral` ships WCAG AA-compliant defaults" is **factually wrong** for three tokens I computed, and target size (2.5.8) is missed by the 17px checkbox and the 10.5px tag chips.

**Verdict: not AA-ready as specified.** 3 critical, 9 high, 12 medium, 6 low. All are fixable inside the achromatic discipline — none of the fixes require introducing an accent hue.

---

## Computed Contrast Ratios

Thresholds: **4.5:1** normal text (< 18.66px, or < 24px if bold), **3:1** large text and non-text UI components (1.4.11).
The type ramp tops out at 20px/650 for page titles; **every other role in this design is "normal text"** and needs 4.5:1. Micro at 10.5px is emphatically normal text.

### Light mode

| Foreground | Background | Ratio | Required | Result | Where |
|---|---|---|---|---|---|
| foreground `#18181B` | bg `#FFFFFF` | **17.72** | 4.5 | PASS | All body / titles / rows |
| foreground `#18181B` | surface `#F4F4F5` | **16.12** | 4.5 | PASS | Text on chips, sidebar pill |
| muted-foreground `#71717A` | bg `#FFFFFF` | **4.83** | 4.5 | PASS (thin) | Channel names, meta, dates |
| muted-foreground `#71717A` | surface `#F4F4F5` | **4.40** | 4.5 | **FAIL** | **Tag chip text @ 10.5px** |
| destructive `#DC2626` | bg `#FFFFFF` | **4.83** | 4.5 | PASS (thin) | Error text on page |
| destructive `#DC2626` | surface `#F4F4F5` | **4.39** | 4.5 | **FAIL** | **Error text on any surface panel** |
| `#FAFAFA` (destructive-fg) | destructive `#DC2626` | **4.63** | 4.5 | PASS (thin) | Destructive button label |
| border `#E4E4E7` | bg `#FFFFFF` | **1.27** | 3.0 (1.4.11) | **FAIL** | **Input borders, chip borders, row separators** |
| border `#E4E4E7` | surface `#F4F4F5` | **1.15** | 3.0 (1.4.11) | **FAIL** | Chip border on surface |
| **active-nav pill `#F4F4F5`** | **bg `#FFFFFF`** | **1.10** | 3.0 (1.4.11) | **FAIL — worst in the system** | Sidebar active state |
| selection ring `#18181B` | bg `#FFFFFF` (via 2px offset) | **17.72** | 3.0 | PASS | Selection outline |
| checkbox fill `#18181B` | white thumbnail region | **17.72** | 3.0 | PASS | Best case |
| checkbox fill `#18181B` | **dark thumbnail region `#000`** | **1.19** | 3.0 | **FAIL** | **Worst case — checkbox disappears** |
| checkmark `#FFFFFF` | checkbox fill `#18181B` | **17.72** | 3.0 | PASS | Glyph inside checkbox |
| bulk bar text `#FFFFFF` | bulk bar `#18181B` | **17.72** | 4.5 | PASS | Count + actions |
| filter chip active `#FFFFFF` on `#18181B` | — | **17.72** | 4.5 | PASS | Active filter |
| filter chip inactive `#71717A` | `#FFFFFF` | **4.83** | 4.5 | PASS (thin) | Inactive filter |
| duration badge `#FFFFFF` | `rgba(0,0,0,.82)` over white thumb → `#2E2E2E` | **13.58** | 4.5 | PASS | Worst case for the badge |
| duration badge `#FFFFFF` | `rgba(0,0,0,.82)` over black thumb → `#000` | **21.00** | 4.5 | PASS | Best case |
| shadcn focus ring `#18181B` | bg `#FFFFFF` | **17.72** | 3.0 | PASS | 2.4.11 / 1.4.11 |
| shadcn focus ring `#18181B` | surface `#F4F4F5` | **16.12** | 3.0 | PASS | Focus on chips/nav |

### Dark mode

| Foreground | Background | Ratio | Required | Result | Where |
|---|---|---|---|---|---|
| foreground `#FAFAFA` | bg `#09090B` | **19.06** | 4.5 | PASS | All body / titles / rows |
| foreground `#FAFAFA` | surface `#18181B` | **16.97** | 4.5 | PASS | Text on chips, sidebar pill |
| muted-foreground `#A1A1AA` | bg `#09090B` | **7.76** | 4.5 | PASS | Channel names, meta |
| muted-foreground `#A1A1AA` | surface `#18181B` | **6.91** | 4.5 | PASS | Tag chip text |
| destructive `#EF4444` | bg `#09090B` | **5.29** | 4.5 | PASS | Error text |
| destructive `#EF4444` | surface `#18181B` | **4.71** | 4.5 | PASS (thin) | Error text on panel |
| `#FAFAFA` (destructive-fg) | destructive `#EF4444` | **3.61** | 4.5 | **FAIL** | **Destructive button label, dark mode** |
| `#09090B` on destructive `#EF4444` | — | **5.29** | 4.5 | PASS | The fix for the row above |
| border `#27272A` | bg `#09090B` | **1.34** | 3.0 (1.4.11) | **FAIL** | Input borders, separators |
| border `#27272A` | surface `#18181B` | **1.19** | 3.0 (1.4.11) | **FAIL** | Chip borders |
| **active-nav pill `#18181B`** | **bg `#09090B`** | **1.12** | 3.0 (1.4.11) | **FAIL** | Sidebar active state |
| selection ring `#FAFAFA` | bg `#09090B` (via 2px offset) | **19.06** | 3.0 | PASS | Selection outline |
| checkbox fill `#FAFAFA` | dark thumbnail region | **19.06** | 3.0 | PASS | Best case |
| checkbox fill `#FAFAFA` | **white thumbnail region** | **1.04** | 3.0 | **FAIL** | **Worst case — checkbox disappears** |
| bulk bar text `#09090B` | bulk bar `#FAFAFA` | **19.06** | 4.5 | PASS | Count + actions |
| shadcn focus ring `#D4D4D8` | bg `#09090B` | **13.46** | 3.0 | PASS | 2.4.11 / 1.4.11 |

### Scrim analysis (status layer)

Contrast here is measured as **scrimmed vs. unscrimmed** — i.e. how much a user can tell the two apart. 1.4.11 wants ≥ 3:1 for a state indicator.

| Scrim | Over black thumb | Over mid-grey thumb | Over white thumb |
|---|---|---|---|
| watched, light `rgba(255,255,255,.55)` | 6.25 PASS | **2.31 FAIL** | **1.00 FAIL (invisible)** |
| watched, dark `rgba(9,9,11,.60)` | **1.03 FAIL (invisible)** | **2.92 FAIL** | 5.32 PASS |
| unavailable, light `rgba(244,244,245,.72)` | 9.68 PASS | **2.66 FAIL** | **1.07 FAIL (invisible)** |
| unavailable, dark `rgba(9,9,11,.72)` | **1.04 FAIL (invisible)** | 3.63 PASS | 8.31 PASS |

**Stacked scrims (watched AND unavailable), light mode** — can a user tell "both" from "unavailable only"?

| Thumbnail | watched only | both | unavailable only | both vs. unavailable-only |
|---|---|---|---|---|
| black | `#8C8C8C` | `#D7D7D8` | `#B0B0B0` | **1.51 FAIL** |
| mid-grey | `#C6C6C6` | `#E7E7E8` | `#D4D4D4` | **1.20 FAIL** |
| white | `#FFFFFF` | `#F7F7F8` | `#F7F7F8` | **1.00 — literally identical** |

The scrims are also **non-commutative in effect but convergent in appearance**: past ~0.7 combined alpha every thumbnail lands in the same narrow band, so "watched", "unavailable" and "watched + unavailable" become the same picture.

### Remediation candidates (computed, so you don't have to guess)

| Candidate | On | Ratio | Use for |
|---|---|---|---|
| `#B91C1C` (red-700) | `#FFFFFF` | **6.47** | Light-mode error *text* |
| `#B91C1C` (red-700) | `#F4F4F5` | **5.89** | Light-mode error text on surface |
| `#09090B` | `#EF4444` | **5.29** | Dark destructive button *label* |
| `#52525B` (zinc-600) | `#F4F4F5` | **7.03** | Tag chip text on surface (replaces 4.40) |
| `#52525B` (zinc-600) | `#FFFFFF` | **7.73** | Meta text wanting margin |
| `#71717A` (zinc-500) | `#FFFFFF` | **4.83** | Minimum viable light border at 3:1+ |
| `#71717A` (zinc-500) | `#09090B` | **4.12** | Dark-mode border/boundary at 3:1+ |
| `#A1A1AA` (zinc-400) | `#09090B` | **7.76** | Strong dark-mode boundary |
| `#949499` | `#FFFFFF` | **3.02** | Absolute lightest border that clears 1.4.11 in light mode |

Note the last row: **no "subtle grey pill" can ever reach 3:1 on white.** `#EAEAEB` → 1.20, `#DCDCE0` → 1.37, `#C9C9CE` → 1.65. The active-nav problem cannot be solved by darkening the pill without destroying the restraint the design is built on. It must be solved with a different indicator. Same in dark: `#2E2E33` on `#09090B` → 1.47, `#4C4C55` → 2.34.

---

## Findings

### CRITICAL

---

**C-1 · Status is conveyed by dimming alone — dimming is colour**
**SC:** 1.4.1 Use of Color (A), 1.3.1 Info and Relationships (A), 1.4.11 Non-text Contrast (AA)
**Location:** `DESIGN.md` § Colors ("Status uses opacity, not hue"), § Components → *Thumbnail status layer*, Do's/Don'ts row 4; `EXPERIENCE.md` § Component Patterns → *Thumbnail status layer*

A translucent scrim is a **lightness change**, and WCAG's definition of "color" covers hue, saturation *and* lightness. "Dimmed" is therefore not an escape from 1.4.1 — it *is* the colour-only signal, just an achromatic one. The design explicitly forbids the redundancy that would rescue it ("Don't: Add colored status badges to the card body"). The numbers make it worse: over a mid-tone thumbnail, watched-light is a **2.31:1** difference and unavailable-light is **2.66:1** — both below 3:1, both invisible on a phone in daylight, both invisible to a low-vision user with reduced contrast sensitivity. Over the extreme ends of the thumbnail range the scrim vanishes entirely (**1.00:1** light-over-white, **1.03:1** dark-over-black), and thumbnails are user-uncontrolled: a bright white vlog thumbnail in light mode shows *no* watched state at all.

Stacking is the killer. Watched + unavailable resolves to **1.20–1.51:1** away from unavailable alone, and on a light thumbnail the two composites are byte-identical `#F7F7F8`. UJ-4 step 4 walks the user straight into this state.

There is also a **direct contradiction between the two spines** that must be resolved before build:
- `DESIGN.md`: "Watched and unavailable apply their scrim to the whole thumbnail" + "Don't add status badges to the card body."
- `EXPERIENCE.md` § Accessibility Floor: "Watched, unavailable, and expired are dimming **plus an icon or label**, never a colored dot."
- `.memlog.md` entry 41: "WATCHED dims the whole thumbnail (**plus badge**)."

EXPERIENCE.md and the memlog are right; DESIGN.md dropped the badge. And the expired-perishable marker's visual form is flagged unresolved in memlog entry 45 item 6 — it is still unresolved, so the third status has no specified rendering at all.

**Fix.** Keep the scrim as reinforcement, add a *shape* signal that lives **on the thumbnail** (so the Do's/Don'ts "not in the card body" rule survives intact):
- Watched → a small filled pill bottom-left of the thumbnail, `rgba(0,0,0,.82)` fill + `#FFFFFF` glyph/label, i.e. the **exact treatment already proven by the duration badge at 13.58–21.00:1**. Icon (eye / check) plus visually-hidden text "Watched".
- Unavailable → a full-width strip across the thumbnail with the same opaque treatment reading "Unavailable", plus a 1px `#71717A` boundary on the card so the state survives on any thumbnail.
- Expired-perishable → resolve the marker now; same badge system, distinct glyph.
- The three markers must be **mutually stackable and individually legible** — badge, not scrim, carries the identity; scrim only carries the mood.
- Every marker exposes a text equivalent to AT (visually-hidden span or `aria-label` on the card), so "watched" is not lost to screen-reader users.
- Amend the DESIGN.md Do's/Don'ts row to "Signal status with an opaque marker *on the thumbnail*, reinforced by dimming / Don't rely on dimming alone."

---

**C-2 · Focus and selection are the same visual indicator — keyboard triage has no visible focus**
**SC:** 2.4.7 Focus Visible (AA), 2.4.13 Focus Appearance (AAA, advisory)
**Location:** `DESIGN.md` § Components → *Selection treatment* (`{components.selection-outline}`), § Elevation; `EXPERIENCE.md` § Accessibility Floor ("Focus rings inherit shadcn's `ring` token"), § Interaction Primitives (`j`/`k`)

Selection is a **3px `{colors.foreground}` outline at 2px offset around the thumbnail**. shadcn's focus ring is `ring-2 ring-ring ring-offset-2`, where `--ring` in the neutral theme resolves to essentially the foreground colour. So a focused card and a selected card are both "a dark ring, offset, around the thumbnail," differing only by 1px of stroke width. In the core loop — `j`/`k` to move, `x` to toggle, across a grid where most items are already selected — **the user cannot see where focus is.** This is the single most-executed keyboard interaction in the product and it has no reliable focus indicator. 2.4.7 requires a visible focus indicator; an indicator that is visually indistinguishable from a different, simultaneously-present state does not satisfy it.

**Fix.** Give the two states orthogonal geometry, still achromatic:
- **Selection** → keep the 3px solid foreground outline + filled checkbox.
- **Focus** → a *double* ring: inner 2px `{colors.background}` + outer 2px `{colors.foreground}`, drawn tight to the thumbnail with **no** offset gap, so a focused-and-selected card reads as two concentric rings separated by a light band. This is the WCAG 2.4.13 "two-colour indicator" pattern and it survives on any thumbnail.
- Alternatively, move focus indication off the ring entirely — e.g. a 3px foreground bar along the left edge of the row/card — so ring = selection, bar = focus, permanently.
- Add an explicit line to `EXPERIENCE.md` § Accessibility Floor: "Focus and selection must remain distinguishable when both are present on the same element."

---

**C-3 · Every shortcut is a single character with no modifier, no off-switch, no remap, and no focus scoping**
**SC:** 2.1.4 Character Key Shortcuts (**AA**)
**Location:** `EXPERIENCE.md` § Interaction Primitives → Keyboard table; § Accessibility Floor bullet "Every keyboard shortcut is modifier-free and single-key; nothing requires a chord or a held key"

2.1.4 states that if a keyboard shortcut is implemented using only letter, punctuation, number or symbol characters, then **at least one** of the following must be true: it can be turned off; it can be remapped to include a non-printable key; or it is **active only when the relevant component has focus**. The spine offers none of the three, and the Accessibility Floor section presents the violation as a feature.

In scope of 2.1.4: `j` `k` `x` `a` `t` `f` `v` `/` and the `g`-prefixed chords `g l` / `g u` / `g t` / `g p` (a two-character sequence is still composed of printable characters — the prefix does not exempt it). Out of scope, and fine as specified: `Esc`, `Enter`, `Backspace`, `Del`, `Shift`+click.

Three concrete harms, not just a paper failure:

1. **Speech input.** Dragon/Voice Control users emit stray characters constantly. A stray `a` selects all hundred loaded videos; a stray `Backspace` after that opens a delete-100 dialog. `t` and `f` mutate data with no confirmation at all.
2. **Screen-reader browse mode.** NVDA and JAWS reserve single letters for quick navigation: `t` = table, `f` = form field, `l` = list, `g` = graphic, `k` = link (JAWS), `x` = checkbox (NVDA), `v` = visited link (JAWS). In browse mode the SR swallows these and the app's shortcuts **never fire**; if the app forces application/forms mode to capture them, the user loses quick-nav across the whole page. Either way the keyboard-accelerated triage that is the desktop product's entire premise is unavailable to screen-reader users. The spine never addresses this.
3. **Text entry.** `/` focuses search, `t` opens a tag typeahead — but nothing in the spine says shortcuts are suppressed while focus is inside an `input`, `textarea`, `contenteditable`, or the player `iframe`. Typing "footage" into the tag field would fire `f`, `t`, `a`, `g` if unguarded. (Bonus collision: `j`, `k` and `f` are YouTube's *own* player shortcuts — seek-back, play/pause, fullscreen — so while focus is in the embed the same keys mean something different.)

**Fix.** All four, not one:
- **Scope to focus.** Shortcuts fire only when focus is within the video grid/list roving-tabindex container. This alone satisfies 2.1.4 and is the cheapest option.
- **Hard-suppress** on `input`, `textarea`, `[contenteditable]`, any `role="textbox"`/`combobox`, and while the player iframe has focus.
- **Add a Settings toggle** "Keyboard shortcuts: on / off" (Settings already exists and already holds theme + watched threshold).
- **Offer modifier-qualified aliases** for the destructive/high-blast-radius ones — `a` (select all) and `Backspace` (discard) at minimum.
- Rewrite the Accessibility Floor bullet: it currently asserts the opposite of the requirement and will otherwise be treated as a spec by downstream implementers.

---

### HIGH

---

**H-1 · Active nav pill at 1.10:1 (light) / 1.12:1 (dark) — the state indicator is effectively invisible**
**SC:** 1.4.11 Non-text Contrast (AA)
**Location:** `DESIGN.md` frontmatter `components.sidebar-nav-item.active-background: '{colors.surface}'`; § Components → *Sidebar nav item*

`#F4F4F5` on `#FFFFFF` computes to **1.10:1**; the dark pair `#18181B` on `#09090B` to **1.12:1**. Against a 3:1 requirement these are not near-misses, they are roughly a third of the way there. The suspicion in the brief is correct.

The redundant signal — weight 400 → 650 at `{typography.meta}` (12px) — does rescue **1.4.1** (weight is a non-colour visual means), so this is *not* a use-of-colour failure. But a 12px weight bump is a weak sole indicator for low-vision users, and 1.4.11 still applies to the pill because the pill is the thing drawn to indicate state.

As computed above, **the pill cannot be tuned into compliance**: the lightest grey that clears 3:1 on white is about `#949499`, which is a mid-grey chip, not a subtle surface — it would blow up the restraint premise and make the sidebar the loudest thing on screen.

**Fix.** Keep the pill as ambience, add a compliant indicator:
- A **3px `{colors.foreground}` bar** on the leading edge of the active item (17.72:1 light / 19.06:1 dark). This is a shape cue, not a hue cue, so it stays inside the discipline — and it is what the "no accent bar, no color" line in DESIGN.md currently forbids, so that line needs amending to "no *coloured* accent bar."
- Or invert the active item entirely (`{colors.foreground}` fill, `{colors.background}` text, 17.72:1) — this is already the system's established "active" idiom for filter chips, so it would make nav consistent with the filter row rather than inventing a second mechanism.
- Regardless: emit `aria-current="page"` on the active nav item (1.3.1 / 4.1.2). Not currently specified anywhere.

---

**H-2 · Border token at 1.27:1 / 1.34:1 is used as a component boundary, including on form inputs**
**SC:** 1.4.11 Non-text Contrast (AA)
**Location:** `DESIGN.md` frontmatter `border: '#E4E4E7'` / `border-dark: '#27272A'`; `components.tag-chip.border`, `components.filter-chip.border`, `components.triage-row.separator`; shadcn `Input` / `Checkbox` inherited unchanged

`#E4E4E7` on `#FFFFFF` = **1.27:1**. `#27272A` on `#09090B` = **1.34:1**. On surface: **1.15:1** and **1.19:1**.

1.4.11 exempts *decorative* boundaries, so the triage-row separator is fine (the rows are identifiable by their content). It does **not** exempt boundaries that are the only thing identifying an interactive component. That covers:
- **Text inputs** — search field, tag typeahead, Settings fields. A shadcn `Input` at rest is a rectangle whose only affordance is its 1px border. At 1.27:1 the field is not perceivable as a field. This is the classic shadcn default failure and it is inherited here verbatim.
- **Unchecked checkboxes** — in list triage the checkbox at rest is border-only. The user must find an unchecked box to start a selection.
- **Filter chips / tag chips at rest** — the pill outline is the affordance.

**Fix.** Introduce an `--input-border` / `--control-border` token distinct from the decorative `--border`, set to `#71717A` in light (**4.83:1**) and `#A1A1AA` in dark (**7.76:1**), applied to inputs, checkboxes, switches, and interactive chips. Leave `#E4E4E7` / `#27272A` for decorative separators only. This is a two-token addition and does not touch the palette's hue discipline.

Also correct the false claim in `EXPERIENCE.md` § Accessibility Floor: *"shadcn `neutral` ships WCAG AA-compliant defaults; no brand override exists to compromise them."* Three inherited defaults fail as computed: border (1.27), muted-foreground-on-surface (4.40), destructive-foreground-on-destructive in dark (3.61). The absence of a brand override is not the same as compliance.

---

**H-3 · Tag chip text fails 4.5:1 — and it is set at 10.5px**
**SC:** 1.4.3 Contrast (Minimum) (AA)
**Location:** `DESIGN.md` frontmatter `components.tag-chip` (`foreground: {colors.muted-foreground}`, `background: {colors.surface}`, `typography: {typography.micro}`)

`#71717A` on `#F4F4F5` = **4.40:1** against a 4.5 requirement. 10.5px is nowhere near WCAG's large-text threshold (18.66px bold / 24px regular), so no relaxation applies. Dark mode passes comfortably (6.91:1) — this is a light-mode-only failure, which makes it exactly the kind of thing a single-mode review would miss.

Compounding: the tag row is described in DESIGN.md as *"the visible evidence of Alexis's own work"* and *"must never be crowded out."* It is the most semantically important custom element in the card and it is rendered in the least legible text in the system.

**Fix.** `#52525B` (zinc-600) on surface = **7.03:1**, or drop the chip fill to `{colors.background}` which lifts `#71717A` to 4.83:1 (still thin — prefer zinc-600). Separately, raise `{typography.micro}` from 10.5px to 12px for tag chips; 10.5px is below every practical low-vision floor and the space saving is ~3px per chip.

---

**H-4 · Selection checkbox contrast collapses over thumbnail imagery**
**SC:** 1.4.11 Non-text Contrast (AA)
**Location:** `DESIGN.md` frontmatter `components.selection-checkbox` (`background: {colors.selection-check-bg}` = foreground; `position: 'thumbnail top-left'`)

The checkbox is a solid foreground-coloured square sitting directly on user-uncontrolled thumbnail imagery. Light mode: `#18181B` over a dark region = **1.19:1**. Dark mode: `#FAFAFA` over a bright region = **1.04:1**. The checkbox does not merely lose contrast, it disappears.

DESIGN.md justifies the redundant pair as *"the outline reads at a glance across a grid, the checkbox reads unambiguously up close."* The outline survives (it sits on the page background, 17.72:1) — but the up-close half is the one that fails, and it is the half that distinguishes *selected* from *merely focused*. The unchecked state is worse still: it is border-only at `#E4E4E7`, i.e. essentially never visible on a thumbnail.

**Fix.** Give the checkbox its own ground:
- A 2px `{colors.background}` ring (light) / `{colors.foreground}`-inverse ring (dark) around the checkbox, so there is always a 17.7:1 edge regardless of what is beneath.
- Or seat the checkbox on an opaque `rgba(0,0,0,.82)` plate — reusing the duration-badge treatment that already measures 13.58–21.00:1, and gaining visual consistency across the two thumbnail overlays.
- The unchecked box needs the same plate plus the `--control-border` from H-2.

---

**H-5 · Target size: 17px checkbox and ~18px tag chips are below the 24×24 minimum**
**SC:** 2.5.8 Target Size (Minimum) (**AA**, new in 2.2)
**Location:** `DESIGN.md` frontmatter `components.selection-checkbox.size: 17px`; `components.tag-chip` at `{typography.micro}`; `components.triage-row`; `EXPERIENCE.md` § Interaction Primitives

- **Selection checkbox, 17×17.** Required 24×24. At 289px² vs 576px² it delivers **50% of the required area**. The spacing exception does not rescue it: the exception requires that a 24px-diameter circle centred on the target not intersect any other target, and the checkbox is positioned *on top of* the thumbnail, which is itself a target (click opens Watch). The circle intersects by construction.
- **Tag chips.** 10.5px type at 1.3 line-height = 13.65px of text; with typical shadcn badge padding (`py-0.5`) the chip lands at roughly **18px tall**. Chips are interactive ("Click a tag chip filters the current view by that tag"). The inline exception applies only to targets inside a sentence or block of text; a chip row is not running text.
- **Filter chip row.** Height is never specified. Must be stated.
- **The `⋮` card menu.** Size never specified; on touch it is always visible, so it is a real target.
- **32px desktop list rows.** The row *itself* passes (≥24 in the constrained dimension). The 17px checkbox inside it does not.
- **Duration badge.** Non-interactive → 2.5.8 does not apply. Correctly out of scope.
- **44px touch floor.** Explicitly stated and exceeds AA. Good — see the closing section.

**Fix.** Set an explicit 24px minimum hit area on every interactive element at every breakpoint (not just touch): checkbox 17px visual box inside a 24px pressable padding box; tag/filter chips `min-height: 24px` desktop / 44px touch; `⋮` at 24/44. Add a line to `EXPERIENCE.md` § Accessibility Floor stating the 24px floor as a desktop requirement, because the current text ties the target-size rule to touch only and 2.5.8 is input-agnostic.

---

**H-6 · Sticky bulk action bar and mobile tab bar will obscure the focused element during `j`/`k` navigation**
**SC:** 2.4.11 Focus Not Obscured (Minimum) (**AA**, new in 2.2)
**Location:** `DESIGN.md` `components.bulk-action-bar.position: 'sticky bottom, above bottom-bar on mobile'`, `spacing.bottom-bar-height: 56px`; `EXPERIENCE.md` § Interaction Primitives, § Responsive & Platform

2.4.11 requires that when an element receives keyboard focus, it is **not entirely hidden** by author-created content. The core loop is: hold `j` to walk down a hundred rows while a sticky bulk bar sits at the bottom of the viewport, with a 56px tab bar beneath it on mobile plus safe-area inset. Default `scrollIntoView` behaviour parks the newly-focused row flush with the viewport bottom — i.e. underneath both bars. Combined stacked height on mobile is comfortably 110px+, which is three or four 32px rows.

The failure is not theoretical; it is guaranteed by the default browser behaviour unless explicitly countered.

**Fix.** Set `scroll-padding-block-end` on the scroll container equal to the live height of (bulk bar + tab bar + safe-area inset), updated when the bulk bar mounts/unmounts, and use `scrollIntoView({ block: 'nearest' })` for `j`/`k`. Note that the *stricter* AAA criterion (2.4.12, no partial obscuring) would additionally require the row to be fully clear — worth doing anyway, since a half-hidden row is unreadable regardless of which SC it trips. Also verify the horizontally-scrolling filter chip row: focusing an off-screen chip must scroll it into view horizontally.

---

**H-7 · Destructive button label fails in dark mode**
**SC:** 1.4.3 Contrast (Minimum) (AA)
**Location:** `DESIGN.md` frontmatter `destructive-dark: '#EF4444'`, inherited shadcn `destructive-foreground`

shadcn's `destructive-foreground` is a near-white (`#FAFAFA`). On `#EF4444` that is **3.61:1** — a clear fail for the button label on the delete confirmation, which is the single highest-consequence control in the product. Light mode scrapes by at **4.63:1** with no margin (any hover-darken or 90%-opacity treatment breaks it).

Related, same token used as text: `#DC2626` **error text** on `{colors.surface}` = **4.39:1**, a fail — and dialogs, banners and form panels are exactly where error text appears. On plain background it is 4.83:1, i.e. also thin.

**Fix.** Split the token by role.
- Destructive **button**: dark mode foreground → `#09090B` on `#EF4444` = **5.29:1**. Light stays `#FFFFFF` on `#DC2626` = 4.83:1 and must not be softened to `#FAFAFA`.
- Destructive **text** (error messages, "Delete 14 videos?" emphasis): light → `#B91C1C` (**6.47:1** on bg, **5.89:1** on surface); dark → `#EF4444` is adequate (5.29 / 4.71) but `#F87171` gives **6.40:1** on surface with more headroom.

---

**H-8 · Hover-revealed `⋮` menu has no specified keyboard path**
**SC:** 2.1.1 Keyboard (A), 1.4.13 Content on Hover or Focus (AA)
**Location:** `EXPERIENCE.md` § Component Patterns → *Video card* ("Hover reveals a `⋮` menu (tag, freshness, add to playlist, delete). ... On touch, `⋮` is always visible — hover-only affordances are banned.")

The spine bans hover-only affordances and then names exactly one — and resolves it for touch but not for keyboard. Touch gets a permanent `⋮`; hover gets a revealed `⋮`; **keyboard focus gets nothing specified.** The shortcut map covers tag (`t`), freshness (`f`) and discard (`Backspace`), but **"add to playlist" has no keyboard route at all** and is therefore unreachable without a pointer. 1.4.13 additionally requires hover-revealed content to be dismissible, hoverable and persistent.

**Fix.** State explicitly that `⋮` becomes visible on `:focus-within` as well as `:hover`, that it is in the tab/roving-focus order of the card, and that the revealed menu stays open while the pointer travels to it. Add a shortcut or menu route for "add to playlist" (`p` is currently free, though see C-3 before adding another bare letter — prefer opening the `⋮` menu via the context-menu key or `Shift+F10`, which Radix `DropdownMenu` supports for free).

---

**H-9 · No keyboard equivalent for range selection**
**SC:** 2.1.1 Keyboard (A)
**Location:** `EXPERIENCE.md` § Interaction Primitives (`Shift`+click → Select range); § Triage Modes, List mode step 2

Range selection is specified only as `Shift`+click. In a hundred-item sweep, range select is the difference between one gesture and forty. A keyboard-only user has `x` per item and `a` for all-loaded, with nothing between. This is a genuine functional gap, not a formality — the "≤2 interactions per video" bound in PRD §8 quietly does not hold for keyboard-only users.

**Fix.** Add `Shift`+`j` / `Shift`+`k` to extend the selection from the anchor (both are non-printable-modified, so they are outside 2.1.4's scope and safe to add). Document the anchor semantics: `x` sets the anchor, `Shift`+`j`/`k` extends, `Esc` clears.

---

### MEDIUM

---

**M-1 · Filter chip active state has no programmatic equivalent**
**SC:** 4.1.2 Name, Role, Value (A), 1.3.1 (A)
**Location:** `EXPERIENCE.md` § Component Patterns → *Filter chip row* ("Active chips invert"); `DESIGN.md` `components.filter-chip.active-background`

Visually the inversion is excellent — 17.72:1 luminance delta, fully greyscale-safe, so 1.4.1 is satisfied. But nothing in either spine says the chip carries `aria-pressed` (toggle-button semantics) or `role="checkbox"` + `aria-checked`. Without it a screen-reader user hears "guitar, button" whether the filter is on or off, and the AND-combination described in FR-13 is invisible to them. Same gap applies to the **view toggle** (grid ⇄ list, `aria-pressed`) and to **Focus mode's pinned tag** ("Filing as: `guitar`").

**Fix.** Specify `aria-pressed` on filter chips and the view toggle; expose the filter set as a labelled `group`. State the "Clear all" chip's accessible name explicitly ("Clear all filters", not "Clear all").

---

**M-2 · `aria-live` selection count: conditional mounting and announcement flooding**
**SC:** 4.1.3 Status Messages (AA)
**Location:** `EXPERIENCE.md` § Accessibility Floor ("Selection count announces via `aria-live`"); § Component Patterns → *Bulk action bar* ("Appears whenever ≥1 item is selected")

Two implementation traps that the spine must pre-empt, because the intent is right but the mechanics defeat it:

1. The live region is described as living **inside the bulk action bar**, and the bar only exists when a selection exists. A live region inserted into the DOM at the same moment its content changes is generally **not announced** — assistive tech must observe the region before the mutation. So the first item selected (the most important announcement) is the one most likely to be silent.
2. During a sweep the count changes on every `x`. A `polite` region queues every intermediate value, so the announcements lag several seconds behind the user and read "one selected, two selected, three selected…" through an eleven-tap Focus-mode sweep (UJ-2 step 4). This is worse than useless.

**Fix.** Render an always-present, visually-hidden `aria-live="polite" aria-atomic="true"` region at the app root, independent of the bar's visibility. Debounce updates to ~500ms of idle and announce the settled value only. Because "selection survives filtering," the announcement must tell the whole truth: *"12 videos selected, 4 not shown in the current filter."*

---

**M-3 · Self-clearing Uncategorized destroys focus and announces nothing**
**SC:** 4.1.3 Status Messages (AA), 2.4.3 Focus Order (A), 3.2.2 On Input (A)
**Location:** `EXPERIENCE.md` § Triage Modes → "Self-clearing"; § Information Architecture ("Uncategorized self-clears the moment a video gets its first tag"); UJ-2 step 5

"One action files all eleven; they vanish from Uncategorized." For a sighted user this is the satisfying moment. For a keyboard or screen-reader user, eleven rows are removed from the DOM — including, very likely, the focused one — and focus resets to `<body>`, dumping the user at the top of the document mid-sweep. Nothing announces what happened.

**Fix.** After an apply: (a) move focus deterministically to the nearest surviving row (next sibling, else previous, else the surface heading) before removal; (b) announce via the status region — *"11 videos tagged guitar. 83 remaining."* The Voice and Tone table already supplies the register for this; it just needs to reach AT.

---

**M-4 · Optimistic tag application: the revert is a silent data change**
**SC:** 4.1.3 Status Messages (AA), 3.3.1 Error Identification (A)
**Location:** `EXPERIENCE.md` § Triage Modes → "Optimistic application" ("Failure surfaces a toast and reverts only the affected rows — never the whole sweep")

The user is told the tag applied, the row leaves the list, and then some seconds later the state silently rolls back and the row reappears somewhere the user is no longer looking. The toast is the only signal. Two requirements follow: the toast must be a real status message (shadcn `Toast` gives `role="status"` — confirm the variant used does), and it must **name what reverted**, not just report failure. "3 videos couldn't be tagged `guitar`. They're back in Uncategorized. Retrying next sync." matches the Voice and Tone hard rule that errors always say what happens next.

**Fix.** Specify the revert announcement text and confirm the toast is polite-live and not focus-stealing. Reverted rows should carry a transient non-colour marker so the user can find them; do not rely on the toast alone.

---

**M-5 · Two adjacent links per card, one of them unnamed**
**SC:** 2.4.4 Link Purpose (A), 4.1.2 Name, Role, Value (A), 2.4.9 (AAA, advisory)
**Location:** `EXPERIENCE.md` § Accessibility Floor ("Video thumbnails are decorative when the title is adjacent (`alt=""`); the title is the accessible name"); § Component Patterns → *Video card*

The `alt=""` decision is correct and I want to be clear about that — it avoids the classic duplicate-announcement problem. But it only works if the thumbnail and the title are **the same link**. The spine says "Click the thumbnail opens Watch" and describes the title as a separate element; if they are built as two anchors, the thumbnail anchor has no accessible name at all (`alt=""` inside a link → unnamed link), which is a 4.1.2 failure and produces "link, blank" in a screen reader on every one of a hundred cards.

**Fix.** Specify the card as a single anchor wrapping thumbnail + title (accessible name = title), with the tag chips and `⋮` as sibling controls *outside* that anchor — nested interactives are invalid. Note that this makes the card a composite: the chips/menu must not be inside the link.

---

**M-6 · Embedded player: iframe naming, captions policy, and shortcut collision unspecified**
**SC:** 4.1.2 (A), 2.4.1 Bypass Blocks (A), 1.2.2 Captions (A), 1.4.2 Audio Control (A)
**Location:** `EXPERIENCE.md` § Information Architecture → Watch; § Accessibility Floor ("The embedded player exposes native controls; playback is never mouse-only"); § Responsive & Platform

"Exposes native controls" is the right call — the YouTube IFrame player is keyboard-operable and ships its own captions UI, and refusing to build a custom skin over it is an accessibility win. But four things need stating so they are not lost in build:
- The `<iframe>` needs a `title` attribute (e.g. "Video player: {video title}"). Untitled iframes are a 4.1.2/2.4.1 failure and are one of the most common real-world audit findings.
- Do **not** pass `controls=0` or `disablekb=1`; both remove keyboard operability.
- Pass `cc_load_policy=1` so captions default on where the uploader supplied them. The app cannot supply captions for third-party content — 1.2.2 responsibility sits with the uploader — but it must not suppress them.
- No keyboard trap (2.1.2): `Tab` exits a YouTube iframe cleanly, so this is fine, but the app's single-key shortcuts must be suppressed while the iframe holds focus (see C-3), because `j`/`k`/`f` are YouTube's own seek/play/fullscreen keys.

*Adjacent product note, offered once:* `rel=0` no longer suppresses related videos in the IFrame API — it only restricts them to the same channel, and the end screen still renders. The "no recommendations, ever" promise leaks at the end of every video. Worth knowing before UJ-3 step 6 is built.

---

**M-7 · `onBlur` validation and error identification**
**SC:** 3.3.1 Error Identification (A), 3.3.2 Labels or Instructions (A), 1.4.1 Use of Color (A)
**Location:** `Docs/FRONTEND-STACK.md` mandate (react-hook-form, `mode: 'onBlur'`, destructive-coloured error text), applied across `EXPERIENCE.md` Settings / tag typeahead / `_Inbox` designation

`mode: 'onBlur'` is, on its own, **fine and arguably preferable** for accessibility — it avoids the anti-pattern of firing errors while the user is still typing, which floods AT with transient messages. Two conditions make it compliant, and neither is stated:
1. Submission must still validate everything. RHF's `handleSubmit` does this by default; keep `reValidateMode: 'onChange'` so a corrected field clears its error without requiring another blur — otherwise a user who fixes the field still sees the error and may not know they succeeded.
2. Blur-triggered errors must be programmatically associated: `aria-invalid="true"` plus `aria-describedby` → the message id. shadcn's `Form`/`FormMessage`/`FormControl` wire this correctly, so the fix is simply "use shadcn `Form`, not a bare `Input`" — worth stating, because the spine lists `Input` and `Label` in the unchanged-components list but **does not list `Form`**.

Separately, **error text in destructive colour alone is a 1.4.1 failure** — the spine's own rule that colour must never be the sole signal applies here too. Errors need an icon or a textual "Error:" prefix in addition to the red. And see H-7: `#DC2626` on a surface panel is 4.39:1, below threshold.

Also unspecified: the accessible name of the `t`-invoked tag typeahead and of the watch-page inline `+` tag adder (3.3.2). A combobox launched by a keystroke with no visible label needs `aria-label` and `aria-expanded`/`aria-controls`; Radix `Command`/`Combobox` supplies most of this but the label must be authored.

---

**M-8 · Spine conflict on phone column count, with a Reflow consequence**
**SC:** 1.4.10 Reflow (AA), 1.4.4 Resize Text (AA)
**Location:** `DESIGN.md` § Layout ("Column counts: 4 at `xl`, 3 at `lg`, 2 at `md`, 2 at `sm`, 1 below") vs. the same file's Do's/Don'ts ("Two columns minimum on phones / Don't ship a single-column full-width feed") vs. `EXPERIENCE.md` § Responsive ("`< md`: Grid at 2 columns" and "**Two columns on phones, never one**")

DESIGN.md contradicts itself within two pages, and EXPERIENCE.md sides with the stricter reading. This matters for accessibility because 1.4.10 requires content to be usable at a 320 CSS px viewport without two-dimensional scrolling — which is also what a desktop user gets at 400% zoom. Two columns at 320px yields ~150px cards; `{typography.card-title}` at 13.5px clamped to two lines will hold roughly 30 characters, and the tag chip row plus `+N` will not fit beside the channel name. The likely outcome is horizontal overflow or clipped content, both of which fail 1.4.10.

**Fix.** Resolve the conflict in DESIGN.md's favour: **the "1 column below `sm`" branch is the accessible one and should survive.** The anti-doomscroll rationale ("a single-column feed *is* the doomscroll shape") is about the *default phone experience*, not about the 320px zoom edge case — and the anti-doomscroll property is actually carried by the absence of infinite scroll and recommendations, not by column count. Recommend: 2 columns as the phone default, single column permitted below 360px and under high zoom, stated explicitly so no one "fixes" it back.

---

**M-9 · Text Spacing overrides will clip the clamped titles**
**SC:** 1.4.12 Text Spacing (AA)
**Location:** `DESIGN.md` § Typography rule 2 ("Video titles clamp, never truncate mid-layout. Two lines in grid view, one line with ellipsis in list view"); `{typography.card-title}` line-height 1.32; `{typography.row-title}` line-height 1.35; `spacing.row-padding-y: 6px`

1.4.12 requires no loss of content when the user forces line-height to 1.5× font size, plus paragraph/letter/word spacing bumps. Both title roles ship at ~1.32–1.35 line-height, so a user stylesheet raising them to 1.5 grows each line by ~13%. If the 2-line clamp is implemented as a fixed `height` (a common way to keep grid rows aligned), the second line clips. The 32px triage row with 6px padding has essentially zero vertical slack.

**Fix.** Implement clamping with `-webkit-line-clamp` / `line-clamp` and `min-height`, never fixed `height`. Verify at 1.5 line-height + 0.12em letter-spacing + 0.16em word-spacing, in both grid and list, as part of the FRONTEND-STACK §8 pre-PR visual gate — which currently gates on light/dark only.

---

**M-10 · No bypass mechanism, landmark structure, or page-title spec**
**SC:** 2.4.1 Bypass Blocks (A), 1.3.1 (A), 2.4.2 Page Titled (A), 2.4.6 Headings and Labels (AA)
**Location:** Absent from both spines

Seven sidebar destinations (plus expandable playlists in Phase 2) repeat on every surface. Neither spine mentions a skip link, landmark regions, an `h1` per surface, or document titles. These are the cheapest wins in the entire audit and their absence is the kind of thing that only gets caught after the sidebar is built.

**Fix.** Specify: a visually-hidden "Skip to content" link as the first focusable element; `<nav>` / `<main>` / `<aside>` landmarks with `aria-label` on each nav; one `h1` per surface matching `{typography.page-title}` (the roles already exist — they just need semantic mapping); `document.title` = "{Surface} — YouTube Organizer", updated on App Router navigation.

---

**M-11 · Banners and toasts need status-message semantics**
**SC:** 4.1.3 Status Messages (AA)
**Location:** `EXPERIENCE.md` § State Patterns (import running, import complete, partial failure, pending-clear orphans, quota exhausted, offline, deletion complete, `_Inbox` missing, read-only scope)

Nine distinct states appear as inline banners or toasts, all of them conveying information the user must have and none of them receiving focus. That is precisely the 4.1.3 case. Currently only the selection count is specified as live.

**Fix.** Inline banners → `role="status"` (or `role="alert"` for the read-only-scope and `_Inbox`-missing notices, which are blocking-ish). Import progress must **not** be a live region that fires on every increment — announce start and completion only, or the user is spammed through a 100-video import. "You're offline" is already correctly specified as fire-once.

---

**M-12 · Playlist reorder needs a non-dragging path**
**SC:** 2.5.7 Dragging Movements (**AA**, new in 2.2)
**Location:** `EXPERIENCE.md` § Information Architecture → Playlist detail ("Ordered contents; add, remove, reorder"), Phase 2

Reorder is unspecified in mechanism, and the obvious implementation is drag-and-drop. 2.5.7 requires a single-pointer alternative that does not involve dragging. Flagging now because it is far cheaper to specify than to retrofit.

**Fix.** Provide "Move up" / "Move down" controls (or a "Move to position…" input) alongside any drag affordance. Note this also gives keyboard users a route for free.

---

### LOW

---

**L-1 · No reduced-motion policy stated**
**SC:** 2.3.3 Animation from Interactions (AAA — advisory only), best practice
**Location:** Absent from both spines

Neither spine specifies motion at all, which is consistent with the restraint premise, but the bulk action bar "appears," toasts slide, dialogs scale, and the sidebar collapses at `md`. None of that is AA-blocking. Recommend one line stating that all transitions respect `prefers-reduced-motion: reduce` — Tailwind's `motion-safe:`/`motion-reduce:` variants make it near-free, and the design's low motion budget means the compliance cost is close to zero. Worth banking.

---

**L-2 · `Backspace` as the discard key**
**SC:** 3.3.4 Error Prevention (AA) — currently *satisfied*, noted as a risk
**Location:** `EXPERIENCE.md` § Interaction Primitives

`Backspace` is not a printable character, so it is outside 2.1.4 — no violation. But it is a high-frequency key for anyone using speech input or an on-screen keyboard, and it is bound to "discard a selection of up to 100 videos." The mandatory confirmation dialog and the 30-day Trash mean 3.3.4 is satisfied twice over, so this is genuinely low. Consider still: make `Del` the primary binding and `Backspace` secondary, and ensure the confirmation dialog's initial focus is on **Cancel**, not Delete — currently unspecified and a meaningful safety difference.

---

**L-3 · Micro type at 10.5px is below practical low-vision floors**
**SC:** No AA failure (1.4.4 is satisfied by browser zoom); usability finding
**Location:** `DESIGN.md` § Typography, `{typography.micro}`

10.5px passes WCAG as long as it scales to 200%, but it sits below every practical minimum (12px is the common floor; iOS/Material both bottom out at 11–12sp). It is used for the tag chips — which DESIGN.md itself calls the most meaningful custom content on the card. Combined with H-3's contrast failure, the tag row is currently the least accessible element in the system while being the most product-important. Raising micro to 12px fixes half of this for free.

---

**L-4 · `Esc` semantics are overloaded**
**SC:** 2.1.2 No Keyboard Trap (A) — satisfied; consistency note
**Location:** `EXPERIENCE.md` § Interaction Primitives ("`Esc` — Clear selection, close dialog, exit search"); § Accessibility Floor ("`Esc` always closes the topmost layer")

No trap exists and the layering rule is correct. One ambiguity to settle: with a live selection *and* an open dialog, one `Esc` must close the dialog only. With a live selection inside Focus mode, does `Esc` clear the selection or exit Focus mode? Specify the stack order explicitly (dialog → typeahead → search → selection → mode) so the behaviour is predictable, which is what 3.2.x consistency is really about.

---

**L-5 · Long-press as the sole touch entry into selection mode**
**SC:** No AA failure (2.5.1 covers path-based and multipoint gestures only)
**Location:** `EXPERIENCE.md` § Interaction Primitives ("long-press enters selection mode")

Long-press is neither multipoint nor path-based, so 2.5.1 does not apply and there is no violation. But users with tremor or limited dexterity may struggle to hold a press steadily, and there is no alternative entry point on touch (desktop has `x` and the checkbox). A persistent "Select" affordance in the surface header would cost one button and remove the dependency entirely. Cheap; recommended, not required.

---

**L-6 · Skeletons need a loading announcement**
**SC:** 4.1.3 Status Messages (AA) — borderline
**Location:** `EXPERIENCE.md` § State Patterns → Cold load ("shadcn `Skeleton` ... Never a spinner")

"Never a spinner" is a good visual call. But skeletons convey nothing to a screen reader — the user hears an empty page. Add `aria-busy="true"` on the container plus a polite "Loading library" / "87 videos loaded" pair. Low because the content arrives quickly and the region is not interactive in between.

---

## What This Design Gets Right

Stated plainly, because several of these are better than what a conventional accented design would have produced — and one of them is the reason the whole achromatic gamble is defensible.

- **The achromatic selection outline is the single best contrast decision in the document.** `#18181B` on `#FFFFFF` = **17.72:1**; `#FAFAFA` on `#09090B` = **19.06:1**. Against a 3:1 requirement, that is roughly six times the floor. Almost any brand accent — a blue at 4.5:1, a YouTube red at 4.83:1 — would have been *worse*. The 2px offset is also load-bearing and correctly specified: it guarantees the ring sits against the page background rather than against arbitrary thumbnail pixels, which is exactly why the outline survives where the checkbox (H-4) does not. This was reasoned well.
- **Selection is redundantly encoded and 1.4.1 falls out for free.** Outline plus filled checkbox, both achromatic, both always present. `EXPERIENCE.md` is right that this satisfies an accessibility requirement independently of the aesthetic choice that produced it — and right to state it explicitly rather than leaving it as a happy accident.
- **The duration badge is the model the rest of the status layer should copy.** `rgba(0,0,0,.82)` + `#FFFFFF` measures **13.58:1** over the worst-case white thumbnail and **21.00:1** over black — i.e. it is legible over *any* image, which is the entire problem the scrims fail to solve. The solution to C-1 and H-4 is already in the document; it just needs to be applied twice more.
- **The inverted bulk action bar** at 17.72:1 / 19.06:1 in both directions, chosen over a heavy shadow. Shadow-based elevation is invisible to low-vision users; a full luminance inversion is not. Good instinct, correct outcome.
- **Reserving red exclusively for destruction is a genuine accessibility argument, not just a brand one.** In an otherwise achromatic field, the one chromatic token becomes maximally salient — and, crucially, red is never load-bearing for *identifying* anything, only for emphasising it, so red/green colour-blind users lose nothing. The reasoning in § Colors ("the moment red is spent on branding, it stops working as a warning") is correct.
- **Banning hover-only affordances** as an explicit, named rule. Most design systems discover this in an audit; this one states it up front. (H-8 is a gap in applying it to keyboard, not a failure of the principle.)
- **Banning infinite scroll** in favour of pagination or explicit load-more. This is an accessibility win well beyond its anti-doomscroll motivation: infinite scroll breaks screen-reader position, makes "end of list" unreachable, and defeats keyboard paging. Getting it for free from a product principle is fortunate.
- **Banning autoplay-next**, which satisfies 1.4.2 Audio Control by construction — there is never auto-starting audio to pause.
- **Never-suppressible destructive confirmation plus a Trash retention window.** 3.3.4 Error Prevention requires reversibility *or* confirmation *or* review for data deletion; this design provides two of the three and explicitly refuses the "optimize away the dialog" pressure. The memlog records it as a chosen cost — that decision is well-made and should not be revisited.
- **Modal stacks capped at one level** — directly supports predictable `Esc` handling and focus return.
- **Tabular numerals mandated on every duration, count and date.** Framed as an anti-jitter decision, but it is also a low-vision scanning aid: fixed-width figures are materially easier to compare in a vertical column.
- **44px touch targets stated as a floor**, exceeding the 24px AA requirement. The only correction needed (H-5) is that the floor must extend to pointer/desktop too, not that the number is wrong.
- **`alt=""` on thumbnails with the title as accessible name.** The correct decision, avoiding the duplicate-link-text problem that plagues most card grids. M-5 is about the markup structure required to make it work, not about the decision itself.
- **Dark mode treated as first-class and gated pre-PR.** Two of the failures in this report (H-3 tag chips, light-only; H-7 destructive button, dark-only) are mode-specific — which is exactly the argument for the dual-mode gate the project already has. Extend that gate to include a contrast check and it would have caught both.
- **The Voice and Tone register is quietly an accessibility asset.** "83 of 87 imported. 4 failed and stayed in `_Inbox`." is a better screen-reader announcement than any friendly alternative, and the hard rule that errors always state what happens next maps directly onto 3.3.3 Error Suggestion.
