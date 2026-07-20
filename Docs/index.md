# Project Documentation Index — YouTube Organizer

_Generated: 2026-07-20 · Mode: initial scan · Depth: deep · This is the primary entry point for AI-assisted development._

## Project Overview

- **Type:** Monorepo with 2 parts (web frontend + REST backend)
- **Primary Languages:** TypeScript (frontend), Python 3.13 (backend)
- **Architecture:** Next.js App Router SPA ⇄ Django REST API ⇄ Google OAuth2 / YouTube Data API v3
- **Auth model:** JWT delivered as an HttpOnly cookie, bridged to DRF SimpleJWT by custom middleware
- **What it does:** Google login → fetch and display the signed-in user's YouTube playlists

## Quick Reference by Part

### Frontend (`frontend/`)
- **Type:** web · **Root:** `frontend/` · **URL:** `https://localhost:3000`
- **Stack:** Next.js 15.4.6 (App Router), React 19, TypeScript (strict)
- **Entry:** `src/app/layout.tsx`, `src/app/page.tsx`
- ⚠️ Shipped code is **legacy** vs. the authoritative `Docs/FRONTEND-STACK.md` target stack.

### Backend (`backend/`)
- **Type:** backend · **Root:** `backend/` · **URL:** `https://localhost:8000`
- **Stack:** Django 5.2, Django REST Framework, PostgreSQL 15
- **Entry:** `youtube_organizer/wsgi.py`, `organizer/urls.py` (API under `/api/`)
- **Key files:** `google_auth_views.py`, `youtube_organizer/middleware.py`, `settings.py`

## Generated Documentation

- [Project Overview](./project-overview.md)
- [Source Tree Analysis](./source-tree-analysis.md)
- [Architecture — Frontend](./architecture-frontend.md)
- [Architecture — Backend](./architecture-backend.md)
- [Integration Architecture](./integration-architecture.md)
- [API Contracts — Backend](./api-contracts-backend.md)
- [Data Models — Backend](./data-models-backend.md)
- [Component Inventory — Frontend](./component-inventory-frontend.md)
- [Development Guide](./development-guide.md)
- [Deployment Guide](./deployment-guide.md)
- [Project Parts Metadata](./project-parts.json)

## Authoritative Source-of-Truth Docs (pre-existing — these win over code)

- [FRONTEND-STACK.md](./FRONTEND-STACK.md) — **single source of truth** for the frontend stack, versions, and conventions
- [CI-AND-GITHUB-GATES.md](./CI-AND-GITHUB-GATES.md) — **source of truth** for CI/branch/deploy gate intent

## Other Existing Documentation

- [README.md](../README.md) — project intro & setup (note: mentions Redux Toolkit, which is not present)
- [backend/README.md](../backend/README.md) — backend/OAuth setup notes
- [frontend/README.md](../frontend/README.md) — frontend env-var setup
- [BACKLOG.md](../BACKLOG.md) — feature backlog
- [_bmad-output/project-context.md](../_bmad-output/project-context.md) — condensed AI rules & gotchas

## Getting Started

1. `cp backend/env.template backend/.env` and `cp frontend/env.template frontend/.env`; fill in Google OAuth credentials.
2. `bash bin/generate-all-certs.sh` (HTTPS is required locally).
3. `make up` then `make backend-migrate`.
4. Open <https://localhost:3000> (accept the self-signed cert on both ports).

Full details in the [Development Guide](./development-guide.md).

## For AI Agents — Start Here

1. Read [_bmad-output/project-context.md](../_bmad-output/project-context.md) for the condensed rule set.
2. Frontend work → follow [FRONTEND-STACK.md](./FRONTEND-STACK.md), **not** the legacy code; see [architecture-frontend.md](./architecture-frontend.md) for what exists and the migration debt.
3. Backend work → see [architecture-backend.md](./architecture-backend.md), [api-contracts-backend.md](./api-contracts-backend.md), [data-models-backend.md](./data-models-backend.md).
4. Cross-part / auth work → [integration-architecture.md](./integration-architecture.md) (do not break the cookie/CORS invariants).

## Known Risks

- Backend `settings.py` ships `DEBUG=True`, hardcoded `SECRET_KEY`, empty `ALLOWED_HOSTS` — **not production-ready**.
- `.github/` CI files are **unadapted placeholders** from another project (assume Nx/pnpm/Prisma).
- **No automated tests** on either part yet; target is 70% frontend coverage + backend `APITestCase`.
