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
