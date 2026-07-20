# Data Models — Backend

_Part: `backend/` · ORM: Django · DB: PostgreSQL 15 · Generated: 2026-07-20 (deep scan)_

The backend defines **one** custom model plus Django's built-in auth tables. Schema is managed
by Django migrations (`organizer/migrations/`). Only `0001_initial` exists.

## Entity Relationship

```
auth_user (Django built-in)
   │ 1
   │
   │ 1
organizer_usersocialtoken   (OneToOne → auth_user, CASCADE)
```

One user has at most one `UserSocialToken`; deleting the user deletes the token.

## Model: `UserSocialToken`

Defined in `backend/organizer/models.py`. Stores the Google OAuth2 credentials for a user so
the backend can later call the YouTube Data API on their behalf.

| Field | Type | Constraints | Purpose |
| --- | --- | --- | --- |
| `id` | BigAutoField | PK | — |
| `user` | OneToOneField → `auth.User` | `on_delete=CASCADE`, unique | Owner of the token |
| `access_token` | TextField | required | Google OAuth2 access token |
| `refresh_token` | TextField | required | Google OAuth2 refresh token (offline access) |
| `token_expiry` | DateTimeField | required | Access-token expiry (`credentials.expiry`) |
| `token_scope` | TextField | nullable, blank | Space-joined granted scopes |
| `token_type` | CharField(50) | nullable, blank | ⚠️ Populated with `credentials.token_uri` (the token endpoint URL), **not** an OAuth token type — see note |
| `created` | DateTimeField | `auto_now_add` | Row creation time |
| `updated` | DateTimeField | `auto_now` | Last update time |

- `__str__` → `"Token for {user.username}"`.
- Written via `UserSocialToken.objects.update_or_create(user=...)` in the OAuth callback, so a
  re-login refreshes the stored tokens in place.

### Note / likely bug

`token_type` is assigned `credentials.token_uri` in `google_auth_views.py`
(`'token_type': credentials.token_uri`). That stores the token **endpoint URL**
(`https://oauth2.googleapis.com/token`) rather than a type like `"Bearer"`. Revisit if
`token_type` is ever read meaningfully.

## Built-in Tables in Use

- **`auth_user`** — standard Django user. Username is set to the Google **email**
  (`get_or_create(username=email, ...)`), plus `email`, `first_name`, `last_name`.
- **`django_session`** — session storage. Used to hold the OAuth `state` and, as a demo
  shortcut, the user's `profile_picture` (which is therefore **not** persisted in a model).

## Migration Strategy

- Migrations live in `organizer/migrations/`; `0001_initial.py` creates `UserSocialToken`.
- After model changes: `python manage.py makemigrations`, then apply with
  `make backend-migrate` (runs `migrate` inside the `backend` container).
- DB connection is entirely env-driven (`POSTGRES_DB/USER/PASSWORD/HOST/PORT`); default
  `HOST=db` (the compose service name).

## Data Not Yet Modeled

- **Playlists / videos are not stored.** The playlists endpoint proxies YouTube live on each
  request; nothing is cached or persisted. Any future "organize playlists" feature will likely
  need new models here.
- **Profile picture** is session-only; persisting it would require extending the user model or
  a profile table.
