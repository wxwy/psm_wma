# Issue28 — K 随真实 Action Horizon 派生：增量 Code Gate 复审

- 审核日期：2026-11-09（CST）
- **Formal Root**：`53b5273c7907e2d7a8fb1831ac0e0ec8b9fa973a`
- **Formal Child/Gitlink**：`4cd5fc8c43d6793745dbc4cac51c59ee8a020dbe`（Root formal Gitlink 已通过 GitHub 原始 tree 读取核对）。
- 上轮 `REQUEST_CHANGES` Pair：Root `050e45d87fe5faf3a830bcaf4629fd7d16ba47a7` / Child `59746af006748488a678aa9a55dfc3e200668219`。
- 合格上游 #27 Pair：Root `9b1756f9099955d6637743f8ad2fa0ee54987b7a` / Child `60b252d05157b2753d2caebae32b11c878504bbe`。
- PR：Root [#30](https://github.com/wxwy/psm_wma/pull/30)、Child [#9](https://github.com/wxwy/cosmos-framework/pull/9)，目前 stacked Draft、未合 V3。
- **正式 verdict：`APPROVE_CODE`，仅 Issue28 的 CPU/静态/设计实现 Code Gate。**

## 1. 本轮增量事实及前次 blocker

独立读取精确 SHAs 相对上轮 formal Pair 的 Root/Child compare，检查实际生产代码、定向测试源码、作者原始 JUnit/Gate/运行日志/Source inventory/两份 dense probe。

**前次唯一 MEDIUM blocker — CLOSED。** 原因是此前把 `K=16` 及 `{1,2,4,8,16}` 固定为全局采样规则。这次改成：
- Child `inference/robocasa_vae_protocol.py:31–54` 实际 `validate_history_k(value, action_horizon)`：`H` 必须正整数，`K=None` 直接解析为 `H`；显式 `K` 必须精确 Python `int`、正数、且 `H%K==0`（不接受 bool/float/负数/0/非整除）；`selected_history_step(...,K,H)` 使用 `stride=H//K`、在真实 chunk 起点的相对索引 j 取模、j0必选，不重编号。
- Root `scripts/robocasa_eval_v2/config.py:21,273–277,336–340` 默认 `None`，从 frozen `ACTION_CHUNK_SIZE` 解析实际K，只有 `K != H` 才扩展新 Manifest execution identity；显式 `K=H` 与默认保持旧 dense identity。
- Child `evaluation/robocasa_v2/contract.py:14–15,228–242` 单独命名已有权威 `ACTION_CHUNK_SIZE=16`，取 `protocol.action_chunk_size` 验证 `K` 约数并保持既有 Native H16 实际模型约束，不误用 `horizons`（Task rollout episode length）。
- Child `local_memory_online.py:78,131–158,168–175,210–215` 从绑定的 `action_horizon` 验证/选择，有 Session 的 `K/H` 一致性围栏；非 H16 的通用 `OnlineLocalMemory` CPU helper 可测试，但不向 Native H16 模型冒充新能力。
- Policy Server `action_policy_server_robocasa.py:541,632–638,1088–1106,1118–1129` 在已解析模型 `action_chunk_size` 上创建 Feature Owner并保持现有 H16 强约束；Root `shared_vae.py:663–677,831–840` 用真实 Policy INFO `action_chunk_size` 比对 frozen Run/Worker READY；Sim/Worker/Local 持续按此 H 维护选帧/Session/Action 完成证据。
- 原 `K=H` dense wire/fingerprint/Manifest省略规则、当前帧缓存 j0、每已完成 Action 真实 source frontier、Native事务/ACK/End、VAE B1/wait0、Policy Batch1..8、通用 Server/Sim 拓扑均未被新设计替代。没有另建仿真/更新引擎。

**结论：此前“K 默认/合法值/步距写死16”的生产 contract finding 已按 Owner 新要求整改。** H12/H24 为工具层行为验证，不要求扩展真实 RoboCasa action-chunk runtime；正式 Native 仍 H16，符合本次冻结范围。

## 2. 证据核验与限制

- 定向新测试 `cosmos_framework/inference/robocasa_history_horizon_test.py`：检查H1–48的全部约数、None→H、采样相对时间/数量/j0、H12/H24、非法类型、非约数；还用原模型 `scan_local_memory` CPU 路径核验H12/H24的真实K次 T1 适配，Native Owner/Worker拒绝冒充真实H12。Root/Child其它定向测试包含 K/H Manifest/Resume、Policy INFO、Worker/Session/Sim绑定错误拒绝、现有H16全部K、NoTTT/事务/泛化拓扑回归。
- 作者原始 `docs/collab/codex/evidence/2026-11-09_issue28_horizon/author01/junit.xml` 实际 `testsuite tests=588 failures=0 errors=0 skipped=0`，566条顶层 testcase；`focused.log` 明示 **566 passed,22 subtests passed**，不是566+22个独立 Python 函数。Ruff/格式22文件PASS；`author01/gate.json` 标记 PASS、精确 Root/Child Pair、未改源码；独立对比 `source_before.json` 和 `source_after.json` 的1331个源码 SHA，**1331/1331 一致**。
- 两个隔离 Child进程（旧`59746af0`、新`4cd5fc8c`）使用相同 CPU probe/seed 输出 `author01/dense_old.json` 和 `dense_new.json`；独立逐项核对来源source0..15和16..31、Feature wire SHA、cached boundary SHA、FastState四份 SHA、Prefix SHA、合成Action SHA、`adapted_steps=16` 完全一致；这是 **CPU默认H16 dense parity**，不是实机Wan/DCP/扩散模型全Action保证。
- 作者`dev01` 早期曾出现558PASS+22subtests/8FAIL（旧模拟Registry INFO夹具遗漏H）；原始失败保留，定向改夹具后正式566+22PASS；这不被计入正式最终失败，也不意味着生产被绕过。

## 3. Gate判定

**`APPROVE_CODE` — Issue28 在精确 Root `53b5273c7907e2d7a8fb1831ac0e0ec8b9fa973a` / Child `4cd5fc8c43d6793745dbc4cac51c59ee8a020dbe` 的 CPU/静态增量 Code Gate 通过，前次 MEDIUM CLOSED，目前无确认的新增代码 blocker。**

本次审核以代码与原始作者测试证据为基础，审核者**没有单独复跑全部 pytest、没有调用 H100/真实 RoboCasa/Wan/DCP**。结论不涵盖真实 GPU 性能收益、实机或仿真SR、全900 EP或训练；**不自动授权 PR 合并至 V3**。后续必须保持先后依赖 #27→#28，正式 GPU 只需按 Owner 后续授权做最小新路径冒烟/性能对照，不重复历史900EP/SR。此 verdict 不应被泛化到改变 Native H16 的新生产代码。
