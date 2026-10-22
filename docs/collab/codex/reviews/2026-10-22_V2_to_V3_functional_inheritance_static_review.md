# V2 → V3 功能继承静态盘点

日期：2026-10-22（Asia/Shanghai）。性质：Owner 要求的只读源码/功能盘点，不是新的实现提交、GPU 验收或对运行中 G1 的修改决定。未执行项目代码、测试、模型、仿真或真实 DCP 操作；本轮交付仅文档。

## 1. 比较基线与判断方式

| 项目 | 锁定 SHA |
| --- | --- |
| V2 Root | `b13024456e313b545871a0d5de07f5495848f4e3` |
| V2 Child/Gitlink | `e3dc9ecce0a4a7223245dc4f5b5efde7b709fd92` |
| 本轮开始及复核时 V3 HEAD | `e577e05c2005d19b3b97f725624c447c53d20f0b` |
| V3 当前生产 Implementation Root | `a4b22b929175e462b6a8db57ad2abee7e220dd37` |
| V3 Child/Gitlink | `c9f21040f462a114d597fc83773cb9b6a9e96214` |

GitHub refs 通过 fetch + ls-remote 重新核对。V2 以 Git archive 的只读源码快照查看，未切换或改动 V2/V3 Child 工作区。V3 最新三个后续提交仅文档，未改变被扫描的生产 Pair。以下 Child 路径均以 `cosmos_framework/` 或 `examples/` 开头，Root 路径另行标明。

判据是“实际配置 → 入口 → 调用链是否接通”，不以缺失文件数量或名称不同判断未继承；也不把 V2 所有实验工具当成必须阻塞 RoboCasa 主线的功能。新的官方框架可以采用不同接口、FSDP 所有权和数据结构。

## 2. 优先复核：V2 实际存在，V3 正式链尚未完整接入

### I-01 — 优化器更新前的全局梯度范数裁剪：确认缺口，优先级高

V2 成功 A2 的完整调用链：

1. Root `tools/g0/launch_local_memory_a2.sh:41,50` 选择 A2 和 active LIBERO TOML。
2. Child `configs/base/experiment/action/posttrain_config/action_policy_libero_edge_all.py:443–447` 明确保留 `optimization`、`job_monitor` 回调；RoboCasa A2 recipe `action_policy_robocasa_edge_all.py:209–220` 也选择这两组及 A2。
3. `configs/base/defaults/callbacks.py:147–150` 注册 **GradClip(clip_norm=1.0)**。
4. `trainer/__init__.py:636–652` 实际走 active backward，GA 完成后 `:678–692` 仍调用 `callbacks.on_before_optimizer_step`；它没有被 TTT backward 回调过滤逻辑排除。
5. `callbacks/grad_clip.py:325–391` 对其覆盖的 `model.net` 参数真实计算跨 mesh 的全局范数，并按 `min(1, clip_norm/global_norm)` 缩放梯度。

V3：`examples/psm_wma_robocasa_corrected_phase5.py:754–755` 关闭 validation 并设置 **`config.trainer.callbacks = {}`**；`utils/callback.py:46–87` 不会暗中补回默认回调；`trainer/local_memory_grouped.py:133–152` 仅额外插入 Local 状态保存回调。优化器边界 `local_memory_grouped.py:363–381` 只有 unscale、两处有限性检查、回调/模型 hook 和 optimizer；`model/generator/omni_mot_model.py:899–919` 的 hook 只处理 router/EMA，没有替代裁剪。

**影响：有限但很大的梯度不再受到 V2 的 norm=1.0 裁剪。有限性检查和范数裁剪是不同能力。** GradClip 文件本身在新框架仍存在，缺的是正式配置接线。

这会影响训练更新语义，应先由 GPT/Owner 明确继承合同和兼容边界。不能根据本次静态发现断言正在运行的 G1 当时的配置、更新幅度或结果无效；本轮未访问其实际运行目录。不得自行给 G1 热加裁剪、修改冻结配置或暂停训练。未来若恢复，应使用新版 FSDP/DTensor 的全局范数语义并单独验收，不能复制旧分布式梯度同步实现。

固定源码：[V2 注册裁剪](https://github.com/wxwy/cosmos-framework/blob/e3dc9ecce0a4a7223245dc4f5b5efde7b709fd92/cosmos_framework/configs/base/defaults/callbacks.py#L147)、[V2 active optimizer 调用](https://github.com/wxwy/cosmos-framework/blob/e3dc9ecce0a4a7223245dc4f5b5efde7b709fd92/cosmos_framework/trainer/__init__.py#L678)、[V3 清空回调](https://github.com/wxwy/cosmos-framework/blob/c9f21040f462a114d597fc83773cb9b6a9e96214/examples/psm_wma_robocasa_corrected_phase5.py#L754)、[V3 optimizer 边界](https://github.com/wxwy/cosmos-framework/blob/c9f21040f462a114d597fc83773cb9b6a9e96214/cosmos_framework/trainer/local_memory_grouped.py#L363)。

### I-02 — Action-only 推理和细分 inference profiling：确认未完整继承

V2 实际 LIBERO server `scripts/action_policy_server_libero.py:1054–1061` 接受 `return_video`、`profile_inference`；`:1150–1154` 可跳过 VAE decode，`:1164–1171` 可跳过 PNG 序列化，`:1200–1238` 返回模型/历史/资源的阶段耗时和内存信息。Root `scripts/profile_history.sh:26–39` 接入单卡、单 Episode 的 action-only profile。

V3 RoboCasa server `scripts/action_policy_server_robocasa.py:1188–1192` **每次正常预测都解码生成视觉**，`:1205–1211` 每次都编码 PNG/base64；客户端 `simulation/robocasa/eval_utils.py:157–174` 不发送相应开关。Batch C 的 `save_generated_video=none/first` 控制客户端保存，**没有减少后续请求的服务端 decode/PNG 成本**。

已有粗粒度 request latency 和日志仍在，不能称为没有遥测。建议后续单独恢复 request 级 action-only 开关、必要的视频采样和阶段计时，再用真实 GPU 测量收益；本次没有测加速幅度，也未修改视频合同。

证据：[V2 条件解码](https://github.com/wxwy/cosmos-framework/blob/e3dc9ecce0a4a7223245dc4f5b5efde7b709fd92/cosmos_framework/scripts/action_policy_server_libero.py#L1054)、[V3 无条件解码](https://github.com/wxwy/cosmos-framework/blob/c9f21040f462a114d597fc83773cb9b6a9e96214/cosmos_framework/scripts/action_policy_server_robocasa.py#L1188)。

### I-03 — `zero` / `init` 因果消融：未接入当前 RoboCasa 评测

V2 `inference/local_memory_policy.py:37–60` 有 auto/off/required/zero/init；`:421` 在 init 模式冻结 Fast Weight 更新，`:428–429` 在 zero 模式注入零 tokens。V3 `inference/robocasa_local_memory_policy.py:30,58–68` 和实际 server `action_policy_server_robocasa.py:517–520` 只有 off/required，正式 Queue 固定 required。

已有 `inference/local_memory_intervention.py:19–55` 的同输入/Seed Prefix-vs-None 对照不是 task-level zero/init 替代：它不能分别回答“Prefix 是否有效”和“在线适应相对初始化是否有效”。属于实验能力缺口，必须在独立消融协议中恢复，不能松动正式 required 模式。

证据：[V2 modes](https://github.com/wxwy/cosmos-framework/blob/e3dc9ecce0a4a7223245dc4f5b5efde7b709fd92/cosmos_framework/inference/local_memory_policy.py#L37)、[V3 modes](https://github.com/wxwy/cosmos-framework/blob/c9f21040f462a114d597fc83773cb9b6a9e96214/cosmos_framework/inference/robocasa_local_memory_policy.py#L58)。

### I-04 — Slow 参数实际变化见证、真实 Native 验证工具：部分继承

V2 的 `PSM_ACTIVE_METRICS_PATH` 接线 `ActiveDeliveryMetrics`（`model/generator/mot/active_local_memory_launch.py:397–402`），`grouped_active_metrics.py:75–102,134` 按所选参数记录优化前后样本及 **changed_samples**；`PSM_A2_POSTTRAIN_VALIDATION_PATH` 接线真实模型 `A2NativeValidation`（launch`:403–408`、`a2_native_validation.py:48–127`）。这些是可选/有界工具，不是每步默认的完整证明。

V3 有 rank-local gradient/parameter norms、Fast State 指纹和 bounded 缺梯度审计，但尚无等价的 Slow 参数优化前后变化见证。参见 `examples/psm_wma_robocasa_corrected_telemetry.py:282–312,380–404,526`、`corrected_phase5.py:901–912,1126–1128`。`local_memory_grouped_window_test.py:104–135` 的梯度对照是 toy CPU oracle，不能代替真实 Cosmos 功能见证。

**这不证明 V3 Slow 参数没有更新。** 它表明 V2 部分诊断工具未移植，Loss/Norm 下降不足以独立验证所有预期 Local 子组实际改变。后续宜做低频、有界、全 Rank/FSDP 合理的语义见证，不增加每步重型审计，也不恢复旧 B1 元素级严格等价作为 Fresh 前置。

### I-05 — 固定专家轨迹的 open-loop policy 诊断：未适配 Corrected RoboCasa

Root `tools/g0/r06_open_loop_replay.py:4–20` 在 V2 用固定专家观测测预测误差；当前 V3 保留该文件，但 `:33–40` 仍绑定旧导入/来源，`:73` 假设 action[T,7]，`:75–76` 使用 LIBERO 相机，`:79–82` 使用 domain=libero。

未找到接入当前 raw15/state15、Exact-Window 与 Corrected server 的对应工具。现有数据 ABI 校验和闭环 action evidence 不能直接替代“固定专家 observation/state 上的模型误差”诊断。它对区分模型预测、decoder、动作幅度和闭环场景漂移有帮助，建议作为独立诊断移植；不把旧 LIBERO 工具称为已验证的 RoboCasa 实现。

### I-06 — 公开操作入口和“当前状态”文档：明确未完成迁移

Root `scripts/train.sh`、`resume.sh` 仍委托 `train_local_memory_ttt.sh`，后者 `:6–7` 主动拒绝 V3；`scripts/eval.sh:4–5` 同样拒绝。更直接的问题是 `scripts/verify.sh:26–38` 仍导入当前 Child 不存在的 `active_local_memory_launch`、`_local_memory_fsdp_ignored_parameters` 和 `_sync_active_local_replicated_gradients`。

README`:15–19,64–69` 仍宣称旧 Child/旧运行状态，并推荐上述入口；`docs/current/training.md:25` 仍说明 Local 参数 replicated 的旧分布式实现。`PROJECT_STATUS.md` 和 `artifacts/CANONICAL.json` 也仍指向旧 V2 身份。

**训练/Resume/评测能力本身已有新后端**：`scripts/train_v3_packed128_staged.sh`、Corrected Phase5 preflight（`examples/psm_wma_robocasa_corrected_phase5.py:851–893`）、`scripts/run_robocasa_eval.sh`。缺的是公开门面/状态指引迁移，不应为兼容旧 verify.sh 把旧分布式算法重新加入。

证据：[旧 public verify](https://github.com/wxwy/psm_wma/blob/e577e05c2005d19b3b97f725624c447c53d20f0b/scripts/verify.sh#L24)、[旧入口保护](https://github.com/wxwy/psm_wma/blob/e577e05c2005d19b3b97f725624c447c53d20f0b/scripts/train_local_memory_ttt.sh#L6)。

### I-07 — 跨 Resume 的全程累计 task exposure：仅部分继承

V2 scheduler snapshot 包含 `cumulative_valid_consumer_exposure`（`model/generator/mot/local_memory_segment.py:287,330,361,382`、`active_local_memory_driver.py:422–440`）。V3 observer 从新 Counter 开始，并诚实标注 `task_exposure_since_observer_start` / `rank_local_observed_since_process_start_not_full_corpus`（`utils/training_audit.py:120–129,188–200`）。

训练 cursor/frontier 的 Resume 已有，缺的是自动恢复一份完整跨进程累计统计；可按历史日志去重汇总，不代表数据进度错误。属于审计统计能力，不应因补计数而修改冻结训练状态。

### I-08 — Slurm SIGUSR1 sentinel 紧急保存：特定环境能力未接线

V2 job_monitor 注册 `TerminationSignalCheckpoint`（defaults/callbacks`:131–144`）。当前 V3 保留类，但 Phase5 清空回调后未注册。触发机制是 `SLURM_LOG_DIR/SIGUSR1_RECEIVED` 文件（`callbacks/termination_signal_checkpoint.py:95–102,139–151`），并有最小保存间隔。

这**不是**通用 Ctrl-C/SIGTERM 自动保存保证。V3 的周期保存和 `--formal-execution-until` 已解决正常分段停止；只有将来使用 Slurm 抢占/超时通知时，才需要另做已提交边界上的安全接线。不能直接挂回旧 callback 或改变运行中 G1。

## 3. 明确延期的继承能力

| 能力 | V2 实际实现 | V3 当前状态与批准边界 |
| --- | --- | --- |
| 同 GPU 多 Session batched Local-TTT / vector env | LIBERO server`:962–999` + Local adapter`:413–443`；eval`:1391–1395,1494–1624` | RoboCasa server`:1028–1035` 在 required 模式拒绝 batch；off-mode batch 仍有。Phase6 v1.1`:526–532` 明确先做串行，Batch C 固定每 GPU 一个 Slot。需独立并发事务 Gate，不是意外回归。 |
| LIBERO 4-suite 完整 Local-TTT 训练/评测 | V2 Root eval.sh、Child `eval_libero_4in1_acceptance_v2.sh`、Local LIBERO server | V3 旧入口主动拒绝，generic LIBERO server 没有对应 Local adapter 接线。MC-07（迁移完成计划`:23`）明确延期，不能把文件存在当可用。 |
| none / native-window / GRU / TTT 四路历史对照 | V2 Root train/eval_history 与 `inference/local_memory_policy.py:42–87,151,408–409` | V3 保留的 shell 最终进入拒绝入口，实际 RoboCasa Local adapter 无 GRU/window dispatch。MC-07 明确延期；官方 KV recent-history 不是 E003 GRU 控制的替代。 |

另有低优先级 API 能力：V2 对特定 `ActiveSourceTransientError` 支持一次内容绑定首 Member 同进程重试（Trainer`:723–761`、grouped runtime`:249–275`）；V3统一 abort/reraise。V2直接生产 raise 未找到，主要有测试注入，不能扩称为“V2 能自动恢复任意 I/O/GPU 故障”。V3 fail-closed + DCP 恢复仍在；若恢复该可选能力，必须另审 RNG/FSDP/事务边界。

## 4. 已继承或经批准替换，不能算遗漏

- **Packed128 与 Stable Slot**：V2 A2 原本就是 Packed；V3 `local_memory_grouped_window.py:191–208` 和 ExactWindow planner 有对应实现，支持真实 Consumer 数和 terminal partial。
- **Batched Fast Weight / create_graph / Prefix 原生连接**：V3 segment adapter、model-owned scan、SequencePlan 和 memory_prefix 接线存在；不能因文件换名认定没有继承。真实效果仍需功能证据。
- **Episode 连续性、确定性 Epoch 重用**：V3 `data/generator/action/datasets/robocasa_exact_window_local.py:181–192,244–295` 有队列、epoch rollover、slot frontier。不是只跑一遍语料。
- **Fast State / Frontier 事务提交**：V3 `local_memory_grouped_window.py:146–153,219–243` 在成功 optimizer 后发布 live candidate，失败 abort。
- **严格模型/Optimizer/Scheduler/RNG/Dataloader/Local 状态保存恢复**：已有新 DCP/F1 实现；不能要求重造 V2 DCP 布局或恢复 V2 optimizer checkpoint。
- **Local replicated → 新 FSDP/DTensor model-owned scan** 是批准的 Host 适配。缺旧 `_sync_active_local_replicated_gradients` 本身不是功能丢失。
- **H16/raw15/state15/composite z_t、exact-window cache → Source 身份链、F0/F1 安全启动/分段/保存** 是当前新实现；旧 B1 endpoint、双相机独立编码、chunk32/iter500、旧自动 Fresh/Resume 行为不应按旧 v1.1恢复。
- **自动 periodic eval watcher → Owner 手动执行** 是本轮明确选择；不应以“继承”名义自动启动仿真。
- **RoboCasa whole-task Attempt Resume** 是场景 RNG/Reset 连续性约束下的选择，不应直接复制 LIBERO Episode 拼接恢复。

Index8 显式兼容入口仍是已记录的 **V3 自身兼容合同债**，但不是 V2 A2 Packed128 的能力丢失；Owner 已要求与主线安全修复分批，不作为 Packed Fresh 前置。

补充过滤：V2 Root `eval_robocasa.sh:103` 引用的 `action_policy_server_robolab` 在锁定 V2 Child 内并不存在。本报告 action-only/zero/init/batching 的依据来自 V2 实际 LIBERO server/adapter，不把旧失效 RoboCasa launcher 的参数当成功证据。

通用 Aux 系数也不能直接列为当前训练 bug：V2 分开计算 `n_i/N*primary + auxiliary/GA`，V3对 native total loss 统一按有效 Consumer 加权，非等长 terminal member 理论上不同。但默认 Edge 配置 `configs/base/experiment/sft/models/edge_model_config.py:71–74` 的 lbl coeff 均为 None；本轮未读取 G1 冻结运行配置。因此仅记录未来启用 Aux 时需要明确的损失合同，不断言现有 G1 正在使用错误目标，也不恢复旧 B1 数值阈值。

## 5. 建议顺序及边界

1. **先裁决 I-01 的梯度裁剪继承合同**：确认是否有意取消、未来新作业/跨版本恢复如何处理；不改当前 G1。
2. 为当前 RoboCasa 主线优先考虑 I-02 action-only/profile、I-04 有界真实参数/Native 见证、I-05 expert open-loop 诊断，再整理 I-06 public facade/当前文档。
3. I-03 消融、I-07 统计、I-08 Slurm 及明确延期路线按单独实验/部署需要立项；不要求一次补齐所有 V2 实验工具。

本轮仅把盘点落为文档，不自行下发整改、变更 Formal 训练语义、关闭新 Gate 或启动 DS/GPU。Batch C r2 的已有审核范围和实际训练授权不因本盘点自动变化。
