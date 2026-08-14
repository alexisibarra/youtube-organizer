"""The DRF authentication class that reads the `access_token` cookie (AD-14).

Owns: turning an HttpOnly `access_token` cookie into `request.user`, for the views
DRF actually authenticates. It replaces `JWTAuthCookieMiddleware`, which copied the
cookie into `HTTP_AUTHORIZATION` for *every* request, app-wide — AD-14 retires that
global request mutation, and this class is what it is retired in favour of. The
cookie contract with the frontend does not move; only this implementation does.

Must never: write application state. AD-1 makes `organizer.services` the only
writer, and `organizer/tests/test_layering.py` enforces it here as an AST rule over
call sites, not as prose. Authentication answers "who is this request", nothing more.

`rest_framework` is the one DRF import the auth layer is allowed — Story 1.3
deliberately left it out of `FORBIDDEN["auth"]` for exactly this class.
"""

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .errors import ExpiredToken, InvalidToken, TokenError, TokenUserError
from .tokens import get_user_from_claims, verify_access_token

#: The cookie the login view sets. Changing this name breaks every live session.
COOKIE_NAME = "access_token"


class CookieJWTAuthentication(BaseAuthentication):
    """Authenticate from the `access_token` cookie, never from a header."""

    def authenticate(self, request):
        """Return `(user, token)`, or `None` when this authenticator has no opinion.

        `None` — not a raise — is what lets `AllowAny` views stay public and lets the
        *permission* layer produce the 401. Raising on a missing cookie would 401 the
        OAuth entry point and break login before it starts.

        The second element becomes `request.auth`. SimpleJWT returned its own token
        object; nothing in this repo reads `request.auth`, so the raw string is the
        honest minimum.
        """
        token = request.COOKIES.get(COOKIE_NAME)
        if not token:
            return None

        # Narrow before broad: ExpiredToken / InvalidToken / TokenUserError are
        # siblings, but TokenError is their base — listing it first would swallow all
        # three and collapse the codes into one. Each code is distinct so the frontend
        # can tell "log in again" from "this token is garbage" later.
        try:
            claims = verify_access_token(token)
            user = get_user_from_claims(claims)
        except ExpiredToken as exc:
            raise AuthenticationFailed("token has expired", code="token_expired") from exc
        except TokenUserError as exc:
            raise AuthenticationFailed(
                "user is unavailable", code="user_unavailable"
            ) from exc
        except InvalidToken as exc:
            raise AuthenticationFailed("token is invalid", code="token_invalid") from exc
        except TokenError as exc:
            # Backstop for a future member of the hierarchy. Deliberately NOT
            # `except Exception`: `verify_access_token` already guarantees no PyJWT
            # type escapes, and a genuine defect owes a 500, not a 401.
            raise AuthenticationFailed("token is invalid", code="token_invalid") from exc

        return (user, token)

    def authenticate_header(self, request):
        """Non-negotiable: this is the mechanism by which a failure is 401, not 403.

        DRF coerces `NotAuthenticated` / `AuthenticationFailed` to 403 unless the
        *first* authenticator supplies a `WWW-Authenticate` header
        (`rest_framework/views.py:458-465`). `BaseAuthentication` returns `None` here
        by default; SimpleJWT's class overrode it, which is the only reason
        `/api/auth/me/` answers 401 today. Omitting the override breaks the frontend's
        session probe silently, with the whole suite still green.
        """
        return 'Bearer realm="api"'
