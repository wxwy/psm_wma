# ChatGPT independent re-review — C6 runtime integration implementation remediation 3 @ 1435db1

**Gate**: `G0-R09-B-TTT-V032-C6-RUNTIME-INTEGRATION-IMPLEMENTATION`  
**Formal target**: root implementation `1435db1560bb920f5e4326ae5c434a19b5109a83`; child/Gitlink `f81a47bc67a45c65b75f399c597c64fab25e9daf`  
**Observed V2 request/bookkeeping HEAD at review start**: `464948159d9c3bbc4c8fe4d5a8018b6dd3475515`  
**Frozen C6 design authority**: `574d28750883d9e69bd03aa39cc3640646190dfa`

## Verdict

`REQUEST_CHANGES`

## Delta and closure status

- Child delta `997d117... -> f81a47b...` is exactly one tests-only commit and changes only `cosmos_framework/model/generator/mot/c6_runtime_adapter_test.py` (+52/-0). No production/runtime/config/optimizer/checkpoint/GPU/training scope drift found.
- Prior production-code blockers remain **CLOSED**.
- The prior Evidence-only HIGH is **PARTIALLY CLOSED**: the remediation now snapshots committed fast-state, chronology, committed replay, reverse index, epoch and write-count around pending `done` rejection and backward failure.

## Remaining blockers

1. **HIGH — rollback/pending snapshot Evidence is still not complete enough to prove the frozen exact-rollback/phase contract.**
   - File: `cosmos_framework/model/generator/mot/c6_runtime_adapter_test.py:28-40,220-252`.
   - `_snapshot()` covers committed state/chronology/replay/index/epoch/write-count but omits `_pending_by_owner` and its `phase`.
   - Therefore `test_pending_done_preserves_complete_public_seam_snapshot()` does not prove that pending phase/rows/witness remain unchanged after rejected `done()`.
   - `test_public_backward_failure_abort_preserves_committed_snapshot()` compares only before/after the failed backward, then calls `abort()` without an after-abort snapshot; it does not directly prove the required abort cleanup/no committed mutation boundary.
   - **Acceptance**: extend the public-seam snapshot to include pending existence + phase + row identities/count (and any other transaction fields needed to prove no mutation), assert exact equality across rejected `done` and failed backward, then assert post-`abort` pending removal while committed state/chronology/replay/index/epoch remain equal to the pre-failed-segment committed baseline.

2. **HIGH — Local-disabled parity is still not the frozen parity contract.**
   - File: `cosmos_framework/model/generator/mot/c6_runtime_adapter_test.py:255-259`.
   - Frozen C6 v0.2 §5 requires: `Local disabled synthetic path 必须与 no-memory 输入/packing/loss 保持 parity`; §6 separately lists `Local disabled parity` as acceptance.
   - New `test_local_disabled_parity_is_zero_write_no_memory_path()` proves only zero C5 writes / no pending state before and after `done("disabled-owner")`. It never constructs the same synthetic no-memory input/packing/loss path and never compares outputs/loss/packing behavior.
   - Zero-write/no-state is necessary but not equivalent to input/packing/loss parity.
   - **Acceptance**: add one direct C6 synthetic fixture that runs the same synthetic sample through (a) Local-disabled path and (b) frozen no-memory baseline, and asserts identical relevant input/packing structure plus identical scalar loss/output semantics. Keep the disabled branch zero-write/no-memory-state assertions as an additional check.

## Scope

Only tests/Evidence remediation at the C6 synthetic adapter seam plus root review/status bookkeeping is authorized. No production-code change is required unless stronger fixtures expose a production defect. Active Cosmos runtime, config/optimizer/checkpoint, attention/packing production wiring, GPU/CUDA/torchrun, real I/O, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1 remain prohibited.