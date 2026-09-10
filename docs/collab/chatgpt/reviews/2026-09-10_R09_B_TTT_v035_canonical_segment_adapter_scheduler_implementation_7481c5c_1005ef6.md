# ChatGPT 独立 Canonical Segment Adapter/Scheduler CPU/static Remediation Review

Formal reviewed pair:
- root implementation SHA: `7481c5cb898efefb739fbc61f27cac80007c3b3c`
- child/Gitlink SHA: `1005ef61de8e462b344dba87f2f6545e23af5a1a`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-ADAPTER-SCHEDULER-CPU-STATIC-IMPLEMENTATION`
- approved design pair: root `4522466880221a64cac77b602e903652d180ccb5` / child `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`
- frozen design chain: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.2.md` + `v0.3.md`
- prior ChatGPT implementation review: `docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_adapter_scheduler_implementation_61f469b_355a440.md`
- request/bookkeeping commit observed: `a8fe71041c046c7e9e863e263dd8c25492bbebc0`; later handoff/poll commits are bookkeeping only and do not replace the formal pair.

Verdict: `REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py:342)`

## Incremental closure against prior review

The remediation is material and stays inside the exact two-file child whitelist. Several prior findings are genuinely improved:

- `ProjectedSchedulerState` now carries target distribution, catalog, frozen epoch permutations/positions, and `freeze_plan()` derives members from projected state rather than accepting arbitrary external members.
- `reconcile_after_backward()` now requires the exact cached frozen member object and exact `before` state, so reconstructed/stale/out-of-order members fail before live mutation.
- stable-slot continuation now checks same category / episode / source digest / `cursor+1`.
- free-slot admission now uses weighted deficit and advances projected queue position on committed admissions.
- deterministic next-epoch permutations are generated from the approved SHA-256 byte contract and exposure is preserved over rollover.
- a separate `CanonicalBatchWindowTransaction` now records backward-started/completed/terminal state.
- the previously missing genuinely unequal 3/1 objective witness and a CPU `.backward()`-before-reconcile witness are now present.

Those changes close substantial parts of the prior HIGH-1, HIGH-2 and MEDIUM finding. They do not, however, fully close the frozen scheduler and retry authority contracts below.

## Current blockers

### 1. HIGH — projected scheduler still conflates episode queue with segment chronology and cannot plan legal multi-slot / rollover cases

**Location:** `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py::_catalog_for`, `_admit`, `derive_member`, `freeze_plan` (around line 342 onward).

**Root cause:** the frozen design has two distinct concepts:

1. an immutable chronology catalog used to resolve the exact continuation segment for an already-bound episode/slot; and
2. a per-category seeded **episode queue** used only when a slot is free, where the scheduler chooses a category by weighted deficit and then takes that category's next fresh episode from step 0.

The implementation uses one `CatalogRow` collection for both. `_catalog_for(category)` includes every catalog row, including continuation rows (`cursor>0`), and `_permutation()` permutes all of those rows. Free admission then takes only the single current permuted row and requires both `candidate.identity.slot_id == slot_id` and `candidate.identity.cursor == 0`.

That creates multiple contract failures:

- Continuation rows needed for bound `cursor+1` lookup are also inserted into the free-episode permutation. If a continuation row lands at the current queue position, free admission fails even when a valid fresh episode exists later in the same category queue.
- Fresh queue entries are pre-bound to a `slot_id`, but the canonical scheduler contract says the **free slot** first selects category and then binds the next fresh episode from that category queue. A queue episode is not intrinsically owned by one future slot before admission.
- `derive_member()` resolves every row against the same pre-member queue positions. Therefore a legal B>1 member with two free slots that should both admit from the same category cannot reserve two successive episode-queue entries. With category `a`, queue position 0, and fresh entries for slot0/slot1, slot0 may consume the head conceptually but slot1 is still derived against position 0 and can fail `no legal free-slot queue admission`; the member cannot be frozen even though the design permits multiple streams from one category.
- `freeze_plan()` advances projected state between members, but it never performs projected epoch rollover inside the frozen GA-plan construction. If a projected member exhausts an epoch and terminalizes all bound slots, the next member in the same pre-load GA window still sees the exhausted permutation and cannot continue. v0.2 §4 explicitly requires projected planning to simulate queue rollover while generating the whole `CanonicalGAWindowPlan`.
- the implementation also does not validate/canonicalize the per-category catalog order by the frozen `(source_digest, episode_id)` rule before applying permutation indices, so logically identical catalogs supplied in different order can select different episodes under the same seed/epoch unless some external caller silently supplies the required order.

**Violated contract:** v0.3.5 addendum §3.2 and approved v0.2 §4-§5: stable slots continue exact chronology; only free slots consume the seeded shuffled **episode queue**; per-category queue catalog is canonically ordered by `(source_digest, episode_id)`; projected state must simulate continuation, tail, rebind, queue admission, projected exposure and queue rollover for the entire frozen GA window without live mutation.

**Exact acceptance:** keep this CPU/static-only scope, but make the scheduler authority structurally match the frozen contract:

1. separate fresh-episode queue authority from continuation-segment chronology authority (or equivalently expose two exact indexed views over one immutable source); queue permutation must range only over unique fresh episodes, never continuation segments;
2. fresh episode queue entries must be bindable to whichever slot is currently free; slot ownership is created by admission, not baked into the queue entry;
3. while deriving one B>1 member, reserve/advance a local projected queue cursor for each already-selected free-row admission so two or more free slots may legally consume successive entries from the same category without duplication or false failure;
4. validate or derive the canonical `(source_digest, episode_id)` queue order and bind `catalog_digest` to that immutable queue content/order;
5. allow `freeze_plan()` to perform **projected-only** safe epoch rollover between projected members when the frozen exhaustion/no-active-binding condition becomes true, generating the next epoch's permutations/positions without mutating live state;
6. keep live `reconcile_after_backward()` as exact cached-transition assignment only.

CPU/static tests must include: (a) one category with at least two fresh episodes admitted into two free slots in the same member, (b) a catalog containing at least one continuation row plus another fresh episode and prove continuation rows never consume/free-queue positions, (c) one multi-member frozen GA plan that crosses terminal/rebind and then an epoch rollover, and (d) logically identical canonically sorted catalog state reproducing the exact same queue sequence/provenance.

### 2. HIGH — retry lifecycle can still be bypassed through the public plan-level retry method

**Location:** `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py::CanonicalGAWindowPlan.retry_first_member_pre_backward` (around line 195) and `CanonicalBatchWindowTransaction.retry_first_member_pre_backward`.

**Root cause:** the new transaction correctly rejects retry after `backward_started` or any completed member. But the old public plan method remains callable directly and has no lifecycle state:

```python
plan.retry_first_member_pre_backward(0)
```

still returns `replace(plan, attempt=1)` whenever `plan.attempt == 0`, even if the same plan's member 0 has already backwarded and reconciled through a `CanonicalBatchWindowTransaction`. The transaction does not revoke, wrap, or capability-gate that public method. The test suite itself still calls the plan-level method directly in the unequal-count objective test, so this is not merely an unreachable private helper.

Thus the exact prior bug remains reachable: after successful member-0 backward/reconcile, code holding the original immutable `plan` can manufacture an attempt-1 retry outside the batch-window lifecycle authority.

There is a second fail-closed gap in the same authority: `mark_backward_started(member_index)` and `mark_reconciled(member_index)` only compare the index to `len(completed_members)` and never require `member_index < len(plan.members)`. After all frozen members complete, a phantom next index can still be marked backward-started/reconciled instead of the transaction closing at the frozen GA boundary.

**Violated contract:** approved v0.2 §6/§7 item 5: attempt-1 retry may be created only for attempt-0 member 0 before any outer backward begins; later/post-backward paths must terminalize the window and no alternate retry capability may exist.

**Exact acceptance:** make `CanonicalBatchWindowTransaction` (or an equivalent capability owner) the **only** authority that can create attempt-1. The immutable plan must not expose an independently usable public retry constructor. Concretely, privatize/remove the plan-level retry API or require an exact transaction-issued one-shot capability that cannot exist after backward starts. Also bound lifecycle indices to `0 <= member_index < len(plan.members)` and close/seal the transaction after the final reconciled member. Add public-path negatives proving:

- after member-0 backward/reconcile, neither transaction nor retained original plan can mint attempt-1;
- attempt-1 cannot retry again;
- out-of-range/phantom member indices fail closed;
- later/post-backward terminalization clears/suppresses the window and leaves no retry/rebind authority.

### 3. MEDIUM — Evidence still does not prove the exact projected cross-boundary contract

**Location:** `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler_test.py`, especially terminal/rebind/rollover tests.

**Root cause:** the remediation fixes two earlier evidence gaps (true 3/1 unequal counts and a direct CPU backward witness), but the remaining scheduler evidence is still split across separate operations rather than proving the frozen GA-plan behavior required by v0.2 §7:

- `test_terminal_projection_reconcile_and_rollover_release_are_atomic` freezes only one terminal member, reconciles it live, and then calls live `rollover_if_exhausted()`; it does not freeze a multi-member GA plan whose projected state crosses tail/terminal/rebind/rollover before any live mutation.
- `test_terminal_rebind_advances_frozen_queue_and_fresh_states_match` freezes/reconciles one plan and only then freezes the next plan; it does not prove terminal rebind inside one pre-load frozen GA plan.
- the fresh-state deterministic comparison checks equality of the first frozen plan, not an entire next-epoch sequence/provenance after rollover.
- there is no same-category B>1 free-slot admission fixture and no catalog fixture containing both cursor-0 fresh episode entries and cursor>0 continuation entries, so the production-contract bug in HIGH-1 is not exposed.
- the retry lifecycle test correctly rejects transaction retry after reconcile, but no test attempts the still-public direct `plan.retry_first_member_pre_backward(0)` bypass after that reconcile.

**Violated contract:** approved v0.2 §7 items 4-6 and prior ChatGPT acceptance: Evidence must establish contract → behavior → evidence for projected multi-member tail/rebind/rollover, deterministic queue provenance, and lifecycle-only retry authority.

**Exact acceptance:** after fixing the two HIGH issues, add direct CPU/static fixtures for the cases listed in HIGH-1/HIGH-2. One test should build the full frozen GA plan first, assert live state is unchanged, then reconcile the exact frozen members one by one and prove live state matches the projected sequence only after successful backward boundaries.

## Scope / current disposition

Current blockers: **2 HIGH production-contract + 1 MEDIUM Evidence**.

The remediation remains correctly limited to the two approved CPU/static contract-double files; no producer/packer/dataset/model-forward/config/optimizer/checkpoint/real-I/O/GPU/trainer production scope was added. The request's reported `24 passed`, Ruff, `py_compile`, and dual-repo diff-check results are treated as submitted Evidence and were not independently rerun by this reviewer.

Only narrow CPU/static remediation inside:
- `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py`
- `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler_test.py`

is authorized by this verdict. No production binding, real I/O, CUDA/GPU, torchrun, runtime sidecar, LIBERO4IN1, training/evaluation/inference is authorized.

Any remediation creates a new child SHA and therefore requires a new root formal pair for fresh review. Reserved success literal remains:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_SEGMENT_ADAPTER_SCHEDULER_CPU_STATIC`.
