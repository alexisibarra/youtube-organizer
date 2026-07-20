# API Contracts — Backend

_Part: `backend/` · Base path: `/api/` · Generated: 2026-07-20 (deep scan)_

All routes are DRF class-based `APIView`s registered in `backend/organizer/urls.py` and
mounted under `/api/` by `backend/youtube_organizer/urls.py`. Base URL in local dev:
`https://localhost:8000/api/`.

**Authentication model:** JWT in an `HttpOnly` cookie named `access_token`.
`JWTAuthCookieMiddleware` promotes the cookie to `Authorization: Bearer <jwt>` before DRF
runs. Clients must send requests with credentials (browsers: `fetch(..., { credentials: "include" })`).

---

## 1. Start Google OAuth — `GET /api/auth/google/`

- **View:** `GoogleAuthInitView` (`google_auth_views.py`)
- **Auth:** none required (must be reachable while logged out)
- **Purpose:** Build the Google OAuth2 authorization URL and stash the OAuth `state` in the
  Django session.
- **Request:** no params.
- **Response `200`:**
  ```json
  { "auth_url": "https://accounts.google.com/o/oauth2/auth?..." }
  ```
- **Side effects:** sets `request.session['oauth_state']`.
- **Scopes requested:** `youtube.readonly`, `openid`, `userinfo.email`, `userinfo.profile`
  (`access_type=offline`, `prompt=consent`).

---

## 2. OAuth2 Callback — `GET /api/oauth2callback/`

- **View:** `GoogleAuthCallbackView` — `permission_classes = [AllowAny]`
- **Purpose:** Google redirects here with `?code=...&state=...`. Exchanges code for tokens,
  provisions the user, mints a JWT, sets the auth cookie, redirects to the frontend.
- **Query params:** `code`, `state` (supplied by Google).
- **Flow:**
  1. `flow.fetch_token(authorization_response=<full request URI>)`
  2. `GET https://www.googleapis.com/oauth2/v2/userinfo` with the Google access token
  3. `User.objects.get_or_create(username=email, defaults={email, first_name, last_name})`
  4. `login(request, user)`; store `profile_picture` in session
  5. `UserSocialToken.update_or_create(...)` with Google tokens
  6. `RefreshToken.for_user(user)` → JWT access token
- **Response `302`:** redirect to `FRONTEND_AUTH_CALLBACK_URL`
  (default `https://localhost:3000/auth/callback`) with header:
  ```
  Set-Cookie: access_token=<JWT>; HttpOnly; Secure; SameSite=None; Max-Age=86400
  ```
- **Error responses:**
  - `400 { "error": "Failed to fetch user info from Google." }` — userinfo call ≠ 200
  - `400 { "error": "No email found in Google user info." }` — email missing

---

## 3. List YouTube Playlists — `GET /api/youtube/playlists/`

- **View:** `YouTubePlaylistsView` — `permission_classes = [IsAuthenticated]`
- **Purpose:** Return the authenticated user's own YouTube playlists by proxying the YouTube
  Data API v3.
- **Auth:** requires valid `access_token` cookie (→ Bearer JWT).
- **Upstream call:**
  `youtube.playlists().list(part='snippet,contentDetails', mine=True, maxResults=50)`
  using `Credentials` built from the stored `UserSocialToken`.
- **Response `200`:** the **raw YouTube Data API response** passed through unchanged, e.g.:
  ```json
  {
    "kind": "youtube#playlistListResponse",
    "items": [
      {
        "id": "PL...",
        "snippet": {
          "title": "…",
          "description": "…",
          "publishedAt": "2024-01-01T00:00:00Z",
          "channelTitle": "…",
          "thumbnails": { "maxres": { "url": "…" }, "high": {"url":"…"}, "…": {} }
        },
        "contentDetails": { "itemCount": 12 }
      }
    ]
  }
  ```
  > The frontend (`usePlaylists.ts`) normalizes `items[]` into a flat `Playlist` shape and
  > applies a thumbnail fallback `maxres → high → medium → default`.
- **Error responses:**
  - `404 { "error": "No YouTube token found for user." }` — no `UserSocialToken`
  - `401` — missing/invalid JWT (DRF default)

---

## 4. Current User — `GET /api/auth/me/`

- **View:** `MeView` (`views.py`) — `permission_classes = [IsAuthenticated]`
- **Purpose:** Return the signed-in user's basic profile; used by the header to decide
  logged-in vs. logged-out UI.
- **Response `200`:**
  ```json
  { "username": "user@example.com", "email": "user@example.com", "profile_picture": "https://lh3.googleusercontent.com/…" }
  ```
  - `profile_picture` comes from `request.session['profile_picture']` (set at OAuth callback);
    it may be `null` if the session lacks it.
- **Response `401`:** unauthenticated (no valid cookie/JWT).

---

## Conventions & Notes

- **All-authenticated by default:** DRF's default auth class is `JWTAuthentication`. Views that
  should be public must set `permission_classes = [AllowAny]` explicitly (as the callback does).
- **No serializers/DTOs:** responses are built ad-hoc from dicts; the playlists endpoint is a
  straight pass-through of the Google payload.
- **CORS:** only `https://localhost:3000` is allowed, with credentials.
- **Errors are shape-inconsistent** (`{ "error": ... }` for app errors vs. DRF's default
  `{ "detail": ... }` for auth failures) — worth standardizing in future work.
