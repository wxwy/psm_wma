# ChatGPT 独立 runtime-owner / sidecar design v0.8.5 review

Formal reviewed pair:
- root design SHA: `28828aaa03d7550e08d6f865216dcaa198b2f369`
- child/Gitlink SHA: `5d16b84fe17a42f128065bf36361f6b1bb93a436`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-WIRING-RUNTIME-SIDECAR-DESIGN`
- request/bookkeeping HEAD observed at review start: `29f6a2e97630fe03e430d0b42d3fbeed701f4e10`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh incremental review relative to prior formal pair `9e3e8714005d5758e06f031274753e5529f6c793` / `5d16b84fe17a42f128065bf36361f6b1bb93a436`. Child is unchanged. v0.8.5 is a docs-only remediation for the prior skip scheduler/sidecar chronology HIGH and inherits the v0.8-v0.8.4 exact wiring, pending preflight atomicity, retry projection, snapshot frontier, whitelist, and no-real-I/O/GPU/training boundary. Review is based only on the Codex canonical request, v0.8.5, the previous ChatGPT review, and the formal child source/tests.

## Prior blocker status

**CLOSED — skip scheduler/sidecar chronology now has a coherent retained-admission path.** v0.8.5 introduces `SKIP_READY`, retains the exact already-admitted-but-uncommitted `SegmentIdentity`, forbids duplicate scheduler admission, rejects snapshot while scheduler/sidecar frontiers intentionally differ, and resumes the retained identity before allowing the next normal cursor. This closes the previous `k -> admitted k+1 -> skip -> fresh-admit k+2` chronology break.

## Current blocker

1. **HIGH — `resume_skipped(plan)` accepts a new caller-supplied attempt-0 `GAWindowPlan` without freezing the plan authority that controls GA order/count/weighting.** `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.8.5.md:21-37`; `cosmos_framework/model/generator/mot/local_memory_segment.py` (`GAWindowPlan.objective`, `LocalMemoryTransaction.validate_success`); `cosmos_framework/trainer/trainer_local_memory_integration_test.py` weighted/suffix fixtures.

   v0.8.5 correctly retains the exact skipped `SegmentIdentity`, but `resume_skipped(plan)` is permitted to create a **new normal attempt-0 transaction** from a caller-provided plan after checking only that `plan.members[0]` matches the skipped identity projection and that scheduler/pending authority is intact. It does not freeze where that new plan comes from or constrain its remaining `members`, `planned_n_valid`, `plan_chain_id`, or effective GA window semantics.

   Those fields are not bookkeeping-only: in the formal child, `GAWindowPlan.objective()` directly derives `n_window` and `ga_effective` from the plan and therefore owns the primary valid-consumer weighting and auxiliary `/GA_effective` scaling; `LocalMemoryTransaction.validate_success()` also uses the plan member ordering and planned counts as execution authority. A different caller-supplied attempt-0 plan can therefore change the future execution/order/weighting after a skip even while passing v0.8.5's first-member identity checks.

   The design explicitly says that multi-member skip window-level exposure/compensation is “不在本 Gate 定义，交由后续 model/trainer integration Gate”. That deferral is acceptable only if this Gate **fails closed** for the undefined case. It is not compatible with granting a generic `resume_skipped(plan)` implementation authority that can already construct a new transaction on an unconstrained plan.

   **Acceptance:** freeze one exact plan authority for skip-resume, or narrow this Gate so undefined cases are rejected. A compatible minimal option is: in this Gate only allow skip-resume when the skipped member is the first unresolved member of an exact retained immutable plan whose object/content authority was captured before skip; `resume_skipped` must consume that retained plan (not an arbitrary caller replacement), and all members/planned counts/chain identity must remain unchanged. If the current `LocalMemoryTransaction` API cannot preserve correct weighting for a later-member mid-window skip, explicitly fail closed for that case in this Gate and defer it to a later design that expands the transaction contract. Add CPU/static negative Evidence that a replacement plan with the same first member but changed `planned_n_valid`, remaining members, attempt/chain metadata, or ordering is rejected with zero owner/scheduler/pending mutation; add a positive supported skip-resume case proving the exact retained plan authority and unchanged objective semantics.

## Scope boundary

No runtime-owner CPU/static implementation authority is granted for this pair. This remains docs-only. No production model/trainer/packer wiring, persistent sidecar/checkpoint I/O, config/default/registry changes, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T, or LIBERO4IN1 is authorized.
