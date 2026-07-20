# Architecture — Frontend (Next.js Web)

_Part: `frontend/` · Type: web · Generated: 2026-07-20 (deep scan)_

> ⚠️ **Read this first.** `Docs/FRONTEND-STACK.md` is the **single source of truth** for the
> frontend stack and conventions. The code described below is the **as-shipped** state, which
> **predates** that doc and diverges from it. This document describes what exists today and
> flags where it conflicts with the target. When writing new code, follow the doc, not this
> legacy code.

## Executive Summary

The frontend is a **Next.js 15.4.6 (App Router) / React 19 / TypeScript** app that renders a
YouTube-style shell (header + sidebar) and a grid of the signed-in user's playlists. It
initiates Google login by calling the backend and reads session/playlist data via credentialed
`fetch` calls. There is currently **no client state library**, **no test setup**, and styling
is a mix of Tailwind (v4), global CSS, and a CSS Module.

## Technology Stack (as shipped)

| Category | Technology | Version | Target-doc status |
| --- | --- | --- | --- |
| Framework | Next.js | 15.4.6 | Doc targets `~16.1.6` |
| UI runtime | React / react-dom | 19.1.0 | ✅ matches (`^19`) |
| Language | TypeScript | ^5, strict | ✅ strict matches |
| Styling | Tailwind CSS | ^4 (`@tailwindcss/postcss`) | ❌ Doc mandates Tailwind **v3** |
| Styling (extra) | global CSS + CSS Modules | — | ❌ Doc mandates shadcn/ui + `cn()` |
| Icons | FontAwesome (`@fortawesome/*`) | ^7 | ❌ Doc mandates `lucide-react` |
| Data fetching | native `fetch` + `useEffect` | — | ❌ Doc mandates React Query + axios |
| State | none | — | Doc: React Query is the only server-state layer |
| Build | `next build` (Turbopack dev) | — | ✅ |
| Tests | none | — | ❌ Doc requires Jest + RTL, 70% coverage |

## Architecture Pattern

**Component-based, App Router with a client-heavy root.** The root layout mounts the chrome;
the home page is a client component that delegates to `PlaylistsPage`, which calls a data hook.

```
src/app/layout.tsx            (Server Component root)
  ├── <YoutubeHeader/>        ("use client" — session check + Google login)
  ├── <YoutubeSidebar/>       ("use client" — static nav)
  └── {children}
        └── src/app/page.tsx  ("use client") → <PlaylistsPage/>
              └── usePlaylists() → fetch /api/youtube/playlists/
                    └── map → <PlaylistCard/> grid
```

Auth landing route: `src/app/auth/callback/page.tsx` — after the backend sets the cookie and
redirects here, this page simply `router.replace("/")` (the JWT is in an HttpOnly cookie, so
there is nothing for JS to parse).

## Data & State

- **`usePlaylists.ts`** performs the only real data fetch: `GET https://localhost:8000/api/youtube/playlists/`
  with `credentials: "include"`. It maps the nested YouTube API response into a flat
  `Playlist` type, with a **thumbnail fallback chain** `maxres → high → medium → default → ""`.
  Preserve that fallback when touching the mapping.
- **`YoutubeHeader.tsx`** independently calls `GET ${NEXT_PUBLIC_BACKEND_URL}/api/auth/me/`
  (credentialed) to determine login state, and `GET .../api/auth/google/` to start OAuth.
- ⚠️ Both use raw `fetch`/`useEffect`. The target doc forbids this pattern for new code (use
  React Query + axios, mocked with `axios-mock-adapter` in tests).
- `NEXT_PUBLIC_BACKEND_URL` is read from env (`frontend/.env`); `usePlaylists` currently
  **hardcodes** `https://localhost:8000` instead of using it — an inconsistency to fix.

## Component Overview

Eight components across `src/components/`. Full inventory in
[component-inventory-frontend.md](./component-inventory-frontend.md). Highlights:

- **Layout/chrome:** `YoutubeHeader`, `YoutubeSidebar`
- **Feature:** `PlaylistCard` (real data), `PlaylistsPage`
- **Demo/static:** `VideoPreview`, `VideoPreviewList` (rendered from hardcoded
  `utils/videosMetadata.tsx`; not wired to the backend)
- **Utils:** `normalizeSrc` (leading-slash guard for image paths)

## Source Tree

See [source-tree-analysis.md](./source-tree-analysis.md). Path alias `@/*` → `./src/*`.

## Configuration

- `next.config.ts` allow-lists remote image hosts (`lh3.googleusercontent.com`,
  `i.ytimg.com`). Adding a `next/image` from a new host requires updating `remotePatterns`
  or the production build fails.
- `tsconfig.json`: strict, `moduleResolution: bundler`, `@/*` path alias.

## Development Workflow

- Dev server: `npm run dev` (Turbopack) or via Docker `next dev --experimental-https`.
- Pre-PR gates (from `Docs/FRONTEND-STACK.md` §8): `tsc --noEmit` clean; production
  `next build` clean (webpack catches phantom-dep errors the dev server hides); visual check
  of the golden path + one error state in light **and** dark mode.
- See [development-guide.md](./development-guide.md).

## Deployment Architecture

- Containerized via `frontend/Dockerfile` (`node:20-alpine`); docker-compose runs
  `next dev --experimental-https` on `:3000` with certs from `frontend/certs/`.
- This is a **dev** configuration; a production build/serve (`next build` + `next start`
  behind TLS, or static/edge hosting) is not yet defined here.

## Testing Strategy

- **Current:** none.
- **Target (per doc §5):** Jest 29 + React Testing Library 16 + `@testing-library/user-event`;
  mock all API with `axios-mock-adapter`; 70% coverage gate; test user-visible behavior by
  role/label, not implementation details.

## Migration Debt Checklist (legacy → target doc)

- [ ] Replace `fetch`/`useEffect` data hooks with React Query + axios
- [ ] Replace FontAwesome with `lucide-react`
- [ ] Move from Tailwind v4 → v3 and adopt shadcn/ui + `cn()`
- [ ] Replace global CSS / CSS Modules styling
- [ ] Rename PascalCase files (`PlaylistCard.tsx`, `YoutubeHeader.tsx`) → kebab-case
- [ ] Add Jest/RTL test setup and reach 70% coverage
- [ ] Use `NEXT_PUBLIC_BACKEND_URL` everywhere (drop hardcoded URLs)
- [ ] Reconcile README's "Redux Toolkit" claim (not present; not the target either)
