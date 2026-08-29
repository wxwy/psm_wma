# ChatGPT Review — R08 Gate B history_mask evidence patch @ root fc520ae / submodule 296f138

- Date: 2026-08-29
- Reviewer: ChatGPT
- Requested scope: history-mask evidence patch only
- Target root: `fc520aed693b83367359677b0febecefe732743a`
- Target submodule: `296f138ff0cd0f40b4f19ef1937b844b43a59f97`
- Verdict on narrow patch: **REQUEST_CHANGES**
- Overall Gate B: **REVIEW**
- GPU recapture: **DO NOT START YET**

## Summary

The patch direction is correct:

- capture the actual `data_batch["history_mask"]` in the Normal/Zero/Shuffle JSON;
- add `history_mask` to comparator exact invariants.

This is exactly the missing machine evidence needed to prove the mask is unchanged across R08 history interventions.

However, the capture helper does not yet mirror the production batch-shape contract, and the larger Gate-B same-checkpoint provenance HIGH from the previous review is still untouched.

## MEDIUM — history_mask capture helper is not compatible with the full production list contract

At `cosmos_framework/callbacks/r07_parity_capture.py:52`:

```python
def _tensor_or_list_summary(value):
    return cls._tensor_list_summary(value) if isinstance(value, list) else cls._tensor_summary(value)
```

This supports:

- `Tensor`;
- `list[Tensor]`.

But the production R08 history path deliberately supports an additional joint-dataloader nesting form.

At `cosmos_framework/model/generator/omni_mot_model.py:960-969`, `_stack()` does:

```python
if isinstance(value, list):
    value = [item[0] if isinstance(item, list) else item for item in value]
    if not all(isinstance(item, torch.Tensor) for item in value):
        raise TypeError(...)
    value = torch.cat(value, dim=0)
```

So `list[list[Tensor]]` is an explicit supported production input shape.

The new capture helper would pass the inner `list` into `_tensor_summary()`, which then calls `.detach()` and fails.

### Required fix

Make the capture normalizer mirror the supported production structure before summarizing.

Minimal pattern:

```python
if isinstance(value, torch.Tensor):
    return cls._tensor_summary(value)
if isinstance(value, list):
    value = [item[0] if isinstance(item, list) else item for item in value]
    if not all(isinstance(item, torch.Tensor) for item in value):
        raise TypeError(...)
    return cls._tensor_list_summary(value)
raise TypeError(...)
```

Do not add tuple support unless the production `_stack()` contract is also expanded to tuple.

Add CPU tests for:

1. tensor `history_mask`;
2. `list[Tensor]` history_mask;
3. `list[list[Tensor]]` history_mask;
4. invalid list entry -> clear TypeError.

## Comparator history_mask exact invariant: PASS

Adding `history_mask` to `INVARIANT_KEYS` in `tools/g0/compare_r07_sensitivity.py` is correct.

Once the three new captures contain the mask summary, the comparator will require:

```text
Normal history_mask == Zero history_mask == Shuffle history_mask
```

exactly, which is the desired Gate B invariant.

## IMPORTANT — previous Gate B provenance HIGH remains OPEN

This narrow patch does not address the main blocker from the prior review:

**Normal / Zero / Shuffle must be machine-proven to use the same fixed checkpoint and runtime state.**

The previous `gate_b_history_sensitivity.json` still lacks:

- per-process root/submodule/Gitlink provenance;
- checkpoint load path/identity;
- same-checkpoint proof across all three modes;
- capture-only/history-mode proof;
- config/raw-sidecar hashes;
- strict Gate-B-specific provenance in PASS logic.

Therefore, fixing mask capture alone is not sufficient to close Gate B.

## Avoid wasting a second GPU recapture

The Inbox says a new three-mode capture-only forward will run after this patch is approved.

Do **not** run that recapture with only the mask change.

Before the next GPU capture, also add the Gate-B-specific runtime provenance instrumentation/verifier requested in the previous review, so the same three minimal forward-only captures close both remaining evidence gaps at once.

Each capture process should record at startup/run time:

- root HEAD;
- submodule HEAD;
- root Gitlink;
- Gitlink == submodule HEAD;
- expected `PSM_R08_HISTORY_MODE`;
- `PSM_R08_GATE_B_CAPTURE_ONLY=1`;
- exact loaded Gate-A checkpoint path;
- loaded checkpoint/iteration marker;
- config hash;
- capture JSON/PT hashes or enough information for the post-run verifier to hash them.

The final strict Gate-B artifact should require:

```text
same checkpoint
AND valid runtime provenance
AND capture-only fixed weights
AND modes = normal/zero/shuffle
AND history_mask exact
AND all other non-history invariants exact
AND history payload changed
AND Future finite/nonzero response
AND Action finite/nonzero response
```

Prefer `r08_gate_b_history_sensitivity_v1` rather than reusing the R07 schema.

## Verdict

**REQUEST_CHANGES on this narrow mask patch.**

Next work remains CPU/static:

1. fix nested-list compatibility and add tests;
2. add the already-required Gate-B same-checkpoint/runtime provenance instrumentation;
3. request re-review;
4. only after approval, run one minimal three-mode capture-only GPU round that produces both mask and provenance evidence.

No Gate C, no R09, no multi-GPU, no long training.