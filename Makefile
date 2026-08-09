# Makefile for the whole YouTube Organizer app (backend + frontend)

.PHONY: backend-migrate frontend-install frontend-dev up

# --- Backend targets ---

backend-migrate:
	docker-compose exec backend python manage.py migrate

# --- Frontend targets ---

# npm ci, not npm install: it installs exactly package-lock.json (the tree CI and
# the pre-push hook reproduce) instead of rewriting the lockfile.
frontend-install:
	cd frontend && npm ci

frontend-dev:
	cd frontend && npm run dev

# --- App-level targets ---

up:
	docker-compose up --build