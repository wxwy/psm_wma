# Issue28 — History K 随 Action Horizon 自适应：增量代码审核

- 审核日期：2026-11-09（CST）
- **Formal Root target**：`050e45d87fe5faf3a830bcaf4629fd7d16ba47a7`
- **Formal Child/Gitlink**：`59746af006748488a678aa9a55dfc3e200668219`
- 前序已批准 #27 Pair：Root `9b1756f9099955d6637743f8ad2fa0ee54987b7a` / Child `60b252d05157b2753d2caebae32b11c878504bbe`
- PR：Root [#30](https://github.com/wxwy/psm_wma/pull/30)、Child [#9](https://github.com/wxwy/cosmos-framework/pull/9)，均独立 Draft，stacked on #27；`71971a6c...` 为后续 evidence/docs HEAD，**不替代** formal implementation Pair。
- **正式 verdict：`REQUEST_CHANGES`**；一个确认的 **MEDIUM / production-contract blocker**。原因是 Owner 于2026-11-09审阅后明确更新通用配置要求，不是否定已证明的 H16稀疏路径。

## 实际已检查范围

独立读取两个 formal SHAs 相对 #27 的生产代码 Diff；重点代码：Root `config.py`、`runtime.py`、`shared_vae.py`；Child `robocasa_vae_protocol.py`、`robocasa_feature_evidence.py`、`sim_shared_vae_client.py`、`robocasa_vae_worker.py`、`local_memory_online.py`、`robocasa_local_memory_policy.py`、`contract.py`、`action_policy_server_robocasa.py`；对应历史K/Sim/Root单元测试。已读作者交接与 `author03/gate.json`、`sparse.log`、`worker_and_sim.log`、`dense_old.json`、`dense_new.json`、`dense_parity.json`、`provenance.json`。

在当前实际 H16 下，代码确实在历史 RGB Compose/Worker Encode1 前选择采样帧；所有真实完成动作的 source/receipt 按原H16因果顺序保留；仅 selected steps 进入已有 Local T1 scan。K16沿旧 dense wire 实现，作者提供 separate-process CPU K16 Old/New byte hashes 一致。Author CPU `631 top-level +207 subtests =838 JUnit`、0 failures/errors/skips，21 Python Ruff/format/syntaxPASS；以上是**作者证据**，Reviewer 未独立执行 CPU/GPU。它们证明**原已冻结 H16×5 K规格**的实现，但不能证明下述最新规格。

## 当前唯一已确认 blocker

### MEDIUM — History-K 合法值/默认值/采样计算依赖静态16，违反 Owner 新的 H 推导合同

**明确位置及已确认行为：**

1. Root `scripts/robocasa_eval_v2/config.py:20,330-331`：`DEFAULTS['local_ttt_history_k']=16`，以及是否在执行身份中保存K直接比较 `!=16`；Root `scripts/robocasa_eval_v2/shared_vae.py:92-96` 无 H 参数地验证 K，并通过 `!=16` 识别稀疏。
2. Child `cosmos_framework/inference/robocasa_vae_protocol.py:31-55`：`validate_history_k` 使用固定集合 `(1,2,4,8,16)`，`selected_history_step` 使用 `stride=16//K`、`chunk_start % 16` 与16帧范围，不从 authoritative action horizon 派生。
3. Child `cosmos_framework/evaluation/robocasa_v2/contract.py:228-237`：Manifest 校验仅允许显式 `K∈(1,2,4,8)`，不按 `H % K ==0` 判定。Child `local_memory_online.py:201-207` 将稀疏窗口与步距写死16；`scripts/action_policy_server_robocasa.py:541`、Sim及Worker入口也将默认K写死16。
4. 对应当前测试 `robocasa_history_k_test.py:67-71` 将K3无条件视为无效；这对当前H16合理，但不满足 H12时K3合法的新合同，缺H参数/通用非约数负例。

**违反的 Owner 最新设计合同：** `H=action_horizon=真实 Action Chunk 长度`（不是 episode horizon），**K省略时K=H**；显式K必须正整数且 `H%K==0`；`stride=H//K`，`source_step=T+j` 仅当 `j%stride==0` 才参与历史 VAE/FW，j0必选。当前 EvalV2 的正式 Model/Protocol仍限定H16，所以新规则在H16下得出的五个K恰与旧列表相同；问题在于**实现错误地把特例当成通用算法**。不要求本次把 Action Chunk本身从H16改成任意H或改训练/架构。

**最小可验收整改：**
- 使用已有 authoritative action_chunk_size / resolved policy Action Horizon 定义H，不把 Task Episode的 `horizons` 字段误用；默认K用未指定/None解析为H，当前H16时K16保持旧 wire、features、FastState/Prefix与 Manifest 行为。
- 抽取/调整统一 `validate_history_k(K,H)`、`selected_history_step(source,chunk_start,K,H)` 合同，严格正整数、不允许 bool/float/zero/negative/non-divisor；对外Root/Child/Sim/Worker/Policy最终依同一冻结K/H行事，不接受错配。将**与 history K 合法性/选择直接有关**的硬编码16替换成H；与正式H16 Action模型独立绑定的固定16不必扩成新模型能力。
- 增量CPU证明：H16默认/旧dense bit-exact +合法K1,2,4,8,16；H12合法K1,2,3,4,6,12（至少纯 helper/contract）、H24 的采样边界；典型负例K0/负数/bool/float/non-divisor；K=H任何合法H均完整16/H帧，K1仅选j0，选中数=K/额外VAE=K-1；strict Manifest/Resume identity、旧NoTTT/多Sim/transaction不回归。**无需为此在真实 RoboCasa 开启H12模型或重跑旧965/900EP。**
- Codex 在现有独立 RootPR#30 / ChildPR#9 上修，不新增第二套 EvalV2或稀疏引擎。修改产出**新正式 Root+Child Pair**，再进行 fresh incremental review。

## Gate边界/下一步

- **`REQUEST_CHANGES`**：本次不发 `APPROVE_CODE`，上述 production/config contract blocker未关闭。既有 H16稀疏正向代码/作者CPU证据保留，不要求推倒重来，也不要求重做 #27。
- 本 verdict 仅针对本形式 Pair 的设计/代码/CPU Gate；**不授权**合并V3、真实GPU/Sim、SR、900EP、训练或修改正在运行的任务。
- 独立审查与作者结果边界严格区分：读了实际源码与归档测试产物，但未独立重跑所有作者CPU或真实 Wan/DCP/Robot执行。
