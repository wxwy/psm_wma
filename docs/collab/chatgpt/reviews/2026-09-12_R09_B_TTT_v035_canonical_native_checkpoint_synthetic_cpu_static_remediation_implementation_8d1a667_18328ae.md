# ChatGPT Independent Review — R09-B TTT v0.3.5 Canonical Native Checkpoint Synthetic CPU/static Remediation Implementation

**Date:** 2026-09-12  
**Formal root:** `8d1a667fa504f316a6f11561c639b1147ecfd16e`  
**Formal child/Gitlink:** `18328aeed1e6c541fadd9d9063903dee585d79a5`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-CHECKPOINT-SYNTHETIC-CPU-STATIC-REMEDIATION-IMPLEMENTATION`

## 1. Pair / scope

- Re-locked remote `V2` and re-read live `CODEX_INBOX.md`.
- Independently verified formal root `8d1a667fa504f316a6f11561c639b1147ecfd16e` resolves `cosmos-framework` exactly to reachable child `18328aeed1e6c541fadd9d9063903dee585d79a5`.
- The request ledger commit is bookkeeping only and is not treated as the formal target.
- Child delta from approved implementation-design baseline `da95139d338ef2ab2cff89d7bdb2a237f711877c` is one commit and exactly the approved two files:
  1. `cosmos_framework/model/generator/mot/config_checkpoint_contract.py`
  2. `cosmos_framework/model/generator/mot/config_checkpoint_contract_test.py`
- Reported `14 passed` plus Ruff/py_compile/diff-check are supporting evidence only; source and direct witness coverage remain authoritative.

## 2. Positive findings

- `base_identity` is now exact five-key `synthetic_cpu_static_v1` and no longer contains child/root Git provenance.
- Legacy stale/current `child_git_revision` mappings are rejected; production-shaped `root_gitlink_authority_v1` mappings are rejected.
- Public save/restore APIs still do not accept caller-supplied expected BaseIdentity.
- Existing FeatureConfigIdentity/live ABI, optimizer/scheduler versioned identities, pristine-before-first-step, detached shadow validation, and quiescent-runtime admission remain intact.
- No root-Gitlink authority, real I/O, GPU/native workload, optimizer/scheduler step, sidecar, training/eval/inference, or LIBERO4IN1 path is introduced.

## 3. Formal verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/config_checkpoint_contract.py:120)`

Current blockers: **2 HIGH**.  
Production blockers: **1**.  
Evidence-only blockers: **1**.  
Design/Authority blockers: **0**.

### HIGH-1 — Production — synthetic fixture digests are placeholder literals, not derived from versioned canonical fixture definitions

The approved remediation design freezes `fixture_descriptor_sha256`, `fixture_manifest_sha256`, and `fixture_source_sha256` as digests that must be derived from module-internal **versioned synthetic fixture descriptor / manifest / source definitions**. Current `_synthetic_fixture_authority()` instead directly returns `"d" * 64`, `"a" * 64`, and `"b" * 64`, and only validates that they look like lowercase 64-hex strings. There is no canonical descriptor/manifest/source mapping whose bytes are hashed, so the fields are format-valid labels rather than content-bound digests.

That weakens the newly refrozen synthetic provenance contract: arbitrary 64-hex constants can satisfy the authority without proving any deterministic fixture definition.

**Acceptance:** define explicit module-internal versioned canonical synthetic fixture descriptor, fixture manifest, and fixture source definitions; derive each digest via canonical JSON/SHA-256 from those definitions (or an equivalently frozen deterministic in-memory encoding) and construct `synthetic_cpu_static_v1` only from those derived digests. Add direct witnesses that independently recompute the expected digests and fail when the underlying definition/digest binding drifts. No real file/Git/environment I/O is required or authorized.

### HIGH-2 — Evidence-only — zero-live-mutation witness does not cover the full frozen object/state set for identity/domain rejects

The approved design requires direct witnesses that **all** synthetic identity/domain rejection cases preserve registered slow tensor bytes, optimizer/scheduler groups and state, iteration, Parameter/module/adapter identity, and runtime authority byte/object-for-object. Current base-identity/domain-drift block calls `_restore()` without optimizer/scheduler and only finishes by checking slow tensor equality. It does not directly snapshot/assert optimizer state, scheduler state, object identities, adapter/frontier/pending authority, or iteration for these identity/domain rejects.

The source ordering is encouraging—the BaseIdentity comparison occurs in staging before live copy/optimizer/scheduler load—but the requested direct evidence is still missing.

**Acceptance:** add a direct parameterized CPU/static witness for the synthetic digest/schema/key drift, legacy child-Git mapping, and `root_gitlink_authority_v1` rejection cases using a live optimizer+scheduler fixture and snapshots of: slow tensor bytes, optimizer/scheduler state, iteration, Parameter/module/adapter object identities, and adapter/frontier/pending authority. Assert exact unchanged state after every reject. This remains in-memory only.

## 4. Scope

This review does **not** authorize real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, native real forward/loss/backward, optimizer/scheduler stepping, runtime sidecar/resume, single-GPU smoke, matched smoke, training, evaluation, inference, LIBERO4IN1, or any `root_gitlink_authority_v1` implementation/simulation.

Remediation should remain within the already-approved two child files only.