# R09-B2 P3 production-constructor witness re-review

- Review request root: `f30ac8a0e3bbaf3e87d12edef8bed97b646800e3`
- Reviewed implementation root: `eb05ea76a33aaabec58d64c63fb856be6ad7ec0a`
- Submodule/Gitlink: `0af5d53900ec169f43104d4fdf1827ad6691600d`
- Scope: static P3 processor-construction evidence hardening only; no GPU/HF/processor/model construction authorization.

## Verdict

**REQUEST_CHANGES**

The previous arbitrary-`Callable` blocker is partially addressed: callers can no longer inject `lambda: object()` into the production wrapper, and the wrapper now requires an `OmniMoTModel` instance and calls `model.set_up_tokenizers()`.

However, this does not establish the required ordering for the *first* production processor construction.

## HIGH — wrapper receives an already-constructed `OmniMoTModel`; its first processor construction has already happened before the P3 precondition gate

At reviewed submodule commit `0af5d53`, `OmniMoTModel.__init__()` executes, in order:

1. `set_precision()`
2. `set_up_data_key()`
3. `set_up_tokenizers()`
4. `set_up_parallelism()`
5. `set_up_model()`

Therefore an ordinary `OmniMoTModel` instance cannot exist without `set_up_tokenizers()` already having run once. The new root-side wrapper:

```python
run_production_processor_construction(record, model)
```

accepts such an existing instance and then calls `model.set_up_tokenizers()` again. That second call can produce a witness, but it cannot prove the required ordering:

`offline env applied -> binding validated -> FIRST production processor construction -> post snapshot`.

In other words, the actual first production construction may already have happened before the offline/binding hard gate. The new `constructor_identity="OmniMoTModel.set_up_tokenizers"` string does not fix that temporal gap.

This is especially important because P3's currently approved scope does not authorize full model construction merely to obtain an `OmniMoTModel` instance.

## Required fix

Do not make P3 processor evidence depend on a pre-existing `OmniMoTModel` instance.

Preferred design:

1. Extract the production VLM-processor construction primitive into a reviewed shared helper in the submodule, for example a function that performs the exact `lazy_instantiate(vlm_config.tokenizer)` construction used by `OmniMoTModel.set_up_tokenizers()`.
2. Make `OmniMoTModel.set_up_tokenizers()` call that shared helper.
3. Make the P3 isolated worker call the same shared helper only after:
   - local asset precheck;
   - offline env application/readback;
   - resolved local tokenizer binding validation.
4. Bind that shared helper source/callsite identity into the already-existing commit-blob provenance set.
5. Only after that helper returns the processor instance may the worker take the independent post snapshot and emit construction witness.

This preserves the P3 processor-only exception without requiring full `OmniMoTModel` construction.

If instead the implementation chooses full `OmniMoTModel(config)` construction, that is a scope expansion because `__init__()` continues into parallelism/model setup and must be separately planned/reviewed before use.

## Required regression

Add a static/isolated regression proving:

- precondition evidence alone -> FAIL;
- an already-constructed `OmniMoTModel` / second `set_up_tokenizers()` call cannot satisfy the first-construction witness contract;
- arbitrary constructor identity -> FAIL;
- only the reviewed shared production processor helper, invoked after preconditions with the exact resolved local tokenizer binding, can produce a valid construction witness;
- changed post asset snapshot -> FAIL.

## Accepted from this round

- arbitrary root-side `Callable` injection was removed;
- verifier now rejects arbitrary `constructor_identity` strings;
- construction witness remains tied to resolved binding SHA and processor type;
- before/after asset equality and fixed phase trace remain enforced;
- no GPU/HF/model execution was performed in this submission.

## Scope

Still not authorized:
- GPU execution;
- HF/Transformers processor construction;
- `OmniMoTModel` construction;
- model/checkpoint/weight/VAE/data/dataloader loading;
- forward/backward/optimizer/scheduler step;
- DCP save/load;
- B2-T, P4/P5, training/eval/inference/closed-loop/SR/multi-GPU/long training/backend freeze/Global/Agent/RL.
