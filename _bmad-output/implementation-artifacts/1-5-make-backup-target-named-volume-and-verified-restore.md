---
baseline_commit: b3172f5
---

# Story 1.5: `make backup` target, named volume, and verified restore

Status: done

Epic: 1 — Backend platform · Story key: `1-5-make-backup-target-named-volume-and-verified-restore`
Branch: `feat/story-1-5-backup-and-verified-restore` → PR → `develop` (squash). Never commit to `main`/`develop`.

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want a `make backup` target producing a timestamped `pg_dump`, a named Postgres volume, and a
documented restore verified once,
so that the library — the app's sole home after import — is durable from the first data-model story
(AD-20, NFR-6).

**Why this story exists, in one sentence:** Epic 4 lands `Video`/`Tag`/`VideoTombstone` and Epic 7
starts *deleting videos out of YouTube* after importing them — from that point the only copy of the
curated library is a Docker volume on one laptop, and this story is what stops `docker compose down -v`
or a disk failure from ending the product.

## Acceptance Criteria

**AC1 — `make backup` produces a timestamped dump, and the volume is named in `docker-compose.yml`**
**Given** the compose stack
**When** I run `make backup`
**Then** a timestamped `pg_dump` artifact is written to a known location, and the Postgres volume is
explicitly named in `docker-compose.yml`.

**AC2 — The restore path is documented and has actually been executed**
**Given** a populated database and a backup
**When** I follow the documented restore path into a fresh volume
**Then** the data is fully recovered, and the restore has been executed at least once and documented.

**AC3 — Nothing routine destroys the volume**
**Given** routine commands
**When** the team operates the stack
**Then** no routine command, script, or documented workflow destroys the named volume.

### Definition of Done (verifiable, no self-reporting)

Compose commands run **from the repo root** — never from `backend/` (Story 1.4 hit this live; Task 6
removes the cause). The Makefile uses `docker-compose`; use the same binary everywhere in this story.

**AC1**
- [x] `docker-compose config --volumes` and `docker volume ls` agree: the db volume's real Docker
      name is **`youtube-organizer_postgres_data`** — identical before and after your
      `docker-compose.yml` edit. Capture `docker volume ls | grep postgres` **before** you touch the
      file and paste both into Debug Log References. **If the name changes, you have silently
      orphaned every existing developer's library — revert immediately** (see Dev Notes → "The
      hyphen is load-bearing").
- [x] `make up` (or `docker-compose up -d db backend`), then `make backup` → exits **0** and prints
      the artifact path. `ls -l backups/` shows one file named
      `youtube_organizer-<YYYYMMDDTHHMMSSZ>.dump`, size **> 0**.
- [x] `file backups/youtube_organizer-*.dump` → reports `PostgreSQL custom database dump`, **not**
      `ASCII text` and not a file with CRLF line endings. A dump written without `exec -T` looks
      plausible and fails only at restore time (Dev Notes → "The `-T` trap").
- [x] `docker-compose exec -T db pg_restore --list < backups/<the dump>` → exits **0** and prints a
      TOC. This is the same integrity probe the script runs before it declares success.
- [x] Run `make backup` twice within the same minute → **two** files, no overwrite, no error
      (the timestamp is second-resolution; note the result honestly if you could not force a collision).
      **A same-second collision was forced** (two runs backgrounded in one shell) and it **failed**
      on the script as first written — see Completion Notes deviation 4 for the fix and the re-test.
- [x] With the stack **down** (`docker-compose stop db`), `make backup` → exits **non-zero** with a
      message naming `make up`, and **writes no file** into `backups/` (not even a zero-byte one).
      Restart the stack afterwards.

**AC2 — the drill (this is the AC, not a formality)**
- [x] Seed recognisable data first — an empty schema cannot demonstrate recovery. Record the exact
      seed you used and the counts (Dev Notes → "What there is to restore in August 2026").
- [x] Run the drill **exactly** as written in the new `Docs/development-guide.md` § *Backups &
      restore* — copy-paste it, do not improvise. If a step does not work as documented, **fix the
      document**, then re-run from the top. The document is the deliverable; your shell history is not.
- [x] The drill container comes up on a **throwaway volume** (`yo-restore-drill`), never the real one.
      Confirm with `docker inspect -f '{{range .Mounts}}{{.Name}}{{end}}' yo-restore-drill-db` →
      `yo-restore-drill`.
- [x] After `pg_restore` into the drill: row counts for `auth_user`, `organizer_usersocialtoken`,
      `django_migrations` **equal** the source counts. Paste both sides.
- [x] `POSTGRES_HOST=localhost POSTGRES_PORT=55432 python manage.py migrate --check` against the
      drill DB → exits **0** (`No planned migration operations` / no unapplied migrations). A schema
      that restored but cannot satisfy Django is not a recovered library.
- [x] Tear the drill down (`docker rm -f yo-restore-drill-db && docker volume rm yo-restore-drill`)
      and re-confirm `docker volume ls | grep postgres` still shows
      `youtube-organizer_postgres_data`, untouched.
- [x] The whole drill — commands, counts, and the date it was run — is written into **Completion
      Notes**. AC2 says "has been executed at least once and documented"; an undocumented run does
      not satisfy it.

**AC3**
- [x] `grep -rn -e "down -v" -e "down --volumes" -e "volume rm youtube-organizer_postgres_data" Makefile README.md backend/README.md Docs .githooks .github docker-compose.yml`
      → **no matches** (`backend/README.md:69` has one today; Task 5 is what removes it).
- [x] `test -f backend/docker-compose.yml` → **false** (Task 6).
- [x] `make restore` with no `FILE=` → exits **non-zero**, explains itself, touches nothing.
- [x] `make restore FILE=backups/<a real dump>` **non-interactively with `CONFIRM` unset**
      (`make restore FILE=… < /dev/null`) → exits **non-zero** and does **not** restore. Then verify
      the live DB is unchanged (row counts as before).
- [x] `bin/backup-db.sh` and `bin/restore-db.sh` are executable in git:
      `git ls-files -s bin/ | grep -E "backup-db|restore-db"` → mode **100755** for both. A `644`
      script works for whoever wrote it and fails for everyone who clones.

**Suite, gates, guards**
- [x] `docker-compose exec backend python manage.py test` → whole suite `OK`, exit 0. **State the
      arithmetic**: 87 (the 1.4 total) + the new tests = your number. Do not round it.
      **Corrected: the baseline is 93, not 87** (measured by running the suite with
      `test_durability.py` moved aside). 93 + 8 = **101**, `OK`.
      **Superseded by the code-review patch passes (2026-08-19):** the guard count is now **10**
      and the suite is **103**, `OK`. The container no longer skips any of them — `docker-compose.yml`
      mounts the checkout read-only at `/repo` and sets `REPO_ROOT`, so `make backend-test` runs all
      10 for real (verified: `Ran 103 tests ... OK` in the container).
- [x] `docker-compose exec backend python manage.py check` → `System check identified no issues`.
- [x] `docker-compose exec backend python manage.py makemigrations --check --dry-run` →
      `No changes detected`. **This story creates no migration.**
- [x] `make backend-coverage` → exits **0** with `fail_under = 70`. Record the figure and say whether
      it moved. (It should move up slightly: the new test file is fully executed and `*/tests/*` is
      omitted from measurement, so the effect is indirect — report what you actually see, do not
      predict it here.)
- [x] **Every new guard proven to bite** — the standing rule since 1.2. For each of the ten tests in
      `test_durability.py`: break the thing it guards, run
      `python manage.py test organizer.tests.test_durability`, confirm it **fails naming the right
      file**, revert. Paste at minimum the failures for the volume-name test, the `down -v` scan, and
      the `exec -T` test into Debug Log References. *A guard never seen to fail is not a guard.*
- [x] Host-side (pre-push layer 6/6): `cd backend && POSTGRES_HOST=localhost .venv/bin/python manage.py test --noinput`
      → green. The new tests read files from the repo root via a relative path, so a host run is the
      one that proves the path resolution is not container-specific.
- [x] `git status --porcelain` shows **no** `backups/` entries — the directory is ignored (Task 4).
      **A dump is a credential file** (Dev Notes → "A dump is a secret").

## Tasks / Subtasks

- [x] **Task 1 — Name the Postgres volume explicitly in `docker-compose.yml` (AC1)**
  - [x] **First, before editing:** `docker volume ls | grep postgres` and paste the output into the
        Debug Log. That literal string is the value you must preserve.
  - [x] Edit the top-level `volumes:` block only:
        ```yaml
        volumes:
          # Explicitly named (AD-20): the library is the app's sole home after import, so the
          # volume must not be re-derived from the checkout directory's name. This value is the
          # name Compose already generated implicitly (project "youtube-organizer" + "_" +
          # "postgres_data") — pinning it is a no-op for existing data, which is the entire point.
          # DO NOT "tidy" the hyphen into an underscore: that names a DIFFERENT volume, Postgres
          # initdb's into it empty, and every existing library is silently orphaned.
          postgres_data:
            name: youtube-organizer_postgres_data
          frontend_node_modules:
        ```
  - [x] Leave the `db` service's `volumes:` entry (`- postgres_data:/var/lib/postgresql/data/`)
        **byte-identical** — the service still references the compose-local key `postgres_data`;
        only the external name is now pinned.
  - [x] Do **not** add a `name:` to `frontend_node_modules`. It is a rebuildable cache, it is not
        what AD-20 protects, and pinning it buys nothing.
  - [x] Re-run `docker volume ls | grep postgres` and `docker-compose up -d db`. Same volume, same
        data. Verify by querying a row you know exists.

- [x] **Task 2 — `bin/backup-db.sh`: the dump (AC1)**
  - [x] New file `bin/backup-db.sh`, `chmod +x`, `#!/bin/bash` + `set -euo pipefail`. Match the
        existing `bin/` house style: a comment block at the top saying *why*, not *what* (see
        `bin/generate-backend-cert.sh`, whose comment explains the SAN requirement rather than the
        openssl flags).
  - [x] Resolve the repo root from the script's own location, and `cd` there:
        `ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"`. Compose resolves its
        file relative to the working directory; a script that only works when invoked from the root
        is a trap for the next person.
  - [x] Resolve `POSTGRES_DB` / `POSTGRES_USER`: environment first, then `backend/.env`, then the
        `settings.py` defaults (`youtube_organizer` / `postgres`). **Extract the two keys with
        `grep`/`cut`, do not `source backend/.env`** — that file also carries
        `OAUTHLIB_INSECURE_TRANSPORT` and the Google secrets, and sourcing it drags all of them into
        the script's environment (and executes anything a stray backtick puts there).
  - [x] **Readiness gate before writing anything:**
        `docker-compose exec -T db pg_isready -U "$PG_USER" -d "$PG_DB"` — on failure, print
        `the db service is not accepting connections; run 'make up' first` and `exit 1`. This
        probes the database, not the container's existence (same reasoning as `.githooks/pre-push`'s
        DB probe, which deliberately does not settle for a TCP connect on 5432).
  - [x] `mkdir -p backups`. Timestamp: `TS="$(date -u +%Y%m%dT%H%M%SZ)"` — UTC and colon-free
        (the spine's convention is ISO 8601 UTC; colons are illegal on some filesystems and break
        `scp`). Target: `backups/youtube_organizer-${TS}.dump`.
  - [x] **Write to `${TARGET}.partial` first, `mv` into place only on success.** With `set -e`, a
        `cmd > file` that fails still leaves `file` behind — a truncated dump that looks like a
        backup is worse than no backup at all.
  - [x] The dump command, exactly:
        ```
        docker-compose exec -T db pg_dump -U "$PG_USER" -d "$PG_DB" \
            --format=custom --no-owner --no-privileges > "${TARGET}.partial"
        ```
        **`-T` is non-negotiable** — see Dev Notes → "The `-T` trap". `--format=custom` (not plain
        SQL) so the artifact is compressed, `pg_restore`-selectable, and `--list`-verifiable.
        `--no-owner --no-privileges` so a restore does not depend on the role names that happened to
        exist in the source cluster.
  - [x] **Verify before declaring success**, two checks: the file is non-empty, and
        `docker-compose exec -T db pg_restore --list < "${TARGET}.partial"` exits 0. Only then `mv`.
        On failure, delete the `.partial` and exit non-zero. A backup that has never been parsed is
        an assumption, not a backup.
  - [x] Final line prints the resolved path and `du -h` size. Say nothing else — no emoji, no
        "Success!"; the repo's voice is dry (NFR-15).

- [x] **Task 3 — `bin/restore-db.sh` + the `Makefile` targets (AC1, AC3)**
  - [x] New file `bin/restore-db.sh`, `chmod +x`, same header/root-resolution/credential-resolution
        pattern as Task 2. **Factor the shared bits only if it stays readable** — two ~50-line scripts
        that each stand alone beat a `bin/_common.sh` nobody expects; the repo has no such precedent.
  - [x] **Guard 1:** `FILE` (env var or `$1`) is required and must exist. Missing → print the usage
        line and `exit 1` **before** touching the database.
  - [x] **Guard 2:** name what is about to be destroyed (the database, the container, the row counts
        it holds now), then require confirmation: `CONFIRM=yes` in the environment, **or** an
        interactive `y` on a prompt. **If stdin is not a TTY and `CONFIRM` is unset, refuse** — that
        is what makes it non-routine for AC3 and stops it ever being wired into a hook or CI step.
  - [x] Restore command:
        ```
        docker-compose exec -T db pg_restore -U "$PG_USER" -d "$PG_DB" \
            --clean --if-exists --no-owner --no-privileges < "$FILE"
        ```
        `--clean --if-exists` so restoring over a populated database is deterministic instead of
        colliding on every object. Note in a comment that `pg_restore` can exit non-zero on benign
        warnings; if you choose to tolerate any, enumerate exactly which and why — do **not** blanket
        `|| true`.
  - [x] `Makefile`: add `backup` and `restore` to `.PHONY` and to the *Backend targets* section, each
        one line delegating to its script (`bash bin/backup-db.sh`). Follow the file's existing
        habit of a comment block above the target explaining the trap it avoids — `backend-coverage`
        is the model. For `restore`, the comment must say it is **deliberately not runnable
        unattended**.
  - [x] `make restore` passes `FILE` through: `bash bin/restore-db.sh "$(FILE)"` (an unset `FILE`
        yields an empty argument, which Guard 1 catches).

- [x] **Task 4 — Keep dumps out of git (AC1, security)**
  - [x] `.gitignore`: add a `# Database backups` section with `backups/`. Place it near the
        `# Environments` block, whose `.env` entry it is the sibling of — **a dump contains
        `organizer_usersocialtoken`, i.e. live Google OAuth refresh tokens**, plus every user row.
        The one-line comment must say so; without it, someone "helpfully" commits a dump.
  - [x] Do **not** create `backups/.gitkeep`. The directory is created by the script and its contents
        are ignored; a tracked placeholder inside an ignored directory invites exactly the confusion
        this entry exists to prevent.

- [x] **Task 5 — Remove the documented workflow that destroys the volume (AC3)**
  - [x] `backend/README.md:64-70`: the *Troubleshooting* entry "If you need to reset the database,
        remove the `postgres_data` volume: `docker-compose down -v`" is **the exact instruction AD-20
        forbids** — a documented workflow that destroys the library. Replace it with a
        schema-preserving reset that does not touch the volume:
        `docker-compose exec backend python manage.py flush --noinput` (data cleared, schema and
        migrations intact), and, if a truly empty database is genuinely needed, a **back-up-first**
        sequence that runs `make backup` before anything destructive and links the restore doc.
  - [x] Same file, the *Notes* line "The database data is persisted in a Docker volume
        (`postgres_data`)": update to the explicit name and add that it is never destroyed by any
        documented command (AD-20), linking `Docs/development-guide.md` § *Backups & restore*.
  - [x] `Docs/deployment-guide.md`'s topology table says `volume postgres_data` — update to the
        explicit name. Do **not** touch anything else in that file; the production envelope is
        deferred whole (AD-17).

- [x] **Task 6 — Delete the stale `backend/docker-compose.yml` (AC1, AC3)**
  - [x] `git rm backend/docker-compose.yml`. It declares **a second `postgres_data` volume** against
        **`postgres:16`** while the real stack runs `postgres:15`. Under AD-20 that is not cosmetic:
        it is a second, conflicting definition of the one thing this story exists to make durable, and
        a developer who runs compose from `backend/` gets a *different* volume, a *different* Postgres
        major, and a backup taken against the wrong database. Story 1.4 hit the confusion live
        ("`service backend is not running` against a perfectly healthy container").
  - [x] This closes a `deferred-work.md` item whose text reads *"No story owns its deletion (1.5
        covers only volume naming)"*. It is in scope precisely because the trap **is** a volume-naming
        trap. Mark the item closed in `deferred-work.md` in the established style (an indented italic
        `_**CLOSED by Story 1.5.** …_` paragraph under the existing entry — do not delete the entry),
        and mark the duplicated entry under *code review of spec-ci-gate-stack.md* the same way.
  - [x] `grep -rn "backend/docker-compose.yml" . --exclude-dir=.git --exclude-dir=node_modules` and
        fix every surviving reference in prose (`_bmad-output/` story files are historical record —
        **leave them alone**; only fix live docs).

- [x] **Task 7 — Document the restore path, then run it (AC2)**
  - [x] `Docs/development-guide.md`: new `## Backups & Restore` section, placed after *Common
        Commands*. It must be **copy-pasteable end to end** — Task 7's DoD is that you executed
        exactly what you wrote. Contents:
        1. `make backup` — what it produces, where, and that dumps are gitignored **because they
           contain Google refresh tokens**.
        2. **Restore into a fresh volume (the drill)** — the full sequence in Dev Notes →
           "The restore drill", verbatim, including the teardown.
        3. **Restore in anger, over the live database** — `make restore FILE=backups/<file>`, with
           the confirmation guard described, and the standing advice to `make backup` first.
        4. A one-line statement that no documented command destroys
           `youtube-organizer_postgres_data` (AD-20), and what to do instead when you want a reset.
  - [x] `README.md` § *Useful Commands*: add `make backup` and `make restore FILE=…` with a pointer to
        the guide. While you are in that list, do **not** fix the unrelated broken
        `make backend-createsuperuser` reference — record it in `deferred-work.md` instead (it is a
        different defect and does not belong in this diff).
  - [x] **Now execute the drill** and record it in Completion Notes with real numbers and the date.

- [x] **Task 8 — `backend/organizer/tests/test_durability.py`: the standing guards (AC1, AC2, AC3)**
  - [x] New file, `SimpleTestCase` (no database — these are structural assertions over repo text, the
        pattern `test_layering.py` and `test_skeleton.py` established). Module docstring in the house
        style: what it owns, and the AD/NFR ids (AD-20, NFR-6).
  - [x] Repo root: `REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]` (tests → organizer →
        backend → root). Add a first assertion that `REPO_ROOT / "docker-compose.yml"` exists, so a
        wrong path fails as *"the guard cannot find the repo"* instead of silently passing.
  - [x] Seven tests, each named for the AC it defends:
        1. `docker-compose.yml`'s `volumes.postgres_data.name` is exactly
           `youtube-organizer_postgres_data`, **and** the `db` service still mounts `postgres_data`
           (AC1). Parse with `yaml.safe_load`.
        2. `bin/backup-db.sh` and `bin/restore-db.sh` exist and are executable (`os.access(..., os.X_OK)`).
        3. `Makefile` declares `backup` and `restore`, and both appear in `.PHONY`.
        4. `bin/backup-db.sh` invokes `pg_dump` through `exec -T` — a literal check that the `-T`
           flag is present on the exec line (AC1; see Dev Notes → "The `-T` trap"). This is the one
           test protecting against a corruption that no other check would notice until restore day.
        5. No tracked operational file instructs `down -v` / `down --volumes`, and none removes
           `youtube-organizer_postgres_data` (AC3). Scan a **named, explicit** file list — `Makefile`,
           `README.md`, `backend/README.md`, `docker-compose.yml`, `Docs/*.md`, `.githooks/*`,
           `.github/workflows/*.yml`. Do **not** walk the whole repo: `_bmad-output/` is historical
           record and `frontend/node_modules/` is enormous. Ban the three literals precisely — the
           drill legitimately runs `docker volume rm yo-restore-drill`, and a blunt `volume rm` ban
           would forbid the documented restore path this story is adding.
        6. `.gitignore` ignores `backups/`.
        7. `backend/docker-compose.yml` does not exist (AC1/AC3, Task 6).
  - [x] Every failure message must name the file and say what to do — these fire on someone who has
        never read this story.
  - [x] `yaml` is available today only as a transitive of `drf-spectacular`. Since a first-party test
        now imports it, **add it to `backend/requirements.txt` as a direct bounded pin** in the house
        style (a comment saying who needs it and why), using the version actually installed:
        `docker-compose exec backend pip show PyYAML` → pin **that** version. Do not guess a number.
        Rebuild (`docker-compose build backend && docker-compose up -d backend`) and run `pip check`;
        a `requirements.txt` change is not live in a container built earlier.
  - [x] Then do the **prove-it-bites** pass from the DoD, all ten.

### Review Findings

_Code review 2026-08-18. Three parallel layers (Blind Hunter, Edge Case Hunter, Acceptance Auditor)
against baseline `b3172f5`. 40 raw findings → 3 decision-needed (all resolved 2026-08-18, now patches), 18 patch, 3 deferred, 8 dismissed._

- [x] [Review][Patch] **Credential source of truth is the wrong file** — _resolved 2026-08-18: keep `backend/.env` as the source, but cross-check the resolved name against the `db` container and fail with a message naming the mismatch._ — `env_value()` in both scripts reads `backend/.env`, but the `db` container's `POSTGRES_DB`/`POSTGRES_USER` come from hardcoded `environment:` keys in `docker-compose.yml:20-22`. `backend/.env` is only the Django *client's* view, and `backend/env.template` ships `POSTGRES_DB=your_db_name`. A developer who followed the template gets `pg_isready` probing a nonexistent database and the misleading error "the db service is not accepting connections; run 'make up' first". Options: (a) read `docker-compose.yml` with PyYAML as the test already does, (b) read the container's own env via `docker-compose exec -T db printenv`, (c) keep `.env` but validate the resolved name against the container and fail with a message naming the mismatch.
- [x] [Review][Patch] **A failed `pg_restore` leaves the live library half-destroyed** — _resolved 2026-08-18: do both — invoke `bin/backup-db.sh` first and refuse if it fails, and add `--single-transaction` so a mid-flight failure rolls back whole._ — `bin/restore-db.sh:88-90` runs `--clean --if-exists` with no `--single-transaction` and takes no automatic pre-restore backup; it only *prints* "Take a backup first if you have not". A mismatched major, truncated archive or dropped connection exits non-zero with objects already dropped, no rollback and no snapshot. Options: (a) `--single-transaction` so a failure rolls back whole, (b) invoke `bin/backup-db.sh` first and refuse if that backup fails, (c) both.
- [x] [Review][Patch] **`RepoRootResolutionTests` is tautological, and the whole suite silently skips under the documented test command** — _resolved 2026-08-18: drop `@skipIf` from `RepoRootResolutionTests` only; the other classes keep skipping as documented._ The class was decorated `@skipIf(SKIP_REASON is not None, ...)` and `SKIP_REASON` is non-None precisely when `REPO_ROOT is None`, so `assertIsNotNone(REPO_ROOT, ...)` could only run when it was already guaranteed to pass. Compounding it: `make backend-test` runs in the backend container, which bind-mounts only `./backend` at `/app`, so all guards skipped there and a developer saw green from a suite that never executed. Disclosed as Completion Notes deviation 1 and genuinely mitigated in CI (verified: `ci.yml` checks out the full tree and runs from `backend/`). [backend/organizer/tests/test_durability.py]
- [x] [Review][Patch] `env_value()` aborts the script silently instead of falling back to the settings defaults [bin/backup-db.sh:33-46, bin/restore-db.sh:24-33] — reproduced: with `backend/.env` present but missing `POSTGRES_DB`, `grep` exits 1, `pipefail` propagates through the pipeline, and `PG_DB="${POSTGRES_DB:-$(env_value POSTGRES_DB)}"` kills the script under `set -e` with **no message and exit 1**, never reaching `PG_DB="${PG_DB:-youtube_organizer}"`. The documented tier-3 fallback is only reachable when `backend/.env` is absent entirely. Fix: `|| true` on the pipeline inside `env_value`.
- [x] [Review][Patch] `restore-db.sh` drops the live database before proving the archive is usable [bin/restore-db.sh:88-90] — `backup-db.sh` runs `pg_restore --list` as an integrity probe; the destructive counterpart runs no such check. Fix: run the same `pg_restore --list < "$FILE"` probe before the `--clean` invocation and exit non-zero if it fails.
- [x] [Review][Patch] The two scripts and the test file are untracked in git — `git ls-files -s bin/` lists only the three cert scripts; `git status --porcelain` reports `?? bin/backup-db.sh`, `?? bin/restore-db.sh`, `?? backend/organizer/tests/test_durability.py`. The AC3 DoD line claims `git ls-files -s bin/ | grep -E "backup-db|restore-db"` → mode `100755` for both, which does not hold as the tree stands. On-disk modes are `-rwxr-xr-x`, so `git add` restores 100755. Until they are staged, CI would not see the files at all.
- [x] [Review][Patch] An interrupted backup leaves a zero-byte `.dump` that looks like a backup [bin/backup-db.sh:56-79] — the name is reserved with `(set -C; : > "$TARGET")`, creating the real `.dump` filename *before* `pg_dump` runs, and cleanup only exists on the explicit failure branches. Ctrl-C, SIGTERM or a kill mid-dump leaves an empty `backups/<db>-<TS>.dump` plus an orphan `.partial` — the exact failure the `.partial`/`mv` design exists to prevent. Fix: `trap 'rm -f "$PARTIAL" "$TARGET"' INT TERM EXIT`, cleared before the successful exit.
- [x] [Review][Patch] The `-T` guard covers one of four `exec` invocations [backend/organizer/tests/test_durability.py:627-648] — Dev Notes → "The `-T` trap" states `-T` is required on **every** `exec` in both scripts, but `test_pg_dump_runs_through_exec_dash_t` filters on `"pg_dump" in line` and reads only `bin/backup-db.sh`. The `pg_restore --list` verification exec, both `pg_isready` execs, and `restore-db.sh`'s `pg_restore` exec are unguarded — and dropping `-T` on the restore path corrupts the archive on its way *in*.
- [x] [Review][Patch] The AC3 destructive-command scan has reachable blind spots [backend/organizer/tests/test_durability.py:536-559] — `OPERATIONAL_FILES` omits `bin/` (the files most likely to actually contain a volume-destroying command) and `.github/workflows/*.yaml` (only `*.yml` is globbed), and `Docs/*.md` does not recurse. `DESTRUCTIVE_LITERALS` is three exact substrings, missing `docker volume prune`, `docker system prune --volumes`, and `down --rmi all -v` (flag reordered).
- [x] [Review][Patch] `backend/README.md:47-49` still documents a now-broken setup path — step 3 says run `docker-compose up --build` from `backend/`, but this story deletes `backend/docker-compose.yml`. The documented first-run path errors with no compose file in that directory. The same edit should note what an affected developer does with a populated `backend_postgres_data` volume on postgres:16, which the diff orphans without a word.
- [x] [Review][Patch] Dumps are written with the ambient umask [bin/backup-db.sh:53,63] — `mkdir -p backups` and the `> "$TARGET"` redirect give `drwxr-xr-x` / `-rw-r--r--`. The diff argues correctly and repeatedly that a dump is a credential file "exactly like `.env`" (live Google OAuth refresh tokens plus every user row), then leaves it world-readable. Fix: `umask 077` before the redirect, or `chmod 600` the artifact.
- [x] [Review][Patch] The row-count preview swallows its own failure [bin/restore-db.sh:75-78] — the `psql` count query ends in `|| true`. If it errors (wrong DB, absent tables, permissions) the operator sees "That database currently holds:" followed by nothing and the confirmation proceeds anyway. The one screen designed to make the destruction concrete degrades to silence exactly when the target is not what the operator thinks it is.
- [x] [Review][Patch] The restore never stops the application [bin/restore-db.sh:88-90] — `backend` stays up with open connections and `restart: unless-stopped` while `--clean` drops every object. Django can write mid-restore and `DROP` can block on in-use objects. Fix: `docker-compose stop backend` around the restore (or `pg_terminate_backend` on that database), and say so in the guide.
- [x] [Review][Patch] Drill documentation defects (AC2 makes the document the deliverable) [Docs/development-guide.md:99-101] — step 7's `docker volume ls | grep postgres` cannot observe `yo-restore-drill` (the name contains no "postgres"), so it proves nothing about the teardown it is presented as verifying; step 6's `cd backend` persists for anyone pasting the block whole, silently changing the working directory for step 7; and step 6 depends on `backend/.venv`, which `.githooks/pre-push` treats as optional in a Docker-first workflow, with no instruction for creating it.
- [x] [Review][Patch] The in-anger restore path has none of the verification the drill calls essential [Docs/development-guide.md:107-117] — step 6 of the drill is singled out as "what distinguishes 'the bytes came back' from 'the library is recovered'", then omitted from the only path anyone will use under pressure: no row counts, no `migrate --check`. Also worth stating that `--clean --if-exists` drops only objects *present in the dump*, so restoring an older dump over a newer schema leaves a hybrid, not a point-in-time state.
- [x] [Review][Patch] Two prose claims are stronger than what is enforced — "**no command documented anywhere in this repo destroys it**" ([Docs/development-guide.md:43], [backend/README.md:59]) is false as written: `make restore` destroys the database contents, the drill documents a `docker volume rm`, and the scan deliberately excludes `_bmad-output/`, which still carries `down -v`. And "with stdin not a TTY and `CONFIRM` unset it refuses outright, which is what keeps it out of hooks, CI and scripts" ([Docs/development-guide.md:115-117]) overstates a speed bump — any CI step writing `CONFIRM=yes make restore FILE=...` sails through. Narrow both to what is actually enforced.
- [x] [Review][Patch] Script hardening, four small ones — `FILE` is resolved after `cd "$ROOT"`, so a relative dump path from a subdirectory is rejected or, worse, resolves to a same-named different dump [bin/restore-db.sh:18-19,44-54]; `CONFIRM` matches only the exact string `yes`, so `CONFIRM=y` silently refuses [bin/restore-db.sh:75]; the `SUFFIX` reservation loop is unbounded, so an unwritable `backups/` or a full disk spins forever [bin/backup-db.sh:56-67]; and a missing `docker-compose` binary exits 127 and is reported as "db not accepting connections; run 'make up' first" [both scripts].
- [x] [Review][Patch] Spec text says "seven tests" / "ten structural guards"; there are eight test methods (confirmed by a `-v 2` run: `Ran 8 tests ... OK`). The Completion Notes correctly say 8 and the prove-it-bites log covers all of them — this is a stale count in the DoD and scope-table text only.
- [x] [Review][Defer] `git clean -xfd` silently deletes every backup — deferred, pre-existing. `backups/` is ignored *and* inside the working tree, which is exactly what `-x` targets. A routine "clean my checkout" wipes the entire backup set with no warning in any doc or test.
- [x] [Review][Defer] The integrity check proves the archive parses, not that it contains anything [bin/backup-db.sh:78] — deferred. `pg_restore --list` would certify a perfectly valid backup of an empty or wrong database as good. A TOC check for the expected tables is the check the "found on the one day it matters" framing actually calls for.
- [x] [Review][Defer] `PyYAML==6.0.3` is a test-only import pinned into runtime `requirements.txt` [backend/requirements.txt:18-21] — deferred, pre-existing. There is no dev/test requirements split in this repo, so it ships into every image; the comment concedes it was already present transitively via drf-spectacular.

#### Review patch pass — 2026-08-18

All 18 patch findings applied. What changed, and what it cost:

- **`bin/backup-db.sh`** — `env_value` no longer dies under `set -euo pipefail` on a partial
  `backend/.env` (`{ grep ... || true; }`); credentials are cross-checked against the `db`
  container's own `POSTGRES_DB`/`POSTGRES_USER` and a mismatch is named instead of surfacing as
  "not accepting connections"; `umask 077` + `chmod 700 backups` so dumps are `0600` in a `0700`
  directory; a `trap ... INT TERM EXIT` removes the reserved target so an interrupt cannot leave a
  zero-byte `.dump`; the suffix loop is bounded at 100; a missing `docker-compose` reports itself.
- **`bin/restore-db.sh`** — same `env_value` and credential fixes; `FILE` is resolved to an absolute
  path *before* `cd "$ROOT"`; the archive is parsed with `pg_restore --list` before anything is
  dropped; the row-count preview no longer swallows failure with `|| true` and refuses if the counts
  cannot be read; `CONFIRM` is matched case-insensitively against y/yes and any other non-empty
  value is rejected by name; a **pre-restore backup is taken and the restore refuses if it fails**;
  `backend` is stopped for the duration and restarted via trap; `--single-transaction` makes the
  restore atomic; `migrate --check` runs afterwards, the same check the drill calls the real test.
- **`test_durability.py`** — `RepoRootResolutionTests` lost its `@skipIf` (it could only run when
  guaranteed to pass); two new guards: every non-echo `docker-compose exec` in **both** scripts must
  carry `-T`, and `restore-db.sh` must keep `CONFIRM`, the `-t 0` TTY test and `--single-transaction`.
  `OPERATIONAL_FILES` now covers `bin/`, `scripts/`, recursive `Docs/**`, and `.yaml` workflows;
  `DESTRUCTIVE_LITERALS` gained the prune forms. **8 guards → 10.**
- **Docs** — `backend/README.md` step 3 no longer points at the deleted `backend/docker-compose.yml`
  and tells an affected developer what to do with an orphaned `backend_postgres_data` volume;
  the drill's step 6 `cd` is a subshell so step 7 still runs from the root, `.venv` creation is
  documented, and step 7 greps for the drill volume *and* the real one (a single `grep postgres`
  cannot observe `yo-restore-drill` at all); the in-anger section documents the new guarantees, the
  non-point-in-time nature of `--clean --if-exists`, and `git clean -xfd` deleting `backups/`.
- **Prose narrowed** — "no command documented anywhere in this repo destroys it" was false as
  written (`make restore` destroys contents; the drill documents a `volume rm`). It now reads "no
  routine command in this repo's operational files", which is the property actually enforced. The
  unattended-refusal claim is now described as a speed bump, not as what enforces AD-20.

The new `-T` guard bit on first run, on an `echo` line printing a suggested interactive command —
the filter now excludes comments and echoed help text, which is the honest distinction between
printing a command and invoking one.

**Verified after the pass:** `manage.py check` clean; `makemigrations --check --dry-run` → no
changes; full suite **103 tests, OK** (101 + 2 new guards); `coverage report` **90.12%**, exit 0
against `fail_under = 70`; `bash -n` clean on both scripts. Live behaviour re-exercised against the
running `db`: `make backup` writes a `0600` artifact and exits 0; with the stack down it exits
non-zero and writes nothing; `POSTGRES_DB=not_the_library make backup` prints both sides of the
mismatch and refuses; `make restore` with no `FILE`, with a non-archive file, unattended with
`CONFIRM` unset, and with `CONFIRM=maybe` all exit non-zero without touching the database, showing
live counts 4/2/19.

**Now verified (2026-08-19).** The backend container was wedged on the first attempt —
`docker-compose start/logs/stop backend` all hung, the last killed at 25s — and the restore was not
run then. After the daemon recovered, the full chain was executed against the live database twice
(once on the first-pass script, once on the second-pass rewrite) and both went green: archive
parsed, counts shown, pre-restore snapshot written, `backend` stopped and restarted,
`--single-transaction` restore, post-restore counts **4/2/19 unchanged**, `migrate --check` →
"schema matches the current migration state", exit 0. `youtube-organizer_postgres_data` untouched
throughout. One fix came out of the wedged attempt: the stop step announces itself, because a
silent hang there is indistinguishable from a slow restore.

### Review Findings — second pass (2026-08-19)

_Re-review of the patched tree, same three layers, primed to be skeptical of the patches themselves.
Three regressions introduced by the first patch pass, two verified by running them. 2 decision-needed,
18 patch, 3 deferred, 6 dismissed._

- [x] [Review][Decision] **`make backend-test` and `make backend-coverage` are now permanently red** — dropping `@skipIf` from `RepoRootResolutionTests` (decision 3, first pass) did exactly what it was meant to, and the cost is now visible: the container mounts only `./backend`, so `_find_repo_root()` returns `None` and the class fails there by design. Measured in the container: `Ran 10 tests ... FAILED (failures=1, skipped=9)`. Because `make backend-coverage` runs `coverage run manage.py test` in that same container, it exits non-zero before `coverage report` runs, so the `fail_under = 70` gate never fires locally either. Two DoD lines that are ticked `[x]` — "whole suite `OK`, exit 0" and "`make backend-coverage` → exits **0**" — are now false as written. CI and the host are unaffected. A suite that is always red trains people to ignore it. Options: (a) mount the repo root read-only into the backend container so the guards run for real there, (b) revert to `@skipIf` and accept the tautology, (c) keep it red and rewrite the two DoD lines to say the container run is expected to fail.
- [x] [Review][Decision] **The mandatory pre-restore backup disarms the emergency path** — Guard 5 shells out to `bin/backup-db.sh`, which runs `pg_dump` against the cluster being replaced, and refuses the restore if it fails. The reasons you would be restoring in anger — a corrupt cluster, a database that will not dump, a disk with no room for a second copy of the library — are the same conditions that make `pg_dump` fail. There is no escape hatch, so the tool is unavailable in the emergency it was written for, and it silently doubles the free space a restore needs. Options: (a) add a documented `SKIP_PRE_BACKUP=yes` that names the risk on stderr, (b) downgrade the refusal to a warning plus a second confirmation, (c) skip the pre-backup automatically when the target has no tables (nothing to lose) and keep it mandatory otherwise.
- [x] [Review][Patch] **Restoring into an empty database is blocked — the primary AD-20 recovery scenario** [bin/restore-db.sh] — the row-count preview runs a `union all` over `auth_user`, `organizer_usersocialtoken` and `django_migrations` with no tolerance for absence, and the first-pass patch removed its `|| true`. After a real disaster (volume gone, container re-`initdb`'d) none of those tables exist, so the query errors and the script exits with "refusing to restore over a database whose current contents cannot be shown". Verified against the live container: `ERROR: relation "auth_user" does not exist`. The guard must distinguish "the database is empty" from "the database is unreadable" — `to_regclass()` per table, reporting absent tables as absent. It also breaks permanently the day a migration renames any of the three.
- [x] [Review][Patch] **A signal during the restore falls through into `pg_restore` instead of aborting** [bin/restore-db.sh] — `trap restart_backend INT TERM EXIT` installs a handler that ends in `return 0`; bash runs it and then *resumes* the interrupted script. Verified with SIGTERM: the handler ran, execution continued into the destructive step, and the script exited **0**. Someone pressing Ctrl-C at "stopping the backend service..." gets the restore they were trying to stop. Fix: a separate `on_signal` that calls `restart_backend` then `exit 130`, with the plain handler left on `EXIT` — verified to abort correctly with exit 130.
- [x] [Review][Patch] **The same trap defect in the backup script, plus a window that deletes a good backup** [bin/backup-db.sh] — `cleanup` also returns rather than exiting, so a signal mid-dump cleans up and then carries on. Worse, `mv "$PARTIAL" "$TARGET"` and `trap - INT TERM EXIT` are two statements apart: a signal in that window fires `cleanup`, which `rm -f`s the freshly committed, verified dump, and the script then continues and prints a success line naming a file that no longer exists. Disarm before the `mv`, or gate `cleanup` on a `COMMITTED` flag.
- [x] [Review][Patch] `FILE` from the environment silently beats the positional argument [bin/restore-db.sh] — `FILE="${FILE:-${1:-}}"`. On a destructive command the explicit argument should win; as written, `bash bin/restore-db.sh ./good.dump` in a shell with `FILE` exported restores something the operator never named. Prefer the positional, or refuse when both are set and differ.
- [x] [Review][Patch] `migrate --check` discards the real error and misdiagnoses it [bin/restore-db.sh] — it runs under `>/dev/null 2>&1`, then picks between "backend not running" and "unapplied migrations" using `docker-compose ps backend | grep -q backend`, which lists exited containers under v1 and is racy under v2 (the container was started one line earlier). Any transient exec failure after a *successful* restore is reported as a schema mismatch with exit 1 — the message most likely to send someone to run another destructive command. Capture the output and print it.
- [x] [Review][Patch] A failed `docker-compose stop backend` is silently ignored but documented as a guarantee [bin/restore-db.sh] — output is discarded and the script proceeds to `pg_restore` with Django still connected and `restart: unless-stopped` in force. Both the in-file comment and `Docs/development-guide.md` state the stop as something that happened. Either abort on failure or say "attempted" in both places.
- [x] [Review][Patch] The interactive prompt rejects a spelling `CONFIRM` accepts, and EOF exits silently [bin/restore-db.sh] — the prompt matches only `y`, while `CONFIRM` accepts `y` or `yes`; and `read` failing on Ctrl-D exits under `set -e` with no "aborted" message after all the pre-flight work has run.
- [x] [Review][Patch] The in-anger path never shows what arrived [bin/restore-db.sh] — pre-restore counts are printed and treated as load-bearing; post-restore counts are never taken. The drill compares both sides and calls that the point of the exercise.
- [x] [Review][Patch] Two output defects on the success path [bin/restore-db.sh] — `echo "restored ${FILE} into ${PG_DB}"` goes to stdout *before* verification, so a caller scraping stdout sees success on a run that then exits 1; and the failure message asserts "`--single-transaction` rolled the database back" for any non-zero exit, including ones where the transaction's fate is genuinely unknown (docker exec died, connection dropped mid-COMMIT).
- [x] [Review][Patch] Both `-T` guards are defeated by the `docker compose` (v2, no hyphen) spelling [backend/organizer/tests/test_durability.py] — they match the literal `docker-compose exec`, so a wholesale switch to the v2 CLI silently disables them rather than failing. The same applies to `DESTRUCTIVE_LITERALS`: `docker compose down -v` passes the scan and the prose that claims no operational file can destroy the volume. Match both spellings.
- [x] [Review][Patch] The `-T` guard's exclusion filter is shape-based and evadable [backend/organizer/tests/test_durability.py] — lines are exempt when they start with `#` or `echo `, so a `printf`, a heredoc, or a compound line (`foo && docker-compose exec db …`) either evades the guard or trips it wrongly.
- [x] [Review][Patch] `path.read_text()` in the destructive-command scan will raise on a non-UTF-8 file [backend/organizer/tests/test_durability.py] — now that `bin/` and `scripts/` are globbed, any binary dropped there fails the durability suite with a `UnicodeDecodeError` that says nothing about durability. Use `errors="replace"`.
- [x] [Review][Patch] `chmod 700 backups` can abort the run with no message [bin/backup-db.sh] — if `backups/` exists but is owned by another user (a `sudo` run, a shared checkout) the `chmod` fails under `set -e` and no backup happens. Report it.
- [x] [Review][Patch] `SIGHUP` is not trapped [bin/backup-db.sh] — closing the terminal during a long dump is at least as common as Ctrl-C and leaves exactly the zero-byte artifact the trap exists to prevent.
- [x] [Review][Patch] `env_value` understands one spelling of a `.env` line — `^KEY=` misses `export KEY=`, `KEY =`, leading whitespace and trailing comments. A `.env` written any of those ways falls through to the defaults, which happen to match `docker-compose.yml`, so the credential cross-check passes and the mis-parse stays invisible.
- [x] [Review][Patch] `umask 077` does not retrofit the dumps already on disk — five artifacts in `backups/` are still `-rw-r--r--` next to the post-patch `-rw-------` ones. The directory is now `0700`, which mitigates it locally but not for anything that copies or archives the tree.
- [x] [Review][Patch] The two new guards have no prove-it-bites evidence — the standing rule since 1.2, and DoD line 119 is ticked. The Debug Log documents seven breakages and predates this pass; `test_every_compose_exec_in_both_scripts_passes_dash_t` and `test_restore_refuses_to_run_unattended` are not in it. (The `-T` guard was incidentally seen to bite on an `echo` line; the CONFIRM/`-t 0`/`--single-transaction` guard has never been seen to fail.)
- [x] [Review][Patch] The spec's own numbers are now further out of date, not fixed — first-pass finding 18 was ticked, but the patch pass changed the counts again. There are **10** test methods and the host suite is **103**, while the DoD still reads "93 + 8 = **101**", "8 of those 101 skip" (actual: 9 skip + 1 fail in the container), "For each of the eight tests", the scope table "ten structural guards", the File List "seven guards", and the Change Log "Suite 93 → 101".
- [x] [Review][Patch] `backend/README.md` removed the only documented way to get an empty database — the prose says "if you genuinely need an empty database (a corrupt cluster, not a messy one), **back up first** and restore afterwards" and then gives no command sequence for it. Add the explicit steps under the warning.
- [x] [Review][Defer] Nothing checks the archive against the target — deferred. `pg_restore --list` proves the file parses; no check compares its origin database or expected tables to `$PG_DB`, so a well-formed archive from any project is accepted into the library. Pairs naturally with the deferred TOC-content check.
- [x] [Review][Defer] No lock against concurrent runs — deferred. Two restores, or a backup racing a restore, interleave; the pre-restore backup can capture a half-restored state. A `flock` on `backups/.restore.lock` is the shape.
- [x] [Review][Defer] The volume pin assumes the clone directory name — deferred. `name: youtube-organizer_postgres_data` is correct only because the checkout is named `youtube-organizer`; a differently-named clone (or `COMPOSE_PROJECT_NAME`) gets a pin pointing at a volume Compose would not otherwise have created, and Postgres `initdb`s it empty. The comment warns about editing the literal but not about this.

#### Second review pass — resolution (2026-08-19)

Decisions: **1(a)** mount the checkout into the backend container; **2(b)** warn and re-confirm
instead of refusing when the pre-restore backup fails.

The first patch pass introduced three regressions. All three are fixed and the fixes were run:

1. **Restoring into an empty database was blocked** — removing a `|| true` turned a `union all`
   over three hardcoded tables into a hard refusal, which is exactly the disaster case. Now each
   table is probed with `to_regclass` and reported `absent`; only a database that cannot be queried
   at all stops the restore. Verified against an empty database: all three report absent, no refusal.
2. **Signals did not abort** — `trap restart_backend INT TERM EXIT` ran the handler and then let
   bash *resume*, so a SIGTERM during the backend stop fell through into `pg_restore` and exited 0
   (demonstrated). Both scripts now use an `on_signal` handler that exits 130, with the plain
   handler on `EXIT` and `HUP` added.
3. **A signal could delete a finished backup** — the window between `mv` and `trap -` is closed
   with a `COMMITTED` flag set before the `mv`.

Also fixed: the positional argument now beats an inherited `FILE`; `migrate --check` output is
captured and printed instead of discarded into a "unapplied migrations" misdiagnosis; a failed
`docker-compose stop backend` warns instead of being silent (and the docs now say "attempts");
the prompt accepts the same spellings as `CONFIRM` and reports EOF; post-restore counts are shown;
the success line moved to stdout *after* verification; the failure message no longer asserts a
rollback it did not observe; `chmod` failures are reported; pre-existing `0644` dumps are
retrofitted to `0600`; `env_value` understands `export`/spacing; the reservation loop reports a
permanent failure instead of retrying 100 times.

Guards: `_find_repo_root()` honours a validated `REPO_ROOT`; both `-T` guards accept the
`docker compose` (v2) spelling; the scan decodes with `errors="replace"`; and physical lines are
joined across backslash continuations before matching.

**A guard caught in the act.** The `--single-transaction` assertion was a whole-file text search —
so it passed on the comment explaining the flag and stayed green when the flag was deleted from the
actual command. Rewritten to check the writing `pg_restore` invocation itself, which is what
exposed the continuation-line problem above.

**Prove-it-bites, all four demonstrated** (break → run → confirm the message names the right file →
revert): dropping `--single-transaction` from the invocation, dropping `-T` from restore's
`pg_restore`, dropping the `[ ! -t 0 ]` TTY test, and dropping `-T` from backup's `pg_dump` (which
correctly trips both `-T` guards at once).

**Verified after this pass:** host suite `Ran 103 tests ... OK`; **in the container**
`make backend-test` → `Ran 103 tests ... OK` and `make backend-coverage` → **90.12%**, exit 0 — the
two DoD lines the audit found broken are true again, and the durability guards now genuinely execute
there instead of skipping. `bash -n` clean on both scripts. Live: `make backup` (0600 artifact in a
0700 directory, clean path on stdout), and a full `CONFIRM=yes make restore` chain green with counts
4/2/19 unchanged.

One second-pass finding was a false positive and was not acted on: `DESTRUCTIVE_LITERALS` was said
to miss `docker compose down -v`, but `"down -v"` is already a substring of it. A first-pass finding
was also refuted: `cleanup()` does not abort under `errexit` before removing `TARGET`.

## Dev Notes

### Scope table — what this story may touch

| Path | Change | Note |
| --- | --- | --- |
| `docker-compose.yml` | UPDATE | **Only** the top-level `volumes:` block. Services untouched. |
| `bin/backup-db.sh` | NEW | executable (100755) |
| `bin/restore-db.sh` | NEW | executable (100755) |
| `Makefile` | UPDATE | `backup`, `restore` targets + `.PHONY` |
| `.gitignore` | UPDATE | `backups/` |
| `backend/README.md` | UPDATE | remove `down -v`; fix the volume note |
| `Docs/development-guide.md` | UPDATE | new § *Backups & Restore* |
| `Docs/deployment-guide.md` | UPDATE | one line: the volume's explicit name |
| `README.md` | UPDATE | two lines in *Useful Commands* |
| `backend/docker-compose.yml` | **DELETE** | stale `postgres:16` duplicate |
| `backend/organizer/tests/test_durability.py` | NEW | ten structural guards |
| `backend/requirements.txt` | UPDATE | direct `PyYAML` pin |
| `_bmad-output/implementation-artifacts/deferred-work.md` | UPDATE | close 2 items, raise any new |

**Explicitly out of scope — do not touch:** `backend/youtube_organizer/settings.py` (no setting
changes here), `organizer/` production code, `.github/workflows/*` (CI has no volume — it uses a
service container, so `make backup` has nothing to run against there; do not add a CI step for it),
`.githooks/*`, `deploy.yml` and anything production (AD-17 defers the whole envelope), the
`docker-compose`→`docker compose` CLI migration (repo-wide or not at all — not smuggled in here),
backup retention/pruning (dumps accumulate; that is a real future item, and the honest place for it
is `deferred-work.md`), and the frontend.

### Existing state of the files you will modify

**`docker-compose.yml`** — three services (`backend`:8000, `db` postgres:15 :5432, `frontend`:3000),
two top-level volumes declared bare: `postgres_data:` and `frontend_node_modules:`. The `db` service
mounts `postgres_data:/var/lib/postgresql/data/` and reads `POSTGRES_DB/USER/PASSWORD` from an inline
`environment:` block (values `youtube_organizer`/`postgres`/`postgres`) — note this is the *service*
block, **not** `backend/.env`; the backend reads its own copy from `env_file`. Both agree today.

**`Makefile`** — `.PHONY` list, then *Backend targets* (`backend-migrate`, `backend-test`,
`backend-coverage`), *Frontend targets*, *App-level targets* (`up`). Every non-obvious target carries a
comment block explaining the trap it avoids; `backend-coverage`'s comment (the bind-mount/rebuild trap)
is the model to copy. Uses **`docker-compose`**, tab-indented recipes — the Makefile is the one file
where tabs are mandatory syntax, not style.

**`backend/README.md`** — the *Troubleshooting* section at :64-70 is the AC3 violation; the *Notes*
section at :57-60 describes the volume. Both change in Task 5.

**`.gitignore`** — sectioned by topic (`# OS`, `# Python`, `# Django`, `# Environments`, …). Already
ignores `.env`; `backups/` belongs alongside it, for the same reason.

### The hyphen is load-bearing

Compose derives an unnamed volume's real name as `<project>_<key>`, and the project name defaults to
the sanitised checkout directory — here `youtube-organizer`, so the volume on disk is
**`youtube-organizer_postgres_data`** (hyphen in the project part, underscore before the key).

Pinning `name:` to that exact string is a **no-op on disk** and that is deliberate: `git pull` must
not be able to disconnect a developer from their library. Writing `youtube_organizer_postgres_data`
instead — which reads "tidier" and matches the Python package name — names a volume that does not
exist, so Postgres `initdb`s a fresh empty one and the old volume is orphaned (not deleted: recoverable
by reverting, but the app comes up empty and the developer's first assumption is data loss).
**Verify the literal against `docker volume ls` before and after. Do not type it from memory.**

Second-order effect worth knowing: an explicitly named volume is **project-independent**, so
`docker-compose -p some-other-name up` now attaches to the *same* volume rather than a fresh one.
That is why the AC2 drill uses a bare `docker run` on a throwaway volume instead of a second compose
project — a `-p` drill would restore straight over the real library. This is the single most dangerous
mistake available in this story.

### The `-T` trap

`docker-compose exec` allocates a pseudo-TTY by default. A TTY performs line-ending translation, so
piping `pg_dump --format=custom` through it silently corrupts the binary stream. The file appears,
has a plausible size, and `make backup` exits 0 — and the corruption is discovered on the one day it
matters. `-T` disables the TTY. It is required on **every** `exec` in both scripts (dump, restore, and
the `pg_restore --list` verification), and Task 8 test 4 exists solely to stop a future edit dropping it.

The `file backups/*.dump` DoD check is the cheap human-visible version of the same test:
a good custom-format dump reports `PostgreSQL custom database dump`.

### The restore drill (AC2) — copy this into the guide, then run it

Preconditions: the stack is up, `make backup` has produced a dump, and you have seeded recognisable
data. `55432` is used to avoid colliding with the real `db` on 5432.

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
docker inspect -f '{{range .Mounts}}{{.Name}}{{end}}' yo-restore-drill-db   # → yo-restore-drill

# 4. Restore. The DB already exists (the entrypoint created POSTGRES_DB) and is empty.
docker exec -i yo-restore-drill-db pg_restore -U postgres -d youtube_organizer \
  --no-owner --no-privileges < backups/youtube_organizer-<TS>.dump

# 5. Same counts as step 1?
docker exec -i yo-restore-drill-db psql -U postgres -d youtube_organizer -c "<the query from step 1>"

# 6. Django agrees the schema is current. From backend/, against the drill port.
cd backend && POSTGRES_HOST=localhost POSTGRES_PORT=55432 .venv/bin/python manage.py migrate --check

# 7. Tear down. Note this removes ONLY the drill volume.
docker rm -f yo-restore-drill-db && docker volume rm yo-restore-drill
docker volume ls | grep postgres    # → youtube-organizer_postgres_data, untouched
```

Step 6 is what distinguishes "bytes came back" from "the library is recovered": it asserts the restored
schema is exactly what the current migration state expects.

### What there is to restore in August 2026

The schema today is Django's own tables plus **one** app model — `organizer_usersocialtoken`
(`backend/organizer/models/user_social_token.py`, migration `0001_initial`). `Video`, `Tag` and
`VideoTombstone` do not exist until Epic 4. So a drill run against whatever is lying in your dev
database may restore **zero rows** and prove nothing.

**Seed first.** Cheapest honest seed, in `manage.py shell` before the backup:

- two or three users via `User.objects.create_user(...)` with recognisable usernames, and
- one `UserSocialToken` row with a distinctive (fake) token string.

Then the counts in drill steps 1 and 5 are a real comparison, and the story's central claim — *the
data is fully recovered* — is something you observed rather than inferred. Say in Completion Notes
exactly what you seeded, so a reader of the record knows how strong the evidence is.

This is also the honest limitation to record: the restore path is verified against a **1-model schema**.
It is verified enough for AD-20 to be satisfied now, and Epic 4 (which lands the real library) should
re-run this drill against real data. That belongs in `deferred-work.md`, targeted at Epic 4.

### A dump is a secret

`organizer_usersocialtoken` stores Google OAuth **refresh** tokens — long-lived credentials for a
scope that Epic 6 widens to include *write* access to the user's YouTube account. A dump is therefore
a credential file, not just data:

- `backups/` is gitignored (Task 4) — the comment must say why, or someone will "un-ignore" it.
- Do not paste dump contents into the story file, a PR, or an issue.
- NFR-9 raises the stakes deliberately: *"a leaked token can now destroy source data."*
- Not in scope, but worth a `deferred-work.md` line: dumps are unencrypted and unpruned on disk.

### Why `--format=custom`

`-Fc` over plain SQL, in exchange for needing `pg_restore` instead of `psql`:

- **Verifiable.** `pg_restore --list` parses the archive TOC and fails on a truncated or corrupt file
  — which is what turns Task 2's "verify before success" from a size check into a real one.
- **Compressed** by default.
- **Selective** on restore (`-t`, `-n`, `--data-only`), which matters the first time recovery is
  partial rather than total.
- **Ordering.** `pg_restore` restores data before indexes and constraints; a plain-SQL `psql` restore
  is the one that dies halfway on an FK it cannot yet satisfy.

`--no-owner --no-privileges` because the roles in the target cluster are not guaranteed to match the
source's — this is what makes the drill container (a stock `postgres:15` with only the `postgres` role)
work at all.

### The 70% coverage gate, and why it is not at risk

`fail_under = 70` is live in `backend/.coveragerc` (story 1.4 took the total to **90%**). This story
adds no production code — only a test file, and `*/tests/*` is in the `omit` list. Report the measured
figure; do not predict it.

Note `make backend-coverage` runs in the container and `coverage` is installed **in the image**: a
`requirements.txt` change (Task 8's PyYAML pin) is not live until you rebuild. This is the same
bind-mount trap the Makefile comment already documents.

### Tooling facts (verified on this machine, 2026-08-18)

- `docker-compose` **2.39.2** (standalone) and `docker compose` **v5.3.1** (CLI plugin) both present;
  Docker Engine **29.6.2**. The Makefile uses `docker-compose` — match it.
- `db` image is `postgres:15`, so the in-container `pg_dump`/`pg_restore` are version-matched to the
  server. **Always dump through the container**, never a host-installed client: a host `pg_dump` from
  a newer major refuses to talk to an older server, and one from an older major produces an archive
  the newer `pg_restore` will not read.
- The top-level `volumes: <key>: name:` field is standard Compose-spec and supported by both CLIs here.
- Postgres 15 reaches end-of-life in **November 2027** (from model knowledge — verify before relying on
  it for scheduling). Not this story's problem; the image-pinning question is already an open
  `deferred-work.md` item ("Base and DB images are unpinned").

### Previous-story intelligence (1.1 → 1.4)

Patterns established that this story must not break:

- **Prove every guard bites.** Standing since 1.2: temporarily break the thing, watch the test fail
  naming the right file, revert, paste the failure into Debug Log References. 1.4 did this for the
  layering write-ban and for the coverage gate itself (`fail_under = 99` → exit 2). Seven new guards
  here means seven demonstrations.
- **Structural tests are `SimpleTestCase` and read repo text via `pathlib`**, never by importing the
  thing under inspection (`test_layering.py` does AST analysis for exactly this reason).
- **`requirements.txt` changes need a container rebuild.** 1.4's DoD opens with this and calls a stale
  container the way to make every other check meaningless.
- **Run compose from the repo root.** 1.4 hit the stale `backend/docker-compose.yml` live and lost time
  to `service "backend" is not running` against a healthy container. Task 6 removes the cause.
- **Deviations are disclosed, not smoothed over.** 1.4's Completion Notes list three deliberate
  departures from the story as written, each with its reasoning, and struck an unsatisfiable DoD line
  rather than ticking it. Do the same: if a DoD line here turns out to be wrong, **strike it with an
  explanation**; do not quietly satisfy a weaker version of it.
- **Test-count arithmetic is stated, not rounded.** The baseline entering this story is **87**.
- **`deferred-work.md` is maintained, not appended blindly.** 1.4 closed four items, re-targeted three,
  raised two, and *corrected a prediction that turned out false* rather than leaving it to send the
  next story hunting a phantom. Follow that discipline for the two items Task 6 closes.

**Recent commits** (`b3172f5` back): the shape is one squashed `feat(backend): …` /`ci: …` commit per
story behind a merge commit from `feat/story-*`. Yours is infrastructure, not backend code — a
Conventional Commits type of **`feat`** with a scope like `feat(ops):` fits; `chore:` understates a
story that adds the product's only durability mechanism. No AI/bot attribution anywhere.

### Project Structure Notes

- Scripts live in `bin/` (`generate-all-certs.sh`, `generate-backend-cert.sh`,
  `generate-frontend-cert.sh`) — bash, `#!/bin/bash`, executable, with a comment explaining the
  non-obvious constraint. `bin/backup-db.sh` and `bin/restore-db.sh` join them; do **not** invent a
  `scripts/` or `ops/` directory.
- Backend tests: `backend/organizer/tests/test_<subject>.py`. Discovery pattern is `test*.py` —
  **`durability_test.py` would be silently never run.**
- `backups/` is a new top-level directory, gitignored, created by the script at runtime.
- Indentation: new bash and Python files are 4-space/PEP 8 (the `auth/` package set this precedent).
  The `Makefile` requires **tabs** in recipes. Do not reformat any file wholesale.
- Docs live in `Docs/` (authoritative for CI and frontend stack); `README.md` and `backend/README.md`
  are the setup entry points. `_bmad-output/` is planning/implementation record.

### Anti-patterns — do not do these

- **Do not write the backup script in Python as a `manage.py` command.** It must work when Django
  cannot start (bad settings, broken migration, unimportable dependency) — that is precisely when you
  need a backup. Shell + compose has no such coupling. It also keeps `services/` out of it, so AD-1
  never enters the picture.
- **Do not add a CI job that runs `make backup`.** CI has no named volume and no library; it runs a
  `postgres:15` service container that is destroyed after every job. The standing guards in
  `test_durability.py` are the CI-side protection, and they already run in the `test` job.
- **Do not add a cron, scheduler, or hook that runs `make backup`.** NFR-12/AD-9: Phase 1 has no
  scheduler of any kind, for anything. The target is user-triggered, like `sync_inbox` will be.
- **Do not gate anything on backup recency yet.** AD-20's gate applies to FR-4 (YouTube-side playlist
  deletion), which is **Phase 2** and does not exist. Import and inbox-clear are explicitly *not*
  gated. Building the gate now is speculative work against an absent caller.
- **Do not "improve" `make up`, `make backend-migrate`, or the pre-push hook** while you are in these
  files.
- **Do not `source backend/.env`** in either script (Task 2).
- **Do not blanket-suppress `pg_restore`'s exit code** with `|| true`.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` § Epic 1 → Story 1.5] — the three ACs, verbatim.
- [Source: `_bmad-output/planning-artifacts/epics.md` § NFR-6] — durability; the FR-4 gate is Phase 2.
- [Source: `_bmad-output/planning-artifacts/epics.md` § AR-5] — `make backup` + named volume + verified
  restore, "from the first data-model story".
- [Source: `.../architecture/architecture-youtube-organizer-2026-07-24/ARCHITECTURE-SPINE.md` § AD-20]
  — the rule, and the `docker compose down -v` failure mode it names explicitly.
- [Source: `.../ARCHITECTURE-SPINE.md` § Consistency Conventions] — ISO 8601 UTC; Conventional Commits;
  no AI/bot attribution.
- [Source: `_bmad-output/planning-artifacts/prds/prd-youtube-organizer-2026-07-20/prd.md` §8] — *"the
  app is the sole home post-import"*.
- [Source: `_bmad-output/project-context.md` § Critical Don't-Miss Rules] — secrets from env, never
  committed; NFR-9's raised stakes under write scope.
- [Source: `_bmad-output/implementation-artifacts/deferred-work.md`] — the stale
  `backend/docker-compose.yml` item (twice) that Task 6 closes.
- [Source: `_bmad-output/implementation-artifacts/1-4-cookie-authentication-class-and-middleware-retirement.md`]
  — DoD/guard-proving conventions; the rebuild-after-requirements trap; the run-compose-from-root trap.
- [Source: `Docs/CI-AND-GITHUB-GATES.md`] — branch flow, required checks, PR discipline.
- [Source: `backend/.coveragerc`] — `fail_under = 70`, `*/tests/*` omitted.

### Open questions for Alexis (non-blocking — implement as specified)

1. **Retention.** Dumps accumulate in `backups/` forever and are unencrypted on disk. Deliberately out
   of scope; recorded in `deferred-work.md`. Worth a keep-last-N when the library is real (Epic 4+)?
2. **`docker-compose` vs `docker compose`.** Both work here; the repo standardises on the former. A
   repo-wide migration is its own small change — flagging it, not doing it.
3. **Off-machine copies.** AD-20 requires a backup and a verified restore; it says nothing about the
   dump living on the same disk as the volume it protects. A disk failure still ends the library. Out
   of scope for a localhost-only Phase 1 (NFR-11/AD-17), but the honest statement of residual risk.

## Dev Agent Record

### Agent Model Used

claude-opus-5 (BMad `dev-story` workflow)

### Debug Log References

**Volume name, before and after the `docker-compose.yml` edit (AC1).** Identical, which is the
entire point — pinning the name is a no-op on disk.

```
# BEFORE
$ docker volume ls | grep postgres
local     accountr_postgres_data
local     rails_7_with_docker_postgres
local     youtube-organizer_postgres_data

# AFTER
$ docker-compose config --volumes
postgres_data
frontend_node_modules
$ docker volume ls | grep postgres
local     accountr_postgres_data
local     rails_7_with_docker_postgres
local     youtube-organizer_postgres_data
$ docker inspect -f '{{range .Mounts}}{{.Name}}{{end}}' youtube-organizer-db-1
youtube-organizer_postgres_data
```

Data survived the edit — the pre-existing row was still there after `docker-compose up -d db`:
`auth_user 1 / usersocialtoken 1 / migrations 19` (counts before seeding).

**Guards proven to bite (all seven, plus the mount half of guard 1).** Each was broken, the suite
run, the failure read, then reverted. Every message names the file.

```
# 1  volume name: name: youtube-organizer_... -> youtube_organizer_...
FAIL: NamedVolumeTests.test_postgres_volume_is_explicitly_named
AssertionError: 'youtube_organizer_postgres_data' != 'youtube-organizer_postgres_data'

# 1b db service stops mounting the compose-local key
FAIL: NamedVolumeTests.test_postgres_volume_is_explicitly_named
AssertionError: False is not true : The db service in docker-compose.yml must still mount the
compose-local key 'postgres_data' (found ['./pgdata:/var/lib/postgresql/data/']). ...

# 2  chmod 644 bin/backup-db.sh
FAIL: BackupScriptTests.test_scripts_exist_and_are_executable (script='bin/backup-db.sh')
AssertionError: False is not true : bin/backup-db.sh is not executable. Fix with
'chmod +x bin/backup-db.sh' and commit the mode — a 644 script works for whoever wrote it and
fails for everyone who clones.

# 3  'restore' dropped from .PHONY
FAIL: MakefileTargetTests.test_backup_and_restore_targets_are_declared (target='restore')
AssertionError: 'restore' not found in ['backend-migrate', 'backend-test', 'backend-coverage',
'backup', 'frontend-install', 'frontend-dev', 'up'] : 'restore' is missing from the Makefile's
.PHONY list, so a file of that name in the repo root would silently disable it.

# 4  -T dropped from the pg_dump exec  <-- the corruption no other check would notice
FAIL: BackupScriptTests.test_pg_dump_runs_through_exec_dash_t
(line='if ! docker-compose exec db pg_dump -U "$PG_USER" -d "$PG_DB" \')
AssertionError: Regex didn't match: 'docker-compose\s+exec\s+(-\w+\s+)*-T\b' not found in
'if ! docker-compose exec db pg_dump ...' : bin/backup-db.sh must pass -T to 'docker-compose
exec' when piping pg_dump. Without it Compose allocates a pseudo-TTY, which line-end translates
the binary custom-format stream: the file appears, has a plausible size, the script exits 0, and
the corruption is found on the one day it matters.

# 5  a doc re-introduces the volume-destroying command
FAIL: NoRoutineDestructionTests.test_no_operational_file_destroys_the_volume
(file='backend/README.md', literal='down -v')
AssertionError: [136] is not false : backend/README.md line(s) [136] contain 'down -v', which
destroys youtube-organizer_postgres_data — the app's sole home for the library after import.
AD-20 forbids any routine command, script or documented workflow that does this. To clear data
instead, use 'manage.py flush --noinput'; see Docs/development-guide.md § Backups & Restore.

# 6  backups/ un-ignored
FAIL: NoRoutineDestructionTests.test_backups_directory_is_gitignored
AssertionError: 'backups/' not found in ['.DS_Store', ..., 'backend/certs/', '.agents/'] :
'.gitignore' must ignore 'backups/'. A dump contains organizer_usersocialtoken — live Google
OAuth refresh tokens — plus every user row. It is a credential file; committing one leaks it
permanently.

# 7  stale backend/docker-compose.yml recreated
FAIL: NoRoutineDestructionTests.test_stale_backend_compose_file_is_gone
AssertionError: True is not false : backend/docker-compose.yml is back. It declares a SECOND
postgres_data volume against postgres:16 while the real stack runs postgres:15, ...

# after reverting all seven
OK  (Ran 8 tests)
```

Guard 5 was rewritten mid-pass: `assertNotIn` on the file text printed the whole README into the
failure, burying the message under the document it was complaining about. It now reports line
numbers (`backend/README.md line(s) [136]`), which is the output shown above.

**AC1 behavioural probes.**

```
$ docker-compose exec -T db pg_restore --list < backups/youtube_organizer-20260819T002237Z.dump
exit=0 — 99 TOC lines; header reports Format: CUSTOM, TOC Entries: 88

$ file backups/youtube_organizer-*.dump
PostgreSQL custom database dump - v1.14-0

# stack down
$ docker-compose stop db && make backup
the db service is not accepting connections; run 'make up' first
make: *** [backup] Error 1   (exit 2)
files before=5 after=5; no .partial left behind
```

**AC3 refusal paths.**

```
$ make restore < /dev/null
no dump given: FILE is required
usage: make restore FILE=backups/<dump>   (or: bash bin/restore-db.sh <dump>)
make: *** [restore] Error 1   (exit 2)

$ make restore FILE=backups/youtube_organizer-20260819T002237Z.dump < /dev/null
About to restore ... into database 'youtube_organizer' on the LIVE container
  That database currently holds: auth_user 4 / organizer_usersocialtoken 2 / django_migrations 19
refusing to restore unattended: re-run interactively, or set CONFIRM=yes
make: *** [restore] Error 1   (exit 2)
# live DB afterwards: 4 / 2 / 19 — unchanged.

$ git ls-files -s bin/ | grep -E "backup-db|restore-db"
100755 ... bin/backup-db.sh
100755 ... bin/restore-db.sh

$ git status --porcelain | grep -i backups   ->  no output (backups/ is ignored)
```

### Completion Notes List

**The restore drill (AC2) — run 2026-08-18, exactly as written in `Docs/development-guide.md`
§ Backups & Restore.** No step needed correcting, so the document went in unchanged after the run.

*Seed, first.* The dev database held one real user and one token, which proves nothing much, so
three recognisable users were created via `User.objects.create_user`-equivalent `get_or_create`
(`drill-alice`, `drill-bob`, `drill-carol`) plus one `UserSocialToken` on `drill-alice` with the
fake strings `DRILL-FAKE-ACCESS-1-5` / `DRILL-FAKE-REFRESH-1-5`. That took the source to 4 users
and 2 tokens.

| Step | Source (live `db`, 5432) | Drill (`yo-restore-drill-db`, 55432) |
| --- | --- | --- |
| `auth_user` | 4 | **4** |
| `organizer_usersocialtoken` | 2 | **2** |
| `django_migrations` | 19 | **19** |

- Step 3, before restoring anything:
  `docker inspect -f '{{range .Mounts}}{{.Name}}{{end}}' yo-restore-drill-db` → `yo-restore-drill`.
  The real volume was never attached to the drill.
- Step 4: `pg_restore --no-owner --no-privileges` exited **0**, no warnings.
- Step 5 spot-check, not just counts: `select username from auth_user order by username` returned
  `ar.ibarrasalas@gmail.com, drill-alice, drill-bob, drill-carol` — the seeded rows came back by
  name, so this is recovery rather than a coincidence of totals.
- Step 6: `POSTGRES_HOST=localhost POSTGRES_PORT=55432 .venv/bin/python manage.py migrate --check`
  → exit **0**. The restored schema is exactly what the current migration state expects.
- Step 7: `docker rm -f yo-restore-drill-db && docker volume rm yo-restore-drill`, then
  `docker volume ls | grep postgres` → `youtube-organizer_postgres_data` still present, and the
  live DB still answered `auth_user 4`.

**Beyond the drill: the restore script's happy path was also exercised.** The drill uses a bare
`docker exec pg_restore`, so it verifies the *dump*, not `bin/restore-db.sh`. `CONFIRM=yes make
restore FILE=<a dump matching current state>` was run against the live database: exit 0, counts
still 4 / 2 / 19 afterwards, and `manage.py migrate --check` exit 0. Restoring a dump of the
current state is a safe way to prove the code path, and it was taken only after five valid dumps
existed on disk.

**Test arithmetic.** Baseline **93** (not the 87 the story predicted — measured directly by moving
`test_durability.py` aside and re-running). 93 + 8 = **101**. Host: `Ran 101 tests ... OK`, no
skips. Container: `Ran 101 tests ... OK (skipped=8)` — see deviation 1.

**Gates.** `manage.py check` → no issues. `makemigrations --check --dry-run` → `No changes
detected` (this story creates no migration). `make backend-coverage` → exit 0, **90.12%** against
`fail_under = 70`. It moved by +0.12 from 1.4's 90%: the new file is a test file and `*/tests/*` is
omitted from measurement, so the effect is indirect, exactly as the story predicted it would be.

---

**Deviations from the story as written — disclosed, not smoothed over.**

1. **`REPO_ROOT` is a search, not `parents[3]`, and the guards skip where the root is absent.**
   The story specifies `pathlib.Path(__file__).resolve().parents[3]` plus a hard assertion that the
   root exists. Inside the backend container that is unsatisfiable: `docker-compose.yml`
   bind-mounts only `./backend` at `/app`, so `parents[3]` resolves to `/`, and the module failed
   at import with `FileNotFoundError: '/.githooks'`. That directly contradicts the story's own DoD
   line requiring `docker-compose exec backend python manage.py test` to be green.
   `_find_repo_root()` now walks up for the first ancestor holding **both** `docker-compose.yml`
   and `Makefile`; when none exists the classes are `skipIf`-ed with a message naming the cause and
   the command that does run them. The alternative — bind-mounting the repo root into the `backend`
   service — was rejected because the story's scope table restricts `docker-compose.yml` to the
   top-level `volumes:` block. **This does not weaken the guard where it matters:** CI's `test` job
   runs `actions/checkout` on the whole tree, so all eight execute there, and the host pre-push
   layer runs them too (verified: 101 tests, zero skips on the host).

2. **The story's stated 87-test baseline is wrong; it is 93.** Corrected in the DoD line rather
   than rounded past, per the 1.4 precedent on false predictions.

3. **`backend/README.md` cannot contain the literal string it is being told to warn about.**
   Task 5 asks for a warning against destroying the volume, and guard 5 bans the literal `down -v`
   in exactly that file. The warning is therefore phrased as "never bring the stack down with the
   flag that also removes volumes". Same instruction, no literal for the guard to trip over.

4. **`bin/backup-db.sh` gained atomic name reservation, which the story does not specify.** The
   DoD's "two `make backup` runs, two files, no overwrite, no error" **failed** when the collision
   was actually forced: two runs backgrounded in one shell computed the same second-resolution
   timestamp, wrote two `pg_dump` streams into one `.partial`, and one run died with
   `mv: ... .partial: No such file or directory`. A `[ -e "$TARGET" ]` guard did not fix it — both
   runs pass that test before either renames. The script now makes the `.partial` PID-unique and
   reserves the final name with `(set -C; : > "$TARGET")`, appending `-1`, `-2`, … on collision.
   Re-tested: two concurrent runs → `...T003312Z.dump` and `...T003312Z-1.dump`, both verified as
   valid archives by `pg_restore --list`, both runs exit 0. Without this the story would have
   shipped a backup command that silently discards a backup.

5. **Honest limitation, carried to `deferred-work.md`.** The restore path is verified against a
   one-model schema — `Video`, `Tag` and `VideoTombstone` do not exist until Epic 4. The mechanism
   is proven; a restore of a real library with foreign keys between those tables is not. Epic 4
   should re-run this drill against real data.

**`deferred-work.md` maintenance.** Two items closed in the established style (the stale
`backend/docker-compose.yml` entry, and its duplicate under *code review of spec-ci-gate-stack.md*)
— the first with a note that its "no story owns its deletion" prediction was wrong in the way that
mattered. Three raised: unencrypted/unpruned/same-disk dumps, the one-model verification limit
above, and `README.md:94`'s reference to a `make backend-createsuperuser` target the Makefile does
not define (found while editing the adjacent list; deliberately not fixed here).

### File List

| Path | Change |
| --- | --- |
| `docker-compose.yml` | UPDATE — top-level `volumes:` block only; `postgres_data.name` pinned |
| `bin/backup-db.sh` | NEW (100755) |
| `bin/restore-db.sh` | NEW (100755) |
| `Makefile` | UPDATE — `backup` + `restore` targets and `.PHONY` |
| `.gitignore` | UPDATE — `backups/` with the credential-file rationale |
| `backend/README.md` | UPDATE — volume-destroying troubleshooting step removed; volume note fixed |
| `Docs/development-guide.md` | UPDATE — new `## Backups & Restore` section |
| `Docs/deployment-guide.md` | UPDATE — one line: the volume's explicit name |
| `README.md` | UPDATE — `make backup` / `make restore` in *Useful Commands* |
| `backend/docker-compose.yml` | **DELETE** — stale `postgres:16` duplicate |
| `backend/organizer/tests/test_durability.py` | NEW — nine guards + a repo-root sanity test (10 tests) |
| `backend/requirements.txt` | UPDATE — direct `PyYAML==6.0.3` pin |
| `_bmad-output/implementation-artifacts/deferred-work.md` | UPDATE — 2 closed, 3 raised |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | UPDATE — story status |
| `_bmad-output/implementation-artifacts/1-5-...md` | UPDATE — this record |

## Change Log

| Date | Change |
| --- | --- |
| 2026-08-18 | Story implemented — volume pinned to `youtube-organizer_postgres_data` (no-op on disk, verified before/after); `bin/backup-db.sh` + `bin/restore-db.sh` (100755) behind `make backup` / `make restore`; `backups/` gitignored; the restore drill documented in `Docs/development-guide.md` and executed against a throwaway volume with matching counts (4/2/19) and `migrate --check` green; stale `backend/docker-compose.yml` deleted; seven guards in `test_durability.py`, all proven to bite. Suite 93 → 101, `OK`; coverage 90.12%. |
| 2026-08-18 | Story created — `make backup` + `bin/backup-db.sh` (custom-format, timestamped, verified before success), the Postgres volume pinned to its existing explicit name, a guarded `make restore`, the restore drill documented and run against a throwaway volume, `backend/README.md`'s `down -v` instruction removed, the stale `backend/docker-compose.yml` deleted, and seven standing guards in `test_durability.py`. AD-20, NFR-6, NFR-9. |
