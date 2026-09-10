# ChatGPT 独立 Canonical Segment Production Integration Source-ABI Audit Review

Formal reviewed pair:
- root audit SHA: `2d34eedcf30163de9e011bf1c4166199e916a2f6`
- child/Gitlink SHA: `3a078f28f3d107bb633c932271f86498f7c427f7`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-INTEGRATION-SOURCE-ABI-AUDIT`
- artifact: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_integration_source_abi_audit_v0.1.md`
- frozen authority: `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md` §18, §20.1--§20.2; approved production-integration design pair `ce8e3502af5226d42c270dca4d5387cec8bed412 / 3a078f28f3d107bb633c932271f86498f7c427f7`; already-closed canonical batch scheduler contract.
- request/bookkeeping SHA observed: `a7b1a705708518b0e410aeacaf49e38052ea690c`; later polling/session SHAs are bookkeeping only and do not replace the formal pair.

Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_integration_source_abi_audit_v0.1.md:74)`

## Findings

### HIGH — P1 loss bridge is frozen against the wrong scalar

- Severity: HIGH
- Location: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_integration_source_abi_audit_v0.1.md:27`, `:74`
- Root cause: the audit concludes that P1 should multiply the **native total loss** by `member.planned_n_valid / plan.original_n_valid_window` before trainer scale/backward. That is not the already-frozen canonical GA objective.
- Violated contract: the closed canonical scheduler contract separates the valid-consumer mean from non-consumer-count-linear auxiliary loss. `CanonicalGAWindowPlan.objective()` is exactly
  `planned_n_valid/original_n_valid_window * consumer_loss + auxiliary_loss/original_ga_effective`.
  The real child source confirms that this distinction is material: `flow_matching.py::compute_flow_matching_loss` reduces per-instance flow loss to a sample mean; `OmniMoTModel._compute_losses()` applies optional sample-level flow scaling and only afterwards adds load-balancing auxiliary losses. Therefore multiplying the returned native total loss by the valid-count factor would incorrectly valid-count-weight the auxiliary term whenever member counts differ, and can also obscure/double native sample-level/DDP scaling.
- Exact acceptance:
  1. Replace the total-loss weighting conclusion in §3/§8 with an exact source map through `cosmos_framework/model/generator/algorithm/loss/flow_matching.py::compute_flow_matching_loss`, `OmniMoTModel._compute_losses`, and the trainer backward/GA seam.
  2. Freeze P1 to expose or derive separate `consumer_loss`, `auxiliary_loss`, and `actual_n_valid` at the real native seam; validate `actual_n_valid == member.planned_n_valid` before backward.
  3. Use only the frozen objective `member.planned_n_valid / plan.original_n_valid_window * consumer_loss + auxiliary_loss / plan.original_ga_effective`.
  4. State where native sample-level/DDP scaling is applied exactly once. If that decomposition/reduction cannot be proven from the real production path, fail closed and split a design Gate rather than reweight an unknown total loss.

### MEDIUM — §20.2-A source map stops above the real packer/loss-mask ABI

- Severity: MEDIUM
- Location: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_integration_source_abi_audit_v0.1.md:16-20`
- Root cause: the audit maps `custom_collate_fn` and high-level `OmniMoTModel._prepare_training_data` / forward calls, then concludes that no canonical variable-valid gather/stream-major/PAD ABI exists, but it does not map the actual `pack_input_sequence` sample loop/order or the actual consumer loss-mask/reduction implementation required by the approved P0 acceptance.
- Violated contract: approved production-integration design P0 requires source-level `file:line` findings for the real dataset/packer/native-batch payload, batch dimension, consumer loss mask, flatten order, and exact reduction seam; P0 PASS is a complete reproducible source map, not only the correct high-level disposition.
- Exact acceptance:
  1. Add the real packer source map (`cosmos_framework/data/generator/sequence_packing/packers.py::pack_input_sequence`) showing native per-`sequence_plan` ordering, payload/index ownership, Memory Prefix per-sample handling, and the absence of canonical `[B_stream,T] consumer_valid` / logical-PAD gather.
  2. Add the real flow-loss mask/reduction source map (`cosmos_framework/model/generator/algorithm/loss/flow_matching.py`) and connect it to `_compute_losses()` so the current native consumer mean is demonstrably identified.
  3. Explicitly state which native ordering/mask semantics are reusable and why they are insufficient to establish canonical stream-major segment gather without the new producer/adapter.

## Verified non-blocking parts

The following source-audit conclusions are supported by the exact child and may be retained:

- Memory Prefix represents per-sample absence as `None -> zero-length offset -> present=False`; S0 therefore need not be represented by a zero token.
- `LocalEvidenceEncoder(feature_config=CANONICAL_EVIDENCE_FEATURE_CONFIG)` truly omits state/dt/age parameter branches, and `encode_segment()` accepts only canonical visual/action evidence.
- `CanonicalBatchScheduler.freeze_plan()` remains metadata-only projected authority and `reconcile_after_backward()` enforces exact planned count/order.
- the old row-wise production active-wiring native adapter is still hard-stopped and cannot be treated as the canonical `[B_stream,T]` production adapter.
- child/Gitlink resolves exactly to `3a078f28f3d107bb633c932271f86498f7c427f7`; this P0 artifact itself is docs-only.

Current blockers: **1 HIGH, 1 MEDIUM**.

No P1 production-ABI implementation design authority is granted. No child implementation, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, runtime sidecar, LIBERO4IN1, training, evaluation, or inference is authorized.
