# ChatGPT 独立 Production Segment Integration Design v0.2 review

Formal reviewed pair:
- root design SHA: `1359c762c84eb5f957baf286a87ce72cd82fb128`
- child/Gitlink SHA: `556e278946b506195a57d0798b2b1a2e8b5eb9cc`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-SEGMENT-INTEGRATION-DESIGN`
- previous formal pair: `454c06086a6b2d198dd726feed66d2edb1b8d4f0` / `556e278946b506195a57d0798b2b1a2e8b5eb9cc`
- upstream closed runtime-owner authority: `e74184ee8ef76c2618658c2bf9cc12ab4d183e8a` / `556e278946b506195a57d0798b2b1a2e8b5eb9cc`
- request/bookkeeping HEAD observed: `df9e92cce66060a6ce9bde7aca4124b07e25760a`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh docs-only remediation review relative to v0.1. Child is unchanged. The new v0.2 correctly freezes a per-member bridge call, one batched native callback, first-member vs continuation behavior, `NativeBatchResult`, `actual_n_valid`, and a new non-disposition trainer seam. Those changes close the two v0.1 blockers as originally stated, but the resulting bridge still conflicts with inherited v0.3.5 / v0.4 transaction semantics in three places.

## Prior blocker closure

- **CLOSED — bridge/native execution unit and return ABI.** `run_member(...)` is now explicitly one GA member; continuation uses the same transaction without a second `begin()`, and the native callback is exactly one batched invocation over the whole gathered `(payloads, locals)` tuple.
- **CLOSED — trainer/runtime double-disposition direction.** v0.2 explicitly removes transaction disposition from the new trainer bridge seam and assigns failure disposition to the runtime-owner side.

## Current blockers

1. **HIGH — retry is not executable through the frozen `run_member(first_member=...)` state machine after `begin_retry()`.**
   - design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_segment_integration_design_v0.2.md` §1-§2
   - current owner: `cosmos_framework/model/generator/mot/canonical_segment_runtime.py` (`abort_retry`, `begin_retry`)

   v0.2 specifies `transient -> owner.abort_retry -> begin_retry(exact suffix)`. The current owner then lands in `MEMBER_READY` with the retained failed identity and attempt-1 transaction. However the public bridge has only two entry modes: `first_member=True` performs `admit -> begin`, while `first_member=False` requires `MEMBER_COMMITTED` and performs `admit_next`. Neither mode is legal for the already-admitted `MEMBER_READY` retry member. If `run_member()` returns immediately after `begin_retry()`, there is no legal next call. If it silently continues internally, that retry-loop behavior and callback cardinality are not frozen and contradict the simple “one member / one callback” wording.

   **Acceptance:** freeze one exact retry execution path. For example, make `run_member` explicitly support a retained retry mode that starts from owner `MEMBER_READY` without any new admission/begin, or define that the same call internally executes attempt-1 after `begin_retry()` and state exactly how many callback/backward attempts are permitted. CPU/static Evidence must cover attempt-0 transient -> exact suffix -> attempt-1 prepare/native/backward/success or terminal, with no duplicate admission and no stale attempt-0 capability reuse.

2. **HIGH — `_run_local_memory_bridge_backward` does not preserve the frozen pre-backward validation/finite ordering and its `BridgeBackwardResult` outcomes are under-specified.**
   - design: v0.2 §2
   - frozen contract: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.4.md` §2
   - current source: `LocalMemoryTransaction.validate_success()` and `CanonicalSegmentRuntimeAdapter.objective()`

   v0.2 says the new trainer seam only checks planned/actual, computes `plan.objective`, and runs backward. The inherited contract is stricter: exact identity/order/count precheck must happen before backward, and raw primary/auxiliary loss must pass the existing finite predicate before graph mutation. `plan.objective()` by itself does not perform the current `CanonicalSegmentRuntimeAdapter.objective()` finite check, and the design does not require `transaction.validate_success(member_index, identity, actual_n_valid)` before backward. If identity/order is invalid, deferring validation to the later `transaction.successful_backward()` would detect it only after gradients have already been mutated.

   The result enum is also not executable as written: a seam whose only inputs are objective/backward data has no GradScaler object and no load/decode callback outcome, so it cannot independently originate `scaler_skip` or `transient`. Callback exceptions are separately declared terminal. Implementation would have to invent hidden inputs or classification rules.

   **Acceptance:** freeze the exact `_run_local_memory_bridge_backward` signature and order: exact transaction/identity/member-index/count validation first, current raw finite predicate second, one objective scaling owner, one backward third, and no transaction disposition. Freeze precisely which exceptions/result codes it may produce. `transient` must originate from an explicitly defined pre-backward callback/source outcome, not from the pure backward seam; numerical/identity/outer classification must be deterministic and tested.

3. **HIGH — GradScaler and real slow-grad cleanup are assigned to the wrong layer / no concrete owner.**
   - design: v0.2 §2-§3
   - frozen training semantics: v0.3.5 §10/§12.2 and production integration v0.4 §2-§3
   - current source: trainer optimizer-step Option-B branch, `CanonicalSegmentRuntimeOwner.abort_*`, and `CanonicalSegmentWiring.clear_local_slow_grads()`

   Frozen Option-B semantics say GradScaler skip is known only after backward has completed at the optimizer boundary; the already-completed fast-state/cursor commits remain valid, while the slow optimizer/LR do not advance and slow grads are cleared. v0.2 instead makes `scaler_skip` a per-member backward result and maps it to `owner.abort_scaler_skip`, whose current semantics discard the PREPARED pending capability before `successful_backward/owner.commit`. Wiring a real scaler decision this way would roll back the very fast commit that v0.3.5 explicitly preserves.

   Separately, v0.2 says the new trainer seam does **not** clear grads. Current runtime-owner `abort_terminal/abort_retry/abort_scaler_skip` mutate the transaction and discard pending state but do not call `wiring.clear_local_slow_grads()`. `LocalMemoryTransaction.slow_grads_cleared=True` is only a contract flag; it does not zero actual parameter `.grad`. Thus backward/terminal failure can leave partial Local slow grads live even though the inherited contract requires cleanup and no slow step.

   **Acceptance:** do not use the per-member backward seam to originate a real GradScaler skip. Keep scaler resolution at an explicit post-backward optimizer/window boundary where completed fast commits are retained, slow optimizer/LR are skipped, and actual Local slow grads are cleared. Separately freeze exactly which bridge/owner method calls `owner.wiring.clear_local_slow_grads()` for terminal/retry/failure cleanup, and prove exactly one real grad-clear plus exactly one transaction disposition plus exactly one pending discard. Add CPU/static Evidence with nonzero preexisting/partial Local grads, not just the transaction boolean flag.

## Scope boundary

No implementation authority is granted for this pair. It remains docs-only. No child production bridge/trainer/runtime-owner changes, real SegmentBatch producer/packer, dataset/cache/checkpoint I/O, model execution, config/default/registry changes, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized.

Requested approval literal remains reserved for a corrected formal pair:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_SEGMENT_INTEGRATION_CPU_STATIC`
