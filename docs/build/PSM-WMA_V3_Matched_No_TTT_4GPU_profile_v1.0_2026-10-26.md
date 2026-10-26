# PSM-WMA V3 — Matched No-TTT world4/GA4 (CUDA 4,5,6,7)

Date: 2026-10-26. Implementation only; training/GPU/real-asset acceptance has not run.

## Scope

This is an **additional, isolated 4-GPU profile** for the existing Cosmos3-Edge-Policy-DROID, exact-window, cached-latent **No-TTT** baseline. It does not replace `scripts/train_v3_matched_no_ttt.sh` (world8/GA2), and it does not change G1 Local-TTT, its ongoing Resume, saved checkpoints, or evaluation runs.

| Setting | G1 world8 Local-TTT | No-TTT world8 | **No-TTT world4** |
|---|---:|---:|---:|
| Physical GPUs | 8 | 8 | **CUDA_VISIBLE_DEVICES=4,5,6,7** |
| nproc/world_size | 8 | 8 | **4** |
| B_stream | 8 | 8 | 8 |
| Consumer block T | 16 | 16 | 16 |
| GA | 2 | 2 | **4** |
| Valid consumers per local forward (full member) | 128 | 128 | 128 |
| Full global consumer budget/optimizer iteration | 2048 | 2048 | **2048** |
| Checkpoint schedule | max30000, warmup500, save100 | same | same |
| Local module / inner TTT / prefix | on | off | **off** |
| Raw data prefetch workers | subject to historical G1 settings | 0 | **0** |

The 4GPU variant preserves the nominal effective **global consumer count**, official DROID fresh initialization, raw15/state15/chunk16/camera/vision/outer-native loss, 7 Generation optimizer selectors and Action LR multiplier5. It **does not preserve the exact rank→episode assignment or per-step Consumer trace**, since `ExactWindowRankPlanner` partitions episodes by episode-hash modulo `world_size`. Do not describe 4GPU and G1 as fully same-sample/gradient matched. A strict same-seed, same-consumer intervention would require a separate virtual-rank plan, not introduced here. Four-way FSDP changes per-card parameter/optimizer memory; a real CUDA canary must verify that GPUs 4–7 fit.

## Dedicated launcher

`scripts/train_v3_matched_no_ttt_4gpu.sh {fresh|resume} EXECUTION_UNTIL`

The script exports `CUDA_VISIBLE_DEVICES=4,5,6,7`, starts 4 local processes, fixes `--world-size 4 --ga 4 --b 8 --t 16 --k 4 --num-workers 0`, `--max-iter 30000 --warmup 500 --save-iter 100`, and always adds `--no-ttt`. If a conflicting `CUDA_VISIBLE_DEVICES` was set, it fails before launching. Visible physical GPU indices 4,5,6,7 become local CUDA 0,1,2,3 inside torchrun.

A distinct `JOB_NAME` is required to end in `_world4_ga4` and begin with `no_ttt_`; default `no_ttt_packed128_droid_fresh_30k_world4_ga4`. Never use the G1 or world8 No-TTT job namespace. `OUTPUT_ROOT` must be an independent location with sufficient capacity.

For this **new 4GPU launcher only**, users do not need to export `EXPECTED_ROOT` or `EXPECTED_CHILD`: the launcher reads actual checked-out Git SHAs and passes them as the Trainer's expected values; the Trainer checks Root/Child/Gitlink and clean Child, and same-job No-TTT Resume still requires the **identical frozen source pair and config**. A later V3 HEAD change is *not* automatically compatible with a saved No-TTT job. Use a dedicated clean, fixed-commit checkout for Fresh and subsequent Resumes; do not update the active G1 checkout. Stale exported EXPECTED_* environment values are ignored for this launcher.

Required env: `OUTPUT_ROOT`, `SOURCE_ROOT`, `CACHE_ROOT`, `DATASET_INDEX_ROOT`, `EDGE_POLICY_CHECKPOINT`, `WAN_VAE_PATH`, `BASE_CHECKPOINT_PATH`. `PYTHON` optionally selects the actual training venv.

Example with those pre-exported environment paths:

```bash
cd /absolute/path/to/independent_clean_no_ttt_4gpu_checkout
export JOB_NAME=no_ttt_packed128_droid_fresh_30k_world4_ga4

# The stage budgets do not change max_iter30000/warmup500/save100.
bash scripts/train_v3_matched_no_ttt_4gpu.sh fresh 100
bash scripts/train_v3_matched_no_ttt_4gpu.sh resume 500

# After actual GPU/real DCP Save→Resume acceptance and Owner authorization:
bash scripts/train_v3_matched_no_ttt_4gpu.sh resume 30000
```

Do not execute the second command until the preceding stage successfully wrote its complete checkpoint. The command with `resume 30000` means total iteration 30000, not +30000. For the first real launch, check current GPU occupancy, root/child workspace lock, dataset/Verified Index receipts, disk and DROID initialization; no training has been run by this code change.

## Inference and Resume

- `scripts/serve_v3_matched_no_ttt.py` now explicitly accepts exactly `(world_size,ga)=(8,2)` or `(4,4)` from the saved No-TTT semantic identity; for either, its saved YAML must agree on FSDP shard degree, replicate degree1 and GA, in addition to raw15/state15/H16/left_wrist/Local off/Generation-only. The CLI remains the same as the standalone off-mode example.
- The No-TTT Frontier uses actual `world_size`, `GA` and `iteration`; 4GPU resumes require all four rank dataloader files and the same source and config digests. Cross-world-size Resume is forbidden; never restore G1 or 8GPU No-TTT checkpoints into a 4GPU job.
- A 4GPU training identity does not imply the existing required-TTT Unified RoboCasa Queue can run it. Off-mode server/client and matched task protocol still require a separate evaluation Gate.

## Required follow-up evidence

1. Independent CPU: 8GPU old-profile regression and new 4GPU profile admission/rejection; four-rank GA4 planner batch count and saved semantic identity; launcher fake-Python argv/env; 4GPU off-inference profile and mismatch negatives.
2. Real-input S0: accepted DROID/Edge/VAE/Verified Index/cache/source witnesses, real action/state/vision masks, observed rank partition. Match **dataset and nominal global batch** to G1; explicitly document distinct rank/Consumer sequence.
3. Owner-authorized world4 CUDA canary on physical GPU4–7: model load, FSDP allocations, output/gradients finite for all Generation groups, no Local graph, valid consumer counts and memory headroom.
4. Owner-authorized Fresh100→Resume101/500 strict full DCP+optimizer+scheduler+per-rank RNG/frontier continuity, then formal30k. No real checkpoint/simulation/GPU action is implied by this source commit.
