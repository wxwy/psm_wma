# ChatGPT re-review — R09-B TTT v0.3.2 C5A validity-prefix remediation @ bfae469

Date: 2026-09-04

## Verdict

**REQUEST_CHANGES**

Formal Gate:
`G0-R09-B-TTT-V032-C5A-CHRONOLOGY-OWNER-SEGMENT-IMPLEMENTATION`

Formal implementation pair:
- root remediation SHA: `bfae469715566a0c82ad80a5e58f3227ab2be50a`
- child/Gitlink: `958bb20b96578acc92a6375899855a5b49274e41`
- request/bookkeeping SHA: `44cc88bdba5fb6b3d281b08d649e631d391defce` (not the implementation target)
- frozen C5A design authority: `bbe0444eaa8c08f05ca5a5eea0e331253d263592`
- immediately preceding implementation pair: root `f030e36b3f866e38793533512bfc5bbda9f98743` / child `26b08e8b1a8861ea8903027b6bef3e9eda1509e2`

Review-start remote `V2` was `44cc88b...`; its parent is exact implementation root `bfae469...`. The bookkeeping SHA therefore does not replace the formal implementation target.

Scope check:
- child `26b08e8... -> 958bb20...` is exactly one commit ahead;
- only `cosmos_framework/model/generator/mot/c5a_owner_segment.py` and adjacent `c5a_owner_segment_test.py` changed;
- root `f030e36... -> bfae469...` only advances SESSION/TODO, Gitlink and carries the prior ChatGPT review;
- no production/runtime Cosmos wiring, config/optimizer/checkpoint/trainer/inference/parallelization, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 scope drift was found.

## Closed relative to f030e36 / 26b08e8

The mixed-validity production finding is CLOSED:
- `materialize_many()` now validates each owner row before Encoder/C5 and requires `valid` to form a contiguous prefix;
- `[True,False,True]` raises `ValueError` before C5 work and leaves the pending phase in `COLLECT_RAW` with zero writes;
- legal `[True,True,False]` is materialized and commit promotes only t0/t1, leaving `_last_timestep=1` and no committed replay for t2;
- the all-invalid-owner protection introduced in `26b08e8` remains intact.

No new production algorithm defect was found in the current child delta.

## Finding

### HIGH — the final acceptance-tail evidence explicitly requested in the prior same-Gate review is still incomplete

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py` around the epoch/replay/rollback fixtures (`~250-330`)
- prior review: `docs/collab/chatgpt/reviews/2026-09-04_R09_B_TTT_v032_C5A_invalid_row_chronology_remediation_f030e36.md`

The current child commit adds only the validity-prefix grammar and its direct fixture. It does not add the four remaining acceptance checks that the prior exact-pair review required:

1. **Changed-byte fresh-epoch reuse.** Existing epoch coverage proves stale epoch-0 rejection and fresh epoch-1 admission for the same owner/source identity/timestep using the same source bytes. It still does not prove a fresh new-epoch capability with changed source bytes is accepted as new epoch-local authority rather than replay/conflict.
2. **Backward-failure exact rollback snapshot.** The current failing-backward fixture proves `BACKWARD_OK` is not opened and commit is rejected, but it does not snapshot and compare committed fast state, `_last_timestep`, committed replay values/shape/presence, reverse identity index and epoch before/after the failed backward.
3. **Abort committed replay equality.** The abort snapshot compares committed key sets, chronology/index/epoch and fast state, but not the committed `ReplayRecord` value/shape/presence contents themselves.
4. **Pending replay numerical equality.** Pending replay proves `present`, shape, graph-free value and zero extra C5 write, but does not directly compare `ReplayRecord.value` with the numerical materialized row from which it was cached.

**Acceptance condition:** a tests-only remediation in `c5a_owner_segment_test.py` is sufficient unless these stronger fixtures expose a production defect. Add the four direct checks above, retain the current validity-prefix, B>1/permutation, hostile admission, graph-bound backward, N/terminal, replay and slow-gradient fixtures, rerun the isolated C5A CPU selector, and report the exact pass count plus py_compile and child/root diff-check.

If those checks pass without revealing a production defect, no further production-code change is expected before closure review.

## Evidence note

Root status records isolated CPU pytest=`33 passed`, plus py_compile and diff-check PASS. Those commands were not independently rerun in this connector environment and are treated as submitted evidence.

Still prohibited until fresh same-SHA closure:
- production/runtime Cosmos wiring;
- config/optimizer/checkpoint/trainer/inference/parallelization;
- GPU/CUDA/torchrun and real model/data/cache/checkpoint I/O;
- training/evaluation/inference;
- P4/P5, B2-T and LIBERO4IN1.
