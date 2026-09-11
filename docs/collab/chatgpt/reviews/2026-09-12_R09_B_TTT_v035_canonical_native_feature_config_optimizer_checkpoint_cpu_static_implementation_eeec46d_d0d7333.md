# ChatGPT Independent Review — R09-B TTT v0.3.5 Canonical Native Feature / Config / Optimizer / Checkpoint CPU/static Implementation

**Date:** 2026-09-12  
**Formal root:** `eeec46d5c5667d7c3a30d9637025cc0819aeb468`  
**Formal child/Gitlink:** `d0d73338ca1b0e8ae350d447181a804308241390`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-CPU-STATIC-IMPLEMENTATION`  
**Requested verdicts:** `APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_NATIVE_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 1. Pair / incremental scope

- Re-locked remote `V2`, re-read live `CODEX_INBOX.md`, and independently verified formal root `eeec46d5c5667d7c3a30d9637025cc0819aeb468` resolves `cosmos-framework` exactly to reachable child `d0d73338ca1b0e8ae350d447181a804308241390`.
- `ee0562a3…` is request/ledger bookkeeping only and is not treated as the formal target.
- Child delta from prior remediation child `11f9adf7fa209805ef6437145cf7a0dbf1625697` is exactly one commit and exactly the approved two files:
  1. `cosmos_framework/model/generator/mot/config_checkpoint_contract.py`
  2. `cosmos_framework/model/generator/mot/config_checkpoint_contract_test.py`.
- This review is incremental against the prior ChatGPT review for `1f5eb1c…/11f9adf…`, which left three Production HIGH findings: owner-derived lineage, versioned/digested optimizer-scheduler identity, and live feature-version ABI binding.

## 2. Remediation status

### Prior HIGH — optimizer/scheduler identity: CLOSED

The remediation now wraps both optimizer and scheduler identities in exact versioned mappings with explicit schema names and canonical JSON SHA-256. Restore validates exact key sets, schema literals, and digest equality before reconstructing pristine detached AdamW / ExponentialLR shadows. Ordered named groups/members, typed hyperparameters, per-member state schema, scheduler optimizer binding, constructor `gamma`, and state schema are preserved.

### Prior HIGH — feature-version live ABI: CLOSED

`_validate_feature_config_against_runtime()` now binds the feature identity to the live registered encoder/core/projector ABI before mutation, including evidence dimension, visual input width `96`, action input width `10`, canonical state/dt/age-disabled evidence config, Local dimension / K-local / TBPTT / inner-LR, projector `32 -> 2048`, bias presence, and modality shape. Direct visual/action/legacy-feature drift witnesses are present.

### Prior HIGH — owner-derived lineage: PARTIALLY CLOSED; one Production HIGH remains

The source descriptor itself is materially improved: it is exact/versioned and now includes `source_kind`, `source_id_sha256`, `source_manifest_sha256`, and `source_sha256`; BaseIdentity derives the checkpoint source fingerprint from its canonical JSON. `LineageOwnerIdentity` also validates SHA-shaped child and manifest fields.

However the authority problem remains. `LineageOwnerIdentity` is a public dataclass whose `child_git_revision` and manifest/source fields are supplied directly by the caller. `build_base_identity()` accepts that object without independently binding it to the current checked-out/reviewed child or an independently owned manifest/source authority. More importantly, both `strict_restore()` and `strict_restore_into()` still accept a caller-provided `base_identity: Mapping` as the expected authority and merely compare the payload against that same caller-selected expected mapping.

The direct test demonstrates the gap: `_lineage_owner()` defaults to `child_git_revision="f" * 40`, not the formal child `d0d73338ca1b0e8ae350d447181a804308241390`, and the ordinary valid payload/restore path uses that synthetic fake revision. A syntactically valid foreign revision is rejected only when it differs from the separately supplied expected mapping; a caller that supplies the same foreign mapping to both payload creation and restore still self-authorizes it.

That violates the frozen refreeze contract: `child_git_revision` must come from the actual checked-out child authority, BaseIdentity must be derived by checkpoint/manifest owner from frozen inputs, and restore must not accept a caller-chosen mapping as canonical identity.

**Acceptance:** remove caller self-authorization. The expected BaseIdentity used by save/restore must be derived inside the trusted lineage owner path from the exact reviewed/current child revision and frozen manifest/source descriptor authority; `strict_restore[_into]` must not accept an arbitrary expected `base_identity` mapping that can be chosen to match a forged payload. Add a direct witness where payload and caller-supplied foreign lineage agree syntactically yet restore still rejects because the trusted owner/current child is `d0d73338ca1b0e8ae350d447181a804308241390` (or the exact independently owned CPU/static lineage authority for this Gate).

## 3. Formal verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/config_checkpoint_contract.py:132)`

Current blockers: **1 HIGH, Production**.  
Authority/Design blockers: **0**.  
Evidence-only blockers: **0**.

## 4. Scope

Positive findings retained: exact two-file whitelist; exact 15-key FeatureConfigIdentity; versioned/digested optimizer/scheduler identity; detached-pristine progress validation; live visual/action/state-dt-age ABI binding; pre-mutation runtime admission. Reported `14 passed` plus Ruff/py_compile/diff-check are supporting evidence only.

No real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, native real forward/loss/backward, optimizer/scheduler step, sidecar/resume, single-GPU smoke, matched smoke, training, evaluation, inference, or LIBERO4IN1 is authorized.
