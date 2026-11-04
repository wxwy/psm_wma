# G2 Gate C S0 — Exact Episode Selection / Resource Budget Freeze — PASS

**Date:** 2026-11-04 16:56 CST (UTC+08:00).  
**Execution:** ChatGPT directly inspected the authorized DS server using Remote Desktop Commander. **Source-read-only S0 only; NO Gate C render/export.**  
**Formal production Root:** `3eb8b334150018212ae1f51afb5e954b83fa1186`  
**Child/Gitlink:** `1069fe78841228cadbbfbe6afbd767eaed6225da`  
**Handoff authority:** `docs/collab/codex/requests/2026-11-04_G2_GateC_S0_Exact_Selection_And_Budget_Readonly_Freeze.md` (`b1bd9e8c9bf3e3e11ab12690647b1d2074a05e39`).

## Verdict

**S0 PASS: the exact three-task proposal and server-side selection manifest are frozen, each full episode/source binding is nonvisually verified, and the real export CLI's full-episode `--dry-run` passes 3/3.** The candidate cache target was **not created**. This is NOT Gate C execution acceptance and does not authorize full export, N100, V3 promotion, training or GPU work.

## Code / source identity

- Reused clean isolated checkout: `/tmp/g2_spatial_v2_gpt_3eb8_20261104`; exact Root and Gitlink verified; `git status --porcelain` **0 lines** before and after S0.
- Flat source: `/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic`.
- Original RoboCasa source: `/mnt/data1/data_v2_0617/robocasa365_official/v1.0/target/atomic`.
- `flat_v3_mapping.parquet` SHA256: `aa884820494a17f50b41a8a8c2bfa6b6fda11babbbef31c449c1c0ce850e09ed`.
- Mapped corpus check: **9,126 episodes / 18 underlying task classes / 2,231,347 frames**.
- Script reused production `tools.g2.rgbd_pose.source.mapping_episodes` and `load_episode`. No new sampler, LeRobotDataset initialization, simulator, camera/Depth rendering or source writes. In all three, original states count == Flat mapped episode length, raw/Flat `observation.state` exact equal, both original RGB camera metadata H/W bound, one unique original source recording matched by the existing source loader.

## Exact frozen members (all full episodes)

| Underlying task class | Local ID | Flat global ID | Full frames | Original half-open row interval | Flat half-open row interval | Cameras / shape | Original recording directory |
|---|---:|---:|---:|---|---|---|---|
| CloseFridge | 0 | 502 | 429 | [0, 429) | [183099, 183528) | left+wrist, each256×256 | `CloseFridge/20250816/lerobot` |
| NavigateKitchen | 0 | 2022 | 177 | [0, 177) | [542111, 542288) | left+wrist, each256×256 | `NavigateKitchen/20250821/lerobot` |
| PickPlaceCounterToCabinet | 0 | 4038 | 246 | [0, 246) | [994452, 994698) | left+wrist, each256×256 | `PickPlaceCounterToCabinet/20250811/lerobot` |

Each original recording is under the original source root above. **Exact matching source dataset count =1** for each; source-state count == full `length` (429/177/246). These are a **bounded Gate C validation sample**, not an N100 membership declaration. Different manipulation/navigation conditions are deliberately represented.

## Frozen server-only artifacts

Evidence folder: `/tmp/g2_gate_c_s0_20261104_1655_cst/`.

| Artifact | SHA256 / status |
|---|---|
| `selection_manifest.json` | `10d668ee42b5145a8cad09878c331ef940b06d91a6a9666ae85434b61c225926` |
| `s0_source_budget.json` | `514c2b8f65c78b043ad5b83eacece654285fd56506489b456df968c14b707605` |
| `gate_c_plan.json` | `e73b5ec6efafb9554c662ed072d0e6f88741d8e7486b1fb412d201290d461564` |
| `gate_c_dryrun_exit.txt` | **0** |

Manifest uses `schema=psm_wma_rgbd_episode_selection_v1`, `episode_namespace=global_episode_index`, exact mapping SHA, and the three actual task/global-ID members. The manifest file **remains only on the DS server**; the public GitHub report includes identities/hashes and aggregate numbers, never raw Parquet/videos/NPZ/reversible data.

## Full-episode CLI dry-run (no renderer)

Production command: `python -m tools.g2.export_robocasa_rgbd_pose --raw-root <original> --flat-root <Flat> --output-root <new target> --selection-manifest <frozen manifest> --cameras robot0_agentview_left,robot0_eye_in_hand --state-index-policy frame_index --depth-format uint16_mm --chunk-frames 32 --dry-run`; run with clean formal checkout, `CUDA_VISIBLE_DEVICES=''`, `MUJOCO_GL=disable`, and one numeric thread per library.

- Exit **0**; `mode=dry_run`; `failed_episode_count=0`; `selected_episode_count=3`.
- All three `PLANNED_NONVISUAL_ALIGNMENT_VERIFIED`. Three underlying classes are unique, each planned frame count equals mapped **full length**, and no `--frames` was used.
- **852 total frames**, **1,704 camera-frames**, both cameras native `256×256`.
- `uncompressed_array_bytes_estimate=335313120` bytes (array-only, ~319.78 MiB), computed as `sum_{episode,camera}(length*(3*H*W+41*4+8))`.
- Proposed future output directory `/mnt/data1/data_v2_0617/g2_rgbd_pose/gpt_gate_c_candidate_s0_20261104` **does not exist after dry-run**, confirmed by independent `test ! -e` check. No cache/renderer/Depth output written and no training jobs changed.
- Note: the existing CLI's generic JSON `status=COMPLETED_EXPORT_NOT_PHYSICAL_GATE_ACCEPTANCE` under `mode=dry_run` does **not** assert any completed export; the mode and actual episode status are authoritative.

## Resource/budget freeze

Measured on `/mnt/data1` at approx **2026-11-04 08:56 UTC**:

| Resource | Value |
|---|---:|
| Filesystem free bytes | **137,937,985,536 B** (~128.46 GiB) |
| Host available memory | **1,691,043,225,600 B** (~1.54 TiB) |
| Uncompressed Depth+mask+K/Pose array estimate | **335,313,120 B** (~319.78 MiB) |
| Conservative proposed disk ceiling | **1,744,368,064 B** (~1.624 GiB) |
| Free-space margin over proposed ceiling | **136,193,617,472 B** |
| Actual compressed cache size | **UNKNOWN** pending Gate C; never extrapolated from the 3-frame test |
| Actual end-to-end full-episode wall-time / peak RSS | **UNKNOWN** pending Gate C |

Proposed execution limits for **a later separately authorized run**: **one CPU OSMesa process**, `CUDA_VISIBLE_DEVICES=''`, one thread each for OMP/OPENBLAS/MKL, **45-minute total wall-time ceiling**, `uint16_mm` + `chunk_frames=32`, preserved >=1GiB disk reserve. Do not touch other GPU jobs; do not switch to EGL/GPU; monitor local CPU RSS, elapsed time, and free space; stop and preserve artifacts on any data/integrity/error and do not automatically rerun. Historical DS ~28ms/frame with environment reuse is only a different-workload feasibility datapoint, **not** a new Gate C benchmark or promise.

## Next decision boundary

The above fixes the exact 3-member full-episode selection and resource proposal. **Gate C execution has not started**. The next authority decision may approve this precise bounded 3-episode plan. After approval it must run full cache export, full offline cache/frame integrity, independent first/middle/last native two-camera spatial checks, new scene-specific RGB–Depth visual review with provenance, restart/idempotency, and time/RSS/compression measurements; error/low coverage remains FAIL/INCONCLUSIVE. Do not infer the previous 6-frame Owner visual acceptance for these 3 new full episodes.

No N100 export, main V3 merge, nav_sg/Global PSS, training, DCP, model changes, or other production actions have been authorized or performed by this S0 work.
