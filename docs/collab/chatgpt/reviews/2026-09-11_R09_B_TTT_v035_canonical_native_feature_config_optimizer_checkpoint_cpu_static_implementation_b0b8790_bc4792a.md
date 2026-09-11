# ChatGPT Independent Review — R09-B TTT v0.3.5 Canonical Native Feature / Config / Optimizer / Checkpoint CPU/static Implementation

**Date:** 2026-09-11  
**Formal root:** `b0b8790924e474f00d0aedf276559d344d5d0e75`  
**Formal child/Gitlink:** `bc4792aa8112ed583b62d22b9f069d2095c764ce`  
**Submitted Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-CPU-STATIC-IMPLEMENTATION-DESIGN`  
**Requested verdicts:** `APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_NATIVE_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 1. Pair / scope

- Re-locked remote `V2`, re-read live `CODEX_INBOX.md`, and independently verified formal root `b0b8790924e474f00d0aedf276559d344d5d0e75` resolves `cosmos-framework` exactly to reachable child `bc4792aa8112ed583b62d22b9f069d2095c764ce`.
- `9d3c4133…` is only request/ledger bookkeeping and is not treated as the formal target.
- Child delta from approved implementation baseline `f49f568923555fe15efe546925cbe6cc9140170e` is exactly one commit and exactly the approved two files:
  1. `cosmos_framework/model/generator/mot/config_checkpoint_contract.py`
  2. `cosmos_framework/model/generator/mot/config_checkpoint_contract_test.py`
- The reported `13 passed` plus Ruff/py_compile/diff-check are supporting evidence only; source truth remains authoritative.

## 2. Positive findings

- The exact 15-key `FeatureConfigIdentity` cardinality is implemented correctly (`schema` + 14 non-schema fields).
- Generic `base_identity=None` fallback is removed from the restore path.
- Runtime/pending/frontier/frozen-transition admission remains pre-mutation.
- The implementation remains synthetic CPU/static and does not add real I/O, GPU/native workload, optimizer/scheduler stepping, sidecar, trainer, packer, or training execution.

## 3. Formal verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/config_checkpoint_contract.py:107)`

Current blockers: **5 HIGH**.  
Production blockers: **4**.  
Authority/Design blockers: **1**.  
Evidence-only blockers: **0**.

### HIGH-1 — BaseIdentity is still caller-supplied text, not the frozen canonical lineage digest contract

Approved implementation design requires the BaseIdentity builder to derive canonical SHA-256 identities from explicit immutable inputs and rejects generic/caller-selected labels. Current `build_base_identity()` simply accepts `child_git_revision`, `checkpoint_source_fingerprint`, `manifest_sha256`, and `source_sha256` as strings and validates only non-emptiness. It does not validate a reachable/full Git SHA, SHA-256 shape/content, or derive `checkpoint_source_fingerprint` from a canonical source descriptor. The test itself passes `checkpoint_source_fingerprint="synthetic-source"`, demonstrating that an arbitrary label is accepted.

**Acceptance:** make BaseIdentity construction fail closed on the frozen lineage schema: derive the source fingerprint from the versioned canonical source descriptor, validate/derive manifest/source SHA-256 values, and bind a full child revision identity rather than accepting arbitrary non-empty text. Add direct drift/invalid-digest witnesses.

### HIGH-2 — FeatureConfigIdentity is not bound to the actual registered owner/projector ABI

The approved refreeze made `enable_input_bias` a projector ABI identity and included active Local dimensions in `FeatureConfigIdentity`. Current `canonical_slow_inventory()` validates only `32 -> 2048` and modality shape; it never checks whether `local_memory2llm.bias` presence matches `feature_config.enable_input_bias`, nor whether registered evidence/core dimensions match `local_history_evidence_dim`. The test fixture actually constructs encoder/core with `evidence_dim=8` while `FeatureConfigIdentity()` defaults `local_history_evidence_dim=96`, so the passing round-trip witness proves that this identity is currently decoupled from the live owner.

**Acceptance:** before any live mutation, validate the exact FeatureConfigIdentity against the registered owner/projector ABI, including projector bias presence and the Local evidence/core dimensions that the identity claims. Add mismatched-live-owner/bias witnesses.

### HIGH-3 — Optimizer/scheduler identity is weaker than the approved exact identity

Approved design requires optimizer fully-qualified class, ordered **group names**, ordered member names, typed hyperparameters, and per-member allowed state schema; scheduler identity requires fully-qualified class, immutable constructor/config mapping, and complete state schema. Current `_optimizer_identity()` returns only class + member lists + hyperparameters, with no explicit ordered group-name identity or per-member state schema. `_scheduler_identity()` returns only class + a type-shaped `state_schema`; it does not bind constructor/config values.

This lets materially different scheduler policy/configurations share the same identity shape, and the tests only mutate scheduler class / optimizer LR rather than constructor/config and state-schema identities.

**Acceptance:** encode and compare the complete frozen optimizer/scheduler identity exactly as approved, including canonical group-name identity, per-member optimizer state schema, and scheduler constructor/config values. Add direct drift witnesses for each omitted field.

### HIGH-4 — pristine scheduler validation trusts the current live scheduler instead of reconstructing the approved pristine shadow

The v0.3 contract requires `saved scheduler state == pristine_state(approved scheduler identity)`, where pristine state is produced by a detached newly constructed optimizer/scheduler before any user-visible step. Current `_stage_restore()` calls:

`pristine_scheduler_state=None if scheduler is None else scheduler.state_dict()`

so the current live scheduler is treated as the pristine authority. If that live scheduler has already advanced and the payload matches its advanced state, the check can pass. `slow_checkpoint_payload()` also does not itself reject non-pristine scheduler progress.

**Acceptance:** reconstruct the detached pristine optimizer/scheduler from the already validated exact identity/config, compare the payload against that reconstructed pristine state, and reject any progressed save payload before live mutation. Add a witness where the live scheduler has advanced but the payload matches it; it must still fail.

### HIGH-5 — closure request is filed under the already-approved DESIGN Gate

The live request labels this implementation closure as `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-CPU-STATIC-IMPLEMENTATION-DESIGN`, while requesting `APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_NATIVE_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_CPU_STATIC`. That collides with the design Gate already approved at formal `9468e10…/f49f568…` and makes closure authority ambiguous.

**Acceptance:** submit the corrected implementation closure under a distinct implementation Gate, consistent with the established progression (i.e. the implementation Gate without the `-DESIGN` suffix), with its exact new root/child pair.

## 4. Scope

No real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, native real forward/loss/backward, optimizer/scheduler step, sidecar/resume, single-GPU smoke, matched smoke, training, evaluation, inference, or LIBERO4IN1 is authorized. The implementation remains confined to the approved two-file synthetic CPU/static scope until these blockers are remediated and a new formal pair is reviewed.
