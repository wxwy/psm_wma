# ChatGPT 独立 Production Active Wiring Design v0.3 review

Formal reviewed pair:
- root design SHA: `a357e5ce7eec842f19db2e30db2b045e840bb54c`
- child/Gitlink SHA: `78b8c9cd1389ff523b703d578208f7a221a64af2`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-DESIGN`
- previous formal pair: `440082a245a0a7ab21df20d1bded8813c0ccc35e` / `78b8c9cd1389ff523b703d578208f7a221a64af2`
- request/bookkeeping commit: `09595449147e85e535909d19dc65a250190e7780`
- latest bookkeeping HEAD observed: `cb1a335b0b17616f3a3949c4a9d9bd8585ff8c63`
- design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.3.md`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh docs-only remediation review relative to v0.2. Child is unchanged. v0.3 substantially closes the three prior findings: it chooses first-member-only retry, adds a pre-step sealed optimizer preflight, and freezes concrete active marker/model/output keys plus a non-callable Mapping payload boundary. Fresh review found two remaining authority/implementability gaps and one legacy-isolation Evidence gap.

## Prior blocker status

1. **CLOSED — suffix retry / original optimizer-window gradient mixing.** v0.3 chooses the minimal safe policy: transient retry is permitted only when `completed_members==()` and trainer `grad_accum_iter==0` before any active backward succeeds. Any later-member transient is terminal/process-fatal and cannot start an in-process suffix optimizer window.

2. **CLOSED IN INTENT — optimizer-boundary preflight is moved before irreversible optimizer mutation.** v0.3 requires exact completed-capability/counter preflight before optimizer callbacks and `grad_scaler.step`, then a sealed success/skip path.

3. **CLOSED — production marker/native-model handoff surface is materially frozen.** Exact marker/output keys are named, caller-supplied callback/function fields are forbidden, `ActiveNativeBatchInputs` is a non-callable Mapping boundary, and the model-internal `_run_active_local_memory_native_forward(...)` seam is named.

## Current blockers

1. **HIGH — the exact active-wiring registry instance and the pre-forward creator/injector of `PreparedActiveMemberCapability` are not frozen, so the object-identity authority chain is still not uniquely executable.**
   - design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.3.md` §§2-3, §6
   - current trainer: `cosmos_framework/trainer/__init__.py::training_step`
   - current model: `cosmos_framework/model/generator/omni_mot_model.py::training_step`

   v0.3 states that `production_active_wiring.py` is the unique capability registry and that both capabilities are registry-created object-identity authorities. However, the frozen `PreparedActiveMemberCapability` fields do not include the exact registry object, while the model pseudocode calls `registry.consume_prepared_for_model(prepared)` without defining where that exact registry instance comes from. The trainer completion/preflight path has the same unresolved registry lookup.

   More importantly, the active model ABI requires `data_batch["psm_local_memory_prepared"]` to already contain a non-serializable, non-cross-process runtime capability, but the design does not freeze which in-process layer calls `prepare_active_member(...)` and injects that exact object before `model_ddp.training_step(...)`. The future data/packer producer is explicitly deferred and cannot legitimately serialize this runtime owner/transaction capability through the data loader. Current trainer directly forwards its `data` object to the model, so an implementation must otherwise invent one of several incompatible orchestration points.

   **Acceptance:** freeze one exact registry-binding and pre-forward orchestration contract. For example: bind one `ProductionActiveWiringRegistry` object to the trainer/model runtime; every `PreparedActiveMemberCapability` and `ActiveForwardCapability` carries or is object-identically registered to that exact registry; `ImaginaireTrainer.training_step` (or another explicitly named main-process method in the approved whitelist) calls `registry.prepare_active_member(...)` before `model_ddp.training_step`, injects the returned prepared object into a shallow active marker envelope, and later uses the same registry for completion/preflight/resolve. No loader/worker/producer may manufacture or transport prepared capabilities. Reconstructed/equal capability or a second registry must fail before model forward/backward with zero owner mutation. Freeze exact method signatures/keys and add CPU/static fixtures for wrong-registry and reconstructed-capability rejection.

2. **HIGH — the promised post-step deterministic sealed resolution cannot be implemented literally with the current owner API while `canonical_segment_runtime.py` is outside the whitelist.**
   - design: v0.3 §5-6
   - current owner: `cosmos_framework/model/generator/mot/canonical_segment_runtime.py::resolve_local_memory_slow_window`

   v0.3 requires `preflight_completed_active_window(...)` to perform all fallible capability/phase/transaction/GA checks before optimizer mutation, and then requires `resolve_preflighted(...)` to perform no further fallible capability/identity/GA validation after `grad_scaler.step`.

   The only currently approved owner slow-window resolution API, `CanonicalSegmentRuntimeOwner.resolve_local_memory_slow_window(...)`, itself performs exact phase, capability-object, owner, transaction and pending-transaction checks before it mutates the transaction and returns the owner to `IDLE`. `canonical_segment_runtime.py` is not in the v0.3 implementation whitelist. Therefore a registry implementation has only two choices, both conflicting with the frozen text: call the existing owner method after `grad_scaler.step` and re-enter a fallible exact-capability validation path, or bypass the owner and directly mutate its transaction/private state, which breaks owner-only authority.

   **Acceptance:** freeze an implementable owner-sealed resolution surface and authorize the required file. Preferred: add `canonical_segment_runtime.py`/adjacent test to the whitelist and split the owner boundary into an owner-created non-mutating preflight/sealed capability plus a deterministic sealed resolve that performs no new identity/boundary checks after optimizer mutation. Alternatively explicitly relax the post-step rule to allow the existing owner resolve only if the design proves those guards are redundant assertions that cannot be invalidated between preflight and step, including optimizer callbacks; this weaker option must still demonstrate that no legitimate stale/substitute/boundary input can reach `grad_scaler.step`. CPU/static negatives must prove zero optimizer/scheduler/owner mutation on all preflight failures.

3. **MEDIUM — active/legacy lifecycle isolation is stated but the required trainer-callback behavior is not witnessed for a pre-existing legacy lifecycle.**
   - design: v0.3 §1, §3, §6
   - current trainer: `ImaginaireTrainer.training_step/_optimizer_step`
   - current legacy callback: `TTTLifecycleCallback`

   The early model branch prevents `_ttt_local_memory_tokens()` from lazily creating the old lifecycle during an active forward. But current trainer still executes generic `on_before_backward` / `on_after_backward` callbacks and the old optimizer resolution path can act whenever `model._ttt_lifecycle` already exists. Because v0.3 explicitly preserves the no-marker legacy path, a lifecycle can pre-exist from an earlier legacy step. The design requires the active path never to create/observe/commit/abort/resolve it, but the CPU/static acceptance only checks the early model branch, not this pre-existing-object case.

   **Acceptance:** freeze the active-step callback/optimizer routing so a pre-existing `_ttt_lifecycle` receives zero observe/commit/abort/resolve calls on an active marker step, without changing no-marker behavior. Add a synthetic fixture with a pre-existing lifecycle spy and prove zero calls throughout forward/backward/optimizer handling.

## Scope boundary

No implementation authority is granted for this formal pair. It remains docs-only. No child production wiring/model/trainer/runtime-owner implementation, packer/dataset/manifest/config/optimizer-selector/checkpoint change, real data/cache/checkpoint I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized.

Requested approval literal remains reserved for a corrected formal pair:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_ACTIVE_WIRING_CPU_STATIC`
