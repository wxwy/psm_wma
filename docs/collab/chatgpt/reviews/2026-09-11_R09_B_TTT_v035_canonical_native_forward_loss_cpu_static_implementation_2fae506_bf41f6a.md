# R09-B TTT v0.3.5 Canonical Native Forward/Loss CPU/static Closure Remediation v2 Review

## Formal target

- Root formal implementation SHA: `2fae506b71e7d9e819a088adf9511d0ee30ae443`
- Child/Gitlink SHA: `bf41f6ae1ac5e2d3a8db95ae56b52a6fc6948f20`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-CPU-STATIC-IMPLEMENTATION`
- Previous valid reviewed pair: `be2cd4656ac0ccd92e90ffbeceeb5cda90dae2a1 / 8d68f791241fbd26f4cdd297d502b6ef19a4a0db`
- Previous review: `docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_forward_loss_cpu_static_implementation_be2cd46_8d68f79.md`
- Frozen design authority: v0.1 + v0.2 + v0.3 + v0.4, final design pair `1c6ceedb27004e52cd256c404159b85f9be6ba8b / 5d0e037ced559c07081fd4880c633dc03f325efe`.

The canonical live Inbox explicitly voids the earlier mistyped child `bf41f6ae4c5f74be2261c5f83d5f9327f8c0d660` and reissues this exact pair. The earlier invalid-pair review `..._2fae506_bf41f6ae4c5.md` therefore has no Gate authority for this corrected request.

Independent verification confirms that root `2fae506b71e7d9e819a088adf9511d0ee30ae443` resolves its `cosmos-framework` Gitlink exactly to `bf41f6ae1ac5e2d3a8db95ae56b52a6fc6948f20`, and that child commit is reachable.

## Incremental scope

Relative to `8d68f791..bf41f6ae`, the child advances by exactly one commit and modifies only four files, all inside the frozen seven-file CPU/static whitelist:

1. `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py`
2. `cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py`
3. `cosmos_framework/trainer/__init__.py`
4. `cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py`

No whitelist expansion was found. Root changes relative to the previous valid formal pair are collaboration/state bookkeeping plus the Gitlink; no additional root production implementation is part of this target.

## Verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:373)`

Current blockers: **3 HIGH** — 2 production-contract blockers and 1 Evidence-only blocker.

## Previous blocker lifecycle

- Previous HIGH-1 raw/missing-`None` fail-open is **CLOSED**: raw `None` with non-empty source owners now fails closed. However the same prior blocker also required the present-but-no-valid graph-zero to remain bound to the exact native modality graph; that part is still open.
- Previous HIGH-2 post-mutation handling is **PARTIALLY CLOSED**: once `frontier.commit()` has returned successfully, the adapter now marks a post-mutation capability and later scheduler/transaction failures can be classified as `CANONICAL_NATIVE_POST_MUTATION_FAILURE`. The marker is still installed too late to cover irreversible mutation occurring *inside* `frontier.commit()`, and trainer still clears slow gradients before checking the post-mutation boundary.
- Previous HIGH-3 production pre-scan Evidence is **PARTIALLY CLOSED**: a direct `ImaginaireTrainer.training_step()` test now exists and covers the real-optimizer rejection path, but the scaler-only path is not independently witnessed because the test passes a real optimizer in both parameterized cases.
- The earlier unauthenticated slow-parameter authority HIGH remains **CLOSED**; this remediation does not regress that exact capability binding.

## HIGH-1 — Production: certified no-valid loses its exact modality graph-zero provenance

**Locations:** `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:365-374`, primary verdict line `:373`; source primitive remains `cosmos_framework/model/generator/algorithm/loss/flow_matching.py:94-100`.

**Root cause:** `compute_flow_matching_loss_terms(..., has_valid_tokens=False)` still creates a graph-connected `dummy_loss` from the exact modality predictions and stores it in the returned `FlowMatchingLossTerms`. But `build_prepared_canonical_native_loss_split()` unwraps the object to `canonical_weighted_per_instance`; when that field is `None`, it drops the typed object's own dummy graph term and simply `continue`s. The final split obtains graph support only from the separately caller-supplied `graph_anchor`.

The existing no-valid CPU witness passes `graph_anchor=sum(prediction)`, so it happens to reconnect the same prediction graph and passes. The production API, however, does not bind or prove that relationship. A caller can supply an unrelated anchor and the certified no-valid modality's exact prediction branch then has no guaranteed graph-connected zero contribution.

**Frozen contract violated:** v0.2 explicitly freezes absent/no-valid modality semantics so the legacy/native dummy graph term is retained only as scalar graph support, never as a fake item/identity. The previous formal review additionally required the no-valid graph-zero provenance to remain bound to the exact native modality graph rather than an unverified caller anchor.

**Exact acceptance:** preserve the exact typed no-valid modality's own graph-connected zero in the scalar dummy graph contribution before discarding its item population; do not rely on a generic caller anchor as a substitute. Raw `None` with non-empty owners must remain fail-closed, absent modality must remain distinct, and valid-path `N/K_m` algebra / legacy wrapper ABI must remain unchanged. Add a CPU/static witness in which the generic `graph_anchor` is deliberately unrelated to the no-valid prediction tensors and backward still reaches every no-valid prediction solely through the exact typed modality dummy; also retain raw-`None` rejection and valid-path algebra witnesses.

## HIGH-2 — Production: irreversible boundary is marked after `frontier.commit()` returns, and post-mutation evidence is partially cleared

**Locations:** `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:458-469` and `:756-757`; `cosmos_framework/trainer/__init__.py:983-990`.

**Root cause:** the new `_post_mutation_commits` marker is added only after `self.frontier.commit(...)` returns. But `CanonicalProductionFastStateFrontier.commit()` itself performs irreversible row-wise mutations: it removes prior slot keys for stream-end rows or assigns newly cloned state into `_states` one row at a time. The per-row clone/construction is still fallible. With multiple rows, an earlier row can therefore be committed before a later row operation raises. In that state `commit_has_crossed_mutation_boundary()` is still false, so the trainer can enter ordinary `abort_commit()` / terminalization and erase scan/capability provenance despite a partially mutated frontier.

The new adapter test injects failure only in `scheduler.consume_prepared_reconcile()` after a fully successful `frontier.commit()`, so it does not exercise this first-irreversible-mutation window. The retained pre-mutation test instead replaces the whole `frontier.commit()` call with an exception, even though v0.4 defines supported pre-mutation failure around known pre-mutation validation, not an untyped failure inside the irreversible operation.

Additionally, `_run_canonical_native_backward()` clears every controlled slow gradient immediately upon entering the commit exception handler, before it checks `commit_has_crossed_mutation_boundary()`. Therefore even the currently detected post-mutation path preserves capability/scan/frontier state but destroys gradient evidence before raising `CANONICAL_NATIVE_POST_MUTATION_FAILURE`.

**Frozen contract violated:** v0.4 states that once *any* frontier/scheduler/transaction irreversible mutation has occurred, the failure is an unsupported terminal bug: no automatic disposal/recovery/retry is allowed and evidence must be preserved. The reviewer addendum also requires all fallible work to occur before irreversible mutation or the mutation phase to be explicitly typed and fail-safe.

**Exact acceptance:** make the irreversible boundary cover the first possible frontier mutation, not merely successful return from `frontier.commit()`. A safe implementation may mark the typed capability as post-mutation immediately before entering the irreversible apply step after all preflight, or stage all fallible state construction before a separately marked non-recoverable apply phase. Any exception after that boundary must raise `CANONICAL_NATIVE_POST_MUTATION_FAILURE` without `abort_commit`, `abort_scan`, transaction terminalization-as-recoverable, retry/reconstruction, or destruction of preserved failure evidence including controlled gradients. Keep a distinct pre-mutation validation-failure path that remains safely abortable. Add a direct trainer CPU/static witness that injects after at least one real frontier row mutation but before completion and proves exact capability/scan/frontier/gradient evidence is preserved; retain a separate pre-mutation validation witness.

## HIGH-3 — Evidence-only: production scaler rejection is not independently witnessed

**Location:** `cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py:200-208`, especially `:204`.

**Root cause:** the new `test_canonical_training_step_rejects_before_model_forward()` parameterizes `scaler_enabled` as `True/False`, but constructs a real `torch.optim.SGD` optimizer in both cases. Because production rejection is `scaler_enabled OR isinstance(optimizer, torch.optim.Optimizer)`, both parameterized executions pass even if the scaler predicate is completely removed. The test therefore directly proves the real-optimizer hard-stop but not the required enabled-scaler-only hard-stop.

The source itself still contains the intended pre-forward disjunction, so this is an Evidence-only blocker rather than a new source-code blocker.

**Frozen contract violated:** v0.2/v0.3 and the previous formal review require direct production `ImaginaireTrainer.training_step()` witnesses for both enabled GradScaler and real optimizer rejection before callback/model-forward/scan/transaction mutation.

**Exact acceptance:** add two independently causal production-entry witnesses: (1) enabled scaler with a non-`torch.optim.Optimizer` sentinel so only the scaler condition can reject, and (2) disabled scaler with a real optimizer so only the optimizer condition can reject. Instrument or sentinel the callback/model-forward/adapter-scan boundary so any entry past the guard fails, and assert no canonical scan/capability/transaction/frontier/scheduler mutation. Do not count the existing post-scan `_run_canonical_native_backward()` scaler test as a substitute for this pre-scan production witness.

## Evidence read

I read the execution results recorded in the corrected formal request: adapter targeted `2 passed`, typed no-valid integration `1 passed`, trainer pre-scan/scaler targeted `3 passed`, target `py_compile` and child/root `git diff --check` PASS. I did **not** independently rerun those commands.

Those pass counts do not close the blockers above because the no-valid witness reuses the same prediction graph as the generic anchor, the post-mutation injection occurs only after a fully successful frontier commit and is adapter-level, and the pre-scan parametrization never isolates scaler from the always-real optimizer.

## Positive findings retained

- Corrected formal root/Gitlink/child binding is exact and reachable.
- The remediation is one child commit and remains inside the frozen seven-file whitelist.
- Raw `None` plus non-empty owner map now fails closed.
- Valid-path weighted terms and `N/K_m` consumer algebra are not changed by this remediation.
- Exact registered encoder/core slow-gradient authority remains capability-bound.
- Post-`frontier.commit()` scheduler failure is now detectably non-abortable at the adapter level; this is useful partial closure, but it does not cover the earlier internal frontier mutation window.
- Production `training_step()` still contains the intended scaler/real-optimizer pre-forward hard-stop.
- Existing working-copy/No-Local/legacy isolation and pack/noise/native-forward hard-stop are not expanded by this remediation.

## Authorized next scope

Remediate only the blockers above within the already-frozen seven-file synthetic CPU/static whitelist and return a new formal root/child pair for fresh closure review. Preserve raw-`None` fail-closed behavior, valid `N/K_m`, exact registered slow-parameter authority, field-wise working ownership, retry/one-shot authority, No-Local/legacy isolation, and the pack/noise/native-forward hard-stop.

Not authorized: whitelist expansion, real data/cache/checkpoint I/O, packer/config/optimizer/dataset/dataloader/collate/runtime-sidecar changes, CUDA/GPU, torchrun, actual native forward/loss/backward execution, real optimizer/scheduler stepping, training/evaluation/inference, distributed execution, or LIBERO4IN1.