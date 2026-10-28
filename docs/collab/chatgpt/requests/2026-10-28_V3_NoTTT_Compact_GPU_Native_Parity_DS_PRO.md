# DS_PRO 执行令 — V3 No-TTT Compact 0/1 真实模型 GPU Forward/Loss/Gradient Parity

- 日期：2026-10-28
- **Owner 本轮授权仅本文件描述的隔离 GPU Parity Gate**；不是允许生产 Resume、停止正式 Job、变更 Checkpoint 或重新训练。
- Reviewer：ChatGPT；Executor：DS_PRO。DS 只执行已冻结范围、归档原始 Evidence，不自行批准 Gate。
- **被冻结的 No-TTT formal implementation**：historical Root `49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9`（其后 Root 包含其他评测/文档 commits），Child/Gitlink `746c5cf2f2324104a62fb71510343aa40d3976c5`。实际运行前只读记录当前 Root SHA、Child SHA 与 Gitlink；Child不一致即 `BLOCKED_SOURCE`，停止。
- **已关闭的上一 Gate**：`docs/collab/chatgpt/reviews/2026-10-28_V3_Compact_Segment_NoTTT_CPU_Evidence_Closure.md`；不要重复 CPU 4 Consumer、3 partial、512 Consumer、Transformer Benchmark或旧 nw0/nw8 审计。

## 0. 最高优先级：GPU 资源预检（GPU 未空闲时仅做这一步）

正式 No-TTT 原使用 GPU4–7；此前报告 GPU0–3 属外部 wzy 任务。**不得根据历史猜测当前可用性**。

1. 在训练服务器只读执行：
   `nvidia-smi --query-gpu=index,uuid,memory.used,memory.total,utilization.gpu --format=csv,noheader`
   `nvidia-smi --query-compute-apps=gpu_uuid,pid,used_gpu_memory --format=csv,noheader`
   必要时只读 `ps -o user,pid,cmd -p <PID>` 查归属；完整 nvidia-smi 输出别暴露隐私信息。
2. 需要 **4 张同时空闲、与其他训练/推理任务物理隔离的 NVIDIA GPU**，用于一次 world4 FSDP2 小 Gate；设备号不限定，但必须先核对没有占用。不得抢占/杀死/暂停/降低既有任务负载，不得运行在当前 No-TTT 使用的设备上。
3. 如果没有4张明确空闲 GPU：**立刻结束，返回 `BLOCKED_RESOURCE` + 当前可用卡数量/占用概况。不得启动模型、torchrun、CUDA 或安排后台等待/轮询。** 这是合法交付结果，不要改成1卡/2卡伪造 world4 FSDP2 Gate。
4. 若资源充足，再执行以下1–5。启动前再次核查资源、显存与用户进程。

## 1. 训练源/输入冻结（必须）

- 不允许运行 `scripts/train_v3_matched_no_ttt_4gpu.sh` 或 `examples/psm_wma_robocasa_corrected_phase5.py` 的 `main()/trainer.train()`；它们会进入训练/Job/DCP生命周期。
- 只新建临时隔离 GPU Parity harness `/tmp/v3_nott_compact_gpu_parity.py`，可调用现有源码库函数，但不修改任何 production Python、Hydra/TOML、Git HEAD、v3_job_identity 或现有 Job目录。Harness 本身仅是测试工件，执行完成后提交脚本/JSON/日志，不合并为生产代码。
- 真实 Native 模型：使用正式 No-TTT `overlay_config` 等价的生成策略/参数选择，`local_memory_enabled=False`、FSDP2 shard_degree=4 replicate=1、相同 precision/compile/activation checkpointing；`model.training_step(...)` 必须是正式 Native 实现（禁止 mock/替换 loss、stub、只跑 inference）。
- **权重冻结**：可只读加载已经验收的独立 `BASE_CHECKPOINT_PATH`（DROID 起点），两侧使用**同一个加载后权重和模型 buffer**。不要读取/复制/Resume 运行中的 No-TTT `no_ttt_packed128_droid_fresh_30k_world4_ga4` DCP；不做正式 optimizer/scheduler state Restore。
- 如模型无法在不启动 trainer.train / 不写正式Job情况下按生产 FSDP2 配置只读加载权重，报告 `BLOCKED_HARNESS`；不得通过启动 Fresh/Resume 训练“绕过”。
- Frozen CPU 输入：使用已验收 Catalog/Index/Source、T16/B8/GA4、`ExactWindowRankPlanner(rank=实际RANK,world_size=4,b_stream=8,active_ga=4,seed=0)` 的 **同一 `plan.members[0]`**（每rank 8 Segment×16 Consumer=128）；两侧独立 `NoTTTCpuLoader`/Producer（可采用已验证的 workers=1/prefetch=1以限制CPU负载），按同一 Request顺序构造 `SegmentBatch` → `MatchedNoTTTWindow.pack` → `collate_grouped_native_batch`。只需要**一个 GA Member（每 Rank 128）**，不重复上一轮全 Window 四个 Member。
- 预处理在 CPU 上先完成并固定 A/B 两份相同的 Native Batch；对同 Rank 的 Python、NumPy、Torch CPU RNG 输入做同起点比较。验证除预期 Video storage/stride/proxy 与 Host device 外，Raw/Action/Token/Latent/SequencePlan/Position完全一致；不一致立即失败，**不进入 GPU**。
- 训练-等价 loss：使用同一个冻结 iteration（推荐 `iteration=1000`，两侧必须相同），对该单 Member 使用正式 No-TTT `weighted_loss = loss * (len(payloads) / plan.n_window)`，本 Gate 正常情况下为 `128/512 = 0.25`。只比较从这个 Member产生的梯度，不声称跑了完整4-GA更新。

## 2. 真实模型 GPU Parity：最多两侧各一次 Forward+Backward

- 用隔离的 `torchrun --standalone --nproc_per_node=4` 启动 `/tmp` 的测试 Harness，`CUDA_VISIBLE_DEVICES` 仅列出通过预检的4张 GPU。记录每 Rank 与物理 GPU UUID 映射。每Rank用本卡，真实4GPU FSDP2参数分片，不能用单进程模拟分布式；训练模型 mode为 `train()`，不能切 `eval()`。
- 禁止 `optimizer.step()`、`scheduler.step()`、`grad_scaler.step/update()`、`checkpointer.save()`、正式 `trainer.train()`、以及新建正式 Job namespace。可**初始化**训练同款 optimizer 只为确定 `keys_to_select`、`requires_grad` 和分组；不得执行任何更新。模型权重和 buffer 必须在A/B两侧保持相同；若模型 forward 改写 buffer且无法安全恢复，则 `BLOCKED_HARNESS`，不可忽略。
- 对 **Compact=0 / Compact=1** 顺序执行，先对上一计算 `zero_grad(set_to_none=True)`，并在每次 `move_cached_native_batch` / `model.training_step(batch,iteration)` 前恢复相同 Rank-local **Python random、NumPy、Torch CPU、Torch CUDA RNG state**；必要时在开始前做一次额外初始化/compile warmup，且warmup不进入两侧计量。
- 移动数据务必调用正式 `move_cached_native_batch(...,move=misc.to)`。检查 Dense模式的 `video` 为真实CUDA Tensor、Compact模式的 `video` 为经验证的CPU shape-proxy（预期设备差异，不算失败），其余 Native loss 相关输入 Tensor 的dtype、数值、形状、设备一致。
- 调用 `output,loss = model.training_step(device_batch,iteration)`，按 `weighted_loss` 反向传播。每侧要记录所有可得 Native model output 的 Tensor字段（特别 `flow_matching_loss_action`、`flow_matching_loss_vision`、总 loss）、标量、shape/dtype，及所有真实 optimizer 选中可训练参数的 **per-rank FSDP local gradient**。
- 每个 selected parameter 检查 `grad is None` 存在性、local shape/dtype、finite、`max_abs` 与 `max_rel/L2`。**不只比较总 grad norm、也不只看 action head。** 分组覆盖 `GENERATION_KEYS`，包括 action和video generation；禁止遗漏 FSDP shard 和其它被训练选中的模块。DType和参数组集合必须逐Rank一致。
- 在比较前显式 `torch.cuda.synchronize()`；只在隔离测试中同步，无所谓同步开销。每侧结束后必须能确认：没有 optimizer/scheduler/权重更新，没有任何正式DCP/Job文件写入。

## 3. Numeric Gate 标准（冻结；DS不得自行放宽）

- 每 Rank Frozen Request序列、valid mask、实际 Consumer位置相同；Native `video_latent/action/text_token_ids/sequence_plan` 与上轮CPU parity一致，GPU H2D的非Video数据相同。
- 两侧所有 Native output key set、shape、dtype一致；所有应有限的 loss与梯度均finite，无NaN/Inf。
- 标量 `loss/weighted_loss` 和 `flow_matching_loss_action/flow_matching_loss_vision`：`atol<=1e-5, rtol<=1e-4`。其它返回Tensor也应对照相同语义（不能忽略所有非标量输出）。
- 所有选中可训练参数 FSDP local gradients：同一 per-rank 参数集合、`None`分布/shape/dtype相同；非None梯度逐元素 `torch.allclose(rtol=1e-3,atol=1e-5)`，报告全参数分组覆盖、worst10、max_abs、relative_L2；仅 `grad_norm` 接近不能PASS。
- A/B 结果不满足阈值时 `FAIL_PARITY`，记录首个差异；如怀疑随机非确定性，仅允许额外**一次**Compact0→Compact0重放（相同Seed、同权重、同Frozen Batch、同运行配置）作`INCONCLUSIVE_NONDETERMINISM`判别，不能擅自改阈值、禁用训练特性、减Batch或变更训练精度。
- 任意 Rank触发异常/OOM，所有 Rank fail-closed、释放隔离资源；不自行扩资源或重复冒烟，状态为 `BLOCKED_RESOURCE` 或 `FAIL_RUNTIME`，附报错阶段。**只有全部四Rank全部检查PASS，才可向GPT申请 Evidence review；DS不得自行宣布正式Gate关闭。**
- 这不是性能 Benchmark，**不要求/不允许扫描 nw、OMP或额外Step Wall实验**，不承诺10s/Step。

## 4. 可执行步骤 / 退出条件

1. `S0 CPU/GPU preflight`：记录 Root/Child、确定4个空闲GPU，验证输入文件是只读，且正式No-TTT训练无改变。如不足即`BLOCKED_RESOURCE`并结束。
2. `S1 Harness/CPU Batch`：独立 `/tmp` 小脚本，复用上一闭合CPU Gate已有结构/字段检查，冻结每rank `plan.members[0]`；不得重做全量16/32Test或使用在线VAE。
3. `S2 Native model load`：生产等价 config、只读加载固定DROID Base model参数、4 Rank FSDP2、train mode；检查 trainable inventory。不能安全加载立即 `BLOCKED_HARNESS`，停止，禁止改训练代码。
4. `S3 A/B`：同起点 RNG、同权重、同一Batch、相同iteration、Native `move_cached_native_batch`→`training_step`→`weighted.backward`→per-key/per-param对比。必要时一次Dense/Dense重放。
5. `S4 结果归档`：脚本、JSON、Rank日志（去除敏感凭证、只保存指标）、截图/资源预检摘要与SHA。不要保存模型权重、完整数据样本、生产DCP内容，且只写隔离`/tmp`或`docs/collab/chatgpt/evidence/`。不自动Git提交生产源码，不写正式Job日志。

## 5. 最终交付（固定 JSON Keys + PASS 认定）

- `gate="V3_NOTTT_COMPACT_0_VS_1_NATIVE_GPU_PARITY"`
- `source.root_formal`、`source.root_head_actual`、`source.child_gitlink`、`model.checkpoint_source`、`model.local_memory_enabled=false`、`model.precision`、`model.distributed="FSDP2_WORLD4"`
- `resources.gpu_uuids`、`resources.preflight_process_count`、`resources.safe_to_launch`、`resources.block_reason`
- `input.world_size=4, b_stream=8, t=16, ga=4, member=0, consumer_count_per_rank=128, weight=0.25`（如果有terminal partial则按真实count/plan.n_window）
- `input.valid_mask_eq`、`input.ordered_positions_eq`、`input.native_nonvideo_eq`、`input.video_expected_proxy_diff`、`input.rng_start_eq`
- `metrics.rank0..3.loss/weighted_loss/action_loss/vision_loss`，含Dense/Compact/max_abs/rtol判定
- `metrics.rank0..3.grads.selected_param_count/covered_param_count/none_mask_eq/dtype_shape_eq/finite/allclose/max_abs/max_rel_l2/worst10/group_coverage`
- `metrics.rank0..3.model_weight_unchanged`、`rng_after_info`、`no_optimizer_scheduler_step`、`no_checkpoint_write`
- `status` 只能取 `PASS_CANDIDATE` / `FAIL_PARITY` / `FAIL_RUNTIME` / `BLOCKED_RESOURCE` / `BLOCKED_HARNESS` / `BLOCKED_SOURCE` / `INCONCLUSIVE_NONDETERMINISM`。
- DS提交 `docs/collab/chatgpt/evidence/2026-10-28_nott_compact_gpu_parity_<unique>.{py,json,log,md}` 的 isolated Evidence（或以附件提供），**只返回本轮结果，不修改任何生产代码、模型、checkpoint或训练配置**。

## 6. 授权与下一 Gate 不可混淆

- 本文件是**唯一授权的GPU实验范围**：一个Frozen Member上 Compact0/1 native Forward/Loss/Grad parity，读已验收Base模型，不接管正式 Job。
- `PASS_CANDIDATE` 只是向GPT提交的验证结论，**不代表已完成独立审核、不授权Resume、不授权更改当前训练Compact开关**。
- 当前正式训练是否运行由资源预检只读判定；不得停训、抢卡或后台等待。如果没有四张GPU空闲，直接交付 `BLOCKED_RESOURCE`，无需浪费时间构建Harness。
