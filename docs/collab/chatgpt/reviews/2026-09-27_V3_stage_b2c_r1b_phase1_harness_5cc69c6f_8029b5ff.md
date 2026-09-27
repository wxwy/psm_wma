# V3 Stage B2-C R1-B Tiny FSDP Micro-Smoke — Phase-1 Harness Review

- Date: 2026-09-27
- Gate: `V3-STAGE-B2C-R1B-TINY-FSDP-MICRO-SMOKE`
- formal harness root: `5cc69c6fa9e5b4f13aa6b2e4b180ec329c874d61`
- formal harness child/Gitlink: `8029b5ff002a350d22ee955db0463cc2e2d3665a`
- design authority: `544bbe0976aa60e935eee431350b20f38c47f28c`
- conclusion: **PASS — one exact R1-B RTX4090 micro-smoke is authorized.**
- this is not B2-C closure and does not authorize full run02.

## Fresh-review basis

Child diff from the closed R1-A baseline adds only:
- `examples/psm_wma_local_fsdp_scan_micro_smoke.py`
- `examples/psm_wma_local_fsdp_scan_micro_smoke_test.py`.

No production file changed.

ChatGPT exact-pair evidence:
- 11-file CPU/static suite: **216/216 PASS**, 4 GPU tests deselected by scope;
- exact-pair `--preflight`: PASS;
- preflight Local inventory: **165,312**;
- training-mode `ParallelDims(world_size=1, dp_shard=1, dp_replicate=1, cp=1, cfgp=1, enable_inference_mode=False)`;
- `dp_enabled=True`;
- no CUDA trace in CPU preflight.

ds independent evidence:
- same 216/216 CPU/static PASS;
- independent verification: **22/22 PASS**;
- 0 blocker / 0 hard-fail.

## Closed Phase-1 contracts

The harness:
- does not instantiate/load Edge, VAE, DCP, RoboCasa or external model/data assets;
- rejects non-single-rank environment before CUDA initialization;
- uses one-rank NCCL plus training-mode ParallelDims;
- root-wraps the tiny Local owner with FSDP2 and:
  `MixedPrecisionPolicy(param_dtype=bf16, reduce_dtype=fp32, cast_forward_inputs=False)`;
- registers `scan_local_memory` using `register_fsdp_forward_method`;
- proves Local runtime parameters are DTensors outside the registered scan;
- feeds ordinary CUDA Tensor evidence into the registered scan;
- validates Local tokens/present/candidate contracts;
- backpropagates a deterministic scalar and requires finite non-zero gradients on representative Local slow parameters;
- records allocator phases, pair lock, parameter types, inputs/outputs/gradients and controlled failures to JSON;
- destroys the process group it creates;
- has no retry/fallback path.

## One-time execution authorization

Exactly one Phase-2 GPU micro-smoke is authorized on the current RTX4090.

Formal harness implementation pair remains:
`5cc69c6fa9e5b4f13aa6b2e4b180ec329c874d61 / 8029b5ff002a350d22ee955db0463cc2e2d3665a`.

A review/bookkeeping-only root commit after this review does not replace that formal pair. The child SHA must remain exactly `8029b5ff002a350d22ee955db0463cc2e2d3665a`.

Execution output must use one new directory under:
`artifacts/v3/stage_b2c_r1b_micro/`.

No retry is authorized. On any failure, retain Evidence and stop.

## Boundary

A PASS only proves the run01 Tensor/DTensor Local-scan lifecycle defect is closed on real CUDA/FSDP2.

Even on PASS:
- B2-C full run02 remains blocked;
- full Edge/VAE/DCP/RoboCasa execution remains unauthorized until a fresh review of R1-B Evidence explicitly authorizes one run02.
