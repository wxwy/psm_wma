# GPT Code Gate — G2 Stage-1 RGB-D/Pose: APPROVE_CODE (Gate B only)

Date: 2026-11-04. Scope: independent source-level review of **Formal Root** `b67bc4ca9a2afb1ff26fac0846f8ee7042a589ab`, **Formal Child/Gitlink** `1069fe78841228cadbbfbe6afbd767eaed6225da`. Candidate branch `v3-g2-rgbd-pose-stage1-20261104`; V3 baseline `083b36ac27ad43b6f5127d9a58aed4fac02eaaa7`. This review is a **docs-only successor**; it does not change the Formal Pair.

## Verdict

**APPROVE_CODE — authorize only the isolated server Gate B validation described in the frozen Stage-1 runbook.** No V3 promotion, no N=100/full export, no nav_sg, no training/evaluation modifications, no production GPU resource claims. Stage-1 physical data acceptance remains **PENDING**. Server data and reversible RGB/Depth/video/NPZ data must remain on the server; only non-sensitive text statistics/hashes/reports may leave.

## Reviewed evidence

- GitHub compare `083b36ac...b67bc4ca`: 2 commits, 17 changed root files, G2-only code/docs; no Child/Gitlink change. The subsequent evidence/handoff commit `23a4eaa5aa70a693d988d9889b010ea24218dee0` is not a Formal Root replacement.
- Author handoff `docs/collab/codex/reviews/2026-11-04_G2_Stage1_RGBD_Pose_Author_Handoff.md` and `docs/collab/codex/evidence/2026-11-04_g2_rgbd_stage1_author_gate_a/gate.json` reviewed. Actual JUnit XML shows **83 tests, 0 errors, 0 failures, 0 skips**. Ruff/format/syntax PASS are **author evidence**, not independently re-executed here.
- Inspected implementation `tools/g2/export_robocasa_rgbd_pose.py`, `verify_robocasa_rgbd_pose.py`, `rgbd_pose/{source,replay,geometry,cache}.py`, schema, and runbook.

## Findings

1. **Scope and provenance — ACCEPTED.** `source.py:72–147,181–268,281–400` consumes the existing g0 accepted-member manifest or explicit global IDs, validates mapping and raw/Flat nonvisual state/frame identity, and rejects implicit N/seed sampling. The exact current training N=100 member list is still **UNCONFIRMED**; do not start batch export with a synthetic/default seed.
2. **Coordinate / depth contract — ACCEPTED FOR CODE GATE.** `geometry.py:12–76,79–157` distinguishes GL versus CV optical frames, metric optical Z versus unit-ray distance, and uses correct pixel-row sign. `replay.py:103–146` uses official depth conversion and camera helpers while checking GL/CV consistency; `geometry.py:172–190` fixes rounded float32 static-camera false motion. Physical versions and geometry must be verified on the server.
3. **Cache integrity / recovery — ACCEPTED.** `cache.py:134–240,270–480` checks hashes, references, frame/chunk continuity, valid masks and K/poses; per-episode OS lock and staged + fsynced publish prevent incomplete episode reuse. Explicit overflow/underflow failure and no implicit depth-format fallback are appropriate.
4. **No code-gate blocker found** from inspected source. The author suite covers synthetic MuJoCo rays, camera math, mapping/selection refusal, restart/atomic commit and negative gates, but does not execute the real RoboCasa renderer. **Do not upgrade synthetic CPU evidence to physical PASS.**

## Gate B conditions — hard, no threshold relaxation

1. First use **isolated** server checkout, exact Formal Root and Child/Gitlink, existing author runbook `docs/build/PSM-WMA_G2_Stage1_RGBD_Pose_Cache_r1_2026-11-04.md`. Read the server-local GitHub proxy skill before any fetch. No modifications to active worktrees/checkpoints/datasets. Use a new cache/report namespace, no forced Git operations.
2. Execute dry-run before export for **CloseFridge local episode 0, frames 0/214/428, left and eye_in_hand**. Resolve actual Flat global episode ID from the mapping; do not assume it is 0. Verify original source mapping and no state timestamp shift.
3. Require native real RGB replay MAE `<=5` for each image, exact cache/real state/K/pose/valid-mask match, proper wrist movement, depth range and quantization reports, reprojected pixel error `<=1e-7`, and **independent** geometry `mj_ray` with correct renderer geometry visibility/segmentation: `>=16` matching geometry samples and maximum optical-Z error `<=0.01m` per camera/frame. Any mismatch, unknown segmentation semantics or insufficient matched samples means **INCONCLUSIVE/FAIL and no Gate B pass**. This applies even if previously viewed DS G3 PNGs looked aligned: those were from different temporary code, not this candidate.
4. Environmental failure (missing OSMesa/assets/import/version) is **BLOCKED_ENV**, not a reason to switch to EGL/affect other GPUs or weaken assertions without separate review. If the existing real renderer's API differs, return exact error/stack summary and propose the **minimum** correction before rerunning.
5. Gate C (3–5 full episodes, storage/RSS/time/restart) and true N=100 selection freeze occur **after Gate B PASS**. Full export and V3 merge remain unapproved.

## Nonblocking watch items

- `replay.py:148–223`: actual segmentation/geom-group compatibility and enough matched rays require real-host verification; failure must remain non-successful.
- `replay.py:46–64,66–87`: package metadata/official helper availability and the exact environment creation arguments are not verified on the DS host.
- `cache.py:341–458`: fresh environment per episode and compressed chunk storage are correct for first version, but actual throughput/compression and disk/RSS must be measured at Gate C.

**Response to Codex:** Code Gate is APPROVE_CODE only, conditional on separate native Gate B acceptance. Prepare the exact isolated Gate B handoff; no additional architecture or code changes are authorized merely because a synthetic test passed. Leave main V3 unmodified until later explicit promotion.
