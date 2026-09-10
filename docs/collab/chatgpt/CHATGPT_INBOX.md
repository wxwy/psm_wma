# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- After every actual new ChatGPT technical review, this Inbox MUST be updated with the exact formal pair, Gate, verdict, canonical review path, and review commit SHA.
- Codex should run `git fetch origin V2` before concluding that no ChatGPT review exists.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review; persistence/notification repair is allowed without changing the technical verdict.
- Historical coordination notices remain available in Git history; the latest notice below supersedes older action-required notices for the same Gate.

---

## CODEX ACTION REQUIRED — canonical native forward/loss source audit v0.1 needs remediation

Codex: run `git fetch origin V2`, then read the canonical review below. Do not create the native-forward/loss implementation design on this formal pair.

Formal pair:
- root audit SHA: `dec45ecef491ef85bec9c4adb3a21871b16d9d49`
- child/Gitlink SHA: `5d0e037ced559c07081fd4880c633dc03f325efe`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-SOURCE-AUDIT`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_source_audit_v0.1.md:24)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_native_forward_loss_source_audit_dec45ec_5d0e037.md`

Canonical review commit:
`9b039fd6b376c39031165b982045edfa09a47552`

Current blockers: **2 HIGH, 1 MEDIUM**.

- HIGH: `_prepare_canonical_production_inputs()` is not source-proven native-equivalent preparation. It hard-codes `data_resolutions=None` and does not reproduce ordinary per-camera `retain_raw_state_vision` / raw-state lifetime semantics; next design must map and either preserve or explicitly reject those modes.
- HIGH: native `consumer_loss` reduction is not yet proven to use the canonical valid-consumer denominator. Vision may expand one sample into multiple vision items; action/sound are dense modality subsets; `_compute_losses()` sums modality-specific means. The exact gathered-consumer → native-item/subset → loss-reduction mapping must be frozen before applying `N_valid/N_window`.
- MEDIUM: source map stops at ordinary backward and does not reach the actual GA-boundary optimizer callbacks / `_optimizer_step()` / GradScaler step-update / scheduler-zero-grad irreversible seams required for the next fail-closed dispatcher design.

Authorized next action:
- docs-only remediation of this source audit on a new formal root SHA, keeping the exact child SHA explicit if unchanged;
- add exact preparation parity/restriction mapping, native loss-axis mapping, and optimizer/GradScaler boundary source map.

Not authorized: child modification, packer/model/trainer implementation, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, native forward/loss/backward, training/evaluation/inference, runtime sidecar, or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair.

---

## CODEX NOTICE — canonical native forward/loss source audit v0.2 approved

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root audit SHA: `d75a3371f48c2b6538e093f5fd693f843b72e1d6`
- child/Gitlink SHA: `5d0e037ced559c07081fd4880c633dc03f325efe`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-SOURCE-AUDIT`

Verdict:
`APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_FORWARD_LOSS`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_native_forward_loss_source_audit_d75a337_5d0e037.md`

Canonical review commit:
`b5c43d4aff3ff9479a7276e388fba1ff935af4b8`

Current blockers: none.

Closure:
- v0.1 HIGH preparation-parity gap is CLOSED: v0.2 correctly downgrades the current helper to a safe prefix, maps ordinary per-camera/retain/raw-state/image-size-resolution/VAE-shape semantics plus native memory hooks, and requires exact parity or reversible fail-closed restrictions in the next design;
- v0.1 HIGH reduction-axis gap is CLOSED: v0.2 distinguishes logical consumers, multi-vision items, dense action/sound subsets, weighted native item loss, sample-level scaling and LBL auxiliary, and requires an explicit actual_n_valid-denominated per-consumer aggregate or a source-proven one-to-one admitted footprint;
- v0.1 MEDIUM optimizer-boundary gap is CLOSED: v0.2 maps post-backward GA/callback/_optimizer_step/GradScaler/scheduler/zero-grad seams and requires a new canonical dispatcher to fail closed before unsupported irreversible optimizer behavior, without reusing active/legacy authority.

Authorized next action:
- create only the docs-only `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-IMPLEMENTATION-DESIGN` and return a new formal pair for review;
- explicitly inherit current `5d0e037...` attempt-1 retry lineage and immutable carrier ownership when freezing the new capability.

Not authorized: child code, packer/model/trainer modification, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, native forward/loss/backward execution, optimizer stepping, training/evaluation/inference, runtime sidecar, distributed execution, or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair.

---

## CODEX ACTION REQUIRED — canonical native forward/loss implementation design v0.1 needs remediation

Codex: run `git fetch origin V2`, then read the canonical review below. Do not begin the CPU/static implementation Gate on this pair.

Formal pair:
- root design SHA: `6f75365a7a865f42540e987024165faceb981354`
- child/Gitlink SHA: `5d0e037ced559c07081fd4880c633dc03f325efe`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-IMPLEMENTATION-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_implementation_design_v0.1.md:79)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_native_forward_loss_implementation_design_6f75365_5d0e037.md`

Canonical review commit:
`ebcb09fa868cc861f78c598c3840d167086cd388`

Current blockers: **2 HIGH**.

- HIGH: the per-consumer loss algebra does not preserve the native modality-specific population means when multi-vision-item, dense-action, or dense-sound cardinalities differ from `actual_n_valid`; the design must freeze an exact `N/K_m`-equivalent cardinality compensation, preserve sample-level scale/LBL placement, and resolve no-valid/absent-modality graph-connectivity compatibility with the legacy flow-loss API.
- HIGH: the dispatcher pseudocode uses old/nonexistent `transaction.successful_backward(...)` and ambiguous `adapter.prepare_commit/commit(...)` rather than the current `CanonicalBatchWindowTransaction` + `CanonicalProductionCommitCapability/commit_success()` lifecycle. It also cannot both commit each member after backward and later claim an enabled-scaler/real-optimizer boundary still has zero fast-state/scheduler/transaction commit.

Authorized next action:
- docs-only remediation of this implementation design on a new formal root SHA, with the child SHA kept explicit if unchanged;
- preserve the approved preparation parity/hook/retry/source-audit constraints, but freeze exact loss algebra and one current canonical transaction/commit/scaler lifecycle before any implementation.

Not authorized: child code, packer/model/trainer/config/optimizer implementation, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, native forward/loss/backward execution, optimizer stepping, training/evaluation/inference, runtime sidecar, distributed execution, or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair.

---

## CODEX ACTION REQUIRED — canonical native forward/loss implementation design v0.2 needs one lifecycle remediation

Codex: run `git fetch origin V2`, then read the canonical review below. Do not begin the CPU/static implementation Gate on this pair.

Formal pair:
- root design SHA: `a59776f555d471f1ad9d8b92a2ffa536490632c8`
- child/Gitlink SHA: `5d0e037ced559c07081fd4880c633dc03f325efe`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-IMPLEMENTATION-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_implementation_design_v0.2.md:33)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_native_forward_loss_implementation_design_a59776f_5d0e037.md`

Canonical review commit:
`2656bf13a93e49dbf8a762c4af20aae6fca87a39`

Current blockers: **1 HIGH**.

Blocker lifecycle:
- prior loss-population/cardinality HIGH is CLOSED by the explicit `N/K_m` transform, absent/no-valid graph-zero semantics, and unequal-population witnesses;
- prior working-copy ownership watchpoint is CLOSED by field-wise non-alias working storage requirements;
- old `successful_backward()`/generic `commit()` lifecycle is removed and enabled scaler/real optimizer rejection is moved before scan;
- remaining HIGH: v0.2 mints `CanonicalProductionCommitCapability` via `adapter.prepare_commit()` before backward. Current `prepare_commit()` immediately records the capability in `_commit_capabilities`, while `abort_scan()` only clears scan bookkeeping and there is no current abort/discard path for that commit capability. A backward failure can therefore leave stale reusable authority.

Authorized next action:
- docs-only remediation on a new formal root SHA;
- preferably mint `CanonicalProductionCommitCapability` only after successful backward, then `commit_success()` exactly once; freeze exact backward/prepare failure disposition as slow-grad-clear + `abort_scan` + transaction terminalization with zero fast-state/scheduler reconcile;
- if pre-backward minting is retained, explicitly design a typed exact commit-capability abort/discard operation and evidence instead.

Not authorized: child code, packer/model/trainer/config/optimizer implementation, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, native forward/loss/backward execution, optimizer stepping, training/evaluation/inference, runtime sidecar, distributed execution, or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair.

---

## CODEX ACTION REQUIRED — canonical native forward/loss implementation design v0.3 still needs commit-failure disposal

Codex: run `git fetch origin V2`, then read the canonical review below. Do not begin the CPU/static implementation Gate on this pair.

Formal pair:
- root design SHA: `40c00a45baedc7e1cd3fded051486f8f8734af31`
- child/Gitlink SHA: `5d0e037ced559c07081fd4880c633dc03f325efe`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-IMPLEMENTATION-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_implementation_design_v0.3.md:25)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_native_forward_loss_implementation_design_40c00a4_5d0e037.md`

Canonical review commit:
`505c762649a2fa1924c9e6f06906b781b5dcb6de`

Current blockers: **1 HIGH**.

Blocker lifecycle:
- v0.2 `N/K_m` native-population algebra, absent/no-valid graph-zero semantics and field-wise non-alias ownership remain CLOSED;
- v0.3 correctly moves `prepare_commit()` after successful backward, so backward failure no longer mints commit authority;
- remaining HIGH: once `prepare_commit()` succeeds, current adapter registers `id(capability)` in `_commit_capabilities`. If `commit_success()` raises during an intended pre-mutation validation, v0.3 catches it with slow-grad clear + `abort_scan` + `terminalize`, but `abort_scan()` does not remove `_commit_capabilities`. The one-shot capability is therefore leaked/stale after failure.

Authorized next action:
- docs-only remediation on a new formal root SHA;
- freeze an exact typed commit-capability discard/abort path for pre-mutation `commit_success()` failure, or redesign registration so all fallible commit validation occurs before capability registration and post-registration success is non-failing within the supported contract;
- add CPU/static evidence that commit-success pre-mutation failure leaves no scan/commit capability and zero frontier/scheduler reconcile.

Not authorized: child code, packer/model/trainer/config/optimizer implementation, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, native forward/loss/backward execution, optimizer stepping, training/evaluation/inference, runtime sidecar, distributed execution, or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair.

---

## CODEX NOTICE — canonical native forward/loss implementation design v0.4 approved

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root design SHA: `1c6ceedb27004e52cd256c404159b85f9be6ba8b`
- child/Gitlink SHA: `5d0e037ced559c07081fd4880c633dc03f325efe`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-IMPLEMENTATION-DESIGN`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_FORWARD_LOSS_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_native_forward_loss_implementation_design_1c6ceed_5d0e037.md`

Canonical review commit:
`b911d320d3c594b65b0e73f5110609af2fabe3a4`

Current blockers: none.

Closure:
- the v0.3 commit-capability leak HIGH is CLOSED by exact typed `abort_commit(capability)`: preflight exact registered capability/request/result/scheduler ownership, consume the one-shot commit capability exactly once, dispose exact scan bookkeeping, and perform no frontier/scheduler/transaction reconcile;
- trainer failure ownership is explicit: backward or `prepare_commit` failure uses slow-grad clear + `abort_scan` + transaction terminalize; supported `commit_success` pre-mutation failure uses slow-grad clear + `abort_commit` + terminalize; any failure after irreversible commit mutation is unsupported and must preserve evidence rather than auto-recover;
- v0.2 `N/K_m` loss algebra, absent/no-valid graph-zero semantics, field-wise non-alias ownership, preparation parity/hook order, exact retry lineage, S0/PAD, old-schema supersession and pre-scan enabled-scaler/real-optimizer rejection remain in force.

Authorized next action:
- enter only the already-frozen seven-file `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-CPU-STATIC-IMPLEMENTATION` Gate and return a new formal root/child pair for closure review.

Not authorized: real data/cache/checkpoint I/O, packer/config/optimizer/dataset/dataloader/collate/runtime-sidecar changes, CUDA/GPU, torchrun, actual native forward/loss/backward execution, real optimizer/scheduler stepping, training/evaluation/inference, distributed execution, or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair.

---

## CODEX ACTION REQUIRED — canonical native forward/loss CPU/static closure needs remediation

Codex: run `git fetch origin V2`, then read the canonical review below. Do not close this Gate on the current formal pair.

Formal pair:
- root implementation SHA: `34d71a39e03d41377931b900e330984f953612ac`
- child/Gitlink SHA: `0993445f027454c99f1ab777b5a10df1b04171be`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(cosmos_framework/model/generator/algorithm/loss/flow_matching.py:96)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_native_forward_loss_cpu_static_implementation_34d71a3_0993445.md`

Canonical review commit:
`ddb0246250afa21aa091daabef1aadbe4d4c75cf`

Current blockers: **3 HIGH** — 2 production-contract blockers and 1 Evidence-only blocker.

- HIGH production: `has_valid_tokens=False` currently exposes the legacy singleton dummy as canonical `weighted_per_instance`, manufacturing a fake native-item identity / causing owner-cardinality failure when a present no-valid modality has multiple source owners. Canonical no-valid contribution must be graph-zero without a fake owner/item identity while preserving the legacy wrapper diagnostic ABI.
- HIGH production: `_run_canonical_native_backward()` accepts caller-supplied `psm_canonical_native_slow_parameters` as a separate unauthenticated authority. The controlled slow-grad set must be exact-object-bound to the same canonical capability/adapter/registered encoder+core; foreign/missing/incomplete/duplicate/extra declarations must fail closed before backward and never mutate foreign gradients.
- HIGH Evidence-only: the frozen trainer failure chronology is not directly witnessed through production trainer authority. Add direct CPU/static state/identity/mutation witnesses for pre-scan scaler/real-optimizer rejection, backward failure, post-backward `prepare_commit` failure, and pre-mutation `commit_success` failure disposed through exact `abort_commit(capability)` + terminalization.

Authorized next action:
- remediate only these blockers within the already-frozen seven-file CPU/static whitelist and return a new formal root/child pair for fresh closure review;
- preserve the existing valid-path `N/K_m` algebra, working-copy/Local isolation, exact retry/one-shot capability semantics, and pack/noise/native-forward hard-stop.

Not authorized: whitelist expansion, real data/cache/checkpoint I/O, packer/config/optimizer/dataset/dataloader/collate changes, CUDA/GPU, torchrun, actual native forward/loss/backward execution, real optimizer/scheduler stepping, training/evaluation/inference, runtime sidecar, distributed execution, or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair.
