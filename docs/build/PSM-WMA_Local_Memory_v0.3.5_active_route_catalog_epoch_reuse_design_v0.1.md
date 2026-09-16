# PSM-WMA Local Memory v0.3.5 — active 路线 catalog 多 epoch 复用设计 v0.2

- 状态：**设计，送审（v0.2，修订 v0.1）**。尚无对应代码改动；当前 operative 行为是 `freeze_window` 在 catalog 耗尽时 fail-closed `raise`。
- 上游证据：
  - `tools/g0/probe_block_capacity.py` → `artifacts/g0/active_static_probe/probe_block_capacity.json`（容量）
  - `tools/g0/probe_catalog_epoch_boundary.py` → `artifacts/g0/active_static_probe/probe_catalog_epoch_boundary.json`（边界可达性）
- 相关 Gate：`G0-R09-B-TTT-V035-ACTIVE-ROUTE-RESUME`（resume 接线，已送审）、`G0-R09-B-TTT-V035-ACTIVE-WINDOW-SLOT-ROTATION`（slot 轮转修复，已送审）
- 建议 Gate：`G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE`

---

## 0. 修订记录（v0.1 → v0.2）

v0.1 已送审（commit `bae39647`）。v0.2 修正了 v0.1 的**核心前提**，并附实测证据：

| 项 | v0.1 的说法 | v0.2 的修正 | 依据 |
|---|---|---|---|
| §3 触发条件 | 直接采用契约 `rollover_projected_if_safe` 的两条条件 | **两条条件在 active 路线上恒不成立（112 个边界上各 0 次，且此后永久不成立）**，契约的 epoch 边界不可达；改用「下一个窗口填不满」的界条件 | §3.1、§10 探针实测 |
| §2 判定 | 「不是新机制，而是接线」 | **部分成立**：快照契约 / 排列函数 / scheduler 接口确为复用；**边界规则必须为 active 路线新定**，契约的规则在本路线不可表达 | §3.1 结构论证 |
| §6 BLOCKED | 「若条件 2 无法成立则本设计不落地，须改为按 slot 独立推进 epoch」 | 该情形**已实测发生**；但 v0.1 给出的回退并非必要——条件 2 在契约里承重的原因在 active 路线不成立，见 §3.3 | `canonical_segment_adapter_scheduler.py:434-435`、`:564-569` |

v0.1 的 §1、§4.1、§4.3、§5、§7 经复核仍然成立，保留；§4.4 为 v0.2 新增（消除 v0.1 §4.2 中「重排 `_by_slot[slot]`」的歧义）。

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

**v0.2 补充**：容量够了也不够——**当前的 epoch 边界规则在本路线上根本触发不了**（§3.1）。两项必须一起解决。

---

## 2. 判定

### 2.1 可复用的部件（v0.1 判断成立）

| 已存在的部件 | 位置 | 现状 |
|---|---|---|
| epoch 快照契约 | `canonical_segment_adapter_scheduler.py:57-67` `QueueEpochSnapshot(queue_seed, epoch, catalog_digest, positions, permutations)` | 已冻结 |
| epoch 排列函数 | 同文件 `:76-110` `queue_digest_preimage` / `queue_permutation`（按 `(seed, epoch, category)` 做 SHA256 确定性排列） | 已冻结，字节序有版本标记 `PSM-WMA/queue/v1` |
| scheduler 接口 | `local_memory_segment.py:331-337` `configure_queue(seed, epoch, permutation, provenance)` | **已实现，但全仓零生产调用点**（仅 `local_memory_segment_test.py:113`） |
| 持久化槽位 | `local_memory_segment.py:362-365`（`rebuild`）与 `:378-381`（`snapshot`）已含 `queue_seed`/`queue_epoch`/`queue_permutation`/`segment_provenance` | 已就位 |
| 完整性自校验 | `canonical_segment_adapter_scheduler.py:455-463` 在构造时用 `queue_permutation` 重算并断言排列与确定性权威一致 | 已冻结，是本设计 §6 判据 1 的参照 |

**单位对齐（已核实）**：契约的 `_queue_for(category)` 只取 `cursor == 0 and consumer_step_start == 0` 的行（`:471-480`），即**每个 episode 一行**。active 路线 `canonical_segment_streams` 为每个 episode 建一个 `CanonicalSegmentStream`（`active_local_memory_launch.py:169-182`），`_by_slot[slot]` 是该 slot 的 episode 列表。**两者逐一对应**。

> 注：模块 docstring 声明该文件是 CPU/static 契约模型（"deliberately models metadata only... not a trainer integration point"）。它定义的是**语义**。

### 2.2 必须新定的部件（v0.2 修正）

**契约的 epoch 边界规则在 active 路线上不可表达**，因此本设计不能只做"接线"：需要为 active 路线新定一条**触发规则**（§3.2）。这条规则**不改契约文件**，定义在 driver 侧。

---

## 3. epoch 边界（v0.2 重写）

### 3.1 为什么契约的两条条件不能直接用

**结构差异（根因）**：契约的窗口成员是**弹性的**——`derive_member(*, member_index, slot_ids)` 由调用方给出本 member 参与哪些 slot（`:522-530`），member 可长可短。active 路线的窗口是**定长的**——`_arm_initial` 断言 `window_members == trainer.config.trainer.grad_accum_iter`（`active_local_memory_driver.py:158-160`）。契约模型允许"最后一个窗口短一点"，本路线不允许。

**条件 1（每个 category 的队列位置都到末尾）在本路线恒不成立**：
- 已核实条件 1 是 **episode 级**（每个 episode 是否已被 admit），不是 block 级：`_admit_free_slot` 用 `positions[category]` 索引 `_queue_for(category)` 的排列（`:512-517`），`_commit_admission` 每 admit 一个 episode 才 +1（`:589-590`）。故「已开始但仍有剩余 block」的 episode 算已 admit。
- `14430 = 112 × 128 + 94`。第 112 个窗口结束后剩 94 个 block，而**任何窗口都需要 128 个 block**；`freeze_window` 在其 128 轮中的任一轮找不到有 block 的 slot 就 `raise`（`:230-231`）。故 94 个 block 永久无法被消耗。
- 实测残留分布：slot 0 = 50、slot 4 = 44，**全部属 libero_10**；libero_goal / libero_object / libero_spatial 已彻底走完（各 0）。
- 其中 **slot 0 已 terminal 但列表里下一个 episode 有 50 个残留 block**，该 episode 永远无法被 admit ⟹ 条件 1 永久为假。
- 实测：112 个窗口边界上条件 1 成立 **0 次**。

**条件 2（所有 stable slot 均 terminal）在本路线恒不成立**：
- 需要 8 个 slot 在同一个窗口边界上**同时**停在各自 episode 的末尾。
- 实测：112 个窗口边界上成立 **0 次**；耗尽时只有 slot 4 非 terminal（stable 且中途），而它带着 44 个永远消耗不掉的残留 block ⟹ 永久为假。

**因此：契约的 epoch 边界在 active 路线上永久不可达。** 这是证明，不是推断（前提：窗口定长 128、block 消耗单调）。探针实测与之一致（§10）。

**为什么只在窗口边界评估**：设计只能在窗口边界动作。冻结的计划是不可逆的（`freeze_window` 的 docstring 明示），在窗口中途重置会让已冻结计划剩余 member 的 identity 失效。故契约在 member 边界评估的语义，在本路线只能退化到窗口边界评估。

### 3.2 修正后的触发规则

> **在窗口边界（`owner.phase is IDLE`），当且仅当「下一个窗口无法被填满」时推进 epoch**，即
> `Σ_slot remaining_blocks(slot) < window_members`。

实测：该条件在窗口 112 之后首次成立，此时剩 94 个 block。

**为什么这是契约规则的忠实类比，而不是另起一套**：
- 它恰好在「catalog 再也供不起一个整窗口」时触发，这正是契约条件 1 想要表达的时刻；
- 当 catalog 恰好能被整窗口消费完时，两者**重合**；
- 它是本路线上唯一可达的触发点。

**边界语义**：一个 epoch 覆盖 catalog 的**完整一遍减去至多 `window_members − 1` 个尾块**。此处每 epoch 有 94 个 block（0.65%）被推迟到下一个 epoch；由于新 epoch 会从位置 0 按新排列重走整个 catalog，**这些 block 不会永久丢失**（见 §6 判据 5）。

**容量换算**：每 epoch 112 个窗口（不是 112.73）。`max_iter = 5000` ⟹ `⌈5000 / 112⌉ = 45` 个 epoch。

### 3.3 为什么不需要 v0.1 §6 的回退（按 slot 独立推进 epoch）

**条件 2 在契约里承重，是因为契约的 rollover 会清空守卫容器**：`rollover_projected_if_safe` 构造新状态时**不传** `stable_slots` / `terminal_slots`（`:564-569`），而这两个字段默认 `()`（`:434-435`）。若边界落在 episode 中途，该 slot 的延续会在 `positions` 已重置的同时**静默消失**——所以契约必须用条件 2 把边界挡在 episode 边界上。

**在 active 路线上这个理由不成立**：§4.3 的重置既清空守卫容器，**又把每个 slot 的游标归零**。中途的 episode 尾部不是被静默丢弃，而是被**显式推迟**到下一个 epoch，并在那里被重新完整走过。因此条件 2 在本路线是多余约束，v0.1 §6 的按-slot-独立推进回退会引入逐 slot 的 epoch 记账、以及「一个 category 的排列要跨两个 slot」的额外语义，**没有收益**。

---

## 4. 实现方案（最小改动）

### 4.1 driver 侧（`active_local_memory_driver.py`）

新增一个 catalog epoch 计数与一个边界推进方法，并在**窗口边界**调用。

**触发点必须是窗口边界，不能是 `freeze_window` 的 raise 点**。理由：`freeze_window` 在循环体内逐 member 调用 `_commit_block`（`:234`），**中途 `raise` 时 `self._stream_index` / `_active_stream` / `_active_cursor` 已被部分推进**，即该函数不是原子的；在 raise 点重置会留下一个半推进的窗口状态。窗口边界（`_arm_initial`，即 `owner.phase is IDLE`）是唯一干净的回滚点。

`_arm_initial`（`:157-166`）在调用 `freeze_window()` **之前**插入边界检查：

- **探测必须是纯的**：`_peek_block` 的 docstring 明示 "commits no driver state"（`:258-263`）。剩余量按与 `_peek_block` 同一规则计算（活跃 episode 剩 `blocks − 1 − _active_cursor`，其后每个 episode 贡献 `block_count`）。
- 实现时应把「剩余量」抽为一个被探测与 `freeze_window` 共用的内部函数，避免两处规则漂移（§6 判据 3）。
- 若不满足 §3.2，则执行 §4.3 的重置并推进 epoch，再调用 `freeze_window()`。

### 4.2 scheduler 侧（`local_memory_segment.py`）

`configure_queue` 当前只把四个字段存下来（`:334-337`），**不改变 `_by_slot` 顺序**（它看不到 `_by_slot`）。**不改 `RankLocalSegmentScheduler` 的公开接口**：`configure_queue` 的签名与语义保持为「记录本 epoch 的队列身份」，`_by_slot` 的重排由 driver 执行（`_by_slot` 是 driver 的状态）。

### 4.3 重置动作的精确清单

在 epoch 边界：

**driver 侧**
- `_stream_index = {slot: 0 for slot in self._by_slot}`
- `_active_stream.clear()`、`_active_cursor.clear()`（清空后 `_peek_block` 的 `rebind = stream is not None` 为 False，新 episode 的 `cursor == 0` 即为合法首块）
- `_by_slot` 按 §4.4 的规则重排（每个 category 独立）
- `_window_index` **不重置**（全局窗口计数，`plan_chain_id` 的单调性依赖它）
- 新增 `_catalog_epoch`，随 epoch 递增

**scheduler 侧**
- `stable_slots.clear()`、`terminal_slots.clear()`
- `admission_order.clear()`、`committed_identities.clear()`
- 经 `configure_queue` 记入新的 `queue_seed`（不变）/`queue_epoch`（+1）/`queue_permutation`/`segment_provenance`
- **`cumulative_valid_consumer_exposure` 不清零**。理由：`freeze_window` 用的是**比例** `exposure[category] / sum(exposure.values())`（`:226`），累计不清零时该比例依然稳定收敛于 `target_distribution`，配额语义不变；清零反而破坏「累计有效消费者曝光」这一字段本身的语义。

**尾部丢弃是刻意语义**：与 v0.1 不同，边界处**不保证**所有 stable slot 都 terminal（§3.1），故尾部 episode 的残余 block 会被推迟。这是设计的一部分，不是缺陷。

**为什么清空 `committed_identities` 是安全的**：`_is_admissible` 的守卫在 `stable_slots` 无该 slot 记录时只要求 `identity.cursor == 0`（`:309-311`）；`terminal_rebind` 会删除 `stable_slots` 条目（`:343`）。故新 epoch 首块（cursor 0）天然可准入。而 `commit` 的重复检查 `identity in self.committed_identities`（`:323`）在清空后不再拒绝跨 epoch 复用的同一 identity。`canonical_segment_runtime.py:181-182` 的一致性校验（commit 的 identity 必须在 `admission_order` 中）因两个容器**同时**清空而保持成立。

**`SegmentIdentity` 的结构与其字段值均不变**——同一 episode 同一 cursor 在不同 epoch 会产生**相等的 identity 值**，这是刻意的：identity 描述「数据段的身份」，跨 epoch 复用同一段本就该是同一个身份；守卫状态由 epoch 边界重置管理，而不是靠给 identity 加 epoch 维度。**因此本设计不触及 `SegmentIdentity` 的 ABI。**

### 4.4 重排规则（v0.2 新增，消除 v0.1 §4.2 的歧义）

排列是**category 级、以 episode 为单位**的，而 `_by_slot[slot]` 是该 category 的 episode 在**各 slot 上的划分**（一个 category 占 `b_stream // len(categories)` = 2 个 slot，`active_local_memory_launch.py:166`）。故「重排 `_by_slot[slot]`」必须精确规定：

1. 对该 category 的全部 episode，按 `(identity.source_digest, identity.episode_id)` **排序**，得到参照序 —— 必须与 `_queue_for` 的排序（`:477`）**逐位一致**。
   - 注意 `_queue_for` 排的是 `row.identity.episode_id`，而 active 路线的 `episode_id = str(stream.episode_index)`（`active_local_memory_driver.py:241`）是**字符串**。参照序是**字符串比较**（`"10" < "2"`），不是数值比较；实现若用 `int()` 排序会与契约不一致。
2. `queue_permutation(queue_seed, epoch, category, catalog_size)` 给出参照序上的索引排列。
3. **每个 slot 取其自身 episode 在该排列中的保序子序列**作为新的 `_by_slot[slot]`（即 `[e for i in permutation if (e := ref[i]) in 该 slot 的 episode 集合]`）。

该规则确定、可逐位校验，且不改变每个 slot 持有的 episode 集合（只改顺序）。

### 4.5 与 `on_train_start` 的关系

不改 `active_local_memory_launch.py:223-289` 的构建路径。catalog 仍只建一次，多 epoch 复用发生在**同一份 catalog 上**（重排 + 游标归零），不重新读取数据集、不重建 producer。

---

## 5. 与 resume 设计的耦合与建议顺序

**耦合点**：本设计引入的 `_catalog_epoch`（driver 侧）与 `queue_epoch`/`queue_permutation`（scheduler 侧）**都必须在 checkpoint 中持久化**，否则 resume 后 epoch 语义错。所幸 scheduler 侧的三个字段**已在 `snapshot()`/`rebuild()` 中就位**（`local_memory_segment.py:362-365`、`:378-381`），driver 侧的 `_catalog_epoch` 需与 `_window_index` 一并加入 resume 设计的 driver 快照。

**建议顺序：先落地 resume 接线，再落地本设计。** 理由：
- resume 设计已要把 driver 的 `_stream_index`/`_active_stream`/`_active_cursor`/`_window_index` 与 scheduler 的守卫容器全部持久化。本设计**只在其上增加 `_catalog_epoch` 一个字段**与 epoch 边界动作。
- 若颠倒顺序，resume 需要一次性把 epoch 语义并入快照，改动面更大、一次送审的技术面更宽。

**本设计不改变 resume 设计 §6 的任何判据**：其中判据 4 的 GPU 短跑至生产 `save_iter = 50 < 112`，落在单 epoch 内，与本设计正交。

---

## 6. 验收判据

**PASS**（全部满足）：

1. **契约一致性（CPU）**：epoch 推进后，每个 slot 的 `_by_slot[slot]` 等于「按 `(source_digest, episode_id)` 排序 → 应用 `queue_permutation(queue_seed, epoch, category, catalog_size)` → 取该 slot 子序列」的结果，**逐位一致**；`queue_epoch` 恰好 +1；且参照序与 `_queue_for`（含其**字符串**比较语义）一致。
2. **容量解除（CPU，纯规划层）**：用 `probe_block_capacity.py` 的 producer 搭建同一套 catalog，在**不取任何张量**的前提下连续推演窗口规划越过 epoch 边界，断言：①可连续规划出 **≥ 5040** 个窗口（45 epoch × 112）而不再 `raise`；②第 113 个窗口成功规划；③跨 epoch 无 identity 被 `commit` 的守卫拒绝。
3. **原子性**：断言窗口边界的探测**不修改** driver 状态（探测前后 `_stream_index`/`_active_stream`/`_active_cursor` 逐位相同），且探测所用的剩余量规则与实际 `freeze_window` 共用同一实现。
4. **触发规则的两侧**：①剩余 ≥ `window_members` 时**不**推进 epoch；②剩余 < `window_members` 时推进；③推进后 `_window_index` **不**重置（递增值连续）。
5. **尾块不丢失**：跨 epoch 后，断言上一个 epoch 被推迟的尾块在新 epoch 中被 `commit` —— 即按 epoch 分别统计的 `committed_identities` 覆盖全部 14430 个 block 身份至少一次（epoch 0 覆盖 14336，epoch 1 覆盖其余 94 + 14336 中的一部分）。
6. **GPU 端到端**：短跑越过一个 epoch 边界，断言无 `raise`、loss 有限、`per_slot_members` 在每个窗口内仍为 8 个 slot 均衡、`cumulative_valid_consumer_exposure` 单调不减（不清零）。
7. **resume 交叉（在 resume 落地后）**：在 epoch ≥ 1 处存盘并 resume，断言 `_catalog_epoch` 与 `queue_epoch` 一致恢复、续跑窗口序列与不中断跑一致。

**FAIL**：epoch 边界推进后出现 identity 守卫拒绝；或探测修改了 driver 状态；或重排结果与 §4.4 规则不一致；或 `cumulative_valid_consumer_exposure` 被清零；或推迟的尾块在新 epoch 中未被覆盖。

**BLOCKED**：若 §3.2 的触发规则在真实链路上仍不可用（例如第 113 个窗口仍 `raise`，或跨 epoch 出现 identity 守卫拒绝而无法通过重置清单解决），则本设计不落地，须改为「按 slot 独立推进 epoch」（代价见 §3.3）。

---

## 7. 禁止范围

- 不改 `SegmentIdentity` / `GAWindowPlan` / `SegmentBatch` 的 ABI 与字段。
- 不改 `admit` / `commit` / `terminal_rebind` 的守卫条件本身（本设计只重置它们所依赖的**状态容器**，不改判定逻辑）。
- 不改 `queue_digest_preimage` / `queue_permutation` 的字节序（契约已冻结，有 `PSM-WMA/queue/v1` 版本标记）。
- 不改 `canonical_segment_adapter_scheduler.py`（它是冻结的 CPU/static 契约模型；本设计只在 driver 侧定义触发规则）。
- 不新增 DCP 顶层 key（`dcp.py:939` 会拒绝）。
- 不重建 catalog、不重新读取数据集、不改 `on_train_start` 的构建路径。
- 不为 identity 增加 epoch 维度。
- 不在 `freeze_window` 的 `raise` 点做重置（非原子，见 §4.1）。

---

## 8. 请求 verdict

请就以下四点裁定：

1. **§3.2 的界条件**（「下一个窗口填不满」⟹ 推进 epoch）是否可接受为 active 路线的 epoch 边界。它以「完整遍历减去至多 127 个尾块」替代契约的「精确到末尾」；v0.2 主张这是契约条件 1 在本路线的忠实类比（§3.2），且契约条件 2 因 §4.3 的重置而成为多余约束（§3.3）。**是否应当改为在契约文件内新增一条广义规则以保持两处语义同步，还是维持「契约只定义语义、driver 侧实现」？**
2. **§4.4 的重排规则**是否正确，特别是 `_queue_for` 的参照序用的是**字符串** `episode_id` 比较（`:477`）——实现若按数值排序会与契约产生偏差，这是否是本设计最易出错的点。
3. **§4.3 的重置清单是否完备**——是否还有第四处状态（driver / scheduler / owner 侧）会跨窗口残留、从而在第二个 epoch 造成静默错误。特别请审 `_rebind_terminal`（driver `:190-195`）在 epoch 边界的时序、以及 `owner` 的 `phase`/`transaction` 是否有未列出的残留状态。
4. **§5 的顺序判断是否成立**：本设计的实现应当排在 resume 落地之后，且 resume 设计 §6 的判据无需因本设计修改。

---

## 9. 实现记录

**当前 operative 行为**：catalog 耗尽时 `freeze_window` fail-closed `raise`（`active_local_memory_driver.py:230-231`）。**D8b 长跑（5000 步）不得在此状态下启动**——会在第 113 步 crash，白耗约 8 小时。

本文档为**设计**，尚无对应代码改动；实现与证据将在 Gate 裁定后补入本节。

---

## 10. 实测证据（v0.2 新增）

探针 `tools/g0/probe_catalog_epoch_boundary.py` 走**真实 driver + 真实 scheduler**（不取任何张量，故能走完全部 catalog），在每个窗口边界上评估契约的两个条件本身：

```
LIBERO_ROOT=/disk/rl/data/LIBERO_LeRobot_v3 \
LIBERO_LATENT_CACHE_ROOT=/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1 \
  cosmos-framework/.venv/bin/python tools/g0/probe_catalog_epoch_boundary.py \
  --output-json artifacts/g0/active_static_probe/probe_catalog_epoch_boundary.json
```

读数（`probe_catalog_epoch_boundary.json`）：

| 项 | 读数 |
|---|---|
| `windows_completed` | 112 |
| `boundary_error` | `active Local window exhausted every segment stream` |
| `condition1_true_count` / 112 个边界 | **0** |
| `condition2_true_count` / 112 个边界 | **0** |
| `both_true_boundaries` | `[]`，`reachable = false` |
| `stranded_blocks` | 94（slot 0 = 50，slot 4 = 44） |
| `remaining_blocks_by_category` | libero_10 = 94，其余三个 = 0 |
| `admissible_episodes` | libero_10 = 375，libero_goal = 424，libero_object = 449，libero_spatial = 428（合计 1676 = streams，无零 block episode） |
| `terminal_slots` | 0,1,2,3,5,6,7 |
| `stable_but_not_terminal` | 4 |

**永久性论证**：第 112 个窗口后总剩余 94 < 128 = `window_members` ⟹ 此后每个 `freeze_window` 都会在其 128 轮之一找不到有 block 的 slot 而 `raise` ⟹ 第 14336 个之后的 block 永不提交 ⟹ 游标永久冻结。于是：slot 0 的下一个 episode（持 50 个残留 block）永不被 admit，条件 1 永久为假；slot 4（中途，持 44 个残留 block）永不到达 terminal，条件 2 永久为假。

**探针自身的一处更正（如实记录）**：该探针的初版把条件 1 算成了 **block 级**（「该 category 还有没有整块」），而契约的条件 1 是 **episode 级**（`:512-517`、`:589-590`、`:471-480` 已核实）。block 级是更强的谓词，两者在边界附近会给出不同答案。初版读数（`condition1_all_categories_drained = false`）因而是**用错谓词得到的、虽然结论方向相同但依据不成立的**读数；v0.2 的读数是修正后探针的输出，并额外记录了逐边界的条件轨迹。初版产物已被覆盖，未提交。
