# Project Overview — YouTube Organizer

_Generated: 2026-07-20 · Scan level: deep · Mode: initial scan_

## Purpose

**YouTube Organizer** is a full-stack web application that lets a user sign in with
their Google account and view/organize their own YouTube playlists. It also doubles as a
learning platform for Django/DRF and modern React, so the codebase carries teaching notes
throughout.

Today the shipped functionality is: **Google OAuth2 login → fetch the signed-in user's
YouTube playlists → render them as cards.** A YouTube-style header/sidebar and a static
video-grid demo round out the UI shell.

## Repository Type

**Monorepo** with two independently-deployable parts orchestrated by Docker Compose:

| Part | Path | Type | Stack |
| --- | --- | --- | --- |
| Frontend | `frontend/` | web | Next.js 15.4.6 (App Router), React 19, TypeScript |
| Backend | `backend/` | backend | Django 5.2, Django REST Framework, PostgreSQL 15 |

## Tech Stack Summary

| Category | Frontend | Backend |
| --- | --- | --- |
| Language | TypeScript 5 | Python 3.13 |
| Framework | Next.js 15.4.6 / React 19 | Django 5.2 + DRF ≥3.13 |
| Auth | HttpOnly `access_token` cookie (JWT) | SimpleJWT + Google OAuth2 |
| Data layer | plain `fetch` (legacy) | PostgreSQL 15 via `psycopg2` |
| Styling | Tailwind v4 + CSS Modules + global CSS (legacy) | — |
| Icons | FontAwesome (legacy) | — |
| External API | — | YouTube Data API v3, Google OAuth2 |
| Dev serving | `next dev --turbopack` / `--experimental-https` | `runserver_plus` (HTTPS) |

> ⚠️ **Stack discipline (critical).** The shipped `frontend/` code **predates**
> `Docs/FRONTEND-STACK.md`, which is the authoritative target stack (React Query, axios,
> shadcn/ui, Tailwind v3, react-hook-form, kebab-case files, 70% test coverage). The
> "legacy" columns above (plain `fetch`, FontAwesome, Tailwind v4, CSS Modules) describe
> the **current** code — do **not** copy those patterns in new work. See
> [FRONTEND-STACK.md](./FRONTEND-STACK.md) and
> [_bmad-output/project-context.md](../_bmad-output/project-context.md).

## Architecture at a Glance

```
Browser (https://localhost:3000)
  │  Next.js App Router UI (React 19)
  │  - fetch() with credentials: 'include'
  ▼
Django REST API (https://localhost:8000/api/)
  │  - JWTAuthCookieMiddleware: cookie -> Authorization header
  │  - DRF APIViews (SimpleJWT auth)
  ├── PostgreSQL 15  (UserSocialToken, auth_user)
  └── Google OAuth2 + YouTube Data API v3
```

- **Auth is cookie-based JWT**, not header-based. The backend mints a JWT after OAuth and
  sets it as an `HttpOnly; Secure; SameSite=None` cookie; a custom middleware promotes that
  cookie to an `Authorization: Bearer` header before DRF sees the request.
- **Everything runs over HTTPS on localhost** with self-signed certs (required for the
  cross-port, cross-site cookie flow).

## Key Documentation

- [Architecture — Backend](./architecture-backend.md)
- [Architecture — Frontend](./architecture-frontend.md)
- [Integration Architecture](./integration-architecture.md)
- [API Contracts — Backend](./api-contracts-backend.md)
- [Data Models — Backend](./data-models-backend.md)
- [Component Inventory — Frontend](./component-inventory-frontend.md)
- [Source Tree Analysis](./source-tree-analysis.md)
- [Development Guide](./development-guide.md)
- [Deployment Guide](./deployment-guide.md)

## Known Constraints & Risks

- **Not production-ready:** `settings.py` ships `DEBUG = True`, a hardcoded `SECRET_KEY`,
  and empty `ALLOWED_HOSTS`. Must be moved to env vars before any non-local deploy.
- **CI files are unadapted placeholders** mirrored from another project (Accountr). See
  [CI-AND-GITHUB-GATES.md](./CI-AND-GITHUB-GATES.md) — they reference Nx/pnpm/Prisma that
  this repo does not use.
- **No automated tests exist yet** on either part (`organizer/tests.py` is empty; frontend
  has no test setup). The authoritative docs require 70% coverage going forward.
- **Frontend/backend architecture mismatch:** README claims Redux Toolkit, but no state
  library is present; the target doc mandates React Query instead.
