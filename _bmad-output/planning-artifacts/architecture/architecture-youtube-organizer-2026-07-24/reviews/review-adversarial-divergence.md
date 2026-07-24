# Review — Adversarial Divergence Hunt

**Lens:** construct two units one level down that each obey every AD to the letter yet still
build incompatibly. Every pair found is a hole to close with a new or tightened AD.

**Verdict:** FAIL — four constructible incompatible pairs, plus one internal contradiction.

---

## D-1 (HIGH) — Two epics, two query grammars

**Unit A:** the Uncategorized/triage epic builds the browse call as
`GET /api/videos/?uncategorized=true&tag=guitar&tag=course&length_max=3600`.
**Unit B:** the Tag-detail/Filters epic builds
`GET /api/videos/?tags=guitar,course&max_minutes=60`.

Both obey AD-4 completely — one endpoint, params combine with AND, page-number pagination, no
infinite scroll. AD-4 says "one **documented** query-param grammar" and then never documents it.
Repeated-param vs comma-joined, seconds vs minutes, and which of the three dates a date filter
targets are all unfixed. This is precisely the clashing shared-data shape the lens hunts for, and
it is also the contract the frontend URL must map onto 1:1.

**Close it:** enumerate the grammar inside AD-4.

## D-2 (HIGH) — Two owners of a video's tag set, with opposite semantics

**Unit A:** the triage epic implements bulk tagging as an *additive delta* —
`POST /api/videos/bulk-tag/ {ids, add: ["guitar"]}`.
**Unit B:** the watch-page epic implements inline tag editing as a *set replacement* —
`PATCH /api/videos/{id}/ {tags: ["guitar","course"]}`, because that is the natural REST reading
of a `tags` field on the resource.

Both obey AD-1 (services only), AD-3 (generated types), AD-12 (optimistic per-item rollback).
Now run `EXPERIENCE.md` UJ-3 step 7: Alexis adds `course` on the watch page, then later
multi-selects that video during triage and applies `podcast`. Unit A's delta is fine — but the
reverse order silently drops tags, and any client holding a stale tag list and PATCHing the whole
set destroys concurrent additions.

Nothing in the spine says which semantics win. **The spine has two owners for one entity's
relationships.**

**Close it:** a new AD fixing tag mutations as explicit add/remove deltas, never set replacement.

## D-3 (HIGH) — Two tag-creation paths, two tag identities

**Unit A:** the triage typeahead creates a tag from whatever the user typed — `Guitar`.
**Unit B:** the Tags index (FR-9) creates `guitar`.

AD-18 makes tags unique *per user*, which both satisfy — `Guitar` and `guitar` are two different
rows. The library now has a split tag: two chips, two filter results, and the AD-11 `tsvector`
indexes both, so search reinforces the split. FR-9 ships tag-merge specifically because tag drift
is an anticipated failure — but merge is a *repair* for drift the architecture should not have
permitted mechanically.

**Close it:** fix tag identity (normalised form + a case-insensitive uniqueness constraint) in
the same AD as D-2.

## D-4 (MEDIUM) — Two places refresh the search vector, or neither does

**Unit A:** the tagging service explicitly recomputes the `tsvector` after mutating tags.
**Unit B:** the import service relies on a `post_save` signal.
**Unit C:** someone adds a database trigger.

AD-11 says the vector "is refreshed whenever a contributing field or tag set changes" without
saying *where*. Signals are the classic Django divergence — they fire on some paths and not
others (`bulk_create`, `update()`, and `bulk_update` all skip them), so a bulk tag apply through
`update()` silently leaves the vector stale and the video stops being findable by its own tags.
AD-1 arguably forbids a trigger, but only by implication.

**Close it:** name the refresh site explicitly in AD-11.

## D-5 (MEDIUM) — Orphans lag a full sync cycle

AD-6 says "a separate drain step"; AD-7 says an uncleared video "is retried on the next run".
**Unit A** drains at the end of the import, so orphans created in run *N* are retried at the end
of run *N+1*. **Unit B** drains at the start. Both obey the ADs; only one honours FR-6's
"retried on the next sync" as a user would read it. Under AD-9 (manual trigger only) each cycle
costs a deliberate user action, so the lag is real, not theoretical.

**Close it:** state that the drain runs at the start of a run *and* after import.

## D-6 (MEDIUM) — AD-5 contradicts AD-15

AD-5: "No boolean column caches a derived state." It then lists **Watched** among the derived
views. AD-15 writes `watched_at` — a column — when the threshold is crossed.

A literal reader of AD-5 concludes `watched_at` is forbidden and tries to derive watched from
playback events. A literal reader of AD-15 stores it. The two ADs disagree inside one spine.

The intent is sound and just needs saying: `watched_at` is a **recorded fact**; the Watched
*surface* is a derived lens over that fact. Uncategorized has no equivalent fact and must stay
computed.

**Close it:** re-word AD-5 to separate facts from derived states.

## D-7 (LOW) — Bulk mutation endpoint shapes

The conventions fix the *payload* shape (id list in, per-id outcome out) but not the endpoint
shape, so one epic writes `POST /api/videos/bulk-tag/` and another `POST /api/tags/{id}/apply/`.
Low blast radius — generated types keep both honest — but a naming rule costs one line.

## D-8 (LOW) — Who writes `availability`?

FR-19 detects unavailability "at play time and/or during sync". Sync-side is covered by AD-8.
Play-time detection happens in the browser, and AD-1 forbids the client writing state except
through a service. Whether that is a dedicated endpoint or a field on the generic video PATCH is
unfixed.

---

## Pairs tested and correctly closed

- Bulk selection vs pagination — conventions mandate an explicit id list, so "select all loaded"
  cannot silently become "apply to the whole filter". **Closed.**
- Soft-deleted, untagged video appearing in Uncategorized — AD-10's default-manager exclusion
  composes correctly with AD-5's derived query. **Closed.**
- Re-import of a video sitting in Trash — AD-10's three-way dedupe check closes it explicitly,
  and it is called out as the invariant rather than left implicit. **Closed, and well.**
- Inline YouTube writes bypassing crash-safety — AD-6's "no service or view ever calls a YouTube
  write directly" plus the layer table's gateway rule closes both routes. **Closed.**
- Sync run state read from two sources — AD-8 makes `SyncRun` the sole record. **Closed.**
