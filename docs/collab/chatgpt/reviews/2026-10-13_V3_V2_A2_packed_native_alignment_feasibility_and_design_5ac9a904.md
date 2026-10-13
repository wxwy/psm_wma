# PSM-WMA V3 — V2 A2 Packed Native 性能对齐的设计与证据边界（尚非实现审批）

**日期:** 2026-10-13
**Owner指令:** 「如果V2是正确的，那就对齐V2；你还需要ds给你更多输入？」
**V3现有实现:** Root Implementation `e730e3063ee3638f0bafd79473f52a76f851c935`, Child/Gitlink `5ac9a904c46da658e1b3e0816d3a7d95ce99c945`，docs-only V3 HEAD 不冒充implementation SHA。
**V2关键参考:** 原冻结 A2 工程验收 Root `2a9df880713da179aee141dd97c6b20a2b1d8c2e`, Child `22acb13c1fdb4f146e51e3c26f1759c73e6d0d7e`；V2后期 RoboCasa 构建分支Child `e3dc9ecce0a4a7223245dc4f5b5efde7b709fd92`。V2是否已经工程验证，依据下面实际归档证据，而非想当然推论。
**裁决:** `V2_A2_PACKED_NATIVE_REFERENCE_ACCEPTED_FOR_DESIGN`；`V3_ALIGNMENT_IMPLEMENTATION_NOT_YET_APPROVED`。现有仓库已有足够资料开始设计，不要DS再次提供V2代码。新的V3执行算法需独立实现+数值/显存/性能验收。

## 1. 已核对的V2证据

1. `artifacts/g0/sync_a2_gpu_control_2a9df880/native_validation.json` 有真实模型/数据、固定sigma=0.5 epsilon=0，`grouped_forwards=1` vs `scalar_forwards=8`，128消费者；Loss relative error `3.0077701726206423e-05`，梯度相对L2 `0.023932465357780673`，Local梯度 `0.02394999587378261`，在**当时冻结的5% L2工程判据内PASS**。它**不验证实际随机训练运行或不同CUDA kernel严格逐位一致**；另一个旧attempt `a2_acceptance_fb386c7a/control/native_validation.json`总体FAIL（online Memory Prefix/Native MemoryState冲突）不能被偷换为无瑕历史，后续最终control修复才PASS。
2. `artifacts/g0/sync_a2_final_verification_2a9df880_v3.json`历史10/10 PASS包括CPU 244 tests、真实模型/数据native parity、resume frontier+fast state、20-step预算；**此归档同时指出独立review尚不在纯verifier JSON中批准**，后续 `docs/build/PSM-WMA_Local_Memory_A2_delivery_runbook_2026-09-18.md`记载正式验收和交付审批。
3. `artifacts/g0/localmem_ttt_a2_training_full_record_iter3288_2026-09-22.md`历史 LIBERO 8×A10080G A2 mean step wall≈16.4s、iter3000评测358/400=89.5%，但原始训练日志留在服务器；`docs/build/PSM-WMA_RoboCasa_Local_TTT_rolling_status_2026-09-24.md` 8卡RoboCasa targetAtomic N100 at iter≈1983 step≈16s（用户/DS当时上报，不是iter800精确值）。
4. **内存跨构型警示：** A2早期 full-catalog 20-step GPU短测 `cuda_peak_allocated_GiB≈45.045`，但该control采用不同 GA/member几何（A2默认GA16, 2048 consumer/rank），**不等于**正式RoboCasa GA2/8卡的实际内存；不能用它直接判定新 V3 batch128是否可在每H100当前约20GiB空闲内运行。需要新实现隔离内存Smoke而不能用历史12GiB小Batch估算必然OK。

## 2. 当前V2/V3执行差异（已逐代码定位）

| 属性 | V2 A2 | V3 当前 |
|---|---|---|
| 每个GA Member | B8×T16消费者合并，一次 `model._run_active_local_memory_native_forward(inputs)` | `run_member`先batched scan，再按每index构造BatchB<=8，调用`native_loss`/backward最多16次 |
| 每个Optimizer Step（GA2） | 常规约2次native forward/backward | 满幅窗口最多32次native forward/backward |
| 完整Segment预取 | `active_local_memory_driver.py` 的`_start_prefetch`+ `_produce_group`可在线程中`producer.produce`包括transform，默认`PSM_ACTIVE_PREFETCH_DEPTH=4` | V3 `OrderedMemberPrefetch`仅GA1 raw `producer.prepare`; `materialize`主线程；nw0时全部同步 |
| Local时序 | batched scan、先计算各Consumer的prefix，合并进入模型；先成功Native backward后commit | V3 model-owned batched scan，逐index F/B，之后各row commit，optimizer成功后发布frontier |
| 数值验证 | A2对当时Scalar固定输入满足5% grad-L2阈值 | V3要针对当前实现冻结独立的packed-vs-index严格对比准则 |

**实现原则:** 恢复V2的**Member级合并Native Batch**，复用V3自身的 `BatchedLocalMemorySegmentAdapter.scan`, `GroupedLocalMemoryWindow`, `LocalMemoryTransaction`, `GroupedLocalMemoryStateCallback`, `GroupedLocalMemoryTrainer`，不直接复制V2完整driver。要确保`(slot,index)`映射、有效valid consumer、prefix与S0 absent、时序依赖、Terminal/partial末段、梯度及Loss归一化/辅助项、CFG sigma epsilon随机调度、FSDP optimizer selected314、cache/video ABI、Strict Resume/DCP不变。V2过去的Grouped native parity不是当前V3自动审批。

## 3. 冻结设计目标与Gate

### 先实现、后批准；当前训练不触碰

- Step A：GPT/code owner 在隔离新实现Target添加 `GA member-packed native` 路径（或冻结设计证明更合理的 V2同等实现）；**首先是CPU synthetic+real-dataset no-update等价**，冻结原V3 per-index路径做对照，逐Consumer检查样本/Local prefix/identity/索引/源，JSONL schema和Source/DCP不可意外改变。
- Step B：真实H100可用时Owner另行批准独立GPU smoke，固定同一输入、同一模型权重、固定random输入或可复现的noise/sigma/epsilon，比较loss分项、full selected314参数 grad FQN、fast state/Local后态、完整Optimizer一步，并冻结容差；不能用“5%是V2旧验收”自动放宽当前V3 Gate，不必要求跨独立进程CUDA bit-exact。训练peak/rank及8×H100资源与部署阈值必须实测。
- Step C：若数学/内存通过，单个隔离短窗口的同源config下比 `native_forward_calls 32→2`、Host/GPU time、CPU prepare、total step-wall p50/p95、loss/local/gradient/VRAM/Checkpoint，标注外部GPU负载；加整段 async materialize仅在Packing验收后作为独立优化，不一次性修改两个变量混淆归因。
- **目标:** 不是保证立即到16s；固定相同有效consumers2048/optimizer、精确数值和状态后尽量恢复A2吞吐，无OOM、无训练统计或恢复语义回退；在必要内存限制下可小于128pack逐步分组，但任何分组改变必须另做梯度权重/随机性审计。
- **严禁：** 在运行中的Formal30k固定Root/Child checkout直接git pull；擅自停止/恢复；DS修改生产代码；把当前`gpu_data_stall_ms`（尚未通过真实GPU计时验证）当实际GPU吞吐证据；用FSDP2或RL替代0-SR或数值等价挑战。

## 4. DS只需提供的一份现实只读证据（不阻塞设计开始）

`docs/collab/chatgpt/requests/2026-10-13_DS_PRO_V3_V2_A2_alignment_minimal_readonly_evidence.md`：
1. 当前Formal30k**实际进程的代码身份、flags、GA2/B8/T16/8rank、来源/ckpt、是否正在运行**；确认新V3 GitHub docs Head≠现场冻结Root。
2. rank0 JSONL中**一个连续稳态20迭代窗口**的`native_forward_calls`,`native_backward_calls`,`valid_consumers`,`local_scan_ms`,`data_prepare_ms`,`forward_ms`,`backward_ms`,`optimizer_ms`,`step_wall_s`,`peak_allocated_gib`,`peak_reserved_gib`,`cuda_sampled/ *_cuda_event_ms`若有；同时保留`missing/nonfinite`。不要重新跑V2、不要额外GPU。
3. 当前8卡free/max perrank allocated/reserved和外部任务是否共享，仅供预计Packed Batch显存安全评估，GPU计算竞争不是Owner单独阻塞标准；不停止其它任务。
4. 如果V2 RoboCasa当年进程峰值记录**已现成可读**，可附一条含file/rank/step证据；没有就写Unavailable，**不为此重新全盘搜日志**。

**当前 Verdict:** `DESIGN_REFERENCE_ACCEPTED; IMPLEMENTATION_AND_FORMAL_DEPLOYMENT_PENDING`。不生成新训练代码变更，也不对原Job发启动指令。本 review 为设计与取证要求，不等于GPU授权。
