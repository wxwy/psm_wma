# PSM-WMA V3 Stage B2-C RTX4090 Real S1 Smoke Design v0.1

- Date: 2026-09-27
- Gate: `V3-STAGE-B2C-RTX4090-REAL-S1-SMOKE`
- B2-B formal pair: root `81fa515593e7cd8e2d4f7d226efb915b17be3b5b` / child `bf6c80e679812b7d2881d6a54aa0b518299e3869`.
- B2-B closure bookkeeping is not a replacement formal pair.
- Resource authority: `PSM-WMA_V3_stage_b2_resource_profiles_4090_h100_design_v0.3_2026-09-27.md`.
- Roles: ChatGPT design/review; cx implementation; ds execution/Evidence; user owner/final decision.
- Current host: RTX4090 24564 MiB.
- Algorithm constants remain T=16, K=4, local_dim=32, evidence_dim=256, ttt_dim=64, fast_hidden=256, inner_lr=0.1, raw15, policy chunk32 / consumer33 frames.

## 1. Goal

Prove that the exact closed V3 path can execute one real Local-only update on the 24GB RTX4090:

```text
real RoboCasa ep0 RGB/raw15 + real cached Wan2.2 evidence
→ B1 producer cursor0 SegmentBatch (T=16, 16 valid)
→ B0 scan
→ B2-B serial native OmniMoT consumer forwards/backwards
→ exact gradient relay
→ Local-only optimizer step
→ fast-state/frontier commit
```

This is a wiring/resource smoke, not a capability-training run.

## 2. Frozen real sample

Use exactly:
- task: `CloseFridge`;
- episode index: `0`;
- cursor: `0`;
- one slot;
- one GA member;
- segment has exactly 16 valid consumers, steps 0..15;
- cached latent:
  `/disk/rl/starVLA/playground/Datasets/robocasa365_wan2.2_latent/v1.0/target/atomic/CloseFridge/20250816/lerobot/ep_000000.h5`;
- v3 training dataset root:
  `/disk/rl/data/robocasa_v30`.

The native episode source must resolve the exact v3 episode0 consumer anchors. It may not use shuffle, first-available heuristics or substitute another episode.

For each consumer t, the native payload must be the official RoboCasa action-policy sample with:
- left_wrist RGB;
- state enabled;
- raw base action;
- policy chunk=32 / 33 observation frames;
- action width 15 after official conversion.

The harness must verify overlapping raw15 transitions are identical before constructing the full episode raw15 authority.

## 3. Frozen Stage-A checkpoint authority

Warm-start the host from the Stage-A closed one-step RoboCasa raw15 DCP:

`/disk/rl/worktrees/psm_wma-v3/artifacts/v3/stage_a_edge_raw15_run02/psm_wma_v3/edge_robocasa/smoke/checkpoints/iter_000000001`

and its Stage-A config under the same smoke run.

This is preferred over the original DROID base because B2-C validates the incremental Local path on the exact Stage-A-closed RoboCasa host.

Required base assets remain:
- Edge processor/model source: `/disk/rl/models/Cosmos3-Edge-Policy-DROID`;
- Wan2.2 VAE: `/disk/rl/models/wan22_vae/Wan2.2_VAE.pth`.

The Stage-A DCP predates Local Memory and therefore legitimately lacks `local_memory*` parameters. B2-C must load all host parameters from the Stage-A DCP while preserving freshly initialized Local-Memory parameters.

Allowed warm-start missing keys are exactly the new Local-Memory namespace plus disabled EMA bookkeeping. Any other missing/unexpected host key is a hard failure.

Do not load Stage-A optimizer/trainer state.

## 4. 4090 Local-only model/optimizer profile

Enable the B2 Local subsystem with the closed constants.

Trainable set is exactly the complete Local-Memory inventory:
- LocalEvidenceEncoder: 29,440
- ContinualTTTLocalMemoryCore: 66,240
- local_memory2llm: 67,584
- local_memory_modality_embed: 2,048
- total: **165,312 parameters**.

Use optimizer allowlist:
`keys_to_select=["local_memory"]`.

All non-Local host parameters must be frozen before the native smoke forward.

Use the inherited Edge base slow LR `5e-5` for this one-step smoke; no Local-specific LR tuning is part of this Gate.

Keep:
- activation checkpointing selective;
- EMA disabled;
- compile disabled;
- native RGB -> online Wan VAE main policy route.

Cached latent remains Local evidence only.

## 5. Exact native callback

B2-C must use the already-closed B2-B serial relay. It must not reimplement gradient relay.

For one gathered consumer:

```text
custom_collate_fn([native_payload])
→ move ordinary native batch to model device
→ OmniMoTModel.training_step(
      collated,
      iteration=0,
      _local_memory_prefixes=(leaf_or_none,)
  )
→ NativeConsumerResult(loss=native_total_loss, detached diagnostics)
```

Rules:
- one consumer per native call;
- S0 prefix is None and under Local-only freezing its loss must carry no Local gradient;
- consumers 1..15 use exact detached prefix leaves;
- native total policy loss is the only outer objective;
- no cached latent is passed to the policy forward;
- no no_grad/inference/detach other than the B2-B paired leaf boundary.

## 6. Single-process runtime

Run in an isolated one-rank process using the same V3 environment and CUDA stack as Stage A.

The harness may initialize a single-rank process group as required by official checkpoint/model setup, but:
- world_size=1;
- no trainer;
- no DDP/FSDP multi-rank execution;
- no checkpoint save;
- no eval/server;
- no auto-resume.

The implementation must reuse current Cosmos config/model/checkpoint primitives rather than implement a second model loader.

## 7. Memory instrumentation

The harness must record structured CUDA memory Evidence at minimum for:
1. CUDA init;
2. processor/config ready;
3. model materialized;
4. Stage-A DCP host loaded;
5. Wan VAE/tokenizer ready;
6. Local-only optimizer ready;
7. B0 scan completed;
8. each native consumer 0..15 after forward/backward;
9. after relay backward;
10. after optimizer step;
11. after fast-state commit.

Record for each phase:
- allocated bytes;
- reserved bytes;
- peak allocated bytes;
- peak reserved bytes.

Before each native consumer, reset peak-memory stats so the result includes a per-consumer peak.

Also record an external `nvidia-smi` sampler if ds chooses, but torch allocator stats are canonical.

Historical context only: Stage A train smoke sampled about 32.2GB with host tuning; this is not an acceptance threshold and is not a B2-C result.

## 8. Acceptance

PASS requires all of:

### Identity/data
- exact B2-B implementation pair used;
- exact Stage-A checkpoint/config path used;
- exact CloseFridge ep0 H5 and v3 episode0 used;
- B1 reader/cache identity, frame count and left_wrist endpoints valid;
- SegmentBatch consumer steps exactly 0..15;
- raw15 source is official v3 loader, not H5 native12.

### Optimizer/gradient
- selected trainable elements exactly 165,312;
- zero non-Local trainable parameters;
- before step, finite non-zero gradients on:
  - representative encoder parameter;
  - `core.slot_queries`;
  - `core.w0_fast_in_weight`;
  - `local_memory2llm.weight`;
  - `local_memory_modality_embed`;
- no sampled frozen host gradient;
- Local optimizer step changes at least one Local tensor;
- sampled frozen host tensors remain bitwise unchanged.

### Transaction
- no sidecar/frontier publish before optimizer success;
- one successful Local optimizer step;
- cursor0 fast-state candidate committed after step;
- committed fast state finite detached fp32;
- scheduler frontier exactly cursor0 once.

### Numerics
- all 16 native losses finite;
- segment mean finite;
- no NaN/Inf in Local gradients or parameters.

### Resource
- the entire process completes on the RTX4090 without CUDA OOM;
- peak allocated/reserved memory is recorded.

## 9. OOM / failure policy

OOM or any runtime failure is Evidence, not permission to alter the algorithm.

On failure:
- record phase and consumer index;
- record allocator stats and exception;
- require zero new fast-state/frontier commit;
- terminate the isolated smoke process;
- do not auto-retry with smaller T/K/chunk, fake terminal, dropped consumers, cached-policy latent, host offload or a different checkpoint.

Any resource remediation requires a new design/review.

## 10. Harness implementation gate before GPU execution

cx first implements only the smoke harness + CPU/static tests. **cx must not run GPU.**

Preferred scope:
- one new child harness, e.g. `examples/psm_wma_robocasa_local_s1.py`;
- focused CPU/static tests for CLI/preflight/config overlay/callback construction/stop rules;
- no semantic edits to B0/B1/B2-A/B2-B production modules unless an unavoidable narrow seam is separately justified.

The harness must provide:
- `--preflight` or equivalent CPU-only mode;
- `--output <unique-dir>`;
- explicit paths for Stage-A checkpoint/config, H5 cache and RoboCasa v3 root;
- deterministic task/episode/cursor;
- JSON result output even on controlled failure/OOM.

After cx forms a fresh pair, ChatGPT performs fresh review. Only after approval will ds execute the exact 4090 command.

## 11. Evidence output

Formal ds run root:
`artifacts/v3/stage_b2c_4090_s1/<unique-run>/`

Required:
- pair lock;
- resolved config/paths;
- command/environment summary;
- stdout/stderr;
- `result.json`;
- CUDA memory trace;
- Local parameter/gradient witness;
- transaction witness.

Artifacts are Evidence and need not be committed into Git.

## 12. Scope boundary

Passing B2-C proves one real Local-only update fits and is correct on RTX4090 24GB.

It does not approve:
- a second/longer 4090 training run;
- checkpoint/resume;
- multi-member/grouped GA;
- formal 8xH100 training;
- joint host+Local optimizer behavior;
- task SR/capability.
