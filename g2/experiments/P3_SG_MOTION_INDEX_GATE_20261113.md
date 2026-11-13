# G2 P3 — Robot Chassis Deadband + Scene Graph Keyframe/Delta (isolated gate)

Date: 2026-11-13 UTC · Branch: `g2-sg-event-index-lab-20261113` · Base V3: `664678fd91c23bfd16505380d0d3db6cf9f15ad6`

**Gate status: CPU/static/real-v2-offline tests PASS; real GPU end-to-end v3 Worker and broader task-layout coverage NOT YET QUALIFIED.** This implementation is opt-in, not merged into V3, and does not touch running `g2_view`, the published v1/v2 data, native `nav_sg`, or immutable 9,126-Episode plan.

## What changed

1. **Robot chassis threshold is now 1 mm XY Euclidean / 1 degree wrapped yaw** rather than nearly zero (`1e-10 m / 1e-10 rad`). Scene object tolerance remains 1 mm 3D Euclidean / 1 degree SO(3).
2. Both robot and nonrobot thresholds are measured against the **last ACTUALLY RENDERED** physical owner (last drawn arrow, last rendered scene respectively), not the immediately preceding 2-Hz sample. Accumulation (0.4+0.4+0.4 mm) triggers the next marker refresh; strict `>= threshold` triggers. Full scene refresh also resets the robot marker owner.
3. **F27 now records the actual per-frame robot XY/yaw motion evidence** and stamps the new threshold recipe in its complete source receipt. Fail closed if a v3 source attempts to reuse floor arrows beyond 1 mm / 1 degree.
4. **PNG v3 index:** same v2 direct `view_refs` format. Additional binary-identical `floor_top.png` files are not recopied; instead a one-hop ref points to an earlier *physical* PNG (even if an earlier v2 physical owner was itself deduplicated).
5. **SG v3 index:** physical `scene_graph.json.gz` for the first frame and nonrobot scene changes (`FULL`), plus an extra physical SG if room/entity/link topology changes independently. For unchanged scene/SG topology, save `scene_graph_delta.json.gz` and `scene_graph_ref={ref_state:physical_sg_owner,delta:...}`. Every delta is against a **physical SG keyframe**, never a ref chain; every state records an independent `scene_graph_sha256`. `resolve_scene_graph(episode_root, state_id)` reconstructs exactly the original *entire* per-frame graph, including `frame_id`, `timestamp_ns`, `original_state_row_sha256`, exact bboxes and floating connection lengths, and relationship evidence.
6. **Fail-closed v3 schema** `g2_atomic_compact_6views_v3`, source/manifest hash check, exact frame monotonicity, explicit SG/Png ref validation, no symlinks and no relative path escapes. `plan.completed_output(... allow_index_v3=True)` accepts it; default v1/v2 codepath unchanged. `--sg-event-index` requires P0/P1/P2 flags explicitly. Production remains owner/manual start only.
7. **Historical v2 policy honesty:** v2 used the prior near-zero, adjacent-state robot threshold; an offline v2→v3 conversion records `PREVIOUS_SAMPLED_STATE_LEGACY`, not a false claim that its image frames were produced using the new 1 mm / 1 degree policy. A fresh real F27 v3 Worker requires `LAST_DRAWN_FLOOR_MARKER` provenance and certified threshold.

## Strict real RoboCasa A/B (offline repackage, original dataset never modified)

All eight Episode sources were existing complete `CloseBlenderLid` v2 data from `robocasa365-target-atomic-6views`. The v3 output was written only under `/tmp/g2_sg_event_lab_20261113/ab_real`.

| Episode ID | States | SG keyframes | SG deltas | Disk saved (allocated bytes) |
|---|---:|---:|---:|---:|
| 000211 | 20 | 12 | 8 | 18.97% |
| 000215 | 28 | 15 | 13 | 21.88% |
| 000217 | 30 | 16 | 14 | 30.31% |
| 000219 | 26 | 16 | 10 | 20.69% |
| 000222 | 35 | 22 | 13 | 11.59% |
| 000368 | 34 | 20 | 14 | 27.74% |
| 000380 | 25 | 14 | 11 | 18.21% |
| 000404 | 27 | 15 | 12 | 25.69% |
| **Total** | **225** | **130** | **95** | **21.54%** |

**Source v2**: 104,140,800 allocated bytes. **Converted v3**: 81,707,008 allocated bytes. 22,433,792 bytes saved across these eight episodes; **225/225 reconstructed SGs are JSON-deep-equal** with original SGs and **1,007/1,007 resolved PNGs are byte-SHA256 identical** to the original v2 logical views. Real Viewer source resolver checked all 100 images of 000211 and 210 images of 000217 against the stored v3 files (without modifying viewer code).

Notes:
- This measured reduction is from SG keyframe/delta and duplicate floor PNG elimination against the **old robot threshold** data. The additional floor savings of fresh 1mm/1degree robot gating have **not** been measured on a new real GPU Episode.
- The 8 real episodes belong to one task class. Other layouts/tasks may have different SG topology change rates and compression savings. Do not extrapolate 21.54% as a guaranteed dataset-wide reduction.
- Exact SG deltas still create a tiny file per sampled non-keyframe where per-frame metadata or numeric geometry evidence differs. This is intentional: avoiding those files would lose exact source/geometry evidence. Only full scene-graph keyframes are skipped when scene topology is stable.

## Tests and producer isolation

- Full copied G2 Python regression **927/927 passed** with real NavigateKitchen MJCF reference present in the isolated lab.
- Existing three Node Viewer regression smokes passed.
- New v3 Viewer read-only integration: 100 + 210 logical v3 image sources resolved to actual physical PNG files (PASS).
- Unit boundaries: 1mm XY, 1deg yaw, cumulative drift relative to last rendered marker, +/-pi wrap, 1mm/1deg strict edge, new source receipt fail-close, topology-change SG fallback, exact per-frame SG reconstruction, forged/future SG ref rejection, forged SG delta rejection even when a manifest receipt checksum is modified, direct one-hop PNG ref rehoming, and old v2/v3 opt-in Resume rejection.
- Original 9,126 immutable plan **read-only `plan --resume` PASS**, 92 batches, no worker dispatched and no formal file modified; this was run while the already owner-started v2 producer continued normally.
- Static Ruff checks for the new P3 module/tests and changed P1/runner Python code passed.

## Limitations and remaining qualification

- This Gate validates **incremental SG storage**; `atomic_6views_snapshots.py` still performs `oracle.extract` and `compute` for each real source state. Therefore **no numerical SG computation speedup** has been demonstrated or claimed.
- A fresh complete GPU F27 Worker with the NEW robot 1mm/1degree renderer + v3 packager has been tested with an isolated F27 source fixture and source-receipt provenance, **but not yet with a newly rendered real RoboCasa GPU Episode**. Do not promote into the user-started full production until a real independent task and H1 image review establish the new marker behavior.
- Existing training/downstream graph consumers need to use `resolve_scene_graph` for v3 instead of directly opening `state_N/scene_graph.json.gz`. The existing Viewer image resolver already works with direct v3 `view_refs`; it does not display SG.
- No current v2 published output is overwritten, and no standalone full-producer start, merge or nav_sg change was performed.
