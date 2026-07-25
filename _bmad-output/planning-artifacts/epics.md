---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
inputDocuments:
  - _bmad-output/specs/spec-youtube-organizer/SPEC.md
  - _bmad-output/specs/spec-youtube-organizer/phasing.md
  - _bmad-output/specs/spec-youtube-organizer/glossary.md
  - _bmad-output/planning-artifacts/architecture/architecture-youtube-organizer-2026-07-24/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/architecture/architecture-youtube-organizer-2026-07-24/WORK-SPLIT.md
  - _bmad-output/planning-artifacts/ux-designs/ux-youtube-organizer-2026-07-23/DESIGN.md
  - _bmad-output/planning-artifacts/ux-designs/ux-youtube-organizer-2026-07-23/EXPERIENCE.md
  - _bmad-output/planning-artifacts/prds/prd-youtube-organizer-2026-07-20/prd.md
  - _bmad-output/project-context.md
  - Docs/FRONTEND-STACK.md
  - Docs/CI-AND-GITHUB-GATES.md
scope: Phase 1
---

# YouTube Organizer - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for **YouTube Organizer — Phase 1**,
decomposing the requirements from the SPEC kernel (`SPEC.md`), the UX spines (`DESIGN.md`,
`EXPERIENCE.md`), and the Architecture spine (`ARCHITECTURE-SPINE.md`) into implementable stories.

**Scope boundary.** Only **Phase 1** capabilities are decomposed here, per `phasing.md`. Phase 2
FRs (FR-3, FR-4, FR-8, FR-10, FR-17, FR-18, FR-19) are out of scope and appear only where a Phase 1
epic must *anticipate* them (schema headroom), never as deliverable stories.

**Epic boundaries are fixed.** `WORK-SPLIT.md` fixes the 14 epics (E1–E14) and their dependency
order. This breakdown adopts those boundaries verbatim and decomposes each into stories — it does
not re-split the work.

**Precedence.** `ARCHITECTURE-SPINE.md`'s `AD-1`–`AD-20` are binding and win over `project-context.md`
and `Docs/` on conflict. Cite `AD-n` ids in PRs. Capability IDs map 1:1 onto FR ids (`CAP-n` *is* `FR-n`).

## Requirements Inventory

### Functional Requirements

**Phase 1 (in scope) — 12 FRs.** `CAP-n` = `FR-n`; Phase-1 scope per `phasing.md`.

- **FR-1** — Sign in with Google and grant **read + write** access to YouTube playlists. After consent
  the app can list playlists, read items, and remove/modify items. *Read-only degraded mode:* if only
  read scope is granted, FR-6 (inbox clear) and FR-4 (playlist deletion, Phase 2) are disabled with a
  clear persistent notice; everything else works.
- **FR-2** — Designate one normal YouTube playlist as the `_Inbox` capture target. Listing for
  selection; choice **persisted per user in the database** (never env var / hardcode); changeable from
  the UI with effect on next import; app can **create an `_Inbox`** if the user has none suitable.
- **FR-5** — Import new videos from `_Inbox` into the Library, where — with no Tags and no Playlist
  membership — they appear as **Uncategorized**. Each Video stores title, description, channel,
  thumbnail, duration, YouTube ID/URL, and **three distinct dates** (imported, source-added, published).
  Dedupe tests active, soft-deleted **and** tombstoned videos by YouTube ID.
- **FR-6** — After a Video is durably held locally, remove it from `_Inbox` on YouTube. Removal only
  after **persist-and-verify** (crash-safe); a failed import/verify is never removed; imported-but-not-
  cleared videos are tracked as **pending-clear orphans**, retried next sync, never skipped as
  duplicates; removal failures surface in the UI.
- **FR-7** — Multi-select Videos in Uncategorized and apply **Tags** or **discard**, in bulk. One action
  applies one-or-more Tags to a whole selection; discard available on the selection. Filing a single
  Video ≤2 interactions. Desktop keyboard triage **and** mobile touch triage both first-class.
  Partially-triaged state is normal and blocks nothing. *(Freshness bulk is Phase 2 — endpoint schema only.)*
- **FR-9** — Manage Tags: **create, apply (by delta), rename, remove**. A Video carries multiple Tags.
  Renaming updates every application. Concurrent tag edits **compose, not overwrite**. Tags differing
  only in case/whitespace are the same tag (normalised identity). *(Merge is Phase 2.)*
- **FR-11** — Delete a Video from the Library (the only action removing a Video from the app). Removes
  it from active views, every Playlist and every Tag; available singly and in bulk; bulk delete requires
  explicit confirmation **stating the count**. Deleted Videos go to a recoverable **Trash** for a
  retention window, then **purge to a tombstone**. App-side only — never touches YouTube.
- **FR-12** — Channel and Length captured automatically and usable as filters. Every imported Video has
  source channel and duration populated; filterable by channel and by length range.
- **FR-13** — Browse the Library filtered by any combination of Tags, Channel, Length range, Watched
  state *(and Freshness + date range — Phase 2)*. Filters combine with **AND**. Every browse surface
  answers a combined query **identically** (AD-4). *(Date-range portion is Phase 2.)*
- **FR-14** — Search the Library by **title, description, channel name and tags**. Runs globally,
  scopable to current view / open Playlist. Composes with FR-13 facets; stays correct after bulk
  tagging (AD-11).
- **FR-15** — Play a Video in an **embedded in-app player**, or open it on YouTube. The embed exposes no
  recommendation feed and no autoplay-next inside the app; open-in-YouTube handles the background-audio case.
- **FR-16** — Mark a Video **Watched** once enough is actually watched. Client measures **contiguous
  covered duration** (never furthest position); crossing the configurable threshold sets Watched and
  shows the badge; the Video stays in place; Watched is manually togglable; playback position is **not**
  persisted (no resume).

**Phase 2 (out of scope, listed for traceability):** FR-3 (playlist migration), FR-4 (post-migration
YouTube deletion, backup-gated), FR-8 (tag suggestions — *pull-forward valve if triage bound slips*),
FR-10 (hand-built ordered Playlists), FR-17 (Freshness), FR-18 (expired-perishable review), FR-19
(Unavailable detection surface).

### NonFunctional Requirements

Drawn from `SPEC.md § Constraints` and `§ Success signal`, plus the UX Accessibility Floor.

- **NFR-1 (Usability — the triage bound).** Filing a single Video ≤ **2 interactions**; applying a Tag
  or attribute to a multi-selection is **a single action**. No per-video modal gauntlet. Load-bearing
  for counter-metric SM-C2 — if triage costs more than the doomscroll, the product has failed.
- **NFR-2 (Usability — incremental).** The app must **never require Uncategorized to be emptied**. A
  partially-triaged Library is a first-class state; browse, search and playback work fully over whatever
  is already organized. No "mark as done" step. No badge count on Uncategorized.
- **NFR-3 (Product identity — anti-doomscroll subtraction).** Banned everywhere: infinite scroll
  (pagination / explicit load-more only), autoplay-next (incl. inside playlists), a right rail at any
  breakpoint (absent, not collapsed), recommendation/subscription/Shorts/Home surfaces, single-column
  full-width feed on phones (two columns minimum), hover-only affordances, modal stacks deeper than one
  level, suppressible destructive confirmations.
- **NFR-4 (Reliability — crash safety).** Fetch → persist locally → verify → enqueue the upstream clear
  (AD-7). Every outbound YouTube mutation goes through a transactional outbox (AD-6); a crash between
  local commit and remote call never loses the only copy or the owed clear.
- **NFR-5 (Reliability — quota).** All import/clear/delete work must fit the single-user daily YouTube
  Data API quota; writes batched and minimized. Exhaustion detected **reactively** from `quotaExceeded`,
  never predicted — stamp the run, commit done work, resume next run; banner persists until acknowledged.
- **NFR-6 (Durability — the library is the sole home).** A `make backup` target (timestamped `pg_dump`)
  and a **verified restore path** exist from the first data-model story; the Postgres volume is named and
  never destroyed by any routine command. FR-4 (Phase 2, the only irreversible upstream op) is gated on
  a recent successful backup. Import and inbox-clear are **not** gated. (AD-20)
- **NFR-7 (Accessibility — WCAG 2.2 AA).** Across both surfaces (desktop + mobile web) and both color
  modes. No state conveyed by color alone (selection = outline + checkmark; status = scrim + badge; active
  nav = tint + edge bar). Focus differs from selection by **style** (dashed vs solid), not width.
  Single-key shortcuts ship with disable toggle, remap, and focus scoping (2.1.4). Target size ≥24×24.
- **NFR-8 (Multi-surface parity).** Desktop keyboard-accelerated, mobile touch — **both first-class from
  day one**, neither a degraded copy. No native app in any phase.
- **NFR-9 (Security — token handling under write scope).** A leaked token can now *destroy* source data.
  Google/DB credentials from env, never hardcoded/committed. Auth invariants (JWT in HttpOnly cookie,
  credentialed CORS against a single origin, `SameSite=None; Secure`) are not relaxed. (AD-14)
- **NFR-10 (Data model — user-scoped, never schema-deep).** No sharing/collaboration/public surface in
  any phase, **yet** every user-owned entity carries a user FK, every query filters on it, uniqueness is
  scoped per user. The single-user assumption is never load-bearing in the schema. (AD-18)
- **NFR-11 (Environment — localhost only, Phase 1).** The dev `docker-compose.yml` is the only
  environment. `DEBUG=True`, hardcoded `SECRET_KEY`, empty `ALLOWED_HOSTS` accepted **only** because
  nothing is deployed. No story assumes a production environment exists. (AD-17)
- **NFR-12 (Operations — user-triggered sync, Phase 1).** Sync is a "Sync now" action plus the
  idempotent `manage.py sync_inbox`. No scheduler, cron, worker daemon or broker. (AD-9)
- **NFR-13 (Testing).** No test touches the network (AD-16): the `youtube/` gateway has an injectable
  fake; backend tests are Django `APITestCase` exercising the cookie-borne auth path end to end; frontend
  mocks every call with `axios-mock-adapter`. **Coverage gate 70%** across lines/statements/functions/branches.
- **NFR-14 (Performance — the payoff).** From opening the app to knowing what to watch in **under ten
  seconds**, without scrolling past anything, because the drilled-into set is finite and *ends*.
- **NFR-15 (Voice & tone).** Dry, factual microcopy; no exclamation marks, no celebration, no
  gamification. **Errors always say what the app will do next**, never only what failed.

### Additional Requirements

Technical requirements from `ARCHITECTURE-SPINE.md` that shape epics and stories. The 20 ADs are binding.

**Architecture invariants (AD-1 … AD-20):**

- **AD-1** — Services are the only mutation path. Every write to app state goes through
  `organizer/services/`; views/commands parse input, call exactly one service fn, serialize. No
  `.save/.create/.update/.delete` outside `services/` or a manager it calls.
- **AD-2** — Two-tree repo (`frontend/` + `backend/`), **no monorepo tooling**. npm + `package-lock.json`
  (not pnpm), no Nx, no `apps/**`/`libs/**`. CI + pre-push hook rewritten onto real commands. Supersedes
  `Docs/FRONTEND-STACK.md §1` and `Docs/CI-AND-GITHUB-GATES.md` on these points (amend them).
- **AD-3** — DRF serializers are the one API contract; TypeScript is **generated** (`drf-spectacular` →
  `@hey-api/openapi-ts` → committed `frontend/src/lib/api/`, never hand-edited). CI regenerates and fails
  on diff. No hand-written API type anywhere in `frontend/`.
- **AD-4** — One list endpoint (`GET /api/videos/`) owns **every** browse surface, with a fixed
  query-param grammar (all params AND-combine; unknown param → 400; page-number pagination with total
  count; infinite scroll banned; URL params map 1:1 onto API params).
- **AD-5** — Derived views are **computed, never stored** (Uncategorized, Needs review, Watched lens,
  Trash). Facts are stored (`watched_at`, `deleted_at`, `availability`, freshness fields); no column
  caches a derived state.
- **AD-6** — Every YouTube write goes through a **transactional outbox** (`PendingYouTubeOp`, committed in
  the same transaction as app state); a separate drain is the only caller of gateway write methods; drain
  runs at run start **and** after import.
- **AD-7** — Persist and verify before mutating the source. Dedupe suppresses re-import, never re-clear;
  removal failures surface in the UI.
- **AD-8** — `SyncRun` is the sole record of run/quota/failure state; UI reads run state only from
  `SyncRun`; reactive quota detection; configurable per-run item cap; quota banner persists until
  `acknowledged_at`.
- **AD-9** — Phase 1 sync is **user-triggered only** (`manage.py sync_inbox`, idempotent). No scheduler.
  Diverges from `EXPERIENCE.md` UJ-2's "next scheduled run" — EXPERIENCE.md amended.
- **AD-10** — Soft-delete (`Video.deleted_at`, excluded by default manager) drives Trash; purge
  hard-deletes and writes `VideoTombstone(youtube_id, purged_at)`; import dedupe tests **all three
  states** (active + soft-deleted + tombstone) by YouTube video ID. App-side only.
- **AD-11** — Search is **PostgreSQL full-text**: maintained `tsvector` (title, description, channel,
  tags) + GIN index, via `SearchVector`/`SearchQuery`. Vector refreshed by an **explicit service call**
  (AD-1) — never a signal/trigger (signals miss `bulk_create`/`update()`/`bulk_update`, the bulk-tag path).
- **AD-12** — One query-key factory; optimistic mutations roll back **per item**; bulk tag restores only
  failed ids; broad prefix invalidation during an active selection banned. React Query is the only
  server-state store.
- **AD-13** — The legacy `frontend/src` prototype is **replaced, not migrated** — deleted when the
  surface replacing it lands. New surfaces built to `Docs/FRONTEND-STACK.md` + UX spines.
- **AD-14** — Cookie-borne JWT is the auth mechanism (unchanged cookie contract); token machinery is
  **first-party over PyJWT** in `organizer/auth/` (SimpleJWT dropped; middleware header-injection
  retired). Scope degradation (read-only mode) is a first-class state; granted scope persisted on
  `UserSocialToken.token_scope`.
- **AD-15** — Watched is **contiguous coverage** via IFrame Player API, not furthest position; one PATCH
  on genuine threshold crossing; position not persisted; manually togglable.
- **AD-16** — No test touches the network (see NFR-13).
- **AD-17** — Phase 1 targets **localhost only** (see NFR-11). `deploy.yml` stays non-functional rather
  than half-adapted.
- **AD-18** — Every user-owned entity carries a **user FK**; every query filters on it; uniqueness scoped
  per user (see NFR-10).
- **AD-19** — Tags have **one identity** (normalised name: trimmed, whitespace-collapsed, case-folded;
  case-insensitive unique per user; display form preserved) and **one mutation semantics** (delta-only
  `add`/`remove`; no endpoint accepts a whole `tags` replacement set, including the single-video PATCH).
  Merge is the only collapsing op (Phase 2).
- **AD-20** — The library has a backup and irreversible upstream deletion is gated on it (see NFR-6).

**Consistency conventions (binding):** Python `snake_case`, models singular, services named for the
operation; frontend kebab-case files / PascalCase components; **`snake_case` on the wire end to end** (no
camelCase transform layer); durations stored as integer seconds (ISO-8601 parsed at gateway); thumbnail
`maxres → high → medium → default` fallback resolved once at the gateway; **one error envelope**
`{ detail, code, errors }` via a single custom DRF `EXCEPTION_HANDLER`; bulk ops namespaced + action-
suffixed (`POST /api/videos/bulk-tag/`, `bulk-delete/`, `bulk-freshness/`) returning per-id outcomes;
client-observed state reported to a dedicated endpoint (never a generic PATCH); structured one-line-per-
sync-decision logging; env-driven config/secrets; Conventional Commits, `feat/story-*` → `develop`
(squash) → `main`; **no AI/bot attribution on any artifact**.

**Infrastructure / setup requirements:**

- **AR-1** — Django 5.2 → **6.0.x** bump; DRF `>=3.17.0`; bounded pins across `requirements.txt`
  (replace unbounded `Django>=4.0`); `drf-spectacular 0.30.0`; PyJWT `2.13.0`.
- **AR-2** — Backend layered package skeleton: `api/`, `auth/`, `services/`, `sync/`, `youtube/`,
  `models/`, `management/commands/sync_inbox.py`, `tests/`.
- **AR-3** — Frontend rebuild to `Docs/FRONTEND-STACK.md`: Tailwind v4 → v3, shadcn/ui init, React Query
  provider, axios client with credentials, `next/font` Geist, the query-key factory, kebab-case
  structure, Jest + RTL harness. **Delete the legacy prototype.** Re-verify the inherited pin block first
  (Next.js pin behind LTS).
- **AR-4** — API contract pipeline + CI: `drf-spectacular` schema → `@hey-api/openapi-ts` into
  `frontend/src/lib/api/`; CI drift gate (regenerate + fail on diff); custom DRF `EXCEPTION_HANDLER`;
  rewrite `ci.yml`, `deploy.yml`, `pre-push` off Nx/pnpm/Prisma onto this repo's real commands
  (`tsc --noEmit`, `next build`, `jest`, `manage.py test`, `manage.py migrate`).
- **AR-5** — `make backup` target + named Postgres volume + verified restore path (AD-20), from the first
  data-model story.
- **AR-6** — `next.config.ts` `remotePatterns` for `lh3.googleusercontent.com`, `i.ytimg.com` (new
  thumbnail hosts require an entry or the build fails).

**No starter template.** This is a brownfield repo (existing Django auth stub + disowned legacy frontend),
not a greenfield scaffold. E1 and E2 are foundation-rebuild epics, not "init from template" stories.

### UX Design Requirements

From `DESIGN.md` (visual identity, tokens, components) and `EXPERIENCE.md` (IA, behavior, states, a11y).
Each is specific enough to generate a story with testable acceptance criteria.

**Design system foundation:**

- **UX-DR1** — **Color token system.** Implement shadcn `neutral` palette with the *measured-contrast*
  overrides only: `chip-foreground` (7.06:1), the two-token border split (`border` 3.02:1 for control
  edges / `border-subtle` decorative-only), `destructive-foreground-dark` (white, 4.55:1), achromatic
  selection tokens (17.72/19.06:1) with 2px checkbox edge, dashed-distinct focus tokens, status
  scrim+badge tokens, thumb-placeholder. **No accent/brand hue anywhere; red reserved strictly for destruction.**
- **UX-DR2** — **Typography scale.** Geist Sans via `next/font` self-hosted; the 8 roles (page/section/
  card/row title, body, meta, chip, numeric). **Tabular numerals mandatory** on every duration, count,
  date. Titles **clamp not truncate** (2 lines grid / 1 line ellipsis list).
- **UX-DR3** — **Shape & spacing tokens.** 12px thumbnail radius (the load-bearing familiarity cue),
  pill chips, the named spacing tokens (sidebar 240/72, bottom-bar 56, player-max 1280, content-max 1600,
  target-min 24, scroll-margin 96). Cards float — no border, fill, or shadow.

**Reusable components (build to `DESIGN.md § Components` + `EXPERIENCE.md § Component Patterns`):**

- **UX-DR4** — **Video card** — 16:9 thumbnail @12px, 2-line-clamp title, channel, then the tag row (the
  app's one addition to YouTube's card); no border/fill/shadow; `⋮` menu (hover on pointer, always-visible
  on touch — hover-only banned).
- **UX-DR5** — **Thumbnail status layer + status badge** — duration always bottom-right; selection
  top-left; status badge bottom-left; **scrim + badge, never scrim alone**; icons ✓ watched / ⚠
  unavailable / ⏳ expired; two statuses render two badges side by side.
- **UX-DR6** — **Selection treatment** — solid 3px outline @2px offset **plus** filled 24px checkbox with
  2px contrasting edge; both always; achromatic.
- **UX-DR7** — **Focus indicator** — **dashed** 2px ring @4px offset, distinct from selection by *style*;
  focused items carry `scroll-margin` clearing sticky bars.
- **UX-DR8** — **Bulk action bar** — sticky bottom (above mobile tab bar), inverted fill, live count via
  `aria-live`, actions Tag · Freshness · Add to playlist · Discard; **all destructive actions live here,
  bound to the selection**.
- **UX-DR9** — **Tag chip** — pill, ≥24px; read-only in browse (click filters), inline-editable on Watch;
  **overflow past three → `+N` popover** (keyboard-operable, `Esc` closes, focus returns to trigger).
- **UX-DR10** — **Filter chip row** — **tags only**, most-used first, horizontally scrollable, ending in
  "All tags →"; multiple tags AND-combine; active chips invert; **filter state lives in the URL**.
- **UX-DR11** — **Filters panel** — channel (searchable multi-select), length range (dual slider +
  numeric inputs), watched, freshness *(P2)*, date range *(P2)*; applied filters surface as removable chips.
- **UX-DR12** — **Shelf row** — Library hub unit: title + count + horizontal card strip + "View more →";
  horizontally scrollable on touch, arrow-key navigable; never paginates in place.
- **UX-DR13** — **View toggle** — grid ⇄ list, **persisted per surface** (not globally).
- **UX-DR14** — **Confirmation dialog** — shadcn `AlertDialog`; states count + consequence;
  **never suppressible**, no "don't ask again"; focus lands on Cancel.
- **UX-DR15** — **Inline banner** — shadcn `Alert`; never modal, never blocking; failure banners never
  auto-dismiss; dismissible only when purely informational.
- **UX-DR16** — **Sync status component** — reports last successful sync + pending-clear orphans; carries
  the **Sync now** trigger; read-only over `SyncRun` (no "next scheduled run" line in Phase 1).

**Information architecture & layout:**

- **UX-DR17** — **Library hub IA** — renders the app's **organizational structure**, one shelf-row per
  dimension (Tags most-used, Channels most-frequent, a **bounded** Recently-imported strip) — **never a
  flat video list**. Empty shelf rows are omitted.
- **UX-DR18** — **Sidebar** — fixed, bounded, never-scrolling order: Library · Uncategorized · Tags ·
  Playlists · Needs review · Watched · Trash; Playlists is a **plain link** (not an expandable list);
  active nav = surface tint + 3px edge bar + `aria-current="page"`.
- **UX-DR19** — **Responsive & platform** — breakpoints: `≥xl` sidebar 240 / grid 4 / 5 cards; `lg`
  sidebar / grid 3 / 4; `md` sidebar 72 icons / grid 2 / 3; `<md` no sidebar, **bottom tab bar (4 tabs:
  Library · Uncategorized · Search · More) + drawer**, grid 2, shelf rows scroll, search full-screen.
  **Two columns minimum on phones, never one.**
- **UX-DR20** — **Watch page** — single column, centered, capped 1280px, **no right rail at any
  breakpoint** (absent, not collapsed); title, channel, inline-editable tags, collapsed description.

**Triage (the weekly core loop):**

- **UX-DR21** — **List mode triage** (default) — Gmail-shaped: densest legible rows; select via checkbox
  / shift-click range / `x` on focused row / `a` all-loaded; bulk action bar with live count; one action
  applies to the whole selection.
- **UX-DR22** — **Focus mode triage** — tag-first: pick tags first (header pins "Filing as: `guitar` +
  `course`"), sweep toggling matches (click/tap only, no dialogs), one **Apply** files the selection with
  the whole tag set; state preserved across a mode switch.
- **UX-DR23** — **Optimistic application + per-row revert** — tags apply instantly, reconcile in
  background; failure surfaces a toast and reverts **only affected rows** (never the whole sweep);
  reverted rows re-announce via `aria-live` (pairs with AD-12).
- **UX-DR24** — **Selection survives filtering** — narrowing mid-sweep must not silently drop
  selected-but-hidden items; the bar's count always tells the truth. Discard always confirms (bound to
  selection); incremental/abandonable mid-sweep; no "mark as done".

**Interaction, state & accessibility:**

- **UX-DR25** — **Keyboard interaction model** — `j`/`k`, `x`, shift-click, `a`, `t`, `f`,
  `Backspace`/`Del`, `Enter`, `v`, `/`, `g`+`l`/`u`/`t`/`p`, `Esc`.
- **UX-DR26** — **WCAG 2.1.4 shortcut conformance** — the mandatory trio: a Settings **disable toggle**,
  **remapping** for every binding, **focus scoping** (shortcuts inert inside text inputs, the tag
  typeahead, dialogs, the player iframe). Discoverable, not buried.
- **UX-DR27** — **Touch interaction model** — long-press enters selection, tap toggles; bottom tab bar +
  drawer; **all tap targets ≥24px**, list rows relax 32→44px on touch.
- **UX-DR28** — **State pattern set** — implement the `EXPERIENCE.md § State Patterns` matrix: cold-load
  skeletons (never spinners), fetch/server error (Retry, cached data stays), auth-expired, all empty
  states (incl. **empty Uncategorized = "Nothing to file." the win state**), sync running / complete /
  partial-failure / orphans / quota-exhausted (persists until acknowledged) / failed / read-only-scope,
  unavailable video, `_Inbox` missing, deletion complete, offline.
- **UX-DR29** — **Voice & tone** — dry factual microcopy per the Do/Don't table; **errors state what the
  app does next**; no exclamation marks, no celebration, no gamification (implements NFR-15).
- **UX-DR30** — **Accessibility floor (cross-cutting)** — WCAG 2.2 AA both surfaces both modes; no state
  by color alone; focus never obscured (2.4.11 scroll-margin); `Tab` order = reading order; `Esc` closes
  topmost layer; decorative thumbnails `alt=""` with title as accessible name; forms `mode: 'onBlur'`
  with programmatically-associated announced errors and persistent visible labels.

### FR Coverage Map

Phase-1 FRs and the epics that deliver them. **Backend + frontend of one FR are split across epics**
by design (AD-3 makes the API contract a build-time seam), so most FRs have a *delivering* backend epic
and a *consuming* frontend epic. Foundation epics (E1–E5) deliver no FR directly — they are governed by
ADs and **enable** the FR-bearing epics; this is `WORK-SPLIT.md`'s explicit structure, not an omission.

- **FR-1** (auth + write scope) → **E6** (OAuth scope, granted-scope persistence, read-only mode) · UI in **E13** (Google connect / re-consent)
- **FR-2** (`_Inbox` designation) → **E6** (`InboxDesignation`, listing, create-fallback) · UI in **E13** (designation screen)
- **FR-5** (inbox import → Uncategorized) → **E7** (sync import, dedupe, metadata + three dates)
- **FR-6** (crash-safe clear + orphans) → **E7** (outbox drain, verify, orphan retry) · surfaced in **E13** (orphan / partial-failure / quota banners, Sync now)
- **FR-7** (bulk triage) → **E9** (`bulk-tag`, `bulk-delete`) · UI in **E11** (List + Focus triage)
- **FR-9** (tag management) → **E9** (tag CRUD, delta apply) · **E4** (normalised identity constraint) · Tags index UI in **E10** · inline edit in **E12** · typeahead in **E11**
- **FR-11** (delete + Trash + tombstone) → **E9** (soft-delete / restore / purge API) · **E4** (`VideoTombstone`, default manager) · UI in **E14** (Trash) · bulk discard in **E11**
- **FR-12** (channel + length facets) → **E5** (gateway parsing) · **E8** (facet params) · filters UI in **E10**
- **FR-13** (facet browse, non-date) → **E8** (`GET /api/videos/` grammar) · UI in **E10** (hub, Tag detail, Filters panel)
- **FR-14** (search) → **E4** (`tsvector` + GIN) · **E8** (`q` param) · search UI in **E10**
- **FR-15** (embedded playback) → **E12** (IFrame embed, open-in-YouTube)
- **FR-16** (auto-watched) → **E12** (contiguous-coverage tracker + PATCH)

**Enabling / infrastructure epics (AD-governed, no direct FR):** **E1** (backend platform — AD-1,14,16,17,20) ·
**E2** (frontend platform — AD-2,12,13) · **E3** (API contract pipeline + CI — AD-2,3) · **E4** (data model — AD-5,10,11,18,19) ·
**E5** (YouTube gateway + fake — AD-1,16). Cross-cutting NFRs and UX-DRs land as stories inside the epic
that owns the surface they govern (e.g. UX-DR1–3 tokens in E2; UX-DR25–27 shortcuts in E11; NFR-6 backup in E1/E4).

## Epic List

Adopted **verbatim from `WORK-SPLIT.md`** (E1–E14), which fixes epic boundaries and dependency order
against the spine. Ordered by the dependency graph; the **critical path is `E1 → E5 → E6 → E7 → E13`**,
with **E2 running fully parallel to E1** from day one.

> **A note on the "user-value, not technical layers" principle.** E1–E5 are foundation/platform epics
> that a greenfield BMAD flow would flag as technical layers. They stand here deliberately: this is a
> **brownfield repo** where "the backend is an auth stub and the frontend is disowned legacy" — the
> architect judged the foundation epics to be *most of the risk*, not overhead, and split them out so the
> highest-risk mechanism (the crash-safe sync engine) can be built and proven from the command line
> before any UI depends on it. The boundaries are an already-validated architectural decision.

### Epic 1: Backend platform

Establish the Django 6.0 backend on a trustworthy foundation: the first-party PyJWT cookie-auth module
(replacing SimpleJWT and retiring the header-injection middleware), the layered package skeleton, the
`APITestCase` harness, and the `make backup` target + named volume that make the library durable from
day one. After this epic the backend boots on Django 6, authenticates over the unchanged cookie contract
with a tested auth path, and has a verified backup/restore.
**Governed by:** AD-1, AD-14, AD-16, AD-17, AD-20 · **Depends on:** nothing (**start here**) · **FRs:** none direct (enabler)

### Epic 2: Frontend platform

Rebuild `frontend/src` to `Docs/FRONTEND-STACK.md` and the UX spines — Tailwind v4→v3, shadcn/ui, React
Query provider, credentialed axios client, `next/font` Geist, the query-key factory, the design-token
system, kebab-case structure, Jest + RTL — and **delete the legacy prototype**. After this epic there is a
clean, tested frontend shell with the token system and data layer in place, ready to consume generated types.
**Governed by:** AD-2, AD-12, AD-13 · **Depends on:** nothing (**parallel to E1**) · **UX-DRs:** UX-DR1–3 · **FRs:** none direct (enabler)

### Epic 3: API contract pipeline + CI

Make the API contract a build-time artifact: `drf-spectacular` schema → `@hey-api/openapi-ts` into a
committed `frontend/src/lib/api/`, the CI drift gate, the custom DRF `EXCEPTION_HANDLER` (one error
envelope), and the rewrite of `ci.yml`, `deploy.yml` and the `pre-push` hook off Nx/pnpm/Prisma onto this
repo's real commands. After this epic every frontend epic can consume typed endpoints and CI fails on drift.
**Governed by:** AD-2, AD-3, error-shape convention · **Depends on:** E1, E2 · **FRs:** none direct (enabler, on the critical path for 4 UI epics)

### Epic 4: Library data model

Land the domain schema and its constraints: `Video`, `Tag` + through-table, `VideoTombstone`, the
`Playlist` skeleton (Phase-2 headroom), user FKs and per-user uniqueness, `deleted_at` + default manager,
tag normalisation + case-insensitive constraint, and the `tsvector` column + GIN index with service-side
refresh. After this epic the data model enforces AD-19 tag identity, AD-10 three-way dedupe, and AD-18
user-scoping **as constraints**, not as later view-layer validation.
**Governed by:** AD-5, AD-10, AD-11, AD-18, AD-19 · **Depends on:** E1 · **FRs:** enables FR-9, FR-11, FR-14

### Epic 5: YouTube gateway + fake

Build the `organizer/youtube/` anti-corruption port: playlist and item reads, batched metadata fetch,
item removal, quota-error translation, availability detection, ISO-8601 duration parsing, and the
`maxres → high → medium → default` thumbnail fallback — **plus the injectable fake** every test uses.
After this epic there is exactly one place that speaks YouTube, and the sync engine can be built honestly
against the fake.
**Governed by:** AD-1, AD-16, gateway conventions · **Depends on:** E1 · **FRs:** enables FR-5, FR-6, FR-12 (channel/length capture)

### Epic 6: Auth, write scope & `_Inbox` designation

Extend OAuth to YouTube **write** scope, persist and read the granted scope at runtime, implement the
read-only degraded mode, and persist the `InboxDesignation` in the database with playlist listing,
selection, and a create-an-`_Inbox` fallback. After this epic Alexis can sign in with write access (or
run read-only with a clear notice) and designate his capture playlist.
**Governed by:** AD-14, AD-18 · **Depends on:** E1, E5 · **FRs:** FR-1, FR-2

### Epic 7: Sync engine

The product's core, hardest mechanism: `manage.py sync_inbox` with the `SyncRun` lifecycle, three-way
dedupe, the fetch → persist → verify → enqueue ordering, `PendingYouTubeOp` written in the import
transaction, the outbox drain at run-start and after import, orphan retry, reactive quota detection with
the per-run cap, and the structured per-decision log. After this epic the crash-safe weekly import loop
works end-to-end from the command line against the real API — the cheapest useful slice of the product.
**Governed by:** AD-6, AD-7, AD-8, AD-9, AD-10, AD-16 · **Depends on:** E4, E5, E6 · **FRs:** FR-5, FR-6

### Epic 8: Browse + search API

The single list endpoint that owns every browse surface: `GET /api/videos/` with the full AD-4 grammar,
page-number pagination with total counts, derived `uncategorized`, PostgreSQL full-text search, channel
and length facets, and the Library hub's per-dimension counts. After this epic one documented query
grammar answers every browse and search question identically.
**Governed by:** AD-4, AD-5, AD-11 · **Depends on:** E4 · **FRs:** FR-12, FR-13 (non-date), FR-14

### Epic 9: Mutation API

The write surface for the Library: tag CRUD, delta-only tag application (single and bulk), the freshness
bulk endpoint (schema only in Phase 1), soft-delete / restore / purge, and the per-id bulk outcome shape.
After this epic every Library mutation goes through a service behind a consistent bulk contract the
frontend can roll back per item.
**Governed by:** AD-1, AD-10, AD-19, bulk conventions · **Depends on:** E4 · **FRs:** FR-7, FR-9, FR-11

### Epic 10: Library hub + browse surfaces

The entry experience and browse-by-intent: the shelf-row Library hub (never a video list), Tag detail,
the Tags index, the Filters panel, search, URL-backed filter state, and pagination / load-more. After
this epic Alexis opens the app to his organizational structure and drills into finite, filtered, linkable
sets — the <10s payoff.
**Governed by:** AD-4, AD-12, AD-13; `EXPERIENCE.md § Information Architecture` · **Depends on:** E3, E8 · **UX-DRs:** UX-DR4–5,9–20,28,30 · **FRs:** FR-13, FR-14 (+ FR-9 Tags index, FR-12 filters)

### Epic 11: Triage surfaces

The weekly loop's UI: Uncategorized in List and Focus modes, selection (checkbox, shift-range, `x`,
long-press), the bulk action bar, optimistic apply with per-row revert, and keyboard shortcuts with the
WCAG 2.1.4 disable/remap/scoping trio. After this epic Alexis files a week's catch within the ≤2-interaction
bound on both desktop and mobile.
**Governed by:** AD-12, AD-19; PRD §8 triage bound; `EXPERIENCE.md § Triage Modes` · **Depends on:** E3, E8, E9, **E10** (reuses the video card + thumbnail-status layer, UX-DR4/5, first built in Story 10.1 — Focus-mode grid and selection treatment operate on it) · **UX-DRs:** UX-DR6–8,21–27 · **FRs:** FR-7 (+ FR-9 typeahead)
**Risk:** the ≤2-interaction bound is load-bearing for SM-C2. If it slips here, the PRD's own fallback is to pull FR-8 suggestions forward from Phase 2.

### Epic 12: Watch + playback

The payoff surface: the single-column watch page with no rail, the IFrame Player API embed, the
contiguous-coverage watched tracker, inline tag editing (delta semantics), open-in-YouTube, and the
unavailable-video state. After this epic Alexis watches inside the app, away from the recommendation
machinery, and videos auto-mark Watched honestly.
**Governed by:** AD-15, AD-19, client-observed-state convention · **Depends on:** E3, E8, E9, **E10** (reuses the video card + thumbnail-status layer, UX-DR4/5, first built in Story 10.1 — the unavailable-video state renders on the card status layer) · **UX-DRs:** UX-DR20 · **FRs:** FR-15, FR-16 (+ FR-9 inline edit)

### Epic 13: Settings + sync status

The control surface: Google connection and re-consent, the `_Inbox` designation UI, the **"Sync now"**
trigger (the only Phase-1 trigger), sync status read from `SyncRun`, the orphan / partial-failure / quota /
read-only-scope banners, theme, and the watched threshold. After this epic Alexis triggers and monitors
sync and manages his connection and preferences.
**Governed by:** AD-8, AD-9, AD-14; `EXPERIENCE.md § State Patterns` · **Depends on:** E3, E7 · **UX-DRs:** UX-DR16,28–29 · **FRs:** FR-1/FR-2 UI, FR-6 surfacing, FR-16 threshold

### Epic 14: Trash

The safety net for deletion: the recently-deleted surface, restore, and the retention purge that writes a
tombstone. After this epic deletion is recoverable within the retention window and purges cleanly to a
tombstone that prevents resurrection.
**Governed by:** AD-10, AD-20 · **Depends on:** E3, E9 · **FRs:** FR-11 (Trash surface)

---

# Epics & Stories

> Story `user_type` is **the developer** for the foundation/enabler epics (E1–E5, E3) — this is
> Alexis's "vision to realize: his own tool, engineered properly" — and **Alexis** for the
> capability epics. Every story is sized for a single dev-agent session and depends only on
> earlier stories. AC references cite the binding `AD-n`, `FR-n`, `NFR-n`, and `UX-DRn` ids.

## Epic 1: Backend platform

Establish the Django 6.0 backend on a trustworthy foundation: the first-party PyJWT cookie-auth module
(replacing SimpleJWT and retiring the header-injection middleware), the layered package skeleton, the
`APITestCase` harness, and the `make backup` target + named volume that make the library durable from
day one.

### Story 1.1: Upgrade to Django 6.0 with bounded dependency pins

As a developer,
I want the backend upgraded to Django 6.0.x with every requirement bounded-pinned,
So that the platform runs on a supported, reproducible dependency set (AD-14 stack).

**Acceptance Criteria:**

**Given** the current `requirements.txt` with an unbounded `Django>=4.0`
**When** I upgrade the stack
**Then** Django is pinned to `6.0.x`, DRF to `>=3.17.0`, `drf-spectacular` to `0.30.0`, and every
other requirement carries a bounded pin
**And** the backend container builds and `manage.py check` passes with no unresolved deprecations.

**Given** the running stack
**When** I start the backend with `make up`
**Then** the server boots on `https://localhost:8000` and existing OAuth/login routes respond,
confirming no regression from the framework bump.

### Story 1.2: Layered backend package skeleton and test runner

As a developer,
I want the `organizer/` package split into the layered structure with a working test runner,
So that every later story lands its code in the correct layer with dependency direction enforced (AD-1).

**Acceptance Criteria:**

**Given** the monolithic `organizer/` app
**When** I introduce the skeleton
**Then** `api/`, `auth/`, `services/`, `sync/`, `youtube/`, `models/`, `management/commands/`, and
`tests/` packages exist, each importable, with `services/` importing neither DRF nor `youtube/`.

**Given** the new structure
**When** I run `manage.py test`
**Then** the suite discovers and runs (green on an empty/placeholder test), establishing the harness
the coverage gate (NFR-13) will later measure.

### Story 1.3: First-party PyJWT token issue/verify module

As a developer,
I want token issuing and verification implemented in `organizer/auth/` over PyJWT, with unit tests,
So that auth no longer depends on the unmaintained SimpleJWT before the swap (AD-14).

**Acceptance Criteria:**

**Given** the `organizer/auth/` module
**When** I mint an access token for a user
**Then** it is a signed PyJWT carrying the expected claims and expiry, and verification round-trips it
back to the same user.

**Given** a tampered, expired, or wrongly-signed token
**When** verification runs
**Then** it rejects the token with a typed error, and unit tests cover each rejection path.

**Given** the module
**When** tests run
**Then** they exercise issue and verify **without** SimpleJWT imported anywhere in the module.

### Story 1.4: Cookie authentication class and middleware retirement

As a developer,
I want a custom DRF authentication class that reads the `access_token` cookie directly, replacing the
header-injection middleware and SimpleJWT,
So that the unchanged cookie contract is served by first-party code with no global request mutation (AD-14).

**Acceptance Criteria:**

**Given** the new authentication class registered as the default
**When** an authenticated request arrives with a valid `access_token` HttpOnly cookie
**Then** DRF resolves `request.user` from the cookie with no `Authorization` header present.

**Given** the swap is complete
**When** I inspect the codebase
**Then** `JWTAuthCookieMiddleware`'s header injection is removed and `djangorestframework-simplejwt`
is absent from `requirements.txt` and imports.

**Given** the cross-port setup
**When** the auth flow runs
**Then** `CORS_ALLOW_CREDENTIALS`, the single allowed origin, and `SameSite=None; Secure` are
unchanged (NFR-9), and an `APITestCase` proves login → authenticated request over the cookie path
end to end (AD-16).

### Story 1.5: `make backup` target, named volume, and verified restore

As a developer,
I want a `make backup` target producing a timestamped `pg_dump`, a named Postgres volume, and a
documented restore verified once,
So that the library — the app's sole home after import — is durable from the first data-model story (AD-20, NFR-6).

**Acceptance Criteria:**

**Given** the compose stack
**When** I run `make backup`
**Then** a timestamped `pg_dump` artifact is written to a known location, and the Postgres volume is
explicitly named in `docker-compose.yml`.

**Given** a populated database and a backup
**When** I follow the documented restore path into a fresh volume
**Then** the data is fully recovered, and the restore has been executed at least once and documented.

**Given** routine commands
**When** the team operates the stack
**Then** no routine command, script, or documented workflow destroys the named volume.

## Epic 2: Frontend platform

Rebuild `frontend/src` to `Docs/FRONTEND-STACK.md` and the UX spines, delete the legacy prototype, and
stand up the design-token system and data layer so later surfaces consume generated types on a clean shell.

### Story 2.1: Re-verify and amend the frontend pin block

As a developer,
I want the inherited `Docs/FRONTEND-STACK.md` pin block re-verified against current releases and the doc
amended where a pin moves,
So that the first frontend PR builds on validated versions rather than another project's stale mirror
(spine Deferred).

**Acceptance Criteria:**

**Given** the inherited pins (notably Next.js `~16.1.6`, already behind its LTS line)
**When** I verify each against its current release and security advisories
**Then** every pin is either confirmed current or updated, and `Docs/FRONTEND-STACK.md` is amended
(the doc, not just the code) to record the resolved versions.

**Given** AD-2
**When** I set the package manager
**Then** the project uses **npm** with `package-lock.json` — no pnpm, no workspaces.

### Story 2.2: Delete the legacy prototype and scaffold the App Router shell

As a developer,
I want the legacy `frontend/src` prototype deleted and replaced with a kebab-case App Router shell in
TypeScript strict mode,
So that no legacy pattern (raw `fetch`, FontAwesome, CSS Modules, Tailwind v4) is dragged forward (AD-13).

**Acceptance Criteria:**

**Given** the shipped prototype
**When** I rebuild the shell
**Then** the legacy files are deleted, and a minimal App Router app boots with `src/` layout, the `@/*`
alias, kebab-case filenames, and `tsc --noEmit` exiting 0 with no `any`.

**Given** the new shell
**When** I inspect dependencies
**Then** every imported package is a direct dependency (no phantom deps), and the production `next build`
exits 0.

### Story 2.3: Design-token system, Tailwind v3, and shadcn/ui

As a developer,
I want the design tokens, Tailwind v3, Geist via `next/font`, and shadcn/ui in place,
So that every surface renders the measured-contrast neutral palette with no accent hue (UX-DR1, UX-DR2, UX-DR3).

**Acceptance Criteria:**

**Given** the token system
**When** I configure colors, typography, radii, and spacing
**Then** they encode the `DESIGN.md` tokens exactly — the two-token border split, achromatic selection
and dashed-focus tokens, status scrim+badge tokens, 12px thumbnail radius, and the 8 type roles — with
**no accent/brand color** anywhere and red reserved for destruction.

**Given** typography
**When** Geist Sans loads
**Then** it is self-hosted via `next/font` (no runtime request, no layout shift), and `tabular-nums` is
applied to durations, counts, and dates.

**Given** shadcn/ui
**When** components are added
**Then** they are generated into `src/components/ui/` via `npx shadcn@latest add` and never hand-edited,
and Tailwind is v3 (not v4).

### Story 2.4: React Query provider, credentialed axios client, and query-key factory

As a developer,
I want a React Query provider, a credentialed axios client, and the single query-key factory,
So that all server state flows through one cache with one key hierarchy (AD-12).

**Acceptance Criteria:**

**Given** the data layer
**When** the app mounts
**Then** a `QueryClientProvider` wraps the tree and an axios instance sends `withCredentials: true`
against the single backend origin.

**Given** the query-key factory
**When** any hook needs a cache key
**Then** it reads from the factory (`['videos','list',params]`, `['videos','detail',id]`,
`['tags','list']`, …) — no hook writes a key literal — and React Query is the only server-state store
(no Redux/Zustand/SWR).

### Story 2.5: Jest + RTL + axios-mock-adapter test harness

As a developer,
I want the Jest + React Testing Library + `axios-mock-adapter` harness with the coverage gate,
So that frontend stories ship tests that never hit a real backend (NFR-13, AD-16).

**Acceptance Criteria:**

**Given** the harness
**When** I run the frontend test suite
**Then** Jest 29 + RTL 16 run, every network call is mocked with `axios-mock-adapter`, and the config
enforces the 70% coverage gate across lines/statements/functions/branches.

**Given** a sample component test
**When** it queries the DOM
**Then** it asserts on role/label (user-visible behavior), demonstrating the RTL convention for later stories.

## Epic 3: API contract pipeline + CI

Make the API contract a build-time artifact — schema, generated types, drift gate, one error envelope —
and rewrite CI and the hooks off the mirrored Nx/pnpm/Prisma scaffold onto this repo's real commands.

### Story 3.1: OpenAPI schema generation with drf-spectacular

As a developer,
I want `drf-spectacular` emitting the OpenAPI schema from DRF serializers,
So that the serializers are the one wire-shape source the frontend generates from (AD-3).

**Acceptance Criteria:**

**Given** `drf-spectacular` configured
**When** I run the schema generation command
**Then** a valid OpenAPI document is produced from the registered DRF serializers, with `snake_case`
field names on the wire (no camelCase transform layer).

**Given** the schema settings
**When** the schema is generated
**Then** it is deterministic (stable ordering) so a re-run produces byte-identical output for the drift gate.

### Story 3.2: Single custom DRF exception handler (one error envelope)

As a developer,
I want one custom DRF `EXCEPTION_HANDLER` emitting `{ detail, code, errors }` for every non-2xx,
So that no DRF default shape leaks through and the frontend can roll back per item (AD-3, error convention).

**Acceptance Criteria:**

**Given** the custom handler registered
**When** any endpoint raises a validation, auth, permission, or not-found error
**Then** the response body is exactly `{ "detail": str, "code": str, "errors": {field:[str]}|null }`.

**Given** a bulk endpoint
**When** it returns partial success
**Then** it carries a per-id outcome list so the client rolls back only failed items (AD-12), and this
is not treated as an error response.

### Story 3.3: Generated TypeScript client via @hey-api/openapi-ts

As a developer,
I want `@hey-api/openapi-ts` generating the committed frontend API types from the schema,
So that no API type is hand-written in `frontend/` (AD-3).

**Acceptance Criteria:**

**Given** the OpenAPI schema
**When** codegen runs
**Then** types and client are written into `frontend/src/lib/api/`, committed, and consumed by data hooks.

**Given** the generated directory
**When** I inspect it
**Then** it is marked generated and never hand-edited, and no `Video`/`Tag` type is declared by hand
anywhere in `frontend/`.

### Story 3.4: CI schema/type drift gate

As a developer,
I want a CI job that regenerates the schema and types and fails on any diff,
So that a serializer change that isn't regenerated cannot merge (AD-3).

**Acceptance Criteria:**

**Given** a PR that changes a serializer without regenerating
**When** the drift gate runs
**Then** it regenerates schema + types, detects the diff, and fails the check.

**Given** a PR with serializer and regenerated types in sync
**When** the gate runs
**Then** it passes with no diff.

### Story 3.5: Rewrite GitHub Actions CI onto this repo's commands

As a developer,
I want `ci.yml` rewritten off Nx/pnpm/Prisma onto the real frontend+backend commands,
So that CI actually gates this two-tree repo (AD-2, `Docs/CI-AND-GITHUB-GATES.md`).

**Acceptance Criteria:**

**Given** the mirrored `ci.yml`
**When** I rewrite it
**Then** triggers use `frontend/**`, `backend/**`, `package-lock.json`, `requirements.txt`; the job
graph runs `tsc --noEmit`, `npm run lint`, `next build`, `npm test -- --coverage`, and `manage.py test`;
and a `postgres:15` service runs Django `migrate` before backend tests.

**Given** the coverage gate
**When** the test job runs below 70%
**Then** CI fails, and every branch of the pipeline references no `nx`/`pnpm`/`prisma` commands.

### Story 3.6: Rewrite pre-push/pre-commit hooks; keep deploy.yml non-functional

As a developer,
I want the local hooks rewritten to real commands and `deploy.yml` left explicitly non-functional,
So that the four-layer local gate works and no half-adapted deploy posture ships (AD-2, AD-17).

**Acceptance Criteria:**

**Given** the `nx run-many` pre-push hook
**When** I rewrite it
**Then** it runs `tsc --noEmit`, `npm run lint`, `npm test -- --coverage`, `npm run build`, and
`python manage.py test`, activated via `git config core.hooksPath .githooks`.

**Given** the optional pre-commit hook
**When** a direct commit to `main`/`develop` is attempted
**Then** it is blocked.

**Given** `deploy.yml`
**When** I inspect it
**Then** it is explicitly marked non-functional/disabled rather than half-adapted to a nonexistent
production target (AD-17).

## Epic 4: Library data model

Land the domain schema and its constraints so tag identity, three-way dedupe, and user-scoping are
enforced as constraints, not later view-layer validation.

### Story 4.1: Video model with soft-delete and the three dates

As a developer,
I want the `Video` model with its local metadata, three distinct dates, user FK, soft-delete, and a
default manager,
So that a captured Video survives removal from any YouTube playlist and is user-scoped and recoverable
(AD-18, AD-10, FR-5).

**Acceptance Criteria:**

**Given** the `Video` model
**When** I inspect its fields
**Then** it stores title, description, channel, thumbnail URL, duration (integer seconds), YouTube
ID/URL, `availability`, `watched_at`, `deleted_at`, and the three **distinct** dates `imported_at`,
`source_added_at`, `published_at` (never conflated).

**Given** AD-18
**When** I inspect constraints
**Then** `Video` carries a `user` FK and YouTube video ID is unique **per user**, not globally.

**Given** the default manager
**When** I query `Video.objects`
**Then** soft-deleted rows (`deleted_at` set) are excluded by default, and Phase-2 freshness fields
exist as nullable headroom with no behavior attached.

### Story 4.2: Tag model with normalised identity and case-insensitive uniqueness

As a developer,
I want the `Tag` model and the `Video`↔`Tag` through-table with normalised-name identity,
So that tags differing only in case or whitespace are the same tag (AD-19, FR-9).

**Acceptance Criteria:**

**Given** the `Tag` model
**When** a tag is created
**Then** its identity is the normalised name (trimmed, internal whitespace collapsed, case-folded), the
first-typed display form is preserved for rendering, and a case-insensitive uniqueness constraint is
enforced **per user** (AD-18).

**Given** an existing tag `guitar`
**When** a create-or-get is attempted with ` Guitar `
**Then** it normalises onto and returns the existing row rather than splitting into two.

**Given** the through-table
**When** a Video is tagged
**Then** it can carry multiple Tags via the join.

### Story 4.3: VideoTombstone and the three-way dedupe helper

As a developer,
I want the `VideoTombstone` model and a dedupe helper that tests all three states,
So that a previously deleted video is never resurrected by a later import (AD-10, FR-5).

**Acceptance Criteria:**

**Given** the `VideoTombstone` model
**When** a Video is permanently purged
**Then** a `VideoTombstone(youtube_id, purged_at)` with a `user` FK is written.

**Given** the dedupe helper (in `services/`)
**When** it checks a YouTube video ID
**Then** it reports a match if the ID exists as an **active**, **soft-deleted**, or **tombstoned** row
for that user, and unit tests cover all three states.

### Story 4.4: Playlist skeleton (Phase-2 headroom)

As a developer,
I want the `Playlist` and `PlaylistItem` models as an inert, user-scoped, ordered skeleton,
So that Phase 2 playlist work is additive and Uncategorized can be defined as "no tags AND no playlist
membership" now (AD-5, AD-18).

**Acceptance Criteria:**

**Given** the skeleton
**When** I inspect it
**Then** `Playlist` (user FK, name) and `PlaylistItem` (playlist, video, order) exist with per-user
uniqueness, and no Phase-1 endpoint or service exposes ordering/reorder behavior.

**Given** the membership relation
**When** the Uncategorized query is later written
**Then** playlist membership is queryable as one of its two conditions.

### Story 4.5: Full-text search vector, GIN index, and service-side refresh

As a developer,
I want a maintained `tsvector` column with a GIN index and an explicit service-side refresh function,
So that search stays correct after the highest-volume operation, bulk tagging (AD-11, FR-14).

**Acceptance Criteria:**

**Given** the `Video` model
**When** the migration runs
**Then** a `tsvector` column spanning title, description, channel name, and tags exists with a GIN index.

**Given** a service that mutates a contributing field or the tag set
**When** it completes
**Then** it calls the refresh function **explicitly** (AD-1), and the vector is **never** maintained by a
`post_save` signal or a database trigger.

**Given** a `bulk_update`/`bulk_create`/`update()` tag path
**When** it runs
**Then** the affected vectors are refreshed by the service call, so videos remain findable by tags they
actually carry.

## Epic 5: YouTube gateway + fake

Build the one anti-corruption port that speaks YouTube, plus the injectable fake every test uses.

### Story 5.1: Gateway port and injectable fake

As a developer,
I want the `organizer/youtube/` port interface and its fake implementation,
So that the sync engine and tests run against one seam with no network in tests (AD-1, AD-16).

**Acceptance Criteria:**

**Given** the gateway port
**When** it is constructed
**Then** it builds a Google API client from a user's `UserSocialToken` and imports **no** models or
services (layer rule).

**Given** the fake
**When** a test injects it
**Then** it satisfies the same interface with fixture-driven responses, and no test authenticates to
Google or calls the Data API.

### Story 5.2: Playlist and playlist-item reads

As a developer,
I want gateway methods to list a user's playlists and read a playlist's items,
So that `_Inbox` designation and import can enumerate source data (FR-2, FR-5 support).

**Acceptance Criteria:**

**Given** the read methods
**When** I list playlists
**Then** each carries id, title, and item count.

**Given** a playlist id
**When** I read its items
**Then** each item returns `videoId`, `playlistItemId`, and the source-added timestamp, exercised via
the fake.

### Story 5.3: Batched metadata fetch with duration and thumbnail resolution

As a developer,
I want a batched video-metadata fetch that parses duration and resolves the thumbnail,
So that every imported Video has channel, length, and a stable thumbnail (FR-12, thumbnail/duration conventions).

**Acceptance Criteria:**

**Given** a set of video IDs
**When** metadata is fetched
**Then** it is requested in batches (quota-minimizing) and returns title, description, channel, published
date, duration, and thumbnail.

**Given** a raw ISO-8601 duration
**When** it is parsed at the gateway
**Then** it is stored as integer seconds and the raw form is never persisted.

**Given** YouTube's nested thumbnail object
**When** the gateway resolves it
**Then** it falls back `maxres → high → medium → default` once, and stores the resolved URL.

### Story 5.4: Item removal and quota-error translation

As a developer,
I want the gateway's item-removal write method and reactive quota-error translation,
So that inbox clear has a single call site and quota exhaustion is a typed signal (FR-6, AD-8, NFR-5).

**Acceptance Criteria:**

**Given** a `playlistItemId`
**When** removal is called
**Then** it deletes that item from the source playlist, and this is a **write** method (only the sync
drain may call it, per AD-6, enforced in E7).

**Given** the API returns a `quotaExceeded` error
**When** the gateway handles it
**Then** it translates it into a typed quota-exhaustion error the caller can detect reactively (never
predicted).

### Story 5.5: Availability detection

As a developer,
I want the gateway to detect when a video is no longer served,
So that a sole-home library can later flag dead links (FR-19 gateway capability; surface is Phase 2).

**Acceptance Criteria:**

**Given** a video that is deleted, private, region-blocked, or removed
**When** the gateway inspects it
**Then** it reports the video as Unavailable with the distinguishing reason where the API provides it.

**Given** an available video
**When** inspected
**Then** it reports Available, and the detection is unit-tested via the fake (no Phase-1 review-sweep
surface is built).

## Epic 6: Auth, write scope & `_Inbox` designation

Extend OAuth to write scope, make scope degradation a first-class state, and let Alexis designate his
capture playlist.

### Story 6.1: OAuth consent with YouTube write scope

As Alexis,
I want to sign in with Google and grant read **and write** access to my YouTube playlists,
So that the app can later read the `_Inbox` and remove imported items (FR-1, AD-14).

**Acceptance Criteria:**

**Given** the OAuth flow
**When** I start sign-in
**Then** the consent screen requests the YouTube read **and** write scopes, and the callback exchanges
the code, upserts my `User`, logs me in, and mints the cookie JWT.

**Given** a successful consent
**When** the app acts on my behalf
**Then** it can list playlists and read playlist items (write paths are validated in E7).

### Story 6.2: Persist granted scope and enable read-only degraded mode

As Alexis,
I want the app to record exactly what scope I granted and degrade gracefully if I withheld write,
So that a read-only grant disables only the write features with a clear notice (FR-1, AD-14).

**Acceptance Criteria:**

**Given** a completed consent
**When** the callback stores tokens
**Then** the granted scope is persisted on `UserSocialToken.token_scope` and read at runtime.

**Given** write scope is absent
**When** the app evaluates capabilities
**Then** it runs read-only — inbox clear (FR-6) and playlist deletion (FR-4, Phase 2) are disabled — and
an endpoint exposes the read-only state for the UI's persistent notice and re-consent offer.

**Given** write scope is present
**When** capabilities are evaluated
**Then** all features are enabled.

### Story 6.3: Designate, change, and persist the `_Inbox`

As Alexis,
I want to pick one of my YouTube playlists as the `_Inbox`, stored in the database and changeable,
So that the app has a capture on-ramp that survives restarts (FR-2, AD-18).

**Acceptance Criteria:**

**Given** the `InboxDesignation` model (user FK)
**When** I request my playlists
**Then** they are listed for selection, and choosing one persists the designation **in the database**,
never an env var or hardcode.

**Given** an existing designation
**When** I change it
**Then** the new choice persists and takes effect on the **next** import, not retroactively.

### Story 6.4: Create an `_Inbox` when none is suitable

As Alexis,
I want the app to create an `_Inbox` playlist for me if I have none,
So that I can start capturing without hand-making a playlist on YouTube (FR-2).

**Acceptance Criteria:**

**Given** I have no suitable playlist
**When** I choose "create one"
**Then** the app creates an `_Inbox` playlist via the gateway and designates it, persisted per user.

**Given** the create path requires write scope
**When** I am in read-only mode
**Then** creation is disabled with the read-only notice rather than failing opaquely.

## Epic 7: Sync engine

The product's core, hardest mechanism: the crash-safe `_Inbox` import loop, built and proven from the
command line against the fake before any UI depends on it. Failure paths are first-class, not edge cases.

### Story 7.1: SyncRun lifecycle record

As a developer,
I want a `SyncRun` model that is the sole record of run, quota, and failure state,
So that the command, banners, and Settings all read progress from one place (AD-8).

**Acceptance Criteria:**

**Given** the `SyncRun` model (user FK)
**When** a run starts and ends
**Then** it records started, finished, per-outcome counts, overall outcome, `quota_exhausted_at`, and
`acknowledged_at`.

**Given** any consumer of run state
**When** it needs progress or outcome
**Then** it reads only from `SyncRun` — no separate progress store exists.

### Story 7.2: `sync_inbox` command scaffold (idempotent, user-triggerable)

As Alexis,
I want an idempotent `manage.py sync_inbox` that opens a run and lists my `_Inbox`,
So that I can pull my inbox on demand with no scheduler (FR-5, AD-9).

**Acceptance Criteria:**

**Given** a designated `_Inbox`
**When** I run `manage.py sync_inbox`
**Then** it opens a `SyncRun`, lists the `_Inbox` items via the gateway, and closes the run with counts.

**Given** the command
**When** I run it twice in a row
**Then** the second run is safe and produces no duplicate work (idempotent), and no scheduler, cron,
worker, or broker is introduced.

### Story 7.3: Three-way dedupe on import

As a developer,
I want import to suppress re-import of any video already known in any of the three states,
So that deleted videos are never resurrected from a still-populated `_Inbox` (AD-10, FR-5).

**Acceptance Criteria:**

**Given** inbox items
**When** dedupe runs
**Then** a video whose YouTube ID matches an active, soft-deleted, or tombstoned row is **not**
re-imported.

**Given** dedupe suppresses re-import
**When** the same video is a pending-clear orphan
**Then** dedupe does **not** suppress its re-clear (dedupe suppresses re-import only, per AD-7).

### Story 7.4: Transactional import — persist, verify, enqueue clear

As a developer,
I want new videos and their clear-intent committed in one transaction after verify,
So that a crash between local commit and remote clear never destroys the only copy (AD-6, AD-7, FR-5).

**Acceptance Criteria:**

**Given** deduped new items with fetched metadata
**When** import runs
**Then** the order is fetch → persist locally → verify persisted → enqueue clear, and the `Video` rows
plus a `PendingYouTubeOp` clear-intent commit in the **same** database transaction (AD-6).

**Given** a video that failed to import or failed verification
**When** the transaction resolves
**Then** **no** `PendingYouTubeOp` clear is enqueued for it (AD-7).

**Given** a simulated crash between persist and clear (test)
**When** the next run starts
**Then** the video exists locally and its clear is still owed as an undrained row — nothing is lost.

### Story 7.5: Outbox drain and orphan retry

As a developer,
I want a drain that is the only caller of the gateway's removal method, run at start and after import,
So that inbox clears execute exactly once and orphans retry (AD-6, FR-6).

**Acceptance Criteria:**

**Given** undrained `PendingYouTubeOp` rows
**When** a run starts **and** again after import
**Then** the drain calls the gateway removal for each, and it is the **only** code path that does so.

**Given** a removal that fails
**When** the drain handles it
**Then** the row stays as a pending-clear orphan, is retried next run, is never skipped as a duplicate,
and the failure surfaces (never silent) — a test covers the clear-fails path.

**Given** the drain succeeds for a row
**When** it completes
**Then** the row is marked drained and the item is gone from the source `_Inbox`.

### Story 7.6: Reactive quota handling with per-run cap

As Alexis,
I want a run that hits YouTube's quota to stop cleanly and resume next time,
So that a partial import is committed and safe rather than lost (AD-8, NFR-5).

**Acceptance Criteria:**

**Given** a `quotaExceeded` error mid-run
**When** the run detects it reactively
**Then** it stamps `quota_exhausted_at`, commits everything already done, and resumes from the same
point on the next run (never predicts quota).

**Given** a large first import
**When** it runs
**Then** a configurable per-run item cap bounds it, and a test covers quota-mid-run behavior.

### Story 7.7: Structured per-decision sync log

As a developer,
I want one structured log line per sync decision,
So that FR-6 behavior is debuggable (logging convention, FR-6).

**Acceptance Criteria:**

**Given** a run processing items
**When** each decision is made
**Then** one structured line is emitted per decision — imported / skipped-duplicate /
skipped-tombstoned / enqueued-clear / clear-failed — each carrying the YouTube id.

## Epic 8: Browse + search API

The single list endpoint that owns every browse surface, with one documented query grammar.

### Story 8.1: `GET /api/videos/` base with pagination and strict params

As a developer,
I want the base list endpoint with page-number pagination, total counts, ordering, and strict param
validation,
So that every browse surface builds on one contract (AD-4).

**Acceptance Criteria:**

**Given** the endpoint
**When** I request a page
**Then** the response is page-number paginated, always carries a **total count**, and supports
`ordering` (field name, `-` prefix for descending); infinite scroll is not offered.

**Given** an unknown query param
**When** it is sent
**Then** the endpoint returns **400**, not a silent ignore; an omitted param is never a filter.

### Story 8.2: Tag, channel, and watched facets

As Alexis,
I want to filter the Library by tags, channels, and watched state, combined with AND,
So that I can narrow to exactly the set I mean (FR-13, AD-4).

**Acceptance Criteria:**

**Given** repeated `?tag=` params
**When** the query runs
**Then** they combine with **AND** across repeats (never comma-joined).

**Given** repeated `?channel=` params
**When** the query runs
**Then** they combine as OR within the facet and AND against other facets.

**Given** `?watched=true|false`
**When** applied
**Then** it filters accordingly; omitted means no watched filter.

### Story 8.3: Length range and channel-as-filter (FR-12)

As Alexis,
I want to filter by length range and channel,
So that channel and length work as the automatic facets FR-12 promises (FR-12, AD-4).

**Acceptance Criteria:**

**Given** `length_min` / `length_max` in **seconds**
**When** applied
**Then** bounds are inclusive and interpreted as seconds, never minutes.

**Given** a channel filter combined with a length range and a tag
**When** the query runs
**Then** all combine with AND and the result reflects the active set.

### Story 8.4: Derived Uncategorized

As Alexis,
I want an `uncategorized=true` view of videos with no tags and no playlist membership,
So that the triage surface has its set without a stored flag (AD-5, FR-5).

**Acceptance Criteria:**

**Given** `?uncategorized=true`
**When** the query runs
**Then** it returns exactly the videos with no tags **and** no playlist membership, computed at read time.

**Given** a video receives its first tag
**When** the query re-runs
**Then** it leaves the Uncategorized result with no column updated (derived, per AD-5).

### Story 8.5: Full-text search param

As Alexis,
I want a `q` search param over title, description, channel, and tags that composes with facets,
So that search is one mode with browse, not a separate one (AD-11, FR-14).

**Acceptance Criteria:**

**Given** `?q=` combined with facet params
**When** the query runs
**Then** it matches any of title/description/channel/tags via the `tsvector`, AND-composed with the
active facets, using `SearchVector`/`SearchQuery` (no `ILIKE`, no external engine).

**Given** a video is bulk-tagged
**When** I search by that tag
**Then** it is found — the vector was refreshed by the mutating service (AD-11).

### Story 8.6: Library-hub dimension counts

As Alexis,
I want an endpoint returning per-dimension counts for the Library hub,
So that the hub renders shelf rows without fetching full lists (AD-4, supports UX-DR17).

**Acceptance Criteria:**

**Given** the hub counts endpoint
**When** it is called
**Then** it returns tags (most-used first), channels (most-frequent first), and a **bounded**
recently-imported set — each with counts and enough to render a shelf strip.

**Given** a dimension is empty
**When** the hub reads counts
**Then** that dimension returns empty so the client omits the row.

## Epic 9: Mutation API

The write surface for the Library, behind a consistent bulk contract that rolls back per item.

### Story 9.1: Tag CRUD

As Alexis,
I want to create, list, rename, and remove tags,
So that I can manage my tag vocabulary (FR-9, AD-19).

**Acceptance Criteria:**

**Given** tag create
**When** I submit a name that normalises onto an existing tag
**Then** the existing tag is returned (create-or-get), preserving the first display form.

**Given** a rename
**When** I rename a tag
**Then** every application updates (the membership is by tag identity), and the refreshed search vectors
reflect the new name (AD-11).

**Given** a remove
**When** I remove a tag
**Then** it is detached from all videos; videos that thereby lose their last tag become Uncategorized by
derivation (AD-5).

### Story 9.2: Delta tag application on a single video

As Alexis,
I want to add or remove specific tags on one video by delta,
So that a single edit never destroys tags another path just added (AD-19, FR-9).

**Acceptance Criteria:**

**Given** the single-video tag endpoint
**When** I apply changes
**Then** it accepts **`add`/`remove`** id/name lists only and **rejects** any whole-`tags` replacement
array (no endpoint accepts a replacement set).

**Given** concurrent edits (a bulk apply and a single-video edit)
**When** both run
**Then** they compose rather than overwrite.

### Story 9.3: Bulk tag application

As Alexis,
I want to apply tags to a selection of videos in one call with a per-id result,
So that triage files a whole selection in a single action and the UI can roll back per item (FR-7, AD-12, bulk convention).

**Acceptance Criteria:**

**Given** `POST /api/videos/bulk-tag/`
**When** I submit an id list with `add`/`remove` tag deltas
**Then** it applies the delta to each and returns a **per-id outcome** list; partial success is a normal
result, not an error.

**Given** the mutation touches contributing fields/tags
**When** it completes
**Then** it refreshes the affected search vectors via the service (AD-11).

### Story 9.4: Soft-delete single and bulk

As Alexis,
I want to delete videos singly or in bulk with an explicit count confirmation contract,
So that deletion is guarded and recoverable (FR-11, AD-10).

**Acceptance Criteria:**

**Given** single delete and `POST /api/videos/bulk-delete/`
**When** I delete
**Then** each targeted video is soft-deleted (`deleted_at` set), removed from active views and from every
Playlist and Tag membership, and never touches YouTube.

**Given** bulk delete
**When** it returns
**Then** it returns a per-id outcome, and the response carries the count for the UI's mandatory
count-stating confirmation (enforced in E11/E14 UI).

### Story 9.5: Restore, purge, and retention

As Alexis,
I want soft-deleted videos restorable and eventually purged to a tombstone,
So that Trash is recoverable within a window and cleanly finalizes (FR-11, AD-10).

**Acceptance Criteria:**

**Given** a soft-deleted video
**When** I restore it
**Then** `deleted_at` is cleared and it returns to active views in its prior tag/playlist memberships
where still valid.

**Given** the retention purge
**When** it runs (service/command)
**Then** eligible rows are hard-deleted and a `VideoTombstone(youtube_id, purged_at)` is written for each.

### Story 9.6: Bulk-freshness endpoint (schema only)

As a developer,
I want the `bulk-freshness` endpoint shape defined without Phase-1 behavior,
So that Phase 2 freshness is additive against a stable contract (FR-7 note, AD-4 grammar).

**Acceptance Criteria:**

**Given** `POST /api/videos/bulk-freshness/`
**When** the schema is generated
**Then** the endpoint and its request/response shapes exist in the OpenAPI schema (id list → per-id
outcome), with no Phase-1 freshness mutation behavior wired.

## Epic 10: Library hub + browse surfaces

The entry experience and browse-by-intent — the app opens to organizational structure, and every drill-in
lands on a finite, filtered, linkable set.

### Story 10.1: Video card, thumbnail status layer, and view toggle

As Alexis,
I want a video card with its status layer and a grid/list toggle persisted per surface,
So that the app reads as YouTube-familiar content across every browse surface (UX-DR4, UX-DR5, UX-DR13).

**Acceptance Criteria:**

**Given** the video card
**When** it renders
**Then** it shows a 16:9 thumbnail at 12px radius, a 2-line-clamped title, channel, and the tag row, with
no border/fill/shadow, and the `⋮` menu is hover-revealed on pointer and always-visible on touch.

**Given** the card `⋮` menu in Phase 1 (UX-DR4 lists tag · freshness · add-to-playlist · delete)
**When** it opens
**Then** it exposes only the **Phase-1** actions — **Tag** and **Delete** — while **Freshness** (FR-17) and
**Add to playlist** (FR-10) are **Phase 2** and are omitted (not shown as working actions); they appear when
their epics land.

**Given** the thumbnail status layer
**When** a video is watched, unavailable, or expired
**Then** it renders **scrim + status badge** (never scrim alone), duration always renders bottom-right,
and two statuses render two badges side by side.

**Given** the view toggle
**When** I switch grid ⇄ list
**Then** the choice persists **per surface**, not globally.

### Story 10.2: Library hub shelf rows

As Alexis,
I want the Library to render shelf rows of my organizational dimensions, not a video list,
So that there is no chronological feed to scroll past (UX-DR12, UX-DR17, NFR-3).

**Acceptance Criteria:**

**Given** the Library hub
**When** it loads
**Then** it renders one shelf row per dimension — Tags (most-used), Channels (most-frequent), and a
**bounded** Recently-imported strip — each with title, count, a horizontal card strip, and "View more →";
it **never** renders a flat list of all videos.

**Given** a dimension with no items
**When** the hub renders
**Then** that shelf row is omitted entirely rather than shown empty.

**Given** a shelf row on touch
**When** I interact
**Then** it scrolls horizontally and is arrow-key navigable, and "View more →" navigates to a real
surface (never paginates in place).

### Story 10.3: App shell — sidebar, responsive layout, mobile tab bar

As Alexis,
I want the navigation shell with the fixed sidebar on desktop and a tab bar + drawer on mobile,
So that both surfaces are first-class and bounded (UX-DR18, UX-DR19, NFR-8).

**Acceptance Criteria:**

**Given** desktop
**When** the shell renders
**Then** the sidebar shows the fixed, non-scrolling order Library · Uncategorized · Tags · Playlists ·
Needs review · Watched · Trash, with Playlists a **plain link**; active nav is surface tint + 3px edge
bar + `aria-current="page"`.

**Given** the breakpoints
**When** the viewport changes
**Then** `≥xl` sidebar 240 / grid 4, `lg` grid 3, `md` sidebar 72 icons / grid 2, `<md` no sidebar with a
4-tab bottom bar (Library · Uncategorized · Search · More) + drawer, grid **2 (never 1)**.

**Given** the fixed sidebar order includes **Playlists**, **Needs review**, and **Watched**, whose
destination surfaces are all **Phase 2** (`EXPERIENCE.md § IA`)
**When** the shell renders in Phase 1
**Then** those three entries are **omitted** from both the desktop sidebar and the mobile "More" drawer —
never rendered as dead links to surfaces that do not yet exist — while the **relative order** of the
remaining Phase-1 entries (Library · Uncategorized · Tags · Trash) is preserved (UX-DR18); they return in
Phase 2. (Watched-as-a-*filter* remains available in Phase 1 via the Filters panel, Story 10.5 — only the
Watched *lens surface* is deferred.)

### Story 10.4: Tag detail with the tags-only filter chip row

As Alexis,
I want Tag detail with a tags-only filter row whose state lives in the URL,
So that browse-by-intent is linkable and combines tags with AND (UX-DR9, UX-DR10, FR-13).

**Acceptance Criteria:**

**Given** Tag detail
**When** it opens
**Then** it lists videos carrying the tag via `GET /api/videos/`, with a horizontally-scrollable
**tags-only** chip row (most-used first, ending "All tags →") whose active chips invert.

**Given** I add more tag chips
**When** they apply
**Then** they combine with AND, the URL params update 1:1 with the API params, and the view is linkable.

**Given** many results
**When** I page
**Then** it uses pagination or explicit load-more (no infinite scroll).

### Story 10.5: Filters panel

As Alexis,
I want a Filters panel for the structured facets,
So that channel, length, and watched filters compose with the tag chips (UX-DR11, FR-12, FR-13).

**Acceptance Criteria:**

**Given** the Filters panel
**When** it opens
**Then** it offers channel (searchable multi-select), length range (dual slider + numeric second inputs),
and watched; freshness and date range render as **Phase-2-disabled** affordances.

**Given** applied filters
**When** they take effect
**Then** they surface as individually removable chips and map onto the AD-4 query params (length in seconds).

### Story 10.6: Search UI

As Alexis,
I want a global search scopable to the current view that composes with facets,
So that I can find a video by title, description, channel, or tag (FR-14, UX-DR).

**Acceptance Criteria:**

**Given** the search entry (`/` or top bar)
**When** I type a query
**Then** it runs globally via the `q` param, composes with active facets, and can be scoped to the
current view.

**Given** no matches
**When** results return empty
**Then** the empty-search state lists active filters as individually clearable (the usual cause), not a
dead end.

### Story 10.7: Tags index management UI

As Alexis,
I want a Tags index to create, rename, and remove tags,
So that I can curate my vocabulary from one surface (FR-9 UI, AD-19).

**Acceptance Criteria:**

**Given** the Tags index
**When** I create a tag whose name normalises onto an existing one
**Then** the UI resolves to the existing tag rather than creating a duplicate.

**Given** rename and remove
**When** I perform them
**Then** the UI reflects the API outcome (rename updates everywhere; remove detaches from all videos),
with a non-suppressible confirmation on remove.

### Story 10.8: Browse state patterns and accessibility floor

As Alexis,
I want skeletons, error/empty states, and the accessibility floor across browse surfaces,
So that the surfaces behave correctly under load, failure, and assistive tech (UX-DR28, UX-DR30, NFR-7).

**Acceptance Criteria:**

**Given** a cold load
**When** data is pending
**Then** the active view's shadcn `Skeleton` shape renders (card/row/shelf) — never a spinner.

**Given** a fetch/server error
**When** it occurs
**Then** an inline banner with an explicit Retry shows, and cached data stays visible beneath rather than
being replaced by an error screen; an empty filter result shows "No videos match these filters" with
"Clear all".

**Given** assistive tech
**When** I navigate browse
**Then** no state is conveyed by color alone, `Tab` order matches reading order, focus is never obscured
(scroll-margin), decorative thumbnails use `alt=""` with the title as the accessible name, and it passes
AA in light and dark.

## Epic 11: Triage surfaces

The weekly loop's UI, held to the ≤2-interaction bound on both desktop and mobile.

### Story 11.1: Uncategorized list mode with selection

As Alexis,
I want Uncategorized in a dense list with checkbox, shift-range, and keyboard selection,
So that I can rapidly select batches for tagging (UX-DR21, UX-DR6, FR-7).

**Acceptance Criteria:**

**Given** Uncategorized in list mode
**When** it loads
**Then** it shows the densest legible rows and is the default triage view.

**Given** selection
**When** I click a checkbox, shift-click a range, press `x` on the focused row, or press `a`
**Then** the corresponding items (or all loaded) become selected, shown by solid outline + filled
checkbox (both, achromatic), and `Esc` clears.

### Story 11.2: Bulk action bar

As Alexis,
I want a sticky bulk action bar with a live count and selection-bound actions,
So that one action applies to a whole selection (UX-DR8, NFR-1, FR-7).

**Acceptance Criteria:**

**Given** ≥1 item selected
**When** the bar appears
**Then** it is sticky at the bottom (above the mobile tab bar), shows the live count via `aria-live`, and
offers the action set with **all destructive actions bound to the selection** (never on individual cards).
In **Phase 1** the live actions are **Tag** and **Discard**; **Freshness** (FR-17) and **Add to playlist**
(FR-10) are **Phase 2** and render **disabled/omitted** (mirroring the Phase-2-disabled treatment of the
Filters panel in Story 10.5), never as working buttons over a schema-only or absent backend.

**Given** the count changes
**When** selection updates
**Then** the announced count always reflects the true selection.

**Given** the **Tag** action opens the tag typeahead (also reachable via the `t` shortcut, Story 11.6)
**When** I type a tag name and apply it to the selection
**Then** the typeahead does **create-or-get on normalised identity** (trimmed, whitespace-collapsed,
case-folded — AD-19), so ` Guitar ` resolves onto an existing `guitar` rather than creating a second tag;
it is **keyboard-operable** end to end (type, arrow to a match, `Enter` to apply, `Esc` to close), visibly
**distinguishes an existing match from creating a new tag**, and is **focus-scoped** so triage single-key
shortcuts are inert while it has focus (NFR-7, WCAG 2.1.4).

### Story 11.3: Optimistic bulk tag with per-row revert

As Alexis,
I want tags to apply instantly and only failed rows to revert,
So that a partial failure never undoes my whole sweep (AD-12, UX-DR23, FR-7).

**Acceptance Criteria:**

**Given** a bulk tag apply
**When** it is issued
**Then** the affected rows optimistically leave the Uncategorized list cache via the query-key factory,
with an `onMutate` snapshot.

**Given** a partial failure
**When** the per-id result returns
**Then** **only the failed ids** are restored, the failure surfaces a toast, reverted rows re-announce via
`aria-live`, and broad prefix invalidation during the active selection does not occur.

### Story 11.4: Focus mode (tag-first bucketing)

As Alexis,
I want a tag-first Focus mode where I pick tags then sweep matches,
So that a week's catch is filed the way it actually clusters (UX-DR22, FR-7).

**Acceptance Criteria:**

**Given** Focus mode
**When** I pick one or more tags
**Then** the header pins "Filing as: `guitar` + `course`", and I toggle matches by click/tap only — no
dialogs, no per-video menus.

**Given** a swept selection
**When** I press Apply
**Then** the whole selection is filed with the entire tag set in one action, and switching between List
and Focus preserves state.

### Story 11.5: Discard flow with count confirmation

As Alexis,
I want discard bound to the selection with a single count-stating confirmation,
So that one dialog covers a whole sweep and no destructive action is suppressible (UX-DR14, UX-DR24, FR-11).

**Acceptance Criteria:**

**Given** a selection
**When** I discard
**Then** a single non-suppressible `AlertDialog` states the count and consequence ("Delete 6 videos? They
move to Trash."), with focus on Cancel.

**Given** a single-card discard
**When** I trigger it
**Then** it also confirms (the rule applies uniformly), and confirmed discards call `bulk-delete`.

### Story 11.6: Keyboard shortcuts, WCAG 2.1.4 trio, and touch model

As Alexis,
I want triage shortcuts on desktop and long-press selection on touch, with the mandated shortcut controls,
So that both input models are first-class and accessible (UX-DR7, UX-DR25, UX-DR26, UX-DR27, NFR-7).

**Acceptance Criteria:**

**Given** desktop
**When** I use `j`/`k`, `x`, `a`, `t`, `f`, `Backspace`/`Del`, `Enter`, `v`, `/`, `g`+`l`/`u`/`t`/`p`, `Esc`
**Then** each performs its triage action, and the focus indicator is a **dashed** ring distinct from
selection.

**Given** the WCAG 2.1.4 requirement
**When** I open Settings
**Then** a disable toggle, per-binding remapping, and focus scoping exist (shortcuts inert inside text
inputs, the tag typeahead, dialogs, and the player iframe), discoverable not buried.

**Given** touch
**When** I long-press
**Then** selection mode enters and tap toggles; all tap targets are ≥24px and list rows relax to 44px.

### Story 11.7: Incremental triage and the win state

As Alexis,
I want to stop mid-sweep with no penalty and see a quiet win state when empty,
So that a partially-triaged Library is first-class and never nags (UX-DR24, UX-DR28, NFR-2).

**Acceptance Criteria:**

**Given** a mid-sweep filter narrowing
**When** selected items become hidden
**Then** they are not silently dropped and the bar's count still tells the truth.

**Given** I abandon triage
**When** I leave
**Then** what I filed is immediately browsable, the rest waits with **no badge** on Uncategorized, and no
"mark as done" step exists.

**Given** an empty Uncategorized
**When** it renders
**Then** it shows "Nothing to file." — dry, no celebration, with a quiet link back to Library.

## Epic 12: Watch + playback

The payoff surface — watch inside the app, away from the recommendation machinery, with honest auto-Watched.

### Story 12.1: Watch page layout (single column, no rail)

As Alexis,
I want a single-column watch page with no rail at any breakpoint,
So that the app never occupies the region YouTube trains the eye to look for "what's next" (UX-DR20, NFR-3, FR-15).

**Acceptance Criteria:**

**Given** the watch page
**When** it renders at any breakpoint
**Then** it is a single centered column capped at 1280px with **no right rail** (absent from the layout,
not collapsed), showing the player, title, channel, the tag row, and a collapsed description behind "more".

### Story 12.2: Embedded IFrame player with open-in-YouTube

As Alexis,
I want an embedded player with no autoplay-next and an open-in-YouTube handoff,
So that I watch in-app but can hand off for background audio (FR-15, NFR-3).

**Acceptance Criteria:**

**Given** the embed
**When** a video plays
**Then** it uses the YouTube IFrame Player API with native controls, exposes no in-app recommendation
feed, and never autoplays the next video.

**Given** the background-audio case
**When** I choose open-in-YouTube
**Then** the app hands off to YouTube (the embed's tab-blur/lock pause limitation is stated as fact, not
an error).

### Story 12.3: Contiguous-coverage auto-Watched

As Alexis,
I want a video marked Watched only after I actually cover enough of it,
So that seeking to the end does not falsely mark it watched (AD-15, FR-16).

**Acceptance Criteria:**

**Given** playback
**When** the client tracks progress
**Then** it measures **contiguous covered duration** via the IFrame API, never furthest position reached.

**Given** covered duration crosses the configurable threshold
**When** the crossing is genuine
**Then** exactly one `PATCH` sets Watched, the badge shows, and the video **stays in place**; seeking to
the end without coverage does not mark it.

**Given** Watched state
**When** I toggle it manually
**Then** it updates, and playback position is **not** persisted (no resume).

### Story 12.4: Inline tag editing on the watch page

As Alexis,
I want to add and remove tags on the watch page without leaving it,
So that I can refine tags at watch time by delta (AD-19, FR-9).

**Acceptance Criteria:**

**Given** the watch-page tag row
**When** I add or remove a tag
**Then** it issues an `add`/`remove` **delta** (never a replacement set), composing with any concurrent edit.

**Given** more than three tags
**When** the row renders
**Then** overflow collapses to `+N` opening a keyboard-operable popover (`Esc` closes, focus returns to
the trigger).

### Story 12.5: Unavailable-video state at play time

As Alexis,
I want a clear message instead of a broken player when a video is gone from YouTube,
So that a sole-home library degrades gracefully (FR-15 "never a broken player"; client-observed-state convention).

**Acceptance Criteria:**

**Given** a video the embed cannot play
**When** I open it
**Then** the card/watch page shows scrim + ⚠ badge with play disabled and the message "This video is no
longer available on YouTube.", offering open-in-YouTube and delete — never a broken player.

**Given** the browser discovers unavailability
**When** it reports it
**Then** it posts to a **dedicated** service endpoint (never a generic resource `PATCH`), so services
remain the only writer (AD-1).

## Epic 13: Settings + sync status

The control surface — trigger and monitor sync, manage the Google connection and `_Inbox`, set preferences.

### Story 13.1: Settings shell, Google connection, and read-only notice

As Alexis,
I want a Settings surface showing my Google connection with re-consent and the read-only notice,
So that I can see and repair my auth state (FR-1 UI, AD-14).

**Acceptance Criteria:**

**Given** Settings
**When** it loads
**Then** it shows Google connection status and a re-consent action.

**Given** read-only scope
**When** Settings renders
**Then** a persistent notice states that inbox auto-clear and playlist deletion are disabled while
everything else works, and offers re-consent.

### Story 13.2: `_Inbox` designation UI

As Alexis,
I want to choose, change, or create my `_Inbox` from Settings,
So that I control my capture on-ramp (FR-2 UI).

**Acceptance Criteria:**

**Given** the designation screen
**When** I open it
**Then** my playlists are listed for selection, my current designation is shown, and choosing one
persists it (effective next import).

**Given** no suitable playlist
**When** I choose "create one"
**Then** the app creates and designates an `_Inbox` (disabled with the notice in read-only mode).

**Given** the `_Inbox` no longer exists
**When** Settings/global banner renders
**Then** it shows "The playlist set as `_Inbox` no longer exists." with an action to choose another.

### Story 13.3: Sync now trigger and sync status

As Alexis,
I want a "Sync now" action and a status read from `SyncRun`,
So that I pull my inbox on demand and see the outcome (AD-8, AD-9, UX-DR16).

**Acceptance Criteria:**

**Given** Settings/inline banner
**When** I tap **Sync now**
**Then** it triggers the sync and shows a non-blocking "Checking `_Inbox`…" banner while the app stays
fully usable; there is **no** "next scheduled run" line in Phase 1.

**Given** a completed run
**When** status renders
**Then** it reports the last successful sync and any pending-clear orphans, read **only** from `SyncRun`.

**Given** a completed sync
**When** it settles
**Then** a toast "87 videos imported." shows, suppressed if I am mid-sweep.

### Story 13.4: Sync banners — partial failure, orphans, quota, failure

As Alexis,
I want banners that tell me what the app will do next when sync is imperfect,
So that a partial import is never mistaken for a complete one (UX-DR15, UX-DR28, UX-DR29, FR-6, NFR-5).

**Acceptance Criteria:**

**Given** a partial failure
**When** it occurs
**Then** an inline banner shows "83 of 87 imported. 4 failed and stayed in `_Inbox`." with expandable
detail, never silent, never auto-dismissing.

**Given** pending-clear orphans
**When** they exist
**Then** a banner shows "N videos imported but not removed from `_Inbox`. Retrying next sync."
(informational, no action demanded).

**Given** quota exhaustion mid-sync
**When** it happens
**Then** the banner shows "YouTube's daily limit reached. 41 of 100 imported. Resuming tomorrow." and
**persists until explicitly acknowledged** (sets `acknowledged_at`); a full failure shows "Last sync
failed at {time}." with manual retry.

### Story 13.5: Theme and watched threshold

As Alexis,
I want to set the theme and the watched threshold,
So that the app fits my environment and my definition of "watched" (UX-DR, FR-16).

**Acceptance Criteria:**

**Given** the theme control
**When** I switch
**Then** both light and dark render at AA, and the choice persists (wrapped in try/catch for storage).

**Given** the watched threshold setting
**When** I change it
**Then** the value drives the FR-16 coverage comparison (the measurement is fixed; the number is mine).

### Story 13.6: Platform-limitation statements and voice pass

As Alexis,
I want honest statements of platform limits and dry microcopy throughout Settings,
So that accepted limits are stated as fact, never surfaced as errors (UX-DR29, NFR-15).

**Acceptance Criteria:**

**Given** Settings
**When** it renders the limitations section
**Then** it states, as plain fact, that background/lock-screen playback is impossible in-app (open-in-
YouTube covers it) and that the embed's end screen shows recommendations.

**Given** all Settings and sync microcopy
**When** reviewed against the voice table
**Then** it is dry and factual — no exclamation marks, no celebration — and every error states what the
app will do next.

## Epic 14: Trash

The safety net for deletion — recoverable within the window, then cleanly finalized to a tombstone.

### Story 14.1: Trash surface with restore

As Alexis,
I want a Trash surface listing recently-deleted videos with restore,
So that deletion is recoverable within the retention window (FR-11 UI, AD-10).

**Acceptance Criteria:**

**Given** the Trash surface (sidebar)
**When** it loads
**Then** it lists soft-deleted videos within the retention window, each restorable.

**Given** I restore a video
**When** the action completes
**Then** it returns to active views and its still-valid tag/playlist memberships, leaving Trash.

**Given** a completed deletion elsewhere
**When** the toast shows
**Then** it reads "14 videos deleted." with **no undo affordance** (the confirmation already did that
job); Trash is where recovery lives.

### Story 14.2: Retention purge to tombstone

As Alexis,
I want Trash to purge past the retention window and prevent resurrection,
So that permanently deleted videos never come back on the next sync (FR-11, AD-10, AD-20).

**Acceptance Criteria:**

**Given** videos past the retention window
**When** the purge runs
**Then** each row is hard-deleted and a `VideoTombstone(youtube_id, purged_at)` is written.

**Given** a tombstoned video still present in a populated `_Inbox`
**When** the next sync runs
**Then** the three-way dedupe (E7) suppresses its re-import — it is never resurrected.
