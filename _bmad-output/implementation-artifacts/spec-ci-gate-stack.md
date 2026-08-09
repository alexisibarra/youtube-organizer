---
title: 'CI gate stack — rewrite ci.yml and add pre-push onto this repo''s real commands'
type: 'chore'
created: '2026-08-09'
status: 'done'
baseline_commit: '7d23ab6'
review_loop_iteration: 2
context:
  - '{project-root}/Docs/CI-AND-GITHUB-GATES.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `.github/workflows/ci.yml` is a verbatim Accountr copy built on Nx + pnpm + Prisma + `apps/**`/`libs/**`, none of which exist here (AD-2) — every trigger path is wrong and every command unrunnable, so the repo has no working CI. There is no `pre-push` hook at all.

**Approach:** Rewrite `ci.yml` onto this repo's real commands using the translation table already in `Docs/CI-AND-GITHUB-GATES.md`, keeping Accountr's proven shape (path-filtered triggers, `concurrency` cancel-in-progress, `typecheck + lint → test → build`, a `postgres:15` service). Add `.githooks/pre-push` running the same layers locally. Gates whose tooling doesn't exist yet are omitted with a TODO naming the owning story — never wired up as permanently-failing or `continue-on-error` noise.

## Boundaries & Constraints

**Always:**
- Every job runs a command that exists today and passes on the current tree. CI must be green on its first run.
- Frontend commands run in `frontend/`, backend in `backend/`. No `pnpm`, no `nx` (AD-2).
- Triggers: push and PR to `main`/`develop`, **no paths filter** (amended 2026-08-09 — see Spec Change Log).
- Node version comes from `frontend/.nvmrc` in every JS job; never hardcoded in the workflow.
- The test job must set `POSTGRES_HOST: localhost` to reach the service container — the settings default is `db`, the compose service name.
- `.githooks/pre-push` is committed with the executable bit set.

**Ask First:**
- Adding any dependency to `frontend/package.json` or `backend/requirements.txt`.
- Any change to `frontend/src` beyond the single typing fix below.
- Making any job `continue-on-error` — the human chose enforcing gates.

**Never:**
- Do not touch `.github/workflows/deploy.yml`; do not add `push-to-ghcr`. Deploy and registry push are deferred whole (AD-17, `Docs` §6).
- Do not add a frontend test job, a coverage threshold, or the OpenAPI drift gate — the Jest/RTL harness (story 2-5) and the codegen pipeline (3-1/3-3/3-4) don't exist yet.
- Do not add changesets (superseded, `Docs` §5) or `fetch-depth: 0` (no affected graph needs history).
- No AI/bot attribution in any file, commit, or PR body.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Docs-only PR | Only `Docs/**` changed | All four jobs run and pass, so required checks always report | N/A |
| Second push to same PR | Run in flight for the ref | In-flight run cancelled, new one starts | N/A |
| Type error introduced | TS error in `frontend/` | `typecheck` fails; `test`/`build` never run | Job exits non-zero |
| Missing Django migration | Model changed, no migration file | `test` fails at `makemigrations --check` | Non-zero, names the model |
| Backend run with zero tests | `organizer/tests.py` empty | `manage.py test` builds the test DB, exits 0 | N/A |
| `pre-push`, stack down | Postgres unreachable locally | DB-free layers run; backend tests skipped with a loud warning naming `make up` | Push proceeds — CI is the authoritative DB gate |

</frozen-after-approval>

## Code Map

- `.github/workflows/ci.yml` -- the Accountr placeholder being fully replaced
- `.github/workflows/deploy.yml` -- deferred; **read-only reference, do not edit**
- `.githooks/pre-commit` -- existing branch guard; new `pre-push` sits beside it, unchanged
- `backend/youtube_organizer/settings.py:117-125` -- the `POSTGRES_*` env contract
- `frontend/package.json` -- only `dev`/`build`/`start`/`lint`; no `test` or `type-check` script, so typecheck calls `npx tsc --noEmit` directly

## Tasks & Acceptance

**Execution:**
- [x] `frontend/src/app/hooks/usePlaylists.ts:33` -- replace `(item: any)` with a local `YouTubePlaylistItem` type covering only the fields read -- unblocks lint and build without an `eslint-disable`; preserve the `maxres → high → medium → default` fallback exactly
- [x] `.github/workflows/ci.yml` -- full rewrite to the four jobs in Design Notes -- replaces unrunnable Nx/pnpm/Prisma commands
- [x] `.githooks/pre-push` -- new executable hook: tsc → lint → build → `manage.py check` → `manage.py test` (DB-gated), blocking the push on any failure (`Docs` §1)
- [x] `Docs/CI-AND-GITHUB-GATES.md` -- replace the §0 "the commands below are Accountr's" banner with a note that §1–§2 are now implemented here; keep the §5/§6 deferrals and the AD-3 drift-gate note -- the doc must not keep calling live CI a placeholder
- [x] `_bmad-output/project-context.md:185-204` -- rewrite the "CI & GitHub Gates" block to describe the real job graph and hook, retaining the deploy/ghcr/drift-gate deferrals -- agents read this file first

**Acceptance Criteria:**
- Given the tree at this branch's tip, when CI runs on the PR, then all four jobs pass with no `continue-on-error` and no skipped-but-required job.
- Given a developer with `core.hooksPath` set and the stack down, when they `git push`, then the DB-free layers run, a visible warning reports the skipped backend tests, and the hook exits 0.
- Given `deploy.yml`, when the PR diff is inspected, then that file is unchanged.

### Review Findings

_Code review 2026-08-09 (review loop iteration 2) — Blind Hunter + Edge Case Hunter + Acceptance Auditor._

**Decisions resolved 2026-08-09:** (1) hook reads `.nvmrc` and **blocks** on mismatch, `.nvmrc` re-pinned exactly; (2) frontend layers **keep blocking** — the host install is a documented prerequisite and `Makefile` now installs the same tree; (3) `build: needs: [typecheck, test]` **reaffirmed as specified** — the frozen Design Notes graph stands, so that finding is dismissed rather than patched.

- [x] [Review][Decision→Patch] **`.nvmrc` parity between CI and the hook does not exist, and the pin was loosened** — `ci.yml:45,67,148`, `Docs/CI-AND-GITHUB-GATES.md:32` and `project-context.md:200` all claim `.nvmrc` is "shared with the pre-push hook" / that CI and the hook "cannot diverge again". `.githooks/pre-push` never reads `.nvmrc` (`grep -rn nvmrc .githooks/` → nothing); it runs whatever `npm`/`node` is on PATH, so the exact Node-20-vs-22 drift the change log says was fixed can recur silently. Separately `v20.17.0 → v22` traded an exact pin for a floating major, so two CI runs a week apart can resolve different 22.x builds. Needs a call on enforcement (hook reads `.nvmrc` and warns / blocks / nothing, with the claims reworded to match) and on pin granularity.
- [x] [Review][Decision→Patch] **`pre-push` blocks on missing frontend deps while skipping missing backend deps** — `.githooks/pre-push:34,40` exit 1 when `npm` is off PATH or `frontend/node_modules/.bin/tsc` is absent, contradicting the skip-not-fail rationale the header applies to the backend. The frontend is equally Docker-based here: `docker-compose.yml:37` mounts `frontend_node_modules` as a named volume, so a developer who followed `make up` has no host `frontend/node_modules` and cannot push at all. Aggravating: the hook demands `npm ci` while `Makefile:13` (`frontend-install`) runs `npm install`. Either both sides skip or both sides block — the asymmetry is unargued and the frozen I/O matrix has no row for it.
- [x] [Review][Decision→Dismissed] **`build: needs: [typecheck, test]` serialises the frontend gate behind the backend** — `ci.yml:140`. A frontend-only PR cannot build until pip install + `postgres:15` + `migrate` + an empty Django suite complete, and a backend flake stops the `build` required check from ever reporting. The two jobs share no artifacts; the dependency is inherited from Accountr's graph, which the frozen Design Notes copied.
- [x] [Review][Patch] **Node 22 rollout stops at CI — the documented dev runtime still runs Node 20** [frontend/Dockerfile:2] — `FROM node:20-alpine` while `.nvmrc` moved to `v22`, so `make up` (the documented workflow) builds and runs the app on a different major than CI. `frontend/package.json:22` also still declares `@types/node: ^20`, and there is no `engines` field to catch a Node-20 shell.
- [x] [Review][Patch] **`project-context.md` no longer describes the hook it documents** [_bmad-output/project-context.md:214-217] — it omits `makemigrations --check --dry-run` (layer 5 of 6) from the layer list; claims "Every other layer is unconditional" when `backend_unavailable()` (`pre-push:67-80`) exits 0 before *all four* backend layers whenever Django is not importable; and describes the skip condition as "Postgres unreachable on `localhost:5432`" when the probe opens a settings-resolved Django connection. This is the file agents are told to read first.
- [x] [Review][Patch] **A partially installed Python environment blocks the push instead of skipping** [.githooks/pre-push:79] — the gate is `import django` alone. A system `python3` with Django but without `psycopg2` (only in `backend/requirements.txt`, normally installed into `.venv` or the container) passes the probe, then `makemigrations --check --dry-run` dies on the postgres backend import and `fail()` blocks the push — violating the KEEP item "the hook must SKIP (never fail) backend layers".
- [x] [Review][Patch] **`Docs` §0 still describes live CI as ending in a ghcr push** [Docs/CI-AND-GITHUB-GATES.md:59] — "GitHub Actions CI — typecheck → lint → test (with DB) → build → (on `main`) push Docker images". This line sits outside the new banner and is not flagged as an Accountr snippet, so it reads as the implemented graph; `ci.yml` has four jobs and no ghcr step (a frozen Never constraint).
- [x] [Review][Patch] **Both availability probes swallow stderr, so misconfiguration is reported as absence** [.githooks/pre-push:79,101] — `2>/dev/null` on both. A settings `ImportError`, a wrong `POSTGRES_PASSWORD`, or a broken venv all render as "Django is not importable" / "no reachable database"; the hook prints a reassuring ⚠️ and exits 0. The comment above the DB probe advertises that it cannot be fooled by a bare TCP listener while the redirect guarantees the real reason is invisible.
- [x] [Review][Patch] **"Each is a named TODO in `ci.yml`" is false** [.github/workflows/ci.yml:8-13] — both `Docs` and `project-context.md:210` assert the deferred gates are named TODOs in the workflow. `grep -c TODO .github/workflows/ci.yml` → 0. The header comment names the owning stories but carries no TODO marker, so the grep the claim invites finds nothing.
- [x] [Review][Patch] **`.githooks/pre-commit` still declares the pre-push gate unbuilt** [.githooks/pre-commit:11-13] — "The four-layer pre-push gate … is intentionally NOT here yet — it is owned by Epic 3 Story 3.6". Story 3-6 is set to `review` in this very diff and `.githooks/pre-push` sits beside it.
- [x] [Review][Patch] **The step counter misreports the skip path** [.githooks/pre-push:67-76] — steps are labelled `[1/6]`…`[6/6]`, but `backend_unavailable()` exits 0 right after `[3/6]`, so the developer sees a run that stopped at 3 of 6 followed by "Proceeding with push", which reads as a truncation rather than a decision.
- [x] [Review][Defer] **`postgres:15` (CI + root compose) vs `postgres:16` (`backend/docker-compose.yml:3`)** — deferred, pre-existing; already tracked in `deferred-work.md` as Story 1.1 Risk R5, and the hook now points developers at `make up` without resolving which compose file that is.
- [x] [Review][Defer] **The hook fixes the stdin hazard per-consumer rather than per-hook** [.githooks/pre-push:106] — deferred, pre-existing class. `--noinput` fixes Django, but `npm run lint`, `next build`, `manage.py check` and `makemigrations` all inherit the same ref list on stdin; closing stdin once (`exec </dev/null`) would close the class. Extends the existing `deferred-work.md` stdin entry.

## Spec Change Log

### 2026-08-09 — review iteration 1

**Finding (both reviewers, independently):** the frozen trigger-paths requirement is incompatible with
the required-status-checks rule in `Docs` §7. GitHub does not synthesize a passing result for a
filtered-out job, so a docs-only PR — the `docs/*` branch class `CLAUDE.md` sanctions — would sit
permanently on "Expected — waiting for status to be reported" and be unmergeable except by admin
override. Latent today (no branch is protected; `main` does not yet exist), live the moment protection
is configured, which is the point of this work.

**Amended:** human renegotiated the frozen Boundaries. The paths filter is removed entirely — all four
jobs run on every push/PR to `main`/`develop`. This also dissolves the `Dockerfile*` pattern, which
could never match: GitHub path patterns are repo-root-relative and both Dockerfiles live under
`frontend/` and `backend/`, already covered.

**Also amended:** Node version is no longer hardcoded. `frontend/.nvmrc` moved `v20.17.0` → `v22` and
all three JS jobs use `node-version-file`, so CI and the pre-push hook cannot diverge again. The
previous state ran the hook on Node 20 and CI on Node 22, defeating the hook's purpose.

**Known-bad state avoided:** a CI stack that looks complete but silently cannot gate merges, plus a
local hook whose green result does not predict CI.

**KEEP on any re-derivation:**
- The empty-suite exit-0 behaviour of `manage.py test` is verified, not assumed — CI stays green today.
- The hook must SKIP (never fail) backend layers when Django or the DB is unreachable: the documented
  backend workflow is Docker-based, so a fresh clone has no `.venv`.
- `manage.py test --noinput` is mandatory in the hook — git supplies the ref list on stdin, which Django
  would otherwise consume as the answer to its stale-test-database prompt.
- The hook must NOT run `manage.py migrate`: that would mutate the developer's dev database as a side
  effect of pushing. `makemigrations --check --dry-run` is DB-free and catches the case that matters.
- The DB probe must open a real Django connection, not a bare TCP connect to 5432.
- `cancel-in-progress` must stay scoped to pull requests only.

## Design Notes

**Job graph** (mirrors `Docs` §2; `push-to-ghcr` deliberately absent):

```
typecheck ─┐
lint ──────┴─▶ test ─▶ build      (test needs [typecheck, lint]; build needs [typecheck, test])
```

- `typecheck` / `lint` / `build`: `setup-node@v4` Node 22, `cache: npm` with `cache-dependency-path: frontend/package-lock.json`, `npm ci` in `frontend/`, then `npx tsc --noEmit` / `npm run lint` / `npm run build`.
- `test`: `setup-python@v5` Python 3.13, `pip install -r backend/requirements.txt`, `postgres:15` service (creds `postgres/postgres`, DB `youtube_organizer`, `pg_isready` health check, port 5432). Steps: `makemigrations --check --dry-run` → `migrate` → `test`.

**Why `next build` is a real gate:** it runs ESLint *and* type-checking during compilation, catching what the Turbopack dev server hides. That is also why it fails today on the same line lint does.

**`pre-push` DB gating:** `manage.py test` builds a test database, so it can't run with the stack down. The hook probes reachability and skips only that layer, loudly; every other layer is unconditional.

**Story mapping:** covers backlog stories `3-5` (CI rewrite) and `3-6` (hooks), pulled forward ahead of Epic 3's E1/E2 dependencies. `3-4` (drift gate) stays in the backlog.

## Verification

**Commands:**
- `cd frontend && npx tsc --noEmit && npm run lint && npm run build` -- expected: exit 0 (lint and build currently exit 1)
- `cd backend && .venv/bin/python manage.py check` -- expected: "System check identified no issues"
- `test -x .githooks/pre-push && python3 -c "import yaml;yaml.safe_load(open('.github/workflows/ci.yml'))"` -- expected: exit 0
- `grep -nE 'nx|pnpm|prisma|apps/|libs/' .github/workflows/ci.yml` -- expected: no matches
- `git diff --stat origin/develop -- .github/workflows/deploy.yml` -- expected: empty output

**Manual checks:**
- `git config core.hooksPath .githooks`, then a real `git push` on this branch: hook output shows each layer, and a failure in any layer aborts the push.

## Suggested Review Order

**The merge-gate decision (start here)**

- No paths filter — the one non-obvious choice; filtered-out jobs never report a status.
  [`ci.yml:15`](../../.github/workflows/ci.yml#L15)

- Cancel superseded PR runs only, so a tagged `main` commit keeps a real CI record.
  [`ci.yml:26`](../../.github/workflows/ci.yml#L26)

**What CI actually runs**

- Node resolved from `.nvmrc`, not hardcoded — CI and the hook cannot drift apart.
  [`ci.yml:43`](../../.github/workflows/ci.yml#L43)

- `POSTGRES_HOST: localhost` overrides the `db` compose default; the test job dies without it.
  [`ci.yml:100`](../../.github/workflows/ci.yml#L100)

- Migration drift check runs before tests — the cheapest failure to catch.
  [`ci.yml:124`](../../.github/workflows/ci.yml#L124)

**The hook's two deliberate divergences from CI**

- Header states both divergences up front: skip-not-fail, and no `migrate`.
  [`pre-push:5`](../../.githooks/pre-push#L5)

- Backend layers skip (never block) when Django is absent — Docker is the documented workflow.
  [`pre-push:67`](../../.githooks/pre-push#L67)

- Real Django connection, not a bare TCP probe: any listener on 5432 would pass that.
  [`pre-push:94`](../../.githooks/pre-push#L94)

- `--noinput` — git feeds the ref list on stdin, which Django would eat as a prompt answer.
  [`pre-push:103`](../../.githooks/pre-push#L103)

**Supporting**

- The typing fix that made lint and build pass; runtime behaviour deliberately unchanged.
  [`usePlaylists.ts:18`](../../frontend/src/app/hooks/usePlaylists.ts#L18)

- `v20.17.0` → `v22`, now the single source of truth for both CI and nvm.
  [`.nvmrc:1`](../../frontend/.nvmrc#L1)

- Corrected warning: the PR template exists and is unsatisfiable, contra my first draft.
  [`project-context.md:193`](../project-context.md#L193)
