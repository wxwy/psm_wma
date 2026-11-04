# G2 spatial-v2 verifier — fresh incremental Code Gate

- Formal Root: `3eb8b334150018212ae1f51afb5e954b83fa1186`.
- Child/Gitlink: `1069fe78841228cadbbfbe6afbd767eaed6225da`, unchanged.
- Candidate: `v3-g2-spatial-policy-20261104`.
- Parent/Owner authority: `f63454610ec2b95617c670444875339034c3c1c7`.
- Prior reviewed implementation: `a9ffd313770c5344195f415425124a5075e62b2b`.
- Evidence/Inbox/publication successors are metadata, not Formal Root replacements.

## Owner decision implemented

Owner accepts the original RGB/Depth contours/occlusions of the six reviewed
CloseFridge images, supported by source identity, native Depth/K/Pose/runtime
and6/6 independent geometry PASS. Re-rendered RGB is diagnostic, not a training
replacement. Numeric MAE5 still fails5/6 historically and is not altered.
Visible aliasing is an observation, not a proved unique root cause. Old
`PHYSICAL_REPLAY_NOT_ACCEPTED` reports remain immutable under their old contract.

Only production file `tools/g2/verify_robocasa_rgbd_pose.py` changes:

1. `acceptance_policy=g2_stage1_spatial_v2` identifies the Owner authority.
2. Automatic `spatial_alignment_gate` retains source/cache/runtime/Depth/mask/
   K/Pose/reprojection/ray checks. `geometry_gate` is a versioned alias.
3. `photometric_diagnostic` separately records complete per-image metrics,
   MAE threshold5 and checked/failed counts; numerical FAIL no longer blocks.
4. `owner_visual_review` is NOT_PROVIDED or EXTERNAL_RECORD_REFERENCED,
   with provenance reference and `verified_by_tool=false`. The tool does not
   read/authenticate the reference, validate its scope or assert human PASS.
   Its automatic spatial scope is explicit. No acceptance checkbox exists.
5. Native success is `SPATIAL_REPLAY_CHECKS_PASS`; synthetic success is distinct.
   No new legacy physical PASS/FAIL is emitted or old report rewritten. CLI0
   expresses automatic native checks/offline integrity, not full Gate C closure.
   Invalid/nonfinite threshold errors still produce finite non-success JSON.

All numeric geometry/codec/runtime tolerances and input ABI/integrity checks
remain strict. A missing/broken RGB input remains an execution/input error;
only a numeric photometric disagreement becomes nonblocking. Renderer, source
mapping, Depth/K/Pose, RGB decoder, codecs, cache publisher/identity, Cosmos,
Local-TTT, training, configs, scripts and Child are unchanged. The export recipe
excludes the verifier, so valid caches do not require migration/rebuild.

## Author checks — exact clean Pair

Evidence: `docs/collab/codex/evidence/2026-11-04_g2_spatial_policy_author_cpu/`.

| Check | Result |
| --- | --- |
| CPU tests | 121 distinct PASS =83 existing +38 policy; 0fail/error/skip,3.44s |
| Frozen35 under old contract | Expected31 failures/4passes; unchanged definitions preserved in final38 |
| Old assertions | 68/69 identical; only expected synthetic status string changes |
| Spatial hard predicate | AST-identical after removing only the authorized RGB threshold clause |
| Ruff0.12.7/check/format | PASS,11 Python files |
| AST/compile/help/lazy imports | PASS; no model/native imports on help |
| Bounded Gate C command syntax | Two Bash blocks and embedded Python parse PASS |
| Evidence/source binding | 39 hashed text artifacts;13 Git Blob+SHA256 bindings |

Tests cover both RGB diagnostic outcomes, each strict spatial failure with
both photometry outcomes, source/cache corruption, RGB ABI/I/O failure,
offline NOT_EXECUTED, inert visual provenance/no automatic Owner PASS, native
CLI status/exit, old/new report immutability and invalid threshold errors.
Native-kind CLI fixtures are explicitly synthetic boundary doubles. They are
not real RoboCasa or native server evidence. Old107 results and24 OSMesa source
are retained unchanged;24 is not re-run or included in121. No server data,
scripts or images were accessed/transferred; no actual render/GPU executed.

## Requested review and next boundary

Request fresh `APPROVE_CODE` / `REQUEST_CHANGES` / `BLOCKED` for the exact Pair,
minimal acceptance split, explicit report/provenance semantics and author CPU
evidence. This does not claim the new verifier ran on the server or Gate C passed.

Runbook and bounded Gate C design:
`docs/build/PSM-WMA_G2_Spatial_Acceptance_v2_and_GateC_Plan_2026-11-04.md`.
After source/plan review, the execution role must produce new immutable native
spatial-v2 text evidence. This can be the first Gate C report; the prepared
read-only replay of the old six-frame cache is an optional policy-check command,
not a requirement to reopen the already accepted six-frame geometry/visual work.
Do not re-label the old verifier's exit or rewrite its report.

Gate C remains a separately approved3–5 full-episode/distinct-task execution
plan. Actual IDs require server-side mapping inspection and a bounded exact
selection manifest. Full-cache integrity, per-episode sampled geometry/coverage,
documented new RGB/Depth visual review and reuse/storage/time/RSS evidence are
required. Existing f634 visual approval cannot be generalized to new scenes.

STOP after isolated publication/readback for fresh review. No Gate C/N100
execution, V3 merge, color/AA correction, nav_sg/Global PSS, GPU/model/training,
DCP/active-worktree or historical-output changes are authorized by this delivery.
