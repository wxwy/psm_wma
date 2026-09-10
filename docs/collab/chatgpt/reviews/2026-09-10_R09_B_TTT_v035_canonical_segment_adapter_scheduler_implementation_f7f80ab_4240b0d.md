# ChatGPT 独立 Canonical Segment Adapter/Scheduler CPU/static Authority Closure Review

Formal reviewed pair:
- root implementation SHA: `f7f80ab70649aead3e822726ff248c5d409d346c`
- child/Gitlink SHA: `4240b0d174bba7a8784c5264670c2a471d1c0abb`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-ADAPTER-SCHEDULER-CPU-STATIC-IMPLEMENTATION`
- approved design pair: root `4522466880221a64cac77b602e903652d180ccb5` / child `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`
- frozen design chain: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.2.md` + `v0.3.md`
- prior ChatGPT implementation review: `docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_adapter_scheduler_implementation_6fc0d11_8609147.md`
- request/bookkeeping commit observed: `4fabdb57663e31cbb8f6ae5405b9edbfae39f325`; request SHA does not replace the formal pair.

Verdict: `REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py:241)`

## Incremental closure against prior review

The remediation is narrow and remains inside the two approved child files. The prior formal pair was `6fc0d11 / 8609147`; the new child delta is only the scheduler contract module and adjacent test.

The following prior blockers are materially closed at production-contract level:

- **dynamic-slot continuation:** bound continuation lookup no longer requires the immutable chronology row to already carry the runtime slot id; it resolves by category / episode / source / `cursor+1` and then binds the exact successor row to the current stable slot via `bind_slot(slot_id)`;
- **direct attempt-1 construction through normal public API:** `CanonicalGAWindowPlan` now rejects `attempt=1` without the internal authority marker, and the transaction is the normal issuer of that marker; attempt-1 cannot retry again;
- **phantom terminalization:** `terminalize()` now requires `0 <= member_index < len(plan.members)` and exact `member_index == len(completed_members)`;
- the previous queue/continuation separation, same-member reservation, projected rollover, exact FIFO cached reconcile, unequal-count objective, and shared-backward witness remain intact;
- no production binding / real I/O / GPU / trainer / config / checkpoint scope was added.

One batch-window lifecycle bug remains.

## Current blockers

### 1. HIGH — post-backward reconcile is not bound to the exact current member's backward

**Location:** `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py:241` (`CanonicalBatchWindowTransaction.mark_reconciled`).

**Root cause:** `backward_started` is a window-level boolean that becomes `True` after the first `mark_backward_started()` and is never cleared or replaced with the identity/index of the member whose backward is active. Therefore this legal-looking sequence is incorrectly accepted:

```python
tx.mark_backward_started(0)
tx.mark_reconciled(0)
tx.mark_reconciled(1)   # succeeds although member 1 never called mark_backward_started(1)
```

After member 0 reconciles, `backward_started` remains `True`; `mark_reconciled(1)` only checks the boolean plus `member_index == len(completed_members)`, so member 1 can cross the post-backward atomic reconcile boundary without its own backward-start transition.

The same state model also permits duplicate `mark_backward_started(i)` calls for the same not-yet-reconciled member because there is no exact current-backward-member owner.

**Violated frozen contract:** approved v0.2 §2/§4/§6 and §7 item 2/4: each native `[B,T]` member must execute exactly one native outer backward before that exact member's all-row atomic reconcile; live scheduler/runtime state may advance only after the corresponding successful backward boundary.

**Exact acceptance:** replace the global-only phase witness with an exact member lifecycle, e.g. `active_backward_member: int | None` plus a separate `ever_backward_started` retry guard (or equivalent state machine):

1. `mark_backward_started(i)` succeeds only when `i == len(completed_members)` and no other backward member is active;
2. `mark_reconciled(i)` succeeds only when `active_backward_member == i`, then clears the active member before advancing to the next index;
3. after `mark_reconciled(0)`, `mark_reconciled(1)` without `mark_backward_started(1)` must fail closed with no transaction/scheduler mutation;
4. duplicate `mark_backward_started(i)` before reconcile must fail closed;
5. the existing first-member-only pre-backward retry prohibition must remain window-global (`ever_backward_started`/equivalent), so clearing the per-member active marker must not re-enable retry;
6. terminalization remains exact-current-member and preserves the current slow-grad-clear/suppress semantics.

### 2. MEDIUM — Evidence still misses the exact fixed continuation path and the per-member backward negative

**Location:** `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler_test.py`.

The submitted test delta proves normal direct `replace(plan, attempt=1)` forgery rejection, second-retry rejection, and phantom terminal index rejection. It does not directly prove:

- a fresh episode whose catalog placeholder slot differs from the runtime free slot is admitted to that free slot, remains nonterminal, and the next frozen member resolves its `cursor+1` continuation then re-binds it to the same runtime slot; and
- after member 0 reconcile, member 1 cannot reconcile until member 1 has explicitly entered its own backward-start phase.

The first is tests/Evidence-only because the current source implementation is structurally correct for slot-neutral continuation. The second must be added alongside the HIGH fix above.

**Exact acceptance:** add CPU/static public-path fixtures for both cases. For the continuation fixture, freeze the plan before live mutation and assert exact episode/category/source/cursor/slot identity across fresh admission -> continuation; for the lifecycle fixture, assert `mark_reconciled(1)` fails before `mark_backward_started(1)`, then succeeds only after that exact call.

## Scope / current disposition

Current blockers: **1 HIGH production-contract + 1 MEDIUM Evidence**.

The request reports `14 PASS`, Ruff and diff-check PASS. These are treated as submitted Evidence and were not independently rerun by this reviewer.

Only narrow CPU/static remediation inside:
- `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py`
- `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler_test.py`

is authorized. No production binding, producer/packer/model-forward/dataset/manifest/config/optimizer/checkpoint changes, real I/O, CUDA/GPU, torchrun, runtime sidecar, LIBERO4IN1, training/evaluation/inference are authorized.

Any remediation creates a new child SHA and therefore requires a new root formal pair for fresh review. Reserved success literal remains:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_SEGMENT_ADAPTER_SCHEDULER_CPU_STATIC`.
