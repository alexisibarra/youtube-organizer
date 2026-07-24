---
name: YouTube Organizer
status: final
created: 2026-07-23
updated: 2026-07-24
sources:
  - ../../prds/prd-youtube-organizer-2026-07-20/prd.md
  - ../../../../Docs/FRONTEND-STACK.md
  - ../../../../Docs/component-inventory-frontend.md
  - ../../../../Docs/architecture-frontend.md
companions:
  - ../../architecture/architecture-youtube-organizer-2026-07-24/ARCHITECTURE-SPINE.md
---

# YouTube Organizer — Experience Spine

## Foundation

Responsive web, multi-surface. Desktop and mobile web are **both first-class from day one** (PRD §8) — this is not a desktop product that tolerates phones. Desktop gets keyboard-accelerated triage; mobile gets touch triage; neither is a degraded copy of the other. There is no native app, in any phase (PRD §6.3).

**UI system:** shadcn/ui on Next.js 16 App Router with Tailwind v3 and Radix primitives, per `Docs/FRONTEND-STACK.md`. Both spines inherit from it. This document specifies the **behavioral delta only**. `DESIGN.md` is the visual identity reference and owns how this looks; token references below resolve into it by name.

**Legacy warning:** the shipped `/frontend` code predates both this spine and the stack doc. It is **migration debt, not a design input** — do not treat existing component behavior as precedent. Inventory in `Docs/component-inventory-frontend.md`.

**Single user.** One person, one account, no sharing, no collaboration, no public surface.

> **Visual references.** `mockups/key-library.html`, `mockups/key-triage.html`, `mockups/key-watch.html`, `mockups/key-mobile.html`. **This spine wins on conflict** — the mocks predate several remediation decisions (notably the Library hub, the tags-only filter row, and status icons) and are directional, not normative.

## Information Architecture

| Surface | Reached from | Purpose | Phase |
|---|---|---|---|
| **Library (hub)** | App open · sidebar · `g l` | The entry surface. Rows of the app's organizational dimensions — **not a list of videos**. | 1 |
| **Tag detail** | Library Tags row · filter chip · `g t` | Videos carrying a tag, filterable and sortable. Where browse-by-intent actually happens. | 1 |
| **Uncategorized** | Sidebar · `g u` | Derived view: no tags, no playlist. The triage surface. | 1 |
| **Tags** | Sidebar · Library row | Tag index. Create, rename, remove, merge. | 1 |
| **Watch** | Any video card | Embedded player + the video's own metadata. Single column, no rail. | 1 |
| **Search** | `/` · top bar | Global over title, description, channel, tags. Scopable to current view. | 1 |
| **Filters panel** | Filters button on any browse surface | Channel, length range, watched, freshness, date range. | 1 |
| **Trash** | Sidebar | Recently deleted, restorable within the retention window. | 1 |
| **Settings** | Avatar menu | Google connection, `_Inbox` designation, sync status, theme, watched threshold. | 1 |
| **Playlists** | Sidebar link · Library row | Index of hand-built collections. Sidebar entry is a **plain link**, not an expandable list. | 2 |
| **Playlist detail** | Playlists index | Ordered contents; add, remove, reorder. | 2 |
| **Needs review** | Sidebar · inline notice | Expired perishables **and** unavailable videos, combined. | 2 |
| **Watched** | Sidebar | Lens over watched videos. Additive — they still live in Library. | 2 |
| **Migration** | First run only | One-time import of pre-existing YouTube playlists. | 2 |

**The Library hub is the load-bearing IA decision.** PRD §3 says Library is *all* captured videos; PRD §8 bans infinite chronological feeds. A single dated list of 900 videos would satisfy the first and violate the second. So Library does not render a list of videos at all — it renders **the app's organizational structure**, one `{components.shelf-row}` per dimension:

- **Tags** — most-used first, a few videos each, "View more →" to the Tags index
- **Playlists** *(Phase 2)* — recently-used first, "View more →" to the Playlists index
- **Channels** — most-frequent first, "View more →"
- **Recently imported** — a **bounded** strip (max one row, no pagination, no "view more" into an endless list). The one concession to recency, deliberately capped so it cannot become a feed.
- **Needs review** *(Phase 2)* — appears only when non-empty

There is no chronology to habituate to and nothing to scroll past. Drilling into any row lands on a finite, filtered set.

**Sidebar order** (fixed, bounded, never scrolls): Library · Uncategorized · Tags · Playlists · Needs review · Watched · Trash. Playlists is a plain link precisely so that 40 playlists cannot push Trash below the fold.

**Surface closure.** Every PRD capability lands on exactly one surface, and every surface is the destination of at least one journey. **Uncategorized** and **Needs review** are *states*, not containers — they self-maintain, never need manual emptying, and never block anything else.

## Subtraction Contract

*Invented section. The product's actual identity statement — behavioral before visual, which is why it lives here.*

The subtractive premise — *keep YouTube's visual language, cut its machinery* — is argued in `DESIGN.md § Brand & Style`. This section owns the operative half: what is **kept**, and what is **cut**.

**Kept — the familiarity budget.** Card shape and proportions. The 16:9 thumbnail at 12px radius. Grid/list duality with a toggle. Duration badge bottom-right. Left sidebar on desktop, bottom tab bar on mobile. Pill-shaped filter chips in a scrollable row. Search in the top bar. Collapsed description behind a "more" toggle.

**Cut — absent, not hidden.**

| Removed | Why it cannot come back |
|---|---|
| Recommended / suggested videos | The doomscroll itself. The most important absence in the product. |
| The right rail entirely | **Absent at every breakpoint**, not collapsed at small ones. The app never occupies the region where YouTube trains your eye to look for "what's next." |
| Comments | Not the user's content, not why he saved the video. |
| Autoplay-next | Even for his own hand-built playlists. Progression is manual, always (PRD §8). |
| Infinite chronological feed | Browse is by intent. Pagination or explicit load-more only. The Library hub exists so no surface ever needs an endless list. |
| Subscriptions, Shorts, Home feed | Anything sourced by anyone other than Alexis. |
| Notifications and badge counts on Uncategorized | An unfiled pile is a backlog, not a debt. Counting it out loud turns the library back into a guilt-pile. |

Uncategorized shows its count **on its own surface**, where it is useful. It does **not** wear a red dot in the nav.

**One acknowledged breach.** The embedded YouTube player renders a recommendation grid on its own end screen when a video finishes. `rel=0` has not suppressed this since 2018 — it now only restricts recommendations to the same channel. Alexis considered an end-card interception and **declined it**; the leak stands as an accepted platform limitation alongside PRD §10 R2. The leak means row 1 of this table is **not fully honored in Phase 1**, at the moment of peak doomscroll vulnerability. Stated plainly here rather than buried, and worth revisiting if it proves to pull him back into scrolling.

## Voice and Tone

Microcopy only. Aesthetic posture lives in `DESIGN.md.Brand & Style`.

**Dry and factual.** A tool Alexis built for himself; no audience to perform for. Full sentences, no exclamation marks, no encouragement, no celebration.

| Do | Don't |
|---|---|
| "87 videos imported." | "Nice! 87 new videos added 🎉" |
| "Inbox cleared." | "All done — inbox zero!" |
| "14 videos deleted." | "Successfully deleted 14 items!" |
| "Nothing here." | "Your library is empty. Let's fix that!" |
| "Couldn't remove 3 videos from `_Inbox`. Retrying next sync." | "Oops! Something went wrong." |
| "This video is no longer available on YouTube." | "Uh oh — we can't find this one 😕" |
| "Delete 14 videos? They move to Trash." | "Are you sure you want to do this?" |

**One hard rule:** errors always say what the app will do next ("Retrying next sync"), never only what failed. Dryness is not unhelpfulness.

## Component Patterns

Behavioral. Visual specs live in `DESIGN.md.Components`.

| Component | Use | Behavioral rules |
|---|---|---|
| **Video card** | Everywhere | Thumbnail click opens Watch. Tag chip click filters by that tag. Hover reveals `⋮` (tag, freshness, add to playlist, delete); on touch `⋮` is always visible — hover-only affordances are banned. |
| **Thumbnail status layer** | Every card and row | Silent unless abnormal. Duration always renders. Watched, unavailable and expired each render **scrim + status badge** — never scrim alone. Two statuses render two badges side by side. |
| **Selection** | Any multi-select surface | Solid outline + filled checkbox, both, achromatic. Desktop: `x` or checkbox click; shift-click ranges. Touch: long-press to enter, tap to toggle. `Esc` clears. |
| **Focus indicator** | Keyboard navigation | **Dashed** ring at wider offset — visually distinct from selection by *style*, not width. Focused items carry `scroll-margin` so sticky bars never obscure them. |
| **Bulk action bar** | ≥1 item selected | Sticky bottom, above the mobile tab bar. Live count, then Tag · Freshness · Add to playlist · Discard. **All destructive actions live here, bound to the selection.** Count announces via `aria-live`. |
| **Tag chip** | Cards, rows, watch page | Read-only in browse (click filters). Inline-editable on Watch. **Overflow past three collapses to `+N`, which opens a popover** with the full set — keyboard-operable, `Esc` closes, focus returns to the trigger. |
| **Filter chip row** | Library drill-downs, Tag detail, Playlist detail | **Tags only**, most-used first, horizontally scrollable, ending in "All tags →". Multiple tags combine with AND. Active chips invert. Filter state lives in the URL. |
| **Filters panel** | Filters button | Everything structured: channel (searchable multi-select), length range (dual slider + numeric inputs), watched, freshness, and date range over imported / source-added / published (from–to, either bound optional). Applied filters surface as removable chips. |
| **Shelf row** | Library hub | Title + count + horizontal card strip + "View more →". Horizontally scrollable on touch; arrow-key navigable. Never paginates in place — "View more" navigates to a real surface. |
| **View toggle** | Any browse surface | Grid ⇄ list. **Persisted per surface**, not globally — Library drill-downs want grid, Uncategorized wants list, and one global preference would fight the user on every visit. |
| **Confirmation dialog** | Every destructive action | shadcn `AlertDialog`. States count and consequence. Never suppressible, no "don't ask again." Focus lands on Cancel. |
| **Inline banner** | Import, sync, quota, orphans, scope | shadcn `Alert`. Never modal, never blocking. Failure banners never auto-dismiss. Dismissible only when purely informational. |
| **Sync status** | Settings, inline banners | Reports last successful sync and any pending-clear orphans, and carries the **Sync now** trigger. Read-only over the sync run's own record. *Phase 1 has no "next scheduled run" — sync is user-triggered (AD-9); that line returns with scheduled sync.* |

## Triage Modes

*Invented section. The weekly loop is the product's core, has no YouTube precedent, and carries the hardest constraint in the PRD.*

**The bound (PRD §8, load-bearing for SM-C2):** filing a single video takes **≤2 interactions**; applying a tag or attribute to a multi-selection is **a single action**. If triage costs more than the doomscroll it replaced, the product has failed.

Two modes, both Phase 1. State is preserved across a switch.

### List mode — the default

Gmail-shaped, because that pattern is already in the user's hands.

1. Uncategorized opens in list view, densest legible rows.
2. Select: checkbox click, shift-click for ranges, or `x` on the focused row. `a` selects all loaded.
3. The bulk action bar appears with the live count.
4. One action applies to the whole selection — Tag, Freshness, Add to playlist, Discard.

Handles mixed batches, discards, freshness, and multi-tag without constraint. **This is the general-purpose mode**, and the one an unpredictable week goes through.

### Focus mode — tag-first bucketing

Inverts the question from *"what tags does this video need?"* to *"which of these are guitar?"* — how a week's catch actually clusters.

1. **Pick the tags first — one or several.** The header pins: **"Filing as: `guitar` + `course`."**
2. Sweep the grid or list, toggling matches. Click or tap only — no dialogs, no menus, no per-video decisions.
3. One Apply files the entire selection with the whole tag set.
4. Change the tag set, sweep again.

**Documented limitation — do not describe this mode as unconstrained multi-tag.** Uncategorized self-clears on a video's *first* tag, so a video leaves the surface as soon as it is filed. **A video's full tag combination must be chosen at sweep time.** A tag realized afterwards costs a Library round-trip via search or Tag detail, outside the ≤2 bound. The multi-tag picker mitigates the common case; it does not remove the underlying constraint. A frozen-working-set model would have, and was not chosen.

### Rules binding both modes

- **Incremental, never all-or-nothing** (PRD §8). Abandonable mid-sweep at any moment. Partially-triaged is a first-class state; whatever was filed is immediately browsable, and a non-empty Uncategorized never blocks Library, search, or playback. No "mark as done" step exists.
- **Optimistic application.** Tags apply instantly and reconcile in the background. Failure surfaces a toast and reverts only the affected rows, never the whole sweep. Reverted rows re-announce via `aria-live`.
- **Selection survives filtering.** Narrowing mid-sweep must not silently drop selected-but-now-hidden items; the bar's count always tells the truth.
- **Discard always confirms.** Bound to the selection rather than the card, so one dialog covers a whole sweep. Single-video discard from a card `⋮` also confirms — FR-11 requires it for bulk, and this spine applies it uniformly rather than splitting the rule.

## State Patterns

| State | Surface | Treatment |
|---|---|---|
| Cold load | Any browse surface | shadcn `Skeleton` in the active view's shape — card skeletons in grid, row skeletons in list, shelf skeletons on the hub. Never a spinner. |
| **Fetch / server error** | Any data surface | Inline banner: "Couldn't load your library. Retry." Explicit Retry action. Cached data stays visible beneath rather than being replaced by an error screen. |
| **Auth expired** | Global | Banner: "Your session expired. Sign in again." Single action to re-auth. In-flight edits are held and replayed after re-auth where possible, or reported as lost — never silently discarded. |
| Empty Library (first run) | Library hub | "Nothing here yet." Body: designate an `_Inbox` playlist to start capturing. Single action → Settings. |
| **Empty Uncategorized** | Uncategorized | **The win state.** "Nothing to file." No celebration, no illustration. The dryness *is* the reward. Quiet link back to Library. |
| Empty search | Search | "No matches for `{query}`." Active filters listed and individually clearable — the usual cause is a filter, not the query. |
| Empty filter result | Any browse surface | "No videos match these filters." Inline "Clear all". |
| Empty playlist | Playlist detail | "`{Playlist name}` is empty." Single action to add. |
| Empty shelf row | Library hub | Row is omitted entirely rather than rendered empty. |
| Sync running | Global banner | "Checking `_Inbox`…" Non-blocking; the app stays fully usable. |
| Sync complete | Any | Toast: "87 videos imported." Nothing more. Suppressed if the user is mid-sweep. |
| Sync partial failure | Uncategorized | Banner: "83 of 87 imported. 4 failed and stayed in `_Inbox`." Expandable detail. Never silent (FR-6). |
| Pending-clear orphans | Uncategorized, Settings | Banner: "3 videos imported but not removed from `_Inbox`. Retrying next sync." Informational; no action demanded. |
| Quota exhausted mid-sync | Global banner | "YouTube's daily limit reached. 41 of 100 imported. Resuming tomorrow." Committed videos stay committed. **Persists until explicitly acknowledged** — a partial import he doesn't notice is a library he thinks is complete. |
| Sync failed entirely | Settings, global banner | "Last sync failed at {time}." Manual retry available. *(The "Next attempt {time}." half returns with scheduled sync — AD-9.)* |
| Read-only scope granted | Settings, Uncategorized | Persistent notice: inbox auto-clear and playlist deletion disabled; everything else works (FR-1). Offers re-consent. |
| Unavailable video | Card, Watch | Card shows scrim + ⚠ badge, play disabled. On Watch: "This video is no longer available on YouTube." Actions: open in YouTube, or delete. Never a broken player (FR-19). |
| `_Inbox` missing | Settings, global banner | "The playlist set as `_Inbox` no longer exists." Action: choose another (PRD Open Question 5). |
| Deletion complete | Any | Toast: "14 videos deleted." No undo affordance — the dialog already did that job. Trash is in the sidebar. |
| Offline | Global | Toast once: "You're offline." Cached browse continues; playback and sync do not. |

## Interaction Primitives

**Two first-class input models.** Desktop is keyboard-accelerated; touch is not a degraded fallback.

**Keyboard (desktop):**

| Key | Action |
|---|---|
| `j` / `k` | Move focus down / up |
| `x` | Toggle selection on focused item |
| `Shift`+click | Select range |
| `a` | Select all loaded |
| `t` | Tag selection (typeahead) |
| `f` | Set freshness on selection |
| `Backspace` / `Del` | Discard selection (always confirms) |
| `Enter` | Open focused video |
| `v` | Toggle grid ⇄ list |
| `/` | Focus search |
| `g` then `l`/`u`/`t`/`p` | Go to Library / Uncategorized / Tags / Playlists |
| `Esc` | Clear selection, close dialog, exit search |

**Shortcut conformance (WCAG 2.1.4 — mandatory, not optional).** These are all printable single characters, which triggers a specific AA requirement. All three of the following ship:

- A **Settings toggle** disabling single-key shortcuts entirely.
- **Remapping** for every binding.
- **Focus scoping** — shortcuts are inert while focus is inside any text input, the tag typeahead, a dialog, or the player iframe (where `j`/`k`/`f` are YouTube's own bindings).

Screen-reader browse mode collides with `t`, `f`, `g`, `k`, `x` and `v` in NVDA and JAWS; the disable toggle is the supported escape and must be discoverable, not buried.

**Touch (mobile):** long-press enters selection mode; tap toggles once in it. Tap outside or Cancel exits. Bottom tab bar for primary destinations, drawer for the rest. **All tap targets ≥24px** (WCAG 2.5.8), with list rows relaxing from 32px to 44px on touch.

**Banned everywhere:**

- **Infinite scroll.** Pagination or explicit load-more only. The delivery mechanism of the doomscroll, banned even where convenient.
- **Autoplay-next**, including within hand-built playlists.
- **Hover-only affordances.**
- **Per-video modal gauntlets** during triage.
- **Modal stacks deeper than one level.**
- **Suppressible destructive confirmations.**

## Accessibility Floor

Behavioral. Computed contrast values and token remediation live in `DESIGN.md § Colors`.

Single-user does not lower this bar — a personal tool is used for years, in bad light, tired, one-handed, at 1am.

- **WCAG 2.2 AA** across both surfaces, both modes. `Docs/FRONTEND-STACK.md` §8 already gates on light-and-dark verification before every PR.
- **No state is conveyed by color alone** (1.4.1). Selection is outline + checkmark; status is scrim + **status badge**; active nav is tint + **edge bar**. In each pair the second element carries the signal because the first one measured below threshold — the arithmetic is in `DESIGN.md § Colors`.
- **Focus is visually distinct from selection** (2.4.7) by *style* — dashed vs solid — not by width.
- **Focus is never obscured** (2.4.11). Every focusable list item carries `scroll-margin` clearing the sticky bulk action bar and the mobile tab bar.
- **Single-key shortcuts ship with disable, remap, and focus scoping** (2.1.4). See Interaction Primitives.
- **Target size ≥24×24** (2.5.8) on every interactive element, including selection checkboxes and tag chips.
- `Tab` order matches reading order on every surface. `Esc` always closes the topmost layer.
- Selection count announces via `aria-live`; the bulk action bar is the only place the count is stated, so it must reach screen readers. Optimistic-revert also announces.
- Active nav carries `aria-current="page"`.
- Video thumbnails are decorative when the title is adjacent (`alt=""`); the title is the accessible name.
- The embedded player exposes native controls; playback is never mouse-only. Captions are the player's own.
- **Forms** (per `Docs/FRONTEND-STACK.md`): `react-hook-form` with `mode: 'onBlur'`. Errors are programmatically associated with their field (3.3.1) and announced; every input has a persistent visible label (3.3.2) — placeholders are never labels. Error text uses `destructive-foreground` at verified contrast.

## Responsive & Platform

| Breakpoint | Behavior |
|---|---|
| `≥ xl` (1280px+) | Sidebar expanded at 240px. Grid 4 columns. Shelf rows show 5 cards. |
| `lg` (1024–1279px) | Sidebar expanded. Grid 3 columns. Shelf rows show 4. |
| `md` (768–1023px) | Sidebar collapses to 72px icons. Grid 2 columns. Shelf rows show 3. |
| `< md` | Sidebar gone; bottom tab bar + drawer. Grid 2 columns. Shelf rows scroll horizontally. Search full-screen. The bulk action bar stacks above the tab bar. |

**Mobile tab bar** (4 tabs): Library · Uncategorized · Search · More. "More" opens the drawer: Tags, Playlists, Needs review, Watched, Trash, Settings.

**Two columns on phones, never one.** A single-column stack of full-width thumbnails *is* the doomscroll shape this product exists to replace — an anti-doomscroll requirement, not a density preference. This is the canonical statement of the rule; `DESIGN.md` carries the measurement.

**Platform limitations (accepted, stated once, never surfaced as errors):**

- **Background / lock-screen playback is impossible in-app** (PRD §10 R2). The embed pauses on tab-blur and lock; continuous audio is Premium-gated and blocked for embeds. *Open in YouTube* covers the cooking-and-driving case.
- **The embed's end screen shows recommendations.** See Subtraction Contract. Accepted, not mitigated, in Phase 1.

Both belong in Settings as plain statements of fact.

## Inspiration & Anti-patterns

- **Lifted from YouTube — deliberately and extensively:** card anatomy, thumbnail proportions and radius, duration badge placement, grid/list duality, pill filter row, sidebar-on-desktop / bottom-bar-on-mobile, collapsed description. The familiarity budget, spent on purpose.
- **Lifted from Gmail:** high-volume list triage — row checkboxes, shift-click ranges, a bulk action bar on selection.
- **Lifted from streaming-service home screens:** the Library hub's shelf rows. Borrowed for their *structure* (finite rows, drill-down) and explicitly **not** their behavior — no algorithmic ordering, no endless carousel, no autoplay preview.
- **Lifted from shadcn:** the entire component vocabulary. The brand is *what is subtracted from YouTube*, not a from-scratch design system.
- **Rejected — filling the right rail with the user's own queue.** Considered seriously. Rejected because occupying that region at all retrains the "what's next" reflex the product exists to break. The rail is absent, not repurposed.
- **Rejected — undo toasts in place of delete confirmations.** Faster, and Trash makes it safe. Rejected in favor of FR-11 as written. **A chosen cost** — downstream must not optimize the dialog away as friction.
- **Rejected — a badge count on Uncategorized.** Re-creates the guilt-pile the product exists to remove.
- **Rejected — swipe-to-triage card stacks.** One-at-a-time by construction; violates the single-action bulk bound.
- **Rejected — a frozen working set for Focus mode.** Would have removed the multi-tag constraint entirely; Alexis chose the multi-tag picker instead. The residual limitation is documented in Triage Modes rather than hidden.
- **Rejected — intercepting the player's end screen.** See Subtraction Contract.
- **Rejected — algorithmic suggestions that auto-apply.** Suggestions (FR-8, Phase 2) are assistive and always confirmed.
- **Rejected — gamification of any kind.** No streaks, no inbox-zero celebrations, no progress rings.

## Key Flows

Journey names mirror PRD §2.3 verbatim.

### UJ-2 — Alexis clears his weekly inbox *(Phase 1 · the recurring core loop)*

Sunday evening. He opens the app and pulls the week's `_Inbox` — 94 videos.

> **Amended 2026-07-24 (`ARCHITECTURE-SPINE.md` AD-9).** This flow originally opened with *"Background sync has already pulled the week's `_Inbox` … without him asking."* **Phase 1 sync is user-triggered only** — Phase 1 runs on localhost (AD-17), so nothing is running to sync on a schedule. Sync is a **"Sync now"** action in Settings. Everything else below is unchanged: sync is non-blocking, the app stays fully usable while it runs, and every state pattern below still applies. Scheduled sync returns with the production envelope.

1. He opens the app on his phone. Library shows its shelf rows. The Uncategorized tab carries **no badge**; he goes there because it's Sunday.
2. He taps **Sync now**. A non-blocking banner reads "Checking `_Inbox`…" and he keeps browsing while it runs. It settles into: "94 videos imported. 3 not removed from `_Inbox` — retrying next sync." Nothing blocks.
3. He switches to **Focus mode** and picks two tags: **"Filing as: `guitar` + `course`."**
4. He sweeps, tapping the eleven guitar-course videos. **Apply** — one action files all eleven with both tags. They leave Uncategorized.
5. He resets to `barca` alone, sweeps eight. Then `podcast` + `history`, fourteen. Then `cooking`, six.
6. Four sweeps have filed 39 videos. **Fifty-five remain**, and this is the honest shape of the work: the long tail is one-offs that don't cluster, and Focus mode has no advantage over List mode there.
7. He switches to **List mode** for the tail, shift-click-selecting runs of similar videos and tagging them in batches of three to six. Another eight or so bulk actions.
8. He selects the junk — six videos past-him saved — and hits Discard. One dialog: "Delete 6 videos? They move to Trash." Confirmed.
9. **Climax:** Ninety-four videos took about **fifteen minutes and twenty bulk actions**, on a phone, one-handed — against a doomscroll that would have taken longer and produced nothing. Uncategorized reads **"Nothing to file."** No confetti. Just a true statement.

*Honest cost note, kept in the spine deliberately:* this flow requires reading ~94 titles and performing ~20 bulk actions. It is **not** four sweeps and done. If real use shows this exceeding the doomscroll it replaces, SM-C2 has failed and FR-8 suggestions should be pulled forward from Phase 2 immediately — that is the designed release valve.

*Incremental exit:* he stops after two sweeps. What he tagged is browsable; the rest waits without penalty or badge. **Failure:** removal from `_Inbox` fails for three videos → they are tracked as orphans, retried next sync, never skipped as duplicates.

### UJ-3 — Alexis finds something to watch for the mood/moment *(Phase 1 · the payoff)*

Random Tuesday night. He has an hour and wants guitar.

1. He opens the app instead of YouTube. **Library shows shelves, not a feed** — Tags, Channels, a bounded Recently-imported strip. Nothing to scroll past.
2. The Tags row shows `guitar · 24` near the front. He taps it.
3. Tag detail opens with 24 videos. He taps **Filters** and sets length **≤ 60 min**. Filters combine with AND; the URL updates, so the view is linkable.
4. Eight videos. He recognizes one immediately — the thumbnail does the work it always did.
5. **Climax:** Under ten seconds from opening the app to knowing what he's watching. No scrolling. The set was finite because he built it, and it *ended* — the structural difference between this and the thing it replaced.
6. He taps it. Watch opens: centered player, single column, **no rail**. Title, channel, his tags beneath, description collapsed.
7. Mid-video he realizes it belongs under `course` too. He taps `+` in the tag row and adds it without leaving the page.
8. At ~90% it auto-marks Watched. Scrim and ✓ badge appear on the thumbnail. It stays exactly where it was.
9. When the video ends, **the embed shows YouTube's own recommendation grid.** This is the accepted platform leak. He closes the tab or navigates back.

*Cooking variant:* he taps **open in YouTube** for background audio, since the embed pauses on lock. **Nothing-fits variant:** no video matches → he still isn't doomscrolling, because there is nothing to scroll.

### UJ-1 — Alexis migrates his existing YouTube playlists into the app *(Phase 2 · one-time)*

1. First run after connecting Google with read **and write** scope.
2. The app lists every YouTube playlist he owns, with counts. Nothing pre-selected.
3. He ticks the ones worth keeping and starts the import. Progress inline; each playlist replicated as an app Playlist of the same name, membership preserved.
4. **Climax:** A summary states it plainly — "7 playlists, 412 videos imported." Years of structure now live in the app, mirroring what he had. Nothing lost, nothing reorganized behind his back.
5. The app *offers* to delete the imported playlists from YouTube. Each deletion confirms individually. He accepts four, declines three.
6. The declined three stay on YouTube untouched. YouTube is now just a source.

**Failure:** a playlist partially imports → reported as failed in the summary, and **deletion is not offered for it** (FR-4).

### UJ-4 — Alexis keeps the library lean *(Phase 2 · ongoing curation)*

1. Opening the app, a Needs-review shelf row has appeared on the Library hub: "14 past their watch-by window." Not a modal, not a badge — a row he can ignore.
2. He opens **Needs review**. Two groups: expired perishables, and videos YouTube no longer serves.
3. Expired first. Match highlights from March; a news explainer whose news is over. He selects nine and discards. One dialog.
4. The unavailable group: three videos deleted or made private at source. Metadata intact, playback impossible. He deletes two, keeps one.
5. **Climax:** One sweep and the library reflects what he still actually wants to watch. The rot leaves in a batch instead of accumulating silently — the difference between a library and a pile.
