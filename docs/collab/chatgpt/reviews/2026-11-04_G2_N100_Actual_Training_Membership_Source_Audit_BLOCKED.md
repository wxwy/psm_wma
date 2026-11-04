# G2 N=100 — actual training membership audit & production budget preparation

**Date:** 2026-11-04, 21:20 CST.  
**Verdict:** **SOURCE_LINEAGE_AUDIT_PASS / N100_EXACT_MEMBERSHIP_BLOCKED / N100_DRY_RUN_NOT_EXECUTED**.  
This is a read-only metadata intake and conservative budget assessment, **not** an N100 selection, export authorization, or a replay/rendering run. No source, cache, training job, checkpoint, V3 branch or prior Gate B/C artifacts were modified.

## Authority / identifiers

- User/Codex request: [G2 N100 Actual Training Membership and Production Budget Preparation](https://github.com/wxwy/psm_wma/blob/ffe931360998cd39b7587a883681fe6b0e25e65b/docs/collab/codex/requests/2026-11-04_G2_N100_Actual_Training_Membership_And_Production_Budget_Preparation.md).
- Approved G2 Stage-1 source: Root **3eb8b334150018212ae1f51afb5e954b83fa1186**, Child/Gitlink **1069fe78841228cadbbfbe6afbd767eaed6225da**, checked clean. Gate C final PASS is separate and remains closed.
- Flat V3 mapping: `/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic/flat_v3_mapping.parquet` SHA256 **aa884820494a17f50b41a8a8c2bfa6b6fda11babbbef31c449c1c0ce850e09ed**, matches Gate C.
- Source dataset bound in the job lineage: `/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic`.
- **Actual identifiable historical training job:** No-TTT corrected Phase5 **no_ttt_packed128_droid_fresh_30k_world4_ga4**, 30k; prior training code Root **215305ecb9ab9631af44cbb3469bc4179dd4aeab**, Child **a4bc0c728b57ee8aaf49f951f6aed1a17b986573**. These historical training commits must not be confused with today's G2 source pair.
- Its `v3_job_identity.json` SHA256 **3842d93c66bc4d90b9ce1e4b6ef3e114290158f1b1e30983d05b05e144b5e679**; independently parsed the job's authoritative `source_paths`, cache/receipt SHA and source-binding digest, not merely a similarly named directory.
- Formal Local-TTT `formal_verified_index_30k/config.yaml` and matched No-TTT config were also inspected. Both declare **18 task classes**, `camera_set=left_wrist`, `split=train`, `split_val_ratio=0.01`, `split_seed=42`. These YAML settings do **not** themselves prove that any N=100 ID subset was used.

## Hash-bound actual G0 cache / verified index

1. G0 exact-window manifest: `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-left_wrist-exact_window/dataset_manifest.json`
   SHA256 **8e63c73b4e07cdbebd6427d9efdd3f2d8b293ecd10511cae25a55c6566f6db88**.
2. Verified index: `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-verified-index-r1/receipt.json`
   SHA256 **247e5a853cbc2ddd007cb4b243b492f8337179276fade9b191f6bb4fe0d5798c**.
3. No-TTT job identity explicitly records **exactly those two hashes** and `source_binding_digest=f91b0b477a048beb439f1d73e7414f6b1d2a0307eee54c858d6cd8503ea19020`; index has the same digest and manifest hash.
4. Reused production `tools.g2.rgbd_pose.source.selected_episodes`, `verify_selection_source` and `mapping_episodes`, not a new sampler. **9,126 accepted** `(task_class, global_episode_index)` pairs match **9,126 verified-index bindings** and **9,126 Flat mapping entries**, with matching frame counts, half-open row ranges and task membership.
5. Crucially the cache manifest has `episode_limit_per_task_class=null`, and each task's `selected_episode_ids` equals its **entire** `episodes[]` accepted list. Thus **this is an unbounded/full G0 cache, NOT an N=100 cohort**. It records **2,085,331 exact windows** across **2,231,347 full raw frames**.
6. Both original RGB camera metadata shapes for all **18** raw task directories are **[256,256,3]**, and each task has one dated official source directory (metadata-level audit only). This makes the two-camera full-corpus **planning estimate** below grounded. It does not assert every individual episode was re-rendered.

## Per-task accepted G0 full-corpus totals (NOT N=100 effective train IDs)

| Underlying task | G0 accepted episodes | Sum of full frames |
|---|---:|---:|
| CloseBlenderLid | 502 | 183,099 |
| CloseFridge | 513 | 155,443 |
| CloseToasterOvenDoor | 505 | 86,401 |
| CoffeeSetupMug | 502 | 117,168 |
| NavigateKitchen | 500 | 72,786 |
| OpenCabinet | 500 | 184,024 |
| OpenDrawer | 514 | 137,431 |
| OpenStandMixerHead | 502 | 58,100 |
| PickPlaceCounterToCabinet | 502 | 131,904 |
| PickPlaceCounterToStove | 501 | 129,560 |
| PickPlaceDrawerToCounter | 501 | 155,749 |
| PickPlaceSinkToCounter | 501 | 194,952 |
| PickPlaceToasterToCounter | 512 | 148,353 |
| SlideDishwasherRack | 502 | 83,544 |
| TurnOffStove | 500 | 114,027 |
| TurnOnElectricKettle | 520 | 84,679 |
| TurnOnMicrowave | 543 | 80,439 |
| TurnOnSinkFaucet | 506 | 113,688 |
| **Total** | **9,126** | **2,231,347** |

**Important distinction:** "cache selected" = "G0 accepted" = 9,126 for *this* full cache. The **effective training episode membership** is **not independently frozen to this list**: saved formal No-TTT/Local-TTT training configs specify `split=train`, `split_val_ratio=0.01`; the verified-index receipt enumerates full accepted corpus, not a separate per-ID effective train split or an N100 cap. Do not silently recompute `torch.randperm`/seed42 or assert that a theoretical train/val split equals an original N100 receipt. A different historical N100 training ID manifest was **not found among these job-bound, authoritative cache/index artifacts**. This is an evidence-scoped finding, not a claim to have searched every historical filesystem archive.

## Server-only preparation evidence

- Runner: `/tmp/g2_n100_actual_training_intake_20261104.py` SHA256 **37bb37919cd0a850828b206e0900007a632e8df0663389fd115d92ba7f528959**; shell wrapper SHA256 **1233b95e568478e75f4052bf4f295031eecf1e037e6a6b66ce93f27ba29efd51**. Python and Bash syntax validated. A single bounded metadata runner executed under the requested shared `timeout --signal=TERM --kill-after=15s 1785s` CPU-only contract and completed safely, without renderer/model/DCP. Earlier targeted read-only discovery did not alter data.
- Evidence JSON: `/tmp/g2_n100_actual_training_lineage_audit_20261104/source_lineage_budget_blocked.json`; SHA256 **e678f9cf935438fe9d76a34d6c8422f6358b41db91e27692717a3759168509c3**.
- Separate per-task aggregate file: `/tmp/g2_n100_actual_training_lineage_audit_20261104/per_task_full_cache_summary.json`.
- The actual N=100 selection manifest, selection SHA, effective E/F, actual dry-run plan and batch budget are recorded as **UNKNOWN/BLOCKED** — no substitute 9,126-member selection manifest was written.
- Proposed future output `/mnt/data1/data_v2_0617/g2_rgbd_pose/gpt_n100_training_cohort_proposal_20261104` did not exist before/after. **No N100 or 9,126 full-corpus cache was generated, no dry-run was invoked**, and no old 3-episode Gate C data was touched.

## Capacity and empirical reference — FULL 9,126 CORPUS scenario ONLY

At **2026-11-04 13:20 UTC** (server) on `/mnt/data1`:

| Resource / scenario | Grounded value |
|---|---:|
| Free disk | **137,476,116,480 B** (~128 GiB) |
| Free inodes | **157,346,873** |
| Host MemAvailable | **1,788,394,827,776 B** |
| Two original cameras | each **256×256** for all 18 task classes |
| **Full cache 9,126 episodes / 2,231,347 frames** | **NOT the N100 request** |
| Full raw Depth+mask+K/Pose array bytes, `R=393560×F` | **878,168,925,320 B** (~818 GiB) |
| Empirical *compressed payload proxy* `R/7.2099` | **121,800,430,702 B** (~113.4 GiB), NOT a capacity guarantee |
| Empirical *successful export time proxy* `F×220.50/852` | **~577,479 seconds (~6.68 days)**, excludes changed task mix/runtime/overhead |
| Conservative *full-corpus* staging+reserve `2R+1 GiB` | **1,757,411,592,464 B** (~1.60 TiB) > current free |
| Actual N100 E/F/camera-frames, disk quota/deadline | **UNKNOWN: member IDs not established** |

**Conclusion:** even the full corpus's optimistic compression proxy would leave little disk margin, and the conservative raw-buffer-based budget exceeds capacity by over an order of magnitude. **Do not run all 9,126 just because the current cache is complete.** Conversely, do not manufacture an N100 cohort or extrapolate 9,126's size to N100 as an actual measured count.

## Required decision before an N100 dry-run or production plan

**BLOCKED_ACTUAL_N100_TRAINING_MEMBERSHIP**:
- Obtain the historical **N100 actual selected/accepted/effective episode-ID receipt** tied to the *specific intended training job*, including relevant task filters/window/train split, and reconcile with the hash-bound full cache and verified-index source.
- If no such historical N100 receipt was created, a **new explicitly approved cohort** may be proposed from real Flat IDs, but must be labelled a **newly defined subset**, not retroactively "actual training membership". The present instructions prohibit re-running the historical seed sampler.
- Only after source/member identity is established, freeze a new exact `psm_wma_rgbd_episode_selection_v1` global-ID manifest and SHA on the server, run the approved **non-rendering `--dry-run`**, compute **actual** member E/F and the R budget, and propose a separate explicit N100 single-CPU-OSMesa deadline/disk/RSS/stop plan.
- Status to Codex: SOURCE AUDIT PASS; TRAINING FULL-CACHE MEMBERSHIP VERIFIED; N100 effective cohort **BLOCKED**; N100 dry-run **NOT EXECUTED**; N100 export **NOT STARTED**; V3 code/Child unchanged. No new Code Gate or repetition of the already closed Gate C.

This report is text-only. Raw training manifest, verified index, camera images, depth, NPZ, DCP and runner files remain only on the authorized server.