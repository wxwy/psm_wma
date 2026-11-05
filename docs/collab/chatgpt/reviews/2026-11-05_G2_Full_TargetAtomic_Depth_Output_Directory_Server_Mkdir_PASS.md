# G2 Stage-1 — Authorized Depth output directory: server mkdir PASS

Date: 2026-11-05 (Asia/Shanghai), server observation `2026-11-05T02:25:15Z`.

**Outcome: PASS — the Owner-selected, ordinary empty sibling directory has been physically created on the authorized server.** This is only filesystem preparation, **not** an approval or start of Depth generation, and it does not create a G2 cache manifest or episode artifacts.

## Authority and exact path

- The Owner's exact directory decision and empty-directory creation authorization are recorded in commit [`e5479c8ebbe8bc45d77c2c130bfe8bd93d0169ba`](https://github.com/wxwy/psm_wma/commit/e5479c8ebbe8bc45d77c2c130bfe8bd93d0169ba), `MEMORY/DECISIONS.md` and `docs/collab/codex/requests/2026-11-04_G2_Full_TargetAtomic_Batched_Depth_Pose_Storage_And_Production_Plan.md`.
- Selected output root: `/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-depth`.
- Input Flat root: `/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic`.
- Original RoboCasa raw root: `/mnt/data1/data_v2_0617/robocasa365_official/v1.0/target/atomic`.
- Formal G2 production source Root `3eb8b334150018212ae1f51afb5e954b83fa1186` / Child-Gitlink `1069fe78841228cadbbfbe6afbd767eaed6225da` unchanged. G2 Gate C remains closed PASS.
- This output is for only the two previously approved cameras: `robot0_agentview_left` and `robot0_eye_in_hand`, with `uint16_mm` Depth+valid/K/Pose per 32-frame NPZ chunk when production is separately authorized; `robot0_agentview_right` remains out of scope.

## Independent real-server preflight and action

The authorized Desktop Commander device `data` was online. Before creation, the execution verified:
1. Parent, Flat source and original raw source all exist as real directories; parent is writable.
2. The exact target did **not** already exist. No file/symlink or existing cache was replaced.
3. Canonical resolved parent `/mnt/data1/data_v2_0617/robocasa365_v3_flat` and target `.../robocasa365-target-atomic-depth` are siblings, not ancestors or descendants of the Flat source or original raw source.
4. The target shares the `/mnt/data1` device with Flat source, as expected, without modifying the source.
5. Executed exactly `mkdir -- /mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-depth` (**no** `-p`), followed by checks that the target is a directory, **not** a symlink, and has **zero** children.

**Verified directory metadata:** `type=directory`, `mode=775`, `uid=1004`, `gid=1004`, device `66307`; canonical `readlink -f` equals the intended output path.

## Current disk capacity snapshot

Filesystem `/mnt/data1`, as reported by `df -B1 --output=target,avail`:
- Free bytes immediately **before** mkdir: **293,427,752,960 B**.
- Free bytes immediately **after** mkdir: **293,427,748,864 B** (single directory allocation).
- Available inodes before creation: **157,347,363**.

These are new server-observed values, **not** the older ~137 GB snapshot from 2026-11-04. Available space may change due to other workloads. The earlier measured Gate C compression proxy gives ~125 GB baseline or ~149 GB with 20% extra compressed payload, but these are **not** hard bounds. This new free-space headroom makes staged production more feasible but does not automatically authorize all 92 batches or establish a production stop/reserve policy.

## Next boundary

**DONE:** Server-local directory creation and canonical path/existence/emptiness check.

**NOT STARTED / NOT AUTHORIZED HERE:** any first-batch or full 92-batch rendering/export, changing `cache_manifest.json`, producing Depth/NPZ or source RGB, cleanup/migration, merging V3, nav_sg conversion, GPU/EGL or training/DCP operations.

Before actual production, independently approve a bounded first-batch execution with this exact new directory, previously frozen batch membership, one CPU/OSMesa process, current space/RSS/time limits and a minimum free-space reserve. The actual output directory is **empty** as of this proof, not an export-complete cache.

Server source data, all sensor payloads and any raw verification artifacts remained on the authorized server. This is a documentation-only closure record for the previously authorized `mkdir`.
