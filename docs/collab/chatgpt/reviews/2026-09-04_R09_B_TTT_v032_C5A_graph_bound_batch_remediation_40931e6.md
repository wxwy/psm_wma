# ChatGPT re-review — R09-B TTT v0.3.2 C5A graph-bound batch remediation @ 40931e6

Date: 2026-09-04

## Verdict

**REQUEST_CHANGES**

Formal Gate:
`G0-R09-B-TTT-V032-C5A-CHRONOLOGY-OWNER-SEGMENT-IMPLEMENTATION`

Formal implementation pair:
- root remediation SHA: `40931e62acc91c225ebd178856443a807ea6ccce`
- child/Gitlink: `be121a492c30f6eb9d322d09d4ad11461775e031`
- frozen C5A design authority: `bbe0444eaa8c08f05ca5a5eea0e331253d263592`
- immediately preceding reviewed pair: root `ddddee444dccac72d5a6a5ddac4c8030e485acfa` / child `9ea54b5484839bd9399029433ffed40831a36ba5`

Review-start remote `V2` was locked to exact root `40931e62acc91c225ebd178856443a807ea6ccce`; its Gitlink is exactly `be121a492c30f6eb9d322d09d4ad11461775e031`.

Scope check:
- child `9ea54b5... -> be121a4...` is exactly one commit ahead;
- only `cosmos_framework/model/generator/mot/c5a_owner_segment.py` and adjacent `c5a_owner_segment_test.py` changed;
- root `ddddee4... -> 40931e6...` only advances SESSION/TODO, the Gitlink, and carries the prior ChatGPT detailed review;
- no production/runtime Cosmos wiring, config/optimizer/checkpoint/trainer/inference/parallelization, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 scope drift was found.

## Closed relative to ddddee4 / 9ea54b5

The current remediation closes the prior production blocker and several acceptance gaps:
- `materialize_many()` now returns a stack derived from each participating owner `pending.witness[-1]`, so a loss built only from the public batch result reaches every owner witness leaf accepted by `backward_and_mark_many()`;
- the corresponding test now uses only `result = materialize_many(...) -> batch_loss = f(result) -> backward_and_mark_many(...)`, with no private pending-witness construction;
- exact-issued capability mutation coverage now includes owner key, source identity, timestep, schema, shape and dtype in addition to the already-covered source bytes/seal/provenance;
- committed replay is now exercised after chronology advances, with explicit zero-extra-write, `grad_fn is None`, shape and presence assertions.

No new production algorithm defect was found in the current child delta.

## Finding

### HIGH — the frozen v0.6 explicit closure matrix is still incomplete; remaining work is tests-only unless stronger fixtures expose a defect

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py:1-305`
- frozen authority: `docs/build/PSM-WMA_R09_B_TTT_v032_c5a_chronology_owner_segment_design_v0.6_2026-09-04.md:7-25`

**Remaining direct acceptance gaps:**
1. **Stateless control isolation:** there is still no `StatelessLocalReplayReadout` spy proving exactly zero calls on the C5A/TTT materialization path. v0.6 §1 explicitly requires this.
2. **Pending replay no-graph record:** committed replay now proves `grad_fn is None` after chronology advance, but the exact pending replay path after materialization still does not directly assert `ReplayRecord.value.grad_fn is None` together with value/shape/presence integrity and zero extra C5 write.
3. **Epoch same-identity reuse boundary:** current reset coverage rejects a stale old-epoch capability and then uses a different source identity (`s2`). It still does not directly prove that a fresh new-epoch capability may reuse the same owner + same source identity + same timestep without stale replay/conflict, for both same source bytes and changed source bytes, while the old-epoch capability rejects before Encoder/C5.
4. **Exact rollback snapshot:** abort/failure coverage still does not snapshot and compare the committed owner fast state, `_last_timestep`, committed replay, reverse identity index and epoch before/after a failed/aborted pending transaction. The frozen contract requires failed/aborted work to leave committed C unchanged and not leak cross-segment authority.

**Contract violation:** v0.6 §§1,3,4 make these CPU checks explicit closure requirements ("必须显式覆盖"), not optional diagnostics. The current root records `29 passed`, but test count alone does not substitute for the named acceptance matrix.

**Acceptance condition:** a tests-only remediation in `c5a_owner_segment_test.py` is sufficient unless the stronger fixtures expose a production defect. Add direct fixtures for the four items above, retain the public multi-owner graph-bound path and current hostile/chronology/permutation/gradient/terminal coverage, then report the exact isolated CPU selector count plus py_compile and child/root diff-check.

## Evidence note

Root status records isolated CPU pytest = `29 passed`, plus py_compile and diff-check PASS. Those commands were not independently rerun in this connector environment and are treated as submitted evidence.

## Required next submission

Remediation remains restricted to the already-approved isolated C5A CPU boundary. If only the four fixtures above are added, no production-code change is expected. Any new child/root implementation SHA still requires fresh same-SHA review.

Still prohibited:
- production/runtime Cosmos wiring;
- config/optimizer/checkpoint/trainer/inference/parallelization;
- GPU/CUDA/torchrun and real model/data/cache/checkpoint I/O;
- training/evaluation/inference;
- P4/P5, B2-T and LIBERO4IN1.
