---
id: SPEC-youtube-organizer
companions:
  - glossary.md
  - phasing.md
  - ../../planning-artifacts/architecture/architecture-youtube-organizer-2026-07-24/ARCHITECTURE-SPINE.md
  - ../../planning-artifacts/architecture/architecture-youtube-organizer-2026-07-24/WORK-SPLIT.md
  - ../../planning-artifacts/ux-designs/ux-youtube-organizer-2026-07-23/DESIGN.md
  - ../../planning-artifacts/ux-designs/ux-youtube-organizer-2026-07-23/EXPERIENCE.md
  - ../../project-context.md
  - ../../../Docs/FRONTEND-STACK.md
  - ../../../Docs/CI-AND-GITHUB-GATES.md
sources:
  - ../../planning-artifacts/prds/prd-youtube-organizer-2026-07-20/prd.md
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability only — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# YouTube Organizer

**Capability IDs map 1:1 onto the PRD's FR ids** — `CAP-n` *is* `FR-n`. `ARCHITECTURE-SPINE.md`'s `binds:` list and `WORK-SPLIT.md`'s epics both address FR ids; the mapping is what keeps them wired to this kernel.

**Precedence.** `ARCHITECTURE-SPINE.md` (invariants `AD-1`–`AD-20`) wins over `project-context.md` and over `Docs/` on any conflict — it was decided for this repo rather than mirrored from another project. `DESIGN.md` and `EXPERIENCE.md` own the visual and behavioral spines respectively and win over the mockups they reference.

## Why

**A pain to solve, for exactly one person.** Alexis saves a lot of interesting YouTube videos and they pile up. YouTube's tools for managing that pile are slow and shallow, so finding *the right thing to watch* means scrolling an endless chronological list — and that scrolling **is** the doomscroll. He ends up watching whatever sits near the top of Watch Later instead of what he actually wants.

YouTube Organizer flips this. It is a **personal curation library** where YouTube is only a *source*, not the home of organization. Videos are captured into the app, organized by intent — tags, channel, length, hand-built playlists — and pruned so the library stays lean. When he wants to watch, he browses by mood and context ("I have an hour for guitar," "a history podcast while I cook") and finds it in seconds, then watches inside the app, away from the recommendation machinery. Secondarily it is a **vision to realize**: his own tool, engineered properly — real architecture, tests, CI — for an audience of one.

## Capabilities

Phase assignment for every capability lives in `phasing.md`. Vocabulary (Library, Video, `_Inbox`, Uncategorized, Facet, Tag, Playlist, Freshness, Watched, Availability) is defined in `glossary.md` and is used with those exact meanings throughout.

- **CAP-1** *(= FR-1)*
  - **intent:** Alexis signs in with Google and grants the app read **and write** access to his YouTube playlists.
  - **success:** After consent the app can list playlists, read playlist items, and remove or modify items on his behalf. If only read scope is granted, CAP-6 and CAP-4 are disabled with a clear persistent notice and everything else still works.

- **CAP-2** *(= FR-2)*
  - **intent:** Alexis designates one of his normal YouTube playlists as the `_Inbox` capture target.
  - **success:** The app lists his playlists for selection; the choice is persisted in the database per user (never an env var or a hardcoded value), is changeable from the UI with effect on the next import, and the app can create an `_Inbox` playlist for him if he has no suitable one.

- **CAP-3** *(= FR-3)*
  - **intent:** Alexis imports selected pre-existing YouTube playlists, replicating their structure in the app.
  - **success:** All his playlists are listed for selection; importing one creates an app Playlist of the same name with membership preserved; completion shows a summary of playlists, videos and failures; re-running creates no duplicate Videos or Playlists.

- **CAP-4** *(= FR-4)*
  - **intent:** After a successful import, Alexis can delete the migrated playlists from YouTube.
  - **success:** Deletion is never automatic, each one is individually confirmed, declining leaves the YouTube playlist untouched, and a deletion only proceeds after its import is confirmed successful. Gated on a recent successful backup (see Constraints).

- **CAP-5** *(= FR-5)*
  - **intent:** Alexis imports new videos from the `_Inbox` into the Library, where — carrying no Tags and no Playlist membership — they appear as Uncategorized.
  - **success:** Each imported Video stores title, description, channel, thumbnail, duration and YouTube ID/URL locally, plus three distinct dates (imported, source-added, published). Dedupe tests active, soft-deleted **and** tombstoned videos by YouTube ID, so a previously deleted video is never resurrected from a still-populated `_Inbox`.

- **CAP-6** *(= FR-6)*
  - **intent:** After a Video is durably held locally, the app removes it from the `_Inbox` on YouTube.
  - **success:** Removal happens only after persist-and-verify, so a crash between steps never destroys the only copy. A video that failed import or verification is never removed. A video imported but not cleared is tracked as a pending-clear orphan, retried on the next sync, and never skipped as a duplicate. Removal failures surface in the UI.

- **CAP-7** *(= FR-7)*
  - **intent:** Alexis multi-selects Videos in Uncategorized and applies Tags, sets Freshness, or discards, in bulk.
  - **success:** One action applies one or more Tags to a whole selection; Freshness is settable the same way; discard is available on the selection. Filing a single Video takes ≤2 interactions. Desktop keyboard triage and mobile touch triage are both first-class. Partially-triaged state is normal and blocks nothing.

- **CAP-8** *(= FR-8)*
  - **intent:** The app suggests Tags or attributes for a Video, which Alexis confirms or ignores.
  - **success:** No suggestion is ever applied without an explicit user action.

- **CAP-9** *(= FR-9)*
  - **intent:** Alexis creates, applies, renames, removes and merges Tags.
  - **success:** A Video carries multiple Tags. Renaming updates every application. Concurrent tag edits **compose rather than overwrite** — a single-video edit never destroys tags a bulk apply just added. Two tags that differ only in case or surrounding whitespace are the same tag, and applying one returns the existing one rather than splitting it across two rows. Merge is the only operation that collapses two tags into one. (Mechanism: `AD-19`.)

- **CAP-10** *(= FR-10)*
  - **intent:** Alexis builds ordered Playlists, adds and removes Videos, and reorders them.
  - **success:** A Playlist has a user-defined order; a Video can belong to several. Removing a Video from a Playlist drops **only that membership** — the Video stays in the Library and in its other Playlists.

- **CAP-11** *(= FR-11)*
  - **intent:** Alexis deletes a Video from the Library — the only action that removes a Video from the app.
  - **success:** Deletion removes it from active views and from every Playlist and Tag, is available singly and in bulk, and bulk delete requires an explicit confirmation stating the count. Deleted Videos go to a recoverable Trash for a retention window, then purge to a tombstone. Deletion is app-side only and never touches YouTube.

- **CAP-12** *(= FR-12)*
  - **intent:** Channel and Length are captured automatically and usable as filters.
  - **success:** Every imported Video has its source channel and duration populated, and can be filtered by channel and by length range.

- **CAP-13** *(= FR-13)*
  - **intent:** Alexis browses the Library filtered by any combination of Tags, Channel, Length range, Freshness, Watched state and a date range.
  - **success:** Filters combine with AND (e.g. `tag=guitar` AND length ≤ 60 min AND watched=no) and results reflect the active set. Date filtering is a from–to window with either bound optional, selectable against imported, source-added or published date, which is what makes age-based pruning ("everything I saved before 2023") possible. **Every browse surface answers a combined query identically** — no two surfaces may disagree about what a given filter combination means. (Mechanism: `AD-4`.)

- **CAP-14** *(= FR-14)*
  - **intent:** Alexis searches the Library by title, description, channel name and tags.
  - **success:** A query matches any of those four fields, runs globally, and can be scoped to the current view or an open Playlist. Search composes with the CAP-13 facets rather than being a separate mode, and stays correct after bulk tagging — the highest-volume operation in the product — so a Video is always findable by the tags it actually carries. (Mechanism: `AD-11`.)

- **CAP-15** *(= FR-15)*
  - **intent:** Alexis plays a Video in an embedded in-app player, or opens it on YouTube.
  - **success:** The embedded player exposes no recommendation feed and no autoplay-next inside the app; an open-in-YouTube action hands off to YouTube for the background-audio case.

- **CAP-16** *(= FR-16)*
  - **intent:** A Video is marked Watched once Alexis has actually watched enough of it.
  - **success:** The client measures **contiguous covered duration**, never furthest position reached, so seeking to the end does not mark a video watched. Crossing the configurable threshold sets Watched and shows the badge; the Video stays exactly where it was; Watched is also manually togglable. Playback position is not persisted — there is no resume feature.

- **CAP-17** *(= FR-17)*
  - **intent:** Alexis marks a Video Evergreen or Perishable with a watch-by window.
  - **success:** Freshness defaults to Evergreen, and is settable in bulk via CAP-7.

- **CAP-18** *(= FR-18)*
  - **intent:** The app proactively surfaces Perishable Videos past their window for bulk review.
  - **success:** Expired Videos are collected into a review surface from which Alexis can bulk discard or keep.

- **CAP-19** *(= FR-19)*
  - **intent:** The app detects Videos YouTube no longer serves and flags them, so a sole-home Library does not silently fill with dead links.
  - **success:** A Video that is deleted, private, region-blocked or removed is marked Unavailable and visibly flagged; Unavailable Videos are filterable and reviewable alongside expired perishables; attempting to play one shows a clear message with open-in-YouTube and delete actions, never a broken player.

## Constraints

- **Triage bound.** Filing a single Video takes **≤2 interactions**; applying a Tag or attribute to a multi-selection is **a single action**. No per-video modal gauntlet. If triage costs more than the doomscroll it replaced, the product has failed — this is the binding form of counter-metric SM-C2.
- **Incremental by design.** The app must never require Uncategorized to be emptied. A partially-triaged Library is a first-class state: browse, search and playback work fully over whatever is already organized, so skipping triage for weeks degrades findability of *new* saves only. No "mark as done" step exists.
- **Anti-doomscroll subtraction.** Banned everywhere: infinite scroll (pagination or explicit load-more only), autoplay-next including inside hand-built playlists, a right rail at any breakpoint (absent, not collapsed), recommendation/subscription/Shorts/Home surfaces, a badge count on Uncategorized, and a single-column full-width feed on phones (two columns minimum — that shape *is* the doomscroll). Also banned: hover-only affordances, modal stacks deeper than one level, and suppressible destructive confirmations.
- **Persist and verify before mutating the source.** The order is fetch → persist locally → verify → enqueue the upstream clear. Dedupe suppresses re-import, never re-clear. (`AD-7`)
- **Every outbound YouTube mutation goes through a transactional outbox.** App state and the intent to mutate YouTube commit in the same database transaction; a separate drain is the only caller of the gateway's write methods. Nothing issues a YouTube write inline. (`AD-6`)
- **Watch Later is inaccessible** via the YouTube Data API, so a user-designated `_Inbox` playlist is the only viable capture on-ramp. Decided, not open — it costs a one-time habit change.
- **Background/lock-screen playback is impossible in-app.** The embed pauses on tab-blur and lock; continuous audio is Premium-gated and blocked for embeds. Accepted; open-in-YouTube covers the case. Stated in Settings as fact, never surfaced as an error.
- **The embed leaks recommendations on its own end screen** and `rel=0` has not suppressed that since 2018. End-card interception was considered and **declined**; the leak stands as an accepted limitation at the moment of peak doomscroll vulnerability, and is worth revisiting if it pulls him back into scrolling.
- **YouTube API quota bounds everything.** All import/clear/delete work must fit the single-user daily quota; writes are batched and minimized. Exhaustion is detected **reactively** from the API's `quotaExceeded` error, never predicted — stamp the run, commit what is already done, resume from the same point next run, and keep the banner up until it is explicitly acknowledged.
- **The app is the sole home of the library after import**, so durability is non-negotiable: a `make backup` target and a verified restore path exist from the first data-model story, the Postgres volume is named and never destroyed by any routine command, and **CAP-4 — the only irreversible upstream operation — is offered only when a successful backup exists within a defined recency window.** Import and inbox-clear are not gated; gating the weekly loop would break it.
- **Both surfaces are first-class from day one.** Desktop is keyboard-accelerated, mobile is touch; neither is a degraded copy. No native app in any phase.
- **WCAG 2.2 AA across both surfaces and both color modes.** No state conveyed by color alone (selection is outline + checkmark, status is scrim + badge, active nav is tint + edge bar). Focus differs from selection by *style* — dashed vs solid — not by width. Single-key shortcuts ship with a disable toggle, remapping, and focus scoping. Target size ≥24×24. Single-user does not lower this bar: a personal tool is used for years, tired, one-handed, at 1am.
- **Single user, but never schema-deep.** No sharing, collaboration or public surface in any phase — yet every user-owned entity carries a user FK, every query filters on it, and uniqueness is scoped per user, so the assumption is never load-bearing in the data model.
- **Phase 1 targets localhost only.** The dev `docker-compose.yml` is the only environment; `DEBUG=True`, a hardcoded `SECRET_KEY` and empty `ALLOWED_HOSTS` are accepted **only** because nothing is deployed. No story may assume a production environment exists, and the full production envelope must land as its own work before any non-local exposure.
- **Phase 1 sync is user-triggered only** — a "Sync now" action and the idempotent `manage.py sync_inbox`. No scheduler, cron, worker daemon or broker.
- **Write scope raises the stakes on token handling.** Adding YouTube write to the OAuth scope set means a leaked token can now *destroy* the user's source data, not just read it. Google and database credentials come from the environment and are never hardcoded or committed; the auth invariants (JWT in an HttpOnly cookie, credentialed CORS against a single origin, `SameSite=None; Secure`) are not relaxed, because the cross-port OAuth flow depends on them.
- **The shipped `frontend/src` prototype is not precedent.** New surfaces are built to `Docs/FRONTEND-STACK.md` and the UX spines; legacy files are deleted when the surface replacing them lands. No long-lived hybrid, no in-place migration.
- **`AD-1`–`AD-20` in `ARCHITECTURE-SPINE.md` are binding**, win over `project-context.md` and `Docs/` on conflict, and are cited by id in PRs.
- **Never add AI or bot attribution to any artifact** in this repository — commit messages, PR titles and bodies, issue and review comments, code comments, changelogs, generated docs. No exceptions and no case-by-case judgement about whether a surface counts.

## Non-goals

- **Not a YouTube playlist manager.** No creating or managing arbitrary playlists *on YouTube* beyond reading and clearing `_Inbox` and the optional migration cleanup. Organization lives in the app.
- **Not multi-user.** No sharing, collaboration, accounts for others, or public surfaces.
- **Not a YouTube-quota dashboard.** Quota is an internal engineering constraint, not a user-facing feature.
- **Not a downloader or offline archive.** No video files are downloaded; playback is always through YouTube's player.
- **Not an algorithmic recommender.** The app never auto-decides what to watch and never auto-categorizes; suggestions are assistive and always confirmed.
- **No native mobile app**, in any phase — reconsidered only if background playback ever becomes a hard requirement, which it is not.
- **No in-app background or lock-screen playback.** Covered by open-in-YouTube.

## Success signal

Alexis opens *this app*, not YouTube's feed, to decide what to watch in the large majority of sessions; his `_Inbox` is cleared roughly weekly and stays near-empty; and a month in, he has not abandoned the tool. Concretely: on a random Tuesday he goes from opening the app to knowing what he is watching in **under ten seconds**, without scrolling past anything, because the set he drilled into was finite and *ended*.

Secondarily, the library trends toward "stuff I'll actually watch" — perishables get pruned rather than accumulating.

Two counter-signals bound this and are as binding as the goals: **library size is not a success metric** — a bigger library is worse, not better, if it is unwatched; and **if keeping the library organized costs more time than the doomscroll it replaced, the product has failed** (the designed response is to pull CAP-8 forward — see `phasing.md`).

## Assumptions

- Tag merge (CAP-9) is wanted to fight the tag drift that only appears after months of tagging.
- The Watched threshold defaults to ~90%. The *measurement* is fixed (contiguous coverage); the *number* is a Settings value.
- Availability (CAP-19) is checked opportunistically at play time and during sync rather than by background polling. The cadence is unset pending real quota measurements.
- Single-user volume (~100 videos/week) fits the default 10k-unit daily YouTube Data API quota. Unvalidated — and it underwrites the entire weekly loop.
- The product rests on YouTube's continued API and embed-player policies. A future policy change — as already happened with Watch Later — could force another capture on-ramp or playback rework. Accepted risk for a personal tool; recorded so it is not a surprise.
- The frontend pin block inherited from `Docs/FRONTEND-STACK.md` records another project's versions at a past date. The one pin that was checked is already behind its LTS line, so the rest are treated as suspect and must be re-verified before the first frontend PR — amending the doc, not the code, where a pin moves.

## Open Questions

- What is the real YouTube API unit cost of a 100-video import-plus-clear cycle? This validates or breaks the quota assumption the weekly loop rests on.
- Longer term, do Watched videos clutter browse enough to warrant an archive-watched sweep? (Deferred until real use; Watched is derived, so a later lens costs nothing.)
- If CAP-8 suggestions are pulled forward, what powers them — channel/title heuristics, or Alexis's own past tagging patterns?
- How should a partial migration import (CAP-3) fail and retry? Definable once API cost and limits are known.
- Removing the last Tag or Playlist membership from a Video silently drops it back into Uncategorized, because that state is derived. Is the silent fallback wanted, or is an explicit "keep, leave untagged" state needed? The latter would require materialising a stored state and a new `AD`.
- How long is the Trash retention window? A product setting, not an architectural invariant — any value works.
