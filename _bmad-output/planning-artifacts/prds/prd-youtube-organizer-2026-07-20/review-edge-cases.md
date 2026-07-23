# Edge-Case Review — YouTube Organizer PRD

Method: walked every branching path, boundary, and state transition the PRD implies. Reports **only unhandled cases** — situations where the PRD does not say what happens. Ranked most-impactful first. Cases the PRD already resolves are excluded.

---

1. **Deleted video resurrects on next import**
   - **Touches:** FR-5 (dedup "already in Library"), FR-6, FR-11 (delete app-side only, no YouTube touch).
   - **Scenario:** During triage Alexis discards a junk video (FR-7/FR-11). If that video is still present in `_Inbox` on YouTube — because its FR-6 removal previously failed, or because he deletes it before the clear runs, or because he re-saves it next week — the next import sees it. Dedup is keyed on "is it in the Library." The deleted video is no longer in the Library, so it is re-imported and lands in Uncategorized again.
   - **Why unhandled:** There is no tombstone / "deleted, do not re-import" record. Delete is defined as purely app-side with no memory that a given YouTube ID was deliberately rejected. Deliberately discarded videos silently come back.

2. **Imported-but-not-cleared: orphaned `_Inbox` items with no retry**
   - **Touches:** FR-5, FR-6.
   - **Scenario:** A video imports into the Library successfully, then the YouTube removal (FR-6) fails (network blip, token refresh, quota). The video is now in the Library **and** still in `_Inbox`. On the next import run, FR-5 skips it as a duplicate ("already in Library, not re-imported"). Because FR-6 removal is described as happening "after a Video is imported," and this run performs no import for that video, the stale `_Inbox` item is never retried.
   - **Why unhandled:** FR-6 says failures are "surfaced, not silent," but the PRD defines no retry, no reconciliation pass, and no idempotent "clear any Library-known item still in `_Inbox`" step. `_Inbox` slowly fills with already-imported ghosts — directly defeating SM-2.

3. **Import commits but removal was already sent — or removal succeeds and import fails: no atomicity/ordering defined**
   - **Touches:** FR-5, FR-6.
   - **Scenario:** If removal is issued before the local write is durably committed and the app crashes in between, the video is gone from `_Inbox` on YouTube but never persisted locally → permanent loss (YouTube was the only source and it's now cleared). The reverse (import commits, removal never sent) is case #2.
   - **Why unhandled:** The PRD states the two operations as a sequence but never specifies ordering guarantees, transactional boundaries, or a recovery path for a crash between the two. "Local durability" NFR (§8) protects metadata after import but says nothing about the import↔clear window.

4. **Bulk library delete has no confirmation and no undo**
   - **Touches:** FR-7 (discard in bulk), FR-11 (`[ASSUMPTION: no undo/trash]`), FR-13 (date-range pruning).
   - **Scenario:** In a multi-select triage session, one wrong click on "discard" permanently destroys the whole selection (could be ~100 videos). Same risk from a facet/date filter like "everything before 2023" → select all → delete. Notably, FR-4 *requires* explicit per-action confirmation to delete a YouTube **playlist**, but no equivalent guard exists for permanently deleting **videos from the Library** in bulk.
   - **Why unhandled:** The PRD mandates confirmation only for the reversible YouTube-side deletion, while the irreversible app-side bulk delete (no trash, no undo) has no confirmation requirement at all. The asymmetry is backwards relative to blast radius.

5. **Video becomes unavailable on YouTube after import (deleted / private / region-blocked / taken down)**
   - **Touches:** Glossary (Library is sole home), FR-15 (embedded playback), FR-16 (auto-Watched).
   - **Scenario:** A video is imported and organized; later it is removed, set private, blocked, or region-locked on YouTube. Its metadata still lives in the Library and it still appears in browse/facets. When Alexis picks it, the embedded player can't play it, and it can never reach the Watched threshold.
   - **Why unhandled:** The PRD has no concept of availability re-validation, a "dead/unplayable" state, a badge, or any behavior for the player when the underlying video is gone. The library-as-sole-home model breaks precisely because playback still depends on YouTube.

6. **Removing the last tag/playlist silently drops an organized (even Watched) video back into Uncategorized**
   - **Touches:** Glossary (Uncategorized = no Tags AND no Playlist; "self-clearing"), FR-9, FR-10.
   - **Scenario:** Alexis organized a video months ago (tagged it, maybe watched it). He later removes its one remaining tag, or removes it from its only playlist (FR-10 explicitly keeps it in the Library). It now has no Tags and no Playlist → it silently reappears in the Uncategorized triage view, mixed in with this week's fresh inbox catch. A Watched video can land back in the "un-triaged" pile.
   - **Why unhandled:** The Glossary defines Uncategorized purely by current facet emptiness with no notion of "was previously organized." There is no distinction between never-triaged and de-organized. The PRD never says whether this fallback is intended or how it should read to the user.

7. **Setting Freshness or Length during triage does NOT clear Uncategorized**
   - **Touches:** Glossary (Uncategorized = no Tags AND no Playlist), FR-7, FR-17.
   - **Scenario:** FR-7 lets Alexis bulk-apply Tags, **Length/Format**, and **Freshness** and discard. But Uncategorized clears only on first Tag or Playlist membership. If during triage he sets Freshness = Perishable(+window) and a Length/format on a batch but doesn't add a Tag or Playlist, those videos remain in Uncategorized — they look un-triaged despite being processed.
   - **Why unhandled:** The Uncategorized definition ignores two of the attributes the triage flow (FR-7) is explicitly built to set. The PRD never reconciles "video I gave attributes to" with "video still shows as Uncategorized."

8. **Perishable window has no defined anchor date**
   - **Touches:** FR-17, FR-18, Glossary (Freshness), FR-5 (three stored dates).
   - **Scenario:** A "watch-by window" (e.g. 14 days) must count from some date, but the PRD stores three (published, source-added, imported) and never says which anchors the window. A video *published* three years ago but *imported* today: if the window counts from published date it is instantly expired and gets swept by FR-18 on arrival; if from imported date it has its full window. Opposite outcomes.
   - **Why unhandled:** FR-17/FR-18 speak of "past their window" without defining the window's origin. Expiry — and therefore what FR-18 sweeps — is ambiguous.

9. **Expired-perishable sweep collides with hand-built Playlists and Watched state**
   - **Touches:** FR-18 (bulk discard expired), FR-11 (delete removes from every Playlist), FR-16 (Watched stays in place).
   - **Scenario:** A Perishable video is a deliberately-ordered member of "Guitar Course Vol.1." Its window passes → FR-18 surfaces it → Alexis bulk-discards → FR-11 rips it out of the curated playlist. Separately, a Perishable video he already *watched* — is it still surfaced for pruning? Surfacing already-watched expired videos wastes triage; not surfacing them may strand them.
   - **Why unhandled:** FR-18 defines the expired set purely by "window passed," with no exclusion for Watched videos and no warning/protection for videos that are curated into Playlists. The bulk-discard blast radius into hand-built sequences is unaddressed.

10. **User deletes / loses the designated `_Inbox` playlist on YouTube**
    - **Touches:** FR-2 (selection persisted in DB), FR-5.
    - **Scenario:** The `_Inbox` selection is stored per-user in the app DB. Alexis later deletes that playlist on YouTube (or it's the very playlist he migrated and then deleted via FR-4). The persisted selection now points at a non-existent playlist. Next import: the read fails.
    - **Why unhandled:** The PRD never covers a dangling `_Inbox` reference — no re-designation prompt, no detection, no distinction between "empty inbox" and "inbox gone." FR-4 (delete migrated playlists) can itself create this state if the migrated playlist is also the designated `_Inbox`.

11. **Token/write-scope revoked externally, or expires mid-triage of 100 items**
    - **Touches:** FR-1, FR-6, §8 (quota), R3.
    - **Scenario:** FR-1 handles the *initial consent* case (only read granted → write features disabled with a message). But if Alexis revokes access from his Google account **after** consent, or the token expires and refresh fails **during** a bulk import+clear of ~100 videos, write calls start failing partway through. Some videos imported+cleared, some imported-not-cleared, some untouched.
    - **Why unhandled:** FR-1's degraded-mode logic is evaluated only at sign-in, not on mid-session revocation/expiry. There is no defined resumable/partial state for a bulk operation that loses write scope halfway. Combines with #2 to leave the inbox inconsistent.

12. **Quota exhaustion mid-cycle leaves import/clear half-done**
    - **Touches:** §8, R4, FR-5, FR-6, Open Q4 (cost unmeasured).
    - **Scenario:** §8 only *assumes* 100 videos/week fits the 10k/day quota, and Open Q4 admits the real cost is unmeasured. A list+per-item-delete cycle can exhaust quota partway. FR-6 surfaces the removal failure, but the run is now partial: N imported+cleared, M imported-not-cleared, the rest not imported.
    - **Why unhandled:** No batching contract, no "resume where quota ran out," no idempotent re-run guarantee that finishes the leftovers without duplicating or skipping the un-cleared ones. The quota assumption failing is treated as an open question, not a handled path.

13. **Same video appears twice in `_Inbox` (duplicate playlist items)**
    - **Touches:** FR-5 (dedup by video ID), FR-6 (remove "the video").
    - **Scenario:** YouTube allows the same video ID to sit in a playlist twice as two distinct playlist-item entries. Dedup on import (by video ID) creates one Library video. FR-6 removal targets "the video" — but there are two `_Inbox` entries with different playlistItem IDs. Removing one leaves the second behind.
    - **Why unhandled:** The PRD models `_Inbox` clearing per-video, not per-playlist-item. A duplicated entry survives the clear and reappears as an uncleared inbox item every run.

14. **Duplicate re-saved to `_Inbox` is never cleared**
    - **Touches:** FR-5 (not re-imported), FR-6 (clear "after import").
    - **Scenario:** Alexis re-saves a video he already imported weeks ago into `_Inbox`. FR-5 correctly does not re-import it. But FR-6's clear is gated on a successful *import* — and no import happens for a duplicate. So the duplicate sits in `_Inbox` uncleared.
    - **Why unhandled:** The PRD ties inbox-clearing to the import event rather than to "this video is known to the Library." Already-known videos re-entering the inbox are neither imported nor cleared — inbox clutter that never resolves.

15. **Migration is defined as strictly one-time — no path for later playlists**
    - **Touches:** Glossary (Migration = "one-time first-run"), FR-3, UJ-1.
    - **Scenario:** After first run, Alexis creates or accumulates new YouTube playlists he'd like to bring in (e.g. a friend shares one, or he organizes a batch on YouTube). Migration is explicitly one-time/first-run.
    - **Why unhandled:** There is no re-run or incremental "import these additional playlists later" entry point. The only ongoing on-ramp is `_Inbox`, which imports loose videos into Uncategorized and does not replicate playlist structure. Structure-preserving import is a one-shot the user can't repeat.

16. **Migration re-run vs. renamed/edited playlists — dedup identity conflicts**
    - **Touches:** FR-3 ("no duplicate Playlists; dedupe by playlist identity"), FR-9/FR-10 (user can rename).
    - **Scenario:** A re-run dedups by YouTube playlist identity. But between runs the playlist may have been renamed on YouTube, or Alexis may have renamed the *app* Playlist, or added/removed videos in either place. Re-import: does it rename the app Playlist back? Re-add videos the user deliberately removed? Merge or diverge?
    - **Why unhandled:** FR-3 guarantees no duplicates but says nothing about conflict resolution when the two sides have diverged. Sync direction and precedence are undefined. (Related: Open Q5 defers partial-import/retry, but that's flagged; the divergence-merge case is not even flagged.)

17. **`_Inbox` or a migrated playlist changes between listing and import**
    - **Touches:** FR-3, FR-5, Open Q5.
    - **Scenario:** The app lists playlist contents, Alexis makes a selection, and while the import runs (or between list and confirm) videos are added/removed on YouTube. The app imports a stale snapshot; newly-added items are missed, and removed items may be imported then fail to clear.
    - **Why unhandled:** Open Q5 defers *migration* partial-import handling, but the same time-of-check/time-of-use gap applies to the recurring `_Inbox` import (FR-5), which is core-loop and not covered by that open question.

18. **Watched auto-marks from scrubbing / trivially-short videos**
    - **Touches:** FR-16 (`[ASSUMPTION: ~90%]`).
    - **Scenario:** Alexis drags the scrubber past 90% to sample the end, or opens a 20-second clip — the threshold trips instantly and marks it Watched without him actually watching. Conversely, "viewed ≥ threshold %" is ambiguous about whether it means cumulative watched time vs. furthest position reached.
    - **Why unhandled:** FR-16 specifies only a percentage threshold with no definition of *how* progress is measured (position reached vs. seconds actually played), no minimum-duration guard, and no anti-seek handling. Watched state (a browse facet, FR-13) becomes unreliable.

19. **`_Inbox` creation when a playlist named `_Inbox` already exists**
    - **Touches:** FR-2 ("if he has no suitable playlist, the app can create an `_Inbox`").
    - **Scenario:** Alexis asks the app to create the `_Inbox` playlist, but one named `_Inbox` (or the app already created one earlier) already exists on YouTube. YouTube permits duplicate playlist names.
    - **Why unhandled:** FR-2 has no collision check; it could create a second `_Inbox`, leaving two and an ambiguous capture target.

20. **Scale: thousands of results vs. the anti-doomscroll "no infinite feed" NFR**
    - **Touches:** §8/§295 (anti-doomscroll: no infinite chronological feeds), FR-13, FR-14, FR-9 (rename/merge across thousands).
    - **Scenario:** A broad filter (or an unfiltered Library, or a tag applied to thousands) returns thousands of results. The app must display them, but the anti-doomscroll NFR forbids reproducing an infinite chronological feed.
    - **Why unhandled:** The PRD gives no pagination, cap, or "narrow your filter" behavior, and no reconciliation between "show large result sets" and "don't build a scrollable feed." Large-set browse UX is undefined. (Tag rename/merge over thousands, FR-9, is a related bulk-performance path with no defined behavior.)

21. **Empty / zero states across the app**
    - **Touches:** FR-3, FR-5, FR-13, FR-18, UJ-2.
    - **Scenario:** First run with **no** YouTube playlists at all (migration list empty); an empty `_Inbox` on import; zero expired perishables for the FR-18 prompt; a filter combination that matches nothing; an empty Library on day one.
    - **Why unhandled:** The PRD describes populated happy paths only. None of these zero-count states have defined messaging or behavior. (Lower impact, but genuinely unspecified.)

22. **Concurrent desktop + mobile sessions on the same single user**
    - **Touches:** §8 (both surfaces first-class), FR-7.
    - **Scenario:** The single user triages on his phone and desktop at the same time (both are first-class). Two sessions bulk-edit or delete overlapping selections, or one runs an import while the other browses.
    - **Why unhandled:** "Single-user" removes multi-*account* concerns but not multi-*session* concurrency. The PRD defines no conflict/last-write-wins/refresh behavior for simultaneous sessions.
