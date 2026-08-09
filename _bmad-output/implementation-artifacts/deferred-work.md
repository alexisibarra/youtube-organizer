# Deferred Work

Items surfaced during reviews that are real but not actionable in the story that found them.

## Deferred from: code review of 1-1-upgrade-to-django-6-0-with-bounded-dependency-pins (2026-08-09)

- **Transitive dependency closure is unpinned, so "reproducible" is not fully achieved.** _Reason for deferring: a lockfile is new-file scope Story 1.1 forbids; revisit at Story 1.3, when PyJWT becomes a first-party direct pin._ AC1 pins 14 direct requirements, but `PyJWT`, `cryptography`, `oauthlib`, `requests-oauthlib`, `httplib2`, `asgiref`, `sqlparse`, `jsonschema` and `uritemplate` float. Two consequences to carry forward: (a) the `Flow.code_verifier` contract Risk R3 was written to protect lives in `oauthlib`/`requests-oauthlib`, neither pinned — a later release can regress commit `8b8d48e` with `requirements.txt` unchanged; (b) "PyJWT 2.13.0 … no pin conflict ahead" rests on an unpinned transitive that loses its only requirer once Story 1.4 removes SimpleJWT.

- **The four `google-*` bumps have no functional verification.** _Reason for deferring: no YouTube Data API surface is exercised until the Epic 3 sync work, which will verify it functionally._ `google-api-python-client` moves to `2.198.0`, `google-auth` to `2.56.3`, `google-auth-httplib2` to `0.4.1`. Every Story 1.1 DoD probe exercises Django, admin and OAuth *init*; none touches a YouTube Data API call, which is the product surface `google-api-python-client` serves. Risk R3 covered only `google-auth-oauthlib`.

- **No CI, no Dependabot and no security audit covers the backend dependency set.** `.github/workflows/ci.yml` triggers on `apps/**`, `libs/**`, `pnpm-lock.yaml`, `nx.json`, `package.json` — nothing matches `backend/requirements.txt`, so a PR rewriting every backend pin runs zero automated jobs. The workflow is also a foreign nx/pnpm/prisma template that would not exercise this stack even if it fired. No `.github/dependabot.yml` exists, so exact `==` pins have no update mechanism — the same reasoning that made 6.0.7→6.0.8 mandatory recurs on every future patch with nothing to trigger it. No `pip-audit`/`safety` was run over the other 13 pins or the transitives this commit freezes. Owned by Stories 3.5/3.6.

- **Base and DB images are unpinned while Django is pinned to the patch level.** `FROM python:3.13-slim` (`backend/Dockerfile:2`) and `db.image: postgres:15` (`docker-compose.yml`) are floating tags; patch/OS drift changes the build result with byte-identical requirements. Digest pinning was never considered.

- **No `.dockerignore`; `backend/.venv` enters the build context via `COPY . .`.** The venv recreated in Task 5 carries a second full Django install into the image. Runtime is shadowed by the `./backend:/app` bind mount, so this is build bloat rather than a correctness bug — but a `docker run` without the mount would execute against the stale tree. Fix is a one-line `backend/.dockerignore`.

- **Stale duplicate `backend/docker-compose.yml` documented as a trap and left armed.** Story 1.1's Risk R5 records that it specifies `postgres:16` against the real stack's `postgres:15` and that nothing invokes it. No story owns its deletion (1.5 covers only volume naming), so a documented footgun with a database major version mismatch persists indefinitely.

- **The strict deprecation check only reaches import and check time.** `-W error … manage.py check` never exercises a request path, an ORM query, a token decode or an OAuth exchange, so "zero warnings, first-party and third-party" is a narrower result than it reads as. A real harness is Story 1.2.

- **`project-context.md:227` requires tests on every story PR; Story 1.1 forbids them.** The story defers the 70% coverage gate to 1.2 but never addresses the per-PR test rule, so a reviewer treating `project-context.md` as binding has grounds to reject a PR the story deliberately shipped test-free.

## Deferred from: `spec-ci-gate-stack.md` (2026-08-09)

- source_spec: `spec-ci-gate-stack.md`
  summary: `.github/pull_request_template.md` auto-applies to every PR but is pure Accountr — it instructs `pnpm exec nx run backend:test --coverage`, cites Prisma DTOs / `HttpException` filters / money-as-string, and links to `Docs/MVPDefinition/…` paths that do not exist here.
  evidence: The user scoped this change to `ci.yml` + hooks and explicitly did not select the PR template. Real and live though: `project-context.md` requires all checklist items ticked before merge, so the template is currently impossible to satisfy honestly. The file is now flagged accurately in `project-context.md` rather than rewritten.

- source_spec: `spec-ci-gate-stack.md`
  summary: `usePlaylists.ts` asserts its response type instead of validating it — `snippet` is declared required though the YouTube API omits it for private/deleted items, and `data.items` is not checked to be an array.
  evidence: Pre-existing runtime exposure, unchanged by this story: the previous `(item: any)` had exactly the same hazard, and one malformed item still throws inside `.map`, is swallowed by the catch, and surfaces as "An unknown error occurred". Epic 2 deletes this file, so hardening it now is throwaway work.

- source_spec: `spec-ci-gate-stack.md`
  summary: `.githooks/pre-push` ignores the ref list git supplies on stdin, so branch deletions and tag-only pushes pay a full typecheck + lint + build cycle for zero coverage.
  evidence: Confirmed by reading the hook — it never reads stdin. Wasteful rather than incorrect (CI skips those pushes entirely), and the dangerous stdin interaction was fixed in this story via `manage.py test --noinput`.

## Deferred from: code review of spec-ci-gate-stack.md (2026-08-09)

- **`postgres:15` in CI and the root compose file, `postgres:16` in `backend/docker-compose.yml`.** The new `ci.yml:87` pins `postgres:15` and `.githooks/pre-push:113` tells developers to run `make up` for a local database — without resolving which compose file that is. At least one local environment therefore tests against a different Postgres major than CI. Already recorded as Story 1.1 Risk R5 ("stale duplicate `backend/docker-compose.yml` documented as a trap and left armed"); this review confirms the trap is now load-bearing, because a gate stack has started pointing at it. No story owns the deletion.

- **The hook closes the stdin hazard one consumer at a time instead of once.** `manage.py test --noinput` (`.githooks/pre-push:106`) fixes the Django prompt that would otherwise eat git's ref list, but `npm run lint`, `npm run build`, `manage.py check` and `makemigrations --check` all inherit that same stdin. A single `exec </dev/null` after the hook's own reads would close the class for every tool added later; the per-flag fix leaves the next one exposed. Extends the stdin entry above rather than replacing it — that one is about wasted work on ref-less pushes, this one about prompt consumption.
