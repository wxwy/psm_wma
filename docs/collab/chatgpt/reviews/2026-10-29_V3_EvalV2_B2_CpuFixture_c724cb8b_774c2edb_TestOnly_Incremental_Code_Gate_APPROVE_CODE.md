# PSM-WMA V3 EvalV2 Phase B B2 — CPU Fixture Test-only Narrow Code Gate

**日期：**2026-10-29。**Formal verdict：`APPROVE_CODE`，仅限本次 test-only 生产候选源码增量。**

| 身份 | 精确 SHA |
| --- | --- |
| 新 Formal Root | `c724cb8b1ac74c8b1748bdaac95450fb0635a095` |
| Child / Root Gitlink | `774c2edb93ec5a6ba85ba1124757064d7cc779a5`（未变） |
| 上一已批生产 Formal Root | `323f0b2a3d4aa3b40d9d8f2eb0b94c9251299728` |
| 新 Root 直接父节点 | `c8e672db1f4f8870d573d26f19fa2895ea2cd000` |
| Candidate Branch | `v3-eval-v2-cpu-fixture-20261029` |

## 1. 技术范围 / 版本证明

直接读取 GitHub 新 Root commit 与 `HEAD:cosmos-framework`；Child Gitlink 精确等于冻结值。新 Commit 与其直接父节点之间**仅有两文件**：`tools/v3/eval_v2_batch_tests/runtime_test.py`（blob `b5f2d254310926375155636e6ea2698f86575fbe`）和 `tools/v3/eval_v2_batch_tests/os_fixture.py`（blob `cb960a7c9c365fa8dfc83e61303a92a1881a9b09`）。旧生产 Base→当前差异中的其他项目 docs/evidence 提交早已存在于候选父节点；不把它们算作本次夹具修复，也不重复扫描/批准。Root `scripts/`、`configs/`、原生产 Eval 及整个 Child 没有本次语义变更。

以前 Phase B 第二批 Formal Root `323f0b2a` / Child `774c2edb` 的 `APPROVE_CODE` 不撤销，但不自动迁移新 SHA；本轮对**真正新增的测试 Diff**作全量针对性审核后给出上述新 Pair 源码 verdict。既有 DS_PRO 独立 CPU Evidence Gate 仍是 `REQUEST_CHANGES`（evidence-only）。

## 2. 逐项技术核对

**F1（先前环境端口错判）— CLOSED，test-only。** `runtime_test.py:33–51` 的 `free_ports` 现在通过 `0.0.0.0` 探测连续端口，与未变的生产 `scripts/eval_robocasa_18task_queue.py::require_free_ports` 一致；保留最多30次尝试并在每轮 `finally` 关闭所有 Socket。新增参数化两个不同回环地址 `127.0.0.2/127.0.0.3` 上的真实 listener 后，用 Probe 固定 `port=0` 指向已占用端口；旧仅127.0.0.1的实现会错误接受，新实现在30次后抛出，且30个探测 socket 已关闭。该负例直接使用 OS socket，而非仅模拟一个返回值。测试不会关闭或重配现有训练服务。通配 bind 和随后 Server bind 之间仍存在普通 TOCTOU 小窗口，本轮不扩成套接字继承改造。

**F2（每拓扑都强求B2）— CLOSED，保留正向强证明。** `runtime_test.py:210–222` 现在所有场景都要求合法 Batch size `1..2`，保持 `sum(size)=2×N×episodes`、per-Server PID 数量、前沿预测逐个正确匹配；只有 `G1/N2/E2` 同 Server 场景继续要求**真实 OS日志中至少一次 size=2**，未以人工拼凑或假日志替代。 `G2/N3/E1`、`G1/N3/E1` 只移除依赖随机请求时序的“每轮必然合2”不成立假设；原有实际 Sim overlap、Session assignment、D5 round barrier、Core 及 completed Resume 字节不变/no new model-Sim probes、进程回收仍逐项断言。Child native Batch 代码及更低层 B1/B2/B3/hot-cold/exact-call 测试完全未变。

**F3（Server死亡故障注入过度依赖恰巧B2）— CLOSED，测试因果更强。** 新 fault case 在 `cpu_run(... fail_server=True)` 时令模型 cap B=1，避免需先合B2。真实 Model Owner `generate` 首成员已 `GENERATING` 时读取被测试生产事务对象的实际锁保护 `_leases/_tickets`，最多20s等待第二个来自另一 Slot 的有效 `QUEUED` ticket；核对两 distinct Slot、Session、Task、Attempt、Episode、run lease、manifest digest 等实际 owner identities 后才记录 `CPU_SERVER_FAULT` 并 `os._exit(23)`。这是 fixture 内只读检测并触发故障，不修改生产排队/commit。 `test_owned_Server_death...` 断言这两个未提交 ticket 属于真实 Server PID、最终 valid=0/不具完整资格、两个 Task 有未结案错误、所有 1 Server+2 Sim 的关闭回执存在且存活PGID为空、Server exit23、外部 foreign 进程未受影响。20s deadline 导致未达前提时**失败而非假造PASS**，避免默默弱化 fail-closed。

## 3. 作者与独立证据界限

作者在本 Formal Commit 消息及本次交接报告声明聚焦 `phase_b_runtime` **26 passed、0 failed/errors/skips**，Ruff0.12.7 check/format、AST29均通过；24项旧运行时 +2项新增负例，完整统一 Gate 预期 `145+255+26=426`。新 Formal Root commit 本身**只包含两个测试源码文件，没有发布本轮原始26-case JUnit/pytest/Ruff日志或外部执行环境快照**。因此本次 GPT **只确认报告与源码测试数量/语义一致，未独立核对26项原始执行字节，未自跑CPU**，更未声称独立DS426 Gate已通过。

本次 `APPROVE_CODE` 为**test-only源码正确性范围**的批准，足以进入已既定的独立DS执行验收；**不是**对作者测试原始Evidence或 DS Evidence Gate 的替代批准。如果新的独立DS用例失败，须按首个真实错误区分测试、环境或生产缺陷，避免重复启动整套 Gate。

## 4. 后续仅一轮 DS 完整CPU

DS仅在**新、干净、隔离、精确 Root `c724cb8b1ac74c8b1748bdaac95450fb0635a095` / Child `774c2edb93ec5a6ba85ba1124757064d7cc779a5`** worktree，外部全新 Evidence 目录执行现有统一入口：

```bash
python tools/v3/run_eval_v2_batch_b2_cpu_gate.py \
  --root-worktree '<EXACT_CLEAN_ROOT_WORKTREE>' \
  --expected-root c724cb8b1ac74c8b1748bdaac95450fb0635a095 \
  --expected-child 774c2edb93ec5a6ba85ba1124757064d7cc779a5 \
  --evidence-dir '<NEW_EXTERNAL_EVIDENCE_DIR>'
```

**硬验收：** shell exit0、`gate.json.status=PASS`、三个身份精准一致、`source_unchanged=true`、三个 test groups 分别 145/255/26、总数426、0 fail/error/skip；`G1/N2/E2` 真实 B2、其他拓扑合法 B1/partial/路由且真实 Sim overlap、故障注入 exit23及两个 active tickets/全部 owned group cleanup、完全有效 Resume 不重启资源。核查 Ruff和OS source-before/after；保留已有前两次 FAIL evidence，独立新证据单独留档。DS只提供一次汇总与原始证据引用，不改生产/测试、不改在训Job。

新 Root test-only 已通过源码 Gate。下一步不要再提出第三批架构整改，也不要给此技术 Pair 重复源码审核。**本批准不授权合并V3/Child生产代码、GPU/Cosmos/DCP/RoboCasa/1GPU Canary/900集或训练/Checkpoint/Vendor修改**；均由Owner另行决定。
