# CI & GitHub Gates Reference (mirrored from Accountr)

> How we gate code in this project: local git hooks, GitHub Actions CI, the PR template, changesets, and deployment. Mirror this setup on the other project. Everything below is read from the live `.github/`, `.githooks/`, and `.changeset/` config — it is what actually runs, not aspiration.

## 0. Overview — the gate stack

Code passes through four layers before it reaches production:

1. **Pre-PR gates (manual, developer-run)** — type-check, prod build, visual verification, dependency check. See `docs/FRONTEND-STACK.md` §8 and the project CLAUDE.md.
2. **Local `pre-push` git hook** — runs the full CI pipeline locally before a push leaves the machine.
3. **GitHub Actions CI** — typecheck → lint → test (with DB) → build → (on `main`) push Docker images.
4. **Deploy workflow** — manual `workflow_dispatch` to the Linux server over SSH.

Branch flow: `feat/story-* ──PR──▶ develop ──PR──▶ main (tag vX.Y.Z)`.

---

## 1. Local git hook — `pre-push`

Hooks are **tracked in the repo** under `.githooks/` and activated via git config (not `.git/hooks`, which is untracked). Each dev must run this once after cloning:

```bash
git config core.hooksPath .githooks
```

### `.githooks/pre-push`

Runs the full pipeline across **all** projects and blocks the push on any failure:

```bash
#!/bin/bash
# Pre-push hook: Run CI pipeline before allowing push
echo "Running CI checks before push..."

pnpm exec nx run-many -t test --coverage && \
pnpm exec nx run-many -t lint && \
pnpm exec nx run-many -t build

if [ $? -ne 0 ]; then
  echo "❌ CI checks failed. Fix errors before pushing."
  exit 1
fi

echo "✅ All CI checks passed. Proceeding with push..."
exit 0
```

> Rationale: catch failures locally before they burn a CI cycle. `tsx`/esbuild (dev server) hides type errors and phantom-dependency resolution that webpack (build) does not — the local build step surfaces them early.

**Optional companion hook (recommended):** a `pre-commit` hook that blocks direct commits to `main`/`develop`, forcing all work onto `feat/story-*` branches. Add to `.githooks/pre-commit`:

```bash
#!/bin/bash
branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$branch" = "main" ] || [ "$branch" = "develop" ]; then
  echo "❌ Direct commits to $branch are forbidden. Use a feat/story-* branch."
  exit 1
fi
```

---

## 2. GitHub Actions — `.github/workflows/ci.yml`

### Triggers

Runs on **push** and **pull_request** targeting `main` or `develop`, but only when relevant paths change:

```yaml
on:
  push:
    branches: [main, develop]
    paths: ['apps/**', 'libs/**', 'pnpm-lock.yaml', '.github/workflows/ci.yml', 'Dockerfile*', 'nx.json', 'package.json']
  pull_request:
    branches: [main, develop]
    paths: [ ... same ... ]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true    # new push cancels the in-flight run for the same ref
```

### Jobs & dependency graph

```
typecheck ─┐
lint ──────┤
           ├─▶ test ─▶ build ─▶ push-to-ghcr (main only)
           │    ↑
typecheck ─┴────┘   (test needs [typecheck, lint]; build needs [typecheck, test])
```

Common setup for every job: `actions/checkout@v4` with `fetch-depth: 0` (full history for `nx affected`), `pnpm/action-setup@v4`, `actions/setup-node@v4` (Node **22**, pnpm cache), then `pnpm install --frozen-lockfile`.

| Job | Command | Notes |
|---|---|---|
| **typecheck** | `pnpm exec nx run-many -t type-check` | ALL projects, not just affected |
| **lint** | `pnpm exec nx affected --base=origin/main --head=HEAD -t lint` | affected only |
| **test** | `pnpm exec nx affected --base=origin/main --head=HEAD -t test -- --coverage --passWithNoTests` | needs `[typecheck, lint]`; spins up Postgres service |
| **build** | `pnpm exec nx affected --base=origin/main --head=HEAD -t build` | needs `[typecheck, test]` |
| **push-to-ghcr** | Docker build + push backend/frontend images | needs `[build]`; `if: github.ref == 'refs/heads/main'` only |

### The `test` job in detail

- **Postgres service container** `postgres:15` with health checks, exposed on `5432`, creds `test/test`, DB `accountr`.
- Creates a **second** database `accountr_test` for integration tests.
- Runs dev migrations (`nx run backend:prisma-migrate`) against `accountr`, then `prisma migrate deploy` against `accountr_test`.
- Runs affected tests with `--coverage`.
- **Env vars** the suite needs (mirror these as CI-only test secrets/values):
  `NODE_ENV=test`, `DATABASE_URL`, `DATABASE_URL_TEST`, `JWT_ACCESS_SECRET` / `JWT_REFRESH_SECRET` (≥32 chars), `JWT_ACCESS_EXPIRES_IN=15m`, `JWT_REFRESH_EXPIRES_IN=7d`, `EXCHANGE_RATE_API_KEY`, `EXCHANGE_RATE_API_BASE_URL`, `FRONTEND_URL`, `NEXT_PUBLIC_API_URL`.
- **Coverage reporting:** uploads `coverage/` as an artifact (`actions/upload-artifact@v4`, 30-day retention) and publishes a per-app table (lines/statements/functions/branches) to `$GITHUB_STEP_SUMMARY` — both with `if: always()` so they run even on failure.

### The `push-to-ghcr` job

Only on `main`. Needs `packages: write` permission. Logs in to `ghcr.io` with the built-in `GITHUB_TOKEN`, then `docker/build-push-action@v5` builds each app's Dockerfile and pushes two tags each — `:latest` and `:${{ github.sha }}` — with GitHub Actions layer cache (`cache-from/to: type=gha`).

---

## 3. The coverage gate

- **Threshold: 70%** across all metrics (lines, statements, functions, branches) for critical services/components.
- Enforced by Jest coverage config in each app; CI fails the `test` job if it drops below.
- Every story PR must include tests that map to the story's acceptance criteria — see the PR template checklist.

---

## 4. PR template — `.github/pull_request_template.md`

Auto-applied to every PR. Sections:

1. **PR Description** — change summary + **Story/Issue** link + change-type checkboxes.
2. **Testing Checklist** — separate backend / frontend / non-story blocks. Backend requires identifying the affected critical service, unit or integration tests, descriptive test names, local `--coverage` pass, ≥70%. Frontend requires the same with React Testing Library + mocked API calls.
3. **CI & Coverage** — states what CI enforces (affected tests + coverage, fail under 70%, artifact upload, PR summary).
4. **Reviewer Checklist** — tests match acceptance criteria; unit-vs-integration approach correct; **no monetary values as JS `number`**; services use `HttpException` subclasses + global filter; DTOs use `class-validator`.

> Rule: all checklist items must be ticked before merge. Never append bot-attribution footers to PR bodies.

---

## 5. Changesets — versioning & changelog

Config: `.changeset/config.json`.

```json
{
  "changelog": [["@changesets/changelog-github", {}]],
  "commit": false,
  "fixed": [], "linked": [],
  "updateInternalDependencies": "patch"
}
```

- Create an entry per user-facing change: `pnpm changeset` (pick bump level, write summary).
- Apply/bump before release: `pnpm changeset version`.
- **CI/policy expectation:** a changeset is required on any PR that changes user-facing behavior or a `libs/` package. Semver tags (`vMAJOR.MINOR.PATCH`) are applied on merge to `main`.

---

## 6. Deploy — `.github/workflows/deploy.yml`

- Trigger: **manual** `workflow_dispatch` with an `environment` input (`production` | `staging`). Never runs automatically.
- Uses GitHub **Environments** (`environment: ${{ inputs.environment }}`) so protection rules / required reviewers can gate it.
- Steps: SSH to the Linux server → `docker compose -f docker-compose.prod.yml pull` → run Prisma migrations in a one-off container → `up -d` → verify (`ps` + last 20 log lines) → always clean up the SSH key.
- **Required secrets** (per environment): `DEPLOY_SSH_KEY`, `DEPLOY_SSH_HOST`, `DEPLOY_SSH_USER`, `DEPLOY_APP_PATH`.

---

## 7. Recommended GitHub branch-protection settings

To match how we operate (set these in repo Settings → Branches for `main` and `develop`):

- Require PRs before merging; **no direct pushes**.
- Require status checks to pass: **typecheck, lint, test, build**.
- Require branches to be up to date before merging.
- Require at least **1 approving review**.
- `develop`: squash-merge story PRs. `main`: merge-commit from `develop`, then tag `vX.Y.Z`.

---

## 8. Mirror checklist

- [ ] Copy `.github/workflows/ci.yml` and adapt project names, DB/env vars, and Dockerfile paths.
- [ ] Copy `.github/workflows/deploy.yml`; set the 4 `DEPLOY_*` secrets per environment.
- [ ] Copy `.github/pull_request_template.md`; adjust doc links.
- [ ] Copy `.githooks/pre-push` (and optional `pre-commit`); document `git config core.hooksPath .githooks`.
- [ ] Copy `.changeset/config.json`; install `@changesets/cli` + `@changesets/changelog-github`.
- [ ] Configure branch protection on `main`/`develop` with the four required checks.
- [ ] Set the coverage threshold to 70% in each app's Jest config.
