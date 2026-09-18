# DS 独立只读审核 — A2 实现（`ab2e3fb3`）

- 日期：2026-09-18
- 审核者：DS（独立，非作者）
- formal pair：root `a09b6f19be1d3fe0c5db309c1d7158ad0c2636eb` / child `ab2e3fb3c0a472fb18be392eb231724b1de5bd69`
- 设计：`docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_member_shape_refreeze_design_v0.2.md`（root）
- 范围：`grouped_active_contract/driver/runtime/metrics`、批量 TTT 更新、D025 exact selectors、native weighted loss 修复
- 重点：repeated-slot waves 的 TBPTT 等价、group 原子 commit/abort、resume/geometry、first-group 同 bytes 重试、状态/梯度隔离
- 方式：**只读**该 commit 树；未修改任何文件、未运行代码/测试、未启动 GPU/训练；未继承作者自测结论
- 边界：`local_memory_online.py`（untracked）不属于本次 target；`artifacts/g0/chatgpt_a2_delivery/`（untracked）未纳入

## 当前验证状态（按用户要求注明）

- **当前仅有作者的 206 项 CPU 验证**（作者自测，DS 未复跑、不继承）。
- **真实 GPU 控制跑进行中**（同 env/seed 对照 vs 中断）；**GPU 与长训均无 closure**。
- 本文件不主张任何远端 formal approval；仅为独立技术意见。

---

## 结论概览

未发现 HIGH 级确定性缺陷。实现整体谨慎：原子 publish、外层 loss 缩放、retry 内容封印、resume 几何校验均**设计-实现一致**（见「已核实正确」）。主要问题集中在**证据缺口**与**若干过宽异常/隐式契约**。

---

## Findings

### MEDIUM-1（证据缺口，非代码 bug）— A2 native 前向数值等价无 CPU 证据

- 依据：等价测试用的是合成 loss。`grouped_active_runtime_test.py:78`（`run_window`）计算 `primary = local.square().sum() / prepared.actual_n_valid`，再 `NativeBatchResult(primary, primary*0)`；模型测试 `grouped_active_model_test.py:19-31` 用 stub `training_step`，只验证 loss 标量代数（`10*vision + 7*action + auxiliary`）。
- 影响：设计 v0.2 §3「不得把合并 forward 自动等同数值等价」与 §5.5「单 GPU 真实 128-consumer forward/backward」所要求的 native 等价，**未被任何 CPU 证据覆盖**；审阅者不能从现有 CPU 证据继承该等价。
- 最小整改：GPU Gate 中显式给出「grouped 一次 128-consumer forward」vs「scalar 16-consumer × 多次」的同数据数值对照，并量化允许的批量归约（非位级）差异。

### MEDIUM-2 — `GroupedPlanMember` 硬性要求整段 TBPTT，缺少与 producer 的显式不变量绑定

- 依据：`grouped_active_contract.py:31-32` 强制每条 row 的 `row_planned_n_valid == tbptt_steps`；`:65` 要求 `segment.consumer_valid[row].all()`。
- 影响：A2 无法表达任何 partial/tail 段。设计 §2.1 声明了该限制，但代码未把「`CanonicalLocalMemorySegmentProducer.block_count` 只产整块（`block_count = valid_start_count // ttt_tbptt_steps`）」这一前提写成断言/注释/测试；一旦到来 partial block，会在组构造/`validate_batch` 处直接抛错。
- 最小整改：加显式不变量/注释链接到 `block_count` 语义，并补一条 partial-row 负例 fixture。

### MEDIUM-3 — `prepare`/`_produce_group` 过宽 `except Exception`，掩盖根因

- 依据：`grouped_active_runtime.py:191-195` 将**任何**异常统一标为 `LOCAL_MEM_GROUP_PREPARE_FAILURE` 并置 `ABORTED`；`grouped_active_driver.py:70-72`（`_produce_group`）同类。
- 影响：编程/环境错误（TypeError/KeyError/device mismatch）被误标，owner 进入 ABORTED，排障困难且可能把可恢复错误误判为不可恢复。
- 最小整改：按异常类型分流，保留原始 code/异常（至少把非「契约/数值」类原样抛出）。

### LOW-1 — `_rebind_terminal` 静默 no-op

- 依据：`grouped_active_driver.py:39-42` 覆盖为 `pass`，使基类 driver 的 `rebind_before_admit` 语义失效。
- 影响：正确性依赖「窗口期间无人读 live scheduler 的 `terminal_slots`」这一隐式不变量（实际由 staged candidate 在 `commit` 时统一处理）。无测试断言该不变量。
- 最小整改：补注释/单测显式锁定该不变量。

### LOW-2 — `segment_fingerprint` 类型集过窄且每个窗口首组都算

- 依据：`grouped_active_contract.py:166-192` 对超出其固定类型集（Tensor/ndarray/dataclass/Mapping/序列/None/标量/Enum/dtype/device/np.generic）的 payload 值抛 `TypeError`；调用点是 `grouped_active_runtime.py:281`（**每个窗口首组**，非仅 retry）。
- 影响：新增一个 payload 字段类型会在首窗口整体失败，而非只影响 retry 路径。
- 最小整改：限定/记录 payload schema，或只对 retry 所需字段做指纹。

### LOW-3 — launch 事后改写 `wiring.local_slow_parameters`

- 依据：`active_local_memory_launch.py:311`（A2 分支）在 `CanonicalSegmentWiring.__init__` 已校验唯一性/leafness 后，把它重设为 `model.net.parameters()` 中 `requires_grad` 的全部参数。
- 影响：意图正确（abort 清空**所有**可训练梯度，含 D025 baseline heads，满足设计 §2.6），但绕过构造期校验。
- 最小整改：改为构造参数，或在重设后复校唯一性/leafness。

---

## 已核实正确（供作者避免误改）

- **外层 loss 无双除**：`GAWindowPlan.objective`（`local_memory_segment.py:133-136`）= `n_i/N * consumer_loss + auxiliary/GA`；active backward 直接用 `objective`（`trainer/__init__.py:929-934`），**不经** `loss / grad_accum_iter`（`:606` 仅非 active 分支）。`primary = native_total - auxiliary`（`omni_mot_model.py:1459-1470`）拆分/重组自洽，模型测试覆盖。
- **首组 retry 内容封印可满足**：`trainer/__init__.py:676` 保留 `armed_prepared.segment`，`:761` 原对象回传，故 `grouped_active_runtime.py:283-285` 的 `segment is _first_segment` + fingerprint 成立且内容绑定。
- **abort 清全部可训练梯度**：经 launch `:311` 重设 `local_slow_parameters`，`production_segment_wiring.py:48-50` 覆盖 D025 baseline heads；测试 `grouped_active_runtime_test.py:133` 断言 `all(p.grad is None)`。
- **原子 publish**：`prepare` 只 stage candidate/records，`commit`（`grouped_active_runtime.py:200-218`）才 swap；失败丢弃 `_group_pending`，live scheduler/sidecar 不变；测试 `:120-135`。
- **resume 几何/布局拒绝**：`grouped_active_driver.py:119-127` 记录/校验 `member_layout`/`group_size`/`tbptt_steps`/`source_catalog_sha256`；基类 `active_local_memory_driver.py:451` 亦拒绝 layout 不一致。
- **repeated-slot 分层 TBPTT**：`dependency_waves`（`grouped_active_contract.py:135-152`）每层至多一 slot；`_scan_group` 跨层用 `_detached` carry（`:167-170`），等价于 scalar 逐段截断。

## 需作者确认

- **单 rank 限制**：`active_local_memory_launch.py`（A2 分支）在 `dist.get_world_size() != 1` 时 raise；设计 §5.5 只要求单 GPU，但 D8b 长跑规模（此前 14.6 天估算）与此是否一致需确认。
- 本审核不覆盖未跟踪的 `local_memory_online.py` 与 `artifacts/g0/chatgpt_a2_delivery/`。

---

*本文件为 DS 独立只读审核记录；不构成远端 formal approval，亦不改变任何 Gate/状态。*
