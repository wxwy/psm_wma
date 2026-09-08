# ChatGPT independent review — Local Memory v0.3.5 production wiring design v0.4

**Date:** 2026-09-08  
**Verdict:** `REQUEST_CHANGES`

Formal reviewed pair:
- root design SHA: `a4556b2c4c12b2337a111a2764fa2632746bfffa`
- child/Gitlink SHA: `d05f14e7195ee5efc37f9d9955923d51fd4e4b25`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-WIRING-RUNTIME-SIDECAR-DESIGN`
- requested literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_WIRING_CPU_STATIC`

Fresh incremental review relative to formal pair `16cadf6b8f0052285d3e4af8256081167c2084b9 / d05f14e7195ee5efc37f9d9955923d51fd4e4b25`. Child is unchanged. The prior v0.3 verdict is not inherited.

## Prior blocker status

### CLOSED — feature-disable precedence
v0.4 now requires both `self.config.local_ttt_enabled` and the test-only marker before entering canonical wiring. `local_ttt_enabled=False` wins unconditionally.

### CLOSED — duplicate canonical backward helper authority
v0.4 now explicitly freezes `_run_canonical_segment_backward` as orchestration-only delegation to existing `ImaginaireTrainer._run_local_memory_segment_backward`, followed by adapter commit only after delegated success. The new helper is forbidden to reimplement objective/finite/taxonomy/backward/`successful_backward`.

### CLOSED — missing spy symbol whitelist
`run_native_forward_for_test(payloads, locals)` is now explicitly whitelisted with a frozen test-only tensor-spy role.

## Current blockers

### HIGH — plan authority is duplicated between `canonical_plan` and `canonical_transaction.plan`

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.4.md:29-40`
- `cosmos_framework/trainer/__init__.py` formal child `d05f14e`: existing `_run_local_memory_segment_backward`
- `cosmos_framework/model/generator/mot/local_memory_segment.py` formal child `d05f14e`: `LocalMemoryTransaction.validate_success`
- `cosmos_framework/model/generator/mot/c6_runtime_adapter.py` formal child `d05f14e`: `CanonicalSegmentRuntimeAdapter.objective`

**Root cause:** v0.4 introduces fixture key `canonical_plan` independently from `canonical_transaction`. The delegated seam computes the loss using the passed `plan` (`CanonicalSegmentRuntimeAdapter.objective(plan, ...)`), while `transaction.validate_success(...)` validates member identity/count against `transaction.plan`. The formal child has no guard requiring the two plans to be the same object or canonically equal. A caller can therefore supply an external plan with different `n_window`, `ga_effective`, attempt/chain metadata, or other scaling semantics while the transaction independently validates against its own plan. That splits the unique GA authority and can produce a backward scalar not authorized by the transaction that commits the chronology.

**Acceptance:** remove independent plan authority. The canonical trainer branch must derive the plan from `transaction.plan` (preferred), or fail closed before objective construction with an exact identity/equality guard proving the external plan is the same frozen transaction plan. `_run_local_memory_segment_backward` must receive that single authoritative plan. Add a negative CPU fixture proving a mismatched external plan cannot alter objective scaling or reach backward/commit.

### HIGH — `clear_slow_grads` is broadened from Local slow groups to the entire optimizer

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.4.md:32-40`
- `cosmos_framework/trainer/__init__.py` formal child `d05f14e`: `_optimizer_step` and `_run_local_memory_segment_backward`
- inherited production-integration v0.4 transaction contract §2

**Root cause:** v0.4 freezes `clear_slow_grads` as `lambda: optimizer.zero_grad(set_to_none=True)`. Repository truth describes the R09-B skip disposition as dropping the four **Local groups'** `.grad`, and the frozen transaction contract requires clearing partial Local slow-side gradients while preserving already committed fast chronology. `optimizer.zero_grad()` clears every parameter group in the optimizer, including unrelated native gradients accumulated by earlier GA work. The new wiring would therefore broaden a Local transaction failure into destructive global-gradient mutation.

**Acceptance:** freeze a Local-only slow-gradient clear owner with exact authorized parameter-group/source semantics; it must clear only the Local slow parameter groups governed by this transaction and must leave unrelated/native accumulated gradients unchanged. Do not implement this by whole-optimizer `zero_grad`. Add a CPU fixture with at least one unrelated gradient sentinel proving Local failure/skip clears Local slow grads while preserving the unrelated gradient exactly.

### MEDIUM — the supposedly exact file whitelist regresses to shorthand paths

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.4.md:6-19`

**Root cause:** v0.3 used full repository paths; v0.4 supersedes it but lists `mot/production_segment_wiring.py`, `omni_mot_model.py`, `trainer/__init__.py`, etc. without freezing the repository-relative prefixes. This Gate grants implementation authority, so shorthand/basename paths are not an exact whitelist.

**Acceptance:** restore the full child repository paths for all eight entries, with exact `new` vs `existing/modified` status and the same frozen symbols. No basename-only or context-dependent path expansion after approval.

## Non-blocking confirmations

- The test-only marker remains unreachable from real dataloader/config under this Gate.
- `run_native_forward_for_test` is explicitly non-native, in-memory, and performs no model/data/cache/checkpoint I/O.
- Existing `_run_local_memory_segment_backward` remains intended as the sole formula/backward/transaction owner.
- The canonical weighted objective and no-second-`/grad_accum_iter`/no-second-backward constraints remain correct.
- Persistent sidecar/resume, real data/cache/checkpoint I/O, config/default/registry/optimizer selector changes, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1 remain prohibited.

No `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_WIRING_CPU_STATIC` authority is granted. Any remediation changes the formal root and requires fresh review.
