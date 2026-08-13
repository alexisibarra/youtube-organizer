---
baseline_commit: 5c1ba29
---

# Story 1.3: First-party PyJWT token issue/verify module

Status: done

Epic: 1 — Backend platform · Story key: `1-3-first-party-pyjwt-token-issue-verify-module`
Branch: `feat/story-1-3-pyjwt-token-module` → PR → `develop` (squash). Never commit to `main`/`develop`.

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want token issuing and verification implemented in `organizer/auth/` over PyJWT, with unit tests,
so that auth no longer depends on the unmaintained SimpleJWT before the swap (AD-14).

## Acceptance Criteria

**AC1 — Issue and verify round-trip**
**Given** the `organizer/auth/` module
**When** I mint an access token for a user
**Then** it is a signed PyJWT carrying the expected claims and expiry, and verification round-trips it
back to the same user.

**AC2 — Every rejection path is typed and tested**
**Given** a tampered, expired, or wrongly-signed token
**When** verification runs
**Then** it rejects the token with a typed error, and unit tests cover each rejection path.

**AC3 — No SimpleJWT inside the module**
**Given** the module
**When** tests run
**Then** they exercise issue and verify **without** SimpleJWT imported anywhere in the module.

### Definition of Done (verifiable, no self-reporting)

Every command runs **inside the container** unless stated: `docker compose exec backend <cmd>`.
`requirements.txt` changes in this story, so rebuild first:
`docker-compose build backend && docker-compose up -d backend` (the 1-2 trap: `./backend` is a bind
mount, so pulling a new requirement does **not** install it in an already-built container).

- [x] `python -c "import jwt; print(jwt.__version__)"` → `2.13.0`.
- [x] `pip show PyJWT | head -2` → PyJWT is installed from the pin, and `grep -n PyJWT requirements.txt`
      shows an exact `PyJWT==2.13.0` line (a **direct** pin now, not a SimpleJWT transitive — this
      closes half of the 1.1 deferred item that named this story).
- [x] `grep -rn "simplejwt" backend/organizer/auth/` → **no matches** (AC3). `requirements.txt` still
      carries `djangorestframework-simplejwt==5.5.1` — removing it is Story 1.4, not this one.
- [x] `python manage.py test organizer.tests.test_auth_tokens` → `OK`, non-zero test count.
- [x] `python manage.py test` → whole suite `OK`, exit 0, count strictly greater than the 7 tests
      story 1-2 shipped.
- [x] `python manage.py check` → `System check identified no issues (0 silenced).`
- [x] `python manage.py makemigrations --check --dry-run` → `No changes detected`, exit 0.
      **This story creates no migration.**
- [x] **Layering guard proven to bite on the new rule**: temporarily add
      `from rest_framework_simplejwt.tokens import AccessToken` to `organizer/auth/tokens.py`,
      run `python manage.py test organizer.tests.test_layering` → **fails** naming
      `auth/tokens.py:<line>`; revert. Record the failure output in Debug Log References. A guard
      never seen to fail is not a guard (the rule 1-2 established, and the defect its own review found).
- [x] **SimpleJWT-compat probe** (this is the de-risking that makes 1.4 a drop-in swap):
      ```
      python -c "
      import django; django.setup()
      from django.contrib.auth.models import User
      from rest_framework_simplejwt.tokens import RefreshToken
      from organizer.auth.tokens import verify_access_token
      u = User(pk=1, username='probe')
      print(verify_access_token(str(RefreshToken.for_user(u).access_token)))
      "
      ```
      with `DJANGO_SETTINGS_MODULE=youtube_organizer.settings` set → prints the claims dict, no
      exception. A token minted by the code running in production **today** must verify under the new
      module, or the 1.4 swap logs every live session out. Also assert this permanently in the test
      suite (see Task 4).
- [x] `curl -sk -o /dev/null -w '%{http_code}\n' https://localhost:8000/api/auth/me/` → **401**
      (unchanged — this story wires nothing into the request path).
- [x] `git diff` shows **no change** to `backend/youtube_organizer/settings.py`,
      `backend/youtube_organizer/middleware.py`, `backend/organizer/google_auth_views.py`,
      `backend/organizer/urls.py`, `backend/organizer/api/views.py`.
- [x] `coverage run manage.py test --noinput && coverage report` → the new baseline percentage is
      recorded in Completion Notes, and it is **≥ 59%** (1-2's recorded figure). `fail_under` stays
      unset — still Story 1.4.
- [x] Host-side (pre-push layer 6/6): `cd backend && POSTGRES_HOST=localhost .venv/bin/python manage.py test --noinput`
      → green. If it dies on `ModuleNotFoundError: jwt`, that is the stale-venv trap, not a code bug:
      `backend/.venv/bin/pip install -r backend/requirements.txt`. **Do not change code to satisfy a
      stale venv.**

## Tasks / Subtasks

- [x] **Task 1 — Pin PyJWT as a direct requirement (AC1)**
  - [x] Append `PyJWT==2.13.0` to `backend/requirements.txt`, keeping the file's existing
        one-pin-per-line style and exact-pin discipline (Story 1.1).
  - [x] Do **not** add the `PyJWT[crypto]` extra. HS256 is symmetric — `cryptography` is only needed
        for RS*/ES*/PS* algorithms, and pulling it in adds a heavyweight build dependency for nothing.
  - [x] Do **not** remove `djangorestframework-simplejwt==5.5.1` and do **not** edit its comment.
        It is still the live token machinery until 1.4 swaps the authentication class.
  - [x] Rebuild the image (`docker-compose build backend && docker-compose up -d backend`) before
        running anything — see the DoD note.

- [x] **Task 2 — `organizer/auth/errors.py`: the typed error hierarchy (AC2)**
  - [x] Create `backend/organizer/auth/errors.py` with a small, closed hierarchy:
        - `TokenError(Exception)` — the base every caller catches.
        - `InvalidToken(TokenError)` — malformed, tampered, wrong signature, wrong algorithm,
          missing/invalid claim, wrong `token_type`.
        - `ExpiredToken(TokenError)` — `exp` is in the past. A **separate** type, because 1.4 and the
          frontend want to distinguish "log in again" from "this token is garbage".
        - `TokenUserError(TokenError)` — the token verifies but resolves to no usable user
          (deleted, or `is_active=False`).
  - [x] Separate module, not buried in `tokens.py`, so 1.4's authentication class can
        `from organizer.auth.errors import ...` without importing token machinery.
  - [x] Module docstring stating what the layer contract permits here (match the house style set by
        the layer `__init__.py` docstrings).

- [x] **Task 3 — `organizer/auth/tokens.py`: issue + verify over PyJWT (AC1, AC2, AC3)**
  - [x] Create `backend/organizer/auth/tokens.py`. 4-space PEP 8 (new file — see the mixed-indentation
        rule in Dev Notes).
  - [x] `issue_access_token(user) -> str` — signs with `settings.SECRET_KEY`, `HS256`, and mints
        exactly the claim set in Dev Notes → "The claim set is not a free choice".
  - [x] `verify_access_token(token) -> dict` — decodes and returns the claims dict, raising only the
        typed errors from Task 2. Non-negotiables:
        - `algorithms=["HS256"]` as a **hardcoded list**. Never derive the algorithm from the token's
          own header — that is the alg-confusion / `alg: none` class of attack.
        - `options={"require": ["exp", "iat", "token_type", "user_id"]}` so a token missing a claim is
          rejected by the library, not by a later `KeyError`.
        - Reject `token_type != "access"` with `InvalidToken` (a refresh token presented as an access
          token must not authenticate).
        - Catch `jwt.ExpiredSignatureError` **before** the broader `jwt.InvalidTokenError`
          (it is a subclass — the wrong order collapses `ExpiredToken` into `InvalidToken` and AC2's
          expired path silently stops being distinguishable).
        - **No PyJWT exception may escape**, and no PyJWT type may appear in the public signature.
          The whole point is that 1.4's authentication class depends on our types, not the library's.
  - [x] `get_user_from_claims(claims) -> User` — resolves `claims["user_id"]` via
        `django.contrib.auth.get_user_model()`, raising `TokenUserError` when the user does not exist
        **or** is not active. This is what makes AC1's "round-trips back to the same user" a real
        round-trip rather than an integer comparison.
  - [x] Lifetime is `getattr(settings, "AUTH_JWT_ACCESS_LIFETIME", timedelta(days=1))` — the default
        matches both today's `SIMPLE_JWT.ACCESS_TOKEN_LIFETIME` and the cookie's `max_age=60*60*24`
        in `google_auth_views.py:146`. **Add nothing to `settings.py`**: the `getattr` default keeps
        the settings diff empty and still lets tests use `override_settings`.
  - [x] **Read that setting inside `issue_access_token`, not at module import.** A module-level
        `ACCESS_LIFETIME = getattr(settings, ...)` is evaluated once at import, which makes
        `override_settings` a silent no-op — the expired-token test then mints a *valid* token and
        fails with "no exception raised", pointing at the wrong file. Same reason `settings.SECRET_KEY`
        is read per call.
  - [x] `verify_access_token` must reject a non-`str` input (`None`, `bytes`, an int) with
        `InvalidToken` rather than a `TypeError`/`AttributeError`. 1.4 feeds it
        `request.COOKIES.get("access_token")`, which is `None` whenever the cookie is absent — the
        single most common call in the system.
  - [x] Timestamps come from `django.utils.timezone.now()` (aware UTC). Never `datetime.utcnow()`
        (deprecated since 3.12, and naive).
  - [x] No `import rest_framework` and no `import rest_framework_simplejwt` anywhere in the package
        — AC3, and Task 5 makes it permanent. (1.4 adds the one DRF import, in its own new file.)

- [x] **Task 4 — `organizer/tests/test_auth_tokens.py` (AC1, AC2)**
  - [x] `TestCase` (the DB is needed for real `User` rows), file named `test_*.py` or discovery
        silently never runs it.
  - [x] AC1: round-trip — issue for a saved user, verify, `get_user_from_claims` returns **that**
        user (assert on `pk`, not on truthiness); `exp - iat == lifetime`; `iat` is in the past-or-now;
        the header is `{"alg": "HS256", "typ": "JWT"}`; the token is three dot-separated segments.
  - [x] AC2 — one test per rejection path, each asserting the **specific** type:
        - expired → `ExpiredToken` (use `override_settings(AUTH_JWT_ACCESS_LIFETIME=timedelta(seconds=-10))`
          to mint an already-dead token; no `freezegun`, no new dependency, no `sleep`)
        - tampered payload → `InvalidToken` (flip a character in the payload segment, keep the shape)
        - wrong signing key → `InvalidToken` (sign with `jwt.encode(..., "some-other-key")`)
        - `alg: none` / unsigned → `InvalidToken`
        - algorithm substitution → `InvalidToken` (a valid HS512 token signed with the real key must
          still be rejected, because `algorithms` is a fixed list)
        - malformed garbage (`"not.a.token"`, `""`, a non-JWT string) → `InvalidToken`
        - missing a required claim → `InvalidToken`
        - `token_type: "refresh"` → `InvalidToken`
        - deleted user → `TokenUserError`
        - `is_active=False` user → `TokenUserError`
        - `None` and `b"..."` inputs → `InvalidToken` (the absent-cookie case 1.4 hits constantly)
  - [x] Every rejection test asserts the narrow type, and at least one asserts
        `isinstance(err, TokenError)` — so the base contract 1.4 catches on is pinned too.
  - [x] **SimpleJWT-compat test**: mint with `RefreshToken.for_user(user).access_token` and assert
        `verify_access_token` accepts it and resolves the same user. This test is the only place in
        the repo that may import SimpleJWT for this purpose — it lives in `tests/`, not in
        `organizer/auth/`, so AC3 and the Task 5 guard are both satisfied. Add a comment saying the
        test is **deleted by Story 1.4** along with the dependency.
  - [x] No network, no mocking of PyJWT itself (AD-16). Test the real library.

- [x] **Task 5 — Extend the AD-1 layering guard to `auth/` (AC3, permanently)**
  - [x] In `backend/organizer/tests/test_layering.py`, add an `auth` entry to `FORBIDDEN`:
        `("rest_framework_simplejwt", "organizer.api", "organizer.services", "organizer.sync", "organizer.youtube")`.
  - [x] `rest_framework_simplejwt` is the entry that turns AC3 from a one-time grep into a standing
        gate. The other four encode the `auth/` docstring's contract: authentication answers "who is
        this request", nothing more.
  - [x] **`rest_framework` itself must NOT be forbidden** — Story 1.4 puts a `BaseAuthentication`
        subclass in this package. Forbidding it here would force 1.4 to weaken the rule it inherits,
        which is exactly the failure mode the 1-2 review flagged.
  - [x] Add the corresponding cases to `test_guard_detects_a_forbidden_import` (both spellings:
        `import rest_framework_simplejwt` and `from rest_framework_simplejwt.tokens import AccessToken`)
        and to `test_guard_allows_a_legitimate_import`
        (`from rest_framework.authentication import BaseAuthentication` inside `auth`,
        `import jwt` inside `auth`). Skipping the self-test cases is precisely how the 1-2 blind spot
        survived review the first time.
  - [x] `organizer.models` is **not** forbidden in `auth/` — `get_user_from_claims` reads
        `django.contrib.auth`'s User, and reading is not the mutation AD-1 governs. Say so in a
        comment next to the entry so a later story does not "tighten" it into a false positive.

- [x] **Task 6 — Verify, measure, record**
  - [x] Walk the DoD list top to bottom in the container and tick only what you actually ran.
  - [x] Record the new coverage baseline in Completion Notes with the per-file breakdown for
        `organizer/auth/*`, and state the remaining distance to 70% so Story 1.4 inherits a true number.
  - [x] Paste the layering-guard failure output (Task 5's proof) into Debug Log References.
  - [ ] PR body: map each test file to its AC (satisfies the per-PR test rule in
        `project-context.md`), cite **AD-14** and **AD-1**, tick the applicable PR-template items and
        strike the rest (see "The PR template trap"). **No attribution trailers anywhere.**

### Review Findings

_Code review 2026-08-13. Three parallel layers (adversarial, edge-case, acceptance-audit), triaged
against the running container. 2 decisions, 7 patches, 7 deferred, 7 dismissed as noise._

- [x] [Review][Decision] _Resolved: leave the tuple as specified; recorded in `deferred-work.md` for Story 1.4, which owns the code that could write._ **AD-1's write ban is unguarded inside `auth/`** — The new `FORBIDDEN["auth"]` tuple is exactly what Task 5 specified, and the "do not tighten" comment is exactly what Task 5 asked for. But a static import guard cannot distinguish a read from a write: nothing stops Story 1.4's authentication class from doing `User.objects.filter(...).update(last_login=...)` inside `auth/`, which is the invariant the file exists to enforce. Forbidding `django.db` would block `transaction` without blocking `User.objects.update()`, so it does not close the hole either. Options: (a) leave as specified and carry a narrower rule into 1.4, (b) forbid `django.db` in `auth/` now as partial cover, (c) accept that the guard structurally cannot express AD-1 here and record it. [backend/organizer/tests/test_layering.py:22-39]
- [x] [Review][Decision] _Resolved: `verify_access_token` now normalizes `user_id` to `int`._ **`user_id` stays polymorphic for the full 1-day cookie window** — Legacy SimpleJWT cookies carry `"7"`, new tokens carry `7`. `verify_access_token` returns the raw claims dict, so any 1.4 consumer doing `claims["user_id"] == request.user.pk`, using it as a cache key, or logging it for correlation sees two behaviours across the fleet. `test_legacy_user_id_is_a_string_and_still_resolves` documents the asymmetry rather than removing it. Coercing to `int` inside `verify_access_token` is one line and eliminates the class. This is the story's own open Question 1 reaching the code. [backend/organizer/auth/tokens.py:96-100]

- [x] [Review][Patch] PyJWT exceptions outside the `InvalidTokenError` subtree escape `verify_access_token` — probe-confirmed in the container: `InvalidKeyError` subclasses `PyJWTError` directly, not `InvalidTokenError`. Breaks Task 3's "no PyJWT exception may escape" non-negotiable and turns 1.4's auth path into a 500 rather than a 401. `test_no_pyjwt_exception_escapes` only feeds inputs inside the subtree, so it is green over the gap. Fix: `except jwt.PyJWTError` as the final clause, after the narrow ones, plus a test input that reaches it [backend/organizer/auth/tokens.py:91-94]
- [x] [Review][Patch] Completion Notes' test-count breakdown is wrong — actual is 28 tests in `test_auth_tokens.py` (not 27), and `test_layering.py` gained **zero** new test methods (verified 3 before and 3 after; the diff adds sub-cases inside the two existing self-tests). The headline 7 → 35 is correct; 28 new + 7 pre-existing. The File List row repeats the 27 [_bmad-output/implementation-artifacts/1-3-first-party-pyjwt-token-issue-verify-module.md]
- [x] [Review][Patch] The rollback direction is never tested — the suite proves SimpleJWT tokens verify under the new code, but not that SimpleJWT accepts a token from `issue_access_token`. That is the direction a 1.4 rollback needs, and it is where the int-vs-str `user_id` divergence would bite. Probed in the container: SimpleJWT **does** accept our token, so this is an unpinned claim rather than a defect. Fix: one test in `SimpleJWTCompatibilityTests` [backend/organizer/tests/test_auth_tokens.py:233-280]
- [x] [Review][Patch] `deferred-work.md:19` was deferred *to this story* and was not updated — the entry still lists `PyJWT` among the floating transitives, which this story fixed, and its consequence (b) ("no pin conflict ahead rests on an unpinned transitive that loses its only requirer once 1.4 removes SimpleJWT") is now live. Fix: update the entry to record the half that closed and re-target the rest [_bmad-output/implementation-artifacts/deferred-work.md:19]
- [x] [Review][Patch] `get_user_from_claims` coerces `True` and `1.9` to pk 1 — probe-confirmed: both resolve to user 1 instead of raising `TokenUserError`, because `pk=` runs `int(value)`. Only reachable via a validly-signed token, so no privilege escalation, but it is a silent wrong-user resolution. Fix: reject `bool` and non-integral values before the query [backend/organizer/auth/tokens.py:112]
- [x] [Review][Patch] `issue_access_token` mints a signed token for a user with no pk — an unsaved `User()` or `AnonymousUser` yields `"user_id": null`, which passes `verify_access_token` in full (`require` checks claim presence, not value) and fails only one layer later. Reject at issue time [backend/organizer/auth/tokens.py:65]
- [x] [Review][Patch] `test_expiry_is_exactly_one_lifetime_after_issue` re-types `timedelta(days=1)` instead of reading the source of truth — it re-encodes the constant rather than testing it, and it fails the moment a real deployment sets `AUTH_JWT_ACCESS_LIFETIME`. Use `_access_lifetime()` [backend/organizer/tests/test_auth_tokens.py:76-78]

- [x] [Review][Defer] Access lifetime lives in three unlinked places [backend/organizer/auth/tokens.py:38] — deferred, 1.4 owns the consolidation (story Question 2)
- [x] [Review][Defer] `AUTH_JWT_ACCESS_LIFETIME` is undeclared and unvalidated [backend/organizer/auth/tokens.py:51] — deferred, pre-existing by design
- [x] [Review][Defer] The layering guard is blind to `importlib.import_module` / `__import__` [backend/organizer/tests/test_layering.py:44-66] — deferred, pre-existing from 1.2
- [x] [Review][Defer] `jti` is minted but no revocation path exists, and the gap is untracked [backend/organizer/auth/tokens.py:64] — deferred, out of scope per Dev Notes
- [x] [Review][Defer] The compat suite's "DELETED BY STORY 1.4" obligation lives only in a docstring [backend/organizer/tests/test_auth_tokens.py:233-241] — deferred, needs recording in 1.4
- [x] [Review][Defer] `get_user_from_claims`'s catch net reports genuine defects as 401 [backend/organizer/auth/tokens.py:113] — deferred, pre-existing shape
- [x] [Review][Defer] AC3's DoD grep is case-sensitive, so it cannot see the prose "SimpleJWT" mentions [_bmad-output/implementation-artifacts/1-3-first-party-pyjwt-token-issue-verify-module.md] — deferred, honestly disclosed in Completion Notes

## Dev Notes

### Scope boundary — what this story does NOT touch

This is the "tests before the swap, not after" half of the auth replacement (WORK-SPLIT § E1:
*"The auth replacement wants tests before the swap, not after"*). The module ships **unwired**.
Nothing in the request path changes; `/api/auth/me/` still returns 401 through SimpleJWT.

| File / area | This story | Owner |
| --- | --- | --- |
| `organizer/auth/tokens.py`, `errors.py` | **create** | 1.3 |
| `organizer/tests/test_auth_tokens.py` | **create** | 1.3 |
| `organizer/tests/test_layering.py` | **edit** — add the `auth` entry | 1.3 |
| `requirements.txt` | **edit** — add `PyJWT==2.13.0` only | 1.3 |
| The DRF authentication class | ✗ do not create | 1.4 |
| `settings.py` `REST_FRAMEWORK` / `SIMPLE_JWT` blocks | ✗ do not touch | 1.4 |
| `youtube_organizer/middleware.py` (retire it) | ✗ do not touch | 1.4 |
| `google_auth_views.py:132` (`RefreshToken.for_user` → `issue_access_token`) | ✗ do not touch | 1.4 |
| Removing `djangorestframework-simplejwt` from requirements | ✗ do not touch | 1.4 |
| `fail_under = 70` in `.coveragerc` | ✗ do not set | 1.4 |
| Moving `google_auth_views.py` into `api/` | ✗ do not touch | 1.4 / 6.1 |
| Refresh tokens, rotation, blocklist | ✗ out of scope entirely | — |

**Why unwired is the right shape:** the two-step exists so that the day the swap happens, the token
code it swaps to already has a green test suite behind it. Wiring here would put an untested
authentication class in the request path in the same PR that introduces the token code — the exact
sequencing the epic and the work-split were written to avoid.

**Refresh tokens are not in scope, and not a gap.** The current system mints a refresh token only as
a means to reach `refresh.access_token` (`google_auth_views.py:132-133`); nothing stores it, no
refresh endpoint exists, and the cookie carries the access token alone. Do not invent one.

### Files being modified (read before editing)

- **`backend/organizer/auth/__init__.py`** — currently a docstring only. Its stated contract:
  *"Owns: token issue and verification over PyJWT, and the DRF authentication class that reads the
  `access_token` HttpOnly cookie. Must never: contain domain logic."* This story fills in the first
  half. Leave the docstring as-is; it already describes what you are building.
- **`backend/organizer/tests/test_layering.py`** — read all 137 lines before editing. `FORBIDDEN`
  (`:15-21`) is a dict of layer → forbidden dotted-path prefixes; `_imported_modules` yields both the
  package path and each `from X import name` candidate (that submodule-candidate behaviour was a
  code-review fix — do not simplify it away). Two self-tests prove the detector still sees and still
  does not over-see. Your edit is additive: one dict entry plus cases in both self-tests.
- **`backend/requirements.txt`** — 17 exact pins, one per line, with a comment block above the
  SimpleJWT line marking it temporary. Append; do not reorder or reformat.
- **`backend/youtube_organizer/settings.py`** — read `:13-19` (the `SIMPLE_JWT` block) and `:170-177`
  (`REST_FRAMEWORK` → SimpleJWT authentication class) so you know what 1.4 replaces. **Read only.**
  `git diff` on this file must come back empty.
- **`backend/organizer/google_auth_views.py:131-148`** — the mint-and-set-cookie site. Read it to
  understand the contract your module must be compatible with (1-day cookie `max_age`, HttpOnly,
  Secure, SameSite=None). **Read only.**

### The claim set is not a free choice

Verified empirically against the running pins (SimpleJWT 5.5.1, PyJWT 2.13.0) on 2026-08-13:

```
USER_ID_CLAIM=user_id  USER_ID_FIELD=id  ALGORITHM=HS256  TOKEN_TYPE_CLAIM=token_type
JTI_CLAIM=jti  ACCESS_TOKEN_LIFETIME=1 day  SIGNING_KEY == settings.SECRET_KEY  →  True

payload: {'token_type': 'access', 'exp': 1786740837, 'iat': 1786654437,
          'jti': 'e28c05a32b824445aff26b3134580384', 'user_id': 7}
header:  {'alg': 'HS256', 'typ': 'JWT'}
```

**Mint exactly this shape.** Not for compatibility's own sake, but because AD-14 says *"the cookie
contract with the frontend is unchanged; only the backend implementation moves"* — and a live
`access_token` cookie has a **1-day** lifetime. If 1.4 swaps in a verifier that cannot read tokens
minted by the code running today, every session in flight at merge time breaks, and the failure looks
like "login is broken again" rather than "the claim names changed". Matching the shape makes the
swap genuinely hot.

- `user_id` — `user.pk` as an `int` (SimpleJWT casts to `str` only for non-int pks; this project's
  User has an integer pk, so an int it is). Do not rename it to `sub` "because that is the standard
  claim" — that is a breaking change dressed as a cleanup.
- `token_type` — the literal `"access"`.
- `iat`, `exp` — PyJWT accepts aware `datetime`s and encodes them as NumericDate integers.
- `jti` — `uuid4().hex`. Nothing consumes it yet; mint it anyway (parity, and it is the handle any
  future revocation needs). **Do not** put it in the `require` list.
- `algorithms=["HS256"]`, key `settings.SECRET_KEY`. Note `SECRET_KEY` is the hardcoded dev value
  (`settings.py:31`) — accepted under **AD-17** because nothing is deployed. Do **not** "fix" it here;
  the production envelope is deferred whole and lands as its own work.

### PyJWT specifics that bite

Pinned: **`PyJWT==2.13.0`** (released 2026-05-21, current; requires Python ≥3.9, container is 3.13).
It is already resolved in the environment as a SimpleJWT transitive — this story makes it a **direct**
pin, which is exactly what the Story 1.1 deferred item asked for ("revisit at Story 1.3, when PyJWT
becomes a first-party direct pin"). SimpleJWT 5.5.1 requires `PyJWT>=1.7.1,<3`, so there is no
conflict while both coexist.

- **Exception hierarchy:** `ExpiredSignatureError`, `InvalidSignatureError`, `DecodeError` and
  `InvalidAlgorithmError` all subclass `InvalidTokenError`. Order your `except` clauses narrow →
  broad, or `ExpiredToken` becomes unreachable and AC2's expired path is untested in practice while
  looking tested.
- **`algorithms` must be a hardcoded list.** PyJWT's own docs: *"Do not compute the `algorithms`
  parameter based on the `alg` from the token itself … either hard-code a fixed value, or configure it
  where you configure the key."* This is what makes the `alg: none` and HS-substitution tests pass.
- **`leeway`:** leave it at the default `0`. Client and server are the same machine in Phase 1
  (AD-17); a clock-skew allowance here would be cargo cult, and a non-zero leeway silently widens the
  expiry window the tests assert on.
- **`options={"require": [...]}`** works with arbitrary claim names, not only registered ones — so
  `user_id` and `token_type` belong in the list.
- `jwt.encode` returns `str` on PyJWT 2.x (it returned `bytes` on 1.x — ignore any 1.x-era snippet).

### The layering guard is your AC3 enforcement

AC3 says "without SimpleJWT imported anywhere in the module". A grep proves that once; the guard
proves it forever, for every later story that touches this package. That is why Task 5 is part of
this story rather than a nice-to-have — and it also starts closing the 1-2 review's standing
observation that *"the AD-1 guard has never run against a single real import, so its green result
carries no information"*. After this story the guard scans a package with real code in it.

Watch the trap in the opposite direction: `auth/` **must** be allowed to import `rest_framework`
(1.4 needs `BaseAuthentication`) and `jwt`. A guard entry that forbids either would be discovered by
the next story as an obstacle and "fixed" by weakening the rule.

### Testing

Standards from **AD-16** and the harness story 1-2 established:

- **No test touches the network.** Nothing here should want to, but note it anyway: no Google, no
  YouTube Data API, no real HTTP.
- Tests live in `organizer/tests/`, one `test_<subject>.py` per subject. Discovery pattern is
  `test*.py` — a file named `auth_tokens_test.py` is silently never run.
- `SimpleTestCase` for DB-free structural tests (that is what the layering guard is);
  `TestCase` when the ORM is involved (that is what this story's token tests are — they need real
  `User` rows for the round-trip and the deleted/inactive paths).
- `APITestCase` is **not** needed here — no endpoint is touched. It arrives with 1.4, where AD-16
  requires the cookie path proven end to end.
- Run: `make backend-test` (container) or `make backend-coverage` for the measured run. Host-side,
  with `make up` running: `cd backend && POSTGRES_HOST=localhost .venv/bin/python manage.py test --noinput`.
- **Coverage:** report only, no threshold. 1-2 recorded **59%** (144 statements, 56 missed, branch
  coverage on) over `organizer/` + `youtube_organizer/`. Well-tested new code should push it up;
  record the new figure. `fail_under` is Story 1.4's to turn on — `ci.yml:11`'s TODO already names
  1-4, retargeted there by 1-2. **Do not turn it on early**, and do not "help" by lowering the goal.

### Previous story intelligence (Story 1.2, merged 2026-08-13)

- **The container is the source of truth; the host venv drifts.** `backend/.venv` is one
  `pip install` behind the moment this story adds a requirement. `ModuleNotFoundError: jwt` on the
  host is a stale venv, not a code error — `backend/.venv/bin/pip install -r backend/requirements.txt`.
  This bit story 1.2 with `coverage`. Do not change code to satisfy a stale venv.
- **A new requirement needs an image rebuild.** `./backend` is bind-mounted over `/app`, so pulling a
  commit that adds a pin does **not** install it in a container built earlier. The 1-2 review found
  this on the `make backend-coverage` targets; the Makefile comment at `:16-19` records it.
- **A bare `python -c "import organizer...."` cannot work** — importing anything that reaches settings
  raises `ImproperlyConfigured`. Every probe needs `DJANGO_SETTINGS_MODULE=youtube_organizer.settings`
  and `django.setup()`. The DoD above is already written that way; keep it that way if you amend it.
- **The guard's self-test is load-bearing.** 1-2's review found `_imported_modules` blind to
  `from <pkg> import <submodule>` — the most idiomatic spelling of the violation — precisely because
  every self-test case was a form the detector already handled. When you add the `auth` entry, add
  cases in **both** spellings.
- **Mixed indentation is real and per-file.** `models/user_social_token.py` and `api/views.py` are
  **tab**-indented; `urls.py`, `settings.py`, `google_auth_views.py` and everything under `tests/` and
  the layer packages are 4-space. Your new files are 4-space PEP 8. **Never reformat a file wholesale.**
- **Two compose files.** Root `docker-compose.yml` is the real one (`make up`, `postgres:15`).
  `backend/docker-compose.yml` is a stale duplicate (`postgres:16`) that nothing invokes. Edit neither;
  do not be confused when a search hits it.
- **`AI-1` is live** (`sprint-status.yaml`): the frontend Sign-in button omits `credentials: "include"`,
  so login through the browser UI fails with `MismatchingStateError`. It is **Epic 2's**. Consequence
  for you: you cannot mint a real cookie through the UI to experiment with — use the SimpleJWT-compat
  probe in the DoD, which constructs the same token directly.
- **The per-PR test rule is now satisfiable** and this story satisfies it cleanly:
  `test_auth_tokens.py` → AC1 + AC2, the extended `test_layering.py` → AC3. Say so in the PR body.

### Git intelligence (last 5 commits)

- `5c1ba29` (merge) / `ecd5fd5` / `8a5d67c` — Story 1.2. `ecd5fd5` is a **code-review hardening pass**:
  it fixed the guard's blind spot, widened `.coveragerc` to `youtube_organizer/`, and added the `api/`
  ✗ ORM rule. The comments it left in `test_layering.py` and `.coveragerc` encode defects that were
  actually found — treat them as load-bearing documentation, not decoration.
- `7117a40` / `7aab44d` — Stories 3.5/3.6, shipped ahead of their dependencies. `ci.yml` and
  `.githooks/pre-push` are **live, working gates**; you are not expected to touch either in this story,
  and `ci.yml` already runs `coverage run manage.py test --noinput` on every push.
- Conventions the history establishes: Conventional Commit subjects with a scope
  (`feat(backend):`, `fix(backend):`, `ci:`), one squash-merge per story PR, **no attribution
  trailers anywhere**. Suggested subject here: `feat(backend): add first-party PyJWT token module`.

### Latest technical information (verified 2026-08-13)

| Item | Value | Note |
| --- | --- | --- |
| PyJWT | **2.13.0**, released 2026-05-21 | Current release; `python_requires >=3.9`, supports 3.9–3.14. Container is 3.13 ✅ |
| PyJWT extras | none | `PyJWT[crypto]` is only for asymmetric algorithms; HS256 needs no `cryptography` |
| SimpleJWT | 5.5.1 (2025-07-21), last release | Requires `PyJWT>=1.7.1,<3` — coexists with the pin above until 1.4 removes it |
| Django | 6.0.8 | `django.utils.timezone.now()` for aware UTC; `datetime.utcnow()` is deprecated since Python 3.12 |
| DRF | 3.18.0 | Not imported by this story |

### Project Structure Notes

- `organizer/auth/` does **not** shadow `django.contrib.auth` — Python 3 imports are absolute, and
  `google_auth_views.py:8`'s `from django.contrib.auth import login` is unaffected. Inside
  `organizer/`, reach the local package as `from .auth import ...` / `organizer.auth`.
- Do **not** name a module `organizer/auth/jwt.py`. Absolute imports mean `import jwt` inside it still
  resolves to PyJWT, but the ambiguity is a trap for the next reader for zero benefit. `tokens.py`.
- Python `snake_case`; test files `test_<subject>.py`; every new directory is a package with a real
  `__init__.py` (never a namespace package) — `test_skeleton.py` asserts this.
- No migration, no schema change, no settings change in this story.
- `.dockerignore` still absent and `backend/.venv` still enters the build context (deferred from 1.1).
  Not yours; just expect a slow `docker-compose build`.

### The PR template trap

`.github/pull_request_template.md` auto-applies and is still Accountr's: it instructs
`pnpm exec nx run backend:test --coverage`, cites Prisma DTOs and money-as-string, and links to
`Docs/MVPDefinition/…` paths that do not exist here. `project-context.md` requires all checklist items
ticked before merge, so it is currently impossible to satisfy honestly. **Tick what applies, strike
through the rest.** Do not rewrite the template in this PR (tracked as deferred work), and do not
silently tick items you did not do.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.3] — user story + acceptance criteria
- [Source: …/ARCHITECTURE-SPINE.md#AD-14] — cookie-borne JWT; first-party PyJWT, not SimpleJWT; the cookie contract is unchanged
- [Source: …/ARCHITECTURE-SPINE.md#AD-1] — services are the only mutation path (why `auth/` stays thin)
- [Source: …/ARCHITECTURE-SPINE.md#AD-16] — no test touches the network; `APITestCase` for endpoints; coverage 70%
- [Source: …/ARCHITECTURE-SPINE.md#AD-17] — localhost only; the hardcoded `SECRET_KEY` is accepted, not yours to fix
- [Source: …/ARCHITECTURE-SPINE.md#Stack] — `PyJWT 2.13.0` replaces djangorestframework-simplejwt
- [Source: …/WORK-SPLIT.md#E1] — "highest risk in the phase … the auth replacement wants tests before the swap, not after"
- [Source: _bmad-output/implementation-artifacts/1-2-layered-backend-package-skeleton-and-test-runner.md] — the harness, the guard, the container/venv traps, the 59% baseline
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] — "revisit at Story 1.3, when PyJWT becomes a first-party direct pin"; the guard's untested-against-real-imports status
- [Source: _bmad-output/project-context.md] — backend rules, auth invariants, testing rules, attribution ban
- [Source: Docs/CI-AND-GITHUB-GATES.md] — gate intent; coverage 70% deferred to 1-4
- [Source: CLAUDE.md] — git workflow, Conventional Commits, attribution ban, project-local memory
- [PyJWT 2.13.0 on PyPI](https://pypi.org/project/PyJWT/) — current release, Python ≥3.9
- [PyJWT API reference](https://pyjwt.readthedocs.io/en/stable/api.html) — `decode()` signature, `options`/`require`, `leeway`, the hardcoded-`algorithms` warning
- [PyJWT usage examples](https://pyjwt.readthedocs.io/en/stable/usage.html) — exp/iat handling, exception types
- [Django 6.0 testing docs](https://docs.djangoproject.com/en/6.0/topics/testing/overview/) — discovery pattern, `SimpleTestCase` vs `TestCase`

## Questions for Alexis

_Save these for after implementation — none of them blocks the work._

1. **Claim compatibility with SimpleJWT is treated as binding.** The module mints and accepts exactly
   SimpleJWT's shape (`user_id`/`token_type`/`jti`, HS256, `SECRET_KEY`) so that Story 1.4's swap does
   not invalidate the 1-day cookies in flight. The cost is inheriting a non-standard claim name
   (`user_id` rather than `sub`) essentially forever. Confirm, or say the word and 1.3 mints a clean
   claim set while 1.4 accepts both for one release.
2. **Lifetime configuration stays out of `settings.py`.** `getattr(settings, "AUTH_JWT_ACCESS_LIFETIME",
   timedelta(days=1))` keeps the settings diff empty and stays overridable in tests. Story 1.4 could
   instead introduce a proper `AUTH_JWT` settings block when it deletes the `SIMPLE_JWT` one. Fine to
   leave that consolidation to 1.4?

## Dev Agent Record

### Agent Model Used

claude-opus-5 (bmad-dev-story workflow)

### Debug Log References

**Layering-guard failure proof (Task 5 / DoD).** `from rest_framework_simplejwt.tokens import AccessToken`
was temporarily added at `organizer/auth/tokens.py:20`, then reverted:

```
FAIL: test_layers_do_not_import_upward (organizer.tests.test_layering.LayerDependencyDirectionTests.test_layers_do_not_import_upward)
AssertionError: Lists differ: ["auth/tokens.py:20 imports 'rest_framewor[55 chars]1)."] != []
First extra element 0:
"auth/tokens.py:20 imports 'rest_framework_simplejwt.tokens' — forbidden in organizer/auth/ (AD-1)."
Ran 3 tests in 0.011s
FAILED (failures=1)
```

The guard names the file and line. After reverting: `Ran 3 tests ... OK`.

**RED phase.** `test_auth_tokens.py` was written before `errors.py`/`tokens.py` existed and failed with
an import error (`Ran 1 test ... FAILED (errors=1)`) before turning green at 27 tests.

**SimpleJWT-compat probe (DoD).** Output:
`{'token_type': 'access', 'exp': 1786744043, 'iat': 1786657643, 'jti': 'aa9e79f90c87410987ae96d1c13a5eab', 'user_id': '1'}`
— no exception. Note `user_id` came back as the **string** `'1'`; see Completion Notes.

### Completion Notes List

**What shipped.** `organizer/auth/errors.py` (4-type closed hierarchy) and `organizer/auth/tokens.py`
(`issue_access_token` / `verify_access_token` / `get_user_from_claims`) over PyJWT 2.13.0, unwired —
nothing in the request path changed, and `/api/auth/me/` still answers `401` through SimpleJWT.
`PyJWT==2.13.0` is now a direct pin (closing half the Story 1.1 deferred item); SimpleJWT stays for 1.4.

**Test counts.** _(corrected during code review — the original breakdown was wrong.)_ **42 tests
total** after the review patches, up from the 7 story 1-2 shipped. **35 in `test_auth_tokens.py`**
(AC1 round-trip + claim shape, AC2 one test per rejection path asserting the narrow type, issue-time
guards, user resolution, SimpleJWT compat in both directions) + **7 pre-existing**.

`test_layering.py` gained **zero new test methods** — it has 3 before and 3 after, because the AC3
change adds `FORBIDDEN` entries and sub-cases *inside* the two existing self-tests. The original
note claimed "27 + 3 + 5"; the correct arithmetic at implementation time was 28 + 7 = 35, and 35 + 7
= 42 after review.

**⚠️ Discrepancy found against the story's Dev Notes — `user_id` is a string on the wire.**
The story recorded SimpleJWT's payload as `'user_id': 7` (int) and reasoned that "SimpleJWT casts to
`str` only for non-int pks". That is **not** true of 5.5.1: `rest_framework_simplejwt/tokens.py:228`
does `user_id = str(user_id)` **unconditionally**. So every live `access_token` cookie carries
`user_id` as a *string*. Consequences, all handled:

- Verification is unaffected — `get_user_from_claims` resolves via `User.objects.get(pk=...)`, and
  Django coerces `"7"` to `7`. Proven by the compat probe and by
  `test_legacy_user_id_is_a_string_and_still_resolves`, which asserts the type asymmetry explicitly
  so it cannot silently regress.
- We mint `user.pk` as an **int**, per the story's explicit instruction. Safe: during this story
  nothing consumes our tokens, and after the 1.4 swap only our own verifier reads them. Minting
  `str` for byte-identity was considered and rejected as inheriting a wart with no live consumer.
- `test_our_claim_shape_matches_simplejwts` compares claim **names** and the header, not value types
  — which is the contract that actually binds AD-14.
- **Resolved in code review:** `verify_access_token` now normalizes `user_id` to `int` on the way
  out, so 1.4 never sees two claim types across the fleet. The wire stays polymorphic (it must — the
  legacy cookies are already minted); the *contract* no longer is. This answers open Question 1
  below in favour of keeping the SimpleJWT claim names while normalizing the value.

**AC3 / the `simplejwt` grep.** `grep -rn "simplejwt" backend/organizer/auth/` returns **no matches**
(exit 1), and the package's only third-party import is `import jwt`. For full disclosure, two prose
mentions of "SimpleJWT" (capitalised, so outside the DoD's case-sensitive grep) remain in
`tokens.py:7` and `tokens.py:30`, documenting *why* the claim names are what they are. They import
nothing; the standing enforcement is the guard entry, not the grep.

**Coverage baseline: 71%** (198 statements, 56 missed, branch coverage on), up from 1-2's **59%**.
_(69% at implementation; the review patches added covered code and moved it to 71%.)_
Per-file for the new code:

| File | Stmts | Miss | Branch | Cover |
| --- | --- | --- | --- | --- |
| `organizer/auth/__init__.py` | 0 | 0 | 0 | 100% |
| `organizer/auth/errors.py` | 4 | 0 | 0 | 100% |
| `organizer/auth/tokens.py` | 50 | 0 | 10 | **100%** |

**The 70% gate Story 1.4 turns on is now already cleared** — 71% with `fail_under` still unset, as
specified. The remaining misses are concentrated in `google_auth_views.py` and
`youtube_organizer/middleware.py`, both of which 1.4 touches directly, so 1.4 inherits headroom
rather than a deficit. **Do not turn `fail_under` on early**; it remains 1.4's to set.

**Not done in this story (deliberate):** the PR body subtask under Task 6 is unticked because no PR
has been opened yet — the work sits on `feat/story-1-3-pyjwt-token-module`, uncommitted.

### File List

| File | Change |
| --- | --- |
| `backend/requirements.txt` | modified — added `PyJWT==2.13.0` (with a comment on the absent `[crypto]` extra) |
| `backend/organizer/auth/errors.py` | **new** — `TokenError` / `InvalidToken` / `ExpiredToken` / `TokenUserError` |
| `backend/organizer/auth/tokens.py` | **new** — issue, verify, and user resolution over PyJWT |
| `backend/organizer/tests/test_auth_tokens.py` | **new** — 35 tests covering AC1 and AC2 (28 at implementation, +7 from code review) |
| `backend/organizer/tests/test_layering.py` | modified — `auth` entry in `FORBIDDEN` + cases in both self-tests (AC3) |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | modified — story status `ready-for-dev` → `review` |
| `_bmad-output/implementation-artifacts/1-3-…-module.md` | modified — this record |

## Change Log

| Date | Change |
| --- | --- |
| 2026-08-13 | Code review — 2 decisions resolved, 7 patches applied: `except jwt.PyJWTError` final clause (InvalidKeyError escaped the net), `user_id` normalized to `int` on verify, bool/float `user_id` rejected, issue-time guard for a pk-less user, rollback-direction compat test (SimpleJWT accepts our token), lifetime test reads `_access_lifetime()`, corrected test counts and the `deferred-work.md` entry deferred to this story. Suite 35 → 42 tests, coverage 69% → 71%, `auth/tokens.py` still 100%. 7 findings deferred, 7 dismissed. |
| 2026-08-13 | Implemented — `PyJWT==2.13.0` direct pin, `organizer/auth/errors.py` + `tokens.py`, 27 token tests, AD-1 layering guard extended to `auth/` (proven to fail on a real SimpleJWT import, then reverted). Suite 7 → 35 tests, coverage 59% → 69%, `auth/*` at 100%. No settings, migration, or request-path change. Status → review. |
| 2026-08-13 | Story created — unwired first-party PyJWT issue/verify module in `organizer/auth/`, typed error hierarchy, full rejection-path test suite, SimpleJWT claim-compat probe, and the AD-1 layering guard extended to `auth/` so AC3 becomes a standing gate. AD-14, AD-1, AD-16. |
