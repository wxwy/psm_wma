# PSM-WMA R09-B TTT v0.3.2 active Cosmos/trainer wiring design v0.2

**状态**：v0.1 superseded；待三方同 SHA 设计审核。仅冻结 active wiring contract，不授权实现、GPU 或训练。
**基线**：v0.1（root `35f8814`）收到 ChatGPT `efcebe3` 与 Kimi 各两项 HIGH/MEDIUM 意见、MM approve；本 v0.2 冻结精确训练 chronology、trainer 事务语义与可检验 disabled parity。其余继承 v0.1 未受质疑部分（config identity、唯一 owner、DCP slow-only、env 互斥、范围边界）。

## 1. 精确训练 chronology（ChatGPT HIGH-1 / Kimi HIGH-1 整改）

冻结映射：**1 micro-batch = 1 native window = 1 evidence row**（`runtime_evidence_steps=1`）。对每个 window 行 `t`（owner 全局连续序号），精确顺序为：

```text
1. admit(t)：graph-free raw evidence 进入 pending（不建图、不改数值 state）。
2. read(t)：当前 window 的 Memory Prefix 从 fast state 读取。
   可见性规则：window t 恰好可见 row 0..t-1 的 post-update 结果，
   永不可见自己的 row t（因果）。记该读取语义为 read-after-(t-1)。
3. write(t)：row t 的数值 fast update 在 forward 内以 detached 方式
   恰好应用一次，推进 candidate state；不写 committed state。
```

两种 read 模式，按 segment 位置二选一，互斥：

- **中间 window（pending 未满 `ttt_tbptt_steps`）**：read 走 **detached candidate state**，不建图。candidate state 由逐步 detached write 推进，因此无 stale read；本 window 的 task loss 不向 Local 慢参数提供梯度。
- **segment-closing window（pending 满 16 或 terminal remainder）**：本 window 的 forward 内执行 `materialize`：从 committed base state 对 pending raw rows 做一次 `create_graph=True` 全 segment scan，产出 witness graph。materialize 的数值结果必须与逐步 detached write 的 candidate state **逐位相等**（同一确定性更新规则对同一 raw rows 重放）；它不第二次数值应用 write——committed/candidate 数值 state 只由第 3 步的 detached write 序列决定，materialize 仅提供等价数值的可微图。本 window 的 read(t) 从 witness graph 取值（同一数值、带图），从而 segment 的唯一一次建图 backward 向四组 slow 参数提供恰好一次 meta-gradient。

**梯度覆盖性质（显式冻结）**：每个 segment 内只有 closing window 的 task loss 经 witness graph 反向传播到 Local 慢参数；中间 window 的 Local read 全部 detached。即 slow 参数每 `ttt_tbptt_steps` 个 micro-batch 获得一次非空梯度，其余 step 梯度为 None（AdamW 跳过该参数）。这是有意冻结的 TBPTT 语义，不是缺陷。

## 2. Trainer 事务语义（ChatGPT HIGH-2 整改）

事务 owner 为一个专用 lifecycle callback（实现 Gate 新增模块），hook 现有 callback 接缝，不改变 trainer 主循环代码路径。精确调用顺序（每个 micro-batch）：

```text
zero_grad(上一步) → forward（§1 admit/read/write，必要时 materialize）
→ on_before_backward → loss.backward()（native 无条件执行）
→ on_after_backward：若本 micro-batch 为 closing window 且 backward 成功
   → commit（fast state 推进、replay/identity 入库）；
   否则无 Local 动作
→ grad-accum 窗口满 → optimizer step → scheduler
```

- **backward 基数**：trainer 每个 micro-batch 恰好一次 `loss.backward()`（不变）；其中每个 segment 恰好一次（closing window 那次）携带 Local witness graph。禁止在 segment 打开期间对 Local witness 做任何额外 backward；中间 window 本无 Local 图，不存在可backward的 Local 分量。
- **optimizer/scheduler 顺序不变**：optimizer step 与 scheduler 仍按 grad-accum 窗口推进；slow 参数在非 closing step 梯度为 None 被跳过，不构成"segment 未关闭就推进 slow 参数"。
- **失败语义**：closing window 的 loss 非有限、`loss.backward()` 抛错、或 optimizer step 失败/被跳过（grad-scaler 等）时，对该 segment 执行 `abort`：candidate state 精确回滚到 committed state（逐张量相等），pending 清空，不得部分 commit；slow 参数梯度由现有 grad-scaler/optimizer 机制整体丢弃，与 fast state 回滚保持一致，二者不得静默分叉。
- **`N_valid_window=0`**：该 window 不 admit、不 read、不写 prefix；若它恰为 closing window，则 segment 走上述 abort 分支而非 commit。由于中间/closing 判定只由 pending 行数驱动，零有效行 window 不会意外触发 materialize。
- **验收（CPU/static spy）**：N=1、N=3、默认 16、terminal remainder 四种场景下断言 admit/materialize/backward/commit/optimizer-step 的精确次数与顺序；no stale read（window k 的 read 等于 row 0..k-1 post-update 状态）；no double write（materialize 输出与 online detached candidate 逐位相等）；abort 后 candidate 与 committed 逐位相等；`N_valid_window=0` 无 commit、无 slow-param 梯度。

## 3. 可检验 disabled parity（Kimi MEDIUM-1 整改）

v0.1 的"composed config diff 为空/逐位一致"不可满足，改写为可检验判据。`local_ttt_enabled=False`（默认）时必须同时满足：

1. 参数集合逐位一致：`named_parameters()` 名字有序列表与现状完全相同（不新增任何 registered parameter/buffer/module）；
2. `keys_to_select` 与现状完全相同；
3. forward 行为一致：`PackedSequence.local_memory_prefix is None`、无新分支被执行（以 spy/计数器证明 prefix 路径零调用）；
4. composed config 与现状的差异**仅允许**为新增的 5 个带默认值字段（`local_ttt_enabled=False`、`ttt_tbptt_steps=16`、`ttt_inner_lr=0.1`、`k_local=1`、`runtime_evidence_steps=1`），验收以逐键 diff 证明差异集合恰好等于该五字段且取默认值。

## 4. 继承与范围

v0.1 的 config identity（§2）、唯一 owner 与对象 identity（§3）、optimizer exact membership（§5）、checkpoint（§6）、允许文件集合与禁止范围（§8）不变，逐条继承。本 v0.2 仍不授权实现、真实 checkpoint I/O、GPU/CUDA/torchrun、训练/评测/推理、P4/P5、B2-T、LIBERO4IN1；推理 chronology 兼容性说明：§1 的训练 read-after-(t-1) 因果规则与已冻结的推理规则（inference-mode 前完成 W-only update）不冲突，推理接线细节仍属后续独立 Gate。

冲突时以本 v0.2 为准；其余条款继承 v0.1 及其引用的 production runtime contract design v0.3、config/optimizer/checkpoint design v0.2。
