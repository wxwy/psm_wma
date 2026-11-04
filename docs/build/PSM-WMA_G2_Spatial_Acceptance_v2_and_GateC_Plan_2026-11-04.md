# G2 Stage-1 spatial-v2 acceptance and bounded Gate C plan

Date: 2026-11-04 (Asia/Shanghai). Authority: Owner decision
`f63454610ec2b95617c670444875339034c3c1c7`, review
`2026-11-04_G2_GateB_Owner_Visual_Alignment_Acceptance_and_Revision.md`.
The new Formal Root is assigned in the author evidence/handoff; Child/Gitlink
stays `1069fe78841228cadbbfbe6afbd767eaed6225da`.

## Scope and evidence preserved

Original dataset RGB remains the training/input reference. Re-rendered RGB is
diagnostic, never a replacement. Only the verifier's acceptance/reporting changes;
source mapping, state indices, RGB decoder, rendering, Depth, K/Pose, codecs,
cache identity/publisher and training are unchanged. The export recipe does not
include the verifier, so this change does not require rebuilding valid caches.

Keep old `PHYSICAL_REPLAY_NOT_ACCEPTED` reports, caches and photometric metrics
immutable. Owner has accepted original-RGB/Depth contours and occlusions for
the six a9ffd313 images, not all future episodes. The correction to earlier
visual interpretation is visible aliasing, not an established global brightness
shift; no unique cause of numerical RGB error has been proved or repaired.
RGB provenance research is diagnostic-only, no longer a spatial prerequisite.

## New report contract

`acceptance_policy=g2_stage1_spatial_v2` and the exact Owner authority URL are
present in every new success/error/offline report.

| Field | Meaning |
| --- | --- |
| spatial_alignment_gate | Automatic source/cache/runtime/state/Depth/K/Pose/reprojection/ray checks only |
| spatial_alignment_scope | AUTOMATED_CHECKS_ONLY_VISUAL_REVIEW_EXTERNAL |
| photometric_diagnostic | Separate PASS/FAIL/NOT_EXECUTED, blocking=false, unchanged MAE5 and checked/failed counts |
| owner_visual_review | NOT_PROVIDED or EXTERNAL_RECORD_REFERENCED; provenance_reference and verified_by_tool=false |
| geometry_gate | Versioned compatibility alias of the automatic spatial gate; no longer includes RGB MAE |

Every camera/frame keeps full MAE/PSNR/SSIM, fresh/cached Depth and masks,
matrices, reprojected pixel error, ray counts/coverage/max error and diagnostics.
Original geometric limits remain0.01m, at least16 matches, matrix1e-5,
reprojection1e-7, codec-bound Depth parity and exact source/state binding.
RGB input absence, corrupt sources, incompatible dimensions or malformed cache
remain errors; only a **numerical photometric mismatch** ceases to block.

Native automatic success is `SPATIAL_REPLAY_CHECKS_PASS`, not legacy
`PHYSICAL_REPLAY_PASS`. Failure is `SPATIAL_REPLAY_CHECKS_NOT_ACCEPTED` or
`VERIFICATION_FAILED`; synthetic success is explicitly
`SYNTHETIC_SPATIAL_REPLAY_CHECKS_PASS`. Offline integrity remains NOT_EXECUTED
for spatial/photometric checks. CLI exit0 means offline validity or completed
native automatic spatial checks, **not human approval or overall Gate C closure**.

`--owner-visual-review-ref` only records a URL/path/citation. The tool does not
read/authenticate it, validate its scope, or convert it to visual PASS. A flag,
file reference or synthetic test cannot assert Owner inspection. The reviewer
must confirm the external record actually covers the examined frames/cameras.
The f634 Owner record already covers the original six images and need not be
re-reviewed merely to change report labels; it cannot authorize new Gate C
images. No code checkbox or automatic inherited visual acceptance exists.

## Focused author checks

Use CPU Python with existing numpy/pyarrow/scipy/pytest/MuJoCo dependencies,
empty CUDA devices and `MUJOCO_GL=disable`. Run the existing83 tests plus new
policy tests, with private HF/MPL/XDG/pytest paths. The old status-string assert
changes deliberately; all other old assertions remain identical. Freeze the
new35 contract tests before old/new execution; preserve expected old RED and
new GREEN. Additional invalid-threshold tests ensure finite failure JSON.
Ruff0.12.7/check/format, AST/compile and help/lazy-import checks apply. The24
software-render tests and replay/geometry source are unchanged, not re-run or
added to this round's count.

## Updated real acceptance report after fresh Code Gate

This is a prepared command, **not an execution claim or independent permission**.
Use an isolated clean checkout of the newly reviewed Formal Pair. Read the
server GitHub fetch skill first, preserve active worktrees and reuse only the
already verified CPU OSMesa environment, including its process-scoped library
search path. No EGL/GPU fallback or new dependency installation is implied.
Set CODE_ROOT/SIM_PYTHON and a fresh external NEW_EVIDENCE directory. Use
`CUDA_VISIBLE_DEVICES=''`, `MUJOCO_GL=osmesa`, `PYOPENGL_PLATFORM=osmesa`,
`LIBGL_ALWAYS_SOFTWARE=1`, private caches and one CPU thread per numeric library.

```bash
cd "$CODE_ROOT"
RAW_ROOT=/mnt/data1/data_v2_0617/robocasa365_official/v1.0/target/atomic
FLAT_ROOT=/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic
OLD_EP=/mnt/data1/data_v2_0617/g2_rgbd_pose/gpt_gate_b_r2_20261104_0630/tasks/CloseFridge/episodes/episode_000502
OWNER_REF=https://github.com/wxwy/psm_wma/blob/f63454610ec2b95617c670444875339034c3c1c7/docs/collab/chatgpt/reviews/2026-11-04_G2_GateB_Owner_Visual_Alignment_Acceptance_and_Revision.md
"$SIM_PYTHON" -m tools.g2.verify_robocasa_rgbd_pose \
  --episode-dir "$OLD_EP" --raw-root "$RAW_ROOT" --flat-root "$FLAT_ROOT" \
  --state-index-policy frame_index --frames 0,214,428 --replay \
  --geometry-atol-m 0.01 --min-ray-samples 16 --rgb-mae-max 5 \
  --owner-visual-review-ref "$OWNER_REF" \
  --report "$NEW_EVIDENCE/spatial_v2_report.json"
```

Read existing cache only; do not export into or mutate it. Expected: automatic
spatial PASS, original RGB diagnostics retained even when FAIL, external Owner
record referenced without automatic attestation, new immutable text report and
unchanged old files. Do not say the old verifier exited0. Any source/runtime/
geometry error remains nonzero and stops progression.

## Gate C design — review before execution

Select3–5 complete episodes from **distinct underlying task classes**, explicitly
resolving their actual Flat/global/local IDs from the existing mapping. CloseFridge
may be one; other names/IDs must be real inspected entries, not copied from
synthetic tests. Freeze a small external selection manifest with exact mapping
SHA using the existing `psm_wma_rgbd_episode_selection_v1` schema. No re-sampler,
N100/default42 membership assumption or historical cache migration.

Use a new GATE_C_CACHE namespace. Omit `--frames` to export each complete
episode, retain both native camera sizes and `uint16_mm/chunk32` unless a
separately reviewed explicit alternative is needed. Prepared dry-run:

```bash
"$SIM_PYTHON" -m tools.g2.export_robocasa_rgbd_pose \
  --raw-root "$RAW_ROOT" --flat-root "$FLAT_ROOT" \
  --output-root "$GATE_C_CACHE" --selection-manifest "$GATE_C_SELECTION" \
  --cameras robot0_agentview_left,robot0_eye_in_hand \
  --state-index-policy frame_index --depth-format uint16_mm --chunk-frames 32 \
  --dry-run > "$NEW_EVIDENCE/gate_c_plan.json"
"$SIM_PYTHON" -c 'import json,sys; p=json.load(open(sys.argv[1])); r=p["episodes"]; assert p["failed_episode_count"]==0; assert 3<=p["selected_episode_count"]==len(r)<=5; assert len({x["episode"]["task_class"] for x in r})==len(r); assert all(x["frame_count"]==x["episode"]["length"] for x in r); print("BOUNDED_FULL_EPISODE_PLAN_PASS")' "$NEW_EVIDENCE/gate_c_plan.json"
```

After the separately approved plan passes, run the same export without
`--dry-run`; save log/exit and its `_runs` summary. For each committed episode:

1. Offline-verify the **whole** cache and frame continuity. Record all-frame
   source/state mapping, validity/range/quantization and per-frame camera poses.
2. Physically check deterministic first/middle/last frames in **each** episode,
   both cameras, with the new verifier and unchanged geometric limits. Report
   full eligible coverage, matching counts, max errors and runtime consistency.
   This is sampled physical evidence, not full-map/every-frame correctness.
3. Require Owner or documented independent visual review of original RGB/Depth
   contours, object placement and occlusions for the new sampled scenes. Keep
   review identity/scope/provenance separate from automatic checks. Numerical
   re-rendered RGB metrics remain diagnostic and must still be present.
4. Repeat the exact export: completed episodes must be SKIPPED_VERIFIED with
   unchanged hashes and no replay/environment creation. Preserve new run records.
   Use existing failure-recovery rules; never corrupt real committed evidence
   to inject a failure. Record any natural failure/retry independently.
5. Measure wall time, frames/s, peak RSS, free space, raw/stored bytes and actual
   compression. Keep chunk-bounded memory and disk reserve; no history cleanup.

Gate C closes only after the bounded independent evidence is accepted. No N100
export, V3 merge, Global PSS/nav_sg, training/DCP or GPU execution is authorized
by this implementation or this plan. Server images/Depth/NPZ/video/probes stay
on the server; share only non-sensitive text summaries/hashes/verdicts.
