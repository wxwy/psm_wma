# R09-B TTT v0.3.5 Canonical Native Forward/Loss CPU/static Closure Remediation v3 Review

## Formal target

- Root formal implementation SHA: `4c962c9ef7448ea02e790eb478d57090e06fe535`
- Child/Gitlink SHA: `dc7ba30228dd141244d7d060ebd47310a0c1e8c1`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-CPU-STATIC-IMPLEMENTATION`
- Previous reviewed pair: `2fae506b71e7d9e819a088adf9511d0ee30ae443 / bf41f6ae1ac5e2d3a8db95ae56b52a6fc6948f20`
- Previous review: `docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_forward_loss_cpu_static_implementation_2fae506_bf41f6a.md`
- Frozen design authority: v0.1 + v0.2 + v0.3 + v0.4, final design pair `1c6ceedb27004e52cd256c404159b85f9be6ba8b / 5d0e037ced559c07081fd4880c633dc03f325efe`.

Independent root inspection confirms that `4c962c9ef7448ea02e790eb478d57090e06fe535` resolves its `cosmos-framework` Gitlink exactly to `dc7ba30228dd141244d7d060ebd47310a0c1e8c1`; the child commit is reachable.

## Incremental scope

Relative to `bf41f6ae..dc7ba302`, the child advances by exactly one commit and modifies only five files, all inside the frozen seven-file CPU/static whitelist:

1. `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py`
2. `cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py`
3. `cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py`
4. `cosmos_framework/trainer/__init__.py`
5. `cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py`

No whitelist expansion was found. Root changes since the previous formal pair are Gitlink plus collaboration/review/ledger state; no additional root production implementation is part of this target.

## Verdict

`REQUEST_CHANGES(cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py:228)`

Current blockers: **1 HIGH — Evidence-only**.

## Previous blocker lifecycle

- Previous HIGH-1 modality-own no-valid graph-zero is **CLOSED in production and direct CPU evidence**. `compute_flow_matching_loss_terms(..., has_valid_tokens=False)` still produces the exact prediction-connected `weighted_mean` dummy; `build_prepared_canonical_native_loss_split()` now folds `terms.weighted_mean * 0.0` into the scalar graph anchor before discarding the no-valid item population. The integration witness now deliberately supplies an unrelated generic `graph_anchor` and still proves gradients reach every no-valid prediction. Raw `None` + non-empty owners remains fail-closed; valid `N/K_m` algebra is unchanged.
- Previous HIGH-2 irreversible-boundary production defect is **CLOSED in source**. `commit_success()` completes all known pre-mutation validation first, records the exact commit capability in `_post_mutation_commits` immediately before entering `frontier.commit()`, and only then begins the row-wise irreversible apply. `_run_canonical_native_backward()` now checks that boundary before clearing slow gradients; post-boundary failure raises `CANONICAL_NATIVE_POST_MUTATION_FAILURE` while preserving slow gradients, commit capability bookkeeping, scan provenance and frontier state. Pre-mutation validation failure remains separately abortable.
- Previous HIGH-3 scaler/optimizer causal Evidence is **CLOSED**. The production-entry witness now uses a non-optimizer sentinel when `scaler_enabled=True` and a real `torch.optim.SGD` only when scaler is disabled, so the two rejection predicates are independently causal and both remain before model-forward/scan.
- Earlier exact registered encoder/core slow-parameter authority remains **CLOSED**.

## HIGH-1 — Evidence-only: post-mutation trainer witness bypasses the production typed commit path

**Location:** `cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py:228`, `test_canonical_native_post_mutation_failure_preserves_trainer_evidence()`.

**Root cause:** the new trainer witness does call the real `_run_canonical_native_backward()` endpoint, but it replaces both production commit-authority operations:

- `adapter.prepare_commit()` is monkeypatched to return a `SimpleNamespace`, not an exact `CanonicalProductionCommitCapability` minted and registered by the adapter;
- `adapter.commit_success()` is monkeypatched by a helper that manually inserts the fake object id into `_commit_capabilities` and `_post_mutation_commits`, performs a full frontier commit, then raises.

This proves that the trainer preserves gradients/evidence **if a post-mutation marker is already manually present**, but it does not directly prove the production chronology that was the previous blocker: the real `CanonicalProductionAdapter.commit_success()` must mark the exact typed capability before the first possible mutation inside `frontier.commit()`. In particular, this test would still pass if production `commit_success()` regressed and moved `_post_mutation_commits.add(...)` back to after `frontier.commit()`, because the test never executes that production method.

The adapter-level post-mutation test uses a real typed capability and real `commit_success()`, but injects only after a fully successful frontier commit at scheduler reconcile; it therefore also does not witness an exception arising during the frontier irreversible apply window.

**Frozen contract violated:** v0.4 requires any failure after *any* irreversible frontier/scheduler/transaction mutation to preserve evidence and forbid automatic disposal. The previous formal review's exact acceptance required a direct trainer CPU/static witness that crosses a real frontier mutation using the exact production capability path, not a mock-only substitute for the authority under review.

**Exact acceptance:** keep the current production code, but add a direct CPU/static trainer witness in which `_run_canonical_native_backward()` obtains a real `CanonicalProductionCommitCapability` from the actual `adapter.prepare_commit()` and enters the actual `adapter.commit_success()`. Inject failure through the frontier apply seam after at least one real frontier mutation (or otherwise assert at the actual frontier entry that the exact capability is already registered as post-mutation, then perform a real mutation before raising). The witness must prove: the exact typed commit capability remains registered, the exact scan remains pending, mutated frontier evidence remains, every controlled slow gradient remains intact, transaction is not recoverably terminalized/reconciled, and neither `abort_commit()` nor `abort_scan()` is performed. It must fail if the production marker is moved to after `frontier.commit()`.

No production-code blocker is asserted on this pair; this is strictly an Evidence closure blocker.

## Evidence read

I read the execution results recorded in the formal request: typed no-valid integration `1 passed, 17 deselected`; adapter `abort_commit` targeted `1 passed, 5 deselected`; trainer pre-scan/scaler/post-mutation `4 passed, 13 deselected`; target `py_compile` and child/root `git diff --check` PASS. I did **not** independently rerun those commands.

Those results directly support the no-valid and causal scaler/optimizer closures. They do not close the remaining post-mutation Evidence gap because the trainer endpoint test manually constructs the commit marker/authority instead of executing the production typed commit path whose ordering is under test.

## Positive findings retained

- Formal root/Gitlink/child binding is exact and reachable.
- Child remediation is one commit and remains inside the frozen seven-file whitelist.
- Modality-own no-valid graph-zero now survives independently of the generic graph anchor.
- Raw `None` plus non-empty source owners remains fail-closed.
- Valid-path weighted terms and `N/K_m` consumer algebra are unchanged.
- Exact registered encoder/core slow-gradient authority remains capability-bound.
- Production irreversible marker now precedes `frontier.commit()` and trainer preserves slow gradients on detected post-mutation failures.
- Scaler-only and optimizer-only production pre-scan rejection are independently witnessed.
- Existing working-copy/No-Local/legacy isolation and pack/noise/native-forward hard-stop are not expanded by this remediation.

## Authorized next scope

Remediate only the remaining Evidence witness within the already-frozen seven-file synthetic CPU/static whitelist and return a new formal root/child pair for fresh closure review. Preserve all production behavior on this pair, including modality-own graph-zero, raw-`None` fail-closed, pre-frontier mutation marking, post-mutation evidence preservation, causal scaler/optimizer guards, valid `N/K_m`, exact slow-parameter authority, field-wise working ownership, retry/one-shot semantics, No-Local/legacy isolation and the pack/noise/native-forward hard-stop.

Not authorized: whitelist expansion, real data/cache/checkpoint I/O, packer/config/optimizer/dataset/dataloader/collate/runtime-sidecar changes, CUDA/GPU, torchrun, actual native forward/loss/backward execution, real optimizer/scheduler stepping, training/evaluation/inference, distributed execution, or LIBERO4IN1.
