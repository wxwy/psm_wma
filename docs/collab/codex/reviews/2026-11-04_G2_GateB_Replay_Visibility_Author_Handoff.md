# G2 Gate B replay visibility — fresh incremental Code Gate request

- Formal Root: `a9ffd313770c5344195f415425124a5075e62b2b`.
- Child/Gitlink: `1069fe78841228cadbbfbe6afbd767eaed6225da`, unchanged.
- Candidate: `v3-g2-gateb-replay-fix-20261104`.
- Direct parent: `992cfc2adb3150c573d19206e176bd8a52574949`; earlier approved
  implementation: `b67bc4ca9a2afb1ff26fac0846f8ee7042a589ab`.
- New handoff/evidence commits are bookkeeping, not new Formal Root values.

## What is fixed and what remains unknown

The old independent-ray checker assumed matching geom IDs meant equivalent
visible surfaces. Native CPU OSMesa experiments reproduce false errors of
0.85m for transparency/MSAA and 0.30m for inward meshes. The normal depth pass,
ID segmentation and native double-sided ray casting have different semantics.
These are code-reachable validation defects, not proof of the real six-frame
failure's unique root cause.

`replay.py` now uses explicit opaque scene identity and fresh-render MSAA
eligibility, near-plane ray starts and an independent compiled-triangle
front-face intersection for culled meshes. Eligibility never reads cached depth
values or measured ray errors; all accepted outliers remain FAIL. Same-ID
interior/plane-consistency and local variation bound account for MSAA edge and
subpixel ambiguity. Cull-off/non-mesh native distances remain in use. Unknown
visibility options and insufficient samples remain INCONCLUSIVE. This changed
visibility protocol, including the small Möller–Trumbore path, is explicitly
submitted for fresh review, not assumed approved under the old code verdict.

**RGB cause remains unresolved.** Official source and synthetic rendering do
not support changing `camera_depths`, controllers or metadata as a guessed fix.
No production RGB kwargs/decoder changes were made. New per-camera scalar RGB
mode/segmentation-cycle/context/material fingerprints let the server compare
the old G3 and current rendering without transmitting their scripts or images.
The existing original-video MAE gate remains active and unchanged.

## Exact source and author evidence

Only one production file changes: `tools/g2/rgbd_pose/replay.py`. A dedicated
software-render test module is added. The old analytic fixture gains explicit
scene/fresh-render metadata; its **69 assertion ASTs are identical**. Root
implementation commit changes six files including runbook and SESSION/TODO.
Child and protected scripts/configs/third_party trees match the parent exactly.
Source mapping, codec, cache, verifier, training, Local-TTT and numeric thresholds
are unchanged. Existing code approvals, old server FAIL and prior evidence stay.

Evidence: `docs/collab/codex/evidence/2026-11-04_g2_gateb_replay_author_cpu/`.

| Check | Author result |
| --- | --- |
| Clean exact-Pair legacy CPU | 83 distinct PASS, 2.07s |
| Clean exact-Pair native CPU OSMesa | 24 distinct PASS, 5.43s |
| Combined distinct tests | 107; 0 failures/errors/skips |
| Frozen first20 on old source | Expected RED9/20; 11 passed |
| Same frozen20 on corrected source | GREEN20; included in final24, not added again |
| Ruff0.12.7 check/format | PASS, ten Python files |
| AST/compile, help/lazy imports | PASS; no native/model imports on CLI import |
| Source and artifact bindings | 11 Git Blob/SHA256 bindings; 61 text artifacts |

Failed first development correction (3 failures) is preserved and clearly
superseded. The MSAA footprint correction closed those without changing the
frozen test definitions. A bad eligible ray still fails, and wrong cached depth
or pose, transparency-only coverage and unsupported flags cannot manufacture
PASS. Final CPU renderer is Mesa llvmpipe/LLVM19.1.7 with MuJoCo3.3.1, not GPU.
Tiny synthetic ray-check wall times are approximately0.13–0.20s; this does not
establish performance on large RoboCasa meshes.

## Requested verdict and next boundary

Request `APPROVE_CODE` / `REQUEST_CHANGES` / `BLOCKED` for this exact Pair,
narrow visibility correction, diagnostics and CPU evidence. Review the changed
sampling/front-face protocol explicitly. This is author evidence, not DS or GPT
independent execution, physical acceptance or evidence that real RGB is fixed.

Gate B remains **FAIL / PHYSICAL_REPLAY_NOT_ACCEPTED**. After code approval,
use a separately accepted new output namespace and the existing unchanged
CloseFridge local0/global502, frames0/214/428, left+wrist contract. Server-side
diagnostics must establish actual original RGB agreement, fresh depth/K/Pose,
adequate ray coverage and geometry against the same thresholds. If RGB remains
over5 or geometry is insufficient, continue reporting FAIL/INCONCLUSIVE.

No server data/scripts/cache were transferred, no server rerun performed, no
GPU/RoboCasa/model loaded, no historical cache/report edited, no Gate C/N100,
nav_sg, training/DCP/active-worktree changes or V3 promotion. STOP after isolated
publication/readback for fresh GPT review. Runbook:
`docs/build/PSM-WMA_G2_GateB_Replay_Visibility_Followup_2026-11-04.md`.
