"""AC1: the layered package skeleton exists and every layer is importable."""

import importlib

from django.test import SimpleTestCase

LAYER_PACKAGES = (
    "organizer.api",
    "organizer.auth",
    "organizer.services",
    "organizer.sync",
    "organizer.youtube",
    "organizer.models",
    "organizer.management.commands",
    "organizer.tests",
)


class LayerPackagesImportTests(SimpleTestCase):
    """Each layer of AD-1 is a real, importable package — not a namespace package."""

    def test_every_layer_package_imports(self):
        for name in LAYER_PACKAGES:
            with self.subTest(package=name):
                module = importlib.import_module(name)
                self.assertTrue(
                    getattr(module, "__file__", None),
                    f"{name} resolved as a namespace package (no __file__); "
                    "it needs a real __init__.py.",
                )

    def test_models_is_a_package_not_a_module(self):
        import organizer.models as models_package

        self.assertTrue(
            models_package.__file__.endswith("organizer/models/__init__.py"),
            f"organizer.models resolved to {models_package.__file__}; expected the package.",
        )

    def test_user_social_token_is_re_exported_from_models(self):
        from organizer.models import UserSocialToken

        self.assertEqual(UserSocialToken._meta.app_label, "organizer")

    def test_layer_packages_carry_a_contract_docstring(self):
        for name in ("organizer.api", "organizer.auth", "organizer.services",
                     "organizer.sync", "organizer.youtube"):
            with self.subTest(package=name):
                module = importlib.import_module(name)
                self.assertTrue(
                    (module.__doc__ or "").strip(),
                    f"{name} has no module docstring; the layer contract is the guardrail "
                    "a later story reads before adding a file here (AD-1).",
                )
