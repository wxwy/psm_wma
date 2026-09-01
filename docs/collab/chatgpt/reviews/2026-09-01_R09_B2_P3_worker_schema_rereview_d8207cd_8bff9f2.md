# R09-B2 P3 worker evidence schema re-review

- Review request root: `d8207cd7168a18716c2ed37624faefd3a854d2c4`
- Reviewed implementation root: `8bff9f2e9c68373f693b097f1d67849f86734e8c`
- Submodule/Gitlink: `0af5d53900ec169f43104d4fdf1827ad6691600d`
- Scope: root-side static worker-precondition/evidence-schema implementation only; no GPU/HF/processor/model construction authorization.

## Verdict

**REQUEST_CHANGES**

The previous schema-layer mismatch is fixed: `prepare_isolated_worker()` now returns a single object suitable for `artifact["local_processor"]`, and the verifier hard-gates `resolved_tokenizer_binding`.

However the new direct-PASS regression exposes a more serious correctness problem: the pre-import helper manufactures the post-construction read-only evidence before any processor construction has occurred.

## HIGH — `after_assets` is fabricated from the pre-construction snapshot, so PASS can occur before processor construction

In `tools/g0/collect_r09_b2_p3_gpu_inventory.py`, `prepare_isolated_worker()` does:

```python
before["before_assets"] = before["required_assets"]
before["after_assets"] = before["required_assets"]
```

Both values are therefore the same pre-import/pre-construction snapshot. No second `local_processor_record()` is performed after processor construction.

The verifier then accepts:

```python
processor.get("before_assets") == processor.get("after_assets") == assets
```

as `processor_package_read_only=true`.

The newly added unit test explicitly embeds the helper output directly into a nominal PASS artifact and expects the verifier to return PASS. That means the current contract can prove "processor package unchanged after construction" without any construction or post-construction observation having happened.

This violates the previously frozen read-only requirement and makes future PASS evidence semantically unsound.

### Required fix

Separate precondition evidence from post-construction evidence.

1. `prepare_isolated_worker()` may record only pre-import/pre-construction facts:
   - canonical path;
   - required-assets snapshot;
   - offline environment + observed values;
   - resolved tokenizer binding;
   - `before_assets`.

   It must **not** populate `after_assets`.

2. Add a distinct post-construction/finalization step inside the future isolated worker that, after the approved processor construction attempt, performs a fresh read-only `local_processor_record()` and records `after_assets` from that new observation.

3. Future PASS verifier must require actual post-phase evidence. A precondition-only record must not be able to PASS `processor_package_read_only`.

4. Add regression coverage:
   - helper/precondition output embedded directly into an otherwise PASS artifact -> verifier **FAIL**;
   - missing `after_assets` -> FAIL;
   - changed post snapshot -> FAIL;
   - finalized equal independent post snapshot -> structurally PASS for this check.

5. When processor construction is later implemented, the same resolved tokenizer config object/effective resolved values used by the production construction path must be the values recorded in `resolved_tokenizer_binding`; a separately fabricated matching dict is not sufficient execution evidence.

## Accepted in this round

- helper output is now at the same `local_processor` nesting expected by the verifier;
- `resolved_tokenizer_binding` is auditable in the artifact;
- PASS hard-gates `repository is None`, `revision is None`, and `tokenizer_type == canonical_path`;
- remote repository/revision binding is rejected statically;
- no GPU/HF/Transformers/processor/model construction or runtime execution was added.

## Remaining run blockers

Even after this schema fix, `APPROVE_TO_RUN_GPU_ONLY_P3_GATE` still requires the exact isolated-worker implementation/order review and actual production DCP persistent-membership inspection. Symbol-only DCP binding remains insufficient.

## Scope

Still not authorized:
- GPU execution;
- HF/Transformers import for the worker run;
- processor/model construction;
- model/checkpoint/VAE/data/dataloader loading;
- forward/backward/optimizer/scheduler step;
- DCP save/load;
- B2-T, P4/P5, training/eval/inference/closed-loop/SR/multi-GPU/long training/backend freeze/Global/Agent/RL.
