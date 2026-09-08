# ChatGPT independent review — R09-B TTT v0.3.5 production integration implementation design

- Gate: `G0-R09-B-TTT-V035-PRODUCTION-INTEGRATION-IMPLEMENTATION-DESIGN`
- Formal root design SHA: `8697a4caf47b43164f03e79b841a11ebb1991287`
- Formal child/Gitlink SHA: `0fddc27f9c3c463f784be9f528ffbbe123f244ff`
- Request/bookkeeping SHA observed: `782b7174aca3809b517388da242bb5d802619600`
- Requested literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_INTEGRATION_CPU_STATIC` or `REQUEST_CHANGES`
- Verdict: `REQUEST_CHANGES`

## Scope checked

Fresh incremental docs-only review relative to the approved production-migration design pair `1bd438d/0fddc27f`. The current design correctly keeps the closed canonical CPU/static core as prerequisite, bans the old one-row lifecycle / `scan_segment_many()` / closing replay/materialize route, and does not itself authorize production wiring, real I/O, GPU or training.

## Blocking findings

1. **HIGH — `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.1.md:15`: failure recovery collapses the canonical taxonomy and incorrectly permits suffix redelivery for terminal failures.** The design states that `actual!=planned`, load/identity, inner, forward/native-loss/backward failures all abort the member and then perform deterministic suffix-only redelivery. Canonical v0.3.8 §4 freezes a narrower authority: only same-digest `LOAD_DECODE_TRANSIENT` at `attempt=0` may create the unique suffix recovery plan; retry at `attempt=1` is terminal `LOCAL_MEM_RETRY_EXHAUSTED`; identity/planned mismatch is terminal `LOCAL_MEM_IDENTITY_CONTRACT_FAILURE`; inner/native-loss non-finite is terminal `LOCAL_MEM_NUMERICAL_FAILURE`; forward/backward exception is terminal `LOCAL_MEM_OUTER_FAILURE`. Terminal failures clear partial slow grads, preserve prior committed fast chronology, skip optimizer/LR and remaining members, but **must not redeliver**.

   **Acceptance:** rewrite the production integration state machine to preserve the exact v0.3.8/v0.3.9 failure-class → recovery/terminal-code mapping. CPU acceptance must separately cover transient attempt0 recovery, attempt1 exhaustion, planned/actual or identity failure, numerical failure and outer exception, observing member identities, retained fast commits, zero slow grads, remaining-member suppression, optimizer/LR iterations and terminal evidence.

2. **HIGH — `...production_integration_implementation_design_v0.1.md:15`: the trainer loss seam drops the frozen primary/auxiliary partition.** The design only says the synthetic consumer returns a “native mean” followed by `planned_N_valid/N_window` scaling. Canonical v0.3.6 §6 requires the model seam to split `L_consumer_mu` (consumer-mean primary loss) from `L_aux_mu` (e.g. load-balancing auxiliary), with the unique objective `L_backward_mu=(N_valid_mu/N_window)*L_consumer_mu + (1/GA)*L_aux_mu` (or `1/GA_effective` in recovery). It explicitly forbids multiplying total loss by the valid-count ratio or applying a second unconditional `/grad_accum_iter` in the Local path.

   **Acceptance:** freeze the adapter/consumer-spy ABI as a structured primary+aux result (or exactly equivalent), check raw native-loss finiteness before Local scaling, freeze normal and recovery objective formulas, and freeze the trainer seam as the unique scaling owner with no second GA division. Add synthetic unequal-valid-count + nonzero-aux fixtures and full-window equivalence.

3. **MEDIUM — `...production_integration_implementation_design_v0.1.md:11`: the claimed “精确白名单” is not actually frozen.** It uses `cosmos_framework/model/.../local_memory_segment.py`, unqualified `production_runtime_adapter.py`, generic `trainer/__init__.py`, and says exact paths/entries will be frozen “实现前”. But this Gate's approval literal would itself authorize the CPU/static implementation. Repository truth already has the canonical file at `cosmos_framework/model/generator/mot/local_memory_segment.py` and a historical `c6_runtime_adapter.py`; an unfrozen adapter/trainer path leaves the implementation edit surface ambiguous.

   **Acceptance:** before approval, enumerate every allowed repository path exactly, mark each as new vs existing, identify the exact symbols/seams allowed to change, specify the adjacent test files, and explicitly state whether the historical C6 adapter is untouched/superseded. No ellipsis, basename-only path, or post-approval whitelist freezing.

## Boundary status

The docs-only boundary and no-real-I/O/no-GPU/no-training prohibitions are sound. No child code/tests or real execution were performed by this reviewer. This verdict authorizes no production-integration implementation or later Gate until a new formal pair closes all three blockers. Review/Inbox bookkeeping does not change the formal pair.
