# ChatGPT independent review — R09-B TTT v0.3.5 production integration CPU/static implementation

- Gate: `G0-R09-B-TTT-V035-PRODUCTION-INTEGRATION-IMPLEMENTATION`
- Formal root implementation SHA: `b4ee077c1d94927f69730b125c0d8c16686b01b1`
- Formal child/Gitlink SHA: `14c005e5226ef1d1bd64fdf78cc76c0af12cda73`
- Approved design pair: `3c1b7ca39fd982f1b00c3d4ca6a6d20cb80da180 / 0fddc27f9c3c463f784be9f528ffbbe123f244ff`
- Request/bookkeeping SHA observed: `9b1bbd654516f3ac82e54c9fc72a34a9ca1a7cc1`
- Requested literal: `APPROVE_TO_CLOSE_R09_B_TTT_V035_PRODUCTION_INTEGRATION_CPU_STATIC` or `REQUEST_CHANGES`
- Verdict: `REQUEST_CHANGES`

## Scope checked

Fresh incremental review. Root delta is only the child Gitlink update. Child compare from `0fddc27f` to `14c005e` changes exactly four approved files: `c6_runtime_adapter.py`, `c6_runtime_adapter_test.py`, `trainer/__init__.py`, and new `trainer_local_memory_integration_test.py`. No registry/defaults/model-forward/real-I/O/GPU/training wiring is introduced.

The primary/auxiliary objective formula itself is preserved: `CanonicalSegmentRuntimeAdapter.objective()` performs raw finite checks then delegates to `GAWindowPlan.objective()`, and `_run_local_memory_segment_backward()` applies that objective exactly once before backward.

## Blocking finding

1. **HIGH — the approved transaction-owner contract is not implemented end-to-end.**

   Files:
   - `cosmos_framework/trainer/__init__.py:546-562`
   - `cosmos_framework/model/generator/mot/c6_runtime_adapter.py:62-81`
   - `cosmos_framework/trainer/trainer_local_memory_integration_test.py:1-17`
   - contract: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.3.md:20-22`, inheriting v0.2 §§2-4.

   Root cause: v0.3 freezes `ImaginaireTrainer._run_local_memory_segment_backward` as the unique Local primary/aux scaling **and backward/commit transaction owner**, while v0.2 requires the exact canonical terminal/recovery state machine and mandatory CPU fixtures. The implementation stops after `loss.backward()` and returns the loss. `CanonicalSegmentRuntimeAdapter` only exposes `gather()` and `objective()`.

   Therefore the approved seam currently has no mechanism to:
   - validate/route identity or planned-vs-actual failure to `LOCAL_MEM_IDENTITY_CONTRACT_FAILURE`;
   - convert backward exception to `LOCAL_MEM_OUTER_FAILURE`;
   - clear the whole partial slow-gradient window on terminal failure;
   - retain prior fast commits while suppressing remaining members and optimizer/LR steps;
   - perform fast cursor/exposure commit only after successful backward + identity validation;
   - allow suffix recovery only for same-digest `LOAD_DECODE_TRANSIENT` at `attempt=0`, and terminate attempt=1 as `LOCAL_MEM_RETRY_EXHAUSTED`;
   - preserve fast commits while suppressing slow optimizer/LR advancement on GradScaler skip.

   The request reports adapter pytest=`23 passed` and trainer fixture=`1 passed`, but the new trainer fixture proves only one successful primary+aux scaling/backward case. Existing `local_memory_segment_test.py` covers some isolated scheduler/plan helpers, not the new adapter/trainer transaction seam. Thus the frozen contract→behavior→evidence chain is not established.

   **Acceptance:** within the already-approved exact whitelist/symbols, implement a CPU/static canonical transaction seam with sufficient explicit transaction/scheduler/identity context so that:
   1. planned==actual and identity are checked before commit;
   2. raw non-finite maps to `LOCAL_MEM_NUMERICAL_FAILURE`;
   3. forward/backward exception maps to `LOCAL_MEM_OUTER_FAILURE`;
   4. successful member backward is followed by the canonical fast chronology/cursor/exposure commit;
   5. terminal failures clear partial slow grads, preserve prior fast commits, suppress remaining members, take no optimizer/LR step, and never redeliver;
   6. only same-digest `LOAD_DECODE_TRANSIENT` at `attempt=0` creates the immutable suffix recovery plan; attempt=1 terminates with `LOCAL_MEM_RETRY_EXHAUSTED`;
   7. GradScaler skip retains committed fast chronology but clears slow grads and takes no slow optimizer/LR step.

   Add/extend only the approved CPU/static fixtures to exercise the inherited v0.2 matrix end-to-end through `CanonicalSegmentRuntimeAdapter` / `ImaginaireTrainer._run_local_memory_segment_backward`: transient attempt0, retry exhaustion, identity/planned mismatch, numerical, outer exception, prior-fast retention, zero slow grads, remaining-member suppression, optimizer/LR unchanged, terminal evidence, unequal valid counts + nonzero aux, full-window equivalence, and no second GA scaling.

## Boundary status

This is an implementation-semantic blocker, not an authorization to wire production. The four-file whitelist itself is respected and there is no production wiring blocker. No real I/O, GPU, training/evaluation/inference was run by this reviewer. The reported test counts are request Evidence and were not independently executed.

This verdict authorizes no production-integration closure, production wiring, registry/defaults, real checkpoint/data/cache I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1. Review/Inbox bookkeeping does not change the formal pair.
