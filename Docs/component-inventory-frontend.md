# Component Inventory — Frontend

_Part: `frontend/` · `src/components/` + `src/app/` · Generated: 2026-07-20 (deep scan)_

> Naming caveat: existing files use **PascalCase** (`PlaylistCard.tsx`). `Docs/FRONTEND-STACK.md`
> mandates **kebab-case** for new files — the current names are legacy.

## Summary

| Category | Components |
| --- | --- |
| Layout / chrome | `YoutubeHeader`, `YoutubeSidebar` |
| Feature (live data) | `PlaylistsPage`, `PlaylistCard` |
| Demo / static | `VideoPreviewList`, `VideoPreview` |
| Utilities | `normalizeSrc`, `videosMetadata` |
| App routes | `layout`, `page`, `auth/callback/page` |

## Layout / Chrome

### `YoutubeHeader` (`components/YoutubeHeader.tsx`, `"use client"`)
The top bar. Owns two responsibilities beyond presentation:
- **Session check:** on mount, `GET ${NEXT_PUBLIC_BACKEND_URL}/api/auth/me/` with
  `credentials: "include"`; sets `user` state (username/email/profile_picture) or `null`.
- **Login initiation:** `handleGoogleLogin()` calls `GET .../api/auth/google/`, then
  `window.location.href = data.auth_url` to start the OAuth redirect.
- Renders avatar + tooltip when logged in, "Sign in" button otherwise. Uses FontAwesome icons
  (legacy) and inline styles.

### `YoutubeSidebar` (`components/YoutubeSidebar.tsx`, `"use client"`)
Static left navigation. Maps a hardcoded `sidebarLinks` array to `next/image` SVG icons from
`public/icons/`, passing each through `normalizeSrc`.

## Feature Components (live data)

### `PlaylistsPage` (`app/PlaylistsPage.tsx`)
Calls `usePlaylists()`; renders loading/error states, then a flex-wrap grid of `PlaylistCard`s.
Maps hook fields → card props (`itemCount`→`video_count`, `publishedAt`→`updated_at`,
`thumbnailUrl`→`thumbnail_url`). Layout via inline styles.

### `PlaylistCard` (`components/PlaylistCard.tsx` + `PlaylistCard.module.css`)
Presentational card for a single playlist. Props (`PlaylistCardProps`): `title`,
`video_count`, `updated_at`, `thumbnail_url`. Renders a `next/image` thumbnail (320×180,
`priority`), title, `video_count.toLocaleString()` videos, and a localized "Updated" date.
Styled with a **CSS Module** (legacy vs. the shadcn/ui + `cn()` target). Uses the
`React.FC<Props>` pattern that the target doc endorses.

## Demo / Static Components (not backend-wired)

### `VideoPreviewList` (`components/VideoPreviewList.tsx`, `"use client"`)
Renders a `<section class="video-grid">` of `VideoPreview`s from the hardcoded
`utils/videosMetadata.tsx`. **Not currently mounted** by any route — demo/scaffold.

### `VideoPreview` (`components/VideoPreview.tsx`)
Fully-parametrized single video card (thumbnail, channel avatar + hover tooltip, title, views,
upload time). Props via a `VideoPreviewProps` `interface` (note: target doc prefers `type`).
Uses `normalizeSrc` for all image paths.

## Utilities

### `normalizeSrc` (`components/utils/normalizeSrc.tsx`)
`(src) => src.startsWith("/") ? src : "/" + src` — guarantees a leading slash so
`public/`-relative image paths resolve.

### `videosMetadata` (`components/utils/videosMetadata.tsx`, `"use client"`)
Hardcoded array of 12 demo videos (MKBHD, Markiplier, etc.) with thumbnails/channel avatars
from `public/`. Pure static data for the demo grid.

## Data Hook

### `usePlaylists` (`app/hooks/usePlaylists.ts`)
Not a component but the frontend's core data source. `fetch`es
`https://localhost:8000/api/youtube/playlists/` (credentialed), maps YouTube `items[]` to the
`Playlist` type with a `maxres → high → medium → default → ""` thumbnail fallback, and returns
`{ playlists, loading, error }`.
- ⚠️ Legacy `fetch`/`useEffect` pattern the target doc replaces with React Query + axios.
- ⚠️ Hardcodes the backend URL instead of using `NEXT_PUBLIC_BACKEND_URL`.

## App Router Entries

| File | Role |
| --- | --- |
| `app/layout.tsx` | Root layout; mounts `YoutubeHeader` + `YoutubeSidebar`; sets fonts/metadata |
| `app/page.tsx` | `"/"` → renders `PlaylistsPage` (client) |
| `app/auth/callback/page.tsx` | OAuth landing; `router.replace("/")` (cookie already set by backend) |

## Design System Status

No design system yet. Styling is split across Tailwind v4 utility classes, global CSS
(`app/styles/*.css`, `app/globals.css`), inline styles, and one CSS Module. The target
(`Docs/FRONTEND-STACK.md`) is **shadcn/ui + Radix + Tailwind v3 + `cn()`** — treat current
styling as migration debt.
