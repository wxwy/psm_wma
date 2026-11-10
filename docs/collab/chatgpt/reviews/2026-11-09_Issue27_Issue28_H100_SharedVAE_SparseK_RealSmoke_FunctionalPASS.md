# Issue27 + Issue28 — H100 真机仿真链路短闭环验收（功能 PASS，性能仍待无干扰验证）

日期：2026-11-09。审核对象为**固定源代码配对** Root `53b5273c7907e2d7a8fb1831ac0e0ec8b9fa973a` / Child-Gitlink `4cd5fc8c43d6793745dbc4cac51c59ee8a020dbe`。Root PR [#30](https://github.com/wxwy/psm_wma/pull/30) / Child PR [#9](https://github.com/wxwy/cosmos-framework/pull/9)，依赖此前通过 CPU Code Gate 的 Root #29 / Child #8。此次**没有修改生产代码、运行训练、合入 V3、运行 900 Episode 或执行 SR Gate**。

## 本轮 Owner 授权范围

Owner 2026-11-09 明确“那就执行吧”，并进一步指定“在 4–7 卡执行，忽略 `gpu_load_sim.py` 模拟负载”。因此不把 GPU4–7 的人工显存/利用率占用当作真实生产业务占用，但**没有停止、杀死或修改** `gpu_load_sim.py`；GPU0–3 的其他训练进程完全保留。由于模拟负载仍运行，所获速度只作非受控观测，**不得据此宣称稳定性能收益**。

代码在训练服务器独立、干净的 worktree 检出并复核 exact Root HEAD、Child HEAD 和 Gitlink；所有运行使用同一套 EvalV2 + Native Policy Batch + Sim-side Shared Wan VAE B1/wait0 + Online Local-TTT 源码。checkpoint：iter15000 Local-TTT，固定任务种子 4603，真实 RoboCasa EGL/MuJoCo，GPU4/5 为渲染/Sim/VAE、GPU6/7 为 Policy。运行数据只保存在服务器本地，本审核文档仅摘录无密钥的统计与哈希，不外传原始服务器日志或文件。

## 1. 单实例对照：同一 H16、同一任务 CloseFridge

`CloseFridge` 每组均为900/900 Sim steps、57 Replans、56个完整历史窗口，最终 Episode 有效、`error=None`、`cleanup_ok=True`，无 process_errors，不以任务是否成功作为本轮 Gate。

| 指标 | K=16（默认）| K=1 | K=4 |
|---|---:|---:|---:|
| Policy/Sim GPU | 6 / 4 | 7 / 5 | 6 / 4 |
| 每个完整历史窗口实际 FW 更新 | 16 | 1 | 4 |
| 每完整历史窗口额外 Worker VAE 特征 | 15 | 0 | 3 |
| 全 Episode 已消费历史 Worker 特征数 | 840 | 0 | 168 |
| 全 Episode 已消费 FW 更新数 | 896 | 56 | 224 |
| Episode execution walltime (s) | 128.536 | 120.135 | 135.595 |
| Replan latency P50 (ms，排除首轮) | 1176.997 | 1096.031 | 1470.662 |
| Replan latency P95 (ms，排除首轮) | 1251.414 | 1459.013 | 1494.832 |
| 57个 Replans/900个 actions/有效 Episode | PASS | PASS | PASS |
| 事务、Prefix、Worker End及进程清理 | PASS | PASS | PASS |

逐条解析原始 `predictions.jsonl`/ `actions.jsonl` / `result.json` 证实每组实际更新次数恒等于 K，所有有历史的 Replan 都注入 Prefix。K1 选中 `[T]`、`verified_worker_features=0`；K4 为 `[T,T+4,T+8,T+12]`、`verified_worker_features=3`；K16 遵循原 dense16 语义。三组**初始 RGB SHA256 完全相同、首次16步 Action SHA256 完全相同**，随后因不同 FW 更新而开始分化，符合预期。

**速度判读**：当前观测 K1 的 Episode比 K16 少约8.40s（约6.5%），但 K4 反而多约7.06s；GPU组合、并行运行时段和模拟负载均存在干扰。此结果证明历史编码/FW计算次数的真实减少，**不构成严格稳定加速结论**。

## 2. 多实例真实闭环：2 Policy Server × 每 Server 2 Sim

- 配置 `scheduling_protocol=streaming_task_affinity_v2`、Policy GPUs `[6,7]`、Render/Sim GPUs `[4,5]`、`sims_per_gpu=2`、`max_infer_batch_size=2`、`batch_wait_ms=0`、`local_ttt_history_k=4`，Worker VAE B1/wait0。
- 实际启动 **2 Policy Server + 2 物理 Sim GPU 共享 Wan Worker + 4 独立 Sim Slots**；真实 Model/Wan/EGL/仿真，非 CPU double。
- 任务级真实完整闭环：

| Task | Sim steps | Replans | FW/完整窗口 | Worker VAE/完整窗口 | execution walltime |
|---|---:|---:|---:|---:|---:|
| CloseFridge | 900 | 57 | 4 | 3 | 144.505s |
| NavigateKitchen | 450 | 29 | 4 | 3 | 72.736s |
| PickPlaceSinkToCounter | 900 | 57 | 4 | 3 | 159.808s |
| TurnOnSinkFaucet | 600 | 38 | 4 | 3 | 86.321s |
| **合计** | **2850** | **181** | — | — | 不相加（并发） |

最终 `summary.json` 为 `status=complete,expected=4,valid=4,invalid=0,interrupted=0,pending=0,results_qualified=true,clean_execution=true,process_errors=[]`。四个 Episode 的 `result.error=None`、`cleanup_ok=True`、Action记录数量与实际步数相等，所有有历史的 Replan 均按真实 Chunk 起点选择 K4且 `adapted_steps=4`、`verified_worker_features=3`、`prefix_present=true`；无错位、跨 Session串用或遗失前缀的证据。

在 Root运行目录内核对到2份`server_identity`、2份`shared_vae_worker_ready`、2份`shared_vae_worker_closed`；两份 Worker Closed receipt 均为`closed=true, acknowledged=true, quiescent=true, ipc_quiescent=true`。结束后 GPU4–7 回到模拟负载本底显存（约36977MiB/卡），无残留本轮 Policy/VAE/Sim进程。

**明确限制：** 本次实际 Policy Batch cap=2，但异步到达并且`batch_wait_ms=0`导致运行时观察到的实际 Native batches 均为 B1；未证明实际 GPU 上合并两个请求的 Native B2 generation。不能把“B2 可配置且2 Server/4 Sim实测运行”表述为“真实 B2组批已通过”。原 #27 CPU测试覆盖 Native B2..B8 Ready grouping；新多实例32 Sim（2×16）仅有通过的 CPU生命周期开关，本次**没有**进行32 Sim H100长测，亦无需重复旧900EP。

## 结论与后续边界

- **`REAL_GPU_FUNCTIONAL_SMOKE_PASS`**：已确认新 Shared VAE + Local-TTT 稀疏 K1/K4/K16 的真实 Action Path运行、真实已完成证据/更新次数、单实例完整 Episode和2 Server×2 Sim拓扑的多 Session Worker共享/清理。既有 `APPROVE_CODE` CPU Gate可保持，不新增必须修复的生产代码 blocker。
- **`PERFORMANCE_NOT_ESTABLISHED`**：观察到历史 VAE和 FW工作量随K降低，但当前`gpu_load_sim.py`负载下的 Episode/P50/P95不是受控公平性能对照；无资格声称K值越低端到端一定越快。
- **`REAL_GPU_POLICY_B2_GROUP_NOT_OBSERVED`**：多实例使用Policy Batch cap2配置，但实际B2组批未出现；若正式批准 Bpolicy>1 的性能用途，需要独立、最小的真实B2/Ready-group现场验收，不能冒充已做。
- **不自动合入 V3**：本次 Owner授权的是必要GPU短闭环和速度对照，不自动等于批准Root#29/Child#8/Root#30/Child#9四个stacked PR合并。官方V3仍维持其原状态，待Owner决定依赖顺序合并；不跑SR/900EP/训练。

仅在训练服务器本地保存原始 `run_K16`/`run_K1`/`run_K4`/`run_M2B2_K4` 结果及校验摘要 `h100_smoke_verification.json`；本GitHub审核仅传输不涉及敏感凭证的实验摘要，不包含原始私有运行文件。
