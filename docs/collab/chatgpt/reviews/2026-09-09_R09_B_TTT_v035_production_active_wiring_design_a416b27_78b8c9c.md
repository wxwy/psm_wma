# ChatGPT 独立 Production Active Wiring Design v0.5 review

Formal reviewed pair:
- root design SHA: `a416b2729ac031bddd78488d07c6301a107390cb`
- child/Gitlink SHA: `78b8c9cd1389ff523b703d578208f7a221a64af2`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-DESIGN`
- previous formal pair: `edea9f9ed199d788c9a3b31b474aa665b503aa93` / `78b8c9cd1389ff523b703d578208f7a221a64af2`
- request/bookkeeping HEAD: `bffaf7338fea910bac2f4c83caa40ca4d3f9fe16`
- design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.5.md`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh docs-only remediation review relative to v0.4. Child is unchanged. v0.5 closes the previous active/native GA-window blocker by binding `GAWindowPlan.ga_effective` to the trainer's configured accumulation window, requiring counter-zero start, exact token/registry continuity, and forbidding active/no-marker interleaving. The callback-isolation direction is also correct, but the proposed trainer-local filtered dispatcher relies on a callback collection that does not exist in the current code under the stated whitelist/encapsulation constraints.

## Prior blocker status

1. **CLOSED — active optimizer-window / native trainer GA boundary.** v0.5 requires `initial_plan.ga_effective == config.trainer.grad_accum_iter`, start only at `grad_accum_iter == 0`, exact same registry/window token for every member, no active/no-marker interleaving, and final completion exactly at the existing optimizer boundary.

2. **NOT CLOSED — selective `TTTLifecycleCallback` dispatch.** See current blocker below.

## Current blocker

1. **MEDIUM — v0.5 requires a trainer-local filter over a "public callback collection", but the current `CallBackGroup` exposes no public callback collection, while `utils/callback.py` is explicitly excluded from the whitelist and the design forbids relying on unfrozen private callback internals.**
   - design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.5.md` §3, §5
   - current code: `cosmos_framework/utils/callback.py::CallBackGroup`

   `CallBackGroup` currently stores callbacks only in the private field `self._callbacks`; its public behavior is dynamic `__getattr__`, which always dispatches the requested hook to every callback in registration order. There is no public iterable callback collection and no exclude/filter method. Therefore the proposed trainer helper `_dispatch_callbacks(callback_group, hook_name, exclude_ttt_lifecycle=...)` cannot both (a) skip exact `TTTLifecycleCallback` instances while preserving the remaining order and (b) avoid reading private callback internals, unless a new supported access/filter surface is added.

   **Acceptance:** freeze one implementable option. Either:
   - add `cosmos_framework/utils/callback.py` and adjacent tests to the whitelist, and expose a minimal ordered filtered-dispatch/public-iteration API used by trainer; or
   - explicitly authorize and freeze trainer access to `callback_group._callbacks` as part of this Gate, including object-identity/order invariants and tests, rather than claiming the collection is public.

   CPU/static Evidence must prove active step skips only exact `TTTLifecycleCallback` objects, preserves every non-TTT callback's registration order/arguments/count, and no-marker continues using the original dispatcher unchanged.

## Scope boundary

No implementation authority is granted for this formal pair. It remains docs-only. No child production wiring/model/trainer/runtime-owner implementation, producer/packer/dataset/manifest/config/optimizer-selector/checkpoint change, real I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized.

Requested approval literal remains reserved for a corrected formal pair:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_ACTIVE_WIRING_CPU_STATIC`
