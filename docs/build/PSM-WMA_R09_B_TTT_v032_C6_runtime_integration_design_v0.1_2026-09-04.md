# PSM-WMA R09-B TTT v0.3.2 C6 runtime integration design v0.1

**状态**：待三方同 SHA 设计审核；仅冻结 runtime contract，不授权实现、GPU 或训练。

## 1. 目标与边界

C6 将已关闭的 C5A synthetic CPU owner/segment contract 接入 Cosmos Local Memory 模态支路。接入必须保持 v0.3.2：每个 causal timestep 只写一组 K/V，更新后的 persistent fast state 用 `K_local` 个 Q 读取，输出 `[B,K_local,32]`，再经既有 `local_memory2llm` 进入 K/V-only Memory Prefix。

本 Gate 只允许 synthetic CPU runtime contract 与相邻单测；禁止真实 staging/P4/P5、模型/数据/cache/checkpoint I/O、GPU/CUDA/torchrun、训练/评测/推理、配置/optimizer/checkpoint refreeze。

## 2. 唯一 runtime 生命周期

每个 sample 绑定稳定 `owner_key` 与 `source_identity`。训练 segment 内严格执行：

```text
completed-causal source admission
  -> LocalEvidenceEncoder [B,256]
  -> C5A materialize/materialize_many (一次 K/V 写入)
  -> ordinary outer loss backward (必须到达每个 witness)
  -> C5A commit
```

`MATERIALIZED_PENDING` 未完成 backward 时禁止 commit、下一 timestep admission 或 segment finish；异常只允许 abort 后以新 epoch 重试。C5A wrapper 不得被生产 runtime 直接 import，生产侧复用同一 phase/owner/epoch 语义的最小 adapter。

## 3. Cosmos 接口合同

- Local payload 只进入既有 `MemoryPrefix` K/V 路径，不成为 Cosmos attention query，不新增 residual/MLP/Q_MEM。
- `K_local` 为正整数配置，并进入 checkpoint identity；首个 runtime fixture 使用 `K_local=1`，同时断言 `[B,K_local,32] -> [B,K_local,2048]`，不把单 slot 写成永久常量。
- `local_memory2llm`、modality embedding、Memory Prefix LayerNorm/packing 复用 C4 已关闭入口；不得复制第二套投影或改变 AR/DM attention mask。
- Local disabled 时输入、packing、loss 与 no-memory 路径逐位不变；Local present 时只增加 Memory Prefix K/V。

## 4. 梯度与模式边界

outer task loss 是唯一训练目标；inner KVB loss 只通过 differentiable update 影响 `theta_K/theta_V` 的 meta-gradient，`theta_Q/slot_queries` 由 readout 路径直接获得 outer gradient。runtime 必须在 ordinary grad-enabled training context 中 fail-closed；`no_grad`、`inference_mode`、eval/closed-loop 读取不得 mutate fast state。

## 5. 允许修改的最小范围与验收

仅允许以下生产入口及相邻 CPU tests 的最小修改：

`omni_mot_model.py`（owner/source/segment 调度）、`data_and_condition.py`（Local payload contract）、`unified_mot.py`/`cosmos3_vfm_network.py`（调用既有 Memory Prefix）、以及对应 `*_test.py`。不得改 optimizer、checkpoint schema、attention 算法或训练命令。

验收至少包括：Local disabled parity；B>1 owner permutation；同 epoch chronology/duplicate/replay；backward witness 全覆盖与失败回滚；`K_local=1` shape/gradient；mixed optional samples 的 None/shape 对齐；no-grad fail-before-mutation；py_compile、CPU tests、双仓 `git diff --check`。未通过不得进入下一 Gate。

## 6. 后续 Gate

C6 设计批准后才可提交 C6 synthetic CPU implementation；其 closure 另需三方同 SHA。之后仍需独立的 config/optimizer/checkpoint contract、最小 GPU smoke、matched LIBERO latent-cache smoke 与正式训练 Gate；本设计不授权任何训练。
