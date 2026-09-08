# ChatGPT independent review — Local Memory v0.3.5 production wiring/runtime-sidecar design v0.3

**Date:** 2026-09-08  
**Verdict:** `REQUEST_CHANGES`

Formal reviewed pair:
- root design SHA: `16cadf6b8f0052285d3e4af8256081167c2084b9`
- child/Gitlink SHA: `d05f14e7195ee5efc37f9d9955923d51fd4e4b25`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-WIRING-RUNTIME-SIDECAR-DESIGN`
- requested literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_WIRING_CPU_STATIC`

Fresh incremental review relative to formal pair `65a643457136d26aec634c95864102cbed8b8378 / d05f14e7195ee5efc37f9d9955923d51fd4e4b25`. Child is unchanged. Prior verdict is not inherited. Only the prior remaining model-seam / exact-whitelist blockers plus new contract violations introduced by v0.3 were reviewed.

## Prior blocker status

### CLOSED — model selector/callsite reachability and test-file status

v0.3 now freezes `OmniMoTModel.training_step(data_batch, iteration)` as the exact marker callsite before `_get_training_inputs(...)`, and `ImaginaireTrainer.training_step` as the exact output-marker callsite before the legacy `loss / grad_accum_iter` path. `omni_mot_model_test.py` is correctly marked `existing/modified`; all eight paths now have explicit new/existing-modified status.

### CLOSED — plan-aware loss ABI

The canonical scalar remains explicitly frozen as `(N_valid_i/N_valid_window) * primary_consumer_mean_i + auxiliary_loss_i/GA_effective`, with raw-primary finite check, no second `/grad_accum_iter`, and no second backward.

## Current blockers

### HIGH — feature-disable precedence regresses under the new pre-input marker branch

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.3.md:23-36`
- `cosmos_framework/model/generator/omni_mot_model.py` current `training_step` / `_inject_local_history` path at formal child `d05f14e`

**Root cause:** v0.3 supersedes v0.2 and makes the first `OmniMoTModel.training_step` branch depend only on `data_batch.get("canonical_local_memory_segment") is True`, before `_get_training_inputs()` and therefore before the current `local_ttt_enabled` decision. This means a test batch carrying the marker can enter canonical wiring even when `local_ttt_enabled=False`. The prose later says the disabled test follows the original disabled route, but the frozen executable selector does not enforce that. This reopens the feature-disable authority that v0.2 had correctly frozen as `local_ttt_enabled=False -> original disabled route, no wiring/adapter/lifecycle`.

**Acceptance:** freeze the selector so `local_ttt_enabled=False` wins unconditionally. For example, the marker branch must require both `local_ttt_enabled=True` and the marker, or an equivalent exact guard. A marker present while disabled must not construct/call `CanonicalSegmentWiring`, adapter, `_ttt_lifecycle`, or `TTTLifecycle`; disabled output/loss/input-gradient parity remains mandatory.

### HIGH — the new trainer helper can become a second canonical backward/transaction authority

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.3.md:37-46`
- `cosmos_framework/trainer/__init__.py` formal child `d05f14e`, existing `ImaginaireTrainer._run_local_memory_segment_backward`

**Root cause:** the formal child already contains the closed canonical Local backward owner `_run_local_memory_segment_backward`, which owns objective construction, `transaction.validate_success`, exactly one `loss.backward()`, failure taxonomy/slow-grad clear, and `transaction.successful_backward`. v0.3 now authorizes a second private `_run_canonical_segment_backward` and describes it as executing the same loss/backward semantics, but does not freeze it as orchestration-only delegation to the existing canonical seam. Implementing the text literally would create duplicate loss/backward/transaction authority; implementing it as a delegate would be an implementer choice rather than a frozen contract. The model output also claims to carry `member_index` and `clear_slow_grads` although the helper is frozen to read only four fixture keys; their authoritative source is not specified.

**Acceptance:** keep `_run_local_memory_segment_backward` as the sole formula/backward/transaction owner. Freeze `_run_canonical_segment_backward` as orchestration-only: derive/fetch the exact `member_index` and trainer-owned `clear_slow_grads` from named authoritative sources, invoke `_run_local_memory_segment_backward` exactly once with the existing ABI, and only after that success call `adapter.commit(...)`. It must not reimplement objective scaling, finite check, taxonomy, backward, or `successful_backward`. Freeze the exact source of `member_index` and `clear_slow_grads`; do not manufacture them in the model output.

### MEDIUM — exact symbol whitelist is internally inconsistent

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.3.md:8-20,29-33`

**Root cause:** the whitelist for new `production_segment_wiring.py` authorizes only `CanonicalSegmentForward`, `CanonicalSegmentWiring`, and `build_segment_batch_for_test`, while §2 requires the model helper to call a module symbol `run_native_forward_for_test(payloads, locals)`. Because the design also states all unlisted symbols are forbidden, the described implementation cannot be written within the approved surface.

**Acceptance:** either add `run_native_forward_for_test` as an exact authorized new symbol with frozen signature/return ABI, or make it an explicitly named method of an already-authorized class and freeze that method. No unlisted helper/function may be introduced after approval.

## Non-blocking confirmations

- v0.3 correctly supersedes v0.2 and narrows the intended Gate to CPU/static test-only wiring; real dataloader selector/config remains outside this Gate.
- Eight repository paths are explicitly enumerated and `omni_mot_model_test.py` is correctly `existing/modified`.
- Model marker reachability is now explicit and bypasses legacy `_get_training_inputs` / `_ttt_local_memory_tokens` on the canonical test path.
- The canonical weighted primary/auxiliary formula and no-second-GA/no-second-backward rule remain correct.
- Persistent sidecar/resume, real data/cache/checkpoint I/O, config/default/registry/optimizer changes, GPU/CUDA/torchrun, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1 remain prohibited.

No production-wiring CPU/static implementation authority is granted by this verdict. A remediation design creates a new formal root and requires fresh review.
