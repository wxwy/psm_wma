# ChatGPT re-review — R09-B TTT v0.3.2 C5A final matrix remediation @ ddddee4

Date: 2026-09-04

## Verdict

**REQUEST_CHANGES**

Formal Gate:
`G0-R09-B-TTT-V032-C5A-CHRONOLOGY-OWNER-SEGMENT-IMPLEMENTATION`

Formal implementation pair:
- root remediation SHA: `ddddee444dccac72d5a6a5ddac4c8030e485acfa`
- child/Gitlink: `9ea54b5484839bd9399029433ffed40831a36ba5`
- frozen C5A design authority: `bbe0444eaa8c08f05ca5a5eea0e331253d263592`
- immediately preceding reviewed pair: root `c897b3a5b7e2992f00f959a316158a5e0dc21c03` / child `7d22b63cba11d642214a15c8a3ccd0bb81a9865b`

Review-start remote `V2` was locked to exact root `ddddee444dccac72d5a6a5ddac4c8030e485acfa`; its Gitlink is exactly `9ea54b5484839bd9399029433ffed40831a36ba5`.

Scope check:
- child `7d22b63... -> 9ea54b5...` is exactly two commits ahead;
- only `cosmos_framework/model/generator/mot/c5a_owner_segment.py` and adjacent `c5a_owner_segment_test.py` changed;
- root `c897b3a... -> ddddee4...` only advances SESSION/TODO status, the Gitlink, and carries the prior ChatGPT detailed review;
- no production/runtime Cosmos wiring, config/optimizer/checkpoint/trainer/inference/parallelization, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 scope drift was found.

## Closed relative to c897b3a / 7d22b63

The current remediation materially closes the prior three findings in part:
- `AdmissionCapability` now binds `provenance_class`, the digest includes it, and `AdmissionAuthority.issue()` only issues `R08_COMPLETED_CAUSAL`; a tampered provenance class is directly rejected before work;
- single-owner materialization now returns a witness-bearing tensor and `backward_and_mark()` requires the supplied scalar loss graph to reach the materialization-specific witness leaf before ordinary `loss.backward()` can open `BACKWARD_OK`;
- terminal `r=N` for N=1/3/16 is now directly covered;
- Encoder, Q, K, V, slot and W0 slow-parameter groups now each have explicit finite/nonzero gradient reachability evidence.

These close the corresponding prior provenance, single-owner unrelated-loss, terminal-full-N and weak-gradient assertions.

## Findings

### 1. HIGH — the public multi-owner materialization output is not bound to the witness graph required by `backward_and_mark_many()`

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:220-234`
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:276-289`
- `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py:102-125`

**Root cause:** `materialize_many()` correctly creates one owner-local `witness_leaf` and `pending.witness = tokens[batch_index] + witness_leaf * 0` for every owner, but its public return remains the raw `tokens[:, -1]`. A normal caller therefore builds the outer loss from a tensor that does not contain any owner witness leaf. `backward_and_mark_many()` then requires the loss to reach every pending `witness_leaf`, so a valid batch loss derived exclusively from the public `materialize_many()` return will be rejected as `backward loss is unrelated to materialized segment`.

The current test avoids this public API contradiction by discarding the returned tensor and constructing `batch_loss` directly from private `runtime._pending_by_owner[*].witness`. That proves the private witness mechanism, not the actual public materialize-many -> loss -> backward-and-mark-many contract.

**Contract violation:** v0.6 §3 freezes one atomic owner-batched materialization followed by the ordinary outer backward on that rematerialized segment graph, then commit/detach. The public owner-batched materialization path must itself supply the graph that the authoritative batched backward accepts.

**Acceptance condition:** make the public `materialize_many()` result graph-bound to all participating owner witnesses (for example, return a stack/view derived from each owner `pending.witness`, preserving the frozen result shape), or redesign `backward_and_mark_many()` so the public materialized result and its authoritative loss binding are the same object/path. Add a test that uses only:
`result = materialize_many(...) -> loss = f(result) -> backward_and_mark_many(owner_keys, loss)`
with no access to private pending witnesses, and proves one successful backward/commit for all owners. Also retain an unrelated-loss rejection fixture and prove no phase/C mutation on rejection.

### 2. HIGH — the explicit v0.6 closure matrix is still incomplete despite the recorded `22 passed`

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py:1-277`
- frozen authority: `docs/build/PSM-WMA_R09_B_TTT_v032_c5a_chronology_owner_segment_design_v0.6_2026-09-04.md:7-25`

**Remaining direct acceptance gaps:**
- no `StatelessLocalReplayReadout` spy proving zero calls on the C5A/TTT materialization path;
- hostile exact-issued capability coverage still does not directly exercise owner change, source-identity change, timestep change and schema/dtype/shape mutation in addition to source-byte/seal/provenance tampering;
- no committed replay after chronology has advanced, proving source-key lookup-before-allocation and zero extra C5 write;
- pending/committed replay still lacks direct `grad_fn is None`, clone/detach independence, shape/presence integrity after pending destruction;
- reset/epoch still lacks same owner + same source identity + same timestep cases across epochs for both same bytes and changed bytes, together with the old-epoch retry/new-epoch visibility rule;
- abort/failure rollback still lacks an exact before/after snapshot proving committed fast state, chronology cursor, committed replay and reverse index are unchanged.

The current delta does close terminal `r=N`, provenance tamper and per-group gradient evidence, but those additions do not satisfy the remaining explicit matrix items above.

**Contract violation:** v0.6 §4 states these CPU tests "必须显式覆盖" before closure.

**Acceptance condition:** add the remaining direct fixtures above within the already-approved isolated C5A two-file CPU boundary; keep the existing true-B>1 permutation/row-mismatch/valid/done, N=1/3/16, terminal and fast-state ownership coverage. Re-run the isolated selector and report the exact count, plus py_compile and child/root diff-check.

## Evidence note

Root status records isolated CPU pytest = `22 passed`, plus py_compile and diff-check PASS. Those commands were not independently rerun in this connector environment and are treated as submitted evidence. The source/contract findings above independently block closure.

## Required next submission

Remediation remains restricted to the already-approved isolated C5A CPU boundary unless scope is explicitly reopened. A new child/root implementation SHA requires a fresh same-SHA review.

Still prohibited:
- production/runtime Cosmos wiring;
- config/optimizer/checkpoint/trainer/inference/parallelization;
- GPU/CUDA/torchrun and real model/data/cache/checkpoint I/O;
- training/evaluation/inference;
- P4/P5, B2-T and LIBERO4IN1.
