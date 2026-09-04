# PSM-WMA R09-B TTT v0.3.2 C6 runtime integration design v0.2

**状态**：v0.1 superseded；待三方同 SHA 设计审核。本文只冻结 synthetic adapter seam，不授权生产 Cosmos 接线、配置/检查点变更、GPU 或训练。

## 1. 唯一 Gate 边界

C6 实现仅新增/修改 `cosmos_framework/model/generator/mot/` 下的 test-only synthetic adapter 与相邻 CPU tests；不得修改 `omni_mot_model.py`、`data_and_condition.py`、`unified_mot.py`、`cosmos3_vfm_network.py` 的 active runtime path。adapter **直接委托**已关闭的 `C5AOwnerSegmentCPU`（不重实现 authority、phase、epoch、replay 或 rollback），从而继承其 36 项验收语义。

本 Gate 禁止 config/optimizer/checkpoint schema 或 identity refreeze、Cosmos attention/packing、真实模型/数据/cache/checkpoint I/O、GPU/CUDA/torchrun、P4/P5、B2-T、训练/评测/推理及 LIBERO4IN1。`K_local` 只在 synthetic fixture 以 `1` 传入，不在本 Gate 固化 checkpoint identity；其正式配置另开 Gate。

## 2. 生产边界映射（仅以 synthetic provenance fixture 冻结）

adapter 的可信输入由 fixture producer 生成不可变 completed-causal capability，字段为：

```text
owner_key      = episode_id + "/" + rollout_id
source_identity = segment_id + ":" + timestep
source_timestep = segment-relative integer
epoch          = owner reset/done counter
provenance     = R08_COMPLETED_CAUSAL
source bytes/schema/digest = C5A canonical serializer
```

唯一 authority 仍是被委托的 `AdmissionAuthority`；adapter 不接受 caller 字符串/布尔值替代 capability，不维护第二份 chronology/reverse index。每次 `reset/done` 先 abort pending（若存在则拒绝 reset），再递增 epoch；新 epoch 的同 owner/identity/timestep 必须可用新源字节重新 admission。admit 的 lookup-before-allocation、replay、changed-byte、cross-owner/epoch、hostile-source fail-before-C5 直接由 C5A 委托覆盖，并在 adapter tests 复现。

## 3. 整段 transaction 与 terminal 语义

每个 owner 的一个 segment 必须先在 `COLLECT_RAW` 收集全部 contiguous timesteps，再**一次**调用 delegated `materialize()`/`materialize_many()`：

```text
COLLECT_RAW (all rows)
  -> MATERIALIZED_PENDING (full N or terminal r)
  -> one scalar segment outer loss backward reaches every witness
  -> BACKWARD_OK
  -> atomic commit/detach
```

保留 C5A 的 `N∈{1,3,16}`、terminal `r=0`（无 backward）、`0<r<N` 与 `r=N`（一次 backward 后 commit）、abort/backward-failure exact rollback、pending 期间禁止下一 segment admission。adapter 不得退化为每 timestep 的 N=1 commit。

## 4. segment outer-loss 来源

Cosmos window task loss 按 segment 的 timestep/owner 选择得到一个标量：

```text
L_segment = sum(L_task[t] for t in segment valid rows) / max(valid_count, 1)
```

该 scalar 是 adapter `backward_and_mark[_many]` 的唯一输入；它必须保留从每个 materialized witness 到 outer loss 的图路径。`r=0` 没有 valid row，不调用 backward 或 commit candidate。C6 synthetic tests 用 witness-connected scalar 模拟 window-loss slice，并覆盖 unrelated/grad-free/partial-owner 拒绝。

## 5. Local Memory 形状边界（只作 synthetic assertion）

delegate readout 输出 `[B,K_local,32]`，其中 C6 fixture `K_local=1`；既有 C4 prefix adapter 的形状断言为 `[B,K_local,32] -> [B,K_local,2048]`，Local 仍只进入 K/V-only Memory Prefix，不成为 Q_MEM，不新增 residual/MLP。Local disabled synthetic path 必须与 no-memory 输入/packing/loss 保持 parity。

## 6. C6 synthetic 验收与后续 Gate

验收：C5A 全量 fixture 委托回归；整段一次 materialize、N/terminal 矩阵、B>1 permutation、owner/source/epoch/replay/hostile admission、segment-loss witness 全覆盖、失败回滚、Local disabled parity、shape/grad/no-grad fail-closed；CPU pytest、py_compile、双仓 `git diff --check` 全部 PASS。

只有 C6 synthetic adapter closure 获三方同 SHA批准后，才可另起 production runtime contract/config-checkpoint design、最小 GPU smoke、matched LIBERO latent-cache smoke 和正式训练 Gate；本文不授权任何后续执行。
