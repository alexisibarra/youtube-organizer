# Architecture — Backend (Django REST API)

_Part: `backend/` · Type: backend · Generated: 2026-07-20 (deep scan)_

## Executive Summary

The backend is a **Django 5.2 + Django REST Framework** service exposing a small REST API
under `/api/`. Its job is to (1) run a Google OAuth2 flow, (2) persist the user's Google
tokens, and (3) proxy the YouTube Data API to return the signed-in user's playlists.
Authentication is **JWT delivered via an HttpOnly cookie**, bridged into DRF by a custom
middleware. There is a single Django app, `organizer`, and a single custom model,
`UserSocialToken`.

## Technology Stack

| Category | Technology | Version | Notes |
| --- | --- | --- | --- |
| Language | Python | 3.13 (Dockerfile) | `requirements.txt` unpinned for most deps |
| Web framework | Django | 5.2 | `requirements.txt` pins `Django>=4.0`; code is on 5.2 |
| API framework | Django REST Framework | ≥3.13 (3.16 installed) | class-based `APIView`s |
| Auth (JWT) | djangorestframework-simplejwt | latest | `ACCESS_TOKEN_LIFETIME = 1 day` |
| OAuth / YouTube | google-auth, google-auth-oauthlib, google-auth-httplib2, google-api-python-client | latest | YouTube Data API v3 |
| Database | PostgreSQL | 15 | via `psycopg2-binary` |
| CORS | django-cors-headers | latest | credentials enabled |
| Dev tooling | django-extensions (`runserver_plus`), Werkzeug, pyOpenSSL | latest | HTTPS dev server |
| HTTP client | requests | latest | fetches Google userinfo |

## Architecture Pattern

**Service/API-centric monolith** — a single Django app with thin DRF views. There is no
service/repository layer; views call the ORM and Google APIs directly. This is appropriate
for the current small surface area.

Layering (as-is):

```
URL routing (organizer/urls.py, mounted at /api/)
   └── DRF APIViews (views.py, google_auth_views.py)
         ├── Django ORM  (organizer/models.py -> UserSocialToken, auth User)
         └── Google clients (google-auth-oauthlib Flow, googleapiclient build)
```

## Request / Auth Flow (the tricky part)

```
1. Frontend → GET /api/auth/google/         (GoogleAuthInitView)
      → builds OAuth2 Flow, returns { auth_url }, stores state in session
2. Browser → Google consent → GET /api/oauth2callback/?code=...  (GoogleAuthCallbackView, AllowAny)
      → flow.fetch_token(); GET Google userinfo
      → User.objects.get_or_create(username=email)
      → login(request, user); store profile_picture in session
      → UserSocialToken.update_or_create(access/refresh/expiry/scope)
      → RefreshToken.for_user(user) → JWT access token
      → HTTP 302 redirect to FRONTEND_AUTH_CALLBACK_URL
         Set-Cookie: access_token=<JWT>; HttpOnly; Secure; SameSite=None; Max-Age=86400
3. Subsequent requests carry the cookie:
      JWTAuthCookieMiddleware reads access_token cookie
      → sets request.META['HTTP_AUTHORIZATION'] = 'Bearer <JWT>'
      → DRF JWTAuthentication authenticates the user
```

**Invariants (do not break):**

- Auth is cookie-based, **not** header-based. Clients never send `Authorization` directly.
- `JWTAuthCookieMiddleware` must run **before** DRF authenticates (it sits after
  `SessionMiddleware`, before `CommonMiddleware`). See middleware ordering in `settings.py`.
- `CORS_ALLOW_CREDENTIALS = True`, origin restricted to `https://localhost:3000`.
- Session/CSRF cookies are `SameSite=None; Secure` — required for the cross-port OAuth flow,
  which is why HTTPS is mandatory even locally.

## Data Architecture

Single custom model plus Django's built-in `auth.User`. See
[data-models-backend.md](./data-models-backend.md).

- `UserSocialToken` — OneToOne with `User`; stores Google `access_token`, `refresh_token`,
  `token_expiry`, `token_scope`, `token_type`, timestamps.
- Profile picture is **not** persisted — it is stashed in the Django session
  (`request.session['profile_picture']`) as a demo shortcut.

## API Design

Four endpoints, all under `/api/`. See [api-contracts-backend.md](./api-contracts-backend.md)
for full request/response detail.

| Method | Path | View | Auth |
| --- | --- | --- | --- |
| GET | `/api/auth/google/` | `GoogleAuthInitView` | default (see note) |
| GET | `/api/oauth2callback/` | `GoogleAuthCallbackView` | `AllowAny` |
| GET | `/api/youtube/playlists/` | `YouTubePlaylistsView` | `IsAuthenticated` |
| GET | `/api/auth/me/` | `MeView` | `IsAuthenticated` |

> Note: `GoogleAuthInitView` sets no explicit `permission_classes`, so it inherits DRF
> defaults. With SimpleJWT as the only auth class and no default permission configured, it is
> effectively open (`AllowAny`) — an unauthenticated user must be able to start login. Making
> this explicit would remove the ambiguity.

## Configuration

- All secrets/config come from environment (`.env` via docker-compose `env_file`):
  `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`,
  `FRONTEND_AUTH_CALLBACK_URL`, and `POSTGRES_*`.
- OAuth `SCOPES`: `youtube.readonly`, `openid`, `userinfo.email`, `userinfo.profile`.
- `env.template` documents the full required set.

## Deployment Architecture

- Containerized via `backend/Dockerfile` (`python:3.13-slim`), started by docker-compose as
  the `backend` service on `:8000`, served over HTTPS with `runserver_plus` and self-signed
  certs from `backend/certs/`.
- **`runserver_plus` is a development server** — not suitable for production. A real deploy
  needs a WSGI/ASGI server (gunicorn/uvicorn) behind TLS, plus the security fixes below.
- See [deployment-guide.md](./deployment-guide.md).

## Testing Strategy

- **Current:** none. `organizer/tests.py` is empty.
- **Target:** Django `APITestCase` (DRF) tests alongside `organizer`. Auth-dependent tests
  must simulate the cookie→header path or authenticate via SimpleJWT directly, because
  `JWTAuthCookieMiddleware` is what populates the auth header.

## Security Notes (must fix before deploy)

- `DEBUG = True`, hardcoded `SECRET_KEY`, empty `ALLOWED_HOSTS` in `settings.py` — dev-only;
  move to env and disable DEBUG outside local.
- `token_type` on `UserSocialToken` is populated with `credentials.token_uri` (the token
  **endpoint URL**, not an OAuth token type like "Bearer"). Likely a bug to revisit.
- Never weaken `SameSite=None; Secure` or `CORS_ALLOW_CREDENTIALS` — login breaks end-to-end.
