# PSM-WMA Local Memory INIT Ablation — Reset Timeout Fix and Rerun Note

- Date: 2026-09-21
- Status: FIX IMPLEMENTED / INIT ABLATION MUST BE RERUN
- Root baseline before fix: `232663d46bc063fe969eff5f3d0c875c00e393eb`
- Child baseline before fix: `879c8e07f353836e8613d50a0cb9530805d7e97d`
- Child fix commit: `d10194c1b87733b4c690c3ab043935b855bf3ab8`

## 1. Observed failure

During the iter_000003000 `LOCAL_MEMORY_MODE=init` ablation, approximately 28 of 40 clients crashed on `POST /reset` read timeout.

The partial 400-episode result is incomplete (only roughly 54 episodes produced usable outputs) and must not be used for aggregate SR conclusions.

## 2. Root cause

Client `ActionEnvironmentClient.end_memory_episode()` used a hard-coded:

```python
timeout=5.0
```

for `POST /reset`, while prediction calls use the configurable client `self.timeout`.

The server is a `ThreadingHTTPServer`, but `/reset` acquires the same `service._lock` used to serialize model/memory transaction execution. Under INIT mode, which still executes the evidence -> query -> Memory Prefix path, concurrent prediction requests can keep reset waiting behind model inference. With multiple clients per server and external GPU training contention, 5 seconds is too short.

OFF did not expose the failure because it bypasses the Local Memory path and prediction is substantially faster.

## 3. Fix

File:

`cosmos-framework/cosmos_framework/simulation/libero/closed_loop_eval.py`

Changed:

```python
timeout=5.0
```

to:

```python
timeout=self.timeout
```

No new environment variable or server-side concurrency behavior was introduced.

A regression assertion was added to:

`cosmos-framework/cosmos_framework/simulation/libero/closed_loop_local_memory_test.py`

to verify reset uses the configured client timeout.

## 4. Why the server lock was not changed

Do not remove `service._lock` from `/reset` as part of this fix.

That would change concurrency semantics between prediction prepare/generate/commit and session reset. The current fix is intentionally limited to client timeout consistency.

If reset latency remains problematic after this change, investigate server-side scheduling separately with explicit transactional tests.

## 5. INIT ablation rerun requirement

The incomplete INIT result is invalid for aggregate comparison and must be rerun.

Use the same iter_000003000 checkpoint and the same matched ablation configuration as REQUIRED/OFF. The only semantic difference must remain:

```text
LOCAL_MEMORY_MODE=init
```

INIT semantics remain:

- real evidence is consumed
- query/read path remains active
- Memory Prefix is injected into MoT
- fast weights stay at checkpoint-learned W0 for the entire episode
- no online inner-update accumulation

Primary comparison remains:

```text
required - init = contribution of online persistent fast-weight update
init - off      = contribution of static Local readout/pathway
```

## 6. Rerun hygiene

Recommended:

- restart affected inference servers before rerun so stale Local Memory sessions from timed-out clients are cleared
- use a fresh INIT result directory, or only resume if the executor can prove completed episode artifacts are internally consistent
- do not merge the previous partial aggregate with the new formal result without explicit episode-level provenance checking
- preserve identical seeds / initial states / task limits / num_steps / guidance / action horizon used in REQUIRED/OFF

## 7. Expected validation

Before the full rerun:

1. run `closed_loop_local_memory_test.py`
2. do a small concurrent INIT smoke with the intended clients-per-server layout
3. confirm no `/reset` timeout
4. then start the full 400-episode INIT ablation
