# PSM-WMA Local Memory v0.3.5 — active 路线 catalog 多 epoch 复用设计 v0.6

- 状态：**设计，送审（v0.6；修订 v0.5；v0.5 修订 v0.4；v0.4 修订 v0.3；v0.3 修订 v0.2；v0.2 修订 v0.1）**。尚无对应代码改动；当前 operative 行为是 `freeze_window` 在 catalog 耗尽时 fail-closed `raise`。
- 上游证据：
  - `tools/g0/probe_block_capacity.py` → `artifacts/g0/active_static_probe/probe_block_capacity.json`（容量）
  - `tools/g0/probe_catalog_epoch_boundary.py` → `artifacts/g0/active_static_probe/probe_catalog_epoch_boundary.json`（边界可达性，§10.1）
  - `tools/g0/probe_epoch_reuse_planning.py` → `artifacts/g0/active_static_probe/probe_epoch_reuse_planning.json`（规划层容量解除，§10.3/§10.4）
  - `tools/g0/probe_epoch_reuse_planning.py --max-epochs 1` → `artifacts/g0/active_static_probe/probe_epoch_reuse_planning_epoch0.json`（**epoch 0 单独基线**，§10.4）
- 相关 Gate：`G0-R09-B-TTT-V035-ACTIVE-ROUTE-RESUME`（resume 接线）、`G0-R09-B-TTT-V035-ACTIVE-WINDOW-SLOT-ROTATION`（slot 轮转修复）。**2026-09-17 09:54 送达更正**：三者 formal root/child 已于本轮推送远端（根仓 `V2=4cdedf68`、子模块 `v2=525f506`），此前「只在本地、未送达」的记录已过期。
- 建议 Gate：`G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE`

---

## 0. 修订记录

### v0.5 → v0.6

v0.5 已推送远端并送达三方（formal pair 见「相关 Gate」下注）。v0.6 是**对三方审核意见的一次性整改**：唯一实质变更是 **§8 第 7 问裁定为 (a)**（引入 per-epoch observed 计数器），并同步闭合其余六问的技术决策。来源：DS `REQUEST_CHANGES`（主因 `:191-197,485-493` 反对把 44/45 epoch regime 塌缩当已知代价）+ MM（「第 7 问不可悬置，应实现前裁定」）。

| 项 | v0.5 的说法 | v0.6 的修正 | 依据 |
|---|---|---|---|
| §4.1 driver 侧 | 仅新增 `_catalog_epoch` | 新增 `_catalog_epoch` **与 per-epoch observed 计数器 `_epoch_observed`** | 选 (a) |
| §4.3 重置清单 | driver 侧无 `_epoch_observed`；exposure 段把「改选择键」列为 §7 之外待裁定 | driver 侧新增「`_epoch_observed` 清零」；exposure 段改为**裁定 (a)**：`cumulative_valid_consumer_exposure` 保留仅作报告量，`freeze_window` 选择键改用 `_epoch_observed` | DS `REQUEST_CHANGES` 主因 |
| §4.6 `queue_seed` | 三候选待裁定 | **选 (b)**：由 catalog 身份派生 | DS（seed 注入与判据）+ §8 第 5 问 |
| §4.7 sidecar 归属 | 三候选待裁定 | **选 (b)**：`owner` 新增 rollover 入口 `discard_committed_carry()` | DS（IDLE 断言与归属协调）+ §8 第 6 问 |
| §6 判据 | 7 条 + sidecar 判据 | 新增**判据 9**（per-epoch observed：epochs ≥1 形态与 epoch 0 逐 epoch 一致）与**判据 10**（queue_seed/queue_epoch resume 一致性） | 选 (a)、(b) 的直接后果 |
| §7 禁止范围 | 「不改 `freeze_window` 选择键」隐含于范围外 | **显式允许**「改 `freeze_window` 选择键的 `observed` 来源（累计字段 → per-epoch observed）」；其余禁止不变 | 选 (a) |
| §8 第 7 问 | 三选一待裁定 | **裁定 (a)**；第 1–6 问技术决策同步闭合（见 §8） | DS/MM |

v0.5 的 §1–§3、§4.2、§4.4–§4.5、§5、§9、§10 在 v0.6 中**逐字未改动**；改动集中在 §4.1、§4.3（exposure 段 + 清单一条）、§4.6、§4.7、§6、§7、§8 与 §0、标题。

### v0.4 → v0.5

v0.4 已提交（blob `219355d3`）但**从未推送、从未送达任何审核者**。v0.5 是**对 v0.4 自己留下的一个未决项的闭合**：v0.4 判定「§6 判据 6 的更正形式是否在今天就已为假」无法由 45 epoch 的全局值判定，须补单 epoch 基线；该基线已跑出，结论是**今天就已为假**，故该判据形式整体撤回。

| 项 | v0.4 的说法 | v0.5 的修正 | 依据 |
|---|---|---|---|
| §6 判据 6 | 把「同类两 slot 成员数之差 ≤ 1」**降级为记录量**，待单 epoch 基线判定 | **整体撤回**（不再作为判据，也不再是候选通过条件）。单 epoch 基线实测 epoch 0 的 `max_within_category_slot_skew = **32**`，该形式在今天就已为假 | `probe_epoch_reuse_planning_epoch0.json` |
| §10.4 | 「epochs 1–44 与 epoch 0 构成相反」，但 epoch 0 的量化基线缺 | 补 epoch 0 单跑基线表：单 suite 窗口 **14.3%（epoch 0）vs 77.3%（epochs 1–44）**，**相差 5.4 倍** | 同上 |

v0.4 的 §1–§4、§5、§7–§9 在 v0.5 中**逐字未改动**；改动集中在 §6 的一条、§10.4 的一节、§0 与标题。

### v0.3 → v0.4

v0.3 已送审（blob `c6693a12`）。v0.4 的唯一来源是**45 epoch 满跑（5040 窗口）把 v0.3 的两处推断证伪**——不是新设计，而是**修正 v0.3 对既有实测的解读**，并把由此暴露的问题升级为送 Gate 的第 7 问：

| 项 | v0.3 的说法 | v0.4 的修正 | 依据 |
|---|---|---|---|
| §10.4 结论 | 「epoch 0 的形态与之后 44 个 epoch **逐位相同**」，偏斜是**既有性质被复用放大** | **前提为假**。相同者只有聚合量（112 窗 / 残留 94）；**窗口内部构成相反**：epoch 0 有 81 个窗口服务全部 4 类，epochs 1–44 为 **0**。≥ **75.3%** 的窗口只服务 1 个 suite | §10.4 严格下界推导 |
| §10.4 归因 | 51 个 2-slot 窗口来自「尾部只剩 libero_10」 | **算术上不可能**（51 × 128 = 6528 > libero_10 每 epoch 消耗 5626） | 同上 |
| §4.3「不清零」 | 「偏差成因不是不清零，而是供给约束」 | 该判断**只对 epoch 0 成立**。`cumulative_valid_consumer_exposure` 同时是 `freeze_window` 的**控制输入**，不清零是 epochs ≥1 构成塌缩的直接原因 | §4.3 第二次更正 |
| §6 判据 6 | 把「同类两 slot 成员数之差 ≤ 1」升为**通过条件** | **降级为记录量**：实测全局 `max_within_category_slot_skew = 64`，但**未按 epoch 分离**，无法判断 epoch 0 单独是否 ≤ 1——若为假则与刚更正掉的原文属同一类缺陷 | §10.4 末段 |
| §8 第 7 问 | 请裁定「是否作为既有行为接受」 | **重写**：前提被推翻，改为三选一（是否把 per-epoch observed 计数器纳入范围 / 是否接受该代价 / 判据 6 降级是否认可） | §8 第 7 点 |

v0.3 的 §1–§3、§4.1–§4.2、§4.4–§4.7、§5、§7、§9 在 v0.4 中**逐字未改动**；改动集中在 §4.3 的一条、§6 的一条、§8 的一条、§10.4 全节、§0 与标题。

### v0.2 → v0.3

v0.2 已送审（blob `8a1dbec3`）。v0.3 是**在下游自查中发现的、v0.2 §4.3 重置清单的一处遗漏**，并补齐规划层实证：

| 项 | v0.2 的说法 | v0.3 的修正 | 依据 |
|---|---|---|---|
| §4.3 重置清单 | driver + scheduler 两处状态 | **不完备：缺第三处——adapter 的 `LocalMemorySegmentSidecar`**。rollover 后新 epoch 第一个 member 必然 `raise ValueError` | §10.2 最小复现 |
| §4.7（新增） | — | sidecar 重置的**归属与可达路径**待裁定（既有 `reset` 是死代码，`sidecar` 被三层持有） | `local_memory_segment_adapter.py:45-46` |
| §6 判据 | 7 条 | **新增判据 8**（sidecar 重置）；**判据 6 措辞更正**——原文「每个窗口内仍为 8 个 slot 均衡」**在今天就已为假**，改为「窗口内 `used` 轮转」 | §10.4 实测 |
| §8 | 5 问 | 第 3 问由本设计自查给出答案（**有且只有 sidecar 一处**）；新增第 6 问（sidecar 归属）、第 7 问（覆盖度偏斜） | `canonical_segment_runtime.py:157-179`、`production_active_wiring.py:62-66` |
| §10 | 仅边界可达性实测 | 补 **10.2** sidecar 最小复现、**10.3** 规划层满跑实证（5040 窗口 PASS）、**10.4** 窗口类别覆盖度偏斜 | 探针 `probe_epoch_reuse_planning.py` |

v0.2 的 §1–§3、§4.1–§4.2、§4.4、§7 在 v0.3 中**逐字未改动**；§4.3（补 adapter 侧）与 §5（补一处 resume 语义）为**增补**，原有条目未改；§4.6 为 v0.2 送审后补入（`queue_seed` 来源）。

### v0.1 → v0.2

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

**per-epoch observed 计数器（v0.6 新增，选 (a) 的落地）**：driver 新增 `self._epoch_observed: dict[category, int]`，与 `_catalog_epoch` 并列。`freeze_window` 的选择键**不再读 `scheduler.cumulative_valid_consumer_exposure`**，改为读 `_epoch_observed`（`observed = _epoch_observed.get(category, 0) / max(sum(_epoch_observed.values()), 1)`）；每选中一个 member 后 `_epoch_observed[category] += planned`（与现行 `:236` 的 `+planned` 一致，只是写到 per-epoch 计数器而非累计字段）。`_epoch_observed` 在 epoch 边界清零（§4.3），`scheduler.cumulative_valid_consumer_exposure` 保留仅作报告量，由 scheduler 在 `commit` 时照旧更新、不被 `freeze_window` 读取。**由此 epochs ≥1 的窗口形态恢复为与 epoch 0 逐 epoch 一致**（§10.4 的塌缩被消除）。

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
- **`_epoch_observed.clear()`（v0.6 新增，选 (a)）**：per-epoch observed 计数器归零，使 `freeze_window` 下一 epoch 的赤字从零开始

**scheduler 侧**
- `stable_slots.clear()`、`terminal_slots.clear()`
- `admission_order.clear()`、`committed_identities.clear()`
- 经 `configure_queue` 记入新的 `queue_seed`（不变）/`queue_epoch`（+1）/`queue_permutation`/`segment_provenance`
- **`cumulative_valid_consumer_exposure` 不清零（v0.6 起为最终裁定，见下）**。**但 §8 第 7 问已裁定为 (a)**：该累计字段**只作报告量**保留，`freeze_window` 的选择键**不再读它**，改读 driver 侧 per-epoch observed（`_epoch_observed`，§4.1）。因此「不清零」从「待裁定的控制输入」降为「报告语义」，不再影响选择。

  **措辞更正（v0.3）**：本条 v0.2 原文写作「累计不清零时该比例依然稳定收敛于 `target_distribution`，配额语义不变」。**该表述过于乐观，与实测不符**——实测 45 epoch 后 `libero_10` 占 **39.2%** 而目标是 25%（§10.4）。

  **第二次更正（v0.4，实测推翻 v0.3 的成因判断）**：v0.3 在此处断言「**偏差的成因不是「不清零」**……偏差来自每个 epoch 尾部另三类已抽干、无可选 block，即**供给约束**而非配额规则」。45 epoch 满跑显示**该判断只对 epoch 0 成立**：epochs ≥1 与 epoch 0 的窗口构成**相反**（epoch 0 有 81/112 个窗口服务全部 4 类；epochs 1–44 该计数为 0），75.3% 的窗口只服务 1 个 suite（§10.4 的严格下界）。根因是 `observed` 取自本字段，而本字段在 rollover 时**保留**——于是 epochs ≥1 开局即继承偏斜赤字，`freeze_window` 连续服务赤字为正的类别直到其抽干，窗口塌缩到单一 category。

  **最终裁定（v0.6，采纳 DS/MM 意见）**：本字段同时是 `freeze_window` 的控制输入，「不清零」不是只影响报告语义的中性选择——这一判断被 DS 采纳为 `REQUEST_CHANGES` 主因（「不应作为已知代价接受」）。故选 (a)：`freeze_window` 选择键改用 per-epoch observed，累计字段仅作报告量。该裁定触及 `freeze_window` 的选择键，§7 已显式放宽这一条。

**adapter 侧（v0.3 补入，v0.2 遗漏）**
- 对**每个 slot** 调用 `LocalMemorySegmentSidecar.reset(identity)`（`local_memory_segment_adapter.py:45-46`，按 `slot_id` pop），把全部 fast-state carry 丢弃。
- **无条件对全部 slot 调用是安全的**：`reset` 用 `pop(slot_id, None)`，对无记录的 slot 是 no-op，故无需先枚举「哪些 slot 有记录」。
- **时序安全**：rollover 发生在两个窗口之间，此时 `owner.phase == IDLE` 且 `adapter._pending_scan is None`（每个窗口的 `commit`/`discard_pending` 已把 pending 清空，`local_memory_segment_adapter.py:185`、`:74`），故重置不与任何未结事务冲突。这也是本设计把 rollover 放在窗口边界而非窗口内的原因之一。

**为什么必须丢弃 carry（决定性论证，非推测）**：`sidecar.commit` 只在该 identity `training_stream_end` 为真时 pop（`:39-43`），否则存下该 slot 的 `state_out`；而 `sidecar.read`（`:29-37`）在「不是前一身份 + 1 个 cursor」时**抛 `ValueError`（不是返回 `None`）**，且**该动作会先把 carry 读出来喂给 `scan`**。

今天这套代码里 `reset` 是**死代码**（生产与测试零调用点），因为 slot 换 episode 只发生在上一 episode 已 terminal 时，而 terminal 的那次 `commit` 已经把记录 pop 掉了——即**不变量**：「slot 换 episode 时，sidecar 必无该 slot 的记录」。

epoch rollover 是这套代码里**第一个在记录仍存活时把 slot 倒回 cursor 0 的操作**，因而打破该不变量，且后果是确定性的：

1. 新 epoch 的 slot 首块由 `_peek_block` 给出，此时 `_active_stream` 已被清空 ⟹ `rebind = stream is not None` 为 **False**（`active_local_memory_driver.py:264-280`）⟹ 运行时**不会**调用 `_rebind_terminal`；而 `_rebind_terminal` 本身也只对 terminal slot 生效（`:190-194`），**且完全不触碰 sidecar**。
2. 该首块的 `cursor == 0`。若记录仍在，`read` 要求 `identity.cursor == previous.cursor + 1`，而 `previous.cursor ≥ 0` ⟹ `0 == previous.cursor + 1` 不可能成立；若首次重排后该 slot 的首个 episode 与记录中的不同，则 `episode_id` 不等先一步触发。**两条路径都抛 `ValueError`**——与排列的具体结果无关，因此这不是「某些 seed 下才出事」，而是**必然发生**。
3. 边界处的记录确实存在：`probe_catalog_epoch_boundary.json` 的 `stable_but_not_terminal = [4]` ⟹ slot 4 的末次 commit 的 `training_stream_end == False` ⟹ `commit` 存下了记录。

丢弃 carry 在语义上也是**正确**的，不只是「避免崩」：epoch rollover 把该 slot 倒回其首 episode 的 **cursor 0**（§4.3 driver 侧），即该 episode 会被**从头重放**；从头重放的首块本应继承**初始**状态，而不是上一 epoch 中途留下的 carry。因此 `reset` 与「重放」语义自洽。

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

### 4.6 `queue_seed` 的来源（v0.6 裁定为 (b)）

`configure_queue` 要求 `seed`，而 `RankLocalSegmentScheduler.queue_seed` / `queue_epoch` **默认 `None`**（`local_memory_segment.py:288-289`）——即在首次 `configure_queue` 之前，队列身份是**未定义**的。契约只要求 seed 非负且**在 epoch 间保持不变**（只有 `epoch` 递增），**未规定它在生产中的来源**；而 `configure_queue` 全仓零生产调用点，亦无先例。

候选：

- **(a) 固定常量**（如 `0`）：最简单，但换 catalog 时会继承同一套 epoch 排列。
- **(b) 由 catalog 身份派生**：`queue_seed = int(sha256(f"{manifest_digest}|{config_digest}|{source_digest}").hexdigest()[:16], 16)`。同一 catalog 重跑 / resume 得到同一排列流（可复现），不同 catalog 不互相继承顺序（隔离）。
- **(c) 新增配置字段**：灵活但引入新的配置面，且需保证 resume 时一致。

**裁定（v0.6）：选 (b)**。可复现性与隔离性都要靠它，且该字段**已在快照中就位**（`snapshot()` 持久化 `queue_seed`），不会丢失。§6 新增判据 10 验证 resume 后 `queue_seed`/`queue_epoch` 与存盘一致。

### 4.7 sidecar 重置的归属与可达路径（v0.6 裁定为 (b)）

§4.3 已确定「必须重置 sidecar」，但**由谁执行**尚未定。现状与约束：

- `LocalMemorySegmentSidecar.reset(identity)` **已存在**（`local_memory_segment_adapter.py:45-46`），只用到 `identity.slot_id`。故**不需要新增接口**，也不触及 §7 关于「不改守卫条件」的禁令。
- 但它当前是死代码（零调用点），且 `sidecar` 被三层持有：`driver.registry.owner.wiring.adapter.sidecar`（`production_active_wiring.py:62` → `production_segment_wiring.py:36` → `local_memory_segment_adapter.py:51`）。

候选：

- **(a) driver 直接穿透三层调用**：`self.registry.owner.wiring.adapter.sidecar.reset(identity)`。改动最小（只动 driver），但把「adapter 的 state 生命周期」的知识泄漏进 driver，且打破了 `production_active_wiring.py` 开头声明的「identity-only capability」分层。
- **(b) 在 `CanonicalSegmentRuntimeOwner` 上新增一个 rollover 入口**（如 `discard_committed_carry()`），由它调用自己 `wiring.adapter.sidecar`，driver 只调 `owner`。分层干净，但要改 `canonical_segment_runtime.py` 的公开面——该文件正被 resume Gate 审查，会与 resume 的改动面重叠。
- **(c) 把「清 carry」并进各层**已有的重置动作（如让 `driver._rebind_terminal` 对所有 slot 都生效并顺带 reset）。**不建议**：`_rebind_terminal` 的语义是「释放已结束的 terminal slot」（`:191`），让它在非 terminal 时也动作会改变其契约含义，且掩盖「rollover 是独立操作」这一事实。

**裁定（v0.6）：选 (b)**。分层与可测性优先；为消除与 resume 的改动面重叠，`discard_committed_carry()` 的落地点与 resume 设计的 `snapshot()`/`rebuild()` 接线一并排入实现顺序（§5），二者在 `canonical_segment_runtime.py` 上的改动以一次协调 commit 完成，避免同一文件的两次独立 review。

---

## 5. 与 resume 设计的耦合与建议顺序

**耦合点**：本设计引入的 `_catalog_epoch` 与 `_epoch_observed`（driver 侧，v0.6 新增）与 `queue_epoch`/`queue_permutation`（scheduler 侧）**都必须在 checkpoint 中持久化**，否则 resume 后 epoch 语义错。所幸 scheduler 侧的三个字段**已在 `snapshot()`/`rebuild()` 中就位**（`local_memory_segment.py:362-365`、`:378-381`），driver 侧的 `_catalog_epoch` 与 `_epoch_observed` 需与 `_window_index` 一并加入 resume 设计的 driver 快照。

**建议顺序：先落地 resume 接线，再落地本设计。** 理由：
- resume 设计已要把 driver 的 `_stream_index`/`_active_stream`/`_active_cursor`/`_window_index` 与 scheduler 的守卫容器全部持久化。本设计**只在其上增加 `_catalog_epoch` 与 `_epoch_observed` 两个字段**与 epoch 边界动作。
- 若颠倒顺序，resume 需要一次性把 epoch 语义并入快照，改动面更大、一次送审的技术面更宽。

**本设计不改变 resume 设计 §6 的任何判据**：其中判据 4 的 GPU 短跑至生产 `save_iter = 50 < 112`，落在单 epoch 内，与本设计正交。

**一处需 resume 侧知晓的语义（v0.3 新增）**：epoch 边界处的 sidecar 是**刻意清空**的（§4.3 adapter 侧）。因此若 checkpoint 恰好落在边界之后，其快照中的 `committed_snapshot()` 为空是**正确状态**，resume 不得把它当成「数据缺失」而回填；`canonical_segment_runtime.py:184-189` 的两条校验在空前沿下自然成立。

---

## 6. 验收判据

**PASS**（全部满足）：

1. **契约一致性（CPU）**：epoch 推进后，每个 slot 的 `_by_slot[slot]` 等于「按 `(source_digest, episode_id)` 排序 → 应用 `queue_permutation(queue_seed, epoch, category, catalog_size)` → 取该 slot 子序列」的结果，**逐位一致**；`queue_epoch` 恰好 +1；且参照序与 `_queue_for`（含其**字符串**比较语义）一致。
2. **容量解除（CPU，纯规划层）**：用 `probe_block_capacity.py` 的 producer 搭建同一套 catalog，在**不取任何张量**的前提下连续推演窗口规划越过 epoch 边界，断言：①可连续规划出 **≥ 5040** 个窗口（45 epoch × 112）而不再 `raise`；②第 113 个窗口成功规划；③跨 epoch 无 identity 被 `commit` 的守卫拒绝。
3. **原子性**：断言窗口边界的探测**不修改** driver 状态（探测前后 `_stream_index`/`_active_stream`/`_active_cursor` 逐位相同），且探测所用的剩余量规则与实际 `freeze_window` 共用同一实现。
4. **触发规则的两侧**：①剩余 ≥ `window_members` 时**不**推进 epoch；②剩余 < `window_members` 时推进；③推进后 `_window_index` **不**重置（递增值连续）。
5. **尾块不丢失**：跨 epoch 后，断言上一个 epoch 被推迟的尾块在新 epoch 中被 `commit` —— 即按 epoch 分别统计的 `committed_identities` 覆盖全部 14430 个 block 身份至少一次（epoch 0 覆盖 14336，epoch 1 覆盖其余 94 + 14336 中的一部分）。
6. **GPU 端到端**：短跑越过一个 epoch 边界，断言无 `raise`、loss 有限、`cumulative_valid_consumer_exposure` 单调不减（不清零）。

   **措辞更正（v0.3）**：本判据 v0.2 原文写作「`per_slot_members` 在每个窗口内仍为 8 个 slot 均衡」。**该措辞在今天就已为假，与本设计无关**：`freeze_window` 只按 category 的 exposure 赤字挑选，而每个 category 的 block 供给量不同，因此**任何 category 一旦抽干，其两个 slot 就从该窗口消失**。实测（§10.4）：epoch 0 自第 **80** 个窗口起就不再覆盖全部 8 个 slot。

   **第二处更正（v0.4）**：v0.3 给出的替代形式是「对**在该窗口实际被服务**的 category，其两个 slot 的成员数之差 ≤ 1」（§10.4 的 `max_within_category_slot_skew`），并拟把它升为**通过条件**。

   **第三处更正（v0.5，实测判定：该形式已撤回）**：v0.4 只把该项**降级为记录量**，理由是「全局值 `64` 未按 epoch 分离，无法判断 epoch 0 单独是否 ≤ 1」。现已跑出单 epoch 基线（`probe_epoch_reuse_planning_epoch0.json`，`--max-epochs 1`）：**epoch 0 的 `max_within_category_slot_skew = 32`**（上限 128）。⟹ **该形式在今天就已为假**，若升为 PASS 条件，则会成为一条「今天的生产行为就已经不满足」的判据——**与 v0.2 原文属同一类缺陷**（把今天不成立的性质写成判据）。故**该形式整体撤回，不再作为判据，也不再作为 v0.3 意义上的「候选通过条件」**；`max_within_category_slot_skew` 仅作为**记录量**保留。

   本判据的 GPU 部分因此只保留两条**已核实可判定**的断言：「loss 有限」与「`cumulative_valid_consumer_exposure` 单调不减」。

   **v0.4 新增的记录量（非通过条件）**：`windows_by_distinct_slots` / `windows_by_distinct_categories` / `all_slots_windows` / `all_categories_windows`。45 epoch 读数、epoch 0 基线读数与两者对照见 §10.4——其中 epoch 0 与 epochs ≥1 的窗口构成**相反**，这是本设计当前最大的未决技术问题（§8 第 7 点）。
7. **resume 交叉（在 resume 落地后）**：在 epoch ≥ 1 处存盘并 resume，断言 `_catalog_epoch` 与 `queue_epoch` 一致恢复、续跑窗口序列与不中断跑一致。
8. **sidecar 重置（v0.3 新增，CPU）**：构造一个「slot 末次 commit 非 terminal」的边界（即 `probe_catalog_epoch_boundary.json` 中 slot 4 的形态），断言 rollover 后 `adapter.sidecar` 对**每个 slot** 的 `read` 都返回 `None`（而非抛 `ValueError`）；并断言重置只经既有 API（§4.7 的裁定结果）。**该判据必须在取张量之前可跑**——因为失败形态是 `scan` 内的 `read` 抛错，等到取张量时才发现代价过高。
9. **per-epoch observed 恢复形态（v0.6 新增，选 (a)，CPU 纯规划层）**：连续推演 ≥ 2 个 epoch，断言**每个** epoch 的窗口类别构成与 epoch 0 逐 epoch 一致（`windows_by_distinct_categories`/`windows_by_distinct_slots` 逐 epoch 相等），而非 v0.5 实测的「epochs ≥1 塌缩为 75.3% 单 suite」；且 `_epoch_observed` 在每次 rollover 后归零、`cumulative_valid_consumer_exposure` 单调不减（仍作报告量）。
10. **queue_seed/queue_epoch resume 一致性（v0.6 新增，选 (b)）**：resume 后 `queue_seed` 与存盘时逐位一致、`queue_epoch` 恢复为存盘值（不与不中断跑偏移），重排结果与不中断跑对应 epoch 一致。

**FAIL**：epoch 边界推进后出现 identity 守卫拒绝；或探测修改了 driver 状态；或重排结果与 §4.4 规则不一致；或 `cumulative_valid_consumer_exposure` 被清零；或推迟的尾块在新 epoch 中未被覆盖；或 rollover 后有 slot 的 sidecar `read` 抛出 `ValueError`；或 `_epoch_observed` 未在 rollover 归零、`freeze_window` 仍读累计字段（选择键未切换到 per-epoch observed）；或 epochs ≥1 的窗口构成仍与 epoch 0 相反。

**BLOCKED**：若 §3.2 的触发规则在真实链路上仍不可用（例如第 113 个窗口仍 `raise`，或跨 epoch 出现 identity 守卫拒绝而无法通过重置清单解决），则本设计不落地，须改为「按 slot 独立推进 epoch」（代价见 §3.3）。

---

## 7. 禁止范围

- 不改 `SegmentIdentity` / `GAWindowPlan` / `SegmentBatch` 的 ABI 与字段。
- 不改 `admit` / `commit` / `terminal_rebind` 的守卫条件本身（本设计只重置它们所依赖的**状态容器**，不改判定逻辑）。
- 不改 `LocalMemorySegmentSidecar.read` 的守卫（`:34-36` 的 `raise`）与 `commit` 的 pop 语义（`:40-42`）；rollover 只调用既有的 `reset`（`:45-46`）。
- 不改 `queue_digest_preimage` / `queue_permutation` 的字节序（契约已冻结，有 `PSM-WMA/queue/v1` 版本标记）。
- 不改 `canonical_segment_adapter_scheduler.py`（它是冻结的 CPU/static 契约模型；本设计只在 driver 侧定义触发规则）。
- 不新增 DCP 顶层 key（`dcp.py:939` 会拒绝）。
- 不重建 catalog、不重新读取数据集、不改 `on_train_start` 的构建路径。
- 不为 identity 增加 epoch 维度。
- 不在 `freeze_window` 的 `raise` 点做重置（非原子，见 §4.1）。

**显式放宽（v0.6，选 (a) 所致）**：本设计**允许**改 `freeze_window` 的选择键中 `observed` 的**来源**（由 `scheduler.cumulative_valid_consumer_exposure` 改为 driver 侧 `_epoch_observed`），其余选择逻辑（`target[category] - observed`、tie-break `(category, -used)`）不变。这是 §8 第 7 问裁定 (a) 的直接后果；除这一条外，上述所有禁止项不变。

---

## 8. 请求 verdict（v0.6 起技术决策已闭合）

**v0.6 起，以下七点不再待裁定**：第 7 问按 DS `REQUEST_CHANGES` 主因与 MM「不可悬置」意见裁定为 (a)，其余各问按 §0 修订记录闭合（第 3 问由本设计自查给出答案）。现仅列出各点的最终决策，供复核而非首答：

1. **§3.2 的界条件**：维持「契约只定义语义、driver 侧实现」——**不改契约文件**（`canonical_segment_adapter_scheduler.py` 是冻结 CPU/static 契约模型，§7 禁止范围）。§3.2 的触发规则在 driver 侧定义，语义上是契约条件 1 的忠实类比（§3.2），契约条件 2 因 §4.3 重置而多余（§3.3）。
2. **§4.4 的重排规则**：正确。参照序用**字符串** `episode_id` 比较（`_queue_for` 的 `:477` 语义），实现严禁用 `int()` 数值排序——这是最易错点，§6 判据 1 已把「与 `_queue_for` 含字符串比较语义一致」列为验收。
3. **§4.3 的重置清单**：自查结论「有且只有 sidecar 一处」**成立**（依据见下，与 v0.3 相同）。
4. **§5 的顺序判断**：成立。本设计实现排在 resume 落地之后；resume 设计 §6 判据无需因本设计修改（其判据 4 的 GPU 短跑 `save_iter=50<112` 落在单 epoch 内）。
5. **§4.6 `queue_seed` 来源**：选 **(b)** 由 catalog 身份派生；§6 已新增判据 10 验证 resume 后 `queue_seed`/`queue_epoch` 与存盘一致。
6. **§4.7 sidecar 重置归属**：选 **(b)** `owner` 新增 rollover 入口 `discard_committed_carry()`；与 resume 的 `canonical_segment_runtime.py` 改动以一次协调 commit 完成。
7. **【v0.6 裁定为 (a)】** v0.3 曾把「窗口覆盖度偏斜」定性为**既有性质**（「epoch 0 与之后各 epoch 逐位相同」），并据此请 Gate 裁定「是否作为既有行为接受、单独开 Gate」。**45 epoch 满跑推翻了该定性的前提**：
   - epoch 0 有 **81/112** 个窗口服务全部 4 个 category；**epochs 1–44 该计数为 0**（`first_partial_category_window` 恒为 1）。
   - **≥ 75.3% 的窗口只服务 1 个 suite**（严格下界，推导见 §10.4），而 epoch 0 是 72.3% 的窗口服务全部 4 个 suite。
   - 根因是 `cumulative_valid_consumer_exposure` **同时是 `freeze_window` 的控制输入**（选择键 `target - observed`），而它在 rollover 时被刻意保留（§4.3）。

   故这**不是**「把既有行为重复 45 次」，而是**让 44/45 的训练步运行在一个今天从未运行过的 regime 里**。**裁定**：
   - **(a) ✅ 采纳**：把「rollover 时同步另起 epoch 内的 observed 计数器（累计字段仍保留作报告量）」纳入范围，触及 `freeze_window` 的选择键（§7 已显式放宽这一条）。
   - **(b) 驳回**：不接受把「epochs ≥1 的 75.3% 窗口为单 suite」作为已知代价（DS 主因「不应作为已知代价接受」）。
   - **(c) 已闭合**：§6 判据 6 的更正形式已由单 epoch 基线判定整体撤回（v0.5）。

---

## 9. 实现记录

**当前 operative 行为**：catalog 耗尽时 `freeze_window` fail-closed `raise`（`active_local_memory_driver.py:230-231`）。**D8b 长跑（5000 步）不得在此状态下启动**——会在第 113 步 crash，白耗约 8 小时。

本文档为**设计**，尚无对应代码改动；实现与证据将在 Gate 裁定后补入本节。

---

## 10. 实测证据

三组证据：**10.1 边界可达性**（v0.2）、**10.2 sidecar 必然抛错的最小复现**（v0.3）、**10.3 规划层容量解除**（v0.3）。

### 10.1 边界可达性（v0.2）

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

### 10.2 sidecar 必然抛错的最小复现（v0.3）

不需要任何数据集或张量即可复现 §4.3 adapter 侧的论证——`LocalMemorySegmentSidecar` 是独立类：

```python
from cosmos_framework.model.generator.mot.local_memory_segment_adapter import LocalMemorySegmentSidecar
from cosmos_framework.model.generator.mot.local_memory_segment import SegmentIdentity
from cosmos_framework.model.generator.mot.local_evidence import ContinualTTTFastState

def ident(ep, cur, end):
    return SegmentIdentity(slot_id=4, episode_id=ep, category="libero_10", cursor=cur,
                           segment_id=cur, source_digest="d", training_stream_end=end)

sc = LocalMemorySegmentSidecar()
sc.commit(ident("7", 3, False), ContinualTTTFastState(*(torch.ones(1, 1) for _ in range(4))))  # epoch 0 末次非 terminal
sc.read(ident("7", 0, False))   # -> ValueError: segment sidecar identity is not a canonical continuation.
sc.read(ident("9", 0, False))   # -> ValueError（不同 episode 走同一条拒绝路径）
sc.reset(ident("7", 3, False))
sc.read(ident("7", 0, False))   # -> None
```

实测输出（`cosmos-framework/.venv/bin/python`，2026-09-17 01:27）：

```
记录已存: True
  同 episode 的 cursor 0: ValueError -> segment sidecar identity is not a canonical continuation.
  不同 episode 的 cursor 0: ValueError -> segment sidecar identity is not a canonical continuation.
reset 后 read 返回: None
```

**结论**：新 epoch 首块是 `cursor 0`，与记录必然不构成「前一身份 + 1」的延续，**与重排结果无关**；因此 §4.3 adapter 侧的重置不是「保险措施」而是**必需动作**，缺它则第二个 epoch 的第一个 member 即在 `scan` 内抛出。

### 10.3 规划层容量解除（v0.3，判据 2 的完整证明）

探针 `tools/g0/probe_epoch_reuse_planning.py` 用**与 §10.1 同一套生产 catalog**，在不取任何张量（`producer.produce` 从不调用）的前提下连续推演窗口规划越过 epoch 边界。rollover 是**探针内的参考实现**（§4.3/§4.4），生产文件 `active_local_memory_driver.py` **未被改动**。

```
LIBERO_ROOT=/disk/rl/data/LIBERO_LeRobot_v3 \
LIBERO_LATENT_CACHE_ROOT=/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1 \
  cosmos-framework/.venv/bin/python tools/g0/probe_epoch_reuse_planning.py \
  --max-epochs 45 --target-windows 5040 \
  --output-json artifacts/g0/active_static_probe/probe_epoch_reuse_planning.json
```

读数（`probe_epoch_reuse_planning.json`）：

| 项 | 读数 |
|---|---|
| `result` | **PASS** |
| `epochs_planned` | 45 |
| `windows_total` | **5040**（= 45 × 112，正是 §3.4 的容量换算） |
| `windows_per_epoch` | 45 项，**唯一值 = 112**（每个 epoch 恰好 112 个窗口，无长尾、无短窗） |
| `single_epoch_limit` | 112.73 |
| `criterion1_slot_order_matches_permutation` | **true**（`criterion1_mismatches = []`） |
| `criterion2_meets_target` / `criterion2_exceeds_single_epoch` | **true** / true |
| `criterion3_probe_is_pure` | **true**（探测前后 `_stream_index`/`_active_stream`/`_active_cursor` 逐位相同） |
| `criterion4_window_index_not_reset` | **true**（`window_index = 5040 = windows_total`） |
| `criterion5_deferred_tail` | `deferred_after_epoch0 = 94`，`recovered_in_epoch1 = 94`，`missing_from_epoch1 = []` |
| `rollovers` | 44 次，`remaining_blocks_at_rollover` **唯一值 = 94**，`windows_in_previous_epoch` **唯一值 = 112**，`queue_epoch` 单调 1→44 |
| `committed_identities` | 14336（= 单 epoch 上界；容器每 epoch 清空，故不随 epoch 累积） |

**该表的三点含义**：

1. **判据 2 完整成立**：第 113 个窗口不再是边界（§10.1 的 `raise` 不再出现），且连续 5040 个窗口全部规划成功——**容量缺口 44.4 倍被解除**。
2. **每个 epoch 都是恰好 112 个窗口、残留恰好 94 块**，45 个 epoch 无一例外。这说明 §3.2 的界条件在真实 catalog 上稳定可复现，不是「碰巧第一次成立」。
3. **复用不引入新的调度开销**：`admit`/`commit` 的守卫成员检查是 **list 线性扫描**（`local_memory_segment.py:322-323`），单次 `commit` 成本随 `len(admission_order)` 线性增长。实测（真实 `RankLocalSegmentScheduler`）：N=2000 时 415 µs，N=14336 时 1261 µs，单 epoch 累计约 **9 s**。因 rollover **清空** `admission_order`/`committed_identities`，该 O(n²) 的 n 上界**恰好等于今天单 epoch 的值**——45 个 epoch 合计约 6.8 min，相对 5000 步训练的墙钟可忽略。**这是「清空守卫容器」这一设计的附带收益**，也是本设计不新增接口、不改 `commit` 的代价上界。

### 10.4 窗口构成：复用**不是**「epoch 0 重复 45 次」（v0.4 重写；v0.5 补 epoch 0 单独基线）

**本节 v0.4 重写的原因**：v0.3 的 §10.4 依据 2 epoch / 224 窗口的冒烟数据写下了两处推断，45 epoch 满跑（`probe_epoch_reuse_planning.json`，5040 窗口）**将其证伪**。两处推断及其推翻依据如下，一并保留以示修订链条：

| v0.3 的表述 | v0.4 实测结论 |
|---|---|
| 「epoch 0 的形态与之后 44 个 epoch **逐位相同**」 | **假**。只有**聚合量**相同（`windows_per_epoch` 全 112、`remaining_blocks_at_rollover` 全 94）；**窗口内部构成完全不同**：epoch 0 有 81 个窗口服务全部 4 个 category，epochs 1–44 的这一计数**为 0**（`first_partial_category_window` 恒为 1）。 |
| 「尾部窗口 100% 给 libero_10」，51 个 2-slot 窗口来自该尾部 | **算术上不可能**。51 × 128 = 6528 > libero_10 每 epoch 的全部消耗 5626。该推断把「2 个 slot」等同于「1 个 category」，而 2 个 slot 也可能来自两个各剩 1 slot 的 category。 |

**45 epoch 满跑的实测读数**（`criterion6_slot_coverage` / `tail_structure`）：

| 项 | 读数 |
|---|---|
| `windows_by_distinct_slots` | `{2: 3826, 3: 51, 4: 1019, 5: 7, 6: 56, 7: 2, 8: 79}` |
| `windows_by_distinct_categories` | `{1: 3826, 2: 1070, 3: 63, 4: 81}` |
| `all_slots_windows` | **79 / 5040 = 1.6%** |
| `all_categories_windows` | **81 / 5040 = 1.6%**（全部落在 epoch 0） |
| `max_within_category_slot_skew` | **64**（上限 128） |
| epoch 0 | `first_partial_window = 80`、`first_partial_category_window = 82` |
| epochs 1–44 | `first_partial_window = 1`、`first_partial_category_window = 1`（**无一窗口覆盖全部 category**） |
| `remaining_by_category_at_epoch_end` | 45 个 epoch **全部**为 `libero_10 = 94`，其余三个 `= 0` |

**单 suite 窗口占比的下界（由直方图严格推出，非估计）**：被服务的 category 实例数 = 1×3826 + 2×1070 + 3×63 + 4×81 = **6479**；实际 distinct slot 实例数 = 2×3826 + 3×51 + 4×1019 + 5×7 + 6×56 + 7×2 + 8×79 = **12898**。若每个被服务的 category 都出满 2 个 slot，应为 2 × 6479 = 12958，**缺口 60**——即全窗中「某 category 只出 1 个 slot」共发生 60 次（与**奇数 slot 窗口数 51 + 7 + 2 = 60** 精确吻合，互为交叉验证）。2-slot 窗口若为「2 category × 1 slot」则每个耗 2 个缺口，故这类窗口**至多 30 个**。直方图不含 1-slot 窗口，故所有 1-category 窗口都落在 2-slot 桶内。于是：

> **单 suite 窗口 ≥ 3826 − 30 = 3796，即 ≥ 3796 / 5040 = 75.3% 的窗口只服务 1 个 suite。**

对照 epoch 0（=今天的单 epoch 行为）：72.3% 的窗口服务全部 4 个 suite、79/112 覆盖全部 8 个 slot。**两者是相反的构成。**

**成因（已核实的机制）**：`freeze_window` 的选择键是 `(target[category] - observed, category, -used)`（`active_local_memory_driver.py:227-232`），**只看 exposure 赤字，不看该 category 还剩多少 block**。而 `observed` 取自 `cumulative_valid_consumer_exposure`——**本设计刻意不清零的那个字段**（§4.3）。于是：

1. **epoch 0**：四个 category 的赤字从零开始同步增长，窗口内四类并存 ⟹ 形态健康（79 个满 8-slot 窗口）。
2. **rollover 后**：`_by_slot` 与游标全部重置（供给恢复到 14430 块），**但 `observed` 保留**，故 epochs ≥1 开局即继承 epoch 0 结束时的偏斜赤字（libero_10 占 39.2%，赤字深度为负；另三类为正）。赤字为正的类别被连续服务直到抽干，libero_10 因赤字最负而被推迟 ⟹ 每个窗口塌缩到单一 category 的 2 个 slot。

**因此 `cumulative_valid_consumer_exposure` 不只是「报告量」，它同时是 `freeze_window` 的控制输入。** v0.3 曾论证「偏差成因是供给约束而非不清零」——**该论证只对 epoch 0 成立**；对 epochs ≥1，实测显示不清零本身即是构成塌缩的直接原因：供给约束决定「每 epoch 尾部谁先抽干」，而不清零决定「每个窗口是 4 类并存还是 1 类独占」。

**供给侧的定量对照**（两份独立产物的交叉验证）：每 epoch 消费 `libero_10 5626 / libero_goal 2588 / libero_object 3480 / libero_spatial 2642`，对照 `probe_block_capacity.json` 的 `per_category_blocks = {libero_10: 5720, libero_goal: 2588, libero_object: 3480, libero_spatial: 2642}` ⟹ 后三类消费量**恰好等于其总供给**（被完全抽干），libero_10 消费 5720 − 94 = 5626。另外 `per_slot_blocks` 显示**同类两 slot 的供给本身就不等**（goal 1255/1333，差 78；spatial 1329/1313；object 1741/1739；libero_10 2865/2855）。其中最小值 1255 ÷ 16（每 slot 每窗口的成员数）= **78.44**，与容量探针的 `windows_until_first_slot_drained = 78.44` **逐位吻合** ⟹ epoch 0 的 `first_partial_window = 80` 是**由供给推出来的**（第 79 窗仍用掉该 slot 剩余的 7 块，第 80 窗起为 0），不是观测巧合。

**e2e exposure 偏斜**：45 epoch 后 `cumulative_valid_consumer_exposure` = `libero_10 4050720（39.2%）/ libero_goal 1863360（18.1%）/ libero_object 2505600（24.3%）/ libero_spatial 1902240（18.4%）`，目标为各 25%。

**这对本设计的意义（v0.6 已裁定为 (a)）**：v0.3 把 39.2% 的偏斜定性为「**既有性质被复用放大**」，据此建议可「作为既有行为接受、单独开 Gate」。**实测推翻了该定性的前提**——epochs ≥1 与 epoch 0 的窗口构成相反，故这不是把既有行为重复 45 次，而是**让 44/45 的训练步运行在一个今天从未运行过的 regime 里**（75.3% 的 batch 只含一个 suite）。一个自然的候选修法是：**保留累计字段作为报告量，但让 `freeze_window` 的赤字改用 per-epoch 的 observed**（即 rollover 时另起一个 epoch 内计数器）——这样 epochs ≥1 的形态会与 epoch 0 相同（每 epoch 79 个满 slot 窗口）。**该候选修法已于 v0.6 采纳为第 7 问裁定 (a)**（§4.1、§4.3、§7、§8），累计字段 `cumulative_valid_consumer_exposure` 保留仅作报告量，`freeze_window` 选择键改用 driver 侧 `_epoch_observed`。

**epoch 0 单独基线与它的对照（v0.5 补测）**：上表最末一项曾被标为「未按 epoch 分离，无法判断 epoch 0 单独是否 ≤ 1」。现已单跑 epoch 0（`probe_epoch_reuse_planning_epoch0.json`，`--max-epochs 1`，`result=PASS`，`windows_total=112`）：

| 项 | epoch 0 单独 | 45 epoch 全体 |
|---|---|---|
| `max_within_category_slot_skew` | **32** | 64 |
| `windows_by_distinct_categories` | `{1: 16, 2: 13, 3: 2, 4: 81}` | `{1: 3826, 2: 1070, 3: 63, 4: 81}` |
| `windows_by_distinct_slots` | `{2: 16, 4: 13, 5: 1, 6: 1, 7: 2, 8: 79}` | `{2: 3826, 3: 51, 4: 1019, 5: 7, 6: 56, 7: 2, 8: 79}` |
| `all_slots_windows` / `all_categories_windows` | 79 / 81（共 112） | 79 / 81（共 5040） |
| `first_partial_window` / `first_partial_category_window` | 80 / 82 | 80（epoch 0）→ 1（epochs ≥1） |
| `remaining_by_category_at_epoch_end` | `{libero_10: 94, 其余: 0}` | 同（45 个 epoch 全部） |

**两项决定性读数**：

1. **`max_within_category_slot_skew = 32` 在 epoch 0 单独就已成立**（不是 1）。⟹ §6 判据 6 的更正形式（「同类两 slot 成员数之差 ≤ 1」）**在今天就已为假**，故已整体撤回（§6 第三处更正）。
2. **单 suite 窗口占比：epoch 0 = 16/112 = 14.3%，epochs 1–44 = (3826 − 16)/44 = 86.6/epoch = 77.3%**（后者的分母 112，分子取全体 1-category 窗口数 3826 减去 epoch 0 的 16）。**同一指标相差 5.4 倍**，且 epoch 0 有 81 个「4 类并存」窗口而 epochs ≥1 为 0。这以最直接的方式量化了「复用改变了训练 regime」，而非「重复了同一个 regime」。

**尚未测的边界（v0.6 起纳入验收）**：`epochs 1–44` 内部的逐 epoch 差异尚未分离（上表把它们合并计数）；`tail_structure` 只保留前 5 个 epoch。**v0.6 判据 9（选 (a)）已把「per-epoch observed 使每个 epoch 的窗口构成与 epoch 0 逐 epoch 一致」列为验收**，届时需把 `tail_structure` 全量（或逐 epoch 直方图）落盘并跑一次；本设计定稿时尚未测（实现后补 §9）。
