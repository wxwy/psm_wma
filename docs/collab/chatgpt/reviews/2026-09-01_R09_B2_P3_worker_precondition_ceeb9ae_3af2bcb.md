# R09-B2 P3 isolated-worker precondition review

- Review request root: `ceeb9aed86687e17dc4495c34c227f174d0b7526`
- Reviewed implementation root: `3af2bcb8836a67ddade774e7504bd58e37c3074e`
- Submodule/Gitlink: `0af5d53900ec169f43104d4fdf1827ad6691600d`
- Scope: root-side static collector/test implementation only; no GPU/HF/Transformers/processor/model construction authorization.

## Verdict

**REQUEST_CHANGES**

The new static checks are directionally correct: local processor assets are required, remote repository/revision are rejected, tokenizer_type must equal the canonical local Edge path, and the offline environment helper reads back the values it applied. The remote-binding negative test is also useful.

However the worker-precondition evidence contract is not yet compatible with the verifier's PASS schema, so this cannot yet be treated as the reviewed isolated-worker precondition path.

## HIGH — `prepare_isolated_worker()` returns evidence at the wrong schema level and does not persist the verified tokenizer binding

`tools/g0/collect_r09_b2_p3_gpu_inventory.py` currently returns:

```python
{
    "local_processor": before,
    "observed_offline_environment": observed,
    "before_assets": before["required_assets"],
}
```

But `tools/g0/verify_r09_b2_p3_gpu_inventory.py` reads PASS evidence from inside `artifact["local_processor"]`:

- `local_processor.observed_offline_environment`
- `local_processor.before_assets`
- `local_processor.after_assets`

Therefore a future worker that directly uses the helper output cannot satisfy the verifier without an additional undocumented reshaping step. More importantly, the helper verifies `repository`, `revision`, and `tokenizer_type` but does not record the resolved tokenizer binding in the auditable `local_processor` record, and the verifier has no hard-gate for that binding.

This leaves the exact production-processor binding non-auditable even if the helper was called.

### Required fix

Make the worker-precondition helper and verifier share one explicit schema. Prefer returning/updating a single `local_processor` object containing at least:

- `canonical_path`
- `required_assets`
- `offline_environment`
- `observed_offline_environment`
- `before_assets`
- `resolved_tokenizer_binding` with exact `repository`, `revision`, `tokenizer_type`

Then make future PASS verification require:

- `repository is None`
- `revision is None`
- `tokenizer_type == canonical_path`
- `observed_offline_environment == offline_environment`
- before/after package evidence under the same `local_processor` object.

Add a regression proving that the helper-produced evidence can be embedded directly into a minimal PASS artifact without reshaping, and that a remote repository/revision or mismatched tokenizer_type fails the verifier, not only the helper.

## Additional note

Applying the offline environment after the local-binding validation is not itself a blocker here because this helper imports no HF/Transformers code. For run approval, however, the actual isolated worker must invoke this precondition before any HF/Transformers/model import and record machine-checkable phase/order evidence.

## Scope

Still not authorized:
- GPU execution;
- HF/Transformers/processor/model construction;
- checkpoint/model-weight/VAE/data/dataloader loading;
- forward/backward/optimizer/scheduler step;
- DCP save/load;
- B2-T, P4/P5, training/eval/inference/closed-loop/SR/multi-GPU/long training/backend freeze/Global/Agent/RL.
