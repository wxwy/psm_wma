# PSM-WMA Local Memory v0.3.5 — active 路线 catalog 多 epoch 复用设计 v0.1

- 状态：**设计，送审**。尚无对应代码改动；当前 operative 行为是 `freeze_window` 在 catalog 耗尽时 fail-closed `raise`。
- 上游证据：`tools/g0/probe_block_capacity.py` → `artifacts/g0/active_static_probe/probe_block_capacity.json`
- 相关 Gate：`G0-R09-B-TTT-V035-ACTIVE-ROUTE-RESUME`（resume 接线，已送审）、`G0-R09-B-TTT-V035-ACTIVE-WINDOW-SLOT-ROTATION`（slot 轮转修复，已送审）
- 建议 Gate：`G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE`

---

## 1. 问题

active 路线的每个训练 member 都从冻结窗口计划取一个 whole block，而 catalog **只建一次、只减不增**。直接实测（`probe_block_capacity.json`）：

| 项 | 读数 |
|---|---|
| `total_blocks` | 14430 |
| 每 window 消耗 | `grad_accum_iter` = 128 |
| **可服务的 optimizer step** | **112.73** |
| 正式计划 `max_iter` | 5000 |
| **缺口** | **44.4 倍** |

第 113 个窗口的 `freeze_window()` 会 `raise RuntimeError("active Local window exhausted every segment stream")`（`active_local_memory_driver.py:230-231`）。

**这与另外两个在审项的关系**：slot 轮转修复把可用量由 7240 提到 14430（翻倍），**必要但不充分**；resume 恢复的是数据进度、**不增加容量**。两者都落地后，5000 步依然跑不完。故本项是"具备正式训练条件"的**独立且更靠前**的阻塞。

**它不是可以靠参数绕开的**：`block_count = valid_start_count // ttt_tbptt_steps`（`canonical_local_memory_producer.py:113-115`），总容量是「数据集 × TBPTT 宽度」的固有属性。把 `ttt_tbptt_steps` 由 16 降到 8 只把上限提到 225 步（且改变 TBPTT 语义），仍远小于 5000；增大 `b_stream` 不改变总 block 数（只改变 slot 间分配，`active_local_memory_launch.py:166`）。

---

## 2. 判定：不是新机制，而是接线

与 resume 设计同性质——**契约、排列函数与 scheduler 接口都已存在并已审核，缺的是 active 生产路线对它们的调用**。

| 已存在的部件 | 位置 | 现状 |
|---|---|---|
| epoch 快照契约 | `canonical_segment_adapter_scheduler.py:57-67` `QueueEpochSnapshot(queue_seed, epoch, catalog_digest, positions, permutations)` | 已冻结 |
| epoch 排列函数 | 同文件 `:76-110` `queue_digest_preimage` / `queue_permutation`（按 `(seed, epoch, category)` 做 SHA256 确定性排列） | 已冻结，字节序有版本标记 `PSM-WMA/queue/v1` |
| epoch 边界规则 | 同文件 `:542-569` `rollover_projected_if_safe` | 已冻结 |
| scheduler 接口 | `local_memory_segment.py:331-337` `configure_queue(seed, epoch, permutation, provenance)` | **已实现，但全仓零生产调用点**（仅 `local_memory_segment_test.py:113`） |
| 持久化槽位 | `local_memory_segment.py:362-365`（`rebuild`）与 `:378-381`（`snapshot`）已含 `queue_seed`/`queue_epoch`/`queue_permutation`/`segment_provenance` | 已就位 |

**单位对齐（已核实）**：契约的 `_queue_for(category)` 取 `cursor == 0 and consumer_step_start == 0` 的行，即**以 episode 为单位**（`:471-477`）。active 路线 `canonical_segment_streams` 为每个 episode 建一个 `CanonicalSegmentStream`（`active_local_memory_launch.py:169-182`），而 `_by_slot[slot]` 是该 suite 的 episode 列表。**两者逐一对应**，故 epoch 重排即「按新 epoch 的 permutation 重排 `_by_slot[slot]`」。

> 注：模块 docstring 声明该文件是 CPU/static 契约模型（"deliberately models metadata only... not a trainer integration point"）。正因如此，它定义的是**语义**，把语义落到 active 生产路线正是本设计的内容。

---

## 3. epoch 边界的精确定义（直接采用契约，不重新发明）

**触发条件**（`canonical_segment_adapter_scheduler.py:546-549`），两条**同时**成立：

1. **每个 category 的游标都已到达其 catalog 末尾** —— 等价于「该 suite 的所有 episode 都已遍历完」；
2. **所有 stable slot 都处于 terminal 状态** —— 即没有任何 slot 停在某个 episode 的中途，不存在跨 epoch 的半截 episode。

条件 2 保证 epoch 边界落在「episode 边界」上，这正是 `_is_admissible` 得以放行的前提（见 §4.3）。

**触发动作**（`:550-565`）：`epoch → epoch + 1`；对每个 category 以新 epoch 生成 `queue_permutation(queue_seed, epoch + 1, category, catalog_size)`；`positions` 重置为空。

**为什么用 SHA256 排列而不是简单顺序绕回**：顺序绕回会让每个 epoch 的窗口组成完全相同，形成周期性偏置；契约给定的排列使不同 epoch 的 episode 顺序不同。本设计**沿用契约的排列函数及其字节序**，不新造。

---

## 4. 实现方案（最小改动）

### 4.1 driver 侧（`active_local_memory_driver.py`）

新增一个 catalog epoch 计数与一个边界推进方法，并在**窗口边界**调用它。

**触发点必须是窗口边界，不能是 `freeze_window` 的 raise 点**。理由：`freeze_window` 在循环体内逐 member 调用 `_commit_block`（`:234`），**中途 `raise` 时 `self._stream_index` / `_active_stream` / `_active_cursor` 已被部分推进**，即该函数不是原子的；在 raise 点重置会留下一个半推进的窗口状态。窗口边界（`_arm_initial`，即 `owner.phase is IDLE`）是唯一干净的回滚点。

`_arm_initial`（`:157-166`）在调用 `freeze_window()` **之前**插入边界检查：

- 计算「本窗口能否走满 `window_members`」。**该探测必须是纯的**：`_peek_block` 的 docstring 明确 "commits no driver state"（`:258-263`），可直接复用它按与 `freeze_window` 相同的选择规则做一次不落地的模拟，或等价地以「各 slot 剩余 whole-block 数之和」判定。
- 若不能走满，则执行 §4.3 的重置并推进 epoch，再调用 `freeze_window()`。

实现时应把「选择规则」抽为一个被 `freeze_window` 与探测器共用的内部函数，避免两处规则漂移（这是本设计唯一有实质风险的地方，见 §6 判据 3）。

### 4.2 scheduler 侧（`local_memory_segment.py`）

`configure_queue` 当前只把四个字段存下来（`:334-337`），**不改变 `_by_slot` 顺序**（它根本看不到 `_by_slot`）。本设计需要让新 epoch 的 permutation 真正生效：由 **driver** 持有 `_by_slot` 的重排动作（`_by_slot` 是 driver 的状态），scheduler 侧维持 `queue_*` 的记录与快照语义不变。

**不改 `RankLocalSegmentScheduler` 的公开接口**：`configure_queue` 的签名与语义保持为「记录本 epoch 的队列身份」，重排由 driver 执行。

### 4.3 重置动作的精确清单

在 epoch 边界（条件 §3 已保证所有 stable slot 均为 terminal）：

**driver 侧**
- `_stream_index = {slot: 0 for slot in self._by_slot}`
- `_active_stream.clear()`、`_active_cursor.clear()`（清空后 `_peek_block` 的 `rebind = stream is not None` 为 False，新 episode 的 `cursor == 0` 即为合法首块）
- `_by_slot` 按新 epoch 的 `queue_permutation(..., category, len(...))` 重排（每个 category 独立）
- `_window_index` **不重置**（全局窗口计数，`plan_chain_id` 的单调性依赖它）
- 新增 `_catalog_epoch`，随 epoch 递增

**scheduler 侧**
- `stable_slots.clear()`、`terminal_slots.clear()`
- `admission_order.clear()`、`committed_identities.clear()`
- 经 `configure_queue` 记入新的 `queue_seed`（不变）/`queue_epoch`（+1）/`queue_permutation`/`segment_provenance`
- **`cumulative_valid_consumer_exposure` 不清零**。理由：`freeze_window` 用的是**比例** `exposure[category] / sum(exposure.values())`（`:226`），累计不清零时该比例依然稳定收敛于 `target_distribution`，配额语义不变；清零反而破坏「累计有效消费者曝光」这一字段本身的语义。

**为什么清空 `committed_identities` 是安全的**：`_is_admissible` 的守卫在 `stable_slots` 无该 slot 记录时只要求 `identity.cursor == 0`（`:309-311`）；`terminal_rebind` 会删除 `stable_slots` 条目（`:343`）。故新 epoch 首块（cursor 0）天然可准入。而 `commit` 的重复检查 `identity in self.committed_identities`（`:323`）在清空后不再拒绝跨 epoch 复用的同一 identity。`canonical_segment_runtime.py:181-182` 的一致性校验（commit 的 identity 必须在 `admission_order` 中）因两个容器**同时**清空而保持成立。

**`SegmentIdentity` 的结构与其字段值均不变**——同一 episode 同一 cursor 在不同 epoch 会产生**相等的 identity 值**，这是刻意的：identity 描述的是「数据段的身份」，跨 epoch 复用同一段本就该是同一个身份；守卫状态由 epoch 边界重置来管理，而不是靠给 identity 加 epoch 维度。**因此本设计不触及 `SegmentIdentity` 的 ABI。**

### 4.4 与 `on_train_start` 的关系

不改 `active_local_memory_launch.py:223-289` 的构建路径。catalog 仍只建一次，多 epoch 复用发生在**同一份 catalog 上**（重排 + 游标归零），不重新读取数据集、不重建 producer。

---

## 5. 与 resume 设计的耦合与建议顺序

**耦合点**：本设计引入的 `_catalog_epoch`（driver 侧）与 `queue_epoch`/`queue_permutation`（scheduler 侧）**都必须在 checkpoint 中持久化**，否则 resume 后 epoch 语义错（例如把 epoch 3 的状态当成 epoch 0）。所幸 scheduler 侧的三个字段**已在 `snapshot()`/`rebuild()` 中就位**（`local_memory_segment.py:362-365`、`:378-381`），driver 侧的 `_catalog_epoch` 需与 `_window_index` 一并加入 resume 设计的 driver 快照。

**建议顺序：先落地 resume 接线，再落地本设计。** 理由：

- resume 设计（在审）已经要把 driver 的 `_stream_index`/`_active_stream`/`_active_cursor`/`_window_index` 与 scheduler 的守卫容器全部持久化。本设计**只在其上增加 `_catalog_epoch` 一个字段**与 epoch 边界动作。
- 若颠倒顺序，resume 需要一次性把 epoch 语义并入快照，改动面更大、一次送审的技术面更宽。
- 本设计不阻塞于 resume 的 verdict（设计与证据可先行），但**实现应当在 resume 落地之后**。

**本设计不改变 resume 设计 §6 的任何判据**：其中判据 4 的 GPU 短跑至生产 `save_iter = 50 < 112`，落在单 epoch 内，与本设计正交。

---

## 6. 验收判据

**PASS**（全部满足）：

1. **契约一致性（CPU）**：在 epoch 边界推进后，driver 的 `_by_slot` 重排结果与独立调用 `queue_permutation(queue_seed, epoch, category, catalog_size)` 得到的排列**逐位一致**；`queue_epoch` 恰好 +1。
2. **容量解除（CPU，纯规划层）**：用 `probe_block_capacity.py` 的 producer 搭建同一套 catalog，在**不取任何张量**的前提下连续推演窗口规划越过 epoch 边界，断言：①可连续规划出 **> 112.73** 个窗口而不再 `raise`；②第 113 个窗口成功规划；③跨 epoch 无 identity 被 `commit` 的守卫拒绝。
3. **原子性**：断言窗口边界的探测**不修改** driver 状态（探测前后 `_stream_index`/`_active_stream`/`_active_cursor` 逐位相同），且探测所用的选择规则与实际 `freeze_window` 的选择规则共用同一实现（防止两处规则漂移）。
4. **边界条件的两条**分别有独立用例：①某 category 未到末尾时**不**推进 epoch；②存在非 terminal 的 stable slot 时**不**推进 epoch。
5. **GPU 端到端**：短跑越过一个 epoch 边界，断言无 `raise`、loss 有限、`per_slot_members` 在每个窗口内仍为 8 个 slot 均衡、`cumulative_valid_consumer_exposure` 单调不减（不清零）。
6. **resume 交叉（在 resume 落地后）**：在 epoch ≥ 1 处存盘并 resume，断言 `_catalog_epoch` 与 `queue_epoch` 一致恢复、续跑窗口序列与不中断跑一致。

**FAIL**：epoch 边界推进后出现 identity 守卫拒绝；或探测修改了 driver 状态；或重排结果与 `queue_permutation` 不一致；或 `cumulative_valid_consumer_exposure` 被清零。

**BLOCKED**：若 §3 条件 2（所有 stable slot 均为 terminal）在真实链路上**无法同时成立**（例如某 slot 因数据形状永远停在非 terminal 的 episode 中途），则 epoch 边界不可达，本设计不落地，须改为「按 slot 独立推进 epoch」的更强语义——那将触及 `GAWindowPlan` 的跨 member 一致性，属于另一项设计。

---

## 7. 禁止范围

- 不改 `SegmentIdentity` / `GAWindowPlan` / `SegmentBatch` 的 ABI 与字段。
- 不改 `admit` / `commit` / `terminal_rebind` 的守卫条件本身（本设计只重置它们所依赖的**状态容器**，不改判定逻辑）。
- 不改 `queue_digest_preimage` / `queue_permutation` 的字节序（契约已冻结，有 `PSM-WMA/queue/v1` 版本标记）。
- 不新增 DCP 顶层 key（`dcp.py:939` 会拒绝）。
- 不重建 catalog、不重新读取数据集、不改 `on_train_start` 的构建路径。
- 不为 identity 增加 epoch 维度。
- 不在 `freeze_window` 的 `raise` 点做重置（非原子，见 §4.1）。

---

## 8. 请求 verdict

请就以下三点裁定：

1. **§3 采用契约既有的 epoch 边界条件（所有 category 到末尾 + 所有 stable slot 均 terminal）是否正确**，尤其是条件 2 在 b_stream=8 / 4 categories 的生产形态下是否恒可满足（这直接决定 §6 的 BLOCKED 判据）。
2. **§4.3 的重置清单是否完备**——是否还有第四处状态（driver 或 scheduler 或 owner 侧）会跨窗口残留、从而在第二个 epoch 造成静默错误。特别请审 `_rebind_terminal`（driver `:190-195`）在 epoch 边界的时序、以及 `owner` 的 `phase`/`transaction` 是否有未列出的残留状态。
3. **§5 的顺序判断是否成立**：本设计的实现应当排在 resume 落地之后，且 resume 设计 §6 的判据无需因本设计修改。

---

## 9. 实现记录

**当前 operative 行为**：catalog 耗尽时 `freeze_window` fail-closed `raise`（`active_local_memory_driver.py:230-231`）。**D8b 长跑（5000 步）不得在此状态下启动**——会在第 113 步 crash，白耗约 8 小时。

本文档为**设计**，尚无对应代码改动；实现与证据将在 Gate 裁定后补入本节。
