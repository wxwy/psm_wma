# R09-B TTT v0.3.5 Canonical Segment Production ABI CPU/static Implementation Review

## Formal target

- Root formal implementation SHA: `b0df0572dfb28b8ec3fb82fe2ca09ca533251d50`
- Child/Gitlink SHA: `f6a660f73043c0fe0c6ba4230c1b6a68f4120cfd`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ABI-CPU-STATIC-IMPLEMENTATION`
- Frozen design authority: `PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_abi_implementation_design_v0.3.md` + non-superseded v0.2 clauses.
- Later explicit supersessions honored in this audit:
  - active-TTT registered owner path is the later-approved `net.local_memory_runtime.evidence_encoder / ttt_core`, not the older v0.3 literal `local_history_runtime.encoder / recurrent_backend`;
  - Canonical Native Forward/Loss v0.4 explicitly supersedes the earlier pre-backward commit-minting/failure-disposal wording and keeps post-backward `prepare_commit()` as the current authority.

Independent root inspection confirms that formal root `b0df0572...` resolves `cosmos-framework` exactly to `f6a660f...`; the child commit is reachable.

## Incremental scope

The immediate child delta `55d6b330..f6a660f` is tests-only and changes the production-integration fixture from the superseded owner path to the current registered-owner path. That narrow change is directionally correct.

For the actual Gate closure, however, the frozen implementation baseline `3a078f2..f6a660f` spans intervening separately authorized Gates. I therefore reviewed the current relevant production ABI and tests under the composite authority above rather than treating the three-line fixture update as sufficient evidence of closure.

## Verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:665)`

Current blockers: **3 HIGH** — **2 production + 1 Evidence-only**.

---

## HIGH-1 — production: `scan()` is not admitted by the exact scheduler `freeze_plan()` authority

**Location**: `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:665` (`CanonicalProductionAdapter.scan`).

### Root cause

`scan()` validates only:

- `request.transaction.plan is request.plan`;
- member index bounds;
- `request.plan.members[index] is request.member`;
- duplicate request id;
- `member.validate_batch()`.

It never proves before frontier/core scan that:

- `request.plan is scheduler.freeze_plan(...)`'s exact returned plan;
- the request member is the scheduler's exact next frozen transition;
- the scheduler live frontier still equals that transition's frozen `before` state.

This is observable in current integration fixtures: `_bound_request_and_carrier()` manually constructs `CanonicalGAWindowPlan(...)` and a `CanonicalBatchScheduler(...)` with no matching `freeze_plan()` transition, yet the adapter accepts the request and scans it.

### Violated frozen contract

v0.2 §3 freezes `CanonicalProductionSegmentRequest.plan` as the scheduler's **exact `freeze_plan()` result** and requires, before scan/forward, exact plan/member/transaction object identity plus live scheduler frontier/exact frozen-transition matching; foreign/reconstructed/stale/reordered requests must fail before scan.

v0.3 §5 retains that attempt-0 requirement: `plan is scheduler.freeze_plan(...) result` with the scheduler frozen transition as the unique admission authority.

### Exact acceptance

1. Add a non-mutating scheduler/request admission validation that can prove the **exact frozen plan identity**, exact member/index, exact next frozen transition and live `before` frontier before any `frontier.state_for()` or encoder/core scan.
2. `CanonicalProductionAdapter.scan()` must use that admission for normal attempt-0 and every legal recovery/retry form, with the later typed retry/suffix authority layered on top.
3. Direct CPU/static negatives must prove zero frontier/scan/scheduler/transaction mutation and zero core scan for:
   - manually reconstructed/equal-by-value plan;
   - foreign scheduler;
   - stale live scheduler frontier/frozen transition;
   - reordered member;
   - plan/member copied/reconstructed around the exact frozen objects.
4. Positive fixtures for this Gate must derive the plan through real `CanonicalBatchScheduler.freeze_plan()` rather than manually manufacturing a plan/scheduler pair that production should reject.

---

## HIGH-2 — production: first-member attempt-1 can bypass the typed retry capability and stale retry is not revalidated pre-scan

**Locations**:

- `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:542` (`consume_retry`)
- `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:665` (`scan`)

### Root cause

`retry_first_member_pre_backward()` preflights the scheduler only when the retry capability is minted. `consume_retry()` then checks static lineage fields, removes the capability id and returns `retry_request`, but it does not:

- revalidate the current live scheduler frozen transition/frontier;
- register the exact returned retry request as the sole one-shot scan authority.

`scan()` capability-gates only suffix recovery (`attempt == 1 and member_index_offset > 0`). A first-member retry has `attempt == 1, member_index_offset == 0`, so the caller can take `capability.retry_request` and call `adapter.scan(...)` **before `consume_retry()`**, bypassing the typed one-shot capability entirely. After minting, a scheduler transition can also become stale and `consume_retry()/scan()` will not reject it until much later `prepare_commit()`.

### Violated frozen contract

v0.3 §5 requires attempt-1 to exist only through the typed `CanonicalProductionRetryCapability`, consumed exactly once, with **all identity/staleness checks before scan/backward**. `foreign/stale/second-retry/member>0/post-backward` must reject pre-scan, with no second admission/transition.

### Exact acceptance

1. Consuming the exact retry capability must revalidate current scheduler admission and mint/register the exact one-shot retry request authority without a second `freeze_plan()` or re-admission.
2. First-member `attempt==1` scan must require that exact consumed retry request and consume its scan authority once; direct access to `capability.retry_request` before `consume_retry()` must fail closed.
3. Direct CPU/static negatives must cover:
   - pre-consume direct scan;
   - copied/reconstructed/foreign retry request;
   - stale scheduler transition/frontier after capability mint but before consume/scan;
   - duplicate scan/replay of the consumed retry request;
   - second retry and post-backward retry.
4. All failures must occur before frontier/core scan and leave scheduler/frontier/transaction/scan bookkeeping unchanged. Legal retry must still reconcile the original frozen transition exactly once and preserve original member objects/denominator/GA/chain.

---

## HIGH-3 — Evidence-only: required exact-registered same-graph and terminal-frontier witnesses are still split/incomplete

**Primary Evidence location**: `cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py:315` plus `canonical_segment_production_adapter_test.py` fast-state tests.

Production source inspection does not currently expose a separate defect here, but the closure Evidence does not directly establish two explicit v0.3 acceptance clauses.

### A. Exact registered encoder/core scan gradient is not directly witnessed

Current tests separately prove:

- adapter lookup object identity;
- production `build_net()` registration under the later-approved `local_memory_runtime` path;
- direct encoder/core differentiability;
- direct frontier fresh-W0 differentiability.

But no direct witness composes these into:

`production-registered encoder/core -> _canonical_production_adapter_from_model() -> actual adapter.scan() -> scan local-token graph/backward -> gradients on those exact same registered encoder/core slow Parameter objects`.

The current integration identity test uses a `SimpleNamespace` owner and performs no scan/backward. The split tests would not necessarily fail if a future adapter-level detach/copy were inserted between exact binding and scan.

v0.3 §3 and §7 explicitly require P2 CPU/static Evidence that canonical scan gradients reach the **exact registered encoder/core slow parameters**.

### B. Terminal fast-state retirement is not directly asserted

The current frontier test directly checks fresh fp32, committed continuation values and slot isolation, but ends at continuation. It does not perform a terminal-success commit and assert that the exact slot/episode/source chain is retired. Downstream suffix/native tests exercise terminal-shaped members but do not directly assert the frozen terminal-frontier postcondition.

v0.3 §4/§7 explicitly require all four fast-state tensors across fresh/continuation/candidate/commit plus terminal retirement, with fp32 and no alias/leak.

### Exact acceptance

Add direct causal CPU/static witnesses that:

1. use the actual production-registered owner objects (or the exact production static build-net construction), obtain the adapter through the production lookup, perform a real canonical `adapter.scan()` on a scheduler-admitted request, backpropagate from the scan/local-token graph, and assert finite/non-null gradients on the exact same registered encoder/core slow `Parameter` objects (including the required W0/K/Q/V/slot-query groups where the frozen graph expects them), with no reconstructed trainable copy;
2. execute a real success commit for a terminal member and assert the exact frontier slot is retired, while all candidate/committed fast-state tensors are fp32 and other slots remain unchanged/non-aliased.

This blocker is Evidence-only; the production blockers are HIGH-1 and HIGH-2 above.

---

## Closures / non-blockers retained

- The `f6a660f` fixture migration to `local_memory_runtime.evidence_encoder/ttt_core` matches the later approved Feature/Config owner refreeze; the older v0.3 path literal is superseded and is **not** a blocker.
- Canonical activation is fail-closed before legacy preparation for enabled TTT; No-Local control remains separated.
- Current adapter lookup caches/binds the selected encoder/core object identities and enforces canonical feature config.
- The current fast-state implementation is fp32-oriented and fresh W0 is differentiable in source; the missing issue above is direct closure Evidence, not a contrary source finding.
- The later Native Forward/Loss v0.4 explicitly authorizes post-backward `prepare_commit()` and typed `abort_commit()` pre-mutation failure disposal. I therefore do **not** carry forward the older pre-backward minting wording as a blocker.
- Current native CPU/static trainer route retains pre-scan hard-stop against enabled scaler / real optimizer and the exact weighted objective/single-backward downstream logic already reviewed in its own Gate.

## Evidence statement

I read the formal request's recorded targeted CPU/static pytest/Ruff/`py_compile`/diff-check results but did not independently rerun them. Test pass counts do not close HIGH-1/HIGH-2 because current fixtures permit non-authoritative manually constructed plan/scheduler requests; they also do not supply the direct v0.3 witnesses described in HIGH-3.

## Scope

This verdict applies only to the formal pair and Gate above. It authorizes no real data/cache/checkpoint I/O, CUDA/GPU, torchrun, actual training/evaluation/inference, optimizer/scheduler execution, runtime sidecar, or LIBERO4IN1.
