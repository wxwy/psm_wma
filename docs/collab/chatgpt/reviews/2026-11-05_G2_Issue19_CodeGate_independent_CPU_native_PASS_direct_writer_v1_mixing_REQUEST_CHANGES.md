# G2 Issue #19 / Draft PR #20 — Independent Code Gate: REQUEST_CHANGES (one focused root-version guard)

Date: 2026-11-05. Reviewer: GPT / independent server execution. All sensor data and artifacts remain server-local.

## Formal identity

- Reviewed implementation Root: `fbe578908a840a5f4e5b351f1c2e8fb019def6e5`.
- Unchanged Child/Gitlink: `1069fe78841228cadbbfbe6afbd767eaed6225da`.
- PR #20 docs/evidence successor head observed: `64ee6c6e4778d6c79f033b39877dc06360b31312`.
- PR base: `v3-g2-spatial-policy-20261104` at `9568723fd19d008be180c7b3e4126e1176c07d26`.
- Scope: only G2 uint16 zero-sentinel encoding/verification and safe versioned cache transition. No V3, V2, training, Child, nav_sg or source-data mutation.

## Independently verified PASS

1. The implementation was independently checked out into a fresh isolated server worktree `/tmp/g2_issue19_review_fbe578_20261105_fullshallow`, exact HEAD `fbe57890`, clean, Gitlink unchanged; this did not modify the previous formal source checkout.
2. A fresh execution using the server's real simulation Python produced **174 passed / 0 failed / 0 skipped** for the same three focused G2 modules, ~6.38 seconds: `tools/g2/test_depth_zero_sentinel.py`, `test_rgbd_pose_export.py`, `test_spatial_photometric_policy.py`. JUnit `/tmp/g2_issue19_independent_cpu_20261105/junit.xml`, SHA256 `23517ac72b42f500f669ce9bb341611669abce5ef2d209ee2d01b550e361289f`. Real independent Ruff 0.12.7 check PASS, format check PASS (12 files), AST 12 files PASS, `git diff --check` PASS.
3. A **real original RoboCasa CloseFridge global736/local234 EGL GPU4** test rendered only frames **73 and 74** into separate, disposable scratch output `/tmp/g2_issue19_native_replay_20261105/cache`, **not** into the Owner's production cache. Strict v2 CLI export PASS, native replay verifier exit 0, `SPATIAL_REPLAY_CHECKS_PASS`, cache integrity PASS, both Left+Wrist geometry PASS for both frames (4/4). RGB diagnostic PASS. v2 NPZ contains **exactly** `depth`, `frame_indices`, `K`, `T_world_camera_gl`, `T_world_camera_cv` and no `valid`, dtype uint16. At Wrist frame73 exactly 25 pixels, frame74 exactly 230 pixels encoded to zero; Left shows zero exclusions. No false 65.535m saturation/wrapping. All native per-camera reprojection/K/Pose/quantization checks passed. Native report SHA256 `e435b29edf2aa174fb26d452d2a9a3d53841a425985478befef83e3cf26715c3`. Exact scratch episode manifest SHA256 `038b53365acfd44d94dc7e9a8dbc8fae1458933d9e58f47694fe0578a89afe11`.
4. The existing 7 **production v1** completed episode caches were verified read-only with the frozen original v1 reader (7/7 PASS, 2,353 full frames); all **308,412,416** pixel mask values were compared, with **zero mismatches** between legacy `valid` and `depth > 0`. Evidence `/tmp/g2_issue19_independent_cpu_20261105/legacy_7_readonly_validation.json`, SHA256 `e10c23e994e85716ca19fdd416edcef08da3cfa837456d01830b4fe99cccea41`. No v1 files were converted/deleted or modified.

## One verified issue — direct writer admits an unversioned legacy-containing root

**Finding G2-I19-F1 (P2, review blocker against the explicit no-mixed-schema contract).**

Current `tools/g2/rgbd_pose/cache.py` `_check_root_schema(root)` rejects `cache_manifest.json` with legacy schema. `ensure_cache_manifest()` additionally rejects unknown nonempty `tasks`/`.staging`/`.failed` when the root manifest is missing. **But `export_episode()` calls only `_check_root_schema`**, bypassing the second check.

A fresh independent synthetic test constructed an output root containing `tasks/OldLegacy/episodes/episode_987654/manifest.json` with legacy schema `psm_wma_robocasa_rgbd_pose_v1` and **no root `cache_manifest.json`**. Direct invocation of `cache.export_episode(root, synthetic_source, [0], storage="uint16_mm", chunk_frames=32, recipe={}, replay_factory=FakeReplay)` unexpectedly succeeded and wrote a v2 episode under the same unversioned root:

```text
UNVERSIONED_DIRECT_WRITER_ACCEPTED EXPORTED legacy_and_v2_coexist_without_root_manifest True
```

The production **CLI path is protected** because it calls `ensure_cache_manifest` first; this is an exposed direct-writer/library path defect, **not** evidence of any actual mixing in the seven production caches. Nonetheless it contradicts the requested strict schema/transition invariant and is a small, reproducible gap to close before code promotion.

**Requested surgical fix:** Make direct `export_episode()` refuse a manifest-less root that already contains unverified/legacy episode artifacts or pending `.staging`/`.failed`, **before any new lock/staging/output creation**; keep the CLI path and legitimate fresh direct-writer test fixtures supported. Add one regression with an old episode and no root manifest and prove neither old files nor the root were mutated on rejection. Prefer a small shared preflight helper rather than creating another manager/framework. Preserve the existing 174 PASS and the real v2 GPU4 acceptance. No need to modify replay, nav_sg or the old caches.

## Decision and remaining operational boundary

**CODE GATE: REQUEST_CHANGES (one P2 preflight fix); not yet `APPROVE_CODE`.** Core codec, float32 distinction, no-persisted-valid storage, independent geometry, and real ep736 regression are confirmed functional. This is deliberately a narrow request, not a broad redesign. Once corrected and independently rechecked, an `APPROVE_CODE` decision may follow.

**No production resume authorization:** The existing official output root holds seven immutable v1 episodes and a v1 `cache_manifest.json`. The v2 CLI correctly refuses it. Codex supplied an **auditable migration plan**, not a runnable migration/promoter; an explicit safe version transition and retained rollback still need separate authorization and implementation before batch000 resumes. Do not claim the v2 two-frame scratch export converted those seven. No V3 merge, no full corpus export, no GPU7 or GPU0–3.

This review has not changed production source, original raw/Flat, the seven v1 caches, prior failures/staging, training or any V3 branch. Only separate ephemeral test/evidence paths were created on the authorized server.
