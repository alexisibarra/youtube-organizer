"""AD-20 / NFR-6 durability guards: the library must survive the developer's laptop.

Once Epic 7 starts deleting videos out of YouTube after importing them, the only copy
of the curated library is a Docker volume on one machine. These are structural
assertions over repo text — the mechanism they defend (a named volume, a verified
backup, a restore path nothing routine can trip over) lives in files, not in Python,
so the tests read those files rather than importing anything.

`SimpleTestCase`: no database is involved, and deliberately so — these must run in CI
against a checkout, where there is no volume and no library to back up.
"""

import os
import pathlib
import re

import yaml
from django.test import SimpleTestCase
from unittest import skipIf

def _is_repo_root(candidate):
    return (candidate / "docker-compose.yml").is_file() and (candidate / "Makefile").is_file()


def _find_repo_root():
    """The checkout root: the directory holding both docker-compose.yml and Makefile.

    Two ways to find it, in order.

    `REPO_ROOT` from the environment comes first, and exists for one environment: the
    backend container mounts ./backend at /app, so the checkout root is *not* an
    ancestor of this file in there — no amount of walking up can reach it. The compose
    file mounts the checkout read-only at /repo and sets REPO_ROOT=/repo, which is what
    lets `make backend-test` run these guards for real instead of skipping them.

    Otherwise walk up from this file. Nominally that is parents[3] (tests -> organizer
    -> backend -> root); it is a search rather than an index so that an unusual checkout
    layout degrades to a skip rather than to a wrong answer. On the host and in CI
    (actions/checkout gives the whole tree) the walk finds the real root.
    """
    declared = os.environ.get("REPO_ROOT")
    if declared:
        candidate = pathlib.Path(declared)
        # Validated, not trusted: a REPO_ROOT pointing somewhere without these files
        # would make every guard below read the wrong tree and pass for the wrong
        # reason. Falling through to the walk keeps a stale value from being load-bearing.
        if _is_repo_root(candidate):
            return candidate
    for candidate in pathlib.Path(__file__).resolve().parents:
        if _is_repo_root(candidate):
            return candidate
    return None


REPO_ROOT = _find_repo_root()

# Skip, never silently pass. An absent root is a known environment limitation; a root
# that exists but fails a guard is the bug these tests are here to catch.
SKIP_REASON = (
    None
    if REPO_ROOT is not None
    else "no repo root above this file (the backend container mounts only ./backend "
    "at /app). Run these on the host or in CI: `cd backend && "
    "POSTGRES_HOST=localhost .venv/bin/python manage.py test organizer.tests.test_durability`."
)

VOLUME_NAME = "youtube-organizer_postgres_data"


def _operational_files():
    """Files that must never instruct anyone to destroy the library.

    Named explicitly rather than walked: _bmad-output/ is historical record that must
    keep quoting the commands this story removed, and frontend/node_modules/ is enormous.
    """
    if REPO_ROOT is None:
        return []
    names = ["Makefile", "README.md", "backend/README.md", "docker-compose.yml"]
    # bin/ carries the most weight here: a shell script is the likeliest place for a
    # volume-destroying command to actually appear, and the original list scanned
    # README.md but not the scripts. Docs/ recurses, because a subdirectory is not a
    # hiding place. Both workflow spellings, because .yaml is as valid as .yml.
    for pattern in (
        "Docs/**/*.md",
        ".githooks/*",
        ".github/workflows/*.yml",
        ".github/workflows/*.yaml",
        "bin/*",
        "scripts/*",
    ):
        names += sorted(
            str(path.relative_to(REPO_ROOT))
            for path in REPO_ROOT.glob(pattern)
            if path.is_file()
        )
    return sorted(set(names))


OPERATIONAL_FILES = _operational_files()

# Precise, because the documented restore drill legitimately runs
# `docker volume rm yo-restore-drill`. A blunt ban on `volume rm` would forbid the
# very path this story adds.
#
# The prune forms matter as much as the explicit ones: `docker volume prune` removes
# every volume not currently attached to a container, so a stack that is merely
# stopped loses the library to a command whose name sounds like tidying.
DESTRUCTIVE_LITERALS = (
    "down -v",
    "down --volumes",
    f"volume rm {VOLUME_NAME}",
    "volume prune",
    "system prune --volumes",
    "system prune -a --volumes",
)

# Both CLI spellings. `docker-compose` (v1, hyphen) is what this repo standardises on,
# but `docker compose` (v2, space) is the same command and is what a newer machine
# reaches for by default. A guard that only knows one spelling is silently disabled the
# day someone modernises a file, which is the worst possible moment for it to go quiet.
COMPOSE_EXEC_SPELLINGS = ("docker-compose exec", "docker compose exec")


def _mentions_compose_exec(line):
    return any(spelling in line for spelling in COMPOSE_EXEC_SPELLINGS)


def _logical_lines(text):
    """Physical lines joined across backslash continuations.

    Shell invocations in these scripts wrap:

        docker-compose exec -T db pg_restore -U "$PG_USER" -d "$PG_DB" \\
            --clean --if-exists --single-transaction < "$FILE"

    Checking physical lines means a flag on the continuation is invisible to a guard
    matching the line that names the command — which is how the --single-transaction
    guard first shipped green while the flag was there, and stayed green when it was
    removed. Joining first makes one command one string, however it is wrapped.
    """
    joined, buffer = [], ""
    for line in text.splitlines():
        stripped = line.rstrip()
        if stripped.endswith("\\"):
            buffer += stripped[:-1] + " "
            continue
        joined.append(buffer + line)
        buffer = ""
    if buffer:
        joined.append(buffer)
    return joined


# Deliberately NOT decorated with @skipIf. SKIP_REASON is non-None precisely when
# REPO_ROOT is None, so skipping this class would make its assertion unreachable —
# it could only ever run in the case where it is guaranteed to pass, which is the
# silent pass the docstring says it exists to prevent. The other classes below stay
# skipped (a container with no repo root cannot check repo files); this one fails,
# so `make backend-test` reports one honest failure instead of eight quiet skips.
class RepoRootResolutionTests(SimpleTestCase):
    """Fail as 'the guard cannot find the repo', never as a silent pass."""

    def test_repo_root_resolves(self):
        self.assertIsNotNone(REPO_ROOT, SKIP_REASON)
        self.assertTrue(
            (REPO_ROOT / "docker-compose.yml").is_file(),
            f"REPO_ROOT resolved to {REPO_ROOT}, which has no docker-compose.yml. "
            "_find_repo_root() walks up for a directory holding both docker-compose.yml "
            "and Makefile; if either moved, fix that search.",
        )


@skipIf(SKIP_REASON is not None, SKIP_REASON or '')
class NamedVolumeTests(SimpleTestCase):
    """AC1: the volume's real Docker name is pinned, not derived from a directory name."""

    def test_postgres_volume_is_explicitly_named(self):
        compose = yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text())
        volumes = compose.get("volumes") or {}
        self.assertIn(
            "postgres_data",
            volumes,
            "docker-compose.yml declares no top-level postgres_data volume.",
        )
        declared = (volumes.get("postgres_data") or {}).get("name")
        self.assertEqual(
            declared,
            VOLUME_NAME,
            "docker-compose.yml must pin volumes.postgres_data.name to exactly "
            f"'{VOLUME_NAME}' (AD-20). Found {declared!r}. That literal is the name "
            "Compose already generates from the checkout directory — the hyphen is "
            "load-bearing. Changing it points the stack at a DIFFERENT volume, "
            "Postgres initdb's it empty, and every existing library is orphaned.",
        )

        # Same guard, same test: pinning the external name must not change how the
        # service refers to the volume. Split into two tests, one half could go green
        # while the stack quietly stopped mounting it.
        mounts = (compose.get("services") or {}).get("db", {}).get("volumes") or []
        self.assertTrue(
            any(str(m).startswith("postgres_data:") for m in mounts),
            "The db service in docker-compose.yml must still mount the compose-local "
            f"key 'postgres_data' (found {mounts!r}). Pinning the external name does "
            "not change how the service refers to it.",
        )


@skipIf(SKIP_REASON is not None, SKIP_REASON or '')
class BackupScriptTests(SimpleTestCase):
    """AC1/AC3: the two scripts exist, are runnable by everyone, and keep the -T flag."""

    def test_scripts_exist_and_are_executable(self):
        for name in ("bin/backup-db.sh", "bin/restore-db.sh"):
            with self.subTest(script=name):
                path = REPO_ROOT / name
                self.assertTrue(path.is_file(), f"{name} is missing (Story 1.5, AD-20).")
                self.assertTrue(
                    os.access(path, os.X_OK),
                    f"{name} is not executable. Fix with 'chmod +x {name}' and commit "
                    "the mode — a 644 script works for whoever wrote it and fails for "
                    "everyone who clones.",
                )

    def test_pg_dump_runs_through_exec_dash_t(self):
        text = (REPO_ROOT / "bin/backup-db.sh").read_text()
        exec_lines = [
            line for line in _logical_lines(text) if _mentions_compose_exec(line) and "pg_dump" in line
        ]
        self.assertTrue(
            exec_lines,
            "bin/backup-db.sh no longer runs pg_dump through 'docker-compose exec'. "
            "The dump must go through the container: a host client of a different "
            "Postgres major cannot talk to the server.",
        )
        for line in exec_lines:
            with self.subTest(line=line.strip()):
                self.assertRegex(
                    line,
                    r"docker[- ]compose\s+exec\s+(-\w+\s+)*-T\b",
                    "bin/backup-db.sh must pass -T to compose 'exec' when piping "
                    "pg_dump. Without it Compose allocates a pseudo-TTY, which line-end "
                    "translates the binary custom-format stream: the file appears, has a "
                    "plausible size, the script exits 0, and the corruption is found on "
                    "the one day it matters.",
                )

    def test_every_compose_exec_in_both_scripts_passes_dash_t(self):
        """The -T rule is per-exec, not per-script.

        The narrower guard above only ever inspected the pg_dump line in backup-db.sh,
        which left the pg_restore --list verification, both pg_isready probes, the
        printenv credential check, and every exec in restore-db.sh unguarded. Dropping
        -T on the restore path corrupts the archive on its way *in* — the same failure
        mode, against the database rather than the file.
        """
        for name in ("bin/backup-db.sh", "bin/restore-db.sh"):
            text = (REPO_ROOT / name).read_text()
            # Comments and printed help text are not invocations. A line that *prints*
            # `docker-compose exec backend python manage.py migrate --check` for a human
            # to run interactively is correct without -T, and demanding it there would
            # teach the reader a flag they do not want.
            #
            # The exemption is deliberately shape-based and therefore evadable — a
            # heredoc, or an exec buried mid-line after `&&`, is not classified here.
            # It errs toward checking too much (a wrongly-flagged line is a visible
            # test failure someone fixes) rather than too little (a missed -T is
            # silent corruption), which is why only whole-line comments and whole-line
            # prints are exempt.
            exec_lines = [
                line
                for line in _logical_lines(text)
                if _mentions_compose_exec(line)
                and not line.lstrip().startswith("#")
                and not line.lstrip().startswith(("echo ", "printf "))
            ]
            with self.subTest(script=name):
                self.assertTrue(
                    exec_lines,
                    f"{name} no longer runs anything through 'docker-compose exec'. "
                    "Both scripts must reach Postgres through the container: a host "
                    "client of a different major cannot talk to the server.",
                )
            for line in exec_lines:
                with self.subTest(script=name, line=line.strip()):
                    self.assertRegex(
                        line,
                        r"docker[- ]compose\s+exec\s+(-\w+\s+)*-T\b",
                        f"{name} must pass -T to every compose 'exec'. Without it "
                        "Compose allocates a pseudo-TTY, which line-end translates any "
                        "binary stream crossing that boundary — silently, and only "
                        "detectably on the day the archive is needed.",
                    )

    def test_restore_refuses_to_run_unattended(self):
        """AC3: the destructive script must keep its unattended refusal.

        The -T guard has a twin that was missing: nothing asserted that restore-db.sh
        still checks for a TTY and still demands CONFIRM. Both are what keep a
        library-destroying command out of a hook or a CI step, so both are guarded.
        """
        text = (REPO_ROOT / "bin/restore-db.sh").read_text()
        self.assertIn(
            "CONFIRM",
            text,
            "bin/restore-db.sh no longer consults CONFIRM. Without it the script can "
            "be driven unattended, which AD-20 forbids for a path that destroys the "
            "library.",
        )
        self.assertIn(
            "-t 0",
            text,
            "bin/restore-db.sh no longer tests whether stdin is a TTY ('[ ! -t 0 ]'). "
            "That test is what makes the script refuse inside hooks, CI steps and "
            "anything else with no human at the keyboard.",
        )
        # Checked on the pg_restore invocation itself, not anywhere in the file. A
        # plain text search passes on the comment that explains the flag and on the
        # failure message that mentions it — this guard was written that way first,
        # and deleting the flag from the actual command left it green.
        restore_invocations = [
            line
            for line in _logical_lines(text)
            if "pg_restore" in line
            and _mentions_compose_exec(line)
            and not line.lstrip().startswith("#")
            and not line.lstrip().startswith(("echo ", "printf "))
        ]
        self.assertTrue(
            restore_invocations,
            "bin/restore-db.sh no longer runs pg_restore through compose 'exec'.",
        )
        # The archive-parsing probe (`pg_restore --list`) is read-only and correctly
        # has no --single-transaction; the one that writes is the one that needs it.
        writing = [line for line in restore_invocations if "--list" not in line]
        self.assertTrue(
            writing,
            "bin/restore-db.sh has no writing pg_restore invocation (only --list).",
        )
        for line in writing:
            with self.subTest(line=line.strip()):
                self.assertIn(
                    "--single-transaction",
                    line,
                    "bin/restore-db.sh must run the writing pg_restore with "
                    "--single-transaction. Without it a mismatched major, a truncated "
                    "archive or a dropped connection leaves the live library "
                    "half-dropped, with --clean having already run.",
                )


@skipIf(SKIP_REASON is not None, SKIP_REASON or '')
class MakefileTargetTests(SimpleTestCase):
    """AC1/AC3: make backup and make restore are real, declared targets."""

    def test_backup_and_restore_targets_are_declared(self):
        text = (REPO_ROOT / "Makefile").read_text()
        phony = " ".join(re.findall(r"^\.PHONY:(.*)$", text, re.MULTILINE)).split()
        for target in ("backup", "restore"):
            with self.subTest(target=target):
                self.assertTrue(
                    re.search(rf"^{target}:", text, re.MULTILINE),
                    f"The Makefile declares no '{target}' target (Story 1.5, AD-20).",
                )
                self.assertIn(
                    target,
                    phony,
                    f"'{target}' is missing from the Makefile's .PHONY list, so a file "
                    f"of that name in the repo root would silently disable it.",
                )


@skipIf(SKIP_REASON is not None, SKIP_REASON or '')
class NoRoutineDestructionTests(SimpleTestCase):
    """AC3: no tracked operational file tells anyone to destroy the library."""

    def test_no_operational_file_destroys_the_volume(self):
        for name in OPERATIONAL_FILES:
            path = REPO_ROOT / name
            if not path.is_file():
                continue
            # errors="replace": bin/ and scripts/ are globbed now, and a binary
            # dropped in either would otherwise fail the durability suite with a
            # UnicodeDecodeError that says nothing about durability.
            lines = path.read_text(errors="replace").splitlines()
            for literal in DESTRUCTIVE_LITERALS:
                hits = [n for n, line in enumerate(lines, 1) if literal in line]
                with self.subTest(file=name, literal=literal):
                    # assertFalse on a bool, not assertNotIn on the file text: the
                    # latter prints the whole document, which buries the message under
                    # the file it is complaining about.
                    self.assertFalse(
                        hits,
                        f"{name} line(s) {hits} contain '{literal}', which destroys "
                        f"{VOLUME_NAME} — the app's sole home for the library after "
                        "import. AD-20 forbids any routine command, script or "
                        "documented workflow that does this. To clear data instead, "
                        "use 'manage.py flush --noinput'; see Docs/development-guide.md "
                        "§ Backups & Restore.",
                    )

    def test_backups_directory_is_gitignored(self):
        patterns = [
            line.strip()
            for line in (REPO_ROOT / ".gitignore").read_text().splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        self.assertIn(
            "backups/",
            patterns,
            "'.gitignore' must ignore 'backups/'. A dump contains "
            "organizer_usersocialtoken — live Google OAuth refresh tokens — plus every "
            "user row. It is a credential file; committing one leaks it permanently.",
        )

    def test_stale_backend_compose_file_is_gone(self):
        path = REPO_ROOT / "backend/docker-compose.yml"
        self.assertFalse(
            path.is_file(),
            "backend/docker-compose.yml is back. It declares a SECOND postgres_data "
            "volume against postgres:16 while the real stack runs postgres:15, so "
            "running compose from backend/ gets a different volume, a different "
            "Postgres major, and a backup taken against the wrong database (AD-20). "
            "There is exactly one compose file, at the repo root.",
        )
