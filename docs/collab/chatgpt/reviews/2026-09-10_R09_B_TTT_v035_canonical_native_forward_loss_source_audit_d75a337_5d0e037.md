# ChatGPT Independent Review — R09-B / TTT v0.3.5 Canonical Native Forward/Loss Source Audit v0.2

**Date:** 2026-09-10  
**Role:** Independent Design / Code / Evidence / Gate Reviewer  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-SOURCE-AUDIT`  
**Formal root audit SHA:** `d75a3371f48c2b6538e093f5fd693f843b72e1d6`  
**Formal child/Gitlink SHA:** `5d0e037ced559c07081fd4880c633dc03f325efe`  
**Previous same-Gate formal pair:** `dec45ecef491ef85bec9c4adb3a21871b16d9d49 / 5d0e037ced559c07081fd4880c633dc03f325efe`  
**Artifact:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_source_audit_v0.2.md`  
**Verdict:** `APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_FORWARD_LOSS`

## 1. Repository-truth lock

- Latest `origin/V2` observed at review start is delivery/bookkeeping HEAD `f59b47dfd796da3d7b26dbcb6ce845d5525eb5ce`; it is not the formal audit target.
- Latest canonical `CODEX_INBOX.md` request declares exactly `d75a3371f48c2b6538e093f5fd693f843b72e1d6 / 5d0e037ced559c07081fd4880c633dc03f325efe` and requests only `APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_FORWARD_LOSS` or `REQUEST_CHANGES(file:line)`.
- Formal root tree `14e3ec2e34b6e99b9bd41a54f91430c9386d4254` stores `cosmos-framework` exactly at Gitlink `5d0e037ced559c07081fd4880c633dc03f325efe`.
- Child SHA is unchanged from the prior v0.1 audit pair. Root compare `dec45ec... -> d75a337...` is docs/review/session/inbox remediation only; it adds v0.2 and the prior canonical ChatGPT review, with no child implementation change.
- Child `5d0e037...` is nevertheless newer than the earlier Producer closure child because it contains the separately authorized CPU/static retry-lineage implementation. This review therefore checked the actual current child rather than reusing older `42e8364...` line assumptions.

## 2. Previous blocker lifecycle

### HIGH-1 CLOSED — native preparation parity / fail-closed matrix is now source-complete enough for design

The prior review rejected v0.1 for treating `_prepare_canonical_production_inputs()` as if it were already a native-equivalent gathered-input creator. v0.2 corrects that characterization explicitly: the helper is now described as a **safe preparation prefix, not native-equivalent preparation**.

The remediation maps the material ordinary-path differences at current child source:

- `_prepare_training_data()` derives `per_camera_vae_encoding` from the marker;
- calls `get_data_and_condition(... retain_raw_state_vision=not per_camera_vae_encoding)`;
- derives per-logical-sample `data_resolutions` from `image_size`;
- extracts `vae_pixel_shapes` before clearing `raw_state_vision` in the per-camera case;
- while current canonical preparation calls `get_data_and_condition()` without the retain override and returns `data_resolutions=None`.

It also correctly maps that `_get_train_noise_level_vision()` consumes `batch_size`, latent-frame count, token count and resolution information, with dict shift explicitly requiring `resolutions`; therefore resolution is no longer misclassified as bookkeeping.

The previously omitted overrideable memory seams are now mapped: `pre_noise_memory_hook()` is after packing and before noising; `build_memory_state()` is before denoise. v0.2 requires the next design either to preserve these semantics or explicitly reject unsupported overrides before irreversible work.

Most importantly, v0.2 no longer chooses implementation behavior inside the audit. It freezes the valid design choice as either exact gathered-axis parity or an explicit reversible fail-closed unsupported set, and requires CPU/static evidence for resolution/per-camera/hook disposition. This exactly closes the previous HIGH-1 acceptance conditions.

### HIGH-2 CLOSED — native reduction axes are now distinguished from canonical valid-consumer exposure

v0.2 now maps the missing axes and no longer assumes native `[B]` means canonical valid-consumer `[N_valid]`.

Verified source facts reflected correctly in the audit:

- `GenerationDataClean` can represent multiple vision items per logical sample via `num_vision_items_per_sample`; logical `batch_size` remains the logical-sample count while vision tensors are flattened by item.
- action and sound tensors/schedules are dense over only the samples carrying those modalities and are reindexed from logical sample positions.
- `compute_flow_matching_loss()` returns a scalar `per_instance_weighted_loss.mean()` but its second `[B]` result is the **unweighted** `per_instance_loss`; the latter cannot be substituted for the weighted scalar semantics.
- `_compute_losses()` combines modality-specific native means/scales, applies optional sample-level scaling before load-balancing loss, and then adds LBL auxiliary terms separately.

v0.2 therefore requires the next design to map:

`canonical flat consumer -> logical sample -> vision item(s)/dense modality entries -> weighted native item/subset terms -> per-consumer aggregate -> consumer mean with actual_n_valid denominator`.

It also freezes the two legitimate next-design strategies allowed by the prior review: source-identified weighted per-consumer aggregation, or a deliberately restricted one-to-one admitted modality footprint with reversible fail-closed negatives for non-equal axes. It explicitly keeps sample-level scaling in native order and keeps LBL auxiliary outside the valid-consumer ratio. This closes the previous HIGH-2.

### MEDIUM-1 CLOSED — post-backward optimizer / GradScaler irreversible seams are now mapped

v0.2 extends the source map beyond ordinary backward:

- ordinary trainer computes `grad_scaler.scale(loss / grad_accum_iter).backward()`;
- after backward/callback completion it increments `grad_accum_iter`;
- at the GA boundary it preflights the existing active route, then enters optimizer callbacks;
- `_optimizer_step()` owns `GradScaler.unscale_()` for the existing active route when enabled, `GradScaler.step()`, scaler outcome handling, conditional `scheduler.step()`, `GradScaler.update()`, and then the caller proceeds to zero-grad callbacks and `_zero_grad()`.

The remediation correctly treats the existing active optimizer path only as source evidence, not authority for the new canonical capability. It requires the next design to place unsupported canonical enabled-scaler/real-optimizer disposition before optimizer callbacks/irreversible slow optimizer or scheduler work, while preserving No-Local ordinary behavior and requiring a CPU/static boundary witness. This closes the prior MEDIUM.

## 3. Independent source-map consistency check

No new blocking source conflict was found.

- Current canonical producer branch still preflights, scans, compares exact gathered identity/count, invokes the safe helper, then intentionally hard-stops before native pack/noise/forward/loss and aborts the scan result.
- Current ordinary preparation/source schedule facts used by v0.2 match child `5d0e037...`.
- Current flow-matching reduction semantics match the audit's weighted-vs-unweighted distinction.
- Current trainer ordinary and historical row-wise canonical dispatchers remain separate; the audit correctly supersedes the old `canonical_segment_forward` schema for the future canonical native capability.
- Addendum §20.2 explicitly leaves native loss reduction / valid-consumer weighting as implementation-design work, so v0.2 is correctly a source-level bridge into that design rather than a claim that the native loss ABI already exists.
- Approved production ABI design v0.3 already freezes GradScaler/real-optimizer hard-stop and typed retry/commit authority; v0.2 does not grant active/legacy authority to replace those contracts.

## 4. Non-blocking inherited obligations for the next implementation design

These are not blockers for this source audit, but the next design must make them explicit rather than silently dropping inherited authority:

1. **Attempt-1 retry lineage:** child `5d0e037...` now contains `CanonicalProductionRetryCapability`. A future native-forward/loss capability must consume the exact authorized attempt-0 or consumed attempt-1 request/transaction; it must not reconstruct retry plans, re-freeze, re-admit, or create another scheduler transition.
2. **Immutable carrier ownership:** current canonical safe preparation begins from a shallow working-dict copy, while native materialization routines may mutate their working mapping during flattening/normalization. The next design must make working-copy/object ownership explicit so exact parity does not reintroduce mutation of immutable producer/carrier source authority.
3. **Scaler/optimizer timing:** the next design must choose an exact preflight point consistent with the inherited zero-commit hard-stop contract; wording such as “before optimizer callbacks” is a latest boundary, not permission to cross an earlier irreversible canonical capability/commit boundary.
4. **Hook order:** if hooks are supported, preserve the actual native order (`pack -> pre_noise_memory_hook -> noise/replace -> device move -> build_memory_state -> denoise`) rather than treating both hooks as interchangeable generic post-pack callbacks.
5. Approval of this audit does not close or skip the separately tracked `CANONICAL-SEGMENT-PRODUCTION-ABI-CPU-STATIC-IMPLEMENTATION` Gate. If that child changes, any design relying on its concrete source must relock/reconcile the new SHA.

## 5. Scope / authorized next action

Current blockers: **0**.

Authorized next action is exactly one docs-only Gate:

`G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-IMPLEMENTATION-DESIGN`.

That design must freeze the precise file whitelist, typed dataclasses/capabilities, gathered preparation parity-or-fail-closed matrix, weighted per-consumer loss split, canonical trainer dispatcher, GA/scaler/optimizer boundary and the CPU/static evidence matrix listed by v0.2.

This approval does **not** authorize child code, packer/model/trainer changes, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, native forward/loss/backward execution, optimizer stepping, training, evaluation, inference, runtime sidecar, distributed execution or LIBERO4IN1.

## 6. Exact verdict

`APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_FORWARD_LOSS`
