# ChatGPT Independent Review — R09-B / TTT v0.3.5 Canonical Native Forward/Loss Implementation Design v0.1

**Date:** 2026-09-10  
**Role:** Independent Design / Code / Evidence / Gate Reviewer  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-IMPLEMENTATION-DESIGN`  
**Formal root design SHA:** `6f75365a7a865f42540e987024165faceb981354`  
**Formal child/Gitlink SHA:** `5d0e037ced559c07081fd4880c633dc03f325efe`  
**Approved source-audit authority:** `d75a3371f48c2b6538e093f5fd693f843b72e1d6 / 5d0e037ced559c07081fd4880c633dc03f325efe`  
**Artifact:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_implementation_design_v0.1.md`  
**Verdict:** `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_implementation_design_v0.1.md:79)`

## 1. Repository-truth lock

- Latest `origin/V2` observed at review start was delivery/bookkeeping HEAD `0b470006697227e68f537e6b54827d1836fee355`; it is not the formal design target.
- Latest `CODEX_INBOX.md` request declares exactly formal pair `6f75365a7a865f42540e987024165faceb981354 / 5d0e037ced559c07081fd4880c633dc03f325efe`, Gate `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-IMPLEMENTATION-DESIGN`, and asks only for `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_FORWARD_LOSS_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Formal root tree `87871300d6d604fa6b033fa6e69152d975090e7f` stores `cosmos-framework` exactly at Gitlink `5d0e037ced559c07081fd4880c633dc03f325efe`.
- Child is unchanged from the approved source-audit pair. Root compare from `d75a337...` to `6f75365...` is docs/review/inbox/session bookkeeping plus the new design; no child implementation change is part of this Gate.
- The current child includes the separately authorized retry-lineage CPU/static implementation at `5d0e037...`; this design therefore must preserve the exact attempt-0/attempt-1 objects and cannot reason against an older child.

## 2. Correct / non-blocking parts

The design correctly carries forward several source-audit conclusions:

- seven-file CPU/static whitelist is explicit and keeps `packers.py`, config, optimizer, dataset/dataloader/collate and runtime-sidecar outside scope;
- old row-wise `canonical_segment_forward` and active route remain non-authoritative;
- the current canonical helper is not treated as a reason to fall back through `_get_training_inputs()` / `_prepare_training_data()` / `_inject_local_history()`;
- per-camera retain/raw-state/resolution/VAE-shape semantics, multi-vision-item mapping, dense action/sound identity mapping and memory-hook order are explicitly required;
- unweighted flow `[B]` diagnostics are not accepted as a canonical weighted term;
- LBL auxiliary remains separate from valid-consumer weighting;
- attempt-1 is required to reuse the existing `CanonicalProductionRetryCapability` lineage without re-freeze/re-admit/second transition;
- CPU/static acceptance remains before real I/O/CUDA/native forward/loss/backward/optimizer execution.

These points do not close the two blocking design contradictions below.

## 3. Current blockers

### HIGH 1 — per-consumer aggregation does not preserve the native modality/subset reduction algebra

**Direct blocking location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_implementation_design_v0.1.md:79`

The design says that each modality's `weighted_per_instance` values are mapped to canonical identities, combined into `weighted_consumer_terms`, and then:

`consumer_loss = weighted_consumer_terms.mean()`

with denominator `actual_n_valid`.

That is not yet a complete or source-equivalent algebra for the native loss that v0.2 audited.

Current child source has different native populations and denominators:

- vision flow is `mean()` over the flattened native vision-item list; one logical consumer can own multiple vision items;
- action flow is `mean()` only over the dense action-bearing subset;
- sound flow is `mean()` only over the dense sound-bearing subset;
- `_compute_losses()` applies the modality weights to those separate native means, then applies optional sample-level scale to the summed flow terms, then adds LBL auxiliary;
- when action/sound modality data is absent, the current source also preserves graph connectivity via zero dummy losses rather than inventing a canonical consumer.

A direct gather-to-consumer sum followed by division by `N = actual_n_valid` changes scale whenever `K_vision != N`, `K_action != N`, or `K_sound != N`. Example: with `N=2` consumers but only one action-bearing consumer, native action contribution is `a`; storing `a` on that consumer, zero on the other, then taking the consumer mean yields `a/2`.

The implementation design must therefore freeze an exact cardinality-preserving formula, not leave the implementation to infer one. One valid form for each native modality population `m` is conceptually:

`consumer_term[j,m] = (N / K_m) * sum(weighted_native_item[i] for i owned by consumer j)`

so that `mean_j consumer_term[j,m] == mean_i weighted_native_item[i]` before applying the existing modality weight. Equivalent algebra is acceptable, but it must be explicit and must also preserve sample-level scaling in the same position as ordinary `_compute_losses()`.

There is a second compatibility ambiguity in §3.1. Current `compute_flow_matching_loss()` returns a singleton graph-connected diagnostic vector on its `has_valid_tokens=False` path. The proposed `FlowMatchingLossTerms` declares `weighted_per_instance: Tensor[N]` while also promising the legacy two-return API is unchanged. The design must state how the new primitive obtains source-mappable weighted terms for the real native item population without silently changing the legacy wrapper's externally visible no-valid behavior or fabricating one fake canonical consumer. Modality-absent action/sound dummy graph paths must likewise remain zero graph-connectivity terms, not new consumer entries.

**Violated frozen contract**

- approved source audit v0.2 §3.2: preserve the exact logical-consumer -> multi-item/dense-subset -> weighted native term -> per-consumer aggregate relation;
- source audit v0.2 requirement that sample-level scaling retain ordinary placement and LBL remain independent;
- v0.3.5 valid-consumer objective: `actual_n_valid` may be the final consumer denominator only after the native item/subset means have been transformed without changing their semantics.

**Exact closure condition**

1. Freeze the exact formula converting each modality's native weighted-item population to the `actual_n_valid` consumer vector, including the `N/K_m`-equivalent cardinality compensation for multi-item vision and dense action/sound subsets.
2. Prove algebraically that taking the final consumer mean reproduces the pre-LBL native modality means/scales for supported batches.
3. Freeze absent/no-valid modality graph-connectivity semantics without creating fake consumer identities.
4. State precisely how the new weighted-term primitive and the legacy `compute_flow_matching_loss()` wrapper preserve old return behavior while exposing the new canonical terms.
5. Add CPU/static witnesses for unequal `K_vision`, `K_action`, `K_sound` versus `N`, not only identity routing.

### HIGH 2 — dispatcher lifecycle mixes superseded transaction APIs and cannot satisfy its own zero-commit optimizer boundary

**Direct blocking location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_implementation_design_v0.1.md:90`

The new dispatcher pseudocode says:

`transaction.successful_backward(...)`

followed by:

`adapter.prepare_commit/commit(...)`.

This does not match the current canonical production authority in child `5d0e037...`:

- `CanonicalBatchWindowTransaction` exposes `mark_backward_started(member_index)`, `validate_reconcile(member_index)`, `mark_reconciled(member_index)` and `terminalize(...)`; it has no `successful_backward(...)` method;
- `successful_backward(...)` belongs to the existing active/old transaction path that this design explicitly says must not be reused;
- `CanonicalProductionAdapter` exposes `prepare_commit(request, result)` returning an exact one-shot `CanonicalProductionCommitCapability`, and `commit_success(capability)`; it does not define the generic `commit(...)` lifecycle written here;
- `commit_success()` itself verifies the exact prepared reconcile, calls `transaction.validate_reconcile()`, commits the fast-state frontier, consumes the scheduler reconcile, then calls `transaction.mark_reconciled()`.

There is also a temporal contradiction with the preceding capability definition and following optimizer rule. §4 says `CanonicalNativeForwardCapability` already object-binds a `prepared reconcile`; §5 then appears to call `prepare_commit` again after backward, which would mint another authority rather than consume the exact one already bound. The design must establish one exact commit capability and one exact lifecycle.

More importantly, §5 says a successful canonical member performs backward and success-only commit, but later in the same section requires an enabled GradScaler / real slow optimizer boundary to terminalize before optimizer callbacks with **zero fast-state/scheduler/transaction commit**. At a GA boundary, if prior canonical members have already executed the stated per-member success commits, zero canonical commit is no longer achievable. This conflicts with the currently frozen CPU/static hard-stop policy for unsupported scaler/real optimizer behavior.

**Violated frozen contract**

- current canonical producer transaction/adapter object authority at child `5d0e037...`;
- source audit v0.2 requirement that the new route not reuse active/legacy lifecycle authority;
- source audit v0.2 unsupported-scaler/optimizer rule: fail closed before irreversible optimizer callbacks with zero canonical fast-state/scheduler/transaction commit;
- v0.3.5 rule that the TTT graph closes per microbatch and successful state commit must have an exact post-backward transaction boundary.

**Exact closure condition**

1. Replace the old `successful_backward(...)` / generic `commit(...)` pseudocode with the exact current canonical sequence and object types, including when `mark_backward_started()` is called and exactly one `CanonicalProductionCommitCapability` / prepared reconcile is created and consumed.
2. `CanonicalNativeForwardCapability` must bind the exact adapter owner, request, scan result, commit capability/prepared reconcile and transaction needed by `commit_success()`; no second `prepare_commit()` may be minted for the same scan result.
3. Freeze attempt-1 consumption so the exact current `CanonicalProductionRetryCapability` lineage remains provable through native preparation/loss/backward; no reconstructed retry request/plan authority.
4. Resolve the unsupported enabled-GradScaler/real-optimizer timing. For this CPU/static Gate, either preflight and reject that condition before any canonical member backward/commit in the affected window, or define another source-consistent zero-commit mechanism. The current sequence cannot both commit per member and later claim the whole boundary still has zero canonical commit.
5. Add CPU/static witnesses for the exact transaction states before backward, after successful backward/commit, attempt-1, and unsupported scaler/optimizer rejection, proving no active/legacy method is called.

## 4. Working-copy ownership watchpoint

No separate blocker is opened for this, but the remediation should make the contract concrete while editing the design.

`CanonicalNativePreparedInputs` is described as immutable and says flatten/normalization occurs only on an independent `working_data_batch`. Current native `get_data_and_condition()` writes/replaces mapping fields such as `num_vision_items_per_sample`, may flatten the media field, and calls in-place normalization/augmentation helpers. A frozen dataclass around a shallow dict is not sufficient evidence of carrier immutability.

The next revision should specify field-wise container/tensor/plan ownership or an equivalent non-aliasing construction, and the CPU/static witness should mutate every admitted working field that native preparation may rewrite and prove the exact `CanonicalRawRowCarrier.model_data_batch` / row source objects remain unchanged. This is part of closing HIGH 1's source-map integrity, not a third blocker.

## 5. Scope / authorized next action

Current blocker count: **2 HIGH**.

Authorized next action is docs-only remediation of this implementation design on a new formal root SHA, keeping child `5d0e037ced559c07081fd4880c633dc03f325efe` explicit if unchanged.

No child code, packer/model/trainer implementation, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, native forward/loss/backward execution, optimizer step, training/evaluation/inference, runtime sidecar, distributed execution, or LIBERO4IN1 is authorized by this review.

## 6. Exact verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_implementation_design_v0.1.md:79)`
