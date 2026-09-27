# V3 Stage B2-C R2 TorchCodec Runtime-Env Preflight — Closure and Run03 Authorization

- Date: 2026-09-27
- Gate: `V3-STAGE-B2C-R2-TORCHCODEC-RUNTIME-ENV`
- execution formal root: `5cc69c6fa9e5b4f13aa6b2e4b180ec329c874d61`
- formal child/Gitlink: `8029b5ff002a350d22ee955db0463cc2e2d3665a`
- design authority: `f798a405de3717abfbbb13812f4db2f79d330224`
- run02 failure review bookkeeping: `e16ea98b19bc0f9edd36afdf0e661141b94c2969`
- verdict: `APPROVE_TO_CLOSE_V3_STAGE_B2C_R2_TORCHCODEC_RUNTIME_ENV`
- additional action: **authorize exactly one full B2-C RTX4090 S1 run03**.

## Evidence reviewed

ds validation-only preflight:
- 26/26 checks PASS, exit 0;
- exact execution pair preserved and child tracked worktree clean;
- run01/run02 unchanged.

Frozen execution library prefix:
`/disk/rl/worktrees/cosmos-framework-v3/.venv/lib/python3.13/site-packages/nvidia/cu13/lib`.

With that path prepended to `LD_LIBRARY_PATH`:
- `libnppicc.so.13` exists;
- `torchcodec.decoders.VideoDecoder` imports successfully;
- TorchCodec reports version `0.10.0+cu130`;
- all five `libtorchcodec_core*.so` resolve `libnppicc.so.13` and `libnppc.so.13` to the frozen CUDA13 lib directory with zero unresolved NPP dependency.

ChatGPT independently reproduced:
- TorchCodec import PASS under the frozen path;
- NPP shared libraries resolve from the frozen path;
- official RoboCasa loader exact CloseFridge/20250816 episode0 decoding succeeds.

## Official episode-source witness

The preflight used the same `RoboCasaLeRobotDataset` construction as the unchanged full S1 harness:
- fps=20
- chunk_length=32
- split=full
- mode=wam
- use_state=True
- use_base_action=True
- base_encoding=raw
- camera_set=left_wrist
- action_normalization=None.

Exact identity:
- task CloseFridge
- date 20250816
- episode0
- frames=429
- valid consumer anchors=397
- exact first consumer flat index 68029 → source0,row0,ep0,step0
- exact step8 consumer flat index 68037 → source0,row8,ep0,step8.

Observed:
- action0/action8 = `[33,15]` fp32;
- video0/video8 = `[3,33,256,512]` uint8;
- original stored action = 12D, official converted episode authority = 15D;
- action[1:] matches exact raw15 transitions;
- step0/step8 overlap raw15 max absolute difference = 0.0;
- no `video_latent` enters the policy payload;
- video backend is TorchCodec;
- no alternate backend, episode substitution, shuffle or fallback.

This closes the exact run02 environment failure. No code or algorithm change is required.

## Run03 authorization

Exactly one full B2-C RTX4090 S1 run03 is authorized.

Formal execution pair must remain:
- root `5cc69c6fa9e5b4f13aa6b2e4b180ec329c874d61`
- child/Gitlink `8029b5ff002a350d22ee955db0463cc2e2d3665a`.

The full harness remains unchanged.

Before execution:
- pair and child cleanliness must be rechecked;
- `artifacts/v3/stage_b2c_4090_s1/run03` must not exist;
- RTX4090 must be otherwise idle;
- run01 and run02 must remain immutable.

Execution environment must prepend:

```bash
V3_CUDA13_LIB=/disk/rl/worktrees/cosmos-framework-v3/.venv/lib/python3.13/site-packages/nvidia/cu13/lib
export LD_LIBRARY_PATH="$V3_CUDA13_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
```

Then run the unchanged full S1 harness with output `run03`.

No retry, fallback, algorithm reduction or alternate checkpoint is authorized.

## Scope

run03 is still one wiring/resource smoke. Even on PASS, B2-C closure requires fresh review of the actual full GPU Evidence. Formal 8xH100 training remains unauthorized until B2-C is closed.
