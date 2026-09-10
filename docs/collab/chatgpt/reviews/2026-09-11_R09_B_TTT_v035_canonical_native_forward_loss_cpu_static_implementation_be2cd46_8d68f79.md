# R09-B TTT v0.3.5 Canonical Native Forward/Loss CPU/static Implementation Remediation Review

## Formal target

- Root formal implementation SHA: `be2cd4656ac0ccd92e90ffbeceeb5cda90dae2a1`
- Child/Gitlink SHA: `8d68f791241fbd26f4cdd297d502b6ef19a4a0db`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-CPU-STATIC-IMPLEMENTATION`
- Previous reviewed pair: `34d71a39e03d41377931b900e330984f953612ac / 0993445f027454c99f1ab777b5a10df1b04171be`
- Previous review: `docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_native_forward_loss_cpu_static_implementation_34d71a3_0993445.md`
- Frozen design authority: v0.1 + v0.2 + v0.3 + v0.4, final design pair `1c6ceedb27004e52cd256c404159b85f9be6ba8b / 5d0e037ced559c07081fd4880c633dc03f325efe`.

The formal root Gitlink was independently verified to resolve exactly to `8d68f791241fbd26f4cdd297d502b6ef19a4a0db`; the child commit is reachable.

## Incremental scope

Relative to `0993445..8d68f79`, the child advances by exactly one commit and modifies only five files, all inside the already-frozen seven-file CPU/static whitelist:

1. `cosmos_framework/model/generator/algorithm/loss/flow_matching.py`
2. `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py`
3. `cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py`
4. `cosmos_framework/trainer/__init__.py`
5. `cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py`

No whitelist expansion was found. Root changes since the previous formal pair are Gitlink plus collaboration/ledger/governance files; no new root production implementation is part of this remediation.

## Verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:367)`

Current blockers: **3 HIGH** — 2 production-contract blockers and 1 Evidence-only blocker.

## Previous blocker lifecycle

- Previous HIGH-1 fake singleton symptom is **PARTIALLY CLOSED**: `FlowMatchingLossTerms` now separates the legacy singleton diagnostic from `canonical_weighted_per_instance`, and a typed no-valid term no longer directly becomes a fake native item. However the remediation introduces a new fail-open ambiguity at the prepared loss boundary; HIGH-1 therefore does not close the overall ownership/no-valid contract.
- Previous HIGH-2 unauthenticated slow-gradient authority is **CLOSED**: `CanonicalNativeForwardCapability` now binds the exact `encoder.parameters()+core.parameters()` object set; `validate_native_forward()` re-verifies exact identity; trainer derives controlled slow parameters only from the capability and rejects any caller-supplied `psm_canonical_native_slow_parameters` without mutating foreign gradients.
- Previous HIGH-3 Evidence-only dispatcher chronology is **PARTIALLY CLOSED**: direct trainer-helper witnesses now cover backward exception, post-backward `prepare_commit` exception, and pre-mutation `commit_success` exception. The production `training_step` pre-scan scaler/real-optimizer witness remains missing.

## HIGH-1 — Production: typed no-valid remediation makes genuinely missing modality terms fail open

**Location:** `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:365-371`, primary verdict line `:367`.

**Root cause:** `build_prepared_canonical_native_loss_split()` first unwraps a `FlowMatchingLossTerms` object to `canonical_weighted_per_instance`, then treats any resulting `None` identically. Consequently both of these cases are accepted as graph-zero when `owner_indexes` is non-empty:

1. the intended typed `FlowMatchingLossTerms(... canonical_weighted_per_instance=None)` no-valid population; and
2. a raw/missing `None` term for a modality whose source owner map proves that native items are present.

The old code failed the second case closed. The remediation therefore removes the distinction between a certified no-valid population and missing/incomplete canonical loss production. In addition, the no-valid modality's own dummy graph term is discarded and graph connectivity is delegated to a caller-supplied generic `graph_anchor`; the current CPU witness makes that anchor from the same predictions, but the production API does not prove that provenance.

**Frozen contract violated:** v0.1 requires foreign/incomplete canonical schema to fail closed. v0.2 freezes absent/no-valid modalities to graph-connected zero while explicitly preserving the legacy dummy only as scalar graph support and never as a fake item/identity. A non-empty source owner map cannot silently convert a genuinely missing term into an absent/no-valid modality.

**Exact acceptance:** preserve an unambiguous typed distinction among (a) absent modality, (b) certified present-but-no-valid modality, and (c) missing/incomplete modality terms. Raw `None` with non-empty owner indexes must fail closed. Only an exact typed/proven no-valid result may contribute zero with a non-empty owner map, and its graph-zero provenance must remain bound to the exact native modality graph rather than an unverified caller anchor. Add CPU/static witnesses for typed no-valid with multiple owners, raw `None` + non-empty owners rejection, incomplete/foreign term rejection, and unchanged valid-path `N/K_m` algebra and legacy wrapper behavior.

## HIGH-2 — Production: post-irreversible `commit_success()` failure can still be auto-disposed as if it were pre-mutation

**Locations:** `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:750-752` and `cosmos_framework/trainer/__init__.py:983-992`.

**Root cause:** `CanonicalProductionAdapter.commit_success()` performs its first irreversible mutation at `frontier.commit(...)`, then calls scheduler reconcile and transaction reconcile. If an exception occurs after `frontier.commit()` but before the later mutation sequence completes, `_run_canonical_native_backward()` enters the generic commit exception handler and calls `adapter.abort_commit(commit_capability)`. `abort_commit()` validates scheduler/transaction state but has no proof that the frontier has not already mutated; therefore it can successfully discard the commit capability and scan even though the frontier has already changed, after which trainer terminalizes the transaction as ordinary `CANONICAL_NATIVE_COMMIT_FAILURE`.

The current direct `phase="commit"` witness monkeypatches the whole `commit_success()` method to throw before any mutation, so it does not cover or prevent this state.

**Frozen contract violated:** v0.4 permits `abort_commit(capability)` only for a known pre-mutation `commit_success` failure. Once any frontier/scheduler/transaction irreversible mutation has occurred, the failure is an unsupported terminal bug: automatic disposal/recovery is forbidden and exact evidence must be preserved.

**Exact acceptance:** the trainer/adapter contract must make the irreversible boundary explicit and testable. A failure after the first irreversible mutation must never execute the ordinary `abort_commit`/`abort_scan` zero-mutation recovery path or erase the exact capability/scan evidence. Either all potentially failing validation/work is completed before the first irreversible mutation and the subsequent commit sequence is contractually non-failing, or a typed mutation-phase authority must route any post-boundary exception to `CANONICAL_NATIVE_POST_MUTATION_FAILURE` while preserving evidence. Add a CPU/static trainer witness that injects after a real frontier mutation but before the remaining reconcile sequence and proves no automatic disposal/retry/reconstruction; retain the existing pre-mutation witness separately.

## HIGH-3 — Evidence-only: production `training_step` pre-scan scaler/real-optimizer boundary is still not directly witnessed

**Location / section:** `cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py`; production seam is `ImaginaireTrainer.training_step()` before forward/scan.

**Root cause:** the production source still contains a pre-forward rejection for canonical mode when GradScaler is enabled or a real optimizer is supplied, which is the intended hard-stop. But the remediation adds only direct `_run_canonical_native_backward()` helper tests after manually constructing scan/preparation/capability, plus direct helper failure-disposition tests. That does not prove the frozen requirement that the real production `training_step` boundary rejects before model forward, scan, capability creation, callbacks into backward, or transaction/frontier/scheduler mutation.

**Frozen contract violated:** v0.2/v0.3 require enabled scaler and real optimizer rejection before scan, transaction mutation, backward, callbacks, optimizer/scheduler operations, and zero-grad; previous formal review explicitly required a direct production authority witness for both scaler and optimizer cases.

**Exact acceptance:** add direct CPU/static Evidence through `ImaginaireTrainer.training_step()` for canonical mode covering both (1) enabled scaler and (2) a real `torch.optim.Optimizer`. Instrument the forward/model/adapter/callback boundary so any forward, scan, capability creation, backward, optimizer/scheduler or zero-grad activity fails the witness, and assert zero transaction/frontier/scheduler mutation. Helper-only post-scan rejection is insufficient.

## Evidence read

I read the execution results recorded in the formal request: direct no-valid, slow-authority/scaler and dispatcher-disposal witnesses reported PASS; the targeted suite is reported as `32 passed, 6 failed in 40.85s`, with the six failures attributed by the request to stale legacy canonical wiring fixtures reproduced on the formal base; five target `py_compile` checks and child/root `git diff --check` are reported PASS, with only pre-existing Ruff I001 findings in `trainer/__init__.py`.

I did **not** independently rerun these commands. The recorded pass/fail totals do not close the production-contract and missing direct-Evidence issues above. On the next pair, if the targeted suite remains red, the closure Evidence should identify the exact failing node IDs and a previous-formal-pair differential rather than relying only on an aggregate baseline attribution.

## Positive findings retained

- Exact formal root/Gitlink/child binding is valid.
- The remediation is one child commit and remains inside the frozen seven-file whitelist.
- Valid-path weighted terms and `N/K_m` consumer algebra are retained.
- Legacy `compute_flow_matching_loss()` valid-path API remains unchanged.
- Exact registered encoder/core slow-gradient authority is now capability-bound and the previous caller-selected authority HIGH is closed.
- Direct helper witnesses now cover backward, prepare-commit, and pre-mutation commit-success failure disposal.
- The production `training_step` source still contains the intended pre-forward canonical scaler/real-optimizer hard-stop.
- Existing working-copy/No-Local/legacy isolation and the model-side pack/noise/native-forward hard-stop are not expanded by this remediation.

## Authorized next scope

Remediate only the blockers above within the already-frozen seven-file synthetic CPU/static whitelist and return a new formal root/child pair for fresh closure review. Preserve the existing valid-path `N/K_m` algebra, exact registered slow-parameter authority, field-wise working ownership, retry/one-shot authority, No-Local/legacy isolation, and pack/noise/native-forward hard-stop.

Not authorized: whitelist expansion, real data/cache/checkpoint I/O, packer/config/optimizer/dataset/dataloader/collate/runtime-sidecar changes, CUDA/GPU, torchrun, actual native forward/loss/backward execution, real optimizer/scheduler stepping, training/evaluation/inference, distributed execution, or LIBERO4IN1.
