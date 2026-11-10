# V3 代码集成前验收 — K16 RoboCasa 四任务独立 Evidence

**2026-11-10。Verdict：`INTEGRATION_INFRASTRUCTURE_PASS / MODEL_SUCCESS_0_OF_4 / V3_MERGE_NOT_AUTHORIZED`。**

## 固定身份与范围

- 最新远端 `origin/V3=e58cef1f53d2382d39c871ce5a50e4acdd5ce268`，其 Gitlink `00f30235da6ffb085a9304ef6501ede509203092`。
- 已独立审核且完全不变的候选实现：Root `1b184204e301a51a7a20ed4dde1a11689589cf2d` / Child+Gitlink `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`。Git证明V3 Root是候选祖先，当前V3 Child也是候选Child祖先；**不需要合并分叉历史，但尚未进行V3合并**。
- Owner决策：停止底层 allocator/Attention 深挖，非阻断地保留长尾和首次慢段；回归V3构建及 RoboCasa 真正任务成功率。**本次属于新集成证据，不是新的 formal code SHA 或对旧代码重复审核。**
- 由 server 外置目录进行验收；未修改当前生产 Memory Prefix 注入方式、模型训练或业务数据。不执行K1/NoTTT重新跑分。

## 集成 CPU 与任务级证据

- 在完整候选 Root/Child clean formal pair 上，**9个与 history-K / SharedVAE / Sim相关的测试模块，115/115 CPU PASS，0失败、0错误、0跳过**；JUnit原始文件与退出码0均已核对。此前限域的Prefix CPU314和BF16 K16严格30-step数值Gate已经APPROVE，不重新跑重复的同SHA技术Gate。
- **GPU6 Policy / GPU4 Sim / Local K=16 / iter15000 / seed4603 / original shared VAE**：已在生产链路实际运行4个RoboCasa任务，每任务1 Episode，结果均为有效任务失败，无代码异常，完整清理。

| 真实评测任务 | 有效步数 | Replan | 任务结果 |
|---|---:|---:|---|
| CloseFridge | 900 | 57 | 失败，未达成任务 |
| NavigateKitchen | 450 | 29 | 失败，未达成任务 |
| PickPlaceSinkToCounter | 900 | 57 | 失败，未达成任务 |
| TurnOnSinkFaucet | 600 | 38 | 失败，未达成任务 |

**汇总：4/4有效完成工程评测，任务成功数0/4，SR=0%（仅此seed/checkpoint/4任务）**。这是算法质量证据不足，而不是推理/调度代码故障；不能把0/4解释成全部18 underlying task的总体SR，也不能以4/4工程PASS宣称模型成功。

CloseFridge具备最强数值比对：GPT独立重新读取57个真实replan的JSON动作与source RGB SHA，分别对照之前已保存的原始Local KVoff以及上一数值修复实现，均**57/57 Action完全相同、57/57 RGB SHA完全相同**。该任务原始Local也未成功，因此这次失败不能归因为Prefix优化改变了任务行为。其余3任务没有本Gate的同Checkpoint KVoff或NoTTT配对，**不能证明其任务成功率没有回归**。

## 生成性能：工程运行指标，不和固定输入计时混算

以下均为真实Episode下的 `native_generation_ms`（含当前帧 VAE，不含FastWeight HTTP及Sim）；按照冻结标准排除前两个Replan，取index2..End：

| Task | 稳定生成P50 | 稳定生成P95 | 说明 |
|---|---:|---:|---|
| CloseFridge | 744.071ms | 1007.559ms | 55稳定replan，900步；后段慢档仍存在 |
| NavigateKitchen | 984.295ms | 995.772ms | 27稳定replan |
| PickPlaceSinkToCounter | 983.942ms | 1000.908ms | 55稳定replan |
| TurnOnSinkFaucet | 988.485ms | 998.717ms | 36稳定replan |

**性能首次慢段/偶发尾延迟风险仍OPEN**，先前可能出现CUDA allocator 2MiB分配阻塞的证据不需要继续深挖，但真实任务生成仍可呈现两档时延；此时不把它当作默认阻断代码集成的理由，同时保持真实任务的延迟/超时监控。该有限样本P99不能视为生产SLA证明。

## 与V3目标集成的必要区分

- 最新候选Root领先V3 **72 commits**；总diff **1084路径**，约**1066 docs/evidence**，而非全部生产代码；若直接把所有Draft当作单个大包推进，会把大量原始测试快照/旧失败证据一并带入V3。需要采用**明确选定的完整依赖堆栈**（history K → sharedVAE → Prefix KV → Pack → 数值修复 → B1组装 → Projection）进行代码集成，并保留独立审核账本，而不是盲目flatten全部Draft。
- 工程集成Gate对本Pair本次4个任务可评估为**PASS**。任务成功率Gate为**NOT_PROVEN/0_OF_4**，若V3的发布决策要求SR证明，则**当前不能宣布交付成功**；需要后续更成熟checkpoint、足够任务与控制对照分析。
- 用户并未授权扩大到新训练、重跑K1/NoTTT、合并未验收完整堆栈或重新设计Memory。**本次不执行V3 merge**；建议先由Codex提交只包含正式依赖产线代码/必要测试的集成候选，并让GPT对新formal pair做一次集中Gate；成功率实验另行设计，不对现有4条失败做掩盖。

## 核查来源与私有数据

服务器授权目录：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/v3_integration_gate_20261110/`。含 `cpu_integration.xml`、`cpu_integration.log`、`independent_four_task_gate.json`、`runs/k16_seed4603/`、`runs/remaining3_k16_seed4603/` 与独立结果 `independent_readback_20261110.json`。最后的独立重读证据 **SHA256 `e23dbf7711776442d3b1f939d218d3055fe030ac4cb0821ce2000f93384fcdc9`**。

全量私有原始Episode、Action、视频和模型权重保留在服务器，没有外传GitHub；GPU4–7结束时均空闲，生产候选工作树保持干净。