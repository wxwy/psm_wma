# ChatGPT Independent Review — R09-B TTT v0.3.5 Canonical Native Consumer Runtime Source Audit v0.1

**Date:** 2026-09-11  
**Formal root:** `d554ee6498c4d4facd60cf688beec77c86ea8705`  
**Formal child/Gitlink:** `08775da2e73e352ebb1497548de5909baab8c2dc`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-CONSUMER-RUNTIME-SOURCE-AUDIT`  
**Upstream approved design:** `825f08673536bcfeb4983688c463e04b5d16f312 / 08775da2e73e352ebb1497548de5909baab8c2dc`  
**Verdict:** `APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_NATIVE_CONSUMER_RUNTIME_SOURCE_AUDIT`

## 1. Lock / pair / scope

- Re-locked remote `V2` and re-read the current Codex request. The request/ledger HEAD is bookkeeping; the exact technical target is the formal pair above.
- Independently verified root `d554ee6498c4d4facd60cf688beec77c86ea8705` resolves `cosmos-framework` exactly to reachable child `08775da2e73e352ebb1497548de5909baab8c2dc`.
- Relative to approved audit-design root `825f086...`, the child is unchanged. The technical delta is root-only documentation, principally `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_consumer_runtime_source_audit_v0.1.md`; intervening review/inbox/session/TODO changes are bookkeeping.
- This review is source/docs only. No project Python/pytest, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, native forward/loss/backward execution, optimizer/scheduler step, runtime sidecar, training, evaluation, inference, or LIBERO4IN1 was executed.

## 2. Independent source verification

### 2.1 Canonical path hard-stop — VERIFIED

At exact child `08775da...`, `OmniMoTModel._canonical_production_segment_forward()` performs carrier preflight, exact production adapter scan, canonical-safe input preparation, native-preparation attachment, and then unconditionally raises:

`RuntimeError("canonical-production native forward seam is unavailable")`

This occurs before the real native pack/noise/network/loss continuation. Therefore the audit is correct to refuse any claim that variable-valid canonical consumers are already connected to real Cosmos native forward/backward.

### 2.2 A — variable-valid gather/PAD — VERIFIED as PARTIAL/fail-closed

`CanonicalRawRowCarrier.expected_for()` validates exact request/member/segment identity, rejects non-absent PAD rows, requires present valid rows, checks canonical identities, and requires the gathered expected count to equal frozen `planned_n_valid`. `OmniMoTModel` also compares the production scan gathered identities/count against the carrier expected traversal before the hard-stop.

This proves metadata/gather preflight only, not that the native packer accepts `N_valid_micro < B_stream*T`. The audit correctly routes the unresolved native ABI to later design and forbids trainable zero-PAD substitution.

### 2.3 B/C — native reduction, GA, planned count, suffix recovery — VERIFIED

`canonical_segment_adapter_scheduler.py` explicitly states that it models metadata only and is not a producer, packer, model-forward, runtime-sidecar, or trainer integration point. Its frozen plan validates actual gathered count against `planned_n_valid` and computes:

`planned_n_valid / original_n_valid_window * consumer_loss + auxiliary_loss / original_ga_effective`.

Its typed suffix recovery preserves the original uncommitted suffix and recomputes suffix-only `N_window` and `GA_effective`.

The trainer's canonical-native branch consumes `request.plan.objective()` and calls `grad_scaler.scale(objective).backward()` without the ordinary branch's unconditional `/grad_accum_iter`; the ordinary fallback still applies `loss / grad_accum_iter`. Because the model hard-stops before producing `psm_canonical_native_forward`, the audit correctly classifies real native objective/backward ownership as NOT PROVEN rather than production-closed.

### 2.4 D — state/dt/age feature disable — VERIFIED module-level PASS

`CANONICAL_EVIDENCE_FEATURE_CONFIG` is `state=False, dt=False, age=False`. `LocalEvidenceEncoder.__init__()` only registers the corresponding state/dt/age modules when enabled; `forward()` rejects disabled feature inputs, and `encode_segment()` requires the canonical config. This is a real construction-time disable, not constant-zero feature injection.

The audit correctly limits this PASS to the module construction/forward owner and carries optimizer/checkpoint inventory into a separate refreeze Gate.

### 2.5 E/F — legacy supersession and Memory Prefix — VERIFIED as PARTIAL/fail-closed

`OmniMoTModel.training_step()` dispatches canonical-production first, then active registry, then the legacy canonical marker before ordinary training. Ordinary `_inject_local_history()` still materializes row-wise `local_memory`. This supports the audit's conclusion that legacy/active row-wise routes cannot be silently reused as canonical `[B_stream,T]` production mutation authority.

`build_memory_prefix_context()` accepts sparse `list[Tensor | None]`, projects present per-sample local slots, maintains per-sample offsets/presence, and enforces common positive `K_local`; Unified MoT layernorms/injects this `memory_prefix_context` into attention. The ABI is reusable, but the canonical route still hard-stops before real native packing, so stream-major valid-gather-to-native identity remains unproven. The audit classification is correct.

### 2.6 G/H — deferred obligations — VERIFIED

The source proves only partial static prerequisites: canonical production rejects context parallelism before scan; the continual TTT core has fp32 K/Q/V computation and explicit `create_graph` controls, but the real native-forward/backward/smoke path is not connected. The audit is therefore correct not to claim measured memory, throughput, budget satisfaction, complete real `W_fast` runtime lifetime, or production single-GPU feasibility.

Runtime sidecar/distributed/world-size exact-resume ownership is likewise not implemented by the metadata-only scheduler or current hard-stopped production branch. The audit correctly keeps G as `DEFERRED / NOT PROVEN` and H as a mandatory separate pre-formal-training Gate.

## 3. Audit-design acceptance

The approved v0.2 design required:

- A–F current-child `file:line` PASS/FAIL facts and identity ownership;
- normal/recovery formula and owner mapping with no second unconditional GA scaling;
- `[B,T] -> valid gather -> [N_valid,K,2048]` ownership/fail-closed disposition;
- legacy retain/bypass/delete classification;
- G explicitly `DEFERRED / NOT PROVEN`;
- H explicitly a named mandatory separate Gate;
- no child modification or runtime execution.

The submitted audit satisfies those requirements. I found no material source misstatement, no silent promotion of synthetic/static evidence into production closure, and no omitted A–H obligation that would invalidate the handoff to a later docs-only implementation design.

## 4. Scope-limited closure

This approval closes only the exact root-only source-audit Gate for formal pair `d554ee6498c4d4facd60cf688beec77c86ea8705 / 08775da2e73e352ebb1497548de5909baab8c2dc`.

It does **not** authorize child implementation, removal of the native-forward hard-stop, project-code execution, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, native forward/loss/backward execution, optimizer/scheduler stepping, runtime sidecar, distributed execution, single-GPU smoke, LIBERO4IN1 matched smoke, training, evaluation, or inference.

The next permitted action is only a separately reviewed docs-only canonical native consumer runtime implementation design based on these fail-closed source facts.

## 5. Formal verdict

`APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_NATIVE_CONSUMER_RUNTIME_SOURCE_AUDIT`

Current blockers: `0`.
