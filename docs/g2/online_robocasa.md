# G2 R1 Online RoboCasa candidate

The opt-in EvalV2 Phase B profile uses the current episode's MuJoCo model and
FULLPHYSICS data. A private MjData copy goes through the pinned nav_sg geometry
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
  --config "$ONLINE_R1_CONFIG" --gpus "$APPROVED_GPU" \
  --owner-decision "$OWNER_DECISION"
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
