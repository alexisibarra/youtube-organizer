---
baseline_commit: b592f2b42fab61049076923c0d0b30a0f604a1ac
---

# Story 1.1: Upgrade to Django 6.0 with bounded dependency pins

Status: in-progress

Epic: 1 — Backend platform · Story key: `1-1-upgrade-to-django-6-0-with-bounded-dependency-pins`
Branch: `feat/story-1-1-django-6-bounded-pins` → PR → `develop` (squash). Never commit to `main`/`develop`.

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want the backend upgraded to Django 6.0.x with every requirement bounded-pinned,
so that the platform runs on a supported, reproducible dependency set (AD-14 stack).

## Acceptance Criteria

**AC1 — Pinned, supported dependency set**
**Given** the current `backend/requirements.txt` with an unbounded `Django>=4.0`
**When** I upgrade the stack
**Then** Django is pinned to `6.0.x`, DRF to `>=3.17.0`, `drf-spectacular` to `0.30.0`, and every
other requirement carries a bounded pin
**And** the backend container builds and `manage.py check` passes with no unresolved deprecations.

**AC2 — No regression from the framework bump**
**Given** the running stack
**When** I start the backend with `make up`
**Then** the server boots on `https://localhost:8000` and existing OAuth/login routes respond,
confirming no regression from the framework bump.

### Definition of Done (verifiable, no self-reporting)

- [x] `docker compose build backend` succeeds from a clean layer (requirements changed → layer rebuilds).
- [x] `docker compose exec backend python -c "import django; print(django.get_version())"` prints `6.0.x`. → `6.0.8`
- [x] `docker compose exec backend python manage.py check` → `System check identified no issues (0 silenced).`
- [x] `docker compose exec backend python -W error::DeprecationWarning -W error::PendingDeprecationWarning manage.py check` → no `RemovedInDjango*Warning` raised from **our** code (see Dev Notes → "no unresolved deprecations" for how to handle third-party noise). → clean; **zero** warnings, first-party or third-party.
- [x] `docker compose exec backend python manage.py migrate` → no new/pending migrations (`makemigrations --check --dry-run` exits 0). → `No migrations to apply.` / `No changes detected`, exit 0.
- [x] `curl -k https://localhost:8000/api/auth/google/` → **200** with an `auth_url` in the body.
- [x] `curl -k -i https://localhost:8000/api/auth/me/` (no cookie) → **401**, not 500.
- [x] `curl -k -i https://localhost:8000/admin/login/` → **200**.
- [x] SimpleJWT still mints under Django 6.0 — the shell probe in Dev Notes returns a token string.
- [ ] Full Google OAuth login exercised manually end to end in the browser (or, if Google credentials are unavailable, that is stated explicitly in the Completion Notes — do not claim it). → **PENDING HUMAN ACTION.** Credentials *are* present in `backend/.env`, so the "unavailable" escape hatch does not apply. The agent cannot drive an interactive Google consent screen. The R3 mechanism was verified at library level instead (see Debug Log) — this is a narrower check, not a substitute.
- [x] Auth/CORS/cookie settings byte-for-byte unchanged (`git diff` on `settings.py` shows no change in the CORS/session/CSRF block). → `settings.py`, `middleware.py`, all of `organizer/`, `Dockerfile` and `docker-compose.yml` are byte-for-byte unchanged; `git diff --stat` is empty.

## Tasks / Subtasks

- [x] **Task 1 — Rewrite `backend/requirements.txt` with exact pins (AC1)**
  - [x] Replace every unbounded requirement with an exact `==` pin using the verified table in Dev Notes → "Pin block to apply".
  - [x] Add `drf-spectacular==0.30.0` (install only — **do not** add to `INSTALLED_APPS` or write `SPECTACULAR_SETTINGS`; that wiring is Story 3.1).
  - [x] Keep `djangorestframework-simplejwt==5.5.1` with the `# TEMPORARY` comment from Dev Notes. It is removed in Story 1.4, not here.
  - [x] Keep alphabetical-ish grouping readable; add the trailing newline the file currently lacks.
- [x] **Task 2 — Rebuild and boot the container (AC1, AC2)**
  - [x] `make up` (or `docker compose build backend && docker compose up -d`).
  - [x] Confirm the Django version, `manage.py check`, and the deprecation-strict check from the DoD.
  - [x] Confirm `runserver_plus` still serves HTTPS (see Risk R2 if it does not). → R2 did **not** materialise; `django-extensions==4.1` boots and serves HTTPS under Django 6.0.
- [x] **Task 3 — Verify SimpleJWT survives the bump (AC2, Risk R1)**
  - [x] Run the `RefreshToken.for_user` shell probe in Dev Notes. → returned a token; R1 did **not** materialise.
  - [x] If it raises: **STOP, do not patch or vendor SimpleJWT.** Record the traceback in Debug Log References and escalate — the fix is pulling Stories 1.3/1.4 forward, not repairing a dead dependency. → n/a, did not raise.
- [~] **Task 4 — Regression-probe the existing routes (AC2)**
  - [x] The three `curl` probes in the DoD.
  - [ ] Manual browser login through Google if credentials are present in `backend/.env`; verify the `access_token` HttpOnly cookie is set and `/api/auth/me/` then returns the user. → **PENDING HUMAN ACTION** (see Completion Notes).
  - [x] Confirm no schema drift: `manage.py makemigrations --check --dry-run`. → exit 0.
- [x] **Task 5 — Refresh the stale local venv (optional but recommended)**
  - [x] `backend/.venv` holds Django 5.2.5, DRF 3.16.1 and **no** SimpleJWT — it is stale and will mislead any local `manage.py` run. Either reinstall it from the new `requirements.txt` or leave it alone and use the container exclusively. Do not "fix" code to satisfy the stale venv. → Recreated from the new pins; it was also **unrelocatable** (shebangs pointed at the repo's old path), so a reinstall alone would not have worked. `.venv/` is gitignored — no repo impact.
- [x] **Task 6 — Commit and PR**
  - [x] Conventional Commit, e.g. `chore(backend): pin dependencies and upgrade to Django 6.0`.
  - [x] Cite `AD-14` (stack) and `AD-17` in the PR body.
  - [x] **No AI/bot attribution anywhere** — no `Co-Authored-By`, no "Generated with" footer, in commit or PR.

## Dev Notes

### Scope boundary — what this story does NOT touch

Everything below is a later story. Doing it here creates merge pain and breaks the risk sequencing.

| Tempting change | Belongs to |
| --- | --- |
| Splitting `organizer/` into `api/ auth/ services/ sync/ youtube/ models/`, adding `tests/` | **Story 1.2** |
| Writing PyJWT issue/verify code | **Story 1.3** |
| Removing SimpleJWT, deleting `JWTAuthCookieMiddleware` header injection, adding the cookie auth class | **Story 1.4** |
| `make backup`, naming the Postgres volume | **Story 1.5** |
| Adding `drf-spectacular` to `INSTALLED_APPS`, schema endpoint, `EXCEPTION_HANDLER` | **Story 3.1 / 3.2** |
| Rewriting `ci.yml` / `deploy.yml` / hooks | **Story 3.5 / 3.6** |
| Any frontend file | **Epic 2** |
| Moving `SECRET_KEY`/`DEBUG`/`ALLOWED_HOSTS` to env | **Deferred by AD-17 — actively forbidden here** |

**AD-17 trap:** `DEBUG = True`, the hardcoded `SECRET_KEY` and empty `ALLOWED_HOSTS` in
[settings.py](backend/youtube_organizer/settings.py#L31-L36) are *accepted* in Phase 1 because nothing is
deployed. Do **not** run `manage.py check --deploy` and then "fix" its warnings — that is half-building a
production posture nothing validates, which AD-17 explicitly prohibits. Plain `manage.py check` is the gate.

### Pin block to apply

Versions verified against PyPI on **2026-08-09**. Use exact `==` pins: "bounded" plus reproducible, which
is the story's stated *so-that*. Django **must** stay on the `6.0.x` line — PyPI's latest is now **6.1**, so
an unbounded or `>=` pin silently jumps a major line the spine did not decide on.

```text
Django==6.0.8
djangorestframework==3.18.0
django-cors-headers==4.9.0
drf-spectacular==0.30.0
# TEMPORARY — removed in Story 1.4 when the first-party PyJWT auth lands (AD-14).
# 5.5.1 (2025-07-21) is the last release; it does not classify Django 6.0 support.
djangorestframework-simplejwt==5.5.1
google-auth==2.56.3
google-auth-oauthlib==1.4.0
google-auth-httplib2==0.4.1
google-api-python-client==2.198.0
psycopg2-binary==2.9.12
requests==2.34.2
django-extensions==4.1
Werkzeug==3.1.8
pyOpenSSL==26.4.0
```

Why these exact values:

- **`Django==6.0.8`** — released **2026-08-04**, the current 6.0.x patch. It carries one high-severity,
  two moderate and one low-severity security fix over 6.0.7 (the version the architecture spine names,
  written 2026-07-24). Taking 6.0.8 rather than 6.0.7 is a deliberate, security-motivated bump inside the
  spine's `6.0.x` decision — not a divergence from it. Django 6.0 supports Python 3.12–3.14; the
  container is `python:3.13-slim` ✅.
- **`djangorestframework==3.18.0`** — Django 6.0 support landed in **3.17.0** (Mar 2026); 3.18.0 is current
  and classifies Django 5.2/6.0/6.1. Satisfies the AC's `>=3.17.0` floor with a reproducible pin.
- **`drf-spectacular==0.30.0`** — current, classifies Django 6.0 + DRF 3.17.
- **`django-cors-headers==4.9.0`** — classifies Django 6.0.
- **`psycopg2-binary==2.9.12`** — Django 6.0 requires psycopg2 **≥ 2.9.9**; psycopg2 is still supported
  (not removed) in 6.0. Do **not** migrate to psycopg 3 in this story — it is an unasked-for change with
  its own regression surface.
- **`django-extensions==4.1`** — see Risk R2.
- **google-* stack** — these are the current releases; the container currently resolves older ones
  (`google-auth-oauthlib 1.2.2`). See Risk R3 before assuming the bump is free.

### Files being modified (read before editing)

| File | Current state | This story changes | Must not break |
| --- | --- | --- | --- |
| [backend/requirements.txt](backend/requirements.txt) | 13 lines, all unbounded; `Django>=4.0`, `djangorestframework>=3.13` | Full rewrite to the pin block above + `drf-spectacular` | Every currently-imported package stays present |
| [backend/Dockerfile](backend/Dockerfile) | `python:3.13-slim`, `pip install -r requirements.txt`, CMD `runserver_plus … --cert-file …` | Nothing expected. Only touch if the build genuinely fails | The certs COPY and the `runserver_plus` HTTPS CMD |
| [backend/youtube_organizer/settings.py](backend/youtube_organizer/settings.py) | Django 5.2 template; `SIMPLE_JWT` dict at top; CORS/session/CSRF cross-origin block; `REST_FRAMEWORK` → SimpleJWT auth class; `DEFAULT_AUTO_FIELD` | Ideally **nothing**. Only a change forced by a real Django 6.0 error is in scope, and it must be called out in Completion Notes | `CORS_ALLOW_CREDENTIALS`, the single `https://localhost:3000` origin, `SESSION_/CSRF_COOKIE_SAMESITE="None"` + `SECURE=True` (AD-14, NFR-9). The `JWTAuthCookieMiddleware` entry stays until Story 1.4 |

Read but **do not edit** in this story:
[middleware.py](backend/youtube_organizer/middleware.py) (12 lines, injects `Authorization: Bearer` from the
`access_token` cookie — retired in 1.4),
[google_auth_views.py](backend/organizer/google_auth_views.py) (imports
`rest_framework_simplejwt.tokens.RefreshToken` at L14, mints at L132; the PKCE verifier session dance at
L49-53 and L84-88), [models.py](backend/organizer/models.py) (`UserSocialToken` only — no schema change here).

### Django 6.0 changes that could bite this codebase

Checked against the Django 6.0 release notes; none of these require a code change here, but know them
before you diagnose an error:

- `DEFAULT_AUTO_FIELD` now defaults to `BigAutoField`. Both
  [settings.py:168](backend/youtube_organizer/settings.py#L168) and
  [apps.py](backend/organizer/apps.py) already set it explicitly to `BigAutoField` — same value, **no
  migration is generated**. Leave both lines in place; removing them is churn.
- Removed in 6.0: `DjangoDivFormRenderer`/`Jinja2DivFormRenderer`, `BaseDatabaseOperations.field_cast_sql()`,
  `cx_Oracle`, `get_prefetch_queryset()`, `ModelAdmin.log_deletion()`, `LogEntryManager.log_action()`,
  positional args to `BaseConstraint`, `Prefetch.get_current_queryset()`. This codebase uses **none** of them.
- Email API modernised (`SafeMIMEText`/`SafeMIMEMultipart` deprecated) — no email code here.
- Custom ORM expressions must return `params` as a tuple — no custom expressions here.

### "No unresolved deprecations" — what the AC actually means

Run the strict check listed in the DoD. Rules for what you find:

- A `RemovedInDjango*Warning` raised from a file under `backend/organizer/` or
  `backend/youtube_organizer/` → **fix it, in this story.**
- A deprecation raised from inside `site-packages` (SimpleJWT, django-extensions, …) → **do not patch the
  dependency.** Record it in Completion Notes as a known third-party warning and move on. Monkey-patching a
  library to silence a warning is out of scope and harms Stories 1.3/1.4.

### Verification probes (copy-paste)

SimpleJWT under Django 6.0 — the single riskiest line in this story:

```bash
docker compose exec backend python manage.py shell -c "
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
u, _ = User.objects.get_or_create(username='smoke-1-1')
print(str(RefreshToken.for_user(u).access_token)[:40], '...OK')
u.delete()
"
```

Route regression (self-signed certs → `-k` is required, not optional):

```bash
curl -sk https://localhost:8000/api/auth/google/ | head -c 200   # 200 + auth_url
curl -sk -o /dev/null -w '%{http_code}\n' https://localhost:8000/api/auth/me/     # 401
curl -sk -o /dev/null -w '%{http_code}\n' https://localhost:8000/admin/login/     # 200
```

Note on `/api/auth/google/`: `GoogleAuthInitView` declares no `permission_classes`, and settings define no
`DEFAULT_PERMISSION_CLASSES`, so DRF's default `AllowAny` applies — it is reachable unauthenticated and is
therefore a valid smoke test that needs no Google login. `/api/auth/me/` is `IsAuthenticated` and
SimpleJWT's authenticator supplies a `WWW-Authenticate` header, so an unauthenticated call is **401**
(a 500 means the auth stack broke — that is the regression this AC is hunting).

### Risks — read these before you start

**R1 · SimpleJWT is unclassified for Django 6.0 (highest risk).**
`djangorestframework-simplejwt==5.5.1` (2025-07-21, last release) classifies Django 4.2/5.0/5.1/5.2 —
**not 6.0**. This story bumps Django *while* SimpleJWT is still the live auth mechanism
([settings.py:173-177](backend/youtube_organizer/settings.py#L173-L177),
[google_auth_views.py:132](backend/organizer/google_auth_views.py#L132)); the replacement is Stories 1.3–1.4.
Nothing on Django 6.0's removal list is territory SimpleJWT is known to use, so it is *expected* to run —
but "expected" is not "verified". Task 3 verifies it. If it breaks: escalate for a re-sequence (1.3 + 1.4
before the bump), do not fork or patch the library. This is the exact blocker the architecture's
version-reality review raised.

**R2 · `django-extensions==4.1` is also unclassified for Django 6.0.**
Its PyPI classifiers stop at Django 5.2. It is load-bearing: `runserver_plus` is what serves HTTPS in
[the Dockerfile CMD](backend/Dockerfile) and in the compose `command`, and HTTPS is what the cookie/OAuth
flow depends on. Plain `manage.py runserver` cannot do SSL. Check for a newer release at implementation
time; if 4.1 fails to boot under Django 6.0, record the traceback and escalate rather than improvising a
new dev server.

**R3 · The Google OAuth stack bump can regress the PKCE fix.**
The most recent commit (`8b8d48e`) fixed a live login-breaking bug by persisting
`flow.code_verifier` in the session across the two requests. That fix depends on `Flow.code_verifier`
remaining a settable attribute. The container currently runs `google-auth-oauthlib 1.2.2`; the pin block
moves to `1.4.0` (2026-05-07). If a manual Google login fails with `invalid_grant: Missing code verifier`
after the bump, that is R3 — pin `google-auth-oauthlib==1.2.2` instead and note it, rather than rewriting
the OAuth views.

**R4 · Stale local venv.** `backend/.venv` has Django 5.2.5, DRF 3.16.1 and **no** SimpleJWT installed, so
`manage.py` run outside Docker will fail on import for reasons unrelated to this story. **The container is
the source of truth.**

**R5 · Two compose files.** [docker-compose.yml](docker-compose.yml) at the repo root is the real one
(`make up` uses it; services `backend`/`db`/`frontend`, `postgres:15`). `backend/docker-compose.yml` is a
stale duplicate (`postgres:16`, a `web` service) that nothing invokes. Edit **neither** in this story —
just don't get confused by the second one. (`postgres_data` volume naming is Story 1.5's business.)

### Testing

**There is no test suite yet.** `backend/organizer/tests.py` is the stock empty stub and the
`APITestCase` harness is **Story 1.2**. Do not stand up a test runner, add `tests/`, or write
`APITestCase` classes here — that is 1.2's acceptance criteria and duplicating it causes a conflicting diff.

Verification for this story is therefore: `manage.py check` (strict), `makemigrations --check`, the
container boot, the SimpleJWT shell probe, and the three route probes — all listed in the DoD. Every
`python`/`manage.py` command runs **inside the container** (`docker compose exec backend …`).

The 70% coverage gate (NFR-13, AD-16) applies from Story 1.2 onward; it has nothing to measure yet.

### Project Structure Notes

- No new files. No directory moves. No migrations. The only mandatory edit is `backend/requirements.txt`.
- Backend indentation is mixed by file — `models.py` and `views.py` use tabs, `settings.py`/`urls.py`/
  `google_auth_views.py` use 4 spaces. Match the file you touch; never reformat wholesale.
- Python naming stays `snake_case`; models singular.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.1] — user story + acceptance criteria
- [Source: _bmad-output/planning-artifacts/architecture/architecture-youtube-organizer-2026-07-24/ARCHITECTURE-SPINE.md#Stack] — Django 6.0.x, DRF `>=3.17.0`, drf-spectacular 0.30.0, PyJWT 2.13.0, PostgreSQL 15
- [Source: …/ARCHITECTURE-SPINE.md#AD-14] — cookie JWT invariant; SimpleJWT dropped in favour of first-party PyJWT
- [Source: …/ARCHITECTURE-SPINE.md#AD-17] — localhost-only Phase 1; `DEBUG`/`SECRET_KEY`/`ALLOWED_HOSTS` deliberately unhardened
- [Source: …/ARCHITECTURE-SPINE.md#AD-2] — two-tree repo, `requirements.txt` is the backend dependency spec
- [Source: …/reviews/review-version-reality.md] — the SimpleJWT-vs-Django-6.0 blocker and the corrected DRF pin
- [Source: …/WORK-SPLIT.md#E1] — "highest risk in the phase; it rewrites the one thing that currently works"
- [Source: _bmad-output/project-context.md] — backend rules, auth invariants, mixed-indentation gotcha, no-attribution rule
- [Source: CLAUDE.md] — git workflow, Conventional Commits, attribution ban
- [Django 6.0 release notes](https://docs.djangoproject.com/en/6.0/releases/6.0/) — Python 3.12–3.14, psycopg2 ≥ 2.9.9, removal list
- [Django 6.0.8 release notes](https://docs.djangoproject.com/en/6.0/releases/6.0.8/) (issued 2026-08-04) — security fixes over 6.0.7
- [DRF 3.17 release announcement](https://forum.djangoproject.com/t/django-rest-framework-3-17-released/44581) — Django 6.0 support
- [djangorestframework-simplejwt on PyPI](https://pypi.org/project/djangorestframework-simplejwt/) — 5.5.1, no Django 6.0 classifier

## Dev Agent Record

### Agent Model Used

claude-opus-5 (Claude Code)

### Debug Log References

All commands run inside the container per Dev Notes → Testing. Branch cut from `origin/develop`
(`b592f2b`), which already contains the merged PKCE fix from PR #10.

| Probe | Result |
| --- | --- |
| `docker compose build backend` | Success. Every pin resolved to the exact requested version — no backtracking, no conflict. |
| `python -c "import django; print(django.get_version())"` | `6.0.8` |
| `manage.py check` | `System check identified no issues (0 silenced).` |
| `manage.py check` with `-W error::DeprecationWarning -W error::PendingDeprecationWarning` | Same clean output — no warning from first-party *or* third-party code. |
| Strict import of all first-party modules (`organizer.{models,views,google_auth_views,urls,apps,admin}`, `youtube_organizer.{middleware,urls,settings}`) under `warnings.filterwarnings('error', …)` | All import clean. Added beyond the DoD because `manage.py check` alone does not guarantee every module is imported. |
| `manage.py migrate` | `No migrations to apply.` |
| `manage.py makemigrations --check --dry-run` | `No changes detected`, exit 0. `DEFAULT_AUTO_FIELD` behaved as Dev Notes predicted — no migration generated. |
| **R1** — `RefreshToken.for_user(u).access_token` | Returned `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ…`. SimpleJWT 5.5.1 works under Django 6.0 despite the missing classifier. |
| `GET /api/auth/google/` | 200, body carries `auth_url` with the real client id and the full scope set. |
| `GET /api/auth/me/` (no cookie) | `401` — auth stack intact, not a 500. |
| `GET /admin/login/` | `200` |
| **R3** — PKCE contract under `google-auth-oauthlib` 1.4.0 | `authorization_url()` still emits `code_challenge` with `code_challenge_method=S256`; `flow.code_verifier` is still readable on the init Flow and still settable on a second Flow, round-tripping intact. This is exactly the contract `google_auth_views.py` L53 and L86 depend on. |

Resolved transitive versions worth noting: `PyJWT 2.13.0` (pulled in by SimpleJWT) already matches
the version AD-14 names for the first-party auth module in Story 1.3 — no pin conflict ahead.
Also resolved: `cryptography 50.0.0`, `sqlparse 0.5.5`, `asgiref 3.12.1`.

### Completion Notes List

**What changed:** exactly one production file — `backend/requirements.txt`, rewritten from 13
unbounded requirements to 15 exact `==` pins plus `drf-spectacular`. No Python source, no settings,
no Dockerfile, no compose file was touched. `git diff --stat` over `settings.py`, `middleware.py`,
`organizer/`, `Dockerfile` and `docker-compose.yml` is empty, which satisfies the auth/CORS/cookie
invariant DoD item by construction rather than by inspection.

**All three named risks failed to materialise**, and each was verified rather than assumed:

- **R1 (SimpleJWT unclassified for Django 6.0 — the story's highest risk):** mints fine. No
  escalation, no re-sequencing of Stories 1.3/1.4 needed.
- **R2 (`django-extensions` unclassified):** `runserver_plus` boots and serves HTTPS on
  `https://localhost:8000` under Django 6.0. No dev-server improvisation needed.
- **R3 (OAuth stack bump regressing the PKCE fix):** the `Flow.code_verifier` contract that
  commit `8b8d48e` depends on is intact under `google-auth-oauthlib 1.4.0`. Verified at library
  level; **not** a substitute for the end-to-end login (see the outstanding item below).

**Third-party deprecation warnings: none.** The Dev Notes anticipated having to record
`site-packages` noise from SimpleJWT / django-extensions and move on. There was none to record —
the strict check is completely clean.

**R4 was worse than documented.** `backend/.venv` was not merely stale (Django 5.2.5, no SimpleJWT);
it was *unrelocatable* — its shebangs pointed at `/Users/alexis/Proyectos/youtube-organizer`, a path
that no longer exists since the repo moved under `Proyectos/Yo/`. `pip install -r requirements.txt`
against it failed with `bad interpreter`, so a plain reinstall (the Task 5 wording) could not have
worked. Recreated with `python3 -m venv --clear`; it now mirrors the container exactly. `.venv/` is
gitignored, so this has no repo footprint — it only removes a local trap.

**Deliberate non-actions, per the story's scope table and AD-17:** `drf-spectacular` is installed but
*not* added to `INSTALLED_APPS` and no `SPECTACULAR_SETTINGS` was written (Story 3.1).
`djangorestframework-simplejwt` stays, with its `# TEMPORARY` comment (removed in Story 1.4).
`manage.py check --deploy` was **not** run and `DEBUG`/`SECRET_KEY`/`ALLOWED_HOSTS` were left alone
(AD-17 forbids it here). No tests were written — the `APITestCase` harness is Story 1.2.

**⚠️ One DoD item is outstanding and is NOT claimed: the end-to-end Google browser login.**
Google credentials *are* present in `backend/.env` (the live client id appears in the `auth_url`
response), so the story's "if credentials are unavailable, state it" escape hatch does **not** apply
— the check is genuinely owed. It cannot be automated: it requires driving Google's interactive
consent screen with a real account. **Alexis must run it before this story is merged:** open
`https://localhost:3000`, log in through Google, then confirm the `access_token` HttpOnly cookie is
set and that `/api/auth/me/` returns the user. If it fails with `invalid_grant: Missing code
verifier`, that is R3 after all — pin `google-auth-oauthlib==1.2.2` and note it, rather than
touching the OAuth views.

### File List

| File | Change |
| --- | --- |
| `backend/requirements.txt` | Modified — full rewrite to exact pins; added `drf-spectacular==0.30.0`; added the trailing newline the file lacked. |
| `_bmad-output/implementation-artifacts/1-1-upgrade-to-django-6-0-with-bounded-dependency-pins.md` | Added — this story file (untracked before this branch). |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Modified — story status → `in-progress` → `review`; `last_updated` bumped. |

Not modified, deliberately: `backend/Dockerfile`, `backend/youtube_organizer/settings.py`,
`backend/youtube_organizer/middleware.py`, everything under `backend/organizer/`, `docker-compose.yml`.
`backend/.venv/` was recreated but is gitignored.

## Change Log

| Date | Change |
| --- | --- |
| 2026-08-09 | Upgraded backend to Django 6.0.8 and replaced all 13 unbounded requirements with exact `==` pins; added `drf-spectacular==0.30.0` (install only). Verified R1 (SimpleJWT), R2 (`runserver_plus` HTTPS) and R3 (PKCE `code_verifier` contract) all hold under the bump. Recreated the unrelocatable local venv. No source, settings, Docker or compose changes. AD-14, AD-17. |
