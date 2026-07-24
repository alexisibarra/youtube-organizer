# Frontend Stack Reference (mirrored from Accountr)

> Source of truth: this is the **shipped** frontend stack of the Accountr app, read from its live `package.json` files. Mirror these exact versions and conventions. Where a legacy architecture doc disagrees, the versions below win.

> ### ⚠️ Superseded in part by the architecture spine (2026-07-24)
>
> `_bmad-output/planning-artifacts/architecture/architecture-youtube-organizer-2026-07-24/ARCHITECTURE-SPINE.md`
> overrides this document on three points, decided deliberately for *this* repo:
>
> | This doc says | The spine decides | Why |
> |---|---|---|
> | §1 Nx `22.7.5` + pnpm workspaces | **No Nx, no workspaces** (AD-2) | Nx's affected-graph and caching earn nothing on one Next app with a Python backend Nx cannot manage |
> | §1 / §6 pnpm | **npm** + `package-lock.json` (AD-2) | The workspace that motivated pnpm is gone; §7.3's phantom-dependency rule is moot under npm's hoisting |
> | §2 shared TypeScript types package | **Generated from DRF** (AD-3) | A two-tree repo has nowhere to host the package; `drf-spectacular` → `@hey-api/openapi-ts` makes serializers the contract instead, with a CI drift gate |
>
> **Version staleness:** this table records another project's pins at a past date. Next.js `~16.1.6` is already behind the 16.2.x LTS line and a July 2026 Next.js security release. **Re-verify every pin below before the first frontend PR**, and amend this doc when one moves — the spine defers to it.
>
> Everything else here — Tailwind v3, shadcn/ui, React Query as the only server-state layer, the component pattern, RHF `onBlur`, naming, the §8 pre-PR gates — remains authoritative and binding.

## 1. Framework & Runtime

| Piece | Version | Notes |
|---|---|---|
| Next.js | `~16.1.6` | App Router, RSC enabled, `src/` directory |
| React / React DOM | `^19.0.0` | React 19 |
| TypeScript | strict | `strict: true`, no `any` (use `unknown` + narrowing) |
| ~~Nx~~ | ~~`22.7.5`~~ | **Not used here** — AD-2. No monorepo runner; `frontend/` and `backend/` are built directly |
| Package manager | **npm** (`package-lock.json`) | AD-2. ~~pnpm workspaces~~. §7.3's phantom-dep rule does not apply under npm's hoisting |

## 2. Server State & Data

- **`@tanstack/react-query` `5.100.14`** — the ONLY server-state layer. No Redux / Zustand / SWR.
- **`axios` `^1.16.1`** — HTTP client.
- ~~A shared TypeScript types package (e.g. `@app/shared-types`) is the single source of truth for API request/response shapes, imported by both frontend and backend.~~
  **Here (AD-3):** DRF serializers are the single source of truth. `drf-spectacular` emits the OpenAPI schema, `@hey-api/openapi-ts` generates types into `frontend/src/lib/api/`, and CI regenerates and fails on drift. The generated directory is committed and never hand-edited; no API type is declared by hand in `frontend/`.

## 3. Forms & Validation

- **`react-hook-form` `7.76.1`** — validation **`mode: 'onBlur'`** is mandatory (validation must fire on blur, not only submit).
- **`zod` `4.4.3`** — schemas (also usable for backend config validation).
- **`@hookform/resolvers` `^5.4.0`** — zod ↔ RHF bridge.

## 4. UI & Styling

- **Tailwind CSS `^3.4.19`** (+ `postcss`, `autoprefixer`) — **v3, NOT v4**.
- **shadcn/ui** — config: `style: default`, `baseColor: neutral`, `cssVariables: true`, RSC on.
  - Generated components live in `src/components/ui/` — **never hand-edit them**; add via `npx shadcn@latest add <component>`.
- **Radix primitives** (wrapped by shadcn): collapsible, label, popover, select, separator, slot, switch, tabs, toast.
- **Util trio for `cn()`**: `class-variance-authority ^0.7.1`, `clsx ^2.1.1`, `tailwind-merge ^3.6.0`.
- **`lucide-react` `^1.17.0`** — icons.
- **`date-fns` `^4.4.0`** + **`react-day-picker` `^10.0.1`** — date picking / calendar.

Baseline shadcn components to generate: `alert, badge, button, calendar, card, collapsible, form, form-message, input, label, popover, select, separator, skeleton, switch, table, tabs, textarea, toast, toaster`.

## 5. Testing

- **Jest `^29.7.0`** + `jest-environment-jsdom` + `ts-jest`.
- **React Testing Library `^16.0.0`** + `@testing-library/user-event` + `@testing-library/jest-dom`.
- **`axios-mock-adapter`** — mock all API calls; never hit a real backend in tests.
- Coverage gate: **70%** minimum.

## 6. Install Commands

> **npm here, not pnpm** (AD-2). Re-verify these pins before running them — see the banner.

```bash
# Core
npm install next@~16.1.6 react@^19 react-dom@^19 \
  @tanstack/react-query@5.100.14 axios@^1.16.1 \
  react-hook-form@7.76.1 zod@4.4.3 @hookform/resolvers@^5.4.0 \
  date-fns@^4.4.0 react-day-picker@^10.0.1 lucide-react@^1.17.0

# shadcn util layer (radix gets pulled per-component by `shadcn add`)
npm install class-variance-authority@^0.7.1 clsx@^2.1.1 tailwind-merge@^3.6.0

# Tailwind v3 (NOT v4)
npm install -D tailwindcss@^3.4.19 postcss autoprefixer
npx shadcn@latest init   # style=default, baseColor=neutral, cssVariables=true

# Testing
npm install -D jest@^29 jest-environment-jsdom ts-jest \
  @testing-library/react@^16 @testing-library/user-event \
  @testing-library/jest-dom axios-mock-adapter

# API type generation (AD-3)
npm install -D @hey-api/openapi-ts@0.99.0
```

## 7. Mandatory Conventions (mirror these, not just the packages)

1. **Money = `string`, never JS `number`.** API returns monetary amounts as strings; keep them as strings until display; format with `Intl.NumberFormat` at display only.
2. **RHF `mode: 'onBlur'`.** Validation fires on blur. Error text must use a `destructive-foreground`-style color for WCAG contrast.
3. **No phantom dependencies.** ~~pnpm does not hoist transitives —~~ every imported package must be a *direct* dependency, or the webpack production build breaks (the dev server hides this). **Under npm (AD-2) hoisting hides this failure locally**, so the §8 production-build gate is the only thing that catches it — do not skip it.
4. **React component pattern (enforced):**
   ```tsx
   type MyComponentProps = {
     foo: string;
   };

   const MyComponent: React.FC<MyComponentProps> = (props) => {
     const { foo } = props;
     // ...
   };

   export default MyComponent;
   ```
   - Props as a `type` named `{ComponentName}Props` (not `interface`).
   - `const` arrow function typed `React.FC<Props>`.
   - Single `props` param; destructure inside the body.
   - `export default` as a separate statement at the bottom.
5. **Guard browser storage.** Wrap every `localStorage.setItem` / `sessionStorage.setItem` in try/catch — Safari private mode throws `DOMException`.
6. **Naming:** files `kebab-case`; components/types `PascalCase`; vars/functions `camelCase`; constants `SCREAMING_SNAKE_CASE`.

## 8. Pre-PR Gates (frontend)

- **Type check:** `tsc --noEmit` must exit 0 (dev server / esbuild silently ignores many type errors).
- **Production build** must exit 0 (webpack catches what the dev server hides).
- **Visual verification** in a real browser: golden path + one error state, light AND dark mode, validation-on-blur confirmed.
- **Every new import** confirmed as a direct dependency before opening a PR.
