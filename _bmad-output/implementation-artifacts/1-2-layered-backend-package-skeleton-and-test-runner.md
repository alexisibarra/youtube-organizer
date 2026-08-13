---
baseline_commit: 6e7c81a0be2be2164ab940634e1f13dd2dff15f5
---

# Story 1.2: Layered backend package skeleton and test runner

Status: review

Epic: 1 — Backend platform · Story key: `1-2-layered-backend-package-skeleton-and-test-runner`
Branch: `feat/story-1-2-backend-package-skeleton` → PR → `develop` (squash). Never commit to `main`/`develop`.

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want the `organizer/` package split into the layered structure with a working test runner,
so that every later story lands its code in the correct layer with dependency direction enforced (AD-1).

## Acceptance Criteria

**AC1 — The layered skeleton exists and is importable**
**Given** the monolithic `organizer/` app
**When** I introduce the skeleton
**Then** `api/`, `auth/`, `services/`, `sync/`, `youtube/`, `models/`, `management/commands/`, and
`tests/` packages exist, each importable, with `services/` importing neither DRF nor `youtube/`.

**AC2 — The test harness runs**
**Given** the new structure
**When** I run `manage.py test`
**Then** the suite discovers and runs (green), establishing the harness the coverage gate (NFR-13)
will later measure.

### Definition of Done (verifiable, no self-reporting)

Every command runs **inside the container** unless stated: `docker compose exec backend <cmd>`.

- [x] `python -c "import organizer.api, organizer.auth, organizer.services, organizer.sync, organizer.youtube, organizer.models, organizer.management.commands, organizer.tests; print('ok')"` → `ok`.
- [x] `python -c "import organizer.models as m; print(m.__file__)"` → path ends in `organizer/models/__init__.py` (package, not module).
- [x] `backend/organizer/models.py` and `backend/organizer/tests.py` no longer exist (`git status` shows them deleted, not left alongside their packages — a stale `models.py` next to `models/` is an import ambiguity, and Python resolves the **package**, silently orphaning the module).
- [x] `python manage.py check` → `System check identified no issues (0 silenced).`
- [x] `python manage.py makemigrations --check --dry-run` → `No changes detected`, exit 0. **No new migration file is created by this story.**
- [x] `python manage.py test` → runs ≥1 real test, `OK`, exit 0. The output must show a non-zero test count — "Ran 0 tests" is a failure of AC2, not a pass.
- [x] `python manage.py test organizer.tests.test_layering` → passes on its own (proves the layering guard is discoverable and self-contained).
- [x] Layering guard is *proven to bite*: temporarily add `import rest_framework` to `organizer/services/__init__.py`, re-run `manage.py test` → **fails**; revert. Record the failure output in Debug Log References. A guard never seen to fail is not a guard.
- [x] `coverage run manage.py test && coverage report` produces a report over `organizer/` with a non-zero percentage; the measured baseline number is recorded in Completion Notes.
- [x] `curl -sk -o /dev/null -w '%{http_code}\n' https://localhost:8000/api/auth/me/` → **401** (not 404, not 500) — proves the `views.py` → `api/views.py` move kept the route wired and the auth stack intact.
- [x] `curl -sk https://localhost:8000/api/auth/google/ | head -c 120` → 200 with an `auth_url`.
- [x] `curl -sk -o /dev/null -w '%{http_code}\n' https://localhost:8000/api/youtube/playlists/` → **401** (route still registered).
- [x] `git diff` on `backend/youtube_organizer/settings.py` shows **no change to** the CORS / session / CSRF / `REST_FRAMEWORK` blocks (AD-14, NFR-9 invariants untouched by this story).
- [x] Host-side: `.githooks/pre-push` layer [6/6] runs the new suite green (`cd backend && POSTGRES_HOST=localhost .venv/bin/python manage.py test --noinput`).

## Tasks / Subtasks

- [x] **Task 1 — Create the six layer packages with contract docstrings (AC1)**
  - [x] Create `backend/organizer/{api,auth,services,sync,youtube}/__init__.py`.
  - [x] Each `__init__.py` contains **only** a module docstring stating that layer's *Owns* / *Must never*
        from the table in Dev Notes → "The layer contract". No code, no imports, no `__all__`.
        The docstring is the guardrail a later story reads before adding a file here.
  - [x] Create `backend/organizer/management/__init__.py` and
        `backend/organizer/management/commands/__init__.py` (both empty). **Do not create
        `sync_inbox.py`** — that is Story 7.2.
- [x] **Task 2 — Convert `models.py` into the `models/` package (AC1)**
  - [x] `git mv backend/organizer/models.py backend/organizer/models/user_social_token.py`
        (create the directory first; use `git mv` so history follows the file).
  - [x] Add `backend/organizer/models/__init__.py` that re-exports the model:
        `from .user_social_token import UserSocialToken` plus `__all__ = ["UserSocialToken"]`.
        Django imports `organizer.models` at app-load; a model class not reachable from that
        namespace is invisible to the ORM and to `makemigrations`.
  - [x] Keep `user_social_token.py` byte-identical apart from the move — **tabs stay tabs** in this
        file (see Dev Notes → indentation).
  - [x] Verify no migration is generated (`makemigrations --check --dry-run`). See Dev Notes →
        "Why the move generates no migration" before you panic at any output.
  - [x] `backend/organizer/google_auth_views.py:8` does `from .models import UserSocialToken` —
        the re-export keeps this working **unchanged**. Do not edit that file in this story.
- [x] **Task 3 — Move `views.py` into the `api/` layer (AC1)**
  - [x] `git mv backend/organizer/views.py backend/organizer/api/views.py`.
  - [x] Delete the two trailing cruft lines (`from django.shortcuts import render` + the
        `# Create your views here.` comment) — dead scaffolding, and an import below the class body.
  - [x] Update `backend/organizer/urls.py`: `from . import views` → `from .api import views`.
        Leave every `path(...)` line, name, and URL string **exactly** as-is.
  - [x] Leave `google_auth_views.py` at `organizer/google_auth_views.py`. It is rewritten by
        Stories 1.4 (SimpleJWT removal) and 6.1 (write scope); moving it here guarantees a
        conflicting diff for zero benefit. The spine's Capability map still names it at the app
        root — that is intentional, not an oversight.
- [x] **Task 4 — Convert `tests.py` into the `tests/` package (AC2)**
  - [x] Delete `backend/organizer/tests.py` (stock empty stub — no content to preserve).
  - [x] Create `backend/organizer/tests/__init__.py` (**empty file, but it MUST exist** — see
        Dev Notes → "The `__init__.py` that is not optional").
  - [x] Create `backend/organizer/tests/test_layering.py` per Task 5.
  - [x] Create `backend/organizer/tests/test_skeleton.py` asserting all eight packages import
        (the AC1 claim, expressed as a test rather than a one-off shell command).
- [x] **Task 5 — Write the layering guard test (AC1 — this is the story's real deliverable)**
  - [x] Implement `organizer/tests/test_layering.py` per the specification and starting shape in
        Dev Notes → "The layering guard". AST-based, no imports of the modules under inspection.
  - [x] It must cover, at minimum: `services/` imports neither DRF nor `organizer.youtube`
        (the literal AC1 clause), and `youtube/` imports neither `organizer.models` nor
        `organizer.services`.
  - [x] Prove it fails when violated (the DoD item above), then revert the deliberate violation.
- [x] **Task 6 — Coverage tooling (NFR-13 harness, threshold NOT enforced here)**
  - [x] Add `coverage==7.15.4` to `backend/requirements.txt`, keeping the file's exact-pin
        discipline from Story 1.1.
  - [x] Add `backend/.coveragerc` per Dev Notes → "Coverage configuration".
  - [x] Add a `backend-test` and a `backend-coverage` target to the root `Makefile`, matching the
        existing `docker-compose exec backend …` style of `backend-migrate`. Add both to `.PHONY`.
  - [x] **Do not set `fail_under = 70`.** Read Dev Notes → "The 70% gate: why it does not turn on
        in this story" before deciding otherwise. This is the one place this story deliberately
        diverges from a TODO comment that names it.
- [x] **Task 7 — Wire coverage into CI as a report, not a gate**
  - [x] In `.github/workflows/ci.yml`, change the `Run tests` step to `coverage run manage.py test`
        followed by a `coverage report` step. Keep `working-directory: backend` and the existing
        `POSTGRES_*` env block untouched.
  - [x] Update the `TODO(story 1-2)` comment at `ci.yml:11`: the harness lands here; retarget the
        remaining *threshold* TODO at story 1-4 with a one-line reason. Do **not** silently delete it.
  - [x] Do not add a paths filter, do not add `continue-on-error`, do not touch the job graph
        (`typecheck + lint → test → build`) — see Dev Notes → "CI rules you must not 'optimize'".
- [x] **Task 8 — Verify, commit, PR**
  - [x] Work through every DoD item; paste real output into Debug Log References.
  - [x] Conventional Commit, e.g. `refactor(backend): split organizer into layered packages and add the test harness`.
  - [x] Cite `AD-1` (layering), `AD-16` (test harness, no network) in the PR body.
  - [x] **No AI/bot attribution anywhere** — commit message, PR title, PR body, code comments.
  - [x] The PR template is Accountr's and partly unrunnable here: tick what applies, strike the rest
        (see Dev Notes → "The PR template trap").

## Dev Notes

### Scope boundary — what this story does NOT touch

| Tempting change | Belongs to |
| --- | --- |
| Writing PyJWT issue/verify code into `organizer/auth/` | **Story 1.3** |
| Removing SimpleJWT, deleting `JWTAuthCookieMiddleware`, the cookie auth class | **Story 1.4** |
| Moving/rewriting `google_auth_views.py` | **Stories 1.4 / 6.1** |
| `make backup`, naming the Postgres volume | **Story 1.5** |
| `sync_inbox.py` (the command file itself) | **Story 7.2** |
| Any `Video` / `Tag` / `SyncRun` / `PendingYouTubeOp` model | **Epics 4 / 7** |
| The YouTube gateway *implementation* or its fake | **Story 5.1** |
| `drf-spectacular` in `INSTALLED_APPS`, `EXCEPTION_HANDLER` | **Stories 3.1 / 3.2** |
| Any frontend file (incl. the `AI-1` login defect) | **Epic 2** |
| `SECRET_KEY` / `DEBUG` / `ALLOWED_HOSTS` to env, `check --deploy` | **Forbidden by AD-17** |

This story creates **empty, documented packages**. Resist filling them. An empty `services/` with a
correct docstring and a test that guards its import direction is the whole point; a `services/`
with a speculative `base.py` in it is scope creep that Epic 4 will have to undo.

### The layer contract (source: ARCHITECTURE-SPINE.md § Design Paradigm)

Put this table's row into each package's `__init__.py` docstring, in prose.

| Layer | Directory | Owns | Must never |
| --- | --- | --- | --- |
| API | `organizer/api/` | HTTP, serialization, query-param parsing, pagination | Contain domain logic or call YouTube |
| Auth | `organizer/auth/` | Token issue/verify over PyJWT, the DRF cookie authentication class | Contain domain logic |
| Services | `organizer/services/` | All domain operations; the only writer of app state | Import DRF, touch `request`, or call YouTube |
| Sync | `organizer/sync/` | Sync runs, the outbox drain, quota handling | Be reachable from a request thread |
| Gateway | `organizer/youtube/` | Every YouTube Data API call, quota-error translation | Import models or services |
| Models | `organizer/models/` | Schema, constraints, managers | Contain multi-entity business rules |

Dependency direction (arrows are *permission*; nothing points back up):

```
api/  ──▶ services/ ──▶ models/
sync/ ──▶ services/
sync/ ──▶ youtube/  ──▶ (YouTube Data API)
```

`sync/` is the only caller of the gateway's **write** methods (AD-6).

### Target tree after this story

```text
backend/organizer/
  __init__.py
  admin.py                     # untouched
  apps.py                      # untouched
  google_auth_views.py         # untouched — moves in 1.4/6.1
  urls.py                      # ONE line changes: the views import
  migrations/                  # untouched, no new migration
  api/
    __init__.py                # docstring only
    views.py                   # moved from organizer/views.py
  auth/__init__.py             # docstring only
  services/__init__.py         # docstring only
  sync/__init__.py             # docstring only
  youtube/__init__.py          # docstring only
  models/
    __init__.py                # re-exports UserSocialToken
    user_social_token.py       # moved from organizer/models.py
  management/
    __init__.py
    commands/__init__.py
  tests/
    __init__.py                # empty but REQUIRED
    test_skeleton.py
    test_layering.py
```

Deleted: `organizer/models.py`, `organizer/views.py`, `organizer/tests.py`.

### Files being modified (read before editing)

| File | Current state | This story changes | Must not break |
| --- | --- | --- | --- |
| [organizer/models.py](backend/organizer/models.py) | 15 lines, **tab-indented**. One model: `UserSocialToken` (OneToOne→`User`, `access_token`, `refresh_token`, `token_expiry`, `token_scope`, `token_type`, `created`, `updated`) | Moves to `models/user_social_token.py`; re-exported from `models/__init__.py` | `from .models import UserSocialToken` in `google_auth_views.py:8`; migration `0001_initial`; `token_scope` (Story 6.2 writes granted scope here per AD-14) |
| [organizer/views.py](backend/organizer/views.py) | 21 lines, **tab-indented**. `MeView(APIView)`, `IsAuthenticated`, returns username/email/`request.session['profile_picture']`. Two cruft lines at the bottom | Moves to `api/views.py`; cruft lines deleted | `/api/auth/me/` must still 401 unauthenticated and return the user with a valid cookie. The session-derived `profile_picture` read stays |
| [organizer/urls.py](backend/organizer/urls.py) | 11 lines, 4-space. Four routes: `auth/google/`, `oauth2callback/`, `youtube/playlists/`, `auth/me/` | **One line**: `from . import views` → `from .api import views` | Every URL string and `name=` unchanged — the frontend and the Google redirect URI are hardcoded against them |
| [organizer/tests.py](backend/organizer/tests.py) | Stock empty stub (`from django.test import TestCase` + comment) | Deleted, replaced by the `tests/` package | Nothing depends on it |
| [backend/requirements.txt](backend/requirements.txt) | 14 exact `==` pins (Story 1.1) | Add `coverage==7.15.4` | Every existing pin stays exactly as-is. Do **not** "tidy" or re-sort |
| [.github/workflows/ci.yml](.github/workflows/ci.yml) | `test` job (L83-140): postgres:15 service, `POSTGRES_HOST: localhost`, `makemigrations --check` → `migrate` → `python manage.py test` | `Run tests` becomes `coverage run manage.py test`; a `coverage report` step follows; the L11 TODO is retargeted | Job graph, `concurrency`, the absent paths filter, `timeout-minutes: 15`, the `POSTGRES_HOST: localhost` override |
| [Makefile](Makefile) | `backend-migrate`, `frontend-install`, `frontend-dev`, `up` | Add `backend-test`, `backend-coverage` to targets **and** `.PHONY` | Existing targets and the `docker-compose exec backend` idiom |

Read but **do not edit**: [google_auth_views.py](backend/organizer/google_auth_views.py),
[settings.py](backend/youtube_organizer/settings.py),
[middleware.py](backend/youtube_organizer/middleware.py),
[apps.py](backend/organizer/apps.py), [admin.py](backend/organizer/admin.py),
`organizer/migrations/`, `.githooks/pre-push`.

### The `__init__.py` that is not optional

`backend/organizer/tests/__init__.py` **must exist as a real file.** Python 3 namespace packages
make it look optional, but `unittest` discovery — which `manage.py test` uses — dropped namespace
package support in Python 3.11, and the container runs **3.13**. Without it the symptom is not an
error: it is `Ran 0 tests in 0.000s / OK`, exit 0. A green CI over zero tests is exactly the
failure AC2 exists to prevent, which is why the DoD requires a **non-zero test count** rather than
just exit 0.

The same applies to `organizer/management/__init__.py` — Django's command discovery walks
`<app>/management/commands/` as a package.

### Why the move generates no migration

Django records models by `app_label.ModelName`, not by Python module path. `UserSocialToken` stays
in the `organizer` app, so `organizer.0001_initial` still resolves it and `makemigrations` sees no
change — the model's `__module__` is not part of migration state. What *would* break it: failing to
re-export from `models/__init__.py` (Django imports `<app>.models`; a class not reachable there is
not registered, and `makemigrations` would propose **deleting** the table). If you see
`Delete model UserSocialToken`, **stop** — that is the missing re-export, not a real schema change.
Do not accept the generated migration.

### The layering guard

This is the mechanism AC1's "with `services/` importing neither DRF nor `youtube/`" asks for.
Checking it once by hand satisfies today and nothing after; a test satisfies every later story.

Requirements:

- Walk `.py` files under each layer directory with `ast.parse` on the **source text**. Do not
  `import` the modules under inspection — an import-based check would execute them and would miss
  a violation inside a function body.
- Handle both `import x` (`ast.Import`) and `from x import y` (`ast.ImportFrom`), including
  **relative** imports: `ast.ImportFrom.level > 0` with `module='youtube'` inside `services/` is a
  violation that a naive string match on `"organizer.youtube"` misses entirely.
- Failure messages must name the offending file, line and import — a bare `assertFalse` will cost
  the next developer ten minutes.

Rules to encode (prefix match on the dotted module path):

| Layer dir | Forbidden imports |
| --- | --- |
| `services/` | `rest_framework*`, `organizer.youtube*`, `django.http`, `django.urls` |
| `youtube/` | `organizer.models*`, `organizer.services*`, `django.db*` |
| `api/` | `organizer.youtube*` |

Starting shape (extend, don't just paste):

```python
import ast
import pathlib
from django.test import SimpleTestCase

ORGANIZER = pathlib.Path(__file__).resolve().parent.parent

FORBIDDEN = {
    "services": ("rest_framework", "organizer.youtube", "django.http", "django.urls"),
    "youtube": ("organizer.models", "organizer.services", "django.db"),
    "api": ("organizer.youtube",),
}


def _imported_modules(tree):
    """Yield (lineno, dotted_path) for every import, resolving relative ones."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # from . / .. import x
                yield node.lineno, f"organizer.{node.module or ''}".rstrip(".")
            else:
                yield node.lineno, node.module or ""


class LayerDependencyDirectionTests(SimpleTestCase):
    """AD-1: nothing points back up. Guards the direction for every later story."""

    def test_layers_do_not_import_upward(self):
        for layer, forbidden in FORBIDDEN.items():
            for path in (ORGANIZER / layer).rglob("*.py"):
                tree = ast.parse(path.read_text())
                for lineno, module in _imported_modules(tree):
                    for bad in forbidden:
                        self.assertFalse(
                            module == bad or module.startswith(bad + "."),
                            f"{path.relative_to(ORGANIZER)}:{lineno} imports "
                            f"'{module}' — forbidden in organizer/{layer}/ (AD-1).",
                        )
```

Note the relative-import resolution above is deliberately coarse (it maps `from .x` to
`organizer.x`). That is correct for one level, which is all these packages are; if a later story
adds nesting, tighten it then.

`SimpleTestCase` — not `TestCase` — because this test touches no database. It therefore also runs
when the DB is unreachable, which matters for the pre-push hook's skip path.

### Coverage configuration

`backend/.coveragerc`:

```ini
[run]
source = organizer
branch = True
omit =
    */migrations/*
    */tests/*
    */__pycache__/*

[report]
show_missing = True
skip_covered = False
```

`branch = True` because NFR-13's gate is stated over lines/statements/functions/**branches**;
turning it on later would move the number under the gate's feet.

`coverage==7.15.4` (current release; requires Python ≥3.10, container is 3.13 ✅). Exact pin,
matching the discipline Story 1.1 established for every requirement.

### The 70% gate: why it does not turn on in this story

`ci.yml:11` reads `TODO(story 1-2): backend coverage gate` and `project-context.md:250` says the
backend coverage gate "arrives with 1-2". Taken literally that means `fail_under = 70` here.
**Do not do that**, for a concrete reason: the measurable `organizer/` surface is dominated by
`google_auth_views.py` (~150 lines of OAuth flow), and the only tests this story is scoped to write
are structural. A 70% gate would therefore either (a) fail CI on merge, or (b) force OAuth tests
that belong to Stories 1.4 and 6.1 into a skeleton PR.

**What this story ships:** the harness, the config, the CI measurement, and a recorded baseline
percentage. **What Story 1.4 turns on:** `fail_under`, once the cookie-auth `APITestCase` (AD-16
requires it there anyway) makes 70% honestly reachable. Retarget the `ci.yml` TODO accordingly with
that one-line reason — the existing comment block's own rule is *"Add them when their tooling
lands — do not stub them as continue-on-error"*, and a threshold nothing can meet is a stub by
another name.

Record the measured baseline in Completion Notes so 1.4 knows the distance.

> Flagged for Alexis: this is a deliberate, reasoned divergence from a TODO that names this story.
> See "Questions for Alexis" at the bottom.

### CI rules you must not "optimize"

From `Docs/CI-AND-GITHUB-GATES.md` and the hard-won comments already in `ci.yml`:

- **No paths filter.** GitHub reports *no status* for a filtered-out job, so path filters plus
  required status checks = permanently unmergeable docs-only PRs. The comment at `ci.yml:16-20`
  says so; it was not a performance oversight.
- **`POSTGRES_HOST: localhost` must stay.** `settings.py:123` defaults it to `db`, the compose
  service name, which does not resolve on a runner.
- **Never `continue-on-error`** to make a gate "soft".
- `concurrency` cancels PR runs only, never `main`/`develop`. Leave it.

### Testing

**This story creates the harness the whole project's testing rests on.** Standards that bind from
here (AD-16, NFR-13):

- Backend tests are Django `APITestCase` (DRF) for anything touching an endpoint; `SimpleTestCase`
  for DB-free structural tests like the layering guard; `TestCase` when the ORM is involved.
- **No test touches the network.** No test authenticates to Google or calls the YouTube Data API.
  The gateway fake arrives in Story 5.1; until then, no test may reach for a real client.
- Auth-dependent tests must exercise the **cookie-borne** path (`access_token` HttpOnly cookie),
  not an `Authorization` header — no real client sends one. Nothing in *this* story needs it, but
  Story 1.4 does, and that is why the harness must not bake in a header-based helper.
- Tests live in `organizer/tests/`, one `test_<subject>.py` per subject.
- Test file naming must match `test*.py` — unittest discovery's default pattern. A file named
  `layering_test.py` is silently never run.

Run locally: `make backend-test` (container) or, on the host with `make up` running,
`cd backend && POSTGRES_HOST=localhost .venv/bin/python manage.py test --noinput`.

### Previous story intelligence (Story 1.1, merged 2026-08-09)

- **The container is the source of truth.** `backend/.venv` was recreated during 1.1 and now
  mirrors the container's pins — but it is one `pip install` behind the moment this story adds
  `coverage`. If a host-side `manage.py` run fails on `ModuleNotFoundError: coverage`, that is a
  stale venv, not a code error: `backend/.venv/bin/pip install -r backend/requirements.txt`.
  **Do not "fix" code to satisfy a stale venv** — the exact trap 1.1 recorded.
- **Two compose files.** Root `docker-compose.yml` is the real one (`make up`, `postgres:15`).
  `backend/docker-compose.yml` is a stale duplicate (`postgres:16`, a `web` service) that nothing
  invokes. Edit neither. Do not get confused when a search hits it.
- **Mixed indentation is real and per-file.** `models.py` and `views.py` are **tab**-indented;
  `urls.py`, `settings.py`, `google_auth_views.py` are 4-space. Moved files keep their own
  indentation; new files (`tests/`, the layer `__init__.py`s, `models/__init__.py`) are 4-space
  PEP 8. **Never reformat a file wholesale** — it destroys the diff this story needs to be readable.
- **Django 6.0.8 / DRF 3.18.0 / Python 3.13** are the running versions. `DEFAULT_AUTO_FIELD` is set
  explicitly in both `settings.py:168` and `apps.py:5`; leave both.
- **A live P1 defect exists** (`AI-1` in `sprint-status.yaml`): the frontend Sign-in button omits
  `credentials: "include"`, so login through the UI fails with `MismatchingStateError`. **It is
  Epic 2's, not yours.** It also means you cannot smoke-test login through the browser UI — use the
  `curl` probes in the DoD, which is what they are for.
- **Story 1.1's deferred item is now yours to partially close:** *"The strict deprecation check only
  reaches import and check time … A real harness is Story 1.2."* Adding the harness closes the
  structural half. Do not attempt the rest.
- **The per-PR test rule** (`project-context.md`: "Every story PR must still include tests mapping
  to its acceptance criteria") was un-satisfiable in 1.1 and is recorded as deferred. This story is
  where it starts being satisfiable — `test_skeleton.py` maps to AC1, `test_layering.py` maps to
  AC1's dependency clause, and the suite running green maps to AC2. Say so in the PR body.

### Git intelligence (last 5 commits)

`6e7c81a` / `7117a40` / `1b10cab` / `7aab44d` — Stories 3.5/3.6, shipped **ahead of** their E1/E2
dependencies. Consequence for you: `ci.yml` and `.githooks/pre-push` already exist, already run
`manage.py test`, and are already green over a zero-test suite. Your changes to `ci.yml` are
therefore **edits to a live, working gate**, not a rewrite — treat the existing comments as
load-bearing documentation and preserve them. `7117a40` in particular was a code-review hardening
pass; several comments there encode a defect that was found and fixed.

`7d23ab6` — Story 1.1. `ec1c62d` on that branch added ~391 files under `.claude/`; it is agent
tooling, unrelated, and already merged. Ignore it when reading history.

Conventions the recent commits establish: Conventional Commit subjects with a scope
(`ci:`, `docs(story-1-1):`), one squash-merge per story PR, no attribution trailers anywhere.

### The PR template trap

`.github/pull_request_template.md` auto-applies and is still Accountr's: it instructs
`pnpm exec nx run backend:test --coverage`, cites Prisma DTOs and money-as-string, and links to
`Docs/MVPDefinition/…` paths that do not exist here. `project-context.md` requires all checklist
items ticked before merge, so it is currently impossible to satisfy honestly. **Tick what applies,
strike through the rest.** Do not rewrite the template in this PR (it is tracked as deferred work),
and do not silently tick items you did not do.

### Project Structure Notes

- Python `snake_case` throughout; models singular. Test files `test_<subject>.py`.
- New directories are packages (`__init__.py` present), never namespace packages.
- `organizer/auth/` does **not** shadow `django.contrib.auth`: Python 3 imports are absolute, and
  `google_auth_views.py:7`'s `from django.contrib.auth import login` is unaffected. Inside
  `organizer/`, reach the local package as `from .auth import …` / `organizer.auth`.
- No new migration, no schema change, no settings change in this story.
- `.dockerignore` still absent and `backend/.venv` still enters the build context (deferred from
  1.1). Not yours to fix; just expect a slow `docker compose build` if you rebuild.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.2] — user story + acceptance criteria
- [Source: …/ARCHITECTURE-SPINE.md#Design Paradigm] — the layer table, dependency arrows, "read the arrows as permission"
- [Source: …/ARCHITECTURE-SPINE.md#AD-1] — services are the only mutation path
- [Source: …/ARCHITECTURE-SPINE.md#AD-16] — no test touches the network; `APITestCase`; cookie path; 70% coverage
- [Source: …/ARCHITECTURE-SPINE.md#AD-17] — localhost only; do not harden settings here
- [Source: …/ARCHITECTURE-SPINE.md#Source tree] — the exact `backend/organizer/` target tree
- [Source: …/WORK-SPLIT.md#E1] — "highest risk in the phase; it rewrites the one thing that currently works"
- [Source: _bmad-output/implementation-artifacts/1-1-…-bounded-dependency-pins.md] — container-is-truth, stale venv, two compose files, mixed indentation, the AI-1 defect
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] — the deprecation-check item this story partially closes
- [Source: _bmad-output/project-context.md] — backend rules, testing rules, CI gates, attribution ban
- [Source: Docs/CI-AND-GITHUB-GATES.md] — gate intent; no paths filter; coverage 70%
- [Source: CLAUDE.md] — git workflow, Conventional Commits, attribution ban, project-local memory
- [coverage.py 7.15.4 on PyPI](https://pypi.org/project/coverage/) — current release, Python ≥3.10
- [Python 3.11 unittest changelog](https://docs.python.org/3/whatsnew/3.11.html) — namespace-package discovery removed (why `tests/__init__.py` is mandatory)
- [Django 6.0 testing docs](https://docs.djangoproject.com/en/6.0/topics/testing/overview/) — discovery pattern `test*.py`, `SimpleTestCase` vs `TestCase`

## Questions for Alexis

1. **Coverage threshold timing.** This story ships the coverage harness + a recorded baseline but
   deliberately does **not** set `fail_under = 70`, retargeting that to Story 1.4 (reasoning in Dev
   Notes → "The 70% gate"). `ci.yml:11`'s TODO names 1-2 for the "backend coverage gate", so this
   is a conscious divergence. Confirm, or say the word and it becomes a ratchet
   (`fail_under = <measured baseline>`, only ever raised) instead.
2. **`google_auth_views.py` placement.** Left at the app root rather than moved into `api/`, because
   Stories 1.4 and 6.1 both rewrite it and the spine's Capability map still names it there. The
   trade-off is that `api/` ships holding one small view while the largest view module sits outside
   it. Fine, or move it now and absorb the conflict risk?

## Dev Agent Record

### Agent Model Used

claude-opus-5 (dev-story workflow)

### Debug Log References

All commands run against the live stack (`docker compose up -d --build`) unless marked host-side.

**1. The `tests/__init__.py` trap, reproduced for real.** The first suite run was made with the
package directory present but `__init__.py` missing (a relative-path `mkdir` had landed the touched
file elsewhere). Exactly the symptom Dev Notes predicts — not an error, a silent pass:

```
Ran 0 tests in 0.000s
NO TESTS RAN
Found 0 test(s).
```

Adding the real `__init__.py` turned it into a discovering, failing suite (the RED step):

```
Ran 7 tests in 0.004s
FAILED (failures=2, errors=11)
AssertionError: organizer.models resolved to .../backend/organizer/models.py; expected the package.
```

**2. Layering guard proven to bite.** `import rest_framework` appended to
`organizer/services/__init__.py`, then `manage.py test`:

```
FAIL: test_layers_do_not_import_upward (organizer.tests.test_layering.LayerDependencyDirectionTests...)
AssertionError: Lists differ: ["services/__init__.py:10 imports 'rest_fr[48 chars]1)."] != []
First extra element 0:
"services/__init__.py:10 imports 'rest_framework' — forbidden in organizer/services/ (AD-1)."
Ran 7 tests in 0.003s
FAILED (failures=1)
```

Violation reverted; suite back to `OK`.

**3. Django state (container).**

```
$ python manage.py check
System check identified no issues (0 silenced).

$ python manage.py makemigrations --check --dry-run
No changes detected                      # exit 0, no migration file created

$ python manage.py test --noinput
Ran 7 tests in 0.007s / OK / Found 7 test(s).

$ python manage.py test organizer.tests.test_layering --noinput
Ran 3 tests in 0.005s / OK / Found 3 test(s).
```

**4. Import probes (container, with `DJANGO_SETTINGS_MODULE` set — the bare `python -c` form in the
DoD raises `ImproperlyConfigured` before it can import anything, since `organizer.models` reads
settings at import time):**

```
ok
/app/organizer/models/__init__.py
```

**5. Route probes (proves the `views.py` → `api/views.py` move kept the URLs wired).**

```
api/auth/me/          -> 401
api/youtube/playlists/-> 401
api/auth/google/      -> 200 {"auth_url":"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=…
```

**6. Coverage (container, `coverage run manage.py test` + `coverage report`).** Full table in
Completion Notes; `TOTAL 97 stmts, 43 miss, 4 branch, 53%`.

**7. `git diff --stat backend/youtube_organizer/settings.py`** → empty. CORS / session / CSRF /
`REST_FRAMEWORK` blocks untouched.

**8. Host-side (pre-push layer 6/6 command):**
`cd backend && POSTGRES_HOST=localhost .venv/bin/python manage.py test --noinput` → `Ran 7 tests / OK`.
The host venv needed `pip install coverage==7.15.4` — the stale-venv trap Story 1.1 recorded, not a
code problem.

### Completion Notes List

- **AC1 satisfied.** `api/`, `auth/`, `services/`, `sync/`, `youtube/`, `models/`,
  `management/commands/` and `tests/` all exist as real packages (every one has an `__init__.py`;
  `test_skeleton.py` asserts `__file__` is present so a namespace package cannot pass). The five
  layer `__init__.py` files carry only their Owns / Must-never contract docstring — no code, no
  imports, no `__all__`, and a test asserts the docstring is non-empty so a later story cannot
  quietly strip the guardrail.
- **AC1's dependency clause is a test, not a one-off check.** `test_layering.py` parses the source
  text with `ast` (never imports the modules under inspection, so a violation inside a function body
  is caught too), resolves relative imports, and reports file:line:import on failure. It covers
  `services/` ✗ `rest_framework`/`organizer.youtube`/`django.http`/`django.urls`, `youtube/` ✗
  `organizer.models`/`organizer.services`/`django.db`, `api/` ✗ `organizer.youtube`. Two extra tests
  exercise the detector itself on synthetic source, so a refactor that broke `_imported_modules`
  fails loudly instead of leaving a blind guard green.
- **AC2 satisfied.** `manage.py test` discovers and runs **7 tests, OK, exit 0** — a non-zero count,
  which is the point of AC2. `SimpleTestCase` throughout, so the suite also runs when the DB is
  unreachable (the pre-push hook's skip path).
- **Coverage baseline: 53%** (97 statements, 43 missed, branch coverage on), measured by
  `coverage run manage.py test && coverage report` in the container. Breakdown of the miss:
  `google_auth_views.py` 37% (64 stmts, 39 missed) is essentially the whole gap, exactly as Dev
  Notes predicted; `api/views.py` 67%, `models/user_social_token.py` 92%, everything else 100%.
  **Distance to the NFR-13 gate: 17 points**, all of it in OAuth code that Stories 1.4 and 6.1 own.
- **`fail_under` deliberately NOT set** (story decision, confirmed at kickoff). The `ci.yml:11` TODO
  was retargeted to story 1-4 with a one-line reason rather than deleted; CI now measures and prints
  coverage on every run, with no `continue-on-error` anywhere.
- **No migration, no schema change, no settings change.** `makemigrations --check --dry-run` reports
  `No changes detected`; the `models/__init__.py` re-export keeps `UserSocialToken` registered and
  `google_auth_views.py:8`'s `from .models import UserSocialToken` working unedited.
- **Scope held.** `google_auth_views.py`, `settings.py`, `middleware.py`, `apps.py`, `admin.py`,
  `migrations/` and `.githooks/pre-push` untouched. No `sync_inbox.py`, no speculative files inside
  the empty layers.
- **Per-PR test rule now satisfiable** (deferred from 1.1): `test_skeleton.py` → AC1,
  `test_layering.py` → AC1's dependency clause, the suite running green → AC2.
- Minor deviation worth recording: the DoD's bare
  `python -c "import organizer.api, …"` cannot work as literally written — importing
  `organizer.models` touches settings, so it needs `DJANGO_SETTINGS_MODULE` plus `django.setup()`.
  Same assertion, run that way; and `test_skeleton.py` encodes it permanently.

### File List

**Added**

- `backend/.coveragerc`
- `backend/organizer/api/__init__.py`
- `backend/organizer/auth/__init__.py`
- `backend/organizer/services/__init__.py`
- `backend/organizer/sync/__init__.py`
- `backend/organizer/youtube/__init__.py`
- `backend/organizer/models/__init__.py`
- `backend/organizer/management/__init__.py`
- `backend/organizer/management/commands/__init__.py`
- `backend/organizer/tests/__init__.py`
- `backend/organizer/tests/test_skeleton.py`
- `backend/organizer/tests/test_layering.py`

**Moved**

- `backend/organizer/models.py` → `backend/organizer/models/user_social_token.py` (content unchanged, tabs preserved)
- `backend/organizer/views.py` → `backend/organizer/api/views.py` (two trailing cruft lines deleted)

**Deleted**

- `backend/organizer/tests.py`

**Modified**

- `backend/organizer/urls.py` (one line: `from . import views` → `from .api import views`)
- `backend/requirements.txt` (`coverage==7.15.4` appended)
- `Makefile` (`backend-test`, `backend-coverage` targets + `.PHONY`)
- `.github/workflows/ci.yml` (`coverage run manage.py test` + `coverage report` step; L11 TODO retargeted to 1-4)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (1-2 → review)
- `_bmad-output/implementation-artifacts/1-2-layered-backend-package-skeleton-and-test-runner.md` (this file)

## Change Log

| Date | Change |
| --- | --- |
| 2026-08-12 | Implemented — layered packages with contract docstrings, `models.py`/`tests.py` → packages, `views.py` → `api/`, AST layering guard (proven to fail on a real violation), coverage harness measuring 53% baseline, CI reports coverage without a threshold. 7 tests green. AD-1, AD-16. |
| 2026-08-12 | Story created — layered package skeleton, `models.py`/`tests.py` → packages, `views.py` → `api/`, AST layering guard, coverage harness wired into CI as a report. AD-1, AD-16. |
