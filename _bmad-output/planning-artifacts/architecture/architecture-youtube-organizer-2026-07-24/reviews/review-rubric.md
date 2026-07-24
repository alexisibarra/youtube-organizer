# Review — Good-Spine Rubric Walker

**Lens:** judge the spine against the good-spine checklist — divergence coverage, enforceable
rules, Deferred safety, verified tech, brownfield ratification, spec coverage, and whether every
dimension the altitude owns is decided, deferred, or an open question.

**Verdict:** PASS WITH FINDINGS — one silent dimension (critical), otherwise structurally sound.

---

## CRITICAL — a whole dimension is silent: durability of the sole copy

This is the sharpest hole in the spine, and it is silent rather than deferred.

The product's own premises stack into a data-loss exposure that nothing in the spine addresses:

- PRD §3: the Library is the canonical home; the app stores its own copy of all metadata.
- PRD §8 *Local durability*: "the app is the sole home post-import".
- FR-6: after import, the app **deletes the video from `_Inbox` on YouTube**.
- FR-4 (Phase 2): the app offers to **delete the migrated playlists from YouTube entirely**.
- AD-17: Phase 1 runs on localhost only — a `postgres_data` Docker volume on one laptop.

So by design the architecture destroys the upstream copy and concentrates the only remaining
copy in an unbacked local Docker volume. `docker compose down -v`, a disk failure, or a bad
migration loses the entire curated library — the exact asset the product exists to build, and the
one thing the PRD names as an NFR.

AD-17 handles the *security* consequences of localhost-only (`DEBUG`, `SECRET_KEY`,
`ALLOWED_HOSTS`) and is explicit about them. It says nothing about durability, and neither does
Deferred. A dimension the PRD names as a cross-cutting NFR should not be absent.

**Recommend:** a backup/restore invariant, even a minimal one (a `make backup` `pg_dump` target,
plus a rule that the volume is never destroyed casually and that FR-4's YouTube-side deletion is
gated on a verified backup). Given Phase 2 turns FR-4 into *irreversible* upstream deletion, this
should not wait for Phase 2 to be designed.

## HIGH — Deferred entry that could let units diverge

Every Deferred item was tested against "could two units diverge on this?". All are safe except:

**Package manager** — `Docs/FRONTEND-STACK.md` mandates pnpm with phantom-dependency discipline;
the repo uses npm; AD-2 removed the workspace motivation. Two stories adding dependencies under
different managers produce competing lockfiles, and the doc's phantom-dependency rule (a real
production-build failure mode) is meaningful under pnpm and meaningless under npm's hoisting. A
one-line answer resolves it; leaving it open invites a lockfile conflict on the first two
parallel PRs.

The rest are genuinely safe to defer: trash retention window, watched threshold value,
suggestion mechanism, availability cadence, archive-watched sweep — all product settings or
unbuilt features that no AD depends on.

## Checklist results

| Criterion | Result |
| --- | --- |
| Fixes the real divergence points for the level below | **Partial** — see the adversarial review; four constructible pairs remain open (query grammar, tag mutation semantics, tag identity, search-vector refresh site) |
| Every Rule is enforceable and prevents its stated divergence | **Mostly** — AD-1, AD-6, AD-7, AD-10, AD-13, AD-16, AD-18 are crisp and mechanically checkable in review. AD-4's "one documented grammar" is not enforceable as written because the grammar is absent. AD-11's refresh rule names no site |
| Nothing under Deferred lets two units diverge | **One exception** — package manager (above) |
| Named tech verified current | **Fails** — see the version review: the Django 6.0 pin is blocked by SimpleJWT, and the DRF pin is wrong |
| Ratifies rather than contradicts the brownfield codebase | **Pass, deliberately** — AD-13 contradicts the shipped frontend, but ratifies the *authoritative doc* that already disowns it, and says so. AD-14 correctly ratifies the real auth mechanism read from `middleware.py` and `google_auth_views.py` rather than reinventing it |
| Covers the driving spec's capabilities | **Pass** — all of FR-1…FR-19 appear in the Capability map, with Phase 2 marked |
| Parent spine conflicts | N/A — no parent spine |
| Every dimension decided, deferred, or open | **Fails on durability** (above). Operational envelope itself is properly handled by AD-17 + Deferred, which is the failure this check most often catches — that one is done well |

## Altitude check

Correct for feature altitude. The spine fixes what epics must share and stops there: it does not
specify serializer fields, component trees, or story-level detail. The Capability map bridges FRs
to owning ADs without expanding into per-story design. `EXPERIENCE.md` and `DESIGN.md` retain
ownership of UX decisions and the spine defers to them rather than re-deciding — correct
separation, and the DESIGN.md constraint entry in the memlog confirms it was deliberate.

## Notable strengths

- **AD-6 + AD-7 are the spine's best work.** Naming the transactional outbox imports a whole
  well-understood model, and the sequence diagram makes the ordering invariant unambiguous.
  Generalising it to FR-4 means Phase 2 inherits crash-safety for free.
- **AD-10 states the invariant rather than the schema** — "the dedupe check is the invariant, not
  the tables" is exactly the right altitude, and it closes a resurrection bug that would
  otherwise have been found in production.
- **AD-9 flags its own conflict with `EXPERIENCE.md`** instead of quietly overriding it. Same for
  AD-2 against `FRONTEND-STACK.md`. Divergences from source inputs are surfaced, not absorbed.
- **AD-18 is cheap foresight** — user-scoped uniqueness costs nothing now and saves a
  whole-schema migration later.
