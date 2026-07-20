---
title: "YouTube Organizer"
status: draft
created: 2026-07-20
updated: 2026-07-20
---

# PRD: YouTube Organizer
*Working title — confirm.*

## 0. Document Purpose

This PRD is the product definition for **YouTube Organizer**, a single-user personal tool built by and for Alexis. It is the source of truth for downstream BMAD workflows (UX, architecture, epics/stories). It **replaces the former `BACKLOG.md`** (now removed), which framed the app as a thin YouTube-playlist remote control — a different product from the one defined here. Vocabulary is anchored in the Glossary (§3); features are grouped with Functional Requirements (FRs) nested and globally numbered; inferred decisions are tagged inline and indexed in §9. Tech/stack detail lives in `project-context.md` and the `Docs/` folder, not here — this PRD describes capabilities, not implementation.

## 1. Vision

Alexis saves a lot of interesting YouTube videos and they pile up. YouTube's own tools for managing that pile are slow and shallow, so finding *the right thing to watch* means scrolling an endless chronological list — and that scrolling **is** the doomscroll. The result: he watches whatever happens to be near the top of Watch Later instead of what he actually wants.

**YouTube Organizer flips this.** It is a **personal curation library** where YouTube is only a *source*, not the home of organization. Videos are captured into the app, organized *by intent* — tags, channel, length, and hand-built playlists — and pruned so the library stays lean. When Alexis wants to watch something, he browses **by mood and context** ("I have an hour for guitar," "I'm in a Barça mood," "a history podcast while I cook") and finds it in seconds — then watches it inside the app, away from YouTube's recommendation machinery.

The measure of success is behavioral, not commercial: **Watch Later stays near-empty, the library stays curated, and the doomscroll stops.**

## 2. Target User

### 2.1 Jobs To Be Done
- **Functional:** Move saved videos out of YouTube's chronological pile into a structure I control (tags, channel, length, playlists), and find the right one fast when I want to watch.
- **Emotional:** Stop feeling like my saved videos are a guilt-pile I doomscroll; feel in control of a curated collection I actually watch.
- **Contextual:** Pick something to watch *for the moment I'm in* — the mood (Barça, concerts), the activity (cooking → long podcast), the time budget (1 hour for guitar), not by upload date.
- **Curatorial:** Keep the library lean — don't hoard thousands of videos I'll never watch; let time-sensitive stuff expire instead of rotting.
- **Builder:** This is my own tool, engineered properly (real architecture, tests, CI) even though the audience is one person.

### 2.2 Non-Users (v1)
Everyone but Alexis. There is no multi-user, sharing, collaboration, or public-facing surface in v1.

### 2.3 Key User Journeys

- **UJ-1. Alexis migrates his existing YouTube playlists into the app (one-time).**
  - **Persona + context:** Alexis, first run, has several YouTube playlists accumulated over years and wants to start from his existing structure rather than a blank slate.
  - **Entry state:** Authenticated via Google/YouTube (existing OAuth), first login.
  - **Path:** App lists all his YouTube playlists → he selects which ones to import → app imports each selected playlist and its videos, **replicating the playlist structure** in the app → he sees a success summary (X playlists, Y videos) → app *offers* to delete the imported playlists from YouTube.
  - **Climax:** His organization now lives in the app, mirroring what he had on YouTube — nothing lost.
  - **Resolution:** He optionally clears the migrated playlists from YouTube, every deletion **explicitly confirmed**. YouTube is now just a source.
  - **Edge case:** He declines deletion for a playlist → it stays on YouTube untouched; the app never deletes without per-action confirmation.

- **UJ-2. Alexis clears his weekly inbox (recurring, ~Sunday).**
  - **Persona + context:** During the week Alexis saves interesting videos to a designated `_Inbox` playlist on YouTube (his new habit, replacing Watch Later). ~100 videos accumulate per week.
  - **Entry state:** Authenticated; opens the app for a triage session on desktop (keyboard) or phone (touch).
  - **Path:** App imports the `_Inbox` playlist → new videos land in **Uncategorized** → app removes them from the `_Inbox` playlist on YouTube (auto-clear) → Alexis works through Uncategorized, **fast**: multi-selecting videos, bulk-applying tags, setting length/format and evergreen-vs-perishable, discarding junk past-him saved.
  - **Climax:** Uncategorized is emptied (or meaningfully reduced) without one-video-at-a-time tedium; `_Inbox` on YouTube is clean.
  - **Resolution:** The week's catch is now organized and findable. `[ASSUMPTION: app may offer tag/attribute *suggestions* he one-click confirms, but never auto-applies.]`
  - **Edge case:** He doesn't finish in one sitting → Uncategorized persists as a working list he returns to; nothing is lost or force-categorized.

- **UJ-3. Alexis finds something to watch for the mood/moment (the payoff).**
  - **Persona + context:** It's a random Tuesday night, or he has a free hour, or he's about to cook.
  - **Entry state:** Authenticated, opens the app instead of YouTube.
  - **Path:** He browses **by intent** — filters by tag ("guitar"), channel ("FC Barcelona"), and/or length ("under/over N minutes"), or opens a hand-built playlist ("Guitar Course Vol.1") → picks a video.
  - **Climax:** In seconds he's found something he genuinely wants — "1 hour of guitar tutorials," "a long history podcast," "Barça highlights" — not whatever was near the top of a list.
  - **Resolution:** He watches it **inside the app** (embedded player, no YouTube sidebar/autoplay), or taps *open in YouTube* when he wants background audio while cooking. It auto-marks watched when he's seen enough.
  - **Edge case:** Nothing fits the mood → he still isn't doomscrolling; he closes the app or prunes instead.

- **UJ-4. Alexis keeps the library lean (ongoing curation).**
  - **Persona + context:** Alexis doesn't want thousands of unwatched videos; some saves are time-sensitive (match results, news) and lose relevance fast.
  - **Entry state:** Authenticated; periodically, or prompted by the app.
  - **Path:** The app surfaces **expired perishables** — e.g., "14 videos marked perishable are past their window" → he bulk-reviews: watch now, or discard.
  - **Climax:** Stale, no-longer-relevant videos leave the library in one sweep instead of silently rotting.
  - **Resolution:** The library reflects what he actually still wants to watch.

## 3. Glossary

- **Library** — The canonical set of **all** captured Videos. A Video **always** lives in the Library, independent of any Tag or Playlist. Tags and Playlists are optional overlays on top of the Library; they never determine whether a Video exists. Deleting a Video from the Library removes it entirely.
- **Video** — A single YouTube video captured into the app, living in the Library. The app stores its own copy of metadata (title, description, channel, thumbnail, duration, published/posted date, YouTube URL/ID) plus app-side timestamps (imported date, source-added date) so it survives after removal from any YouTube playlist. Belongs to zero-or-more Playlists; carries Facets.
- **Source (YouTube)** — YouTube, used only as the origin of videos. The app does not treat YouTube as the home of organization.
- **`_Inbox` (Inbox playlist)** — One normal YouTube playlist the user designates (via UI selection, persisted per-user) as the capture target — replacing Watch Later, which the YouTube API cannot access. The app reads it and removes imported items from it.
- **Migration** — The one-time first-run import of the user's pre-existing YouTube playlists, replicating their structure in the app.
- **Uncategorized** — A **derived view** of the Library: Videos that have not yet been organized — i.e. carry **no Tags and belong to no Playlist**. Self-clearing: a Video leaves Uncategorized the moment it gets its first Tag or Playlist membership. It is a state, not a container — an Uncategorized Video still lives in the Library.
- **Facet** — A structured attribute of a Video used for filtered browsing: **Tag**, **Channel**, **Length**, **Freshness**, and **Dates** (imported / source-added / published). Facets are how the user *finds*.
- **Tag** — A free-form, multi-value label the user applies (e.g. `history`, `guitar`, `barca`, `podcast`). Carries topic *and* format. A Video has zero-or-more Tags.
- **Channel** — The source YouTube channel of a Video, captured automatically. A browse/filter facet.
- **Length** — The Video's duration, captured automatically; used to filter (e.g. exclude very long/short).
- **Playlist** — A hand-built, user-curated, **ordered** collection the user assembles deliberately (e.g. "Guitar Course Vol.1"). Distinct from Tags/facets; how the user *curates sequences*. Distinct from the YouTube playlists that exist only as source/inbox.
- **Freshness / Shelf-life** — A Video is **Evergreen** (never expires) or **Perishable** (has a watch-by window). The app tracks a Perishable's age and flags it once expired.
- **Watched** — State auto-set when the user views ≥ a threshold percentage of a Video; shown as a badge. The Video stays in place (not auto-removed).

## 4. Features

### 4.1 YouTube Connection & Account
**Description:** Alexis signs in with Google/YouTube (existing OAuth foundation). Because the app must *remove* videos from the `_Inbox` (and optionally delete migrated playlists) on YouTube, it requires **write** scope in addition to read — a broader scope than the current build. Single-user; no account management beyond his own connection. Realizes UJ-1, UJ-2.

**Functional Requirements:**

#### FR-1: Authenticate with YouTube (read + write scope)
Alexis can sign in with his Google account and grant the app read **and write** access to his YouTube playlists.
**Consequences (testable):**
- After consent, the app can list the user's playlists, read playlist items, and remove/modify playlist items on the user's behalf.
- If only read scope is granted, Inbox auto-clear (FR-6) and playlist deletion (FR-4) are disabled with a clear message; the rest of the app still works.

#### FR-2: Designate the `_Inbox` playlist
Alexis sees a list of all his YouTube playlists and selects one as the `_Inbox` capture target. The selection is stored in the app (per-user), **not** hard-coded or set via environment variable.
**Consequences (testable):**
- The app lists the user's YouTube playlists and lets him pick which one is `_Inbox`.
- The chosen playlist is persisted in the app database and used for all subsequent imports.
- He can change the `_Inbox` selection at any time from the UI; changing it takes effect on the next import.
- If he has no suitable playlist, the app can create an `_Inbox` playlist on YouTube for him.

### 4.2 First-Run Migration
**Description:** On first use, Alexis brings his existing YouTube organization into the app, replicating his playlist structure, then optionally clears those playlists from YouTube — with hard guards against accidental deletion. Realizes UJ-1.

**Functional Requirements:**

#### FR-3: Import selected YouTube playlists (structure-preserving)
Alexis can see all his YouTube playlists and select which to import; the app imports each as an app Playlist containing its videos. Realizes UJ-1.
**Consequences (testable):**
- All of the user's YouTube playlists are listed for selection.
- Importing a playlist creates an app Playlist of the same name containing the imported Videos, preserving membership.
- On completion the app shows a summary (playlists imported, videos imported, any failures).
- Re-running import does not create duplicate Videos or duplicate Playlists. Dedupe by YouTube video ID / playlist identity.

#### FR-4: Optionally delete migrated playlists from YouTube (confirmed)
After a successful import, Alexis can choose to delete the imported playlists from YouTube.
**Consequences (testable):**
- Deletion is never automatic; each deletion requires an explicit confirmation.
- Declining leaves the YouTube playlist untouched.
- A deletion only proceeds after the corresponding import is confirmed successful.

### 4.3 Weekly Inbox Triage
**Description:** The recurring core loop. The app imports the `_Inbox` playlist, lands new videos in **Uncategorized**, clears them from `_Inbox` on YouTube, and gives Alexis **fast, bulk** tools to organize ~100 videos/week without one-at-a-time tedium. Categorization is always manual; the app may *suggest* but never auto-applies. Realizes UJ-2.

**Functional Requirements:**

#### FR-5: Import the `_Inbox` into the Library (Uncategorized)
Alexis can import new videos from the `_Inbox` playlist; they enter the Library and, being un-tagged and un-playlisted, appear as Uncategorized. Full metadata is stored locally. Realizes UJ-2.
**Consequences (testable):**
- Each imported Video stores, locally: title, **description**, channel, thumbnail, duration, **published/posted date**, and YouTube ID/URL.
- Each imported Video also records app-side timestamps: **imported date** (when it entered the app) and **source-added date** (when it was added to the source playlist, from the YouTube playlist-item data).
- Imported Videos appear in Uncategorized until organized.
- Videos already in the Library are not re-imported as duplicates.

#### FR-6: Auto-clear the `_Inbox` on YouTube after import
After a Video is imported, the app removes it from the `_Inbox` playlist on YouTube.
**Consequences (testable):**
- A Video successfully imported is removed from `_Inbox` on YouTube.
- A Video that failed to import is **not** removed from `_Inbox`.
- Removal failures are surfaced, not silent.

#### FR-7: Fast bulk categorization
Alexis can multi-select Videos in Uncategorized and apply Tags, Length/Format, and Freshness in bulk, and discard junk. Realizes UJ-2.
**Consequences (testable):**
- User can select multiple Videos and apply one or more Tags to all at once.
- User can set Freshness (Evergreen / Perishable + window) on selected Videos.
- User can discard (delete) selected Videos.
- Desktop supports keyboard-driven triage; mobile supports touch-driven triage (both first-class).

#### FR-8: Categorization suggestions (assistive, never automatic)
The app may suggest Tags/attributes for a Video, which Alexis confirms or ignores.
**Consequences (testable):**
- Suggestions are never applied without explicit user action.
- `[ASSUMPTION: suggestions are a nice-to-have; acceptable to defer past MVP — see §6.2.]`

### 4.4 Organization Model
**Description:** How videos are organized: free-form **Tags** (topic + format), automatic **Channel** and **Length** facets, and hand-built ordered **Playlists**. Tags/Channel/Length = how he *finds*; Playlists = how he *curates sequences*. Realizes UJ-3.

**Functional Requirements:**

#### FR-9: Manage Tags
Alexis can create, apply, rename, merge, and remove Tags on Videos.
**Consequences (testable):**
- A Video can carry multiple Tags.
- Renaming a Tag updates it everywhere it's applied.
- `[ASSUMPTION: merge two tags into one is wanted to fight tag drift over time.]`

#### FR-10: Build and manage Playlists
Alexis can create ordered Playlists, add/remove Videos, and reorder them.
**Consequences (testable):**
- A Playlist has a user-defined order.
- A Video can belong to multiple Playlists.
- **Removing a Video from a Playlist only drops that membership — the Video remains in the Library** (and in any other Playlists). It is *not* deleted.
- A Video that belongs to no Playlist still lives in the Library; if it also has no Tags it appears as Uncategorized.

#### FR-11: Delete a Video from the Library
Alexis can permanently delete a Video from the Library — the only action that removes a Video from the app entirely.
**Consequences (testable):**
- Deleting a Video removes it from the Library and from every Playlist and Tag it was on.
- Delete is available both singly and in bulk (the "discard" action in FR-7 is this operation applied during triage).
- Deletion is app-side only; it does not touch YouTube. `[ASSUMPTION: no undo/trash in MVP — deletion is immediate; revisit if it feels risky.]`

#### FR-12: Channel & Length as automatic facets
Channel and Length are captured automatically and usable as filters.
**Consequences (testable):**
- Every imported Video has its source Channel and duration populated.
- Videos can be filtered by Channel and by Length range.

### 4.5 Browse & Retrieval (by intent)
**Description:** The payoff. Alexis finds something to watch by combining facets — tag, channel, length — and/or opening a curated Playlist, matching mood/context/time-budget. Realizes UJ-3.

**Functional Requirements:**

#### FR-13: Filter/browse by combined facets (incl. date ranges)
Alexis can browse his Library filtered by any combination of Tag(s), Channel, Length range, Freshness, Watched state, and **Date range** over any of the three dates (imported / source-added / published). Realizes UJ-3.
**Consequences (testable):**
- Filters combine (e.g. Tag=`guitar` AND Length ≤ 60 min AND Watched=no).
- **Date filtering is a time-lapse range** — a from–to window (either bound optional, so "before 2023", "after June 2024", or "between X and Y" all work) — selectable against imported date, source-added date, or published date.
- The date filter supports age-based pruning (e.g. "everything I saved before 2023") so Alexis can bulk-review or delete old saves. Realizes UJ-4.
- Results update to reflect the active filters.

#### FR-14: Text search
Alexis can search his Library by **title, description, channel name, and tags**.
**Consequences (testable):**
- A query matches Videos whose title, description, channel name, or tags contain it.
- Search runs globally across the Library, and can be scoped to the current view / an open Playlist.

### 4.6 Playback
**Description:** Alexis watches inside the app via an embedded player — deliberately **without** YouTube's sidebar, related videos, or autoplay-next (the doomscroll machinery) — with an *open in YouTube* escape hatch for background audio (e.g. cooking). Progress is tracked to auto-mark Watched. Realizes UJ-3.

**Functional Requirements:**

#### FR-15: Embedded playback with open-in-YouTube option
Alexis can play a Video in an embedded in-app player, or open it in YouTube.
**Consequences (testable):**
- The embedded player plays the Video without exposing YouTube's recommendation feed/autoplay-next within the app.
- An "open in YouTube" action opens the Video on YouTube.

#### FR-16: Auto-mark Watched at a threshold
A Video is marked Watched when Alexis views at least a threshold percentage of it.
**Consequences (testable):**
- Reaching the threshold (`[ASSUMPTION: ~90%]`) sets Watched and shows the badge.
- A Watched Video **stays in place** with the badge; it is not auto-archived or deleted.
- The user can also manually toggle Watched.

**Feature-specific NFRs:**
- **Known limitation (accepted):** the embedded web player **pauses when the phone locks or the tab loses focus**; continuous background/lock-screen playback is not supported in-app (it is YouTube-Premium-gated and blocked for embeds). The *open in YouTube* handoff covers the background-audio case. See §10.

### 4.7 Freshness & Curation
**Description:** The anti-rot system. Videos are Evergreen or Perishable (with a watch-by window); the app tracks age and proactively surfaces expired perishables for bulk watch-or-discard, keeping the library lean. Realizes UJ-4.

**Functional Requirements:**

#### FR-17: Set Freshness / shelf-life
Alexis can mark a Video Evergreen or Perishable with a watch-by window.
**Consequences (testable):**
- A Video's Freshness is Evergreen or Perishable(+window); default Evergreen.
- Freshness is settable in bulk (see FR-7).

#### FR-18: Surface expired perishables for pruning
The app proactively shows Perishable Videos past their window for bulk review. Realizes UJ-4.
**Consequences (testable):**
- Videos whose watch-by window has passed are collected into a review view/prompt.
- From that view Alexis can bulk discard or keep.
- `[ASSUMPTION: a freshness cue is shown on Video cards; exact form is a UX decision.]`

## 5. Non-Goals (Explicit)
- **Not a YouTube playlist manager.** The app does not aim to create/manage arbitrary playlists *on YouTube* (beyond reading/clearing `_Inbox` and optional migration cleanup). Organization lives in the app.
- **Not multi-user.** No sharing, collaboration, accounts-for-others, or public surfaces.
- **Not a YouTube-quota dashboard.** Exposing daily quota usage to the user is a non-goal; quota is an internal engineering constraint (§8), not a feature.
- **Not becoming a general video downloader / offline archive.** No downloading of video files; playback is via YouTube's player.
- **Not an algorithmic recommender.** The app does not auto-decide what he should watch or auto-categorize; suggestions are assistive only.

## 6. MVP Scope

### 6.1 In Scope
- YouTube auth with write scope (FR-1), designate `_Inbox` (FR-2).
- First-run migration with confirmed optional deletion (FR-3, FR-4).
- Weekly Inbox import → Uncategorized → auto-clear, with fast bulk categorization (FR-5, FR-6, FR-7).
- Organization model: Tags, Playlists, delete-from-Library, Channel & Length facets (FR-9–FR-12).
- Browse by combined facets + date filters + search over title/description/channel/tags (FR-13, FR-14).
- Embedded playback + open-in-YouTube + auto-Watched (FR-15, FR-16).
- Freshness/shelf-life + expired-perishable pruning (FR-17, FR-18).
- Responsive: desktop and mobile web both first-class.

### 6.2 Out of Scope for MVP
- **Categorization suggestions (FR-8)** — assistive nicety; defer until the manual triage loop is proven. `[NOTE FOR PM: if 100/week triage feels painful even with bulk tools, pull this forward — it's the pressure valve.]`
- **Native mobile app** — deferred; would only be reconsidered if background playback becomes a hard requirement (it isn't — §10).
- **Background/lock-screen in-app playback** — not supported; covered by open-in-YouTube.
- **Any multi-user / sharing capability.**

## 7. Success Metrics
Personal tool — success is behavioral, measured by Alexis's own use.

**Primary**
- **SM-1 — Doomscroll replaced:** Alexis opens *the app* (not YouTube's feed) to decide what to watch in the large majority of sessions. Validates UJ-3 / FR-13.
- **SM-2 — Inbox stays clean:** Watch Later / `_Inbox` is kept near-empty via regular triage (e.g. cleared roughly weekly). Validates UJ-2 / FR-5, FR-6.
- **SM-3 — Still using it after a month:** He hasn't abandoned the tool; the weekly loop stuck. Validates the whole product.

**Secondary**
- **SM-4 — Library stays lean:** Perishables get pruned rather than accumulating; the library trends toward "stuff I'll actually watch." Validates FR-18.

**Counter-metrics (do not optimize)**
- **SM-C1 — Not a hoarding contest:** Total library size is *not* a success signal. A bigger library is worse, not better, if it's unwatched. Counterbalances SM-2/SM-4 — don't let "capture everything" beat "watch and prune."
- **SM-C2 — Triage effort stays low:** If keeping the library organized starts costing more time than the doomscroll it replaced, that's failure. Counterbalances the manual-categorization design — protect throughput (FR-7).

## 8. Cross-Cutting NFRs
- **Triage throughput:** Bulk operations on ~100 items must feel fast (multi-select + bulk apply); no per-video modal gauntlet. This is load-bearing for SM-C2.
- **Responsive/both surfaces:** Desktop (keyboard-accelerated triage) and mobile (touch) are both first-class from day one.
- **YouTube API quota:** All import/clear/delete operations must stay within the app's YouTube Data API daily quota for a single user; batch and minimize write calls. `[ASSUMPTION: single-user volume (~100 videos/week) fits the default 10k-unit/day quota; validate the cost of list+delete per item.]`
- **Local durability:** Video metadata is stored in the app and must survive removal from YouTube playlists (the app is the sole home post-import).
- **Anti-doomscroll by design:** Surfaces should not reproduce infinite chronological feeds or expose YouTube's recommendation/autoplay machinery inside the app.
- **Security (inherited):** OAuth tokens stored securely per existing auth design; the new write scope raises the stakes of token handling. See `project-context.md`.

## 9. Assumptions Index
*Remaining unconfirmed inferences (several earlier assumptions were confirmed by Alexis and are now stated as fact in the body):*
- §4.3 FR-8 — Categorization suggestions are a nice-to-have; deferrable past MVP.
- §4.4 FR-9 — Tag merge is wanted to combat tag drift over time.
- §4.4 FR-11 — No undo/trash in MVP; deletion is immediate (revisit if it feels risky).
- §4.6 FR-16 — Watched threshold ≈ 90%.
- §4.7 FR-18 — Video cards show a freshness cue (exact UX TBD).
- §8 — Single-user volume (~100 videos/week) fits the default YouTube API daily quota (needs validation).

## 10. Platform Constraints & Risks
*The product sits on top of YouTube's API and player, which impose hard limits. These are decided, not open — but downstream work must respect them.*

- **R1 — Watch Later is inaccessible (decided).** The YouTube Data API cannot read/modify the Watch Later playlist. **Mitigation:** the user designates a normal `_Inbox` playlist as the capture target instead (FR-2). Requires a one-time habit change (save to `_Inbox`, not WL).
- **R2 — Background/lock-screen playback is not possible in-app (decided).** Embedded YouTube playback pauses on tab-blur/lock; continuous background audio is Premium-gated and blocked for embeds. **Mitigation:** accept the limitation; provide *open in YouTube* for the background-audio case (FR-15). Not an MVP requirement.
- **R3 — Write scope required.** Clearing `_Inbox` (FR-6) and deleting migrated playlists (FR-4) require YouTube **write** access, a broader OAuth scope than the current read-only build — larger consent surface and higher token-handling stakes.
- **R4 — API quota & write-cost.** Weekly import + per-item removal consumes quota; must be batched and validated against the daily limit (§8).
- **R5 — ToS/policy dependency.** The product depends on YouTube's continued API and embed-player policies; a future policy change (as with Watch Later) could force another on-ramp/playback rework. `[NOTE FOR PM: acceptable risk for a personal tool; noted for awareness.]`

## 11. Open Questions
1. **Watched → then what, longer term?** Watched videos stay with a badge (FR-16). Do they eventually clutter browse, and should there be an "archive watched" sweep later? (Deferred; revisit after real use.)
2. **Suggestion engine (FR-8):** if pulled into MVP, what powers suggestions — channel/title heuristics, or the user's own past tagging patterns?
4. **Quota cost per triage:** measure real API-unit cost of a 100-video import+clear cycle to confirm §8 assumption.
5. **Migration failure handling:** partial-import behavior and retry (FR-3) — define once the API cost/limits are known.
