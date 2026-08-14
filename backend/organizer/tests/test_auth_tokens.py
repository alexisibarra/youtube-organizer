"""First-party PyJWT token issue/verify (AD-14, Story 1.3).

AC1 — issue/verify round-trips back to the same user.
AC2 — every rejection path raises its own typed error.

The real library is exercised throughout: no PyJWT mocking, no network (AD-16).
"""

import base64
import json
from datetime import timedelta

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from organizer.auth.errors import (
    ExpiredToken,
    InvalidToken,
    TokenError,
    TokenUserError,
)
from organizer.auth.tokens import (
    access_lifetime,
    get_user_from_claims,
    issue_access_token,
    verify_access_token,
)

User = get_user_model()

# Long enough to keep PyJWT's InsecureKeyLengthWarning out of the test output —
# the attacker's key in these fixtures is wrong, not weak.
OTHER_KEY = "an-entirely-different-signing-key-of-sufficient-length"


def _decode_segment(segment):
    """Decode one base64url JWT segment without verifying anything."""
    padded = segment + "=" * (-len(segment) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


class IssueAndVerifyRoundTripTests(TestCase):
    """AC1: mint, verify, and land back on the same user."""

    def setUp(self):
        self.user = User.objects.create_user(username="round-trip", password="x")

    def test_token_is_three_dot_separated_segments(self):
        token = issue_access_token(self.user)
        self.assertIsInstance(token, str)
        self.assertEqual(len(token.split(".")), 3)

    def test_header_is_hs256_jwt(self):
        token = issue_access_token(self.user)
        self.assertEqual(
            jwt.get_unverified_header(token), {"alg": "HS256", "typ": "JWT"}
        )

    def test_round_trip_returns_the_expected_claim_set(self):
        claims = verify_access_token(issue_access_token(self.user))
        self.assertEqual(
            set(claims), {"token_type", "exp", "iat", "jti", "user_id"}
        )
        self.assertEqual(claims["token_type"], "access")
        self.assertEqual(claims["user_id"], self.user.pk)
        self.assertIsInstance(claims["user_id"], int)
        self.assertIsInstance(claims["jti"], str)

    def test_round_trip_resolves_that_same_user(self):
        claims = verify_access_token(issue_access_token(self.user))
        resolved = get_user_from_claims(claims)
        self.assertEqual(resolved.pk, self.user.pk)

    def test_expiry_is_exactly_one_lifetime_after_issue(self):
        """Read the lifetime from the module, not a re-typed literal.

        A copied `timedelta(days=1)` re-encodes the constant instead of testing
        it, and fails the moment a deployment sets AUTH_JWT_ACCESS_LIFETIME.
        """
        claims = verify_access_token(issue_access_token(self.user))
        self.assertEqual(
            claims["exp"] - claims["iat"], int(access_lifetime().total_seconds())
        )

    @override_settings(AUTH_JWT_ACCESS_LIFETIME=timedelta(minutes=5))
    def test_lifetime_setting_is_read_per_call_not_at_import(self):
        claims = verify_access_token(issue_access_token(self.user))
        self.assertEqual(claims["exp"] - claims["iat"], 300)

    def test_iat_is_in_the_past_or_now(self):
        claims = verify_access_token(issue_access_token(self.user))
        self.assertLessEqual(claims["iat"], int(timezone.now().timestamp()))

    def test_jti_differs_between_tokens(self):
        first = verify_access_token(issue_access_token(self.user))
        second = verify_access_token(issue_access_token(self.user))
        self.assertNotEqual(first["jti"], second["jti"])


class RejectionPathTests(TestCase):
    """AC2: one test per rejection path, each asserting the narrow type."""

    def setUp(self):
        self.user = User.objects.create_user(username="reject", password="x")

    def _payload(self, **overrides):
        now = timezone.now()
        payload = {
            "token_type": "access",
            "exp": now + timedelta(days=1),
            "iat": now,
            "jti": "deadbeef",
            "user_id": self.user.pk,
        }
        payload.update(overrides)
        return payload

    @override_settings(AUTH_JWT_ACCESS_LIFETIME=timedelta(seconds=-10))
    def test_expired_token_raises_expired_token(self):
        token = issue_access_token(self.user)
        with self.assertRaises(ExpiredToken):
            verify_access_token(token)

    @override_settings(AUTH_JWT_ACCESS_LIFETIME=timedelta(seconds=-10))
    def test_expired_token_is_not_swallowed_by_invalid_token(self):
        """ExpiredSignatureError subclasses InvalidTokenError — order matters."""
        token = issue_access_token(self.user)
        with self.assertRaises(ExpiredToken) as ctx:
            verify_access_token(token)
        self.assertNotIsInstance(ctx.exception, InvalidToken)
        self.assertIsInstance(ctx.exception, TokenError)

    def test_tampered_payload_raises_invalid_token(self):
        header, payload, signature = issue_access_token(self.user).split(".")
        flipped = ("B" if payload[5] != "B" else "C") + payload[6:]
        tampered = f"{header}.{payload[:5]}{flipped}.{signature}"
        with self.assertRaises(InvalidToken):
            verify_access_token(tampered)

    def test_wrong_signing_key_raises_invalid_token(self):
        token = jwt.encode(self._payload(), OTHER_KEY, algorithm="HS256")
        with self.assertRaises(InvalidToken):
            verify_access_token(token)

    def test_unsigned_alg_none_token_raises_invalid_token(self):
        token = jwt.encode(self._payload(), key="", algorithm="none")
        with self.assertRaises(InvalidToken):
            verify_access_token(token)

    def test_algorithm_substitution_raises_invalid_token(self):
        """A valid HS512 token signed with the real key must still be rejected."""
        token = jwt.encode(self._payload(), settings.SECRET_KEY, algorithm="HS512")
        with self.assertRaises(InvalidToken):
            verify_access_token(token)

    def test_malformed_garbage_raises_invalid_token(self):
        for garbage in ("not.a.token", "", "     ", "abc", "a.b", "a.b.c.d"):
            with self.subTest(token=garbage):
                with self.assertRaises(InvalidToken):
                    verify_access_token(garbage)

    def test_missing_required_claim_raises_invalid_token(self):
        for claim in ("exp", "iat", "token_type", "user_id"):
            with self.subTest(missing=claim):
                payload = self._payload()
                del payload[claim]
                token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
                with self.assertRaises(InvalidToken):
                    verify_access_token(token)

    def test_refresh_token_type_raises_invalid_token(self):
        token = jwt.encode(
            self._payload(token_type="refresh"), settings.SECRET_KEY, algorithm="HS256"
        )
        with self.assertRaises(InvalidToken):
            verify_access_token(token)

    def test_non_string_input_raises_invalid_token(self):
        """1.4 feeds this request.COOKIES.get("access_token") — None when absent."""
        for value in (None, b"not.a.token", 12345, [], {}):
            with self.subTest(value=repr(value)):
                with self.assertRaises(InvalidToken):
                    verify_access_token(value)

    def test_every_rejection_is_a_token_error(self):
        """The base contract 1.4 catches on."""
        with self.assertRaises(TokenError):
            verify_access_token(None)

    def test_no_pyjwt_exception_escapes(self):
        """PyJWT types must never cross the module boundary."""
        for token in (None, "not.a.token", jwt.encode({}, OTHER_KEY, algorithm="HS256")):
            with self.subTest(token=repr(token)):
                try:
                    verify_access_token(token)
                except TokenError:
                    pass
                except jwt.PyJWTError as exc:  # pragma: no cover - the failure we guard
                    self.fail(f"PyJWT exception escaped: {exc!r}")

    def test_pyjwt_error_outside_the_invalid_token_subtree_is_wrapped(self):
        """InvalidKeyError subclasses PyJWTError directly, not InvalidTokenError.

        Catching only InvalidTokenError leaves it to cross the boundary raw — a
        500 where 1.4 owes a 401. Every input in the test above lands inside the
        InvalidTokenError subtree, so only a key failure reaches this branch.
        """
        self.assertFalse(issubclass(jwt.InvalidKeyError, jwt.InvalidTokenError))
        token = issue_access_token(self.user)
        pem_shaped_key = "-----BEGIN PUBLIC KEY-----\nnot-a-real-key\n-----END PUBLIC KEY-----"
        with override_settings(SECRET_KEY=pem_shaped_key):
            with self.assertRaises(InvalidToken):
                verify_access_token(token)

    def test_unusable_user_id_claim_raises_invalid_token(self):
        """A signed token carrying a bool or float must not resolve to pk 1.

        `pk=True` and `pk=1.9` both reach the database as `1`, so without an
        explicit reject they authenticate as a real, wrong user.
        """
        for user_id in (True, 1.9, [], None):
            with self.subTest(user_id=repr(user_id)):
                token = jwt.encode(
                    self._payload(user_id=user_id), settings.SECRET_KEY, algorithm="HS256"
                )
                with self.assertRaises(InvalidToken):
                    verify_access_token(token)


class UserResolutionTests(TestCase):
    """AC1's round-trip is a real user lookup, not an integer comparison."""

    def setUp(self):
        self.user = User.objects.create_user(username="resolve", password="x")

    def test_deleted_user_raises_token_user_error(self):
        claims = verify_access_token(issue_access_token(self.user))
        self.user.delete()
        with self.assertRaises(TokenUserError):
            get_user_from_claims(claims)

    def test_inactive_user_raises_token_user_error(self):
        claims = verify_access_token(issue_access_token(self.user))
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        with self.assertRaises(TokenUserError):
            get_user_from_claims(claims)

    def test_token_user_error_is_a_token_error(self):
        claims = verify_access_token(issue_access_token(self.user))
        self.user.delete()
        with self.assertRaises(TokenError):
            get_user_from_claims(claims)

    def test_unusable_user_id_raises_token_user_error(self):
        for user_id in (None, "not-an-int", 10**12):
            with self.subTest(user_id=repr(user_id)):
                with self.assertRaises(TokenUserError):
                    get_user_from_claims({"user_id": user_id})

    def test_missing_user_id_claim_raises_token_user_error(self):
        with self.assertRaises(TokenUserError):
            get_user_from_claims({})

    def test_coercible_user_id_types_do_not_resolve_a_wrong_user(self):
        """get_user_from_claims is public: 1.4 may hold a dict verify never saw."""
        for user_id in (True, 1.9):
            with self.subTest(user_id=repr(user_id)):
                with self.assertRaises(TokenUserError):
                    get_user_from_claims({"user_id": user_id})

    def test_string_user_id_still_resolves(self):
        with self.assertRaises(TokenUserError):
            get_user_from_claims({"user_id": "not-an-int"})
        self.assertEqual(
            get_user_from_claims({"user_id": str(self.user.pk)}).pk, self.user.pk
        )


class IssueGuardTests(TestCase):
    """A signed token over a null user_id verifies cleanly — reject at issue."""

    def test_unsaved_user_raises_token_user_error(self):
        with self.assertRaises(TokenUserError):
            issue_access_token(User(username="never-saved"))

    def test_anonymous_user_raises_token_user_error(self):
        from django.contrib.auth.models import AnonymousUser

        with self.assertRaises(TokenUserError):
            issue_access_token(AnonymousUser())


class LegacyWireFormatTests(TestCase):
    """Live cookies minted by the retired code must keep working after the swap.

    Story 1.4 removed `djangorestframework-simplejwt`, so the legacy token is
    hand-minted here rather than produced by the library. This is the payload
    SimpleJWT 5.5.1 writes for an access token: `user_id` cast to `str`
    (tokens.py:228), `token_type: "access"`, a `jti`, `iat`/`exp`, signed HS256 with
    `settings.SECRET_KEY`.

    Do **not** "simplify" this into `issue_access_token`: that mints the `int` form,
    which is the very distinction this test exists to make. Every `access_token`
    cookie in flight at merge time carries the string form and stays valid for a full
    day; without this test the suite goes green over the one regression that would log
    every user out — and it would not surface until the next day.

    Replaces `SimpleJWTCompatibilityTests`, which proved the same property at the cost
    of the dependency this story removes. The rollback direction that suite also
    covered (SimpleJWT reading our token) is gone with the library and cannot be
    asserted without reinstalling it; the claim-shape test below is what remains of it.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="legacy-wire", password="x")

    def _mint_legacy(self, **overrides):
        now = timezone.now()
        payload = {
            "token_type": "access",
            "exp": now + timedelta(days=1),
            "iat": now,
            "jti": "0123456789abcdef0123456789abcdef",
            "user_id": str(self.user.pk),  # the str cast is the whole point
        }
        payload.update(overrides)
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    def test_legacy_token_verifies_and_resolves_the_same_user(self):
        claims = verify_access_token(self._mint_legacy())
        self.assertEqual(claims["token_type"], "access")
        self.assertEqual(get_user_from_claims(claims).pk, self.user.pk)

    def test_legacy_string_user_id_is_normalized_to_int_on_the_way_out(self):
        """The wire carries "7"; verification hands the caller 7.

        Asserting both halves pins the normalization — without it there are two claim
        types across the fleet for the full 1-day cookie window.
        """
        legacy = self._mint_legacy()
        self.assertIsInstance(_decode_segment(legacy.split(".")[1])["user_id"], str)

        legacy_claims = verify_access_token(legacy)
        self.assertIsInstance(legacy_claims["user_id"], int)
        self.assertEqual(legacy_claims["user_id"], self.user.pk)
        self.assertEqual(get_user_from_claims(legacy_claims).pk, self.user.pk)

    def test_our_claim_shape_matches_the_legacy_one(self):
        legacy = self._mint_legacy()
        ours = issue_access_token(self.user)
        self.assertEqual(
            set(_decode_segment(legacy.split(".")[1])),
            set(_decode_segment(ours.split(".")[1])),
        )
        self.assertEqual(
            jwt.get_unverified_header(legacy), jwt.get_unverified_header(ours)
        )
