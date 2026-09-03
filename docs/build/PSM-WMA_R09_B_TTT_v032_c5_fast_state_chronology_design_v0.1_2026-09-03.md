# PSM-WMA R09-B TTT v0.3.2 C5 持续 fast-state 与时间因果设计 v0.1

**日期**：2026-09-03  
**状态**：design-only；实现前必须三方同 SHA 审核  
**上游权威**：`PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.2.md`  
**前置关闭 Gate**：C2 multi-slot CPU core、C3 source/ABI audit、C4 Memory Prefix CPU contract  

## 1. 目的与范围

C5 只把已关闭的 multi-slot continual-TTT CPU core 接到一个**独立、显式、逐 control-timestep** 的 Local runtime owner。它解决当前 `LocalHistoryRuntime` 仅对窗口重放、没有跨调用 `W_t` 生命周期的问题。

本设计不把 fast state 伪装为 Cosmos `MemoryState`/native KV cache，也不接入 `Cosmos3VFMNetwork.forward`、packer、attention、trainer、config、optimizer、checkpoint 或数据读取。实现和验证仅可使用合成 CPU tensor。

## 2. 独立状态与输入合同

新增 runtime（名称在实现 Gate 固定）持有的输入/输出必须显式为：

```text
state_in: ContinualTTTFastState | None
evidence_t: [B,256]                 # 本 control timestep 新完成且因果可见的唯一 evidence
valid_t: [B] bool                   # false 行不写入、不读取、输出精确零
done_before_t: [B] bool             # true 行在本 timestep 写入前重置为 learned W0
step_index_in: [B] int64            # 当前未 detach 的 segment 内更新计数
```

输出：

```text
tokens_t: [B,K_local,32]
state_out: ContinualTTTFastState
present_t: [B] bool
step_index_out: [B] int64
```

`state_in=None` 只表示本 episode 的初始化，不表示重新扫描历史窗口。runtime 不接受 `[B,H,256]` 作为生产 C5 输入，以避免把 overlapping history 重放成重复写入。

## 3. 固定顺序与逐样本语义

对每个样本行严格执行：

1. 若 `done_before_t`，先以 learned `W0` 重置该行及该行计数；
2. 若 `valid_t=false`，state 和计数保持，`tokens_t` 精确全零、`present_t=false`；
3. 若有效，恰好一次 `theta_K(e_t), theta_V(e_t)` KVB write，得到更新后的 `W_t`；
4. 仅从更新后的 `W_t` 用 `theta_Q(e_t)+r_k` 一次性读取 `K_local` 槽，输出 `[K_local,32]`；
5. 有效行计数加一。不得重复 K/V write，不得先 read 后 write。

不同 batch 行不得交换或共享 state；一行 reset 不得影响其他行。`present_t == valid_t`，但其含义是“本调用产生有效 Local slots”，不是 native KV-cache initialized 标记。

## 4. TBPTT 与梯度边界

`ttt_tbptt_steps` 必须是正整数，默认 **16**，与 RoboTTT 对齐；允许配置其他正值。它是梯度截断长度，不是 state history horizon，也不是 episode reset 周期。

每个有效行在计数达到该长度后，必须在该 timestep 的 outer-loss readout 已建立后，对**该行** `state_out` 执行 `detach_state()` 并把计数归零。该 detach 不得改变 fast-state 数值、Local token 数值或其它 batch 行；下一 timestep 从数值相同但无跨段图的 state 继续。训练段内调用 `create_graph=True`；inference 语义虽允许 fast update，但不属于本 Gate 的运行授权。

## 5. 失败关闭与禁止混用

实现必须在任何投影/inner update 前拒绝：shape、dtype/device、nonfinite、`valid_t`/`done_before_t`/计数 shape 不匹配，负计数，或不合法 TBPTT 长度。以下均明确 fail closed：

- `torch.inference_mode()` 或 `torch.no_grad()` 下的训练/meta-update 路径；
- 将 C5 state 与 `MemoryState`、CUDA graph、replicated attention-I/O 混用；
- 将窗口 replay、future evidence、未完成 observation、GT future action作为 `evidence_t`；
- 由 C5 创建/恢复 checkpoint 或改变 optimizer 参数集合。

## 6. 后续最小实现与 CPU 验收

仅在本设计获得三方 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_C5_FAST_STATE_CHRONOLOGY_CPU` 后，才允许修改 `local_evidence.py` 与相邻 `local_evidence_test.py`，新增：

- 正常两段/多段 carry 等价于连续 scan 的数值与 write-count；
- 一次 write、更新后 multi-slot read、`K_local=1` compatibility；
- per-row reset、稀疏 valid、不同行独立性；
- 默认 16 与非默认截断长度，detach 数值不变且图边界正确；
- future/overlap replay 拒绝由显式 step identity（如实现需要）或 runtime 不接受 history tensor保证；
- 参数梯度可达 `theta_Q`、slot queries、`theta_K/V`、learned W0；fast state 不进入 `named_parameters()`。

CPU selector、`py_compile`、child/root `git diff --check` 是该实现 Gate 的最低证据。C5 closure 后仍须独立 C6（config/optimizer/checkpoint）、C7（CPU 全量复审）、C8（GPU smoke）及 C9（LIBERO4IN1 matched smoke）审核；本文件不授权任何 GPU、训练、评测、推理或真实 cache/checkpoint I/O。
