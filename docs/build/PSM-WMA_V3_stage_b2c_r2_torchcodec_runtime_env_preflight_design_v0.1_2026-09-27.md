# PSM-WMA V3 Stage B2-C R2 TorchCodec Runtime-Env Preflight Design v0.1

- Date: 2026-09-27
- Gate: `V3-STAGE-B2C-R2-TORCHCODEC-RUNTIME-ENV`
- Parent Gate: `V3-STAGE-B2C-RTX4090-REAL-S1-SMOKE`.
- Full-S1 execution formal pair remains:
  - root `5cc69c6fa9e5b4f13aa6b2e4b180ec329c874d61`
  - child/Gitlink `8029b5ff002a350d22ee955db0463cc2e2d3665a`.
- R1-A and R1-B are closed. run01 and run02 Evidence remain immutable.
- run02 failure review bookkeeping root: `e16ea98b19bc0f9edd36afdf0e661141b94c2969`.
- This Gate is environment preflight only. It does not authorize a full S1 run.

## 1. Failure being remediated

B2-C run02 failed at `episode_source`, before model construction, B0 scan or any native consumer work.

TorchCodec failed to load because `libnppicc.so.13` was not on the dynamic loader search path.

The required library already exists at:
`/disk/rl/worktrees/cosmos-framework-v3/.venv/lib/python3.13/site-packages/nvidia/cu13/lib/libnppicc.so.13`.

No package installation or code modification is justified.

## 2. Canonical runtime library path

For the V3 environment on this host, freeze:

```bash
V3_CUDA13_LIB=/disk/rl/worktrees/cosmos-framework-v3/.venv/lib/python3.13/site-packages/nvidia/cu13/lib
export LD_LIBRARY_PATH="$V3_CUDA13_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
```

The V3 path must be prepended, not appended. This adjustment is execution-only and does not alter the formal code pair.

## 3. Exact preflight

Run under the exact formal pair, validation-only.

### Pair / hygiene
- root HEAD exactly `5cc69c6fa9e5b4f13aa6b2e4b180ec329c874d61`;
- root Gitlink exactly `8029b5ff002a350d22ee955db0463cc2e2d3665a`;
- child HEAD exactly `8029b5ff002a350d22ee955db0463cc2e2d3665a`;
- child tracked worktree clean;
- run01/run02 unchanged.

### Library authority
- frozen CUDA13 lib directory exists;
- `libnppicc.so.13` exists there;
- after setting the frozen `LD_LIBRARY_PATH`, importing `torchcodec.decoders.VideoDecoder` succeeds;
- inspect the relevant `libtorchcodec_core*.so` using `ldd` under the same environment and require no unresolved `libnpp*.so.13` dependency.

### Exact official episode-source decode
Use the same official V3 RoboCasa / LeRobot source path as the full harness, not a custom video reader.

Frozen source:
- task `CloseFridge`;
- date `20250816`;
- episode index `0`;
- dataset root `/disk/rl/data/robocasa_v30`;
- `use_base_action=True`;
- `base_encoding="raw"`;
- `camera_set="left_wrist"`;
- `use_state=True`;
- fps 20;
- chunk_length 32;
- action_normalization None.

Resolve the exact first consumer anchor for episode0 through the existing RoboCasa dataset implementation and call its normal `__getitem__` path.

Acceptance witness:
- official sample decode completes through TorchCodec;
- action tensor shape is `[33,15]` because row0 is the clean state token and rows1..32 are raw15 action transitions;
- native RGB payload is present under the normal dataset contract;
- no H5 native12 action is substituted;
- no alternate video backend is selected;
- no episode/task substitution, shuffle or fallback occurs.

Also decode at least one later overlapping consumer from the same episode and verify overlapping raw15 transitions are identical.

## 4. No GPU model execution

This R2 preflight may let TorchCodec/CUDA libraries load, but it must not instantiate Edge, load Stage-A DCP, load Wan VAE, run B0 scan, run policy forward/backward, create optimizer state, or run full S1.

## 5. Evidence

Write `/tmp/v3_b2c_r2_torchcodec_env_preflight.txt` with: exact pair, LD path, library path, TorchCodec import, ldd results, exact episode identity, sample indexes/frame anchors, action/image shapes, overlapping raw15 max diff, absence of fallback, commands and exit codes.

No repo changes.

## 6. Acceptance / next authorization

PASS requires all checks above with zero unresolved NPP dependency and successful official episode0 decoding.

A PASS does not itself execute S1. ChatGPT must freshly review the Evidence. Only after that review may one new full B2-C S1 execution be authorized with the same formal pair, unchanged harness, new output `artifacts/v3/stage_b2c_4090_s1/run03`, and the frozen LD_LIBRARY_PATH prefix.

No retry of run01 or run02 is allowed.
