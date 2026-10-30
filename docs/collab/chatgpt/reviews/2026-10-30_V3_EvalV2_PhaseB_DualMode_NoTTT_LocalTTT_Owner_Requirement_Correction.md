# PSM-WMA V3 EvalV2 — Owner 最终需求澄清：No-TTT / Local-TTT 双模式共用仿真优化

- 日期：2026-10-30（CST）。
- **Owner 最新确认**：“仿真优化必须在nottt和localttt都能work”。
- 此文件为**需求/审核方向纠错**，不代表已经修改生产代码或关闭新能力 Gate。
- 参考的当前被审核正式实现 Pair：Root `7c74dc26ac4837f193727ecf847b9b64554c18b2` / Child+Gitlink `53c3c95202e14d3b72d236eee6899a80acf82989`。该 formal pair 无生产修改，不重复做同一 SHA 的代码审核。
- **本文优先于同日两份相互矛盾的实施路线建议**：
  1. `2026-10-30_V3_EvalV2_PhaseB_Canary_7c74dc26_53c3c952_TTT_Checkpoint_Compatibility_Evidence_Gate.md` 中“只换TTT checkpoint、无需支持NoTTT”的建议；
  2. `2026-10-30_V3_EvalV2_PhaseB_NoTTT_Target_Owner_Correction_Erratum.md` 中将目标表达为“仅接替NoTTT”而未包含LocalTTT的部分。
  两者原有的精确源码观察和真实Canary阻断证据仍保留，**单模式限定建议均撤回**。

## 1. 冻结的总体功能目标

**一套 EvalV2 RoboCasa 仿真/评测系统同时支持 No-TTT checkpoint 和 Local-TTT checkpoint**，以模式显式区分，不复制两套独立的仿真调度框架。

| 功能层 | No-TTT | Local-TTT |
| --- | --- | --- |
| RoboCasa环境、task/episode调度、动态slot、seed/scene、仿真器重用 | 共用 | 共用 |
| 多GPU/多Sim、单GPU多Sim、native batch、batch histogram | 支持 | 支持 |
| slot/episode ownership、session lease/generation、retry/ACK/replay/timeout、End/cleanup、resume | 支持 | 支持 |
| checkpoint/config/runtime/Manifest身份与safe persistence | 严格验证 | 严格验证 |
| 模型推理输入/输出、SR、Core、视频与诊断 | 模式正确且证据齐全 | 模式正确且证据齐全 |
| Local fast weight / visual evidence / online adaptation / memory prefix / fast-state commit | **明确不存在/不执行** | **required，严格执行** |

- **与科研实验一致**：不能用TTT模型替代NoTTT来宣布NoTTT链路通过，也不能只用NoTTT宣布LocalTTT通过。不同模式、模型和配置拥有独立的不可变科学身份与结果目录；不可在同一个Run中混合覆盖。
- NoTTT路径必须避免构造伪fast-state、伪memory snapshot或假的Local-TTT成功指标。需要的Response cache/去重/ACK属于**事务层拥有的通用状态**。
- LocalTTT路径保持真实fast-weight更新、evidence chronology、prefix生成/模型推理与原有fail-closed机制，不得为了支持NoTTT降低它的安全性。

## 2. 当前代码差距（来自精确正式 SHA，先前已阅读；不重复代码技术 verdict）

- Root `scripts/eval_robocasa_18task_queue.py:257-284` 强制 `--local-memory-mode required`；EvalV2 runtime复用其服务器argv。
- Child `action_policy_server_robocasa.py:623-663,894-930` 强制required + `raw15/state15/H16/K4/local32`；`robocasa_local_memory_policy.py:74-78` 要求真实Local runtime。
- Child `robocasa_session_transactions.py:150-167,308-398` 把Session事务与 Local adapter fast/response snapshot 绑定；`robocasa_batch_transactions.py:190-279` 无条件 `prepare`、`commit_many`、`status`，并在Local snapshot里存Response；`action_policy_server_robocasa.py:1231-1258` 无条件注入Local prefix；Sim `eval_v2_transactions.py:23-69` 强制实例化Local evidence客户端。
- Child `robocasa_v2/contract.py:89` 固定 `local_memory="required"`，当前Manifest无法准确标识NoTTT Run。
- 结论：原来的真实NoTTT Canary报`required Local-TTT checkpoint has no net.local_memory_runtime`，是**双模式需求尚未实现的能力阻断**；当前TTT用例与冻结的强制要求一致，但**还没有真实GPU通过证据**。

## 3. 授权范围/最小整改指导（需Codex产生候选；GPT再审）

1. **明确选择运行模式**：经config/CLI显式指定NoTTT `off` 或LocalTTT `required`，校验与checkpoint的已验证能力、训练配置相容；冲突fail-closed，不得遇错自动降级。模式进入正式Manifest/Run identity与server / sim handshake。保持明确区分两种科学结果。
2. **公共能力一套**：保留RoundScheduler、SimSlot、Session lease/slot generation、请求身份校验、replay/ACK/End、original deadline、bounded queue/native batch以及媒体/ledger路径；最小分离Transaction通用Response缓存/成功提交与LocalTTT Fast/Visual snapshot这两类不同权威。NoTTT执行真实一次native generation，不调用TTT scan、不注入Local memory prefix。
3. **既有LocalTTT行为不退化**：原`required`模式K4/local32与evidence chronology、prepare/commit/abort/reset、atomicity等严格合同维持。若实现必须改变原冻结字段/协议，新增明确版本与回归；不偷偷复写现有身份语义。
4. **先小范围CPU验证双模式**：真实公共API（非只测helper）的NoTTT/LocalTTT启动接线、B1/B2形状/单模型调用、两Sim隔离、NoTTT无fast state、LocalTTT有真实fast更新、request replay变化拒绝、timeout/cancel/cleanup、manifest mode隔离及旧模式regression。避免重扫无关全仓435项；以代码实际改动决定定向集合。
5. **真实验收必须覆盖两模式**：GPU Canary分别在稳定同源checkpoint+config上运行，至少验证单GPU双Sim/native B=2实测命中以及结果/MP4/cleanup；NoTTT与LocalTTT各自提交独立结果，不能以一次冒充两次。**本文件不自动授权把原4Episode GPU实验扩大成8Episode，也不授权正式900**；需在新Code Gate通过后由Owner明确GPU执行范围。

## 4. 状态说明

- F5-P1 bounded persistence: **CLOSED / 旧Code Gate APPROVE_CODE 保留**。
- NoTTT 当前真实 GPU Canary: **BLOCKED_DUAL_MODE_NOT_IMPLEMENTED**；原report包含5,085字节小run_inputs、Server LocalTTT-required失败，属DS现场报告，GPU raw文件未在GPT直接取得。
- LocalTTT真实 GPU Canary: **NOT_YET_VERIFIED**；不能宣称PASS。
- 双模式功能 Gate: **OPEN / REQUEST_CHANGES**（新范围，需新formal production Pair）。
- 不改变当前NoTTT训练、训练数据、checkpoint、旧审核SHA或共享GPU资源策略；不自动merge/跑900。

**最终原则：通用仿真/事务/Batch共用，在线LocalTTT适配是可选且严格的附加行为；两种模型都必须真实可运行。**
