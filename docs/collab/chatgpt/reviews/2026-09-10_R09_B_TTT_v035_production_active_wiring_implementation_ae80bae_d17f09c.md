# ChatGPT 独立 Production Active Wiring CPU/static implementation retry-exhaustion closure review

Formal reviewed pair:
- root implementation SHA: `ae80bae6474a81ca0c93f761b6bce8c29f6b4806`
- child/Gitlink SHA: `d17f09c349cad2da93381033749c4a901391e920`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-CPU-STATIC-IMPLEMENTATION`
- previous formal pair: `27b60046080290adeb574281f8fcdedf5840439b` / `19394c2824d36728976a9df680eab839cfd915e0`
- approved design pair: `721b4100624a37edbdd75bb555515b7d7e67c8e1` / `78b8c9cd1389ff523b703d578208f7a221a64af2`
- request/bookkeeping HEAD observed: `e2c039802021f52a707d4d61d6dcb56201e3b6ca`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh incremental review relative to `27b6004 / 19394c2`. Root formal changes only the Gitlink. Child is one remediation commit ahead and changes only approved whitelist surfaces: `production_active_wiring.py`, `production_active_wiring_test.py`, and `trainer/active_wiring_callback_test.py`.

Request Evidence reports active CPU `25 passed`, callback `3 passed`, target `py_compile` and diff-check PASS. These execution claims were not independently rerun; implementation and fixtures were independently inspected.

## Previous blocker status

1. **CLOSED — attempt-1 retry exhaustion now terminal-cleans the exact prepared member.**
   `abort_source_transient()` explicitly routes `plan.attempt != 0` through `owner.abort_terminal(..., "LOCAL_MEM_RETRY_EXHAUSTED")`, clears registry capability state, and the added fixture proves `ABORTED` + pending `None`.

2. **PARTIALLY CLOSED — no-marker callback parity Evidence improved but still does not satisfy the frozen trainer-level legacy-path witness.** See MEDIUM blocker 2.

## Current blockers

1. **MEDIUM — retry-exhaustion check now precedes the frozen later-member transient rule, so an attempt-1 later-member transient gets the wrong terminal disposition code.**
   - implementation: `cosmos_framework/model/generator/mot/production_active_wiring.py::ProductionActiveWiringRegistry.abort_source_transient`
   - frozen contract: retained v0.3/v0.4 retry policy.

   Current order is:
   1. `if prepared.transaction.plan.attempt != 0 -> LOCAL_MEM_RETRY_EXHAUSTED`
   2. `if prepared.member_index != 0 or completed_members -> LOCAL_MEM_RETRY_AFTER_MEMBER`

   After a first-member retry succeeds in an attempt-1 multi-member window, a transient on member 2 satisfies both conditions. The frozen contract says **any later-member transient, including after a successful member, must terminalize as `LOCAL_MEM_RETRY_AFTER_MEMBER`**. Current code instead emits `LOCAL_MEM_RETRY_EXHAUSTED`.

   Safety is still terminal/fail-closed, so this is not a HIGH data/gradient leak, but the exact disposition contract is wrong.

   **Acceptance:** give later-member precedence: if `member_index != 0` or `completed_members` is non-empty, terminalize `LOCAL_MEM_RETRY_AFTER_MEMBER`; only a repeated transient on the retried first member (`member_index==0`, no completed members, attempt==1) uses `LOCAL_MEM_RETRY_EXHAUSTED`. Add an attempt-1 later-member fixture proving exact code, `ABORTED`, pending `None`, zero further optimizer/scheduler mutation.

2. **MEDIUM — the required no-marker parity witness is still callback-group-level, not trainer-level legacy lifecycle Evidence.**
   - evidence: `cosmos_framework/trainer/active_wiring_callback_test.py`
   - frozen contract: v0.6 §3 and prior ChatGPT acceptance.

   The new test proves `CallBackGroup.on_before_backward()` invokes an exact `TTTLifecycleCallback` in original order. It monkeypatches that callback's hook and therefore does not prove the actual trainer no-marker path preserves the existing lifecycle observe/abort/resolve behavior. The prior acceptance explicitly required a neighboring **trainer-level no-marker control** with a pre-existing lifecycle spy.

   **Acceptance:** add one trainer-level no-marker control adjacent to the active fixture. Prove original `self.callbacks.<hook>` dispatch is used; exact TTT callback is invoked with preserved order/args/count; the pre-existing legacy lifecycle follows its existing observe/backward/abort-or-resolve route; active marker control remains zero-call to that lifecycle. Re-run/report exact pair CPU/static suites, target `py_compile`, root/child `git diff --check`.

## Scope boundary

No closure authority is granted for this pair. No producer/packer/dataset/manifest/config/optimizer-selector/checkpoint changes, real I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 are authorized.

Requested closure literal remains reserved for a corrected formal pair:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_PRODUCTION_ACTIVE_WIRING_CPU_STATIC`
