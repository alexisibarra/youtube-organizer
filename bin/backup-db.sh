#!/bin/bash
# Timestamped pg_dump of the library database (AD-20, NFR-6).
#
# Deliberately shell + compose rather than a manage.py command: a backup is most
# needed exactly when Django cannot start (bad settings, broken migration,
# unimportable dependency), so it must not depend on Django importing at all.
#
# Three non-obvious constraints, all load-bearing:
#   * `exec -T` — without it Compose allocates a pseudo-TTY, which line-end
#     translates the binary custom-format stream. The file looks plausible, the
#     script exits 0, and the corruption surfaces on the one day it matters.
#   * write to .partial, mv on success — with `set -e`, a redirection whose
#     command fails still leaves the target behind. A truncated file that looks
#     like a backup is worse than no backup.
#   * a trap, not just failure branches — the target name is reserved before
#     pg_dump runs, so a Ctrl-C between the two would otherwise leave a zero-byte
#     .dump that is indistinguishable by name from a real backup.
set -euo pipefail

# A dump carries organizer_usersocialtoken — live Google OAuth refresh tokens — plus
# every user row. Treat it like a private key: 0700 on the directory, 0600 on the
# files, set before anything is created rather than chmod'ed after (a chmod leaves a
# window where the file is already world-readable).
umask 077

# Compose resolves docker-compose.yml relative to the working directory, so run
# from the repo root regardless of where the caller invoked this from.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Diagnose a missing binary as a missing binary. Without this, `docker-compose` not
# being on PATH exits 127 inside the readiness probe below and gets reported as
# "the db service is not accepting connections", which sends the reader to `make up`
# to fix a problem `make up` cannot fix.
if ! command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose is not on PATH; this repo's stack is driven by it (see Makefile)" >&2
    exit 127
fi

# Credentials: environment first, then backend/.env, then the settings.py defaults.
# Read the two keys out with grep/cut — do NOT source backend/.env: it also carries
# the Google client secret and OAUTHLIB_INSECURE_TRANSPORT, and sourcing executes
# whatever a stray backtick puts in there.
#
# The `|| true` is not decoration. Under `set -euo pipefail`, a key absent from
# backend/.env makes grep exit 1, pipefail propagates it out of the pipeline, and the
# `PG_DB="${POSTGRES_DB:-$(env_value POSTGRES_DB)}"` assignment below kills the script
# with no message at all — never reaching the defaults this function exists to fall
# back to. The fallback was unreachable whenever backend/.env existed but was partial.
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

# backend/.env is the DJANGO CLIENT's view of the database. The server's own identity
# comes from the hardcoded `environment:` keys on the db service in docker-compose.yml,
# and the two can diverge — backend/env.template ships POSTGRES_DB=your_db_name, so a
# developer who followed the template has a .env naming a database the container never
# created. Left unchecked that surfaces as "the db service is not accepting
# connections", which is a lie: the service is fine, we asked it for the wrong name.
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
    echo "credential mismatch — refusing to back up a database that is not the library:" >&2
    echo "  resolved from environment/backend/.env: db='${PG_DB}' user='${PG_USER}'" >&2
    echo "  the db container was created with:      db='${CONTAINER_DB}' user='${CONTAINER_USER}'" >&2
    echo "Fix backend/.env to match docker-compose.yml's db service (or export POSTGRES_DB/POSTGRES_USER)." >&2
    exit 1
fi

# Probe the database, not the container: a running container whose Postgres is
# still doing initdb would pass a mere `ps` check and fail the dump.
if ! docker-compose exec -T db pg_isready -U "$PG_USER" -d "$PG_DB" >/dev/null 2>&1; then
    echo "the db service is not accepting connections; run 'make up' first" >&2
    exit 1
fi

mkdir -p backups
# umask only governs files created from here on, so it cannot tighten a backups/ that
# an earlier version of this script already created 0755, nor the dumps already in it.
# Say both explicitly, every run — and report a failure instead of dying wordlessly
# under set -e, which is what happens when the directory belongs to another user.
if ! chmod 700 backups 2>/dev/null; then
    echo "could not chmod 700 backups/ — check its ownership (a sudo run, or a shared" >&2
    echo "checkout, leaves it owned by someone else). Dumps are credential files." >&2
    exit 1
fi
# Pre-existing dumps predate the umask and are likely 0644. Best effort: a dump we
# cannot re-secure is not a reason to refuse to take a new one.
chmod 600 backups/*.dump 2>/dev/null || true

# ISO 8601 UTC, colon-free: colons are illegal on some filesystems and break scp.
TS="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET="backups/${PG_DB}-${TS}.dump"

# Anything created from here on is provisional until the final mv, so arm the cleanup
# before the first file exists. INT/TERM as well as EXIT: the reserved TARGET is a
# zero-byte file with a real backup's name, and a Ctrl-C during the dump is the most
# likely way to create one.
PARTIAL=""
COMMITTED=no
cleanup() {
    # Once the mv has happened the artifact is a real backup and must survive. Without
    # this flag there is a window between `mv` and `trap -` in which a signal deletes
    # the finished, verified dump and the script still prints a success line naming it.
    if [ "$COMMITTED" = "yes" ]; then
        return 0
    fi
    [ -n "$PARTIAL" ] && rm -f "$PARTIAL"
    [ -n "${TARGET:-}" ] && rm -f "$TARGET"
    return 0
}
on_signal() {
    cleanup
    echo "" >&2
    echo "interrupted; no backup was written" >&2
    exit 130
}
# INT/TERM/HUP must EXIT, not return: a handler that returns lets bash resume the
# interrupted script, so the dump would carry on after a Ctrl-C that was meant to stop
# it. HUP is included because closing the terminal mid-dump is as common as Ctrl-C, and
# it leaves exactly the zero-byte artifact this trap exists to prevent.
trap on_signal INT TERM HUP
trap cleanup EXIT

# The timestamp is second-resolution, so two runs started within the same second
# resolve to the same name. Disambiguate rather than overwrite: a backup silently
# replacing an earlier backup is the same class of loss this whole story exists to
# prevent. The .partial carries the PID for the same reason — without it, two
# concurrent runs redirect two pg_dump streams into one file and interleave them.
SUFFIX=0
while :; do
    if [ "$SUFFIX" -gt 0 ]; then
        TARGET="backups/${PG_DB}-${TS}-${SUFFIX}.dump"
    fi
    # Reserve the name atomically. `set -C` (noclobber) makes the redirection fail if
    # the file already exists, which a plain `[ -e ]` test cannot do: between the test
    # and the mv, a concurrent run reaches the same verdict and one dump is lost.
    if (set -C; : > "$TARGET") 2>/dev/null; then
        break
    fi
    # Bounded, because the redirection also fails for reasons that will never clear:
    # an unwritable backups/, a full disk, a read-only filesystem. Unbounded, those
    # spin a silent infinite loop instead of reporting the actual problem.
    # A redirection that failed for any reason other than the name already existing
    # will fail identically 100 more times. Report that reason now instead of burning
    # the retries and then blaming the count.
    if [ ! -e "$TARGET" ]; then
        TARGET=""
        echo "could not create a backup file in backups/ (the name is free, so this is" >&2
        echo "not a collision) — check the directory is writable and the disk is not full" >&2
        exit 1
    fi
    SUFFIX=$((SUFFIX + 1))
    if [ "$SUFFIX" -gt 100 ]; then
        TARGET=""
        echo "could not create a backup file in backups/ after 100 attempts;" >&2
        echo "check that the directory is writable and the disk is not full" >&2
        exit 1
    fi
done
PARTIAL="${TARGET}.$$.partial"

# --format=custom: compressed, pg_restore-selectable, and --list-verifiable (which
# is what makes the integrity check below a real parse rather than a size check).
# --no-owner --no-privileges: a restore must not depend on the role names that
# happened to exist in the source cluster.
if ! docker-compose exec -T db pg_dump -U "$PG_USER" -d "$PG_DB" \
        --format=custom --no-owner --no-privileges > "$PARTIAL"; then
    echo "pg_dump failed; no backup written" >&2
    exit 1
fi

# A backup that has never been parsed is an assumption, not a backup.
if [ ! -s "$PARTIAL" ]; then
    echo "pg_dump produced an empty file; no backup written" >&2
    exit 1
fi
if ! docker-compose exec -T db pg_restore --list < "$PARTIAL" >/dev/null 2>&1; then
    echo "the dump did not parse as a PostgreSQL archive; no backup written" >&2
    exit 1
fi

# Set BEFORE the mv, not after: the flag is what makes cleanup a no-op, so it has to
# be true for every instant in which a finished artifact exists.
COMMITTED=yes
mv "$PARTIAL" "$TARGET"
PARTIAL=""
trap - INT TERM HUP EXIT
# stdout is the path and nothing else, so `$(bin/backup-db.sh)` is directly usable as
# one — restore-db.sh captures it and names it in its failure message, and a path with
# a size glued onto the end is not a path. The human-readable size goes to stderr.
echo "${ROOT}/${TARGET}"
echo "  ($(du -h "$TARGET" | cut -f1))" >&2
