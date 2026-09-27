# PSM-WMA V3 H3-E — 8×H100 集成短跑设计 v0.1

- 日期：2026-09-27。cx 负责技术决策、harness/CPU preflight 与 blocker 修复；ds 执行独立 GPU 验证；ChatGPT 非在线审核，不作为 CPU 构建停点。
- 只做两个优化窗口的 matched smoke：fresh `max_iter=1` → 保存 DCP → 同一 output job `max_iter=2` 恢复。不得自动缩小 8 rank、8 slot、GA2、T16、K4、raw15、policy chunk32/33 帧，不得退回 4090 detached relay。

## 输入和模型

启动资产为 Stage-A one-step Edge-Policy-DROID DCP 与其 resolved config；本地 Edge tokenizer、Wan VAE、RoboCasa v3.0 18 类 train source、双相机 cached latent。policy 仍走官方 RGB→Wan VAE；cache 只供 Local evidence。每 rank 的 H3-B catalog 按稳定 UID hash 分片，固定 8 stable slots 和同 index B≤8 native batch。Stage-A DCP warm-start 仅允许缺 `net.local_memory*`、禁用 EMA；upstream DCP planner 的 `keys_to_skip_loading=["net_ema.", "local_memory"]` 只用于 warm-start，同 job resume 自动不用 skip，须严格载入全部 slow+Local 状态。配置显式保留 `max_action_dim=64`、`raw_action_dim=15`、`num_embodiment_domains=32`、`encode_exact_durations=[33]`、20fps。

8×H100 profile：FSDP shard degree8、replicate1；沿 Stage-A 配置使用 BF16 compute、FP32 master、BF16 reduce。selected optimizer namespace 为 `moe_gen,time_embedder,vae2llm,llm2vae,action2llm,llm2action,action_modality_embed,local_memory`。冻结 reasoner/其余 host，完整 Local trainable inventory 165312。沿用 Stage-A FusedAdam/LR、domain projection weight-decay skip 与 ActionTransformPipeline；GA2 由 H3-C trainer 窗口归一化一次，不复用 4090 Local-only config。

## 启动与记录

child 新增独立 H100 smoke launcher，CLI 必须显式给出 output root、formal root/child SHA 与 `fresh|resume`；两阶段使用相同 job namespace，preflight 不创建 GPU 产物。每 rank 写 append-only phase/consumer CUDA memory JSONL、selected parameter inventory、loss/grad witness、optimizer/commit 事件与 result JSON；任何失败保留原始目录，不覆盖。观测只在 H3-E smoke 开启，不改变训练目标/梯度；OOM 不降级。fresh 需一窗口一次真实 optimizer step 与 fast/frontier commit、DCP iter1；resume 需读取同 job iter1 的 model/optim/scheduler/GradScaler/trainer RNG/Local rank-pkl，执行下一窗口并保存 iter2，记录 next identity 与恢复状态 digest。

CPU preflight/测试验证：本地资产与 DCP metadata、18 类 catalog digest、rank partition、完整 trainable selector、warm-start skip 仅在外部 DCP 生效、真实 Stage-A 8 consumer batch ABI、CLI pair 锁、fresh/resume 同目录规则、监控字段；Ruff/format/diff-check PASS。cx 不启动 GPU；ds 按冻结命令跑 8×H100，回传原始 Evidence。H3-E 真实 PASS 后 H3-F 才冻结正式长训 cadence/output 与命令。
