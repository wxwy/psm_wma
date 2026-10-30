# PSM-WMA V3 EvalV2 Phase B — No-TTT + Local-TTT 双模式窄增量 Code Gate

- 日期：2026-10-30（CST）。审核者：ChatGPT 独立 Code/Evidence 审核。
- **Formal Root implementation：`d18b420c02cfc51a1b85e9f1d6ce5d26f7bd3163`**。
- **Formal Child/Gitlink：`2f7334c4ada6ace1d21185985aae90539052bf18`**，根仓正式 Git Tree 已核验。
- 上一审核的 F5-P1 implementation Pair：Root `7c74dc26ac4837f193727ecf847b9b64554c18b2` / Child `53c3c95202e14d3b72d236eee6899a80acf82989`；其 F5-P1 有界持久化 `APPROVE_CODE` 维持，不重新审核。根仓新源码的直接 parent `608f55dccff6077e276e78644af6a578b4087781` 包含已发布 Evidence/bookkeeping；新增实施提交为 `d18b420c`，Child 新源码是 `2f7334c4`。
- 冻结 Owner 目标：**同一 EvalV2 同时支持 No-TTT 和 Local-TTT**，共享仿真任务、Slot、Session、Batch、恢复、可追溯身份和结果链；No-TTT 不伪造 Local state/prefix，Local-TTT 不降低既有 strict required 合同。
- 作者交接/证据：`docs/collab/codex/evidence/2026-10-30_eval_v2_dual_mode_author_cpu/`（已由作者发布于 `4cdf611b1a4e8455ca752fde6fa8e461c0ee5b49`，bookkeeping 非 formal target）。
- **正式 verdict：`APPROVE_CODE`，仅此双模式增量与作者 CPU Evidence。** 未发现增量生产 blocker；真实 GPU、真 checkpoint/DCP、真 RoboCasa 仿真/视频均未由本 Gate 执行。

## 1. 精确变更边界

直接读取 GitHub exact SHA/commit/compare，Root 最新实施提交改变 Gitlink、4个 Root production 文件（`eval_robocasa_18task_queue.py`、`robocasa_eval_v2/{config.py,identity.py,runtime.py}`）和受影响 tests/fixtures；Child 最新提交改变13个文件，包括 `contract.py`、`evidence.py`、`store.py`、`robocasa_session_transactions.py`、`robocasa_batch_transactions.py`、`robocasa_transaction_client.py`、`robocasa_transaction_mode.py`、`action_policy_server_robocasa.py`、Simulator thin wrappers 和新测试。此前 Root F5 后续 documentation 不作本轮生产 diff。

实际关键事实：

1. **模式选择与科学身份**：Root `config.py` 保留 required 默认，No-TTT off 仅允许 phase_b；`identity.py` 将 mode 传入 `build_manifest`；Child `contract.py` 将 `protocol.local_memory` 改为 off/required 的冻结身份字段，Manifest 校验重建并严格比较；`runtime.py` 对 manifest 与 requested mode 不同 fail-closed。Root server argv 原 required 被 Root Runtime 按已绑定 Manifest 修改，Server/Worker/Client ACK/INFO 均检查模式。没有自动静默降级。
2. **真实权重树身份**：Child `robocasa_transaction_mode.py` 在真实 ActionServer 模型加载后核对 `config.model.config.local_memory_enabled`、实际 `model.net` capability、DCP metadata Local tensor inventory（含应选 net/net_ema 的参数 shape）；`action_policy_server_robocasa.py` 只对 LocalTTT required 强制 K4/local32，No-TTT 则保持 raw15/state15/H16 的通用 Phase B 合同。
3. **复用同一事务执行者而不伪造 Local**：`robocasa_session_transactions.py` 引入 mode-specific request frontier（required 的 consumer_step，off 的 `inference.request_index`）及由事务 Owner 持有的 `_responses`。在原单 actor lock 下预分配完整响应副本，required 仍真实调用 `adapter.commit/commit_many/reset`，off 不创建 fast/visual snapshot、不调用 Local lifecycle；`robocasa_batch_transactions.py` 仍按原 bounded queue、deadline、fence、单次 native B1/B2 generation、atomic publication 和 ACK/End。相关失败语义继续 fail-closed。
4. **Native Action Batch**：Server `_transaction_prefixes()` 在 off 模式不注入 `_local_memory_prefixes` 参数，required 时仍提供每个 Session 独立的真实 prefix；Model 的同一 `generate_samples_from_batch` 计算路径、raw15 输出/denormalize 保持。
5. **Simulator/Core**：`eval_v2_transactions.py` off 时不创建 `AssignedLocalMemoryClient`，只发送由可信 Session lease 绑定的 inference request_index；`eval_v2_adapter.py` off 时在成功 End ACK 后写入 common Session 关闭证据，未宣称发生 memory adaptation；`evidence.py` 的 commit/read 核验由 `Store` 使用 frozen Manifest mode，required 旧 Local status/动作证据保持，off 拒绝 Local status 或 Local completed action，检查事务 protocol/frontier/assignment、actions/cleanup；`Store` safe persistence、F5 writer 与 JSON 上限保持未变。

## 2. Evidence 独立复核

- GitHub 作者原始 `raw/final/junit.xml`：`tests=324`、`failures=0`、`errors=0`、`skipped=0`；按 `classname + name` 检查 **324/324 个不同用例**。对应 `raw/final/console.log`：`324 passed, 14 warnings in 212.66s`；`raw/final/shell-exit.txt` 为0；`raw/final/execution.json` 记录前后同一准确 Root/Child、clean `root_status/child_status`、`source_unchanged=true`。14 warnings 非测试失败。
- `summary.json` 记录新增 Child35+Root12=47，用到的旧回归277，总计324；16个测试模块，不能把中间迭代通过数或原435累计。
- 作者 `raw/static-final/static.json` 与 `check_0/1/2.log` 显示 Ruff check、format changed files与 Queue 已改函数范围、compile21、Root/Child diff-check 全部 shell0，Source Guard smoke exact Pair PASS；`source_gitblob_bindings.json` 记录44个受监控 Git Blob/SHA256。GPT 已独立读取关键 production diff，不将作者测试数当作代替真实代码审核。
- 原始 CPU OS 运行在 synthetic Model/Sim/CPU boundary 下：No-TTT `G1×N2×M2×B2` 生成4 Core、8 replans、batch histogram `B1×4+B2×2`，1个Server和2个Sim均被 tracked/closed；Local-TTT 原 G1×N2E2: `B1×2+B2×3`、G2×N3E1: `B1×4+B2×1`、G1×N3E1: `B1×6`（动态窗口不强求B2）；Source/Lease/End/Resume/owned cleanup 回归通过。F3 fault 证据2个Slot分别 GENERATING/QUEUED，3个 owned groups cleanup，0 Core。
- 新模式 tests 在公开模型/API层验证 mode/DCP mismatch 拒绝、NoTTT 不传 Local prefix 或执行 Local lifecycle、LocalTTT 独立 fast update、B1/B2生成次数、replay、ACK丢包、timeout/End、COW分配失败/required commit validate 失败的无半提交、NoTTT Core commit/read 故障拒绝、CLI Fresh→Resume模式漂移拒绝。
- 作者 README 明确 GPU、真 DCP 模型大权重、真实 RoboCasa assets/physics、MP4 的执行尚未发生。**本结论仅 CPU 合成范围，不得用 `324 passed` 宣称双模式真实 GPU PASS。**

## 3. Findings / Verdict

- **Previous: F5-P1 HIGH CLOSED**（先前已批准有界持久化；此次未回退）。
- **NoTTT PhaseB unsupported: CLOSED_AT_CODE_LEVEL**。生产代码通过 mode-specific Request/Runtime Adapter/Client/Native Model 接线支持 NoTTT，同时保留 LocalTTT required 路径。
- **本增量未发现新的 HIGH/MEDIUM 阻断级 production violation**。不因旧 formal pair 而重复跑435测试，也不要求拆分两套评测框架。
- **未关闭的真实运行 Evidence**：当前仅证明合成 CPU 系统行为；真实 checkpoint 的 config/weight-tree/DCP 对齐、GPU显存/时延、真实B2 hit、两任务各2 Episode/MP4、Session fast-state与进程关闭仍待 DS 分别执行和上交。若出现真实失败应建立独立可复现 Evidence，不将其预设为已通过或本次代码缺陷。

## 4. Gate 权限边界

**`APPROVE_CODE`** ——仅允许精确候选 Formal Root `d18b420c...` / Child+Gitlink `2f7334c4...` 作为双模式真实 Canary 的可验证代码对象。请 DS 在各自干净 exact Pair、新输出目录、已确认完整且同源的 checkpoint/config 上运行，**分别**记录 NoTTT 和 LocalTTT 的原有1GPU/2Sim/B=2核心验收：实际 batch histogram、4 Episode、MP4、显存、时延、Session/fast-state以及 owned-only cleanup。NoTTT 不应出现 Local Fast State；LocalTTT必须有真实 Local prefix与状态隔离。

本 Code verdict **不自动**授权新增GPU次数或从4 Episode扩大到8 Episode；新增 LocalTTT GPU run 需要 Owner 明确确认。**不授权**自动合并 V3/Child、修改训练/活跃NoTTT Job、调整GPU共享政策或正式900 Episode。新的真实运行结果单独做 Evidence Gate。
