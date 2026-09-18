# PSM-WMA Local Memory v0.3.5 — active 路线 scheduler-semantics refreeze 设计 v0.1

- 状态：**设计（独立 Gate，D8b 长跑前置）**。本文件只做 docs-only 决策冻结；无代码改动。
- 上游依据：catalog epoch-reuse 设计 v0.8 §8 第 7/8 点、§9、§10.4；`G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE`。
- 建议 Gate：`G0-R09-B-TTT-V035-ACTIVE-SCHEDULER-SEMANTICS-REFREEZE`。

---

## 1. 问题（实测，非推断）

`freeze_window` 的选择键是 `(target[category] - observed, category, -used)`，其中
`observed` 取自 `RankLocalSegmentScheduler.cumulative_valid_consumer_exposure`（长期累计，
**epoch 边界不清零**）。epoch 0 时四类赤字从零同步增长，窗口内四类并存（81/112 窗覆盖全部
4 suite）；catalog 首次耗尽（~第 112 窗）后，**`observed` 继续保留**，epochs ≥1 开局即继承
epoch 0 末尾的偏斜（实测 `libero_10` 占 39.2%，另三类赤字为正），于是赤字为正的类别被连续
服务直到抽干、`libero_10` 被推迟 ⟹ **每个窗口塌缩到单一 category**。

实测（`probe_epoch_reuse_planning.json`，5040 窗）：

| 项 | epoch 0 | epochs 1–44 |
|---|---|---|
| `windows_by_distinct_categories` | `{1:16, 2:13, 3:2, 4:81}` | `{1:3826, 2:1070, 3:63, 4:81}` |
| 单 suite 窗占比（下界） | 14.3% | **77.3%** |
| 覆盖全部 4 suite 的窗 | 81 | 0（全在 epoch 0） |

即：复用把训练步推进到一个**今天从未运行过的 regime**（约 77% 的 batch 只含一个 suite），
而不是「重复 epoch 0」。本 Gate 解决这一项；catalog 复用机制本身已由 epoch-reuse Gate 关闭。

## 2. 目标

冻结一个明确的选择语义，使 **epochs ≥1 的窗口构成与 epoch 0 一致**（四类按 `target_distribution`
均衡服务），同时不改任何已冻结 ABI。

## 3. 候选与裁定

### 3.1 (a) per-epoch exposure（复位）

在每个 **per-slot rollover 边界**将 `cumulative_valid_consumer_exposure` 复位为 0（或等价的
per-epoch 计数），使 `freeze_window` 的 `observed` 在每个 epoch 内独立计量。

- **优点**：epochs ≥1 与 epoch 0 同构，消除 77% 单 suite 塌缩。
- **代价/风险**：`cumulative_valid_consumer_exposure` 目前同时是 **`admit` 的赤字来源**与
  **快照字段**。复位会改变 resume 语义（须把复位后的值写入快照，`rebuild` 后一致）。
- **实现落点（最小）**：`active_local_memory_driver._maybe_rollover` 在**所有 slot 完成复用的
  那个边界**上将 `scheduler.cumulative_valid_consumer_exposure` 全部置 0。不改
  `RankLocalSegmentScheduler` 公开接口、不改 `freeze_window` 的选择键结构（只改 `observed`
  的来源值）、不改 `SegmentIdentity`/`GAWindowPlan`/`SegmentBatch` ABI。
- **与 v0.8 §4.3 的关系**：本 Gate 显式取代 v0.8「`cumulative_valid_consumer_exposure` 不清零」
  的**运行期行为**（v0.8 当时把 per-epoch 撤回、明确移交「独立 scheduler-semantics refreeze
  Gate」，即本 Gate）。

### 3.2 (b) 接受累计（不复位）

保持 v0.8 现状，把 77% 单 suite 如实作为**已知 regime**写进正式训练 runbook，并在 D8b 报告中
显式标注数据混合。

## 4. 请求 verdict

请裁定 **(a) 实现 per-epoch 复位** 或 **(b) 接受累计 regime**：

- 若选 (a)：授权 `active_local_memory_driver._maybe_rollover` 的最小改动 + 相邻 CPU 测试
  （复位时机、epochs≥1 窗口四类构成与 epoch 0 一致、resume 快照一致），并更新
  `probe_epoch_reuse_planning.py` 增加 per-epoch 构成断言。
- 若选 (b)：本 Gate 以 docs-only 关闭，D8b runbook 必须写明「epochs ≥1 ≈77% 单 suite」的已知
  代价与观测口径。

## 5. 冻结边界（两选一共同）

- 不改 `QueueEpochSnapshot` 字节序、`queue_permutation`/`queue_digest_preimage`、`SegmentIdentity`
  /`GAWindowPlan`/`SegmentBatch` ABI。
- 不改 `freeze_window` 的选择键**结构** `(deficit, category, -used)`；若选 (a) 只改 `observed`
  的取值来源（累计 → per-epoch）。
- resume：`_slot_epoch` 与 `cumulative_valid_consumer_exposure` 均须随快照持久化/恢复一致。

## 6. 验收（若选 (a)，草案）

1. epochs ≥1 的 `windows_by_distinct_categories` 与 epoch 0 同构（4 类窗占比一致，单 suite 窗
   占比回到 ~14%）；
2. 复位后 `cumulative_valid_consumer_exposure` 单调（epoch 内），跨边界复位记录可核；
3. resume 后复位值与存盘一致；
4. 相邻 CPU 测试全绿，`SegmentIdentity`/`GAWindowPlan`/`SegmentBatch` ABI 不变。

---

## 7. 与「训练条件」的关系

- 本 Gate 不改变「catalog 复用是否可行」（已由 epoch-reuse Gate 关闭），只决定**复用后每个窗口的
  数据混合是否与 epoch 0 同构**。
- D8b 长跑（`max_iter=5000`）在本 Gate 关闭前不得启动（v0.8 §9）。

---

## 8. 状态裁决（2026-09-18，用户）

**本设计 withdrawn（不落地）。** 理由：

1. **HIGH-1（前提过时，已核实）**：本设计 §1 引用的旧读数（epochs≥1 单 suite ≈77.3%，仅 epoch 0 有四类窗）已不成立。当前 committed
   `artifacts/g0/active_static_probe/probe_epoch_reuse_planning.json` 实测
   `windows_by_distinct_categories={1:2703, 2:1893, 3:367, 4:149}`、单 suite=**52.88%**、
   `cumulative_exposure` 四类各 ≈25%（25.29/24.92/24.96/24.83）——**总用量已均衡**。
2. **用户裁决**：active 路线是**测试路线**（非正式训练），且总用量已均衡；不清零即可，
   接受当前「约一半窗口单 suite、总体各 25%」的 regime。
3. **随之 HIGH-2 消解**：不清零 ⇒ 无需定义异步 per-slot 下的 reset authority。

**保留**：HIGH-3（acceptance command 硬化）与本设计无关，另行处理。
**取代范围**：v0.8 §8 第 7/8 点、§9 中「D8b 长跑须先经独立 scheduler-refreeze Gate」的前置**被本次裁决解除**（接受当前 regime）。
