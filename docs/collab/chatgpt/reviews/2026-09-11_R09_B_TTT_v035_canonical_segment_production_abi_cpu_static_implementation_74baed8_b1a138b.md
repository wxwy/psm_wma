# R09-B TTT v0.3.5 Canonical Segment Production ABI CPU/static Implementation Review

## Formal target

- Root formal implementation SHA: `74baed85688c84aa42e9eb3fb00077665267b588`
- Child/Gitlink SHA: `b1a138b79bdc2d4dc40b978ea34094512a07d378`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ABI-CPU-STATIC-IMPLEMENTATION`
- Requested verdict literals: `APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCTION_ABI_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Frozen authority: `PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_abi_implementation_design_v0.3.md` + non-superseded v0.2 clauses, with the already-approved later registered-owner and post-backward-commit supersessions retained.
- Prior same-Gate review: `docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_segment_production_abi_cpu_static_implementation_b0df057_f6a660f.md`.

Independent root inspection confirms that formal root `74baed85688c84aa42e9eb3fb00077665267b588` updates the `cosmos-framework` Gitlink from `f6a660f73043c0fe0c6ba4230c1b6a68f4120cfd` to exactly `b1a138b79bdc2d4dc40b978ea34094512a07d378`; the child commit is reachable. This is therefore a new formal pair and received a fresh incremental review.

## Incremental review result

The child remediation changes the scheduler/adapter plus focused CPU/static tests. Source inspection finds the two prior production defects corrected:

1. `CanonicalBatchScheduler.freeze_plan()` now records exact frozen plan identity, and `validate_frozen_admission()` requires the exact plan object, exact next frozen member and current live `before` scheduler state.
2. `CanonicalProductionAdapter.scan()` applies that admission before frontier/core scan for attempt-0 and reuses original frozen admission for typed retry/recovery.
3. First-member attempt-1 now requires a consumed typed retry authority: `consume_retry()` revalidates live scheduler admission and registers the exact retry request one-shot; `scan()` rejects an unconsumed/foreign retry request, revalidates live admission again, and consumes that exact scan authority.

Accordingly the prior HIGH-1/HIGH-2 **production root causes are CLOSED** in this formal pair. I found no replacement production blocker in the reviewed delta.

The terminal-frontier half of prior HIGH-3 is also **CLOSED**: current Evidence performs a real terminal `commit_success()` and asserts retirement of the exact slot while preserving the other slot.

However, two Evidence-only HIGH blockers remain. Gate closure is therefore not proven.

## Verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py:330)`

Current blockers: **2 HIGH, both Evidence-only**. Production blockers: **0**.

---

## HIGH-1 — Evidence-only: exact registered production owner -> adapter.scan -> backward witness still uses fake authority

**Location**: `cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py:330` (`test_registered_owner_scan_backpropagates_to_the_exact_registered_slow_parameters`).

### Root cause

The new witness names itself a registered-owner scan witness, but it constructs fresh `LocalEvidenceEncoder` / `ContinualTTTLocalMemoryCore` objects and then manually installs them under:

`SimpleNamespace(net=SimpleNamespace(local_memory_runtime=SimpleNamespace(...)))`.

It then obtains the adapter, scans and backpropagates. This proves graph connectivity for manually assembled objects, but it does **not** compose the already-separate production registration witness with the actual scan/backward path. A future regression in production `build_net()` registration/ownership could still leave this test green.

The prior review explicitly required:

`production-registered encoder/core -> production lookup -> actual adapter.scan() -> graph-connected loss/backward -> gradients on those exact same registered slow Parameter objects`.

The reviewer contract also rejects `SimpleNamespace`/fake authority as a substitute for real production authority when the contract is about registered ownership.

### Why current Evidence does not close it

The test does correctly assert gradients on encoder parameters and the required core K/Q/V/slot-query/W0 parameters, but the owner itself is reconstructed by the fixture. Therefore the missing link is still **production registration -> those exact objects**, not differentiability.

### Exact acceptance

Add one direct CPU/static witness that obtains the encoder/core through the actual production static registration/build-net path (or another exact production registration constructor already accepted by the frozen Gate), then:

1. resolve the canonical adapter through `_canonical_production_adapter_from_model()`;
2. prove `adapter.encoder/core` are the same registered Python objects;
3. execute a scheduler-admitted `adapter.scan()`;
4. backpropagate from the scan/local-token graph;
5. assert finite non-null gradients on those exact registered encoder/core slow `Parameter` objects, including required W0/K/Q/V/slot-query groups;
6. do not reconstruct the registered owner with `SimpleNamespace`, fake modules or copied trainable parameters.

---

## HIGH-2 — Evidence-only: scheduler-admission / attempt-1 negative matrix is not yet a direct causal witness of the frozen fail-closed boundary

**Locations**:

- `cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py:79` (`test_adapter_scan_rejects_reconstructed_frozen_plan_before_frontier_or_core_scan`)
- `cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py:500` (attempt-1 retry witness block)

### Root cause

The production source now contains the required checks, but the remediation Evidence only adds/strengthens a subset of the prior review's frozen direct negatives:

- reconstructed/equal-by-value plan rejection;
- pre-consume direct attempt-1 scan rejection;
- one-shot capability consumption / legal retry success.

The prior exact acceptance also required direct CPU/static fail-closed witnesses for the scheduler-admission dimensions (foreign scheduler; stale live scheduler frontier/frozen transition; reordered/copied member around otherwise exact authority) and for attempt-1 lineage/staleness after capability mint (stale before consume/scan; copied/foreign retry request; duplicate consumed-request scan/replay; post-backward retry, in addition to second retry).

Those direct causal witnesses are not present in the current targeted test file. In particular, searching the target test shows no retry stale-after-mint witness and no reordered admission witness.

Also, the reconstructed-plan test asserts unchanged scheduler snapshot, empty `_scan_requests`, and empty frontier state, but it does not instrument the core scan seam. Thus it does not itself prove the frozen requirement of **zero core scan**: a regression that calls core scan before raising could evade these postconditions if it leaves those containers unchanged.

### Violated frozen acceptance

Prior same-Gate HIGH-1/HIGH-2 exact acceptance froze these negative witnesses specifically so Evidence is causally sensitive to authority/order regressions, not merely to final bookkeeping state. Production source correctness does not waive that Evidence requirement.

### Exact acceptance

Add focused CPU/static negatives, using real scheduler/typed authorities, that cover the missing cases above. At each relevant pre-scan rejection boundary assert:

- scheduler/live frozen transition unchanged;
- frontier unchanged;
- transaction unchanged;
- scan bookkeeping unchanged;
- an instrumented production core-scan seam/counter was not entered.

For retry, explicitly include scheduler staleness introduced **after capability mint** and prove rejection both at the appropriate consume/scan boundary; prove duplicate/foreign/reconstructed request authority cannot scan; prove post-backward retry cannot create a second path. Do not manufacture authority via private sets/dicts.

---

## Closed prior findings

- Prior HIGH-1 production scheduler-admission defect: **CLOSED in source**.
- Prior HIGH-2 production attempt-1 capability bypass/staleness defect: **CLOSED in source**.
- Prior HIGH-3 terminal frontier retirement half: **CLOSED by direct terminal commit witness**.
- Prior HIGH-3 exact registered same-graph half: **OPEN as HIGH-1 Evidence-only above**.

## Evidence statement

I treated the request's recorded `28 passed`, Ruff, `py_compile`, child/root diff-check results only as supporting information; I did not use pass counts as Gate closure. I independently inspected the current production admission/retry control flow and the new focused witnesses. Other reviewer votes were not used as authority.

## Scope

This review is bound only to formal pair `74baed85688c84aa42e9eb3fb00077665267b588 / b1a138b79bdc2d4dc40b978ea34094512a07d378` and the exact CPU/static Gate above. It authorizes no real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, native real forward/backward, optimizer/scheduler step, training, evaluation, inference, runtime sidecar, mid-episode resume, or LIBERO4IN1.
