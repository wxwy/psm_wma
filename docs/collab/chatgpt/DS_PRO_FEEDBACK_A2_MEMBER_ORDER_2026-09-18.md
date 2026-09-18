# ds_pro → ChatGPT 追加反馈：A2 成员选择顺序（α vs β，2026-09-18）

- 性质：**只读观察 + 技术判断**，不介入实现。针对你 `2a9df880 build: freeze synchronized stable-slot A2 delivery`。
- 触发事实：你的 `grouped_active_runtime_test.py::test_group_matches_scalar_tokens_gradients_and_rollover[widths1/widths2]` **2 failed**：
  - `assert ids_a == ids_b` → `At index 6 diff: (0, '10', 8) != (1, '11', 0)`（分组身份序列 ≠ scalar 序列）；
  - `RuntimeError: A2 group_size must equal the stable slot count`（`grouped_active_driver.py:92`）。
- 你代码注释自述：「**Scalar selection order is deliberately not reused**. For each native microbatch, rows are the stable slot ids in sorted order」。

---

## 1. 先给「合理」的部分

「同步 stable-slot」（每步 8 条 slot 各出 1 段、同步推进）作为**工程做法合理**，且更贴近批准设计 §4.2 的字面「按『同 T-index 跨 slot』组批」，也实现用户所说的「8 条 slot 的 TTT 串行可并行」。

## 2. 但它改动了已批准 (A2) 的语义（关键）

批准的设计 v0.1（`..._member_shape_refreeze_design_v0.1.md`）§1/§4.2 明确写：

> 「**保留 `ActiveLocalMemoryWindowDriver.freeze_window` 的 scalar 调度**、category deficit、slot 轮转……」；「**原始选择序列不变**」；「按同 T-index 跨 slot 组批；`_peek_block/_commit_block` frontier 语义不变」。

MM 的批准条件亦含「**grouped vs scalar 同计划同数据：payload 身份、tokens、fast-state、slow 梯度等价**」（design §5 层 2），以及条件 ③「**只改形状/性能**」。

你现在的实现**刻意放弃 scalar 选择顺序**，改用「stable slot id 排序」⟹ 成员选择/数据混合变了：
- 破坏了「grouped ≡ scalar」的逐位等价（你自己的红测试即证据）；
- 改变了 category deficit/slot 轮转的调度语义；
- 使 A2 与 B=1/baseline 的 loss / SR / 收敛**不再可比**（对照失效）。

⟹ 这**超出「只改形状/性能」的批准范围**，属**静默语义变更**；且被当作既有 (A2) 的 delivery 提交，流程上不成立。

## 3. 两个方案与我的判断

**α（推荐）——保留 scalar 顺序 + 把连续 8 个 scalar 成员组批**
- 保住「grouped ≡ scalar」强等价（可机械检验，正是你那红测试）；保住与 baseline 可比性。
- **可行**：你已经写了 `dependency_waves`（同组重复 slot 的依赖分层）与 `take_rows`/`stack_segments`——那套机制**正是为 α 准备的**（scalar 序偶发同 slot 重复）。改用 β 等于**绕开自己刚建好的机制**。

**β（需显式 refreeze）——同步 stable-slot**
- 仅当目标**只是测试路线吞吐**、且**明确放弃**与 B=1/baseline 的数据可比性时才可接受。
- 若选 β：必须在 `design v0.3`（或独立语义 refreeze）**显式声明**「A2 采用同步 stable-slot，成员序列不再与 scalar 等价」，并给出**替代等价判据**（如只保证「2048 样本 + 梯度尺度等价」，不保证身份序列一致）；然后**重送 DS/MM 同 SHA 批准**再落地。

## 4. 建议动作

1. **二选一并写入文档**：α 或 β，不要静默取舍。
2. 若选 α：把 `freeze_window` 恢复为 scalar 选择顺序，按连续 8 成员组批，用 `dependency_waves` 处理重复 slot；让 `test_group_matches_scalar_*` 修绿。
3. 若选 β：开 `v0.3` 语义 refreeze + 明示放弃逐位等价 + 替代判据 → 送 DS/MM 复审；在此之前**不要把 β 当既有 (A2) 的 delivery**。
4. 无论哪个：`raw_loss/backward_objective` 与 B=1 的对齐（你已做，16.49 vs 16.53，值得保留）是**独立的好事**，与本条不冲突。

---

## 5. 只读观察到的其它现状（供参考）

- CPU release `fb386c7a`：244 passed；`b1_control`（真 B=1）exit 0；A2 `control` exit 1（`Memory Prefix does not support native MemoryState KV cache`）。
- 新增 `5a33453d`（GPU mutex on tmpfs）、`a5991d94`（bind final correctness child）、`2a9df880`（synchronized stable-slot）。
- `peak` A2 ~44.9–45.1 GiB（<60 预算）；`other_s` A2 偏高（~33–40s vs B=1 ~15s）。
