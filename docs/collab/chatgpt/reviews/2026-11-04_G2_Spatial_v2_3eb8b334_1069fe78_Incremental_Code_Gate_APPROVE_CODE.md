# GPT independent incremental Code Gate — G2 Stage-1 spatial-v2 verifier

Date: 2026-11-04 (Asia/Shanghai). **VERDICT: APPROVE_CODE** — for the exact Formal Pair **Root `3eb8b334150018212ae1f51afb5e954b83fa1186` / Child+Gitlink `1069fe78841228cadbbfbe6afbd767eaed6225da`**.

Candidate branch: `v3-g2-spatial-policy-20261104`. Parent Owner-policy authority and implementation base: `f63454610ec2b95617c670444875339034c3c1c7` (prior source formal `a9ffd313770c5344195f415425124a5075e62b2b`). This review is a **docs-only bookkeeping successor**, not a replacement for Formal Root. V3 not promoted. A previous native old-contract report correctly remains FAIL under its original photometric hard gate; this document never retroactively changes its outcome.

## Exact scope independently inspected

- GitHub compare `f6345461..3eb8b334`: **one** implementation commit, seven root paths. Only production change `tools/g2/verify_robocasa_rgbd_pose.py`; one new policy test module, one legacy status assertion updated, README/runbook, SESSION/TODO. Child/Gitlink and `tools/g2/rgbd_pose` including native renderer/ray/Depth/cache are unchanged.
- Reviewed actual source diff and final `verify_robocasa_rgbd_pose.py`, complete policy tests and `docs/build/PSM-WMA_G2_Spatial_Acceptance_v2_and_GateC_Plan_2026-11-04.md`.
- Author evidence under `docs/collab/codex/evidence/2026-11-04_g2_spatial_policy_author_cpu/`: `gate.json`, `final_cpu/junit.xml`, `final_cpu/summary.json`, `contract_and_scope_proof.json`, `runbook_syntax.json`. JUnit explicitly shows **121 tests, 0 failure/error/skip**, comprising previous 83 + 38 new policy tests. Frozen 35 old-contract tests expected RED31/4 passed; author evidence records no definition changes. Ruff/format/AST/CLI are author-reported, not separately re-executed here. Previous 24 native synthetic OSMesa suite was **not re-run**, not counted in 121; earlier real RoboCasa geometry6/6 PASS belongs to source `a9ffd313` and must not be re-labelled as current-version execution.

## Findings

1. **PASS — policy semantics, `verify_robocasa_rgbd_pose.py:24–50,85–113,229–250`.** New `g2_stage1_spatial_v2` is explicitly identified, and `spatial_alignment_gate` is distinguished from original RGB photometry and from external human visual review. `geometry_gate` retains a compatibility name but is a **policy-versioned alias of complete automated spatial checks**, not merely isolated ray distance; consumers must inspect `acceptance_policy`.
2. **PASS — preserved physical criteria, `verify_robocasa_rgbd_pose.py:141–223`.** Author removed only `metrics['mae'] <= rgb_mae_max` from automatic spatial conjunction. Runtime identity, source/cache integrity, exact state/frame alignment, valid masks, quantization-bound fresh Depth, per-camera K+GL/CV poses, pixel reproject error <=1e-7, ray_status PASS with >=16 matches and <=0.01m underlying unchanged checker remain strict. Camera status is a spatial status under v2.
3. **PASS — diagnostics not suppressed, `verify_robocasa_rgbd_pose.py:161–170,203–215,238–240`.** Original RGB is still decoded and MAE/PSNR/SSIM computed and recorded; photometric status/count are independent, with unchanged MAE5 threshold and `blocking=false`. Missing/corrupt RGB is still an error. High RGB MAE may accompany automated spatial PASS but never becomes numerical RGB PASS.
4. **PASS — human provenance does not self-attest, `verify_robocasa_rgbd_pose.py:34–40,77–81,99–103`.** Owner review ref records only `EXTERNAL_RECORD_REFERENCED`, `verified_by_tool=false`. It does not verify ownership/scope/verdict. Users/reviewers must separately match the reference to the exact camera/episode/frames. Prior Owner visual acceptance was for the previously reviewed six images, **not** a blanket approval of new Gate C episodes.
5. **PASS — CLI/report compatibility, `verify_robocasa_rgbd_pose.py:241–324`.** New native return `SPATIAL_REPLAY_CHECKS_PASS` is clearly distinct from legacy `PHYSICAL_REPLAY_PASS`; synthetic and offline results are distinct. Invalid numeric thresholds result in non-success JSON. Legacy outputs are immutable, and CLI exit0 does **not** mean an external human review or complete Gate C.
6. **Gate C plan — ACCEPTABLE AS A BOUNDED DESIGN, NOT EXECUTION APPROVAL.** Three-to-five **complete episodes from distinct real underlying task classes**, external exact mapping-SHA selection manifest, per-episode complete cache verification, deterministic first/middle/last native geometry and RGB-to-Depth contour review, full bounds/coverage/throughput/RSS/compression and idempotent skip. Do not infer actual episode IDs or N100 membership. Server selection and resource readiness still need evidence.

No actionable production blocker was found in the reviewed incremental change.

## Next Gate and explicit boundaries

**Code Gate APPROVE_CODE only.** A narrowly scoped server-local read-only replay of the previously committed six-frame CloseFridge/global502 cache is technically appropriate next, using this exact Formal Root, no re-export, new immutable text report, unchanged physical thresholds and the actual Owner f634 reference. Require:
- `spatial_alignment_gate=PASS`, `status=SPATIAL_REPLAY_CHECKS_PASS`, true native `evidence_kind=SERVER_NATIVE_REPLAY`, all six independent geometry and cache/fresh checks PASS.
- `photometric_diagnostic=FAIL` if existing 5/6 MAE exceed 5, with unchanged values, and `owner_visual_review.status=EXTERNAL_RECORD_REFERENCED`, `verified_by_tool=false`. No reclassification of photometric FAIL as PASS.
- Preserve all prior reports/caches. Read-only access to source plus writing only a new report in an isolated evidence namespace; never touch the active shared worktree or live jobs.

**Gate C production execution is a separate decision after the new v2 real-host policy evidence.** Do not automatically launch 3–5 full-episode exports, N100, main V3 merge, video replacement, nav_sg/Global PSS, model training or GPU/EGL jobs. Gate C must separately review concrete task/episode manifest, estimated full-frame budget and disk capacity before execution. Any full native Gate C conclusion requires independent geometry *and* documented new-episode RGB/Depth alignment visual evidence.

Raw RGB/Depth/NPY/NPZ/MP4, server scripts and reversible payload remain server-only. Share non-sensitive aggregate textual evidence and paths, not raw sensor data.

**Codex response:** APPROVE_CODE for `3eb8b334/1069fe78` under v2 spatial acceptance. Do not confuse status labels or treat Owner provenance as an automatic PASS. Stage-1 Gate B v2 evidence on native server remains pending until actual replay.
