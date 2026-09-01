# R09-B2 P3 construction-witness re-review

- Review request root: `27fe7bdab822e7e9630d9f261342493046c4e410`
- Reviewed implementation root: `349715c9ef5f3d0a141e4c9edb7614f8c2ee3670`
- Submodule/Gitlink: `0af5d53900ec169f43104d4fdf1827ad6691600d`
- Scope: root-side static worker/verifier hardening only; no GPU/HF/processor/model construction authorization.

## Verdict

**REQUEST_CHANGES**

The previous self-filled boolean witness was removed, but the new construction witness is still not bound to the actual production processor construction path.

## HIGH — arbitrary `Callable` can manufacture a valid construction witness

`run_isolated_worker_processor_construction(record, construct_processor)` accepts any zero-argument callable. If it returns any non-`None` object, the helper records:

- `phase_trace=[offline_env_applied, binding_validated, processor_constructed, post_snapshot_taken]`
- a SHA256 of the already-declared resolved binding
- the returned object's Python type string

The verifier then only requires that trace, binding hash, a non-empty `processor_type`, and unchanged before/after assets.

This does not prove the worker actually executed the production processor constructor. The committed regression demonstrates the bypass directly: it calls `run_isolated_worker_processor_construction(record, lambda: object())`, and the verifier subsequently PASSes.

At the reviewed submodule revision, the production construction path is `OmniMoTModel.set_up_tokenizers()`, specifically `self.vlm_processor = lazy_instantiate(self.vlm_config.tokenizer)`. The current witness is not tied to that callsite/symbol or to a fixed production wrapper that invokes it.

### Required fix

Do not let an arbitrary caller-supplied callable define the production construction witness. Before claiming this blocker closed, make the approved isolated-worker implementation itself own a fixed production constructor path. For example:

1. after offline env + local binding preconditions, invoke the reviewed production tokenizer/processor construction path from fixed source code (or a fixed wrapper whose exact source is included in provenance);
2. bind the witness to the reviewed constructor identity/callsite and exact resolved tokenizer config;
3. only after that real constructor returns a non-null production processor may the worker record the post snapshot;
4. verifier must hard-require the expected production constructor identity/wrapper identity and matching binding hash, not merely any non-empty `processor_type`.

Negative regression requirements:

- `lambda: object()` / arbitrary callable must not be able to produce PASS;
- wrong constructor identity must FAIL;
- wrong resolved binding must FAIL;
- precondition-only evidence must FAIL;
- only the fixed reviewed production constructor path + correct binding + independent unchanged post snapshot may satisfy the construction-witness gate.

## Accepted from this round

- post snapshot is taken after the supplied callable returns;
- phase ordering is represented explicitly;
- binding hash is cross-checked against the resolved binding;
- before/after asset equality remains required;
- no GPU/HF/model/processor construction was executed in this submission.

## Remaining scope

No authorization for GPU execution, HF/Transformers import, processor/model construction, weights/VAE/data/dataloader access, DCP I/O, forward/backward/optimizer/scheduler step, B2-T/P4/P5, training/eval/inference/closed-loop/SR/multi-GPU/long training/backend freeze/Global/Agent/RL.

The separate unresolved pre-run requirement for actual production DCP persistent-membership inspection also remains.
