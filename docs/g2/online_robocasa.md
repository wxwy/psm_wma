# G2 R1 Online RoboCasa candidate

The opt-in EvalV2 Phase B profile uses the current episode's MuJoCo model and
FULLPHYSICS data with mocap pose components. A private MjData copy goes through the pinned nav_sg geometry
extractor and a private ROS1 worker. Room, Wall, Floor, Object, Island and
association rules come from the native snapshot. At frame zero the Actor
binds official task roles and builds CAP2 from that snapshot. Subsequent
decisions use the current 20 Hz PandaOmron State15, current Left+Wrist
composite and the existing committed Local frontier. CAP2 stays static for
the episode. The worker publishes frame 0 and then every 20 completed
simulation steps. Every snapshot identifies its live state and native build.
An unchanged occupancy raster skips native grid recomputation. Source
objects still carry their current geometry.

The Actor uses existing canonical Raw15→Env12 execution and persists Local
evidence following a successful step. Legacy EvalV2 continues to use the
default profile. The new server profile requires the published model shards,
canonical config, run recipe, metadata SHA256 and matching tokenizer. It
uses existing Model-D transactions and Omni forward with the R1 conditions.

## Shared offline and online paths

The archived and live sources call the same RoboCasa geometry classifier
and grid planner in `g2/sim/robocasa_geometry.py`. Both import the pinned
nav_sg serializer and use the existing snapshot contract and SG projection
in `g2/nav_bridge`. The original offline metadata and grid commands retain
their entry points and output fields.

F27 material keyframes use `g2/views/f27.py` in both the production episode
renderer and live diagnostics. The offline caller supplies its clean RGB
audit. The live caller supplies its camera EGL restoration. Projection,
member sets, white-background composition and robot marker use the same
View implementations. The offline producer seals archived packages and
the live runtime retains the active image owners.

`g2/data/task_entities.py` holds the shared task initialization semantics.
The same CAP2 and State15 builders consume that binding and the appropriate
source observation. EvalV2 owns the live lifecycle and causal frontier.

## Configuration

Start from `configs/eval/robocasa_eval_v2_phase_b.example.yaml` in a new
namespace. Apply the following R1 settings on the fixed candidate. Use
an immutable model-only checkpoint publication under the original job
directory layout, along with its canonical `config.yaml` and materialized
G2 training recipe. A currently retained checkpoint in a running job can
expire. The Owner must select a stable evaluation copy before authorizing
execution.

```yaml
execution_profile: phase_b
local_memory_mode: required
local_evidence_profile: server_vae
local_ttt_history_k: 16
g2_profile: g2_r1
g2_run_recipe: /reviewed-r1-job/g2_run_recipe.json
g2_checkpoint_metadata_sha256: REPLACE_WITH_EXACT_MODEL_METADATA_SHA256
g2_actor_options:
  nav_checkout: /fixed/nav_sg
  nav_revision: REPLACE_WITH_FULL_NAV_CANDIDATE_SHA
  ros_setup: /isolated-nav-catkin/devel/setup.bash
  scratch_root: /new-private-run-root/spatial
  render_f27: true
render_backend: egl
tasks: [OpenDrawer, CloseFridge, NavigateKitchen]
episodes_per_task: 1
sims_per_gpu: 1
max_infer_batch_size: 1
guidance: 1.0
```

The existing EvalV2 assigned render device must support EGL when
`render_f27` is enabled. R1 never assembles a Global condition or invokes
View VAE. With `render_f27: false` it also skips diagnostic F27 images.
With diagnostics enabled, F27 reuses the existing material and background
renderer, motion thresholds and arrow overlay. For each generated View the
report includes its actual image owner, SHA256 and projection. Clean and
marked top variants can have different owner frames. Source metadata and
the newest owner artifacts stay in the episode scratch directory.

Use the existing EvalV2 preflight and the separate Owner authorization.
Specify the approved visible GPU explicitly. Both paths, including the
native checkout and Catkin setup, must exist in the runtime's namespace.

```bash
cd /fixed/psm_wma
"$EVAL_SERVER_PYTHON" scripts/robocasa_eval_v2_cli.py dry-run \
  --config "$ONLINE_R1_CONFIG" --gpus "$APPROVED_GPU"
"$EVAL_SERVER_PYTHON" scripts/robocasa_eval_v2_cli.py fresh \
  --config "$ONLINE_R1_CONFIG" --gpus "$APPROVED_GPU"
```

Each private episode scratch directory contains `source_frames.jsonl`,
`initial_condition.json` and native process diagnostics. The producer keeps
native frame 0 plus the newest validated full snapshot. F27 retains its
current physical image owners. EvalV2 persists request/ACK and success
or failure in its existing run directory.

## Acceptance sequence

1. Compare real online MuJoCo/native snapshot and F27 outputs to matching
   source frames, including Door/Drawer geometry, arrow, empty directions,
   owner frames and native memberships.
2. Compare State15 and CAP2 bytes/tokens to the training-side recipe.
3. Load the actual reviewed four-rank R1 DCP on one authorized GPU.
   Verify Raw15/H16 output, native Session ACK and execution history.
4. Record actual final success/failure for each named task and measure
   stage latencies. R2, selected-view Wan encoding and Global Reader are
   gated on this result.

The CPU DCP reshard check exercises real serialized four-rank tensors
with the native loader. The formal R1 model, real EGL pixels, closed-loop
success and latency remain separate execution results.

## CPU author evidence

The implementation pair passed 187 cases in the existing server Python
environment. This covers the old archived source preparation, Stage A,
task roles, CAP2 and F27 event behavior as well as the live actor,
mocap capture and shared keyframe audit order. The exact command was run
from the fixed Root checkout with its fixed Child:

```bash
env CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  PYTHONPATH="$PWD:$PWD/cosmos-framework:$PWD/scripts" \
  "$EVAL_SERVER_PYTHON" -m pytest --noconftest -o addopts='' -p no:cacheprovider -q \
  g2/tests/test_online_runtime.py g2/tests/test_online_live_views.py \
  g2/tests/test_shared_f27.py g2/tests/test_pose5.py g2/tests/test_initial_language.py \
  g2/tests/test_atomic_6views_run.py g2/tests/test_atomic_6views_preparation.py \
  g2/tests/test_stage_a_task_semantics.py g2/tests/test_stage_a_contracts.py \
  g2/tests/test_scene_view_event_index.py g2/tests/test_robot_pose_marker.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval_phase6_test.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval_lifecycle_test.py \
  tools/v3/eval_v2_replan_tests/config_test.py tools/v3/eval_v2_production_tests/entry_test.py \
  --junitxml="$ONLINE_EVIDENCE/candidate-root-shared.xml"
```

The native Noetic build also passed in the local reference environment.
The real native transport fixture accepted three snapshots and rejected
four malformed packets. Real server RoboCasa samples contributed 63
source-observation comparisons against the official exporter and 15
exact State15 comparisons against training-window conversion. The
NavigateKitchen probe included a measured 0.018606 m base displacement.
An R1 run recipe, checkpoint manifest, canonical config and all four DCP
shard witnesses passed the native authority check on CPU.

The fixed server build linked `gt_oracle_native` with the existing
Noetic/PCL 1.15 runtime. A CPU preview admitted all three tasks with zero
models loaded and zero environments created. In a separate real
no-camera smoke run, each task executed 20 simulation actions and received
native frame 0 and 20 snapshots. Frame 16 consumed the frame 0 snapshot.
The later frame consumed frame 20. All nine requested State15 values
matched the official source and training-window builders exactly.

| Task | Native frames | Rooms | Native entities |
| --- | --- | ---: | ---: |
| OpenDrawer | 0 and 20 | 1 | 49 |
| CloseFridge | 0 and 20 | 1 | 51 |
| NavigateKitchen | 0 and 20 | 1 | 43 |

OpenDrawer and CloseFridge used official evaluation metadata with
a fixed target layout/style and neutral actions. NavigateKitchen used
the vendor's default PandaOmron controller and a small base command.
The probes kept cameras and CUDA off. They do not produce image parity
or policy success rates.

Server logs stay in the isolated verification workspace. The main files
are `candidate-root-shared.log`, `candidate-root-shared.xml`,
`native-build-unused-include.log`, `live-native-real-shared.log` and
the per-episode `source_frames.jsonl`. The initial candidate handed off
EGL parity, trained R1 inference and task success or failure to the
execution Gate.

## MuJoCo 3.3.1 and masked EGL follow-up

Fixed Root `98beed4a6ecb9134d4925427a5129615d509b744`, Child/Gitlink
`3ef4f6c79aeba3d825ae247c1e884b6199eaf85d`, and nav_sg
`c7997241b2b0f1e6f7d44f851f8cea62de2144ad`. The patches address the real
OpenDrawer findings on the existing Drafts. [Root #93](https://github.com/wxwy/psm_wma/pull/93) · [Child #26](https://github.com/wxwy/cosmos-framework/pull/26)

The shared material resolver now reads the compiled 3.3.1 RGB/RGBA upload
without an sRGB transfer. The verified native explicit mesh UV path uses the
compiled coordinates. The archived 3.3.7 recipe keeps its existing mesh UV
and color-space behavior. Unknown versions retain invalid color and opacity
masks. Online F27 rejects zero-valid-color clean Views before drawing the
robot marker or publishing an owner. [3.3.1 texture upload](https://github.com/google-deepmind/mujoco/blob/a209134315dda126a714529bfa80f7478902644d/src/render/render_context.c) · [3.3.1 explicit UV binding](https://github.com/google-deepmind/mujoco/blob/a209134315dda126a714529bfa80f7478902644d/src/render/render_gl3.c)

EvalV2 keeps CUDA masked in the Actor. An isolated driver probe maps NVIDIA
EGL persistent UUIDs to PCI. The Actor selects its own enumerated EGL device
and requires the actual current context's process-local device handle and,
when supplied, its UUID. Ambiguous PCI evidence or a missing context handle
fails admission.

| Check | Author result |
| --- | --- |
| F27/material CPU regressions | 71 passed, 1 existing opt-in real-asset test skipped |
| EvalV2 rendering device and Actor CPU regressions | 38 passed |
| Stock software EGL fixtures on MuJoCo 3.3.1 and 3.3.7 | 10 fixtures and 1,732 pixels per version, maximum RGB delta 1 byte. The 3.3.7 receipt matches the archived candidate byte for byte. |
| `data` masked CUDA driver selection | All 8 physical GPUs matched by UUID and PCI in both default GLVND and NVIDIA-only modes. The probe opened no GPU render context. |
| Real OpenDrawer F27 on MuJoCo 3.3.1, Mesa llvmpipe | 49 entities and 1 Room. Clean floor top has 171,864 valid color pixels. The two side Views have 99,792 and 193,752. All four PNGs match the same snapshot rendered with the offline eager decoder byte for byte. The arrow changes 363 pixels on the separate marked top. |
| Real 20 Hz causal index | Decision frames 0/16/20 consume spatial frames 0/0/20. The second snapshot reports `REUSE_ALL` and its images keep their frame 0 owners. |
| R1 Iter 1000, OpenDrawer config preview | `CPU_PREVIEW_ONLY`, 0 models loaded, 0 environments created |
| Real NVIDIA camera context, R1 action, Local ACK and task outcomes | Await the independent GPU run for this exact candidate. |

The stock texture probe compares base-level texels against MuJoCo's actual
EGL pixels. Run it from the fixed Root with each existing MuJoCo interpreter.

```bash
CUDA_VISIBLE_DEVICES='' MUJOCO_GL=egl PYOPENGL_PLATFORM=egl \
  LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=2 PYTHONPATH="$PWD" \
  "$G2_MUJOCO_PYTHON" g2/tests/mujoco_material_compat_smoke.py
```

The real OpenDrawer run used the existing simulator with Layout 1, Style 1,
seed 42 and 20 neutral steps. The scratch runner selects the Mesa software
device and verifies `llvmpipe`. Its per-process GL/GLSL version overrides
enable the existing F27 compute shaders in software. The comparison uses the
same native snapshot and renderer with live lazy and offline eager decoding.
The first verifier log is preserved. It compared report lengths before
rereading the on-disk marker receipt. The corrected run rereads both receipts.

```bash
G2_FOLLOWUP=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_online_compat_98beed4a_20261120.DWqLLm
G2_REPLAY=$(mktemp -d "${G2_FOLLOWUP%/*}/.g2_online_compat_replay.XXXXXX")
for item in root nav ws; do
  ln -s "$G2_FOLLOWUP/$item" "$G2_REPLAY/$item"
done
cp "$G2_FOLLOWUP"/{data_egl_pci_probe.py,data_f27_software_probe.py,run-egl-pci.sh,run-f27-software.sh} "$G2_REPLAY/"
mkdir "$G2_REPLAY/spatial"
cd "$G2_REPLAY"
bash run-egl-pci.sh
bash run-f27-software.sh
```

The original scene data, images and raw logs stay on `data`.
`f27-software-gate.json` in the first completed directory
has SHA256 `6b9ac7f8def6c5cce5bc1c1a80a8799f37dd7fcb707f3fad8b735732e77d78dc`.
The preview `r1-review-OpenDrawer.yaml` uses the prior Iter 1000 model-only
publication, an independent output directory and `render_f27: true`.
For the next GPU execution, apply the independently assigned GPU with the
existing `fresh` command above. Verify the Actor's current EGL context,
the first `16×15D` action and its persisted Local ACK.

## G2 Actor runtime identity after independent NVIDIA verification

On Root `98beed4a6`, independent validation on `data` passed the real
NVIDIA EGL context handle check and proved pixel-for-pixel equality for
all four F27 PNGs from live lazy and offline eager decoding. The R1 Iter
1000 service loaded the four-rank DCP on one GPU. The Actor then rejected
its runtime digest. [Independent F27 and R1 evidence](https://github.com/wxwy/psm_wma/pull/93#issuecomment-7029673676) · [Independent EGL device/context evidence](https://github.com/wxwy/cosmos-framework/pull/26#issuecomment-7029775485)

Fixed Root `b5ac5f7af3d3b28d7b2bfcbde63360f39ecd8470`, Child/Gitlink
`3ef4f6c79aeba3d825ae247c1e884b6199eaf85d`, nav_sg
`c7997241b2b0f1e6f7d44f851f8cea62de2144ad`. Preflight constructs the
G2 `PYTHONPATH` with the candidate Root and Child once, followed by the
inherited entries. Fresh moves only the writable caches into the Run.
Fresh and Resume both supply the measured search path directly to the
Actor. The source and digest checks remain strict.

The focused regression exercises Fresh and Resume with and without the
project paths inherited. Both cases originally raised `Simulator runtime
changed after preflight` at the native verifier. With the fix, both pass and
an altered path still fails. The exact candidate passed all 205 targeted CPU
tests in the existing `data` environment. The log and JUnit are
`actor-env-regressions.log` and `actor-env-regressions.xml` in:

```text
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_online_actor_b5ac5f7a_20261120.HIFjS6/
```

The real Worker startup probe uses that release's actual simulator and
vendor manifest. It reuses the stat-checked model identity from the
earlier GPU run. The Worker passes `verify_runtime` and returns `READY`.
The launcher compares the actual process environment with the preflight
record and confirms an orderly close with exit code 0. This probe stops
before any environment, GPU context or policy server is created.
`ready-replay.VhIrt5/actual-actor-ready.json` has SHA256
`f1cc31e139b9ac478449e779afd5129e032050dbcc09d4068e771ea605f20ea8`.
The first raw log is preserved. Its harness expected a natural process
exit after supervisor cleanup. The completed replay waits for the Worker
close reply before checking the exit code. Replay with
`bash run-actor-ready.sh` from the isolated evidence directory. The
focused CPU suite uses `bash run-actor-env-regressions.sh`.

The isolated `r1-gpu-retest.yaml` uses OpenDrawer, Iter 1000 and
`render_f27: true`. Its CPU preview reports zero models loaded and zero
environments created. For independent GPU execution, set
`G2_ACTOR_EVIDENCE` to the directory above and use the existing server
Python from the isolated YAML with the assigned GPU.

```bash
cd "$G2_ACTOR_EVIDENCE/root"
export PYTHONPATH="$PWD:$PWD/cosmos-framework:$PWD/scripts"
export __EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/10_nvidia.json
"$EVAL_SERVER_PYTHON" scripts/robocasa_eval_v2_cli.py fresh \
  --config "$G2_ACTOR_EVIDENCE/r1-gpu-retest.yaml" \
  --gpus "$APPROVED_GPU" --render-gpus "$APPROVED_GPU"
```

Check the actual EGL context, one finite `16×15D` action, the corresponding
persisted Local ACK and the recorded outcome.

### NVIDIA stock-render reference investigation

The native stock-render material probe and the shared F27 comparison test
different paths. The independent H100 probe failed on the first stock 2D
fixture with a maximum 208-byte RGB delta. The shared F27 decoder's live
and offline PNGs on that hardware were identical. [Independent stock-render diagnosis](https://github.com/wxwy/psm_wma/pull/93#issuecomment-7029758645)

The scratch `stock_material_diagnose.py` runs the same 400-pixel fixture
and records compiled texture bytes versus GL upload, stock RGB versus
direct RGBA framebuffer readback, forced base-level sampling, white
emission and a constant RGB texture. On the `data` Mesa software driver
the upload, readback and constant controls are exact, and the base-level
projection differs by at most one byte. From the evidence directory,
`bash run-stock-material-nvidia.sh "$APPROVED_GPU"` uses the physical
EGL selection and records the per-stage deltas alongside the original
two-byte acceptance limit. The existing 3.3.7 archive recipe and version
guards continue to define the F27 output.
