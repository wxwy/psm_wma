# G2 Stage-1 RoboCasa365 RGB-D/Pose — implementation and validation runbook r1

Date: 2026-11-04 (Asia/Shanghai). Scope: Root-only offline data preparation on
V3; no nav_sg, scene graph, BEV/PSS, model/recipe/Local-TTT/training modifications.
Status: implementation candidate; author CPU evidence is separate from real-data
acceptance. Formal source SHA is assigned in the subsequent author handoff.

## Existing contracts and reuse

- DS confirmed the13-column episode mapping:9,126 episodes/18 classes/2,231,347
  frames. These are **user-forwarded DS observations**, not data read in cloud.
- Existing `tools/g0/build_cosmos_robocasa_latent_dataset.py` owns selection
  scoring and manifests; Stage-1 consumes its accepted IDs without resampling.
  N100 actual membership and whether N means per-task have not been confirmed.
- Existing g0 `robocasa_work_queue.atomic_write_json` is reused for JSON atomic
  replacement, with file/directory fsync in this tool. No new task scheduler.
- Actual native replay delegates to
  `robocasa.scripts.dataset_scripts.playback_dataset_hdf5.reset_to`, as DS used.
  Model/XML and ep_meta are supplied once per fresh episode environment, then
  each mapped state is restored individually. No action replay. Every episode
  environment is closed before its output is committed; no environment reuse
  across episodes is attempted in r1.
- Official robosuite camera helpers provide K, metric buffer conversion and CV
  pose. Raw MuJoCo camera position/rotation independently provide GL pose.
  Reference reading used RoboCasa6f90063 and robosuite824ac14. The tool records
  the actual installed versions/helper hashes; physical/runtime parity is DS's
  responsibility, not inferred from a package version string alone.

See [input/output schema](../../tools/g2/rgbd_pose_schema.md) and the Owner
clarifications under `docs/collab/codex/requests/`.

## Code map

| File | Responsibility |
| --- | --- |
| tools/g2/export_robocasa_rgbd_pose.py | CLI, exact membership, dry-run, nonvisual binding, per-episode execution |
| tools/g2/verify_robocasa_rgbd_pose.py | Offline integrity and optional native replay numerical report |
| tools/g2/rgbd_pose/source.py | Existing mapping/manifest reader, original/Flat source identity |
| tools/g2/rgbd_pose/geometry.py | Explicit GL/CV transforms, Z-depth codec, numeric metrics |
| tools/g2/rgbd_pose/replay.py | Official replay/render adapter; no native imports on dry-run |
| tools/g2/rgbd_pose/cache.py | Bounded chunks, atomic episode commit, strict reuse/failure isolation |
| tools/g2/test_rgbd_pose_export.py | Synthetic Gate A and an actual CPU mj_ray analytic scene |

## Gate A — author CPU/static

Use CPU Python with numpy, pyarrow, scipy, pytest and MuJoCo3.3.1; no RoboCasa
installation/assets are required for CPU tests. MuJoCo is used only for ray
intersection against a tiny synthetic tilted plane, **without a GL context**.
Native replay is covered through explicit external-boundary doubles, not claimed
as a real environment restore. Keep caches and pytest basetemp outside sources:

```bash
export CUDA_VISIBLE_DEVICES='' MUJOCO_GL=disable PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH="$CODE_ROOT${CPU_EXTRA_DIR:+:$CPU_EXTRA_DIR}"
export HF_HOME="$EVIDENCE/cache/hf" MPLCONFIGDIR="$EVIDENCE/cache/mpl"
export XDG_CACHE_HOME="$EVIDENCE/cache/xdg" RUFF_CACHE_DIR="$EVIDENCE/cache/ruff"
cd "$CODE_ROOT"
python -m pytest --noconftest -c /dev/null -q -p no:cacheprovider \
  tools/g2/test_rgbd_pose_export.py \
  --basetemp "$EVIDENCE/pytest_tmp" --junitxml "$EVIDENCE/junit.xml"
ruff check tools/g2
ruff format --check tools/g2
```

Ruff version0.12.7. Expected: no failed/error/skipped tests, syntax/import/static
PASS, exact source binding, no Child/recipe/old corpus changes. The final frozen
JUnit is authoritative for author test count; development results are not a
server Gate. No old EvalV2122/379 or training GPU experiment is rerun here.

## Server source sync — before any execution

Owner permits server-side validation after repository publication. First **on the
server** read:

```bash
cat /mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/.codex/skills/github-fetch-proxy/SKILL.md
```

Follow that skill's actual proxy/fetch route, not an invented SSH/proxy command.
Fetch the candidate into a **new isolated checkout** of the Formal Root from the
author handoff, Child/Gitlink1069fe78841228cadbbfbe6afbd767eaed6225da. Verify full
Root/Child/Gitlink and clean state before and after tests. No reset/clean/force,
no active shared training/evaluation checkout updates, no vendor-source changes.
Server skill contents and private files must not be downloaded/copied into cloud.
Code flows from local author -> Git -> server. Temporary validation code may be
created on the server; any resulting implementation fix must first be made and
committed in the repository, then pulled there again.

Use DS's verified simulator interpreter (`SIM_PYTHON`); historical `.venv` paths
in the environment map are clues, not proof of current imports/version. Log
actual interpreter, versions, source origins and helper hashes. Model/DCP is not
an input to this tool.

## Gate B — one episode / three frames / two cameras

Run after source review and server CPU checks. The OSMesa route below touches no
GPU; if its libraries/assets are unavailable report BLOCKED_ENV. Do not silently
switch to EGL or inspect/manage other GPU tasks. A separately selected EGL setup
can be validated by DS/Owner later using the same export contract.

Choose a new `RUN_TAG` and external evidence/cache directory. Paths below are the
Owner-provided server inputs, not hardcoded program defaults:

```bash
set -euo pipefail
RAW_ROOT=/mnt/data1/data_v2_0617/robocasa365_official/v1.0/target/atomic
FLAT_ROOT=/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic
RUN_TAG=gate_b_closefridge_ep000000_$(date -u +%Y%m%dT%H%M%SZ)
CACHE=/mnt/data1/data_v2_0617/g2_rgbd_pose/$RUN_TAG
EVIDENCE=/tmp/g2_rgbd_pose_evidence_$RUN_TAG
mkdir -p "$EVIDENCE"
export PYTHONPATH="$CODE_ROOT" CUDA_VISIBLE_DEVICES=''
export MUJOCO_GL=osmesa PYOPENGL_PLATFORM=osmesa PYTHONDONTWRITEBYTECODE=1
export HF_HOME="$EVIDENCE/cache/hf" MPLCONFIGDIR="$EVIDENCE/cache/mpl"
export XDG_CACHE_HOME="$EVIDENCE/cache/xdg" NUMBA_CACHE_DIR="$EVIDENCE/cache/numba"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$CODE_ROOT"

"$SIM_PYTHON" -m tools.g2.export_robocasa_rgbd_pose \
  --raw-root "$RAW_ROOT" --flat-root "$FLAT_ROOT" --output-root "$CACHE" \
  --task-class CloseFridge --local-episode 0 --frames 0,214,428 \
  --cameras robot0_agentview_left,robot0_eye_in_hand \
  --state-index-policy frame_index --depth-format uint16_mm --chunk-frames 32 \
  --dry-run > "$EVIDENCE/plan.json"
```

Stop if dry-run fails; do not infer global episode0 from local episode0. The plan
reports the actual mapped global ID. If raw binding is ambiguous, DS supplies
`--source-dataset` from the existing G3 binding; never pick the first directory.
Then execute the **same command without `--dry-run`** (retain its stdout and exit
code). Find the single committed episode directory using the exact global ID
from the plan. Do not assume it is000000 in Flat V3.

```bash
"$SIM_PYTHON" -m tools.g2.export_robocasa_rgbd_pose \
  --raw-root "$RAW_ROOT" --flat-root "$FLAT_ROOT" --output-root "$CACHE" \
  --task-class CloseFridge --local-episode 0 --frames 0,214,428 \
  --cameras robot0_agentview_left,robot0_eye_in_hand \
  --state-index-policy frame_index --depth-format uint16_mm --chunk-frames 32 \
  > "$EVIDENCE/export.log" 2>&1
GLOBAL_EP=$("$SIM_PYTHON" -c 'import json,sys; p=json.load(open(sys.argv[1])); assert p["selected_episode_count"]==1 and not p["failed_episode_count"]; print(p["episodes"][0]["episode"]["global_episode_index"])' "$EVIDENCE/plan.json")
EXACT_COMMITTED_EPISODE_DIR="$CACHE/tasks/CloseFridge/episodes/episode_$(printf '%06d' "$GLOBAL_EP")"
"$SIM_PYTHON" -m tools.g2.verify_robocasa_rgbd_pose \
  --episode-dir "$EXACT_COMMITTED_EPISODE_DIR" \
  --raw-root "$RAW_ROOT" --flat-root "$FLAT_ROOT" \
  --state-index-policy frame_index --frames 0,214,428 --replay \
  --geometry-atol-m 0.01 --min-ray-samples 16 --rgb-mae-max 5 \
  --report "$EVIDENCE/physical_report.json"
```

Use a new report path each time. Requirements:

- Exact raw/Flat row counts, all nonvisual states equal, state-index declaration
  retained; actual simulator restored state error <=1e-8, no time-based shift.
- RGB MAE<=5 by default; report PSNR and SSIM per camera/frame. SSIM definition
  is uniform7x7, sample covariance, RGB mean on valid crop; exact-match PSNR is
  JSON null plus an explicit exact-match flag, not Infinity.
- Valid depth fraction/min/median/max and quantization error reported. Both K and
  GL/CV proper poses validate; fresh/cached matrices max difference<=1e-5.
- Cached/fresh valid masks match and depth error stays within recorded codec
  bound (minimum comparison allowance1e-5m for float serialization).
- Report actual wrist pose change. Backprojection uses downward CV v or sign-
  corrected GL y; roundtrip pixel error<=1e-7. This alone is not independent
  geometry evidence.
- Independent `mj_ray`: unit-ray distance converted back to Z, actual renderer's
  geomgroup filter, static geoms included, no body excluded. Compare only ray
  hits whose geom ID matches rendered segmentation. At least16 matches per
  camera/frame and maximum optical-Z error<=0.01m. Unknown filters, insufficient
  matches or incompatible visibility semantics yield INCONCLUSIVE/nonzero,
  **never** evidence that depth is wrong or a geometry PASS.
- Record actual runtime/helper hashes, CLI exit0, cache integrity and report
  `PHYSICAL_REPLAY_PASS`. A `SYNTHETIC_REPLAY_VERIFIED` or offline-only status is
  not Gate B. No PNG/video output is needed and original RGB is never re-encoded.

These explicit numeric thresholds are part of this candidate review contract;
do not tune them after seeing a failure to obtain PASS. Diagnose/filter semantics
and retain evidence. DS compares with its existing G3 scripts; it does not need to
repeat the large feasibility inventory or transfer those scripts/data to Codex.

## Gate C — three to five complete episodes, then membership freeze

After B passes, DS/Owner choose3–5 exact IDs from different tasks. Supply an
external verified selection manifest with the current mapping SHA. Use a new
cache namespace and omit `--frames`; verify each entire cache offline, repeat the
same export and confirm SKIPPED_VERIFIED without opening environments. Record
full frame counts, no offsets, per-camera pose separation, unchanged file hashes,
time/throughput, actual compressed bytes, raw-array bytes and measured ratio.
Recheck a small deterministic subset physically rather than assuming integrity
checks prove geometry. Original RGB/Depth/cache remain on the server.

Default disk reserve is1GiB, configurable `--min-free-bytes`; checked before
environment creation and before each chunk. This is an operational guard, not a
promise against unrelated concurrent disk writers. All existing source/evidence
is preserved on ENOSPC/failure. Memory scales with cameras × chunk_frames × H×W,
not the entire corpus. Chunk count is bounded; measure actual RSS at Gate C.

**No N100/full export before B and C close and the actual training membership is
confirmed.** Do not substitute `--episode-limit 100 --episode-seed 42`, and do not
interpret N100 as a known total episode count. Capacity estimates use the exact
selected frame count/camera shapes; compression benefit is measured, not assumed.

## Failure/recovery and evidence boundaries

- Before atomic rename, any incomplete episode stays in .staging/.failed; it
  cannot be skipped as complete. OS advisory locks release on process death.
- Valid completed episodes are immutable and skipped after full structural,
  checksum/array/frame-reference verification. Config drift requires a new
  namespace. An expanded same-source selection can reuse matching completed eps.
- Corrupt existing final directories are rejected and left untouched. To retry,
  preserve/move that exact damaged output into a new diagnostic directory first;
  do not overwrite evidence or alter raw inputs. Stale .staging may be retained
  while a fresh episode attempt is made. Never clean another worker's staging.
- Failures retain diagnostics and other episodes can finish, but the final CLI
  exit is nonzero. Encoder/model/DCP/Local-TTT paths are not involved.
- Only code/text statistics/hashes/JUnit may be sent across sessions. Server RGB,
  depth, videos, caches and reversible encodings stay there. Author Evidence
  contains no such server data; all CPU fixtures are newly synthetic.
