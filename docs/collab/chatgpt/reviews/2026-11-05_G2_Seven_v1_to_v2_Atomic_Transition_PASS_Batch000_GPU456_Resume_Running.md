# G2 — Actual v1→v2 version transition PASS; frozen Batch000 GPU4/5/6 resume RUNNING

Date: 2026-11-05 CST. Owner instruction: execute the next approved G2 migration and Batch000 continuation. This is a **real connected-server execution report**, not just a proposal. This report has no raw sensor data, PNG or code changes.

## Authority and source boundaries

- Previously code-approved implementation Root `5e6903b9dd09828f725dc61dcd6e98012fae87b3` / Child-Gitlink `1069fe78841228cadbbfbe6afbd767eaed6225da`. The reviewed code was checked out clean in isolated server worktree `/tmp/g2_issue19_f1_independent_5e6903_20261105`; no unapproved source edits.
- Production output is the Owner's exact path `/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-depth`.
- Cameras ONLY `robot0_agentview_left,robot0_eye_in_hand`, 256×256, `uint16_mm` with encoded zero sentinel, 32 frames/chunk, no persisted `valid` array.
- Frozen Batch000 identity SHA256 `8561c81b0382bf79d360f5028d6fa67ab2848589bf77199f9d3f97861e760080`: exactly 100 distinct source episodes, 24,059 full source frames from complete 9,126-source lineage. No sampling change.

## Real seven-episode v1→v2 generation and atomic transition — PASS

1. A connected server audit read, verified and hashed every file of the legacy production v1 root, including 7 fully committed episodes, 2,353 frames, 214 files, and preserved `.failed/` and `.staging/` artifacts. Original root manifest schema: `psm_wma_robocasa_rgbd_pose_v1`.
2. Rather than deleting `valid` from legacy NPZ and inventing renderer-source diagnostics, the exact reviewed v2 code **re-rendered only those seven full episodes** into a **new sibling staging directory** using GPU4/5/6. Each new episode passed v2 cache integrity, source/frame/RGB-index binding, schema and metadata validation.
3. An independent numeric comparison between old v1 and newly rendered v2 checked **308,412,416 camera-depth pixels**: **0 different uint16 values, 0 validity mismatches, 0 matrix differences, 0 frame/source identity differences**. Seven episodes/2,353 frames identical; no new screenshot or RGB duplicate. Staging comparison report SHA256: `46ad74d7ce2e24e26a4d0e9f3dfee2a6435cf4591f39db7ab54ccf2c7d3fc8b4`.
4. Linux `renameat2(RENAME_EXCHANGE)` was smoke-tested in the same data1 filesystem, then used for an **atomic exchange of the old production root with the fully verified staged v2 generation**. The old generation was subsequently renamed (not deleted) to the permanent rollback sibling path. Parent directory fsyncs were performed. Output root now v2; old root preserved v1, neither overwritten nor modified.
5. A non-data error occurred **after successful atomic exchange and archive rename**: the final-report script referenced an unbound local name `v2`. Execution stopped with nonzero exit, but both paths and all existing artifacts remained correct. **The atomic exchange was NOT retried**. A separate read-only final auditor verified both manifests, 214 archived v1 hashes, all 7 v2 completed episodes and 2,353 frames, then recorded the success receipt. This was a reporting bug, not a migration failure.
6. Final server report `/tmp/g2_issue19_v1_to_v2_20261105/atomic_exchange_final.json`, SHA256 `4535f4680552720c989f0e67be105d937fb91ca6870df987d5e546e05869f1c1`; old inventory SHA256 `62370d1f7edfc165566602b477f821ae04bdf0166e7f3a7b5696a9f03c375dc0`.
7. Exact current manifest hashes:
   - Official v2 root `cache_manifest.json`: `3a8fbae3187fe0d5bbb8b67e5ef8fad3105f247936fd47bfa214fa2e6842f2b4`.
   - Archived v1 root `cache_manifest.json`: `b753814a7234a7ba3f8fdb65a0c0c148afb9015a1aabb570fe6e5fa49f696594`.
8. Permanent v1 rollback (DO NOT DELETE): `/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-depth-v1-rollback-20261105`. It holds all seven original v1 caches plus prior failures/staging, original proofs and provenance.

This used the exact approved code and ephemeral server-side scripts, never copied source RGB/Depth away from the connected machine.

## Batch000 v2 production resume — IN PROGRESS

- Started 2026-11-05T07:30:14Z, in tmux `psm_g2_batch000_v2_gpu456_20261105`; runner `/tmp/g2_batch000_v2_gpu456_resume_runner_20261105.py`, SHA256 `790289c25cbfd0b3a156028ef2e61e59e03a86154fbcbd7359210177833529ab`.
- New v2 root was preflight-verified. All original **7/7** completed episodes were recognized by the v2 exporter as **`SKIPPED_VERIFIED`**; they were not regenerated again.
- The previously failing real `CloseFridge` global736/local234 **full 230-frame episode** is now `EXPORTED` with strict v2 cache integrity PASS on GPU6. Its Wrist camera records **12,658** pixels beyond65.535m across the whole episode, written as zero with compact diagnostics; **12** frames warn for >1% excluded pixels. This is expected storage-range filtering for far floor, not an assertion of zero physical distance. The sample native geometry check for frames73/74 was previously PASS.
- A live snapshot at 2026-11-05T07:32:19Z reported **19/100 episodes**, **5,250/24,059 source frames**, compressed NPZ payload ~**0.262 GB**, and free space ~**292.3 GB**. This is a historical mid-run snapshot; the job may advance. 
- All three GPU IDs **4/5/6 only**; GPU7 and GPU0–3 untouched by this producer. No 25 GiB total-size limit or four-hour global runtime deadline. Per-episode checks, strict stop-on-error, 100 GiB minimum free disk, and server telemetry/monitor refresh are enabled. A planned 10-minute server heartbeat is recorded in `/tmp/g2_batch000_v2_gpu456_resume_20261105/events.jsonl`.
- Current monitor: `/tmp/g2_batch000_v2_gpu456_resume_20261105/monitor_status.json`. CLI/event log: `/tmp/g2_batch000_v2_gpu456_resume_20261105.log`. Final report to appear at `/tmp/g2_batch000_v2_gpu456_resume_20261105/final_batch000.json` if and only if 100 episodes/24,059 frames complete. 
- No automatic progression to Batch001…Batch091. Do not claim Batch000 PASS before final receipt. If failure, inspect log and preserve committed caches/failed staging before a separately approved retry.
- A separate scheduled follow-up will check the job result, without giving an authorization to modify or restart it.

**No V3/V2 branch merge, Child update, nav_sg integration, old-cache cleanup or unsupported data transfer occurred in this execution.**
