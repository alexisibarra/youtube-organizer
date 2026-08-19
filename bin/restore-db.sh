#!/bin/bash
# Restore a pg_dump artifact over the LIVE library database (AD-20, NFR-6).
#
# This is the destructive counterpart to bin/backup-db.sh and it is deliberately
# awkward to run: it refuses without an explicit confirmation, and refuses outright
# when stdin is not a TTY unless CONFIRM=yes is set in the environment. That raises
# the cost of running it unattended — it does not make it impossible, and the docs
# must not claim otherwise: anything that can set CONFIRM=yes can still run it.
#
# For rehearsing a restore without risking the real library, use the drill in
# Docs/development-guide.md § Backups & Restore, which restores into a throwaway volume.
#
# `exec -T` is required here for the same reason as in backup-db.sh: a pseudo-TTY
# corrupts the binary archive on its way into pg_restore.
#
# Things that happen before a single object is dropped, because this database has no
# other copy: the archive is parsed, the current contents are shown, a backup of the
# current state is attempted, and the app is stopped so nothing writes into a
# half-restored schema. Note "attempted" — see the pre-restore backup section for why
# a failure there is a loud warning and a second confirmation rather than a refusal.
set -euo pipefail

# The positional argument wins over an inherited FILE. On a command that destroys the
# library, what the operator typed must beat what their shell happened to export.
FILE="${1:-${FILE:-}}"
if [ -n "$FILE" ] && [ "${FILE#/}" = "$FILE" ]; then
    # Resolve against the caller's working directory BEFORE cd'ing to the repo root, so
    # `make restore FILE=../dumps/x.dump` from a subdirectory is not rejected as missing
    # — or worse, silently resolved to a same-named different file under the root.
    FILE="$(pwd)/${FILE}"
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

usage() {
    echo "usage: make restore FILE=backups/<dump>   (or: bash bin/restore-db.sh <dump>)" >&2
}

# See backup-db.sh: a missing binary must be reported as a missing binary, not as a
# database that is not accepting connections.
if ! command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose is not on PATH; this repo's stack is driven by it (see Makefile)" >&2
    exit 127
fi

# Credentials: environment first, then backend/.env, then the settings.py defaults.
# grep/cut, never `source` — backend/.env also holds the Google client secret.
# The `|| true` keeps a partial backend/.env from killing the script silently under
# `set -euo pipefail` before the defaults are ever reached (see backup-db.sh).
env_value() {
    local key="$1"
    [ -f backend/.env ] || return 0
    { grep -E "^[[:space:]]*(export[[:space:]]+)?${key}[[:space:]]*=" backend/.env || true; } \
        | tail -n 1 | cut -d= -f2- \
        | sed -e 's/\r$//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' \
              -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'$/\1/"
}

PG_DB="${POSTGRES_DB:-$(env_value POSTGRES_DB)}"
PG_USER="${POSTGRES_USER:-$(env_value POSTGRES_USER)}"
PG_DB="${PG_DB:-youtube_organizer}"
PG_USER="${PG_USER:-postgres}"

# Guard 1: a dump to restore, checked before the database is touched at all.
if [ -z "$FILE" ]; then
    echo "no dump given: FILE is required" >&2
    usage
    exit 1
fi
if [ ! -f "$FILE" ]; then
    echo "no such dump: ${FILE}" >&2
    usage
    exit 1
fi

# Guard 2: the same credential cross-check backup-db.sh does. Restoring into the wrong
# database is worse here than backing up the wrong one — it destroys what is there.
container_env() {
    docker-compose exec -T db printenv "$1" 2>/dev/null | tr -d '\r\n' || true
}

CONTAINER_DB="$(container_env POSTGRES_DB)"
CONTAINER_USER="$(container_env POSTGRES_USER)"
if [ -z "$CONTAINER_DB" ]; then
    echo "the db container is not running (could not read its POSTGRES_DB); run 'make up' first" >&2
    exit 1
fi
if [ "$PG_DB" != "$CONTAINER_DB" ] || { [ -n "$CONTAINER_USER" ] && [ "$PG_USER" != "$CONTAINER_USER" ]; }; then
    echo "credential mismatch — refusing to restore into a database that is not the library:" >&2
    echo "  resolved from environment/backend/.env: db='${PG_DB}' user='${PG_USER}'" >&2
    echo "  the db container was created with:      db='${CONTAINER_DB}' user='${CONTAINER_USER}'" >&2
    echo "Fix backend/.env to match docker-compose.yml's db service (or export POSTGRES_DB/POSTGRES_USER)." >&2
    exit 1
fi

if ! docker-compose exec -T db pg_isready -U "$PG_USER" -d "$PG_DB" >/dev/null 2>&1; then
    echo "the db service is not accepting connections; run 'make up' first" >&2
    exit 1
fi

# Guard 3: parse the archive BEFORE --clean drops anything. backup-db.sh runs exactly
# this probe before it will call a file a backup; the destructive path has more reason
# to run it, not less. A truncated or foreign-format file must not cost the library.
if ! docker-compose exec -T db pg_restore --list < "$FILE" >/dev/null 2>&1; then
    echo "not a readable PostgreSQL archive: ${FILE}" >&2
    echo "nothing was restored, and the live database was not touched" >&2
    exit 1
fi

# Row counts, per table, tolerating tables that do not exist yet.
#
# This distinction is the whole point: an EMPTY database — volume lost, container
# re-initdb'd — is the disaster this story exists to recover from, and it has none of
# these tables. A single `union all` over all three fails to parse in that case, and an
# earlier version of this script turned that into a refusal, which blocked the primary
# recovery path outright. "Absent" is information; "unreadable" is the actual problem.
LIBRARY_TABLES="auth_user organizer_usersocialtoken django_migrations"

db_is_readable() {
    docker-compose exec -T db psql -U "$PG_USER" -d "$PG_DB" -tAc "select 1;" >/dev/null 2>&1
}

print_counts() {
    local tbl exists n
    for tbl in $LIBRARY_TABLES; do
        exists="$(docker-compose exec -T db psql -U "$PG_USER" -d "$PG_DB" -tAc \
            "select to_regclass('public.${tbl}') is not null;" 2>/dev/null | tr -d '[:space:]')"
        if [ "$exists" != "t" ]; then
            echo "  ${tbl}: absent (this database has no such table yet)"
            continue
        fi
        n="$(docker-compose exec -T db psql -U "$PG_USER" -d "$PG_DB" -tAc \
            "select count(*) from ${tbl};" 2>/dev/null | tr -d '[:space:]')"
        echo "  ${tbl}: ${n}"
    done
}

# Guard 4: name what is about to be destroyed, with the row counts it holds now, and
# then require an explicit yes. Refuse when stdin is not a TTY and CONFIRM is unset.
echo "About to restore ${FILE}" >&2
echo "  into database '${PG_DB}' on the LIVE container (volume youtube-organizer_postgres_data)." >&2
echo "  --clean --if-exists: every object it contains is dropped and recreated." >&2
echo "  Objects NOT in the dump are left alone — this is not a point-in-time restore." >&2
echo "  That database currently holds:" >&2
# A database that cannot be read at all is a real problem worth stopping for; a database
# that is merely empty is not.
if ! db_is_readable; then
    echo "could not query '${PG_DB}' at all — it is not readable, not merely empty." >&2
    echo "refusing to restore over a database whose state cannot be established." >&2
    exit 1
fi
print_counts >&2

# CONFIRM is matched case-insensitively against y/yes, and anything else non-empty is
# rejected by name rather than silently treated as "no" — CONFIRM=y in a script that
# then reports success is a worse outcome than an explicit complaint.
CONFIRMED=no
case "$(printf '%s' "${CONFIRM:-}" | tr '[:upper:]' '[:lower:]')" in
    y|yes) CONFIRMED=yes ;;
    "") ;;
    *)
        echo "CONFIRM is set to '${CONFIRM}', which is not 'yes'; refusing rather than guessing" >&2
        exit 1
        ;;
esac

if [ "$CONFIRMED" != "yes" ]; then
    if [ ! -t 0 ]; then
        echo "refusing to restore unattended: re-run interactively, or set CONFIRM=yes" >&2
        exit 1
    fi
    # `read` failing (Ctrl-D, closed stdin) must say so rather than exiting silently
    # under set -e after all the pre-flight work has already run.
    if ! read -r -p "Type y to restore over ${PG_DB}: " reply; then
        echo "" >&2
        echo "aborted at the prompt; nothing was restored" >&2
        exit 1
    fi
    # Same spellings the CONFIRM variable accepts — a prompt that rejects "yes" while
    # the environment variable accepts it is a trap, not a safeguard.
    case "$(printf '%s' "$reply" | tr '[:upper:]' '[:lower:]')" in
        y|yes) ;;
        *)
            echo "aborted; nothing was restored" >&2
            exit 1
            ;;
    esac
fi

# Guard 5: a recovery point for the state we are about to destroy. Printing "take a
# backup first" is advice; taking one is a mechanism.
#
# But a failure here must NOT be a refusal. The conditions that make pg_dump fail —
# a corrupt cluster, an undumpable database, no room for a second copy of the library —
# are the same conditions that make someone reach for a restore in the first place. A
# hard refusal would make this tool unavailable in exactly the emergency it exists for.
# So: a loud warning, and a second confirmation that has to be typed in full.
echo "taking a pre-restore backup of the current state..." >&2
PRE_RESTORE=""
if PRE_RESTORE="$(bash bin/backup-db.sh)"; then
    echo "pre-restore backup: ${PRE_RESTORE}" >&2
else
    PRE_RESTORE=""
    echo "" >&2
    echo "WARNING: the pre-restore backup FAILED." >&2
    echo "  There will be no snapshot of the current state to fall back on. If this" >&2
    echo "  restore goes wrong, whatever is in '${PG_DB}' now is gone." >&2
    echo "  (This is expected if the cluster is already broken — which is also exactly" >&2
    echo "   when you may still want to proceed.)" >&2
    if [ "$CONFIRMED" = "yes" ]; then
        echo "  CONFIRM=yes was set, so continuing without a recovery point." >&2
    else
        if ! read -r -p "Type 'restore anyway' to continue with no recovery point: " reply2; then
            echo "" >&2
            echo "aborted; nothing was restored" >&2
            exit 1
        fi
        if [ "$(printf '%s' "$reply2" | tr '[:upper:]' '[:lower:]')" != "restore anyway" ]; then
            echo "aborted; nothing was restored" >&2
            exit 1
        fi
    fi
fi

# Guard 6: stop the app before dropping the objects it has open. Django holds
# connections and `restart: unless-stopped` keeps it coming back, so without this a
# DROP can block on an in-use object, and Django can write into a half-restored
# schema. Restart it on the way out whether or not the restore worked.
#
# INT/TERM get a handler that EXITS. A handler that merely returns lets bash resume the
# interrupted script — so a Ctrl-C here would run the cleanup and then carry straight on
# into the destructive pg_restore below, which is the opposite of what the person
# pressing it wants. SIGHUP too: closing the terminal is as common as Ctrl-C.
BACKEND_STOPPED=no
restart_backend() {
    if [ "$BACKEND_STOPPED" = "yes" ]; then
        echo "restarting the backend service..." >&2
        docker-compose start backend >/dev/null 2>&1 || \
            echo "could not restart the backend service; run 'make up'" >&2
        BACKEND_STOPPED=no
    fi
    return 0
}
on_signal() {
    echo "" >&2
    echo "interrupted; stopping here rather than continuing into the restore" >&2
    restart_backend
    exit 130
}
trap on_signal INT TERM HUP
trap restart_backend EXIT

# Announced, because this is the one step that can block indefinitely: a wedged
# backend container makes `docker-compose stop` hang, and a silent hang here is
# indistinguishable from a slow restore. It hangs *before* pg_restore runs, so the
# database is untouched if you have to Ctrl-C out of it.
echo "stopping the backend service so nothing writes during the restore..." >&2
if docker-compose stop backend >/dev/null 2>&1; then
    BACKEND_STOPPED=yes
else
    # Not fatal — the restore itself is transactional — but never silent: the docs and
    # the comment above both describe the stop as protection, and an operator is
    # entitled to know they did not get it.
    echo "WARNING: could not stop the backend service. Django may hold connections" >&2
    echo "  during the restore: DROPs can block on in-use objects, and the app can" >&2
    echo "  write into a schema that is still being rebuilt. Continuing anyway." >&2
fi

# --clean --if-exists so restoring over a populated database is deterministic instead
# of colliding on every existing object.
#
# --single-transaction makes the whole restore atomic: a mismatched major, a truncated
# archive or a dropped connection rolls back to the state that existed a moment ago
# instead of leaving the library half-dropped. It implies --exit-on-error, so the
# first real problem stops the run rather than being buried in the log.
#
# pg_restore can exit non-zero on warnings that are benign in principle (e.g. dropping
# an object the target never had). No exit code is tolerated here: the whole point of
# this story is that a restore either demonstrably worked or demonstrably did not, and
# a blanket `|| true` is how a half-restored library gets reported as a success. If a
# specific warning ever needs tolerating, enumerate that warning — do not widen this.
if ! docker-compose exec -T db pg_restore -U "$PG_USER" -d "$PG_DB" \
        --clean --if-exists --no-owner --no-privileges --single-transaction < "$FILE"; then
    echo "pg_restore failed." >&2
    # Deliberately not asserting the rollback happened: --single-transaction means it
    # should have, but a docker exec that died or a connection dropped mid-COMMIT
    # leaves the outcome genuinely unknown, and telling someone their database is fine
    # when it might not be is the worst thing this script could say.
    echo "  --single-transaction means the restore was meant to roll back whole." >&2
    echo "  VERIFY before trusting it: check the row counts above are unchanged." >&2
    if [ -n "$PRE_RESTORE" ]; then
        echo "  A pre-restore snapshot is at: ${PRE_RESTORE}" >&2
    else
        echo "  There is NO pre-restore snapshot (the backup failed earlier)." >&2
    fi
    exit 1
fi

restart_backend
trap - INT TERM HUP EXIT

# The drill in Docs/development-guide.md calls the migrate --check step "what
# distinguishes 'the bytes came back' from 'the library is recovered'". The path
# people actually use under pressure is this one, so it runs the same check here — and
# it shows what arrived, not only what was destroyed.
echo "the restored database now holds:" >&2
print_counts >&2

echo "verifying the restored schema against the current migration state..." >&2
# Capture, never discard: an exec failure and a genuine schema mismatch are different
# problems, and >/dev/null 2>&1 made every one of them read as "unapplied migrations".
if MIGRATE_OUT="$(docker-compose exec -T backend python manage.py migrate --check 2>&1)"; then
    echo "schema matches the current migration state." >&2
    # stdout is the success line and nothing else, and it comes last — a caller
    # scraping stdout must not see "restored" on a run that then exits non-zero.
    echo "restored ${FILE} into ${PG_DB}"
else
    echo "" >&2
    echo "the data restored, but 'migrate --check' did not pass:" >&2
    echo "${MIGRATE_OUT}" >&2
    echo "" >&2
    echo "If that output names unapplied migrations, the dump is older than the code in" >&2
    echo "this checkout — run 'make backend-migrate'. If it names a connection or import" >&2
    echo "error, the restore is probably fine and the backend container is not." >&2
    exit 1
fi
