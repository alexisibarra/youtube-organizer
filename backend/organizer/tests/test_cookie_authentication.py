"""Cookie-borne authentication, end to end (AD-14, AD-16, Story 1.4).

AC1 — a valid `access_token` cookie authenticates, with no Authorization header in play.
AC2 — the header-injection middleware and SimpleJWT are gone, asserted over repo text.
AC3 — the cross-port cookie contract is byte-identical, and login → authenticated
      request round-trips over the cookie path.

No network anywhere (AD-16): Google is faked at the boundary. Neither PyJWT nor the
authentication class is mocked — the real path through DRF is what is under test.
"""

import ast
import pathlib
import re
from datetime import datetime, timedelta, timezone
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory, APITestCase

from organizer.auth.authentication import CookieJWTAuthentication
from organizer.auth.tokens import issue_access_token

User = get_user_model()

BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

#: "mint a fresh token" — distinct from `None` and from `""`, both of which are
#: rejection paths this suite asserts on.
_MINT = object()


def _drf_request(**cookies):
    """A DRF Request carrying `cookies` and nothing else."""
    from rest_framework.request import Request

    django_request = APIRequestFactory().get("/")
    django_request.COOKIES.update(cookies)
    return Request(django_request)


class CookieJWTAuthenticationUnitTests(TestCase):
    """The authentication class in isolation: what it returns, and what it raises."""

    def setUp(self):
        self.user = User.objects.create_user(username="cookie-unit", password="x")
        self.auth = CookieJWTAuthentication()

    def test_no_cookie_returns_none_rather_than_raising(self):
        """`None` means "no opinion" — it is what keeps AllowAny views public.

        Raising here would 401 the OAuth entry point and break login before it starts.
        """
        self.assertIsNone(self.auth.authenticate(_drf_request()))

    def test_empty_cookie_returns_none(self):
        self.assertIsNone(self.auth.authenticate(_drf_request(access_token="")))

    def test_valid_cookie_returns_the_user_and_the_raw_token(self):
        token = issue_access_token(self.user)
        user, auth = self.auth.authenticate(_drf_request(access_token=token))
        self.assertEqual(user.pk, self.user.pk)
        self.assertEqual(auth, token)

    def test_expired_cookie_raises_token_expired(self):
        with override_settings(AUTH_JWT_ACCESS_LIFETIME=timedelta(seconds=-10)):
            token = issue_access_token(self.user)
        with self.assertRaises(AuthenticationFailed) as ctx:
            self.auth.authenticate(_drf_request(access_token=token))
        self.assertEqual(ctx.exception.detail.code, "token_expired")

    def test_tampered_cookie_raises_token_invalid(self):
        token = issue_access_token(self.user)
        with self.assertRaises(AuthenticationFailed) as ctx:
            self.auth.authenticate(_drf_request(access_token=token + "x"))
        self.assertEqual(ctx.exception.detail.code, "token_invalid")

    def test_deleted_user_raises_user_unavailable(self):
        token = issue_access_token(self.user)
        self.user.delete()
        with self.assertRaises(AuthenticationFailed) as ctx:
            self.auth.authenticate(_drf_request(access_token=token))
        self.assertEqual(ctx.exception.detail.code, "user_unavailable")

    def test_inactive_user_raises_user_unavailable(self):
        token = issue_access_token(self.user)
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        with self.assertRaises(AuthenticationFailed) as ctx:
            self.auth.authenticate(_drf_request(access_token=token))
        self.assertEqual(ctx.exception.detail.code, "user_unavailable")

    def test_authenticate_header_is_present(self):
        """The mechanism behind 401-not-403 (see the story's "401→403 trap").

        DRF coerces AuthenticationFailed to 403 when the first authenticator's
        authenticate_header() returns None (rest_framework/views.py:458-465).
        """
        self.assertEqual(
            self.auth.authenticate_header(_drf_request()), 'Bearer realm="api"'
        )

    def test_authenticating_does_not_write_last_login(self):
        """AD-1: services are the only writer. The auth class touches no state."""
        before = User.objects.get(pk=self.user.pk).last_login
        self.auth.authenticate(_drf_request(access_token=issue_access_token(self.user)))
        self.assertEqual(User.objects.get(pk=self.user.pk).last_login, before)


class RetirementIsCompleteTests(SimpleTestCase):
    """AC2 as a standing gate, asserted over settings and repo text.

    Text assertions, not `import rest_framework_simplejwt` + assertRaises: the host
    venv keeps the package installed until someone re-runs `pip install`, and
    `pip install -r` does not uninstall a removed package. A test that depends on an
    uninstall passes and fails for environmental reasons rather than code ones.
    """

    def test_jwt_cookie_middleware_is_not_installed(self):
        self.assertNotIn(
            "youtube_organizer.middleware.JWTAuthCookieMiddleware", settings.MIDDLEWARE
        )

    def test_middleware_module_does_not_exist_on_disk(self):
        """Removed, not merely unregistered — AD-14 retires the global mutation."""
        self.assertFalse((BACKEND_ROOT / "youtube_organizer" / "middleware.py").exists())

    def test_session_and_auth_middleware_survive(self):
        """The OAuth callback calls login(); MeView reads request.session."""
        self.assertIn(
            "django.contrib.sessions.middleware.SessionMiddleware", settings.MIDDLEWARE
        )
        self.assertIn(
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            settings.MIDDLEWARE,
        )

    def test_the_cookie_class_is_the_only_default_authenticator(self):
        """Exactly one entry. SessionAuthentication would enforce CSRF on unsafe
        methods and change the very contract AC3 protects."""
        self.assertEqual(
            settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"],
            ("organizer.auth.authentication.CookieJWTAuthentication",),
        )

    def test_views_default_to_authenticated(self):
        """AD-14: AllowAny is explicit and justified, never inherited."""
        self.assertEqual(
            settings.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"],
            ("rest_framework.permissions.IsAuthenticated",),
        )

    def test_simple_jwt_settings_block_is_gone(self):
        self.assertFalse(hasattr(settings, "SIMPLE_JWT"))

    def test_access_lifetime_is_declared_in_settings(self):
        """One knob. tokens.py and the login cookie's max_age both read it."""
        self.assertEqual(settings.AUTH_JWT_ACCESS_LIFETIME, timedelta(days=1))

    def test_the_dependency_is_absent_from_requirements(self):
        """Case-insensitive, so a re-added pin cannot hide behind capitalisation —
        the defect 1.3's case-sensitive grep was found to have."""
        text = (BACKEND_ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"simplejwt", text, re.IGNORECASE))

    def test_nothing_under_either_package_imports_the_retired_library(self):
        """AC2's real claim, checked by parsing rather than by grepping.

        A flat text scan cannot be the gate here: `test_layering.py` must keep
        `rest_framework_simplejwt` as a *forbidden-list entry* (Story 1.4 Task 7 —
        that entry is what stops a later story reintroducing the package), and several
        docstrings name the retired library to explain the wire format they emulate.
        A grep sees a forbid-rule, a history note and a real import as the same thing.

        Walking the AST distinguishes them: only genuine `import` / `from ... import`
        statements count, so the guard's own string literals and every docstring are
        correctly ignored while an actual import — the thing AC2 forbids — cannot hide
        anywhere, including inside a function body.
        """
        offenders = []
        for package in ("organizer", "youtube_organizer"):
            for path in sorted((BACKEND_ROOT / package).rglob("*.py")):
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        names = [alias.name for alias in node.names]
                    elif isinstance(node, ast.ImportFrom):
                        names = [node.module or ""]
                    else:
                        continue
                    for name in names:
                        if name.split(".")[0] == "rest_framework_simplejwt":
                            offenders.append(
                                f"{path.relative_to(BACKEND_ROOT)}:{node.lineno}"
                            )
        self.assertEqual(offenders, [], f"retired library still imported: {offenders}")


class CrossPortContractTests(SimpleTestCase):
    """AC3 / NFR-9 in executable form.

    The frontend never reads the cookie (it is HttpOnly) — it relies on the browser
    sending it on credentialed requests, which depends entirely on these six values.
    The next story that "cleans up settings" gets a red test, not a broken login.
    """

    def test_cors_allows_credentials(self):
        self.assertIs(settings.CORS_ALLOW_CREDENTIALS, True)

    def test_exactly_one_allowed_origin(self):
        self.assertEqual(settings.CORS_ALLOWED_ORIGINS, ["https://localhost:3000"])

    def test_session_and_csrf_cookies_are_samesite_none_and_secure(self):
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, "None")
        self.assertEqual(settings.CSRF_COOKIE_SAMESITE, "None")
        self.assertIs(settings.SESSION_COOKIE_SECURE, True)
        self.assertIs(settings.CSRF_COOKIE_SECURE, True)


class AccessLifetimeValidationTests(SimpleTestCase):
    """A misconfigured lifetime must fail loudly, not mint a broken token.

    Split deliberately across two mechanisms, because the two failure modes have
    different audiences:

    * **Wrong type** — an `int` previously raised a bare `TypeError` out of
      `issue_access_token`, i.e. a 500 on the login path. Rejected at
      `access_lifetime()`, at the moment of use.
    * **Out of bounds** — mints tokens dead on arrival (non-positive, or positive but
      under a second) or overflows `now + lifetime` (absurdly large). Rejected by a
      Django system check, **not** at runtime:
      `override_settings(AUTH_JWT_ACCESS_LIFETIME=timedelta(seconds=-10))` is how this
      suite and 1.3's mint an expired token, and a runtime raise would make the
      expired-token path untestable. The check catches the operator; the runtime stays
      testable.
    """

    def test_non_timedelta_raises_improperly_configured(self):
        from django.core.exceptions import ImproperlyConfigured

        from organizer.auth.tokens import access_lifetime

        for bad in (86400, "1 day", None):
            with self.subTest(value=bad):
                with override_settings(AUTH_JWT_ACCESS_LIFETIME=bad):
                    with self.assertRaises(ImproperlyConfigured):
                        access_lifetime()

    def test_a_positive_timedelta_is_returned_unchanged(self):
        from organizer.auth.tokens import access_lifetime

        with override_settings(AUTH_JWT_ACCESS_LIFETIME=timedelta(minutes=5)):
            self.assertEqual(access_lifetime(), timedelta(minutes=5))

    def test_the_default_applies_when_the_setting_is_absent(self):
        """The `getattr` fallback branch, which nothing else exercises.

        `override_settings` can only *set* a value, so removing the setting takes
        `del settings.AUTH_JWT_ACCESS_LIFETIME` on the override handle. Worth a test
        because this is the branch that makes the setting "optional", and the login
        view's cookie `max_age` now resolves through the same function — so if the
        default ever diverges from `settings.py`, the cookie and the token's `exp`
        still agree with each other rather than silently splitting.
        """
        from organizer.auth.tokens import DEFAULT_ACCESS_LIFETIME, access_lifetime

        with override_settings():
            del settings.AUTH_JWT_ACCESS_LIFETIME
            self.assertEqual(access_lifetime(), DEFAULT_ACCESS_LIFETIME)

    def test_system_check_flags_a_non_positive_lifetime(self):
        from organizer.checks import check_access_token_lifetime

        for bad in (timedelta(0), timedelta(seconds=-1)):
            with self.subTest(value=bad):
                with override_settings(AUTH_JWT_ACCESS_LIFETIME=bad):
                    self.assertEqual(
                        [e.id for e in check_access_token_lifetime(None)],
                        ["organizer.E001"],
                    )

    def test_system_check_flags_a_sub_second_lifetime(self):
        """Positive, and still broken: `int(0.5)` is 0, and `max_age=0` tells the
        browser to drop the cookie immediately — the same symptom as a negative
        lifetime, which a sign-only check would pass."""
        from organizer.checks import check_access_token_lifetime

        with override_settings(AUTH_JWT_ACCESS_LIFETIME=timedelta(milliseconds=500)):
            self.assertEqual(
                [e.id for e in check_access_token_lifetime(None)], ["organizer.E001"]
            )

    def test_system_check_flags_an_implausibly_long_lifetime(self):
        """`now + timedelta.max` raises OverflowError inside `issue_access_token` —
        a 500 on the login path from a settings typo."""
        from organizer.checks import check_access_token_lifetime

        with override_settings(AUTH_JWT_ACCESS_LIFETIME=timedelta.max):
            self.assertEqual(
                [e.id for e in check_access_token_lifetime(None)], ["organizer.E001"]
            )

    def test_system_check_flags_a_non_timedelta_lifetime(self):
        from organizer.checks import check_access_token_lifetime

        with override_settings(AUTH_JWT_ACCESS_LIFETIME=86400):
            self.assertEqual(
                [e.id for e in check_access_token_lifetime(None)], ["organizer.E001"]
            )

    def test_system_check_flags_an_absent_setting(self):
        from organizer.checks import check_access_token_lifetime

        with override_settings():
            del settings.AUTH_JWT_ACCESS_LIFETIME
            self.assertEqual(
                [e.id for e in check_access_token_lifetime(None)], ["organizer.E001"]
            )

    def test_system_check_passes_on_the_shipped_settings(self):
        from organizer.checks import check_access_token_lifetime

        self.assertEqual(check_access_token_lifetime(None), [])

    def test_the_system_check_is_actually_registered(self):
        """Every other test here calls the check function directly, which means all of
        them would still pass if `OrganizerConfig.ready()` stopped registering it —
        and registration is the *only* thing that makes `organizer.E001` fire, since
        `tokens.py` deliberately declines to duplicate the bounds check at runtime.
        `apps.py` reports 100% coverage either way, so coverage will not catch it.
        Assert the wiring, not just the callable.
        """
        from django.core.checks import registry

        from organizer.checks import check_access_token_lifetime

        self.assertIn(check_access_token_lifetime, registry.registry.get_checks())


class CookieAuthenticationOverHTTPTests(APITestCase):
    """AC1: the request path itself, through the real DRF stack.

    `self.client.cookies["access_token"] = ...` is how APIClient carries a cookie.
    Nothing here mocks PyJWT or the authentication class — a test that mocks the
    thing under test would also pass against the middleware this story deleted.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="cookie@example.com", email="cookie@example.com", password="x"
        )
        self.me_url = reverse("me")

    def _authenticate(self, token=_MINT):
        # Sentinel, not `token or issue_access_token(...)`: the empty-string case is
        # one of the rejection paths under test, and a falsy check would silently mint
        # a valid token for it and assert nothing.
        if token is _MINT:
            token = issue_access_token(self.user)
        self.client.cookies["access_token"] = token

    def test_valid_cookie_authenticates_and_returns_the_user(self):
        self._authenticate()
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertEqual(response.data["email"], self.user.email)

    def test_no_authorization_header_is_involved(self):
        """AC1's actual claim. "The response was 200" was also true of the middleware
        this story deleted — the header's *absence* inside the request cycle is what
        distinguishes the cookie path from the header-injection one."""
        self._authenticate()
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("HTTP_AUTHORIZATION", response.wsgi_request.META)

    def test_no_cookie_is_401(self):
        self.assertEqual(self.client.get(self.me_url).status_code, 401)

    def test_the_401_carries_a_www_authenticate_header(self):
        """Assert the mechanism, not just its current effect.

        This header is *why* the status is 401 rather than 403
        (rest_framework/views.py:458-465). Without it the app still "works", nothing
        raises, and the frontend's session probe silently starts seeing 403.
        """
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response["WWW-Authenticate"], 'Bearer realm="api"')

    def test_empty_cookie_is_401(self):
        self._authenticate(token="")
        self.assertEqual(self.client.get(self.me_url).status_code, 401)

    def test_expired_cookie_is_401(self):
        with override_settings(AUTH_JWT_ACCESS_LIFETIME=timedelta(seconds=-10)):
            self._authenticate()
        self.assertEqual(self.client.get(self.me_url).status_code, 401)

    def test_tampered_cookie_is_401(self):
        self._authenticate(token=issue_access_token(self.user)[:-2] + "xy")
        self.assertEqual(self.client.get(self.me_url).status_code, 401)

    def test_cookie_signed_with_another_key_is_401(self):
        import jwt

        now = datetime.now(timezone.utc)
        forged = jwt.encode(
            {
                "token_type": "access",
                "exp": now + timedelta(days=1),
                "iat": now,
                "jti": "f" * 32,
                "user_id": self.user.pk,
            },
            "an-entirely-different-signing-key-of-sufficient-length",
            algorithm="HS256",
        )
        self._authenticate(token=forged)
        self.assertEqual(self.client.get(self.me_url).status_code, 401)

    def test_cookie_for_a_deleted_user_is_401(self):
        self._authenticate()
        self.user.delete()
        self.assertEqual(self.client.get(self.me_url).status_code, 401)

    def test_cookie_for_an_inactive_user_is_401(self):
        self._authenticate()
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        self.assertEqual(self.client.get(self.me_url).status_code, 401)

    def test_a_valid_token_in_the_authorization_header_is_401(self):
        """The regression test for the retirement itself: header auth is dead.

        This is the one assertion that would have passed *before* this story for the
        wrong reason and must now pass for the right one — no cookie is set, so the
        only credential offered is the header, and nothing reads it any more.
        """
        response = self.client.get(
            self.me_url, HTTP_AUTHORIZATION=f"Bearer {issue_access_token(self.user)}"
        )
        self.assertEqual(response.status_code, 401)


class EndpointPermissionTests(APITestCase):
    """The per-endpoint outcome of the default-permission change (Task 2).

    Three of the four API endpoints are exercised here; `/api/oauth2callback/` is
    covered by `LoginRoundTripTests` instead, because asserting its permission means
    driving the whole faked-Google flow.

    No endpoint *changes behaviour*. The one that changed declaration is
    `GoogleAuthInitView`: it previously relied on DRF's implicit `AllowAny` default
    and now carries an explicit `permission_classes = [AllowAny]`, so its 200 below is
    the assertion that the new `IsAuthenticated` default did not lock the login entry
    point. The value of the change is for the *next* view — see
    `test_a_view_that_declares_no_permission_classes_is_locked`, which is where that
    claim is actually gated.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="perms@example.com", password="x")

    def test_oauth_entry_point_is_public(self):
        """The one view that must survive the default-permission change: the user is
        not logged in yet, so locking it would break login before it starts."""
        response = self.client.get(reverse("google_auth_init"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("auth_url", response.data)

    def test_me_requires_authentication(self):
        self.assertEqual(self.client.get(reverse("me")).status_code, 401)

    def test_me_with_a_cookie_is_200(self):
        self.client.cookies["access_token"] = issue_access_token(self.user)
        self.assertEqual(self.client.get(reverse("me")).status_code, 200)

    def test_playlists_requires_authentication(self):
        """401-without is the whole assertion. Calling it *with* a valid cookie would
        build a real YouTube client and reach the network (AD-16)."""
        self.assertEqual(
            self.client.get(reverse("youtube_playlists")).status_code, 401
        )

    def test_a_view_that_declares_no_permission_classes_is_locked(self):
        """The actual point of DEFAULT_PERMISSION_CLASSES, as behaviour.

        Asserting `settings.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"]` only says
        the setting holds the value it was set to. The claim the change is *for* —
        "a story that forgets `permission_classes` now gets a locked endpoint rather
        than an open one" — cannot be observed on any shipped view, because every one
        of them declares its own. So this drives a throwaway view that declares none,
        through the real DRF dispatch, and pins the default to 401.
        """
        from rest_framework.response import Response
        from rest_framework.views import APIView

        class ForgetfulView(APIView):
            def get(self, request):  # pragma: no cover - reached only if unlocked
                return Response({"leaked": True})

        request = APIRequestFactory().get("/forgetful/")
        response = ForgetfulView.as_view()(request)
        self.assertEqual(response.status_code, 401)


class LoginRoundTripTests(APITestCase):
    """AC3: login → authenticated request, over the cookie, end to end.

    Google is faked at the boundary — `Flow` and the userinfo `requests.get`, both
    patched in `organizer.google_auth_views`. No network, no credentials (AD-16).
    Mint by the login view, consume by the authentication class: that round trip is
    the sentence AC3 asks for, and no smaller test covers it.
    """

    def _fake_google(self):
        flow = mock.MagicMock()
        flow.credentials = mock.MagicMock(
            token="google-access-token",
            refresh_token="google-refresh-token",
            expiry=datetime(2030, 1, 1, tzinfo=timezone.utc),
            scopes=["https://www.googleapis.com/auth/youtube.readonly"],
            token_uri="https://oauth2.googleapis.com/token",
        )
        userinfo = mock.MagicMock(status_code=200)
        userinfo.json.return_value = {
            "email": "round-trip@example.com",
            "given_name": "Round",
            "family_name": "Trip",
            "picture": "https://lh3.googleusercontent.com/x",
        }
        return flow, userinfo

    def test_login_sets_the_contracted_cookie_and_that_cookie_authenticates(self):
        flow, userinfo = self._fake_google()
        with mock.patch(
            "organizer.google_auth_views.Flow.from_client_config", return_value=flow
        ), mock.patch(
            "organizer.google_auth_views.requests.get", return_value=userinfo
        ):
            response = self.client.get(reverse("google_auth_callback"), {"code": "x"})

        self.assertEqual(response.status_code, 302)

        cookie = response.cookies["access_token"]
        self.assertTrue(cookie["httponly"])
        self.assertTrue(cookie["secure"])
        self.assertEqual(cookie["samesite"], "None")
        self.assertEqual(
            cookie["max-age"], int(settings.AUTH_JWT_ACCESS_LIFETIME.total_seconds())
        )

        # That exact cookie value, fed back in. This is the half a settings assertion
        # cannot reach: the login view mints it, the authentication class consumes it.
        self.client.cookies["access_token"] = cookie.value
        me = self.client.get(reverse("me"))
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data["email"], "round-trip@example.com")

    def test_login_creates_the_user_and_stores_the_google_tokens(self):
        flow, userinfo = self._fake_google()
        with mock.patch(
            "organizer.google_auth_views.Flow.from_client_config", return_value=flow
        ), mock.patch(
            "organizer.google_auth_views.requests.get", return_value=userinfo
        ):
            self.client.get(reverse("google_auth_callback"), {"code": "x"})

        user = User.objects.get(username="round-trip@example.com")
        self.assertEqual(user.first_name, "Round")
        self.assertEqual(user.usersocialtoken.access_token, "google-access-token")
