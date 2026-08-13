"""Auth layer (AD-1).

Owns: token issue and verification over PyJWT, and the DRF authentication class
that reads the ``access_token`` HttpOnly cookie.

Must never: contain domain logic. Authentication answers "who is this request",
nothing more; anything that reads or mutates app state belongs to
``organizer.services``.

This package does not shadow ``django.contrib.auth`` — Python 3 imports are
absolute. Reach this package as ``organizer.auth`` / ``from .auth import ...``.
"""
