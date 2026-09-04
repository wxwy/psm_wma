# PSM-WMA R09-B TTT v0.3.2 active Cosmos/trainer wiring design v0.8

**状态**：v0.7 superseded；待三方同 SHA 设计审核。仅冻结 active wiring contract，不授权实现、GPU 或训练。
**基线**：v0.7（root `0d6bfd3`）获 Kimi、MM 双方 `APPROVE_TO_IMPLEMENT` 与 ChatGPT `12d5235` REQUEST_CHANGES（HIGH-1：terminal-during-lag 丢弃行绕过已冻结 terminal-remainder 事务合同；HIGH-2：skip 重试载体违反单 pending authority）。两条 HIGH 的共同根源是 v0.3 引入的**两阶段 commit 所造成的 publication lag**。本 v0.8 采用 ChatGPT 在 v0.3 评审（`ca982ea` HIGH-2 验收）中显式提供的 Option (B)：**重新定义合同，使 Local fast commit 仅依赖成功的 backward，移除对后续 optimizer skip/failure 回滚的承诺**。lag 消失后，v0.4–v0.7 的顺延队列/双不变量/terminal-during-lag/skip 重试载体/单 pending 冲突整类消解。

## 1. 单阶段 commit 与 fast/slow 语义重定义（核心变更）

- **commit 点**：segment 在 live window 关闭（满 `ttt_tbptt_steps` 或 terminal remainder）、witness-bound `backward()` 成功后，于该 micro-batch 的 `on_after_backward` 接缝 commit（fast state 发布、replay/identity 入库）。不再等待 optimizer step。
- **重定义的合同（显式声明）**：fast-state 发布只与"closing backward 成功"原子绑定；后续 optimizer step 被 scaler skip 时 fast state 不回滚、slow 参数不步进——该组合是**既定语义**。数值自洽依据：committed fast state 是"未变化的 slow 参数 + 已发布数据 chronology"的确定性函数，skip 后两侧恰好对应同一 slow 参数版本；不存在需要撤回的重放。
- **backward 路径失败**（loss 非有限、`backward()` 抛错）：发生在 commit 点之前，segment `abort`——candidate 精确回滚到最后 committed state，pending 清空。该回滚语义不变。
- **optimizer exception**：仍为 process-fatal；恢复边界为最近 DCP checkpoint（slow state；fast state 本就不入 checkpoint，重启后按新 episode 语义重建——两侧恰好回卷到同一 checkpoint 边界，无分叉）。
- **SCALER_SKIP**：commit 保持有效；slow 参数 `.grad` 由 `resolve_transaction(SCALER_SKIP)` 回调清零四组（v0.6 §3 继承）；scheduler 不推进（v0.4 体内闸继承）；无重试、无重入队。验收 spy 断言 skip 后/下一 backward 前四组 `.grad` 为 None。
- **随之移除**：两阶段 publish 门、publication lag、顺延队列、`grad_accum_iter ≤ ttt_tbptt_steps` cap 校验、连续 run 校验、per-owner flush——全部为 lag 的派生物，lag 消失后无存在必要（显式声明移除，非静默）。

## 2. 事务时序（回到无 lag 形态）

每个 micro-batch = 1 native window = 1 evidence row，全部 live 处理：

```text
forward：admit(t)（graph-free raw）→ read(t)（read-after-(t-1)，中间行
  走 detached candidate；closing 行走 pre-write witness 图）→ write(t)
  （detached 恰好一次）→ 若 t 使 pending 满 N 或为 terminal remainder：
  本 window forward 内 materialize（create_graph scan）
→ loss.backward()（trainer 每 micro-batch 恰好一次，不变）
→ on_after_backward：若本 window 为 closing 且 backward 成功 → commit；
  terminal 时 commit 后 reset（owner epoch+1）
→ grad-accum 边界：optimizer step / scheduler（skip 闸与 .grad 清零见 §1）
```

- 单 pending authority 无冲突：commit 发生在下一 micro-batch forward 之前，下一 window `begin()` 时 pending 已释放。
- `N_valid_window=0`：不 admit、不 read、不写 prefix；若恰为 closing window 则 segment abort（缺 backward-ok 标记，commit 不发生）。
- 梯度覆盖性质（v0.3 §3 继承并仍为显式冻结）：仅 closing window 的 task loss 经 witness 图向四组 slow 参数提供恰好一次 meta-gradient；中间行无 Local 梯度；terminal remainder 与其余 segment 完全同构（总有 live carrier——自己的 terminal window），不存在无载体事务。

## 3. 继承与验收

继承：v0.3 §1 pre-write witness 语义与 T≥17/terminal 验收；v0.2 §3 disabled parity 四判据；v0.1 §2/§3/§5/§6（config identity、唯一 owner、selector、checkpoint）。v0.3 §3 的梯度 supersede 声明继续有效（closing-only meta-gradient）。

验收（CPU/static，真实接缝驱动）：N=1/3/16 与 terminal remainder 的 admit/materialize/backward/commit/reset 精确次数与顺序；commit 严格先于下一 micro-batch forward（无 lag 断言）；closing 梯度与新鲜参考 scan 逐元素相等；backward 失败 abort 回滚逐位相等；SCALER_SKIP 后 committed state 保持、`.grad` 清零、scheduler 不推进；optimizer exception 按 process-fatal 语义退出且无后续 callback；`N_valid_window=0` 无 commit；authority 无 BACKWARD_OK 之外的 commit 路径（反向断言）；disabled parity 四判据。

## 4. 允许范围与禁止

允许文件集合不变：`configs/base/defaults/model_config.py`、`configs/base/experiment/action/posttrain_config/action_policy_libero_edge_all.py`、`model/generator/omni_mot_model.py`、`model/generator/mot/local_evidence.py`（pre-write witness 路径）、`model/generator/mot/production_runtime_adapter.py`、`trainer/__init__.py`（仅 `_optimizer_step` 体内 skip 闸 + 结果回调）+ 一个新 lifecycle callback 模块与相邻测试。`runtime_authority.py` 零改动（commit 的 BACKWARD_OK 门不变）。仍禁止：实现之外的任何真实 checkpoint I/O、GPU/CUDA/torchrun、训练/评测/推理、P4/P5、B2-T、LIBERO4IN1；推理接线仍属后续独立 Gate。

冲突时以本 v0.8 为准；其余条款继承 v0.7–v0.1 及其引用的 C5A design v0.6、production runtime contract design v0.3、config/optimizer/checkpoint design v0.2。
