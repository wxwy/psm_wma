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


## 2026-10-29 — Training/NoTTT Issue #11 DS independent301 CPU report Evidence Review

- Exact Formal Root `e0fe911dfb9fd34957234828195cf051713f6c3d` / Child+Gitlink `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7` **未变**，先前 Code Gate `APPROVE_CODE` 保持，禁止重复源码Gate。
- DS已提供其独立运行报告：exact-pair, clean detached, async72+regression229=301全部PASS、gate PASS/exit0、source_unchanged true、CPU fake-compute Source/Transform跨Member/Window overlap，完整PID和RNG/Frontier/Resume synthetic覆盖。**本轮GPT只能审用户粘贴报告，服务器raw JUnit/trace未能直接读取；状态 `DS_CPU_PASS_REPORTED / REPORT_CONSISTENT / RAW_BYTES_NOT_YET_REVIEWED`，不得写成独立raw bytes验证PASS。** 详细Review `docs/collab/chatgpt/reviews/2026-10-29_V3_NoTTT_AsyncOverlap_Issue11_DS301_Independent_CPU_Evidence_Review.md`。
- 原正式Job `no_ttt_packed128_droid_fresh_30k_world4_ga4` DS现场报告已是 `NOTTT_LOADER_WORKERS=8`，用的仍是旧RAW loader，未引入新async/Compact；GPU仍占用中，绝不并行新Trainer。DS仅补现成raw文件，不重跑301。
- 后续GPU/DCP资格方案 `docs/collab/chatgpt/requests/2026-10-29_V3_NoTTT_AsyncCompact_Real_DCP_GPU_Qualification_Proposal.md` **`PROPOSED_NOT_AUTHORIZED`**，拟同一旧正式DCP克隆A Compact1/nw0 vs B Compact1/nw8新async，需Owner提供独占GPU和另外授权；无正式Job停/Resume/GPU/合并许可。

## 2026-10-30 — EvalV2 F4-P1 同锁InFlight Snapshot 新FormalPair `a139b5a3/0ae313e3`：APPROVE_CODE

- 新 **Formal Root `a139b5a35877a79e0a56c2208f3002f731972b11` + Child/Gitlink `0ae313e329d290fc6b8a50fda1112820fb7ac485`**，Parent Root `9657fb6ab590f228d760362e506d5dd1b626880a`，Child不变。相比上一Formal仅Root `scripts/robocasa_eval_v2/runtime.py` +3/-1与新增 `tools/v3/eval_v2_production_tests/runtime_progress_test.py` 108行；实际GitBlob和原始Evidence哈希绑定吻合。详细Review `docs/collab/chatgpt/reviews/2026-10-30_V3_EvalV2_F4P1_InFlight_Snapshot_a139b5a3_0ae313e3_APPROVE_CODE.md`。
- **F4-P1源码CLOSED，正式 `APPROVE_CODE`（仅此最小源/回归Gate）**：诊断持既有`scheduler._lock`复制tuple snapshot，然后锁外文件I/O，保留全部D5/Core/Resume/Batch约束。旧版相同回归受控RED 1FAIL真实`runtime.py:796`字典变化，新版GREEN3PASS(实际Core/round/cleanup证据)、静态Ruff/format/AST通过、54/54源码指纹新Pair前后清洁。旧RED worktree有未提交文档和同一新回归临时文件，不声称旧RED是clean完整Formal Gate；源与回归哈希可验证。
- **旧作者434事故throw-site原始证据仍未知**（单例不复现 INCONCLUSIVE），本批准不自动关闭作者/DS CPU Evidence。新Pair完整作者Gate `NOT_RUN`，预计435=145 inference+256 PhaseA+34 PhaseB，实际收集为准；授权作者在干净新Pair且全新外部Evidence目录**只跑一次完整统一CPU**，作者PASS后GPT核证，再交DS_PRO独立完整CPU。**不合并V3生产、不启GPU/真实RoboCasa/900/训练**。


## 2026-10-30 — EvalV2 PhaseB formal Pair `a139b5a3/0ae313e3` 作者完整CPU435 Evidence: PASS

- **Formal source Pair未变** Root `a139b5a35877a79e0a56c2208f3002f731972b11` / Child+Gitlink `0ae313e329d290fc6b8a50fda1112820fb7ac485`；作者Evidence/bookkeeping commit `2c2f590093ae7d1f8d97b828bb6113487960b1fc` **不是**新的正式实施SHA，不重新进行Code Gate。正式作者CPU Evidence verdict **`PASS`**；详细Review `docs/collab/chatgpt/reviews/2026-10-30_V3_EvalV2_PhaseB_Author435_a139b5a3_0ae313e3_Evidence_Gate_PASS.md`。
- GPT经GitHub实际读取 `raw/gate.json`、分组与combined原始JUnit及日志：145 inference +256 PhaseA+34 PhaseB=**435/435 PASS**，0fail/error/skip、Shell0、6step全exit0、Gate PASS/source_unchanged=true；54/54 前后source SHA256一致，额外62/62 source GitBlob绑定与完整冻结Root/Child Git树吻合，Root/Child干净；Combined JUnit 435 unique IDs和三组完全相同。原始归档201项原件映射、209项hash manifest均与发布路径一致。
- 行为原件：F4快照旧竞态新回归`copy_held_writer_lock=[true]`、2 workers可在progress I/O期间finish；synthetic900 900 valid/50barrier/450成功450失败；真实CPU OS G1/N2/E2 B1×2+B2×3、G2/N3/E1 B1×4+B2×1，执行间存在physics overlap；F3两个活跃Ticket、Server退出23、owned清理3/3、故障记录不伪造success；Store并发两条不同UUID fault。foreign survival/Resume byte parity以实际PASSED测试断言为证据，未冒称额外独立raw witness。
- **DS独立CPU Gate仍 OPEN/NOT_RUN，不继承作者PASS**；下一步只由DS在新独立干净Exact Pair执行一次同一完整435 CPU Gate，输出完整原始JUnit/OS/Source证据交GPT。此前旧作者434 FAIL不能被此单证据覆盖其真实原抛错行；无V3生产合并/GPU/Canary/正式900/训练授权，不增架构Gate。


## 2026-10-30 — Training/NoTTT Issue#11 DS301五份原始Evidence SHA核验（只剩完整Trace）

- Frozen Formal Pair root `e0fe911dfb9fd34957234828195cf051713f6c3d` / Child+Gitlink `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7` **未变**；旧 `APPROVE_CODE` 不重审。
- 用户上传DS 6核心raw的copy-paste包，GPT已按raw文本字节重建并哈希匹配5份完整的gate.json、async.xml、regression.xml、environment.json、source_sha256.json（**5/5**）；原始JUnit72+229=301唯一case、0fail/error/skip、Gate PASS/5steps exit0、source unchanged、18/18 source hash与原Formal源清单一致。
- 第6份 `timelines/overlap_trace.json` 只包含头部/派生摘要/worker PID清单，92KB完整事件未贴；**`DS_CPU_TEST_EXECUTION=PASS_VERIFIED_FROM_PASTED_RAW`，`RAW_TRACE_INTEGRITY=PENDING_ONE_FILE`，完整6项Evidence审核仅此OPEN（Evidence-only）**。已有overlap testcase JUnit确实PASS，单个时序ms尚不能独立重算。不要求重跑301项/补传663项。
- 时间戳XML UTC15:13–15:32，对应CST23:13–23:32；报告误标CST非阻断。详细 Review `docs/collab/chatgpt/reviews/2026-10-30_V3_NoTTT_Issue11_DS301_5Raw_SHA_Verification_Trace_Pending.md`。只请DS补已生成的**完整trace一个文件**，无源码/训练动作；GPU/DCP未授权，正式nw8旧RAW训练继续。

## 2026-10-30 — DS_PRO EvalV2 PhaseB B2 独立435 CPU报告口径核查：PASS_REPORTED / RAW_PENDING

- Formal Root `a139b5a35877a79e0a56c2208f3002f731972b11` / Child+Gitlink `0ae313e329d290fc6b8a50fda1112820fb7ac485` **未变**；沿用之前Code Gate `APPROVE_CODE`与作者完整CPU435原件核验 `PASS`，此次**不重新Code Gate、不重复作者Evidence审核**。本轮详细Review：`docs/collab/chatgpt/reviews/2026-10-30_V3_EvalV2_PhaseB_B2_DS435_Independent_CPU_Report_Consistent_Raw_Pending.md`。
- DS报告在其**独立Git Clone** `/tmp/ds_pro_evalv2_435_20261030/` 声称435/435（145+256+34）、0 fail/error/skip、shell0、Gate PASS/source_unchanged true、真实G1/N2/E2 histogram{1:4,2:2}、F1/F2/F3/Store/F4/D5/Resume PASS，未碰NoTTT目录/训练或GPU。**报告自洽、无新生产Code blocker线索**，允许记录`DS_CPU_PASS_REPORTED`。
- **本轮GPT未读到DS自身的原始文件字节**：仅用户报告的Gate SHA `919f3ca9...` 等待核实，服务器`/tmp`不在本会话沙箱，Desktop Commander设备离线，V3暂无本次DS evidence。**独立DS Evidence正式Gate=`REQUEST_CHANGES`（Evidence-only: `DS-RAW-1`），不是“DS测试失败”；只请DS归档/交付现成Gate+JUnit+log+source+关键OS原件，无需重跑435或更改源码。**
- 最新origin V3 `e7543ff63bfc1f492349fb05e61aa0c8317588b1`且Gitlink仍为旧`746c5cf2...`；DS本地`5b540cce`不能作为合并远端HEAD依据。未授权V3受控合并、真实GPU/Canary/正式900；禁止操作NoTTT训练目录。原件复核后再给DS独立Gate最终结论。


## 2026-10-30 — NoTTT Issue#11 DS301独立CPU Gate六份原始Evidence正式PASS（Trace已关闭）

- **Frozen Formal Root `e0fe911dfb9fd34957234828195cf051713f6c3d` / Child+Gitlink `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7` 未变；旧源码 `APPROVE_CODE` 维持，禁止重复代码审核**。
- 用户上传完整第6份 `overlap_trace.json` 分为3个文本，GPT拼接解析后以 `json.dumps(indent=2)` 原样序列化117909字节，sha256 `27357f1034a0b2ea91e887240c6566c1aac2630f37bd5f983123a332e3396c11` 与既冻hash**完全一致**；先前5份完整raw亦已匹配。**`DS_CPU=PASS / RAW_EVIDENCE=PASS_6_OF_6`**。详细正式Review `docs/collab/chatgpt/reviews/2026-10-30_V3_NoTTT_Issue11_DS301_SixRaw_Trace_Hash_Overlap_Independent_Evidence_GATE_PASS.md`。
- GPT独立从399异步事件重算下一GA Member Source87.798/Transform128.965ms、下一Window Source20.455/Transform32.393ms（各绝对差0），串行204事件交叠0；主进程等待96事件合计10376.207ms一致。旧已核原始JUnit72+229=301唯一PASS、0fail/error/skip、Gitlink一致、source unchanged记录。无需重跑CPU或补交原件。
- **GPU吞吐与真实DCP Resume仍 NOT_RUN**，CPU cold fake异步12.142s反而慢于同步3.452s；原正式NoTTT旧RAW nw8 Job仍不得停/切/并发Resume。真实GPU资格提案 `PROPOSED_NOT_AUTHORIZED`，需Owner另行授权和GPU空闲窗口；Compact strict Gradient失败历史维持。

## 2026-10-30 — V3 EvalV2 PhaseB B2 已受控提升（源码树等价Gate）

- 已在GitHub远端V3受控提升生产Root `978337deef0173f60336977367e21f513772a465` / Child+Gitlink `0ae313e329d290fc6b8a50fda1112820fb7ac485`；被测试正式Root `a139b5a35877a79e0a56c2208f3002f731972b11` / same Child，**区别是V3文档历史导致的新Root SHA**。本轮详细Review：`docs/collab/chatgpt/reviews/2026-10-30_V3_EvalV2_B2_Controlled_Promotion_978337de_0ae313e3_Source_Equivalence.md`。
- 提升提交single-parent，仅新增/更新53个审核源Git对象：2 configs+10 scripts+40 tools+1 Child Gitlink，未直接merge候选全分支；保留V3已有docs/SESSION/TODO和NoTTT现有代码。GitHub完整GitTree**9,844个非文档文件/对象在Promotion Root和被测试Root之间精确同SHA、mode、type（0 diff）**，非文档源码equivalence窄Gate `APPROVE_CODE`。新Root没有独立执行435CPU，不能虚构新Root raw evidence。
- CPU：作者旧正式Pair完整435原始证据GPT已核`PASS`；DS同Pair435/435独立运行报告`PASS_REPORTED`，Owner指示依报告继续但GPT未取得DS raw，禁止写成独立raw字节验过。远端仅Source Promotion，未做NoTTT工作树任何操作。
- 下一步真实1GPU/M2/B2 Canary需Owner单独授权和**不影响NoTTT训练**的独占可用GPU；正式900更需独立授权。不得把本次受控源码提升当成GPU/真实仿真合格。


## 2026-10-30 — Owner授权 No-TTT 真DCP Resume + Compact1 nw0/nw8 GPU资格（条件执行）

- 原 No-TTT Async Frozen Root `e0fe911dfb9fd34957234828195cf051713f6c3d` / Child+Gitlink `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`，前序 `APPROVE_CODE` + Issue#11 DS 301 CPU/6raw全部PASS不重审。
- Owner本轮明确「我授权」前序提出的**真实DCP恢复与隔离真实GPU性能**，**状态从`PROPOSED_NOT_AUTHORIZED`更新为`AUTHORIZED_CONDITIONAL_RESOURCE`**，详细正式执行指令 `docs/collab/chatgpt/requests/2026-10-30_V3_NoTTT_Real_DCP_Compact1_NW0_vs_NW8_Owner_Authorized_Execute.md`；**只授权这一次候选代码20步A (Compact1,nw0) + 20步B (Compact1,nw8)的匹配C真实DCP Resume实验**。其余训练/仿真/代码无关。
- GPU4–7若被旧正式Job占用，DS只读核对并 `BLOCKED_RESOURCE_OR_CHECKPOINT`、绝不停止正在训Job；GPU4–7全空闲且原Job已退出、完整C/四rank DCP +独立输出/磁盘可用时才可分别依序启动。DS不可修改/清理正式Job的source/Checkpoint/identity/git/disk，也不可直接合并V3/Child。Root/Child Gitlink在V3可能被其它工作改变，必须使用**冻结NoTTT精确隔离Pair**而不是 V3 HEAD。
- 实验后GPT独立审核实际真实DCP/数据/监控/GPU性能；只需新Evidence，不新代码Gate；即便通过也不代表授权正式Job切换或Compact旧严格GPU梯度历史PASS。

## 2026-10-30 — Training NoTTT Issue#12 真实DCP/GPU A PASS / B first-materialize Timeout，Evidence REQUEST_CHANGES

- Frozen Root `e0fe911dfb9fd34957234828195cf051713f6c3d` / Child+Gitlink `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7` **未变**，原源码`APPROVE_CODE` + DS独立CPU301/6raw`PASS`保持，不重新审核旧源码。新 DS原始资料未上传，仅用户粘贴 `ISSUE12_EXECUTION_REPORT`；独立新Evidence Review `docs/collab/chatgpt/reviews/2026-10-30_V3_NoTTT_Issue12_RealDCP_GPU_ArmA20_PASS_ArmB0_TIMEOUT_Evidence_GATE_REQUEST_CHANGES.md`。
- DS报告：合法完整DCP C=iter9600克隆13/13；ArmA `Compact1,nw0`真实Resume 9601..9620 **20/20 commits PASS**，wall P50=20.50s/P90=22.70s（共享GPU环境）；ArmB `Compact1,nw8` DCP load成功后首批 `next(loader)`120s Timeout、**0次commit FAIL**；`PERFORMANCE=INCONCLUSIVE`，不能称新async GPU加速或已证实更慢。
- **关键归因疑点**：B每个Worker `PreparedDataset.__getitem__`首用`AsyncRecipe.build`重建官方`RoboCasaExactWindowSourceReader`+LeRobotDataset，主Preflight的186s初始化耗时不能排除该**Worker内冷启动**作为120s Timeout机制；与正式Job同时占GPU4–7/HostIO的资源争用并列待证，未确认生产代码新Bug，不自动变更Timeout。A报告的data wait5.35s需查原始字段。
- 原授权 `e5fde3f7` 要求正式Job存活/GPU4–7占用即BLOCKED，DS现称Owner外部豁免并发但本轮未提供权威Waiver记录。无论是否有效，共享资源下A壁钟不能作为将来独占B的公平baseline。
- **Issue#12当前真实 Evidence Gate `REQUEST_CHANGES`（运行失败+原始日志待核），正式Job未触碰为DS报告**。DS仅提交现存ArmA/B4rank/manifest/S0/超时stack/指标字段及waiver凭据，**不重跑A或B、不改码、不停训、不GPU实验、不合并V3**；若后续需要新独占matched A/B须Owner另外授权。

## 2026-10-30 — Training Issue12 DS补证：ArmA20监控字段核验、CUDA Event语义纠正；B首包Timeout仍OPEN

- Formal Root `e0fe911dfb9fd34957234828195cf051713f6c3d` / Child+Gitlink `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7` **未变**，前序`APPROVE_CODE`及Issue#11独立CPU301/6raw PASS保持，**本轮只审核新增Evidence**。详见正式新Review `docs/collab/chatgpt/reviews/2026-10-30_V3_NoTTT_Issue12_Supplement_ArmA20_CUDAStall_ColdStart_Evidence_Incremental.md`。
- 用户上传 `arm_a_20step_monitor_v1`完整20行JSON，GPT程序化解析：9601..9620连续20条optimizer commit、4F/4B、missing/nonfinite0；全20步 wall median20.723s，稳态18步median20.490s；稳态 `data_prepare` median5884.427ms，`gpu_data_stall` median5354.804ms。`data_wait_ms=null`。
- **ISS12-E3字段疑义CLOSED，但DS“cuda_sampled=false表示gpu_data_stall来自主机墙钟”属于错误解释**：Frozen `corrected_telemetry.py:148-211,441-465`有独立`_sample_data_stall`每步记录CUDA Events并`elapsed_time`；`cuda_sampled`仅对应常规每100步的compute events。20步`gpu_data_stall_status=ready` = rank0 current CUDA stream data-gap estimate，不能解释成全卡GPU idle。
- B4rank真实DCP9600成功加载，首个materialize 120sTimeout，0 optimizer commits；`ISSUE12=REQUEST_CHANGES`保持。Worker每次首请求重建LeRobot Dataset，高成本冷启动/正式Job共享争用都可能，缺worker-init时戳，归因未证。现成manifest粘贴列14项而摘要称13，LOW；Owner外部GPU共享豁免仅DS转述+RUN_MANIFEST，`REPORTED_UNVERIFIED`，不能推断未授权。
- **不重跑CPU/GPU、不修改生产代码、不停训练、不合并**。下步仅证据可用性整理，若要新探针/独占匹配A/B需Owner明确授权。

## 2026-10-30 — Issue12 NoTTT 首包超时诊断 DS 指导交付（Phase R now / Phase P未授权）

- 冻结Root `e0fe911dfb9fd34957234828195cf051713f6c3d` / Child `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`，当前 Issue12真实B120s首包Timeout、0commit、归因未定，原NoTTT CPU301 PASS不重审。
- 正式DS指导 `docs/collab/chatgpt/requests/2026-10-30_V3_NoTTT_Issue12_DS_OneWorker_ColdStart_CPU_Diagnostic_Guidance_NOT_AUTHORIZED.md`：立即仅只读整理已有B四Rank日志（标明确切缺失的Worker init计时）；准备单Worker/单真实request CPU-only外部脚本和精确命令，**`PENDING_OWNER_AUTHORIZATION`不执行新真实数据探针**。禁止动GPU/正式NoTTT/产线代码/Checkpoint/V3。

## 2026-10-30 — Training Issue12 DS外部冷启动探针代码评审REQUEST_CHANGES（未批准运行）

- Formal生产Pair `e0fe911dfb9fd34957234828195cf051713f6c3d` / Child `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7` **未变**，旧APPROVE_CODE、CPU301/6raw PASS不重审。本轮只审用户上传外部`issue12_worker_coldstart_probe.py`源码SHA `5215bf115ea48b3cd05d833599b0c6f50fd38a31dbc62601be882ffdd1ce9167`，正式独立Review `docs/collab/chatgpt/reviews/2026-10-30_V3_NoTTT_Issue12_DS_External_CPUColdStartProbe_5215bf11_REQUEST_CHANGES.md`，本版脚本 `REQUEST_CHANGES`、PhaseP真实数据CPU仍`PENDING_OWNER_AUTHORIZATION`。
- 最小阻断：探针`_require_cpu_only`读模块全局`torch`，但torch仅在main内部局部导入→必然NameError；Phase1手工重写build/跳过worker import与spawn，Phase2计时起点在`_begin`之后，不是包含spawn的真实冷启动；仅消费1 segment却调用`finish()`必报incomplete Window且绕过公开API/finally；初始frontier≠9600恢复frontier、硬编码digest不等于完成实际身份核证；拟运行命令缺真正外层timeout/强制资源上限，输出与高占用数据卷混用。
- DS只修临时外部脚本、带完整安全命令和静态check后再申请脚本复审；**不执行任何真实数据CPU/GPU/正式训练，不改production/timeout/V3**。修正后脚本审核与Owner新CPU-only执行授权分开。


## 2026-10-30 — EvalV2 GPU7 PhaseB 真实Canary RunInputs超限：生产阻断 HIGH / Evidence REQUEST_CHANGES

- **Formal Root** `427b4d09cdd8070820a39b93ebf2ff832a23e359` / **Child+Gitlink** `0ae313e329d290fc6b8a50fda1112820fb7ac485` 未改变；此前共享GPU最小代码/CPU63 + Ruff原Gate不重审。现只审新DS真实Canary运行Evidence。
- **Formal Evidence verdict = `REQUEST_CHANGES`；Canary因生产缺陷BLOCKED。** 独立Review：`docs/collab/chatgpt/reviews/2026-10-30_V3_EvalV2_PhaseB_Canary_427b4d09_0ae313e3_RunInputs_Oversize_Evidence_REQUEST_CHANGES.md`。
- **F5-P1 HIGH（源码已直接确认）**：Root `robocasa_vendor.py:130,260-286` 包含全部untracked资产SHA +原始stdout；`identity.py:201-215` 把全部作为`inputs`，`cli.py:139-140`写并读`run_inputs.json`；Child `store.py:30,75-99,117-118`严格256KiB，故大数据必报`oversized JSON`。现场20,989,831B、123,363资产、GPU7等数字仅DS用户报告，原raw服务器文件GPT未读取。
- **整改仅限**把小型稳定runtime digest等身份字段留在`run_inputs`，全量`evaluation_runtime`和`runtime_probe_evidence`另外通过专用限额（建议64MiB）原子Evidence writer保存；原256KiB普通合同、vendor逐资产SHA、Manifest runtime identity、strict resume/source清洁校验、owned cleanup全部保持。针对真实大型payload做Fresh→Resume公开路径CPU回归及大证据/普通ledger边界负例。Codex新Root/Child提交后GPT fresh窄增量审；无须重跑旧435 CPU，无理由反复在旧SHA fresh。
- **未授权**在旧审核Root上用local patch绕过、放宽全部JSON limit、停NoTTT训练、直接正式900；新源码批准后仅按原授权重试1GPU×2Sim×B2×4Episode真实Canary。

## 2026-10-30 — Training Issue12 DS仓库外Probe v2 d54ef1b0 增量复审 REQUEST_CHANGES

- Formal Root `e0fe911dfb9fd34957234828195cf051713f6c3d` / Child+Gitlink `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7` **未变**，既有production APPROVE_CODE、Issue#11 CPU301/6raw PASS不重审。此次唯一新对象仓库外script v2 SHA256 `d54ef1b006bbf99bc4aedef633f8adf267b2d67334e993bcd1ac21526f096795`（从用户上传的CRLF文本提取并统一LF/单行尾，18378 bytes，AST compile PASS）。
- 审核记录 `docs/collab/chatgpt/reviews/2026-10-30_V3_NoTTT_Issue12_DS_External_CPUColdStartProbe_v2_d54ef1b0_INCREMENTAL_REQUEST_CHANGES.md`：v1 P1 torch NameError CLOSED，partial-window finish + finally清理 CLOSED；P2真实Worker spawn时长仍漏测（_begin在timer前）、ScopeA预热ScopeB；P3还用private API；P4 initial_frontier不是iter9600真实恢复frontier；P5 budget/RSS只是阻塞后检查且命令无外层timeout/输出仍近满盘；新P6失败时没有阶段实时日志/partial witness。此次 `SCRIPT_v2=REQUEST_CHANGES`；只由DS改仓库外脚本，生产源码只能Codex修改。
- `REAL_DATA_CPU_EXECUTION=PENDING_OWNER_AUTHORIZATION`、Issue12 B真实GPU0commit/timeout性能Inconclusive不变；不运行脚本、CPU301、GPU或训练、不动正式Job/Checkpoints/V3实现。


## 2026-10-30 — EvalV2 F5-P1 有界Runtime Probe持久化 新FormalPair增量Code Gate：APPROVE_CODE

- **Formal Source Root `7c74dc26ac4837f193727ecf847b9b64554c18b2` / Child+Gitlink `53c3c95202e14d3b72d236eee6899a80acf82989`**，与前一被阻断Pair `427b4d09/0ae313e3`不同，已实施窄fresh review；作者证据/bookkeeping `608f55dc`及本条review commit都不替代Formal Pair。
- **GPT verdict=`APPROVE_CODE` 仅F5-P1最小生产源码增量 + 作者Synthetic CPU Evidence**。详细Review `docs/collab/chatgpt/reviews/2026-10-30_V3_EvalV2_F5P1_RuntimeProbe_7c74dc26_53c3c952_Incremental_Code_Gate_APPROVE_CODE.md`。
- **F5-P1 HIGH CLOSED**：Root仅`cli.py`将大`evaluation_runtime`+raw `runtime_probe_evidence` 按独立Evidence追加（UUID+canonical hash），`run_inputs.json`保留`runtime.digest`及其它身份字段；Child`store.py`只增64MiB专用writer。普通256KiB `read/write`、原vendor逐资产SHA、Source/Gitlink严检、manifest/runtime identity、Model Cache/Resume保护与SharedGPU均不变。
- GPT直接核GitHub原始JUnit **85 unique/85 PASS，0fail/error/skip**、shell0/clean和10项source fingerprint、公开Fresh→Resume大型合成用例、2,553字节原`run_inputs.json`及Cache/两invocation引用；作者Evidence sidecar37,200,840/37,200,847 B，gzip原件**未由GPT独立解压**；Ruff/format为作者报告，非GPT独立重跑。无DS真实GPU/真实vendor验证。
- **下一步仅允许已有Owner范围1GPU×2Sim×B2×2Task各2Episode（4总量）的独立clean候选Canary**，须新输出namespace、稳定完整Checkpoint、正确source/Child，真实batch histogram/MP4/4Episode/显存/清理原始证据交GPT；不自动合并V3/Child、不停止NoTTT、不启动900/额外GPU实验、不重跑旧435 CPU。

## 2026-10-30 — Training Issue12 DS外部Probe v3 增量复审（当前REQUEST_CHANGES，不授权CPU探针）

- 生产 Formal Root `e0fe911dfb9fd34957234828195cf051713f6c3d` / Child `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7` **未变**，之前生产APPROVE_CODE + Issue11 301CPU/6raw PASS不重审。新审对象为DS在服务器**仓库外**的v3脚本（自述SHA `5eea42983a88ca823b2419e69a18fa6d0016cdc0bc252942488c3eeaca68d9c4`，但上传大粘贴Markdown格式化破坏Python字节，不可独立检原.py SHA/compile），独立增量Review `docs/collab/chatgpt/reviews/2026-10-30_V3_NoTTT_Issue12_DS_External_CPUColdStartProbe_v3_INCREMENTAL_REQUEST_CHANGES.md`。
- 本轮关闭v2的publicAPI、只消费单请求不得finish、漏算begin-spawn时长；仍BLOCKER：P6卡在Scope A/B高成本构造/首包时PARTIAL只在Scope完成后更新，SIGTERM失去阶段定位（应增加flush start/done阶段日志）；P5命令虽`timeout1800`但缺kill-after、stderr/stdout持久化且输出仍在高占用/data1；P2真实Worker跑在ScopeA已重建/读取之后的warm状态，不能称严格cold。ScopeB需独立进程或明确降格辅助。
- `SCRIPT_v3=REQUEST_CHANGES`，`REAL_DATA_CPU=NOT_AUTHORIZED`，DS仅修自己仓库外临时脚本并回传原始.py字节与精确SHA，不动仓库代码/正式训练/GPU/DCP。

## 2026-10-30 — Training Issue12 DS仓库外Probe v4审阅：方案旧P2/P5/P6关闭，唯一SCRIPT原件Evidence缺件

- Production Formal Root `e0fe911dfb9fd34957234828195cf051713f6c3d` / Child `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`未变，不复审旧生产APPROVE_CODE/CPU301/6raw。用户v4大粘贴报原.py SHA `9f1996b01d76f33ad8b15d19e47c15ef46471781f35599d591b55b8e5f016c67`，但本次上传仅57,344 byte经Markdown转码的文本，`from **future**`等导致无法独立验证原脚本的字节/SHA/语法。正式增量Review `docs/collab/chatgpt/reviews/2026-10-30_V3_NoTTT_Issue12_DS_External_CPUColdStartProbe_v4_EvidenceOnly_REQUEST_CHANGES.md`。
- P2 Spawn/取数计时拆分、P3公开API/partialClose、P4 representative frontier标注、P5 timeout -k/独立日志、P6 START/DONE阶段持久化，经控制流审查均`CLOSED_AS_DESIGN`；ScopeB在ScopeA之后受预热，只能作warm单worker证据；原B4rank120s Timeout/0commit/性能INCONCLUSIVE未改变。
- **SCRIPT正式Verdict `REQUEST_CHANGES`（EVIDENCE_ONLY：缺原始v4 .py/zip，不能绑定原SHA）**，不要求v5重构或重跑301。只让Owner上传DS已有原始ZIP，GPT复核bytes/hash/AST，之后Owner再单独授权CPU-only真实数据；本轮`REAL_DATA_CPU=NOT_AUTHORIZED`，无GPU/正式Job/Checkpoint操作。


## 2026-10-30 — EvalV2 PhaseB真实Canary NoTTT checkpoint与required Local-TTT协议不兼容：Evidence REQUEST_CHANGES / 非生产Bug

- **Exact Formal Root `7c74dc26ac4837f193727ecf847b9b64554c18b2` / Child+Gitlink `53c3c95202e14d3b72d236eee6899a80acf82989` 未变化**；原F5-P1持久化Code Gate `APPROVE_CODE`保持，不再重审。新DS真实Canary Evidence审核见 `docs/collab/chatgpt/reviews/2026-10-30_V3_EvalV2_PhaseB_Canary_7c74dc26_53c3c952_TTT_Checkpoint_Compatibility_Evidence_Gate.md`。
- **Evidence verdict=`REQUEST_CHANGES`，当前`BLOCKED_INPUT_INCOMPATIBLE`，不是源码生产新blocker**。Root `eval_robocasa_18task_queue.py:272`强制`required`，Child `action_policy_server_robocasa.py:653-663,894-930`要求raw15/state15/H16/K4/local32，`robocasa_local_memory_policy.py:74-78`无runtime立即拒绝，`robocasa_session_transactions.py:166`要求实际 Local Memory，`robocasa_v2/contract.py:89` manifest为required。NoTTT model不能拿来验证此冻结LocalTTT Session/Batch路径；简单`off`会改变协议并触发更多拒绝。
- DS报告此次已用clean精确Pair、GPU7 dry-run PASS，紧凑`run_inputs.json` 5,085B、独立Evidence已生成（F5修复现场生效）；Action Server启动退出1，NoTTT `iter_000010400` config禁用LocalTTT，0 valid（2 invalid/2 pending）、无实际B2。DS服务器raw与TTT A1/A2 checkpoint字节本轮GPT未读取，不写成独立现场验证。
- **技术路线选A（作为建议，Owner仍需确认改变测试模型）**：DS只读核A1 `formal_verified_index_30k/iter1300` checkpoint真实Local runtime和同源config及raw15/state15/H16/K4/local32；若A1不合格，再核A2 `packed128_droid_fresh_g1_20261019/iter20000` 的真实完整同源config，不能借A1 config冒充。若无同源匹配Pair即BLOCKED。通过且Owner确认后原授权范围内新namespace重跑1GPU/2Sim/B2/两Task各2Episode，提交真实Session/Batch/MP4/cleanup证据；**不修改正式代码、不允许NoTTT auto-off、不授权900或NoTTT正式评测**。


## 2026-10-30 — Owner目标纠正：EvalV2 PhaseB 接替NoTTT评测；此前“切LocalTTT checkpoint”建议RETRACTED

- Owner本轮明确 **“我们就是接替nottt，为什么要强制要求是local-ttt？”**：原 1GPU×2Sim×B2×4Episode Canary 是在 **NoTTT checkpoint** 上验证EvalV2多Sim/native batch和结果链，不是LocalTTT算法测试。此前Review `2026-10-30_V3_EvalV2_PhaseB_Canary_7c74dc26_53c3c952_TTT_Checkpoint_Compatibility_Evidence_Gate.md` 的“换TTT checkpoint / 非生产能力缺口”建议**正式撤回**；旧F5-P1 `APPROVE_CODE` 和产线代码事实不变，Formal Pair 未变不重审旧实现。
- 正式纠错详细文件：`docs/collab/chatgpt/reviews/2026-10-30_V3_EvalV2_PhaseB_NoTTT_Target_Owner_Correction_Erratum.md`。NoTTT场景当前 **`REQUEST_CHANGES / BLOCKED_NOTTT_PHASE_B_UNSUPPORTED`**，属于新目标下缺乏执行能力，而非NoTTT checkpoint选择错误。
- Root `eval_robocasa_18task_queue.py:272` hardcode required；Child `action_policy_server_robocasa.py:654,910-912,1257`、`robocasa_session_transactions.py:166,328,339`、`robocasa_batch_transactions.py:201-273`、Sim `eval_v2_transactions.py:23-69` 的Session/fast state/prefix均耦合TTT。**不是仅把required换off**；应由Codex在新隔离候选实现明确NoTTT模式，把Slot/Lease/ACK/Deadline/native B2复用、response cache归事务状态、不生成fast-state、不注入Local prefix；原TTT模式严检不变、不同模式不同科学身份、NoTTT模型及原定4Episode真实验收不变。
- 未授权在旧 SHA 上现场patch、用TTT模型替代目标、直接正式900、修改NoTTT训练。新精确Root+Child产出后GPT按增量Code Gate审核；本条仅文档勘误与正确路线登记。


## 2026-10-30 — Owner最终澄清：EvalV2 仿真优化必须同时支持 NoTTT + LocalTTT（纠正两次单模式建议）

- **Owner最新要求**：“仿真优化必须在nottt和localttt都能work”。最终不是选NoTTT或LocalTTT；一套RoboCasa EvalV2多Sim/NativeBatch/Session/Resume/视频/资源/clean-up复用，两种checkpoint均需真实可运行。该要求**优先覆盖**同日先前“只换TTT checkpoint”和随后“仅替换NoTTT链路”的单一模式建议；两份报告的精确源码观察及原生Canary失败原始事实仍保留。
- 纠错/需求记录：`docs/collab/chatgpt/reviews/2026-10-30_V3_EvalV2_PhaseB_DualMode_NoTTT_LocalTTT_Owner_Requirement_Correction.md`。关联旧Formal Pair Root `7c74dc26ac4837f193727ecf847b9b64554c18b2` / Child+Gitlink `53c3c95202e14d3b72d236eee6899a80acf82989` 未改，不重复技术审核；既有F5-P1持久化APPROVE_CODE仍生效。
- **双模式整改Gate OPEN/REQUEST_CHANGES**：NoTTT config显式`off`且不得要求/伪造fast权重、Local evidence/Prefix；LocalTTT config显式`required`仍严格K4/local32、evidence chronology及memory commit；两模式共用Sim/Scheduler/Lease/ACK/replay/timeout/NativeBatch，通用response cache属事务层，不依赖fast-state。模式纳入Manifest/Run身份，checkpoint/config不匹配fail-closed；不能仅删除启动`required`断言，原BatchTransaction/Simulator依赖Local状态须真实解耦。Codex最小改动实现，GPT对新formal Pair增量Code Gate审核。
- 当前真实NoTTT Canary已被原required模型启动拒绝；LocalTTT Canary尚未有GPU通过证据。**最终真实验收必须分别覆盖NoTTT和LocalTTT**（稳定各自checkpoint、单GPU×2Sim、实测B2、Episode/MP4/显存/清理），不得用其中一次代表另一次；本条不自动授权额外GPU run或900 Episode、不修改训练和checkpoints、不merge生产候选。

## 2026-10-30 — Training Issue#12 DS仓库外Probe v4文本充分，设计Gate APPROVED，不再索取ZIP

- Owner明确纠正“传原始ZIP”为不可执行重复要求；用户已经提供完整v4代码、Diff、SHA与静态验证结论。正式新 Review `docs/collab/chatgpt/reviews/2026-10-30_V3_NoTTT_Issue12_Probe_v4_TextComplete_Design_APPROVED_NoZip.md`，**覆盖**原v4因`ZIP未上传`的`REQUEST_CHANGES(EVIDENCE_ONLY)`。
- **`SCRIPT_v4=APPROVE_SCRIPT_DESIGN`**：逻辑已满足计时拆分、公开Loader、异常清理、START/DONE及时日志、timeout/输出隔离和预热/代表请求边界；DS声称源码SHA `9f1996b01d76f33ad8b15d19e47c15ef46471781f35599d591b55b8e5f016c67` 标`REPORTED_NOT_INDEPENDENTLY_VERIFIED`，**不阻断**。不让DS继续v5/要求再次转ZIP。
- **`REAL_DATA_CPU_EXECUTION=PENDING_OWNER_AUTHORIZATION`**：Owner批准后才能单次CPU-only真实数据探针；原生产Pair`e0fe911dfb9fd34957234828195cf051713f6c3d`/`f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`及CPU301 PASS、Issue12 B首包Timeout性能INCONCLUSIVE、正式Job未修改均保持。


## 2026-10-30 — EvalV2 PhaseB NoTTT+LocalTTT 双模式新FormalPair增量 Code Gate：APPROVE_CODE

- **Formal Root `d18b420c02cfc51a1b85e9f1d6ce5d26f7bd3163` / Child+Gitlink `2f7334c4ada6ace1d21185985aae90539052bf18`**，已从 GitHub Root GitTree 核实；相对已审F5 `7c74dc26/53c3c952` 为新 implementation，完成窄fresh review。作者 `4cdf611b` Evidence commit、本 Review/Inbox commit 均不替代 Formal Pair。
- **正式 verdict=`APPROVE_CODE`（仅双模式增量 + 作者合成 CPU Evidence）。** 详细 Review：`docs/collab/chatgpt/reviews/2026-10-30_V3_EvalV2_DualMode_d18b420c_2f7334c4_Incremental_Code_Gate_APPROVE_CODE.md`；之前F5-P1 bounded persistence `APPROVE_CODE`保留，不重审旧435。
- 实际 diff：Root config/identity/runtime/legacy Queue少量接线，Child manifest/evidence/transaction/client/Native Sim与server mode支持。NoTTT `off` 的 Session request_index与公共response cache独立于Local memory、模型调用不注入prefix、不建fast snapshot；LocalTTT `required` 的真实prepare/commit/abort/reset、raw15/state15/H16/K4/local32严格合同保留。模式进入Manifest，config/net能力/DCP Local tensor inventory校验，握手/ACK与Core读写按mode验证，原有共享GPU/F5写入安全未动。
- GPT从作者GitHub原始`raw/final/junit.xml`独立解析 **324 unique/324 PASS，0fail/error/skip**，对应 `console.log` 324 passed/14 warning、shell0和before/after clean；`raw/static-final/static.json` 的Ruff/format/compile/diff-check exit0，44项source绑定；CPU OS NoTTT G1N2M2B2得到4Core/8replan/histogram B1×4+B2×2，LocalTTT CPU旧多拓扑及F3故障回归正常。**均是合成CPU边界，不是假装真实GPU、真实DCP或真实仿真PASS。**
- 下一步仅在Owner已确认的准确范围交DS进行 **NoTTT 与 LocalTTT 两模式独立真GPU Canary**：每模式各自同源完整Checkpoint+Config、clean exact Pair、新namespace，实测GPU4–7任选1×2Sim×B2、原指定CloseFridge/OpenCabinet各2Episode、MP4/VRAM/latency、Session状态/End/owned cleanup。**此Code verdict不自动授权由4 Episode增到8**，如需新增LocalTTT GPU执行先Owner明确确认；不合并V3/Child、不启动正式900、不触碰训练或活跃Job。

## 2026-10-30 — No-TTT Issue12 RealCPU cold-start：高置信度重复LeRobotDataset构建瓶颈，Codex窄修设计交接

- Frozen root e0fe911dfb9fd34957234828195cf051713f6c3d/child f6a92d47b6dac7998ddc58b3da26ef93f8068dc7 保持；旧APPROVE_CODE、CPU301/6raw PASS不重审。DS Owner授权的CPU-only实测ScopeA build193652.7ms、SourceReader192970.6ms、LeRobot init188782.1ms、prepare224.5ms，ScopeB real single worker materialize120.249s Timeout（warm状态）。这些为DS报告，GPT未直接验原始服务器JSON；单Worker超时证实不必32并发，SourceReader eager初始化为首要可行动瓶颈，Worker内部阶段未实测。
- Review docs/collab/chatgpt/reviews/2026-10-30_V3_NoTTT_Issue12_RealCPU_OneWorker_ColdStart_RootCause_Review.md；Codex窄修设计交接 docs/collab/chatgpt/requests/2026-10-30_V3_NoTTT_Issue12_Codex_LeRobot_WorkerColdStart_NarrowFix_Handoff.md。无需再DS Probe/ZIP/旧301，Codex只在隔离候选解决昂贵首包初始化，保证Source/Delta/RNG/Frontier/DCP与异步功能；新真实CPU/GPU/正式切换须Owner授权。Issue12 GPU B0 commits、性能INCONCLUSIVE不变。

## 2026-10-30 — Training NoTTT Issue12 Worker ColdStart 新FormalPair 增量 Code Gate APPROVE_CODE

- **Formal Root fd9021b0908b4b2763b3d02508b1f34df377dc97 / Child+Gitlink 224c5f3c0bd6911bb49cb6bb0895ba7da53ff822**（旧production Pair e0fe911d/f6a92d47不重审）。Child相对旧Pair只改 2 production files：Recipe注入新的 VerifiedWorkerLeRobotDataset Factory；新Worker Source使用VerifiedIndex、每Episode Arrow按需投影、官方LeRobot inherited Delta/Caption/Torch read和有界LRU，旧NoTTT Loader、nw0、120s timeout、RNG/Frontier/DCP不改。2 test files加入Source合成对照/真实spawn接线。
- GPT直接读GitHub原始`final/junit.xml`：47+11=**58唯一PASS/0failure/error/skip**；独立SHA核验manifest里的**11/11关键原件一致**；Ruff、format日志exit0（作者构建，GPT未本机运行pyarrow/datasets/lerobot）。正式Review `docs/collab/chatgpt/reviews/2026-10-30_V3_NoTTT_Issue12_WorkerColdStart_fd9021b_224c5f3_Incremental_Code_Gate_APPROVE_CODE.md`，**`APPROVE_CODE`仅代码+合成CPU Gate**。
- 新Pair **真实RoboCasa首包<120s、4rank DCP Resume、GPU吞吐尚未运行**；由Owner另批DS真实1Worker首包（含RAM/IO/worker清理）后再决定独占GPU同DCP匹配A/B。禁止直接合并V3/Child、触碰现役NoTTT 30k Job及Checkpoint，EvalV2线隔离，旧301不重跑。

## 2026-10-31 — NoTTT Issue#12 Candidate 真RoboCasa CPU 1Worker首包 Evidence Gate：PASS（DS报告支持）

- Formal Pair Root `fd9021b0908b4b2763b3d02508b1f34df377dc97` / Child `224c5f3c0bd6911bb49cb6bb0895ba7da53ff822`不变，旧合成CPU Code`APPROVE_CODE`不重新审核。DS获Owner授权新真实data CPU probe：真实SingleWorker `first_materialize=14.421s`、`first_packet_total=14.436s`，`status=ok`并通过`NoTTTAsyncLoader.materialize`严格Segment身份；旧单Worker 120.249s timeout。ScopeA进程内新build7.2035s vs旧193.6527s，已减少全源LeRobot构造，Parent eager约192s仍存在。原始数据在DS服务器，GPT独立核对冻源码校验逻辑，未直接验证原始JSON字节。
- **CPU_REAL_DATA_SINGLE_WORKER_FIRST_PACKET=PASS**（严格仅此Gate）；**4Rank×8Worker/DCP C+1/GPU性能 NOT_RUN**。Worker RSS `5917056KiB≈5.643GiB`；`cache_mapped_bytes≈56.59MiB`仅旧Latent/Episode mmap，不是新增Source Arrow LRU；32Worker内存/IO容量必须下一个受控Gate实测，不从单Worker推25x并发余量。
- 正式Evidence Review `docs/collab/chatgpt/reviews/2026-10-31_V3_NoTTT_Issue12_Candidate_RealCPU_FirstPacket_Evidence_GATE_PASS.md`；不重复冷启动探针/旧CPU301、不直接合并V3/修改活跃训练/覆盖DCP，下一步仅在Owner另批后安排独占GPU4–7相同完整DCP的隔离matched A/B commits。


## 2026-10-31 — EvalV2 NoTTT 真实Canary 同卡 EGL/CUDA SIGABRT：DS根因归因过强，A包装脚本不可行（Evidence REQUEST_CHANGES）

- **Formal Source Pair 未变**：Root `d18b420c02cfc51a1b85e9f1d6ce5d26f7bd3163` / Child+Gitlink `2f7334c4ada6ace1d21185985aae90539052bf18`；原双模式增量 `APPROVE_CODE` 保留，不重复代码技术审核。本次只审DS新GPU事故报告；详细Review：`docs/collab/chatgpt/reviews/2026-10-31_V3_EvalV2_NoTTT_EGL_CUDA_Canary_DS_Analysis_Evidence_REQUEST_CHANGES.md`，**真实Evidence verdict=`REQUEST_CHANGES`，`BLOCKED_NATIVE_SIM_SIGABRT`**。
- DS报告3次NoTTT同卡闭环在`mjr_readPixels`附近SIGABRT，纯MuJoCo/随机RoboCasa/Server idle可稳定，跨卡Sim4/5+Server7闭环两集和32次推理稳定；这些是同卡并发/资源压力强关联，但**不证明**“CUDA alloc/free破坏EGL context/已知NVIDIA驱动bug”，真实`iso_*.log`与`GPU7_S0_simulator.log`未由GPT取得；要提供前序stderr/原生错误、EGL设备到物理GPU UUID映射、推理/显存时序。
- **DS方案A shell包装`sim_python`行不通**：Root `robocasa_vendor.py:244-278`要求`sim_python`与真实`sys.executable`/二进制sha相等，shell脚本`exec`真实Python会导致探针身份不匹配；Root `runtime.py:327-332`还硬覆盖`MUJOCO_EGL_DEVICE_ID`，外部export也无效。不得通过绕过身份守卫规避。
- **优先零生产改动诊断**：明确检查 `iso_closed_loop` 有没有发`media`。Child `eval_v2_transactions.py:115-117` 的`save_generated_video=first`仅首个replan请求可选VAE decode，不是每次；可以新输出namespace尝试`save_generated_video:none`但继续`save_rollout_mp4:true`，共享训练不变、同卡仍B2，若iso本来无media则跳过该测试。备选`MUJOCO_GL=osmesa` CPU渲染（需真机可用性/性能/画面预检和记录renderer）。
- 若仍不稳定，则建议Codex **窄改Root config+runtime** 显式Sim EGL renderer GPU与Server CUDA GPU分离（先查物理UUID与renderer显存预算）；不得使用shell`sim_python`包装/改训练/降低B2伪造验证。新Formal Pair需增量Code Gate；不自动授权额外GPU run或900。当前NoTTT/LocalTTT真实B2 Canary均未关闭。


## 2026-10-31 — Owner选择：CPU OSMesa渲染先行，小规模性能/稳定性验收后才考虑EGL异卡方案

- **Owner最新执行指令**：“可以先尝试cpu渲染，如果速度太慢跟不上sim和server，我们再尝试别的方案”。**优先 OSMesa CPU headless rendering**，不触碰 GPU0–3（他人训练满载）；GPU4–7 当前训练/推理共享策略、NoTTT checkpoint、模型参数与正式生产源码保持不变。当前已批准的正式实现 Pair Root `d18b420c02cfc51a1b85e9f1d6ce5d26f7bd3163` / Child+Gitlink `2f7334c4ada6ace1d21185985aae90539052bf18`，此前 `APPROVE_CODE` 保持。此次仅是运行策略，不是新 Code Gate 或新 SHA。
- **DS_PRO 第一步（CPU小烟测）**：在独立新进程环境设置 `MUJOCO_GL=osmesa`、`PYOPENGL_PLATFORM=osmesa`、`LIBGL_ALWAYS_SOFTWARE=1`；使用原本真实 `sim_python` 不采用shell wrapper，不改`verify_source`或Vendor probe。在不修改共享训练环境/不安装系统依赖的前提下，检查 `libOSMesa` 可用、RoboCasa camera RGB/depth、几十步真实 env.step→render/readPixels、2个独立sim兼容；记录 backend和CPU时延、CPU/RSS、设备映射/残余GPU渲染。当前 `runtime.py` 在spawn时仍设置 `MUJOCO_EGL_DEVICE_ID`，OSMesa一般忽略；须在实际worker确认选中了OSMesa，而不是只相信env变量。
- **第二步（仅短测可接受才跑原授权Canary）**：保留GPU7 Action Server、两Sim、B2、NoTTT `local_memory_mode: off`、CloseFridge+OpenCabinet各2集、seed0、prediction_steps30、`save_rollout_mp4:true`；新 `fresh` namespace；不得Resume旧失败namespace。输出真实 `native_batch` histogram（至少存在真正 B=2）、4条有效Core/结果/rollout MP4、Session结束/owned-only cleanup、sim渲染耗时p50/p95、推理与队列等待时间、每集wall time、CPU/RSS/显存峰值，确认训练任务无干扰。可选模型生成视频设置若改变必须单独记录，别把其与渲染后端一起当作单因素对照。
- **速度判据**：不是强制仿真20Hz现实时间；看OSMesa是否显著拖慢env+render、超出既定episode/request timeout、明显破坏两Sim请求重合导致B2长期无法命中，及CPU资源/评测总耗时是否可接受；不可通过取消B2、挪用他人GPU或破坏任务指标伪造通过。
- **若OSMesa缺库、不兼容或明显太慢**：DS只保留可复核日志和性能对比，停止扩大运行；再交 GPT/Owner 决定 EGL异卡（正式显式`render-gpus`新代码/新SHA窄审）或其他办法。**不自动启动900 Episode，不授权额外GPU正式实验，不修改生产代码和训练。**

## 2026-10-31 — Training Issue12 new Lazy Source 4R8W GPU C9620→C9625功能PASS；非独占nw0/nw8表观对比

- Formal Root `fd9021b0908b4b2763b3d02508b1f34df377dc97` / Child `224c5f3c0bd6911bb49cb6bb0895ba7da53ff822`，旧Code/CPU Gate不重审。DS获Owner本次GPU4–7并发豁免，报告5/5 optimizer commits迭代9621–9625，首包24.2s<120s、保存iter9625完整DCP、无OOM；GPT源码post_commit审阅但没有服务器原始日志字节。审核 `docs/collab/chatgpt/reviews/2026-10-31_V3_NoTTT_Issue12_Candidate_4R8W_C9620_C9625_Resume_Functional_PASS_SharedGPU_Perf_INCONCLUSIVE.md`：功能 `PASS_REPORTED_WITH_CODE_CROSSCHECK`。
- 非独占旧nw0稳态P50约20.49s（18步）与新nw8 P50 13.75s（4步），描述性−32.9% wall/吞吐1.49×；因不同时段/原DCP区间/争用和样本不匹配 **speedup INCONCLUSIVE**。nw0 data_prepare与nw8 data_wait不同指标；新gpu_data_stall值没有；不得称current-stream stall下降。下一步只在Owner另授权下排他同DCP matched nw0/nw8；不改正式训练或合并V3。

## 2026-10-31 — Issue12 C12200 Exclusive GPU4–7 Owner授权matched A/B：待Owner完成保存并停正式Job后DS执行

- Owner明确授权正式NoTTT训练在C12200完整Checkpoint保存后**由Owner自己停止并释放GPU4–7**，DS据真实资源检查GREEN执行 **一次正式匹配A/B：同候选Root `fd9021b0908b4b2763b3d02508b1f34df377dc97` / Child `224c5f3c0bd6911bb49cb6bb0895ba7da53ff822`、同源完整DCP C12200独立双clone、同GPU4–7独占/同模型Config/Compact1，A nw0→12220 20 commits，B nw8→12220 20 commits**。严格只改worker配置，前2步冷启动，剩18步稳态P50/P90/mean+current CUDA stream stall，HostRAM/WorkerRSS/清理/DCP验证；无需重复征得这次限定授权。正式request `docs/collab/chatgpt/requests/2026-10-31_V3_NoTTT_Issue12_C12200_Owner_Authorized_Exclusive_Matched_NW0_NW8_20x2.md`。
- S0必须确认正式Job所有PID已退出、GPU4–7无残留且Host资源足、C12200真实DCP complete/rank0–3 sidecars/完整optimizer/scheduler/trainer、双clone原文件不动；若S0失败STOP，不改正式Job、不占GPU；只由DS执行测试、Codex才可改Git仓代码。GPT Remote Desktop设备Offline，不能在DS服务器直接启动；已通过Github Issue发DS执行合同。测试不自动合并当前V3 EvalV2技术线，不改原120sTimeout/正式30000 Training/Checkpoint。


## 2026-10-31 — Owner暂停NoTTT训练至iter12200后的GPU空窗执行顺序（仅运行建议，非新Code Gate）

- Owner通知：NoTTT正式训练预计保存 `iter_000012200` 后由Owner本人暂停，释放 **GPU4–7**；GPU0–3被其他人员使用，严禁触碰。请**不要**由DS/GPT主动停止、kill、修改训练进程或checkpoint；只在Owner确认保存完成、训练退出之后操作。检查 `iter_000012200/model/.metadata`、所有DCP shards、配套 config及其文件大小/mtime稳定，防止读到未完成的checkpoint；即使metadata存在也不等于实际模型必然可加载。训练重新启动前保留原始checkpoint供Resume。
- 本轮继续使用已批准 **Formal Pair Root `d18b420c02cfc51a1b85e9f1d6ce5d26f7bd3163` / Child `2f7334c4ada6ace1d21185985aae90539052bf18`**，没有新implementation SHA、不重新审核源码。运行器为 `scripts/run_robocasa_eval_v2.sh`，实际底层CLI支持 `dry-run/fresh --config --gpus --sims-per-gpu --max-infer-batch-size --local-memory-mode --output-dir`。
- **优先0生产修改**：原`sim_python`真实解释器不变，独立运行前设置 `MUJOCO_GL=osmesa PYOPENGL_PLATFORM=osmesa LIBGL_ALWAYS_SOFTWARE=1`。先测试`libOSMesa`/RoboCasa相机/几十步render→readPixels + 双Sim并行短测，记录CPU/RSS、render step p50/p95、图像形状、是否真实OSMesa；不能仅靠环境变量宣称backend已选择。如果库缺失，不在共享服务器上未经授权安装/升级系统依赖。
- **仅烟测通过才做原授权NoTTT 4Episode**：GPU7模型Server + 2×CPU OSMesa Sim，checkpoint `iter_000012200` 与同源config，`execution_profile:phase_b`、`local_memory_mode:off`、`gpu_ids:[7]`、`sims_per_gpu:2`、`max_infer_batch_size:2`、`batch_wait_ms:20`、CloseFridge/OpenCabinet各2、seed0、prediction_steps30、`save_rollout_mp4:true`。模型生成视频的`save_generated_video`设置保持原值，除非独立登记变更。**新fresh namespace**，不得Resume之前iter10700失败目录。验收四个有效Core/MP4、原生B2 histogram非零、Session/End/owned-only cleanup、CPU/RSS、GPU显存、render/Server latency与wall time，确保GPU0–3他人任务存活。
- 若CPU软件渲染显著拖慢、导致请求无法重叠/B2=0或超时，则**停止扩大**；在GPU4–7空闲期间先做无训练竞争的GPU7同卡EGL短隔离对照。若仍崩，可用DS现有隔离脚本尝试Server7 + Sim EGL4/5，确认物理EGL映射；**现有正式`runtime.py`绑定EGL=Server GPU，不能用shell`sim_python` wrapper绕过**，如需正式异卡EvalV2则交Codex最小新实现/新Formal Pair审核。
- 本次训练暂停的Canary只能证明**无GPU4–7训练竞争**下的功能正确性与性能，不等同未来**与训练并行**的稳定性Gate。若已经稳定，后续并发压力测试应在可控训练窗口按Owner明确授权单独进行。未授权正式900、额外实验、切换TTT权重或合并V3生产分支。
- GPT Remote Desktop Commander设备当前`Offline`，不能从ChatGPT直接操作训练GPU；DS_PRO可在Owner明确训练保存/停止与原Canary许可后手动执行并回传原始证据。不要将本条视为由GPT已实际运行。

## 2026-10-31 — NoTTT控制台只显示Progress，完整日志保留：独立输出层小任务

- Owner希望开始NoTTT Training后终端仅Rank0 `[CorrectedV3][progress]`，但保留完整训练指标JSONL/原始观察者Raw日志、Loader/Rank/异常日志。Frozen phase5中的`TelemetryJournal`已有`[train]`写JSONL不回显；多余`[NoTTT][cpu_loader]`等来自未走Journal的print，因此**建议外层launcher完整tee落盘后只过滤console**，而不是修改Trainer/数据或删除日志。
- 指令 `docs/collab/chatgpt/requests/2026-10-31_V3_NoTTT_Console_ProgressOnly_FullLogs_Preserved_Minimal_Handoff.md`：DS可改自己仓库外下一次启动脚本，以`PYTHONUNBUFFERED=1`+`tee -a full_launch.log`+`awk progress fflush`实现，`PIPESTATUS`透传失败且失败时tail原始日志，正常只progress；真实运行前需保持独占matched A/B frozen命令不变。若要纳入仓库由Codex修改shell的独立可选小Patch，旧training/EvalV2与A/B均不能被日志改动污染。

## 2026-10-31 — Owner要求NoTTT默认Progress-only Console（不是可选/外部手动过滤），Codex生产启动脚本修改任务

- Owner明确要求NoTTT训练开始后终端**默认只显示Rank0 `[CorrectedV3][progress]`**；完整stdout/stderr(含all ranks/NoTTT loader/errors)须记录外部full log，训练结构化`monitor/train_rank0.jsonl`和Observer raw不变。既有TelemetryJournal已不console回显`[train]`，直接loader print仍会刷屏，因此应在Root NoTTT启动脚本外层作全量落盘后只console progress，而不改Trainer。具体Codex实施合同 `docs/collab/chatgpt/requests/2026-10-31_V3_NoTTT_Default_Progress_Only_Console_Codex_Implementation_Order.md`，取代先前“DS仓库外可选过滤”的建议。
- 仅Codex改Git repo标准NoTTT 4GPU/8GPU启动器，默认开启，日志路径不侵占Job namespace，正确传递torchrun/tee/awk失败码与SIGINT，stderr/其它rank真实保留。当前C12200 matched A/B不得改源码/启动命令，不增加GPU/CPU训练Gate。代码**尚未修改**，待Codex隔离候选SHA与shell synthetic evidence供GPT增量Review。
