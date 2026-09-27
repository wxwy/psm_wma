# PSM-WMA V3 Stage B2-C R1 — FSDP Local Scan Remediation Design v0.1

- Date: 2026-09-27
- Remediation gate: `V3-STAGE-B2C-R1-FSDP-LOCAL-SCAN`
- Parent gate: `V3-STAGE-B2C-RTX4090-REAL-S1-SMOKE`
- Parent design authority: root `ced270eb07bbf9fac321e410f6d1992911d591cb`.
- Failed run review bookkeeping: root `edc2846d7d6a99ef999f41d620adaf5ed7ea1326`.
- Failed harness formal pair remains root `3c125a51af39bfcadeeeb02f83795784e23a1d66` / child `7de65c8e752c47359786e5ff2535a8d3cd5ddced`.
- run01 Evidence remains immutable under `artifacts/v3/stage_b2c_4090_s1/run01/`.
- Status: DESIGN_FROZEN_FOR_R1A_IMPLEMENTATION.
- No second full RTX4090 S1 run is authorized by this design.

## 1. Failure being remediated

run01 reached:
`model_materialized -> Stage-A DCP host loaded -> Wan tokenizer ready -> Local optimizer ready`,
then failed at B0 scan before any native consumer:

```text
F.linear(plain B1 evidence Tensor, FSDP2 DTensor local_memory_runtime.encoder.visual_proj.weight)
-> RuntimeError: mixed torch.Tensor and DTensor
```

This is not OOM. Recorded peak before failure was about 14.90 GB allocated / 15.21 GB reserved.

The Local parameters become DTensors during model build, before DCP:
- training-mode `ParallelDims.dp_enabled=True` even for world_size=1;
- `parallelize_vfm_network()` applies root `fully_shard(model,...)`;
- Local runtime/bridge are model-owned top-level parameters and therefore part of the root FSDP group.

The failure occurs because B0/B2-B calls `runtime.encoder/core` directly outside a root FSDP forward method, so FSDP never unshards those Local weights for the scan.

## 2. Architectural fix

Do not convert Local parameters to plain tensors and do not disable FSDP.

Add one model-owned Local scan entrypoint on `Cosmos3VFMNetwork`, conceptually:

```text
scan_local_memory(
    visual_summary,
    executed_action,
    valid,
    state_in
) -> (local_tokens, candidate_fast_state, present)
```

Its body delegates to the exact existing objects:

```text
self.local_memory_runtime.core.scan_segment_masked_encoded_many(
    self.local_memory_runtime.encoder,
    visual_summary,
    executed_action,
    valid,
    state_in,
)
```

No duplicate encoder/core, no extra parameters, no alternative loss.

When root FSDP is active and Local Memory is enabled, register that method with PyTorch:

```text
register_fsdp_forward_method(model, "scan_local_memory")
```

after root `fully_shard(model,...)`, analogous to the already-established `generate_reasoner_text` registration.

The registration is the authority that performs root FSDP unshard/reshard around the B0 scan.

## 3. Adapter/relay seam

Extend `CanonicalLocalMemorySegmentAdapter` with one optional scan callable/capability.

Rules:
- encoder/core object identity remains exactly model-owned;
- when a model-owned scan callable is provided, `adapter.scan()` invokes it instead of directly invoking `core.scan_segment_masked_encoded_many`;
- the callable receives exactly the same B0 visual/action/valid/state tensors;
- returned token/candidate/present contract is validated by the existing B0 core/state checks;
- sidecar/transaction prepare/commit/discard semantics are unchanged;
- no model forward may commit fast state.

`SingleSegmentNativeGradientRelay` must pass `model.net.scan_local_memory` to the adapter when that entrypoint exists.

CPU toy models without that method retain the current direct B0 path, preserving B0/B2-B unit-test simplicity.

## 4. FSDP ownership / future H100 compatibility

The fix must preserve Local parameters as normal model-owned FSDP parameters.

Forbidden:
- `ignored_params` for Local in the formal model;
- post-load `.to_local()` replacement of model parameters;
- copying Local weights into an unsharded side module;
- setting `enable_inference_mode=True` to suppress training FSDP;
- disabling the single-rank FSDP policy;
- a 4090-only Local implementation branch.

Reason: the remediation must be structurally compatible with later 8xH100 training, where Local slow gradients need the same FSDP ownership/reduction semantics as other trainable model parameters.

This R1 does not yet authorize H100 grouped training; it only avoids creating a single-rank-only shortcut.

## 5. Gradient semantics

The registered Local scan output must retain autograd connectivity to the model-owned FSDP Local parameters.

B2-B serial relay stays unchanged semantically:
- scan once;
- native leaf detach per consumer;
- native backward per Local-bearing consumer;
- relay captured prefix gradients to original scan tokens;
- FSDP Local backward/reduction follows from that original scan graph;
- optimizer step;
- fast-state commit.

No `no_grad`, inference mode, or detach is allowed around the registered scan.

## 6. R1-A CPU/static implementation scope

Preferred minimal child changes:
- `cosmos_framework/model/generator/mot/cosmos3_vfm_network.py`
- `cosmos_framework/model/generator/mot/parallelize_vfm_network.py`
- `cosmos_framework/model/generator/mot/local_memory_segment_adapter.py`
- `cosmos_framework/model/generator/mot/local_memory_native_segment.py`
- focused tests only.

No changes to:
- B1 producer/cache semantics;
- Local dimensions/T/K/inner_lr;
- Stage-A DCP/config;
- optimizer inventory/LR;
- trainer;
- checkpoint save;
- inference/server/eval;
- formal policy chunk32/33-frame;
- harness sample/asset identity.

Any additional production file requires explicit implementation-record justification.

## 7. R1-A CPU/static acceptance

Tests must prove:

1. **Exact model identity**
   - `scan_local_memory` uses the exact `net.local_memory_runtime.encoder/core`;
   - no second Local parameter set exists;
   - total Local inventory remains exactly 165,312 for Edge hidden 2048.

2. **Registration**
   - when root FSDP wrapping is applied and Local is enabled, `register_fsdp_forward_method(model, "scan_local_memory")` is invoked exactly once;
   - no registration when Local is disabled or FSDP is not active;
   - existing `generate_reasoner_text` registration is unchanged.

3. **Adapter routing**
   - production relay with a model scan entrypoint routes scan through that exact bound method;
   - direct `core.scan...` is not called on that route;
   - CPU/no-owner fixture retains existing direct route.

4. **Contract parity**
   - registered-route outputs match direct B0 scan outputs on ordinary CPU tensors;
   - S0/padding/present masks/state_out are identical;
   - transaction/sidecar/commit/failure behavior remains identical.

5. **Gradient parity**
   - registered-route synthetic gradients to representative Local slow params match direct-route gradients within tolerance;
   - B2-B monolithic-vs-serial relay equivalence remains PASS.

6. **Fail closed**
   - if a model reports FSDP/DTensor-owned Local parameters but the registered scan capability is absent, B2-B production relay rejects before B0 scan instead of reaching mixed Tensor/DTensor `F.linear`.

7. All B0/B1/B2-A/B2-B/B2-C harness CPU suites remain PASS.

R1-A performs no real GPU run.

## 8. R1-B tiny RTX4090 FSDP lifecycle micro-smoke

R1-A fresh approval authorizes at most one **tiny** GPU micro-smoke, not the full Stage-A model.

Purpose: reproduce and close the exact Tensor/DTensor lifecycle issue before spending another full S1 run.

The micro-smoke must:
- initialize single-rank NCCL/FSDP2 using the same training `ParallelDims` / mixed-precision policy semantics;
- construct a tiny owner containing the real `LocalMemoryRuntime` and Local bridge, with Edge local dimensions but no Edge language/vision backbone;
- root-`fully_shard` the owner;
- prove Local parameters are DTensor outside the registered method;
- call the registered `scan_local_memory` with ordinary Tensor B0 evidence;
- produce finite `[B,T,K,D]` Local tokens / candidate state without mixed Tensor/DTensor error;
- relay/backward a deterministic scalar and prove finite non-zero representative Local parameter gradients;
- perform no optimizer step unless needed by the fixture;
- record peak GPU memory;
- run once, with no retry.

A failure is Evidence and blocks full S1.

## 9. New full S1 authorization

Even if R1-B passes, **run02 is not automatically authorized**.

A fresh ChatGPT review of:
- R1-A formal pair and tests;
- R1-B micro-smoke Evidence;

must explicitly authorize one new full B2-C S1 execution with a new unique output directory.

run01 remains the immutable failed run and must never be overwritten/reused.

## 10. Gate boundary

R1 fixes only the FSDP lifecycle of the Local scan.

It does not reopen or change the conclusions of Stage A, B0, B1, B2-A or B2-B, and it does not yet establish that full T16 consumer forward/backward fits in 24 GB.
