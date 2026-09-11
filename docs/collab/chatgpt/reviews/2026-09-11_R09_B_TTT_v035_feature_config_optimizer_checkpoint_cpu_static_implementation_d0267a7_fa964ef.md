# ChatGPT Independent Review — R09-B TTT v0.3.5 Feature / Config / Optimizer / Checkpoint CPU/static Implementation Remediation

- Date: 2026-09-11
- Formal root implementation SHA: `d0267a77280c51133f3ad48a149441ec6c0ea568`
- Child/Gitlink SHA: `fa964ef3974d5b622081cc1ded89b69d851b9eb5`
- Gate: `G0-R09-B-TTT-V035-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-REFREEZE-CPU-STATIC-IMPLEMENTATION`
- Approved implementation design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_feature_config_optimizer_checkpoint_cpu_static_implementation_design_v0.1.md`
- Prior formal review: `docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_feature_config_optimizer_checkpoint_cpu_static_implementation_a27e942_ddd49d3.md`

## Verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/config_checkpoint_contract_test.py:255)`

## Current blockers

`1 HIGH` — Evidence-only. I found no remaining production/contract blocker in the four areas remediated on this pair, but the previously frozen direct acceptance matrix is still not fully witnessed.

## Prior HIGH-1 — CLOSED for this synthetic CPU/static scope: restore preflight now stages optimizer/scheduler loadability before live mutation

The prior pair copied live slow tensors before any full optimizer/scheduler loadability check. This remediation changes `_stage_restore()` so that, before `strict_restore_into()` touches live slow tensors, it validates:

- exact optimizer payload top-level schema;
- exact live optimizer parameter-object flattening/order against the canonical slow inventory;
- saved `param_groups` identity/order against the live serialized groups;
- saved optimizer state-id/schema consistency;
- full optimizer `load_state_dict()` loadability on a deep-copied shadow optimizer;
- scheduler key schema and full `load_state_dict()` loadability on a deep-copied shadow scheduler.

`strict_restore_into()` still performs the live optimizer/scheduler apply after the slow tensor copies, but for the approved synthetic CPU/static contract the fallible compatibility/loadability decisions are now performed on the shadows before the first live mutation. The new legal AdamW + ExponentialLR round-trip proves restoration of slow tensors, optimizer state and scheduler state, and the deliberately malformed optimizer/scheduler payloads reject before those live states mutate. I therefore do not retain the prior atomicity production blocker on this pair.

This closure does not authorize or generalize to arbitrary real training optimizer/scheduler stacks, hooks, distributed wrappers, checkpoint backends or real optimizer steps; those remain outside this Gate.

## Prior HIGH-2 — production behavior CLOSED; direct negative Evidence is still incomplete

The implementation now binds the live optimizer to the exact canonical slow `Parameter` objects before mutation:

- flattened live optimizer parameter count must equal the canonical inventory;
- every live parameter must be the exact corresponding canonical `Parameter` object by `is` identity;
- duplicate live parameter objects are rejected;
- saved parameter IDs/groups must match the live serialized group structure.

This closes the source/contract defect that allowed same-count foreign optimizers. The new test directly rejects a same-shape/same-count foreign optimizer.

However, the prior exact acceptance also required direct reordered / duplicated / missing optimizer-membership witnesses. The current source would reject these cases, but the remediation does not add those direct negative witnesses. This is one component of the remaining Evidence-only HIGH below.

## Prior MEDIUM-1 — CLOSED: active-TTT projector ABI is fail-closed at config and inventory boundaries

`OmniMoTModelConfig.__attrs_post_init__()` now requires `local_memory_enabled=True` and `local_memory_dim=32` whenever `local_ttt_enabled=True`.

`canonical_slow_inventory()` independently rejects any projector that is not an `nn.Linear(32, 2048)` and any modality embedding not shaped `(2048,)`. The new negative tests cover a 31-wide projector/config and a wrong-width modality embedding. This closes the prior `32 -> 2048` ABI blocker without changing public runtime activation.

## Remaining HIGH — Evidence matrix is not fully closed

The approved implementation design and the prior review require direct CPU/static witnesses for *each* relevant live authority using actual production/typed creation paths, plus a direct active-TTT production registration witness.

The remediation substantially improves the evidence: `test_restore_rejects_real_pending_and_committed_runtime_authorities_before_mutation()` now uses a real `CanonicalBatchScheduler.freeze_plan()`, a real `CanonicalBatchWindowTransaction`, `adapter.scan()`, `prepare_commit()` and `commit_success()` to witness:

- pending scan authority;
- an actual frozen scheduler transition;
- a committed fast-state frontier;
- an explicitly supplied open transaction.

That is a real improvement over the prior manual `_scan_requests.add()` / fake `_frozen_transitions.append(SimpleNamespace())` evidence.

But the test still does **not** directly create and reject the rest of the frozen live-authority matrix:

- pending native-forward capability;
- pending commit capability *before* `commit_success()`;
- retry capability;
- suffix-recovery capability / consumed suffix request authority;
- a real recovery receipt / recovery lineage.

The implementation itself enumerates these adapter collections in `validate_runtime_admission()`, so I do not find a production-code omission there. The problem is Evidence: the closure request asks to close the approved nine-item matrix, and the direct witnesses still stop at scan/frozen/frontier/transaction.

The optimizer-membership Evidence is also incomplete relative to the prior exact acceptance: add direct reordered, duplicated and missing live-optimizer membership negatives, each proving pre-mutation rejection and unchanged live slow/optimizer/scheduler state.

Finally, the prior HIGH-3 exact acceptance required a direct static witness of the *production active-TTT registration branch*. `omni_mot_model_test.py::test_canonical_adapter_binds_only_the_registered_ttt_owner()` still manually constructs a `local_memory_runtime` container and therefore proves adapter lookup/binding, not that `OmniMoTModel.build_net()` itself registers exactly one active-TTT `local_memory_runtime.evidence_encoder/ttt_core` root with no legacy registered trainable owner/readout. This remediation modifies only `model_config.py`, `config_checkpoint_contract.py` and its test, so that production-registration witness remains absent.

### Exact acceptance for closure

Within the already-approved six-file synthetic CPU/static scope only:

1. extend direct optimizer negatives to reordered, duplicated and missing canonical `Parameter` membership, with zero mutation assertions;
2. create real typed/public native-forward, pending-commit, retry, suffix and recovery-receipt authorities and prove each causes pre-mutation restore rejection with unchanged slow/runtime snapshots;
3. add a direct static production-registration test that exercises the active-TTT `OmniMoTModel.build_net()` registration branch (using lightweight mocks/fixtures as necessary) and proves exact `local_memory_runtime.evidence_encoder/ttt_core` ownership plus absence of a legacy registered trainable owner/readout;
4. retain the existing legal optimizer/scheduler/iteration round-trip, late-defect zero-mutation, pending-scan/frozen/frontier/open-transaction witnesses, config identity, selector/inventory, runtime-key exclusion and public hard-stop tests.

No production code change is required by this review if the existing source behavior is preserved and the missing direct Evidence can be added in the approved test files.

## Pair / scope verification

- Formal root `d0267a77280c51133f3ad48a149441ec6c0ea568` resolves `cosmos-framework` exactly to reachable child `fa964ef3974d5b622081cc1ded89b69d851b9eb5`.
- The child is exactly one commit ahead of the prior `ddd49d318...` pair and changes only three files inside the approved six-file whitelist: `model_config.py`, `config_checkpoint_contract.py`, and `config_checkpoint_contract_test.py`.
- The formal root bookkeeping text contains a stale intermediate child string `fa964efb81090...`; it is not used as technical authority because the root Gitlink and the formal request resolve to `fa964ef3974...`. This is bookkeeping-only and not a technical Gate blocker.
- MM/Kimi conclusions were not used as technical authority.

## Evidence / execution scope

I treated the reported `49 passed` as supporting information, not as proof by itself. This review is based on the exact child diff, the prior blocker acceptance criteria, the relevant production source and direct tests. I did not execute real checkpoint/filesystem/DCP/remote I/O, public runtime activation, native forward/loss/backward, optimizer/scheduler step, CUDA/GPU, `torchrun`, runtime sidecar, training, evaluation, inference, distributed execution, matched smoke or LIBERO4IN1.

## Authorized next action

Evidence-only remediation inside the already-approved six-file synthetic CPU/static whitelist, then submit a new formal root/child pair for fresh incremental closure review.

Still not authorized: Gate closure, any file outside the six-file whitelist, real checkpoint I/O/backend wiring, public runtime/hard-stop removal, real native forward/loss/backward, real optimizer/scheduler stepping, CUDA/GPU, `torchrun`, runtime sidecar/mid-episode resume, training, evaluation, inference, distributed execution, matched smoke or LIBERO4IN1.
