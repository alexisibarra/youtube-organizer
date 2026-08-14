"""Django system checks for this app's settings (AD-14).

`manage.py check` is pre-push layer 4/6, so a check here fails the push. It is *not*
a step of its own in `ci.yml` — CI runs it implicitly, because Django runs the system
checks inside `makemigrations`, `migrate` and `test`, all three of which the test job
does execute. Either way an operator's bad value fails the build rather than reaching
a user; the mechanism is worth stating accurately, because "there is a `check` step"
is the kind of claim a later story would rely on and find missing.

The runtime deliberately does not duplicate the sign check: see
`organizer/auth/tokens.py::access_lifetime`.
"""

from datetime import timedelta

from django.conf import settings
from django.core.checks import Error

#: Below this and `int(total_seconds())` floors to 0, which `set_cookie` treats as
#: "expire immediately" — the same user-visible failure as a negative lifetime, so it
#: is the same error rather than a separate one.
MIN_ACCESS_LIFETIME = timedelta(seconds=1)

#: An upper bound exists because `now + lifetime` raises OverflowError near
#: `timedelta.max` — a 500 on the login path from a settings typo. Ten years is far
#: past anything defensible for an access token and nowhere near the overflow edge,
#: so it fails the value long before arithmetic does.
MAX_ACCESS_LIFETIME = timedelta(days=3650)


def check_access_token_lifetime(app_configs, **kwargs):
    """AUTH_JWT_ACCESS_LIFETIME must be a timedelta between one second and ten years.

    A non-positive value mints access tokens that are already expired when the login
    view sets them, and sets the cookie's `max_age` to zero or negative — the browser
    drops it immediately. Login would appear to succeed and every subsequent request
    would 401, with nothing in the logs pointing at the setting.

    Both bounds are checked, not just the sign: a positive value under a second
    (`timedelta(milliseconds=500)`) floors to `max_age=0` and fails identically, and a
    value near `timedelta.max` overflows `now + lifetime` inside `issue_access_token`.
    A check that only rejects `<= 0` leaves both of those green.
    """
    lifetime = getattr(settings, "AUTH_JWT_ACCESS_LIFETIME", None)
    if (
        isinstance(lifetime, timedelta)
        and MIN_ACCESS_LIFETIME <= lifetime <= MAX_ACCESS_LIFETIME
    ):
        return []
    return [
        Error(
            "AUTH_JWT_ACCESS_LIFETIME must be a datetime.timedelta between "
            f"{MIN_ACCESS_LIFETIME} and {MAX_ACCESS_LIFETIME}, got {lifetime!r}.",
            hint="Set it in settings.py, e.g. AUTH_JWT_ACCESS_LIFETIME = timedelta(days=1).",
            id="organizer.E001",
        )
    ]
