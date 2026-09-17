# Local Memory v0.3.5 Active-Route Resume 接线设计 v0.4

- Gate：`G0-R09-B-TTT-V035-ACTIVE-ROUTE-RESUME`
- formal root：`168f9fc7`（上一版本 v0.3 提交；本版本正式 root 由 SESSION/Inbox 在提交后回填）
- child/Gitlink：`525f5066393cba044f00f1104b83f5eb424a9c49`
- 目标文件：`active_local_memory_driver.py`、`active_local_memory_launch.py`
- 状态：**设计，送审（v0.4；修订 v0.3；v0.3 修订 v0.2；v0.2 修订 v0.1）**。本文不含已落地代码改动；当前 operative 行为是 §9 的 fail-closed 守卫。

---

## 0. 修订记录

### v0.3 → v0.4

v0.3 已送审（blob `待回填`）。v0.4 是对 DS 第 3 轮 `REQUEST_CHANGES` 的**唯一剩余 MEDIUM 半项**（`resume_wiring_design_v0.1.md:176-191,209-216`「load 侧未规定 `CanonicalRuntimeSnapshot` 的重建落地」）与两条 LOW（`:4` 头部 root、`:213` catalog_digest）的一次性整改。

| 项 | v0.3 的说法 | v0.4 的修正 | 依据 |
|---|---|---|---|
| §4.3 第 5 项（新增） | 无「runtime snapshot 重建落地」规定 | 新增第 5 项：`state_dict["runtime"]`（`CanonicalRuntimeSnapshot`）的**重建落地**——scheduler `rebuild()` + sidecar 回填 + identity 对象同一性，保证 resume 后 `canonical_segment_runtime.py:184-186` 的 `is` 校验与后续 `scan` 读取成立 | DS `:176-191,209-216` |
| §6 判据 7（新增） | 无 round-trip fixture | 新增 CPU fixture：round-trip 后断言 `committed_by_slot[slot] is stable_slots[slot]`（对象同一性）、sidecar 记录身份与 scheduler 一致、`owner.snapshot()` 可再次调用不抛错、`scan` 读到非空 `state_in` | DS fixture 要求 |
| §4.3 第 4 项 | 版本校验用 `source_digest`/`plan_chain_id` | 增补 `catalog_digest`（钉 catalog 顺序的 identity） | DS LOW `:213` |
| 头部 formal root | `1ba933c1` | 改为 `168f9fc7`（上一版本提交；本版本 root 由 SESSION/Inbox 回填） | DS LOW `:4` |

v0.3 的 §1–§4.2、§5、§7、§9 逐字未改动；改动集中在头部、§0、§4.3（第 4/5 项）、§6（判据 7）与标题。

### v0.2 → v0.3

v0.2 已送审（blob `ab65f3c8`）。v0.3 是对 DS 第 2 轮 `REQUEST_CHANGES` 的 MEDIUM 意见（`resume_wiring_design_v0.1.md:4,198,163-177,194-200`「头部陈旧 / 同一性判定未钉死 / 重建·同一性·版本 fail-closed 完备性」）的一次性整改。

| 项 | v0.2 的说法 | v0.3 的修正 | 依据 |
|---|---|---|---|
| 头部 formal root | `8bb48f35` | 改正为整改提交 `1ba933c1`（同其余两 Gate） | DS `:4` |
| §4.3 第 1 项「同一性」 | 「按 `(episode_index, episode_position, category)` 找到同一个对象」未钉死判定标准 | 钉死：以**值相等**匹配（`slot_id` + `episode_id` + `category` 三元组逐位相等，在重建的 `_by_slot[slot]` 中定位到唯一的 `CanonicalSegmentStream`），且要求**恰好命中一个**（0 个或 ≥2 个均 `raise`） | DS `:198` |
| §4.3 校验项数 | 三项（重建确定性 / 窗口边界 / window_index 单调） | 增补**第 4 项「版本/身份一致性」**：`state_dict` 持久化 `source_digest`/`plan_chain_id`，load 时校验与当前 run 逐位一致，否则 `raise`（防止 catalog/config 变更后被静默误 load） | DS `:163-177,194-200` |
| §4.1 `state_dict` | 无版本字段 | 增补 `source_digest`/`plan_chain_id` 两个字段入 `state_dict` | 同上 |

v0.2 的 §1–§4.2、§5、§6（判据 1–4）、§7、§9 逐字未改动；改动集中在头部、§0、§4.1 `state_dict`、§4.3、§6（判据 5）与标题。

### v0.1 → v0.2

v0.1 已送审（blob `a8dd24ca`）。v0.2 是对 DS `REQUEST_CHANGES` HIGH 意见（`resume_wiring_design_v0.1.md:59,148-150`「load 时序使 `_DataloaderWrapper` 永不命中 driver」）的一次性整改，经代码核实该意见成立。

| 项 | v0.1 的说法 | v0.2 的修正 | 依据 |
|---|---|---|---|
| §2.1 第 4 条 | 「构造时机无约束，driver 只需在 `attach()` 之后具备该接口即可」 | **错误**。`checkpointer.load()`（`trainer/__init__.py:383`）早于 `callbacks.on_train_start()`（`:400`，driver 在此 attach）⟹ load 时 driver 不存在，wrapper 永远绑定不到 | `trainer/__init__.py:383,400` |
| §4.1 接口位置 | 把 `checkpoint_component`/`has_checkpoint_state`/`state_dict`/`load_state_dict` 加在 **driver** 上 | 移到 **`ActiveLocalMemoryLaunchCallback`**（callback group 成员；`_DataloaderWrapper` 遍历的是 `callbacks._callbacks`，不是 driver） | `dcp.py:132-141` |
| §4.1 load 时序 | 无「driver 未构建时如何 load」的处理 | 新增 `_pending_resume_state` buffer：load 时 driver 未构建则暂存，`on_train_start` 构建 driver 后应用 | 同上 |
| §4.1 `has_checkpoint_state` | `return self._trainer is not None`（依赖 attach） | 改为 `return True`（launch callback 始终声明可 checkpoint，不依赖 driver 是否构建；冷启动无 `dataloader` key 时 load 自动 skip） | `dcp.py:914-926` |

v0.1 的 §1、§3、§5、§6（判据 1–4）、§7、§9 逐字未改动；改动集中在 §2.1、§4.1、§4.4、§6（判据 5）与 §0、标题。

---

## 1. 问题

active Local-Memory 路线的**数据进度状态完全不入 checkpoint**，而 model / optimizer / LR-scheduler / trainer 均正常恢复。

### 1.1 未入 checkpoint 的状态

| 持有者 | 状态 | 作用 |
|---|---|---|
| `ActiveLocalMemoryWindowDriver` | `_stream_index` | 每 slot 在 catalog 中的位置 |
| 同上 | `_active_stream` | 每 slot 当前消费的 episode |
| 同上 | `_active_cursor` | 每 slot 在该 episode 内的 block 游标 |
| 同上 | `_window_index` | 窗口计数（进 `plan_chain_id`） |
| `RankLocalSegmentScheduler` | `cumulative_valid_consumer_exposure` | weighted-deficit 的观测项 |
| 同上 | `stable_slots` / `terminal_slots` | 每 slot 的稳定流与终止流 |
| 同上 | `admission_order` / `committed_identities` | 提交守卫 |
| 同上 | `queue_seed` / `queue_epoch` / `queue_permutation` / `segment_provenance` | 队列确定性 |

### 1.2 后果

`on_train_start` 里全部**从零重建**。resume 后 driver 的 slot 前沿回到 catalog 首条 episode，scheduler 的 exposure 归零、守卫清空，而 optimizer 与 LR-schedule 已从 checkpoint 前进 ⟹ **数据回退、模型前进**的语义错乱：同一批 episode 被重复训练，且慢参数已按被重复的数据更新。

对 D8b 长跑（5000 步 ≈ 11.9 天，必然中断）不可接受。

---

## 2. 判定：不是重新设计，而是接缝未接线

**这是本设计最重要的更正。** 此前记录为「机制未知、需重新设计」，经 grep 核实**不成立**：

```
$ grep -rn "\.snapshot()\|CanonicalRuntimeSnapshot\|committed_snapshot" --include='*.py' cosmos_framework/ | grep -v _test.py
canonical_segment_runtime.py:173:    def snapshot(self) -> CanonicalRuntimeSnapshot:      ← 只有定义
canonical_segment_runtime.py:180:        committed = self.adapter.committed_snapshot()
canonical_segment_runtime.py:190:        return CanonicalRuntimeSnapshot(self.generation, self.scheduler.snapshot(), committed)

$ grep -rn "rebuild(" --include='*.py' cosmos_framework/ | grep -v _test.py
local_memory_segment.py:351:    def rebuild(cls, snapshot: dict[str, object]) -> "RankLocalSegmentScheduler":   ← 只有定义
```

即 `CanonicalSegmentRuntimeOwner.snapshot()`（`canonical_segment_runtime.py:173-190`）与 `RankLocalSegmentScheduler.rebuild()`（`local_memory_segment.py:351-364`）**均已完整实现，但全仓零生产调用点**。（`dcp.py:585`、`distributed.py:755` 的同名 `_rebuild` 是无关函数。）

**缺的只有持久化接线。**

### 2.1 持久化机制（核实 `dcp.py`，推翻两条此前的错误判断）

1. **`on_load_checkpoint` 不可用**：`dcp.py:943` 的 `on_load_checkpoint(model, state_dict={})` 拿到的是**空 dict**，源码注释明言「this callback is never used in the codebase」。
2. **不能新增顶层 key**：在 `on_save_checkpoint` 往 `to_save_dict`（`dcp.py:1114-1125`）新增顶层 key 会让 resume 直接 `raise ValueError(f"Invalid key: {key}. not support to resume.")`（`dcp.py:939`）。
3. **真正被认可的机制**是 `_DataloaderWrapper`（`dcp.py:112-153`）：回调声明类属性 `checkpoint_component = "dataloader"` 并提供 `has_checkpoint_state()` / `state_dict()` / `load_state_dict()`，即被持久化到既有的 `"dataloader"` key 并在 load 时回灌。参考实现：`callbacks/cosmos_dataloader_state.py:150+`。
4. **构造时机是关键约束（v0.2 更正，推翻 v0.1 的「无约束」判断）**：`_DataloaderWrapper` 在**存/取盘时**构造（`dcp.py:1120`、`:934`），每次重新遍历 `callbacks._callbacks`。**load 早于 `on_train_start`**（`trainer/__init__.py:383` load，`:400` 才 `callbacks.on_train_start`），而 driver 在 `on_train_start` 里才构建 + attach ⟹ **load 时 driver 不存在，若接口挂在 driver 上则 wrapper 永远绑定不到**。故接口必须挂在**始终存在于 callback group 的 `ActiveLocalMemoryLaunchCallback`** 上，且 `has_checkpoint_state()` 不得依赖 driver 是否已构建（§4.1）。
5. **该槽当前为空**：`DataLoaderStateCallback` 只注册于 reasoner 系列配置；`action_policy_libero_edge_all.py` 及其 callbacks 链均未注册。注意 wrapper **只看第一个** tag 为 `dataloader` 的回调，若将来 action 链引入同类回调会静默抢占。

---

## 3. 无界列表的修剪安全性证明

`admission_order` 与 `committed_identities` 在 `admit()`/`commit()` 中 append，`terminal_rebind()` 只清 `terminal_slots`/`stable_slots`，**从不修剪**。128 member/步 × 5000 步 = 每 rank 64 万条。

**此前记录的选项 (a)「排除二者（判定其为审计轨迹）」已被证伪**：二者是**活的守卫状态**，排除会直接打断守卫。全部读取点：

| 位置 | 用法 |
|---|---|
| `local_memory_segment.py:322-323` | commit 守卫：`identity not in admission_order or identity in committed_identities` → 拒绝 |
| `local_memory_segment_adapter.py:79` | 同上形态的提交守卫 |
| `canonical_segment_runtime.py:86` | skip-resume 守卫：`identity not in admission_order or identity in committed_identities` |
| `canonical_segment_runtime.py:224` | resolve 守卫：同上 |
| `canonical_segment_runtime.py:181` | `committed_by_slot = {i.slot_id: i for i in committed_identities}` — **后写覆盖 = 每 slot 最近一条** |
| `canonical_segment_runtime.py:182` | 断言 `admission_order` 每一项都在 `committed_identities` 中 |

### 3.1 修剪正确的依据（来自 `owner.snapshot()` 自身）

`CanonicalSegmentRuntimeOwner.snapshot()`（`:173-190`）：

- 只在 **IDLE（窗口边界）** 可调用，否则 `raise RuntimeError("snapshot requires idle committed frontier")`；
- `:181` 以**后写覆盖**派生 `committed_by_slot`；
- `:182` 断言 `admission_order ⊆ committed_identities`；
- `:183-186` 要求 `committed_by_slot[slot]` 与 `stable_slots[slot]` **恰为** sidecar 的该 slot 已提交 identity；
- `:187-188` 拒绝「已提交 slot 仍留在 `terminal_slots`」。

⟹ **resume 路径只咨询「每 slot 最近一条」**。更早的条目在 snapshot 路径上**没有任何读取点**，故按 slot 修剪**不改变任何被读取的信息**。这不是新引入的假设，而是 `snapshot()` 现有校验的直接推论。

### 3.2 修剪的作用域

- **只修剪 snapshot 的输出**（`snapshot()` 发修剪后的列表、`rebuild()` 恢复之）。
- **运行期活列表保持不修剪**：`:86` 与 `:224` 的 skip/retry 守卫要求 `identity in admission_order`，而这两条路径的 `_skipped_plan` / `_retry_plan` 均为**内存态**、resume 后为 `None`，故恢复后的修剪列表不影响它们。
- **副作用范围**：修剪解决的是**落盘体积**；运行期两个列表仍增长到 ~130 MB/列表（粗估）。若同时要有界运行期内存，须另证「每 slot 保留最近 N 条」不削弱 `:322-323` 的重复提交守卫——依据是同一 slot 内 `cursor` 单调递增、换 episode 时 `episode_id` 改变，故 identity 在全 run 内唯一，该守卫实际只对**当次窗口内**的重复提交起作用。**本设计不包含运行期有界化**，留作独立项。

---

## 4. 实现方案（最小改动）

### 4.1 checkpoint 接口挂在 launch callback（`active_local_memory_launch.py`，v0.2 更正）

`_DataloaderWrapper` 遍历的是 `callbacks._callbacks`（`dcp.py:136`），**不是 driver**。故四个成员必须加在 `ActiveLocalMemoryLaunchCallback` 上（它是 callback group 成员），由它**委托 driver**；driver 只需提供 `state_dict()` / `load_state_dict()` 供委托，不声明 `checkpoint_component`。

```python
class ActiveLocalMemoryLaunchCallback(Callback):
    checkpoint_component: str = "dataloader"

    def __init__(self, ...):
        ...
        self.driver: ActiveLocalMemoryWindowDriver | None = None
        self._pending_resume_state: dict[str, Any] | None = None   # v0.2 新增

    def has_checkpoint_state(self) -> bool:
        return True    # 始终声明可 checkpoint；不依赖 driver 是否构建

    def state_dict(self) -> dict[str, Any]:
        # save 发生在迭代结束，driver 必已构建（on_train_start 已过）
        if self.driver is None:
            raise RuntimeError("active Local-Memory cannot save: driver not attached")
        return self.driver.state_dict()

    def load_state_dict(self, state_dict: dict[str, Any]) -> None:
        # load 早于 on_train_start（trainer/__init__.py:383 vs :400），driver 可能未构建
        if self.driver is None:
            self._pending_resume_state = state_dict   # 暂存，on_train_start 后应用
        else:
            self.driver.load_state_dict(state_dict)
```

`on_train_start` 构建并 attach driver 后，应用暂存状态：

```python
    def on_train_start(self, model, iteration=0) -> None:
        ...  # 构建 driver（同 v0.1）
        driver.attach(trainer, model)
        self.driver = driver
        if self._pending_resume_state is not None:
            driver.load_state_dict(self._pending_resume_state)   # 见 §4.3 的 fail-closed 校验
            self._pending_resume_state = None
```

**driver 侧**（`active_local_memory_driver.py`）只新增 `state_dict()` / `load_state_dict()`（不声明 `checkpoint_component`）：

```python
def state_dict(self) -> dict[str, Any]:
    return {
        "source_digest": self.producer.source_digest,        # v0.3 增补：版本/身份
        "catalog_digest": self.catalog_digest,               # v0.4 增补：catalog 顺序身份
        "plan_chain_id": self.plan_chain_id,                 # v0.3 增补：版本/身份
        "window_index": self._window_index,
        "stream_index": dict(self._stream_index),
        "active_stream": {
            slot: (s.slot_id, s.episode_index, s.episode_position, s.category)
            for slot, s in self._active_stream.items()
        },
        "active_cursor": dict(self._active_cursor),
        "runtime": self.registry.owner.snapshot(),
    }

def load_state_dict(self, state_dict: dict[str, Any]) -> None:
    ...   # 见 4.3 的 fail-closed 校验
```

`CanonicalSegmentStream`（`canonical_local_memory_producer.py:49-63`）的四个字段全为标量，可直接序列化。

**冷启动安全性**：`has_checkpoint_state()` 始终 `True` 意味着冷启动（`iteration==0`）时 wrapper 也会在 save 时绑定本 callback，但 save 在 `on_train_start` 之后、driver 已构建，`state_dict()` 正常；load 侧冷启动时 checkpoint 无 `dataloader` key（从未 save 过），`dcp.py:915-926` 因文件不存在而 `continue`，不会误 load。

### 4.2 scheduler 快照的修剪

在 `RankLocalSegmentScheduler.snapshot()`（`local_memory_segment.py:368-381`）中把两个列表改为按 slot 取最后一条：

```python
"admission_order": tuple(_last_per_slot(self.admission_order)),
"committed_identities": tuple(_last_per_slot(self.committed_identities)),
```

`_last_per_slot` 定义为 `tuple({i.slot_id: i for i in items}.values())` —— 与 `canonical_segment_runtime.py:181` **同一个派生式**，故与 resume 路径唯一消费者逐位一致。`rebuild()` 无需改动（它已 `list(snapshot[...])`）。

### 4.3 load 侧必须 fail-closed 的四项校验（v0.3 增补第 4 项）

resume 状态**半对半错比不做 resume 更危险**（会静默错配 slot 与 episode），故 load 必须拒绝而非猜测：

1. **`_by_slot` 重建确定性（v0.3 钉死「同一性」判定）**：`canonical_segment_streams` 依赖 dataset `_ep_vals` 与 `episode_shuffle_seed`。恢复的 `active_stream[slot]` 是标量元组 `(slot_id, episode_index, episode_position, category)`，**按值相等**（四元组逐位相等）在重建后的 `_by_slot[slot]` 中定位 `CanonicalSegmentStream`；要求**恰好命中一个**（命中 0 个或 ≥2 个均 `raise RuntimeError`），并校验命中对象的 `episode_id == str(episode_index)`（字符串语义，与 `freeze_window` 的 identity 构造一致）。slot→episode 绑定错位即拒绝。
2. **恢复点必须是窗口边界**：`owner.snapshot()` 的输出只在 IDLE 时产生；load 时若 `_window` 非空或 owner 非 IDLE，拒绝。
3. **`window_index` 单调**：恢复值必须 ≥ 0 且小于当前配置的 `max_iter`。
4. **版本/身份一致性（v0.3 增补；v0.4 增补 catalog_digest）**：`state_dict` 里的 `source_digest`、`catalog_digest` 与 `plan_chain_id` 必须与当前 run 的 `self.producer.source_digest` / catalog 身份 / `self.plan_chain_id` **逐位一致**，否则 `raise RuntimeError`（防止 catalog/config 变更后被静默误 load——这是「半对半错」里最隐蔽的一类：游标对上、但数据身份已变）。`catalog_digest` 钉 catalog 顺序身份（manifest/config/source 三身份派生），与 §4.3 第 1 项的 `_by_slot` 重建确定性互为交叉验证。
5. **`CanonicalRuntimeSnapshot` 重建落地（v0.4 新增）**：`state_dict["runtime"]`（`owner.snapshot()` 的输出）在 load 时必须完整重建，且满足 `canonical_segment_runtime.py:184-186` 的 **`is`（对象同一性）校验**与后续 `scan` 读取：
   - **scheduler 重建**：`RankLocalSegmentScheduler.rebuild(runtime.scheduler)` 得到恢复后的 scheduler（其 `committed_identities`/`stable_slots` 里的 `SegmentIdentity` 是反序列化对象），并把它重绑到 owner（`owner.scheduler = scheduler`、`scheduler._canonical_runtime_owner = owner`，保持双向绑定）。
   - **sidecar 回填（identity 对象同一性）**：对 `runtime.committed` 的每条 `(identity, fast_state)`，**不得**直接把它写回 `sidecar`（那是反序列化的新对象，与 scheduler 里的不是同一对象，会使 `:184-186` 的 `is` 校验失败）；必须**用 scheduler 里同一 slot 的 identity 对象**（`scheduler.committed_identities` 中该 slot 最近一条）作为 sidecar 记录的 identity，`fast_state` 照搬：`sidecar._records[slot] = (scheduler_identity, ContinualTTTFastState(*fast_state))`。
   - **一致性自检**：回填后调用 `owner.snapshot()` 必须**不抛错**（`:182` 的 `admission_order ⊆ committed_identities`、`:184-186` 的 `is` 校验、`:188` 的 terminal-slot 无 sidecar 状态均通过）；且 `sidecar.read(identity)` 返回**非空** `state_in`（scan 可继续）。
   - 若任一自检失败，视为「半对半错」，`raise RuntimeError` 拒绝 resume。

### 4.4 与 `on_train_start` 守卫的关系（v0.2 更正）

`active_local_memory_launch.py:234` 的 fail-closed 守卫（`if iteration > 0: raise RuntimeError`）在本设计落地后**改为**：`iteration > 0` 时，若 `_pending_resume_state is not None`（load 已把 driver 状态灌入 buffer）则应用之并放行；若为 `None`（checkpoint 无 `dataloader` key，即本设计的 checkpoint 接口尚未在该 run 生效过）则保持拒绝。**不取消该守卫**——本设计未落地前它必须继续生效。

**load/守卫的时序链（v0.2 修正后，可核实）**：`checkpointer.load()`（`trainer/__init__.py:383`）→ `_DataloaderWrapper` 绑定 launch callback → `load_state_dict()` 灌入 `_pending_resume_state`；随后 `callbacks.on_train_start()`（`:400`）构建 driver 并 `load_state_dict(_pending_resume_state)` 应用到 driver（触发 §4.3 四项 fail-closed 校验）。故「load 成功」的判据是 `_pending_resume_state is not None`，而非 v0.1 误写的「`load_state_dict` 在 `on_train_start` 时尝试」。

---

## 5. 不变性论证

| # | 性质 | 为何不变 |
|---|---|---|
| 1 | `GaWindowPlan` ABI | 不触碰 |
| 2 | `SegmentIdentity` ABI | 不触碰 |
| 3 | `admit`/`commit` 守卫语义 | 运行期活列表不修剪；仅 snapshot 输出修剪 |
| 4 | `_is_admissible` 的 cursor 连续性 | 不触碰 |
| 5 | weighted-deficit 选取 | 不触碰（slot 轮转修复是独立 Gate） |
| 6 | `_DataloaderWrapper` 的既有占用者 | action/libero 链上该槽为空；本设计是它的**第一个**占用者 |
| 7 | 不 resume 时的行为 | `has_checkpoint_state()` 始终 `True`；冷启动无 `dataloader` key，load 自动 skip（`dcp.py:915-926`），冷启动路径零改动 |

---

## 6. 验收判据

**PASS**（全部满足）：

1. CPU 单测：`snapshot()` 修剪后的列表长度 = 该 slot 数；`rebuild()` 往返后 `committed_by_slot` 与修剪前**逐位一致**。
2. CPU 单测：`load_state_dict` 在 `_by_slot` 不可复现时 fail-closed（构造一个 episode 顺序被改动的 catalog）。
3. 生产链路（`tools/g0/probe_r09_b_active_static.py` 形态，CPU-only）：走满一个窗口后取 `state_dict()`，在**新建的 driver** 上 `load_state_dict()`，断言 `_stream_index`/`_active_cursor` 逐位相同。
4. GPU 端到端 resume 短跑：跑到 `save_iter` 存盘 → 杀进程 → 以 auto-resume 重启 → 断言 ①不再抛 `cannot resume`；②重启后首窗的 `SegmentIdentity` 序列**与不中断跑的对应窗口一致**；③`cumulative_valid_consumer_exposure` 连续（不归零）。
5. 既有 launch 测试改为断言 resume **被接受**而非被拒绝；并新增 CPU 单测验证 **load 时序**（v0.2 新增）：driver 未构建时 `launch_callback.load_state_dict(state)` 正确暂存到 `_pending_resume_state`，随后 `on_train_start` 构建 driver 并把暂存状态应用，断言 `_stream_index`/`_active_cursor`/`window_index` 与保存值逐位一致；再断言 `state_dict()` 在 driver 为 `None` 时 `raise`（save 侧 fail-closed）。
6. **版本/身份一致性 fail-closed（v0.3 新增）**：CPU 单测构造 `state_dict` 的 `source_digest`（或 `plan_chain_id`）与当前 driver 不一致，断言 `load_state_dict` `raise RuntimeError`；再构造「`active_stream` 命中 0 个 / ≥2 个对象」的边界，断言 `raise`（第 1 项「恰好命中一个」）。
7. **`CanonicalRuntimeSnapshot` round-trip（v0.4 新增）**：CPU 单测走满一个窗口 → `state_dict()` → 在新建 driver 上 `load_state_dict()`，断言：①`committed_by_slot[slot] is stable_slots[slot]`（对象同一性，非值相等）；②sidecar 记录身份与 scheduler 对应 slot 的 identity 是**同一对象**；③`owner.snapshot()` 可再次调用不抛错；④`sidecar.read(identity)` 读到非空 `state_in`。

**FAIL**：任一校验被绕过而 resume 成功；或 resume 后首窗 identity 序列与对照不一致。

**BLOCKED**：`_by_slot` 的重建被证明**不确定**（同 dataset 同 seed 下逐次不同）⟹ 须先解决 catalog 确定性，本设计不落地。

---

## 7. 禁止范围

- 不改 `GaWindowPlan` / `SegmentIdentity` / `SegmentBatch` ABI。
- 不改 `admit`/`commit`/`terminal_rebind` 的守卫。
- 不新增 DCP 顶层 key（`dcp.py:939` 会拒绝）。
- 不引入运行期列表有界化（§3.2 留作独立项）。
- 不取消 `active_local_memory_launch.py:234` 的 fail-closed 守卫，直至 §6 PASS。

---

## 8. 请求 verdict

请就以下三点裁定（第 3 点已由 v0.2 按 DS HIGH 意见修正，请复核而非首答）：

1. **§3 的修剪证明是否成立** —— 按 slot 取最后一条是否确实不改变 resume 路径读取的信息（依据是 `owner.snapshot()` 的 `:181-186` 校验）。
2. **§4.3 的五项 fail-closed 校验是否充分（v0.4 已按 DS 第 3 轮意见增补第 5 项「`CanonicalRuntimeSnapshot` 重建落地」并补第 4 项 catalog_digest）** —— 是否还有「半对半错」的静默通道未被拒绝。
3. **§4.4 的守卫收敛方式（v0.2 已修正）** —— DS 指出的「load 时序使 `_DataloaderWrapper` 永不命中 driver」已在本版修正（接口移到 launch callback + `_pending_resume_state` 暂存 + `has_checkpoint_state()` 恒 `True`，见 §2.1/§4.1/§4.4）。故守卫收敛为「`iteration > 0` 且 `_pending_resume_state is not None` 则应用放行，否则拒绝」，请复核该收敛是否成立、是否仍有 load 早于 attach 的静默通道。

---

## 9. 实现记录

**当前 operative 行为**：`active_local_memory_launch.py:234` 的 fail-closed 守卫已落地（child `525f5066`），未 attach 时 `has_checkpoint_state()` 尚不存在。中断即须从头重跑。**D8b 长跑（5000 步 ≈ 11.9 天）不得在此状态下启动。**

本文档为**设计**，尚无对应代码改动；实现与证据将在 Gate 裁定后补入本节。
