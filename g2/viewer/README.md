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
