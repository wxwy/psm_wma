# PSM-WMA R09-B TTT v0.3.2 active Cosmos/trainer wiring design v0.6

**状态**：v0.5 superseded；待三方同 SHA 设计审核。仅冻结 active wiring contract，不授权实现、GPU 或训练。
**基线**：v0.5（root `1db84a6`）获 ChatGPT `22872c5`、Kimi、MM 三方 REQUEST_CHANGES，收敛于：q≥N 时 FIFO/单 pending/closing-live 三者矛盾、terminal-during-lag 的 loss 载体、skip 重试的梯度载体与 `.grad` 残留。v0.5 已获接受部分逐条继承：惰性成形方向、行保留队首、scheduler 体内闸、三态接缝、pre-write witness、梯度 supersede 声明、disabled parity、config/owner/selector/checkpoint 边界。

## 1. Lag 不变量与 per-owner flush（ChatGPT HIGH-1 屏障选项 / Kimi flush 作用域 / MM MEDIUM-1）

- **容量不变量（fail-closed config 校验）**：仅当 `grad_accum_iter ≤ ttt_tbptt_steps` 时允许启用本 wiring，否则 config composition 直接拒绝。默认 16≤16 成立；`accum > N`（如 N=3×accum=7）必须在验收中被拒绝。
- **连续 run 不变量（fail-closed runtime 校验）**：dataloader stream 须将同一 owner（episode）的 window 作为连续 run 呈现（B2 P1 stream manifest 已保证）；wiring 检测到同一 owner 非连续出现时 fail-closed。
- 两条不变量联合保证：普通顺延积压 `q ≤ grad_accum_iter - 1 ≤ N - 1`，**队列行永远不会在队列中凑满一个 segment**——v0.5 的 q≥N 三方矛盾对普通路径结构性不可达。
- **flush 作用域 per-owner**：owner 的顺延队列只在该 owner 的下一个 live window 的 forward 接缝 flush（按 FIFO begin/admit，base=当时最后 committed state），随后处理本 window 自身的行。因 q ≤ N-1，含队列行的 segment 最早由本 live 行或更后的 live 行填满——**closing 总是 live window**；若恰由本 flush window 填满（q=N-1），本 window 的 read 取自该 witness 图（Kimi (i) 的精确规则）。其他 owner 的 window 不触发本 owner 的 flush。

## 2. Fast-state-only commit 路径（terminal-during-lag 与 skip 重试的统一语义；ChatGPT HIGH-1(ii)/HIGH-2(C)、Kimi (ii-a)）

显式冻结梯度目标修正：**两类 segment 以 fast-state-only commit 发布、不获得 slow meta-gradient，这是既定语义而非缺陷**——(a) terminal-during-lag 的旧 epoch remainder segment；(b) 原 closing 被 scaler skip 的 segment。其余 segment（live 关闭）保持恰好一次 witness meta-gradient 不变。

- 机制：authority 增加显式无 witness 的 commit 路径（detached 重放行推进 candidate、`gradient=None` 记录、phase 合法性校验），发布仍只在 `resolve_transaction(SUCCESS)` 边界发生；不需要 live window 的 loss 载体。
- terminal-during-lag：含 `terminal_hint` 的行在队列中不关闭；resolve(SUCCESS) 时该 remainder 以 fast-only commit 发布，随后立即 reset（owner epoch+1）；新 episode 的行在 reset 后才以新 epoch begin，FIFO 保证不交错。无跨 episode loss 载体，episode 独立性保持。
- skip 重试：失败行放回队列前端（FIFO、timestep 连续）；下一个 SUCCESS 边界以 fast-only commit 发布（slow 参数在 skip 时未变，重放数值确定）；不重放旧 witness 图、不需要原 closing 的 native loss。

## 3. SCALER_SKIP 的 slow 侧清理（MM MEDIUM-2）

`resolve_transaction(SCALER_SKIP)` 回调内显式清零四组 Local slow 参数的 `.grad`（置 None），杜绝中止 witness backward 的残留 meta-grad 与后续 backward 累加。该清零先于 trainer 的 `zero_grad` 接缝、与其幂等兼容。验收 spy 断言：`grad_scaler.step` 之后、下一 backward 之前，四组 slow 参数的 `.grad` 为 None。

## 4. 验收矩阵（CPU/static，真实接缝驱动）

- cap 校验：`N=3 × accum=2/3` 通过、`N=3 × accum=7` 与任何 `accum>N` fail-closed；`16×16` 边界通过。
- 连续 run 校验：非连续同 owner window 注入 → fail-closed。
- 精确 trace：`N=3, accum=2/3` 下 FIFO timestep、segment 边界、每个 witness 图的 task loss 来源、单 pending 合法性、每 segment 恰好一次 meta-gradient、无跨 episode loss、无 double write、reset 顺序。
- terminal-during-lag：fast-only commit、无 meta-gradient、publish 后 reset、epoch 归属。
- skip 重试：行不丢失、FIFO 不插队、fast-only commit 在下一 SUCCESS、`.grad` 清零 spy、无 fast publish 无对应 SUCCESS 边界。

## 5. 继承与范围

v0.3 §1（pre-write witness 与 T≥17/terminal 验收）、v0.2 §3（disabled parity 四判据）、v0.1 §2/§3/§5/§6 逐条继承；v0.3 §3 的梯度 supersede 声明由本 v0.6 §2 的精确修正版替代。允许文件集合不变（含 `runtime_authority.py` 的 fast-only commit 路径与 `trainer/__init__.py` 的体内闸）。本 v0.6 仍不授权实现、真实 checkpoint I/O、GPU/CUDA/torchrun、训练/评测/推理、P4/P5、B2-T、LIBERO4IN1；推理接线仍属后续独立 Gate。

冲突时以本 v0.6 为准；其余条款继承 v0.5/v0.4/v0.3/v0.2/v0.1 及其引用的 production runtime contract design v0.3、config/optimizer/checkpoint design v0.2。
