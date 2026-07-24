# Glossary — YouTube Organizer

Companion to `SPEC.md`. These terms are used with exactly these meanings in the kernel, in
`ARCHITECTURE-SPINE.md`, and in `EXPERIENCE.md`. Where a term names a *derived* state, that
is load-bearing: derived states are computed by query at read time and never stored (`AD-5`).

| Term | Definition |
|---|---|
| **Library** | The canonical set of **all** captured Videos. A Video always lives in the Library, independent of any Tag or Playlist — those are optional overlays and never determine whether a Video exists. Deleting a Video from the Library removes it entirely. |
| **Video** | A single YouTube video captured into the app. The app stores its **own copy** of the metadata (title, description, channel, thumbnail, duration, published date, YouTube URL/ID) plus app-side timestamps, so it survives removal from any YouTube playlist. Belongs to zero-or-more Playlists; carries Facets. |
| **Source (YouTube)** | YouTube, used only as the origin of videos. Never the home of organization. |
| **`_Inbox`** | One normal YouTube playlist the user designates as the capture target, replacing Watch Later (which the Data API cannot reach). The app reads it and removes imported items from it. The designation is persisted per user in the database — never an environment variable. |
| **Migration** | The one-time first-run import of pre-existing YouTube playlists, replicating their structure in the app. |
| **Uncategorized** | A **derived view** of the Library: Videos with no Tags and no Playlist membership. Self-clearing — a Video leaves the moment it gets its first Tag or Playlist membership. A *state*, not a container; an Uncategorized Video still lives in the Library. |
| **Facet** | A structured attribute used for filtered browsing: **Tag**, **Channel**, **Length**, **Freshness**, and **Dates**. Facets are how the user *finds*. |
| **Tag** | A free-form, multi-value label (`history`, `guitar`, `barca`, `podcast`) carrying topic *and* format. Identity is the **normalised name** — trimmed, internal whitespace collapsed, case-folded — unique per user; the display form the user first typed is preserved for rendering. A Video has zero-or-more Tags. |
| **Channel** | The source YouTube channel, captured automatically. A browse/filter facet. |
| **Length** | The Video's duration, captured automatically, stored as integer seconds. A filter facet. |
| **Playlist** | A hand-built, user-curated, **ordered** collection ("Guitar Course Vol.1"). How the user *curates sequences*, as distinct from Tags/facets which are how he *finds*. Distinct from the YouTube playlists that exist only as source or inbox. |
| **Freshness / Shelf-life** | A Video is **Evergreen** (never expires) or **Perishable** (has a watch-by window). The app tracks a Perishable's age and flags it once expired. |
| **Watched** | Derived state, set when the user's **contiguous covered playback** passes the threshold. Shown as a badge; the Video stays in place, and the state is manually togglable. |
| **Availability** | Whether a Video is still playable on YouTube. **Available** by default; **Unavailable** when YouTube no longer serves it (deleted, private, region-blocked, removed). Metadata survives; playback does not. |
| **Needs review** | A derived view combining expired Perishables and Unavailable Videos. Like Uncategorized, a state rather than a container. |
| **Trash** | Soft-deleted Videos, restorable within the retention window. On permanent purge the row is hard-deleted and a **tombstone** (YouTube ID) is written. |
| **Tombstone** | A lightweight record of a permanently purged YouTube ID, so a deleted Video is never resurrected by a later import from a still-populated `_Inbox`. |
| **Orphan (pending-clear)** | A Video imported and durably persisted, but not yet removed from `_Inbox` on YouTube. Retried on the next sync, never skipped as a duplicate. |
