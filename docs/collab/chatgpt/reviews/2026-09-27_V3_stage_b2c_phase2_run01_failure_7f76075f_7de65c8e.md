# V3 Stage B2-C RTX4090 S1 — Phase-2 run01 Failure Review

- Date: 2026-09-27
- Gate: `V3-STAGE-B2C-RTX4090-REAL-S1-SMOKE`
- design authority: `ced270eb07bbf9fac321e410f6d1992911d591cb`
- reviewed harness formal pair: root `3c125a51af39bfcadeeeb02f83795784e23a1d66` / child `7de65c8e752c47359786e5ff2535a8d3cd5ddced`
- Phase-1 review bookkeeping root used at execution: `7f76075fa51b76b006facd5c633e5caff55cc5fa`
- B2-B closed baseline: root `81fa515593e7cd8e2d4f7d226efb915b17be3b5b` / child `bf6c80e679812b7d2881d6a54aa0b518299e3869`
- run Evidence: `artifacts/v3/stage_b2c_4090_s1/run01/{result.json,cuda_memory_trace.json,stdout_stderr.log}`
- verdict: **REQUEST_CHANGES**
- retry status: **FORBIDDEN until a new remediation design/implementation pair receives fresh review and a new execution authorization.**

## 1. Exact run result

The single authorized Phase-2 run was executed exactly once and exited code 1.

Result:
- status: FAIL
- exception: `RuntimeError`
- phase: `b0_scan`
- consumer: null
- message: `aten.addmm.default got mixed torch.Tensor and DTensor`
- no native consumer forward ran
- no optimizer step ran
- no fast-state/frontier commit occurred
- no retry or resource/geometry downgrade occurred.

The frozen data/identity preconditions passed:
- root execution bookkeeping `7f76075f...`
- child/Gitlink `7de65c8e...`
- exact Stage-A DCP/config
- exact CloseFridge/20250816/ep0/cursor0
- 429 source frames
- raw15 official V3-loader path
- 16 official RGB/chunk32 consumers.

## 2. Memory evidence

The failure is **not OOM**.

Highest recorded torch allocator values before failure:
- peak allocated: 14,895,660,544 bytes (~14.90 GB decimal / 13.87 GiB)
- peak reserved: 15,206,449,152 bytes (~15.21 GB decimal / 14.16 GiB).

The process reached:
`cuda_init -> processor_config_ready -> model_materialized -> stage_a_dcp_host_loaded -> wan_vae_tokenizer_ready -> local_optimizer_ready -> failure`.

It failed before `b0_scan_completed`, consumer forward/backward, relay backward, optimizer step or fast-state commit. This run therefore does not yet establish full T16 peak memory, but it does establish that model materialization + Stage-A host load + Local optimizer fit comfortably below 24 GB.

## 3. HIGH-1 — B0 scan bypasses FSDP2 unshard lifecycle

**Observed traceback:**
- harness `psm_wma_robocasa_local_s1.py` -> `relay.prepare`
- `local_memory_native_segment.py:125` -> `adapter.scan`
- `local_memory_segment_adapter.py:111` -> direct Local core scan
- `local_evidence.py:61` -> `visual_proj(...)`
- PyTorch -> mixed Tensor / DTensor `aten.addmm` error.

**Root cause:**

The Local parameters are already FSDP2/DTensor **before** the Stage-A DCP load:
1. `OmniMoTModel.build_net()` calls `parallelize_vfm_network(...)` before model materialization/checkpoint load.
2. `ParallelDims.dp_enabled` is intentionally true for training even at world_size=1.
3. `parallelize_vfm_network()` therefore applies root `fully_shard(model,...)`; the new Local runtime and Local bridge are part of the root FSDP parameter group.
4. B0 scan is currently performed outside `net.forward()` by calling `runtime.encoder/core` directly. It therefore does not trigger the root FSDP pre-forward unshard hook.
5. B1 evidence tensors are ordinary tensors. `F.linear(plain Tensor, DTensor weight)` fails exactly as observed.

The DCP path is **not** the origin of the DTensor conversion. Its log `kept_keys=549 dropped_keys=20` shows it correctly skips the new Local parameters after FSDP materialization.

## 4. Rejected remediation shortcuts

Do **not**:
- retry run01 unchanged;
- convert Local DTensor parameters to plain tensors after DCP load;
- disable training FSDP by pretending the model is in inference mode;
- use a 4090-only Local parameter copy;
- detach Local slow parameters from the model-owned optimizer inventory;
- reduce T/K/chunk or switch the policy to cached latent input.

Those would either violate the frozen training architecture or create a 4090-only path that does not transfer to formal 8xH100 training.

## 5. Required acceptance fix

The Local scan must execute through the **same model-owned FSDP2 lifecycle** as the Local parameters.

Freeze a narrow model method on `Cosmos3VFMNetwork`, e.g. a Local scan entrypoint which delegates to the exact registered:
- `net.local_memory_runtime.encoder`
- `net.local_memory_runtime.core`.

When root FSDP is active, register that method with PyTorch `register_fsdp_forward_method(model, <local_scan_method>)`, analogous to the existing registered `generate_reasoner_text` path.

The B0/B2-B adapter/relay should invoke this registered scan entrypoint when it exists, while preserving:
- exact encoder/core object identity;
- B0 scan/transaction semantics;
- ordinary CPU fallback when no FSDP owner exists;
- the same 165,312 Local optimizer inventory;
- no duplicate Local modules or weights;
- no Local copy outside the FSDP-owned model.

Required static/CPU acceptance includes:
1. registered Local scan method uses the exact model-owned runtime encoder/core;
2. adapter/relay selects the registered model scan path for production model ownership;
3. CPU/no-FSDP fixtures retain the existing direct path and all B0-B2B tests pass;
4. registration is applied only when Local is enabled and root FSDP is active;
5. a DTensor/FSDP lifecycle fixture or equivalent controlled test proves plain input can pass through the registered scan without Tensor/DTensor mixing;
6. no change to T=16/K=4/raw15/chunk32/33-frame or transaction ordering.

A fresh formal pair and fresh review are required before any second RTX4090 execution authorization.

## 6. Scope

This REQUEST_CHANGES is limited to the B2-C runtime integration seam.

It does not reopen:
- Stage A
- Stage B0
- Stage B1
- Stage B2-A
- Stage B2-B.

The failed run is valid Evidence and must remain preserved unchanged.
