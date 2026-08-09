---
title: 'CI gate stack — rewrite ci.yml and add pre-push onto this repo''s real commands'
type: 'chore'
created: '2026-08-09'
status: 'done'
baseline_commit: '7d23ab6'
review_loop_iteration: 1
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
