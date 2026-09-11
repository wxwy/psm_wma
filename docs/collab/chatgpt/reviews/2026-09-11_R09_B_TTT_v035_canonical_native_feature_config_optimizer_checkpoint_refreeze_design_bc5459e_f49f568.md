# ChatGPT Independent Review — R09-B TTT v0.3.5 Canonical Native Feature / Config / Optimizer / Checkpoint Refreeze Design v0.2

**Date:** 2026-09-11  
**Formal root:** `bc5459e91ad8b53c52ffaadfde9d585508dadec4`  
**Formal child/Gitlink:** `f49f568923555fe15efe546925cbe6cc9140170e`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-REFREEZE-DESIGN`  
**Requested verdicts:** `APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_REFREEZE` or `REQUEST_CHANGES(file:line)`.

## 1. Pair / scope

- Re-locked remote `V2`, re-read live `CODEX_INBOX.md`, and independently verified formal root `bc5459e91ad8b53c52ffaadfde9d585508dadec4` resolves `cosmos-framework` exactly to reachable child `f49f568923555fe15efe546925cbe6cc9140170e`.
- Child remains unchanged; the remediation is root docs-only.
- This review is incremental against rejected v0.1 formal pair `f890b72fe1ff27eaa5eca0eb7b185af2c6b75459` / same child and its three Design-only HIGH findings.

## 2. Remediation status

### HIGH-1 — CLOSED

v0.2 freezes a versioned `FeatureConfigIdentity` that now includes the active Local activation/backend/dimension fields and `enable_input_bias`, together with the resolved TTT identity. It explicitly rejects missing/unknown/type/value drift before mutation and correctly treats projector bias as ABI identity rather than relying on a late tensor mismatch.

### HIGH-2 — CLOSED

v0.2 replaces the generic caller-selected base mapping with a versioned exact `base_identity` schema binding child revision, canonical model-config digest, checkpoint-source fingerprint, manifest digest, and source digest. It explicitly forbids generic defaults/caller-chosen labels and requires pre-mutation exact comparison.

### HIGH-3 — PARTIALLY CLOSED; one Design HIGH remains

The optimizer/scheduler class, ordered groups/members, typed hyperparameters, state-key/schema/shape/dtype/device identity and staged shadow validation are now substantially frozen. However the required **progress relation itself is still not frozen in this Gate**.

At v0.2 line 64 the optimizer identity only requires each member's `step` plus "its consistency rule" with global `iteration`, without stating that rule. More importantly, line 66 says scheduler progress must have an exact relation to optimizer progress and payload `iteration`, but then explicitly defers the executable single predicate to the **next implementation design**.

That does not close the prior acceptance requirement: this refreeze Gate must determine what exact progress identity means; the next implementation design may encode/test the predicate but must not invent it. Otherwise two incompatible step/iteration policies can both satisfy this design while claiming the same checkpoint identity.

**Acceptance:** freeze the exact canonical optimizer-step / scheduler-progress / payload-iteration relation in this design (or a superseding design) before approval. If the relation is class-dependent, freeze the approved optimizer/scheduler class(es) and the exact predicate for each. The later implementation design may translate that already-frozen relation into executable validation and witnesses, but may not choose the semantics.

## 3. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_feature_config_optimizer_checkpoint_refreeze_design_v0.2.md:66)`

Current blockers: **1 HIGH, Design-only**.  
Production blockers: **0**.  
Evidence blockers: **0**.

## 4. Scope

No child implementation or real execution is authorized. Real checkpoint/data I/O, DCP, CUDA/GPU, `torchrun`, native real forward/loss/backward, optimizer/scheduler stepping, sidecar/resume, single-GPU smoke, matched smoke, training, evaluation, inference, and LIBERO4IN1 remain prohibited.
