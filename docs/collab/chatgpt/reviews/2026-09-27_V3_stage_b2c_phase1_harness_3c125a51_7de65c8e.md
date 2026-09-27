# V3 Stage B2-C RTX4090 S1 — Phase-1 Harness Fresh Review

- Date: 2026-09-27
- Gate: `V3-STAGE-B2C-RTX4090-REAL-S1-SMOKE`
- design authority: `ced270eb07bbf9fac321e410f6d1992911d591cb`
- formal harness implementation root: `3c125a51af39bfcadeeeb02f83795784e23a1d66`
- formal harness child/Gitlink: `7de65c8e752c47359786e5ff2535a8d3cd5ddced`
- B2-B closed baseline: `81fa515593e7cd8e2d4f7d226efb915b17be3b5b / bf6c80e679812b7d2881d6a54aa0b518299e3869`
- Phase-1 conclusion: **PASS — B2-C §10 harness precondition satisfied; ds may execute one exact Phase-2 RTX4090 S1 run.**
- Gate status after this review: **REVIEW**. This is not B2-C closure.

## Fresh-review basis

The formal pair is new and was reviewed from the actual diff and frozen B2-C design. Relative to the closed B2-B child, the child adds only:

- `examples/psm_wma_robocasa_local_s1.py`
- `examples/psm_wma_robocasa_local_s1_test.py`.

No B0/B1/B2-A/B2-B production file changed.

Independent ChatGPT exact-pair CPU regression:
- **187/187 PASS**
- 21 third-party deprecation warnings
- runtime 30.82 s.

Independent ChatGPT real CPU preflight on the exact child, using the V3 child venv and correct TorchCodec CUDA-library search path:
- status PASS
- exact CloseFridge ep0
- Stage-A DCP/config authority accepted
- 429 episode frames
- official raw15 authority
- 16 cursor0 policy payloads.

An earlier ChatGPT preflight attempt failed only because the reviewer invoked the correct V3 Python from a different worktree while giving an incorrect relative `LD_LIBRARY_PATH`; rerunning from the exact V3 child environment passed. That reviewer execution error is not a harness finding.

## Contract findings

### Pair/scope — PASS

Root Gitlink equals the reviewed child SHA. The child diff is harness/tests only. Runtime pair lock additionally rejects a dirty child worktree or root/child Gitlink drift.

### Stage-A warm start — PASS

The harness validates the frozen Stage-A config and DCP metadata before GPU execution. The actual DCP has 549 model keys and predates Local Memory.

The load path uses the training-side sequence:
`ModelWrapper.state_dict -> DCP load with CustomLoadPlanner(skip local_memory) -> ModelWrapper.load_state_dict`.

Thus Stage-A host tensors are written back while freshly initialized Local-Memory tensors are preserved. Missing/unexpected-key validation only permits the new Local namespace and disabled EMA bookkeeping.

### Exact RoboCasa authority — PASS

The harness hard-binds CloseFridge / 20250816 / ep0 / cursor0. It constructs raw15 through the official V3 RoboCasa loader conversion, not H5 native12, verifies frame/episode continuity and overlapping action chunks, and materializes exactly 16 official policy consumers with chunk32 / 33-frame RGB input.

Cached Wan latent is used only by the B1 Local evidence reader and is rejected if it appears in a native policy payload.

### Local-only profile — PASS

The runtime overlay enables the frozen Local constants without modifying the formal Edge recipe on disk.

Optimizer selection is exactly `keys_to_select=["local_memory"]`, with **165,312** selected Local parameters. All non-Local parameters, including parameters outside `net`, are explicitly frozen before optimizer construction.

### B2-B relay reuse — PASS

The harness imports and executes the already closed `SingleSegmentNativeGradientRelay`; it does not reproduce the serial gradient relay implementation.

Each native callback calls ordinary `OmniMoTModel.training_step(..., _local_memory_prefixes=(leaf_or_none,))`. No trainer, checkpoint save, eval, server or auto-retry path is introduced.

### Failure/Evidence contract — PASS

Controlled failures write `result.json` with exception type/message, phase, consumer and traceback. OOM handling records failure memory evidence and does not authorize fallback geometry.

CUDA trace schema includes allocated/reserved and peak allocated/reserved bytes. Per-consumer forward coverage is 0..15. Local-bearing native backward coverage is 1..15; consumer0 is S0 and, by B2-B/resource v0.3, has no Local prefix and requires no Local backward. Relay backward is separately recorded once.

The earlier pre-review concern that consumer0 needed a `consumer_backward` record is therefore CLOSED as a reviewer interpretation error, not an implementation change.

## ds independent Phase-1 Evidence

ds independently validated the exact pair without GPU:
- harness CPU/static: **12/12 PASS**
- B0/B1/B2-A/B2-B regression: **175/175 PASS**
- real frozen-asset `--preflight`: PASS
- independent harness checks: **16/16 PASS**
- blockers/hard-fails: **0 / 0**.

The independent checks cover root/child/Gitlink identity, 165,312 inventory, exact B2-B relay reuse, forward 0..15, backward 1..15 with S0 exception, relay trace, memory schema and per-consumer peak reset.

## Phase-2 execution authorization

B2-C design §10 preconditions are satisfied.

ds is authorized to execute **one** exact RTX4090 S1 run using this reviewed child implementation and the frozen B2-C inputs. Execution must:
- use CloseFridge ep0 cursor0 T16 exactly;
- use Stage-A DCP/config and frozen asset paths;
- use Local-only 165,312 trainable parameters at LR 5e-5;
- run one rank / one process;
- use native RGB -> online Wan VAE for policy;
- perform no retry or automatic geometry/resource fallback;
- write the required result/memory/gradient/transaction Evidence under a unique `artifacts/v3/stage_b2c_4090_s1/<run>/` directory.

Any code/config/formal child change before execution invalidates this authorization and requires a fresh review.

## Scope boundary

This Phase-1 PASS does not close B2-C and does not approve:
- a second or longer 4090 run;
- DCP save/resume;
- multi-member/grouped GA;
- formal 8xH100 training;
- host+Local joint training;
- evaluation/server/SR claims.

B2-C closure requires fresh review of the actual Phase-2 GPU Evidence.
