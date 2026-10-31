# V3 No-TTT Issue #12 Async Lazy Source → Canonical Child 移植 — 独立增量 Code Gate

**日期：2026-10-31；正式 Verdict：`APPROVE_CODE`（仅本精确Canonical-based隔离移植Pair与定向synthetic CPU Evidence）。**

- **Formal Root** `c66ade95b044d3664cd782d43d7917a604425db3`；**Child/Gitlink** `baf1b5bf46853e9849a91518803b9738fc216235`。基线Canonical V3 Root `2bcc27e94576837167cacd190af7dc837e6129cd` / Child `0ae313e329d290fc6b8a50fda1112820fb7ac485`。已批准的真GPU性能donor Root `fd9021b0908b4b2763b3d02508b1f34df377dc97` / Child `224c5f3c0bd6911bb49cb6bb0895ba7da53ff822` 是另一个历史Pair；**本轮只审核移植差异，不重新批准或重跑donor GPU**。Codex交接docs SHA `fe28a51185b85b512d3ebdf14a089b732dd18f9b`不是Formal Implementation SHA。
- 实际Canonical baseline在`MatchedNoTTTTrainer.bind_grouped_stream`仍绑定Raw/`NoTTTCpuLoader`，缺`NoTTTAsyncLoader`及AsyncRecipe，故只拷贝Lazy Source+Recipe两文件**不足以使线上配置使用新路径**。本轮受审完整最小依赖闭包为**6个生产文件+7个测试/支持文件**（Root额外测试1个），不是无理由扩大算法改造。

## 1. 生产Scope与精确Donor等价

- 6个生产文件：Child新`no_ttt_async_loader.py`、`no_ttt_async_recipe.py`、`no_ttt_worker_source.py`；修改`matched_no_ttt.py`(nw>0路由/Frontier边界)、`no_ttt_loader_profile.py`(async runtime profile/identity)、`robocasa_exact_window_cached_sft.py`(重建原Transform metadata)。七个配套Test/support改动受限。模型、损失、optimizer、checkpoint、官方 SourceReader、`120s` timeout、Job Identity、RNG、正式launchers未变。
- GPT独立从GitHub Fetch File的**实际接收Child**取得上述**13/13文件Git Blob SHA**，逐项同已审donor对应Git Blob SHA交叉一致，无一不符（不只是作者的assert或文件名）；现有Child baseline→candidate GitHub compare精确只有这13个文件。
- GPT进一步独立读取Canonical、Port与Donor三个Child Git Tree：Port `cosmos_framework/trainer`、`data`、`utils`、`model`、`checkpoint`、`configs`及`examples`的整树SHA与donor完全相同；**Port `cosmos_framework/evaluation`、`inference`、`simulation`、`model`、`checkpoint`、`configs`的SHA均与Canonical `0ae313e3`相同**，保留EvalV2而没有整棵旧子模块回滚；根仓训练4/8GPU launcher未改。作者`object_equivalence.json`的1255 unchanged对象也与GitHub差异一致，但该1255数字属作者清单，不声称逐对象重新枚举。
- 原donor合成CPU Code Gate和C12200同DCP独占matched Step Wall `APPROVE_PERFORMANCE`都绑定旧donor SHA；此移植由于训练链路对象**字节级完全一致**，具备沿用donor行为证明的条件，同时仍必须通过本独立Formal Pair的集成测试与Gate，不把旧donor verdict直接转移。

## 2. 接收端真实绑定与合成Evidence

| Contract | 证据 | 结果 |
| --- | --- | --- |
| `nw0`走原同步、`nw∈{1,2,4,8}`真正建Async Worker Loader；不落回旧Raw | Root新增`tools/v3/no_ttt_async_port_test.py`直接使用**实际**`MatchedNoTTTTrainer.bind_grouped_stream()`与真实`NoTTTAsyncLoader`类，在0/1/2/4/8下验证类型、worker仅lazy启动、API/checkpoint callback、训练binding未漂移。仅Recipe元数据使用合成seam，不替换真实Trainer binding。 | PASS |
| Stable Frontier/CFG/Source/Runtime identity、不把Worker配置混入训练状态 | `test_async_runtime_ownership_is_explicit_without_mutating_legacy_identity[1,8]`，源Episode/Padding/Caption/Row identity逐值对照、worker-source绕过全量LeRobot构建、LRU bounds、source mismatch/corrupt data fail-closed；NoTTT本来的20步/A-B真实 GPU历史donor保持不重跑 | PASS（测试为合成CPU，未测新Pair真实GPU） |
| 按真实Trainer lifecycle跨Window异步CPU并与同步raw值对齐；CPU全状态Resume无错位 | 定向regression测试跨member/window overlap、T16末段、RNG、source file changed拒绝、0→8与8→8、rank3、failed window/worker cleanup、same-job config identity；有原始JUnit。 | PASS |
| Canonical EvalV2与其它子系统不变 | GitHub Child Git compare与上述subtree SHA独立核对，只有13个受准入文件变化；Root extra test不是训练生产代码。 | PASS |

## 3. Evidence独立验收

- Codex原始包：`docs/collab/codex/evidence/2026-10-31_nottt_async_lazy_canonical_port_author_cpu/`（docs Handoff `fe28a51185b85b512d3ebdf14a089b732dd18f9b`）。GPT直接读取`junit.xml`、`async.xml`、`regression.xml`：**33+10=43 unique passed，0 fail/error/skip**，不把早期7项重复累加。
- GPT使用独立SHA256实现核对`artifact_manifest.json`的**3/3关键原件**`junit.xml`、`gate.json`、`object_equivalence.json`，均字节级SHA匹配；`gate.json`的import origin、Ruff0.12.7 check+format、14个文件语法检查及两组synthetic CPU运行均exit0；GPT没有本机重跑，未调用真实GPU/真实DCP。
- 作者原始日志保留`pynvml` deprecation、nw8高于CPU affinity建议及resource_tracker两枚Semaphore告警。已有测试检验owned worker正确回收，这些告警不构成当前Code Gate的已证 blocker；不能据此宣称长期CPU RAM/IO耗尽风险已完全消失。

## 4. Verdict/后续条件

**`APPROVE_CODE`**（接收端已正确接线、捐赠代码13/13字节身份、EvalV2对象保留、43定向合成CPU行为）。无残留当前生产blocker，本Gate完成；不重做donor旧301/58或GPU matched A/B。

**不等于**：Canonical V3已合并、不授权Owner正式30k重启、不证明本新组合Pair已在GPU重跑。当前Issue#13默认Progress-only仍是另一隔离候选，不能因本Port批准顺手合并历史Root树。

**最少下一步**：Codex从最新Canonical V3创建clean整合候选，合入已批Port Child+Gitlink与Issue#13 Root日志最小改动，保留EvalV2；只审核新组合Formal Pair的Git Blob和已有必要shell/receiver接线证据。生产Resume仍用**正式原始C12200 DCP**而不是A/B生成的临时DCP，并由Owner另行明确授权。

本Review与Canonical Inbox共同落盘才构成正式Verdict；docs-only SHA不代替Implementation Pair。