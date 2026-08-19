# Makefile for the whole YouTube Organizer app (backend + frontend)

.PHONY: backend-migrate backend-test backend-coverage backup restore frontend-install frontend-dev up

# --- Backend targets ---

backend-migrate:
	docker-compose exec backend python manage.py migrate

backend-test:
	docker-compose exec backend python manage.py test --noinput

# Measures and enforces: `fail_under = 70` lives in backend/.coveragerc (NFR-13,
# live since story 1-4), so `coverage report` exits non-zero when the total drops
# below it — here and in CI. The pre-push hook does NOT run coverage: layer 6/6 is
# `manage.py test` bare, so use this target (or CI) to know where you stand.
#
# `coverage` is installed into the image, and ./backend is bind-mounted over /app —
# so pulling a commit that adds a requirement does NOT install it in a container
# built earlier. If this dies with "executable file not found", rebuild:
#   docker-compose build backend && docker-compose up -d backend
backend-coverage:
	docker-compose exec backend coverage run manage.py test --noinput
	docker-compose exec backend coverage report

# The durability mechanism (AD-20, NFR-6): a timestamped custom-format pg_dump into
# backups/, which is gitignored because a dump carries live Google refresh tokens.
# The script writes to a .partial and only renames after pg_restore --list has parsed
# the archive, so a half-written file can never be mistaken for a backup.
backup:
	bash bin/backup-db.sh

# Restores OVER the live database. Refuses when stdin is not a TTY and CONFIRM is
# unset, which stops it running unattended by accident — a speed bump, not a wall
# (anything that sets CONFIRM=yes still runs). Before dropping anything it parses the
# archive, takes its own backup (a failure there warns and asks again rather than
# refusing — a broken cluster is exactly when you still need this tool), and attempts
# to stop the backend; the restore runs in one transaction. To rehearse safely,
# follow the drill in Docs/development-guide.md § Backups & Restore — it restores into
# a throwaway volume, never the real one.
#   make restore FILE=backups/youtube_organizer-<TS>.dump
restore:
	bash bin/restore-db.sh "$(FILE)"

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