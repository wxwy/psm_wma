# ChatGPT Review — R08 Gate B batch-packing mask lifecycle hotfix @ root 2ad910a / submodule 860f532

- Date: 2026-08-29
- Reviewer: ChatGPT
- Review request: `2ad910aab2060a720e607fb826a4c4cf9db673f2`
- Runtime/root tree: V2 at `2ad910a`
- Target submodule/Gitlink: `860f5328b5b9fa41103497abaad7985a6c0333ae`
- Scope: effective history-mask audit lifecycle across batch repacking
- Verdict: **APPROVE_TO_RUN_GATE_B_CAPTURE_ONLY**

## Review

This hotfix closes the failure exposed by the previous approved capture attempt.

The real training path is:

```text
_prepare_training_data(data_batch)
  -> _inject_local_history(data_batch, sequence_plans)
  -> get_data_and_condition(...)
  -> typed/payload packing
  -> training_step(...)
  -> output_batch
  -> callback
```

The previous patch stored the audit copy in the pre-pack `data_batch`:

```python
data_batch["r07_parity_history_mask"] = history_mask
```

but runtime confirmed that the batch is repacked between injection and the end of `training_step`, so that dict-side audit field is not a reliable carrier.

The new patch stores the **effective normalized mask** on the current model instance:

```python
history_mask = _stack("history_mask").bool()
self._r07_parity_history_mask = history_mask
```

and later emits exactly that value:

```python
output_batch["r07_parity_history_mask"] = self._r07_parity_history_mask
```

This remains the exact mask passed to:

```python
local_history_runtime(..., history_mask=history_mask)
```

so the verifier still observes the actual effective Local-history mask.

## State-safety assessment

For the approved Gate-B scope this temporary model attribute is acceptable:

- single GPU;
- one capture forward per process/mode;
- `_inject_local_history` runs before the corresponding `training_step`;
- the value is overwritten by the current batch before it is emitted;
- no asynchronous callback path was identified;
- no optimizer/backward/long loop is approved.

Therefore there is no credible stale-mask attribution risk in the current Gate-B capture-only execution.

This approval does **not** freeze this model attribute as the eventual long-training design. If later reused in multi-step/multi-GPU training, a more explicit per-step carrier may be preferable, but that is outside this hotfix and is not a Gate-B blocker.

## Provenance / Gitlink

The current V2 tree at `2ad910a` points exactly to:

`cosmos-framework@860f5328b5b9fa41103497abaad7985a6c0333ae`.

So the reviewed root/submodule state is coherent.

## Unchanged contracts

The patch does not change:

- Normal/Zero/Shuffle history intervention semantics;
- `history_mask` contents;
- Local model input;
- model weights/architecture;
- checkpoint;
- optimizer;
- canonical checkpoint manifest/verifier;
- sequence packing/attention;
- capture-only exit semantics.

## Verdict

**APPROVE_TO_RUN_GATE_B_CAPTURE_ONLY**

Restart:
1. Normal
2. Zero
3. Shuffle

Keep all existing constraints:
- pinned reviewed Gate-A checkpoint;
- same current sample/batch;
- same noise;
- same masks;
- same non-history config/inputs;
- only history intervention changes;
- forward/capture only;
- no backward;
- no optimizer;
- no long training;
- no multi-GPU;
- no Gate C;
- no R09.

After the three valid captures, run the strict Gate-B verifier and submit the final artifact + JSON/PT/provenance/log/config hashes for runtime review.
