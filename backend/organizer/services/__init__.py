"""Services layer (AD-1).

Owns: all domain operations. This is the only writer of application state — every
mutation path in the system goes through here.

Must never: import DRF, touch ``request``, or call the YouTube Data API. Services
know nothing about HTTP; that keeps them callable from both a request thread
(``organizer.api``) and a management command (``organizer.sync``).
"""
