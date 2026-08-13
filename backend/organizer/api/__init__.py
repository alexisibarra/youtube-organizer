"""API layer (AD-1).

Owns: HTTP concerns — request/response handling, serialization, query-parameter
parsing and validation, pagination.

Must never: contain domain logic, or call the YouTube Data API. Domain operations
belong to ``organizer.services``; every YouTube call belongs to ``organizer.youtube``
and is reached only from ``organizer.sync``.
"""
