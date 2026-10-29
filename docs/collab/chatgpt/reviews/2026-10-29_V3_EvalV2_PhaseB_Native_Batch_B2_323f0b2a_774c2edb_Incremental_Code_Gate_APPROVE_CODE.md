# V3 Evaluation V2 — Phase B 第二批增量 Code Gate

- 日期：2026-10-29（Asia/Shanghai）。
- 审核者：GPT；独立源码与作者原始证据核查，包含 Batch 事务、运行时/Sim 接口、版本/CPU 证据三个并行子审，主审复核 Native Generation 调用及关键结论。
- **正式结论：`APPROVE_CODE` — Phase B 第二批多 Sim / 多 Session / Native Batch 源码通过。**
- 本轮未发现需要 `REQUEST_CHANGES` 的新增可达阻断问题。此结论不是 DS 独立 CPU 或真实 GPU/RoboCasa 验收。

## 1. 唯一正式审核对象

| 身份 | 完整 SHA |
| --- | --- |
| Formal Implementation Root | `323f0b2a3d4aa3b40d9d8f2eb0b94c9251299728` |
| Formal Child / Root Gitlink | `774c2edb93ec5a6ba85ba1124757064d7cc779a5` |
| 已批准第一批 Root | `dc7757922d7273f50f3de23363d41e12e157a07f` |
| 已批准第一批 Child | `4a938e41b0c335baca1c1d8f1caabc433b0e2001` |
| 第一批批准 Review docs commit | `66a5b99c0a23312525ccbdc0fadb4655bc7d0b19` |
| 本轮固定作者 Evidence ref | `e549a4f5e5d0b3f90a75cd37e047f006af90c94b` |

候选分支为 Root/Child 的 `v3-eval-v2-batch-b2-20261029`。本轮远端锁定时 Root 候选 HEAD 为 `c8e672db1f4f8870d573d26f19fa2895ea2cd000`，Child HEAD 等于上述 Formal Child。Root Formal→候选 HEAD 的 4 个后续提交仅涉及 docs/SESSION/TODO；未改变正式生产源码或 Gitlink。Evidence、发布回执及本 Review 的 docs SHA 均不替代 Formal Pair。

已直接读取 Formal Root 的 `cosmos-framework` Gitlink，类型为 submodule，值与 Formal Child 完全一致。Child 相对批准第一批为 1 个提交、12 个变更文件；Root 技术变更集中于 5 个 eval-v2 运行模块、新示例、统一 CPU 入口及测试。并行 Compact 文档不属于本次技术审核对象。

## 2. 审核范围与继承关系

仅审查 `dc775792→323f0b2a` / `4a938e41→774c2edb` 的第二批增量及其实际影响接口。已批准 Phase A、Phase B r1+r2+r3 设计和第一批保持原结论；`B1-F1 CLOSED`、`B1-P1 WITHDRAWN` 不重开。本次 `commit_many` 影响旧单成员提交，因此同时检查该委托路径与新 B=1 回归。

源码 Gate 关注当前正常入口可达、影响状态/动作/调度/恢复的错误。未添加新设计 Gate、第三批架构工作、参数扫描或历史阶段重复验收。未修改生产代码，也未执行项目测试、GPU、Cosmos/DCP 加载、RoboCasa/EGL、训练或 900 集评测。

## 3. 关键源码结论

### 3.1 多 Sim 入口与同卡模型所有权已接通

Root `scripts/robocasa_eval_v2/resources.py` 的 `physical_slots()` 按 Slot index / GPU 顺序构造 `min(G*M,N)` 个有用物理 Slot。`runtime.py:57–64,143–236,238–421` 每个 used GPU 只创建一个 Server，每个物理 Slot 一个独立持久 Sim；setup lock 防止并发重复初始化。Task 切换继续走已有环境 close/rebuild；同 Task 可复用环境。

`runtime.py:460–543` 先经过已有 D4 初始化准入与采样绑定，随后才由 Coordinator 注册 Session。私有注册 capability 留在 Coordinator；Sim 得到精确 assignment ACK。Child `eval_v2_slot.py` 检查 run/manifest/physical Slot/Task/Episode/Attempt，再进入已有原生 action/evidence loop。

`runtime.py:720–790` 复用原有 RoundScheduler、Store 和 round barrier；本次没有替换 D1–D5 的 authority。`config.py:125–139,191–201` 显式选择 Phase B，默认 Phase A 仍拒绝 M>1/B>1。`identity.py`、Child `contract.py` 以及 `Runtime.__init__:48–49` 同时约束冻结 manifest 的 GPU IDs/M/B/wait/noise/profile，禁止同一 Run 静默改变执行配置。

### 3.2 真实模型调用边界为一个 Batch，一次生成

Child `cosmos_framework/scripts/action_policy_server_robocasa.py:1231–1287`：

- 为 B 个样本构造对应 observation、state/action carrier、prompt、domain、SequencePlan 和 action-processing record；没有循环调用单样本 policy Generation。
- `:1251–1258` 仅调用一次实际生产 `self.model.generate_samples_from_batch`；传入长度 B 的 literal seed 列表和逐样本 prefix tuple，cold 项为 `None`。
- `:1259–1266` 按原有顺序拆分并去除 state-conditioning 首行，再由 Actor 检查每成员 finite `[16,15]` 后发布。

主审进一步检查未改的实际 `omni_mot_model.py:3698–3728,3871–3899,4109–4147`：模型 API 接受逐样本 seed/prefix，按 native batch cardinality 验证并挂接 Local prefix，Generation 的 velocity 路径携带完整 sequence plans / clean batch。`memory_prefix.py:50–69,85–124` 保留 mixed hot/None/hot 的独立 sample offsets。这里确认源码调用接口正确；完整模型的 GPU 数值及实际显存/吞吐仍需真实 Canary。

### 3.3 Fast / Visual / Frontier / Response 一次事务发布

`robocasa_local_memory_policy.py:215–246` 中旧 `commit()` 委托 `commit_many()`。后者在同一 store lock 下验证每个 pending capability 与 predecessor、拒绝重复 Session、预先构建完整 Fast/Visual/Response 映射，唯一发布点为 `:243` 的 snapshot 替换。Frontier 随 fast/visual replacement 一起发布，没有逐成员先后提交的中间状态。

`robocasa_batch_transactions.py:190–323` 在一次 `generate_many` 后检查 cardinality、finite shape、序列化和响应上限；`:263–273` 先 quiesce，再对每个成员做 deadline/lease/closing fence，最后一次 `commit_many`。sealed 后任一成员出错统一 abort 所有未提交成员。无法证明 drain/abort 成功则 quarantine，保留 unresolved ownership。

排队项从 `_queue` 移除时不释放 `_tickets` 所有权；成功项保留到 delivery ACK/End，失败项到 quiescent 后才释放。pre-seal cancelled/expired/closing 成员先单独移出处理，不牵连尚未 sealed 的有效 peers。上述边界由 fault matrix、短成员 deadline、Generation 中 End、pre-seal End 等新增测试覆盖。

### 3.4 Session 清理、重试与分发闭环完整

`robocasa_transaction_client.py:45–68,119–180` 的 POST/轮询/429/503/网络重试/ACK 继续使用同一原始 deadline。完整 assignment、request key、payload hash、frontier、Local status、batch ID/size/index、finite actions 验证发生在 ACK 和返回动作之前。已 ACK replay 沿用原 cache-first admission，不重新创建 ticket 或更新 Fast State。

`eval_v2_transactions.py:83–113` 不允许同一成功 frontier 再次 delivery；预测失败后必须 End/新 Attempt，不能在外层重新调用 predict 延长预算。`closed_loop_eval.py:447–491` 的原生 finally 清理，经 facade reset→End、`eval_v2_adapter.py:225–227` reset_ok 检查和 Slot reset_ack 验证后，Slot 才回到 CLEAN。Root Core commit/finish 位于 execute 成功返回之后。

`robocasa_session_transactions.py:415–432` 仍先等 executor/owned ticket quiescence，且 quarantine 时不返回成功 End ACK；reset 只清理对应 Session。新增 hot/cold/hot 测试检查 prefix offsets `[0,4,4,8]`、Fast tensors 不共享、W0 不变/无 grad，以及 reset 一个 Session 不影响另一个。

### 3.5 可选媒体不成为新的动作状态 authority

`robocasa_batch_transactions.py:325–411` 使用同一模型 executor 处理有界 CPU spool 的可选 decode；普通 decode/spool/mapping 错误保留为 media diagnostic。动作事务先发布，decode 不参与 SR 判定。`eval_v2_transactions.py:142–231` 的 background fetch 验证 key/hash，End 先设 delivery fence；晚到响应不能写入已关闭 sink。

未知 device drain 或未结束的 owned helper 继续按基础设施故障处理，不伪造清理成功。该保守行为与现有 D1 资格语义一致，不要求另起媒体架构整改。

## 4. 作者 CPU Evidence 的独立核对

固定目录：`docs/collab/codex/evidence/2026-10-29_eval_v2_phase_b_native_batch_b2_author_cpu/`，全部按上述 Evidence ref 读取。

| 原始 JUnit | 实际 testcase 数 | Failure / Error / Skip |
| --- | ---: | --- |
| `final/inference.xml` | 145 | 0 / 0 / 0 |
| `final/phase_a_regression.xml` | 255 | 0 / 0 / 0 |
| `final/phase_b_runtime.xml` | 24 | 0 / 0 / 0 |
| **总计** | **424** | **0 / 0 / 0** |

核对 XML suite attributes 及实际 testcase 数，一致。上一批 99 项 inference 和 255 项 Phase A 的完整 classname:name 全保留；exact compare 未显示旧测试源修改。新 Batch profile B=1 参考在 `robocasa_batch_transactions_test.py:328–344` 以 rtol=0/atol=0 比较动作和真实 CPU Fast State。

`formal_source_bindings.json` 的 61/61 GitBlob 已逐一对照精确 Root/Child 文件一致；52 个运行期 source fingerprints 对应正式 bindings。`final/gate.json` 的 Root/Child/Gitlink、全部 step exit code 0、source_unchanged=true 相符。Ruff 0.12.7 check/format、AST 29、import origin 的原始记录支持作者声明。

作者第一次 clean Pair `cd538b0d.../774c2edb...` 的 421 PASS 与 wrapper 错误退出码负例单独保留。正式 Root 的 thin wrapper 已 `raise SystemExit(main(...))`；新增 3 项 entry tests 覆盖 0/1 传播及实际 wrong-pair 子进程 BLOCKED/exit1。最终 424 已重新绑定本次 Formal Root，未以旧 421 代替。

### OS 子进程证据支持到什么程度

| CPU fixture | Server / Sim | 实际 fixture generation size 记录 | 有效 Core |
| --- | --- | --- | ---: |
| G1/N2/E2，M2/B2 | 1 / 2 | B1×2，B2×3 | 4 |
| G2/N3/E1，M2/B2 | 2 / 3 | B1×4，B2×1 | 3 |
| G1/N3/E1，M2/B2 | 1 / 2 | B1×2，B2×2 | 3 |

原始 execute_begin/end 跨 PID 区间确实重叠；例如 G1/N2/E2 的两轮交集约 0.123 秒与 0.456 秒。日志含 cold/hot 混合及新 Episode cold 状态。测试验证 logical plan/round barrier、精确 response assignment、Task 切换、Session 清理；完成后 Runtime.run 的 Resume 不触发 resource probe、不创建 Server/Sim，已提交 result.json 字节不变。

负例 Server close receipt 的 returncode=23 对应 fixture 仅在 size>1 generation 内退出的分支；所有 owned group 关闭回执记录 live_group=false、remaining_pids=[]，报告不具备完整结果资格。无关进程存活由最终 PASS 的测试断言支持；不声称发布了额外独立 foreign-PID 收据。

**证据边界：以上是作者实际 CPU 执行记录，经 GPT 独立源码/证据核查；不是 GPT 或 DS 独立重跑。** Local encoder/scan/state、native input/prefix helpers、Client→Dispatcher→Actor、Runtime/Worker/Core、HTTP/OS 进程实际执行；完整 diffusion/WAN、模型权重、物理环境及 kernel bytes 为显式替身。`CPU_NATIVE_BATCH` 不是完整模型已经上 GPU 的证据；合成 900 也不是 Success Rate。

实际 cloud clock probe 仍为 `BLOCKED_KERNEL_IDENTITY_UNAVAILABLE`、production_bypass=false。目标服务器正常 exec 的 active/children/domain 检查已在 `identity.py:193–200,254–280` 接入启动前置；留到真实目标环境核验，不重开时钟域设计专题。

## 5. Gate 决定与下一步

**本 Formal Pair 第二批增量：`APPROVE_CODE`。无新增阻断 finding，无需追加架构批次。** 与已批准 Phase A、第一批结合，完整实现候选进入既定验收阶段；作者 424 不能替代独立执行验收。

后续保持三步，不重复已关闭阶段：

1. 在该精确干净 Root/Child 上，由 DS 按既定授权执行一次完整候选统一 CPU replay，保留原始 Gate/JUnit/import origin/source-before-after/OS cleanup 证据。
2. CPU 验收通过后，另行 Owner 授权小型真实 **1 GPU / M=2 / B=2** Canary。确认实际模型 B>1、Session 隔离/清理、正确任务环境、动作有限、显存与时间；测量必要的跨 Task 环境重建成本即可，不扩成参数扫表。
3. Canary 达标后，再按 Owner 独立授权进入 **18 Task × 50 Episode = 900**，冻结已验证配置并沿用只补缺失/无效 Episode 的 Resume。

统一 CPU 入口（这是交接命令，本次 GPT 未执行或派发）：

```bash
python tools/v3/run_eval_v2_batch_b2_cpu_gate.py \
  --root-worktree '<EXACT_CLEAN_ROOT_WORKTREE>' \
  --expected-root 323f0b2a3d4aa3b40d9d8f2eb0b94c9251299728 \
  --expected-child 774c2edb93ec5a6ba85ba1124757064d7cc779a5 \
  --evidence-dir '<NEW_EXTERNAL_EVIDENCE_DIR>'
```

执行接受条件：shell exit0 与 gate.json PASS 同时满足、零失败/错误/跳过、精确 Pair/import origin/source unchanged、owned process 清理可核验。若环境不满足，报告具体 BLOCKED；不把部署缺口转成新的架构路线。

本 Review 仅发布 docs，不合并候选生产代码/Gitlink，不启动 DS/GPU/Canary/900/训练，不更改其它并行项目 Gate。后续新增 blocker 应提供当前实际可达路径与对运行/结果的明确影响。

## 6. 可复核入口

- [作者交接（固定 Evidence ref）](https://github.com/wxwy/psm_wma/blob/e549a4f5e5d0b3f90a75cd37e047f006af90c94b/docs/collab/codex/reviews/2026-10-29_V3_EvalV2_PhaseB_Native_Batch_B2_author_handoff.md)
- [完整原始 Evidence](https://github.com/wxwy/psm_wma/tree/e549a4f5e5d0b3f90a75cd37e047f006af90c94b/docs/collab/codex/evidence/2026-10-29_eval_v2_phase_b_native_batch_b2_author_cpu)
- [Formal Root](https://github.com/wxwy/psm_wma/commit/323f0b2a3d4aa3b40d9d8f2eb0b94c9251299728)
- [Formal Child](https://github.com/wxwy/cosmos-framework/commit/774c2edb93ec5a6ba85ba1124757064d7cc779a5)
- [Native generation source](https://github.com/wxwy/cosmos-framework/blob/774c2edb93ec5a6ba85ba1124757064d7cc779a5/cosmos_framework/scripts/action_policy_server_robocasa.py#L1231)
- [Batch Actor source](https://github.com/wxwy/cosmos-framework/blob/774c2edb93ec5a6ba85ba1124757064d7cc779a5/cosmos_framework/inference/robocasa_batch_transactions.py#L190)
- [Atomic commit source](https://github.com/wxwy/cosmos-framework/blob/774c2edb93ec5a6ba85ba1124757064d7cc779a5/cosmos_framework/inference/robocasa_local_memory_policy.py#L215)
- [Runtime/OS tests](https://github.com/wxwy/psm_wma/blob/323f0b2a3d4aa3b40d9d8f2eb0b94c9251299728/tools/v3/eval_v2_batch_tests/runtime_test.py#L149)
