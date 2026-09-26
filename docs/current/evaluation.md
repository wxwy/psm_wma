# Evaluation

## Closed-loop LIBERO

The project uses the existing Cosmos action server plus the LIBERO closed-loop client. Current Local Memory inference is integrated into both sides:

- server: `cosmos_framework/scripts/action_policy_server_libero.py`
- policy adapter: `cosmos_framework/inference/local_memory_policy.py`
- online fast state: `cosmos_framework/inference/local_memory_online.py`
- client/session bridge: `cosmos_framework/simulation/libero/local_memory_client.py`
- rollout: `cosmos_framework/simulation/libero/closed_loop_eval.py`

The server exposes `local_memory_mode = auto | off | required`. `auto` enables session memory when the loaded checkpoint contains the Local TTT modules; `off` is the explicit memory ablation.

## Evaluate one checkpoint

Use the project facade:

```bash
scripts/eval.sh /absolute/path/to/checkpoint
```

Optional environment variables:

- `OUTPUT_DIR` — result directory
- `NUM_STEPS` — denoising steps; default 30 in the facade
- `NUM_TRIALS` — trials per task
- `TASK_SUITES` — space-separated suite list
- `TASK_IDS` — comma-separated task IDs
- `LOCAL_MEMORY_MODE` — `required`, `auto`, or `off`
## Recommended comparisons

For a checkpoint trained with Local Memory, keep the checkpoint and rollout setup fixed and compare:

1. `LOCAL_MEMORY_MODE=required` — Local Memory active
2. `LOCAL_MEMORY_MODE=off` — same checkpoint, Local Memory ablated

This isolates the online Local conditioning path from checkpoint identity. It does not replace a separate no-memory training baseline when measuring the full effect of memory-aware training.

## Result interpretation

The current repository has engineering evidence that the online Local path is finite, session-isolated and action-affecting. It does **not** yet contain the final 5000-step LIBERO success-rate conclusion.

Evaluation outputs are experiment results, not authority documents. Record the checkpoint SHA/path, suite/task/trial coverage, denoising steps and Local Memory mode alongside every reported SR.

## Unified history controls

History selection now uses one user-facing switch:

```bash
PSM_HISTORY_MODE=none|window|gru|ttt
```

The modes intentionally keep different history representations rather than forcing
all controls through a Local token:

| Mode | History span | Representation into MoT | Persistent state |
|---|---|---|---|
| `none` | none | current observation only | no |
| `window` | last H=16 completed steps | native full-spatial clean vision latents + clean executed-action prefix | bounded window only |
| `gru` | last H=16 completed steps | canonical `visual96 + executed_action10` -> zero-state GRU replay -> `1 x 32` Local token | bounded window only |
| `ttt` | full episode | canonical evidence -> fast-weight updates -> `1 x 32` Local token | episode-level |

For `window`, every historical observation is represented by the first causal
latent of its exact-window VAE cache entry at full spatial latent resolution.
There is no visual96 pooling, GRU, or learned history compressor. Historical
executed actions are prepended as clean action conditions. The final WAM vision
item keeps the native layout: current latent clean, future temporal latents noised
and supervised. FPS-aware mRoPE positions align the history vision items and
executed actions on the same source-frame clock.

Fully-clean history vision items are excluded from the final vision scalar mean,
so they do not dilute the native WAM target loss. The final WAM item's own
current-clean/future-noised denominator remains unchanged.

`gru` is the previous E003 bounded recent-history control. Its recurrent replay
starts from zero on every policy query and carries no hidden state across queries.

`ttt` is not H=16 memory. `ttt_tbptt_steps=16` only truncates the training
graph; numerical fast weights carry across detached segments for the full episode.
At a new episode, training initializes fast weights from the latest slow `W0`;
inference initializes them from the checkpoint-saved `W0`.

The bounded controls do not by themselves form a persistence-only ablation because
TTT also changes the representation and update mechanism. The strongest bounded
history comparison is `window` versus `ttt`: the window gives MoT the last 16
steps without an extra learned compression bottleneck.

### Train

Unified entrypoint:

```bash
PSM_HISTORY_MODE=window bash scripts/train_history.sh
PSM_HISTORY_MODE=gru    bash scripts/train_history.sh
PSM_HISTORY_MODE=ttt    bash scripts/train_history.sh
```

The WINDOW-H16 formal training ceiling is `max_iter=5000`. This is a ceiling, not a required stopping point: the owner may manually stop at any checkpoint. Do not treat iter2800 or iter3000 as the formal training endpoint.

For 8-GPU FSDP WINDOW training, use 16 samples/rank/native-forward with `grad_accum_iter=16`, giving `16 × 8 × 16 = 2048` consumers/update. The single-GPU recipe keeps GA=128 for the same 2048-consumer update size.

### Evaluate

Evaluation checkpoint selection is separate from the training stop condition. Use the owner-selected WINDOW checkpoint when requested; matched checkpoints such as iter2800 may still be used for historical comparison, but are not training endpoints.

```bash
PSM_HISTORY_MODE=window \
TASK_SUITES="libero_goal libero_10" \
scripts/eval_history.sh /absolute/path/to/window/checkpoint
```

For a trained history checkpoint, `LOCAL_MEMORY_MODE=off` can be used as a
same-checkpoint inference-path ablation. For `window` this removes the native
history prefix entirely; for `gru`/`ttt` it removes the Local conditioning
path. This does not replace the separately trained Native Cosmos baseline.


## Single-episode inference profiling

Batch LIBERO evaluation and inference profiling are separate protocols:

- **Batch evaluation**: measure SR / task breakdown / aggregate wall time.
- **Profile evaluation**: one GPU, one model-server process, one serial LIBERO env, one task, one episode, action-only output.

Every reported history method (`none`, `window`, `gru`, `ttt`) must run the same profiling protocol on the same hardware, task, initial-state seed, image resolution, action horizon, denoising steps and checkpoint-selection policy.

Run:

```bash
PSM_HISTORY_MODE=window \
PROFILE_GPU=0 \
PROFILE_SUITE=libero_10 \
PROFILE_TASK_ID=0 \
NUM_STEPS=30 \
ACTION_HORIZON=8 \
bash scripts/profile_history.sh /absolute/path/to/checkpoint
```

Change only `PSM_HISTORY_MODE` and the corresponding checkpoint for the other methods.

Profiling is action-only: Cosmos still performs vision encoding, MoT packing and denoising/action generation, but predicted future-video VAE decode and PNG encoding are disabled. If video output is explicitly enabled elsewhere, its decode/PNG costs remain separately measurable and must not be merged into core action latency.

The profile output stores every policy-query timing in the episode prediction JSON and writes an aggregate profile JSON under:

```text
<output>/<suite>/profile/task_XXX/episode_000.json
```

Required comparison fields:

| Category | Required fields |
|---|---|
| End-to-end | client total, HTTP roundtrip, server total |
| Server | preprocess, batch build, lock wait, policy generation, action postprocess |
| Cosmos model | prompt upsample, prepare inference, pack template, diffusion sampling, output unpack, total generation |
| History common | history overhead total |
| WINDOW | payload/history preprocessing, action normalization, prefix assembly, output trim |
| GRU | raw-history visual-summary encoding, action normalization, request build, evidence encoder, window merge, GRU replay, Local inject/commit |
| TTT | raw-history visual-summary encoding, action normalization, request build, validation, evidence encoder, K/Q/V projection, inner update+read, state detach, Local inject/commit |
| Resources | GPU allocated before request, peak allocated, peak reserved, peak delta allocated, server RSS, client RSS |
| Environment overhead | MuJoCo env-step time, client completed-memory record time |

The first policy query is reported separately as **cold start**. The remaining policy queries are summarized independently as **steady state** with mean / p50 / p95 / min / max. Do not mix the empty-history first query into the steady-state history-cost comparison.

Profiling uses explicit CUDA synchronization to make GPU stage timings observable. Therefore the profiling run is diagnostic and may add a small probe overhead. Deployment/batch throughput must still be reported from the normal non-profile evaluation path.

Inference speed and resource use are first-class comparison metrics alongside SR; a method with higher SR but materially larger latency/VRAM must report that trade-off explicitly.


H32 remains optional and should only be considered after the H16 results leave a
context-length ambiguity.


## Closed-loop RoboCasa

RoboCasa now has a separate closed-loop evaluation path for the current active Local-TTT training route:

- server: `cosmos_framework/scripts/action_policy_server_robolab.py`
- online Local-TTT adapter: `cosmos_framework/inference/local_memory_policy.py`
- client completed-evidence ledger: `cosmos_framework/simulation/robocasa/local_memory_client.py`
- rollout / SR aggregation: `cosmos_framework/simulation/robocasa/closed_loop_eval.py`
- project launcher: `scripts/eval_robocasa.sh`

The evaluator follows RoboCasa's native Gym task registry, task horizon, and `info["success"]` semantics. The current training/eval observation contract is `left_wrist` (agentview-left concatenated horizontally with wrist) plus the 16-D RoboCasa state.

Evaluate a checkpoint:

```bash
LOCAL_MEMORY_MODE=required \
ROBOCASA_SPLIT=target \
TASK_SETS="atomic_seen" \
NUM_TRIALS=10 \
REPLAN_STEPS=5 \
scripts/eval_robocasa.sh /absolute/path/to/checkpoint
```

First bounded smoke:

```bash
LOCAL_MEMORY_MODE=required \
ROBOCASA_SPLIT=target \
TASK_SETS="atomic_seen" \
MAX_TASKS=1 \
NUM_TRIALS=1 \
REPLAN_STEPS=1 \
scripts/eval_robocasa.sh /absolute/path/to/checkpoint
```

RoboCasa Local-TTT inference uses canonical completed evidence `causal_visual96_executed_action20_v1`. At each executed step the base component of the 20-D evidence is reconstructed from the observed pre/post base pose instead of copying an unexecuted model prediction.

The current formal 20-D evaluator uses `BASE_DECODE_MODE=calibrated` by default. The calibrated decoder preserves the ego-frame slot/sign contract, maps `[ego_dx, ego_dy, relative_yaw]` through the held-out fitted linear inverse, clamps native base commands to `[-1,1]`, forces `base_motion[3]=0`, and zeros all base commands when the predicted control channel selects arm mode. Legacy `velocity`, `delta`, and `zero` modes remain diagnostic only.

Runtime validation status:

- full `atomic_seen` smoke completed 18/18 tasks on checkpoint `iter_000003300`;
- `LOCAL_MEMORY_MODE=required`, `BASE_DECODE_MODE=calibrated`, `REPLAN_STEPS=1`, `NUM_TRIALS=1`;
- no infrastructure error;
- `bm3_nonzero_steps == 0` across all 18 tasks;
- `arm_active_nonzero_base_steps == 0` across all 18 tasks;
- base-active execution was exercised by NavigateKitchen (450/450 steps) and CloseFridge (116/900 steps).

Control-mode diagnostics show a strongly bimodal policy output rather than threshold jitter: 16/18 tasks stayed saturated near -1 and never activated the base; NavigateKitchen stayed near +1; CloseFridge switched between negative and positive modes. Do not change the zero threshold on this evidence.

This 18-task run is a **runtime smoke**, not a RoboCasa SR benchmark: it uses one rollout per task and `REPLAN_STEPS=1`. Benchmark-style evaluation must use a separately declared rollout protocol; do not report the smoke's 0/18 successes as benchmark SR.

See:

- `docs/build/PSM-WMA_RoboCasa_atomic_seen_smoke_full_2026-09-26.md`
- `docs/build/PSM-WMA_RoboCasa_base_decoder_calibration_closure_2026-09-24.md`
- `docs/build/PSM-WMA_RoboCasa_base_physics_diagnostics_2026-09-25.md`
