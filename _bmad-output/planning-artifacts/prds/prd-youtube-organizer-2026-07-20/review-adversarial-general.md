---
title: "Adversarial Review — YouTube Organizer PRD"
reviewer: "Cynical Product Reviewer"
date: 2026-07-20
target: prd.md (prd-youtube-organizer-2026-07-20)
---

# Adversarial Review: YouTube Organizer PRD

**Verdict up front:** This PRD is well-written and internally consistent, which is exactly the problem — it has polished the *architecture of a chore* until it looks like a product. It names its own kill-risk (SM-C2) and then builds 18 FRs on top of it without ever proving the loop is worth doing. The core premise — that manual triage of ~100 videos/week beats doomscrolling — is asserted, never tested. Below, sharpest first.

---

## CRITICAL

### C1 — The premise is unfalsifiable and the design never protects against the one way it fails
**Location:** §1 Vision; §7 SM-C2; §4.3 (whole feature)
**Attack:** The entire product rests on one bet: that *browsing 100 curated videos by tag* is less of a time-sink than *scrolling Watch Later*. But triage is scrolling too — you still have to look at all 100 videos, just now with the added labor of tagging each one. You haven't removed the pile; you've added a data-entry step in front of it and moved the scroll from Sunday-on-YouTube to Sunday-in-the-app. SM-C2 ("triage effort stays low… if it costs more than the doomscroll it replaced, that's failure") is the honest admission that this could be a net *increase* in time spent. Yet nothing in the design bounds triage cost. FR-7 makes triage *faster*; it does not make it *smaller*. There is no cap, no "auto-archive anything untouched for 2 weeks," no forcing function. The PRD names the failure mode and then declines to engineer against it.
**Dodged decision / fix:** Decide the actual smallest test that proves the premise *before* building the org model. E.g.: for 4 weeks, import the _Inbox, tag nothing, and just use search + channel filter. If find-by-intent already beats YouTube with zero manual tagging, then Tags/Playlists/Freshness are gold-plating. If it doesn't, you've learned the premise is weak for the price of a weekend — not 18 FRs. Add a real guardrail metric with a number (e.g. "median triage session < 15 min" — measured, not vibes).

### C2 — "Uncategorized" is Watch Later with extra steps, and the PRD knows it
**Location:** §3 Glossary (Uncategorized); UJ-2 edge case ("Uncategorized persists as a working list he returns to"); memlog line 22 ("or Uncategorized becomes a new doomscroll")
**Attack:** The memlog literally flags the tension: "~100 videos/week land in Uncategorized but categorization is manual → Uncategorized becomes a new doomscroll." The PRD's answer is FR-7 (bulk tools) and a shrug: the UJ-2 edge case reframes an *unfinished, growing pile* as "a working list he returns to." That is the exact rationalization every abandoned todo-app inbox gets. At 100/week, one skipped Sunday = 100 stale items; a skipped month = 400. Because Uncategorized is a *derived view* (no Tag, no Playlist), it can never be "cleared" except by tagging everything — there is no "dismiss without tagging" that removes an item from the view but keeps it in the Library. So the only exits are (a) tag it or (b) delete it. Miss two weekends and the derived view is a 200-item wall of guilt — the doomscroll, reincarnated inside your own tool where it's *less* fun than YouTube.
**Dodged decision / fix:** Add a third exit: a "seen / skip" state that removes a video from Uncategorized without requiring a tag (an implicit "reviewed, keep untagged" facet). Or invert the model — default-import as *Evergreen, untagged, but NOT Uncategorized*, so the inbox self-drains on import and tagging becomes opt-in enrichment, not mandatory toll. Either way, decide: is tagging *required* or *optional*? The current model makes it required-by-omission, which is the trap.

### C3 — Destructive writes against the real account, for a benefit that a read-only design delivers just as well
**Location:** FR-1, FR-4, FR-6; R3; §8 quota
**Attack:** The app takes **write scope** on the user's actual YouTube account to do two things: delete migrated playlists (FR-4) and auto-clear the _Inbox after import (FR-6). Both are destructive, irreversible on YouTube's side, quota-costly, and — critically — *unnecessary to the product's value*. The value is "organize in the app and browse by intent." That value is 100% achievable read-only: copy videos from _Inbox into the Library, and instead of deleting from _Inbox, just track "already-imported" locally (you already store the YouTube video ID for dedupe — FR-5). The user never sees a dirty _Inbox because the *app* is where he lives now; YouTube is "just a source" (§1). So why hand a solo weekend tool the power to mutate the user's real account? The stated reason (FR-6 consequence: "_Inbox on YouTube is clean") is cosmetic tidiness on a surface the product explicitly wants him to stop looking at. You're taking on the single largest blast-radius risk in the app to keep a playlist tidy that the whole product is designed to make him ignore.
**Dodged decision / fix:** Ship MVP **read-only**. Replace FR-6 auto-clear with local "imported" tracking. Make _Inbox clearing a manual, user-initiated, batched action *outside* MVP (or never). Reframe FR-4 migration-delete as "you can delete these yourself on YouTube" with a link. This drops you from `youtube.force-ssl` to read scope, halves the R3/R4 risk surface, kills a whole class of "the app deleted my stuff" bugs, and loses *nothing* the vision actually needs.

---

## HIGH

### H1 — The whole product depends on a forever-habit-change the PRD treats as a one-line footnote
**Location:** R1 ("Requires a one-time habit change"); UJ-2 ("his new habit, replacing Watch Later"); SM-3
**Attack:** Two behavior changes must hold *forever* or the product dies: (1) save to _Inbox instead of the muscle-memory "Save to Watch Later," and (2) run weekly triage. R1 calls #1 "a one-time habit change" — it is not one-time, it is *every single save, forever*, fighting a UI where "Watch Later" is the default one-tap action and "_Inbox" is buried three taps deep in "Save to playlist." The friction is on the *capture* side, every day, and the app has zero presence there (it can't change YouTube's save UI). If he reflexively saves to WL even 30% of the time, those videos are *invisible to the app forever* (R1: WL is API-inaccessible) — so the Library is silently incomplete, and "find something to watch" fails because the thing he wanted isn't there. SM-3 ("still using it after a month") is the only metric that would catch this, and it's self-reported and binary.
**Dodged decision / fix:** Acknowledge capture-side friction as a *primary* risk, not a decided-and-closed one. Consider: can the app periodically read WL via any path (it can't via Data API — confirm there's truly no workaround before betting the product on _Inbox)? At minimum, add a metric for "videos that ended up in WL instead of _Inbox" (he can eyeball WL) so leakage is visible instead of silent.

### H2 — "Embedded player = anti-doomscroll" is a category error; the doomscroll is the user, not the sidebar
**Location:** §1; §4.6; FR-15; NFR "Anti-doomscroll by design"
**Attack:** The thesis is that removing YouTube's sidebar/autoplay stops the doomscroll. But the PRD's own diagnosis (§1) is that the doomscroll happens at *decision time* — "scrolling an endless chronological list to find the right thing." That scroll is now *inside your app* (Uncategorized, browse views). Removing the sidebar from the *playback* screen addresses a different, weaker failure mode (getting sucked into "related videos" *after* you've already chosen something). Worse, FR-15 keeps an "open in YouTube" escape hatch, and FR-16 tracks watched-% via the IFrame Player API — you're paying real complexity (IFrame API integration, progress polling, tab-blur handling per §10) to build a worse video player than YouTube's, for one user, to solve a problem (post-selection related-video rabbit-holing) that isn't the one §1 describes. And the moment he taps "open in YouTube" for background audio (a first-class use case — cooking), he's back in the recommendation machine anyway.
**Dodged decision / fix:** Justify the embedded player on its own merits or cut it from MVP. The cheapest anti-doomscroll playback is: click video → opens YouTube in a new tab. You lose watched-% auto-tracking (FR-16) — but is auto-Watched worth an IFrame API integration for a solo tool? Make Watched a manual toggle (already in FR-16 as a fallback) and defer embedded playback + FR-16 auto-tracking entirely. Prove people *find* better first; playback polish is the least-risky thing to add later.

### H3 — 18 FRs for a solo tool; at least half are self-deception about "MVP"
**Location:** §6.1 (all of it)
**Attack:** §6.1 lists essentially every FR except FR-8 as "in scope." That is not an MVP; that's the whole product relabeled. The premise (C1) is unproven, yet the MVP commits to: migration + confirmed deletion (FR-3/4), auto-clear writes (FR-6), Tag CRUD *including rename AND merge* (FR-9), ordered multi-playlist membership with reordering (FR-10), a Freshness/shelf-life engine with expiry surfacing (FR-17/18), combined-facet browse with *tri-date time-lapse range* filtering (FR-13), and an embedded IFrame player with watched-% (FR-15/16). Tag *merge* (FR-9) is a fight-tag-drift feature you only need after months of use — it's premature by definition. The Freshness engine (FR-17/18) is described as "distinctive/differentiating" (memlog 24) — differentiating *to whom?* There's one user. It's two more schema fields, an expiry job, and a review UI solving a problem ("perishable match results rot") that a `date-published` filter (already in FR-13) mostly handles. Migration (FR-3/4) is a *one-time* flow — the highest-code, highest-risk, lowest-repeat feature — front-loaded into MVP where it delays proving the *recurring* loop that actually matters.
**Dodged decision / fix:** Ruthless cut. True MVP to prove the premise: FR-5 (import, read-only), FR-9 minus merge/rename (just create/apply/remove tags), FR-12 (channel/length auto), FR-13 minus tri-date ranges (one date, or none), FR-14 (search). That's it. Defer FR-3/4 (migration), FR-6 (writes), FR-8, FR-10 (playlists), FR-15/16 (embedded player), FR-17/18 (freshness). Ship that, live with it a month, *then* decide what's missing from real pain — not from a planning document.

### H4 — Success is entirely self-reported and binary; nothing here can prove the product failed
**Location:** §7 (all metrics), especially SM-1 "large majority of sessions," SM-2 "roughly weekly," SM-3 "hasn't abandoned it"
**Attack:** Every primary metric is a feeling the user reports about himself. "Large majority of sessions" — measured how? The app can't see his YouTube sessions, so it can't know what fraction of watch-decisions started in-app vs. on YouTube. "Roughly weekly" and "still using after a month" are yes/no vibes. There is no instrumentation proposed, no baseline captured ("how much do I doomscroll *now*?"), so even after a month there's no before/after. SM-C2 ("triage costs more than the doomscroll it replaced") is the one metric that could falsify the whole premise — and it has no unit, no threshold, no measurement plan. The result: this product cannot fail on paper. Whatever happens, the metrics can be narrated as success.
**Dodged decision / fix:** Instrument the two things the app *can* actually see: (1) triage-session duration and items-processed (gives SM-C2 a real number), and (2) in-app "play" events over time (proxy for SM-1/SM-3 — if it drops to zero, he abandoned it). Capture a one-line baseline now: "I currently open YouTube ~N times/day and it eats ~M minutes." Without a before-number, "the doomscroll stopped" is unprovable.

---

## MEDIUM

### M1 — R5 (platform dependency) is dismissed as "acceptable risk" when it already came true once
**Location:** R5 ("acceptable risk for a personal tool; noted for awareness"); R1; R2
**Attack:** R5 waves off ToS/policy dependency in one glib note — but the PRD's *own history* refutes the glibness: R1 (Watch Later got API-locked in ~2016, per memlog 11) and R2 (background playback Premium-gated) are *two policy walls the product already hit* during planning. The on-ramp had to be redesigned (WL → _Inbox) before a line of code was written. So "policy could change" isn't a hypothetical to note — it's the established failure pattern of this exact API. Betting write-scope + embedded-player + _Inbox-clearing on "YouTube won't tighten further" is betting against the trend line the PRD itself documented.
**Dodged decision / fix:** Reframe R5 from "acceptable, noted" to "the app must degrade gracefully when a scope/embed gets revoked." Concretely: because the Library stores full local metadata (§8 durability — good), the *organization* survives any API change. Say that explicitly as the mitigation. And it's another argument for read-only (C3): fewer scopes = fewer things YouTube can yank.

### M2 — Quota is hand-waved with an unvalidated assumption the PRD flags but doesn't resolve
**Location:** §8 quota ASSUMPTION; §9; R4; Open Q4
**Attack:** The PRD assumes ~100 videos/week fits the 10k-unit/day quota, tags it "needs validation," lists it in §9, restates it as R4, and re-asks it as Open Q4 — four mentions, zero answers. This is a decision dodged four times. It matters because *write* calls (playlistItems.delete for FR-6, playlists.delete for FR-4) cost 50 units *each* on the YouTube Data API. 100 deletes = 5,000 units in a single triage session — half the *entire daily quota* — before you've read anything. Add the reads for import and a re-run and a single Sunday could blow the cap, at which point FR-5/FR-6 silently fail mid-triage. This is not a footnote; it's a potential hard wall on the core loop.
**Dodged decision / fix:** Do the arithmetic *now*, in the PRD, not "later." It's public: list=1, playlistItems.delete=50, playlists.delete=50. Rough it out. If 100 deletes/week is fine, say so with numbers. If it's tight, that's a *third* independent reason to drop FR-6 auto-clear (C3) — read-only import costs ~1 unit/page and the quota question evaporates.

### M3 — Migration is the riskiest feature, runs exactly once, and gates first-run before value is proven
**Location:** UJ-1; FR-3; FR-4; §6.1; Open Q5
**Attack:** UJ-1 puts a bulk import of "playlists accumulated over years," structure-preserving, with dedupe, partial-failure handling (Open Q5 admits this is undefined), *and* an optional destructive delete of the originals — all as the *first thing the user experiences*. If migration partially fails (Open Q5: "define once API cost/limits are known" = undefined at ship), the user's first impression is a half-imported mess with real videos possibly deleted from YouTube (FR-4). Highest complexity, highest blast radius, lowest repeat value (runs once), placed at the point of maximum user uncertainty (first run, before he trusts the tool).
**Dodged decision / fix:** Cut migration from MVP entirely. Start with an empty Library and let it fill from weekly _Inbox triage — the loop you actually need to prove. If migration is ever built, it's read-only-copy with NO delete option, and partial-failure behavior (Open Q5) must be *defined before build*, not deferred.

### M4 — Freshness/Perishable requires a prediction the user can't reliably make at triage time
**Location:** FR-17; FR-18; §3 (Freshness); UJ-4
**Attack:** The Freshness model asks the user, *while triaging 100 videos fast*, to also decide per-video whether it's Evergreen or Perishable *and set a watch-by window*. That's a forecast about his own future interest — the exact judgment humans are worst at, made under the exact time pressure (fast bulk triage, SM-C2) that makes them not do it. So in practice everything defaults to Evergreen (the stated default, FR-17), Perishable goes unused, FR-18's expiry-surfacing has nothing to surface, and the "distinctive feature" (memlog 24) is dead weight. Meanwhile the actual goal — prune old stuff — is already served by FR-13's published-date filter ("everything before 2023") with zero per-video labeling.
**Dodged decision / fix:** Kill explicit Freshness for MVP. Derive staleness automatically from the dates you already store (FR-5): "saved > N months ago and never watched → surface for prune." No per-video forecast required. If real use shows some channels are reliably perishable (news, match results), add a *per-channel* default later — not a per-video chore.

### M5 — "First-class mobile AND desktop from day one" doubles the build for an unproven premise
**Location:** §8 "Responsive/both surfaces"; FR-7 (keyboard + touch); memlog 27
**Attack:** "Both surfaces first-class from day one" sounds disciplined but is scope inflation. Fast bulk triage (FR-7, load-bearing for SM-C2) has *opposite* optimal interactions on the two surfaces: keyboard multi-select + hotkeys on desktop, versus touch multi-select on mobile — two genuinely different triage UIs to design, build, and test, both on the critical path, before you know the loop is worth doing at all. For a solo tool the honest question is: where will he *actually* triage 100 videos? Almost certainly at a desk with a keyboard. Mobile is for *watching* (couch, cooking), not for bulk-tagging.
**Dodged decision / fix:** Decide the *primary* triage surface (near-certainly desktop/keyboard) and build that first-class; make mobile *watch-and-browse* first-class but triage merely functional. "Both first-class for everything" is a cost the premise hasn't earned.

---

## LOW

### L1 — Working title still unconfirmed at the top of a "source of truth" doc
**Location:** §0 title; line 9 "Working title — confirm"
**Attack:** Minor, but a PRD that declares itself "the source of truth for downstream BMAD workflows" and then can't name the product is a small tell that other confirmations may be soft too.
**Fix:** Confirm or change the name; it's a 10-second decision blocking nothing.

### L2 — No-undo deletion is immediate and irreversible, flagged only as a deferrable assumption
**Location:** FR-11 ASSUMPTION ("no undo/trash in MVP… revisit if it feels risky"); FR-7 discard
**Attack:** "Discard" (FR-7) is bulk delete-from-Library during *fast* triage — the highest-velocity, lowest-attention moment in the app — with *no undo* (FR-11). Fast bulk actions + no undo = the user will nuke something he wanted and have no recovery. "Revisit if it feels risky" means revisit after it's already bitten him.
**Fix:** A trash/soft-delete is cheap (a `deleted_at` column + a filter) and specifically de-risks the fastest, most error-prone flow. Pull it into MVP; it's not gold-plating, it's a seatbelt on the one destructive bulk action.

### L3 — Open Questions are numbered 1, 2, 4, 5 — there is no 3
**Location:** §11
**Attack:** Trivial, but a missing item in a numbered list of open questions suggests a question was silently dropped. In a doc this careful, the gap invites the question: what *was* #3, and was it resolved or lost?
**Fix:** Renumber, or if #3 was deliberately removed, note why. Loose ends in the "open questions" section undermine confidence that the rest is tight.

---

## Summary of the through-line

Three cuts collapse most of the risk, and they reinforce each other:
1. **Go read-only** (C3) — kills the write-scope blast radius (R3), most of the quota question (M2/R4), and shrinks the ToS exposure (M1/R5).
2. **Cut to a real MVP** (H3) — drop migration (M3), embedded player (H2), freshness (M4), and dual-surface triage (M5); keep import + tag + search + browse.
3. **Instrument and bound triage** (C1/H4/C2) — give SM-C2 a real number, add a non-tagging exit from Uncategorized, capture a baseline.

Do those and you have a weekend test of the actual premise. Skip them and you've spent weeks building a beautifully-specified machine for turning one chore (doomscrolling) into another (triage) — with the extra feature that the new chore can delete videos from your real account.
