# GPT independent Design Gate — Evaluation V2 Phase B r1 Multi-Sim / Session-safe Transactional Batch (2026-10-29)

## 0. Formal decision and immutable source target

**VERDICT: `REQUEST_CHANGES` — Phase B r1 DESIGN / isolated symbolic CPU protocol Gate only.**

**This is not a finding against the previously approved Phase A production implementation.** The proposed architecture in the document is predominantly aligned with the Owner's direction, but its explicitly supplied, tested **executable protocol model contradicts two core frozen safety invariants**. The current 29 green synthetic tests do not close these invariants. Resolve the narrow design/protocol test findings below, produce a **new Formal Design Root SHA** and stop for GPT incremental review; **do not edit production Root/Child or start Phase B production.**

| Identity | Exact frozen value |
| --- | --- |
| Current Formal **Design Root** | `fac029c83eb94fdafcc26d030ca5942542d740a3` |
| Formal Child / Root Gitlink | `d2c1bda62880dbeee196f70945e5bc430b73f4b6` |
| Isolated design candidate | `v3-eval-v2-batch-b-design-20261029` |
| Previous Phase A **implementation** (unchanged `APPROVE_CODE` only) | Root `fd7e43f6630a436ab3d83edcd3ce9d1516b342d1` / Child `d2c1bda62880dbeee196f70945e5bc430b73f4b6` |
| Design doc | `docs/build/PSM-WMA_V3_EvalV2_PhaseB_MultiSim_Transactional_Batch_Design_r1_2026-10-29.md` |
| Protocol model/test | `tools/v3/eval_v2_batch_design/protocol_model.py`, `protocol_model_test.py` |
| Author handoff | `docs/collab/codex/reviews/2026-10-29_V3_EvalV2_PhaseB_MultiSim_Batch_Design_r1_author_handoff.md` |
| Evidence path | `docs/collab/codex/evidence/2026-10-29_eval_v2_phase_b_design_author_cpu/` on the isolated candidate; later documentation/bookkeeping HEAD is **not** Formal Design Root |

**Fresh remote identity proof:** fetched V3 and the candidate separately, fetched exact Formal Design Root commit and its Git tree, verified gitlink mode `160000` and exact Child. Comparing Root Git trees at Phase A `fd7e43f6` and current design `fac029c8`, `scripts/`, `configs/`, `third_party/` and Child are byte-identical tree/gitlink SHAs. Formal Design Root changes new design, isolated prototype/tests and SESSION/TODO only, not production. Do not confuse documentation HEAD `377489716751b2785acf3e4bb985436657e78e6d` with Formal Design SHA.

Reviewed current and frozen Owner scopes: `docs/collab/chatgpt/requests/2026-10-28_V3_EvalV2_Dynamic_SimSlots_LocalTTT_Batch_Owner_Implementation_Directive.md` §4, previous D1–D5 Owner contract, previous exact Phase A Code Gate. The historical Stage2 F1 allegation remains explicitly **withdrawn** and is unrelated to the findings below.

## 1. Positive design assessment — no reason to redesign the whole architecture

The frozen design correctly separates `G` selected GPUs, `N` Task classes, `M` physical Sim processes/GPU and `B` max policy microbatch, with a permanent model Server per used GPU and separate real physics processes. It retains the Episode-major D5 same-round barrier and Task/Episode/Attempt binding; N=1 cannot fill a multi-Task batch within one round, which the document acknowledges.

The proposed server data plane correctly rejects the unsupported shortcut `max_sessions=M` / serial `predict_policy` loop: the frozen production `action_policy_server_robocasa.py:1028–1035` still refuses required-Local batch, while `generate_samples_from_batch(..., seed=[...], _local_memory_prefixes=(...))` plus `memory_prefix.py` have per-sample carriers. One native invocation is not one diffusion neural forward. Model-owned Local scan, immutable per-session W0/fast state, exact raw15→env12, sampling provenance, D4 admission before sessions and media/SR separation are preserved in the **design intent**, not yet actual production code.

The proposed single publication owner for Fast+Visual+Frontier+Response, per-ticket canonical idempotency, cache replay after lost HTTP response, per-Session generation fencing, atomic all-or-none committed batch and owner-scoped process death recovery are appropriate architecture. The following findings concern the missing/inconsistent **design executable state-machine authority**, not an allegation of already deployed GPU defects.

## 2. Current blocking findings

### B-D1 — HIGH — positive Session end/reset ACK while a sealed inference transaction is still in flight

- **Exact file:line:** `tools/v3/eval_v2_batch_design/protocol_model.py:104–116` (`ProtocolModel.reset`), `:148–191` (`ProtocolModel.execute`); `tools/v3/eval_v2_batch_design/protocol_model_test.py:110–116` (`test_cancel_between_generation_and_publication_fences_whole_batch`).
- **Independent reachable interleaving:** `execute([A,B])` seals/prepares both, calls the fake vector generator and validates both responses. Its `before_publish` hook executes `model.reset(lease_A)`, which immediately removes A's state and returns `True` (positive cleanup ACK) even though the original A+B transaction has not reached COMMITTED/ABORTED and has not released its in-flight ownership. The subsequent original-bundle/ownership check aborts publication, but **the reset ACK has already been delivered before transaction quiescence**. The test calls this a 'cancel' test even though it uses the positive `reset()` API.
- **Frozen-contract conflict:** design `docs/build/...PhaseB...r1...md:78–91,110–113` states `QUEUED→SEALED→...→COMMITTED/ABORTED`, and explicitly says *Reset ACK only after pending work is absent*, with cleanup proven before physical Slot reuse. Owner Phase B directive §2 likewise requires positive Session cleanup ACK before subsequent Episode/Task assignment. This protocol witness presently conflates *request cancellation* with *fully completed state cleanup*.
- **Risk:** a coordinator can reuse a Sim Slot for another Task/Episode on the basis of an ACK while the old session remains owned by an unfinished batch; the model is incapable of representing the required pending/sealed/generating drain barrier. An uninterruptible real GPU kernel is an even stronger reason not to ACK early.
- **Minimum accepted remediation:** distinguish `cancel_requested` from `session_end_ack` with explicit pending/sealed/in-flight membership. An end request during sealed/generating/pre-commit work must **not** immediately return positive cleanup; it must defer until all affected in-flight transactions reach ABORTED/COMMITTED and are released (or fail closed/quarantine Server if not safely drainable). Test both orders: end before/while/after prepare/generate/precommit and after commit, including lost ACK replay and other batch participants' intact state. Use a dedicated cancellation hook, **not `reset()` as a fake cancellation signal**. Demonstrate that Root cannot give the Slot another Episode before positive cleanup/quiescence.

### B-D2 — MEDIUM — queued-only capacity ledger loses in-flight Slot reservation after flush

- **Exact file:line:** `tools/v3/eval_v2_batch_design/protocol_model.py:195–238`, specifically `BatchQueue.add:205–221` checks only `self.rows`, and `BatchQueue.pop:223–238` removes selected tickets without recording any in-flight reservation. Current `protocol_model_test.py:179–209` validates duplicate/backpressure only while tickets remain queued.
- **Independent reachable counterexample:** add `Request(slotA, frontier0)` to the queue; let `pop(t>wait)` return A for execution (A has **not** committed or aborted). Now `add(Request(slotA, frontier1))` is accepted because `self.rows` is empty; an identical A submission is also treated as a new queue ticket rather than attaching to the existing in-flight ticket. Physical Slot capacity and queue+in-flight byte accounting have been released prematurely.
- **Frozen-contract conflict:** design `docs/build/...PhaseB...r1...md:49–60` requires *one unique queued/**inflight** inference ticket per physical Slot*, `<=M` total active tickets/GPU, bounded queue+in-flight bytes and duplicate HTTP reattachment. §4–§5 require a stable ticket through SEALED/PREPARED/GENERATED/VALIDATED/COMMITTED and safe replay, not a second submission of an already sealed request.
- **Risk:** duplication/out-of-order frontier, undercounted memory/credit and two active requests from the same physical Slot, even while the fake queue shows within-capacity counts. This is **design/evidence-only**, not a demonstrated fault of existing Phase A production.
- **Minimum accepted remediation:** freeze an explicit ticket registry and per-Slot reservation spanning `QUEUED→SEALED/INFLIGHT→terminal/ack`, with a complete transition/credit-release contract. After flush, same-key/same-payload retry must join the in-flight ticket; changed payload or new frontier from that Slot must be rejected until old ownership is released; byte/slot credits cannot be reissued while its model transaction is running. Include deterministic fake-clock counterexamples at `after_pop_before_prepare`, `during_generation`, `after_commit_before_delivery`, `abort`, `timeout` and one restarted epoch. For the immutable committed replay case, the old request may be served from the cache, but never regenerated.

**Both findings can be closed with a narrow modification to the r1 DESIGN/isolated symbolic model and its tests**; no Phase A production source change is indicated. If Codex changes the contract instead of modeling the existing frozen authority, explicitly justify that change for a new Owner decision; do not silently relax end-ACK or outstanding ticket limits.

## 3. Evidence and source controls

- Fetched `final/junit.xml`: 29 testcases/0 failures/0 errors/0 skipped, total `0.084s`. Fetched `final/pytest.log`: `29 passed in 0.08s`. Author records Ruff0.12.7 check/format and AST3 PASS. These are **original author CPU logs**. GPT did NOT re-run tests in the author's environment and no GPU/tensor/native sim was executed.
- Independently verified **6/6 Design Root source bindings** (SESSION, TODO, design MD, protocol init/model/tests) against exact GitHub Git Blob IDs.
- Independently verified **16/16 frozen production source-audit Git Blob bindings** against the actual Phase A Root/Child frozen SHAs, including runtime, scheduler/store, Local online/adapter, Policy Server, native generator and memory-prefix; confirmed production Root trees/Child Gitlink unchanged. Author artifact SHA manifest is present, **not individually rehashed in full**.
- The protocol uses tuples/integers/fake vector and fake clock. 29 green tests prove their actual assertions, **not** real session in-flight reset/queued+inflight ownership, torch Fast Weight isolation, model Batch mask/seed shape, HTTP concurrency, renderer/EGL, media or native throughput. Current B-D1/B-D2 show two safety properties are not correctly represented by the claimed design evidence even at symbolic level.

## 4. Required re-review target and boundary

**Formal verdict: `REQUEST_CHANGES`.** Phase B Design Gate remains OPEN on `fac029c8/d2c1bda6`. The proposed architecture direction is retained; no need to redesign W0 math, D1–D5, or off-mode/V1 behavior.

**Codex authorized remediation scope:** on isolated `v3-eval-v2-batch-b-design-20261029` only, correct the *design contract where needed* and the symbolic protocol/tests to prove B-D1 and B-D2. Supply targeted negative RED evidence where feasible, final full design-protocol CPU JUnit, Ruff/format/AST, frozen source and artifact hashes and a **new Formal Design Root SHA** (Child remains `d2c1bda6` unless justified new changes are separately authorized). STOP for independent GPT incremental Design Gate. Do not use a later doc/Evidence SHA as the Formal target.

**Still PENDING independently:** Phase A DS_PRO clean independent CPU; any Phase B production implementation/merge; real GPU/Cosmos/DCP/RoboCasa/EGL/900; training/Checkpoint/Vendor/old431. No current review gives permission for these activities. Previous Phase A `APPROVE_CODE` at `fd7e43f6/d2c1bda6` stays unchanged.

This verdict is **formal only after** this Detailed Review AND a matching newest append-only `docs/collab/chatgpt/CODEX_INBOX.md` entry are both committed and independently read back.
