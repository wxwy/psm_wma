# ChatGPT 独立 Production Active Wiring Design v0.1 review

Formal reviewed pair:
- root design SHA: `305b791ac6cc4f6cf3a5ebb578fa3a332a6688fb`
- child/Gitlink SHA: `78b8c9cd1389ff523b703d578208f7a221a64af2`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-DESIGN`
- previous closed implementation pair: `1c6c9ec3c5a8befa32875e05e3779357208ead31` / `78b8c9cd1389ff523b703d578208f7a221a64af2`
- request/bookkeeping HEAD observed: `ab887a54f3b8a8cd05d77f1a9e90e41851ba1ab8`
- design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.1.md`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh design review for the new active-wiring Gate. The child is unchanged from the just-closed production-segment-integration implementation pair. Root changes since that formal pair are docs/review/bookkeeping only, including this new v0.1 design.

Review basis is the Codex request, v0.1, frozen v0.3.5 segment semantics, the closed production-segment bridge/runtime-owner contract, and the actual current `OmniMoTModel.training_step` / `_inject_local_history` / `_ttt_local_memory_tokens`, trainer `training_step` / `_optimizer_step`, and `production_segment_bridge.run_member` source. No MM/Kimi/DS conclusion is used.

## Correct direction

- The design correctly recognizes that the old row-wise `TTTLifecycle.process_sample()` / closing-row replay witness path cannot remain the Local-enabled production path under v0.3.5 `[B_stream,T]` segment semantics.
- It keeps `SegmentBatch`, `CanonicalSegmentRuntimeOwner`, `CanonicalSegmentWiring`, transaction-owned valid-count weighting, post-backward fast commit, and post-window slow-resolution authority.
- It correctly keeps dataset/packer/config/checkpoint/real I/O/GPU/training outside this CPU/static design Gate.
- It explicitly requires the test-only `_canonical_local_memory_segment_forward` / `run_native_forward_for_test` path not to become production.

Those directions are necessary but the production orchestration is not yet frozen tightly enough for a unique implementation.

## Current blockers

1. **HIGH — native forward/callback cardinality in v0.1 contradicts the already-closed batched bridge contract.**
   - design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.1.md:23-35,57-59`
   - frozen upstream: production-segment design v0.3 §1 and v0.3.5 addendum §§6,18.

   v0.1 §3 describes gather -> native Cosmos forward, but §6 requires CPU/static Evidence for `one native callback per gathered consumer`. That reopens the exact cardinality ambiguity already closed in the production-segment Gate. The frozen bridge contract is one **batched** native callback per GA member/microbatch over the entire gathered `(payloads, locals)` tuple; multiple valid consumers are parallel entries in that one callback. v0.3.5 likewise requires gather valid consumers -> one Cosmos batch forward -> one backward for the microbatch.

   **Acceptance:** replace every per-consumer callback/forward wording with one exact batched native-forward contract. Freeze that one Local-enabled member invokes the native model seam exactly once with the whole gathered ordered batch; each valid consumer appears exactly once as an entry, PAD appears zero times, and no per-consumer loop may call the model. CPU/static Evidence must include at least two valid consumers and prove exactly one native seam invocation containing both entries.

2. **HIGH — the model/trainer/bridge split-phase execution contract is not frozen and currently conflicts with the APIs that actually exist.**
   - design: `...production_active_wiring_implementation_design_v0.1.md:21-41,45-52`
   - current model: `cosmos_framework/model/generator/omni_mot_model.py` methods `_inject_local_history`, `_ttt_local_memory_tokens`, `_canonical_local_memory_segment_forward`, `training_step`.
   - current trainer: `cosmos_framework/trainer/__init__.py::training_step`.
   - current bridge: `cosmos_framework/model/generator/mot/production_segment_bridge.py::run_member`.

   Current `run_member` is a monolithic authority: it performs entry validation/admission, `owner.prepare`, calls the one native callback, performs the pure backward, then owner disposition/commit/finish. Current trainer, however, calls `model_ddp.training_step(...)` first and only afterwards enters the normal backward section. v0.1 now says the model seam should execute the real native forward inside ordinary `training_step`, while the trainer should later call the bridge pure-backward. No approved public API currently represents the graph-bearing state between those two phases.

   Therefore implementation would have to choose one of several incompatible behaviors that the design does not authorize: call `run_member` inside model forward (which performs backward/commit before trainer callbacks and before the normal backward phase), bypass `run_member` and duplicate its owner state machine in model/trainer, or invent a new split-phase capability/API. The same ambiguity affects legacy supersession: current ordinary `_get_training_inputs -> _inject_local_history` calls `_ttt_local_memory_tokens()` when `local_ttt_enabled`, which creates/uses the old lifecycle before the ordinary native forward. v0.1 says the new path must bypass it but does not freeze the exact branch point/marker schema that prevents both paths from running.

   **Acceptance:** freeze one exact production execution API and capability chronology before implementation. A compatible design is an explicit split-phase bridge: e.g. an owner-created `PreparedActiveMemberCapability` from admission/prepare/gather, consumed exactly once by the model-native batched forward, followed by an exact trainer completion capability that owns scaled backward + owner commit/abort. Whatever names are chosen, freeze public signatures, exact object-identity checks, phase transitions, which layer owns each call, and stale/substitute/double-consumption rejection. Also freeze the exact `OmniMoTModel.training_step` branch point so the active marker bypasses `_inject_local_history/_ttt_local_memory_tokens` before the legacy lifecycle can be created or observed, while the no-marker path remains byte/behavior equivalent.

3. **HIGH — GA-window / GradScaler clock and Local-enabled backward scaling are not frozen for the real trainer path.**
   - design: `...production_active_wiring_implementation_design_v0.1.md:23-41,57-61`
   - frozen upstream: v0.3.5 §§7.1,10.2,11,12.2.
   - current trainer: `ImaginaireTrainer.training_step` and `_optimizer_step`.

   Frozen v0.3.5 defines two separate clocks: one `[B_stream,T]` graph/backward/fast-commit per microbatch, while slow gradients accumulate across exactly one GA optimizer window. Its outer objective already provides `N_valid_micro / N_valid_window` scaling and degenerates to `1/GA` for full microbatches. Slow mixed precision must still follow the native recipe.

   Current normal trainer backward is `grad_scaler.scale(loss / grad_accum_iter).backward()`. The closed CPU bridge pure seam instead calls raw `loss.backward()` because it is a CPU/static contract. v0.1 says the trainer should call the bridge pure-backward for the active path but never freezes how the real GradScaler is applied, whether `/grad_accum_iter` is omitted (it must not be applied a second time when the transaction objective already owns GA weighting), or how `GAWindowPlan` member progress is synchronized with trainer `grad_accum_iter`.

   It also does not freeze how a transient retry affects the trainer GA counter, how the final `CompletedWindowCapability` is guaranteed to coincide with the native optimizer boundary, or the exact point at which the actual scaler-skip verdict is captured and consumed without invoking `TTTLifecycle` resolution. Leaving this to implementation can cause double GA scaling, unscaled mixed-precision backward, optimizer-step before/after the transaction window, or an off-by-one retry/accumulation clock.

   **Acceptance:** freeze the production trainer clock explicitly. At minimum: one successful bridge member == one successful trainer accumulation microbatch; transient retry does not advance `grad_accum_iter`; terminal failure does not silently continue the window; initial plan start and `ga_effective` are tied to the current optimizer window; final member completion must coincide with the optimizer boundary. Freeze the Local-enabled backward as exactly one `grad_scaler.scale(transaction-plan-weighted objective).backward()` with no second `/grad_accum_iter`/GA division. Freeze the exact `step -> found_inf/skip determination -> completed-capability resolution -> scaler update / scheduler / zero_grad` ordering (or an equivalent proven native ordering), including success vs skip and one-shot capability consumption. CPU/static tests must model the counters and scaler result seam without running CUDA.

## Scope boundary

No implementation authority is granted for this formal pair. It remains docs-only. No child implementation, packer/dataset/config/checkpoint change, real data/cache/checkpoint I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized.

Requested approval literal remains reserved for a corrected formal pair:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_ACTIVE_WIRING_CPU_STATIC`
