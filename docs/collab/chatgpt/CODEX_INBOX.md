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


## 2026-10-29 — EvalV2 F3 Store mkdir 新Pair `657061e6/0ae313e3` 窄增量审核：REQUEST_CHANGES（Evidence-only）

- **精确 Formal Root `657061e6893bd61e685685089a1cf1f61e9eb1fe` / Child+Gitlink `0ae313e329d290fc6b8a50fda1112820fb7ac485`**；Root只改Gitlink +新增`tools/v3/eval_v2_batch_tests/store_mkdir_test.py`8项，Child只改`cosmos_framework/evaluation/robocasa_v2/store.py::mkdir` (+7/-1)。详细独立 Review：`docs/collab/chatgpt/reviews/2026-10-29_V3_EvalV2_StoreMkdir_657061e6_0ae313e3_Incremental_Code_Evidence_GATE.md`。
- **F3-P1 生产并发mkdir竞态：源码层面CLOSED，无发现新增生产Code blocker**：并发只容忍真实目录，拒绝file/symlink/parent-symlink，保留`safe`、parent fsync、EIO传播、不同UUID fault持久化。作者报告focused58 PASS、独立PhaseB34 PASS、static PASS；未获取作者原始JUnit。
- **完整作者CPU未过**：inference145 PASS、PhaseA72 PASS/1 FAIL（`-x`），PhaseB未执行；整套期待434而非426。唯一称150ms READY超时；GPT从未改PhaseA`process_test.py`确认`actor(timeout=0.15)`把启动READY和stall请求超时耦合，但当前没有原始traceback，不能直接判环境或新Production Bug。
- **Formal verdict=`REQUEST_CHANGES`（仅Evidence/A1-E1待确认）**：先要本次`phase_a_regression.xml/log`唯一首错与调用行；若确为startup READY，用仅PhaseA-test方式拆离启动timeout和实际150ms stall deadline，保持Actor生产不变；新Root时只审该增量。之后作者一次全CPU，DS再一次独立全CPU。不原样反复满跑/不新增架构。
- 未合并V3生产、未授权GPU/Canary/900/DCP/训练，未触碰在训Job。此次只将新 Review 和本条append落盘。


## 2026-10-29 — EvalV2 READY 原始失败修复 `9657fb6a/0ae313e3` Test-only Code Gate：APPROVE_CODE

- **Formal Root** `9657fb6ab590f228d760362e506d5dd1b626880a`; **Child/Gitlink** `0ae313e329d290fc6b8a50fda1112820fb7ac485` 未变；前一Root `657061e6...`。单文件 `tools/v3/eval_v2_production_tests/process_test.py` +3/-1，test-only、没有任何生产代码/Child变更。另有作者证据 HEAD `bac28c293d4b7900e39030ca86575c8085667e28` 仅为bookkeeping，不替代Formal Pair。详细独立审核：`docs/collab/chatgpt/reviews/2026-10-29_V3_EvalV2_PhaseB_READY_9657fb6a_0ae313e3_TestOnly_Incremental_Code_Gate_APPROVE_CODE.md`。
- **READY 原因现由原始JUnit/traceback确认**：旧完整作者 Gate `phase_a_regression` 第73个test在`actor(...timeout=.15)` 等 `READY` 的`sock.recv(4)`先失败，未发 stall。新代码仅将初始化READY提高到5s，返回后立刻恢复Actor.timeout=.15再发stall，3秒上限和foreign/owned cleanup断言没动。
- **作者聚焦证据真实已归档**：`process.xml` 8/8；`delayed.xml` 1/1，实子进程READY延迟400ms，观测READY预算5.0s、stall预算0.15s。GitBlob `8f1ae2f0...` 与`source_proof`一致。Ruff/format/diff-check为作者报告，GPT未在容器自跑，原始Full Gate FAIL保留。
- **新 Formal Pair `APPROVE_CODE`仅限本test-only补丁，A1-E1源码/focused evidence CLOSED**；本次**未进行434作者完整CPU或DS独立CPU**，更大的Evidence Gate仍`REQUEST_CHANGES`。按既定顺序授权作者只跑**一次完整434统一CPU Gate**（145+255+34，零skip/error/fail，exit0/gate PASS/source unchanged），通过后GPT核验再交DS独立full replay。无V3生产合并、GPU、900、训练授权。


## 2026-10-29 — EvalV2 Full Author434 attempt1 旧FormalPair新增 Evidence FAIL（synthetic900）

- Formal Source Pair **未变** Root `9657fb6ab590f228d760362e506d5dd1b626880a`, Child/Gitlink `0ae313e329d290fc6b8a50fda1112820fb7ac485`；作者证据 HEAD `f65ac07d3fc3e56117dd9192ba77e4b58b5c9934` 仅为后续 bookkeeping，勿替代Formal Pair。原 READY-only `APPROVE_CODE`不重审。本轮**Evidence verdict=`REQUEST_CHANGES`**，详见 `docs/collab/chatgpt/reviews/2026-10-29_V3_EvalV2_Author434_9657fb6a_0ae313e3_900_Scheduler_RuntimeError_Evidence_Gate.md`。
- GPT已独立回读远端原始`raw/gate.json`/JUnit/log/调度末尾4记录与`derived`哈希：`inference145 PASS`、`PhaseA112 PASS/1 FAIL`、PhaseB未执行 → 总**257 PASS+1 FAIL+176未执行**、shell1/gate FAIL；READY测试PASS，53 hashes事后相同且WT干净；原Gate无最终source_unchanged=true。
- 唯一失败`scheduler_test.py:95` synthetic900，`Runtime.run()`返回`RuntimeError('dictionary changed size during iteration')`。208 valid(104/104)、692 pending，3 coordinator_stop；末尾FINISH×3后CANCEL，`inflight=[]`。原归档只有pytest外层assert栈及`repr(error)`，**内部抛错行未确认**，勿先改生产。
- **HIGH-priority candidate**：Root`runtime.py:796`对`scheduler.inflight.items()`无锁遍历，工作线程Child`scheduler.py:165`可同时`pop`；代码层面可达race，但不冒称此次确证throw-site。
- 仅建议Owner授权Codex**一次只跑原失败synthetic900用例的外置透明 traceback 捕获**，原样保留Runtime返回值和测试断言、不改生产/测试源码；若定位则只做目标生产snapshot窄修+确定性回归、新Pair窄fresh审核；若未复现报告INCONCLUSIVE。**暂不重跑完整434、不启动DS**。没有V3生产合并/GPU/RoboCasa/900真实/训练授权。


## 2026-10-29 — EvalV2 synthetic900 单次诊断未复现：INCONCLUSIVE；生产无锁迭代F4-P1待修

- **Formal Source Pair未变** Root `9657fb6ab590f228d760362e506d5dd1b626880a` / Child+Gitlink `0ae313e329d290fc6b8a50fda1112820fb7ac485`。单次新证据commit `f92adc66f3a5f41d5bb71f2c3260ac27ab74fb14`仅bookkeeping。GPT只增量审核新运行Evidence与直接相关源码，不重复 `APPROVE_CODE`。详细正式Review `docs/collab/chatgpt/reviews/2026-10-29_V3_EvalV2_Synthetic900_Once_INCONCLUSIVE_Concurrent_Inflight_Source_Finding.md`。
- 实际远端raw：单合成900 CPU test 1 PASS、wall293.75s、shell exit0；`Runtime.run`原样调用一次，error=None，900 valid/450成功/450失败、wrapper恢复；53/53 watched SHA与旧FAIL证据哈希前后一致，Root/Child干净。**本轮无异常栈，精确原抛错行仍未证实：INCONCLUSIVE**。
- **作者完整434 Gate仍为257 PASS/1 FAIL/176未执行，Evidence verdict=`REQUEST_CHANGES`**；DS未启动，不能拼接单用例PASS。绝不将 synthetic900 认定正式真实900。
- **F4-P1 HIGH（源码可达生产风险，旧FAIL是否由此引发未确认）**：Root`scripts/robocasa_eval_v2/runtime.py:796`每5s诊断未加锁迭代`scheduler.inflight.items()`，Child `scheduler.py:165` Worker `finish()`在自己的锁里pop同一字典；诊断文件I/O期间可触发`dictionary changed size`导致评测不必要停止。建议Codex仅Root在**同一scheduler._lock保护下复制快照**，磁盘读在锁外，旧红新绿确定性测试，不重审调度架构、不再随机重跑单例。
- Codex新Formal Root/Child不变→GPT窄增量→作者全CPU→DS独立全CPU；无V3生产合并/GPU/Canary/900/训练权限。

