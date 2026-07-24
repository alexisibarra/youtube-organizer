# Validation Report — youtube-organizer

- **DESIGN.md:** `_bmad-output/planning-artifacts/ux-designs/ux-youtube-organizer-2026-07-23/DESIGN.md`
- **EXPERIENCE.md:** `_bmad-output/planning-artifacts/ux-designs/ux-youtube-organizer-2026-07-23/EXPERIENCE.md`
- **Run at:** 2026-07-23
- **Lenses:** rubric walker · accessibility (WCAG 2.2 AA) · adversarial
- **Total findings:** 111 — **9 critical** · 35 high · 41 medium · 23 low

## Overall verdict

Shape is sound; substance has holes. The spine pair passes structurally — all eight DESIGN.md sections in canonical order, all required EXPERIENCE.md sections plus two justified invented ones, all 46 token references resolving, all source paths verified, UJ names verbatim. What blocks it from being a usable contract is a narrow, deep band of defects: **the core triage loop does not close**, several load-bearing decisions were never actually made and got papered over with confident prose, and three accessibility decisions break the achromatic thesis they were meant to serve.

The adversarial lens named the real hazard precisely: *the prose quality is itself a risk*. Well-written sentences are sitting on top of decisions nobody made — most damagingly around when an import runs, how a video receives its second tag, and what the YouTube embed actually renders when a video ends.

The accessibility lens delivered a genuine vindication alongside its criticism: the achromatic selection outline computes to **17.72:1 (light) / 19.06:1 (dark)** — measurably better than any accent hue would have achieved. The no-accent-color decision is an accessibility *asset*. Three specific applications of it are not, and all three have fixes that stay inside the discipline.

## Category verdicts

| Category | Verdict |
|---|---|
| Flow coverage | adequate |
| Token completeness | thin |
| Component coverage | thin |
| State coverage | thin |
| Visual reference coverage | broken |
| Bloat & overspecification | adequate |
| Inheritance discipline | adequate |
| Shape fit | strong |
| Accessibility (AA readiness) | **not ready** |
| Core-loop viability (adversarial) | **does not close** |

## Findings by severity

### Critical (9)

**[Adversarial] Focus mode structurally caps at one tag per video** — `EXPERIENCE.md § Triage Modes`
Focus mode operates over Uncategorized, and Uncategorized self-clears the moment a video receives its first tag. A video needing `guitar` *and* `course` leaves the surface after the first sweep and can never be swept again — the second tag costs ≥6 interactions against a ≤2 bound. The PRD's own tag model (tags carry topic *and* format) makes multi-tag the **normal** case, not the exception. Focus mode was the named mitigation for SM-C2, the only counter-metric that can kill the product.
*Fix:* give a triage session a frozen working set that persists until the session ends, and/or allow selecting multiple tags before applying. Requires a product decision.

**[Adversarial] UJ-2's climax is arithmetically false** — `EXPERIENCE.md § Key Flows, UJ-2`
Four sweeps at "eleven taps" plus six discards files ~50 of 94 videos, after which the flow reads "Nothing to file." Honest cost is ~310 title-reads, ~39 sweep actions, 15–25 minutes — which is SM-C2's explicit failure condition, stated in the flow that exists to prove SM-C2 is met.
*Fix:* rewrite the flow with true arithmetic, or change the design until the arithmetic is true. Do not adjust the prose alone.

**[Adversarial] No import trigger was ever decided** — absent from `EXPERIENCE.md § Information Architecture`, Interaction Primitives, Settings, and all 47 memlog entries
Nothing anywhere says when or how an import runs — manual button, on app open, scheduled, or background. UJ-2 and UJ-3 imply contradictory trigger models. FR-5 and FR-6 cannot be turned into stories in this state.
*Fix:* decide the trigger model and add the affordance to the IA.

**[Adversarial] The YouTube embed ships recommendations on its end screen** — violates `EXPERIENCE.md § Subtraction Contract` row 1
`rel=0` has not suppressed related videos since 2018; it now only restricts them to the same channel. At video end the embed renders a recommendation grid — inside the app, at the moment of peak doomscroll vulnerability. This defeats the product's top-line promise and FR-15's testable consequence. Neither spine mentions it.
*Fix:* intercept the end state before the embed renders it, or accept and document the leak. Product decision.

**[Adversarial] Phase 1 has no playlists, no ordering, and no sort** — `EXPERIENCE.md § Information Architecture`
Watching a 9-video course in Phase 1 costs ~30 navigations, with "open in YouTube" available on the same screen as the cheaper alternative. The spine's own mitigation (manual prev/next) is Phase 2.
*Fix:* confirm Phase 1 genuinely stands alone for the month SM-3 requires, or pull minimal ordering forward.

**[Accessibility C-1] Status-by-scrim is invisible on light thumbnails (WCAG 1.4.1)** — `DESIGN.md § Colors`, `§ Components`
Dimming is a lightness change — still color. Watched-light over a mid-tone thumbnail is a 2.31:1 delta; over a white thumbnail, **1.00:1 — literally invisible**. Watched + unavailable stacked resolves to byte-identical `#F7F7F8`. DESIGN.md forbids the badge that EXPERIENCE.md's accessibility floor and the memlog both require — an unresolved contradiction between the spines.
*Fix:* pair every scrim with a non-color indicator (icon or label). Resolve the DESIGN/EXPERIENCE contradiction in favor of the badge.

**[Accessibility C-2] Selection ring and focus ring are indistinguishable (WCAG 2.4.7)** — `DESIGN.md § Components`
Both are foreground-colored offset rings on the thumbnail, differing by 1px. During `j`/`k`/`x` triage across a mostly-selected grid, there is effectively no focus indicator.
*Fix:* differentiate by style, not just width — e.g. dashed focus vs solid selection, or move focus to the card body.

**[Accessibility C-3] Single-key shortcuts violate 2.1.4 (Character Key Shortcuts)** — `EXPERIENCE.md § Interaction Primitives`
`j k x a t f v /` and the `g`-chords are all printable characters with no off-switch, no remap, and no stated focus scoping. EXPERIENCE.md presents this as a virtue. Compounded by NVDA/JAWS browse-mode collisions on `t/f/l/g/k/x/v`, and by `j/k/f` being YouTube's own keys inside the player iframe.
*Fix:* add a remap/disable setting, and scope shortcuts out of text inputs and the player iframe. 2.1.4 requires at least one of: off-switch, remap, or focus-only activation.

**[Rubric] Dark-mode selection checkbox tokens are missing** — `DESIGN.md` frontmatter
`selection-check-bg` / `selection-check-fg` have no `-dark` pairs while `selection-ring` does, so dark-mode checkboxes resolve to light-mode values. Dark mode is a hard pre-PR gate in `Docs/FRONTEND-STACK.md` §8.
*Fix:* add the `-dark` token pair.

### High (35) — the load-bearing subset

**[Accessibility H-1] Active-nav pill is 1.10:1 light / 1.12:1 dark (WCAG 1.4.11)** — the worst number in the system, and unfixable by tuning: the lightest grey clearing 3:1 on white is ~`#949499`. *Fix:* add a shape indicator (foreground edge bar or full inversion) plus `aria-current`.

**[Accessibility H-3] Tag chip text 4.40:1 at 10.5px** — light-mode fail on the card's most product-important element, the one thing the app adds to YouTube's card.

**[Accessibility H-4] Selection checkbox collapses to 1.19:1 over dark thumbnails**, 1.04:1 in dark mode over bright ones — the checkbox has no border or shadow to separate it from arbitrary imagery.

**[Accessibility H-5] Target size (2.5.8)** — 17px checkbox and ~18px tag chips both miss 24×24 with no spacing exception available.

**[Rubric] Two direct cross-spine contradictions** — unavailable dims *thumbnail* (DESIGN) vs *whole card* (EXPERIENCE); watched is *dim only* vs *dim + icon/label* vs *badge* (PRD FR-16). Three answers to one question.

**[Rubric] The under-player column is missing from both spines** — memlog decision 29 (inline tag editing, collapsed description, manual playlist position) was never written in. The no-rail consequence it resolved is, in the document, still open.

**[Rubric] Inline banner / `Alert` is undefined on both sides** despite six State Patterns rows depending on it. `Triage row` and `Sidebar nav item` are visual-only; `View toggle` and `Import status` are behavioral-only.

**[Rubric] Both `.working/` studies are orphans** — zero spine references, and "spines win on conflict" is never stated.

**[Rubric] No generic fetch/server-error state and no auth-expired state** anywhere in State Patterns.

**[Adversarial H-1] Selection ring and focus ring same color on same element** — independently found by two lenses, which raises confidence.

**[Adversarial H-9] FR-13's channel and length-range controls have no specified UI at all.**

**[Adversarial H-6] The confirmation-dialog amortization argument covers one moment per week** and ignores every other prune path — and FR-11 only ever required the dialog for *bulk* delete, not single delete.

**[Accessibility] Border token at 1.27:1** on inputs and checkboxes; **dark destructive button label at 3.61:1**; **focus-obscured-by-sticky-bars (2.4.11)** is a guaranteed-by-default `j`/`k` failure with both the bulk action bar and the mobile tab bar.

### Medium (41) / Low (23)

Held in the individual reviewer reports. Predominantly: token naming consistency, state rows needing behavioral detail, prose that restates source material, and unspecific cross-references.

## What the design gets right

Recorded because it is load-bearing and should not be lost in remediation:

- **The achromatic selection decision is an accessibility asset**, not a liability — 17.72:1 / 19.06:1, better than any accent hue would have delivered.
- Shape fit verdict: **strong**. Canonical ordering, required sections, invented sections earning their place.
- All 46 `{token}` references resolve; all four source paths verified on disk; UJ names verbatim from the PRD.
- The redundant selection treatment (outline *plus* checkbox) satisfies 1.4.1 for selection by construction.
- The accessibility lens returned a 15-item "what this design gets right" section; see its report.

## Reviewer files

- `review-rubric.md` — 45 findings, per-category verdicts, mechanical notes
- `review-accessibility.md` — computed contrast tables both modes, scrim composites, remediation table with pre-computed replacement values
- `review-adversarial.md` — failure scenarios with locations, "what would actually break first"
