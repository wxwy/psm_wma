# PSM-WMA V3 — H3-E Route-B Stage 3C BLOCKED: multi-file camera video local offset

- Date: 2026-09-29
- Frozen formal implementation root: `a707c80393f927e8e30ace877473d475fd24c6cf`
- Frozen formal child/Gitlink: `55582980b992dac10481b0ba9e86cd8075cef33c`
- Stage 3C verdict: **H3E_ROUTE_B_STAGE3C_BLOCKED**
- Candidate fix child: `ba1996c85cc4de41df2e8bd22c0289ea4deef736`
- Candidate fix is **not formal authority yet**; it requires CPU + targeted GPU regression evidence.

## Failure

The frozen Stage 3C B1 H5 builder reads the global LeRobot `dataset_from_index` and passes it as
the start frame inside a single camera mp4. This is valid only while that camera lives in one
video file.

For `SlideDishwasherRack/20250820`, the wrist camera spans `file-000.mp4` and
`file-001.mp4`. Episodes in file 1 therefore require a file-local frame offset. The frozen
builder instead uses the global dataset offset and raises an out-of-range frame-index error.

Observed affected production-train scope:

- one shard: `SlideDishwasherRack/20250820`;
- 43 / 9036 train episodes;
- wrist camera only;
- all eight Stage 3C worker partitions contain affected episodes.

Production `RoboCasaLeRobotDataset` decodes the same episode successfully, so source data and
the production loader are not reopened.

## Candidate fix

Child `ba1996c85cc4de41df2e8bd22c0289ea4deef736` changes only the B1 asset builder/test:

1. `load_shard_episode_meta` now requires and stores per-camera
   `videos/{cam}/from_timestamp`;
2. a fail-closed `video_local_start_frame(...)` converts that file-local timestamp to
   `round(from_timestamp * fps)`;
3. video decoding now uses this camera-local start rather than global `dataset_from_index`;
4. source-backed regression locks `SlideDishwasherRack/20250820/ep_000461`:
   global row `76996`, wrist file index `1`, local timestamp `23.7`, local start `474`.

No production loader, Local/model/trainer, H5 schema, manifest authority, or catalog semantics
are changed.

## Validation required before promotion

1. child HEAD exactly `ba1996c85cc4de41df2e8bd22c0289ea4deef736`;
2. full builder test file PASS, zero skips on H100 source host;
3. ruff check PASS;
4. ruff format --check PASS;
5. git diff --check PASS;
6. targeted real-VAE build of exact affected identity
   `SlideDishwasherRack/20250820/ep_000461` in a fresh temp output;
7. compare decoded source frames against production loader for the same wrist episode and
   demonstrate exact/zero-difference equivalence;
8. H5 reader/schema/causality PASS;
9. one single-file control identity also PASS to demonstrate unchanged behavior.

Only then may root Gitlink advance to `ba1996c85cc4de41df2e8bd22c0289ea4deef736` and Stage 3C resume.

## Recovery rule

Do not run old and new builders concurrently against the same worker partition/output path.
Allow the frozen 555 workers to finish or stop them first. Once the candidate fix is promoted,
rerun all 8 worker partitions against the existing Stage 3C output. Valid H5 files are verified
and skipped; failed/missing affected episodes are rebuilt. Existing valid cache files must not
be deleted or regenerated wholesale.
