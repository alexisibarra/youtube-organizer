# Makefile for the whole YouTube Organizer app (backend + frontend)

.PHONY: backend-migrate frontend-install frontend-dev up

# --- Backend targets ---

backend-migrate:
	docker-compose exec backend python manage.py migrate

# --- Frontend targets ---

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

# --- App-level targets ---

up:
	docker-compose up --build