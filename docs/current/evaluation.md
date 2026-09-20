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

## E003 bounded recent-history control

E003 uses the same canonical `visual96 + executed_action10` evidence inventory and
the same one-token Local interface as Local TTT, but keeps only the most recent
finite window. The recurrent replay is recomputed from zero state on every policy
query; no GRU hidden state or TTT fast weight is carried across queries.

The formal matched control uses `H=16`, equal to `ttt_tbptt_steps=16`.
This isolates persistence while keeping the bounded raw-history window equal to one
TTT segment. `H=32` is reserved as an optional stronger finite-history control
only if the H16 result leaves a context-length ambiguity; H64 is not part of the
current E003 plan.

Train:

```bash
LIBERO_ROOT=/disk/rl/data/LIBERO_LeRobot_v3 \
bash examples/launch_sft_action_policy_libero_edge_all_recent_history.sh
```

Evaluate the formal `iter_000002800` checkpoint:

```bash
TASK_SUITES="libero_goal libero_10" \
scripts/eval_recent_history.sh /absolute/path/to/iter_000002800
```

The E003 launcher fail-closes against R09-A1 and all TTT routes. Training and
inference both emit a single `1 x 32` Local token; the only episode memory kept
by inference is the last `H` canonical evidence rows.
