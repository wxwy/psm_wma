# ChatGPT 独立 Production Active Wiring CPU/static implementation closure remediation v2 review

Formal reviewed pair:
- root implementation SHA: `27b60046080290adeb574281f8fcdedf5840439b`
- child/Gitlink SHA: `19394c2824d36728976a9df680eab839cfd915e0`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-CPU-STATIC-IMPLEMENTATION`
- previous formal pair: `5d548d97029302817efeaad49983a2a16883be6e` / `3b3d83c33b54a14d52ce54f97e920875f9b48e4e`
- approved design pair: `721b4100624a37edbdd75bb555515b7d7e67c8e1` / `78b8c9cd1389ff523b703d578208f7a221a64af2`
- approved design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.6.md`, retaining v0.5/v0.4/v0.3 retry/native/GA contracts
- request/bookkeeping HEAD observed: `f86cad3c13500a46a88bcde5b298be8d013b8974`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh incremental review relative to `5d548d9 / 3b3d83c`. Root formal diff is collaboration records plus Gitlink update. Child is one remediation commit ahead of the previous child and changes only approved whitelist surfaces: `production_active_wiring.py`, `omni_mot_model.py`, `trainer/__init__.py`, and adjacent CPU/static tests. No producer/packer/dataset/manifest/config/optimizer-selector/checkpoint file changed.

The request reports targeted CPU/static pytest `47 passed in 29.43s`, target `py_compile`, and root/child `git diff --check` PASS. These are request Evidence and were not independently rerun by this reviewer. Code and fixtures were independently inspected against the frozen design and prior ChatGPT blockers.

## Previous blocker status

1. **CLOSED — production active path no longer enters the test-only native seam.**
   `OmniMoTModel._run_active_local_memory_native_forward()` now fail-closes with `active Local native MoT adapter is unavailable`; the synthetic native spy moved to a test-only subclass. This matches the prior acceptance that CPU/static wiring may close without pretending the future real native MoT adapter exists.

2. **CLOSED FOR FIRST ATTEMPT — tagged first-member retry is now integrated into the standard trainer control path.**
   `_run_active_forward_with_exact_retry()` catches the exact tagged first transient, retains the owner-created attempt-1 authority, re-arms the same `SegmentBatch` without another dataloader fetch or GA advance, and executes one retry in-process.

3. **CLOSED — retry identity / active backward fail-closed.**
   `prepare_retry()` derives identity from `owner.begin_retry()` rather than accepting a caller identity. Active backward validates `transaction.validate_success(...)` before scaled backward and owner-terminalizes identity/numerical/backward failure.

4. **CLOSED — optimizer exact-chain preflight.**
   `_preflight_active_optimizer_boundary()` binds open registry, completed registry, owner, transaction, and GA counter before optimizer callbacks/step and has open-incomplete/foreign-completion negatives.

5. **CLOSED — optimizer-window token retirement.**
   `retire_resolved_window()` clears `_ga_window_token` only after exact owner resolution to IDLE; the next optimizer window receives a fresh token.

6. **PARTIALLY CLOSED — Evidence matrix.**
   Two-consumer ordered S0/PAD, first-attempt in-process retry, enabled-scaler success/skip, optimizer preflight negatives, and consecutive-window token freshness are now directly witnessed. Remaining Evidence issue is below.

## Current blockers

1. **HIGH — a second tagged transient on the allowed attempt-1 retry is not terminalized; `abort_retry()` can raise `LOCAL_MEM_RETRY_EXHAUSTED` before pending discard/owner terminal cleanup.**
   - implementation: `cosmos_framework/model/generator/mot/production_active_wiring.py::ProductionActiveWiringRegistry.abort_source_transient`
   - owner/transaction: `canonical_segment_runtime.py::abort_retry`, `local_memory_segment.py::GAWindowPlan.suffix_after_failure`
   - trainer integration: `trainer/__init__.py::_run_active_forward_with_exact_retry`
   - violated contract: retained v0.3/v0.4 retry policy — only the initial attempt may retry; attempt-1 transient must be terminal/process-fatal and must not create another suffix retry.

   `abort_source_transient()` currently checks only `member_index != 0` or `completed_members`. For the retried first member, `member_index == 0` and `completed_members == []`, so a second `ActiveSourceTransientError` still enters `owner.abort_retry(...)`. The attempt-1 transaction then executes `recover_transient(0) -> plan.suffix_after_failure(0)`, and `GAWindowPlan.suffix_after_failure()` raises `RuntimeError("LOCAL_MEM_RETRY_EXHAUSTED")` because `attempt == 1`.

   That exception occurs inside `owner.abort_retry()` *after* Local slow grads are cleared but *before* `adapter.discard_pending(...)`, before owner fields are cleared, and before phase changes to `RETRY_READY` or `ABORTED`. Therefore the second transient can leave the owner in `PREPARED` with the exact pending graph still retained instead of producing the frozen terminal disposition.

   **Acceptance:** `abort_source_transient()` must explicitly reject `prepared.transaction.plan.attempt == 1` before calling `owner.abort_retry()`. Route that case through exact `owner.abort_terminal(...)` with a frozen retry-exhausted terminal code (compatible: `LOCAL_MEM_RETRY_EXHAUSTED`), clear registry prepared/model/published authority, discard pending, clear Local slow grads, suppress remaining members, and propagate process-fatal failure. Add an actual trainer-path fixture where the same first member raises `ActiveSourceTransientError` twice; prove: first transient retries at counter 0, second transient terminalizes, owner=`ABORTED`, pending `None`, no optimizer/scheduler/fast commit, no third forward.

2. **MEDIUM — v0.6's required adjacent no-marker callback/lifecycle parity is still not directly witnessed.**
   - Evidence file: `cosmos_framework/trainer/active_wiring_callback_test.py`
   - frozen contract: v0.6 §3 requires a pre-existing lifecycle spy and a **neighboring no-marker control** that continues through the original `self.callbacks.<hook>` dispatcher and legacy lifecycle route.

   The current callback Evidence proves exact-class `TTTLifecycleCallback` exclusion and that the active filtered helper does not touch an existing lifecycle. It does not include the required adjacent no-marker trainer control proving the original dispatcher still invokes the real `TTTLifecycleCallback` with preserved order/args/count and legacy lifecycle behavior.

   **Acceptance:** add a no-marker trainer-level control adjacent to the active fixture. It must prove the active branch gives zero lifecycle observe/commit/abort/resolve calls while the no-marker control still uses the original dispatcher and preserves the pre-existing legacy path. Re-run/report the exact formal pair's targeted CPU/static suites, target `py_compile`, and root/child `git diff --check`.

## Scope boundary

No closure authority is granted for this formal pair. This `REQUEST_CHANGES` is limited to the approved v0.6 CPU/static active-wiring implementation Gate. No producer/packer/dataset/manifest/config/optimizer-selector/checkpoint changes, real data/cache/checkpoint I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized.

Requested closure literal remains reserved for a corrected formal pair:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_PRODUCTION_ACTIVE_WIRING_CPU_STATIC`
