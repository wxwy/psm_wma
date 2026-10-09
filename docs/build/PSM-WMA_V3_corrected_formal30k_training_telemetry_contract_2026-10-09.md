# Corrected V3 Formal30k — Training Telemetry Contract

Date: 2026-10-09
Gate: CORRECTED-V3-FORMAL30K-CONFIG-AND-TELEMETRY-READINESS

## Purpose

Observe training health **without altering numerical training behavior**. The verified
formal30k config remains: max_iter=30000, warmup=500, save_iter=100, T=16,
B_stream=8, GA=2, K_local=4, world_size=8. Exact cache and source are unchanged.

One structured `[CorrectedV3][train]` line per **successfully committed optimizer
step**, from rank0 only. Failed/aborted windows must never be logged as success.
Save latency is a separate `[CorrectedV3][checkpoint]` event.

## Loss, every step

- `outer_loss`: actual sum of already-weighted native backward losses; never
  reweight this term when aggregating.
- `flow_matching_loss_action`, `flow_matching_loss_vision`: raw model scalar
  losses, aggregated as a valid-consumer-weighted mean across GA members and
  TBPTT indices, not a mean over native-forward calls.
- `action_contribution`, `vision_contribution`: above raw means multiplied
  by frozen config weights, reported only if a constant weight is demonstrably
  valid (dynamic sample-level scaling or image-only special weights => null).
- `aux_loss_gen`, `aux_loss_und`: actual model scalar auxiliary losses if
  produced. Not-present is null, never fabricated zero.
- Each scalar component records coverage, and rank0 loss is explicitly labeled
  rank-local. Action is a subset of generation parameters, not a separate
  autograd objective for gradient norm computation.

The fast-weight inner loss does **not** add directly into outer loss.

## Local-TTT, every step

Reuse `ContinualTTTLocalMemoryCore.drain_telemetry()`, no new fast update:
- `inner_loss_mean/max/count`
- `fast_state_norm_mean/max/count`
- `fast_update_norm_mean/max/count`

These aggregate per-inner-update row samples. Core runs in fp32 and reports
detached values.

## Gradient and slow parameter norms

Every step, after existing unscale and pre-optimizer hooks, before optimizer:
- `total_grad_norm_rank_local`
- `generation_grad_norm_rank_local`
- `action_grad_norm_rank_local` (subset of generation)
- `local_grad_norm_rank_local`
- Local details:
  - `local_encoder_grad_norm_rank_local`
  - `local_core_grad_norm_rank_local`
  - `local2llm_grad_norm_rank_local`
  - `local_modality_embed_grad_norm_rank_local`
- selected-gradient tensor counts, missing and non-finite tensor counts.

Every 100 successful optimizer iterations, sample rank-local L2 norms of
the same slow-parameter groups. All selected parameters are included even
if their gradients are absent on that step. **FSDP/DTensor local shards are
not globally reduced**; do not compare this field against global clipping
norms as if they were identical.

## Step time, every step

The corrected implementation uses an *empty trigger loader*. Raw windows
and segments are synchronously materialized inside the grouped training step;
there is no background dataloader queue.

- `data_wait_ms=null`: explicitly unavailable, not falsely reported as zero.
- `data_prepare_ms`: `ExactWindowSegmentProducer.produce` over all GA members
  (raw/cache lookup, transforms and segment construction, on host).
- `batch_collate_ms`: grouped native-batch collation.
- `batch_transfer_ms`: batch materialization / CPU-to-device dispatch.
- `local_scan_ms`: model-owned Local adapter scan and fast-weight update.
- `forward_ms`: model Policy native forward.
- `backward_ms`: native backward.
- `optimizer_ms`: optimizer + scheduler call.
- `step_wall_ms`: first trigger fetch to Local `post_commit`, excluding
  checkpoint I/O and telemetry scalar materialization.
- `valid_consumers_per_second_rank_local`: throughput denominator from that
  step's valid consumer count.

These are CPU host wall / CUDA-dispatch stage durations, **not GPU occupancy**
or GPU kernel busy time. `other_host_overhead_ms` covers uncategorized work
(validation, planning, tensor checks, etc.). No per-consumer `.item()` for
telemetry: loss/grad stats are detached and collected at successful step end.

## CUDA and checkpoint timing, low cadence

Every 100 steps (rank0 only), use CUDA events around transfer, Local scan,
forward, backward, optimizer. One synchronize is permitted on a sampled step,
not once per consumer or once every step. Fields are current-stream event
elapsed estimates and do not assert all-rank CUDA utilization.

Record peak rank0 allocated/reserved GPU memory each step. Log checkpoint
save wall time only upon successful `Checkpointer.save`, as a separate record.

## Guardrails

- Retain `config.trainer.callbacks={}` and the sole DCP dataloader owner.
- Do not change optimizer parameter selection, loss scaling, TBPTT/GA
  ordering, Local commit, DCP state or sampling.
- Telemetry code must never perform extra distributed collectives.
- No duplicated static/GPU/full-corpus smoke due to logging-only changes.
- Targeted CPU tests for weighting, no per-consumer item, timing boundaries,
  rank0-only success, abnormal-step no-success, and checkpoint timing.
- A fresh exact child/root/Gitlink pair and explicit review is required
  before formal30k training. No training authorization is implied by this doc.
