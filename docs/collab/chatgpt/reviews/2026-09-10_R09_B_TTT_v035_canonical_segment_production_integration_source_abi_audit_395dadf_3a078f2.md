# ChatGPT 独立 Canonical Segment Production Integration Source-ABI Audit v0.3 Review

Formal reviewed pair:
- root audit SHA: `395dadff0b17ed6206887e372718bb166aa63b40`
- child/Gitlink SHA: `3a078f28f3d107bb633c932271f86498f7c427f7`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-INTEGRATION-SOURCE-ABI-AUDIT`
- artifact: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_integration_source_abi_audit_v0.3.md`
- previous formal review: `e0cc97e7178d345c6575bb7f73f540b8ec056f1c / 3a078f28f3d107bb633c932271f86498f7c427f7`, verdict `REQUEST_CHANGES`, canonical review `docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_production_integration_source_abi_audit_e0cc97e_3a078f2.md`.
- request/ledger/session commits after the formal root are bookkeeping only and do not replace this formal pair.

Verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCTION_ABI_IMPLEMENTATION`

## Incremental review result

### CLOSED — prior HIGH: duplicate GA normalization / `1/GA^2`

v0.3 precisely corrects the sole blocker from v0.2.

The audit now keeps four distinct concerns separate:

1. `CanonicalGAWindowPlan.objective()` owns the canonical member-level scalar normalization:
   `planned_n_valid/original_n_valid_window * consumer_loss + auxiliary_loss/original_ga_effective`.
2. the new canonical production branch must perform exactly one scaled backward on that already-window-normalized scalar: `grad_scaler.scale(L_member).backward()`;
3. native `grad_accum_iter` still owns DDP sync timing, GA member clock, optimizer-step cadence and zero-grad boundary;
4. the ordinary No-Local path retains the existing native `loss / grad_accum_iter` behavior unchanged.

Therefore a full-valid GA window now correctly degenerates to exactly `1/GA` per member, not `1/GA^2`. Unequal-valid members remain exactly weighted by `N_valid_i/N_valid_window`, while auxiliary loss remains exactly `1/GA` per member.

This matches v0.3.5 §7.1 and the already-closed scheduler objective contract.

### Prior v0.1/v0.2 closures remain valid

No regression was found in the items already closed by v0.2:

- native flow consumer loss and load-balancing auxiliary loss remain explicitly separated;
- the source map reaches `compute_flow_matching_loss`, `OmniMoTModel._compute_losses`, the real `pack_input_sequence` ordering/prefix behavior, and the trainer GA boundary;
- sample-level/native scaling is required to occur exactly once;
- S0 remains a valid native consumer with Memory Prefix absent (`None`), while PAD produces no native sample;
- existing packer ordering is reusable only after a new canonical producer freezes the stream-major gathered list;
- `CanonicalBatchScheduler.freeze_plan/reconcile_after_backward` remains metadata authority; trainer does not reconstruct chronology;
- old row-wise runtime owner/bridge/active marker routes remain provenance/fail-closed references only and are not production authority for the new `[B_stream,T]` route.

### Scope / authority check

The formal child remains exactly `3a078f28f3d107bb633c932271f86498f7c427f7`; this remediation is docs-only and introduces no child code change.

The next authorized action is only to create the P1 **docs-only production ABI implementation design**. That design must independently freeze the exact whitelist and new segment-level production seam, including:

- immutable `SegmentBatchProducer` and scheduler-member identity/count binding;
- stream-major valid gather with PAD excluded and S0 prefix absent;
- real native `consumer_loss` / `auxiliary_loss` / `actual_n_valid` decomposition;
- exact pre-backward count validation;
- exactly-once canonical objective/backward scaling with native GA clock/DDP sync/optimizer cadence preserved;
- post-success backward reconcile/fast-state commit and fail-closed exception/GradScaler disposition;
- No-Local parity;
- CPU/static algebra Evidence proving full-valid `1/GA`, unequal-valid `N_valid_i/N_valid_window`, and auxiliary `1/GA`.

Current blockers: none.

`APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCTION_ABI_IMPLEMENTATION`

This approval closes only the P0 docs-only source-ABI audit for the exact formal pair above. It does **not** authorize child implementation, producer/packer/dataset/model/trainer/config/optimizer/checkpoint changes, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, runtime sidecar, LIBERO4IN1, training, evaluation, or inference. Any later formal root or child SHA change requires fresh independent review.
