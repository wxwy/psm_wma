# PSM-WMA R09-B TTT v0.3.2 active Cosmos/trainer wiring design v0.3

**状态**：v0.2 superseded；待三方同 SHA 设计审核。仅冻结 active wiring contract，不授权实现、GPU 或训练。
**基线**：v0.2（root `6b1af60`）获 ChatGPT `ca982ea`、Kimi、MM 三方 REQUEST_CHANGES，意见收敛于两点：closing witness 的 pre-write 因果语义、commit 与 optimizer-step 成功的事务顺序。本 v0.3 冻结这两点并显式处理梯度目标继承；v0.2 其余已获接受部分（detached candidate / graph rematerialization 概念、可检验 disabled parity、config identity、唯一 owner、selector、slow-only checkpoint、范围边界）逐条继承。

## 1. Pre-write witness 语义（ChatGPT HIGH-1 整改）

v0.2 已冻结 read-after-(t-1)：window t 恰好可见 row 0..t-1 的 post-update 结果、永不可见自身行。v0.3 进一步冻结 witness 图必须提供**同一因果语义的可微 read**：

- 冻结新的 witness API 语义：segment scan 对每一行发射 **pre-write token**——row t 的 token 从该行 write 之前的状态 `S_{t-1}` 读取（可微）；segment 的最终 candidate `S_t`（全部 write 之后）单独计算。二者在一次 materialize 中同时产出，但 token 绝不取自 post-write 状态。
- closing window 的 Memory Prefix 必须等于标量参考 `read(S_{t-1})`（与中间 window 的 detached candidate read 同一数值、仅多携带图）；committed candidate 必须等于恰好一次 write 序列得到的 `S_t`。
- 现有 `step_projected_many()` 的 post-write token（`local_evidence.py:485-496`）不满足该语义；实现 Gate 在已授权文件集合内新增 pre-write witness 路径，不改既有 post-write CPU contract 的历史语义。
- 验收（CPU/static）：`T≥17`（跨 segment 边界）+ terminal remainder fixture，逐项证明：segment 边界因果、无 self-evidence leakage（window t 的 prefix 对自身 row 的梯度/数值依赖为零）、无 stale read、无数值 double write、witness token 与 pre-write 标量参考逐元素相等、committed candidate 与单次 write 参考逐元素相等。

## 2. 两阶段 commit：publication 以 optimizer-step 成功为门槛（三方同源 HIGH/MEDIUM 整改，采用 Option A/(a)）

替代 v0.2 §2 的 `on_after_backward` 立即 commit。冻结事务状态机与精确顺序：

```text
closing window 的 micro-batch：
  forward（materialize，pre-write witness 建图）→ loss.backward() 成功
  → on_after_backward：仅标记 segment 为 BACKWARD_OK（pending/unpublished）
grad-accum 窗口满：
  → optimizer step 成功 → on_before_zero_grad 接缝 commit（发布 fast state、
    replay/identity 入库）
  → optimizer step 被 grad-scaler 跳过或抛错 → abort：candidate 精确回滚到
    最后 committed state，pending 清空，fast/slow 两侧同时无进展
```

- **可见性规则**：只有 committed state 对后续 window 可见。closing backward 成功到 optimizer step 成功之间的 micro-batch（`grad_accum_iter>1` 时存在）属于下一 segment，其 read 使用**最后 committed state**；该 publication lag 是显式冻结的事务语义，不算 stale-read 缺陷。segment 打开期间（未满 16 行）的中间 window 仍按 v0.2 §1 读 transaction-local detached candidate；该 candidate 在 closing 事务未 publish 前不得被下一 segment 的 window 消费。
- **失败语义收窄且自洽**：backward 路径失败（loss 非有限、`backward()` 抛错）发生在 backward-ok 标记之前，segment 直接 abort；optimizer step 失败/跳过发生在 publish 之前，abort 回滚的是**尚未发布**的 candidate——不再存在"commit 后无法回滚"的矛盾。fast-state 发布与 slow 参数步进以 optimizer-step 成功为同一原子门槛，二者不得静默分叉。
- **验收（CPU/static trainer spy）**：`grad_accum_iter=1` 与 `>1`、optimizer step 成功、grad-scaler skip、optimizer step 抛错四类场景，断言 admit/materialize/backward/backward-ok 标记/optimizer-step/commit/abort 的精确次数与顺序；失败事务对后续 window 不可见（后续 read 等于最后 committed state）；`N_valid_window=0` 无 commit、无 slow-param 梯度（backward 路径不变，由 backward-ok 标记缺失阻断 commit）。

## 3. 梯度目标的显式继承声明（ChatGPT additional concern 整改）

显式声明：**本 wiring 在 Local 慢参数维度上 supersede** production runtime contract design v0.3（`..._v0.3_2026-09-04.md:10-27`）的"segmented 与 unsliced 参数梯度 parity"目标。新冻结目标：Local 四组 slow 参数每个 segment 恰好经 closing window 的 witness graph 获得一次 meta-gradient，参考实现为同一 raw rows 的全 segment `create_graph` scan；验收用直接梯度参考比对（closing backward 的 slow-param 梯度 vs 参考 scan 的梯度逐元素相等）。该 supersede **不影响** v0.3 的 native 侧冻结：`L_segment` 标量分解与 `N_valid_window` 归一化、native 参数梯度路径完全不变——native task loss 的数值构成不依赖 Local read 是否建图。

## 4. 继承与范围

v0.2 §3 的可检验 disabled parity 四判据、v0.1 §2/§3/§5/§6/§8（config identity、唯一 owner 与对象 identity、optimizer exact membership、checkpoint、允许文件集合与禁止范围）不变，逐条继承；允许文件集合继续覆盖实现 §1 pre-write witness 路径所需的 `local_evidence.py`/`runtime_authority.py`/`production_runtime_adapter.py` 改动。本 v0.3 仍不授权实现、真实 checkpoint I/O、GPU/CUDA/torchrun、训练/评测/推理、P4/P5、B2-T、LIBERO4IN1；推理 chronology 兼容性：read-after-(t-1) 与两阶段 commit 均属训练侧语义，与已冻结的推理规则（inference-mode 前 W-only update）不冲突，推理接线仍属后续独立 Gate。

冲突时以本 v0.3 为准；其余条款继承 v0.2/v0.1 及其引用的 production runtime contract design v0.3、config/optimizer/checkpoint design v0.2。
