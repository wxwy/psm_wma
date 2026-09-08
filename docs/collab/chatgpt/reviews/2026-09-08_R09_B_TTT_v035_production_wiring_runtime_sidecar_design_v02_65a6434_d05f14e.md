# ChatGPT independent review — Local Memory v0.3.5 production wiring/runtime-sidecar design v0.2

**Date:** 2026-09-08  
**Verdict:** `REQUEST_CHANGES`

Formal reviewed pair:
- root design SHA: `65a643457136d26aec634c95864102cbed8b8378`
- child/Gitlink SHA: `d05f14e7195ee5efc37f9d9955923d51fd4e4b25`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-WIRING-RUNTIME-SIDECAR-DESIGN`
- requested implementation literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_WIRING_CPU_STATIC`

Fresh incremental review relative to formal pair `f3d74c01de0626bf667ee0943e4158374e92d26b / d05f14e7195ee5efc37f9d9955923d51fd4e4b25`. Child is unchanged; prior verdict is not inherited. Review scope is only the v0.2 root-design delta plus repository truth needed to test implementation-readiness.

## Prior blocker status

### CLOSED — unique selector / old-path supersession semantics

v0.2 now freezes an explicit test-only marker and precedence. When `local_ttt_enabled=True` and `canonical_local_memory_segment=True`, the canonical path must be selected and `_ttt_local_memory_tokens`, `_ttt_lifecycle`, and `TTTLifecycle.process_sample()` must remain uncalled/unconstructed. When the marker is absent, the old path remains unchanged. This closes the prior double-authority/selector ambiguity at the contract level.

### CLOSED — plan-aware loss reduction ABI

v0.2 now freezes `primary_consumer_mean_i`, `auxiliary_loss_i`, `N_valid_i`, `N_valid_window`, `GA_effective`, raw-finite checking, and the unique backward scalar:

`L_i = (N_valid_i/N_valid_window) * primary_consumer_mean_i + auxiliary_loss_i/GA_effective`

It explicitly forbids an additional `/grad_accum_iter` and a second backward. This closes the prior reduction ambiguity.

## Current blockers

### HIGH — approved child surface cannot actually realize the frozen model selector/forward ABI

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.2.md:10-18,24-45`
- `cosmos_framework/model/generator/omni_mot_model.py:1280-1515`

**Root cause:** v0.2 claims to be the unique implementation-ready design and freezes `canonical_local_memory_segment=True -> OmniMoTModel._canonical_local_memory_segment_forward`. However the exact whitelist authorizes `omni_mot_model.py` only for adding that new private method; it does not authorize any change to `_inject_local_history`, `_prepare_training_data`, `_get_training_inputs`, or `training_step()` to call it. Repository truth shows `OmniMoTModel.training_step()` is a monolithic native path: `_get_training_inputs -> pack -> noise -> denoise -> _compute_losses -> return (output_batch, loss)`. There is no existing named “native training forward helper” matching the design text, and no authorized callsite can route the marker into the new method. As written, the frozen canonical selector is therefore unreachable under the approved surface, while implementing it would require an unapproved modification or ad-hoc refactor. The subsequent trainer trigger (“output contains canonical_segment_forward”) is likewise not grounded because the model training_step return ABI remains `(output_batch, loss)` and the design does not freeze which authorized symbol inserts that field.

**Violated contract:** implementation authority must bind an exact reachable production-adjacent seam with one owner; no implementer-created selector/forward authority is allowed after approval.

**Acceptance:** in a new formal root, freeze one exact reachable model seam and its exact modified symbol(s). Either:
1. explicitly authorize and specify the exact controlled branch in an existing method such as `_inject_local_history` / `_prepare_training_data` / `training_step`, including exact input/output ABI and where `canonical_segment_forward` enters `output_batch`; or
2. introduce a named new helper that owns the native pack/denoise/loss subset and explicitly authorize the minimal existing callsite that invokes it.

Also name the exact native forward/loss symbol used by the canonical branch; do not use “existing native training forward helper” unless that symbol actually exists at the formal child. The canonical marker path must be reachable in CPU synthetic tests without modifying any unlisted symbol, and the legacy path must remain uncalled on that branch.

### MEDIUM — whitelist new/existing status is not repository-exact

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.2.md:12-18`
- `cosmos_framework/model/generator/omni_mot_model_test.py:1`

**Root cause:** the whitelist says `omni_mot_model_test.py` may be modified “若不存在则新建”, but that file already exists at formal child `d05f14e`. An implementation-authorizing whitelist must not leave existing/new status conditional.

**Acceptance:** mark `cosmos_framework/model/generator/omni_mot_model_test.py` as `existing/modified` unconditionally, and mark every other authorized path as exact `new` or `existing/modified`. Keep all unlisted paths/symbols unchanged and uncalled.

## Non-blocking confirmations

- v0.1 is explicitly superseded as source-audit-only; v0.2 is the only current design authority.
- Config/default/recipe/registry/optimizer/dataset/manifest/checkpoint/C6/old lifecycle production route remain outside this Gate.
- Runtime-sidecar persistence/resume, real data/cache/checkpoint I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1 remain prohibited.
- The proposed `CanonicalSegmentWiring`/`CanonicalSegmentForward` in-memory object ABI and sidecar no-persistence boundary are directionally consistent with the closed v0.5 CPU/static contract.

No production-wiring CPU/static implementation authority is granted by this verdict. A remediation design forms a new formal pair and requires fresh independent review.
