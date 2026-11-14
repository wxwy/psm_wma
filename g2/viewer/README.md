# G2 Spatial Replay Viewer

Source-controlled static multi-view player for RoboCasa365 target-atomic.

## Install

Run after the compact producer created the output `tasks/` directory:

```bash
cd /mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3
PY=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/robocasa_sim_venv_20261023/bin/python
PYTHONPATH="$PWD/.g2_runtime_deps_py313:$PWD" "$PY" -m g2.viewer.install \
  --mapping /mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic/flat_v3_mapping.parquet \
  --raw-root /mnt/data1/data_v2_0617/robocasa365_official/v1.0/target/atomic \
  --output-root /mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-6views
```

Generated `view/` content:

- `index.html`, `viewer.css`, `viewer.js` — copies of tracked sources.
- `catalog.json` — all 9,126 episodes in the V3 mapping (global/local ID,
  original frame count and original task instruction).
- `source_videos` — symlink to read-only source LeRobot data. MP4s are **not**
  copied or converted.

Existing generated views, scene graphs, manifests and working producer processes
are not modified.

## HTTP access

For a standalone local server:

```bash
python3 -m http.server 18765 --bind 127.0.0.1 \
  --directory /mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-6views
```

Open `http://127.0.0.1:18765/view/`.

With the existing 18765 service whose root contains a `data1` symlink,
open `http://127.0.0.1:18765/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-6views/view/`.

Bind to loopback only or add authentication; Python `http.server` has no
access controls and will serve all files readable by its process.

## Behavior

- Tasks and metadata are from the immutable catalog; completed episodes
  are discovered **live** through the HTTP directory index. Press Refresh
  to include newly finished episodes without restarting the server.
  Incomplete episodes are rejected by `COMPLETE.json` validation.
- The instruction is sourced from each original V3 mapping entry.
- The timeline uses the original 20 Hz timestamps. All three camera videos
  share a clock. The View image is the most recent **preceding** G2 spatial
  frame (normally 2 Hz). Previous/Next step through available G2 spatial
  frames and seek the cameras to the matching source timestamps.
- View PNGs are downloaded and fully decoded ahead of time, then synchronously
  drawn onto a persistent Canvas. The previous frame remains visible during
  network/decode latency; rapid scrubbing invalidates stale async frames.
  This prevents floor_top from flashing blank between 2 Hz frame changes.
- The six view choices are `floor_top`, `upper_up`, `plus_X`, `minus_X`,
  `plus_Y`, `minus_Y`, plus original left/right/wrist cameras. If G2 omitted
  an empty upward view, the card displays a missing-view placeholder.
- The layout allows adding/removing rows and blocks (max five per row);
  drag the handle to insert into another column/row. Dropping onto a full
  row swaps blocks. Rows of 1–3 cards cap each card to one third of the
  workspace; rows of 4–5 cards resize evenly to fit the entire line.
- Layout settings reside in browser localStorage, never in the dataset.
  Reset Layout enables the three-row adaptive default.

## Tests

```bash
node --check g2/viewer/viewer.js
python -m pytest -q g2/tests/test_viewer_install.py
```

Run the installer again only when the checked-in UI or V3 mapping changes.
Newly completed episodes do not require reinstalling or reindexing.
## Island four-direction views

For each selected Episode, the UI discovers Island IDs from the original
episode_manifest.json state records. Only direction PNGs explicitly listed in
view_pngs are offered; the four Island directions are plus_X, minus_X,
plus_Y and minus_Y, grouped under each specific Island ID. Multiple Islands
are shown as separate groups. The Viewer uses the corresponding Island PNG
for that exact spatial state; it does not substitute a global room side view.

Saved layouts remain stable when changing Episode. A previously selected Island
that is absent from the current Episode is explicitly marked as unavailable and
displays a placeholder, never another Island image.



## Fixed G2 and video directories

The Viewer intentionally uses fixed, read-only server paths and offers
no filesystem picker, server-directory chooser or recursive scan.

- Six-view PNGs and Scene Graphs:
  /mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-6views
- Original 20 Hz left/right/wrist camera videos:
  /mnt/data1/data_v2_0617/robocasa365_official/v1.0/target/atomic

The browser loads pinned task and instruction metadata from catalog.json.
When a Task is selected or Refresh Episode is clicked, only that task's
tasks/<task>/episodes/ one-level HTTP listing is read to identify already
generated Episodes. The selected Episode COMPLETE receipt and manifest are
loaded on demand. Images are fetched and decoded on demand; no scan of frame
directories is performed.

The renderer supports v1 view_pngs and v2 direct view_refs. The latter
resolves only an earlier reference state containing the real PNG. This also
applies to Island directional views. The original 20 Hz video timeline
remains unchanged.

## Published-only task and view filtering

The browser supports both the original long /data1/.../view/ URL and the
shortcut /view/ symlink. It resolves the actual fixed output root once by
probing the dataset's tasks directory, so /view/ does not accidentally point
to the HTTP server's unrelated /tasks/ path.

At page load and on Refresh Episode it reads only the published task and
Episode directory indexes. The Task dropdown shows **only tasks with output
Episode directories**, with each task's **published Episode count** rather than
its total target-data count. In the G2 compact pipeline, output directories
are published on completion. When an Episode is selected its COMPLETE and
manifest records are validated before any media is displayed.

A View dropdown lists only sources backed by the selected Episode's manifest:
real sixview/Island PNGs plus valid direct view_refs that resolve to an earlier
owner state. The three camera entries appear only when the original MP4 is
reachable by a same-origin HEAD request. Missing choices from a saved layout
are replaced by an available source for the new Episode; no disabled phantom
choices are shown. The display row limit of five and the no-flicker Canvas
renderer are unchanged.

## Adaptive three-row default workspace

The workspace opens with **three rows** when no custom saved layout exists:

1. The original left, right and wrist camera videos.
2. Global floor_top, plus_Y and plus_X views.
3. The first available Island's plus_X, minus_X, plus_Y, minus_Y views
   (the actual Island ID comes from the selected Episode manifest).

Only sources available in that Episode are chosen. If an expected camera,
global direction or Island direction is missing, it is filled in deterministic
order from floor_top, plus_Y, plus_X, minus_Y, minus_X, upper_up, left, right,
wrist, then other actual Island directions. Row 1/2 never consume Island views
if a real global/camera source exists, preserving the four Island directions
for row 3. When fewer than 10 distinct views exist, real views may be reused
to retain the 3/3/4 block shape; no missing images are invented.

Automatic defaults follow each new Episode's manifest and accessible cameras.
An explicit drag, add, remove or source change persists a custom arrangement.
The Reset Layout button restores the adaptive three-row defaults. Existing
saved custom layouts from the previous v1 storage key are preserved, while
the previous untouched two-row default migrates to the new adaptive default.


## Recovering the default from browser layout storage

If an old two-row layout remains after updating, click Reset Layout in
the workspace. Alternatively open the one-time recovery URL:
  /view/?reset_layout=1&v=20261114-force-3rows

The recovery URL stores auto preference in the current browser layout-only
localStorage key. history.replaceState consumes the reset_layout flag, so
later manual layout edits persist normally. The v parameter forces a fresh
HTML URL. No unrelated browser storage, cookies or data are deleted.


## Seven independent view filters and exact global view count

Above the Episode instruction, seven **independent three-state dropdowns**
filter the current Task's completed Episodes: floor_top, upper_up, plus_X,
minus_X, plus_Y, minus_Y and Island. Each has exactly three choices:
不限 (no condition), 包含 (must exist), 不含 (must not exist). All selected
conditions are combined using logical AND.

The separate exact count input accepts integers **1 to 6**, or blank for
no count condition. Count uses only distinct available **global sixview**
directions across the Episode (sixview PNGs or valid direct view_refs).
Island directional views do not affect that count. The Island condition is
based on Episode state islands metadata.

When filters are inactive, the existing published Episode list loads without
extra per-Episode I/O. When active, the Viewer reads only the current Task's
episode_manifest.json files, bounded to 10 concurrent requests, and caches
the resulting facts. No frame PNGs or original MP4s are scanned to filter
Episodes. Invalid numeric inputs are flagged; clearing filters restores
the full published Episode list. Filter results update the Episode dropdown
and its matched count, without touching production data.


## Camera playback synchronization

The hidden original left-camera video establishes the 20 Hz master playback
timeline. Visible Left, Right and Wrist video tiles are followers.

All play/resume operations align the follower media time with the current
master timestamp before invoking play. If an HTML5 video seek is pending, the
follower waits for the seeked event rather than starting at zero. Seeked
callbacks recheck the current master timestamp, discard stale tiles, and never
start playback if the Viewer is paused. At the end of a follower MP4, the
final video frame remains visible and its play() is not invoked (which could
otherwise auto-rewind an ended HTMLVideoElement to zero). On pauses and
scrubbing, all cameras are aligned to the same time; during playback, drift
is corrected periodically. The original video files are never rewritten.

This fixes Right/Wrist jumping back to their first frame while the main
timeline remains at an unrelated nonzero position.


## Floating row rails and sticky morphing timeline

The Viewer workspace no longer has a text header, help subtitle or footer
legend. Reset Layout and Add Row retain their prior look and work **after**
the complete display-row stack.

Each row has an *absolutely positioned* control rail outside the view grid's
right boundary. Its top square X button removes the row; the narrow vertical
plus button below adds a view block (up to five). Both have hover titles,
keyboard focus styling and low idle opacity. The control rail is not a grid
column and must never shrink or shift the 1–5 view tile columns.

The original Timeline is maintained at the same natural document position
until its top reaches the viewport. A zero-height non-sticky anchor before
the player measures scroll displacement over 76 CSS pixels. The Timeline
panel itself uses CSS position:sticky;top:0; and becomes a compact toolbar
as that displacement rises from zero to 76px. The scroll progress controls
simultaneous geometric height/opacity interpolation: original title/time/
transport fade and compress, current Episode instruction appears in the same
18px semibold typography as the original language instruction, the existing
range input narrows between View-frame prev/play/next controls on the left
and current spatial frame, raw frame and clock time on the right.

Scroll back up and the exact same interpolation reverses before the timeline
returns to its original position. All compact actions delegate to the
original View-frame step and play/pause functions; the shared scrub element
and three-camera master clock remain unchanged. Passive scroll events are
requestAnimationFrame-throttled. On smaller screens the control rail and
compact toolbar shrink responsively. The compact toolbar keeps the media
visible below it, not above it.

The JavaScript smoke test checks scroll 0/50/100%, upscroll reversal,
resizing, disabled controls, preserved scrub identity, source-instruction
copy, and the display-row rail's absolute positioning.


## Smaller flat compact timeline, stable workspace position

The 2026-11-14 compact refinement halves the compressed instruction font
from 18px to 9px (16px to 8px on mobile), and the progress bar thickness
from 6px to 3px. The compressed progress thumb is hidden entirely; only
the blue filled track remains. Previous/next View frames are now « and »,
with a small flat play/pause symbol in the middle; all three controls have
no backgrounds or borders. Compact metrics retain both spatial and raw
frame numbers and now show current **and total** time.

Morph speed is doubled: 76px of scrolling, down from 152px. The compact
surface is roughly 40–45px tall on desktop, versus about 89px previously,
a reduction over 40%. A new timeline-surface child owns the visible
timeline while the transparent, pointer-pass-through outer sticky panel
keeps its normal height in document flow. Morphing the inner surface
never moves the following display grid and never changes the scroll
anchor's natural document position. This prevents the previous intermediate
jitter and leaves real views visible below the compact flat toolbar.
The compact surface has no shadow or floating-card appearance; it keeps
only a subtle bottom dividing line.

The same native time-scrub range input, master-clock camera synchronization
and View-frame step handlers remain in use. The normal expanded timeline
is unchanged, and scrolling upward reverses the morph.


## Dense workspace controls and more legible compact timeline

2026-11-14 revision: compact instruction font grows from 9px to 18px
(8px to 16px on mobile); compact spatial frame, raw frame, and current/total
time fonts grow from 9px to 12px (8px to 10.4px on mobile).
Instruction row height adjusts to 24px desktop / 21px mobile,
with a tightened line height to preserve the compact toolbar footprint.
Frame/time metric slots become wider to prevent truncation.

Each view tile's top select/drag/remove toolbar shrinks from 43px to
26px (~60%; mobile 35px to 21px); the view select height shrinks
29px to 17px, and label type 11px to 8.8px (~80%; mobile 9px to 7.2px).
All top-bar affordances remain accessible and functional.

Adjacent display tile columns now use exactly half the previous gap:
--gap:clamp(4px,.55vw,8.5px) versus 8px/1.1vw/17px, with mobile
gap 2px versus 4px. The three-column rule uses explicit equal fractions
so the prior space-between does not mask the requested reduction.
Display row-to-row spacing halves from 10px to 5px; workspace-to-timeline
and bottom actions spacings are halved as well. The absolute floating
row control rail remains outside the grid and does not consume tile width.


## Ending Right/Wrist videos on the actual last frame

The prior ended event callback could call resumeSlave on an already
finished follower while Left was still short of the nominal Episode duration.
That could trigger the browser's native replay-from-zero semantics.

The revised end handler never invokes play(). It pauses the follower
and parks its current frame at duration - 0.025s, within the final decoded
20 Hz video frame. A bounded 0.10s end guard preemptively parks followers
before the browser fires ended. A WeakSet latches finished followers across
normal master-clock polling, sync and pause; only an explicit backward seek
releases that hold. Terminal seeking is issued once, not repeatedly while
seeking is true. Left remains the master timeline. No original MP4 bytes
or production Episodes are changed.

The view tile's bottom metadata/text strip is separately reduced to about
60% of its previous vertical height using 9px -> 3px top/bottom padding
on desktop and 6px -> 2px on mobile. The metadata text and fonts are
unchanged. Source selector toolbar height and tile spacing remain unchanged.


## Reliable MP4 replay: byte-range HTTP and seek-first playback

The stock Python SimpleHTTPRequestHandler used on port 18765 returned
HTTP 200 and the full MP4 payload even when browsers requested a Range
(e.g. Range: bytes=1200-1399). The source-controlled lightweight
g2.viewer.http_server serves MP4 single-byte ranges with HTTP 206,
Accept-Ranges: bytes, exact Content-Range, Content-Length, suffix
and open-ended ranges, HEAD and HTTP 416. Static HTML/JS/CSS, task/
Episode directory listings and symlinked RoboCasa videos remain unchanged.

From the V3 repository:

    python3 -m g2.viewer.http_server --bind 127.0.0.1 --port 18765       --directory /mnt/data/shenzhen/szrobot/logs/g2_http_18765_root

For video replay, the browser now waits for the Left hidden master
HTMLVideoElement's completed seeked/metadata state BEFORE invoking play().
The replay generation invalidates asynchronous results if a user pauses
or selects another Episode. The old ended event no longer overrides a
fresh rewind to zero. Redundant forced seeks at pause and during replay
have been removed; Right/Wrist still receive independent guarded seeked
callbacks and remain parked at their real final MP4 frames on completion.

These changes address a verified HTTP seek protocol defect plus an
independent JS race, rather than assuming server CPU shortage.
The server is threaded, serves only trusted local bound paths and
does not change any producer or training workflows.
Test with original RoboCasa clips, including repeated EOF/replay, pause
during asynchronous seeks, nonzero replays, and scrubbing.
