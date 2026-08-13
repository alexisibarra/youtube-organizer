"""The typed errors token verification raises (AD-14).

A small, closed hierarchy, deliberately in its own module: Story 1.4's DRF
authentication class catches these without importing the token machinery, and no
PyJWT exception type ever reaches a caller.

Must never: contain domain logic — this is the auth layer's contract, nothing more.
"""


class TokenError(Exception):
    """Base for every token failure. This is what callers catch."""


class InvalidToken(TokenError):
    """The token cannot be trusted.

    Malformed, tampered, wrongly signed, signed with an unexpected algorithm,
    missing a required claim, or carrying the wrong ``token_type``.
    """


class ExpiredToken(TokenError):
    """``exp`` is in the past.

    A separate type on purpose: "log in again" is a different answer to the caller
    than "this token is garbage", and the frontend renders them differently.
    """


class TokenUserError(TokenError):
    """The token verifies, but resolves to no usable user.

    The user row was deleted, is inactive, or the ``user_id`` claim is unusable.
    """
