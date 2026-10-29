# PSM-WMA V3 Issue #9 — No-TTT Async Source/Transform Overlap 独立增量 Code Gate

- 日期：2026-10-29（Asia/Shanghai）。
- **FORMAL VERDICT：`APPROVE_CODE` — 仅限此精确 Formal Pair 的隔离生产源码与作者合成 CPU Evidence。**
- **Formal Root：`e0fe911dfb9fd34957234828195cf051713f6c3d`；Formal Child/Gitlink：`f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`**。
- Baseline：Root `3d5806a2b702b42d3f24e7645aa7cec9cd70b0c7` / Child `746c5cf2f2324104a62fb71510343aa40d3976c5`。
- Candidate：`v3-nottt-async-overlap-20261029`。Author Evidence/Handoff HEAD `c645d3d6452f6817a888c5b3e429b3f6b143762e` **仅为 docs/Evidence HEAD，不是正式代码 SHA**。
- Owner frozen contract：`docs/collab/chatgpt/requests/2026-10-29_V3_NoTTT_Async_Data_GPU_Overlap_Codex_Implementation_Directive.md`；Issue [#9](https://github.com/wxwy/psm_wma/issues/9)。既有 #4 的 nw>0 RAW worker 代码不自动满足本新 Gate。
- 本轮 **没有** 在 GPT 环境执行 Torch/pytest、真实数据、模型、CUDA、DCP 或服务器性能测试；评审基于 Formal Git 树、真实源代码、完整 Author JUnit/Gate/Trace 与实际修改 Diff。未操作活动正式 Job。

## 一、Formal 源码范围核验

1. 直接从 GitHub 读取 Root formal commit/tree，`cosmos-framework` mode160000 Gitlink 精确为 `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`；V3 主分支仍为历史 Child `746c5cf2...`，候选未合入。
2. 对 Root baseline→formal 的4次增量：仅 `SESSION/TODO`、两份设计说明、`tools/v3/no_ttt_workers_entry_test.py` 与新的精确 CPU Gate Runner，以及 Child Gitlink；没有修改 Root 训练 launcher、configs、Vendor、G1。
3. Child baseline→formal 的3次增量：新增 `trainer/no_ttt_async_recipe.py`、`trainer/no_ttt_async_loader.py`及关联合成测试，窄改 `matched_no_ttt.py`、No-TTT loader runtime profile、cached-SFT 仅生成重建 metadata，以及原有两处测试 fixture。未修改 model/Generation optimizer、generic Trainer、DCP writer、原 Frontier schema、Local-TTT/G1。
4. Author `formal_source_bindings.json` 列出的 **18/18 当前正式 Root/Child Git Blob**，由 GPT 逐项直接 fetch 比对完全匹配；Author Handoff/evidence 提交在 Formal 后仅包含 docs/证据与记录，不构成另一新 implementation pair。

## 二、真实行为审核（Contract → Source → Evidence）

| Contract | 实际源码和权威行为 | Code Gate 判断 |
| --- | --- | --- |
| `NOTTT_LOADER_WORKERS=0` 保持同步历史路径 | `matched_no_ttt.py:230–233,266–288`，0时仍走原 `producer.produce` 和原 Pack/Collate/H2D/Native training | 通过（源分支保持） |
| `nw>0` 真 CPU worker Source/Transform | `AsyncRecipe.from_producer/build` 封装已冻结 local Index/Source/Cache/JSON SFT；`AsyncWorkerState.prepare:277–299` 在 spawned worker 中调用真实 `producer.prepare + materialize`；`PreparedDataset.__getitem__:129–160` 传送有界 CPU bytes | 通过（合成 CPU 类内/进程路径） |
| 跨 Member/跨 Window 的真实 overlap | `NoTTTAsyncLoader._begin:245–284` 预览 active 的 candidate frontier 对应下一 Window；`_materialize:286–375` 按请求顺序取回，并在 current GA native 计算时异步推进后续 Source/Transform；父进程不再同步完成大块 Transform | 通过（CPU fake-compute 时序 Gate） |
| 原 RNG/CFG 保持 | `_known_pipeline:25–99` fail-closed 仅支持已知 JSON pipeline + `legacy_global`；worker 用 cfg_dropout=0 准备 conditioned + empty tokens，主进程 `_materialize:340–345` 在原有效 Consumer 顺序消耗 `random.random`，没有 per-sample seed 或 speculative RNG 前进 | 通过（当前受限能力，需真实 tokenizer Gateway 验证） |
| Frontier / Optimizer / Save-Resume | `MatchedNoTTTTrainer.training_step:266–361` 只有 GA4 backward 完成且 optimizer 成功后 `window.finish`，再 `loader.finish`；`NoTTTFrontierCallback.state_dict:140–159` 保留原 format/strict sidecar；下个 `begin` 强制核对 preview predecessor | 通过（作者 synthetic CPU） |
| Identity、资源有界、失败 | 请求 token、generation、Window、owned worker PID、Segment provenance、Source/Cache stat 核验；单 packet cap 默认32MiB，prefetch1/nw8 最多256MiB编码队列/RANK（另有 worker内存）；异常关闭进程、清除 pending，失败 Trainer poisoned | 通过（代码＋fault tests） |

### 独立 Evidence 交叉核验

- 从已提交的 **原始** `final/async.xml` 读到72个 testcase，`final/regression.xml` 与冻结 `final/gate.json` 合计 **301 tests，0 failures，0 errors，0 skipped，`source_unchanged=true`**，精确 Root/Child/Gitlink 一致。Ruff/format/AST13 均记录 exit0；GPT未宣称亲自运行 CPU suite。
- 1个真实数据 optional 节点以 `--deselect` 明确排除，**不计算为PASS，也不伪报为skip=0代表全量真实数据已测**。
- 直接读取 `final/timelines/overlap_trace.json`，独立按每个 CPU Source/Transform 与 fake GPU compute 的 `max(0,min(end)-max(start))` 重算：后续 Member Source **96.257ms**、Transform **160.573ms**；下一 Window Source **24.373ms**、Transform **38.022ms**。时间线中96个 Source、96个 Transform、12个 fake-compute interval、3次 commit；交集分别有18/18/4/4个非零配对，确实不是“只创建 worker PID”。
- 相同日志明确 **CPU-only cold spawn 短测 async7.761s vs serial3.315s**，主线程 wait累计5.972s。仅证明同时性，不证明更快；不得向 Owner 声称 GPU 训练收益已完成。旧 Raw Backend 的 RED witness 仅作为负例，不计入301失败。
- `bounds/bounds.json` 含8个真实子进程 PID及reaped，synthetic RSS各约503MiB、sample packet271437bytes；真实world4/8worker/rank所需RAM、I/O、processor启动、cache mmap与性能未测。
- 作者保留了旧失败的 fixture attempts；`protected/audit.json` 102条旧assert AST保护为作者内部证据。GPT未把作者内部source audit等价为独立全测试执行。

## 三、明确保留的未闭环项目（不新增本 Code blocker）

1. **Real processor/reconstruction**：`AsyncRecipe.from_producer` 硬要求已staged local `Nemotron3DenseVLProcessor`，CPU真实Source/Cache实验使用合成文件和fake processor；真实 Cache/Index/Tokenizer/DROID Model 从nw0→nw8的 on-site 4Rank、DCP和Runtime没有执行。若Native时出现不符，按新Bug/Gate处理，不反向声称此 Code Gate验证了真实资产。
2. **Numerical parity**：先前 Compact 0↔1 GPU strict gradient `FAIL_PARITY`、Dense0→Dense0重复性未达冻结阈值、Compact独立影响 `INCONCLUSIVE` 保持，不因本异步源码合格而变更。此CPU测试不能证明GPU数值等价。
3. **Performance**：CPU并发存在不代表真实GPU利用率提升。后续真实Compact1 `nw0` 对 `nw8` 需匹配Checkpoint/数据，测 CUDA forward/backward、CPU读/Transform、GPU data stall、完整 Step Wall P50/P90、Host RAM/worker errors及共存干扰，不能外推10步nw0均值20.32s为nw8加速。
4. **Failure/RNG on CUDA**：作者只以CPU合成模型验证 0→8 / 8→0 / 8→8全状态续训及失败；真实CUDA RNG/optimizer scheduler/4Rank Frontier/DCP恢复仍待独立真实 Gate。
5. **Nonpersistent mode**：显式关闭 persistent worker 会丢弃跨Window preview，不是目标吞吐配置；推荐 `nw8,prefetch1,persistent1` 进入后续GPU阶段。真实内存容量不能仅按synthetic RSS推算。

## 四、正式结论和严格执行边界

**VERDICT = `APPROVE_CODE`，只关闭 Issue #9 这个精确 Formal Pair 的隔离生产源码＋作者 CPU Evidence Gate。** 当前没有证据足以确认一项违反冻结行为合同的生产源 blocker。**不能**把此 verdict 写成GPU加速PASS、真实DCP Resume PASS、正式Job切换授权或完全数值等价声明。

下一步按已授权分工派 **DS_PRO 在隔离干净 exact-pair Root/Child 上做一次独立301项 CPU Gate**，原始 JUnit、负例、时序、Source绑定和进程cleanup回传。要求详见 `docs/collab/chatgpt/requests/2026-10-29_V3_NoTTT_AsyncOverlap_DS_PRO_Independent_CPU_ExactPair.md`。如DS有真实代码失败，原Gate重开；如DS独立CPU PASS，再由 Owner 独立决定 isolate real DCP/GPU Canary 和最终原Job checkpoint边界切换。

**不授权：** 合并V3或Child正式分支、停止/重启当前正式 Job、改旧 identity/checkpoint/source/cache、直接GPU/model/DCP/RoboCasa训练/评测、30k续训、任何自动Runner/PID清理外部进程。ChatGPT本轮不实施源码修复。正式源 target 是 e0fe/f6a92；此次Review/Inbox/DS Request commit只属Bookkeeping。
