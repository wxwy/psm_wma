# ChatGPT 独立 runtime-owner / sidecar design v0.8.2 review

Formal reviewed pair:
- root design SHA: `a763c116322e1e360d575d430dc20c0b777a8465`
- child/Gitlink SHA: `5d16b84fe17a42f128065bf36361f6b1bb93a436`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-WIRING-RUNTIME-SIDECAR-DESIGN`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh incremental review relative to prior formal pair `0792388fb1d6bc851d50897ceb4d202d4d4b38f5` / `5d16b84fe17a42f128065bf36361f6b1bb93a436`. Child is unchanged. v0.8.2 is a docs-only remediation that supersedes v0.8.1 and inherits the v0.8/v0.8.1 whitelist, phase machine, exact wiring authority, snapshot frontier and no-real-I/O/GPU/training boundary.

## Prior blocker status

1. **CLOSED — pending exact capability identity.** `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.8.2.md:5-17`. `pending()` is now explicitly the original exact tuple: transaction/result remain object-identical to the current pending capability and graph-bearing tensors must not be cloned/detached/reconstructed. Only committed snapshot state is deep-copied/detached.

2. **CLOSED IN DIRECTION — no duplicate scheduler admission for the failed retry member.** `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.8.2.md:19-29`. v0.8.2 correctly preserves the failed attempt-0 `SegmentIdentity` as `retry_first_identity` and explicitly forbids `scheduler.admit()` for the first attempt-1 suffix member.

## Current blocker

1. **HIGH — retry entry freezes an impossible equality between a `GAWindowPlan` member key and a `SegmentIdentity` object.** `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.8.2.md:25-27`; `cosmos_framework/model/generator/mot/local_memory_segment.py:128-170,188-196,293-317`.

   v0.8.2 requires `retry_plan.members[0] == retry_first_identity`. In the formal child, `GAWindowPlan.members` is frozen as `tuple[tuple[int, str, int], ...]`, i.e. each member is the `(slot_id, episode_id, cursor)` projection. `retry_first_identity` is a `SegmentIdentity` dataclass object with additional fields (`category`, `segment_id`, `source_digest`, `training_stream_end`). Under these exact types, the stated equality can never be true, so `begin_retry()` cannot satisfy its own frozen precondition and cannot enter `MEMBER_READY`.

   This is not repaired by the adjacent scheduler-authority check: `admission_order` / `stable_slots` contain `SegmentIdentity`, but the plan member itself remains a three-tuple. The design must explicitly distinguish the plan-member projection from the full exact admitted identity.

   **Acceptance:** replace the impossible cross-type equality with the existing canonical member projection, e.g. require `retry_plan.members[0] == (retry_first_identity.slot_id, retry_first_identity.episode_id, retry_first_identity.cursor)`, and separately freeze exact admitted-identity authority against the retained scheduler state (preferably the retained exact `retry_first_identity` object/value in `stable_slots` and `admission_order`, with no duplicate admission and not yet in `committed_identities`). Preserve the new attempt-1 transaction creation and direct `MEMBER_READY` transition. Add CPU/static Evidence that a real failed `SegmentIdentity` satisfies the projected suffix member check, the same admitted identity is reused without scheduler mutation, retry scan reads the prior committed sidecar frontier, and a mismatched full identity (same member tuple but wrong source/category/segment metadata where constructible) is rejected by the scheduler/owner exact-identity guard.

## Scope boundary

No runtime-owner CPU/static implementation authority is granted for this pair. This remains docs-only. No production model/trainer/packer wiring, persistent sidecar/checkpoint I/O, config/default/registry changes, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T, or LIBERO4IN1 is authorized.
