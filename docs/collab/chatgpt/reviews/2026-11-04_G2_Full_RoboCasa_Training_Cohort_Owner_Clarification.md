# G2 Stage-1 — Owner correction: Local-TTT and No-TTT use full RoboCasa target-atomic

Date: 2026-11-04. Owner's explicit clarification in the PSM-WMA project conversation:

> local ttt和nottt都是全量RoboCasa target-atomic 数据

**Decision:** Local-TTT and No-TTT are both trained against the **full RoboCasa365 v3 target-atomic dataset lineage**, not a historically frozen N=100 subset. This resolves the mistaken *requirement* to locate a historical N100 training-membership manifest before G2 Stage-1 Depth production planning. Do **not** erase or rewrite the previous read-only N100 audit; its observation that the G0 exact-window cache contains 9,126 episodes and no N100 cap remains correct.

## Verified lineage facts

- Full source mapping: 18 underlying task classes, **9,126 episodes**, **2,231,347 full frames**. Mapping SHA256 `aa884820494a17f50b41a8a8c2bfa6b6fda11babbbef31c449c1c0ce850e09ed`.
- G0 exact-window cache manifest `dataset_manifest.json`: **9,126 selected = 9,126 accepted**; `episode_limit_per_task_class=null` and **2,085,331 windows**. Manifest SHA256 `8e63c73b4e07cdbebd6427d9efdd3f2d8b293ecd10511cae25a55c6566f6db88`.
- Verified index `receipt.json`: 9,126 bindings matching all G0 accepted and Flat mapping members. SHA256 `247e5a853cbc2ddd007cb4b243b492f8337179276fade9b191f6bb4fe0d5798c`.
- Saved Local-TTT `formal_verified_index_30k/config.yaml` and No-TTT `no_ttt_packed128_droid_fresh_30k_world4_ga4/config.yaml` both point to **all 18 task classes** under the Flat target-atomic source and specify `split=train`, `split_seed=42`, `split_val_ratio=0.01`. **Important nuance:** "full dataset" describes source and no N100 cap. The effective `train` partition can exclude the configured validation split; the verified index includes both partitions. Do not describe every one of the 9,126 as definitely consumed by the `train` dataloader without a consumer split record.
- No-TTT run's job identity independently binds the exact cache manifest and verified-index SHA256. The previous audit's inability to find a distinct historical N100 effective training receipt is not a defect: **such a receipt is not a prerequisite because N100 was not used as the training cohort**.

## Corrected G2 production scope

The true dataset lineage for Depth/Pose is **full target-atomic**, with incremental/batched offline production to manage resources. "N=100" (if retained) is only a **new Stage-1 production batch/canary size**, **not** a historical Local-TTT or No-TTT membership. Do not retroactively label any newly selected 100 episodes (total/per task still undecided) as training-selected members.

- **Next action**: design a bounded staging scheme for full-corpus RGB-D/Pose recovery, including exact global IDs per incremental batch, explicit selection basis, immutable per-batch manifest/SHA, validated source mapping and the existing G2 `uint16_mm`/chunk32 output.
- First obtain a **real storage/throughput plan**. Full corpus array-only raw Depth/mask/K/Pose estimate is **878,168,925,320 bytes (~818 GiB)** for two 256x256 cameras. Gate C's compression ratio gives an **empirical-only** payload proxy of ~121.8 GB and time proxy of ~6.68 days for a single worker; neither is a capacity promise. Data disk available at the previous read-only audit was ~137.5 GB. Conservative full-corpus 2×raw + 1GiB budget is ~1.757 TB, far above current free disk. **Do not launch full-corpus export into the current disk blindly**.
- Make disk placement, bounded staging/batch size, resume/skip, existing asset preservation and per-batch verification explicit. If desired, use a small first production subset for validation before scaling; its selection policy requires a new explicit decision and must not be falsely attributed to historical N100 training membership.
- Existing G2 Gate C remains **FINAL PASS** for 3 full episodes / 18 native geometry samples and Owner-reviewed RGB–Depth alignment. Do not repeat it, modify its artifacts, or reinterpret it as full-corpus proof.

## What is now resolved vs pending

**RESOLVED:** historical N100 training subset lookup no longer needed; both training tracks are full-source RoboCasa target-atomic.  
**PENDING:** production staging cohort policy, storage space/placement, hard runtime/resource budgets, and explicit export execution authorization.  
**NOT STARTED:** full-corpus or N100-batch Depth export, merge into V3, nav_sg conversion, training/GPU job.

This addendum is documentation-only and does not modify any old report, code, Child/Gitlink, V3 branch or server sensor data.