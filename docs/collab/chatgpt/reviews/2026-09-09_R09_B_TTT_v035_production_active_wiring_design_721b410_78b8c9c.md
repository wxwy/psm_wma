# ChatGPT 独立 Production Active Wiring Design v0.6 review

Formal reviewed pair:
- root design SHA: `721b4100624a37edbdd75bb555515b7d7e67c8e1`
- child/Gitlink SHA: `78b8c9cd1389ff523b703d578208f7a221a64af2`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-DESIGN`
- previous formal pair: `a416b2729ac031bddd78488d07c6301a107390cb` / `78b8c9cd1389ff523b703d578208f7a221a64af2`
- request/bookkeeping HEAD: `7abf307a331d2e2001ded68f7098bb1c1713e4e3`
- design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.6.md`

Verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_ACTIVE_WIRING_CPU_STATIC`

## Incremental scope

Fresh docs-only remediation review relative to v0.5. Child is unchanged. v0.6 addresses the sole remaining v0.5 blocker without widening the production API: it explicitly authorizes one narrowly scoped read-only access to the existing `CallBackGroup._callbacks` registration list inside the active trainer branch, freezes exact-class exclusion for `TTTLifecycleCallback`, preserves registration order/arguments/count for all non-excluded callbacks, preserves no-marker use of the original dispatcher, and requires identity/no-mutation/subclass/no-marker parity Evidence.

## Prior blocker closure

1. **CLOSED — trainer-local selective `TTTLifecycleCallback` dispatch is now implementable under the frozen whitelist.**
   - The design no longer claims a nonexistent public callback collection.
   - The only private-field exception is an explicit, read-only, active-branch-only access to `callback_group._callbacks`.
   - Mutation/reordering/caching/re-registration are forbidden; list identity, length and element identity must remain unchanged.
   - Exclusion is exact `type(callback) is TTTLifecycleCallback`; subclasses are intentionally not implicitly excluded.
   - Non-TTT callbacks retain registration order, original arguments and exactly-once invocation.
   - No-marker/legacy steps continue to call the original `self.callbacks.<hook>(...)` dispatcher and retain the existing legacy lifecycle route.

2. **CLOSED — active/native GA clock remains frozen from v0.5.** `GAWindowPlan.ga_effective` equals the trainer configured accumulation window; active mode starts only at counter zero, remains active with exact registry/window token across the whole window, forbids no-marker interleaving, and completes exactly at the existing trainer optimizer boundary.

3. **CLOSED — owner sealed preflight/resolve, registry binding, exact marker/native seam, first-member-only retry, legacy isolation, and CPU/static-only scope remain intact from v0.4/v0.5.**

## Current blockers

None.

## Approval scope

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_ACTIVE_WIRING_CPU_STATIC`

This approval authorizes only the v0.6 CPU/static implementation whitelist: `production_active_wiring.py`, `canonical_segment_runtime.py`, `omni_mot_model.py`, `trainer/__init__.py`, `production_segment_bridge.py`, and adjacent CPU/static tests. `utils/callback.py` remains out of scope. It does not authorize producer/packer/dataset/manifest/config/optimizer-selector/checkpoint changes, real data/cache/checkpoint I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T, or LIBERO4IN1. The implementation must be submitted under a new formal root/child pair for independent closure review.
