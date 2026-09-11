# ChatGPT Independent Review — R09-B TTT v0.3.5 Canonical Native Production Runtime CPU/static Implementation Design v0.1

**Date:** 2026-09-11  
**Formal root:** `750410ce0928f2b03b0dadfa3015a22f9f71c7d2`  
**Formal child/Gitlink:** `f49f568923555fe15efe546925cbe6cc9140170e`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-PRODUCTION-RUNTIME-CPU-STATIC-IMPLEMENTATION-DESIGN`  
**Requested verdicts:** `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_PRODUCTION_RUNTIME_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 1. Pair / scope

- Re-locked remote `V2` and re-read live `CODEX_INBOX.md`.
- Independently verified formal root `750410ce0928f2b03b0dadfa3015a22f9f71c7d2` resolves `cosmos-framework` exactly to reachable child `f49f568923555fe15efe546925cbe6cc9140170e`.
- Child is unchanged from the approved production-runtime-integration design pair. The formal-root technical delta is docs-only: the new CPU/static implementation design plus SESSION/TODO and prior review/coordination bookkeeping.
- The six-file whitelist stays inside the already established model/adapter/trainer + directed-test surfaces; config/checkpoint/sidecar/data/packer/flow-matching/registry and real execution remain excluded.

## 2. Positive findings

The design otherwise preserves the approved contract:

- synthetic single-process/world-size-1 CPU/static only;
- real native model execution remains hard-stopped;
- exact carrier/preparation identity, typed weighted consumer loss, independent auxiliary loss, normal/recovery objective algebra and one-backward capability are retained;
- `CanonicalGAWindowPlan.objective()` remains the sole GA/window scaling owner;
- enabled scaler, real optimizer and distributed topologies remain pre-entry rejects;
- suffix recovery remains exact one-shot lineage with no second admission/resample;
- after implementation closure, the next stage remains feature/config/optimizer/checkpoint refreeze, not GPU/sidecar/training.

The current child source supports the intended synthetic implementation boundary: `omni_mot_model.py` still exposes only the injected CPU/static typed-loss seam after canonical preparation, the adapter already owns `build_prepared_canonical_native_loss_split()` / typed capabilities, and trainer `_run_canonical_native_backward()` already owns the one-objective/one-backward/commit lifecycle.

## 3. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_production_runtime_cpu_static_implementation_design_v0.1.md:40)`

Current blockers: **1 HIGH, Design-only**.  
Production blockers: **0**.  
Evidence blockers: **0**.

### HIGH — post-mutation failure taxonomy is internally contradictory

At line 40, §2 states that `post-mutation failure` belongs to the class that must `fail closed` **before the irreversible commit boundary**. That is impossible by definition and conflicts with the frozen failure semantics restated correctly later in §3.4: pre-mutation failures abort/terminalize with zero reconcile, while failures after the mutation boundary preserve commit/frontier/scan evidence and reject automatic disposal/retry.

This distinction is safety-critical because an implementation following §2 literally could attempt to abort/reconstruct authority after an irreversible frontier mutation, which the existing canonical contract explicitly forbids.

### Exact acceptance

Revise §2 so the failure classes are unambiguous:

1. missing typed terms, foreign/stale capability, count mismatch, duplicate consumption, ordinary second GA scaling, unsupported scaler/optimizer/topology, forward/pre-backward/loss-build/prepare-commit and **pre-mutation commit failure** must fail closed before the irreversible boundary, disposing exact capability/scan and terminalizing with zero frontier/scheduler reconcile;
2. **post-mutation failure** must be listed separately: preserve exact commit capability, scan provenance, frontier state and controlled evidence; do not call ordinary abort/reconstruction; reject automatic retry and surface the typed post-mutation failure;
3. keep §3.4 / witness E aligned with the same split.

No other design blocker was found.

## 4. Scope

No child modification or real execution is authorized by this verdict. Real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, native real forward/loss/backward, real optimizer/scheduler stepping, sidecar write, training, evaluation, inference and LIBERO4IN1 remain prohibited.
