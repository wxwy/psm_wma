# ChatGPT Independent Review — R09-B TTT v0.3.5 Canonical Native Feature / Config / Optimizer / Checkpoint Refreeze Design v0.1

**Date:** 2026-09-11  
**Formal root:** `f890b72fe1ff27eaa5eca0eb7b185af2c6b75459`  
**Formal child/Gitlink:** `f49f568923555fe15efe546925cbe6cc9140170e`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-REFREEZE-DESIGN`  
**Requested verdicts:** `APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_REFREEZE` or `REQUEST_CHANGES(file:line)`.

## 1. Pair / scope

- Re-locked remote `V2`, re-read live `CODEX_INBOX.md`, and independently verified formal root `f890b72fe1ff27eaa5eca0eb7b185af2c6b75459` resolves `cosmos-framework` exactly to reachable child `f49f568923555fe15efe546925cbe6cc9140170e`.
- Child is unchanged from the closed CPU/static runtime Gate; the technical root delta is docs-only plus review/coordination bookkeeping.
- The inherited runtime source-audit contract remains binding, especially item 7: feature flags/dims, exact canonical trainable inventory, optimizer membership, checkpoint config/manifest/source identity, and old-checkpoint fail-closed ownership.

## 2. Positive findings

The design correctly preserves the frozen progression and does not authorize GPU/real I/O. It also correctly captures the active trainable Local projection path: current child registers `local_memory2llm` and `local_memory_modality_embed`; the refreeze inventory includes both together with the registered evidence encoder and TTT core. The projector remains per-token `32 -> 2048`, and fast runtime/frontier/pending authority is excluded from the slow payload.

## 3. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_feature_config_optimizer_checkpoint_refreeze_design_v0.1.md:15)`

Current blockers: **3 HIGH, Design-only**.  
Production blockers: **0**.  
Evidence blockers: **0**.

### HIGH-1 — versioned config identity does not freeze the active Local feature flags/dimensions

Section 2 says the `LocalMemoryConfig` / `OmniMoTModelConfig` exact identity must contain **only** six TTT fields (`ttt_tbptt_steps`, `ttt_inner_lr`, `k_local`, feature version, fast dtype, resume mode). That is weaker than the inherited source-audit requirement to refreeze feature flags/dims.

Current child source shows that active construction also depends on `local_memory_enabled`, `local_memory_dim`, `local_history_enabled`, `local_history_backend`, `local_history_evidence_dim`, and `local_ttt_enabled`; `enable_input_bias` changes the Local projector parameterization. These are not decorative fields: they determine whether the registered owner exists, its shapes, backend, and whether the projector has a bias.

**Acceptance:** freeze the exact active Local feature/config identity, either directly in the versioned Local mapping or in a separately named exact config-identity block that is mandatory before restore. It must at minimum bind the activation/backend/dimension fields that determine the canonical owner/projector ABI. Unknown/missing/drift values must fail before mutation. Do not rely on later tensor-shape failure as the definition of config identity.

### HIGH-2 — `base_identity` is not a frozen checkpoint identity schema

Section 4 requires a `base identity` but does not define its exact fields, derivation, or allowed values. Therefore a caller-chosen non-empty mapping can satisfy the design while failing to bind the slow payload to the intended model/config/source lineage. This does not satisfy the inherited requirement for checkpoint config/manifest/source identity and old-checkpoint fail-closed behavior.

The current child implementation illustrates the gap: `slow_checkpoint_payload()` accepts an arbitrary mapping and even defaults to `{"schema": "local-memory-cpu-static-v1"}`; restore only compares equality with a caller-provided expected mapping. That proves a schema owner exists, not that the checkpoint identity is canonical.

**Acceptance:** define a versioned, exact `base_identity` schema and its owners. It must bind the immutable identities needed to reject a foreign/old slow payload (for example child/source revision plus canonical model/config/checkpoint-source fingerprint; include manifest/source digests where this Gate claims them). Missing/unknown/drift keys must reject before live mutation; no caller-guessed generic identity is sufficient.

### HIGH-3 — optimizer / scheduler identity is not actually refrozen

Sections 3–5 mention exact optimizer membership, `optimizer/scheduler schema+state`, and iteration, but do not freeze the optimizer class, ordered param-group schema and hyperparameters, state-slot tensor semantics, scheduler type/state identity, or scheduler/optimizer/iteration step consistency.

The current child validator likewise checks structural loadability and parameter IDs but does not require saved param-group hyperparameter values to equal an approved frozen identity before load; a load can therefore mutate optimizer policy while still being structurally valid. A refreeze Gate must distinguish identity from mere `state_dict` loadability.

**Acceptance:** freeze the optimizer and scheduler identity explicitly: optimizer class; ordered groups/member names; required hyperparameters; allowed state keys and tensor shape/dtype/device semantics; scheduler class/config/state; and exact step/iteration consistency. Validate all of these on staged copies before any parameter/optimizer/scheduler/iteration mutation. Add direct witnesses for class/group/hyperparameter/state/step drift with zero live mutation.

## 4. Scope

No child implementation or real execution is authorized by this verdict. Real checkpoint/data I/O, DCP, CUDA/GPU, `torchrun`, native real forward/loss/backward, optimizer/scheduler stepping, sidecar/resume, single-GPU smoke, matched smoke, training, evaluation, inference, and LIBERO4IN1 remain prohibited.
