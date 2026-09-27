# PSM-WMA V3 Stage B2-C R1-B Tiny FSDP Micro-Smoke Design v0.1

- Date: 2026-09-27
- Gate: `V3-STAGE-B2C-R1B-TINY-FSDP-MICRO-SMOKE`
- Parent remediation Gate: `V3-STAGE-B2C-R1-FSDP-LOCAL-SCAN`.
- R1-A formal pair: root `cae1c4bf5d681f93228a9b1a5c74e14d1b5acee4` / child `558f364efaf6704c9d65037c17ec250a9331be8a`.
- R1-A closure bookkeeping: root `64db2a285ceff28d7f72111e6466bc5489f10a81`; it does not replace the formal pair.
- Parent B2-C design: root `ced270eb07bbf9fac321e410f6d1992911d591cb`.
- One real RTX4090 execution only after harness fresh review.
- This Gate does not authorize full B2-C run02.

## 1. Goal

Reproduce and close exactly the run01 failure mechanism without loading the 4B Edge host:

```text
plain Tensor B0 evidence
→ model-owned LocalMemoryRuntime under training-mode root FSDP2
→ registered scan_local_memory forward lifecycle
→ finite Local tokens/candidate
→ scalar backward through scan graph
→ finite non-zero Local parameter gradients
```

This is an FSDP lifecycle test only. It does not test policy loss, Stage-A DCP, VAE, RoboCasa data or memory fit of the full model.

## 2. Tiny owner

Implement a small CUDA module with:
- `local_memory_runtime = LocalMemoryRuntime()` using frozen dimensions:
  evidence_dim=256, action_dim=15, local_dim=32, ttt_dim=64,
  fast_hidden_dim=256, inner_lr=0.1, T=16, K=4;
- `local_memory2llm = Linear(32,2048)`;
- `local_memory_modality_embed [2048]`;
- `config.local_memory_enabled=True`;
- a `scan_local_memory(...)` method with the exact R1-A semantics:
  delegate to the same runtime encoder/core objects.

No Edge language/vision backbone is instantiated.

## 3. Exact distributed/FSDP lifecycle

The GPU harness must:
1. reject WORLD_SIZE != 1 before CUDA work;
2. set rank 0 CUDA device;
3. initialize one-rank NCCL process group;
4. construct `ParallelDims(world_size=1, dp_shard=1, dp_replicate=1, cp=1, cfgp=1, enable_inference_mode=False)`;
5. call `build_meshes("cuda")`;
6. place tiny owner parameters in FP32 master dtype on CUDA;
7. root-wrap with:
   `fully_shard(owner, mesh=fsdp_mesh(parallel_dims), mp_policy=MixedPrecisionPolicy(param_dtype=torch.bfloat16, reduce_dtype=torch.float32, cast_forward_inputs=False))`;
8. call `register_fsdp_forward_method(owner, "scan_local_memory")`;
9. set `owner._local_memory_scan_fsdp_registered=True`.

This intentionally mirrors the training-mode single-rank FSDP2 semantics that produced DTensor Local parameters in run01.

Do not call `.to_local()`, ignored_params, inference mode, CPU offload or disable FSDP.

## 4. Real lifecycle witness

Before invoking `scan_local_memory`, prove at least one Local runtime parameter is a `DTensor` outside the registered method.

Create ordinary CUDA tensors:
- visual `[1,16,96]` fp32;
- executed_action `[1,16,15]` fp32;
- valid `[1,16]` bool with S0 absent and steps 1..15 valid.

Call the registered `owner.scan_local_memory(visual, action, valid, None)`.

PASS requires:
- no mixed Tensor/DTensor exception;
- Local tokens shape `[1,16,4,32]`;
- present shape `[1,16]` and S0 false / remaining 15 true;
- candidate fast state contains four finite ordinary fp32 tensors with B=1 shapes;
- output tensors finite.

Then form a deterministic scalar from Local-bearing tokens, e.g. mean square over tokens at present rows, and call backward.

Gradient witness:
- at least `runtime.encoder.visual_proj.weight` and `runtime.core.slot_queries` have finite non-zero gradients through the registered FSDP route;
- no gradient is required on the unused Local bridge in this micro-smoke;
- no no_grad/inference/detach surrounds scan.

No optimizer step is needed.

## 5. Memory / Evidence

Record JSON:
- formal root/child pair used;
- CUDA device/model and total memory;
- torch/CUDA version;
- process-group/world-size;
- ParallelDims and mixed-precision policy;
- Local parameter type names before scan, explicitly proving DTensor ownership;
- input shapes/dtypes/types;
- output shapes/dtypes/finiteness;
- gradient norms for the required representative parameters;
- allocated/reserved/peak allocated/peak reserved bytes at:
  - CUDA init;
  - owner materialized;
  - root FSDP wrapped;
  - before scan;
  - after scan;
  - after backward;
- exit status / exception.

Use a new unique directory:
`artifacts/v3/stage_b2c_r1b_micro/<unique-run>/`.

Any failure must produce result JSON and destroy the process group. No retry.

## 6. Harness implementation Gate

cx first implements only:
- one example/harness file, preferred:
  `examples/psm_wma_local_fsdp_scan_micro_smoke.py`;
- one CPU/static test file for CLI, world-size guard, output uniqueness, JSON schema and construction semantics.

cx must not run GPU.

The harness must provide:
- `--preflight` CPU-only mode;
- `--output <unique-dir>`;
- no external checkpoint/data/model arguments because this Gate intentionally uses none.

CPU/static tests must prove the script does not instantiate Edge/VAE/dataset assets and that its FSDP recipe matches §3.

After fresh pair, ChatGPT reviews the harness. Only then ds may execute exactly one GPU command.

## 7. Acceptance and next authorization

R1-B PASS means the exact run01 mixed Tensor/DTensor lifecycle defect is closed on real CUDA/FSDP2.

It does **not** close B2-C or authorize run02 automatically.

After PASS, ChatGPT must freshly review the R1-B Evidence and explicitly authorize one full B2-C run02 in a new directory.
