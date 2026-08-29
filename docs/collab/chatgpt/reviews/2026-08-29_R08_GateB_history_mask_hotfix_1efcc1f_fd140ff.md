# ChatGPT Review — R08 Gate B history-mask capture hotfix @ root 1efcc1f / submodule fd140ff

- Date: 2026-08-29
- Reviewer: ChatGPT
- Target root: `1efcc1fdc6f4c70dd3623a5e6106857e69099aec`
- Review-request root: `098846aeb540368b4cf2b80de4cbd67bb889b83b`
- Target submodule/Gitlink: `fd140ff52afd7d55d35b8cf7c87aff9823373b0c`
- Scope: history-mask capture lifecycle hotfix only
- Verdict: **APPROVE_TO_RUN_GATE_B_CAPTURE_ONLY**

## Review

The runtime failure is consistent with the actual data lifecycle:

- `history_mask` is normalized/stacked inside `_inject_local_history()`;
- the old parity callback tried to read `data_batch["history_mask"]` later in `on_training_step_end`;
- by then that original field is not guaranteed to remain available.

The hotfix now captures the mask at the correct point:

```python
history_mask = _stack("history_mask").bool()
data_batch["r07_parity_history_mask"] = history_mask
```

This is the exact mask passed to `local_history_runtime(..., history_mask=history_mask)`.

At the end of `training_step`, the audit value is copied into the callback-visible output:

```python
output_batch["r07_parity_history_mask"] = data_batch["r07_parity_history_mask"]
```

and the callback reads only:

```python
output_batch["r07_parity_history_mask"]
```

Therefore the recorded value is the **effective normalized Local history mask**, not an unrelated reconstructed or stale field.

The intervention logic remains unchanged:
- Normal/Zero/Shuffle alter history payload fields;
- `history_mask` itself is not zeroed or shuffled;
- the same mask can therefore remain an exact non-history invariant across the three captures.

The patch does not alter:
- Local evidence values in Normal mode;
- Zero/Shuffle intervention semantics;
- model architecture or weights;
- checkpoint load path;
- optimizer behavior;
- canonical manifest pinning/verifier;
- sequence packing or attention contracts.

The focused callback tests exercise the new `r07_parity_history_mask` output field and production-supported mask shapes. No new blocker found.

## Verdict

**APPROVE_TO_RUN_GATE_B_CAPTURE_ONLY**

Restart from **Normal**, then:
1. Zero
2. Shuffle

Retain all previously approved constraints:
- pinned reviewed Gate-A checkpoint;
- same batch/current sample;
- same noise;
- same masks;
- same non-history inputs/config;
- only history intervention changes;
- forward/capture only;
- no backward;
- no optimizer step;
- no long training;
- no multi-GPU;
- no Gate C;
- no R09.

After all three captures, run the strict Gate-B verifier and submit the final artifact plus raw JSON/PT/provenance/log/config hashes for runtime review before advancing.
