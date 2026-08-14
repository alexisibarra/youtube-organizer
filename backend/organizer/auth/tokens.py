"""Access-token issue and verification over PyJWT (AD-14).

Wired as of Story 1.4: ``organizer.auth.authentication.CookieJWTAuthentication``
is the sole consumer on the request path, ``JWTAuthCookieMiddleware`` is gone, and
so is the third-party token dependency this module replaces. The one mint site is
the OAuth callback in ``organizer/google_auth_views.py``.

The claim set matches what the retired library minted (``user_id`` / ``token_type``
/ ``jti``, HS256 over ``settings.SECRET_KEY``) so the swap did not invalidate the
1-day ``access_token`` cookies in flight. The claim names are a compatibility
contract, not a style choice —
``organizer/tests/test_auth_tokens.py::LegacyWireFormatTests`` is what keeps that
true now that the library is no longer around to be compared against.

Must never: contain domain logic, or let a PyJWT type appear in a public
signature — callers depend on ``organizer.auth.errors``, not on the library.
"""

from datetime import timedelta
from uuid import uuid4

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

from .errors import ExpiredToken, InvalidToken, TokenUserError

#: Hardcoded, never derived from the token's own header — deriving it is the
#: alg-confusion / `alg: none` class of attack, and PyJWT's docs say so outright.
ALGORITHM = "HS256"

#: The literal SimpleJWT writes into TOKEN_TYPE_CLAIM for an access token.
ACCESS_TOKEN_TYPE = "access"

#: Rejected by the library rather than by a later KeyError. `jti` is deliberately
#: absent: nothing consumes it yet, so requiring it would reject tokens for a
#: claim we do not read.
REQUIRED_CLAIMS = ["exp", "iat", "token_type", "user_id"]

DEFAULT_ACCESS_LIFETIME = timedelta(days=1)


def access_lifetime():
    """Resolve the lifetime per call, never at import.

    **Public because it has a caller outside this module.** The login view's cookie
    ``max_age`` reads it too (``organizer/google_auth_views.py``), so that the cookie
    and the ``exp`` of the token it carries resolve the setting the same way —
    including when the setting is absent and this default applies. A bare
    ``settings.AUTH_JWT_ACCESS_LIFETIME`` at the mint site would be an
    ``AttributeError``/500 mid-callback in exactly that case.

    A module-level ``getattr(settings, ...)`` is evaluated once at import, which
    makes ``override_settings`` a silent no-op — the expired-token test would then
    mint a *valid* token and fail pointing at the wrong file.

    The ``getattr`` default is kept so the setting stays optional and
    ``override_settings`` keeps working. ``DEFAULT_ACCESS_LIFETIME`` is therefore a
    second copy of the number ``settings.py`` declares, and that is the price of the
    fallback: it is the value used *only* when the setting is missing, which
    ``organizer.E001`` reports as an error anyway.

    :raises ImproperlyConfigured: the setting is not a ``timedelta``. An ``int``
        used to raise a bare ``TypeError`` out of ``issue_access_token`` — a 500 on
        the login path, blamed on the wrong module.

    Sign is deliberately **not** checked here. A non-positive lifetime is an
    operator error, caught by the ``organizer.E001`` system check; checking it at
    runtime too would make
    ``override_settings(AUTH_JWT_ACCESS_LIFETIME=timedelta(seconds=-10))`` — the
    only way to mint an expired token for a test — impossible.
    """
    lifetime = getattr(settings, "AUTH_JWT_ACCESS_LIFETIME", DEFAULT_ACCESS_LIFETIME)
    if not isinstance(lifetime, timedelta):
        raise ImproperlyConfigured(
            "AUTH_JWT_ACCESS_LIFETIME must be a datetime.timedelta, got "
            f"{type(lifetime).__name__}"
        )
    return lifetime


def _normalize_user_id(value):
    """Coerce a ``user_id`` claim to ``int``, or raise ``ValueError``.

    SimpleJWT casts ``user_id`` to ``str`` unconditionally (5.5.1 tokens.py:228),
    so a live cookie carries ``"7"`` while we mint ``7``. Normalizing here means no
    caller has to care which minted the token it is holding — otherwise every
    consumer that compares, caches, or logs the claim gets two behaviours across
    the fleet for the full 1-day cookie window.

    ``bool`` and ``float`` are rejected rather than coerced: ``pk=True`` and
    ``pk=1.9`` both reach the database as ``1`` and would silently resolve to a
    real, wrong user.
    """
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError(f"user_id must be an int or str, got {type(value).__name__}")
    return int(value)


def issue_access_token(user):
    """Mint a signed access token for ``user``.

    :raises TokenUserError: ``user`` has no primary key (unsaved, or
        ``AnonymousUser``). Minting anyway produces a fully valid signature over
        ``"user_id": null``, which passes verification — ``require`` checks that a
        claim is present, not that it is usable — and fails only one layer later at
        ``get_user_from_claims``. Reject at the point the caller made the mistake.
    :returns: the encoded JWT as ``str`` (PyJWT 2.x returns str, not bytes).
    """
    if getattr(user, "pk", None) is None:
        raise TokenUserError("cannot issue a token for a user without a primary key")

    now = timezone.now()  # aware UTC; datetime.utcnow() is naive and deprecated
    payload = {
        "token_type": ACCESS_TOKEN_TYPE,
        "exp": now + access_lifetime(),
        "iat": now,
        "jti": uuid4().hex,
        "user_id": user.pk,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token):
    """Verify ``token`` and return its claims.

    :raises ExpiredToken: ``exp`` is in the past.
    :raises InvalidToken: anything else — including a non-``str`` input, because
        1.4 feeds this ``request.COOKIES.get("access_token")``, which is ``None``
        whenever the cookie is absent.
    :returns: the claims dict, with ``user_id`` normalized to ``int``.
    """
    if not isinstance(token, str):
        raise InvalidToken(f"token must be a str, got {type(token).__name__}")

    try:
        claims = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": REQUIRED_CLAIMS},
        )
    # Narrow before broad: ExpiredSignatureError subclasses InvalidTokenError, so
    # the reverse order would collapse ExpiredToken into InvalidToken and quietly
    # stop distinguishing the expired path.
    except jwt.ExpiredSignatureError as exc:
        raise ExpiredToken("token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidToken(str(exc) or "token is invalid") from exc
    # Not every PyJWT failure is an InvalidTokenError: InvalidKeyError and the
    # PyJWK* family subclass PyJWTError directly. Without this clause they cross
    # the boundary raw, breaking the module's contract and turning 1.4's
    # authentication path into a 500 where it owes a 401.
    except jwt.PyJWTError as exc:
        raise InvalidToken(str(exc) or "token is invalid") from exc

    if claims.get("token_type") != ACCESS_TOKEN_TYPE:
        # A refresh token presented as an access token must not authenticate.
        raise InvalidToken(f"expected token_type {ACCESS_TOKEN_TYPE!r}")

    try:
        claims["user_id"] = _normalize_user_id(claims["user_id"])
    except ValueError as exc:
        raise InvalidToken("user_id claim is unusable") from exc

    return claims


def get_user_from_claims(claims):
    """Resolve the user a verified token points at.

    :raises TokenUserError: no such user, an unusable ``user_id``, or the user is
        inactive. A verified signature says the token is ours; it says nothing
        about the account still existing.
    """
    user_model = get_user_model()
    try:
        # Normalized again rather than assumed: this is a public entry point, and
        # 1.4 may hold a claims dict it did not get from verify_access_token.
        user = user_model.objects.get(pk=_normalize_user_id(claims["user_id"]))
    except (KeyError, TypeError, ValueError, user_model.DoesNotExist) as exc:
        raise TokenUserError("token does not resolve to a user") from exc

    if not user.is_active:
        raise TokenUserError("user is inactive")

    return user
