# ChatGPT 独立 Production Active Wiring CPU/static implementation closure follow-up review

Formal reviewed pair:
- root implementation SHA: `5d548d97029302817efeaad49983a2a16883be6e`
- child/Gitlink SHA: `3b3d83c33b54a14d52ce54f97e920875f9b48e4e`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-CPU-STATIC-IMPLEMENTATION`
- previous formal pair: `f24599d92f7447064c7422a43575e38cec843d48` / `acb2bf2c8b4caf5a415b3eaaffa34edf9a514323`
- approved design pair: `721b4100624a37edbdd75bb555515b7d7e67c8e1` / `78b8c9cd1389ff523b703d578208f7a221a64af2`
- approved design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.6.md`, with retained v0.5/v0.4 native/GA/retry contracts
- request/bookkeeping HEAD observed: `2433963a88509f618f16c38d9b9561e951a63cf7`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh incremental review relative to the prior formal implementation pair. Root formal diff is collaboration records plus Gitlink update. Child is six commits ahead of the prior child and changes only approved whitelist surfaces: `production_active_wiring.py`, `trainer/__init__.py`, `production_active_wiring_test.py`, and `active_wiring_callback_test.py`. No producer/packer/dataset/manifest/config/optimizer-selector/checkpoint file changed.

The request reports targeted CPU/static pytest `43 passed in 34.18s`, target `py_compile`, and root/child `git diff --check` PASS. Those are request Evidence and were not independently rerun by this reviewer. Code and fixtures were independently inspected against the frozen design and prior blockers.

## Previous blocker status

1. **CLOSED — retry identity and pre-backward identity failure cleanup.**
   `prepare_retry()` no longer accepts an independent caller identity; it consumes the owner-retained retry identity after `begin_retry()`. Active backward now calls `transaction.validate_success(...)` before scaled backward and owner-terminalizes identity/numerical/backward failure.

2. **PARTIALLY CLOSED — trainer retains and can explicitly consume first-member retry authority.**
   `_handle_active_forward_exception()` now stores the exact attempt-1 retry plan/registry and `arm_active_local_memory_retry()` consumes it at counter zero. However the standard trainer loop still propagates the tagged transient out of `training_step()`, so the in-process retry contract is not yet executable by the actual production trainer flow. See HIGH blocker 2.

3. **CLOSED — optimizer boundary exact registry/owner/transaction/GA preflight.**
   `_preflight_active_optimizer_boundary()` now rejects open-incomplete and foreign/mismatched completed authority before optimizer callbacks/step.

4. **NOT CLOSED — active-specific Evidence matrix remains incomplete.** See MEDIUM blocker 4.

## Current blockers

1. **HIGH — the production active model branch still invokes the explicitly test-only `run_native_forward_for_test()` instead of the ordinary MoT native forward/loss surface.**
   - implementation: `cosmos_framework/model/generator/omni_mot_model.py::_run_active_local_memory_native_forward`
   - frozen contract: active-wiring v0.1 §4 and retained v0.3 §2 / v0.5 §4.

   The frozen design explicitly states that `_canonical_local_memory_segment_forward` and `run_native_forward_for_test` are test-only and must not enter production. The production active branch must inject gathered Local tokens into the existing Memory Prefix/native MoT path and execute one batched ordinary model forward/loss. Current `_run_active_local_memory_native_forward()` instead calls `run_native_forward_for_test(...)`, a pure tensor spy that never runs the native MoT model/loss. Therefore the production marker can complete prepare -> forward -> backward -> owner commit without exercising the production model seam at all.

   **Acceptance:** remove the production dependency on `run_native_forward_for_test`. The production model method must route to the model-owned ordinary batched MoT forward/loss surface with the gathered Local inputs and no caller-supplied callback/function. If concrete payload packing remains intentionally deferred to a later producer ABI Gate, the production method must fail closed until that internal native adapter exists, while CPU/static tests use a test subclass/monkeypatch/internal spy outside the production runtime path. Add static/CPU Evidence proving the production branch does not call the test helper and that the synthetic test spy is test-only.

2. **HIGH — the retained first-member retry authority still does not form an executable in-process retry in the standard trainer loop.**
   - implementation: `ImaginaireTrainer.training_step`, `_handle_active_forward_exception`, `arm_active_local_memory_retry`
   - frozen contract: retained v0.3/v0.4 retry policy — first-member transient may retry at counter zero; later transient is terminal/process-fatal; retry must not advance the trainer counter/optimizer/scheduler/fast frontier.

   On `ActiveSourceTransientError`, `_handle_active_forward_exception()` correctly calls `abort_source_transient(...)` and retains the exact attempt-1 plan/registry, but `training_step()` immediately re-raises the exception. The ordinary `train()` loop calls `training_step()` without an exact tagged-retry catch/re-arm path, so the process exits instead of consuming `arm_active_local_memory_retry()`. The new unit tests prove the handler and retry-arm APIs separately, not the actual production trainer control flow.

   **Acceptance:** freeze and implement one production trainer control path that consumes the retained retry authority without advancing `grad_accum_iter`: either an exact tagged-retry outcome returned to the same main-process orchestration or a narrow catch/re-arm/re-execute path in the trainer loop. It must retain the exact retry SegmentBatch/plan/registry authority needed for retry and must not fetch/advance a different member. CPU/static Evidence must drive tagged first-member transient through the actual trainer control path -> exact retry -> successful member, with unchanged counter/optimizer/scheduler/fast frontier before retry. Later-member tagged transient must remain process-fatal.

3. **MEDIUM — `ga_window_token` is never retired after exact slow-window resolution, so consecutive optimizer windows reuse the same token.**
   - implementation: `ProductionActiveWiringRegistry._ga_window_token`
   - frozen contract: v0.5 §2 open-token continuity and closure at the final completed/sealed resolution.

   `_ga_window_token` is created when `None`, retained across retry/continuation as intended, but no success/skip resolution path clears it. After owner resolution returns to `IDLE`, a later `prepare_initial()` reuses the previous window token. This weakens the window identity contract and prevents the token from representing one exact optimizer window.

   **Acceptance:** retire the exact token only after successful/skip final slow-window resolution, while preserving it across first-member retry and all members of the same active window. The next initial window must receive a fresh object. Add a two-consecutive-window fixture asserting retry/member continuity within one window and token inequality across resolved windows.

4. **MEDIUM — the active closure Evidence matrix still does not directly witness several frozen invariants.**
   The reported `43 passed` materially improves coverage: wrong identity, exact retry arm, tagged handler retention, open/no-marker interleave, foreign optimizer completion, two-member GA, enabled scaler success/skip, marker rejection and legacy callback isolation are now represented. However the active-specific suite still does not directly prove:
   - at least two valid consumers in one active batched native seam with ordered entries, S0=None and PAD absent;
   - a complete production-trainer tagged transient -> retained retry -> re-arm -> successful member sequence;
   - two consecutive resolved active windows with fresh `ga_window_token`;
   - the required adjacent no-marker original-dispatch / pre-existing lifecycle parity through the full trainer path rather than helper-only lifecycle isolation.

   **Acceptance:** add the missing CPU/static fixtures after the production blockers are fixed and rerun/report the exact new formal pair's targeted suites, target `py_compile`, and root/child `git diff --check`. Evidence must demonstrate the active production control path invariants rather than only helper-level components.

## Scope boundary

No closure authority is granted for this formal pair. This `REQUEST_CHANGES` is limited to the CPU/static active-wiring implementation Gate. No producer/packer/dataset/manifest/config/optimizer-selector/checkpoint changes, real data/cache/checkpoint I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized.

Requested closure literal remains reserved for a corrected formal pair:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_PRODUCTION_ACTIVE_WIRING_CPU_STATIC`
