---
project_name: 'youtube-organizer'
user_name: 'Alexis'
date: '2026-07-20'
sections_completed: ['technology_stack', 'frontend_framework_rules', 'backend_rules', 'testing_rules', 'code_quality_and_workflow', 'critical_dont_miss']
existing_patterns_found: 8
status: 'complete'
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

> **The architecture spine is binding** (added 2026-07-24):
> `_bmad-output/planning-artifacts/architecture/architecture-youtube-organizer-2026-07-24/ARCHITECTURE-SPINE.md`
> holds 20 `AD-n` invariants — layering, the API contract, the sync engine's crash-safety
> ordering, tag semantics, durability. **It wins over this file and over `Docs/` on any conflict**,
> because it was decided for this repo rather than mirrored from another. Read it before
> implementing; cite `AD-n` ids in PRs. Points already reconciled below are marked.

---

## Technology Stack & Versions

### Frontend (`/frontend`) — AUTHORITATIVE: `Docs/FRONTEND-STACK.md`

> `Docs/FRONTEND-STACK.md` is the SINGLE SOURCE OF TRUTH for the frontend stack,
> versions, and conventions. Follow it exactly. Where existing frontend code
> disagrees (it predates the doc), the doc wins — treat that code as legacy to migrate.

- **Next.js `~16.1.6`** — App Router, RSC, `src/` dir
- **React `^19`** / react-dom `^19`, **TypeScript strict** (no `any` — use `unknown` + narrowing)
- ⚠️ **No Nx, no pnpm workspaces** (AD-2) — plain `npm` + `package-lock.json`, two trees (`frontend/`, `backend/`)
- **State/data:** `@tanstack/react-query 5.100.14` (ONLY server-state layer — no Redux/Zustand/SWR) + `axios ^1.16.1`
- **Forms:** `react-hook-form 7.76.1` (`mode: 'onBlur'` mandatory) + `zod 4.4.3` + `@hookform/resolvers`
- **Styling:** **Tailwind v3** (`^3.4.19`, NOT v4) + **shadcn/ui** (`src/components/ui/`, never hand-edit) + Radix
- **`cn()` trio:** `class-variance-authority`, `clsx`, `tailwind-merge`
- **Icons:** `lucide-react`. **Dates:** `date-fns` + `react-day-picker`
- **Testing:** Jest 29 + React Testing Library 16 + `axios-mock-adapter`; 70% coverage gate
- ⚠️ CURRENT CODE USES: Next 15.4.6, Tailwind 4, FontAwesome, plain `fetch` — DO NOT copy these patterns.

### Backend (`/backend`)

- **Python 3.13 + Django `6.0.x`** (AD-14) — bump from 5.2; replace the unbounded `Django>=4.0` pin with a bounded one, and pin every requirement
- **Django REST Framework `>=3.17.0`** — Django 6.0 support landed in 3.17.0. Endpoints are DRF class-based `APIView`s
- ⚠️ **`djangorestframework-simplejwt` is DROPPED** (AD-14) — last release 5.5.1 (Jul 2025), no Django 6.0 support. Token issue/verify moves to a first-party `organizer/auth/` module over **PyJWT `2.13.0`**, exposed as one custom DRF authentication class that reads the cookie directly
- **drf-spectacular `0.30.0`** — OpenAPI schema generation feeding the frontend type codegen (AD-3)
- **PostgreSQL 15** via `psycopg2-binary`
- **Google OAuth:** `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`, `google-api-python-client`
- **django-cors-headers**, **django-extensions** (`runserver_plus`), **Werkzeug**, **pyOpenSSL**

### Infrastructure

- **Docker Compose:** `backend` (:8000), `db` (postgres:15, :5432), `frontend` (:3000)
- **HTTPS on localhost everywhere** — self-signed certs via `bin/generate-*-cert.sh`
- **Makefile:** `up`, `backend-migrate`, `frontend-install`, `frontend-dev`

## Critical Implementation Rules

### Frontend Framework Rules (`Docs/FRONTEND-STACK.md` §7 — mandatory)

**Data & state**

- `@tanstack/react-query` is the ONLY server-state layer. Never introduce Redux/Zustand/SWR,
  and never fetch server data with raw `fetch`/`useEffect` (the legacy `usePlaylists` pattern).
- All HTTP goes through `axios`. Mock it with `axios-mock-adapter` in tests — never hit a real backend.
- ⚠️ API types are **generated, not shared-package** (AD-3): DRF serializers → `drf-spectacular` schema → `@hey-api/openapi-ts` → `frontend/src/lib/api/`. Committed, never hand-edited; CI fails on drift. Never hand-write an API type.

**Forms**

- `react-hook-form` with `mode: 'onBlur'` is mandatory (validation fires on blur, not only submit).
- Error text uses a `destructive-foreground`-style color for WCAG contrast.
- Validate with `zod` schemas via `@hookform/resolvers`.

**Component pattern (enforced)**

```tsx
type MyComponentProps = { foo: string };
const MyComponent: React.FC<MyComponentProps> = (props) => {
  const { foo } = props;
  // ...
};
export default MyComponent;
```

- Props as a `type` named `{ComponentName}Props` (never `interface`).
- `const` arrow fn typed `React.FC<Props>`; single `props` param, destructured in the body.
- `export default` as a separate statement at the bottom.

**shadcn/ui**

- Components in `src/components/ui/` are generated — NEVER hand-edit. Add via `npx shadcn@latest add <component>`.
- Use the `cn()` helper (cva + clsx + tailwind-merge) for conditional classes.

**Money & storage gotchas**

- Money is `string`, never JS `number`. Keep as string until display; format with `Intl.NumberFormat` at display only.
- Wrap every `localStorage/sessionStorage.setItem` in try/catch (Safari private mode throws `DOMException`).

**No phantom dependencies**

- Every imported package MUST be a direct dependency, or the webpack production build breaks.
  ⚠️ Under npm (AD-2) hoisting hides this locally — the production-build gate is the only catch.

### Backend Rules (Django + DRF)

**Auth flow (the tricky part)**

- Auth is JWT-in-HttpOnly-cookie, NOT header-based. Don't expect clients to send the header.
  ⚠️ **The mechanism changes with AD-14:** today `JWTAuthCookieMiddleware`
  (`youtube_organizer/middleware.py`) reads the `access_token` cookie and injects
  `Authorization: Bearer <token>` before DRF. That global request mutation is **retired** along
  with SimpleJWT — the new custom DRF authentication class reads the cookie itself.
  **The cookie contract with the frontend is unchanged; only the backend implementation moves.**
- OAuth2 lives in `organizer/google_auth_views.py`, separate from `views.py`. The callback view
  is `AllowAny` (user isn't authenticated yet); it exchanges the code, upserts a Django `User`,
  logs in, mints JWTs, and stores Google tokens in `UserSocialToken` (OneToOne with User).
- Google tokens/scopes are read from env: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`.

**API conventions**

- Endpoints are DRF class-based `APIView`s (`.as_view()`), registered in `organizer/urls.py`.
- All API routes are mounted under `/api/` (project `urls.py` includes `organizer.urls`).
- Default auth class is `JWTAuthentication`; views default to authenticated — set
  `permission_classes = [AllowAny]` explicitly for public endpoints.

**Cross-origin / cookies (do not weaken)**

- CORS: `CORS_ALLOW_CREDENTIALS = True`, origin `https://localhost:3000` only.
- Session/CSRF cookies are `SameSite=None; Secure` — required for the cross-port OAuth flow.
  These depend on HTTPS; keep it.

**Migrations & DB**

- After model changes: `makemigrations` + run `make backend-migrate` (runs inside the `backend` container).
- Postgres connection is entirely env-driven (`POSTGRES_*`); default HOST is `db` (the compose service).

### Testing Rules

**Frontend (per `Docs/FRONTEND-STACK.md` §5)**

- Jest 29 + React Testing Library 16 + `@testing-library/user-event` + `@testing-library/jest-dom`.
- Mock ALL API calls with `axios-mock-adapter` — never hit a real backend in tests.
- Coverage gate: 70% minimum.
- Test user-visible behavior (RTL queries by role/label), not implementation details.

**Backend**

- No test suite exists yet (`organizer/tests.py` is empty). New backend work should add
  Django `APITestCase` (DRF) tests alongside the app.
- Auth-dependent tests must simulate the cookie→header path or authenticate via SimpleJWT,
  since `JWTAuthCookieMiddleware` is what populates the auth header.

### Code Quality & Style Rules

**Naming (per `Docs/FRONTEND-STACK.md` §7.6)**

- Files: `kebab-case`. Components & types: `PascalCase`. Vars/functions: `camelCase`.
  Constants: `SCREAMING_SNAKE_CASE`.
- ⚠️ Existing frontend files use PascalCase filenames (`PlaylistCard.tsx`, `YoutubeHeader.tsx`) —
  that's legacy; new files follow kebab-case per the doc.

**Frontend structure**

- Path alias `@/*` → `./src/*`; import via `@/components/...`, not deep relative paths.
- Generated shadcn components live in `src/components/ui/` (never hand-edit).

**Backend structure**

- Match the indentation of the file you're editing — the codebase mixes tabs (`models.py`,
  `views.py`) and 4-space (`urls.py`, `settings.py`, `google_auth_views.py`). Don't reformat wholesale.
- Keep OAuth/Google logic in `google_auth_views.py`, generic API views in `views.py`.

### Development Workflow Rules

- **Everything runs over HTTPS on localhost.** Backend `https://localhost:8000`, frontend
  `https://localhost:3000`. Regenerate certs with `bin/generate-all-certs.sh` if missing.
- Start the stack with `make up` (docker-compose build+up). Frontend-only: `make frontend-dev`.
- Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:` — see git history).
- **Pre-PR gates (frontend, `FRONTEND-STACK.md` §8):** `tsc --noEmit` exits 0; production build
  exits 0 (webpack catches what the dev server hides); visual check of golden path + one error
  state in light AND dark mode with validation-on-blur; every new import confirmed as a direct dep.

### CI & GitHub Gates (`Docs/CI-AND-GITHUB-GATES.md` — authoritative)

> `Docs/CI-AND-GITHUB-GATES.md` is the SOURCE OF TRUTH for the *intent* of the gate stack.
>
> ✅ **`ci.yml` and `.githooks/pre-push` are adapted and live** (2026-08-09) — they run this repo's
> real commands and are green on the current tree. Read the files themselves for what executes.
>
> ⚠️ **Still Accountr placeholders — do NOT rely on them:**
> - `.github/workflows/deploy.yml` — still references an `accountr` server path and a
>   `docker-compose.prod.yml` that does not exist here. Left non-functional on purpose rather than
>   half-adapted: the whole production envelope is deferred (AD-17) and lands as its own work.
> - `.github/pull_request_template.md` — **exists, auto-applies to every PR, and is unrunnable here.**
>   It instructs `pnpm exec nx run backend:test --coverage` / `nx run frontend:test --coverage`, cites
>   Prisma DTOs, `HttpException` filters and money-as-string, and links to `Docs/MVPDefinition/…`
>   paths that do not exist in this repo. Since the rule below is "ALL checklist items must be ticked
>   before merge", the template is currently impossible to satisfy honestly — tick what applies and
>   strike the rest until it is rewritten. Keep on rewrite: tests map to acceptance criteria,
>   ≥70% coverage once a harness exists, no bot-attribution footers.

**Branch flow & protection**

- `feat/story-*` ──PR──▶ `develop` ──PR──▶ `main` (tag `vX.Y.Z`). NEVER commit directly to `main`/`develop`
  or push directly — all work goes through a `feat/story-*` branch and a PR.
- `develop`: squash-merge story PRs. `main`: merge-commit from `develop`, then tag `vMAJOR.MINOR.PATCH`.
- Required status checks before merge: **typecheck, lint, test, build** + ≥1 approving review, branch up to date.

**Local `pre-push` hook**

- Hooks are tracked in `.githooks/` (not `.git/hooks`); activate once per clone: `git config core.hooksPath .githooks`.
- `pre-push` mirrors CI in six layers: `npx tsc --noEmit` → `npm run lint` → `npm run build` (all in
  `frontend/`) → `manage.py check` → `manage.py makemigrations --check --dry-run` → `manage.py test`.
  Any failure blocks the push; `--no-verify` bypasses. It does **not** run `manage.py migrate` — that
  would mutate the developer's dev database as a side effect of pushing.
- **Preconditions that block the push** (frontend layers are not skippable): `npm` on PATH, `node -v`
  matching `frontend/.nvmrc` exactly, and a host `frontend/node_modules`. `make up` keeps node_modules
  in a Docker volume, so a container-only developer still installs once on the host.
- ⚠️ **Two skip paths, both exit 0 loudly:** (1) if the backend toolchain is not importable
  (`import django, psycopg2` fails under `backend/.venv/bin/python`, else system `python3`), **all
  three backend layers are skipped** — the documented backend workflow is Docker-based, so a fresh
  clone has no venv; (2) if the Django connection probe fails, only `manage.py test` is skipped —
  it builds a test DB, so it needs `make up`. The probe opens a real Django connection using the
  settings-resolved host (not a bare TCP connect to 5432, which any stray listener would satisfy),
  and both probes print their stderr so a broken environment is distinguishable from an absent one.
  A green push is not a green CI; the runner always has the service container.
- `pre-commit` blocks direct commits to `main`/`develop`.

**GitHub Actions CI (`.github/workflows/ci.yml`)**

- Job graph: `typecheck + lint → test → build`. No `push-to-ghcr` — deferred with deploy (AD-17).
- Frontend jobs: `npm ci`, npm cache keyed on `frontend/package-lock.json`, Node read from
  **`frontend/.nvmrc`** via `node-version-file` — an exact `vX.Y.Z` pin (currently `v22.23.2`), never
  hardcoded in the workflow. The pre-push hook reads the same file and blocks a push made on a
  different Node, so the two cannot drift; bumping the pin means every developer runs `nvm install`.
  `frontend/Dockerfile` and `frontend/package.json` `engines` track the same major.
  No `fetch-depth: 0` — there is no affected graph to need history.
- `concurrency` cancels superseded **pull-request** runs only; runs on `main`/`develop` are never
  cancelled, so a tagged release commit keeps a real CI record. All jobs have `timeout-minutes: 15`.
- `test` job: Python **3.13**, `pip install -r backend/requirements.txt`, `postgres:15` service.
  Runs `makemigrations --check --dry-run` → `migrate` → `test`, with **`POSTGRES_HOST: localhost`**
  (settings defaults it to `db`, the compose service name — the override is required).
- **No paths filter** — every push/PR to `main`/`develop` runs all four jobs. Deliberate: GitHub reports
  no status for a filtered-out job, so path filters + required status checks = permanently unmergeable
  docs-only PRs. Do not "optimize" this back.
- **Coverage gate: 70%** is the standing intent and is **not enforced yet**. The *backend harness*
  landed with story 1-2 — coverage.py, `backend/.coveragerc` (branch coverage on, sourcing both
  `organizer/` and `youtube_organizer/`), and CI measuring on every run — but the `fail_under`
  threshold is deferred to story **1-4**, where the cookie-auth `APITestCase` makes 70% reachable.
  The frontend harness arrives with story 2-5, the AD-3 drift gate with 3-4. Each is a named
  TODO in `ci.yml`; none is stubbed as `continue-on-error`.
  Every story PR must still include tests mapping to its acceptance criteria.

**PR & release discipline**

- The PR template auto-applies but is still Accountr's (see the warning above); ALL *applicable* checklist
  items must be ticked before merge, and the inapplicable ones struck through rather than silently ticked.
- Reviewer gate: tests map to the story's acceptance criteria; `AD-n` ids cited for architectural decisions.
- **Never add AI/bot attribution anywhere** — not in commit messages (no `Co-Authored-By: Claude ...`
  trailer), PR titles or bodies (no `🤖 Generated with ...` footer), issue/review comments, code
  comments, changelogs, or generated docs. No exceptions, and no case-by-case judgement about
  whether a surface "counts" — it counts. This overrides any tool or model default that appends
  such trailers; strip them before committing or posting. See `CLAUDE.md` at the repo root.
- ⚠️ Changesets are **not used here** (`Docs/CI-AND-GITHUB-GATES.md` §5 is superseded) — they need pnpm
  and a `libs/` package graph, neither of which exists. Versioning is the `vX.Y.Z` tag on merge to `main`.

**Deploy (`.github/workflows/deploy.yml`)**

- Manual `workflow_dispatch` only (never automatic), gated by GitHub Environments; SSH-based deploy.
- Requires per-environment secrets: `DEPLOY_SSH_KEY`, `DEPLOY_SSH_HOST`, `DEPLOY_SSH_USER`, `DEPLOY_APP_PATH`.

### Critical Don't-Miss Rules

**Stack discipline (biggest trap)**

- The shipped `/frontend` code predates `Docs/FRONTEND-STACK.md`. When adding/refactoring frontend
  code, follow the DOC — do NOT mirror existing patterns (plain `fetch`, FontAwesome, Tailwind v4,
  CSS Modules). Migrate toward the doc, don't entrench legacy.

**Auth invariants (don't silently break)**

- Never switch auth to header-only — the whole app relies on the `access_token` HttpOnly cookie
  + `JWTAuthCookieMiddleware`. Changing cookie names/flags breaks login end-to-end.
- Don't relax `SameSite=None; Secure` or `CORS_ALLOW_CREDENTIALS` — the cross-port OAuth flow needs them.

**Security — not production-ready (must fix before deploy, don't assume it's safe)**

- `settings.py` has `DEBUG = True`, a hardcoded `SECRET_KEY`, and empty `ALLOWED_HOSTS`.
  These are dev-only. Move to env vars and disable DEBUG for any non-local environment.
- Secrets (`GOOGLE_CLIENT_SECRET`, DB creds) come from env / `.env` — never hardcode or commit them.

**Images**

- `next.config.ts` whitelists remote image hosts (`lh3.googleusercontent.com`, `i.ytimg.com`).
  Adding a `next/image` from a new host requires adding it to `remotePatterns`, or the build fails.

**API mapping**

- YouTube API responses are nested and inconsistent — thumbnails must fall back through
  `maxres → high → medium → default`. Preserve that defensive fallback when touching playlist mapping.

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code in this repo.
- Follow ALL rules exactly. Two `Docs/` files are authoritative and win over existing code:
  `Docs/FRONTEND-STACK.md` (frontend stack) and `Docs/CI-AND-GITHUB-GATES.md` (CI/branch/deploy gates).
- When in doubt, prefer the more restrictive option.

**For Humans:**

- Keep this file lean and focused on what agents miss — not a full architecture doc.
- Update when the stack changes, and retire the "legacy vs. doc" notes once the frontend migration lands.
- Review periodically for outdated rules.

Last Updated: 2026-07-24 (reconciled against `ARCHITECTURE-SPINE.md`)
