# R09-B2 P3 post-phase evidence re-review

- Review request root: `b9d6b9eec56c3e7593f7e7e3d184dcdc19e2aceb`
- Reviewed implementation root: `f21e4a14fc0d5d1316b55dd72de75360560cfd29`
- Submodule/Gitlink: `0af5d53900ec169f43104d4fdf1827ad6691600d`
- Scope: root-side static collector/verifier/test hardening only; no GPU/HF/processor/model construction authorization.

## Verdict

**REQUEST_CHANGES**

The previous fake `after_assets = before_assets` assignment has been removed, and precondition-only evidence now fails until a separate finalize function populates post-phase fields. However the core machine-evidence problem is not closed.

## HIGH — `finalize_isolated_worker_processor_record()` can assert post-construction evidence without any construction witness

`tools/g0/collect_r09_b2_p3_gpu_inventory.py` now separates `prepare_isolated_worker()` and `finalize_isolated_worker_processor_record()`, but `finalize_isolated_worker_processor_record()` merely:

1. re-runs `local_processor_record()`;
2. assigns `after_assets`;
3. sets `post_construction_observed = True`.

It accepts only the mutable record and has no processor instance, construction result, construction phase token, worker phase state, or any other execution-derived witness proving that production processor construction actually occurred between the two snapshots.

The new regression itself demonstrates the bypass: it calls `prepare_isolated_worker()`, verifies FAIL, immediately calls `finalize_isolated_worker_processor_record(record)` with **no processor construction in between**, and then expects verifier PASS.

Therefore `post_construction_observed=True` is still a self-asserted boolean, not machine evidence of post-construction observation.

### Required fix

Before this can be considered closed:

- The future worker must own the phase transition, not an arbitrary caller.
- `prepare` should produce a precondition record and an opaque/internal phase state that cannot be represented as a plain artifact boolean.
- The actual approved production processor construction path must execute between pre and post phases.
- Post-phase evidence must be emitted only by the worker after successful construction of the exact resolved production processor/tokenizer binding already recorded in `resolved_tokenizer_binding`.
- The artifact should record a machine-checkable phase/order trace, e.g. `offline_env_applied -> binding_validated -> processor_constructed -> post_snapshot_taken`, with the construction step populated from the actual worker path rather than caller-supplied JSON.
- Verifier PASS must require the actual construction witness/phase ordering in addition to `before_assets == after_assets == required_assets`.

Required negative regressions:

1. `prepare -> finalize` with no construction step => FAIL;
2. missing construction witness => FAIL;
3. construction witness for a different tokenizer/processor binding => FAIL;
4. correct production binding + actual construction phase + unchanged post snapshot => only then may the processor read-only item PASS.

This does **not** authorize running that construction yet. It only requires the static worker contract to make it impossible for a caller to manufacture post-construction evidence without the real construction phase.

## Accepted

- precondition no longer directly writes `after_assets`;
- missing post phase now fails;
- changed post snapshot fails;
- verifier requires `post_construction_observed is True` plus before/after/required equality;
- no GPU/HF/model/processor construction or checkpoint/data execution was introduced by this reviewed commit.

## Remaining run blockers

Even after this fix, `APPROVE_TO_RUN_GPU_ONLY_P3_GATE` still requires separate review of the exact worker implementation and actual production DCP persistent-membership inspection. No GPU/model/processor construction is authorized by this review.
