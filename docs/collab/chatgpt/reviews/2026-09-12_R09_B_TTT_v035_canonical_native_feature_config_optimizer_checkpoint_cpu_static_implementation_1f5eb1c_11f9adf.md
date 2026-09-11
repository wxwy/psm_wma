# ChatGPT Independent Review — R09-B TTT v0.3.5 Canonical Native Feature / Config / Optimizer / Checkpoint CPU/static Implementation remediation

**Date:** 2026-09-12  
**Formal root:** `1f5eb1cbf172893a1640008a15d23e878ca73ed3`  
**Formal child/Gitlink:** `11f9adf7fa209805ef6437145cf7a0dbf1625697`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-CPU-STATIC-IMPLEMENTATION`  
**Requested verdicts:** `APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_NATIVE_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 1. Pair / scope

- Re-locked remote `V2`, re-read live `CODEX_INBOX.md`, and independently verified formal root `1f5eb1cbf172893a1640008a15d23e878ca73ed3` resolves `cosmos-framework` exactly to reachable child `11f9adf7fa209805ef6437145cf7a0dbf1625697`.
- `568711bb…` is request/ledger bookkeeping only and does not replace the formal pair.
- The corrected Gate is now the distinct implementation Gate without the `-DESIGN` suffix.
- The remediation child remains within the approved two-file scope: `config_checkpoint_contract.py` and `config_checkpoint_contract_test.py` only.
- The reported `14 passed` plus Ruff/py_compile/diff-check are supporting evidence only; source truth remains authoritative.
- Binding authority remains the approved composite refreeze contract v0.1+v0.2+v0.3 and the approved CPU/static implementation design v0.1+v0.2.

## 2. Prior HIGH remediation status

### Prior HIGH-1 — PARTIALLY CLOSED; lineage authority is still not canonical

The remediation improves syntax substantially: child revision is now constrained to lowercase 40-hex; manifest/source fields are constrained to 64-hex; and `checkpoint_source_fingerprint` is derived by canonical JSON SHA-256 from a versioned descriptor.

However, the approved refreeze contract is stricter than syntactic digest shape:

- `child_git_revision` must come from the current checked-out/reachable child owner and must not be arbitrary caller input;
- the checkpoint source descriptor must contain at least source kind, immutable source identifier, and source-manifest digest;
- manifest/source identities must be derived from frozen owner inputs rather than accepted as caller-selected digest strings.

Current `_SOURCE_DESCRIPTOR_KEYS` is only `{schema, source_sha256}` and `build_base_identity()` still accepts `child_git_revision`, `manifest_sha256`, and `source_sha256` directly from its caller. The test fixture uses `child_git_revision="f" * 40`, which proves that an unrelated but syntactically valid SHA is accepted. Therefore a foreign lineage can still be made canonical-looking without being bound to the actual child/manifest/source owner.

**Acceptance:** make BaseIdentity construction owner-derived rather than caller-authoritative. The versioned source descriptor must include the frozen source-kind / immutable-source-id / source-manifest fields required by the approved refreeze contract; child revision and manifest/source digests must be tied to explicit immutable owner inputs. Add a witness that a different syntactically valid 40-hex child SHA and a descriptor lacking those lineage fields are rejected.

### Prior HIGH-2 — CLOSED for the requested owner/core/projector dimensions, but one inherited feature-version ABI hole remains

The remediation now correctly binds live evidence/core dimensions, Local dimension, K_local, TBPTT, inner LR, projector `32 -> 2048`, projector-bias presence, and modality shape before mutation. This closes the specific previous HIGH.

A remaining inherited contract hole is described separately below because `local_evidence_feature_version=causal_visual96_executed_action10_v1` still is not bound to the live encoder's visual/action input ABI or canonical state/dt/age-disabled construction.

### Prior HIGH-3 — PARTIALLY CLOSED; structural fields are added, but the identity is still not the frozen versioned/digested identity mapping

The remediation adds the requested structural fields: named/ordered AdamW groups and members, member state schema, scheduler optimizer binding, constructor gamma, and scheduler state schema; it also narrows the synthetic path to AdamW + ExponentialLR.

But the approved refreeze contract states that **all identity mappings** are versioned exact mappings serialized with canonical JSON/SHA-256, and that saved mapping, expected mapping, digest, and schema key-set all exact-match. Current `optimizer_identity` is an unversioned raw `{class, groups}` mapping and `scheduler_identity` is an unversioned raw `{class, optimizer_identity, constructor, state_schema}` mapping. Neither has a schema/version nor a canonical digest, and restore compares ordinary Python mappings directly.

That leaves the implementation weaker than the frozen identity contract and also makes typed identity equality depend on Python value equality rather than canonical typed serialization.

**Acceptance:** make optimizer and scheduler identities versioned exact schemas, canonical-JSON serializable, with their frozen SHA-256 identity digests carried/validated in the payload exactly as required by refreeze v0.2. Missing/unknown/type/digest drift must reject before mutation. Add direct schema/digest/type-drift witnesses.

### Prior HIGH-4 — CLOSED

Save and restore now reconstruct detached pristine AdamW + ExponentialLR shadows from validated identity. Restore compares payload scheduler state against the reconstructed pristine shadow rather than current live scheduler state. The new direct witness where live scheduler progress is advanced while payload is changed to match that live state correctly targets the prior defect.

### Prior HIGH-5 — CLOSED

The formal request now uses the distinct implementation Gate:
`G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-CPU-STATIC-IMPLEMENTATION`.

## 3. New source-level blocker inherited from FeatureConfigIdentity semantics

### HIGH — `local_evidence_feature_version` is not bound to the actual live evidence encoder feature ABI

The frozen identity value `causal_visual96_executed_action10_v1` semantically binds the Local evidence path to 96-d visual summary + 10-d executed action with canonical state/dt/age-disabled evidence construction. Current `_validate_feature_config_against_runtime()` checks only `runtime_encoder.evidence_dim`; it does not verify:

- `runtime_encoder.visual_proj.in_features == 96`;
- `runtime_encoder.action_proj.in_features == 10`;
- `runtime_encoder.feature_config == CANONICAL_EVIDENCE_FEATURE_CONFIG` (state/dt/age all disabled).

Thus a live encoder with the same output `evidence_dim=96` but foreign visual/action input ABI or legacy state/dt/age adapters can pass while the payload still claims `causal_visual96_executed_action10_v1`.

**Acceptance:** bind the feature-version identity to the actual registered encoder ABI before mutation: exact visual/action input dimensions and canonical disabled state/dt/age feature config. Add direct drift witnesses for visual dim, action dim, and legacy feature config.

## 4. Formal verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/config_checkpoint_contract.py:46)`

Current blockers: **3 HIGH, Production**.  
Authority/Design blockers: **0**.  
Evidence-only blockers: **0**.

Open blockers:
1. BaseIdentity lineage remains syntactically canonical but caller-authoritative and source descriptor is under-specified.
2. Optimizer/scheduler identities remain unversioned and undigested despite the frozen canonical identity discipline.
3. `local_evidence_feature_version` is not bound to live visual/action/state-dt-age evidence ABI.

Closed from the prior review: exact implementation Gate separation, detached pristine scheduler reconstruction, and the requested owner/core/projector dimension/bias binding.

## 5. Scope

No real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, native real forward/loss/backward, optimizer/scheduler step, sidecar/resume, single-GPU smoke, matched smoke, training, evaluation, inference, or LIBERO4IN1 is authorized. Remediation remains limited to the already approved two child files unless a new design Gate is required.