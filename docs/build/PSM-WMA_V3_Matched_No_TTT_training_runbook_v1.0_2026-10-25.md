# V3 Matched No-TTT baseline — implementation candidate and acceptance runbook

Date: 2026-10-25 (Asia/Shanghai). Owner request authorizes implementation and CPU checks only. This document does not authorize GPU, training, model serving or RoboCasa execution. Exact implementation pair and author evidence are recorded in the accompanying Codex handoff; later documentation commits are not replacement implementation SHAs.

## Contract and scope

The baseline reuses the current V3 Cosmos3-Edge-Policy-DROID recipe, official DROID model initialization check, Verified Index, Cached Latent SFT, ExactWindowLocalCatalog, ExactWindowRankPlanner, ExactWindowSegmentProducer, native collator, native Cosmos model, outer loss, optimizer construction and F0/F1 lifecycle. It does not port V2 or build another Cosmos model.

| Property | Matched contract |
| --- | --- |
| Initialization | Same official DROID DCP as G1; model-only warm start, never G1 iter12000 or its optimizer |
| Data | Same RoboCasa365 Target Atomic source/cache/verified-index identities as the chosen G1 reference |
| ABI | left_wrist, WAM, raw15/state15, model-space64, H_pred/chunk16, 17 observation frames, 20fps |
| Scheduling | Same deterministic rank partition, seed0, task-balanced episode queue, stable slots and episode order |
| Packing | B8 × next chronological T16, slot-major, at most128 valid consumers per rank/member; GA2 |
| Update count | Full window256 consumers/rank, world8 nominal2048; terminal partials retain actual counts |
| Optimizer | Same seven Generation selectors and frozen understanding backbone; no Local selectors/parameters |
| LR/schedule | Base5e-5, same action-head multipliers5×, same weight decay/skips, warmup500/max30000/save100 |
| Local model | local_memory_enabled=False before model construction; runtime/projection/embed parameters forbidden |
| Native call | training_step(batch, iteration), with no private prefix override and no dataset Local tokens |
| Local algorithm | No scan, inner-loop, Fast Weights, Local sidecar, TBPTT graph or Local commit |
| State | Own strict per-rank data frontier format, separate config digest/job namespace and optimizer state |
| Inference | Original native RoboCasa Action Server with explicit off/raw15/chunk16/state-enabled saved config |

T and K remain in the shared configuration/identity for geometry and compatibility. T16 is only a consumer grouping length for this profile; K4 is inert and does not create Local tokens. The unchanged Producer still materializes its small evidence fields in CPU SegmentBatch objects to preserve exactly the established transform order/RNG and source validation. No-TTT consumes only valid payloads and never feeds those evidence fields to a Local algorithm or model. This is not a throughput optimization.

For member m with actual n_m consumers, the exact existing G1 objective is:

`weighted_native_loss_m = native_loss_m * n_m / sum_j(n_j)`.

One native forward/backward executes per GA member. No extra division by GA or fixed128 occurs; auxiliary losses remain inside the original native scalar. Native token/sample loss averaging and distributed reduction policy are inherited, including G1's rank-local denominator for uneven terminal windows. This is not a new globally consumer-weighted reduction. It does not require identical gradients/losses or identical model-noise RNG between Local and No-TTT architectures.

## Entrypoints and parameters

New training entry: `scripts/train_v3_matched_no_ttt.sh {fresh|resume} EXECUTION_UNTIL`.

Use an independent clean checkout of the reviewed exact Root/Child. Set `EXPECTED_ROOT`/`EXPECTED_CHILD` to that checkout's exact pair. Existing G1 checkout/config/identity/checkpoints remain immutable. Do not update an active G1 worktree.

Environment interface:

```bash
export OUTPUT_ROOT=/new/independent/baseline/output
export JOB_NAME=no_ttt_packed128_droid_fresh_30k
export SOURCE_ROOT=/same/verified/robocasa365/target/atomic
export CACHE_ROOT=/same/accepted/exact_window_cache
export DATASET_INDEX_ROOT=/same/accepted/verified_index
export EDGE_POLICY_CHECKPOINT=/official/Cosmos3-Edge-Policy-DROID
export WAN_VAE_PATH=/same/accepted/Wan_VAE.pth
export BASE_CHECKPOINT_PATH=/official/DROID_DCP
export EXPECTED_ROOT=<reviewed-exact-root-40hex>
export EXPECTED_CHILD=<reviewed-exact-child-40hex>
# Optional PYTHON=/training/environment/bin/python
```

`JOB_NAME` defaults to `no_ttt_packed128_droid_fresh_30k`; explicit names must start `no_ttt_`. Namespace remains `OUTPUT_ROOT/psm_wma_v3/corrected_phase5/JOB_NAME`, independently claimed by F0. Existing directories, symlink aliases, cross-profile Resume, G1 Owner Resume overrides and mismatching identity are rejected. The launcher fixes world8/T16/B8/GA2/K4, synchronous workers0 and legacy-global transforms. It cannot silently enable TTT or fall back to Index8.

After independent review/acceptance and explicit Owner runtime authorization, the requested command form is:

```bash
bash scripts/train_v3_matched_no_ttt.sh fresh 30000
```

For first acceptance, prefer the same formal schedule with execution budget100, then one Resume to500:

```bash
# Runtime commands, NOT authorized by this CPU implementation delivery.
bash scripts/train_v3_matched_no_ttt.sh fresh 100
bash scripts/train_v3_matched_no_ttt.sh resume 500
```

Read-only CPU preflight on the actual training host uses the shared Python entry with the same flags plus `--no-ttt --preflight`; it needs the real accepted assets and dependencies but constructs no model. Copy the launcher's complete flags and externalize HF/Matplotlib/XDG caches. It is not a substitute for GPU Config.validate or model execution.

Same-job Resume requires the identical reviewed source pair, unchanged canonical config/identity, F1 completion marker, all rank state/RNG and full optimizer/scheduler/model state. There is no No-TTT cross-pair override. The new per-rank state is `psm_v3_matched_no_ttt_frontier_v1`; G1 Local state and this format reject one another. The per-rank frontier, source/config/rank/world/B/T/GA/seed binding and committed iteration are checked before the first native forward. Pending/failed windows cannot be checkpointed; frontier publishes only after a successful optimizer step.

## Matching the actual G1 reference

Fixed geometry alone is not evidence that paths point to identical data. Before claiming a matched experiment, DS must compare the new preflight report with the immutable reference G1 report/identity:

- cache manifest/corpus/source-binding digests and accepted index receipt;
- official Edge/VAE/base DROID asset identity and model metadata; do not substitute a trained G1 model;
- per-rank sampler seed, episode partition/queue, Consumer identity trace, masks and sequence plan;
- Generation parameter names/shapes/initialization, LR groups, outer loss weights/normalization and scheduler;
- formal schedule and actual effective consumers, including terminal partials.

The new configuration gets its own Root/Child/profile/config digest. Do not copy G1's digest or rewrite G1's saved chunk32 compatibility mirror: that old mirror was not its real Exact-Window Producer. Current No-TTT canonical config saves the actual chunk16 and records the actual MatchedNoTTTTrainer producer chain. Actual same-data/asset matching is a target-host acceptance requirement, not established by dummy paths in author CPU tests.

## Inference configuration

Copy/edit `configs/eval/robocasa_matched_no_ttt.example.yaml` into an external run directory. Bind `checkpoint` and `config_file` to this baseline's own completed checkpoint and canonical saved config, not a G1 config modified to say off.

```bash
# CPU-only command preview; reads identities/config/model-file presence, loads no model.
python scripts/serve_v3_matched_no_ttt.py --config /external/baseline_inference.yaml --dry-run

# Only after separate GPU authorization; starts the existing native server.
python scripts/serve_v3_matched_no_ttt.py --config /external/baseline_inference.yaml
```

The wrapper verifies No-TTT semantic identity and config hash, same-job checkpoint path, model metadata/shard presence, raw15/state15/H16/Packed128 contract, left_wrist/state-enabled dataset configuration, and Generation-only optimizer. It explicitly supplies `--local-memory-mode off --raw-action-dim 15 --action-chunk-size 16 --max-action-dim 64 --fps 20`. It never edits saved config or model weights. It does not read optimizer files for inference. Runtime `/info` and model-weight loading remain separate target-host checks.

The existing unified required-TTT Queue is unchanged and continues to reject off-mode profiles; do not feed the new standalone schema into it or combine baseline results with its Local-TTT Resume catalog. The existing Child closed-loop client supports explicit `--local-memory-mode off`; actual baseline evaluation must use off on both server and client with the same raw/state/camera/horizon protocol. This delivery provides an inference profile/entry, not approval of a new formal No-TTT benchmark or automatic 18-task Queue migration.

## Acceptance and stopping rules

| Gate | Evidence | Owner |
| --- | --- | --- |
| Author CPU | New trainer/profile/launcher/inference negatives, real small Cosmos constructor, G1 Consumer order/partial weighting, strict frontier roundtrip, nonfinite/hook/scaler failures, complete real-recipe YAML/pickle serialization; relevant existing regressions and static checks | Codex |
| Fresh incremental code review | New exact Root/Child + diff + author evidence, including shared G1 default-path compatibility | GPT |
| Independent CPU | Clean detached exact pair, same frozen test list/environment/source hashes; all new cases execute, optional real-asset skips explicitly retained | DS_PRO |
| S0 real inputs/storage | Actual matched G1 witnesses above, index/ABI/masks and native config validation, storage/retention plan without deleting old evidence | DS_PRO, read-only |
| GPU canary/Fresh100 | Owner separately authorizes; prove no Local params/scan/prefix/state, generation gradients present/finite, native batch counts/order/action masks, loss and successful world8 saves | DS_PRO |
| Resume100→101→500 | Full model/optimizer/scheduler/CUDA-RNG/frontier continuity, same selected config/layout, no reseed or duplicate/skipped consumers | DS_PRO |
| Matched task evaluation | Same runtime/vendor/controller/physics/task/seed/episode/max-step/num-steps/horizon/guidance protocol as reviewed G1, baseline off end to end | Owner authorization required |

Any identity/source/mask/gradient/restore/state/IO failure stops. Preserve failed artifacts and old G1/evaluation evidence; never label CPU pass as GPU/30k or SR acceptance. Stop after publication and handoff for GPT/DS; no actual training/server/simulator action is authorized here.
