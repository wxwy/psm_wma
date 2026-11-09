# Issue27 — Shared VAE 通用拓扑增量审核（2×16 验收证据缺口）

- 日期：2026-11-09
- Review target：**Root formal implementation** `15dbc97bf13437905ec38247382834067e5341ae`；**Child/Gitlink** `60b252d05157b2753d2caebae32b11c878504bbe`。
- 基线：Root V3 `e58cef1f53d2382d39c871ce5a50e4acdd5ce268`；Child branch `b0dbd115d03e801ec4d0788c30ee0b0e9655d4db`（与旧 V3 Gitlink `00f30235` 完整 tree 相同）。
- PR：Root [#29](https://github.com/wxwy/psm_wma/pull/29)、Child [#8](https://github.com/wxwy/cosmos-framework/pull/8)；均保持 Draft。
- **Formal verdict literal：`REQUEST_CHANGES`（当前为 Evidence-only；非已确认生产代码缺陷）。**

## 已独立确认的实际修改

读取精确 formal pair 的 GitHub 生产增量与直接测试、Codex 原始 handoff/summary/gate：
- Root 只修改 `scripts/robocasa_eval_v2/config.py`、`shared_vae.py`，引入 general shared history 配置，保留 `single_latency_arm` 作为可选的单实例 A/B/C 测量身份，按物理 render GPU 复用一个 Worker，按 `(render_gpu, policy_gpu)` 分别注册 Policy Owner；
- Child 只修改六个既有生产模块：`contract.py`、`robocasa_batch_transactions.py`、`robocasa_boundary_capture.py`、`robocasa_vae_daemon.py`、`robocasa_vae_worker.py`、`action_policy_server_robocasa.py`。Bvae仍为1/wait0；Policy 原生批量上限可配置1..8；准备完成后走已有 READY Native batch，逐成员捕获原生 Policy current-frame B1 编码，Worker 的 Policy epoch/session 容量按拓扑派生。
- 旧 NoTTT/server_vae 路径和单实例 A/B/C 配置在增量中未见被改成独立新架构；原始 full16/15+1 FW 语义未被本 Issue 修改。
- Gitlink 在 Root formal pair 下实际指向 Child `60b252d0...`。
- 作者证据 `summary.json` / `author-01/gate.json` 表示965顶层+207 subtests、0失败/错误/跳过；19 Python Ruff/格式/语法通过。这是**作者证据**，本轮 reviewer 没有独立运行其 CPU 测试，也没有真实 H100/Sim 验收；不能因为 test count 直接批准。

## 当前仍存在的唯一明确 Blocker

### MEDIUM — 必选代表性 `2 Policy Server × 16 Sim/Server`（合计32 Sim）缺乏真正 Worker/Session 生命周期 CPU 验证

**位置：**
- Root `tools/v3/eval_v2_batch_tests/shared_vae_routing_test.py:189–201`：实际 Subprocess+FD+UnixIPC+OwnerHTTP 的参数集只有 `(2,8,False)` / `(2,8,True)`，测试代码用 `total_sim_slots = servers*sims`；这只验证了 **2 Server × 8 Sim/Server = 16 总 Sim**。
- Root `tools/v3/eval_v2_batch_tests/shared_vae_topology_test.py:42–62`：非 streaming 的通用解析只列 `(2,8,8)` 等；
- Root `tools/v3/eval_v2_batch_tests/shared_vae_server_wire_test.py:16–53` 虽有 `(2,32,8)`，但 `_spawn` 被替身在启动前中止，只证明 Server argv/Strict Options，**没有**验证32个真实注册 Session/Worker ACK/End/共享生命周期。

**根因：** 作者将 Issue27 中 `2×16` 明确缩写解释成 “2 Server / 16 total Sim”；原需求/Issue23 多 Sim 资源布局是**每个 Policy Server 对应16个 Sim、总32 Sim**。由于 round M≤8，原目标需要用既有 streaming M16 模式，当前完整 Owner-IPC 生命周期开关未覆盖它。

**违反验收：** Issue27 的“1×1 / 1×8 / 2×16 三组代表性真实生产入口 CPU/合约验收、任意合法 M/B/Server-Sim 配置”，及 Worker 每物理 GPU 一份、16 Session/Policy 的对照。不能用 `(2,8)` 或被 mock 掉进程的 `(2,32)` 自动代替。

**可验收的最小修复：** 只补测试/证据，不要求改生产代码：沿用现有 `rig_for` 真实 CPU Worker subprocess + 私有 FD + UnixIPC + Owner HTTP 测试路线，加 **2 Server × 每 Server 16 Sim = 32 Session** 的 streaming M16 样例（两个 render GPU 各一 Worker），验证全部32 注册/权限/分组/End、Worker确为2份、资源和清理；如设计允许跨 Policy Server 同 render GPU，再保留一个 same-render 共享场景作为窄补充。确保实际传入 streaming 的 frozen manifest/capacity，不能只传 `physical_slots(cfg,128)` 的配置模拟。提交固定 SHA 的原始 JUnit + 直接证据并与原有 1×1/1×8 回归对照；若暴露生产缺陷则升级 production blocker。**不需要重新做900EP、SR、旧2×16评测或重写调度。**

## Gate 决定与后续

- 本轮未发现可由已读实际增量确认的其他生产 blocker；**不能据此宣称新拓扑的 H100 实时吞吐已验收**。
- 当前仅阻塞 `#27` 的增量 Code Gate closure，保留已完成的1×1真实 H100加速和旧 server_vae 测试，Root#29/Child#8 暂不合并。
- **#28 FW稀疏更新独立跟进**：以 #27 完整验收后的精确新 Pair 为基线，在**同一套** EvalV2/Shared VAE 上增加唯一 `local_ttt_history_k∈{1,2,4,8,16}`（默认16）；每次完整 H16 Chunk 的前一轮 Replan 帧索引0必选，selected indices `i % (16/K) == 0`，跳过帧无额外VAE/无FW更新但保留真实动作完成因果。K1/2/4/8/16额外历史 Encode1数分别0/1/3/7/15，FW更新分别1/2/4/8/16。仅启动后续隔离实现，不得将未经审核的 #28 代码混入本正式 #27 Pair。
- 本 verdict 只针对 Issue27 精确 CPU/static Gate，不授权真实GPU/仿真、900EP、训练或 V3 合并。
