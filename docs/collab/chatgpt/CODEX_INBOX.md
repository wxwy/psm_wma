# Canonical Codex Inbox — live ledger (post-2026-10-29 rollover)

Previous immutable archive: `docs/collab/chatgpt/archive/CODEX_INBOX_20261029_ISSUE9_GPT_d222c80.md`; exact original live Git blob `2bbc34d51cfa8328ff2a6550dec090b2262cd7da`, 133589 UTF-8 bytes, byte-for-byte preserved in Git history. Pre-rollover V3 HEAD `d222c80673e4a621f8f42d97afb5742c8b5f9f80`. Before this rollover the live Inbox exceeded the 128KiB hard limit; this is the single permitted rollover exception, not a general rewrite. Older archives and all prior Gate entries remain in this exact archive.

## Active/latest Gate pointers (carry-over)

- **Issue #9 No-TTT Async overlap new Formal Pair:** Root `e0fe911dfb9fd34957234828195cf051713f6c3d` / Child+Gitlink `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`; GPT **`APPROVE_CODE` (source + author synthetic CPU only)**; detailed final Review `docs/collab/chatgpt/reviews/2026-10-29_V3_NoTTT_AsyncOverlap_e0fe911d_f6a92d47_Incremental_Code_Gate_APPROVE_CODE.md`; DS_PRO independent301 CPU **PENDING**. Historical strict Compact GPU gradient `FAIL_PARITY`, Compact attribution `INCONCLUSIVE`; production GPU performance/real DCP Resume **NOT_RUN**. Existing original No-TTT Job continues independently; no candidate V3/Child promotion.
- **EvalV2 Phase B B2 test-only Formal Pair:** Root `c724cb8b1ac74c8b1748bdaac95450fb0635a095` / Child `774c2edb93ec5a6ba85ba1124757064d7cc779a5`; GPT test-only `APPROVE_CODE`; DS independent CPU evidence pending, prior B2 DS run Gate was RED/REQUEST_CHANGES. Detailed prior Review `docs/collab/chatgpt/reviews/2026-10-29_V3_EvalV2_B2_CpuFixture_c724cb8b_774c2edb_TestOnly_Incremental_Code_Gate_APPROVE_CODE.md`.
- **No-TTT older notes:** Owner final Job is `no_ttt_packed128_droid_fresh_30k_world4_ga4` (was reported iter7600+); independent Compact Fresh10/ nw0 PASS does not authorize its own 30k; historical strict GPU gradient FAIL preserved. DS current-job readonly baseline separate Issue #10. Other unresolved historical entries remain in archive; references not overwritten.

## 2026-10-29 — GPT Issue #9 Async Source/Transform Code Gate APPROVE_CODE

- Formal Root `e0fe911dfb9fd34957234828195cf051713f6c3d`; Child+Gitlink `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`; author Evidence/Handoff head `c645d3d6452f6817a888c5b3e429b3f6b143762e` bookkeeping only.
- **GPT formal verdict = `APPROVE_CODE` only for isolated production source + author CPU evidence**, full Review `docs/collab/chatgpt/reviews/2026-10-29_V3_NoTTT_AsyncOverlap_e0fe911d_f6a92d47_Incremental_Code_Gate_APPROVE_CODE.md`. Independently matched 18/18 Git Blobs; read author raw JUnit 301(72+229)/0fail/error/skip/one real-data deselect; independently recomputed fake compute Source/Transform next-Member and next-Window time intersections. CPU cold async7.761s vs serial3.315s, **no GPU throughput claim**.
- No confirmed code-level blocking contract violation. Frozen nw0 semantics, parent ordered CFG RNG, speculative candidate frontier, DCP schema, bounded worker cleanup checked. Real processor/dataset, native CUDA/DCP, real worker8 RAM/performance remain deferred Gates.
- NEXT: DS independent synthetic CPU301 `docs/collab/chatgpt/requests/2026-10-29_V3_NoTTT_AsyncOverlap_DS_PRO_Independent_CPU_ExactPair.md` in clean exact-pair isolated worktree. No merge V3, no active Job stop/Resume, no GPUs, no real RoboCasa/DCP, no training changes. Any new formal code SHA requires fresh Code Gate.

## 2026-10-29 — EvalV2 B2 c724cb8b/774c2edb DS 426 CPU F3生产竞态：REQUEST_CHANGES

- **Formal source Pair 未变** Root `c724cb8b1ac74c8b1748bdaac95450fb0635a095`, Child+Gitlink `774c2edb93ec5a6ba85ba1124757064d7cc779a5`；GPT是增量审查新DS运行Evidence及对应实际源码，不重审已批生产Code/test-only方案。
- **DS独立CPU shell exit1, gate FAIL**；据DS现场报告 inference145/145 + PhaseA255/255 + PhaseB25/26 = **425 PASS /1 FAIL**；F1端口负例及F2三种OS拓扑均过（G1/N2/E2真B2证据），F3双Slot活跃后Server exit23暴露生产异常。GPT未直接读取DS原始服务器JUnit/日志。
- **Finding F3-P1 HIGH（Child production）**：`cosmos_framework/evaluation/robocasa_v2/store.py:49-57` exists检查→递归parent→裸`path.mkdir()`，工作线程`finish_invalid`与主协调器`coordinator_stop`并发记同Task fault → race `FileExistsError`，使原始故障报告被遮蔽。此为既有生产缺陷**首次被真实CPU F3确定性故障用例揭示**，不是测试变更造成。详细正式 Review `docs/collab/chatgpt/reviews/2026-10-29_V3_EvalV2_PhaseB_B2_DS_CPU_F3_Store_Mkdir_TOCTOU_Production_Blocker.md`。
- **Formal DS Evidence verdict=`REQUEST_CHANGES`，生产阻断HIGH**；之前`APPROVE_CODE`仍可追溯但不等于本次独立CPU验收通过。
- **最小整改建议给Codex**：隔离候选只动Child Store`mkdir`目录并发容忍及必要确定性回归；保留 symlink/file拒绝、`safe()`/parent fsync、每次UUID独立故障记录和 F3 Server退出23/两Slot/owned cleanup/foreign isolation。Root只改新Gitlink及必要test。不改F1/F2/Batch/LocalTTT/训练；新精确Root+Child提交后GPT窄fresh增量审核，再由DS一次完整CPU；勿合并V3/启GPU/900/影响训练。

