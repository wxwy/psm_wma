# PSM-WMA R09-B TTT v0.3.2 active Cosmos/trainer wiring design v0.4

**状态**：v0.3 superseded；待三方同 SHA 设计审核。仅冻结 active wiring contract，不授权实现、GPU 或训练。
**基线**：v0.3（root `73cf4a1`）获 ChatGPT `e632f9a`、Kimi、MM 三方 REQUEST_CHANGES，收敛于 publication-lag 状态机与 optimizer 事务可观测性。v0.3 已获接受部分逐条继承：§1 pre-write witness 语义与 T≥17/terminal 验收、§3 Local 梯度目标 supersede 声明、disabled parity 四判据、config identity、唯一 owner、selector、slow-only checkpoint、范围边界。

## 1. Publication-lag 状态机：raw 顺延缓冲（ChatGPT HIGH-1 / Kimi MEDIUM-1 / MM 整改，采用顺延方向）

冻结：单一 pending transaction 的 authority 语义**不变**（`runtime_authority.py:105,110-113` 不加第二 pending、不加 rebase）。publication lag 由 wiring 层（lifecycle callback）在 authority 之外吸收：

- 每个 owner 维护一个 graph-free **raw 顺延队列**（仅 raw evidence payload + owner-global 连续 `source_timestep`，不建图、不产生 candidate）。
- segment 关闭（BACKWARD_OK、未 publish）后到达的同一 owner window：不调用 `begin()`/`admit()`，raw 行进入顺延队列；这些 window 的 Local read 使用**最后 committed state**（显式 lag 语义，v0.3 已冻结），prefix 照常产生。
- publish（optimizer step 成功）或 abort（事务失败）发生时：按队列顺序 `begin()`（`pending.base_state` = 当时最后 committed state——MM 条款）并逐行 admit 顺延行。owner-global timestep 连续性由队列顺序保持，无丢失、无 admission failure、无 rebase——candidate 从正确基座单次构建，materialize 等价不变量（重放 == online candidate）天然恢复。
- lag 期间已被消费的 read（last committed state）是显式冻结的事务语义，不回溯、不重算。
- 该设计对任意 `ttt_tbptt_steps`/`grad_accum_iter` 对齐关系一致成立，不依赖整除性。
- **验收（CPU/static）**：故意错位组合（如 segment=3 × grad_accum=2/4/5，及默认 16 × 16）fixture 证明：无 admission failure、无丢失 prior-segment write、owner-global timestep 连续、publish 前后 read-after-(t-1) 因果、无数值双写、顺延行 publish 后 admit 的基座与参考逐元素相等。

## 2. Optimizer 事务结果的真实可观测接缝（ChatGPT HIGH-2 整改）

v0.3 假设的"optimizer step 成功 → `on_before_zero_grad` commit"在现有 trainer 不可观测（`trainer/__init__.py:500-527`：`_optimizer_step()` 无返回值、异常时 `on_before_zero_grad` 不执行、GradScaler skip 无回传、scheduler 无条件推进）。v0.4 冻结真实接缝与失败策略：

- **接缝（实现 Gate 允许最小修改 `cosmos_framework/trainer/__init__.py`）**：在 grad-accum 边界对 `_optimizer_step` 包一层结果捕获，产生恰好一次 `resolve_transaction(result)` 回调，`result ∈ {SUCCESS, SCALER_SKIP, EXCEPTION}`。scaler skip 的判定复用 GradScaler 内部 found-inf 状态（实现细节在 implementation Gate 冻结并接受审查）。`local_ttt_enabled=False` 时该接缝零行为变化（disabled parity 判据不变）。
- **成功**：`resolve_transaction(SUCCESS)` → publish 恰好一次（fast state、replay/identity 入库），scheduler 正常推进。
- **SCALER_SKIP**：不 publish；abort 未发布 candidate（回滚到最后 committed state——该 candidate 从未可见，回滚无副作用）；**scheduler 不推进**（本设计明确将"skip 时 scheduler 步进"定义为禁止的 slow 侧进展）；顺延队列保持，下一 grad-accum 窗口重试。
- **EXCEPTION**：定义为 process-fatal。训练进程终止，无 commit；恢复边界显式冻结为从最近 DCP checkpoint 重启（slow state），fast state 本就不进 checkpoint，按新 episode 语义重建。"slow 侧无进展"不以运行时回滚保证，而以进程终止 + checkpoint 恢复边界保证；partial optimizer mutation 随进程消亡。
- **验收（CPU/static trainer spy，驱动真实 trainer 顺序）**：`grad_accum_iter=1` 与 `>1` × 成功/SCALER_SKIP/EXCEPTION：成功 publish 恰好一次；skip 永不 publish 且 scheduler 不推进；抛错后无 candidate 可见且进程按 fatal 语义退出（spy 断言无后续 callback）；`N_valid_window=0` 无 commit、无 slow-param 梯度。helper-only/test-side abort 调用不作为证据——必须经真实接缝触发。

## 3. 继承与范围

v0.3 §1（pre-write witness 语义与验收）、§3（Local 梯度目标 supersede 声明）、v0.2 §3（disabled parity 四判据）、v0.1 §2/§3/§5/§6（config identity、唯一 owner、selector、checkpoint）逐条继承不变。**允许文件集合扩增一项**：`cosmos_framework/trainer/__init__.py`（仅 §2 的 optimizer 事务结果捕获与回调转发，最小 diff）；其余仍为 `model_config.py`、`action_policy_libero_edge_all.py`、`omni_mot_model.py`、`local_evidence.py`、`production_runtime_adapter.py`、`runtime_authority.py` + 一个新 lifecycle callback 模块与相邻测试。本 v0.4 仍不授权实现、真实 checkpoint I/O、GPU/CUDA/torchrun、训练/评测/推理、P4/P5、B2-T、LIBERO4IN1；推理接线仍属后续独立 Gate。

冲突时以本 v0.4 为准；其余条款继承 v0.3/v0.2/v0.1 及其引用的 production runtime contract design v0.3、config/optimizer/checkpoint design v0.2。
