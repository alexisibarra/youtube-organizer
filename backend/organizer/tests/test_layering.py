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
        ]
        for source, layer in allowed:
            with self.subTest(source=source):
                found = [m for _, m in _imported_modules(ast.parse(source))]
                self.assertFalse(
                    any(_violates(m, bad) for m in found for bad in FORBIDDEN[layer]),
                    f"guard wrongly flagged {source!r} inside organizer/{layer}/",
                )
