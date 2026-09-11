# ChatGPT Independent Review — R09-B TTT v0.3.5 Canonical Native Consumer Runtime CPU/static Implementation remediation

**Date:** 2026-09-11  
**Formal root:** `748a6ad4380a2934672c8d261d15f7bddfa0ef62`  
**Formal child/Gitlink:** `9368b0b5df9ddc76eed237c80ffeff40fe46a3ef`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-CONSUMER-RUNTIME-CPU-STATIC-IMPLEMENTATION`  
**Previous reviewed pair:** `64858d3bc76f3d0a8d755a02bd1dd7ab213499ae / 4dd2eed00a1d9d6e2b28716c106fd9edfe940fcc`  
**Previous verdict:** `REQUEST_CHANGES(cosmos_framework/trainer/__init__.py:553)`  
**Requested verdicts:** `APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_NATIVE_CONSUMER_RUNTIME_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 1. Lock / pair / incremental scope

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; request/bookkeeping HEAD is not the technical target.
- Independently verified formal root `748a6ad4380a2934672c8d261d15f7bddfa0ef62` resolves `cosmos-framework` exactly to reachable child `9368b0b5df9ddc76eed237c80ffeff40fe46a3ef`.
- Compared child against the rejected child `4dd2eed00a1d9d6e2b28716c106fd9edfe940fcc`: exactly two files changed, both inside the approved whitelist:
  - `cosmos_framework/trainer/__init__.py`
  - `cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py`
- Root delta is bookkeeping/review persistence plus the Gitlink update; no unrelated production scope expansion was found.
- Reported `48 passed`, Ruff/py_compile/diff-check are supporting evidence only. This verdict is based on source behavior and direct-witness coverage.

## 2. Prior HIGH-1 — CLOSED: pre-backward canonical capability disposition

The previous production HIGH required every trainer exit after a registered `psm_canonical_native_forward` capability is returned but before `_run_canonical_native_backward()` to dispose the exact typed authority.

The remediation adds `_abort_canonical_native_pre_backward_exit()` which:

1. accepts only an exact `CanonicalNativeForwardCapability` from `output_batch`;
2. validates that capability through its adapter;
3. clears only its registered Local slow-parameter gradients;
4. calls `adapter.abort_native_forward(capability)` to consume the exact native-forward capability and pending scan;
5. terminalizes the exact transaction member with a typed terminal code.

`ImaginaireTrainer.training_step()` now invokes that helper on all three previously leaking seams:

- `callbacks.on_after_forward` exception → `CANONICAL_NATIVE_AFTER_FORWARD_FAILURE`;
- canonical `capture_only` early return → `CANONICAL_NATIVE_CAPTURE_ONLY`;
- `callbacks.on_before_backward` exception → `CANONICAL_NATIVE_BEFORE_BACKWARD_FAILURE`.

The new direct witness obtains a real capability through `OmniMoTModel._canonical_production_segment_forward()` rather than fabricating adapter registries, drives each of the three production exits through `ImaginaireTrainer.training_step()`, and checks:

- native-forward registry empty;
- pending scan registries empty;
- frontier state unchanged;
- scheduler snapshot unchanged;
- typed terminal failure recorded;
- Local slow grads cleared.

This closes the previous Production HIGH.

## 3. Formal verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py:624)`

Current blockers: **1 HIGH, Evidence-only**.  
Production blockers: **0**.  
Evidence blockers: **1 HIGH**.

---

## HIGH — Evidence-only: the exact per-topology witness obligation is still incomplete

### Frozen acceptance

The previous canonical review did not merely ask for a generic distributed rejection test. Its exact acceptance explicitly required direct production-entry coverage for the missing topology classes, including:

- `torch.nn.DataParallel`;
- project `distributed.DistributedDataParallel`;
- FSDP / FSDP2 wrapper identity;
- trainer-side initialized process group;
- stronger `world_size > 1` admission negative;

and required each witness to establish rejection before `distributed.ddp_sync_grad`, callbacks, model-forward/core scan with zero scheduler/transaction/frontier/scan/retry mutation and no Local slow-grad side effects.

### What the remediation now proves

The new tests materially improve coverage:

- `torch.nn.DataParallel` is directly exercised;
- an object whose top-level class name is `FullyShardedDataParallel` exercises the current class-name branch;
- trainer-side initialized process group is exercised;
- `world_size == 2` is exercised separately;
- the earlier non-`none` `distributed_parallelism` config witness remains;
- the earlier CP, optimizer and enabled-scaler witnesses remain.

### Remaining gap

Two exact topology obligations from the previous review are still not directly witnessed:

1. **project `distributed.DistributedDataParallel`**: current production predicate is `isinstance(model_ddp, (torch.nn.DataParallel, distributed.DistributedDataParallel))`, but the new wrapper test exercises only the first tuple member. It does not exercise the project DDP type relied on by the predicate.
2. **FSDP2 identity**: the new FSDP test uses `type("FullyShardedDataParallel", (), {})()`, which only proves the literal top-level class-name branch. It does not exercise the repository's FSDP2-style identity (`FSDPModule`) that the previous review explicitly called out. Therefore it cannot establish whether the current class-name predicate is sufficient for the real FSDP2 topology.

The wrapper tests also assert only the expected rejection error; they do not directly assert the full zero-side-effect contract required by the previous acceptance (no callback / ddp-sync / model-forward / core-scan entry and unchanged scheduler/transaction/frontier/scan/retry state with no Local slow-grad side effect).

This is still an Evidence-only blocker because the newly reviewed production lifecycle fix is sound, and this review does not independently prove a concrete admitted distributed execution path. But closure cannot be granted until the exact witness obligations are met.

### Exact acceptance

Within the already-approved CPU/static test scope:

1. add a direct `ImaginaireTrainer.training_step()` witness for the project `distributed.DistributedDataParallel` predicate. No real process group is needed; a CPU/static test double or monkeypatched project DDP class is acceptable so long as the actual `isinstance(..., distributed.DistributedDataParallel)` branch is exercised;
2. add a direct FSDP2 identity witness using the repository/PyTorch `FSDPModule`-style topology or an equivalent test double that exercises the actual predicate intended to reject FSDP2. If that witness demonstrates the current top-level class-name check is insufficient, fix `_canonical_native_cpu_static_topology_error()` inside the already-approved `trainer/__init__.py` scope;
3. for both witnesses, explicitly prove rejection occurs before `distributed.ddp_sync_grad`, callbacks, model-forward/native prepare/core scan;
4. explicitly prove scheduler / transaction / frontier / scan / retry bookkeeping is unchanged and no Local slow-grad side effect occurs.

No GPU or real distributed launch is needed or authorized.

## 4. Positive findings retained

Subject to the remaining Evidence HIGH, the implementation remediation is otherwise consistent with the approved composite v0.1 + v0.2 contract:

- exact formal pair/Gitlink is valid;
- no whitelist expansion occurred;
- pre-scan real optimizer / enabled scaler rejection remains;
- initialized group and world-size rejection are before `ddp_sync_grad`;
- canonical pre-backward capability leaks are fixed with exact typed disposition;
- one-objective / one-scale / one-backward / typed commit semantics remain unchanged;
- no ordinary second `/grad_accum_iter` scaling is introduced;
- real I/O/GPU/distributed execution/training surfaces remain unauthorized.

## 5. Scope

This verdict is bound only to formal pair `748a6ad4380a2934672c8d261d15f7bddfa0ef62 / 9368b0b5df9ddc76eed237c80ffeff40fe46a3ef` and the exact CPU/static implementation Gate above.

Still not authorized: real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, native real workload forward/loss/backward, real optimizer/scheduler stepping, enabled AMP/scaler-skip lifecycle, distributed execution, runtime sidecar/resume, single-GPU smoke, matched smoke, training, evaluation, inference, or LIBERO4IN1.
