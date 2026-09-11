# R09-B TTT v0.3.5 Canonical Segment Production ABI CPU/static Implementation Review

## Formal target

- Root formal implementation SHA: `59d0848ff5d77023365a0f540fcdf1f562500583`
- Child/Gitlink SHA: `331622d41ac0c76fe2f14479fb67ceb607b8aef9`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ABI-CPU-STATIC-IMPLEMENTATION`
- Requested verdict literals: `APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCTION_ABI_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Prior same-Gate review: `docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_segment_production_abi_cpu_static_implementation_3f4c76f_218484e.md`.

Independent root inspection confirms that formal root `59d0848ff5d77023365a0f540fcdf1f562500583` changes the `cosmos-framework` Gitlink from `218484efbd1363633c379a21f82499a237267ca9` to exactly reachable child commit `331622d41ac0c76fe2f14479fb67ceb607b8aef9`. The child delta is one tests-only commit touching only `cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py`. No production source changed. The prior pair had zero production blockers and one Evidence-only HIGH, so this review is limited to that frozen evidence acceptance.

## Incremental closure result

Four of the five remaining evidence gaps are now directly closed:

1. reconstructed/equal-by-value plan rejection now runs through `_assert_pre_scan_rejected_without_core_scan()`, which instruments the production core-scan seam and snapshots scheduler state/frozen transitions, transaction, frontier and scan bookkeeping;
2. a real two-member frozen plan now submits the exact later `plan.members[1]` while the scheduler still expects member 0, proving genuine out-of-order authority rejection before core scan with zero mutation;
3. copied retry-request identity is now tested only after successful `consume_retry()`, and the exact registered retry authority is asserted preserved across the copied request rejection;
4. scheduler staleness is now introduced after successful `consume_retry()` and before `scan()`, proving the scan-time admission revalidation rejects before core scan while preserving the exact one-shot retry authority.

These additions directly close prior acceptance items 1–4. Production behavior remains unchanged and no new source defect was found.

However, prior acceptance item 5 remains incomplete.

## Verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py:604)`

Current blockers: **1 HIGH, Evidence-only**. Production blockers: **0**.

---

## HIGH — Evidence-only: second-retry and post-backward retry still lack the frozen full zero-mutation witness

**Primary locations**:

- `cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py:604` — second `retry_first_member_pre_backward(request)` rejection in `test_adapter_retry_preserves_original_frozen_transition_exactly_once`;
- `cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py:678` — post-backward rejection in `test_adapter_retry_rejects_stale_copied_duplicate_and_post_backward_paths_before_core_scan`.

### Root cause

The prior formal review explicitly froze acceptance item 5: strengthen **second-retry** and **post-backward retry** negatives so that, across each rejected call, the test snapshots and proves unchanged:

- scheduler live snapshot;
- exact frozen-transition sequence;
- transaction snapshot;
- frontier state;
- `_scan_requests` and `_scan_results` bookkeeping;
- retry authority/capability bookkeeping where applicable.

The current child does not add those assertions at either boundary.

For the second-retry case, the test still records only `scheduler_before = scheduler.snapshot` before an earlier pre-consume scan rejection, then calls `retry_first_member_pre_backward(request)` again and only asserts that it raises. It does not snapshot/compare the frozen-transition tuple, transaction, frontier, scan result bookkeeping, or retry-capability state specifically across this second-retry rejection.

For the post-backward case, the test marks backward started, calls `retry_first_member_pre_backward(post_backward_source)`, then only asserts `_retry_capabilities == set()`, `_scan_requests == set()`, and empty frontier. It does not snapshot/compare scheduler live state, frozen transitions, transaction snapshot, `_scan_results`, or the full adapter authority state across the rejected call.

These are not source defects: current production still appears to reject both boundaries correctly. The missing issue is direct causal Evidence for the frozen zero-mutation contract.

### Exact acceptance

A tests-only remediation is sufficient:

1. immediately before the second-retry rejection, snapshot scheduler state, exact `_frozen_transitions`, request transaction snapshot, frontier state, `_scan_requests`, `_scan_results`, `_retry_capabilities`, and `_retry_scan_requests`; after rejection assert all are byte/value/identity-equivalent as appropriate;
2. do the same immediately before the post-backward retry rejection after `mark_backward_started(0)`; the transaction snapshot used as the baseline should therefore already include backward-started state, and the failed retry call must add no further mutation;
3. do not manufacture authority by mutating private containers; reading them for zero-mutation evidence is acceptable because the authority itself must still have been created through the public typed production path.

If these witnesses pass without exposing a source defect, the remaining Evidence-only blocker can close.

---

## Closed findings retained

- Scheduler exact-plan / exact-next-transition / live-frontier production blocker: CLOSED.
- First-member attempt-1 consumed typed capability/staleness production blocker: CLOSED.
- Terminal fast-state retirement Evidence: CLOSED.
- Exact production-registered encoder/core -> adapter.scan -> backward gradients: CLOSED.
- Reconstructed-plan zero-core/full-zero-mutation witness: CLOSED in this pair.
- Exact later frozen-member out-of-order witness: CLOSED in this pair.
- Post-consume copied retry identity witness: CLOSED in this pair.
- Post-consume pre-scan stale retry witness: CLOSED in this pair.
- Remaining blocker: only second/post-backward retry full zero-mutation evidence above.

## Evidence statement

I treated the request's recorded adapter CPU/static `12 passed`, Ruff, `py_compile` and child diff-check as supporting information but did not independently rerun them. The verdict is based on independent inspection of the formal Gitlink, the one-file child delta, the current test body and the exact acceptance frozen in the immediately prior ChatGPT review. MM/Kimi votes were not used as authority.

## Scope

This review is bound only to formal pair `59d0848ff5d77023365a0f540fcdf1f562500583 / 331622d41ac0c76fe2f14479fb67ceb607b8aef9` and the exact synthetic CPU/static Gate above. It authorizes no real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, native real forward/loss/backward, optimizer/scheduler stepping, runtime sidecar, training, evaluation, inference, distributed execution, matched smoke, or LIBERO4IN1.
