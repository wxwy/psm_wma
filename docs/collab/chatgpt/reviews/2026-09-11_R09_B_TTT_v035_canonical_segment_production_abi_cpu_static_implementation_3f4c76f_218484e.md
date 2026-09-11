# R09-B TTT v0.3.5 Canonical Segment Production ABI CPU/static Implementation Review

## Formal target

- Root formal implementation SHA: `3f4c76fdfdc70564d40c4e3f66a922924968c315`
- Child/Gitlink SHA: `218484efbd1363633c379a21f82499a237267ca9`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ABI-CPU-STATIC-IMPLEMENTATION`
- Requested verdict literals: `APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCTION_ABI_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Frozen authority: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_abi_implementation_design_v0.3.md` plus the non-superseded v0.2 clauses and the already-approved later registered-owner/post-backward-commit supersessions.
- Prior same-Gate review: `docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_segment_production_abi_cpu_static_implementation_74baed8_b1a138b.md`.

Independent root inspection confirms that formal root `3f4c76fdfdc70564d40c4e3f66a922924968c315` resolves `cosmos-framework` exactly from prior `b1a138b79bdc2d4dc40b978ea34094512a07d378` to `218484efbd1363633c379a21f82499a237267ca9`. The child delta is one tests-only commit touching only:

- `cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py`
- `cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py`

No production source changed in this remediation. The prior pair had zero production blockers and two Evidence-only HIGHs, so this review is limited to whether those Evidence gaps are directly closed and whether the new tests introduce any contrary finding.

## Incremental review result

### Prior HIGH-1 — exact registered production owner -> adapter.scan -> backward: CLOSED

The new `_build_registered_ttt_owner()` witness now executes the actual `OmniMoTModel.build_net()` active-TTT registration branch. Although the surrounding heavyweight base network is reduced with CPU/static stubs, the canonical owner itself is not reconstructed: production `build_net()` creates the real `LocalEvidenceEncoder`, real `ContinualTTTLocalMemoryCore`, wraps them in the registered `net.local_memory_runtime`, and the test obtains those exact registered Python objects from that runtime.

The witness then resolves `_canonical_production_adapter_from_model(model)`, executes a scheduler-admitted `adapter.scan()`, backpropagates from `result.local_tokens`, proves `adapter.encoder/core` are the exact registered objects, and checks finite non-null gradients on all encoder parameters plus core K/Q/V, slot-query and all W0 parameters. This composes the previously split production-registration and graph-connectivity evidence into the required same-object chain.

I therefore close the prior registered-owner Evidence blocker.

### Prior HIGH-2 — scheduler/retry negative matrix: PARTIALLY CLOSED, still HIGH Evidence-only

The new tests materially improve the evidence:

- foreign scheduler, copied member and a publicly reconciled stale scheduler are now passed through `_assert_pre_scan_rejected_without_core_scan()`;
- that helper snapshots scheduler state/frozen transitions, transaction, frontier and scan bookkeeping and instruments the real core-scan seam to prove zero entry;
- stale retry capability before `consume_retry()`, duplicate scan/replay of the consumed exact request, and post-backward retry are now covered;
- no authority is fabricated by writing private capability sets/dicts.

However the prior review froze a direct negative matrix, not only source-level correctness, and several required causal boundaries are still not witnessed directly.

## Verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py:117)`

Current blockers: **1 HIGH, Evidence-only**. Production blockers: **0**.

---

## HIGH — Evidence-only: the frozen scheduler/retry fail-closed matrix is still incomplete at exact authority boundaries

**Primary locations**:

- `cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py:117` (`test_adapter_scan_rejects_reconstructed_frozen_plan_before_frontier_or_core_scan`)
- `cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py:589` (`test_adapter_retry_rejects_stale_copied_duplicate_and_post_backward_paths_before_core_scan`)

### 1. Reconstructed-plan boundary still does not prove zero core scan

The pre-existing reconstructed/equal-by-value plan test remains outside the new `_assert_pre_scan_rejected_without_core_scan()` helper. It checks the scheduler snapshot plus empty `_scan_requests`/frontier, but still does not instrument `core.scan_segment_masked_encoded_many`, snapshot the frozen-transition sequence, snapshot the transaction, or check `_scan_results`.

This is the exact evidence weakness called out in the prior review: a regression that enters core scan before raising could still evade the current reconstructed-plan postconditions.

### 2. Exact reordered/out-of-order frozen member is still absent

The new admission test covers a copied member object, but not an exact member object taken from the same multi-member frozen plan in the wrong next-transition order. These are different authority cases:

- copied member: object identity is foreign even if value-equal;
- reordered member: object identity is genuine and belongs to the exact frozen plan, but is not the scheduler's exact next frozen transition.

The prior acceptance explicitly froze both dimensions. A direct multi-member witness must present the later exact `plan.members[i]` while the scheduler still expects the earlier member and prove rejection before frontier/core scan with zero mutation.

### 3. Retry copied-request witness is currently pre-consume, so it does not test the consumed one-shot identity boundary

The new copied retry case calls:

`replace(copied_capability.retry_request)` -> `adapter.scan(...)`

before `consume_retry()` has registered any retry scan authority. That request would fail merely because no retry capability has been consumed, even if the post-consume exact-request identity guard were later weakened.

The missing direct witness is:

1. mint exact retry capability;
2. consume it successfully, thereby registering the one exact returned retry request;
3. submit a copied/reconstructed/foreign attempt-1 request and prove it cannot scan and cannot consume/erase the exact registered authority;
4. optionally prove the exact returned request remains usable once, so the negative is specifically about identity rather than a dead retry path.

### 4. Staleness is tested before consume, but not after consume before scan

The current stale test mutates/reconciles the scheduler after capability mint and then proves `consume_retry()` rejects. That closes the consume-boundary half.

The prior acceptance also required scan-boundary revalidation. There is still no direct witness that:

1. mints and successfully consumes a retry capability while the original scheduler admission is live;
2. makes the scheduler frozen transition/live frontier stale **after consume but before scan**;
3. calls the exact consumed retry request;
4. proves rejection before core scan, with scheduler/frontier/transaction/scan bookkeeping unchanged and the exact one-shot authority not incorrectly consumed by the failed stale scan.

This matters because production deliberately performs a second `validate_frozen_admission()` inside `scan()` after `consume_retry()`; the current Evidence does not causally protect that second check.

### 5. Second/post-backward retry zero-mutation assertions remain weaker than the frozen acceptance

The existing second-retry and new post-backward-retry checks prove rejection and absence of newly minted retry capabilities, but they do not snapshot and assert the full scheduler frozen transition / transaction / frontier / scan-bookkeeping state across those rejection calls. The prior exact acceptance required zero mutation at these authority failures.

### Violated frozen acceptance

The previous formal review froze direct witnesses for reconstructed/manual/stale/reordered scheduler authority and for retry staleness/foreign-or-copied request/duplicate/second/post-backward boundaries, with zero core scan and zero scheduler/frontier/transaction/scan-bookkeeping mutation at the applicable pre-scan boundaries.

The current production source still appears to implement those checks correctly; this blocker is therefore **Evidence-only**, not a production defect. Test pass counts do not substitute for the missing direct causal cases.

### Exact acceptance

A narrow tests-only remediation is sufficient. At minimum:

1. route the reconstructed-plan rejection through the same zero-core / zero-mutation instrumentation used by the new helper;
2. add a real multi-member frozen-plan test that submits an exact later member out of order and proves zero core/frontier/scheduler/transaction/bookkeeping mutation;
3. after a successful `consume_retry()`, submit a copied/reconstructed/foreign retry request and prove it cannot scan or consume the exact registered one-shot authority;
4. after a successful `consume_retry()`, stale the scheduler before scan and prove the exact retry request is rejected by the scan-time revalidation with zero core scan and no accidental authority consumption;
5. strengthen second/post-backward retry negatives to assert the frozen scheduler transition, transaction, frontier and scan bookkeeping are unchanged.

No production change is requested unless these stronger witnesses expose a source defect.

---

## Closed findings retained

- Scheduler exact-plan / exact-next-transition / live-frontier production blocker: **CLOSED** in the prior pair and unchanged here.
- First-member attempt-1 consumed typed capability/staleness production blocker: **CLOSED** in the prior pair and unchanged here.
- Terminal fast-state retirement Evidence: **CLOSED** in the prior pair.
- Exact production-registered encoder/core -> adapter.scan -> backward gradients: **CLOSED in this pair**.
- Remaining blocker: **1 HIGH Evidence-only**, scheduler/retry direct negative matrix above.

## Evidence statement

I treated the request's recorded adapter `11 passed`, integration `19 passed`, Ruff, `py_compile` and diff-check results as supporting information but did not independently rerun them. I independently inspected the new child diff, the current tests, the production `build_net()` owner registration path, the prior same-Gate review and the frozen design acceptance. Other reviewer votes were not used as authority.

## Scope

This review is bound only to formal pair `3f4c76fdfdc70564d40c4e3f66a922924968c315 / 218484efbd1363633c379a21f82499a237267ca9` and the exact synthetic CPU/static Gate above. It authorizes no real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, native real forward/loss/backward, optimizer/scheduler stepping, runtime sidecar, training, evaluation, inference, distributed execution, matched smoke, or LIBERO4IN1.
