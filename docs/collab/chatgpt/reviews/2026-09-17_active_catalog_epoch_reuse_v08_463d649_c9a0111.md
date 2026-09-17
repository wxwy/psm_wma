# ChatGPT independent review — ACTIVE-CATALOG-EPOCH-REUSE v0.8

Date: 2026-09-17
Gate: `G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE`
Formal pair reviewed:
- root: `463d649e7d0a6417095b7d694a17b2ed28a8a886`
- exact child/Gitlink: `c9a01116e8d48a13d1f38fffafcf72461c2352c3`
- design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_catalog_epoch_reuse_design_v0.1.md`

## Verdict

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE`

This approval is design-to-implementation authority for this Gate only. It is not implementation/evidence closure and does not authorize D8b 5000-step training.

## Why the previous blockers are closed

### 1. Previous authority-chain HIGH is closed

The old v0.8 wording tried to keep the global `QueueEpochSnapshot` authority frozen while simultaneously bypassing it for per-slot reuse. The current design no longer makes that contradictory claim.

Section 3.3 now explicitly declares a scoped **active-route queue-semantics refreeze/supersession**: the global rollover clause from canonical scheduler design v0.2 is superseded only for this active route; `_slot_epoch[slot]` is the canonical per-slot queue-identity authority; scheduler scalar `queue_epoch` / `queue_permutation` are compatibility metadata and do not drive active-route reorder or resume witness. The frozen `queue_permutation` algorithm and ABI remain unchanged.

That is a coherent single-authority model. It also preserves the frozen chronology requirement: non-terminal slots continue the same episode/cursor/fast-state, while only terminal slots enter a fresh reuse traversal.

### 2. Previous capacity-evidence HIGH is closed

The probe has been materially corrected rather than merely relabeled:

- rollover reorder now derives the reference order from the whole category and filters the slot subsequence, matching §4.4;
- criterion 1 is independently recomputed from the pre-rollover snapshot;
- top-level PASS and process exit now include capacity target and full block coverage;
- the committed artifact reports `windows_total=5112`, `criterion2_meets_target=true`, `capacity_target_met=true`, `catalogue_blocks=14430`, `covered_blocks=14430`, `full_coverage=true`, and no stranded blocks.

This is sufficient design-phase evidence that the proposed asynchronous per-slot state machine can cross the former 112-window capacity wall and reach the 5000-step planning horizon.

### 3. Previous chronology and cumulative-exposure blockers remain closed

The design keeps `cumulative_valid_consumer_exposure` as the selection authority and does not revive per-epoch `_epoch_observed`. Non-terminal slots are not rewound at a reuse boundary; their exact episode identity, next cursor and fast-state carry remain continuous until `training_stream_end`.

## Implementation-review requirements (non-blocking for this design approval)

1. Production implementation must persist `_slot_epoch` and derive/replay each slot's queue identity exactly as frozen in §3.3/§4.4. A later implementation pair must be freshly reviewed.
2. The current planning artifact uses `queue_seed=0`; production §4.6 derives the seed from catalog identity. The implementation/evidence closure must rerun the relevant planning/continuity witness with the exact production-derived seed (or prove seed-independence for the claimed property). The seed-0 artifact is feasibility/design evidence, not production closure evidence.
3. The current resume child `c9a0111` still has a separate closure defect at terminal frontiers; Gate 3 implementation must not use a Gate 2 closure token until that is fixed and re-reviewed.
4. §3.2 still contains the historical `5000 / 112 -> 45` capacity wording while the current per-slot probe needs 63 boundaries for 5112 windows. §10.3 is the current measured authority; clean the stale 45-boundary wording during implementation/docs synchronization.
5. §10.4's 75.3% / 39.2% regime discussion comes from the older global-reset experiment. The current per-slot/category-level probe has different window composition and near-balanced cumulative exposure. Keep §10.4 explicitly historical; do not use those old numbers as current-v0.8 evidence when deciding the later D8b scheduler-semantics Gate.

## Scope

- Gate 3 design: APPROVED TO IMPLEMENT.
- Gate 3 implementation/evidence: not yet reviewed.
- D8b formal 5000-step long run: remains blocked by the design's explicit §8/§9 policy until the required downstream scheduler-semantics decision and Gate 3 implementation/evidence closure are complete.
