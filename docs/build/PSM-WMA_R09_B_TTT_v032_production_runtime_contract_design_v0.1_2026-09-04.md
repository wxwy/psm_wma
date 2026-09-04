# PSM-WMA R09-B TTT v0.3.2 production runtime contract design v0.1

**状态**：待三方同 SHA 设计审核；仅冻结 production runtime contract，不授权实现、GPU 或训练。
**设计基线**：v0.3.2 multi-slot TTT、C6 synthetic runtime closure（root `4fd219c` / Gitlink `fce9918`）。

## 1. 目标与边界

本 Gate 只冻结把已关闭的 CPU core/C6 synthetic seam 映射到 Cosmos Local Memory 生产调用的接口合同。必须保持：每个 causal timestep 只写一组 K/V；用更新后的 fast state 做 `K_local` 个 Q 读取；输出 `[B,K_local,32]`，再经既有 `local_memory2llm` 进入 K/V-only Memory Prefix。

本设计不授权：修改 production runtime、config/optimizer/checkpoint、P4/P5、真实模型/数据/cache/checkpoint I/O、GPU/CUDA/torchrun、训练、评测、推理或 LIBERO4IN1。上述事项必须另起 implementation、GPU smoke、matched smoke 和正式训练 Gate。

## 2. 唯一 state owner 与输入合同

新增 runtime adapter 必须由单一 chronology owner 管理每个稳定 rollout owner key（不得使用 packed batch row）。每个 control timestep 输入一个 canonical evidence record `e_t`、owner key、owner epoch、全局 `source_timestep`、segment id/row index、valid/done/reset 元数据；history window 不得在 runtime 内回放或重复写入。

owner 必须保证：同一 owner 的 timestep 严格连续；skip、duplicate、changed-byte、旧 epoch capability 在 fast-state kernel 前拒绝；pending segment 只能显式 abort 后 reset；reset 成功使 epoch 恰增一并清理旧 epoch replay/index。C5A/C6 已验证的 authority 不得在 production adapter 中重实现。

## 3. 训练调用语义

训练 adapter 以 `ttt_tbptt_steps` 分段，默认 16（与 RoboTTT 对齐），但该值可配置且不改变跨 segment carry 的数值 state。segment 内保留 outer task loss 到每个 materialized witness 的梯度图；segment 结束严格执行 `materialize once -> outer backward once -> commit`，无有效 row 时不得 backward 或 commit。KVB inner loss 只驱动 fast-state update，不加入 Cosmos outer loss。

outer loss 必须由原生 vision/action flow-matching 逐 item numerator 与 `outer_valid` 分母组成，padding/context-only item 不计入分母；denominator 为零禁止 optimizer step。Cosmos 原 target、mask、time weighting、loss scale 保持不变。

## 4. 推理调用语义

推理请求必须携带稳定 rollout/env identity、连续 timestep、上一步实际执行 action 及 reset/done；active-slot 压缩不得改变 owner key。Local W-only update 必须在最外层 `torch.inference_mode()` 之前完成，随后只以 detached `[B,K_local,32]` token 进入既有 Memory Prefix；AR 不读 Memory，DM 按 v0.3.2 的 K/V-only route 读取。请求缺少 identity、时序或 reset/done 信息时 fail-closed。

## 5. 参数、状态与 disabled parity

`theta_Q/theta_K/theta_V`、slot query bank、learned W0、encoder、`local_memory2llm` 与 modality embedding 是 slow learned parameters；fast W_t 仅为 owner runtime state，不注册为 model parameter/buffer，不进入普通 optimizer/checkpoint。`K_local` 必须为正整数且同一 batch present sample 一致；首版实现需保留 K=1 兼容路径并覆盖 K=1/4/8 shape/slot-order fixtures。

Local-disabled 必须通过公开 runtime bypass 产生 no-memory packed input、`None` payload 与零写/零 state，且与独立 no-memory baseline 在同一输入上的 packing/loss 逐值一致；不得以测试内两个 clone 自等作为唯一证据。

## 6. 后续 Gate 顺序

三方批准本设计后，依次申请并关闭：

1. production adapter CPU/static implementation（仅 runtime adapter、相邻测试）；
2. config/optimizer/checkpoint selector 与 state-schema design/implementation；
3. 最小 GPU smoke（短训练、validation、checkpoint reload）；
4. matched LIBERO4IN1 latent-cache smoke；
5. 正式 Local Memory 训练。

任一 Gate 的批准不隐含解锁后续 Gate；在全部所需审核同 SHA 批准前不得越过当前 Gate。
