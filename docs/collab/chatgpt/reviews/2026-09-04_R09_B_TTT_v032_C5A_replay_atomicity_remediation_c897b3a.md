# ChatGPT re-review — R09-B TTT v0.3.2 C5A replay/atomicity remediation @ c897b3a

Date: 2026-09-04

## Verdict

**REQUEST_CHANGES**

Formal Gate:
`G0-R09-B-TTT-V032-C5A-CHRONOLOGY-OWNER-SEGMENT-IMPLEMENTATION`

Formal implementation pair:
- root remediation SHA: `c897b3a5b7e2992f00f959a316158a5e0dc21c03`
- child/Gitlink: `7d22b63cba11d642214a15c8a3ccd0bb81a9865b`
- frozen C5A design authority: `bbe0444eaa8c08f05ca5a5eea0e331253d263592`
- immediately preceding reviewed child: `4ae44604eeb63f2ebc258f8d73fb2d0a12e82e76`

Review-start `origin/V2`/remote V2 was locked to exact root `c897b3a5b7e2992f00f959a316158a5e0dc21c03`; its parent is ChatGPT review bookkeeping `40b10798ad473e5b406428863efda71d3d69657a`, and its Gitlink is exactly `7d22b63cba11d642214a15c8a3ccd0bb81a9865b`.

Scope check:
- child `4ae4460... -> 7d22b63...` is exactly one commit ahead;
- only `cosmos_framework/model/generator/mot/c5a_owner_segment.py` and adjacent `c5a_owner_segment_test.py` changed;
- root-side change advances SESSION/TODO + Gitlink only;
- no production/runtime Cosmos wiring, config/optimizer/checkpoint/trainer/inference/parallelization, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 scope drift was found.

## Closed relative to 4ae4460

The current remediation materially closes several prior blockers:
- **post-materialize unseen admission is now fail-closed**: exact S replay is returned first, but a new unseen S is rejected unless the pending phase remains `COLLECT_RAW`;
- **replay now carries explicit numerical metadata** through detached `ReplayRecord(value, shape, present)` for both pending and committed records;
- **backward failure no longer opens commit**: `backward_and_mark()` changes phase only after `loss.backward()` returns successfully;
- **stateful `done_before` cannot silently reset committed owner chronology**: a stateful owner must pass the explicit owner reset/epoch transition before a `done_before=True` materialization;
- prior exact-issued registry, epoch-bound capability, repeated-materialize guard and true B>1 scan/gather-scatter remain present.

## Findings

### 1. HIGH — the admission capability still does not authenticate the frozen completed-causal provenance class

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:27-68`
- `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py:20-35`

**Root cause:** `AdmissionCapability` now authenticates exact owner/source identity/timestep/source bytes/schema/epoch via an authority registry, but it has no `provenance_class` (or equivalent trusted completed-causal provenance field). `AdmissionAuthority.issue()` will issue a capability for any non-empty tensor dict satisfying only type/timestep/epoch checks. The later `LocalEvidenceEncoder` ABI restricts field names/shapes, but that is not equivalent to proving that the payload came from the frozen R08 completed-causal source rather than future/GT/substituted source construction.

**Contract violation:** v0.6 §2 explicitly freezes R08 capability authentication of `provenance_class=R08_COMPLETED_CAUSAL` and requires history/future/GT substitution to reject before C5. Exact byte authentication of an unauthenticated provenance source is insufficient.

**Acceptance condition:** bind an authority-issued provenance class/source-handle class into the exact issued record and require `R08_COMPLETED_CAUSAL` at `admit()` before chronology/Encoder/C5. Add fail-before-work fixtures for wrong/missing provenance class and future/GT-class substitution, in addition to owner/source/timestep/schema/dtype/shape/bytes field tampering.

### 2. HIGH — `BACKWARD_OK` can still be obtained from an unrelated loss; the phase is not bound to the current materialization graph

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:238-246`
- `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py:50-56, 145-174`

**Root cause:** moving `loss.backward()` inside `backward_and_mark()` correctly closes the prior caller-only boolean/phase transition and correctly leaves the phase closed on thrown backward. However, the wrapper accepts any scalar tensor whose `backward()` succeeds; it never proves that `loss` is connected to the current segment's live materialized tokens/graph. The tests explicitly call `backward_and_mark(..., torch.tensor(0.0, requires_grad=True))` in lifecycle and N/terminal cases, which succeeds without traversing the C5A materialization graph and still enables commit. `test_outer_backward_gradients...` first performs a separate external materialization loss backward, then opens the authoritative phase using a second unrelated zero loss.

**Contract violation:** v0.6 §3 freezes `MATERIALIZE_PENDING -> ordinary outer backward on the rematerialized segment graph -> commit/detach`, with Encoder and C5 slow/Q/K/V/slot/W0 gradient reachability. A successful unrelated backward is not the required segment backward and permits committed chronology/state promotion without the frozen outer-loss graph.

**Acceptance condition:** make the backward authority graph-bound to the current materialization. For example, retain a materialization-specific live output/witness and require the supplied loss to have autograd reachability to it, or make the wrapper own a callback/loss constructed from the live materialized output. An unrelated leaf loss must reject and leave phase/C unchanged. A successful bound outer backward must prove finite/nonzero gradients to each frozen parameter group: LocalEvidenceEncoder and C5 key/query/value projections, slot queries, and W0 fast-in/fast-out slow parameters.

### 3. HIGH — the submitted `17 passed` evidence still does not satisfy the explicit v0.6 closure matrix, and several current assertions are weaker than the recorded claims

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py:20-215`

**Root cause / missing direct acceptance evidence:**
- no `StatelessLocalReplayReadout` spy proving zero calls on the TTT materialization path;
- hostile admission only directly tests modified `source_bytes` and forged `_seal`; it does not test exact-issued owner/source identity/timestep/schema/dtype/shape/provenance mutations;
- committed replay is tested only immediately after commit, not after chronology advances while proving lookup-before-allocation and zero extra write;
- pending/committed replay tests do not directly assert `grad_fn is None`, clone/detach independence, shape/presence integrity after pending destruction;
- outer-gradient test asserts `any(...)` nonzero gradient across all encoder+core parameters, not finite/nonzero reachability for every frozen Encoder and C5 Q/K/V/slot/W0 group;
- the N=1/3/16 parameterization tests nonterminal full `N`; the terminal branch tests `r=0` only when N=1 and `r=N-1` for N=3/16. It does **not** directly test terminal `r=N` and does not span the frozen terminal remainder grammar sufficiently to support the root claim that `r=0/r<N/r=N` is fully covered;
- reset/epoch coverage rejects one stale capability, but same owner/source identity/timestep across epoch with same bytes and changed bytes plus old-epoch retry/new-epoch visibility ordering is still not directly demonstrated;
- rollback assertion after abort is weak (`all(key[0] == "a" for key in _identity_index)`) and does not snapshot/compare committed C, chronology, replay and reverse-index state before/after the failed pending transaction.

**Contract violation:** v0.6 §4 explicitly makes this CPU acceptance matrix part of closure, not optional evidence.

**Acceptance condition:** complete the frozen matrix with direct behavioral assertions, including stateless spy=0; full hostile admission/provenance matrix; pending and chronology-advanced committed graph-free replay; exact rollback snapshots; per-group gradients; terminal `r=0`, representative `0<r<N`, and `r=N` for the relevant N variants; epoch same-identity same/changed-byte cases; and retain true B>1 permutation/row-mismatch/valid/done coverage. Re-run the isolated CPU selector and report the exact pass count plus py_compile and child/root diff-check.

## Evidence note

Repository status records isolated CPU pytest = `17 passed`, plus py_compile and diff-check PASS. Those commands were not independently rerun in this connector environment and are treated as submitted evidence. The source/contract findings above independently block closure.

## Required next submission

Remediation remains restricted to the already-approved isolated C5A CPU boundary unless scope is explicitly reopened. A new child/root implementation SHA requires a fresh same-SHA review.

Still prohibited:
- production/runtime Cosmos wiring;
- config/optimizer/checkpoint/trainer/inference/parallelization;
- GPU/CUDA/torchrun and real model/data/cache/checkpoint I/O;
- training/evaluation/inference;
- P4/P5, B2-T and LIBERO4IN1.
