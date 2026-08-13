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
    "api": ("organizer.youtube",),
}


def _imported_modules(tree):
    """Yield (lineno, dotted_path) for every import, resolving relative ones.

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
                yield node.lineno, f"organizer.{node.module or ''}".rstrip(".")
            else:
                yield node.lineno, node.module or ""


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
                tree = ast.parse(path.read_text(), filename=str(path))
                for lineno, module in _imported_modules(tree):
                    for bad in forbidden:
                        if _violates(module, bad):
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
        ]
        for source, layer in allowed:
            with self.subTest(source=source):
                found = [m for _, m in _imported_modules(ast.parse(source))]
                self.assertFalse(
                    any(_violates(m, bad) for m in found for bad in FORBIDDEN[layer]),
                    f"guard wrongly flagged {source!r} inside organizer/{layer}/",
                )
