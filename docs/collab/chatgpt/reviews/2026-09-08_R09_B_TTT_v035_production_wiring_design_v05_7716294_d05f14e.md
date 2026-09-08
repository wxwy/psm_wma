# ChatGPT independent review — Local Memory v0.3.5 production wiring design v0.5

Formal reviewed pair:
- root design SHA: `7716294794cba108c42bafcc78feb0a24a427e45`
- child/Gitlink SHA: `d05f14e7195ee5efc37f9d9955923d51fd4e4b25`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-WIRING-RUNTIME-SIDECAR-DESIGN`

Verdict: `REQUEST_CHANGES`

Fresh incremental review relative to `a4556b2 / d05f14e`; prior verdict not inherited.

## CLOSED from prior review

1. **CLOSED — single GA plan authority.** v0.5 removes `canonical_plan` from the model output, freezes the sole plan as `transaction.plan`, requires external plan fixture input to fail closed before objective/backward/commit, and delegates that exact object to the existing `_run_local_memory_segment_backward` seam.
2. **CLOSED — Local-only slow-gradient clearing.** `CanonicalSegmentWiring` now owns an explicit tuple of Local slow parameters; `clear_local_slow_grads()` clears only those `.grad` references and the acceptance includes an unrelated-gradient sentinel. The prior whole-optimizer `optimizer.zero_grad()` behavior is removed from the contract.
3. **CLOSED — exact whitelist paths.** All eight child paths are restored to full repository-relative paths with exact `new` vs `existing/modified` status.

## Current blocker

### HIGH — v0.5 supersedes v0.4 but no longer freezes a complete model→trainer capability/data ABI

Locations:
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.5.md:20-32`
- prior v0.4 ABI for comparison: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.4.md:30-38`
- formal child `cosmos_framework/model/generator/mot/local_memory_segment_adapter.py:45-79`

Root cause:
- v0.5 explicitly supersedes v0.4 and states that model output "仅携带" `canonical_transaction`, `canonical_member_index`, `canonical_identity`, and `canonical_segment_forward`.
- The orchestration immediately below requires `wiring.clear_local_slow_grads` and then `adapter.commit(...)`, but neither the listed output nor the previously frozen `CanonicalSegmentForward` supplies the exact `CanonicalSegmentWiring` object / adapter capability.
- The same v0.5 output list also omits `primary_consumer_mean`, `auxiliary_loss`, and `actual_n_valid`, although the delegated existing seam requires all three arguments.
- The formal child adapter is deliberately exact-result and exact-transaction bound: commit must use the adapter instance whose pending scan contains the same identity, transaction and `SegmentScanResult`. Therefore the implementation cannot safely obtain an arbitrary adapter/wiring through hidden model state, globals, or reconstruction.

This is not a cosmetic omission. Under the implementation authority requested by this design, the trainer bridge cannot execute the frozen delegation without inventing a second, undocumented capability/data transport path.

Acceptance:
1. Freeze one complete exact output ABI for the marker branch. It must include, directly or through a frozen immutable carrier, the exact values required by `_run_local_memory_segment_backward`: `primary_consumer_mean`, `auxiliary_loss`, `actual_n_valid`, `transaction`, `member_index`, and `identity`.
2. Freeze the exact source of the `CanonicalSegmentWiring` capability used by the trainer branch. Either carry the exact `canonical_wiring` object in `output_batch`, or add an exact field/capability to `CanonicalSegmentForward`; do not use a global/model attribute lookup or reconstruct another wiring/adapter.
3. Prove object identity: the wiring/adapter used for `clear_local_slow_grads` and `commit` must be the same wiring/adapter that produced `forward.result`; `forward.result` must be the exact pending result. A mismatched wiring/adapter/result must fail closed before commit.
4. Preserve the newly closed rules unchanged: `plan is transaction.plan` as the sole GA authority; no external plan; Local-only grad clearing with unrelated-gradient sentinel; disable-first selector; one delegation to `_run_local_memory_segment_backward`; no second formula/finite/taxonomy/backward owner.
5. Add adjacent CPU/static negative fixtures for missing/mismatched capability and mismatched adapter/result, plus the already required weighted-loss/commit/failure witnesses.

No other technical blocker is open in this pair.

This verdict authorizes no production-wiring implementation, persistent sidecar, real data/cache/checkpoint I/O, config/default/registry/optimizer/dataset/manifest/C6 changes, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1.
