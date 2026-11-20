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
the per-episode `source_frames.jsonl`. Actual EGL pixel parity, trained
R1 weights and inference, and task success or failure remain execution
gates.
