# R09-B TTT v0.3.5 Canonical Native Forward/Loss CPU/static Implementation Review

## Formal target

- Root formal implementation SHA: `34d71a39e03d41377931b900e330984f953612ac`
- Child/Gitlink SHA: `0993445f027454c99f1ab777b5a10df1b04171be`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-CPU-STATIC-IMPLEMENTATION`
- Frozen design authority: v0.1 + v0.2 + v0.3 + v0.4, final design pair `1c6ceedb27004e52cd256c404159b85f9be6ba8b / 5d0e037ced559c07081fd4880c633dc03f325efe`
- Root Gitlink at the formal target was independently verified to resolve exactly to `0993445f027454c99f1ab777b5a10df1b04171be`; the child commit is reachable.

## Incremental scope

`5d0e037..0993445` changes exactly the seven frozen CPU/static whitelist files:

1. `cosmos_framework/model/generator/algorithm/loss/flow_matching.py`
2. `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py`
3. `cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py`
4. `cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py`
5. `cosmos_framework/model/generator/omni_mot_model.py`
6. `cosmos_framework/trainer/__init__.py`
7. `cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py`

No whitelist expansion was found. The production model path remains CPU/static fail-closed before pack/noise/native forward, so this review does **not** authorize real I/O, CUDA/GPU, torchrun, real native forward/loss/backward, optimizer/scheduler stepping, training/eval/inference, runtime sidecar, distributed, or LIBERO4IN1.

## Verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/algorithm/loss/flow_matching.py:96)`

Current blockers: **3 HIGH** — 2 production-contract blockers and 1 Evidence-only blocker.

## Blocker lifecycle

The v0.4 design blocker concerning disposal of a minted commit capability is **CLOSED at the implementation primitive level**: current `CanonicalProductionAdapter.abort_commit(capability)` validates and consumes the exact registered commit capability, then aborts the exact pending scan without frontier/scheduler/reconcile mutation; double/foreign disposal fails closed. This closure does not override the new blockers below.

## HIGH-1 — Production: no-valid modality creates a fake canonical native item / ownership-cardinality failure

**Location:** `cosmos_framework/model/generator/algorithm/loss/flow_matching.py:96-97`, interacting with `CanonicalProductionAdapter.build_prepared_canonical_native_loss_split()`.

**Root cause:** `compute_flow_matching_loss_terms(..., has_valid_tokens=False)` constructs a singleton `dummy_per_instance` and returns it as both `unweighted_per_instance` and canonical `weighted_per_instance`. That singleton is acceptable only as the legacy diagnostic dummy. In the canonical path it becomes a synthetic native-item term. A modality may be present for more than one canonical consumer while having no valid native tokens; its source-side owner map can therefore have `K_m > 1`, while the returned canonical weighted term has length 1. The prepared loss builder then either sees a term/owner cardinality mismatch or assigns a fake native identity.

**Frozen contract violated:** v0.2 freezes absent/no-valid-token modalities to graph-connected zero **without creating any fake consumer/native-item identity**; the legacy singleton dummy is diagnostic only and must not become a canonical ownership term. The weighted consumer algebra must preserve the source-side native item population and owner map.

**Exact acceptance:** for any present modality with zero valid native tokens, including a source owner population with `K_m > 1`, canonical loss construction must contribute graph-connected zero without manufacturing a canonical item/owner identity and without term/owner cardinality failure. The legacy public wrapper must retain its frozen legacy diagnostic behavior. Add a direct CPU/static witness for a present, no-valid modality with multiple source owners that proves zero contribution, no fake identity, no cardinality exception, and unchanged valid-path weighted algebra.

## HIGH-2 — Production: controlled slow-gradient ownership is an unauthenticated second authority channel

**Location:** `cosmos_framework/trainer/__init__.py:941-953`, method `ImaginaireTrainer._run_canonical_native_backward()`.

**Root cause:** the trainer reads `output_batch["psm_canonical_native_slow_parameters"]` as an arbitrary tuple and validates only that each element is a `torch.nn.Parameter`. The tuple is not exact-object-bound to the canonical native-forward capability, adapter, or the registered canonical encoder/core that produced the scan graph. An empty, incomplete, extra, duplicate, or foreign parameter tuple therefore remains a separate mutable authority for failure cleanup.

This matters because v0.3/v0.4 failure disposition requires clearing the exact controlled canonical slow gradients before scan/capability disposal and terminalization. With the current interface, a failure can leave actual canonical slow gradients uncleared or clear a foreign parameter's gradient instead.

**Frozen contract violated:** v0.1 freezes the exact typed native-forward capability as trainer authority and requires foreign/incomplete schema to fail before backward; the current reviewer contract additionally requires the exact registered canonical encoder/core to own the same autograd graph. v0.3/v0.4 require failure cleanup of the exact controlled slow gradients, not caller-selected parameters.

**Exact acceptance:** before backward, the controlled slow-parameter set must be derived from or exact-object-verified against the same canonical capability/adapter/registered encoder+core authority. Foreign, missing, incomplete, duplicate, or extra declarations must fail closed before backward with zero foreign-gradient mutation. Backward and post-backward failures must clear every exact canonical controlled slow gradient and no foreign gradient. Add CPU/static witnesses using the actual registered canonical slow parameters plus foreign/incomplete cases; a synthetic anchor-only tuple is insufficient.

## HIGH-3 — Evidence-only: frozen trainer failure disposition is not directly witnessed through the production dispatcher

**Location / section:** `cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py`, `test_canonical_native_scaler_rejection_disposes_before_backward`; and `cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py`, `test_adapter_abort_commit_consumes_exact_capability_without_reconcile`.

**Root cause:** the current adapter test proves the `abort_commit()` primitive by manually catching an injected `commit_success()` exception and manually invoking `abort_commit()` plus `transaction.terminalize()`. It does not prove that `ImaginaireTrainer._run_canonical_native_backward()` performs the frozen v0.4 pre-mutation `commit_success` failure disposition. The trainer test directly manufactures a scan/native capability before invoking the helper with an enabled scaler; it therefore proves helper disposal, not the frozen production `training_step` pre-scan scaler/real-optimizer rejection. I found no direct trainer-dispatch witnesses for backward exception or post-backward `prepare_commit` exception.

**Frozen contract violated:** v0.3/v0.4 require CPU/static witnesses for the actual trainer chronology and all three failure dispositions: backward exception → clear controlled grads → abort exact scan → terminalize; post-backward prepare failure → same; pre-mutation commit failure → clear controlled grads → exact `abort_commit(capability)` → terminalize. Enabled scaler/real optimizer must be rejected before scan/capability creation in the production canonical path.

**Exact acceptance:** add direct CPU/static Evidence through the production trainer authority showing (1) enabled scaler and real optimizer reject before scan/capability mutation, (2) backward failure clears exact controlled canonical slow grads, aborts exact scan, terminalizes, and performs zero reconcile, (3) post-backward prepare failure has the same zero-commit disposition, and (4) pre-mutation commit failure is disposed by the trainer through exact `abort_commit(capability)` and terminalization with zero frontier/scheduler/reconcile mutation. Tests must assert state, identity, and mutation boundaries, not only exception text.

## Evidence read

I read the execution results recorded in the formal request, including the reported `23 passed`, Ruff PASS, `py_compile` PASS, and child `diff --check` PASS, plus the targeted cases. I did **not** independently rerun those commands. Pass counts and static checks do not close the contract violations above.

## Positive findings retained

- Seven-file whitelist is preserved.
- Existing public `compute_flow_matching_loss()` compatibility is retained on the valid path.
- Valid-path weighted per-instance terms and canonical `N/K_m` owner aggregation are structurally present.
- Prepared working-copy / canonical production preparation remains isolated from ordinary Local authority and stays hard-stopped before native pack/noise/forward in this Gate.
- `abort_commit(capability)` is an exact one-shot adapter primitive and closes the prior v0.4 capability-disposal design issue at that layer.
- No approval is granted beyond the current CPU/static Gate.

## Reviewer repository-hygiene note

During this review, the reviewer accidentally created an empty root `noop` file while invoking a GitHub write interface, immediately disclosed the mistake, and removed only that accidental file in correction commit `d48febf9c85350087b62979486627f6c3daf0ea9`. This bookkeeping correction is outside the formal pair and has no technical-verdict authority.
