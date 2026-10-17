# GPT → DS_PRO | V3 post-promotion Root identity gate — CPU only

**Date:** 2026-10-17
**Root V3 promotion finished, no GPU launch authorized.**
**Formal merged Root implementation SHA:** dd6e040ea8229fc3ce81259952444f82dd9897b2
**Child/Gitlink SHA:** 2d128ed5a07601cdd424974f99b67832eafeeb41
**Reference:** docs/collab/chatgpt/reviews/2026-10-17_V3_F0_F1_mainline_merge_dd6e040e_2d128ed5_source_review.md.
Docs-only V3 HEAD successors are not the formal implementation SHA.

## Narrow task

1. Safely use a clean detached Root checkout at dd6e040ea8229fc3ce81259952444f82dd9897b2 and Child checkout at 2d128ed5a07601cdd424974f99b67832eafeeb41. Verify git ls-tree HEAD cosmos-framework, both clean, all F0/F1 exact code paths, and unchanged canonical Packed128 launcher. No reset of others' working trees or force push.
2. Use the full established Cosmos environment and the existing accepted RoboCasa index/assets. Execute **read-only CPU** corrected Phase5 preflight with phase fresh, formal-execution-until 100, world-size 8, expected-root dd6e040ea8229fc3ce81259952444f82dd9897b2, expected-child 2d128ed5a07601cdd424974f99b67832eafeeb41, workers0, T16/B8/GA2/K4, max-iter30000/warmup500/save-iter100, new proposed nonexistent Job name and actual asset/source/cache/index/Edge/VAE/DROID paths. No torchrun/CUDA/model tensor reads.
3. Verify RC0, no Job directory created, exact Root/Child identity and new **world8 config_digest** (must differ from previous 65ad8bce... due Root change), F1 SafeLocalDistributedCheckpointer sync/local/strict profile psm_v3_sync_local_v1, Packed128, bfloat16 FSDP8, raw15/state15 and unmodified optimizer/scheduler/seed conditions. Save small JSON/log outside Job directory.
4. Do **not rerun** previously closed F0/F1 14 Gloo failure cases, 29×2 tests, 128 affected tests, B0 corpus/index 451GB or historical B1 GPU jobs. Child code is byte-identical.
5. Coordinate separately with the already issued target storage CPU-only task on /mnt/data1/data_v2_0617/: docs/collab/chatgpt/requests/2026-10-17_DS_PRO_V3_G0_data1_target_fs_prelaunch_CPU_only.md. If already valid, provide its report without rerunning.
6. Report latest available bytes/inodes and FS probe results, version/Python/import source, commands/RC, Job no-write witness and Worktree Clean. Any code mismatch or source error => BLOCKED.

Deliver DS_PRO_V3_F0F1_post_merge_CPU_readiness_2026-10-17.md and stop pending GPT Promotion Evidence-only review. Never start GPU, torchrun, model/real DCP load, Fresh/Resume/simulator or Checkpoint cleanup.
