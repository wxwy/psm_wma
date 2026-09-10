# ChatGPT 独立 Canonical Segment Adapter/Scheduler CPU/static Queue-Authority Remediation Review

Formal reviewed pair:
- root implementation SHA: `6fc0d111756177e60b06325c8d400dc6a25972ef`
- child/Gitlink SHA: `86091472fd9a49e0b5b8a35d7797abb2d70b4fa8`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-ADAPTER-SCHEDULER-CPU-STATIC-IMPLEMENTATION`
- approved design pair: root `4522466880221a64cac77b602e903652d180ccb5` / child `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`
- frozen design chain: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.2.md` + `v0.3.md`
- prior ChatGPT implementation review: `docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_adapter_scheduler_implementation_7481c5c_1005ef6.md`
- request/bookkeeping commit observed: `c615315c412bd79ac6017518a5f3780cda3106a0`; later review-handoff/poll commits are bookkeeping only and do not replace the formal pair.

Verdict: `REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py:367)`

## Incremental closure against prior review

This remediation is substantial and remains inside the exact two-file child whitelist. The following prior findings are materially improved or closed:

- fresh episode queue is now separated from continuation chronology through `_queue_for()`, and queue permutations range only over `cursor==0` / `consumer_step_start==0` fresh entries;
- fresh queue order is canonicalized by `(source_digest, episode_id)` and duplicate fresh provenance is rejected;
- free-slot admission binds the selected fresh episode to the chosen slot rather than requiring a pre-bound fresh slot;
- one B>1 member now reserves queue state sequentially across its slots, preventing duplicate same-position admissions;
- `freeze_plan()` performs projected-only rollover at a safe projected member boundary and caches exact projected transitions for FIFO live reconcile;
- the old plan-level `retry_first_member_pre_backward()` method was removed;
- batch transaction `mark_backward_started()` / `mark_reconciled()` now reject negative/out-of-range indices and seal after the final member;
- the test suite now contains a same-category two-free-slot multi-member frozen plan with projected rollover, FIFO exact reconcile, out-of-order no-mutation, and genuine unequal-count/shared-backward evidence.

Those are real closures. Two authority gaps remain.

## Current blockers

### 1. HIGH — dynamically admitted episode cannot reliably continue on its assigned stable slot

**Location:** `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py:367` in `ProjectedSchedulerState._admit()`; related `CatalogRow.bind_slot()`.

**Root cause:** fresh queue entries are correctly made slot-independent at admission by selecting an episode and calling `bind_slot(slot_id)`. After that commit, the stable runtime identity owns the newly selected slot. However, the continuation path searches the immutable catalog with:

```python
item.identity.slot_id == slot_id
and item.identity.category == stable.category
and item.identity.episode_id == stable.episode_id
and item.identity.source_digest == stable.source_digest
and item.identity.cursor == stable.cursor + 1
```

The continuation catalog row therefore has to have been pre-created with the exact runtime slot that happened to receive the episode. That is inconsistent with the new slot-independent fresh episode queue: the queue episode may be admitted to any currently free slot, but its later chronology row is not rebound to that slot.

Concrete legal case: an episode whose catalog fresh/continuation rows were authored with placeholder/canonical `slot_id=0` is admitted to free `slot_id=1`. The fresh row succeeds because `bind_slot(1)` rewrites it. On the next projected member, exact continuation for the stable slot 1 fails because the catalog's cursor+1 row still carries slot 0. The only workaround would be to pre-expand continuation rows for every possible runtime slot, which is not the frozen episode-chronology model and is not required/validated anywhere.

**Violated contract:** v0.3.5 addendum §3.2/§4 and approved v0.2 §4-§5: stable slot ownership is created by scheduler admission, then the same episode/source advances `cursor+1` on that slot until terminal. Episode queue identity is not intrinsically tied to a future slot before admission.

**Exact acceptance:** continuation lookup must resolve the unique chronology successor by episode/category/source/cursor independently of the catalog's placeholder slot and then bind that continuation row to the current stable runtime slot (or introduce an equivalently exact slot-neutral chronology key). Reject ambiguous/missing successors. Add CPU/static evidence where an episode whose catalog rows originate with one placeholder slot is admitted to a different free slot and then successfully projects exact cursor+1 on that new stable slot; wrong episode/source/cursor must fail before mutation.

### 2. HIGH — attempt-1 remains forgeable outside the batch transaction; terminalization still accepts phantom future members

**Location:** `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py:171` (`CanonicalGAWindowPlan.attempt`) and `:249` (`CanonicalBatchWindowTransaction.terminalize`).

**Root cause:** removing the public plan retry method closes the obvious bypass, but it does not make the transaction the sole attempt-1 authority. `CanonicalGAWindowPlan` remains a public frozen dataclass whose constructor accepts `attempt=1`; any caller holding the original members/denominator/GA can directly construct or `dataclasses.replace(..., attempt=1)` without a transaction-issued capability. No consumer can distinguish this forged attempt-1 from the one returned by `CanonicalBatchWindowTransaction.retry_first_member_pre_backward()`.

The same lifecycle still has a second exactness gap: `terminalize()` checks only `member_index < len(completed_members)` and does not require `member_index < len(plan.members)` or `member_index == len(completed_members)`. A transaction with no completed members can therefore accept `terminalize(99, code)` or skip directly to a later frozen index, mutating the window into a terminal state for a member that cannot be the current failure site. The request states phantom indices are rejected, but this method does not enforce it.

**Violated contract:** approved v0.2 §6/§7 item 5 and the prior review acceptance: attempt-1 may arise only from the attempt-0 first-member pre-backward transaction path; later/post-backward failure must be tied to the exact current frozen member and no alternate retry authority may exist.

**Exact acceptance:** make attempt-1 carry an exact one-shot transaction-issued authority/capability that ordinary plan construction cannot satisfy, or otherwise make the plan constructor fail closed for externally minted attempt-1. The transaction must be able to validate that authority when an attempt-1 window is opened. Also change `terminalize()` to accept only the exact current frozen member (`member_index == len(completed_members)` and within `[0, len(plan.members))`). Add negatives for direct `CanonicalGAWindowPlan(..., attempt=1)` / `replace(..., attempt=1)` without authority, attempt-1 second retry, `terminalize(len(plan.members), ...)`, and skipping directly to a later member.

### 3. MEDIUM — current Evidence does not expose the two remaining authority bypasses

**Location:** `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler_test.py`, especially the multi-member and batch-window lifecycle fixtures.

**Root cause:** the new tests successfully close much of the previous Evidence gap: same-category B>1 queue reservation, projected rollover in one frozen plan, FIFO/out-of-order reconcile, unequal count, and shared backward are now directly exercised. But they do not cover the production-contract failures above:

- the multi-member rollover fixture terminalizes its fresh episodes; it never admits a nonterminal episode to a slot different from the catalog placeholder and then proves exact bound cursor+1 continuation;
- the retry test checks that the old plan method is absent, but never attempts a direct constructor/`replace(..., attempt=1)` forgery;
- phantom rejection is tested for `mark_backward_started(2)`, not for `terminalize()`; `terminalize()` remains independently permissive.

**Violated contract:** contract → behavior → evidence must exist for the actual stable-slot continuation and transaction-only retry/failure authority, not only neighboring methods.

**Exact acceptance:** after fixing HIGH-1/HIGH-2, add the direct public-path fixtures listed above. Keep the existing multi-member projected-rollover/FIFO/backward evidence; those are useful and should remain.

## Scope / current disposition

Current blockers: **2 HIGH production-contract + 1 MEDIUM Evidence**.

The implementation remains correctly limited to:
- `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py`
- `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler_test.py`

No production binding, producer/packer/dataset/model-forward/config/optimizer/checkpoint, real I/O, CUDA/GPU, torchrun, runtime sidecar, LIBERO4IN1, training/evaluation/inference is authorized by this verdict. The request's reported `24 passed`, Ruff, `py_compile`, and dual-repo `git diff --check` results are treated as submitted Evidence and were not independently rerun by this reviewer.

Only narrow CPU/static remediation of the two current authority gaps and their direct tests is authorized. Any new child SHA requires a new root formal pair and fresh implementation review. Reserved success literal remains:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_SEGMENT_ADAPTER_SCHEDULER_CPU_STATIC`.
