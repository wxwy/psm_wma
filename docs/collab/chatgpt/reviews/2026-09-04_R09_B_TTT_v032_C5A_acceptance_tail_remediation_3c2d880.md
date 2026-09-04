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
- production code remains unchanged in this remediation.

## Findings

### 1. HIGH — `valid=False` rows still advance committed chronology/replay despite zero C5 execution

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:190-245`
- especially `materialize_many()` replay population and `commit()` chronology promotion.

**Root cause:** `scan_segment_many()` receives the row-level `valid` mask and `c5_write_count` increments only by `valid.sum()`, so an invalid row performs zero C5 write. However, after the scan the wrapper still creates a `ReplayRecord` for every pending row, including `valid=False`, and `commit()` unconditionally sets `_last_timestep[owner] = pending.rows[-1].source_timestep` and promotes the whole pending replay/reverse index. Thus an owner row can consume/commit chronology for a transition that did not execute a C5 update. The new test explicitly demonstrates `present=False` for such a row but then stops before checking commit semantics.

**Contract violation:** the frozen v0.6 owner/chronology contract requires one authoritative chronology transition per admitted/materialized causal source and fail-closed owner semantics. A masked-out row cannot silently become an ordinary committed transition while `c5_write_count` proves no C5 work occurred, unless the design explicitly defines `valid=False` as a consumed chronology event with a separate proof model. No such exception is frozen.

**Acceptance condition:** freeze and implement one coherent rule. Preferred: `valid=False` must not advance `_last_timestep`, committed replay or reverse index for that owner and must not be exposed as an ordinary committed source transition. If the intent is instead "consumed but no C5 update", that semantics must be explicitly added to the design with a distinct committed presence/consumed contract before closure. Add a true B>1 row-selective fixture that commits one `valid=True` and one `valid=False` owner and verifies per-owner fast state, `_last_timestep`, replay/index contents and write count.

### 2. HIGH — three explicit acceptance-tail details remain unproven

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py:248-291`
- prior same-Gate review: `docs/collab/chatgpt/reviews/2026-09-04_R09_B_TTT_v032_C5A_graph_bound_batch_remediation_40931e6.md`
- frozen authority: `docs/build/PSM-WMA_R09_B_TTT_v032_c5a_chronology_owner_segment_design_v0.6_2026-09-04.md`

**Remaining direct gaps:**
1. **Pending replay integrity/zero-write is only partially asserted.** The new pending replay test proves `present=False` and `value.grad_fn is None`, but it does not assert `tuple(replay.value.shape) == replay.shape`, does not compare value/metadata to the materialized row, and does not snapshot/assert `c5_write_count` is unchanged by the exact pending replay lookup.
2. **Changed-byte fresh-epoch reuse is still missing.** The new epoch test covers same owner/source identity/timestep with the same source bytes in epoch 1, but not a fresh new-epoch capability with changed source bytes. The old-epoch capability must reject before Encoder/C5 in both cases.
3. **Backward-failure rollback lacks exact committed-state snapshot.** Abort now has a committed-state snapshot, but the failing-backward path only proves phase/commit rejection. It still needs before/after equality for committed fast state, `_last_timestep`, committed replay, reverse index and epoch.

**Acceptance condition:** keep production code unchanged for these evidence items unless stronger fixtures expose another defect. Add direct tests for the three points above, retain all current v0.6 coverage, rerun the isolated selector and report the exact count plus py_compile and child/root diff-check.

## Evidence note

Root status records isolated CPU pytest = `32 passed`, plus py_compile and diff-check PASS. These commands were not independently rerun in this connector environment and are treated as submitted evidence.

## Required next submission

The next remediation must address Finding 1 in production semantics/code (or formally reopen/freeze the design if a consumed-invalid transition is intentional) and complete the remaining evidence in Finding 2. A new child/root implementation pair requires fresh same-SHA review.

Still prohibited until fresh same-SHA closure:
- production/runtime Cosmos wiring;
- config/optimizer/checkpoint/trainer/inference/parallelization;
- GPU/CUDA/torchrun and real model/data/cache/checkpoint I/O;
- training/evaluation/inference;
- P4/P5, B2-T and LIBERO4IN1.
