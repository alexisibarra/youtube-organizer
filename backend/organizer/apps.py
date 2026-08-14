from django.apps import AppConfig
from django.core.checks import register


class OrganizerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'organizer'

    def ready(self):
        # Registered here, not at module import: settings are guaranteed configured
        # by the time ready() runs, and `manage.py check` picks the check up from the
        # app registry (AD-14 — see organizer/checks.py).
        from .checks import check_access_token_lifetime

        register(check_access_token_lifetime)
