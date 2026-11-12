# G2 RoboCasa365 Target-Atomic 6views — Full-Corpus Source Preparation Audit (2026-11-12)

## Purpose / output

The owner fixed the eventual dataset root to:

`/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-6views`

"6views" is a dataset family name. The output contains valid room top/up/four wall directions plus **independent Island 4views** when native Room/Island geometry needs them. Island images must remain in `islands/<island-id>/...`, not silently merged into wall views. The default renderer is **F27**. Visual surface resolution 10 mm, navigation collision resolution 10 cm, and orthographic output sampling 1 cm/pixel. Nonexistent views are not generated. Source observations are 20 Hz; selected map states are 2 Hz including final frame.

**Only the owner may manually launch production.** Source-read-only discovery, code updates, CPU unit tests and isolated offline model-compile probes do not constitute approval or launch.

## Actual independent on-server discovery

- Flat V3 mapping and meta episodes: **9,126 matched records**; **18 task classes**; source frames **2,231,347**.
- Per-record official `model.xml.gz`, `states.npz`, `ep_meta.json`: **9,126 / 9,126 present**.
- Existing target-atomic-depth `manifest.json`, `COMPLETE.json`: **9,126 / 9,126 present**, matched to the global mapping. This does not replace a full audit of each depth chunk's contents.
- Layout counts: 1=636, 2=1029, 3=870, 4=852, 5=961, 6=845, 7=1062, 8=946, 9=1014, 10=911.
- Selected spatial state frames (20 Hz → 2 Hz, final frame included): **235,475**.
- Immutable plan batches with 100 episodes except final: **92**. The plan files exist only in the server's V3 `.g2_acceptance` area; the final target output directory was not created by this audit.
- GPU jobs, true native data production, final six-view data production, model training: **NOT STARTED**.
- Available disk measured on November 12: /mnt/data1 approximately **156 GiB free**, /mnt/data approximately **206 GiB free**; avoid permanent retention of intermediate world-pointclouds, 10mm voxel artifacts, numeric graphics diagnostics.

## Source probe and code

- Source-asset path rebinding maps only verified historical absolute asset prefixes to the installed RoboCasa/robosuite source directories. **10 / 10 different official Layout IDs** independently compiled with MuJoCo 3.3.7; model import samples have 1,083 to 2,927 compiled Geoms. The derived geom-role and official category/fixture candidate has **0 unmatched collision Geoms** in those 10 sampled episodes. These are *probe outcomes*, not all 9,126 compiled.
- Source role extraction uses the factual compiled collision/geom-group/alpha flags and official ep_meta fixture/object identities. Robot and auxiliary Geoms excluded, glass and windows retained, unknown categories explicit. It does not fabricate semantic Room/Island labels.
- `g2/offline/atomic_6views_plan.py`: flat-map and Depth source identity discovery, immutable batch plans, final-frame sampling, output path and Island policy.
- `g2/offline/atomic_6views_source.py`: episode-specific source rebinding and FULLPHYSICS shape/width audit; no model rendered.
- `g2/offline/atomic_6views_metadata.py`: episode-specific semantic candidates from compiled source and official metadata. Historical generator/source role review remains independent.
- `g2/offline/atomic_6views_compact.py`: atomic compact export from a **completed** F27 per-episode receipt, retaining only orthographic PNGs, independent Island PNGs, compressed SG, simple completeness receipt.
- `g2/tests/test_atomic_6views_preparation.py`: synthetic plan/source/compact tests.
- Layout IDs are **not a whitelist**; only positive integer and source provenance are checked. The 10 IDs above are descriptions of the current dataset. The generic transport adapter and nav_sg native worker have separately been merged as [PSM-WMA #44](https://github.com/wxwy/psm_wma/pull/44) and [nav_sg #11](https://github.com/wxwy/nav_sg/pull/11).


## Task selection and resumable manual planning (November 12 update)

The selection API is independent of batch size:

- Omit `--task`: select **all 18 tasks**. Repeat `--task OpenDrawer --task CloseFridge` or use `--task OpenDrawer,CloseFridge` to select some.
- Omit `--episodes-per-task`: select **ALL** episodes from every chosen task (this is the default, not 100).
- `--episodes-per-task 100`: choose the fixed earliest **100 global episode IDs per task**, not 100 newly pending episodes on every restart. The limit is per task; `--batch-size 100` independently controls dispatch grouping.
- `--resume`: skip only compact episode directories whose source-pinned `source_fingerprint`, expected frames, renderer, manifest SHA and atomic completion receipt all agree. An incomplete or mismatched directory blocks rather than silently overwriting.
- An existing `--plan-root` can be **reused with `--resume`**; it is checked against the original selection and source recipe. Batch manifests are not regenerated; the caller's later executor must skip already-completed outputs at dispatch time. The real `g2.offline.batch_render` scheduler also already has own resume for *materialized* render jobs.
- The compact publisher accepts a `--selection-record` to bind its completion receipt to the planning source identity; legacy unbound outputs are not silently resumed as complete.
- `scan` and `plan` are CPU/read-only discovery and immutable manifest operations. They **do not start any production jobs**.

Illustrative preflight only (from V3 source root; don't confuse with a production launch command):

```bash
python -m g2.offline.atomic_6views_plan scan
python -m g2.offline.atomic_6views_plan scan --task OpenDrawer --task CloseFridge --episodes-per-task 3 --resume
python -m g2.offline.atomic_6views_plan plan --plan-root /new/immutable/preflight_plan --batch-size 100
# Repeat the same plan command with --resume to reuse that plan's immutable batches.
```

Real server dry-run: task selection OpenDrawer+CloseFridge, 3 each, yielded 6 selected/pending, 190 spatial states, production_started=false. Selection/resume CPU tests are checked separately from runtime/semantic production readiness.

## Unresolved production blockers — no automatic start

1. The existing F24/F27 render command requires a **source-bound scene GT manifest**, per-state verified Room/Island snapshots and Scene Graph, complete native 10 cm occupancy and 10 mm color worker outputs, plus original visual-Geom inventory. Today these were assembled only for the approved two pilot episodes, **not** for each of 9,126 distinct original scenes.
2. Room boundaries and Island ownership are derived by the native pipeline. The existing source-known-free-region approximation has `TEST_ONLY_NOT_CERTIFIED` provenance. Do not recycle Layout1 or Layout10 Room/Island snapshots or stage-scene role maps for new scenes.
3. A new per-episode native source → Room/SG → dualmap → F27 → compact orchestration and bounded resume still needs to be implemented and independently real-scene validated. The 92 planning manifests are **not** accepted by `g2.offline.batch_render` as if they were already-prepared native scene manifests.
4. Human review is complete for original Layout1/10 **visuals**, not every unique room layout/object configuration. Source candidates are not human semantic certification. True end-to-end production readiness, 1/2 Hz online throughput and Cosmos 256x256 packing remain separate gates.

Current status: **FULL_CATALOG_AND_SOURCE_COMPILE_READY; NEW-SCENE_NATIVE_ROOM_SG_PIPELINE_BLOCKED; NO 9,126-EPS PRODUCTION START AUTHORIZED.**

Recommended immediate engineering target: one independently built non-pilot Layout4 native Room/Island scene graph from its source (without copying Layout1/10 evidence), followed by the full dualmap/F27/compact chain; only then submit a manual-start batch plan for broader acceptance.
