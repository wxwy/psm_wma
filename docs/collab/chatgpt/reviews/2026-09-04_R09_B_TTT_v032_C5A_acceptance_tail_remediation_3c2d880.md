# ChatGPT re-review — R09-B TTT v0.3.2 C5A acceptance-tail remediation @ 3c2d880

Date: 2026-09-04

## Verdict

**REQUEST_CHANGES**

Formal Gate:
`G0-R09-B-TTT-V032-C5A-CHRONOLOGY-OWNER-SEGMENT-IMPLEMENTATION`

Formal implementation pair:
- root remediation SHA: `3c2d8808dd04d5d3a7a49aaf3b2236d493994a05`
- child/Gitlink: `87bd7f71ac6eddbcf753f0b2365eea4747145b7b`
- frozen C5A design authority: `bbe0444eaa8c08f05ca5a5eea0e331253d263592`
- immediately preceding reviewed pair: root `40931e62acc91c225ebd178856443a807ea6ccce` / child `be121a492c30f6eb9d322d09d4ad11461775e031`

Review-start remote `V2` was locked to exact root `3c2d8808dd04d5d3a7a49aaf3b2236d493994a05`; its Gitlink is exactly `87bd7f71ac6eddbcf753f0b2365eea4747145b7b`.

Scope check:
- child `be121a4... -> 87bd7f7...` is exactly one tests-only commit;
- only `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py` changed;
- no production `c5a_owner_segment.py` change in this remediation;
- root advances SESSION/TODO + Gitlink and carries the prior ChatGPT review only;
- no production/runtime Cosmos wiring, config/optimizer/checkpoint/trainer/inference/parallelization, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 scope drift was found.

## Closed relative to 40931e6 / be121a4

The current tests-only remediation materially closes most of the prior acceptance-tail finding:
- `StatelessLocalReplayReadout.forward` is spied and proven zero-call on the C5A materialization path;
- pending replay after `valid=False` now proves `present=False` and `ReplayRecord.value.grad_fn is None`;
- stale old-epoch capability rejection plus fresh same-owner/same-source-identity/same-timestep capability admission in epoch 1 is directly covered;
- abort after an already-committed owner now snapshots and compares committed fast state, `_last_timestep`, reverse identity index, epoch and committed-key set;
- production code remains unchanged, and no new production defect was found.

## Finding

### HIGH — three explicit acceptance details from the prior review remain unproven; remediation is still tests-only

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py:248-291`
- prior same-Gate review: `docs/collab/chatgpt/reviews/2026-09-04_R09_B_TTT_v032_C5A_graph_bound_batch_remediation_40931e6.md`
- frozen authority: `docs/build/PSM-WMA_R09_B_TTT_v032_c5a_chronology_owner_segment_design_v0.6_2026-09-04.md`

**Remaining direct gaps:**
1. **Pending replay integrity/zero-write is only partially asserted.** `test_pending_invalid_replay_preserves_presence_and_stateless_readout_is_unused()` proves `present=False` and `value.grad_fn is None`, but it does not assert `tuple(replay.value.shape) == replay.shape`, does not compare the replay value/metadata to the materialized row, and does not snapshot/assert `c5_write_count` is unchanged by the exact pending replay lookup. The prior acceptance condition explicitly required pending replay value/shape/presence integrity plus zero extra C5 write.
2. **Changed-byte fresh-epoch reuse is still missing.** `test_epoch_allows_same_identity_fresh_capability_and_rejects_stale()` covers the fresh epoch-1 capability only with the same source bytes. The prior acceptance condition explicitly required the same owner + same source identity + same timestep across the new epoch for both same bytes and changed bytes, while the old-epoch capability rejects before Encoder/C5. Add a second fresh epoch case whose source bytes differ and prove admission is a new epoch-local row rather than stale replay/conflict.
3. **Backward-failure rollback lacks the exact committed-state snapshot.** `test_abort_exact_snapshot_preserves_committed_owner_state()` proves the abort half. The existing `test_backward_failure_does_not_open_commit_phase()` proves phase/commit rejection, but does not snapshot and compare committed fast state, `_last_timestep`, committed replay, reverse index and epoch before/after the failed backward. The prior acceptance condition required failed/aborted pending work to leave committed C exactly unchanged.

**Acceptance condition:** keep production code unchanged unless these fixtures expose a defect. Add direct tests for the three points above, retain all current v0.6 coverage, rerun the isolated selector and report the exact count plus py_compile and child/root diff-check. If those pass without revealing a production issue, this Gate should be ready for closure review.

## Evidence note

Root status records isolated CPU pytest = `32 passed`, plus py_compile and diff-check PASS. These commands were not independently rerun in this connector environment and are treated as submitted evidence.

Still prohibited until fresh same-SHA closure:
- production/runtime Cosmos wiring;
- config/optimizer/checkpoint/trainer/inference/parallelization;
- GPU/CUDA/torchrun and real model/data/cache/checkpoint I/O;
- training/evaluation/inference;
- P4/P5, B2-T and LIBERO4IN1.
