# Local Memory v0.3.5 Active-Window Slot Rotation 修复设计 v0.1

- Gate：`G0-R09-B-TTT-V035-ACTIVE-WINDOW-SLOT-ROTATION`
- formal root：`5d527f3ea8db25f23482c9a3e13b5c7ca2fd6a99`
- child/Gitlink：`6dc25e0f8c3ba39525c8ba994b8d0c38c2ce5461`
- 目标文件：`cosmos_framework/model/generator/mot/active_local_memory_driver.py:214-229`
- 状态：**已实现，待审**。实现先经「fixture 先证伪 → 再落地 → 生产链路复验」，全部证据见 §9。
- 修订（v0.1 → 本文头部校正，2026-09-17）：头部早前误写 `formal root=3065bc8a` / `child=81fa342d`（设计定稿时的会话 HEAD 与修复前 Gitlink），已按 DS 意见改正为送审件实际提交 `5d527f3e` / child `6dc25e0f`；设计正文 §1–§9 无改动。

---

## 1. 问题

`ActiveLocalMemoryWindowDriver.freeze_window()` 的 weighted-deficit 选取在**同一 category 内恒定偏向 `slot_id` 较大者**，导致 `b_stream=8` 中恰有一半 slot（0/1/2/3）在**任何** window 中都不会被选中。

### 1.1 生产链路实测（决定性证据）

用真实 dataset（`LIBERO_LeRobot_v3` + `LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1` 精确窗口 latent cache）、真实 `CanonicalLocalMemorySegmentProducer`、真实 `canonical_segment_streams` 构造真实 `ActiveLocalMemoryWindowDriver`，直接调用生产代码的 `freeze_window()`（CPU-only，无 GPU、无 checkpoint、无 trainer）：

```
window_members = b_stream * ga = 8 * 16 = 128
ga_effective = 128
window_per_slot_members    = {4: 32, 5: 32, 6: 32, 7: 32}      ← slot 0/1/2/3 恒为 0
window_slots_used          = [4, 5, 6, 7]
window_slots_starved       = [0, 1, 2, 3]
per_slot_total_blocks      = {0:2865, 1:1255, 2:1741, 3:1329, 4:2855, 5:1333, 6:1739, 7:1313}
per_slot_catalog_streams   = {0:188, 1:212, 2:225, 3:214, 4:187, 5:212, 6:224, 7:214}
slot_sequence[:32]         = [7,6,5,4] × 8                       ← 完美轮转，0-3 永不入选
per_category_members       = {libero_10:32, libero_goal:32, libero_object:32, libero_spatial:32}
```

### 1.2 量化后果

| 项 | 现值 |
|---|---|
| 饿死 slot 独占 block | 7190 / 14430 = **49.83%** |
| 每 suite episode 覆盖率 | **50%**（`canonical_segment_streams:166,176` 把每个 suite 的 episode round-robin 对半分给该 suite 的 2 条 slot，如 libero_spatial slot3=214 / slot7=214） |
| 可达唯一 block / window 数上限 | 7240 / **56.6 window ≈ 7240 步**（修复后 14430 / 112.7 ≈ 14430 步） |

正式训练计划约 5000 步。7240 步的容量**刚好够用**，因此**不会崩溃、不会报错、loss 正常**——它会静默地用一半 episode 训完整个训练。这是本缺陷最危险之处。

### 1.3 根因

```python
# active_local_memory_driver.py:221-225  现状
observed = exposure.get(stream.category, 0) / max(sum(exposure.values()), 1)
choices.append((target[stream.category] - observed, stream.category, slot_id, view))
...
_, category, slot_id, view = max(choices, key=lambda item: item[:3])
```

deficit 在 `:221` 是**按 category** 计算的，因此同一 suite 的两条 slot（如 slot 4 与 slot 0，同属 `libero_10`）拥有**恒等的 deficit**；`max` 的 tie-break 落到第三项 `slot_id`，**恒取较大者**。`canonical_segment_streams:166` 的 `slot % len(categories) == index` 分配保证同一 category 恰好占两条 slot，故该 tie 在每个 window、每一次选取都发生。

---

## 2. 为什么这是实现缺陷，而非 v0.3.5 冻结语义

### 2.1 规范只约束 category 级配额

`docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.2.md:86`：

> 随后下一 projected member 才按 **weighted deficit 为 free slots 选 category** 与该 category 当前 epoch 的最前 eligible entry。……同一 epoch 内 **weighted deficit 仅对 free slot 新 admission 选择 category**；已绑定 slot 必须同 episode、同 digest、`cursor+1` 连续推进。

`docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md:229` 同义。

规范把 deficit 定义为 **category 之间的配额平衡**，并把「同 category 内如何取」规定为「该 category 当前 epoch 的**最前 eligible entry**」。规范**从未**把 tie-break 定义为「恒取 `slot_id` 大者」，更未授权任何 slot 永久饿死。

### 2.2 active 路径上 `scheduler.admit()` 的多候选 tie-break 根本不被行使

`production_active_wiring.py:88` 传的是 **singleton 候选** `owner.admit_next((identity,))`；`canonical_segment_runtime.py:98-111`：

```python
member = self.transaction.plan.members[index]
eligible = tuple(item for item in candidates if (item.slot_id, item.episode_id, item.cursor) == member)
if len(eligible) != 1:
    raise RuntimeError("next admission must follow the frozen plan")
identity = self.scheduler.admit(eligible)
```

候选先按冻结计划第 `index` 个成员过滤，要求恰好 1 个匹配，再交给 `scheduler.admit()`。**单候选下 `max` 平凡返回该候选**，故 `RankLocalSegmentScheduler.admit()` 的多候选 tie-break **在 active 路径上不被行使**：`freeze_window` 的顺序即唯一权威。

因此本修复可**完全自包含于 `freeze_window`**，不触及 owner / scheduler / sidecar / `GAWindowPlan` 任何冻结接口。

### 2.3 现实现违反本 Gate 家族已有的 (B) 裁决所依赖的前提

`docs/build/PSM-WMA_Local_Memory_v0.3.5_functional_active_route_implementation_design_v0.1.md:129-138` 裁决 (B) 的**理由 #1** 是：

> **(A)/(B) 数值等价。** ……故 8 行 batched 与 8 次单行在数值上一致。差别只在吞吐，不在语义。

而 (A) 的一个 member 持有 `B_stream` 行（`MicrobatchPlanMember.row_identities`，`:107-110`），即 8 行来自 **8 条不同 slot**。要使 (B) 的「同 window 内 8 个连续 member」与 (A) 数值等价，这 8 个连续 member 必须覆盖**同样这 8 条 slot**。

现实现下 8 个连续 member 为 `[7,6,5,4,7,6,5,4]`——**只跨 4 条 slot、各重复 2 次**，且整个 window 完全不见 slot 0-3。这**不满足** (B) 裁决理由 #1 所断言的数值等价：它不是 (A) 的等价重排，而是**另一个更小的数据集**。

即：本修复不是「改变 (B) 语义」，而是**恢复 (B) 裁决所依赖的前提**。修复后 `8 slot × 16 = 128 = b_stream × ga`，每 8 个连续 member 恰好来自 8 条不同 slot 流。

> **请 Gate 一并裁定**：§2.3 的解读（(B) 要求每 8 个连续 member 跨 8 条不同 slot）是否正确。若 Gate 认为 (B) 只要求「member 数为 `8*GA`」而不要求跨 8 条流，则本缺陷的定性应降为「数据覆盖缺陷」而非「ABI 契约违反」——**但修复动作与判据不变**。

---

## 3. 最小补丁

仅 `active_local_memory_driver.py:214-229`，新增 1 行、改 2 行：

```diff
         exposure = dict(scheduler.cumulative_valid_consumer_exposure)
         members: list[ActiveWindowMember] = []
         identities: list[SegmentIdentity] = []
+        used: dict[int, int] = {}
         for _ in range(self.window_members):
-            choices: list[tuple[float, str, int, tuple]] = []
+            choices: list[tuple[float, str, int, int, tuple]] = []
             for slot_id in self._by_slot:
                 view = self._peek_block(slot_id)
                 if view is None:
                     continue
                 stream, _cursor, _terminal, _rebind, _position = view
                 observed = exposure.get(stream.category, 0) / max(sum(exposure.values()), 1)
-                choices.append((target[stream.category] - observed, stream.category, slot_id, view))
+                choices.append(
+                    (target[stream.category] - observed, stream.category, -used.get(slot_id, 0), slot_id, view)
+                )
             if not choices:
                 raise RuntimeError("active Local window exhausted every segment stream")
-            _, category, slot_id, view = max(choices, key=lambda item: item[:3])
+            _, category, _used, slot_id, view = max(choices, key=lambda item: item[:3])
             stream, cursor, terminal, rebind, position = view
             self._commit_block(slot_id, stream, cursor, position)
+            used[slot_id] = used.get(slot_id, 0) + 1
             exposure[category] = exposure.get(category, 0) + planned
```

语义：tie-break 第三项由 `slot_id` 改为 `-used[slot_id]`（**本 window 内**该 slot 已被选中次数）。同一 category 内的两条 slot 交替入选；跨 category 仍完全由 deficit 决定。

`used` 的作用域是单次 `freeze_window()` 调用，**不跨 window 持久**，故不引入新的 driver 状态、不影响 `RESUME-ACTIVE-DRIVER-STATE` 的缺口面（该缺口独立存在，见 TODO）。

---

## 4. 不变性论证

| 性质 | 论证 |
|---|---|
| **category 配额不变** | deficit 仍在 `exposure[category]` 上按 category 累计、每次 `+= planned`，与选取了哪条 slot 无关。实测 `per_category_members` 修复前后均为各 32。 |
| **`ga_effective` 不变** | 循环次数仍为 `self.window_members`。实测 128 → 128。 |
| **`GAWindowPlan.members` 形状不变** | 仍为 `8*GA` 项、仍为 `(slot_id, episode_id, cursor)` 三元组；`ActiveWindowFreeze.__post_init__` 的对齐校验仍成立。 |
| **`_is_admissible` 连续性成立** | 已绑定 slot 要求 `cursor == previous.cursor + 1`。交替选取下每条被选中的 slot 仍逐次 `cursor+1`（本 window 每 slot 恰推进 16 次）。 |
| **admission 兼容** | singleton 候选路径（§2.2）只校验候选等于冻结计划成员，故 freeze 顺序被无条件接受。 |
| **既有测试不回归** | `active_local_memory_driver_test.py:138` 的 `test_slot_rotation_follows_the_scheduler_deficit_rule` 用两个**不同** category（slots 0/1 分属 a/b），deficit 不等，tie 不发生；补丁下序列仍为 `["b","a"]`。（已按补丁逻辑手工推演：`a` 0.5-0=0.5 vs `b` 0.5-0=0.5 → tie 由 category 名决出 `b`；随后 `b` 的 observed=2/2=1 → deficit -0.5，`a` 仍 0.5 → 选 `a`。） |
| **ABI 冻结面** | 不触碰 `SegmentIdentity`、`RankLocalSegmentScheduler`、`LocalMemorySegmentSidecar`、`CanonicalSegmentRuntimeOwner`、`ProductionActiveWiringRegistry`、`GAWindowPlan` 的任何字段或方法签名。 |

---

## 5. 测试缺口与拟增 fixture

### 5.1 缺陷为何能溜过既有测试

`active_local_memory_driver_test.py` 中唯一涉及 slot 轮转的用例是 `:138` 的 `test_slot_rotation_follows_the_scheduler_deficit_rule`，它构造的是 `_FakeStream(0,1,"a")` 与 `_FakeStream(1,2,"b")`——**两条 slot 分属不同 category**。而生产形态是 `b_stream=8` 覆盖 4 个 category，**同一 category 恒有两条 slot**。既有 fixture **从未构造过同 category 多 slot 的情形**，故 tie-break 分支从未被覆盖。

### 5.2 拟增 fixture（随补丁落地，加在 `active_local_memory_driver_test.py`）

```python
def test_slot_rotation_covers_every_slot_sharing_one_category() -> None:
    """同一 category 的两条 slot 必须在一个 window 内交替入选。

    生产形态 b_stream=8 / 4 categories 使每个 suite 恒有两条 slot
    (slot % len(categories) == index)，故该分支是唯一的生产分支。
    """
    producer = _FakeProducer()
    producer.blocks[(0, 1)] = 4
    producer.blocks[(4, 2)] = 4
    driver = _driver(
        _registry({"suite": 1.0}),
        producer,
        (_FakeStream(0, 1, "suite"), _FakeStream(4, 2, "suite")),
        window_members=4,
    )

    freeze = driver.freeze_window()

    slots = [identity.slot_id for identity in freeze.identities]
    assert set(slots) == {0, 4}            # 修复前恒为 [4, 4, 4, 4]
    assert slots == [4, 0, 4, 0]           # 交替，而非由 slot_id 大者独占
    assert [identity.category for identity in freeze.identities] == ["suite"] * 4
```

并建议补一条**回归护栏**（断言生产几何下无 slot 饿死）：

```python
def test_no_slot_starves_when_every_category_owns_two_slots() -> None:
    """b_stream=8 / 4 categories 的几何下，一个 window 必须覆盖全部 8 条 slot。"""
    producer = _FakeProducer()
    categories = ("c0", "c1", "c2", "c3")
    streams = []
    for index, category in enumerate(categories):
        for slot_id in (index, index + 4):
            producer.blocks[(slot_id, slot_id)] = 64
            streams.append(_FakeStream(slot_id, slot_id, category))
    driver = _driver(
        _registry({category: 0.25 for category in categories}),
        producer, tuple(streams), window_members=128,
    )

    freeze = driver.freeze_window()

    per_slot = Counter(identity.slot_id for identity in freeze.identities)
    assert sorted(per_slot) == list(range(8))       # 修复前为 [4,5,6,7]
    assert set(per_slot.values()) == {16}           # 8 slot × 16 = 128 = b_stream * ga
    per_category = Counter(identity.category for identity in freeze.identities)
    assert set(per_category.values()) == {32}       # category 配额仍为各 1/4
```

---

## 6. 验收判据

**PASS**
1. `active_local_memory_driver_test.py` 全部既有用例 + 新增 2 例通过。
2. 新增用例在**未打补丁**的代码上**必须失败**（先证伪再证真，避免空转断言）。
3. 真实生产链路 `freeze_window()`（§1.1 的构造方式）得到 `window_slots_starved == []`、`per_slot_members` 为 8 个 slot 各 16、`per_category_members` 仍为各 32、`ga_effective == 128`。
4. Ruff + `py_compile` + `git diff --check` 通过。
5. 改动面仅为 `active_local_memory_driver.py:214-229` 与 `active_local_memory_driver_test.py`。

**FAIL**
- 任一既有用例回归；`per_category_members` 偏离各 32；`ga_effective != 128`；改动溢出上述两个文件。

**BLOCKED**
- 无法构造真实 latent cache 链路（§1.1 的 `LIBERO_ROOT` / `LIBERO_LATENT_CACHE_ROOT` 缺失）。

---

## 7. 禁止范围

- 不改 `SegmentIdentity` / `GAWindowPlan` / `MicrobatchPlanMember` 任何字段。
- 不改 `RankLocalSegmentScheduler`（含 `admit` / `cumulative_valid_consumer_exposure` 语义）。
- 不改 `_peek_block` / `_commit_block` / `exposure` 更新逻辑。
- 不改 `canonical_segment_streams` 的 slot 分配。
- 不引入 `used` 之外的持久状态；不新增依赖；不触碰 GPU / trainer / checkpoint 路径。
- 本 Gate **不含** `RESUME-ACTIVE-DRIVER-STATE` 与 `REBIND-COVERAGE-D8A`（见 TODO.md，独立跟踪）。

---

## 8. 请求

请给出 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_WINDOW_SLOT_ROTATION` 或 `REQUEST_CHANGES(file:line)`。

重点核验：
1. §2.1/§2.2 对本缺陷「非冻结语义改动」的定性是否成立。
2. §2.3 关于 (B) 裁决前提的解读，以及 §1.1 中「修复后更贴合契约」的判断。
3. §4 不变性论证，特别是 category 配额与 `_is_admissible` 连续性。
4. §5.2 fixture 是否足以覆盖 tie-break 分支、是否会出现空转断言。

---

## 9. 实现记录（已落地，待审）

### 9.1 改动面

| 文件 | 改动 |
|---|---|
| `cosmos_framework/model/generator/mot/active_local_memory_driver.py` | `freeze_window` 内 +6/-2（含 3 行说明性注释、`used` 初始化、tie-break 项替换、`used` 递增） |
| `cosmos_framework/model/generator/mot/active_local_memory_driver_test.py` | import `Counter` +2 例 fixture（`test_slot_rotation_covers_every_slot_sharing_one_category`、`test_no_slot_starves_at_the_production_stream_geometry`） |

无其他文件改动。

### 9.2 证据一：fixture 先证伪（补丁前）

```
cd /disk/rl/psm_wma/cosmos-framework
.venv/bin/python -m pytest cosmos_framework/model/generator/mot/active_local_memory_driver_test.py -q

2 failed, 11 passed in 41.14s
FAILED ...::test_slot_rotation_covers_every_slot_sharing_one_category
FAILED ...::test_no_slot_starves_at_the_production_stream_geometry

E  assert [4, 5, 6, 7] == [0, 1, 2, 3, 4, 5, ...]
```

新增 fixture 在未打补丁的代码上失败，且失败值 `[4,5,6,7]` 与 §1.1 生产链路实测的 `window_slots_used` 一致——**证明 fixture 捕获的正是生产缺陷，而非空转断言**。

### 9.3 证据二：补丁后全绿 + 静态检查

```
.venv/bin/python -m pytest .../active_local_memory_driver_test.py -q
13 passed in 24.35s

ruff check <driver.py> <driver_test.py>   → All checks passed!
py_compile <两文件>                        → PASS
git diff --check                          → PASS
```

### 9.4 证据三：生产链路复验（无 monkeypatch，跑的就是已修改的仓库代码）

```
LIBERO_ROOT=/disk/rl/data/LIBERO_LeRobot_v3 \
LIBERO_LATENT_CACHE_ROOT=/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1 \
.venv/bin/python /tmp/probe_freeze_slots.py

ga_effective               = 128
window_members             = 128
window_per_slot_members    = {0:16, 1:16, 2:16, 3:16, 4:16, 5:16, 6:16, 7:16}
window_slots_used          = [0, 1, 2, 3, 4, 5, 6, 7]
window_slots_starved       = []                      ← 修复前 [0, 1, 2, 3]
window_per_category_members= {libero_10:32, libero_goal:32, libero_object:32, libero_spatial:32}
first_rebind_position      = 40                      ← 修复前 28
rebind_count               = 12                      ← 修复前 13
```

`per_category_members` 与 `ga_effective` 与修复前逐项一致，**category 配额与 ABI 均未改变**。

### 9.5 证据四：相邻契约测试无回归

```
.venv/bin/python -m pytest production_active_wiring_test.py local_memory_segment_test.py \
    canonical_segment_runtime_test.py active_local_memory_launch_test.py -q

58 passed in 142.96s
```

### 9.6 结论

§6 的 PASS 判据 1–5 全部满足。数据集覆盖率由每 suite 50% 恢复为 100%，可达唯一 block 由 7240 提升至 14430。
