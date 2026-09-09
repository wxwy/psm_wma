# ChatGPT 独立 Production Active Wiring Design v0.4 review

Formal reviewed pair:
- root design SHA: `edea9f9ed199d788c9a3b31b474aa665b503aa93`
- child/Gitlink SHA: `78b8c9cd1389ff523b703d578208f7a221a64af2`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-DESIGN`
- previous formal pair: `a357e5ce7eec842f19db2e30db2b045e840bb54c` / `78b8c9cd1389ff523b703d578208f7a221a64af2`
- request/bookkeeping HEAD: `9b34a15b360c0635d599804303b5d14270c89f6c`
- design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.4.md`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh docs-only remediation review relative to v0.3. Child is unchanged. v0.4 closes the previous registry-binding, owner-sealed-resolution, and pre-existing-legacy-isolation findings in substance, but fresh review found one remaining optimizer-window clock ambiguity and one selective-callback dispatch implementability gap.

## Prior blocker closure

1. **CLOSED — registry binding / pre-forward runtime capability creator.** v0.4 now freezes one trainer-created `ProductionActiveWiringRegistry`, object-identically binds it to trainer and model, requires trainer main-process pre-forward preparation/injection, forbids loader/worker capability transport, and makes every runtime capability carry the exact registry object.

2. **CLOSED — owner-level preflight/sealed deterministic resolve surface.** `canonical_segment_runtime.py` is now explicitly whitelisted and the design freezes owner-created `preflight_slow_window(...)` plus `resolve_preflighted_slow_window(...)`.

3. **CLOSED IN INTENT — active step must isolate a pre-existing legacy lifecycle.** v0.4 explicitly forbids legacy observe/commit/abort/resolve during active forward/backward/optimizer handling and requires a pre-existing lifecycle spy fixture.

## Current blockers

1. **HIGH — the active optimizer window is still not bound to the trainer's existing accumulation boundary, so active and no-marker microbatches can be mixed or stepped on different clocks.**
   - design: v0.4 §§2-4
   - current trainer: `ImaginaireTrainer.training_step`, whose optimizer step is triggered by `grad_accum_iter == self.config.trainer.grad_accum_iter`.

   v0.4 says the final active member may complete only when `grad_accum_iter + 1 == ga_effective`, but it never freezes either `GAWindowPlan.ga_effective == self.config.trainer.grad_accum_iter` or an explicit active-path replacement for the trainer's existing optimizer trigger. It also says that when there is no active admission authority the trainer passes the normal batch through unchanged, without defining what happens if that occurs after an active optimizer window has already begun.

   Therefore an implementation can legally reach several inconsistent states: active plan length shorter/longer than trainer configured accumulation, active window starting mid normal accumulation, or a no-marker batch being accumulated between members of one active `ga_window_token`. In each case the transaction-weighted objective and the actual optimizer boundary no longer describe the same window.

   **Acceptance:** freeze one exact optimizer-window mode contract. Minimal compatible form: active window may start only at `grad_accum_iter==0`; at start require `initial_plan.ga_effective == self.config.trainer.grad_accum_iter`; once active begins, every accumulation microbatch until exact final completion must come from the same registry/`ga_window_token` and be active; no-marker/legacy batch during an open active window, or active start during a nonzero normal window, fails before model forward/backward with zero optimizer/owner mutation. Alternatively explicitly supersede the trainer optimizer trigger for active mode, but the exact branch and counter reset semantics must be frozen. Add CPU/static tests for mismatched GA length and active/no-marker interleaving.

2. **MEDIUM — selective skipping of only `TTTLifecycleCallback` is not implementable through the current callback dispatcher under the stated whitelist without relying on an unfrozen private-list bypass.**
   - design: v0.4 §5-6
   - current callback dispatcher: `cosmos_framework/utils/callback.py::CallBackGroup.__getattr__`, which unconditionally iterates every callback and exposes no exclude/filter API.

   v0.4 requires generic callbacks to retain their existing order while `TTTLifecycleCallback.on_before_backward/on_after_backward` alone is skipped on active steps. `utils/callback.py` is not in the implementation whitelist. The trainer could only achieve this by directly iterating the private `self.callbacks._callbacks` list or by skipping all callbacks, neither of which is frozen by the design.

   **Acceptance:** freeze one supported selective-dispatch mechanism. Either add `cosmos_framework/utils/callback.py`/adjacent tests to the whitelist and define a filtered dispatch API, or explicitly authorize a trainer-local filtered dispatcher with exact `TTTLifecycleCallback` type exclusion while preserving all other callback order/arguments. CPU/static Evidence must prove: active step calls non-TTT callbacks in the same order as normal, calls TTT lifecycle hooks zero times, and no-marker behavior is unchanged.

## Scope boundary

No implementation authority is granted for this pair. It remains docs-only. No child production wiring/model/trainer/runtime-owner implementation, packer/dataset/manifest/config/optimizer-selector/checkpoint change, real I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized.

Requested approval literal remains reserved for a corrected formal pair:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_ACTIVE_WIRING_CPU_STATIC`
