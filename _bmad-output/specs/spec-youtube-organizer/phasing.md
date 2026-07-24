# Phasing — YouTube Organizer

Companion to `SPEC.md`. Scope is **phased, not cut**: phasing sequences capabilities, it deletes
none. Phase 1 exists to answer one question — *will Alexis actually use this instead of
doomscrolling?* Everything not needed to answer that is Phase 2.

`WORK-SPLIT.md` decomposes Phase 1 into epics `E1`–`E14` and fixes their dependency order; it is
the bridge into `bmad-create-epics-and-stories`. This file fixes *what is in which phase*.

## Phase 1 — Prove the premise

The smallest loop that replaces the doomscroll: **capture → organize → find → watch.**

| Capability | Scope in Phase 1 |
|---|---|
| CAP-1 | Auth with YouTube **write** scope, plus the read-only degraded mode |
| CAP-2 | `_Inbox` designation, persisted, changeable, with create-one fallback |
| CAP-5 | `_Inbox` import → Uncategorized, full local metadata, three-way dedupe |
| CAP-6 | Crash-safe auto-clear, orphan retry, surfaced failures |
| CAP-7 | Fast bulk categorization — Tags and discard (Freshness is Phase 2; endpoint schema only) |
| CAP-9 | Manage Tags — create, apply by delta, rename, remove. **Merge is Phase 2** |
| CAP-11 | Delete from Library, guarded and recoverable, with Trash and purge-to-tombstone |
| CAP-12 | Channel and Length as automatic facets |
| CAP-13 | Browse by combined facets. **The date-range portion is Phase 2** |
| CAP-14 | Text search over title, description, channel, tags |
| CAP-15 | Embedded playback + open-in-YouTube |
| CAP-16 | Contiguous-coverage auto-Watched |

Plus, as cross-cutting Phase 1 work: desktop and mobile web both first-class, and the whole
Phase-1 surface set in `EXPERIENCE.md § Information Architecture`.

## Phase 2 — Curation depth and convenience

Earned once Phase 1 proves the habit sticks. Deliberately not decomposed into epics.

| Capability | Why it waits |
|---|---|
| CAP-3, CAP-4 (migration) | Valuable, but the *weekly loop* is what proves the premise, not the one-time import. Reuses the Phase-1 outbox; **CAP-4's upstream deletion is gated on a recent successful backup** |
| CAP-10 (hand-built Playlists) | A curation-sequence nicety on top of facet browsing. The schema is anticipated in Phase 1 so this is additive; ordering and reorder are the new work |
| CAP-17, CAP-18 (Freshness + pruning) | Library-health features that matter more as the Library ages. Adds `freshness` params to the existing browse grammar |
| CAP-19 (Unavailable detection) | Gateway detection exists from Phase 1; the surface and the review sweep are the new work |
| CAP-13 date-range filters | Old-save cleanup needs history to be useful. Params are already reserved in the browse grammar |
| CAP-9 tag merge | Fights drift that only appears after months of tagging. Already assigned to a service operation |
| CAP-8 (suggestions) | **The triage pressure valve — see the pull-forward trigger below** |
| Production envelope | Settings split, env-driven secrets, `DEBUG` off, `ALLOWED_HOSTS`, TLS hostname, updated Google redirect URI, a retargeted `deploy.yml`, and scheduled/unattended sync — which needs an always-on host and therefore this whole dimension. **Revisit the moment anything is exposed beyond localhost**; the current dev defaults are unsafe on a real host |

### The CAP-8 pull-forward trigger

CAP-8 is the designed release valve for the triage bound, and it is **not** a wait-and-see item.
If Phase-1 triage of ~100 videos/week hurts even with bulk tools — i.e. if triage starts costing
more than the doomscroll it replaced — **pull CAP-8 forward from Phase 2 immediately.** That is
the PRD's own stated fallback and the reviewers' identified mitigation for counter-metric SM-C2.
No suggestion mechanism is committed until the valve is actually needed.

## Out of scope in every phase

- Native mobile app — reconsidered only if background playback becomes a hard requirement, which it is not.
- Background / lock-screen playback in-app — covered by open-in-YouTube.
- Any multi-user or sharing capability.
