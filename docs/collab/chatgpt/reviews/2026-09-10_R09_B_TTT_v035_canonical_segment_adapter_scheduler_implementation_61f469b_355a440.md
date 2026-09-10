# ChatGPT 独立 Canonical Segment Adapter/Scheduler CPU/static Implementation Review

Formal reviewed pair:
- root implementation SHA: `61f469b0a142e340becd8038e2be23eca63b73e4`
- child/Gitlink SHA: `355a44087d0149b4875fb37e81d726523af66fdd`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-ADAPTER-SCHEDULER-CPU-STATIC-IMPLEMENTATION`
- approved design pair: root `4522466880221a64cac77b602e903652d180ccb5` / child `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`
- frozen design chain: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.2.md` + `v0.3.md`
- request/bookkeeping commit observed: `9425ff8046e44a321ef21074028f79a9ebd1b434`; later review-handoff/poll commits are bookkeeping only and do not replace the formal pair.

Verdict: `REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py:241)`

## Incremental scope / positive findings

The child diff from the approved design child `f14a8d8` to `355a440` is correctly limited to two new files:
- `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py`
- `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler_test.py`

The implementation correctly carries several approved contracts:
- S0 is counted as a valid native consumer while Local remains absent; PAD is excluded.
- `NativeConsumerBatch.from_segment()` preserves stream-major gathered identity/count and checks `item_count == planned_n_valid`.
- `CanonicalGAWindowPlan.objective()` uses the frozen original window denominator and GA effective value.
- v0.3 queue preimage bytes are implemented as UTF-8 / single NUL / ASCII decimal without ambient RNG or Python hash.
- retry attempt-1 preserves the original immutable members/denominator/GA because it uses `replace(self, attempt=1)` rather than the inherited suffix plan.
- no producer/packer/model-forward/config/optimizer/checkpoint/real-I/O/GPU/trainer production path was modified.

These points are not blockers. The request's reported `8 passed`, Ruff, `py_compile`, and diff-check results were read as submitted Evidence and were not independently rerun by this reviewer.

## Current blockers

### 1. HIGH — `ProjectedSchedulerState` is a blind member replay, not the frozen projected scheduler/planning authority

**Location:** `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py:241` (`ProjectedSchedulerState.project_commit`) and `:270-293` (`CanonicalBatchScheduler.project` / `rollover_if_exhausted`).

**Root cause:** the approved v0.2 design freezes a projected scheduler that derives a GA-window plan from committed state and deterministically simulates bound continuation, tail terminalization, terminal rebind/free-slot admission, weighted-deficit category selection, queue positions/permutations, exposure, and rollover without mutating live state. The implementation does not model that authority:

- `ProjectedSchedulerState` has no target distribution or immutable chronology catalog.
- `QueueEpochSnapshot` stores seed/epoch/catalog digest/positions but not the per-category frozen permutation required by the design.
- `CanonicalBatchScheduler.project()` accepts already-constructed `MicrobatchPlanMember` objects instead of deriving/admitting them from the projected scheduler state.
- `project_commit()` checks only exact queue-snapshot equality and exposure-before equality, then blindly overwrites `stable[slot_id] = identity`.
- It never validates an already-bound slot as exact same category/episode/source with `cursor+1` continuation.
- It never validates legal terminal release/rebind or free-slot admission.
- It never advances queue position/permutation on admission and never performs weighted-deficit category choice.
- normal member projection leaves the queue snapshot unchanged, so a projected multi-member window cannot represent actual queue consumption.

A member replacing an already-bound slot with another episode/category/cursor can therefore be accepted by the scheduler state transition as long as its own frozen metadata is self-consistent. That violates the stable-slot chronology authority and means the CPU/static double does not prove the scheduler/GA contract it is intended to close.

**Violated frozen contract:** v0.2 §4-§5 and §7 items 4/6, inherited unchanged by v0.3: pure projected planning must simulate exact continuation/tail/rebind/queue admission/exposure/rollover, preserve deterministic weighted scheduling, and reconcile only the exact frozen valid transition after successful backward.

**Exact acceptance:** within the same bounded CPU/static scope, implement an exact projected scheduler transition/planning authority that:
1. binds the state needed by the frozen design, including target distribution, chronology/catalog authority, queue positions and exact per-category epoch permutation (or change the design under a new design SHA before using a different authority model);
2. enforces unique stable slots and exact bound continuation `(category, episode_id, source_digest, cursor+1)`;
3. permits terminal release/rebind/free-slot admission only at the frozen legal boundary;
4. deterministically selects new admissions by the frozen weighted-deficit + queue-permutation rule and advances projected queue positions;
5. projects cross-tail/rebind/rollover members without mutating live state;
6. after successful backward, atomically reconciles the live state to exactly the previously projected/frozen member transition and rejects any foreign/stale/reconstructed transition before mutation.

CPU/static Evidence must include at least a multi-member window crossing a tail/rebind boundary, illegal episode/category/cursor replacement rejection, queue-position advancement, weighted-deficit admission, and deterministic next-epoch sequence/provenance.

### 2. HIGH — first-member retry is not actually guarded by a pre-backward/window lifecycle

**Location:** `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py:194` (`CanonicalGAWindowPlan.retry_first_member_pre_backward`).

**Root cause:** the method enforces only `attempt == 0` and `member_index == 0`. There is no batch-window transaction/lifecycle state for `backward_started`, completed members, terminal failure, cleared slow grads, or suppressed remaining members. Consequently, calling the same original plan after member-0 has already successfully backwarded/reconciled still returns an attempt-1 retry plan. The API name says "pre_backward", but the contract is not behaviorally enforced.

Likewise, a later-member retry request merely raises; there is no new batch-level authority that terminalizes the whole window, marks/clears the slow-gradient window, suppresses the remaining suffix, and prohibits rebind/retry as required. The old row-wise `LocalMemoryTransaction` cannot silently supply this missing authority because the approved design explicitly isolates the new batch-level route from that old row-wise contract.

**Violated frozen contract:** v0.2 §6 and §7 item 5, inherited by v0.3: only attempt-0 member-0 may retry before any native outer backward starts; any later-member transient or any post-backward failure must terminalize the whole GA window, clear/suppress the slow-gradient window, and forbid suffix retry/rebind.

**Exact acceptance:** add a bounded CPU/static batch-window transaction/lifecycle double (or equivalent exact authority) that records sufficient phase/completion state to enforce:
1. retry only for attempt-0 member-0 while no backward has started and no member has committed;
2. attempt-1 can never retry again;
3. once backward starts or a member has reconciled, the original plan can no longer generate a retry;
4. later-member or post-backward failure produces an explicit terminal window state with `slow_grads_cleared=True` (contract-state witness), remaining members suppressed, and no retry/rebind capability;
5. failure before reconcile leaves projected/live scheduler authority unchanged.

Tests must exercise the public lifecycle path, including the negative "call retry after successful member-0 backward/reconcile" case.

### 3. MEDIUM — acceptance Evidence is incomplete even where the implementation logic is otherwise plausible

**Location:** `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler_test.py:84` and following acceptance tests.

**Root cause:** several named tests do not prove the frozen matrix they claim:

- `test_unequal_count_ga_objective_and_first_member_only_retry` uses two members that both have `planned_n_valid == 3`, so it is not an unequal-count GA test. It does not prove the v0.2/v0.3 weighted objective with e.g. `5/3` or `3/1` counts including S0.
- no test performs an actual shared CPU tensor `.backward()` witness for one B>1 member before the all-row reconcile boundary; the current atomic test directly calls `reconcile_after_backward`.
- the B>1 fixture has `training_stream_end=False` for both rows, and the projected-planning test uses only one nonterminal member, so it does not prove a GA plan crossing a tail/terminal/rebind boundary.
- the rollover test compares `queue_permutation(...)` to another immediate call of the same function and checks only epoch/exposure; it does not prove two independent fresh scheduler states produce the same next-epoch admission sequence/provenance under the full projected scheduler state.

**Violated frozen contract:** v0.2 §7 items 2-6 and v0.3 §4 supplementary Evidence requirements.

**Exact acceptance:** after the production-contract blockers above are fixed, add direct CPU/static Evidence for:
1. genuinely unequal member counts containing S0 and exact frozen weighted-objective coefficients;
2. one shared backward witness followed by exactly one all-row atomic reconcile;
3. a multi-member projected plan crossing terminal/tail and legal rebind, plus mismatch/failure no-mutation negatives;
4. two fresh scheduler states with identical frozen inputs producing byte-identical preimages, identical permutations, identical next-epoch sequence/provenance; changed frozen inputs must be observably distinct.

This blocker is tests/Evidence-only; it does not by itself claim the already-correct count/objective formula is wrong.

## Scope / next authorized action

Current blockers: **2 HIGH production-contract + 1 MEDIUM Evidence**.

Only a narrow CPU/static remediation inside the already-approved adapter/scheduler contract-double scope and adjacent tests is authorized. No production binding, real producer/packer/model forward, dataset/manifest/config/optimizer/checkpoint change, real I/O, CUDA/GPU, torchrun, runtime sidecar, LIBERO4IN1, training/evaluation/inference is authorized.

Any remediation creates a new child SHA and therefore a new root formal pair; that pair requires fresh independent implementation review. The reserved close literal remains:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_SEGMENT_ADAPTER_SCHEDULER_CPU_STATIC`.
