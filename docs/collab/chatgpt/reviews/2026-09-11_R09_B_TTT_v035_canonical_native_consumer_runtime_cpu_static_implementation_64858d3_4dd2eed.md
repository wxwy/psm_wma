# ChatGPT Independent Review — R09-B TTT v0.3.5 Canonical Native Consumer Runtime CPU/static Implementation

**Date:** 2026-09-11  
**Formal root:** `64858d3bc76f3d0a8d755a02bd1dd7ab213499ae`  
**Formal child/Gitlink:** `4dd2eed00a1d9d6e2b28716c106fd9edfe940fcc`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-CONSUMER-RUNTIME-CPU-STATIC-IMPLEMENTATION`  
**Requested verdicts:** `APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_NATIVE_CONSUMER_RUNTIME_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 1. Lock / pair / scope

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; request/bookkeeping HEAD is not the technical target.
- Independently verified root `64858d3bc76f3d0a8d755a02bd1dd7ab213499ae` resolves `cosmos-framework` exactly to reachable child `4dd2eed00a1d9d6e2b28716c106fd9edfe940fcc`.
- Compared child against approved design baseline `08775da2e73e352ebb1497548de5909baab8c2dc`: exactly three child files changed, all inside the approved six-file whitelist:
  - `cosmos_framework/model/generator/omni_mot_model.py`
  - `cosmos_framework/trainer/__init__.py`
  - `cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py`
- No out-of-whitelist production file change was found.
- Reported `41 passed`, Ruff/py_compile/diff-check are supporting evidence only; verdict below is based on source behavior and direct witness coverage.

## 2. Positive findings

The implementation correctly closes several important design obligations:

- `omni_mot_model.py` now rejects context parallelism and an initialized distributed process group before canonical adapter lookup / scan.
- The old unconditional native-forward hard-stop is replaced only by an explicitly injected CPU/static typed-loss seam. Without that seam the exact pending scan is aborted and the route remains fail closed.
- The injected seam must return the exact `CanonicalNativeLossSplit`; `CanonicalProductionAdapter.bind_native_forward()` independently checks exact pending scan identity, `actual_n_valid == gathered.item_count == planned_n_valid`, and consumer identity equality before publishing a one-shot capability.
- `training_step()` preserves pre-scan rejection for a real `torch.optim.Optimizer` and enabled scaler and adds a topology guard before `ddp_sync_grad`, callbacks, model-forward and scan.
- The existing real canonical-native dispatcher continues to own the sole plan objective / one-scale / one-backward / typed commit path and therefore does not re-enter the ordinary unconditional `/grad_accum_iter` branch.
- Existing normal non-uniform valid-count and suffix-recovery dispatcher witnesses exercise the real `CanonicalGAWindowPlan.objective()` seam.
- Legacy ordinary/row-wise Local preparation remains bypassed by the canonical model branch.

These are substantive implementation improvements and are not the reason for the rejection.

## 3. Formal verdict

`REQUEST_CHANGES(cosmos_framework/trainer/__init__.py:553)`

Current blockers: **2 HIGH**.

- Production blockers: **1 HIGH**.
- Evidence blockers: **1 HIGH**.

---

## HIGH-1 — Production: a canonical native capability can be orphaned after model-forward and before canonical backward

**Location:** `cosmos_framework/trainer/__init__.py:553-563` (the region after model-forward return and before `_run_canonical_native_backward()`).

### Frozen contract

Approved composite design v0.1 + v0.2 requires that before successful canonical backward, any failure must abort the exact native-forward/scan authority, and that a successful capability is one-shot. v0.1 §4 states that every pre-success failure must `abort_native_forward/abort_scan`; v0.2 preserves that lifecycle contract unchanged.

### Current source behavior

`OmniMoTModel._canonical_production_segment_forward()` now returns a registered `psm_canonical_native_forward` capability after `adapter.bind_native_forward(...)` succeeds. At that point the adapter owns a live native-forward capability and the underlying pending scan.

However, `ImaginaireTrainer.training_step()` then executes all of the following **before** entering `_run_canonical_native_backward()`:

```text
callbacks.on_after_forward(...)
if capture_only:
    return output_batch, loss, 0
callbacks.on_before_backward(...)
```

There is no canonical-native cleanup wrapper around those exits. Therefore:

1. an `on_after_forward` exception can leave `_native_forward_capabilities` plus the pending scan live;
2. `PSM_R08_GATE_B_CAPTURE_ONLY=1` can return successfully while leaving the same authority live;
3. an `on_before_backward` exception can likewise leave the capability/scan live.

The existing model-side `try/except` cannot help because model-forward has already returned successfully. `_run_canonical_native_backward()` also cannot help because these exits happen before it is entered.

This is a production lifecycle violation, not merely missing test coverage: the current source has an observable path that leaks canonical transaction authority across a trainer exit.

### Exact acceptance

Fix the production trainer so that once an output contains `psm_canonical_native_forward`, every path before `_run_canonical_native_backward()` is disposition-safe. Acceptable implementations include an exact capability guard/finalizer, but the behavior must prove all of the following:

1. `on_after_forward` exception aborts the exact canonical native capability / scan before re-raising;
2. `on_before_backward` exception does the same;
3. canonical `capture_only` either rejects **before model-forward/scan** or explicitly aborts the exact capability before returning — it may not return with live native/scan authority;
4. no ordinary/legacy abort path is substituted for the canonical typed capability;
5. after each pre-backward exit, adapter native-forward/scan registries contain no live authority for that request, frontier has not committed, scheduler state is unchanged, and no Local slow gradient is created/retained;
6. failure disposition remains typed/fail-closed under the inherited transaction taxonomy rather than silently allowing the same request to continue.

Add direct production-endpoint witnesses for `on_after_forward` failure, canonical capture-only behavior, and `on_before_backward` failure. The witness must obtain the real capability through the canonical model seam, not manually fabricate adapter registries.

---

## HIGH-2 — Evidence-only: v0.2 required per-topology pre-entry witnesses, but the implementation does not provide them

**Locations:**
- `cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py:524-620`
- `cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py` (unchanged in this implementation commit)

### Frozen acceptance

Approved v0.2 §3 explicitly required direct CPU/static witnesses for **each** unapproved topology, with rejection before callback/model-forward/core scan and zero scheduler/transaction/frontier/scan mutation:

```text
DDP wrapper
FSDP wrapper
initialized distributed process group
world_size != 1
data-parallel configuration
context parallelism
```

The prior ChatGPT design review repeated this as a closure requirement, not an optional suggestion.

### Current evidence

The implementation commit adds:

- model-side initialized-process-group rejection witness;
- trainer-side non-`none` `distributed_parallelism` configuration rejection witness;
- the pre-existing model-side CP rejection witness remains available;
- pre-existing optimizer/enabled-scaler witnesses remain available.

But the implementation commit adds no direct trainer production-entry witness for:

- `torch.nn.DataParallel` wrapper;
- project `distributed.DistributedDataParallel` wrapper;
- FSDP/FSDP2 wrapper identity;
- trainer-side initialized process group;
- the world-size>1 case as an admitted-topology negative distinct from merely setting config text.

The production helper contains code intended to reject some of these states, but unexecuted branches are not closure evidence. In particular, the FSDP check currently relies on the top-level class name `FullyShardedDataParallel`, while this repository's distributed utility also contains FSDP2 handling via `FSDPModule`; without a direct witness the required wrapper rejection is not established.

### Exact acceptance

Within the already-approved test whitelist, add direct witnesses that drive `ImaginaireTrainer.training_step()` at its production entry for the missing topology classes. Each witness must assert:

1. rejection occurs before `distributed.ddp_sync_grad`, callbacks, model forward, native preparation and core scan;
2. scheduler / transaction / frontier / scan / retry bookkeeping is byte-identical or otherwise exactly unchanged;
3. no Local slow gradient is created or cleared as a side effect of the rejection;
4. the DDP/DataParallel/FSDP cases exercise the actual topology predicate being relied on, not only `distributed_parallelism="ddp"` text;
5. initialized-group/world-size coverage proves the stronger single-process/world-size-1 admission contract.

If the direct FSDP2 witness shows the current class-name predicate is insufficient, fix that production predicate inside the already-approved `trainer/__init__.py` whitelist and include the corresponding direct witness.

No real distributed process launch is needed or authorized; CPU/static wrappers/test doubles are sufficient.

---

## 4. Scope / unchanged restrictions

This review is bound only to formal pair `64858d3bc76f3d0a8d755a02bd1dd7ab213499ae / 4dd2eed00a1d9d6e2b28716c106fd9edfe940fcc` and Gate `G0-R09-B-TTT-V035-CANONICAL-NATIVE-CONSUMER-RUNTIME-CPU-STATIC-IMPLEMENTATION`.

The two blockers above can be repaired entirely inside the already-approved six-file CPU/static scope; no new real-I/O/GPU/distributed execution is required.

Still not authorized: real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, native real workload forward/loss/backward, real optimizer/scheduler stepping, enabled AMP/scaler-skip lifecycle, distributed execution, runtime sidecar/resume, single-GPU smoke, matched smoke, training, evaluation, inference, or LIBERO4IN1.
