"""AD-1 layering guard: the dependency arrows are permission, and nothing points back up.

Static (AST) analysis of the source text — the modules under inspection are never
imported, so a violation buried inside a function body is caught just the same.
"""

import ast
import pathlib

from django.test import SimpleTestCase

ORGANIZER = pathlib.Path(__file__).resolve().parent.parent

# Prefix match on the dotted module path: "x" matches "x" and "x.anything".
FORBIDDEN = {
    "services": ("rest_framework", "organizer.youtube", "django.http", "django.urls"),
    "youtube": ("organizer.models", "organizer.services", "django.db"),
    # organizer.models / django.db: AD-1 makes organizer.services the only writer of
    # application state, so a view reaching the ORM directly bypasses the whole rule.
    "api": ("organizer.youtube", "organizer.models", "django.db"),
    # rest_framework_simplejwt turns Story 1.3's AC3 from a one-time grep into a
    # standing gate: the first-party PyJWT module must never reach back for the
    # library it replaces (AD-14). The other four encode the package docstring's
    # contract — authentication answers "who is this request", nothing more.
    #
    # `rest_framework` itself is deliberately NOT forbidden: Story 1.4 puts a
    # BaseAuthentication subclass in this package. Note the prefix match is exact
    # or dotted, so "rest_framework" and "rest_framework_simplejwt" stay distinct.
    #
    # organizer.models is NOT forbidden either: get_user_from_claims reads
    # django.contrib.auth's User, and reading is not the mutation AD-1 governs.
    # Do not "tighten" this into a false positive.
    "auth": (
        "rest_framework_simplejwt",
        "organizer.api",
        "organizer.services",
        "organizer.sync",
        "organizer.youtube",
    ),
}


def _imported_modules(tree):
    """Yield (lineno, dotted_path) for every import, resolving relative ones.

    For `from X import a, b` both the package path `X` and each candidate submodule
    path `X.a` / `X.b` are yielded. Without the submodule candidates the guard is
    blind to `from . import youtube`, `from organizer import youtube` and
    `from django import http` — the plainest spellings of the violations it exists
    to catch, since their `node.module` is only `organizer` / `django`.

    Relative resolution is deliberately coarse: `from .x import y` inside a layer
    package maps to `organizer.x`. That is correct for the single level of nesting
    these packages have; tighten it if a later story nests deeper.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # from . / .. import x
                base = f"organizer.{node.module or ''}".rstrip(".")
            else:
                base = node.module or ""
            yield node.lineno, base
            for alias in node.names:
                if alias.name != "*":
                    yield node.lineno, f"{base}.{alias.name}" if base else alias.name


def _violates(module, forbidden_prefix):
    return module == forbidden_prefix or module.startswith(forbidden_prefix + ".")


# --- AD-1's write ban, as a second and independent check (Story 1.4) -------------
#
# The import guard above structurally cannot express this. Forbidding `django.db`
# would block `transaction` while leaving `User.objects.update()` wide open, and
# `organizer/auth/` legitimately *reads* django.contrib.auth's User — a static import
# check cannot tell a read from a write. So this walks call sites instead of imports.
#
# Directories to scan for writes. `auth/` is the one that matters today: Story 1.4
# put a DRF authentication class there, which is the first code in a layer package
# that could plausibly write (a `last_login` touch is the classic one).
WRITE_SCANNED_LAYERS = ("auth",)

#: Unconditional: these spellings are only ever an ORM write in this codebase.
#:
#: The `a`-prefixed forms are Django's async ORM, fully supported on Django 6.0 —
#: `await user.asave()` inside organizer/auth/ is the single most plausible future
#: violation on this stack, and listing only the sync spellings would wave it
#: through. Story 1.2's review found the *import* detector blind to the most
#: idiomatic spelling of a violation; this is that lesson applied here.
ALWAYS_WRITE_CALLS = ("save", "delete", "asave", "adelete")

#: Conditional — flagged only when the receiver chain looks like a queryset.
#:
#: The receiver condition is load-bearing, not caution. An unconditional `.update()`
#: rule flags `dict.update()`, `set().update()` and `claims.update()` — all of which
#: appear in perfectly correct auth code — and the first false positive is invariably
#: "fixed" by deleting the rule. A rule that cries wolf is a rule that gets removed,
#: so it must not cry wolf.
#:
#: The false negative it buys, stated plainly so the next reader does not over-trust
#: the gate: a write through a receiver this walk cannot resolve to a marker is not
#: flagged. `QUERYSET_LOCAL_HINTS` recovers the common local-variable spelling; a
#: queryset passed in as an arbitrarily-named parameter still escapes. Raw SQL
#: (`cursor.execute`) and related-manager writes (`.add`/`.set`/`.remove`/`.clear`)
#: are likewise out of reach of a call-site rule and are not claimed to be covered.
QUERYSET_WRITE_CALLS = (
    "create",
    "get_or_create",
    "update_or_create",
    "bulk_create",
    "bulk_update",
    "update",
    # Async ORM, same reasoning as ALWAYS_WRITE_CALLS.
    "acreate",
    "aget_or_create",
    "aupdate_or_create",
    "abulk_create",
    "abulk_update",
    "aupdate",
)

#: What makes a receiver chain a queryset rather than a plain object.
QUERYSET_MARKERS = ("objects", "filter", "exclude", "all")

#: Local names that conventionally hold a queryset. `qs = User.objects.filter(...)`
#: followed by `qs.update(...)` walks back to the bare name `qs`, which matches no
#: marker above — the split-across-two-statements spelling of exactly the write the
#: markers are meant to catch. These names are specific enough not to collide with a
#: `dict`/`set` local in auth code, which is what the receiver condition protects.
#:
#: Kept deliberately to the two names that mean "queryset" and nothing else. `users`,
#: `rows`, `objs` were considered and rejected: each is an equally plausible name for
#: a dict, and a rule that flags `users.update(...)` on a mapping is the false
#: positive that gets the whole rule deleted.
QUERYSET_LOCAL_HINTS = ("qs", "queryset")


def _receiver_names(node):
    """Yield every name in the receiver chain of an attribute access.

    `User.objects.filter(pk=1).update` walks back to 'filter', 'objects', 'User' —
    the call in the middle is stepped over via its `.func`, which is what lets a
    queryset be recognised however long the chain is.
    """
    while True:
        if isinstance(node, ast.Attribute):
            yield node.attr
            node = node.value
        elif isinstance(node, ast.Call):
            node = node.func
        elif isinstance(node, ast.Subscript):
            node = node.value
        elif isinstance(node, ast.Await):
            # `await User.objects.aget_or_create(...)` — step over the await or the
            # walk stops here and the chain's markers are never seen.
            node = node.value
        elif isinstance(node, ast.Name):
            yield node.id
            return
        else:
            return


def _write_calls(tree):
    """Yield (lineno, method) for every call site that writes application state."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        method = node.func.attr
        if method in ALWAYS_WRITE_CALLS:
            yield node.lineno, method
        elif method in QUERYSET_WRITE_CALLS:
            receivers = set(_receiver_names(node.func.value))
            if receivers & (set(QUERYSET_MARKERS) | set(QUERYSET_LOCAL_HINTS)):
                yield node.lineno, method


class LayerDependencyDirectionTests(SimpleTestCase):
    """AD-1: nothing points back up. Guards the direction for every later story."""

    def test_layers_do_not_import_upward(self):
        violations = []
        for layer, forbidden in FORBIDDEN.items():
            layer_dir = ORGANIZER / layer
            self.assertTrue(
                layer_dir.is_dir(),
                f"organizer/{layer}/ does not exist — the layer skeleton is incomplete (AD-1).",
            )
            for path in sorted(layer_dir.rglob("*.py")):
                # encoding is explicit: under a C/POSIX locale the default would be
                # ASCII and a single non-ASCII byte would crash the guard instead of
                # reporting a verdict.
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                # One import statement yields several candidate paths (see
                # _imported_modules), so report at most one violation per line.
                reported = set()
                for lineno, module in _imported_modules(tree):
                    for bad in forbidden:
                        if _violates(module, bad) and lineno not in reported:
                            reported.add(lineno)
                            violations.append(
                                f"{path.relative_to(ORGANIZER)}:{lineno} imports "
                                f"'{module}' — forbidden in organizer/{layer}/ (AD-1)."
                            )
        self.assertEqual(violations, [], "Layer dependency violations:\n" + "\n".join(violations))

    def test_guard_detects_a_forbidden_import(self):
        """The guard's own detector, proven on synthetic source.

        Without this, a refactor that broke _imported_modules would leave the suite
        green over a guard that can no longer see anything.
        """
        cases = [
            ("import rest_framework", "services", "rest_framework"),
            ("from rest_framework.views import APIView", "services", "rest_framework.views"),
            ("from .youtube import client", "services", "organizer.youtube"),
            ("from organizer.services import x", "youtube", "organizer.services"),
            ("from django.db import models", "youtube", "django.db"),
            # `from <package> import <submodule>`: node.module is only "organizer" /
            # "django", so these are invisible unless the alias names are inspected.
            ("from . import youtube", "services", "organizer.youtube"),
            ("from .. import youtube", "services", "organizer.youtube"),
            ("from organizer import youtube", "services", "organizer.youtube"),
            ("from django import http", "services", "django.http"),
            ("from django import urls", "services", "django.urls"),
            ("from organizer import models", "youtube", "organizer.models"),
            ("from django import db", "youtube", "django.db"),
            # AD-1: the api layer may not reach the ORM directly — services is the
            # only writer of application state.
            ("from organizer.models import UserSocialToken", "api", "organizer.models"),
            ("from django.db import transaction", "api", "django.db"),
            # AD-14: the first-party token module may not reach back for the
            # library it replaces. Both spellings — the `from X import name` one
            # is how the violation is actually written.
            ("import rest_framework_simplejwt", "auth", "rest_framework_simplejwt"),
            (
                "from rest_framework_simplejwt.tokens import AccessToken",
                "auth",
                "rest_framework_simplejwt.tokens",
            ),
            ("from organizer.services import tagging", "auth", "organizer.services"),
            ("from organizer import services", "auth", "organizer.services"),
            ("from . import youtube", "auth", "organizer.youtube"),
        ]
        for source, layer, expected in cases:
            with self.subTest(source=source):
                found = [m for _, m in _imported_modules(ast.parse(source))]
                self.assertIn(expected, found)
                self.assertTrue(
                    any(_violates(m, bad) for m in found for bad in FORBIDDEN[layer]),
                    f"guard failed to flag {source!r} inside organizer/{layer}/",
                )

    def test_guard_allows_a_legitimate_import(self):
        allowed = [
            ("from organizer.services import tagging", "api"),
            ("from .models import UserSocialToken", "services"),
            ("import googleapiclient.discovery", "youtube"),
            # The submodule candidates must not turn every `from X import name` into
            # a false positive: only the dotted path matters, not the bound symbol.
            ("from rest_framework.views import APIView", "api"),
            ("from django.conf import settings", "services"),
            ("from organizer.services.tagging import apply_tags", "api"),
            # auth/ must keep importing these: `jwt` is the whole point (1.3), and
            # rest_framework arrives with 1.4's BaseAuthentication subclass. A rule
            # that forbade either would be discovered next story as an obstacle and
            # "fixed" by weakening the guard.
            ("import jwt", "auth"),
            ("from rest_framework.authentication import BaseAuthentication", "auth"),
            ("from django.contrib.auth import get_user_model", "auth"),
            ("from .errors import InvalidToken", "auth"),
        ]
        for source, layer in allowed:
            with self.subTest(source=source):
                found = [m for _, m in _imported_modules(ast.parse(source))]
                self.assertFalse(
                    any(_violates(m, bad) for m in found for bad in FORBIDDEN[layer]),
                    f"guard wrongly flagged {source!r} inside organizer/{layer}/",
                )


class LayerWriteBanTests(SimpleTestCase):
    """AD-1's write ban, enforced over `WRITE_SCANNED_LAYERS` — today `auth/` alone.

    The authentication class Story 1.4 added answers "who is this request" and
    nothing more — no `last_login` touch, no `save()`, no queryset update. This turns
    that sentence from a docstring into a gate.

    **Scope, stated so the gate is not read as more than it is:** AD-1's full claim
    is that `organizer.services` is the *only* writer of application state. This
    checks one directory. `organizer/api/`, `organizer/youtube/`, `organizer/sync/`
    and `google_auth_views.py` are outside it — the last of those genuinely does call
    `User.objects.get_or_create` and `UserSocialToken.objects.update_or_create`, which
    is recorded in `deferred-work.md` and owned by Story 6.1. Widening
    `WRITE_SCANNED_LAYERS` is how this becomes AD-1's full claim; until then it is a
    guard over the layer that has code in it.
    """

    def test_scanned_layers_contain_no_orm_writes(self):
        violations = []
        for layer in WRITE_SCANNED_LAYERS:
            layer_dir = ORGANIZER / layer
            self.assertTrue(
                layer_dir.is_dir(),
                f"organizer/{layer}/ does not exist — the layer skeleton is incomplete (AD-1).",
            )
            for path in sorted(layer_dir.rglob("*.py")):
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                for lineno, method in _write_calls(tree):
                    violations.append(
                        f"{path.relative_to(ORGANIZER)}:{lineno} calls '{method}()' — "
                        f"organizer/{layer}/ must not write application state (AD-1)."
                    )
        self.assertEqual(violations, [], "Layer write violations:\n" + "\n".join(violations))

    def test_write_guard_detects_a_write(self):
        """The detector, proven on synthetic source — the positive direction."""
        cases = [
            "User.objects.filter(pk=1).update(last_login=None)",
            "get_user_model().objects.filter(pk=1).update(last_login=None)",
            "user.save()",
            "user.save(update_fields=['last_login'])",
            "obj.delete()",
            "User.objects.create(username='x')",
            "User.objects.get_or_create(username='x')",
            "UserSocialToken.objects.update_or_create(user=user)",
            "Model.objects.bulk_create([])",
            "Model.objects.bulk_update([], ['f'])",
            "User.objects.all().update(is_active=False)",
            "User.objects.exclude(pk=1).update(is_active=False)",
            # The write hidden one level down a chain, and inside a function body —
            # exactly where an import-based guard would see nothing at all.
            "def f():\n    User.objects.filter(pk=1).update(last_login=None)",
            # Django 6.0's async ORM. Listing only the sync spellings is how a guard
            # ships blind to the most plausible violation on this stack.
            "async def f():\n    await user.asave()",
            "async def f():\n    await obj.adelete()",
            "async def f():\n    await User.objects.acreate(username='x')",
            "async def f():\n    await User.objects.aget_or_create(username='x')",
            "async def f():\n    await User.objects.filter(pk=1).aupdate(is_active=False)",
            "async def f():\n    await UserSocialToken.objects.aupdate_or_create(user=user)",
            # The queryset split across two statements — the same write as the first
            # case, spelled the way it is actually written when the filter is reused.
            "qs = User.objects.filter(pk=1)\nqs.update(last_login=None)",
            "queryset = User.objects.all()\nqueryset.update(is_active=False)",
        ]
        for source in cases:
            with self.subTest(source=source):
                self.assertTrue(
                    list(_write_calls(ast.parse(source))),
                    f"write guard failed to flag {source!r}",
                )

    def test_write_guard_allows_reads_and_non_orm_updates(self):
        """The negative direction, which matters as much as the positive one.

        Story 1.2's review found the import detector blind to the most idiomatic
        spelling of a violation because every self-test case was a form it already
        handled. The inverse failure is a guard that flags `dict.update()` on its
        first real run and gets deleted for it — so every plain-object spelling of
        these method names is pinned here as *allowed*.
        """
        allowed = [
            # Reads: the auth layer does these legitimately.
            "user_model.objects.get(pk=1)",
            "User.objects.filter(pk=1).first()",
            "User.objects.all()",
            "User.objects.filter(pk=1).exists()",
            # Plain-object `.update()` — dicts, sets, and anything else.
            "claims.update({'x': 1})",
            "headers.update(other)",
            "set().update([1])",
            "payload.update(overrides)",
            # A `.create` that is not a manager call.
            "flow.create(scopes)",
            "logging.getLogger(__name__).info('x')",
            # Async *reads* — the `a`-prefixed write list must not swallow these.
            "async def f():\n    await User.objects.aget(pk=1)",
            "async def f():\n    await User.objects.filter(pk=1).aexists()",
            # Plain-object `.update()` on names the local hints deliberately exclude,
            # pinning the narrowness of QUERYSET_LOCAL_HINTS as intentional.
            "users.update(other)",
            "rows.update(other)",
        ]
        for source in allowed:
            with self.subTest(source=source):
                self.assertEqual(
                    list(_write_calls(ast.parse(source))),
                    [],
                    f"write guard wrongly flagged {source!r}",
                )
