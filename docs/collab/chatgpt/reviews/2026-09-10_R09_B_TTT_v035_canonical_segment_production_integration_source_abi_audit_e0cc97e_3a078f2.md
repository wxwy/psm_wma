# ChatGPT 独立 Canonical Segment Production Integration Source-ABI Audit v0.2 Review

Formal reviewed pair:
- root audit SHA: `e0cc97e7178d345c6575bb7f73f540b8ec056f1c`
- child/Gitlink SHA: `3a078f28f3d107bb633c932271f86498f7c427f7`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-INTEGRATION-SOURCE-ABI-AUDIT`
- artifact: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_integration_source_abi_audit_v0.2.md`
- frozen authority: v0.3.5 addendum §18/§20.1--§20.2, approved production-integration design `ce8e3502af5226d42c270dca4d5387cec8bed412 / 3a078f28f3d107bb633c932271f86498f7c427f7`, and the closed `CanonicalGAWindowPlan.objective()` contract.
- previous formal review: `2d34eedcf30163de9e011bf1c4166199e916a2f6 / 3a078f28f3d107bb633c932271f86498f7c427f7`, `REQUEST_CHANGES`, review `docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_production_integration_source_abi_audit_2d34eed_3a078f2.md`.

Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_integration_source_abi_audit_v0.2.md:32)`

## Incremental result

### CLOSED — prior HIGH: native total-loss valid-count weighting

v0.2 correctly removes the v0.1 instruction to multiply the whole native `total_loss` by `N_valid/N_window`. It now maps `compute_flow_matching_loss()` to the per-instance/per-member consumer mean, separates the flow consumer terms from the later load-balancing auxiliary addition in `OmniMoTModel._compute_losses()`, and freezes the already-approved objective:

`planned_n_valid/original_n_valid_window * consumer_loss + auxiliary_loss/original_ga_effective`.

It also preserves `actual_n_valid == member.planned_n_valid` as a pre-backward requirement and explicitly fails closed if the real production path cannot preserve the consumer/auxiliary decomposition.

### CLOSED — prior MEDIUM: real packer/loss-mask source map

v0.2 now reaches the real `pack_input_sequence()` loop/order, per-sample Memory Prefix `None` handling, modality index ownership, and the actual flow loss-mask/reduction implementation. The audit correctly distinguishes reusable native per-plan ordering/token masks from the still-missing canonical `[B_stream,T]` logical PAD/`consumer_valid`/stream-major gather ABI, which remains a future producer responsibility.

### HIGH — canonical objective is followed by a second GA division

- Severity: HIGH
- Location: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_integration_source_abi_audit_v0.2.md:32` (section 2.2 item 5), together with section 2.3.
- Root cause: v0.2 correctly defines `L_member = N_valid/N_window * consumer_loss + auxiliary_loss/GA`, but then says P1 should return this `L_member` into the existing ordinary trainer seam while retaining the native `loss / grad_accum_iter` division. That applies GA normalization twice.
- Violated contract: in a full-valid window, `N_valid/N_window == 1/GA`; therefore `CanonicalGAWindowPlan.objective()` already yields the canonical `1/GA` member contribution. Passing that scalar through the ordinary trainer branch `grad_scaler.scale(loss / self.config.trainer.grad_accum_iter).backward()` makes the effective consumer coefficient `1/GA^2`, and the auxiliary coefficient likewise `1/GA^2`, violating v0.3.5 §7.1 and the closed scheduler objective.
- Source confirmation: current child `trainer/__init__.py` has separate special canonical/active backward branches that bypass the ordinary `/grad_accum_iter` loss division; `_run_active_local_memory_backward()` performs `grad_scaler.scale(objective).backward()` directly, and `_run_canonical_segment_backward()` delegates to a transaction-owned objective/backward seam. Those old paths are not production authority for the new canonical route, but they demonstrate the necessary scaling shape: once the canonical objective has already normalized the GA window, backward must not divide it by GA again.
- Exact acceptance:
  1. Correct §2.2 item 5 and §2.3 to separate **trainer GA clock/DDP sync/optimizer-step cadence** from the ordinary scalar `/grad_accum_iter` normalization.
  2. Freeze P1 so the new canonical production branch computes the exact `CanonicalGAWindowPlan.objective()` and performs exactly one scaled backward on that already-window-normalized scalar, with **no additional `/GA`**. No-Local/ordinary training must keep its native `/GA` behavior unchanged.
  3. Add a required P1 CPU/static algebra fixture proving full-valid members contribute exactly `1/GA`, not `1/GA^2`; unequal-valid members must contribute exactly `N_valid_i/N_valid_window`, and auxiliary must remain exactly `1/GA`.
  4. Preserve the native DDP sync boundary and optimizer-step cadence at the GA window boundary while avoiding duplicate sample-level/DDP/GA scaling.
  5. Do not reuse the old row-wise canonical/active lifecycle as the new implementation authority; P1 must define a new segment-level production seam under its own reviewed whitelist.

## Scope

Current blockers: **1 HIGH**.

The previous v0.1 HIGH and MEDIUM are closed. This new HIGH blocks P0 closure and therefore blocks authority to create/execute the P1 production ABI implementation design as an approved next step.

Authorized next action is docs-only remediation of this P0 audit on a new formal root SHA. No child implementation, producer/packer/model/trainer/config/optimizer/checkpoint modification, real I/O, CUDA/GPU, torchrun, runtime sidecar, LIBERO4IN1, training, evaluation, or inference is authorized.
