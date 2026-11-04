# G2 Stage-1 RGB-D/Pose — author implementation handoff

Date: 2026-11-04 (Asia/Shanghai). Request: fresh **Code Gate**, not real-data
acceptance. Author Gate A PASS; server Gate B/C and exact N100 membership pending.

| Identity | Exact SHA |
| --- | --- |
| **Final Formal Root** | `b67bc4ca9a2afb1ff26fac0846f8ee7042a589ab` |
| **Child / Gitlink, unchanged** | `1069fe78841228cadbbfbe6afbd767eaed6225da` |
| Implementation base, latest V3 at start | `083b36ac27ad43b6f5127d9a58aed4fac02eaaa7` |
| Preliminary feature commit, superseded | `3d163e91d42802efe487deb89286637cc91ed74c` |

Isolated Root branch: `v3-g2-rgbd-pose-stage1-20261104`. **Review the cumulative
base083b36ac → finalb67bc4ca change and the final tree**, not just the final
four-file follow-up commit. The full new feature spans two implementation commits.
Later Evidence/Inbox HEADs do not replace the final Formal Root.

## Implementation and boundaries

Root-only17-file cumulative change: nine new Python source/test files in
`tools/g2/`, tool README/schema, Stage-1 runbook, three Owner-request/provenance
documents and SESSION/TODO. Child, scripts/configs, g0/g3 tools, vendor, training,
model/Local-TTT algorithms and old Evidence remain unchanged. No V3 promotion.

- Real13-column **episode-level** Flat mapping with half-open row intervals,
  explicit global/local episode/frame/state identity and per-episode raw/Flat
  nonvisual state/index checks. No timestamp-based state shift.
- Existing g0 accepted cache membership or an externally verified global-ID
  manifest; source/mapping identity is mandatory. No copied sampler, seed42 or
  N100 IDs. N100 actual members and whether N means per-task remain unconfirmed.
- Official `playback_dataset_hdf5.reset_to`, fresh environment per episode,
  complete model/XML + ep_meta restoration, then state-only restoration per frame.
  Original RGB is referenced; only verification decodes a few frames locally.
- Explicit upright pixel centers, metric optical Z-depth, independent GL/CV
  camera-to-world poses and per-camera/per-frame K. No double axis correction.
- Configurable lossless NPZ chunks; uint16_mm candidate or explicit float32_m,
  mask/overflow/quantization checks, no saturation or automatic format fallback.
- Episode-level OS lock, staged/fsynced files, final COMPLETE marker and atomic
  directory rename. Verified completed episodes skip without native construction;
  corrupt final outputs are rejected/preserved, failed new attempts isolated.
  Source changes, low disk budget and cleanup/write failures cannot publish a
  partial episode. Memory scales with chunk dimensions, not whole RGB-D corpus.

## Final Gate A evidence

**83 distinct tests, 0 failure/error/skip**,1.66 seconds, on the clean exact final
Pair; Root/Child/source bytes unchanged before/after. Python3.12.14,
pytest9.0.2, NumPy2.2.6, PyArrow26.0.0, scipy1.15.3. MuJoCo3.3.1 and its lightweight
dependencies installed only into an external temporary target, not shared envs.
Ruff0.12.7 check/format PASS; nine-file AST/compile PASS; both CLI help and lazy
import probes PASS (no Torch/Cosmos/MuJoCo/RoboCasa/robosuite/LeRobot import on
ordinary CLI import/help). No native robot environment, renderer or GPU executed.

Meaningful CPU checks cover real production paths: mapping/selection/source
refusal, codec/quantization/ranges/invalid mask, per-camera poses, atomic commit
and interruption/fault cleanup, strict corruption/Unicode/truncated frame index,
idempotent skip/config drift, CLI dry-run/export/failure isolation and text report.

Actual CPU `mj_ray` on an independently constructed tilted plane:64 matching
static-geom hits, optical-Z error `2.220446049250313e-16m`; erroneous depth flip
and ray-range encoding fail, unknown visibility filtering is INCONCLUSIVE.
This is synthetic physics/coordinate evidence, **not a real Depth render**.

Preliminary3d/82 evidence is preserved and marked superseded. Final inspection
reproduced false stationary-camera motion (`0.00048828125rad`) from float32
R.T@R. Same frozen production-path regression RED1 on3d, GREEN1 after float64
relative solve/nearest proper rotation; frozen function AST/assertions unchanged.
Stored depth/poses and acceptance thresholds were not relaxed. Final83 is not
the sum of historical development suite counts.

Evidence: `docs/collab/codex/evidence/2026-11-04_g2_rgbd_stage1_author_gate_a/`.
Main `gate.json` and `final83/junit.xml` bind this final Pair. Manifest hashes114
text artifacts,12 source/config bindings, exact cumulative/protected-tree scope,
minimal source diff, logs/commands/versions, synthetic ray diagnostics and the
separately labelled preliminary82 package. No recordings, RGB/depth arrays,
video, NPZ/NPY, Parquet or other reversible server payload is in this Evidence.

## Usage, schema and server validation

- Entry points and conventions: [tool README](../../../../tools/g2/README.md),
  [input/output schema](../../../../tools/g2/rgbd_pose_schema.md).
- [Complete runbook and Gate B/C commands](../../../build/PSM-WMA_G2_Stage1_RGBD_Pose_Cache_r1_2026-11-04.md).
- Single episode: CloseFridge/local0, frames0,214,428; cameras left + eye_in_hand;
  mapping resolves the actual global ID. `--state-index-policy frame_index` must
  be explicit. Dry-run first, then same export without --dry-run and native
  verifier, text-only report. No N100 command substitutes an unverified seed/list.
- The runbook provides an OSMesa route with CUDA visibility disabled, new output
  namespace, cache/report paths, exact thresholds and nonzero failure criteria.
  Geometry/ray visibility INCONCLUSIVE is not PASS. Raw RGB versus rerendered
  MAE/PSNR/SSIM, Depth ranges/validity, matrices, wrist motion, quantization,
  corrected backprojection, source identity and actual timing are all reported.

Owner has permitted later server-side fetch/testing. First read the **server's**
`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/.codex/skills/github-fetch-proxy/SKILL.md`,
then fetch this exact isolated candidate without touching active worktrees.
Code maintenance flows local -> Git -> server; no server files/data may be copied
to the cloud author. Temporary server validation code is allowed, final fixes
must first be committed locally. Actual server runtime/interpreter paths must be
verified there rather than inferred from the historical environment map.

**Server execution was not performed**: current tools expose no Remote Desktop
Commander/SSH/remote execution capability. The server skill was not read, no
server checkout was changed and no server file was transferred. This is a tool
availability limitation, not a request for Owner to authorize the same step again.
Any future author-executed server test must be labelled author server evidence,
not DS independent execution.

## Remaining risk / next decision

Gate B must establish actual source-state/RGB alignment, metadata/version/assets
compatibility and renderer/ray visibility semantics. Gate C then validates3–5
complete episodes, actual RSS/time/storage/compression and repeatability. The
uint16 format/range and resource budget remain real-data measurements, not claims
from a constant synthetic fixture. If range is insufficient, use an explicitly
reviewed float32 namespace; don't clip. Preserve original/raw and failed evidence.
Freeze true training membership before any N100 export. No nav_sg, G2 training,
existing train/DCP/job changes, large export or automatic V3 merge is authorized
by this author Gate A. Submit for GPT Code review, then stop.
