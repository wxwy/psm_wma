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

Formal H16 bounded-control checkpoints use `iter_000002800`.

The WINDOW recipe packs 16 samples/native forward with GA=128; the GRU recipe
packs 128 samples/native forward with GA=16. Both therefore preserve 2048
consumers per optimizer update.

### Evaluate

```bash
PSM_HISTORY_MODE=window \
TASK_SUITES="libero_goal libero_10" \
scripts/eval_history.sh /absolute/path/to/window/iter_000002800

PSM_HISTORY_MODE=gru \
TASK_SUITES="libero_goal libero_10" \
scripts/eval_history.sh /absolute/path/to/gru/iter_000002800
```

For a trained history checkpoint, `LOCAL_MEMORY_MODE=off` can be used as a
same-checkpoint inference-path ablation. For `window` this removes the native
history prefix entirely; for `gru`/`ttt` it removes the Local conditioning
path. This does not replace the separately trained Native Cosmos baseline.

H32 remains optional and should only be considered after the H16 results leave a
context-length ambiguity.
