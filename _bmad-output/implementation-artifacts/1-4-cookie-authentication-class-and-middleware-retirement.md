---
baseline_commit: 8331225
---

# Story 1.4: Cookie authentication class and middleware retirement

Status: done

Epic: 1 — Backend platform · Story key: `1-4-cookie-authentication-class-and-middleware-retirement`
Branch: `feat/story-1-4-cookie-authentication-class` → PR → `develop` (squash). Never commit to `main`/`develop`.

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want a custom DRF authentication class that reads the `access_token` cookie directly, replacing the
header-injection middleware and SimpleJWT,
so that the unchanged cookie contract is served by first-party code with no global request mutation (AD-14).

## Acceptance Criteria

**AC1 — The cookie authenticates, with no header in play**
**Given** the new authentication class registered as the default
**When** an authenticated request arrives with a valid `access_token` HttpOnly cookie
**Then** DRF resolves `request.user` from the cookie with no `Authorization` header present.

**AC2 — The old mechanism is gone, not merely bypassed**
**Given** the swap is complete
**When** I inspect the codebase
**Then** `JWTAuthCookieMiddleware`'s header injection is removed and `djangorestframework-simplejwt`
is absent from `requirements.txt` and imports.

**AC3 — The cross-port contract is untouched, and proven end to end**
**Given** the cross-port setup
**When** the auth flow runs
**Then** `CORS_ALLOW_CREDENTIALS`, the single allowed origin, and `SameSite=None; Secure` are
unchanged (NFR-9), and an `APITestCase` proves login → authenticated request over the cookie path
end to end (AD-16).

### Definition of Done (verifiable, no self-reporting)

Every command runs **inside the container** unless stated: `docker compose exec backend <cmd>`.
`requirements.txt` changes in this story (a **removal**), so rebuild first:
`docker-compose build backend && docker-compose up -d backend`. A removal is the one case where the
bind mount lies in the *dangerous* direction: the old package stays installed in a container built
earlier, so `import rest_framework_simplejwt` keeps working and a stale container will happily run
code that CI cannot. **Rebuild, or every SimpleJWT check in this list is meaningless.**

- [x] `python -c "import rest_framework_simplejwt"` → `ModuleNotFoundError` (after the rebuild).
      If it succeeds, you are on a stale image — stop and rebuild.
- ~~`grep -rni "simplejwt" backend/organizer/ backend/youtube_organizer/ backend/requirements.txt`
      → **no matches** (AC2).~~ **STRUCK — unsatisfiable as written, see Completion Note 2.** Task 7
      of this same story requires `FORBIDDEN["auth"]` to keep the literal
      `"rest_framework_simplejwt"`, so a repo-wide text scan can never return zero (it returns 19).
      Replaced by two checks that *are* satisfiable: `requirements.txt` scanned case-insensitively,
      and an AST import walk over both packages
      (`test_cookie_authentication.py::test_nothing_under_either_package_imports_the_retired_library`).
- [x] `test -f backend/youtube_organizer/middleware.py` → **false**; `grep -n JWTAuthCookieMiddleware -r backend/`
      → no matches (AC2).
- [x] `python manage.py check` → `System check identified no issues (0 silenced).`
- [x] `python manage.py makemigrations --check --dry-run` → `No changes detected`, exit 0.
      **This story creates no migration.**
- [x] `python manage.py test` → whole suite `OK`, exit 0. Record the count; it is **42 minus the 4
      deleted compat tests plus the new ones** — state the arithmetic, do not round it.
- [x] `curl -sk -o /dev/null -w '%{http_code}\n' https://localhost:8000/api/auth/me/` → **401**
      (unchanged). **`-w '%{http_code}'` alone is not enough here** — also run
      `curl -skI https://localhost:8000/api/auth/me/ | grep -i www-authenticate` and confirm the
      header is present. A missing `authenticate_header` silently turns this into **403**, which is
      the single most likely way to ship this story broken (see Dev Notes → "The 401→403 trap").
- [x] `curl -sk -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer <a valid token>" https://localhost:8000/api/auth/me/`
      → **401**. Header auth is *gone*, deliberately. Mint the token with
      `python -c "…; print(issue_access_token(User.objects.first()))"` under
      `DJANGO_SETTINGS_MODULE=youtube_organizer.settings` + `django.setup()`.
- [x] `curl -sk -o /dev/null -w '%{http_code}\n' --cookie "access_token=<that same token>" https://localhost:8000/api/auth/me/`
      → **200**, and the body carries the user's `username`/`email`. This is AC1 by hand.
- [x] `curl -sk -o /dev/null -w '%{http_code}\n' https://localhost:8000/api/auth/google/` → **200**
      (the OAuth entry point stays public; it is the one view that must survive the
      default-permission change).
- [x] `git diff backend/youtube_organizer/settings.py` shows changes **only** to: the `SIMPLE_JWT`
      block (deleted, replaced by `AUTH_JWT_ACCESS_LIFETIME`), the `MIDDLEWARE` list (one line
      removed), and `REST_FRAMEWORK`. **`CORS_ALLOWED_ORIGINS`, `CORS_ALLOW_CREDENTIALS`,
      `SESSION_COOKIE_SAMESITE`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SAMESITE`,
      `CSRF_COOKIE_SECURE` must be byte-identical** (AC3, NFR-9). Assert it in the diff, and the
      test suite asserts it permanently.
- [x] **Layering guard proven to bite on the new rule**: temporarily add
      `get_user_model().objects.filter(pk=1).update(last_login=None)` inside
      `organizer/auth/authentication.py`, run `python manage.py test organizer.tests.test_layering`
      → **fails** naming `auth/authentication.py:<line>`; revert. Paste the failure into Debug Log
      References. A guard never seen to fail is not a guard (the standing rule since 1.2).
- [x] `coverage run manage.py test --noinput && coverage report` → exits **0** with
      `fail_under = 70` set in `.coveragerc`. Record the figure. Then temporarily set
      `fail_under = 99`, re-run, confirm it **exits non-zero**, and revert — same principle as the
      layering guard: an unproven threshold is decoration.
- [x] `pip check` → `No broken requirements found.` after the SimpleJWT removal, and record what
      `pip list` says about `cryptography` (see Dev Notes → "What the removal drags out with it").
- [x] Host-side (pre-push layer 6/6): `cd backend && POSTGRES_HOST=localhost .venv/bin/python manage.py test --noinput`
      → green. If it dies on a stale `rest_framework_simplejwt` still being importable, that is the
      host venv lagging, not a code bug — the tests must not depend on the package's absence at
      import time (they assert on repo *text*; see Task 6). **Run directly, not via an actual push:
      the hook fires on `git push`, which has not happened — the branch is still uncommitted.**

## Tasks / Subtasks

- [x] **Task 1 — `organizer/auth/authentication.py`: the DRF authentication class (AC1)**
  - [x] Create `backend/organizer/auth/authentication.py`. 4-space PEP 8 (new file).
  - [x] `class CookieJWTAuthentication(BaseAuthentication)` from
        `rest_framework.authentication`. This is the **one** DRF import the `auth/` layer is allowed
        (1.3 Task 5 deliberately left `rest_framework` out of `FORBIDDEN["auth"]` for exactly this).
  - [x] `authenticate(self, request)`:
        - `token = request.COOKIES.get("access_token")`
        - **`if not token: return None`** — not `raise`. Returning `None` means "this authenticator
          has no opinion", which is what lets `AllowAny` views stay public and lets the
          *permission* layer produce the 401. Raising here would 401 the OAuth entry point and
          break login before it starts.
        - `claims = verify_access_token(token)` → `user = get_user_from_claims(claims)` →
          `return (user, token)`. The second element becomes `request.auth`; return the raw token
          string (SimpleJWT returned its token object — nothing in this repo reads `request.auth`,
          so the string is the honest minimum).
        - Translate the typed errors from `organizer.auth.errors`, narrow → broad, each with its
          own `code` so the frontend can distinguish them later:
          `ExpiredToken` → `AuthenticationFailed("token has expired", code="token_expired")`;
          `TokenUserError` → `…("user is unavailable", code="user_unavailable")`;
          `InvalidToken` → `…("token is invalid", code="token_invalid")`.
          Catch `TokenError` last as a backstop → `token_invalid`. **Order matters** —
          `ExpiredToken`/`InvalidToken`/`TokenUserError` are siblings, but `TokenError` is their
          base, so listing it first swallows all three.
        - **Never let an untyped exception through.** `verify_access_token` already guarantees no
          PyJWT type escapes; do not re-wrap `Exception` — a genuine defect owes a 500, not a 401
          (this is the deferred-work item about the catch-net reporting defects as 401; do not
          widen it here).
  - [x] **`authenticate_header(self, request)` returning `'Bearer realm="api"'` — non-negotiable.**
        See Dev Notes → "The 401→403 trap". Without it every unauthenticated response becomes 403
        and the frontend's session probe stops meaning what it means today.
  - [x] **Write nothing.** No `user.last_login` update, no `save()`, no `objects.update()`. AD-1
        makes `services/` the only writer, and Task 7 turns that from prose into a test.
  - [x] Module docstring in the house style set by `auth/__init__.py`, `errors.py` and `tokens.py`:
        what it owns, what it must never do, and the AD ids.

- [x] **Task 2 — Settings: register the class, retire the middleware, declare the lifetime (AC1, AC2, AC3)**
  - [x] `REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']` →
        `('organizer.auth.authentication.CookieJWTAuthentication',)`, exactly one entry. Do **not**
        add `SessionAuthentication` "for the browsable API": it enforces CSRF on unsafe methods and
        would change the contract this story is sworn not to change.
  - [x] Add `'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',)` and mark
        `GoogleAuthInitView` with an explicit `permission_classes = [AllowAny]`. AD-14: *"Views
        default to authenticated; `AllowAny` is explicit and justified."* Today only
        `GoogleAuthInitView` relies on DRF's implicit `AllowAny` default — the callback view is
        already explicit, and `MeView`/`YouTubePlaylistsView` are already `IsAuthenticated`, so
        this is a four-endpoint change with a provable outcome (see the table in Dev Notes) rather
        than an open-ended sweep. **Add a test per endpoint** so the intent survives.
  - [x] Delete the `SIMPLE_JWT` block (`settings.py:13-19`) **including its comment**, and delete the
        now-unused `from datetime import timedelta` only if nothing else needs it — the next bullet
        needs it, so it stays. Keep the import where it is; do not reorder the file.
  - [x] Declare `AUTH_JWT_ACCESS_LIFETIME = timedelta(days=1)` with a comment stating that
        `organizer/auth/tokens.py` and the login cookie's `max_age` both read it, and that changing
        it changes both. This closes the deferred-work item *"Access lifetime lives in three
        unlinked places"*, which names this story as its owner.
  - [x] Remove `'youtube_organizer.middleware.JWTAuthCookieMiddleware'` from `MIDDLEWARE` and its
        two comment lines. Leave every other middleware, in order — `SessionMiddleware` and
        `AuthenticationMiddleware` both stay (the OAuth callback calls `login()`, and `MeView`
        reads `request.session['profile_picture']`).
  - [x] Touch **nothing** in the CORS / cookie block (`:80-89`). AC3 and NFR-9.

- [x] **Task 3 — Delete `youtube_organizer/middleware.py` (AC2)**
  - [x] `git rm backend/youtube_organizer/middleware.py`. Delete the file; do not leave an empty
        module or a commented-out class. The whole point of AD-14's retirement clause is that the
        global request mutation is *gone*, not disabled.
  - [x] Update the comment in `backend/.coveragerc:2-5`, which cites `middleware.py` as a reason the
        `youtube_organizer/` package is measured. The reason still holds (`settings.py`, project
        `urls.py`), but the example is now a file that does not exist.

- [x] **Task 4 — Mint with first-party code at the one mint site (AC1, AC2)**
  - [x] `backend/organizer/google_auth_views.py`: delete `from rest_framework_simplejwt.tokens import RefreshToken`
        (`:14`) and its `# JWT imports` comment; import `from .auth.tokens import issue_access_token`.
  - [x] Replace `:131-133` (`refresh = RefreshToken.for_user(user)` / `access_token = str(refresh.access_token)`)
        with `access_token = issue_access_token(user)`. One line, one call. Keep the numbered
        step comments; renumber nothing else.
  - [x] `:146` — `max_age=int(settings.AUTH_JWT_ACCESS_LIFETIME.total_seconds())` instead of the
        hardcoded `60*60*24`, with `from django.conf import settings` added to the imports. The
        cookie and the token now expire from one source. **Everything else in the `set_cookie` call
        — `httponly=True`, `secure=True`, `samesite='None'`, `key='access_token'` — is byte-identical.**
        That is the contract AD-14 says does not move.
  - [x] This file is **not** inside a scanned layer directory, so the layering guard has no opinion
        about it. Importing `organizer.auth` from it is correct and intended (`api → auth` points
        downward). Its pre-existing AD-1 violations (inline YouTube client, direct `UserSocialToken`
        write) are recorded in `deferred-work.md` and belong to 6.1 — **do not fix them here**.

- [x] **Task 5 — Drop the dependency (AC2)**
  - [x] `backend/requirements.txt`: delete `djangorestframework-simplejwt==5.5.1` **and** the
        two-line `# TEMPORARY — removed in Story 1.4 …` comment above it (`:5-7`). That comment was
        written as a promissory note to this story; leaving it behind is the giveaway that the swap
        was half-done.
  - [x] Rebuild the image before running anything else (`docker-compose build backend && docker-compose up -d backend`).
        A removal does **not** uninstall itself from a container built earlier.
  - [x] Run `pip check` and record what happened to `cryptography` — see Dev Notes → "What the
        removal drags out with it". If the environment changed in a way `requirements.txt` does not
        describe, say so in Completion Notes and add it to `deferred-work.md` rather than pinning a
        new transitive on the way past (that is the lockfile item, still deferred).

- [x] **Task 6 — Retire the compat suite without losing what it proved (AC2)**
  - [x] Delete `class SimpleJWTCompatibilityTests` from `backend/organizer/tests/test_auth_tokens.py`
        (`:297-361`). Its docstring says "DELETED BY STORY 1.4"; this is that deletion. All three
        SimpleJWT imports are function-level, so leaving the class behind yields cryptic per-test
        `ModuleNotFoundError`s rather than one obvious failure — delete the whole class, not the
        imports.
  - [x] **Do not delete what it was protecting.** Keep the legacy-shape coverage by hand-minting the
        SimpleJWT wire format with PyJWT — a payload with `user_id` as the **string** `str(user.pk)`,
        `token_type: "access"`, `jti`, `iat`/`exp`, signed HS256 with `settings.SECRET_KEY`. Assert
        `verify_access_token` normalizes it to `int` and `get_user_from_claims` resolves the same
        user. Live cookies minted by the old code stay valid for a full day after merge; this is the
        test that says so, and it now costs no dependency.
  - [x] Add a comment on the replacement test explaining *why* a hand-built token is used, so a
        later reader does not "simplify" it into `issue_access_token`, which mints the int form and
        would test nothing.
  - [x] Check `_decode_segment` and any other module-level helper is still used after the deletion;
        remove it only if it is genuinely orphaned (it is used by the claim-shape tests — expect it
        to stay).

- [x] **Task 7 — Extend the AD-1 guard to catch writes inside `auth/` (AD-1)**
  - [x] `deferred-work.md:71` names **this story** as the owner: the import-based guard structurally
        cannot express AD-1's write ban, and this is the story that adds the code that could write.
        Implement the option that decision recommended — an AST rule over call sites, not imports.
  - [x] In `backend/organizer/tests/test_layering.py`, add a second check that walks `organizer/auth/`
        and flags ORM-write call sites:
        - any `.save(...)` or `.delete(...)` call, and
        - `.create/.get_or_create/.update_or_create/.bulk_create/.bulk_update/.update` **only when
          the receiver chain contains `objects`, `filter`, `exclude` or `all`**.
        The receiver condition is load-bearing: an unconditional `.update()` rule flags
        `dict.update()` and `claims.update()`, and the first false positive is "fixed" by deleting
        the rule. Say that in a comment.
  - [x] Self-test it in **both** directions, in the style the 1.2 review established:
        `User.objects.filter(pk=1).update(last_login=None)`, `user.save()`, `obj.delete()` → flagged;
        `claims.update({"x": 1})`, `headers.update(...)`, `set().update(...)`,
        `user_model.objects.get(pk=1)` (a **read**) → not flagged. Skipping the negative cases is
        precisely how the 1.2 blind spot survived its first review.
  - [x] Keep `FORBIDDEN["auth"]` exactly as 1.3 left it, minus nothing — including
        `rest_framework_simplejwt`. The package is gone from requirements, but the guard entry is
        what stops a later story reintroducing it, and it costs nothing.

- [x] **Task 8 — `organizer/tests/test_cookie_authentication.py`: the end-to-end proof (AC1, AC3)**
  - [x] New file, `APITestCase` (`rest_framework.test`) — AD-16 requires the cookie path proven end
        to end, and this is the story that owes it. Set the cookie with
        `self.client.cookies["access_token"] = issue_access_token(self.user)`.
  - [x] **AC1 — the golden path.** `GET /api/auth/me/` with the cookie → `200`, body carries the
        user's `username` and `email`. Assert **no `Authorization` header is involved**: the
        strongest form is a small probe — assert `response.wsgi_request.META` has no
        `HTTP_AUTHORIZATION` key inside the request cycle, plus the settings assertion in the next
        bullet. Do not settle for "the response was 200"; that is also true of the old middleware.
  - [x] **AC2 as a standing gate, asserted over repo text** (a `SimpleTestCase`, no DB):
        - `'youtube_organizer.middleware.JWTAuthCookieMiddleware'` not in `settings.MIDDLEWARE`, and
          `youtube_organizer/middleware.py` does not exist on disk;
        - `settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] == ('organizer.auth.authentication.CookieJWTAuthentication',)`;
        - a case-insensitive scan of `backend/requirements.txt` and every `.py` under `organizer/`
          and `youtube_organizer/` finds no `simplejwt`.
        **Text assertions, not `import rest_framework_simplejwt` + `assertRaises`** — the host venv
        keeps the package installed until someone re-runs `pip install`, and a test that depends on
        an uninstall passes and fails for environmental reasons.
  - [x] **AC3 — the contract that must not move.** Assert `CORS_ALLOW_CREDENTIALS is True`,
        `CORS_ALLOWED_ORIGINS == ["https://localhost:3000"]`,
        `SESSION_COOKIE_SAMESITE == CSRF_COOKIE_SAMESITE == "None"`, and both `*_SECURE` are `True`.
        NFR-9 in executable form: the next story that "cleans up settings" gets a red test, not a
        broken login.
  - [x] **AC3 — login → authenticated request, end to end.** Drive `GoogleAuthCallbackView` with the
        Google side faked at the boundary (`unittest.mock.patch` over the `Flow` and the
        `requests.get` userinfo call in `organizer.google_auth_views` — **no network**, AD-16), then
        assert: the response sets an `access_token` cookie that is `HttpOnly`, `Secure`,
        `SameSite=None`, with `max-age == int(settings.AUTH_JWT_ACCESS_LIFETIME.total_seconds())`;
        and feeding **that exact cookie value** back into `GET /api/auth/me/` returns `200` for the
        same user. That round trip — mint by the login view, consume by the authentication class —
        is the sentence AC3 actually asks for, and no smaller test covers it.
        *If faking `Flow` proves disproportionate, the fallback is to assert the cookie attributes
        against `issue_access_token`'s output directly and record in Completion Notes that the
        callback's own wiring is covered by the manual `curl` DoD step instead — but try the fake
        first; `google_auth_views.py` is the largest uncovered block in the coverage report and
        Task 9 needs the headroom.*
  - [x] **Rejection paths, each asserting `401` and not `403`:**
        no cookie · expired cookie (mint under `override_settings(AUTH_JWT_ACCESS_LIFETIME=timedelta(seconds=-10))`)
        · tampered cookie · cookie signed with another key · deleted user · `is_active=False` user
        · empty-string cookie · a valid token sent as `Authorization: Bearer …` with **no** cookie.
        That last one is the regression test for the retirement itself: header auth must be dead.
  - [x] At least one rejection test asserts the `WWW-Authenticate` header is present on the 401
        response. That header is the *mechanism* by which the status is 401 — assert the mechanism,
        not just its current effect.
  - [x] **Per-endpoint permission table**, one assertion each (Task 2's change):
        `/api/auth/google/` → 200 without a cookie · `/api/auth/me/` → 401 without · 200 with ·
        `/api/youtube/playlists/` → 401 without. Do not call the playlists endpoint *with* a valid
        cookie — it builds a real YouTube client (AD-16). 401-without is the whole assertion.
  - [x] No network anywhere. No mocking of PyJWT or of the authentication class itself — test the
        real path through DRF.

- [x] **Task 9 — Turn the 70% coverage gate on (NFR-13)**
  - [x] Measure first: `coverage run manage.py test --noinput && coverage report`. 1.3 recorded
        **71%**. Removing `middleware.py` and adding covered code should raise it; the callback test
        in Task 8 is where the real headroom is.
  - [x] Add `fail_under = 70` under `[report]` in `backend/.coveragerc`, with a comment citing
        NFR-13 and `Docs/CI-AND-GITHUB-GATES.md`. **70, not the measured number** — a ratchet pinned
        to today's figure fails the next honest refactor, and the gate's stated intent is 70.
  - [x] Prove it bites (`fail_under = 99` → non-zero exit → revert). DoD.
  - [x] Delete the `TODO(story 1-4)` block from `.github/workflows/ci.yml:11-15` — the header
        comment lists TODOs "each waiting on the story that creates its tooling", and this is that
        story. Leave 2-5, 3-4 and AD-17 exactly as they are. `coverage report` in the test job needs
        no change: it already exits non-zero when `fail_under` is missed.
  - [x] Update the Makefile comment at `:13-14` ("the 70% threshold (NFR-13) is not enforced yet —
        see … story 1-4") — it is enforced now, by `.coveragerc`.
  - [x] If 70% turns out to be genuinely unreachable, **do not lower the number and do not stub the
        gate.** Stop, record the measured figure and the uncovered surface in Completion Notes, and
        raise it — the standing instruction since 1.2 is that a threshold nothing can meet is worse
        than no threshold.

- [x] **Task 10 — Verify, record, close the deferred items this story owns**
  - [x] Walk the DoD top to bottom in the container and tick only what you actually ran.
  - [x] Update `_bmad-output/implementation-artifacts/deferred-work.md`: mark **closed** the entries
        this story resolves — access lifetime in three places (Task 2), `AUTH_JWT_ACCESS_LIFETIME`
        undeclared/unvalidated (Task 2 + the `_access_lifetime` guard), the compat suite's removal
        obligation (Task 6), AD-1's write ban inside `auth/` (Task 7). Re-target what remains: the
        transitive-closure/lockfile item (whatever `pip check` reveals), the `get_user_from_claims`
        catch-net (now has a real call site — record what 1.4 learned about which failures are
        genuinely client-caused), and `google_auth_views.py`'s own AD-1 violations (→ 6.1).
  - [x] **New deferred item to raise: CSRF.** Cookie-borne auth with no CSRF check means any
        state-changing endpoint is CSRF-exposed — SimpleJWT-via-header was accidentally immune,
        because a cross-site form cannot set an `Authorization` header, and reading the cookie
        directly removes that accident. There are **no** unsafe-method API endpoints today, so
        nothing is exploitable now; Epic 9 (mutation API) is where it becomes live. Record it with
        that framing — this story creates the exposure surface even though it creates no exploit.
  - [x] Record the new coverage figure with the per-file breakdown for `organizer/auth/*` and
        `organizer/google_auth_views.py`, and the test-count arithmetic.
  - [ ] PR body: map each test file to its AC (the per-PR test rule in `project-context.md`), cite
        **AD-14**, **AD-1**, **AD-16** and **NFR-13**, tick the applicable PR-template items and
        strike the rest (see "The PR template trap"). **No attribution trailers anywhere.**
        *Still open at code-review time — the branch is uncommitted and no PR exists yet.*

### Review Findings

_Code review, 2026-08-14. Three layers (adversarial, edge-case, acceptance-audit), run against the
working tree at baseline `8331225`. The behaviour under AC1/AC2/AC3 was verified live in the
container — 87 tests green, coverage 90%, `curl` returning 401 with `WWW-Authenticate` and 200 on the
cookie path — so nothing below disputes that the story works. What follows is what the layers found
around it._

**Patches** — all 19 applied and verified: `manage.py check` clean, **93 tests OK** (87 + 6 added by
this pass), coverage **90.12%** with `fail_under = 70` exiting 0.

_The first two were raised as decisions and resolved by Alexis during the review._

- [x] [Review][Patch] **[resolved decision — comments corrected, hook left alone]** The 70% gate is not enforced by the pre-push hook, but two shipped comments say it is — `.coveragerc:22-24` ("which is what fails CI and the pre-push hook — no separate step needed") and `Makefile:13-15` ("here, in CI and in the pre-push hook alike"). `.githooks/pre-push:145` runs `"$PY" manage.py test --noinput` bare; `coverage` is never invoked. CI is genuinely gated. **Fix: correct both comments to say CI-only.** Adding `coverage` to the hook was considered and rejected — it slows every push and would import the hook's skip paths into the gate [backend/.coveragerc:22, Makefile:13]
- [x] [Review][Patch] **[resolved decision — keep the fallback, share one resolver]** `AUTH_JWT_ACCESS_LIFETIME` has three different contracts across three files. `organizer/auth/tokens.py:65` keeps `getattr(settings, ..., DEFAULT_ACCESS_LIFETIME)` and calls the setting optional; `organizer/google_auth_views.py:152` reads `settings.AUTH_JWT_ACCESS_LIFETIME` bare (an `AttributeError`/500 mid-callback if absent); `organizer/checks.py:23` treats absence as `organizer.E001`. **Fix: keep the `getattr` fallback and route the mint site through the same resolver** (promoting `_access_lifetime` to a public name, since it now has a caller outside its module), so the cookie's `max_age` and the token's `exp` cannot diverge even when the setting is absent. Correct the "one source of truth" comment at `google_auth_views.py:150-151`, which is false while `DEFAULT_ACCESS_LIFETIME` remains a second copy of the number, and add the missing test for the fallback branch [backend/organizer/google_auth_views.py:152, backend/organizer/auth/tokens.py:45]

- [x] [Review][Patch] `Docs/CI-AND-GITHUB-GATES.md` — declared authoritative by `CLAUDE.md` — still says the backend `fail_under` is deferred to story 1-4 [Docs/CI-AND-GITHUB-GATES.md:39-41]
- [x] [Review][Patch] `project-context.md` still documents SimpleJWT and `JWTAuthCookieMiddleware` as the live auth mechanism, including the testing rule "authenticate via SimpleJWT, since `JWTAuthCookieMiddleware` is what populates the auth header" [_bmad-output/project-context.md:112-116, 153-154]
- [x] [Review][Patch] The AD-1 write guard is blind to Django 6's async ORM — `asave`/`adelete`/`acreate`/`aget_or_create`/`aupdate_or_create`/`abulk_create`/`abulk_update`/`aupdate` all pass. `await user.asave()` inside `organizer/auth/` is the most plausible future violation on this stack, and it is exactly the 1.2 failure mode (self-tests enumerating only forms the detector already handles) repeating in the new detector [backend/organizer/tests/test_layering.py:88-105]
- [x] [Review][Patch] Nothing asserts the system check is registered — every test calls `check_access_token_lifetime(None)` directly. Delete the `register(...)` call and the suite stays green while the only enforcement of the non-positive-lifetime rule disappears; `apps.py` reports 100% coverage, so coverage will not catch it either [backend/organizer/apps.py:15]
- [x] [Review][Patch] The write guard misses a queryset held in a local — `qs = User.objects.filter(...)` then `qs.update(...)` yields a receiver chain of `qs` alone, which matches no `QUERYSET_MARKERS`. The comment defends the receiver condition at length as anti-false-positive without acknowledging the false negative it buys [backend/organizer/tests/test_layering.py:141]
- [x] [Review][Patch] `organizer/checks.py` docstring claims "`manage.py check` is a CI job step" — `ci.yml`'s test job runs `makemigrations --check`, `migrate`, `coverage run manage.py test`, `coverage report` and no `check`. `E001` is still enforced in CI, but implicitly, via Django's system checks inside those commands [backend/organizer/checks.py:3-4]
- [x] [Review][Patch] The default-permission change is asserted only against `settings.REST_FRAMEWORK`, never behaviourally. Its stated benefit — "a view that forgets `permission_classes` now gets a locked endpoint" — has no test, because every existing view declares its own. A throwaway `APIView` asserting 401 would turn the claim into a gate [backend/organizer/tests/test_cookie_authentication.py:150]
- [x] [Review][Patch] `ci.yml`'s `Run tests` comment still reads "The report is informational — see the threshold TODO at the top of this file" — this same diff deleted that TODO, and the report is no longer informational [.github/workflows/ci.yml:135-137]
- [x] [Review][Patch] DoD item 2 is ticked `[x]` for a check Completion Note 2 of the same story calls unsatisfiable (the grep returns 19 matches). The host-side pre-push line and Task 10's PR subtask are likewise ticked for work that cannot have happened on an uncommitted tree. Strike them rather than tick them — "verifiable, no self-reporting" is the DoD's own header [_bmad-output/implementation-artifacts/1-4-cookie-authentication-class-and-middleware-retirement.md:52, 93, 325]
- [x] [Review][Patch] `organizer.E001` bounds the lifetime only below zero. `timedelta(milliseconds=500)` passes and yields `max_age=0` (browser drops the cookie); a value near `timedelta.max` passes and yields `OverflowError` on `now + lifetime` at login [backend/organizer/checks.py:24]
- [x] [Review][Patch] `COOKIE_NAME` is declared in `authentication.py` with the comment "Changing this name breaks every live session", but the sole mint site writes `key='access_token'` as a bare literal — the one place the constant would earn its keep does not import it [backend/organizer/google_auth_views.py:145]
- [x] [Review][Patch] `LayerWriteBanTests`' docstring claims "AD-1: `organizer.services` is the only writer of application state" while `WRITE_SCANNED_LAYERS = ("auth",)` scans one directory — `api/`, `youtube/`, `sync/` and `google_auth_views.py` (which really does call `objects.update_or_create`) are outside it [backend/organizer/tests/test_layering.py:85]
- [x] [Review][Patch] `EndpointPermissionTests`' docstring promises "four endpoints … and a test each" and describes "one intended behavioural change (none)"; three endpoints are tested, and the one endpoint that did change (`GoogleAuthInitView`, previously implicitly `AllowAny`) is not identified [backend/organizer/tests/test_cookie_authentication.py:390]
- [x] [Review][Patch] `coverage` runs at default `precision = 0`, so a total of 69.6% renders as `70` and passes the gate it should fail. `precision = 2` under `[report]` closes it [backend/.coveragerc:19]
- [x] [Review][Patch] Deviation 1 discloses `organizer/checks.py` as the one file added outside the story's scope table; `organizer/apps.py` was also modified (new `ready()` + `register(...)`) and is equally absent from that table [_bmad-output/implementation-artifacts/1-4-cookie-authentication-class-and-middleware-retirement.md:683]
- [x] [Review][Patch] `sprint-status.yaml`'s mirrored header comment says `# last_updated: 2026-08-13T21:30:00-0400` while the actual key is set to `2026-08-14T00:00:00-0400` [_bmad-output/implementation-artifacts/sprint-status.yaml:66]
- [x] [Review][Patch] The deferred-work entry raised about the DoD grep calls the AST scan "strictly stronger than the grep it replaces" — it is not, for the dynamic-import case (`importlib.import_module("rest_framework_simplejwt")`), which the same file already tracks as a known blind spot in the import guard. That blind spot now covers two gates and the entry was not updated to say so [_bmad-output/implementation-artifacts/deferred-work.md]

**Deferred**

- [x] [Review][Defer] `SECRET_KEY` is hardcoded in the repo, and this story makes it the sole thing standing between an attacker and a forged `access_token` for an arbitrary `user_id` [backend/youtube_organizer/settings.py:32] — deferred, pre-existing (AD-17)
- [x] [Review][Defer] No logout or revocation path: `jti` is minted but never consumed, and a rejected `access_token` cookie is left in the browser to be re-sent for the remainder of its day [backend/organizer/auth/tokens.py] — deferred, pre-existing
- [x] [Review][Defer] A misconfigured lifetime fails the login path only after side effects have landed — `login()` and `UserSocialToken.objects.update_or_create(...)` run before `issue_access_token()` can raise [backend/organizer/google_auth_views.py:117-133] — deferred, pre-existing
- [x] [Review][Defer] `.githooks/pre-push` exits 0 and skips the backend test layer entirely when the DB probe fails, so a push can proceed with neither the suite nor the coverage gate [.githooks/pre-push:151] — deferred, pre-existing (story 3-6 design)
- [x] [Review][Defer] `request.auth` carries the raw JWT string, putting a live one-day credential into DRF's exception and logging context [backend/organizer/auth/authentication.py:66] — deferred, pre-existing pattern
- [x] [Review][Defer] The `except TokenError` backstop is unreachable while the hierarchy has three leaves, and fails in the wrong direction: a future subclass would be silently laundered into a generic `token_invalid` 401 rather than failing loudly [backend/organizer/auth/authentication.py:60-64] — deferred, deliberate as documented

## Dev Notes

### Scope boundary — what this story does NOT touch

This is the "swap" half of the auth replacement. 1.3 shipped the token module unwired with a green
suite behind it precisely so this story could be a wiring change (WORK-SPLIT § E1: *"the auth
replacement wants tests before the swap, not after"*). **You are not writing token logic here** —
`issue_access_token` / `verify_access_token` / `get_user_from_claims` exist, are 100% covered, and
have already been probe-verified against tokens minted by the code running today.

| File / area | This story | Owner |
| --- | --- | --- |
| `organizer/auth/authentication.py` | **create** | 1.4 |
| `organizer/tests/test_cookie_authentication.py` | **create** | 1.4 |
| `youtube_organizer/settings.py` (REST_FRAMEWORK, MIDDLEWARE, SIMPLE_JWT→AUTH_JWT) | **edit** | 1.4 |
| `youtube_organizer/middleware.py` | **delete** | 1.4 |
| `organizer/google_auth_views.py` — mint site + cookie `max_age` only | **edit** | 1.4 |
| `requirements.txt` — remove SimpleJWT + its comment | **edit** | 1.4 |
| `organizer/tests/test_auth_tokens.py` — delete the compat class, keep the legacy-shape proof | **edit** | 1.4 |
| `organizer/tests/test_layering.py` — the write-guard | **edit** | 1.4 |
| `.coveragerc` `fail_under = 70`, `ci.yml` TODO, Makefile comment | **edit** | 1.4 |
| `organizer/auth/tokens.py` — logic changes | ✗ do not touch (except the `_access_lifetime` validation guard, Task 2) | 1.3 shipped it |
| Refresh tokens, rotation, blocklist, `jti` revocation | ✗ out of scope entirely | — |
| Moving `google_auth_views.py` into `api/`, its inline YouTube client, its direct `UserSocialToken` write | ✗ do not touch | 6.1 |
| The frontend `credentials: "include"` bug (AI-1) | ✗ do not touch | Epic 2 |
| `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, production settings split | ✗ do not touch (AD-17) | deferred whole |
| A CSRF defence | ✗ record it, do not build it | Epic 9 |

### The 401→403 trap (the way this story ships broken)

DRF coerces an authentication failure to **403** unless the *first* authenticator supplies a
`WWW-Authenticate` header. Verified in the installed source, `rest_framework/views.py:458-465`:

```python
if isinstance(exc, (exceptions.NotAuthenticated, exceptions.AuthenticationFailed)):
    auth_header = self.get_authenticate_header(self.request)   # → authenticators[0].authenticate_header(request)
    if auth_header:
        exc.auth_header = auth_header
    else:
        exc.status_code = status.HTTP_403_FORBIDDEN
```

`BaseAuthentication.authenticate_header` returns `None` by default. SimpleJWT's class overrides it,
which is the only reason `/api/auth/me/` answers **401** today. Omit the override and every
unauthenticated request becomes 403 — the app still "works", nothing raises, and the frontend's
session probe (`YoutubeHeader.tsx:57`, the one call that *does* send credentials) starts seeing a
status it does not expect. This is a silent contract break dressed as a passing test suite. Hence a
DoD step, a `curl -I`, and an assertion on the header itself.

### Files being modified (read before editing)

- **`backend/youtube_organizer/settings.py`** — read `:13-19` (`SIMPLE_JWT`), `:59-70` (`MIDDLEWARE`,
  with the JWT middleware at `:64` and its comment at `:63`), `:80-89` (the CORS/cookie block that
  **must not move**), `:170-177` (`REST_FRAMEWORK`). Note the file's own oddity: `from datetime import
  timedelta` sits at `:15`, above the module docstring's usual position, because the `SIMPLE_JWT`
  block was bolted to the top. Your `AUTH_JWT_ACCESS_LIFETIME` replaces that block in place — keep
  the import, do not "tidy" the file. 4-space indented; do not reformat.
- **`backend/youtube_organizer/middleware.py`** — 12 lines, one class. Read it once so you can state
  in the PR what behaviour is disappearing: it copied the `access_token` cookie into
  `HTTP_AUTHORIZATION` for *every* request, app-wide, whether or not the view was a DRF view. That
  global mutation is what AD-14 retires; the authentication class reads the cookie only when DRF
  invokes it, on the views that are actually authenticated.
- **`backend/organizer/google_auth_views.py`** — read `:1-16` (imports) and `:131-148` (mint +
  `set_cookie`). Only the mint call and `max_age` change. `login(request, user)` at `:117` stays: the
  session carries `profile_picture`, which `MeView` reads. It is not the auth mechanism and it is not
  yours to remove.
- **`backend/organizer/api/views.py`** — **tab-indented** (a real one, not a rendering artefact).
  `MeView` needs no change; if you touch it at all, match the tabs. See "mixed indentation" below.
- **`backend/organizer/tests/test_layering.py`** — read all 176 lines before editing. `FORBIDDEN`
  (`:15-40`) is layer → forbidden dotted prefixes; `_imported_modules` (`:43-68`) yields both the
  package path and each `from X import name` candidate — that submodule-candidate behaviour was a
  code-review fix, **do not simplify it away**. Your write-guard is a *second*, independent check
  alongside the import one; do not try to express it through `FORBIDDEN`.
- **`backend/organizer/tests/test_auth_tokens.py`** — 361 lines. Your edit is confined to deleting
  `SimpleJWTCompatibilityTests` (`:297-361`) and adding the hand-minted legacy-shape replacement.
  Everything above `:297` is 1.3's rejection-path suite and stays untouched.
- **`backend/organizer/auth/tokens.py`** — read it, change almost nothing. The one permitted edit is
  Task 2's validation inside `_access_lifetime()`: raise `ImproperlyConfigured` when the setting is
  not a positive `timedelta` (an `int` currently raises a bare `TypeError` out of
  `issue_access_token` — a 500 on the login path; a negative value mints tokens dead on arrival).
  Keep the `getattr` default so `override_settings` and the existing tests keep working.

### Endpoint-by-endpoint outcome of the default-permission change (Task 2)

| Endpoint | Today | After | Why |
| --- | --- | --- | --- |
| `/api/auth/google/` (`GoogleAuthInitView`) | implicit `AllowAny` (DRF default) | **explicit** `AllowAny` | The user is not logged in yet — this is the login entry point. AD-14 wants the exemption stated, not inherited. |
| `/api/oauth2callback/` (`GoogleAuthCallbackView`) | explicit `AllowAny` | unchanged | Already explicit. |
| `/api/auth/me/` (`MeView`) | explicit `IsAuthenticated` | unchanged | — |
| `/api/youtube/playlists/` | explicit `IsAuthenticated` | unchanged | — |

Four endpoints, one behavioural change (none, if you add the explicit `AllowAny`). The value is for
the *next* view: a story that forgets `permission_classes` now gets a locked endpoint rather than an
open one.

### What the removal drags out with it

`deferred-work.md:19` predicted that removing SimpleJWT leaves `cryptography` — an unpinned
transitive — without a requirer, so the environment could change under an unchanged
`requirements.txt`. **Check this rather than assuming it**: `pyOpenSSL==26.4.0` is pinned and depends
on `cryptography`, so the prediction is probably wrong in this repo. Run `pip check` and `pip list`
after the rebuild and record what actually happened. If `cryptography` survives, say so and correct
the deferred item — a carried-forward prediction that turned out false is worth as much as one that
came true, and leaving it uncorrected sends the next story hunting a phantom.

PyJWT is unaffected: it became a **direct** pin in 1.3 (`PyJWT==2.13.0`), which was the whole point
of doing it there.

### The cookie contract, verbatim (do not paraphrase it into a change)

```python
response.set_cookie(
    key='access_token', value=access_token,
    httponly=True, secure=True, samesite='None',
    max_age=60*60*24,     # ← the only line that changes: derived from AUTH_JWT_ACCESS_LIFETIME
)
```

and in settings, untouched: `CORS_ALLOWED_ORIGINS = ["https://localhost:3000"]`,
`CORS_ALLOW_CREDENTIALS = True`, `SESSION_COOKIE_SAMESITE = "None"`, `SESSION_COOKIE_SECURE = True`,
`CSRF_COOKIE_SAMESITE = "None"`, `CSRF_COOKIE_SECURE = True`.

AD-14: *"The cookie contract with the frontend is unchanged; only the backend implementation
moves."* The frontend never reads the cookie (it is HttpOnly) — it relies on the browser sending it
on credentialed requests, which depends entirely on `SameSite=None; Secure` plus
`CORS_ALLOW_CREDENTIALS` plus the single allowed origin. Relaxing any one of them breaks login in a
way that looks like a frontend bug.

### Live sessions survive the merge — and that is testable

Every `access_token` cookie in flight at merge time was minted by SimpleJWT and carries `user_id` as
a **string**. 1.3 proved `verify_access_token` accepts them and normalizes to `int`. Task 6 keeps
that proof alive without the dependency by hand-minting the same wire shape. If you delete the compat
class *and* skip the replacement, the suite goes green over the one regression that would log every
user out — and it would not surface for a full day.

### CSRF: the exposure this story creates (and correctly does not fix)

Header-borne JWT was accidentally CSRF-immune — a cross-site form cannot set an `Authorization`
header. Reading the cookie directly removes that accident: a `SameSite=None` cookie is attached to
cross-site requests by design, and DRF enforces CSRF only for `SessionAuthentication`. Today there
are zero unsafe-method API endpoints, so there is nothing to forge. Epic 9 introduces them. **Record
it in `deferred-work.md` with Epic 9 named** (Task 10); do not build a defence here, and do not add
`SessionAuthentication` as a back-door CSRF check — that would change the contract AC3 protects.

### Testing

Standards from **AD-16** and the harness 1.2 established:

- **No test touches the network.** The callback test fakes Google at the boundary
  (`Flow`, and the `requests.get` userinfo call) — never a real HTTP call, never real credentials.
- Tests live in `organizer/tests/`, one `test_<subject>.py` per subject. Discovery pattern is
  `test*.py` — a file named `cookie_authentication_test.py` is silently never run.
- `SimpleTestCase` for DB-free structural assertions (settings, repo text, the layering guards);
  `TestCase` when the ORM is involved; **`APITestCase` for the request path** — AD-16 requires the
  cookie-borne path proven end to end, and 1.3 explicitly deferred that requirement to this story.
- `self.client.cookies["access_token"] = <token>` is how DRF's `APIClient` carries a cookie. Assert
  response cookie attributes off `response.cookies["access_token"]` (`["httponly"]`, `["secure"]`,
  `["samesite"]`, `["max-age"]`).
- Run: `make backend-test` (container) or `make backend-coverage` for the measured run. Host-side,
  with `make up` running:
  `cd backend && POSTGRES_HOST=localhost .venv/bin/python manage.py test --noinput`.
- **Coverage:** this is the story that turns `fail_under = 70` on. See Task 9, including the
  instruction not to lower it.

### Previous story intelligence (Stories 1.2 and 1.3)

- **The container is the source of truth; the host venv drifts.** After this story the host venv
  still has `rest_framework_simplejwt` installed until someone re-runs
  `backend/.venv/bin/pip install -r backend/requirements.txt` — and `pip install -r` does **not**
  uninstall a removed package. This is why every AC2 test asserts on repo *text*, not on
  importability. Do not change code to satisfy a stale venv.
- **A requirements change needs an image rebuild** — and for a *removal* the stale container is
  actively misleading, not merely lagging: it still has the package.
- **A bare `python -c "import organizer…"` cannot work.** Every probe needs
  `DJANGO_SETTINGS_MODULE=youtube_organizer.settings` and `django.setup()`.
- **Guards must be seen to fail.** 1.3's DoD required temporarily breaking the layering guard and
  pasting the failure. Task 7's write-guard and Task 9's `fail_under` inherit that rule.
- **The guard's self-test is load-bearing, in both directions.** 1.2's review found the detector
  blind to the most idiomatic spelling of a violation because every self-test case was a form it
  already handled. Your write-guard's negative cases (`dict.update()`) matter as much as its
  positive ones.
- **Mixed indentation is real and per-file.** `models/user_social_token.py` and `api/views.py` are
  **tab**-indented; `urls.py`, `settings.py`, `google_auth_views.py`, everything under `tests/` and
  the layer packages are 4-space. New files are 4-space PEP 8. **Never reformat a file wholesale.**
- **Two compose files.** Root `docker-compose.yml` is the real one (`make up`, `postgres:15`).
  `backend/docker-compose.yml` is a stale duplicate (`postgres:16`) that nothing invokes. Edit
  neither.
- **`AI-1` is live** (`sprint-status.yaml`): the frontend Sign-in button omits
  `credentials: "include"`, so login *through the browser UI* fails with `MismatchingStateError`
  — **before** any of your code runs. Consequence: you cannot verify this story by clicking Sign in.
  Use the `curl` DoD steps and the faked callback test. Do not "discover" AI-1 and fix it here; it
  is Epic 2's, and putting a frontend fix in this PR muddies the swap.
- **1.3's answered questions are settled:** the SimpleJWT claim names stay (`user_id`, not `sub`),
  and `verify_access_token` normalizes `user_id` to `int` on the way out. Do not relitigate either.

### Git intelligence (last 5 commits)

- `8331225` (merge) / `c1637e3` / `dc8c2f1` — Story 1.3. `dc8c2f1` is the module; the review pass
  that followed added the `except jwt.PyJWTError` backstop, the `user_id` normalization, and the
  issue-time pk guard. Those three are exactly the properties your authentication class leans on —
  read the comments around them before assuming a simpler error path.
- `5c1ba29` / `ecd5fd5` — Story 1.2. `ecd5fd5` is a code-review hardening pass; the comments it left
  in `test_layering.py` and `.coveragerc` encode defects actually found. Load-bearing documentation.
- `7117a40` / `7aab44d` — Stories 3.5/3.6. `ci.yml` and `.githooks/pre-push` are live gates; the only
  CI edit you make is deleting the `TODO(story 1-4)` block.
- Conventions the history establishes: Conventional Commit subjects with a scope
  (`feat(backend):`, `fix(backend):`, `ci:`), one squash-merge per story PR, **no attribution
  trailers anywhere**. Suggested subject: `feat(backend): authenticate from the access_token cookie`.

### Latest technical information (verified against the installed environment, 2026-08-13)

| Item | Value | Note |
| --- | --- | --- |
| DRF | **3.18.0** | `BaseAuthentication` in `rest_framework.authentication`; `AuthenticationFailed` in `rest_framework.exceptions`; the 401→403 coercion at `views.py:458-465` |
| Django | **6.0.8** | `MIDDLEWARE` order unchanged; `SessionMiddleware` + `AuthenticationMiddleware` both stay |
| PyJWT | 2.13.0 | Direct pin since 1.3; nothing here calls it directly — go through `organizer.auth.tokens` |
| SimpleJWT | 5.5.1 | **Removed by this story.** Last release 2025-07-21; no Django 6.0 support claim (AD-14) |
| coverage.py | 7.15.4 | `fail_under` lives under `[report]`; `coverage report` exits non-zero when missed |

`authenticate()` returns `(user, auth)` or `None`; `None` means "no opinion" and DRF moves on to the
next authenticator (there is only one) and then to the permission classes. `AuthenticationFailed`
short-circuits with 401 — *provided* `authenticate_header` returns a value.

### Project Structure Notes

- `organizer/auth/` does **not** shadow `django.contrib.auth` — Python 3 imports are absolute.
  Inside `organizer/`, reach it as `from .auth import ...` / `organizer.auth`.
- The settings path is `organizer.auth.authentication.CookieJWTAuthentication` — a dotted string, so
  a typo surfaces as an `ImproperlyConfigured` at first request, not at `manage.py check`. The DoD's
  `curl` steps are what catch it.
- Python `snake_case`; test files `test_<subject>.py`; every new directory is a package with a real
  `__init__.py` — `test_skeleton.py` asserts this.
- No migration, no schema change, no model change in this story.
- `.dockerignore` still absent and `backend/.venv` still enters the build context (deferred from
  1.1). Not yours; just expect a slow `docker-compose build`.

### The PR template trap

`.github/pull_request_template.md` auto-applies and is still Accountr's: it instructs
`pnpm exec nx run backend:test --coverage`, cites Prisma DTOs and money-as-string, and links to
`Docs/MVPDefinition/…` paths that do not exist here. `project-context.md` requires all checklist
items ticked before merge, so it is currently impossible to satisfy honestly. **Tick what applies,
strike through the rest.** Do not rewrite the template in this PR (tracked as deferred work), and do
not silently tick items you did not do.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.4] — user story + acceptance criteria
- [Source: …/ARCHITECTURE-SPINE.md#AD-14] — cookie-borne JWT; SimpleJWT dropped; `JWTAuthCookieMiddleware` retired; the cookie contract is unchanged; views default to authenticated
- [Source: …/ARCHITECTURE-SPINE.md#AD-1] — services are the only mutation path (why the auth class writes nothing)
- [Source: …/ARCHITECTURE-SPINE.md#AD-16] — no test touches the network; `APITestCase` must exercise the cookie path end to end; coverage 70%
- [Source: …/ARCHITECTURE-SPINE.md#AD-17] — localhost only; `DEBUG`/`SECRET_KEY`/`ALLOWED_HOSTS` are accepted, not yours to fix
- [Source: …/WORK-SPLIT.md#E1] — "highest risk in the phase … the auth replacement wants tests before the swap, not after"
- [Source: _bmad-output/implementation-artifacts/1-3-first-party-pyjwt-token-issue-verify-module.md] — the token module, the claim set, the compat proof, the 71% baseline, the container/venv traps
- [Source: _bmad-output/implementation-artifacts/1-2-layered-backend-package-skeleton-and-test-runner.md] — the harness, the layering guard, the "guards must be seen to fail" rule
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] — the four items this story owns and closes; the transitive-closure item to re-check
- [Source: _bmad-output/project-context.md] — auth invariants, backend rules, testing rules, CI gates, attribution ban
- [Source: Docs/CI-AND-GITHUB-GATES.md] — gate intent; the 70% coverage gate deferred to this story
- [Source: CLAUDE.md] — git workflow, Conventional Commits, attribution ban, project-local memory
- [DRF authentication docs](https://www.django-rest-framework.org/api-guide/authentication/#custom-authentication) — `authenticate` / `authenticate_header` contract, and the 401-vs-403 note
- [DRF permissions docs](https://www.django-rest-framework.org/api-guide/permissions/#setting-the-permission-policy) — `DEFAULT_PERMISSION_CLASSES`
- [Django 6.0 middleware docs](https://docs.djangoproject.com/en/6.0/topics/http/middleware/) — ordering, and what removing one changes
- [coverage.py configuration](https://coverage.readthedocs.io/en/latest/config.html#report-fail-under) — `fail_under` semantics and exit code

## Questions for Alexis

_Save these for after implementation — none of them blocks the work._

1. **`DEFAULT_PERMISSION_CLASSES = IsAuthenticated` is included** (Task 2) because AD-14 states views
   default to authenticated with `AllowAny` explicit, and this is the auth story. It is a
   four-endpoint change with a table of outcomes and a test each — but it is not literally in an AC.
   Say the word and it moves to its own follow-up.
2. **The 70% gate is set to 70, not to the measured figure.** A ratchet pinned to today's coverage
   would fail the next honest refactor; 70 is the number `Docs/CI-AND-GITHUB-GATES.md` states. Happy
   with the flat threshold?
3. **CSRF is recorded, not fixed.** This story removes the accidental CSRF immunity that header auth
   provided, and Epic 9 is where unsafe-method endpoints arrive. Comfortable carrying that as a
   tracked deferred item until then, or would you rather Epic 9 open with a CSRF story?

## Dev Agent Record

### Agent Model Used

claude-opus-5 (BMad dev-story workflow)

### Debug Log References

**The AD-1 write-guard, proven to fail on real code** (the standing rule since 1.2 — a guard
never seen to bite is not a guard). Temporarily inserted
`get_user_model().objects.filter(pk=1).update(last_login=None)` into
`organizer/auth/authentication.py`, then reverted:

```
FAIL: test_scanned_layers_contain_no_orm_writes
AssertionError: Lists differ: ["auth/authentication.py:66 calls 'update([58 chars]1)."] != []
First extra element 0:
"auth/authentication.py:66 calls 'update()' — organizer/auth/ must not write application state (AD-1)."
```

It names the file and the line, and it sees a write buried inside a method body — which is
exactly what the import-based guard structurally could not do.

**The coverage gate, proven to bite.** `fail_under = 99` → `coverage report` exits **2** with
`Coverage failure: total of 90 is less than fail-under=99`; reverted to `70` → exits **0**.

**A bug the tests caught in the tests.** `_authenticate(token=None)` was first written as
`token or issue_access_token(...)`, which turned the empty-string rejection case into a freshly
minted *valid* token — `test_empty_cookie_is_401` returned 200. Replaced with an explicit
`_MINT` sentinel. Worth recording because the falsy-default idiom silently disarms exactly the
rejection paths this story exists to prove.

**`docker compose` must be run from the repo root.** Running it from `backend/` picks up the
stale duplicate `backend/docker-compose.yml` and answers `service "backend" is not running`
against a perfectly healthy container. The trap Story 1.1 R5 documented, hit live.

### Completion Notes List

**What shipped.** A `CookieJWTAuthentication` reading the `access_token` cookie directly,
registered as DRF's sole default authenticator; `JWTAuthCookieMiddleware` deleted; SimpleJWT
gone from `requirements.txt`, imports and the compat suite; the mint site and the cookie's
`max_age` moved onto one `AUTH_JWT_ACCESS_LIFETIME` setting; an AST write-guard over `auth/`;
the end-to-end `APITestCase` AD-16 required; and `fail_under = 70` turned on.

**Verified by hand (AC1, container, over HTTPS):** cookie → **200** with the user's
`username`/`email`; the same token in an `Authorization: Bearer` header → **401** (header auth
is deliberately dead); no cookie → **401** *with* `WWW-Authenticate: Bearer realm="api"` present
— the 401→403 trap avoided, and asserted in the suite rather than only observed;
`/api/auth/google/` → **200** (the one view the default-permission change had to leave public).

**Test arithmetic: 42 → 87.** 42 baseline − 4 deleted compat tests + 3 hand-minted legacy-shape
replacements + 3 write-guard tests + 43 in `test_cookie_authentication.py` = **87**, all green
in the container *and* on the host.

**Coverage: 71% → 90%**, gate set to **70**. Per-file: `auth/tokens.py` 100%,
`auth/authentication.py` 92% (the uncovered lines are the `TokenError` backstop clause, which is
unreachable while the hierarchy has exactly three members — kept deliberately),
`auth/errors.py` 100%, `checks.py` 100%, and `google_auth_views.py` **80%**, up from near-zero:
the faked-`Flow` callback test was worth attempting rather than falling back to the manual
`curl`, exactly as Task 8 hoped.

**`pip check` → `No broken requirements found.`** And the carried-forward prediction was
**false**: `cryptography` did *not* lose its requirer when SimpleJWT went — `pyOpenSSL==26.4.0`
is a direct pin that depends on it, so `cryptography 50.0.0` survives a clean rebuild.
`deferred-work.md` is corrected rather than left to send the next story hunting a phantom.

**Three deviations from the story as written, each deliberate:**

1. **`AUTH_JWT_ACCESS_LIFETIME` validation is split across two mechanisms**, because the story
   asks for two incompatible things: Dev Notes wants `_access_lifetime()` to reject a
   non-*positive* `timedelta`, while Task 8 (and four existing 1.3 tests) mint expired tokens
   via `override_settings(AUTH_JWT_ACCESS_LIFETIME=timedelta(seconds=-10))` — which that rule
   would forbid. Resolution: `_access_lifetime()` rejects the wrong *type* (the 500-on-login
   defect the deferred item actually named), and the *sign* check is a Django system check,
   `organizer.E001` in the new `organizer/checks.py`. `manage.py check` is a CI job step and
   pre-push layer 4/6, so an operator's bad value fails the build — while the runtime stays
   testable. **This touches two files not in the story's file table:** `organizer/checks.py` (new)
   and `organizer/apps.py` (modified — `ready()` registers the check with Django's registry, which
   is what makes `organizer.E001` fire at all; code review added a test pinning that registration,
   since every other test calls the check function directly).

2. **The DoD's `grep -rni "simplejwt" backend/organizer/ …` → "no matches" is unsatisfiable**,
   because Task 7 of the same story requires `FORBIDDEN["auth"]` to keep the literal
   `"rest_framework_simplejwt"` — the entry that stops a later story reintroducing the package.
   AC2's real claim (absent from `requirements.txt` and **imports**) is enforced instead by an
   AST scan that counts only genuine `import` statements: immune to docstrings, and it cannot be
   defeated by burying an import in a function body, which a grep-as-specified also could not
   see through. `requirements.txt` *is* checked case-insensitively for any mention. Recorded in
   `deferred-work.md` for the next story that edits the DoD.

3. **`organizer/auth/tokens.py`'s module docstring was updated**, beyond the `_access_lifetime`
   edit the story permits: it opened with "Ships unwired: Story 1.4 puts this behind a DRF
   authentication class", which this story makes false. The prose mentions of the retired
   library elsewhere in that file are kept — they are precise, checkable citations
   (`5.5.1 tokens.py:228`) and the gate that matters is the AST one.

**Deferred items closed:** access lifetime in three places · `AUTH_JWT_ACCESS_LIFETIME`
undeclared/unvalidated · the compat suite's removal obligation · AD-1's write ban inside
`auth/`. **Re-targeted:** the `cryptography` half of the transitive-closure item (closed as
false) · the `get_user_from_claims` catch-net (now recorded with what a real call site taught) ·
`google_auth_views.py`'s own AD-1 violations (→ 6.1). **Raised new:** the CSRF exposure this
story creates and correctly does not fix (Epic 9), and the DoD-grep note above.

**Not touched, on purpose:** AI-1 (the frontend `credentials: "include"` bug — Epic 2; it is
also why this story cannot be verified by clicking Sign in, hence the `curl` steps), refresh
tokens/rotation/revocation, `google_auth_views.py`'s inline YouTube client and direct
`UserSocialToken` write, and the CORS/cookie settings block — whose absence from
`git diff backend/youtube_organizer/settings.py` is itself the AC3 evidence.

**Open questions for Alexis are unchanged and non-blocking** — see the section above; all three
were implemented as the story specified.

### File List

**Added**
- `backend/organizer/auth/authentication.py`
- `backend/organizer/checks.py`
- `backend/organizer/tests/test_cookie_authentication.py`

**Modified**
- `backend/youtube_organizer/settings.py`
- `backend/organizer/apps.py`
- `backend/organizer/auth/tokens.py`
- `backend/organizer/google_auth_views.py`
- `backend/organizer/tests/test_auth_tokens.py`
- `backend/organizer/tests/test_layering.py`
- `backend/requirements.txt`
- `backend/.coveragerc`
- `.github/workflows/ci.yml`
- `Makefile`
- `_bmad-output/implementation-artifacts/deferred-work.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/implementation-artifacts/1-4-cookie-authentication-class-and-middleware-retirement.md`

**Deleted**
- `backend/youtube_organizer/middleware.py`

## Change Log

| Date | Change |
| --- | --- |
| 2026-08-13 | Story created — cookie authentication class over 1.3's token module, `JWTAuthCookieMiddleware` deleted, SimpleJWT dropped from requirements and imports, the mint site and cookie `max_age` moved onto `AUTH_JWT_ACCESS_LIFETIME`, an AD-1 write-guard inside `auth/`, the end-to-end `APITestCase` AD-16 requires, and `fail_under = 70` turned on. AD-14, AD-1, AD-16, NFR-13. |
| 2026-08-14 | Implemented. 42 → 87 tests, coverage 71% → 90% with the 70% gate live and proven to bite. Header auth retired and regression-tested; 401-not-403 asserted via `WWW-Authenticate`. Lifetime validation split between `_access_lifetime()` (type) and the new `organizer.E001` system check (sign) so the expired-token path stays testable. Four deferred items closed, three re-targeted, two raised (CSRF for Epic 9; the unsatisfiable DoD grep). |
