# ChatGPT independent review — R09-B TTT production integration CPU/static remediation

- Gate: `G0-R09-B-TTT-V035-PRODUCTION-INTEGRATION-IMPLEMENTATION`
- Formal root implementation SHA: `764eb09da87dddae265f4476c0237ca00b05cd52`
- Formal child/Gitlink SHA: `6c5251b9f07901bf0161838fb7d17e895c0ce37d`
- Request/bookkeeping SHA observed: `6846280c71edf0d2e3541c5da2c70231584a7882`
- Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh incremental review relative to prior remediation pair `f5c89ef7488935045a4eee9d5f6cb65f2b9e2beb / d5b2cd3e1da1d105e46dcda37487d2b483205da4`. The child delta touches only the two approved trainer-side CPU/static files: `cosmos_framework/trainer/__init__.py` and `cosmos_framework/trainer/trainer_local_memory_integration_test.py`. No production wiring, registry/defaults, model-forward wiring, real checkpoint/data/cache I/O, CUDA/GPU/torchrun, training, evaluation or inference was introduced.

## Prior HIGH status

**OPEN — partially remediated, not closed.** This pair correctly closes two concrete sub-gaps from the previous review:

1. `actual_n_valid != planned_n_valid` (`GAWindowPlan.objective()` `ValueError`) is now caught, clears slow grads and is re-routed to `LOCAL_MEM_IDENTITY_CONTRACT_FAILURE`.
2. `commit_fast` and `clear_slow_grads` are now mandatory callables; successful backward unconditionally invokes `commit_fast`, and identity/numerical/outer terminal paths unconditionally clear slow grads.

These fixes are correct but do not implement the full inherited transaction-owner contract.

## Blocking finding

1. **HIGH — `_run_local_memory_segment_backward` is still a single-member backward/commit primitive, not the canonical GA transaction owner required by the approved v0.2/v0.3 design.**

   - `cosmos_framework/trainer/__init__.py:550-582` validates only a caller-provided boolean `identity_valid` and `actual_n_valid`; it does not own or inspect the frozen member identity/plan state itself.
   - The seam has no failure-kind/attempt input and never invokes `CanonicalSegmentRuntimeAdapter.classify_failure()`. Therefore the frozen transient-only recovery taxonomy remains disconnected from the trainer transaction path.
   - There is no seam-level creation or execution of the unique suffix recovery plan for same-digest `LOAD_DECODE_TRANSIENT` attempt=0, nor attempt=1 `LOCAL_MEM_RETRY_EXHAUSTED` handling.
   - There is no authoritative remaining-member suppression state, no explicit prior-fast-retention/terminal evidence state, and no optimizer/LR suppression state owned by this seam.
   - GradScaler skip semantics are not represented or driven through this seam: the approved contract requires committed fast chronology retention + slow-grad clear + no slow optimizer/LR step at the same transaction boundary.
   - The new trainer tests now cover success commit, identity failure clear/no-commit, and planned/actual mismatch routing, but do not cover the inherited mandatory matrix: numerical failure, outer failure, transient attempt0 recovery, attempt1 exhaustion, prior-fast retention, remaining-member suppression, optimizer/LR suppression, GradScaler skip, unequal valid counts/nonzero aux/full-window equivalence/no second GA scaling through the new transaction owner.

   **Acceptance:** within the already-approved exact whitelist/symbols, make `ImaginaireTrainer._run_local_memory_segment_backward` (with `CanonicalSegmentRuntimeAdapter` and canonical plan primitives) the actual deterministic CPU/static GA transaction owner. It must expose/own enough immutable plan/member/attempt state to:
   1. validate exact planned member identity and `actual_n_valid == planned_n_valid` before backward/commit;
   2. perform mandatory post-backward fast commit on success;
   3. classify terminal identity/numerical/outer failures, clear partial slow grads, retain prior committed fast chronology, suppress remaining members, and suppress slow optimizer/LR advancement;
   4. permit suffix recovery only for same-digest `LOAD_DECODE_TRANSIENT` at attempt=0, and terminate attempt=1 with `LOCAL_MEM_RETRY_EXHAUSTED`;
   5. represent GradScaler skip at the same transaction boundary: retain committed fast chronology, clear slow grads, no slow optimizer/LR step;
   6. add adjacent CPU fixtures proving the complete inherited v0.2 matrix end-to-end through the trainer/adapter seam, including unequal valid counts + nonzero aux, full-window equivalence and no second GA scaling.

## Evidence assessment

The reported trainer fixtures (`3 passed`) are useful but insufficient for Gate closure because they cover only three local cases and do not establish the required `contract -> behavior -> evidence` mapping for the GA transaction lifecycle. Existing lower-level `GAWindowPlan` / `LocalMemoryTransaction` tests remain primitive evidence only; they do not demonstrate that the newly-authorized trainer seam orchestrates those semantics end-to-end.

## Boundary

This verdict does not authorize production-integration closure, production wiring, registry/defaults, real checkpoint/data/cache I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1. Review/Inbox bookkeeping does not change the formal pair.
