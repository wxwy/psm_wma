# ChatGPT independent review — R09-B TTT production integration CPU/static remediation

- Gate: `G0-R09-B-TTT-V035-PRODUCTION-INTEGRATION-IMPLEMENTATION`
- Formal root implementation SHA: `f5c89ef7488935045a4eee9d5f6cb65f2b9e2beb`
- Formal child/Gitlink SHA: `d5b2cd3e1da1d105e46dcda37487d2b483205da4`
- Request/bookkeeping SHA observed: `1b0849547fac490d1e4a6c1b7ad68884ad7cb950`
- Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh incremental review relative to prior blocked implementation pair `b4ee077c1d94927f69730b125c0d8c16686b01b1 / 14c005e5226ef1d1bd64fdf78cc76c0af12cda73`. The child delta remains within the approved CPU/static whitelist and touches only `c6_runtime_adapter.py`, `c6_runtime_adapter_test.py`, `trainer/__init__.py`, and `trainer_local_memory_integration_test.py`. No production wiring, registry/defaults, model-forward wiring, real checkpoint/data/cache I/O, CUDA/GPU/torchrun, training, evaluation or inference was introduced.

## Prior HIGH status

**OPEN — partially remediated, not closed.** The new child adds a failure-classification helper, identity fail-close handling, slow-grad-clear callback and successful-path commit callback. However, these pieces do not form the canonical transaction owner required by the approved v0.2/v0.3 design.

## Blocking finding

1. **HIGH — the canonical backward/commit transaction state machine is still not implemented end-to-end.**

   - `cosmos_framework/trainer/__init__.py:550-582` accepts caller-provided `identity_valid`, optional `commit_fast` and optional `clear_slow_grads`; it does not own or validate the actual member identity/plan state, does not require the callbacks, and does not drive retry/recovery/remaining-member suppression/optimizer-LR state.
   - `cosmos_framework/model/generator/mot/c6_runtime_adapter.py:82-94` adds `classify_failure()`, but the trainer seam never calls it. Therefore the frozen failure taxonomy is descriptive rather than transaction-authoritative.
   - `GAWindowPlan.objective()` still raises `ValueError` when `actual_n_valid != planned_n_valid`. `_run_local_memory_segment_backward()` catches only `RuntimeError`, so a planned/actual mismatch escapes without `clear_slow_grads()` and without the required `LOCAL_MEM_IDENTITY_CONTRACT_FAILURE` routing.
   - `commit_fast` and `clear_slow_grads` are optional. A successful call can return without any fast commit, and a terminal failure can occur without any slow-grad clear, contradicting the design statement that this seam is the unique backward/commit transaction owner.
   - There is still no seam-level path that creates the unique attempt=0 suffix recovery plan, handles attempt=1 `LOCAL_MEM_RETRY_EXHAUSTED`, suppresses remaining members on terminal failure, preserves prior fast commits, or enforces no slow optimizer/LR step and GradScaler-skip semantics.

   **Acceptance:** within the already-approved exact whitelist/symbols, make `ImaginaireTrainer._run_local_memory_segment_backward` (with `CanonicalSegmentRuntimeAdapter` / canonical plan primitives) the actual transaction owner rather than a callback wrapper. It must, with deterministic CPU-observable state:
   1. validate actual member identity and `actual_n_valid == planned_n_valid` before backward/commit and route violations to `LOCAL_MEM_IDENTITY_CONTRACT_FAILURE`;
   2. require/own successful post-backward fast commit rather than allowing a no-commit success path;
   3. on numerical/outer/identity terminal failures clear partial slow grads, retain prior fast chronology, suppress remaining members and suppress slow optimizer/LR advancement;
   4. permit suffix recovery only for same-digest `LOAD_DECODE_TRANSIENT` at attempt=0, and terminate attempt=1 with `LOCAL_MEM_RETRY_EXHAUSTED`;
   5. preserve GradScaler-skip semantics: committed fast chronology retained, slow grads cleared, no slow optimizer/LR step;
   6. add adjacent CPU fixtures that exercise these behaviors through the new trainer/adapter seam, including planned/actual mismatch, identity failure, numerical failure, outer failure, transient attempt0 recovery, attempt1 exhaustion, prior-fast retention, remaining-member suppression, optimizer/LR suppression, GradScaler skip, unequal valid counts + nonzero aux, full-window equivalence, and no second GA scaling.

## Evidence assessment

The new tests demonstrate the failure-classification mapping and one identity-failure clear/no-commit case, but do not establish `contract -> behavior -> evidence` for the full inherited transaction matrix. Existing lower-level `LocalMemoryTransaction` tests remain useful evidence for the primitives, but they do not prove the newly-authorized trainer/adapter seam actually orchestrates those primitives correctly.

## Boundary

This verdict does not authorize production-integration closure, production wiring, registry/defaults, real checkpoint/data/cache I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1. Review/Inbox bookkeeping does not change the formal pair.
