# V3 Stage B2-C RTX4090 S1 run02 — Environment Failure Review

- Date: 2026-09-27
- Parent Gate: `V3-STAGE-B2C-RTX4090-REAL-S1-SMOKE`
- execution formal root: `5cc69c6fa9e5b4f13aa6b2e4b180ec329c874d61`
- execution child/Gitlink: `8029b5ff002a350d22ee955db0463cc2e2d3665a`
- authorization bookkeeping root: `872ea11ac29f9f7f8d8b757b15991b9b9fb21f9e`
- run Evidence: `artifacts/v3/stage_b2c_4090_s1/run02/`
- verdict: `REQUEST_CHANGES`
- no retry of run02 is authorized.

## Result

The single authorized run02 produced `result.json.status=FAIL`.

Failure phase:
`episode_source`.

The harness failed while the official RoboCasa v3 loader attempted to import TorchCodec before model construction / B0 scan / native consumer execution.

Error authority:
`libnppicc.so.13: cannot open shared object file`.

The failure occurs inside TorchCodec shared-library loading, before any Local-Memory or policy execution.

## Root cause

The required CUDA 13 NPP shared object is present in the active V3 virtualenv:

`/disk/rl/worktrees/cosmos-framework-v3/.venv/lib/python3.13/site-packages/nvidia/cu13/lib/libnppicc.so.13`.

The same directory also contains the companion CUDA13 NPP/CUDART libraries.

run02 was launched without adding that directory to `LD_LIBRARY_PATH`. A generic CUDA/cuDNN conv3d sanity check passed because PyTorch can locate its own CUDA/cuDNN runtime through its package loading path; that check does not prove a separately dlopen'ed TorchCodec shared object can resolve NPP dependencies.

The failure is therefore a dynamic-loader environment omission, not:
- a missing package;
- a Local/FSDP lifecycle regression;
- a Stage-A DCP problem;
- a 4090 OOM;
- a B0/B1/B2-A/B2-B semantic failure.

## Evidence boundary

run02 never reached:
- full model construction;
- B0 Local scan;
- native consumer forward;
- outer backward;
- optimizer step;
- fast-state/frontier commit.

Its CUDA memory trace is empty.

Therefore run02 gives no new evidence on 24GB fit of the full native consumer path.

The immutable run01 Tensor/DTensor defect remains closed by R1-A + R1-B GPU micro-smoke; run02 does not reopen it.

## Required remediation

No code change is justified.

Before any new full S1 authorization, a separate environment preflight must prove under the exact execution pair:
1. the V3 CUDA13 library directory is prepended to `LD_LIBRARY_PATH`;
2. TorchCodec imports successfully;
3. its shared objects have no unresolved CUDA/NPP dependencies relevant to this failure;
4. the exact frozen CloseFridge episode0 video path can be decoded through the same official RoboCasa/LeRobot source path;
5. the output pair/code remains unchanged.

Only after fresh review of that preflight may one new full S1 execution be authorized with a new unique output directory.

run01 and run02 remain immutable.
