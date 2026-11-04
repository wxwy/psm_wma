# G2 Stage-1 — Owner visual alignment evidence and acceptance-contract revision

Date: 2026-11-04 (Asia/Shanghai). Project: PSM-WMA V3/G2 Stage-1 RoboCasa365 offline Depth/Pose cache. **Evidence recorded from Owner’s direct inspection** of server-local figures; no image bytes are transferred, and no code or runtime asset was edited by this document.

## Exact subject

- Formal implementation **Root**: `a9ffd313770c5344195f415425124a5075e62b2b`, **Child/Gitlink**: `1069fe78841228cadbbfbe6afbd767eaed6225da`. This document is docs-only: not a new formal implementation.
- Original RoboCasa365 target-atomic **CloseFridge local episode 000000**, Flat V3 **global episode 502**, frames **0/214/428** at 20Hz, cameras `robot0_agentview_left` and `robot0_eye_in_hand`.
- Server-only visual evidence:
  - Original RGB + rendered metric Depth/grayscale/pseudocolor/red edge overlay: `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_G2_rgbd_preview/formal_a9ffd313_visual_RGB_Depth/ALL_6_comparisons_OriginalRGB_Depth.png`.
  - Original RoboCasa RGB vs old G3 renderer RGB vs current renderer RGB and amplified differences: `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_G2_rgbd_preview/formal_a9ffd313_visual_RGB_compare/ALL_6_RGB_compare_Original_OldG3_Current.png`.
- Source Gate B real report: `docs/collab/chatgpt/reviews/2026-11-04_G2_GateB_a9ffd313_1069fe78_Server_Geometry_PASS_RGB_FAIL.md`, whose immutable historical verdict is `PHYSICAL_REPLAY_NOT_ACCEPTED` **under the old photometric hard gate**.

## Owner’s new first-person visual observation (recorded, not attributed to an autonomous image analysis)

The Owner inspected complete images, boundaries/contour relative to entire image, relative positions of local objects, and robot-arm occlusions. Owner reports that all three compared RGB images show **no perceptible structural, contour-placement, object-position, or occlusion differences**; the newly generated Depth edges were previously confirmed to follow source RGB contours of the arm, fridge, table and objects. **Old G3 rendered RGB is noticeably closer to the original dataset RGB. The current rendered RGB has more conspicuous jagged/aliased edges than both. Perceived overall brightness is the same across all three.**

No claim that aliasing is the **unique numerical cause** of the reported MAE is established here; photometric differences may remain unexplained. The prior GPT hypothesis of a global brightness shift was not supported by this owner visual inspection and must not be asserted as a verified root cause.

## Objective corroboration and separate observations

Native real-robot-simulator Gate B r2 under formal `a9ffd313` had:
- Exact source mapping and frame identity dry-run PASS.
- Real native rendering / Depth cache export PASS, with `uint16_mm` quantization <= ~0.0005 m.
- Cache integrity/runtime parity PASS.
- Independent 3D geom/ray comparisons **6/6 PASS**, 128 matched rays per frame-camera, maximum optical-Z errors **0.000880..0.004423 m**, with >=16/<=0.01 m standards unchanged.
- Original-video vs current re-rendered RGB MAE **5/6 FAIL** under the **previous** <=5 criterion; original-vs-old-G3 RGB MAE was ~1.05..2.07, original-vs-current 2.27..12.95.
- RGB vs RGB-D render readback and segmentation-before/after both pixel-identical for each frame in current runtime. No direct evidence that current Depth and original RGB have a frame/geometry offset.

## Acceptance-policy decision for G2 Stage-1

**The target output is original RoboCasa365 RGB (already used by training) + new action/state-conditioned replay Depth/K/Pose. The newly rendered RGB is a reconstruction/diagnostic channel only, and is NOT a training substitute.**

For the scope of G2 Stage-1 **spatial RGB-D alignment**, interpret evidence as:

1. **`DEPTH_GEOMETRY_PASS`** — independent scene ray test pass with frozen min samples/tolerances and valid source/pose/frame mapping.
2. **`OWNER_VISUAL_ALIGNMENT_PASS`** — Owner explicitly accepts original RGB vs new Depth edge/occlusion alignment for these six images.
3. **`RENDER_RGB_PHOTOMETRIC_DIAGNOSTIC_FAIL`** — MAE<=5 fails for five of six, retained as a **diagnostic** with complete numbers and no suppression/threshold alteration.
4. This is **revised spatial Stage-1 Gate B evidence sufficient to proceed to a narrowly bounded Gate C design**, but the previous production verifier’s `PHYSICAL_REPLAY_NOT_ACCEPTED` remains the factual result of its **old contract**. Do NOT retroactively rewrite the prior report or claim that the original verifier returned `PHYSICAL_REPLAY_PASS`.

**Follow-up implementation requirement (Codex; minimal change, separate reviewed formal pair)**:
- Decouple the combined `geometry_gate` / `PHYSICAL_REPLAY_PASS` status from source-video vs re-render RGB MAE in the verifier.
- Preserve independent geometry, alignment, full cache/fresh consistency, original-video metrics, available coverage, and unchanged numerical geometric tolerances.
- Provide explicit separate `spatial_alignment_gate`, `photometric_diagnostic`, and `owner_visual_review` evidence status/provenance; do not automatically claim owner inspection from a source-code checkbox or synthetic tests.
- New status must unambiguously indicate **new spatial acceptance policy** and avoid mislabeling previous legacy physical PASS/FAIL.
- Re-run focused CPU/static Code Gate and then test updated acceptance logic with **new immutable text report output**, not overwriting any old evidence. Gate C requires independent multi-episode geometry, valid RGB/Depth contour/camera alignment (owner or documented independent review), and adequate coverage; a six-frame success alone is not general proof.
- No change to generated Depth, frame index policy, source videos, reconstruction brightness/gamma, antialiasing workaround, Cosmos training, Global PSS, nav_sg, or full export is justified by this decision.

## Next bounded action

Prepare and review the **minimal acceptance-contract change** and a plan for **3–5 full episodes from different task classes** after explicit approval. Do not start N=100 or merge V3 based solely on this six-frame owner review. Retain server images and arrays exclusively on server. The V3 main branch is not updated by this document.
