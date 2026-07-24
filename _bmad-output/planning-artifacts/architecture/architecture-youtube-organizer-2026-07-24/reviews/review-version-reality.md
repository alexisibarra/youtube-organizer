# Review — Version & Reality Check

**Lens:** every committed decision must be web-researched or reality-checked, not asserted from
training data. Verify current versions, that each named technology still exists and fits, and
flag anything not confirmed against the web or the existing project.

**Verdict:** FAIL — one critical blocker, one incorrect pin, one under-verified block.

---

## CRITICAL — the Django 6.0 bump is blocked by an auth dependency

`djangorestframework-simplejwt` is at **5.5.1, released 2025-07-21** — roughly twelve months
without a release. Its PyPI trove classifiers list Django **4.2, 5.0, 5.1, 5.2**. Django 6.0 is
**not** listed, and the project changelog contains no mention of Django 6.0 support.

This collides head-on with two spine decisions:

- The Stack table pins **Django 6.0.7**.
- **AD-14** makes cookie-borne SimpleJWT the entire auth invariant, and the shipped code already
  imports `rest_framework_simplejwt.tokens.RefreshToken`.

So the spine currently commits to running the app's *authentication* on a library that does not
claim support for the Django version the spine also commits to. For an auth dependency,
"it probably still works" is not an acceptable posture.

This decision needs the user — it reverses a choice they made with different information.

Sources:
- <https://pypi.org/project/djangorestframework-simplejwt/>
- <https://github.com/jazzband/djangorestframework-simplejwt/blob/master/CHANGELOG.md>

## CRITICAL — DRF pin is wrong

The Stack table says **DRF 3.16.1 (Django 6.0-compatible)**. A follow-up search indicates
**Django 6.0 support landed in DRF 3.17.0 (March 2026)**. The earlier result that produced
3.16.1 was unreliable and should not have been bound. If Django 6.0 survives the blocker above,
the pin must be `>=3.17.0`.

Source: <https://www.django-rest-framework.org/community/release-notes/>

## MEDIUM — the whole frontend pin block is inherited, not verified

`Docs/FRONTEND-STACK.md` is explicitly "mirrored from Accountr" — it records another project's
shipped versions at some past date. The spine inherits that entire table (React Query
`5.100.14`, Tailwind `^3.4.19`, `react-hook-form 7.76.1`, `zod 4.4.3`, `lucide-react ^1.17.0`,
`react-day-picker ^10.0.1`, …) on the strength of the doc being authoritative, not on the
strength of any of them being current.

Only the Next.js pin was independently checked and it is already behind (16.2.x is the LTS line,
and a Next.js security release shipped in July 2026). The Deferred entry names only Next.js; the
same staleness argument applies to every row.

**Recommend:** widen the Deferred entry from "Next.js version posture" to the whole inherited
frontend block, with a re-verification pass before the first frontend PR.

## Verified and correct

| Item | Status |
| --- | --- |
| Django 6.0.7 current stable (released 2025-12-03; 6.0.7 on 2026-07-07) | Verified |
| Django 6.0 supports Python 3.12–3.14; project venv is 3.13 | Verified, compatible |
| `django.tasks` ships no worker/scheduler — correctly **not** used as the sync runtime | Verified against the Django 6.0 docs |
| drf-spectacular 0.30.0, released 2026-07-06, actively maintained | Verified |
| `@hey-api/openapi-ts` 0.99.0, published ~June 2026, actively released | Verified |
| `openapi-typescript` correctly rejected (no release since Feb 2026, TS 6 blocked) | Verified |
| PostgreSQL 15 | Matches `docker-compose.yml` |

## Note on the codegen pin

`@hey-api/openapi-ts` is at **0.99.0** — a pre-1.0 version number. That is normal for this
project and it is widely used, but a `^` range on a `0.x` package does not pin the major in the
usual way. The Stack row should say so rather than leaving "current release at implementation".
