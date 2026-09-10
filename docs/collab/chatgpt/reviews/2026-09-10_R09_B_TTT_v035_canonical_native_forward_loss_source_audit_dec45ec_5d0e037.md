# ChatGPT 独立 Canonical Native Forward/Loss Source Audit Review

Formal reviewed pair:
- root audit SHA: `dec45ecef491ef85bec9c4adb3a21871b16d9d49`
- child/Gitlink SHA: `5d0e037ced559c07081fd4880c633dc03f325efe`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-SOURCE-AUDIT`
- artifact: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_source_audit_v0.1.md`
- direct authority: v0.3.5 addendum §18/§20 and approved canonical production ABI design v0.3 (`36df68dff72a6cf1b9bc60f1bb97d0aa78642bb5 / 3a078f28f3d107bb633c932271f86498f7c427f7`).
- request/delivery/session SHAs after the formal root are bookkeeping only and do not replace this formal pair.

Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_source_audit_v0.1.md:24)`

## Incremental review result

The audit is directionally correct on the current producer hard-stop, packer Local Prefix ABI, ordinary `/GA` backward, and supersession of the historical `canonical_segment_forward` schema. However, the source map is not yet complete enough to authorize the next native-forward/loss implementation design.

### HIGH-1 — canonical-safe preparation is incorrectly treated as native-equivalent input preparation

- Severity: HIGH
- Location: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_source_audit_v0.1.md:24` (`safe gathered preparation` row), together with §3.2.
- Root cause: the audit labels `_prepare_canonical_production_inputs()` as a reusable gathered native-input creator without recording material semantic differences from the real ordinary `_prepare_training_data()` path.
- Exact source conflict in child `5d0e037`:
  - ordinary `_prepare_training_data()` derives `per_camera_vae_encoding`, calls `get_data_and_condition(..., retain_raw_state_vision=not per_camera_vae_encoding)`, derives `data_resolutions` from `image_size`, and clears `raw_state_vision` after VAE-shape extraction for the per-camera case;
  - `_prepare_canonical_production_inputs()` calls `get_data_and_condition(data_batch, iteration=iteration)` without that retain flag, hard-codes `data_resolutions = None`, and does not reproduce the ordinary per-camera raw-state cleanup.
  - the subsequent native path passes `data_resolutions` into `_get_train_noise_level_vision(...)`; therefore this is not bookkeeping-only metadata and cannot be silently dropped when claiming native preparation parity.
- Violated contract: v0.3.5 §20.2 requires source-level native ABI closure before implementation design. A canonical helper may intentionally differ, but the audit must identify the difference and freeze either exact parity or a fail-closed unsupported condition; it cannot call the helper reusable as-is while omitting a native schedule/materialization input.
- Exact acceptance:
  1. Amend the source map with the exact ordinary-vs-canonical preparation differences for `per_camera_vae_encoding`, `retain_raw_state_vision`, `image_size -> data_resolutions`, `vae_pixel_shapes`, and raw-state lifetime.
  2. Freeze the next design to either reproduce the ordinary semantics exactly on the gathered axis, or explicitly reject every unsupported mode/key before pack/noise/forward. `data_resolutions=None` may only be used when native semantics prove it is equivalent for the admitted canonical batch.
  3. Add a required CPU/static witness for `image_size`/resolution propagation and the per-camera flag (or explicit fail-closed negatives if those modes are intentionally excluded).
  4. Include the native `pre_noise_memory_hook()` / `build_memory_state()` seam in the post-pack map if the target model class can override those hooks; do not bypass an override implicitly.

### HIGH-2 — native loss reduction axis is not proven to be the canonical valid-consumer axis

- Severity: HIGH
- Location: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_source_audit_v0.1.md:27-28`, §3.2-§3.3.
- Root cause: the audit identifies `compute_flow_matching_loss()` and `_compute_losses()`, but stops before proving that their native instance/reduction axes equal the gathered canonical consumer axis on which `planned_n_valid/original_n_valid_window` is defined.
- Exact source conflict:
  - `compute_flow_matching_loss()` forms a scalar as `per_instance_weighted_loss.mean()` over `len(pred)` for each modality; the returned `[B]` `per_instance_loss` is the unweighted per-instance loss, not the time-weighted vector used to form the scalar;
  - `GenerationDataClean` explicitly allows `num_vision_items_per_sample`, where one logical sample can expand to multiple vision items;
  - action and sound are dense only over samples that have those modalities, and the native training path separately reindexes their schedules;
  - `_compute_losses()` therefore sums modality-specific means and optional sample-level scaling; it is not source-proven here to equal a mean of one combined loss per canonical valid consumer.
- Violated contract: v0.3.5 §7/§20.2-B requires the outer objective to be normalized by actual valid-consumer exposure. Multiplying a scalar whose denominator is a different native item/subset axis by `N_valid/N_window` is not proven equivalent.
- Exact acceptance:
  1. Map the exact cardinality/order relation from gathered consumer rows -> `SequencePlan` -> `GenerationDataClean.batch_size` / `num_vision_items_per_sample` / dense action/sound lists -> `out_net["preds_*"]` -> `compute_flow_matching_loss()` reduction.
  2. Freeze one of two valid next-design contracts: (a) restrict canonical P2 to a source-proven modality footprint where each valid consumer contributes exactly one native instance to every included consumer term; or (b) define an explicit per-consumer aggregation from native item/subset losses before the canonical member mean.
  3. Do not use the currently returned unweighted `per_instance_loss` vector as a surrogate for the weighted scalar without an explicit source/implementation change.
  4. Required evidence must prove `actual_n_valid` is the denominator of the final canonical `consumer_loss` semantics, including any multi-item/dense-subset negative or supported case.

### MEDIUM-1 — GradScaler/optimizer irreversible boundary source map stops at backward

- Severity: MEDIUM
- Location: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_source_audit_v0.1.md:29`, §3.3.
- Root cause: the audit maps the ordinary `loss / grad_accum_iter` backward but then requires the next design to hard-stop before unsupported enabled-GradScaler/optimizer behavior without mapping the actual post-backward optimizer boundary.
- Exact source gap: current trainer increments `grad_accum_iter`, enters optimizer callbacks at the GA boundary, calls `_preflight_active_optimizer_boundary(...)`, then `_optimizer_step(...)`; `_optimizer_step` owns `grad_scaler.unscale_/step/update` and scheduler disposition for the existing active route. None of that route is authority for the new canonical path, but these are the concrete irreversible seams the new design must avoid or supersede.
- Exact acceptance:
  1. Add the exact trainer source map from post-backward `grad_accum_iter` increment through optimizer callbacks, `_optimizer_step`, `GradScaler.step/update`, scheduler step and zero-grad.
  2. Freeze the next canonical dispatcher/design hook so an unsupported enabled scaler/real optimizer boundary fails before any irreversible slow optimizer/scheduler action, with no reuse of active/legacy lifecycle authority.
  3. Preserve ordinary No-Local callback/optimizer behavior unchanged and require a CPU/static boundary witness.

## Verified non-blocking parts

- formal Gitlink at `dec45ec` resolves exactly to child `5d0e037`;
- the current canonical producer bridge really hard-stops before native pack/noise/forward and aborts its scan capability;
- `pack_input_sequence()` consumes Local prefixes out-of-band in caller plan order and represents absent Local as `None` without changing native geometry;
- the current ordinary trainer branch does divide the returned loss by native GA, so the future canonical window-normalized objective must bypass that scalar division;
- the historical `canonical_segment_forward` / `CanonicalSegmentWiring` dispatcher is a separate old schema and must remain non-authoritative;
- this audit pair itself is docs-only and authorizes no child/model/trainer/packer modification or real execution.

Current blockers: **2 HIGH, 1 MEDIUM**.

No authority is granted to create `CANONICAL-NATIVE-FORWARD-LOSS-IMPLEMENTATION-DESIGN` yet. Authorized next action is docs-only remediation of this source audit on a new formal root SHA, keeping the child SHA explicit if unchanged. No child modification, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, native forward/loss/backward, training, evaluation, inference, runtime sidecar, or LIBERO4IN1 is authorized.