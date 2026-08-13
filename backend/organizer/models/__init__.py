"""Models layer (AD-1).

Owns: the schema — fields, constraints and managers.

Must never: contain multi-entity business rules. Those belong to
``organizer.services``, the only writer of application state.

Django imports ``<app>.models`` at app-load, so every model must be reachable
from this namespace: a class that is not re-exported here is invisible to the ORM
and ``makemigrations`` will propose deleting its table.
"""

from .user_social_token import UserSocialToken

__all__ = ["UserSocialToken"]
