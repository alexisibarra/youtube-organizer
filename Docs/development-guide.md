# Development Guide — YouTube Organizer

_Generated: 2026-07-20 · Monorepo (frontend + backend), Docker Compose orchestrated_

## Prerequisites

- **Docker & Docker Compose** (primary path — runs all three services)
- **Node.js 20+** (for running the frontend outside Docker)
- **Python 3.13** (for running the backend outside Docker)
- A **Google Cloud OAuth2 client** (Client ID/Secret) with YouTube Data API v3 enabled and
  `https://localhost:8000/api/oauth2callback/` as an authorized redirect URI.

## First-Time Setup

```sh
# 1. Environment files
cp backend/env.template  backend/.env
cp frontend/env.template frontend/.env
#    → fill in GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET in backend/.env

# 2. Self-signed certs for local HTTPS (required — SameSite=None cookies need Secure)
bash bin/generate-all-certs.sh
#    (or bin/generate-backend-cert.sh / bin/generate-frontend-cert.sh individually)

# 3. Build & start everything (backend:8000, db:5432, frontend:3000)
make up            # == docker-compose up --build

# 4. Apply DB migrations (inside the backend container)
make backend-migrate
```

Then open:
- Frontend: <https://localhost:3000>
- Backend API: <https://localhost:8000/api/>

You will need to accept the self-signed cert warning in the browser for **both** ports.

## Required Environment Variables

**Backend (`backend/.env`)**

| Var | Purpose | Default |
| --- | --- | --- |
| `GOOGLE_CLIENT_ID` | OAuth2 client id | — |
| `GOOGLE_CLIENT_SECRET` | OAuth2 client secret | — |
| `GOOGLE_REDIRECT_URI` | OAuth callback | `https://localhost:8000/api/oauth2callback/` |
| `FRONTEND_AUTH_CALLBACK_URL` | Post-login redirect | `https://localhost:3000/auth/callback` |
| `POSTGRES_DB/USER/PASSWORD/HOST/PORT` | DB connection | `youtube_organizer/postgres/postgres/db/5432` |

**Frontend (`frontend/.env`)**

| Var | Purpose | Default |
| --- | --- | --- |
| `NEXT_PUBLIC_BACKEND_URL` | Backend base URL | `https://localhost:8000` |

## Common Commands

| Task | Command |
| --- | --- |
| Start full stack (build) | `make up` |
| Run DB migrations | `make backend-migrate` |
| Frontend only (dev) | `make frontend-dev` (`cd frontend && npm run dev`) |
| Install frontend deps | `make frontend-install` |
| Backend shell (container) | `docker-compose exec backend python manage.py shell` |
| Make migrations | `docker-compose exec backend python manage.py makemigrations` |
| Create superuser | `docker-compose exec backend python manage.py createsuperuser` |
| Frontend typecheck | `cd frontend && npx tsc --noEmit` |
| Frontend production build | `cd frontend && npm run build` |
| Frontend lint | `cd frontend && npm run lint` |

## Running Parts Individually

- **Frontend outside Docker:** `cd frontend && npm install && npm run dev` (uses Turbopack;
  Docker uses `next dev --experimental-https`). Point `NEXT_PUBLIC_BACKEND_URL` at your backend.
- **Backend outside Docker:** needs a reachable Postgres and the `.env`; run
  `python manage.py runserver_plus 0.0.0.0:8000 --cert-file ... --key-file ...`.

## Testing

> ⚠️ **No test suites exist yet** on either part.

- **Backend target:** Django `APITestCase` (DRF) in `organizer`. Auth-dependent tests must
  simulate the cookie→header path or authenticate via SimpleJWT directly (because
  `JWTAuthCookieMiddleware` populates the auth header).
- **Frontend target (per `Docs/FRONTEND-STACK.md` §5):** Jest 29 + React Testing Library 16 +
  `@testing-library/user-event`; mock all API with `axios-mock-adapter` (never hit a real
  backend); **70% coverage gate**; query by role/label, not implementation details.

## Coding Conventions (authoritative)

- **Frontend:** follow `Docs/FRONTEND-STACK.md`, **not** the shipped legacy code. Key points:
  React Query (only server-state layer) + axios; react-hook-form `mode: 'onBlur'` + zod;
  shadcn/ui in `src/components/ui/` (never hand-edit); `cn()` for conditional classes;
  kebab-case filenames; no phantom deps (every import must be a direct dependency); wrap
  `localStorage` in try/catch. See [architecture-frontend.md](./architecture-frontend.md).
- **Backend:** match the indentation of the file you edit (repo mixes tabs in `models.py`/
  `views.py` and 4-space in `urls.py`/`settings.py`/`google_auth_views.py` — don't reformat
  wholesale). Keep OAuth/Google logic in `google_auth_views.py`, generic views in `views.py`.
  Public endpoints must set `permission_classes = [AllowAny]` explicitly.
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:` …).

## Branch & PR Flow

Per [CI-AND-GITHUB-GATES.md](./CI-AND-GITHUB-GATES.md):

- Never commit/push directly to `main` or `develop`. Work on `feat/story-*` branches; open a
  PR into `develop`; `develop` → `main` via merge-commit, then tag `vMAJOR.MINOR.PATCH`.
- Required checks (intent): typecheck, lint, test, build + ≥1 approving review.
- Optional local `pre-push` hook lives in `.githooks/` — activate once per clone with
  `git config core.hooksPath .githooks`.

> ⚠️ The `.github/workflows/*.yml` files are **unadapted placeholders** copied from another
> project (they assume Nx/pnpm/Prisma). Treat them as scaffold, not working CI, until rewritten
> for this repo's real paths (`frontend/**`, `backend/**`) and tooling (npm + Django). Details
> in [CI-AND-GITHUB-GATES.md](./CI-AND-GITHUB-GATES.md).

## Gotchas

- **Adding a `next/image` from a new remote host** requires adding it to `remotePatterns` in
  `frontend/next.config.ts`, or the production build fails.
- **HTTPS is mandatory locally** — the cross-port OAuth cookie flow needs `Secure` cookies.
- **DEBUG/SECRET_KEY/ALLOWED_HOSTS** in `backend/youtube_organizer/settings.py` are dev-only;
  do not ship as-is (see [deployment-guide.md](./deployment-guide.md)).
