# V3 Stage B2-C R1-B Tiny FSDP Micro-Smoke — Closure and Run02 Authorization

- Date: 2026-09-27
- Gate: `V3-STAGE-B2C-R1B-TINY-FSDP-MICRO-SMOKE`
- formal harness root: `5cc69c6fa9e5b4f13aa6b2e4b180ec329c874d61`
- formal child/Gitlink: `8029b5ff002a350d22ee955db0463cc2e2d3665a`
- design authority: `544bbe0976aa60e935eee431350b20f38c47f28c`
- Phase-1 review bookkeeping root: `2aaf0a8e65b417b447fe246b2f9bfffab6217ef0`
- verdict: `APPROVE_TO_CLOSE_V3_STAGE_B2C_R1B_TINY_FSDP_MICRO_SMOKE`
- additional action: **authorize exactly one full B2-C RTX4090 S1 run02**.

## Phase-2 GPU Evidence

The one authorized R1-B RTX4090 micro-smoke executed once, with no retry or downgrade.

Evidence directory:
`artifacts/v3/stage_b2c_r1b_micro/run01/`.

Result:
- exit code: 0
- status: PASS
- device: NVIDIA GeForce RTX 4090
- process group: NCCL, world_size=1
- training-mode ParallelDims: dp_shard=1, dp_replicate=1, cp=1, cfgp=1, inference=False
- mixed precision: FP32 master / BF16 param compute / FP32 reduce / cast_forward_inputs=False
- Local inventory: 165,312 parameters
- process_group_destroyed: true.

### Exact lifecycle defect witness

Before the registered scan, all sampled Local runtime parameters were reported as `DTensor`, including:
- encoder.visual_proj.{weight,bias}
- encoder.action_proj.{weight,bias}
- encoder.norm.{weight,bias}
- core.slot_queries
- core fast-state initialization parameters
- core key/query/value projections.

Inputs remained ordinary CUDA tensors:
- visual: `[1,16,96]` fp32 Tensor
- action: `[1,16,15]` fp32 Tensor
- valid: `[1,16]` bool Tensor.

The registered `scan_local_memory` completed without mixed Tensor/DTensor dispatch failure.

Outputs:
- Local tokens: `[1,16,4,32]` fp32 finite
- present: S0 false, steps 1..15 true
- candidate fast state: four finite ordinary fp32 tensors with B=1 shapes.

Backward completed through the registered FSDP route.

Representative finite non-zero gradient norms:
- encoder.visual_proj.weight: 0.0267910566
- core.slot_queries: 0.00272601447.

This directly reproduces the run01 precondition (DTensor-owned Local params + ordinary Tensor B0 evidence) while proving the R1-A registered forward-method remediation removes the failure.

### Memory

Tiny micro-smoke peak allocator values:
- peak allocated: 24,537,088 bytes (~23.4 MiB)
- peak reserved: 31,457,280 bytes (~30.0 MiB).

These values only characterize the tiny lifecycle fixture and are not evidence that the full Edge consumer path fits 24GB.

## Full S1 harness stability

The full S1 harness files:
- `examples/psm_wma_robocasa_local_s1.py`
- `examples/psm_wma_robocasa_local_s1_test.py`

have zero diff between the original Phase-1-approved harness child `7de65c8e...` and current child `8029b5ff...`.

Current child differences from the original approved harness are limited to:
- R1-A FSDP Local-scan remediation production changes and focused test;
- R1-B tiny micro-smoke harness/test.

R1-A was freshly closed, and R1-B is closed by this review.

## Run02 authorization

Exactly one full B2-C RTX4090 S1 execution is now authorized.

Execution pair must remain:
- root `5cc69c6fa9e5b4f13aa6b2e4b180ec329c874d61`
- child/Gitlink `8029b5ff002a350d22ee955db0463cc2e2d3665a`.

A later review/bookkeeping root commit does not replace that formal execution pair.

The run must:
- use the unchanged frozen B2-C harness and default frozen assets;
- use `CloseFridge` episode0 cursor0, T=16, K=4, raw15, policy chunk32/33-frame;
- warm-start the Stage-A one-step DCP;
- train only the 165,312 Local parameters at LR 5e-5;
- use native RGB→Wan VAE policy input and cached latent only as Local evidence;
- serialize all 16 native consumers using the closed B2-B exact gradient relay;
- use a new unique output directory `artifacts/v3/stage_b2c_4090_s1/run02`;
- retain allocator/gradient/transaction Evidence;
- perform no retry, no algorithm reduction, no cached-policy-latent fallback and no alternate checkpoint.

On failure, retain Evidence and stop.

## Scope

This authorization is for one wiring/resource smoke only.

Even if run02 passes, B2-C closure requires fresh review of its actual GPU Evidence. It does not authorize a longer 4090 run, checkpoint/resume, formal 8xH100 training or SR/capability claims.
