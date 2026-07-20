# Source Tree Analysis — YouTube Organizer

_Generated: 2026-07-20 · Monorepo (frontend + backend)_

```
youtube-organizer/
├── docker-compose.yml        # Orchestrates backend(:8000), db(:5432), frontend(:3000) over HTTPS
├── Makefile                  # up / backend-migrate / frontend-install / frontend-dev
├── README.md                 # Project intro + setup
├── BACKLOG.md                # Feature backlog
├── bin/                      # Self-signed cert generators for local HTTPS
│   ├── generate-all-certs.sh
│   ├── generate-backend-cert.sh
│   └── generate-frontend-cert.sh
├── Docs/  (== docs/)         # AUTHORITATIVE source-of-truth docs + generated project docs
│   ├── FRONTEND-STACK.md     # ← SINGLE SOURCE OF TRUTH for the frontend stack
│   └── CI-AND-GITHUB-GATES.md# ← SOURCE OF TRUTH for CI/branch/deploy gate intent
├── .github/                  # ⚠️ Placeholder CI (ci.yml, deploy.yml, PR template) — unadapted
│
├── backend/                  # ── Part: backend (Django REST API) ──
│   ├── Dockerfile            # python:3.13-slim, runserver_plus w/ HTTPS
│   ├── requirements.txt      # Django, DRF, SimpleJWT, google-auth*, psycopg2
│   ├── manage.py
│   ├── certs/                # Self-signed localhost certs (gitignored content)
│   ├── organizer/            # The single Django app (all business logic)
│   │   ├── models.py         # UserSocialToken (OneToOne User) — stores Google tokens
│   │   ├── views.py          # MeView (/api/auth/me/)
│   │   ├── google_auth_views.py  # ★ OAuth2 init/callback + YouTube playlists view
│   │   ├── urls.py           # App routes (mounted under /api/)
│   │   ├── admin.py          # (empty)
│   │   ├── apps.py
│   │   ├── tests.py          # ⚠️ empty — no tests yet
│   │   └── migrations/
│   │       └── 0001_initial.py   # Creates UserSocialToken table
│   └── youtube_organizer/    # Django project package (settings/entry points)
│       ├── settings.py       # ★ CORS, SimpleJWT, DB, middleware order, INSTALLED_APPS
│       ├── middleware.py     # ★ JWTAuthCookieMiddleware (cookie → Authorization header)
│       ├── urls.py           # Root URLconf: admin/ + api/ (includes organizer.urls)
│       ├── wsgi.py / asgi.py # WSGI/ASGI entry points
│
└── frontend/                 # ── Part: frontend (Next.js web) ──
    ├── Dockerfile            # node:20-alpine, next dev
    ├── package.json          # next 15.4.6, react 19, fontawesome, tailwind v4 (LEGACY set)
    ├── tsconfig.json         # strict; path alias @/* -> ./src/*
    ├── next.config.ts        # ★ remote image hosts: lh3.googleusercontent.com, i.ytimg.com
    ├── certs/                # Self-signed localhost certs
    ├── public/               # Static assets
    │   ├── icons/            # Sidebar SVG icons
    │   ├── channel-pictures/ # Demo channel avatars
    │   └── thumbnails/       # Demo video thumbnails (webp)
    └── src/
        ├── app/              # Next.js App Router
        │   ├── layout.tsx    # ★ Root layout: mounts YoutubeHeader + YoutubeSidebar
        │   ├── page.tsx      # "/" → renders PlaylistsPage (client)
        │   ├── PlaylistsPage.tsx    # Playlist grid (uses usePlaylists)
        │   ├── globals.css   # Global styles + Tailwind
        │   ├── hooks/
        │   │   └── usePlaylists.ts  # ★ fetch playlists (legacy fetch/useEffect pattern)
        │   ├── auth/
        │   │   └── callback/page.tsx  # OAuth landing → redirects to "/"
        │   ├── styles/       # general/header/sidebar/video CSS (legacy global CSS)
        │   └── assets/images/
        └── components/
            ├── PlaylistCard.tsx        # + PlaylistCard.module.css (CSS Module, legacy)
            ├── YoutubeHeader.tsx       # ★ top bar + Google sign-in + session check
            ├── YoutubeSidebar.tsx      # left nav
            ├── VideoPreview.tsx        # single video card (demo)
            ├── VideoPreviewList.tsx    # static demo grid from videosMetadata
            └── utils/
                ├── normalizeSrc.tsx    # ensures leading slash on image paths
                └── videosMetadata.tsx  # hardcoded demo video list
```

## Critical Directories & Files

### Backend

- **`backend/organizer/google_auth_views.py`** — the heart of the backend. Contains the
  OAuth2 init view, the callback view (exchanges code, upserts user, mints JWT, sets cookie),
  and the `YouTubePlaylistsView` that calls the YouTube Data API. Keep Google logic here,
  separate from generic views.
- **`backend/youtube_organizer/middleware.py`** — `JWTAuthCookieMiddleware`, the linchpin
  of the cookie-based auth. Reads the `access_token` cookie and injects the `Authorization`
  header before DRF authenticates.
- **`backend/youtube_organizer/settings.py`** — CORS credentials, `SameSite=None; Secure`
  cookies, SimpleJWT lifetime, env-driven Postgres, and the exact middleware ordering.

### Frontend

- **`frontend/src/app/layout.tsx`** — the only place the header/sidebar chrome is mounted.
- **`frontend/src/app/hooks/usePlaylists.ts`** — data-fetching for playlists (legacy
  `fetch`/`useEffect`; the target doc says migrate to React Query + axios).
- **`frontend/src/components/YoutubeHeader.tsx`** — owns Google login initiation and the
  `/api/auth/me/` session check.
- **`frontend/next.config.ts`** — image host allow-list; adding a `next/image` from a new
  host requires editing `remotePatterns` or the build fails.

## Entry Points

| Part | Entry point | Notes |
| --- | --- | --- |
| Backend (WSGI) | `youtube_organizer/wsgi.py` | Production server target |
| Backend (dev) | `manage.py runserver_plus` | HTTPS via django-extensions |
| Backend (routes) | `youtube_organizer/urls.py` → `organizer/urls.py` | All API under `/api/` |
| Frontend | `src/app/layout.tsx` + `src/app/page.tsx` | App Router root |
| OAuth landing | `src/app/auth/callback/page.tsx` | Post-login redirect target |

## Integration Point

The frontend talks to the backend over **REST + credentialed cookies** only. See
[integration-architecture.md](./integration-architecture.md).
