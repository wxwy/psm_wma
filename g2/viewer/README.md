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
  Reset Layout returns to the initial two-row layout.

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


## Choosing data folders

The source selector above Task/Episode supports local operating-system folders
and same-origin server HTTP directories, without modifying the data producer.

### Browser filesystem picker

Click 选择本机文件夹. On desktop Chromium/Edge (localhost or HTTPS), this calls
the browser's native operating-system directory chooser in read-only mode.
Choose an output root, parent folder, or a directory containing nested G2
outputs. The browser recursively discovers complete G2 Episode directories
using both COMPLETE.json and episode_manifest.json. It prunes state/frame
image subdirectories, limits traversal size, and reads PNG frames on demand.
No chosen files are uploaded or written.

The native file chooser sees the filesystem of the computer RUNNING THE
BROWSER, including mounted network drives. A browser on a local laptop
reaching the server over SSH port forwarding cannot open an unmounted
remote /mnt/data1 path. Use the server HTTP path feature for that.

When the modern directory API is unavailable, a webkitdirectory input lets
the browser enumerate a folder for compatibility. Beware that it may be
costly on multi-million-file dataset roots; desktop Chrome/Edge is preferred.
Task descriptions and episode indices reuse matching pinned V3 metadata;
unknown tasks display only metadata present in their manifests.

Use 原始视频目录 to optionally select the local LeRobot target/atomic root,
so left/right/wrist videos are loaded from local MP4s. If not provided, mapped
Episodes continue using the existing same-origin source video links.

### Server HTTP directory

Enter a URL visible to this HTTP server in 服务器 HTTP 目录 and click
扫描子目录. The Viewer recursively discovers dataset roots containing a
tasks folder and lists Episode directories. The COMPLETE.json receipt and
manifest are validated upon selection, so incomplete outputs are not played.
The URL must be same-origin. Plain Python http.server cannot browse arbitrary
filesystem paths: only paths under its configured web root are available.
The configured old HTTP service has a /data1/ symlink to /mnt/data1/; entering
/mnt/data1/... also uses that known URL mapping. Click 恢复默认 to return to
the pinned G2 output.

Both source modes are read-only. The saved layout stays in localStorage;
selected directory handles are not uploaded or persisted to the server.

## UI layout: local and remote directory panels

The data-source selector uses two balanced columns on desktop (Local left,
Server right), stacking vertically below 1,000px. The remote panel offers a
hierarchical directory dropdown populated from the **current same-origin HTTP
directory listing**. Select a child to enter it, or use the Up button to return
one level; Refresh rereads the current level. The manually editable HTTP path
and the existing Scan & Load action remain available. This dropdown **cannot**
enumerate arbitrary Linux paths outside the server's published HTTP root.

The task's natural-language instruction now uses 18px semibold type on desktop
(16px on small screens) for clearer review; other playback and layout controls
are unchanged.
