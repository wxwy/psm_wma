# Local Memory v0.3.5 Active-Route Resume 接线设计 v0.1

- Gate：`G0-R09-B-TTT-V035-ACTIVE-ROUTE-RESUME`
- formal root：`8bb48f3507dda24090de41bbc4208dfc9e4538aa`
- child/Gitlink：`525f5066393cba044f00f1104b83f5eb424a9c49`
- 目标文件：`active_local_memory_driver.py`、`active_local_memory_launch.py`
- 状态：**设计，待审**。本文不含已落地代码改动；当前 operative 行为是 §9 的 fail-closed 守卫。

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
4. **构造时机无约束**：`_DataloaderWrapper` 在**存/取盘时**构造（`dcp.py:1120`、`:934`），每次重新遍历 `callbacks._callbacks`。故 driver 只需在 `attach()`（`on_train_start`）之后具备该接口即可。
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

### 4.1 driver 侧（`active_local_memory_driver.py`）

新增四个成员，形态对齐 `callbacks/cosmos_dataloader_state.py:150+`：

```python
checkpoint_component: str = "dataloader"

def has_checkpoint_state(self) -> bool:
    return self._trainer is not None      # 未 attach 时不得被 wrapper 绑定

def state_dict(self) -> dict[str, Any]:
    return {
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

### 4.2 scheduler 快照的修剪

在 `RankLocalSegmentScheduler.snapshot()`（`local_memory_segment.py:368-381`）中把两个列表改为按 slot 取最后一条：

```python
"admission_order": tuple(_last_per_slot(self.admission_order)),
"committed_identities": tuple(_last_per_slot(self.committed_identities)),
```

`_last_per_slot` 定义为 `tuple({i.slot_id: i for i in items}.values())` —— 与 `canonical_segment_runtime.py:181` **同一个派生式**，故与 resume 路径唯一消费者逐位一致。`rebuild()` 无需改动（它已 `list(snapshot[...])`）。

### 4.3 load 侧必须 fail-closed 的三项校验

resume 状态**半对半错比不做 resume 更危险**（会静默错配 slot 与 episode），故 load 必须拒绝而非猜测：

1. **`_by_slot` 重建确定性**：`canonical_segment_streams` 依赖 dataset `_ep_vals` 与 `episode_shuffle_seed`。恢复的 `active_stream` 必须能在重建后的 `_by_slot[slot]` 中**按 `(episode_index, episode_position, category)` 找到同一个对象**；否则 `raise RuntimeError`（slot→episode 绑定错位）。
2. **恢复点必须是窗口边界**：`owner.snapshot()` 的输出只在 IDLE 时产生；load 时若 `_window` 非空或 owner 非 IDLE，拒绝。
3. **`window_index` 单调**：恢复值必须 ≥ 0 且小于当前配置的 `max_iter`。

### 4.4 与 `on_train_start` 守卫的关系

`active_local_memory_launch.py:234` 的 fail-closed 守卫（`if iteration > 0: raise RuntimeError`）在本设计落地后**改为**：先尝试 `load_state_dict`，成功则放行，失败则保持拒绝。**不取消该守卫**——本设计未落地前它必须继续生效。

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
| 7 | 不 resume 时的行为 | `has_checkpoint_state()` 在未 attach 时返回 False；冷启动路径零改动 |

---

## 6. 验收判据

**PASS**（全部满足）：

1. CPU 单测：`snapshot()` 修剪后的列表长度 = 该 slot 数；`rebuild()` 往返后 `committed_by_slot` 与修剪前**逐位一致**。
2. CPU 单测：`load_state_dict` 在 `_by_slot` 不可复现时 fail-closed（构造一个 episode 顺序被改动的 catalog）。
3. 生产链路（`tools/g0/probe_r09_b_active_static.py` 形态，CPU-only）：走满一个窗口后取 `state_dict()`，在**新建的 driver** 上 `load_state_dict()`，断言 `_stream_index`/`_active_cursor` 逐位相同。
4. GPU 端到端 resume 短跑：跑到 `save_iter` 存盘 → 杀进程 → 以 auto-resume 重启 → 断言 ①不再抛 `cannot resume`；②重启后首窗的 `SegmentIdentity` 序列**与不中断跑的对应窗口一致**；③`cumulative_valid_consumer_exposure` 连续（不归零）。
5. 既有 launch 测试改为断言 resume **被接受**而非被拒绝。

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

请就以下三点裁定：

1. **§3 的修剪证明是否成立** —— 按 slot 取最后一条是否确实不改变 resume 路径读取的信息（依据是 `owner.snapshot()` 的 `:181-186` 校验）。
2. **§4.3 的三项 fail-closed 校验是否充分** —— 是否还有「半对半错」的静默通道未被拒绝。
3. **§4.4 的守卫收敛方式** —— 本设计落地后，`iteration > 0` 应从「一律拒绝」变为「load 成功则放行、失败则拒绝」，是否正确。

---

## 9. 实现记录

**当前 operative 行为**：`active_local_memory_launch.py:234` 的 fail-closed 守卫已落地（child `525f5066`），未 attach 时 `has_checkpoint_state()` 尚不存在。中断即须从头重跑。**D8b 长跑（5000 步 ≈ 11.9 天）不得在此状态下启动。**

本文档为**设计**，尚无对应代码改动；实现与证据将在 Gate 裁定后补入本节。
