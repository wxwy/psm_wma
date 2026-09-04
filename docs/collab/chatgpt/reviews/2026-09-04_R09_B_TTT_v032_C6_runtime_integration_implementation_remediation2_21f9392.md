# ChatGPT independent re-review — C6 runtime integration implementation remediation 2 @ 21f9392

**Gate**: `G0-R09-B-TTT-V032-C6-RUNTIME-INTEGRATION-IMPLEMENTATION`  
**Formal target**: root implementation `21f939287477e3791546954eaac808bd1c0aff8c`; child/Gitlink `997d117ff1a9780af9e1c82507a441b7adc787ec`  
**Observed V2 request/bookkeeping HEAD at review start**: `0f89ce83635645cbeac68dfa5846a449fbd0d465`  
**Frozen C6 design authority**: `574d28750883d9e69bd03aa39cc3640646190dfa`

## Verdict

`REQUEST_CHANGES`

## Closed from prior review

- Prior production-code blockers remain **CLOSED**; child delta `0a2a438... -> 997d117...` is tests-only and changes only `c6_runtime_adapter_test.py`.
- Public C6 seam now directly covers N=1/3/16 segment closure, terminal r=0/1/3, fresh-epoch re-admission, pending done rejection, unrelated/grad-free/partial-owner loss rejection, backward failure, public permutation/value equivalence, row mismatch, identity/chronology/replay cases.
- No active Cosmos/runtime/config/optimizer/checkpoint/GPU/training scope drift found.

## Remaining blocker

1. **HIGH — C6 public-seam Evidence still does not prove the full frozen rollback/state-parity contract.**
   - File: `cosmos_framework/model/generator/mot/c6_runtime_adapter_test.py:163-174,197-207` and absence across `c6_runtime_adapter_test.py:1-207`.
   - Pending `done` rejection checks only `c5_write_count`; it does not prove the frozen phase/fast-state/committed-replay/reverse-index/epoch snapshot invariance.
   - Backward-failure coverage proves `finish()` remains closed and then aborts, but does not compare exact pre/post committed state, chronology, replay/index and epoch snapshots required for rollback evidence.
   - The frozen C6 v0.2 Local-disabled parity requirement remains untested at the C6 seam; no Local-disabled/no-memory input/packing/loss parity fixture exists in this file.
   - **Acceptance**: tests-only remediation is sufficient: add exact public-seam before/after snapshot assertions for pending `done` and backward-failure/abort rollback, plus the frozen Local-disabled parity fixture. Re-run C5A+C6 selector, `py_compile`, and child/root `git diff --check` with exact counts. No production-code change is required unless stronger fixtures expose a defect.

## Scope

Allowed remediation remains tests-only in the C6 synthetic adapter boundary plus root review/status bookkeeping. Active Cosmos runtime, config/optimizer/checkpoint, attention/packing, GPU/CUDA/torchrun, real I/O, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1 remain prohibited.