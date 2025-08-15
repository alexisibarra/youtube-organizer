# Copilot Instructions for YouTube Organizer

## Project Overview

This project is a full-stack application to organize YouTube playlists, using Python/Django (DRF) for the backend and Next.js (with TypeScript and Redux Toolkit) for the frontend. The goal is also to learn Python and Django, so every step should include explanations and teaching moments. For the frontend, use modern React best practices with Next.js, TypeScript, and Redux Toolkit.

## Instructions

- Always explain what you are doing and why, especially for Python and Django code.
- When generating code, include comments and learning notes.
- Suggest best practices and alternatives where relevant.
- When a new concept is introduced (e.g., Django models, DRF serializers), provide a brief teaching section before the code.
- For each major step, update the BACKLOG.md file to track progress.
- When running commands, explain what they do and why they are needed.
- If there are errors, help debug and explain the cause and solution.
- Encourage hands-on experimentation and provide links to official docs when possible.
- Help with Docker, Next.js, TypeScript, React, and Redux as needed, but focus teaching on Python/Django.
- If the user asks for a summary or review, provide a recap of what has been learned so far.

## Architecture Overview

- **Monorepo** with two main components:
  - `backend/`: Django + Django REST Framework API, PostgreSQL DB, Google OAuth2 for YouTube access
  - `frontend/`: Next.js (TypeScript) app, communicates with backend via REST
- **Docker Compose** is used for local development and orchestration of backend, frontend, and database services.
- **Environment variables** are managed via `.env` files (see `env.template` for required keys).

## Workflow

1. Plan the next step based on the backlog and user goals.
2. Teach the concept, then implement it.
3. Update the backlog and instructions as progress is made.
4. Repeat until the project is complete.

## Backend (Django)

- Main Django app: `organizer/` (API endpoints, models, Google OAuth logic)
- Project config: `youtube_organizer/` (settings, URLs)
- Uses PostgreSQL (not SQLite); DB config is in `settings.py` and expects env vars.
- Google OAuth2 flow is handled in `organizer/google_auth_views.py`.
- Migrations, superuser creation, and shell access are run via Docker Compose (see Makefile).
- **Key commands:**
  - `make up` — start all services
  - `make backend-migrate` — run Django migrations
  - `make backend-createsuperuser` — create a Django admin user
  - `make backend-shell` — open Django shell

## Frontend (Next.js)

- Located in `frontend/`, standard Next.js structure
- Start with `make frontend-dev` or `cd frontend && npm run dev`
- Communicates with backend at port 8000 (see Docker Compose)

## Developer Workflows

- Use the top-level `Makefile` for common tasks (build, up, migrate, etc.)
- Environment setup: copy `env.template` to `.env` and fill in required values
- All backend management commands should be run via Docker Compose (`backend` service)
- For OAuth2, follow the flow described in `backend/README.md`

## Conventions & Patterns

- **Service names** in Docker Compose: `backend`, `frontend`, `db`
- **No credentials** are committed; always use `.env` for secrets
- **API endpoints** are in `organizer/views.py` and `organizer/google_auth_views.py`
- **Database migrations** must be run after changing models
- **Frontend** is decoupled from backend, communicates via REST

## Integration Points

- Google OAuth2: see `organizer/google_auth_views.py` and `backend/README.md`
- PostgreSQL: configured via env vars, data persisted in Docker volume
- REST API: backend serves endpoints for frontend consumption

## Examples

- To run the full stack: `make up`
- To migrate DB: `make backend-migrate`
- To start frontend only: `make frontend-dev`

---

For more, see `backend/README.md`, `frontend/README.md`, and the top-level `Makefile`.
