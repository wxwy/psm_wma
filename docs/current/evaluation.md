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