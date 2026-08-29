# ChatGPT Review — R09-A1 final-checkpoint sensitivity capture @ e256cfb

- Date: 2026-08-29
- Reviewer: ChatGPT
- Request commit: `e256cfb273197357769a58a201ec1a27d385687a`
- Corrected training source: `32e3bce9cf9815816f6fdb8cabc29f2effac7c5d`
- Corrected submodule/Gitlink: `c0287e215f265134cb8b8d947de7eb398f0246cf`
- Proposed sensitivity source: `1aee1091693b0254cf1cc63999e9fdc6dfa6f329`
- Verdict: **APPROVE_TO_RUN_A1_FINAL_SENSITIVITY**

## Corrected 100-step source boundary

The corrected training source is within the approved implementation boundary.

`d91ee0c -> 32e3bce` changes only `docs/collab/chatgpt/CODEX_INBOX.md`; the R09 model/config/probe implementation remains the reviewed `c0287e2`.

Likewise `32e3bce -> 1aee109` changes only ChatGPT review/Inbox documentation. No model, dataflow, optimizer allowlist, or submodule change is introduced.

Therefore the proposed sensitivity source remains code-equivalent to the approved corrected A1 runtime.

## Fixed-weight capture semantics independently verified

The proposed use of:

```text
PSM_R08_GATE_B_CAPTURE_ONLY=1
trainer.max_iter=1
```

is valid for a fixed-weight capture.

In the trainer implementation, capture-only returns immediately after `model_ddp.training_step(...)` and before backward:

```python
output_batch, loss = model_ddp.training_step(data, iteration)
...
if capture_only:
    return output_batch, loss, 0
```

Therefore the three captures do not execute:

- backward;
- optimizer step;
- scheduler step;
- gradient update.

The outer loop may still advance the bookkeeping iteration and may write an incidental final checkpoint at train end; that does not change model weights and must not be used as the sensitivity source checkpoint. Every mode must independently reload the same corrected `iter_000000100/model`.

## Sensitivity comparator is suitable

The existing `tools/g0/compare_r07_sensitivity.py` hard-checks 15 non-history invariants:

```text
x0_vision
xt_vision
sigma_vision_schedule
sigma_vision_effective
x0_action
xt_action
sigma_action_effective
text_ids
text_indexes
vision_indexes
action_indexes
split_lens
attn_modes
position_ids
history_mask
```

It also requires:

- Normal→Zero Local payload change;
- Normal→Shuffle Local payload change;
- nonzero `preds_vision` response;
- nonzero `preds_action` response.

For the R09-A1 gate, treat `preds_vision` as the Future/vision branch response and `preds_action` as the Action response.

## Authorized captures

Authorize exactly three independent single-GPU capture-only runs:

```text
Normal History
Zero History
Shuffle History
```

For all three:

- load the same corrected final `iter_000000100/model`;
- same exact source/submodule/Gitlink;
- same config;
- same deterministic seed;
- same dataset/cache root;
- same sample/batch ordering;
- same stochastic/noise inputs;
- `PSM_R08_GATE_B_CAPTURE_ONLY=1`;
- `trainer.max_iter=1`;
- only `PSM_R08_HISTORY_MODE` may differ;
- use separate output paths for JSON/tensor/provenance captures;
- no R09 training extension, TTT, evaluation, or optimizer update.

Run the existing read-only sensitivity comparator after all three captures.

## Required PASS conditions

A1 final sensitivity PASS requires:

1. all 15 non-history invariants exact across Normal/Zero/Shuffle;
2. Local payload changes under Zero and Shuffle as required by comparator;
3. Normal→Zero:
   - Future/`preds_vision` L2 diff > 0;
   - Action/`preds_action` L2 diff > 0;
4. Normal→Shuffle:
   - Future/`preds_vision` L2 diff > 0;
   - Action/`preds_action` L2 diff > 0;
5. same final checkpoint and same runtime source across all three captures;
6. capture-only true for all three.

No minimum effect-size threshold is introduced at this gate; nonzero response plus exact non-history invariants is the frozen requirement.

## Important A1 closure evidence still required

This approval authorizes the sensitivity capture but does not itself close A1.

Before `R09-A1 = DONE`, commit canonical, independently reviewable evidence into V2:

- corrected 100-step smoke artifact produced by the clean-source verifier;
- D005 sidecar/provenance reference;
- final Normal/Zero/Shuffle capture summaries/tensors or stable machine-readable digests;
- final sensitivity comparison artifact;
- exact root/submodule/Gitlink for the three captures.

The currently described corrected artifact at:

```text
/gemini/code/r09-a1-corrected/artifacts/a1_single_gpu_smoke_corrected.json
```

is not yet present as a canonical V2 artifact, so it cannot be the sole basis for final A1 closure until committed/referenced in a stable artifact.

## Still blocked

```text
R09-B / TTT = BLOCKED
multi-GPU = BLOCKED
long training = BLOCKED
matched SR = BLOCKED
backend freeze = BLOCKED
shared MoT = BLOCKED
Global / Agent / RL = BLOCKED
```

After the three captures and canonical artifact commit, stop at REVIEW and request `APPROVE_TO_CLOSE_A1`.
