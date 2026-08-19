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

## Backups & Restore

The library is the app's sole home once videos have been imported and deleted out of YouTube,
so it lives behind a backup and a restore path that has actually been run (AD-20, NFR-6). The
Postgres volume is explicitly named `youtube-organizer_postgres_data` in `docker-compose.yml`,
and **no routine command in this repo's operational files destroys it** — that is the property
`organizer/tests/test_durability.py` enforces, over `Makefile`, `README.md`, `backend/README.md`,
`docker-compose.yml`, `Docs/`, `bin/`, `scripts/`, `.githooks/` and `.github/workflows/`.

Two documented commands *are* destructive, deliberately and with guards: `make restore` replaces
the contents of the live database, and step 7 of the drill below removes the drill's own throwaway
volume. Neither touches `youtube-organizer_postgres_data` by accident.

### Take a backup

```sh
make backup
```

Writes `backups/youtube_organizer-<YYYYMMDDTHHMMSSZ>.dump` — a compressed, `pg_restore`-selectable
custom-format dump, timestamped in UTC. What the script guarantees:

- It refuses (exit 1, no file written) when the `db` service is not accepting connections.
- It refuses when the database name resolved from `backend/.env` does not match the one the `db`
  container was actually created with, and says which is which. `backend/.env` is only the *Django
  client's* view; the server's identity comes from `docker-compose.yml`, and `backend/env.template`
  ships a placeholder, so the two can disagree.
- It only renames the file into place after `pg_restore --list` has parsed it, and a trap removes
  the reserved name on interrupt — so neither a truncated dump nor a Ctrl-C leaves a file that
  looks like a good backup.
- Dumps are written `0600` inside a `0700` directory, set via `umask` before anything is created.

`backups/` is **gitignored, and must stay that way**: a dump contains `organizer_usersocialtoken`,
i.e. live Google OAuth refresh tokens, plus every user row. Treat a dump like `.env` — never commit
one, never paste its contents into a PR or an issue. Note the corollary: because `backups/` is both
ignored and inside the working tree, `git clean -xfd` deletes every backup you have. If that matters
to you, keep copies outside the checkout.

### Restore into a fresh volume (the drill)

This is how you verify a backup without risking the real library. It restores into a throwaway
volume on port `55432`; the live `db` on 5432 is never touched.

> Do **not** rehearse with `docker-compose -p some-other-name up`. Because the volume is now
> explicitly named, it is project-independent — a second compose project attaches to the *same*
> volume and would restore straight over the real library. Use the bare `docker run` below.

```sh
# 1. Source-side counts — write these down.
docker-compose exec -T db psql -U postgres -d youtube_organizer -c \
  "select 'auth_user' t, count(*) from auth_user
   union all select 'usersocialtoken', count(*) from organizer_usersocialtoken
   union all select 'migrations', count(*) from django_migrations;"

# 2. A throwaway volume and a throwaway server. Same major as the real stack (15) —
#    pg_restore refuses a dump from a newer server.
docker volume create yo-restore-drill
docker run -d --name yo-restore-drill-db \
  -e POSTGRES_DB=youtube_organizer -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres \
  -v yo-restore-drill:/var/lib/postgresql/data -p 55432:5432 postgres:15

# 3. Prove it is on the throwaway volume BEFORE restoring into it.
docker inspect -f '{{range .Mounts}}{{.Name}}{{end}}' yo-restore-drill-db   # -> yo-restore-drill

# 4. Restore. The DB already exists (the entrypoint created POSTGRES_DB) and is empty.
docker exec -i yo-restore-drill-db pg_restore -U postgres -d youtube_organizer \
  --no-owner --no-privileges < backups/youtube_organizer-<TS>.dump

# 5. Same counts as step 1?
docker exec -i yo-restore-drill-db psql -U postgres -d youtube_organizer -c \
  "select 'auth_user' t, count(*) from auth_user
   union all select 'usersocialtoken', count(*) from organizer_usersocialtoken
   union all select 'migrations', count(*) from django_migrations;"

# 6. Django agrees the schema is current, against the drill port. The parentheses
#    matter: they keep the `cd` inside a subshell, so step 7 still runs from the
#    repo root if you paste this block as a whole.
( cd backend && POSTGRES_HOST=localhost POSTGRES_PORT=55432 \
  POSTGRES_DB=youtube_organizer POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres \
  .venv/bin/python manage.py migrate --check )
#    All four are pinned to what step 2 created the drill container with. Without them
#    they come from backend/.env, and any developer whose password differs gets an
#    authentication failure at the one step the guide calls the real test of recovery.

# 7. Tear down. Note this removes ONLY the drill volume.
docker rm -f yo-restore-drill-db && docker volume rm yo-restore-drill
docker volume ls | grep yo-restore-drill    # -> no output: the drill volume is gone
docker volume ls | grep postgres            # -> youtube-organizer_postgres_data, untouched
```

Step 6 is what distinguishes "the bytes came back" from "the library is recovered": it asserts the
restored schema is exactly what the current migration state expects. It needs a host virtualenv,
which the Docker-first workflow does not otherwise require — `.githooks/pre-push` treats it as
optional. Create it once with:

```sh
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

Step 7's two greps are separate on purpose: the first proves the drill volume is gone, and the
second proves the real one survived. A single `grep postgres` cannot observe `yo-restore-drill` at
all — the name contains no "postgres" — so it would report success without having looked.

### Restore in anger, over the live database

```sh
make restore FILE=backups/youtube_organizer-<TS>.dump
```

`make restore` prints what it is about to destroy — the database, the volume, and its current row
counts — and then requires an explicit `y`. Before it drops anything it parses the archive (a
truncated file costs you nothing), cross-checks the target database against the container, takes a
backup of the current state, and *attempts* to stop the `backend` service so Django cannot write
into a half-restored schema. The restore itself runs in a single transaction, so a mismatched major
or a dropped connection rolls back whole rather than leaving the library half-dropped. Afterwards it
restarts `backend`, prints the row counts that arrived, and runs the same `migrate --check` that
step 6 of the drill calls the real test of recovery.

Two of those are attempts rather than guarantees, deliberately:

- **If the pre-restore backup fails, it warns and asks again** rather than refusing. The conditions
  that make `pg_dump` fail — a corrupt cluster, an undumpable database, a disk with no room for a
  second copy — are the same conditions that make you reach for a restore. A hard refusal would take
  the tool away in the emergency it exists for, so instead you have to type `restore anyway` in full,
  knowing there is no recovery point. (With `CONFIRM=yes` it proceeds and says so.)
- **If stopping `backend` fails, it warns and continues.** You are told you did not get that
  protection. The restore is transactional either way.

**Restoring into an empty database works** — that is the disaster case, and the row-count preview
reports each missing table as `absent` rather than treating an empty target as an error.

Two things it does **not** do, and you should know both:

- `--clean --if-exists` drops only the objects *present in the dump*. Restoring an older dump over a
  database that has since gained tables leaves those tables in place — you get a hybrid schema, not
  a point-in-time state. The `migrate --check` at the end is what surfaces this.
- Being awkward to run is not the same as being impossible to run. With stdin not a TTY and
  `CONFIRM` unset it refuses, which stops it happening *by accident* in a hook or a CI step — but
  anything that sets `CONFIRM=yes` runs it. Treat that as a speed bump, not as the mechanism that
  enforces AD-20.

### When you want a reset, not a restore

No routine command in this repo's operational files destroys `youtube-organizer_postgres_data`
(AD-20), and the guards keep it that way. Be aware that Docker's own volume-pruning subcommands
remove any volume no container is currently using, so a *stopped* stack is not protected from them
by anything in this repo. To clear data while keeping the schema and migration history:

```sh
docker-compose exec backend python manage.py flush --noinput
```

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
