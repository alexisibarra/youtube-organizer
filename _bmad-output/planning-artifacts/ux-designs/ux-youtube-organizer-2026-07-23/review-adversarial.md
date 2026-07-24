---
title: "Adversarial Review — UX Spine Pair (DESIGN.md + EXPERIENCE.md)"
reviewer: Cynical Adversarial Review
date: 2026-07-23
targets:
  - DESIGN.md
  - EXPERIENCE.md
  - .memlog.md (41 entries)
source-of-truth: ../../prds/prd-youtube-organizer-2026-07-20/prd.md
---

# Adversarial Review — YouTube Organizer UX Spine

## Overall Verdict

This is a beautifully written spine for a product whose core loop does not close. Focus mode — the named mitigation for the one counter-metric that can kill the product — is structurally incapable of applying more than one tag per video, because Uncategorized self-clears on first tag and Focus mode's working surface *is* Uncategorized; the flagship journey UJ-2 then papers over this with arithmetic that doesn't add up (4 sweeps × "eleven taps" ≈ 44 of 94 videos, yet the climax reads "Nothing to file"). Add that nothing in either spine, or the PRD, or the 41-entry memlog ever decides **when an import runs or how the user triggers one**, and the weekly loop has no ignition, no working engine, and a documented escape hatch to YouTube parked on the page where the friction is worst.

The prose quality is actively dangerous here: confident, well-argued sentences ("Roughly four sweeps clear a hundred-video week") sit on top of decisions that were never made and numbers that were never computed. Downstream architecture and story work will treat them as settled.

---

## CRITICAL

### C-1. Focus mode can apply exactly one tag per video, ever. It is structurally incapable of the PRD's normal case.

**Locations:** `EXPERIENCE.md` L125–134 (Focus mode), L139 (Self-clearing), L100 (tag chips read-only in browse); `PRD` FR-7 ("apply **one or more** Tags"), FR-9 ("A Video can carry multiple Tags"), FR-7 description ("Tags carry topic *and* format, e.g. `podcast`").

Focus mode's surface is Uncategorized. The Self-clearing rule states: *"A video leaves Uncategorized the instant it receives its first tag or playlist membership."* Therefore:

1. Sweep 1 = `guitar`. He taps the Paul Davids fingerstyle lesson. Apply.
2. The video **immediately leaves Uncategorized**.
3. Sweep 2 = `course`. The video is not on the surface. It cannot be tapped.
4. Sweep 3 = `tutorial`. Same.

Focus mode's per-video ceiling is **one tag**. Not a limitation the doc acknowledges — it is never mentioned anywhere.

Now look at what the PRD says the tag model is: tags carry **topic *and* format**. `podcast` + `history`. `guitar` + `course`. `barca` + `highlights`. Multi-tagging is not an edge case in this product; it is the stated design of the taxonomy. The mock in `.working/key-library.html` confirms it — nearly every card carries two tags (`guitar`+`course`, `guitar`+`theory`, `guitar`+`gear`).

**The real moment this breaks:** Sunday, sweep 1, video 3. He taps a video, applies `guitar`, and half a second later realizes it's the third video of a course series he wants under `course` too. The video is gone from the screen. To fix it he must: navigate to Library (1) → filter by `guitar` (1) → scroll to find it among 60 results in an unspecified sort order (n) → open Watch (1) → click `+` in the tag row (1) → type (1) → commit (1). That is **≥6 interactions plus a search**, for a video the PRD budgets at ≤2. He does this once, learns the lesson, and thereafter stops using Focus mode — which was the entire SM-C2 mitigation.

**The workaround the spine assumes but never specifies:** apply multiple tags in a single bulk action from list mode. `EXPERIENCE.md` L178 says only "`t` Tag selection (typeahead)". Whether the typeahead accepts one tag or many before committing, whether it stays open, whether it can create a tag that doesn't exist yet — **none of this is specified anywhere in either document or in the memlog.** The most-invoked control in the product has no behavioral spec.

**Severity: critical.** This invalidates memlog entry 30 ("focus mode amortizes to well under 2 interactions per video"), which was asserted and never tested.

---

### C-2. UJ-2's climax is arithmetically false. The journey files ~47% of the week and declares the inbox empty.

**Locations:** `EXPERIENCE.md` L249 ("94 videos imported"), L252 ("Eleven taps"), L254 ("six videos"), L255 ("ninety-four videos became four sweeps and one discard… Uncategorized reads **'Nothing to file.'**"), L134 ("Roughly four sweeps clear a hundred-video week").

Take the journey's own numbers at face value:

| Step | Count |
|---|---|
| Imported | 94 |
| Sweep 1 `guitar` | 11 (stated) |
| Sweeps 2–4 `barca`/`podcast`/`history` | ~11 each ⇒ ~33 |
| Discarded | 6 |
| **Filed or discarded** | **~50** |
| **Still in Uncategorized** | **~44** |

For "Nothing to file" to be true, the four clusters would need to average **22 videos each**, which contradicts the only cluster size the doc actually gives (11). The journey contradicts itself two steps apart.

This is not pedantry. It is the load-bearing existence proof for the entire product, and it fails on arithmetic. The honest reading of a real ~100-video week from a general-interest YouTube saver is a **long tail**: 4–5 clusters of 6–12, plus 40–60 genuine one-offs (a lock-picking video, a Kurzgesagt, a woodworking jig, an obscure live set). Those one-offs are precisely what Focus mode cannot handle — each needs its own sweep, and a sweep costs a full re-scan of the remaining pile.

**Focus mode's true cost function is O(remaining × distinct tags), not O(videos).** The doc never states this and the memlog (entries 29–30) never computed it.

**Honest interaction count for the claimed happy path**, on a phone, 2-column grid (~8 cards visible per screen):

| Cost | Count |
|---|---|
| Title-reads (94+83+72+61 across 4 sweeps) | **~310 read-and-decide events** |
| Scroll gestures (310 ÷ 8 cards/screen) | **~39 swipes** |
| Selection taps | ~44 |
| Tag pick + Apply per sweep | ~12 |
| Discard (long-press, 6 taps, Discard, confirm) | 9 |
| **Total deliberate actions** | **~104, plus 310 reads** |

At a conservative 1.5s per title-read-and-decide (YouTube titles are long, clickbait-optimized, and deliberately ambiguous), **the reading alone is ~8 minutes**. The stated total is "under ten minutes." With scrolling, taps, tag switching and the discard dialog, **15–25 minutes is the realistic figure — for a week that resolves cleanly into four clusters.** A messy week is 30–40 minutes.

Against SM-C2 ("if triage costs more time than the doomscroll it replaced, the product has failed"), this is at best a wash, and worse than a wash in *felt* cost: doomscrolling is passive entertainment, triage is labor. Twenty minutes of labor does not trade evenly against twenty minutes of scrolling.

**Severity: critical.** Fix the journey's numbers or fix the mode; do not ship both.

---

### C-3. Nothing in the spine, the PRD, or the memlog decides when an import happens or how the user triggers one.

**Locations:** `EXPERIENCE.md` L104 (Import status = "inline banner"), L154–158 (four import states), L249 (UJ-2: "Uncategorized shows an inline banner: 'Importing…'"), L27–42 (IA table), L171–184 (keyboard map), L222 (mobile tab bar), `.memlog.md` (all 41 entries).

Search the IA table for a Sync destination: none. Search the keyboard map for a sync/refresh key: none. Search the sidebar order (L42): Library · Uncategorized · Tags · Playlists · Needs review · Watched · Trash — no Sync. Search Settings' stated contents (L35): "Google connection, `_Inbox` designation, theme, watched threshold" — no sync control, no schedule, no "import now."

So the app imports… when? Three possibilities, all unstated and all with consequences the spine never handles:

- **On app open.** Then the "Importing…" banner races the user's first paint every single session, including the 8-second UJ-3 payoff session (L267), and the import-complete toast fires while he's picking a guitar video. UJ-3 never mentions an import banner — so the spines model two mutually exclusive trigger behaviors in two adjacent journeys.
- **Background cron.** There is no native app (L17) and no notifications (L66) — so a background import produces a toast nobody is present to see, and the Import-complete state (L155, "Toast: '87 videos imported.'") fires into the void.
- **Manual.** There is no affordance for it anywhere in either document.

**The real moment:** it's Sunday. He opens the app. Whether he sees anything to triage depends entirely on a decision no one made. And the failure states — quota-exhausted mid-import (L158), pending-clear orphans (L157), partial failure (L156) — all describe *retry on next sync* without ever defining what "next sync" is or how a user forces one when four videos are stuck in `_Inbox` and he wants them now.

This is the clearest instance of the pattern the review was asked to hunt: a load-bearing decision that was never made, papered over with confident state-table prose.

**Severity: critical.** FR-5/FR-6 are Phase 1 and cannot be storied from this spine.

---

### C-4. The embedded player will show YouTube's recommendations at the end of every video. Neither spine addresses it.

**Locations:** `EXPERIENCE.md` L60 ("Recommended / suggested videos — the doomscroll itself. The single most important absence in the product"), L61, L228–239 (Watch flow), L270 (auto-marks watched at 90%); `PRD` FR-15 testable consequence: *"The embedded player plays the Video **without exposing YouTube's recommendation feed/autoplay-next within the app**."*

The YouTube IFrame embed ships an **end screen**. Since 2018, `rel=0` no longer suppresses related videos — it merely restricts them to the same channel. When a video finishes inside this app, the player area fills with a grid of YouTube-chosen thumbnails, clickable, inside the product whose entire identity is the absence of exactly that.

Neither DESIGN.md nor EXPERIENCE.md mentions end screens, `rel`, `modestbranding`, the IFrame Player API, or any end-of-playback state at all. The State Patterns table (L146–163) has no "video ended" row. `.working/key-watch.html` renders only the playing and unavailable states.

**The real moment:** he finishes a 22-minute guitar lesson. The player fills with six Paul Davids thumbnails. He clicks one. He is now consuming a YouTube-selected sequence inside the app built to prevent exactly that — and it is *more* seductive than YouTube's, because he trusts this app not to do this to him.

This is a hard, testable failure of FR-15 and of the Subtraction Contract's own top row, and it lands at the single moment of maximum doomscroll vulnerability. It requires an intercept — pausing before end via the IFrame API and rendering the app's own end state — which is a real engineering commitment that nobody has budgeted because nobody noticed.

**Severity: critical.**

---

### C-5. Phase 1 has no ordering, no sort, and no playlists — so the 9-video guitar course is ~30 navigations, and "open in YouTube" is on the same page.

**Locations:** `EXPERIENCE.md` L228 / `DESIGN.md` L228 (no rail at any breakpoint), L63 (no autoplay-next), `.memlog.md` 33–34 (playlist position + manual prev/next = **Phase 2**), IA table L36–37 (Playlists = Phase 2); `PRD` §6.2.

Walk it in the Phase 1 product that SM-3's month actually measures:

1. Playlists don't exist. The 9-video course is nine cards sharing a `course` tag.
2. Library → filter `guitar` + `course`. Nine results, **in no specified order**. There is no sort control anywhere in either spine, and no default order is stated. Course part 4 sits wherever it sits.
3. He identifies part 1 by reading titles. Opens it. Watches 18 minutes.
4. Video ends. (See C-4 — YouTube's end screen is what he actually sees.)
5. To reach part 2: leave the watch page (browser back? unspecified — no back affordance is defined and UJ-3 never returns from the watch page), land back on the filtered view (URL state survives, L101 — the one thing that works), re-scan nine titles to find part 2, click it.
6. Repeat ×8.

**~30 navigation interactions and eight full context switches for one course**, versus zero on YouTube (autoplay) or one per video (rail). The under-player "4 of 9 — Guitar Course Vol.1" line with manual prev/next, which is the spine's own mitigation, is Phase 2 (memlog 34). Phase 1 ships **no progression affordance of any kind**.

And directly on that same watch page sits the first-class **"open in YouTube"** action (L272, FR-15). The product places its own defection button adjacent to its worst friction. The anti-doomscroll purity is self-defeating here in the most literal sense: the purest possible reading of "no rail, no autoplay" pushes the user to the platform that has both.

**Severity: critical for SM-1.** A manual "next in this filter" control under the player — reachable only by explicit click, never automatic — costs nothing against the anti-doomscroll NFR (PRD §8 bans autoplay machinery, not user-initiated advance) and is the difference between a usable course experience and a defection.

---

## HIGH

### H-1. Selection ring and focus ring are the same colour on the same element. Keyboard triage cannot show its own state.

**Locations:** `DESIGN.md` L32–33 (`selection-ring: {colors.foreground}`), L134–138 (`selection-outline`: foreground, 3px, 2px offset); `EXPERIENCE.md` L211 ("Focus rings inherit shadcn's `ring` token"), L172 (`j`/`k` move focus), L173 (`x` toggle selection).

shadcn's `ring` token under `baseColor=neutral` resolves to a near-foreground neutral. The selection outline is `{colors.foreground}` at 3px/2px offset. These are **the same hue, on the same element, at similar weight**, and the desktop triage model is `j`/`k` to move focus and `x` to toggle selection — meaning focus and selection are constantly on different items and constantly need to be told apart.

**The real moment:** he holds `j` down the list. He can't tell whether the ringed row is the one he's about to act on or one he already selected. He presses `x` on a row he already selected, silently deselecting it. The bulk bar count ticks *down* by one while he believes it went up.

The memlog shows how this happened: entry 23 correctly flagged the selected-state problem as "load-bearing, needs an explicit decision"; entry 28 declares it "resolved by the theme render Alexis picked" — a mock showing **three selected videos in a static grid**. The decision was made by a proxy artifact that could not exhibit the failure, and focus state was never in the render at all.

**Severity: high.** Selection and focus need different treatments (e.g. offset-outline for selection, inset dashed/2px ring for focus), or the achromatic constraint has to bend for one of them.

---

### H-2. The selection checkbox has no scrim, stroke, or shadow — on a surface the design elsewhere admits is unpredictable.

**Locations:** `DESIGN.md` L128–133 (`selection-checkbox`: bg = foreground, fg = background, radius sm, size 17px, position thumbnail top-left), L122–127 (`duration-badge`: background `rgba(0,0,0,0.82)`).

The duration badge got an explicit 82%-black plate **because it sits on unpredictable imagery**. The checkbox — same surface, same problem, more load-bearing — got nothing: no plate, no 1px stroke, no drop shadow.

In light mode the checkbox is near-black `#18181B` with a white check. YouTube thumbnails put burned-in title cards, black bars, dark vignettes, and faces in the top-left constantly. A 17px black square with a white tick on a black title card is **invisible**. Since selection is redundantly encoded (outline + checkbox, L261), the design's own fallback is the outline — which H-4 shows is the weaker of the two at scan distance. In dark mode the checkbox inverts to near-white on the same unpredictable image, which fails against bright/white thumbnails instead.

**Severity: high.** One line of spec (a `rgba(0,0,0,0.5)` backing plate or a 1.5px `{colors.background}` stroke) closes it, and its absence is a straight inconsistency with the duration badge two entries above it.

---

### H-3. Achromatic selection does not survive a fast scroll over 12 screens of saturated thumbnails, and failure is silent.

**Locations:** `DESIGN.md` L193 ("the outline reads at a glance across a grid"), L261; `EXPERIENCE.md` L125–134 (sweeping), L208 (count announced via `aria-live` — the count is the only stated truth).

Peripheral and para-foveal vision key off **luminance mass and colour**, not thin contours. A 3px contour is a foveal cue: you have to look *at* the card to see it. The claim that "the outline reads at a glance across a grid" is asserted, never tested, and the test artifact that produced the decision showed three selections in a static grid (`.memlog.md` 26, 28) — not twenty selections during a 39-swipe scroll over clickbait thumbnails.

**The real moment:** sweep 1, `guitar`, screen 7 of 12. He taps a video. Two swipes later the layout re-flows slightly on a rotation or a thumbnail load and he scrolls back. Was that one tapped? The ring is thin, the thumbnail is a screaming yellow-and-red face, and he's moving fast. He taps it again — **deselecting it**. There is no feedback of any kind for deselection: no animation spec, no haptic spec, no per-item state readout. The count in the bulk bar is 200px away at the bottom of the screen and he isn't reading it.

Result: that video never gets the `guitar` tag and silently persists in Uncategorized. He notices nothing. This is **silent data loss during the product's core loop**, and the redundancy that was supposed to catch it (the checkbox) is compromised by H-2.

The achromatic constraint is defensible for *branding*; it is being asked to do a job — high-speed group discrimination against hostile imagery — it is not suited for. The standard solution is mass, not contour: desaturate/dim **unselected** cards during an active sweep. That stays fully achromatic, is consistent with the existing scrim vocabulary, and changes luminance mass, which is what the eye actually uses.

**Severity: high.**

---

### H-4. The Phase 1 bulk action bar has four actions and two of them are Phase 2.

**Locations:** `EXPERIENCE.md` L99 ("the actions: Tag · Freshness · Add to playlist · Discard"), L121 (list mode step 4, same four), L96 (card `⋮`: "tag, freshness, add to playlist, delete"), L178 (`f` = Set freshness), L255 (DESIGN.md `Calendar` in the shadcn list); `PRD` §6.1 vs §6.2 (Freshness FR-17/18 = Phase 2; Playlists FR-10 = Phase 2; date filters = Phase 2).

The spine phases the **IA table** (L27–40) meticulously and then phases **nothing else**. Every component spec, every keyboard binding, every triage-mode step, and every journey describes the union of Phase 1 + Phase 2 capability as though it were one product. `.working/key-library.html` at least badges P2 destinations in the sidebar mock — the spine documents don't, which means the mock and the spine disagree about what ships.

**The real moment:** a developer builds the bulk action bar from L99. Half of it can't be wired. Either they ship dead buttons, or they invent a phase split the spine didn't authorize, or Freshness/Playlists get pulled into Phase 1 by accident and Phase 1's scope inflates by two whole feature areas.

**Severity: high.** This is the specific defect that turns a clean spine into scope creep at story-writing time.

---

### H-5. The two spines directly contradict each other on delete-on-card.

**Locations:** `EXPERIENCE.md` L96 — *"Hover reveals a `⋮` menu (tag, freshness, add to playlist, **delete**). No delete affordance on the card face itself."* vs `DESIGN.md` L265 — *"**Destructive actions live here** [the bulk bar], attached to the selection — **never on individual cards**"* and L281 Do/Don't — *"Don't: Put a delete affordance on individual cards."*

EXPERIENCE tries to thread it with "not on the card *face*" — a distinction that does not survive contact: the `⋮` is on the card, it is reachable in one tap, and on touch it is **permanently visible** (L96). So the per-card delete path exists on every card of every surface, which is exactly the path DESIGN.md's amortization argument depends on being rare.

**Severity: high** — because it directly undermines F-1 below.

---

### H-6. The confirmation-dialog amortization argument is false in every real pruning moment.

**Locations:** `.memlog.md` 39–40 (the decision and the override), `EXPERIENCE.md` L142 ("one dialog covers the whole sweep"), L103 ("Never suppressible, never remembered, no 'don't ask again'"), L162 ("no undo affordance in the toast — the dialog already did that job"), L160 (unavailable video on Watch offers delete), L272 (UJ-3 "he closes the app or prunes instead"), L290 (UJ-4: "He deletes two and keeps one").

The mitigation is: *discard is bulk, so one dialog amortizes across the selection.* Now enumerate where deletes actually originate:

| Moment | Batch size | Source |
|---|---|---|
| Weekly triage junk sweep | 5–15 | UJ-2 L254 — **the only bulk case** |
| "Why did I save this" mid-browse | **1** | UJ-3 L272 |
| Unavailable video hit at play time | **1** | L160, FR-19 |
| Needs-review keep/discard triage | 1–2 at a time | UJ-4 L290 ("deletes two and keeps one") |
| Search result cleanup | **1** | implied by FR-13/14 |

**Bulk discard is one moment per week. Single discard is every other moment, forever.** The amortization argument covers the rare case and ignores the common one — and H-5 means the single-video path is one tap away on every card, so it *will* be the default gesture.

**The real cost of a single prune:** open `⋮` (1) → Delete (1) → modal mounts, focus traps, he must read a sentence he has read four hundred times → Confirm (1) → toast. **Three interactions and a full modal interrupt to remove one video that is recoverable from Trash for 30 days anyway.** The guard guards nothing Trash does not already guard.

**The behavioural consequence, which is the real damage:** pruning is the *only* mechanism keeping the library lean in Phase 1 (freshness and date filters are Phase 2 — see H-8). SM-4 and SM-C1 both depend on it. Make the cheapest curation gesture cost three interactions and a modal, and a human being does the rational thing: **he stops pruning in the moment and defers it to "the big cleanup," which never happens.** The library grows monotonically. SM-C1 ("a bigger library is worse") fails by design.

The memlog records this as settled and unreopenable ("it is a chosen cost", memlog 40, `EXPERIENCE.md` L234). It was chosen on a literal reading of FR-11, whose own text says *"**Bulk** delete requires an explicit confirmation showing the count"* — **FR-11 requires the dialog for bulk, not for singles.** The spine over-honored the PRD and invented friction the PRD did not ask for. Re-read the FR: an undo toast on single delete is fully PRD-compliant.

**Severity: high.**

### H-7. There is no undo and no bulk un-tag. A mis-applied sweep is unrecoverable at reasonable cost.

**Locations:** `EXPERIENCE.md` L100 ("Tag chip … **Read-only in browse contexts** — clicking filters"), L140 (optimistic application reverts only on *failure*), L139 (self-clearing), L162 (no undo in toast), keyboard map L171–184 (no undo key).

There is no `Ctrl+Z` anywhere in the product. Tag chips are read-only everywhere except the watch page. So:

**The real moment:** sweep 2, he has 14 videos selected for `barca`, and hits Apply while the pinned tag still reads `guitar` from sweep 1 (a genuinely easy mistake — the tag is pinned in the header, 400px from his thumb, and the selection UI looks identical between sweeps). Fourteen videos are now wrongly tagged `guitar` and **have left Uncategorized**. To fix: Library → filter `guitar` → find the 14 among ~60 → open each on Watch → remove the chip → back. **~70 interactions to undo one mis-tap.** In practice he doesn't fix it; his taxonomy is now permanently polluted, which is precisely the drift FR-9's tag-merge exists to fight — and tag-merge is Phase 2.

Compounding: `EXPERIENCE.md` L141 promises "Selection survives filtering," but never says what happens to a live selection when the pinned Focus tag is **changed without applying**. UJ-2 step 6 ("He switches the tag to `barca`, sweeps again") only covers the post-Apply case. If he changes the tag mid-sweep to correct himself, does the selection clear or carry? Undefined, and both answers cause data loss in different directions.

**Severity: high.**

### H-8. Phase 1 is a hoarding machine. Every lean-keeping mechanism is Phase 2, during the exact month SM-3 measures.

**Locations:** `PRD` §6.1 vs §6.2; `EXPERIENCE.md` IA table L36–40; `PRD` SM-4, SM-C1.

Phase 1 ships: capture ~100/week, tag, browse, watch, delete-one-at-a-time-with-a-modal. Phase 1 does **not** ship: Freshness/perishables (FR-17/18), Needs review, unavailable detection (FR-19), date-range filters, tag merge.

Month 1 trajectory: week 1 = 100 videos, week 4 = ~400. There is **no bulk pruning tool of any kind** — the only bulk-discard opportunity is the junk sweep at import time, i.e. only over videos he *hasn't yet decided about*. There is no way to say "everything I tagged `news` before June" (date filters, Phase 2), no way to find rot (Needs review, Phase 2), no way to find dead links (FR-19, Phase 2).

**The real moment:** week 4, Library shows 400 videos, he has watched maybe 15 of them. The JTBD he actually stated — *"Stop feeling like my saved videos are a guilt-pile"* — is now being violated by the app he built to fix it, with 385 unwatched videos and no sweep tool. SM-C1 explicitly warns about this ("a bigger library is worse, not better, if it's unwatched"), and Phase 1 as scoped has no counter-force.

Meanwhile the spine documents Needs review, Freshness markers, and unavailable states in detail (L38, L97, L160, L287–291), which makes it read as though the health system exists. It doesn't, for the entire evaluation window.

**Severity: high.** Either pull a minimal bulk-prune (a date-imported filter alone would do it) into Phase 1, or accept that SM-3's month is measured on a product that only accumulates.

### H-9. FR-13's core filter controls — channel and length range — have no specified UI. The payoff journey rests on a hardcoded chip.

**Locations:** `EXPERIENCE.md` L101 (Filter chip row: "Horizontally scrollable, pill-shaped… Multiple filters combine with AND"), L265 (UJ-3: "He adds a length filter: **≤ 60 min**"); `DESIGN.md` L145–151, L263; `.working/key-library.html` (chip row renders literal chips: `guitar`, `≤ 60 min`, `barca`, `podcast`, `history`, `Channel`, `Unwatched`, `Clear all`); `PRD` FR-13 ("Length **range**", "Channel", "Date **range**").

The filter chip row is the *only* filtering UI specified in either document, and the spine never says what populates it. The mock reveals the guess: a handful of tags, one hardcoded length preset, and a bare "Channel" chip that presumably opens something undefined.

- **Length.** FR-13 requires a *range* ("under/over N minutes", "≤ 60 min"). A pill is a preset, not a range. Which presets? Who defines them? A user with a 47-minute budget has no control.
- **Channel.** By month 3 he has 200+ distinct channels. A horizontally scrollable pill row is not a channel picker. What the "Channel" chip opens — a popover, a Select, a search — is unspecified. FR-12 makes channel a Phase 1 facet and UJ-3's PRD text names channel filtering explicitly ("FC Barcelona").
- **Tags.** By month 2 he has 40+ tags. A horizontal scroller of 40 pills means horizontally scrolling to reach `woodworking`. The Tags surface exists (L31) but it is described as an index/management surface, not as a filter picker, and no route connects it to a filtered Library view.

**The real moment:** month 2. He wants "Barça, under 30 minutes." He opens Library. The chip row shows his six most-used tags and a "≤ 60 min" chip. `barca` requires horizontal scrolling; 30 minutes isn't an option. He gives up and uses search. **The browse-by-intent payoff — the thing this product exists for — is unbuildable from this spine.**

**Severity: high.** This is the largest specification gap by product value: the payoff journey's controls do not exist.

### H-10. The Accessibility Floor asserts a compliance the visual spec does not deliver.

**Locations:** `EXPERIENCE.md` L205 — *"Status must never be conveyed by color alone. Watched, unavailable, and expired are **dimming plus an icon or label**, never a colored dot."* vs `DESIGN.md` L194 (status = scrims only), L260 (Thumbnail status layer — specifies duration badge, checkbox, and scrims; **no icon or label for watched or unavailable**); `.memlog.md` 45 item 6 — *"the expired-freshness marker is specified to exist but its visual form is left unresolved — genuine gap, not an invention."*

Three problems stacked:

1. **The claimed icon/label doesn't exist in DESIGN.md** for watched or unavailable. The mock (`key-library.html`) renders a "Watched" text label — so the mock is ahead of the spec, and the spec is what gets built.
2. **The expired marker is an admitted hole**, yet L205 asserts it complies.
3. **The two scrims are visually near-identical.** `watched-scrim: rgba(255,255,255,0.55)` vs `unavailable-scrim: rgba(244,244,245,0.72)` — 55% pure white versus 72% of `#F4F4F5`. Two *semantically opposite* statuses (one is "you're done with this," the other is "this is broken") rendered as two washes of near-white that differ by ~17% opacity. **Nobody can tell these apart on a grid.** In dark mode they are `rgba(9,9,11,0.60)` vs `rgba(9,9,11,0.72)` — same hue, 12% apart, effectively identical.

The accessibility statement is doing what the rest of the document does: asserting a resolved state over an unresolved one, confidently.

**Severity: high** (accessibility claims that fail audit are expensive to discover late).

### H-11. "Checkbox click" is listed as the way to enter selection mode, but the checkbox doesn't render until selection mode is active.

**Locations:** `EXPERIENCE.md` L98 — *"Entering selection mode: desktop `x` or **checkbox click**; touch long-press"*; `.memlog.md` 42 — *"The selection checkbox renders **whenever a selection-capable mode is active**"*; `DESIGN.md` L133 (checkbox position = thumbnail top-left), `EXPERIENCE.md` L96 (thumbnail click opens Watch).

Circular. And the resolution has a second problem: if the checkbox *is* always rendered on Uncategorized, it overlays the thumbnail — whose click target opens the Watch page. A 17px hit target sitting inside a ~180px click-to-play region on a phone, with no stated hit-slop, guarantees mis-taps in both directions.

**The real moment:** mid-sweep on a phone, he aims for the checkbox on a card near the screen edge, misses by 6px, and **the Watch page opens and starts playing a video**. He now has to stop playback, navigate back, and find his place in a 12-screen sweep — and the spine specifies no back behavior (see M-9). This is the single highest-frequency mis-tap in the product and it costs ~5 interactions each time.

**Severity: high.**

### H-12. "No badge" was over-generalized into "no prompt," and the design already owns the pattern that would fix it.

**Locations:** `EXPERIENCE.md` L66 (the subtraction row), L68 ("Uncategorized shows its count **on its own surface**"), L248 (UJ-2: "he goes there because it's Sunday, not because the app nagged him"), L287 (UJ-4: **"a quiet inline notice: '14 videos are past their watch-by window.' Not a modal, not a badge — a statement he can ignore"**), L104/L154/L157/L159 (inline banners for import, orphans, scope).

The badge rejection is correct and well-argued. The over-generalization is not: the design has **already invented** the dry, non-guilty, ignorable prompt — it uses it for imports, orphans, OAuth scope, and (in UJ-4) for freshness. It refuses to use it for the one thing the entire product depends on.

So the mechanism that starts the weekly loop is: **unaided habit, with zero external cue.** And Phase 1 asks Alexis to form *two* simultaneous new habits from cold, with no reinforcement for either:

1. Save to `_Inbox` instead of Watch Later (PRD R1: "requires a one-time habit change").
2. Open the app on Sunday and triage.

Habit (1) has no in-app surface at all — if he lapses and saves to Watch Later out of muscle memory, the app is silent, the import returns nothing, and the app just looks empty. Habit (2) has no cue.

**The real moment that kills SM-2 and SM-3:** week 2 is busy; he skips Sunday. Nothing tells him. Week 3 he opens the app and Uncategorized holds ~200 videos. Focus mode's scan cost is per-remaining-video-per-sweep, so the session that was already 20 minutes is now **40+**. He closes it. Week 4: ~300. The pile is now exactly the guilt-pile the badge was removed to prevent — **the design's anti-guilt reasoning produced the guilt-pile by removing the only thing that would have stopped it.** Missing a week is catastrophic and superlinear, and nothing prevents missing a week.

The fix is one line and is already in the design's own vocabulary: an inline, dismissible, count-free notice on Library — *"Videos are waiting to be filed."* — phrased in the existing dry register. It is not a badge, not a red dot, not a count, and not a nag.

**Severity: high.**

---

## MEDIUM

### M-1. The two spines contradict each other on the phone grid: DESIGN says one column, EXPERIENCE says never one.

`DESIGN.md` L224: *"Column counts: 4 at `xl`, 3 at `lg`, 2 at `md`, 2 at `sm`, **1 below**."* Then L278, four sections later: *"Do: Two columns minimum on phones / Don't: Ship a single-column full-width feed (that shape *is* the doomscroll)."* `EXPERIENCE.md` L220 and L224 both say two columns, never one, and call it *"an anti-doomscroll requirement, not a density preference."*

`sm` is 640px in Tailwind. "Below `sm`" is every phone in portrait — i.e. **the product's primary triage surface ships the exact layout both documents call the doomscroll shape.** Two sentences in the same document, 54 lines apart.

### M-2. UJ-2 triages in grid view, contradicting the list-mode default and halving the density.

`EXPERIENCE.md` L116 ("Uncategorized opens in **list view**, densest legible rows"), L102 ("Uncategorized naturally wants list"), L226 in DESIGN ("List view exists for volume") — versus L131 ("Sweep **the grid or list**") and L252 ("He sweeps **the grid**, tapping every guitar video").

The flagship journey performs the highest-volume task in the product in the lower-density view, on a phone. Grid at 2 columns ≈ 8 cards/screen; list at 44px touch rows ≈ 16/screen. **The journey doubles its own scroll count** relative to the mode the spine says is right for the job — which makes C-2's ~39 swipes a floor, not an estimate. Nobody reconciled which view Focus mode actually runs in.

### M-3. "Select all loaded" plus mandatory pagination makes the bulk bar's count structurally misleading.

`EXPERIENCE.md` L119 (`a` selects all **loaded**), L190 ("Infinite scroll… banned. **Pagination or explicit load-more only**"), L141 ("the count in the action bar **always tells the truth**").

Page size is never specified anywhere. On a 200-video Uncategorized, `a` selects page 1 only; the count truthfully reports a number that the user reads as "everything." Worse for Focus mode: a sweep must now be performed and applied **per page**, so a 4-sweep week over 4 pages becomes 16 apply cycles, and the sweep's mental model ("I've seen all of these") breaks at every page boundary. The interaction between the anti-doomscroll pagination ban and the bulk-triage model was never worked out.

### M-4. Channel name on the card has no defined behavior — dead text under every single card.

`EXPERIENCE.md` L96 defines exactly two card interactions: thumbnail → Watch, tag chip → filter. Channel is a Phase 1 facet (FR-12) and appears on every card (`DESIGN.md` L259). On YouTube, clicking the channel goes to the channel. Here it does… nothing? Or filters by channel (which would be right, and is the obvious muscle-memory expectation)? Unstated.

**The real moment:** he sees three Paul Davids videos in a row, taps the name to see all of them, and nothing happens. It's the most natural filtering gesture in the entire product and it's undefined — while H-9 shows the *specified* channel filter path doesn't exist either.

### M-5. Search is scoped to the library, and the empty state blames the wrong thing.

`EXPERIENCE.md` L33 (Search: global over the library), L151 (*"No matches for `{query}`." Plus the active filters, each individually clearable — **the usual cause is a filter, not the query**"*).

The app looks like YouTube and puts search in the top bar exactly where YouTube's is. YouTube's search searches *the world*. This one searches only what he saved. The first three times he reflexively searches for something he never saved, he gets "No matches" plus a filter-clearing UI that implicates filters he hasn't set. **The most likely uncanny-valley moment in the whole product**, and the empty state actively misdiagnoses it. One clause — *"Search covers your library only"* — fixes it.

### M-6. The mobile below-player region is exactly the "what's next" region, and the rail-purity claim doesn't survive it.

`EXPERIENCE.md` L61 (*"The app never occupies the screen region where YouTube trains your eye to look for 'what's next'"* — **absent at every breakpoint**), L226/`.memlog.md` 34 (under-player column: title, channel, tags, description, and Phase-2 playlist progression).

On mobile, YouTube has no right rail — its recommendations are a vertical list **below the player**, which is precisely where this spine puts the tag row, the description, and (Phase 2) playlist progression. The "absent at every breakpoint" claim is a desktop statement dressed as a universal one. It doesn't break anything functionally, but it means the loudest rhetorical claim in the Subtraction Contract is false on the surface the user actually triages and watches on.

### M-7. The phone card can't fit what's specified on it.

`EXPERIENCE.md` L96 (`⋮` **always visible** on touch), `DESIGN.md` L259 (card = thumbnail + 2-line title + channel + tag row; *"the tag row… must never be crowded out"*), L262 (overflow past three chips → `+N`), L224 (2 columns on phone).

A 390px phone at 2 columns with 16px gutters gives a ~172px card. Into that width: three `{typography.micro}` (10.5px) pills with padding and gaps — realistically ~50–60px each — will not fit. In practice the overflow threshold is 1–2 chips, not 3, so `+N` is the normal state on mobile and the "visible evidence of Alexis's own work" is collapsed to a number on the surface where he does most of his work. Plus a permanently-visible `⋮` competing for the same row. Nobody measured it.

### M-8. "Surface closure" is asserted and is false.

`EXPERIENCE.md` L44: *"Every capability in the PRD lands on exactly one of these surfaces."*

Counter-examples in Phase 1 alone: **FR-16's manual Watched toggle** (*"The user can also manually toggle Watched"*) has no affordance on any surface, in any component, in the keyboard map, or in the card `⋮` menu. **Import triggering** (C-3) lands nowhere. **FR-2's "create an `_Inbox` playlist for him"** is implied to be in Settings but never stated. The claim is a rubric-satisfying sentence, not a verified property, and it will be trusted by whoever writes the epics.

### M-9. There is no specified return path from the watch page. UJ-3 never comes back.

`EXPERIENCE.md` L259–272: the payoff journey ends at *"the thumbnail dims. It stays exactly where it was"* — describing a card the user cannot currently see, because he is on the watch page. No back affordance, no breadcrumb, no "return to `guitar` · ≤60 min" is specified anywhere. Filter state lives in the URL (L101), so browser-back works on desktop — but on mobile web, back is a system gesture the app doesn't own, and after H-11's mis-tap it's the recovery path for the product's most common error.

### M-10. Watched-at-90% is undermined by the accepted tab-blur limitation, in the same document.

`EXPERIENCE.md` L270 (auto-marks Watched at ~90%) vs L226 (*"embedded playback pauses on tab-blur and screen lock"* — accepted, PRD R2). Any video he leaves running while switching tabs never reaches 90% and never marks Watched — so the Watched lens, the watched-dimming status, and the "Unwatched" filter chip in the mock all quietly under-report. Acceptable for a personal tool, but it means SM-1's "did he actually watch it" signal is unreliable and nobody said so.

### M-11. The triage row's own numbers don't produce its own stated height.

`DESIGN.md` L152–156 (`triage-row`: `row-padding-y: 6px`, `thumbnail-width: 34px`) vs L226 (*"Row height lands near **32px** on desktop"*).

34px of thumbnail plus 12px of vertical padding is 46px minimum — 44% taller than stated. Which matters, because the 32px figure is the basis for the density argument that justifies list mode over grid mode, which is the argument C-2's scroll count depends on. The density claim is ~30% optimistic.

---

## LOW

- **L-1. A 30-day Trash retention is invented and hard-coded into binding microcopy.** `EXPERIENCE.md` L84 and L254 both put *"They move to Trash for 30 days"* in confirmation copy; `.memlog.md` 45 flags it as a distill-pass invention; PRD FR-11 says only *"a retention window."* A never-made decision is now user-facing text in two places.
- **L-2. `Calendar` is in the Phase-1 shadcn component list** (`DESIGN.md` L255) for date filters that are Phase 2 (PRD §6.2). Symptomatic of H-4.
- **L-3. `.memlog.md` 42 explicitly flagged the duration-as-content / checkbox-rendering interpretation "for Alexis to confirm at review."** It was never confirmed and ships as spec — and H-11 shows it was the wrong call.
- **L-4. The spine documents phase nothing, but the mock badges P2 in the sidebar** (`.working/key-library.html`). Mock and spine disagree about what Phase 1 looks like.
- **L-5. `EXPERIENCE.md` L226 says the playback limitation is mentioned "once, in Settings"** — but UJ-3's cooking variant (L272) depends on him already knowing it, and there is no other surface that teaches it. He will discover it by having a video stop while cooking.

---

## What Would Actually Break First

**The first triage session — week 1, Sunday, on the phone. Specifically: the moment he tags his third video.**

Everything converges there:

1. **Focus mode is empty on day one.** Step 1 is "Pick the target tag first" — from a tag set that does not exist yet. Nothing in either spine explains creating a tag during triage, and the Tags surface is a separate destination. So the very first use of the SM-C2 mitigation is a dead end, and he falls back to list mode with a typeahead whose behavior is unspecified (C-1).
2. **He tags a video `guitar`, and it disappears.** Self-clearing does what it says. Half a second later he wants `course` on it too — the taxonomy the PRD designed (topic *and* format) requires it — and there is no path back that costs less than six interactions (C-1).
3. **He has ~100 videos, most needing two tags, no undo** (H-7), **no sort**, **an unreadable selection state at scroll speed** (H-3), **a checkbox he keeps missing into the player** (H-11), **and a modal on every discard** (H-6).
4. **He hits ~25 minutes**, well past the "under ten minutes" the spine promised and past the doomscroll it replaced — SM-C2's explicit failure condition.
5. **Nothing reminds him to come back next Sunday** (H-12). Week 2 has 200. Week 3 has 300.
6. **Two of those three weeks he opens the app, finds nothing curated worth watching** (H-8: Phase 1 only accumulates), **and the watch page's "open in YouTube" button is right there** (C-5).

SM-3 asks whether he's still using it after a month. On this spine, the honest answer is that **he abandons it in week two**, and the proximate cause is that Focus mode — the one thing designed to make week one survivable — cannot do the thing his own tag model requires on the second tag of the first video.

**Fix ordering, by leverage:** (1) resolve the Focus-mode / self-clearing collision and re-derive UJ-2's numbers honestly [C-1, C-2]; (2) decide import triggering and give it an affordance [C-3]; (3) intercept the embed's end screen [C-4]; (4) add a manual next-in-filter control under the player [C-5]; (5) re-scope the "no badge" rule to permit the dry inline notice the design already uses everywhere else [H-12].
