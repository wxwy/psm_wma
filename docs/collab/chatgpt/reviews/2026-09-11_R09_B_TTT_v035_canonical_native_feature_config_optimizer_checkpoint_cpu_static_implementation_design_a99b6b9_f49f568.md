# ChatGPT Independent Review — R09-B TTT v0.3.5 Canonical Native Feature / Config / Optimizer / Checkpoint CPU/static Implementation Design v0.1

**Date:** 2026-09-11  
**Formal root:** `a99b6b94777517b5d1ecf0fcd099524544ea3309`  
**Formal child/Gitlink:** `f49f568923555fe15efe546925cbe6cc9140170e`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-CPU-STATIC-IMPLEMENTATION-DESIGN`  
**Requested verdicts:** `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 1. Pair / scope

- Re-locked remote `V2`, re-read live `CODEX_INBOX.md`, and independently verified formal root `a99b6b94777517b5d1ecf0fcd099524544ea3309` resolves `cosmos-framework` exactly to reachable child `f49f568923555fe15efe546925cbe6cc9140170e`.
- Child is unchanged from the approved composite refreeze design; this formal root is docs-only plus review/coordination bookkeeping.
- Binding authority is the approved composite refreeze contract v0.1 + v0.2 + v0.3, formal `5ede9ac264518ccdbca1cdbc24f4e0694b6cf85a` / same child.
- Proposed implementation scope is correctly limited to exactly two child files: `config_checkpoint_contract.py` and `config_checkpoint_contract_test.py`. Real checkpoint/data I/O, DCP, CUDA/GPU, `torchrun`, native model forward/loss/backward, optimizer/scheduler stepping, sidecar, trainer, packer/producer, training/eval/inference and LIBERO4IN1 remain prohibited.

## 2. Positive findings

The design correctly translates the approved composite contract in the important behavioral areas:

- exact versioned FeatureConfig/BaseIdentity instead of generic caller-selected mappings;
- exact registered slow inventory and runtime-fast-state exclusion;
- exact optimizer/scheduler identity rather than mere `state_dict` loadability;
- the v0.3 pristine-before-first-step predicate (`iteration == 0`, empty optimizer state, exact pristine scheduler state);
- preflight-first restore ordering with fresh/quiescent runtime admission before live mutation;
- direct CPU/static negative witnesses for config/base/tensor/optimizer/scheduler/progress/runtime-authority drift with zero live mutation;
- no optimizer/scheduler step or real I/O in evidence construction.

## 3. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_feature_config_optimizer_checkpoint_cpu_static_implementation_design_v0.1.md:24)`

Current blockers: **1 HIGH, Design-only**.  
Production blockers: **0**.  
Evidence blockers: **0**.

### HIGH-1 — FeatureConfigIdentity exact key count contradicts the frozen v0.2 schema

Section 3 states that `FeatureConfigIdentity` must equal “v0.2 §2 的 **15 个 active fields 加 schema**”. That describes 16 keys. The already-approved v0.2 §2 exact schema contains **15 keys total, including `schema`**: `schema` plus 14 active/config fields (`local_memory_enabled`, `local_memory_dim`, `local_history_enabled`, `local_history_backend`, `local_history_evidence_dim`, `local_history_state_enabled`, `local_ttt_enabled`, `enable_input_bias`, `ttt_tbptt_steps`, `ttt_inner_lr`, `k_local`, `local_evidence_feature_version`, `local_fast_state_dtype`, `local_runtime_resume_mode`). The same implementation design later calls this a “15-field FeatureConfigIdentity”, so the document is internally inconsistent on the exact schema cardinality.

For a fail-closed exact-identity Gate this cannot be left as a counting typo: an implementation/test can legitimately interpret the current sentence as requiring an extra key, contradicting the frozen refreeze schema.

**Acceptance:** replace the ambiguous sentence with an exact statement such as “the key set is exactly the 15-key v0.2 §2 mapping, including `schema` (14 non-schema fields + `schema`)”, or enumerate the 15 keys verbatim. Keep the witness wording consistent with that exact total. No other design changes are required by this review.

## 4. Scope

No child implementation is authorized by this verdict. The two-file synthetic CPU/static implementation may begin only after a corrected formal root/child pair receives the required approvals. Real checkpoint/data I/O, DCP, CUDA/GPU, `torchrun`, native real forward/loss/backward, optimizer/scheduler step, sidecar/resume, single-GPU smoke, matched smoke, training, evaluation, inference and LIBERO4IN1 remain prohibited.
