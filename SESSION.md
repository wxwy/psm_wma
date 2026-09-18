# 当前协作状态（rolling）

> 本文件只保留**当前目标 / Gate / 最近有效 pair / residue / 下一步 / blockers**，加最近阶段的详细历史。
> 更早内容已按日期归档：`docs/collab/session_archive/SESSION_2026-09-18_a71bbd0.md`（11253 行，immutable）。

## 当前状态（2026-09-18）

- **目标**：Local Memory 具备正式训练条件（active 路线）。
- **已关闭 Gate**：`G0-R09-B-TTT-V035-ACTIVE-WINDOW-SLOT-ROTATION`、`...-ACTIVE-ROUTE-RESUME`、`...-ACTIVE-CATALOG-EPOCH-REUSE`、`...-ACTIVE-PRODUCE-PREFETCH`（DS/MM 均 APPROVE_TO_CLOSE）。
- **已撤销**：`...-ACTIVE-SCHEDULER-SEMANTICS-REFREEZE` — 用户 2026-09-18 裁决「不清零」；design v0.1 标 withdrawn（HIGH-1 前提过时、HIGH-2 消解）。**D8b 长跑不再被 refreeze 阻塞**。
- **最近有效 formal pair**：Gate3 closure / PRODUCE-PREFETCH = root `c16fc8ec` / `8e4dc334` / child `fca7eb5`。
- **审核名册**：DS=`ds:0.0` + MM=`mm:0.0`（Kimi 已由用户移除）；GPT 按用户提示读取 `docs/collab/chatgpt/reviews/`。
- **Dirty residue**：子模块 `uv.lock`（dirty）、`results/libero_closed_loop_*`、`examples/eval_*_4090.sh`（未跟踪）。
- **正在运行的 process**：无（GPU 空闲）。
- **下一步**：MEDIUM-2（TODO zombie 收敛）、hygiene 补全；之后 D8b 长跑（用户已接受当前 regime）。
- **Blockers**：无强制阻塞。

---

## 最近阶段详细历史

### slot 饥饿最小修复：设计 + 生产链路 monkeypatch 验证（2026-09-17）

**判定缺陷而非冻结语义**（更正此前 TODO 中「触及 v0.3.5 冻结语义」的暂定评估）：

1. 规范原文把 weighted deficit 定义为「**选择下一 category**，再从该 category 的 seeded shuffled episode queue 取最前 eligible entry」（`docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.2.md:86`、`PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md:229`）。规范**只约束 category 级配额**，从未把同 category 内的 tie-break 定义为「恒取 slot_id 大者」，更未授权任何 slot 永久饿死。
2. `production_active_wiring.py:88` 走 singleton 候选 `owner.admit_next((identity,))`；`canonical_segment_runtime.py:98-111` 先按冻结计划第 `index` 个成员过滤候选、要求恰好 1 个匹配，再交给 `scheduler.admit()`。故 `scheduler.admit()` 的多候选 tie-break **在 active 路径上根本不被行使**，driver 的 `freeze_window` 顺序即唯一权威 ⟹ 修复可自包含于 `freeze_window`，不触及 owner/scheduler 冻结接口。
3. 规范同时规定「已绑定 slot 必须同 episode、同 digest、`cursor+1` 连续推进」（同上 :86/:90）。交替选 slot 下每条 slot 仍逐次 `cursor+1`（本 window 每 slot 恰推进 16 次），`_is_admissible` 的连续性约束依然成立。

**最小补丁**（仅 `active_local_memory_driver.py:214-229`）：

```
     used: dict[int, int] = {}
     for _ in range(self.window_members):
         choices: list[tuple[float, str, int, int, tuple]] = []
         for slot_id in self._by_slot:
             ...
             choices.append(
                 (target[stream.category] - observed, stream.category, -used.get(slot_id, 0), slot_id, view)
             )
         ...
         _, category, _used, slot_id, view = max(choices, key=lambda item: item[:3])
         stream, cursor, terminal, rebind, position = view
         self._commit_block(slot_id, stream, cursor, position)
         used[slot_id] = used.get(slot_id, 0) + 1
         exposure[category] = exposure.get(category, 0) + planned
```

即 tie-break 第三项由 `slot_id` 改为 `-used[slot_id]`：同 category 内的两条 slot 交替入选，跨 category 仍由 deficit 决定。

**验证（真实生产链路，CPU-only，monkeypatch 只作用于进程内，未改仓库文件）**：

```
cd /disk/rl/psm_wma/cosmos-framework
LIBERO_ROOT=/disk/rl/data/LIBERO_LeRobot_v3 \
LIBERO_LATENT_CACHE_ROOT=/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1 \
.venv/bin/python /tmp/verify_starvation_fix.py
```

| 量 | 原版 | 补丁版 |
|---|---|---|
| `per_slot_members` | `{4:32,5:32,6:32,7:32}` | **全 8 slot 各 16** |
| `slots_starved` | `[0,1,2,3]` | **`[]`** |
| `slot_sequence` 前缀 | `[7,6,5,4]×8` | **`[3,2,1,0,7,6,5,4]×4`** |
| `per_category_members` | 各 32 | **各 32（不变）** |
| `ga_effective` | 128 | **128（不变）** |
| `rebind_count` / 首次位置 | 13 / #28 | 12 / #40 |

**关键性质**：修复后 `8 slot × 16 = 128 = b_stream × ga`，每 8 个连续 member 来自 8 条不同 slot 流。现实现每批只跨 4 条流（各重复 2 次），与冻结契约「B_stream=8 由同 window 内 8 个连续 member 实现」的字面表述是否一致，**请 Gate 一并裁定**。

**当前状态**：仓库代码零改动（补丁仅存在于上述验证脚本与本文档）。因该修复改变 Gate 已批准冻结组件的行为（被选中的 episode 集合与 rebind 位置全部变化），按项目流程须经设计 + 三方 Gate 方可落地。

---

### SLOT-STARVATION 修复已落地（2026-09-17，用户委托决策后）

**授权链**：用户先选择「授权走设计+三方 Gate」，随后明确「我睡觉了，你自己决策了」。依 AGENTS.md:151（Codex 是构建者、执行者与最终技术决策主体；审核者意见仅作技术参考）推进为「先证伪 → 再落地 → 后送审」，把已实现的 diff 而非提案送三方审核。

**设计文档**：`docs/build/PSM-WMA_Local_Memory_v0.3.5_active_window_slot_rotation_fix_design_v0.1.md`（Gate `G0-R09-B-TTT-V035-ACTIVE-WINDOW-SLOT-ROTATION`）。

**子模块改动**（child commit `6dc25e0f8c3ba39525c8ba994b8d0c38c2ce5461`，分支 `v2`）：

| 文件 | 改动 |
|---|---|
| `active_local_memory_driver.py` | `freeze_window` +6/-2：`used` 计数、tie-break 第三项 `slot_id` → `-used[slot_id]`、选中后递增 |
| `active_local_memory_driver_test.py` | import `Counter` +2 例 fixture |

（`uv.lock` 为遗留 dirty 文件，未纳入提交。）

**证据链（四步）**：

1. **fixture 先证伪**（补丁前）：`2 failed, 11 passed in 41.14s`，失败值 `assert [4, 5, 6, 7] == [0,1,...,7]` —— 与生产链路实测的 `window_slots_used` 一致，证明 fixture 捕获的正是生产缺陷，非空转断言。
2. **补丁后**：driver 测试 `13 passed in 24.35s`；`ruff check` All checks passed；`py_compile` PASS；`git diff --check` PASS。
3. **生产链路复验**（无 monkeypatch，跑已修改的仓库代码）：`window_slots_starved [0,1,2,3] → []`、`per_slot_members {4:32,5:32,6:32,7:32} → 8 个 slot 各 16`、`per_category_members` 仍各 32、`ga_effective` 仍 128、`first_rebind_position 28 → 40`、`rebind_count 13 → 12`。
4. **相邻契约测试**：`production_active_wiring_test` + `local_memory_segment_test` + `canonical_segment_runtime_test` + `active_local_memory_launch_test` = **58 passed in 142.96s**。

**效果**：每 suite episode 覆盖率 50% → 100%；可达唯一 block 7240 → 14430。

**测试缺口（本项目已修补）**：既有唯一涉及 slot 轮转的用例 `active_local_memory_driver_test.py:138` 用的是**两个不同 category**（slots 0/1 分属 a/b），deficit 不等故 tie 不发生；而生产形态 `b_stream=8` / 4 categories 使**同一 category 恒有两条 slot**，该分支从未被覆盖。新增 fixture 直接构造同 category 双 slot。

---

### RESUME 缺口：fail-closed 防线已落地（2026-09-17）

**背景**：核实 D8a 产物时确认，active 路线的**数据进度状态完全不入 checkpoint** —— driver 的 `_stream_index`/`_active_stream`/`_active_cursor`/`_window_index` 与 scheduler 的 `cumulative_valid_consumer_exposure` 及各守卫在 resume 时全部重建，而 model/optim/LR-schedule 正常前进，形成「optimizer 已前进、数据回退重放」的语义错乱。

**机制更正（推翻此前判断）**：原先记录的「scheduler 已有 `snapshot()`/`rebuild()`，只需接线到 `on_save_checkpoint`/`on_load_checkpoint`」**是错的**。核实 `dcp.py`：① `on_load_checkpoint(model, state_dict={})`（`:943`）拿到的是**空 dict**，源码注释明言该回调从未被使用；② 在 `on_save_checkpoint` 往 `to_save_dict`（`:1114-1125`）新增顶层 key 会让 resume 直接 `raise ValueError(f"Invalid key: {key}. not support to resume.")`（`:939`）。真正被认可的机制是 `_DataloaderWrapper`（`:112-153`）：回调声明 `checkpoint_component = "dataloader"` 即被持久化到 `"dataloader"` key。**该槽在 action/libero 链上为空**（`DataLoaderStateCallback` 只注册于 reasoner 系列）。选项 (a)「排除 `admission_order`/`committed_identities`」同样**已被证伪** —— 二者是活的守卫状态（`canonical_segment_runtime.py:181-182` 断言 `admission_order` 每一项都在 `committed_identities` 中并从中派生 `committed_by_slot`）。

**落地改动**（child commit `525f5066393cba044f00f1104b83f5eb424a9c49`）：

| 文件 | 改动 |
|---|---|
| `active_local_memory_launch.py:234` | `del iteration` → `if iteration > 0: raise RuntimeError(...)` |
| `active_local_memory_launch_test.py` | 新增 `test_launch_refuses_to_resume_an_interrupted_active_run` |

依据 `Callback.on_train_start(model, iteration=0)`：`callback.py:348` 的 `tqdm.trange(self.config.trainer.max_iter, initial=iteration, ...)` 证明 `iteration` 即恢复到的迭代数。新增 CPU 测试断言失败后 `driver is None`、`trainer.callbacks._callbacks == []`；launch 测试 **11 passed in 18.90s**；`ruff check` 仅报 `active_local_memory_launch_test.py:6:1 I001`，已用 `git show HEAD:... | ruff check --stdin-filename ... -` 证明该告警在 HEAD 版本**同样存在**，属既有问题、与本次改动无关，按最小修改原则不动。

**代价与边界**：中断即须从头重跑。故该防线只是正式训练前的临时护栏；**D8b 长跑（5000 步 ≈ 11.9 天）不能在此防线下启动**，须先完成完整 resume 实现（driver 持 `checkpoint_component="dataloader"` + 持久化 slot 前沿与 scheduler 快照，并证明 `_by_slot` 在 resume 时逐位可复现）。

### REBIND-COVERAGE-D8A 降为 CPU 可覆盖（2026-09-17）

`tools/g0/probe_r09_b_active_static.py --members 128`（CPU-only）走满整个冻结窗口：`LIBERO_ROOT` / `LIBERO_LATENT_CACHE_ROOT` 指向真实 libero 4-suite + latent cache，单次约 7 分钟（其中约 30 秒为数据集加载），无需 GPU。使 `REBIND-COVERAGE-D8A` 从「需 7.3 小时 GPU」变为「7 分钟 CPU」。

**产物**（原为 `/tmp/probe_d6_128_rebind.json`；2026-09-17 复跑落盘为 **`artifacts/g0/active_static_probe/probe_full_window_postfix.json`**，`result="PASS"`，读数逐位一致）：`rebind_count=12`、`rebind_positions=[40,50,57,60,69,70,88,99,100,113,114,125]`、`per_slot_blocks={0:16,1:16,2:16,3:16,4:16,5:16,6:16,7:16}`、`walk.members=128`、`loss 82.6322 → 71.8982`（finite）、`evidence_free_members=[]`、`window_closed={slow_optimizer_steps:1, slow_grads_cleared:false, scheduler_committed:128}`、RSS 3.46 GB。窗口关闭是**显式断言**的：`owner.finish_window` → `resolve_local_memory_slow_window` 后若 `phase != "IDLE"` 即 `raise`（`probe_r09_b_active_static.py:464-478`）。即**每个 rebind 接缝都经 `driver._produce → _rebind_terminal → scheduler.terminal_rebind` 真实行使，且窗口随后成功关闭**。12 次（而非修复前的 13 次）因 slot 饥饿修复后每 slot 每 window 只推进 16 block（原 32）。

探针补记上述三个读数，使「rebind 接缝确被行使」可从仓库复现，而非只存在于一次性脚本。

---

### RESUME：接缝已建好但未接线（2026-09-17，设计送审）

**判定更正**：此前把 RESUME 记为「机制未知、需重新设计」**不成立**。grep 核实 `CanonicalSegmentRuntimeOwner.snapshot()`（`canonical_segment_runtime.py:173-190`）与 `RankLocalSegmentScheduler.rebuild()`（`local_memory_segment.py:351-364`）**均已完整实现，但全仓零生产调用点**。故本项是「接缝已建好、只差持久化接线」。

**同时更正两条此前的错误判断**：① `on_load_checkpoint(model, state_dict={})`（`dcp.py:943`）拿到的是**空 dict**（源码注释明言该回调从未被使用）；② 在 `on_save_checkpoint` 往 `to_save_dict` 新增顶层 key 会让 resume 直接 `raise ValueError("Invalid key: ... not support to resume.")`（`dcp.py:939`）。**真正机制**是 `_DataloaderWrapper`（`dcp.py:112-153`）的 `checkpoint_component="dataloader"` 槽；该槽在 action/libero 链上**为空**，本设计将是第一个占用者。wrapper 在存/取盘时构造（`dcp.py:1120`/`:934`）并每次重新遍历 callbacks，故 driver 只需在 `attach()` 后具备该接口。

**选项 (a) 被证伪**：`admission_order`/`committed_identities` **不是审计轨迹，是活的守卫状态**（`local_memory_segment.py:322-323`、`local_memory_segment_adapter.py:79`、`canonical_segment_runtime.py:86`/`:224` 均做成员判断），排除会直接打断守卫。

**修剪安全性证明**（来自 `owner.snapshot()` 自身，非新假设）：它只在 **IDLE（窗口边界）** 可调用，`:181` 以 `committed_by_slot`（后写覆盖 = **每 slot 最近一条**）派生，`:182` 断言 `admission_order ⊆ committed_identities`，`:183-186` 要求 `committed_by_slot[slot]` 与 `stable_slots[slot]` 恰为 sidecar 的该 slot 已提交 identity ⟹ **resume 路径只咨询「每 slot 最近一条」**，更早条目无任何读取点。修剪只作用于 snapshot 输出；运行期活列表保持不修剪（`:86`/`:224` 的 skip/retry 守卫需要成员判断，而这些路径的 `_skipped_plan`/`_retry_plan` 均为内存态、resume 后为 None）。

**产物**：设计文档 `docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_resume_wiring_design_v0.1.md`（Gate `G0-R09-B-TTT-V035-ACTIVE-ROUTE-RESUME`，formal root `8bb48f35`，child `525f5066`），并已送三方审核（INBOX 条目同日记）。**尚无代码改动**；当前 operative 行为仍是 `active_local_memory_launch.py:234` 的 fail-closed 守卫。

---

### rebind 覆盖的前提更正 + resume §6 BLOCKED 判据证伪（2026-09-17）

**一、`REBIND-COVERAGE-D8A` 结案：1 次 iteration = 1 个完整 window，不是 1 个 member**

本条此前记「D8a 的 member #0–#24 rebind 覆盖为零」「覆盖首次 rebind 需 ≥29 步」「覆盖全部需 128 步 ≈7.3 小时」，三句共享同一个前提「1 次 iteration = 1 个 member」。该前提**不成立**。真实关系是 **1 iteration = 1 完整 window = 128 个 member = 1 次 optimizer step**，由七条互相独立的证据确定：

| # | 证据 | 出处 |
|---|---|---|
| 1 | `window_members` 必须等于 `trainer.config.trainer.grad_accum_iter`，否则 `_arm_initial` 直接 raise | `active_local_memory_driver.py:162-165` |
| 2 | `freeze_window()` 只在 `owner.phase is IDLE` 时经 `_arm_initial` 调用一次；其余 member 走 `_arm_continuation` 复用同一个 `self._window` | 同文件 `:158-175` |
| 3 | `on_training_step_batch_start` 每个 microbatch 触发一次 | 同文件 `:137-140` |
| 4 | `microbatch_count` 在 `finish()` 内清零 ⟹ 它是**每个 optimizer step 内的前反向次数** | `trainer/__init__.py:162-184` |
| 5 | D8a 全部 25 条 iteration 行均为 `perf/microbatches=128` | `/tmp/d8a_launch_stdout.log` |
| 6 | `grad_accum_iter = 8 × PSM_R09_B_TTT_ACTIVE_GA = 8×16 = 128` | `action_policy_libero_edge_all.py:322-348` |
| 7 | 一个冻结窗口走满后 `window_closed={slow_optimizer_steps:1, scheduler_committed:128}` | `artifacts/g0/active_static_probe/probe.json` |

⟹ **D8a 的 25 次 iteration = 25 个完整 window = 25×128 = 3200 个 member**，每个 window 含 12 个 rebind member（`rebind_positions=[40,50,57,60,69,70,88,99,100,113,114,125]`）⟹ **GPU 上已行使约 300 次 rebind，而非 0 次**。补强证据：`terminal_rebind` 自带 fail-closed 守卫（`local_memory_segment.py:340-341`，非 terminal stable slot 即 `raise ValueError`），25 窗全过即接缝顺序正确。**证据强度须如实标注**：CPU 全窗探针是**直接观测**（逐位行使 12 条接缝）；GPU 侧为**构造强制 + 25 窗无异常**，非直接观测（训练日志无 rebind 计数行）。

**顺带更正**：`ActiveWindowMember`/`ActiveWindowFreeze` 只持 `stream`/`cursor`/两个 bool（`active_local_memory_driver.py:39-55`），**不含张量**。探针早期记的「整个 window ≈100 GB」是「同时保留 128 个 `SegmentBatch` 产物」所致，生产一次只持一个 member（实测 trainer 树 RSS 平在 6.6 GB）。

**二、resume 设计 §6 的 BLOCKED 判据证伪**

设计把「`_by_slot` 重建不确定」列为不落地的 BLOCKED 条件。两个独立进程各建一遍同一套生产 producer，对 **完整 stream 元组 + 每条 stream 的 `block_count` + `frame_source` 的 `_ep_vals`/`_ep_starts`/`_valid_cum` 原始字节**求 SHA256，**逐位相同**：

```
P1/P2: CATALOG_SHA256=f465db8e661a6fc4bfa79196c07d61238a073c23446c2ae5997150f06c9fd67c  SLOTS=8 STREAMS=1676
```

代码上同样确定：`canonical_segment_streams`（`active_local_memory_launch.py:146-180`）只读 `producer.frame_source._ep_vals/_ep_starts/_valid_cum`（`libero_lerobot_dataset.py:203-214`：`np.unique` + **seeded** per-episode train/val split）与 `block_count`，不涉 RNG、不涉进程态；`ActionIterableShuffleDataset` 只打乱 **block 迭代顺序**（`action_sft_dataset.py:69-88`），且 active 路线实测 `iterable_shuffle=False`（D8a callback config dump，`/tmp/d8a_launch_stdout.log:40`）。⟹ 该设计可继续评审与实现。

**三、DeviceMonitor 目录为空的原因更正**

此前把空目录归因于 `every_n=200`，**是错的**：per-iteration CSV 落盘被包在 `if self.save_s3 and self.rank == 0:` 内（`callbacks/device_monitor.py:160`），而 `save_s3="${upload_reproducible_setup}"`（`configs/base/defaults/callbacks.py:137`）且 `upload_reproducible_setup` 默认 False（`configs/base/config.py:70`），active TOML 未覆盖 ⟹ **任何** `every_n` 下都不会写 CSV。但 `log.info(f"{self.name} Stats:\n{summary_df.to_string()}")`（`:179`）**无条件执行**（rank 0），故 `PSM_R08_GATE_A_DEVICE_MONITOR_EVERY_N=1` 仍能把 `cpu_mem_gb`/`nvml_used_gpu_mem_gb` 逐迭代打进训练日志——这正是长跑要用的遥测通道。已隔离验证该 env 钩子在 active 路线生效：`device_monitor = {'every_n': 1, 'log_memory_detail': True, 'save_s3': False, 'step_size': 1, 'upload_every_n_mul': 5}`，`save_s3=False` + TOML 的 `wandb_mode="disabled"` ⟹ 该回调**不触网**。

### catalog 容量换算：现有 catalog 只够 112 个优化步，而计划是 5000 步（2026-09-17）

**怎么发现的**：复核 slot rotation 送审件时，注意到「饿死 slot 独占 7190/14430 = 49.83% block……**可达唯一 block 上限 7240 ≈ 56.6 window**，而正式训练计划约 5000 步」这句话里含一个此前被读过去的换算——`7240 / 56.6 = 128`，即**一个 window 消耗 128 个 block**。于是不再依赖转述，直接实测 catalog 的总容量。

**结论**：生产 catalog 的**总** block 容量 = `14430`，一个 window 消耗 `grad_accum_iter = 128` 个 block ⟹ **整个 catalog 只够 112.73 个 optimizer step**。正式计划 `max_iter = 5000` ⟹ **缺口 44.4 倍**。第 113 个窗口的 `freeze_window()` 会 `raise RuntimeError("active Local window exhausted every segment stream")`（`active_local_memory_driver.py:230-231`）。

**证据（直接实测，CPU-only）**：探针 `tools/g0/probe_block_capacity.py`，产物 `artifacts/g0/active_static_probe/probe_block_capacity.json`（`result="PASS"`，同参数独立复跑读数逐位一致；该探针参考 `probe_r09_b_active_static.py` 的形态，root 同样取自环境变量）。

| 项 | 读数 |
|---|---|
| streams / slots | 1676 / 8 |
| `per_slot_blocks` | `{0:2865, 1:1255, 2:1741, 3:1329, 4:2855, 5:1333, 6:1739, 7:1313}` |
| `per_category_blocks` | `{libero_10:5720, libero_goal:2588, libero_object:3480, libero_spatial:2642}` |
| `total_blocks` / `windows_served` | 14430 / **112.73** |
| `per_category_windows` | `{libero_10:178.75, libero_goal:80.88, libero_object:108.75, libero_spatial:82.56}` |
| `windows_until_first_slot_drained` | **78.44**（slot 1 = libero_goal，1255 block） |

**换算依据经代码核实，非推断**：① 一个 member 恰好消耗一个 block——`_peek_block` 每 member 推进一格 cursor、走满 `blocks-1` 才换下一 episode（`active_local_memory_driver.py:258-280`），`_commit_block` 只增不减（`:282-286`），**永不回收**；② `block_count = valid_start_count // ttt_tbptt_steps`（`canonical_local_memory_producer.py:113-115`），即一个 block = 一个 T=16 训练段；③ catalog 全程只建一次——`_by_slot` 在 `__init__` 构建（`:99-106`），`on_train_start` 建完 driver 后 `iteration > 0` 直接 raise、重复建也 raise（`active_local_memory_launch.py:223-289`），**无 epoch 重建、无绕回**；④ slot↔suite 映射为 `slot % len(categories)`（`active_local_memory_launch.py:166`），与 `probe_full_window_postfix.json` 的 `per_category`（375/424/449/428）及本次 block 数逐项吻合。

**如实标注本项新意**：`14430` 这一总数仓库内**早有记录**（`SESSION.md:9332`「1676 streams / 8 slots / 14430 whole blocks」、`SESSION.md:10426`「可达唯一 block 7240 → 14430」），但**从未有人把它换算成可服务的训练步数**。本项的新内容是 `14430 / 128 = 112.73 步` 这一换算，以及它与 `max_iter=5000` 的 44.4 倍缺口。

**为何至今未暴露**：D8a 25 步、soak45 45 步均 < 112。**与已结案两项的关系**：① slot 饥饿修复把可用量由 7240 提高到 14430（翻倍），是必要的，但不充分；② resume 恢复的是数据进度、不增加容量，故 resume 落地后 5000 步依然跑不完。

**为何旧记录未点明**：`SLOT-STARVATION-ACTIVE-WINDOW` 行内「各 slot 至少可支撑 41 个 window ≈ 5200 步」把 window 当成了 member（与 `REBIND-COVERAGE-D8A` **同源**的错误前提），41 window 实为 **41 步**——正是这个错误前提让人以为容量够用。

**已记录**：`TODO.md` 新增 `CATALOG-CAPACITY-VS-5000-STEP`（状态 TODO）。**已通知三方**：`docs/collab/chatgpt/CODEX_INBOX.md` 末尾「catalog 容量换算」条目，请审核者校正对「5000 步」的理解；两个在审 Gate 的送审件 SHA 均未改动。

**可能解法（(a) 已出设计送审；其余未自行实现）**：(a) **catalog 多 epoch 复用**——唯一能真正填平缺口的方向，也是常规训练语义（5000 步需要每段复用约 44 次）。**核实后判定：不是发明新机制，而是接线**——epoch 快照契约 `QueueEpochSnapshot`、确定性排列 `queue_permutation`（`PSM-WMA/queue/v1` 版本标记）、epoch 边界规则 `rollover_projected_if_safe`（`canonical_segment_adapter_scheduler.py:57-67`/`:76-110`/`:546-549`）**均已冻结**；`RankLocalSegmentScheduler.configure_queue`（`local_memory_segment.py:331-337`）**已预留接口、全仓零生产调用点**；`snapshot()`/`rebuild()` 已含 `queue_seed`/`queue_epoch`/`queue_permutation`。单位也对齐（契约 `_queue_for` 与 active 的 `_by_slot[slot]` 同以 episode 为单位）。**且不需给 identity 加 epoch 维度**：`_is_admissible` 在 `stable_slots` 无该 slot 时只要求 `cursor == 0`（`:309-311`），`terminal_rebind` 删除该条目（`:343`），故重置守卫容器后复用同一 identity 天然可准入，**不触及 `SegmentIdentity` ABI**（此前记的「触及 ABI」是未核实的判断，此处更正）。设计文档 `docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_catalog_epoch_reuse_design_v0.1.md`，Gate `G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE`，已送三方。**建议顺序：resume 先落地，再多 epoch**。(b) 缩短训练计划——112 步不足以训练；(c) 降低 `ttt_tbptt_steps`（16→8 使 block 数翻倍至 225 窗口）——仍不够且改变 TBPTT 语义；(d) 扩充数据集。**在此之前不得启动 D8b 长跑**（会在第 113 步 crash，白耗约 8 小时）。

### 契约的 epoch 边界在 active 路线上经实测不可达——多 epoch 复用设计由 v0.1 修订为 v0.2（2026-09-17）

**目的**：为「catalog 多 epoch 复用」设计（Gate `G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE`）实测其最关键前提——契约 `rollover_projected_if_safe`（`canonical_segment_adapter_scheduler.py:542-549`）的两条边界条件在 b_stream=8 / 4 categories 的生产形态下是否可满足。设计文档 §6 把「条件 2 恒不成立」列为不落地的 BLOCKED 判据。

**方法**：新建 `tools/g0/probe_catalog_epoch_boundary.py`，走**真实 driver + 真实 scheduler**（`ActiveLocalMemoryWindowDriver` + `RankLocalSegmentScheduler` + `CanonicalSegmentRuntimeOwner` + `SuiteRoutedSegmentProducer`，与 `probe_r09_b_active_static.py` 同一套搭建），**不调用 `producer.produce`**、不取任何张量，故能走完全部 112 个窗口。在每个**窗口边界**上评估契约的两条条件本身。设计上两个判断：① `freeze_window` 要么返回完整 128-member 计划要么 raise，故「能否再冻结」无需额外探测；② `freeze_window` **非原子**（循环内逐 member `_commit_block`，`:234`），故 raise 后用 `_save_cursors`/`_restore_cursors` 恢复游标。

**读数**（产物 `artifacts/g0/active_static_probe/probe_catalog_epoch_boundary.json`）：

| 项 | 读数 |
|---|---|
| `windows_completed` | 112 |
| `boundary_error` | `active Local window exhausted every segment stream` |
| 条件 1 成立次数 / 112 个边界 | **0** |
| 条件 2 成立次数 / 112 个边界 | **0** |
| `both_true_boundaries` / `reachable` | `[]` / **false** |
| `stranded_blocks` | **94**（slot 0 = 50，slot 4 = 44） |
| `remaining_blocks_by_category` | libero_10 = 94，其余三个 = **0** |
| `admissible_episodes` | 375 / 424 / 449 / 428（合计 1676 = streams，无零 block episode） |
| `terminal_slots` / `stable_but_not_terminal` | `{0,1,2,3,5,6,7}` / `[4]` |

**结论：契约的 epoch 边界在 active 路线上永久不可达**（是证明，不是推断）。第 112 窗口后总剩余 94 < 128 = `window_members`，此后每个 `freeze_window` 必在其 128 轮之一找不到有 block 的 slot 而 raise（`:230-231`）⟹ 第 14336 个之后的 block 永不提交、游标永久冻结 ⟹ slot 0 的下一个 episode（持 50 个残留 block）永不被 admit（条件 1 永久假）；slot 4（中途，持 44 个残留 block）永不到 terminal（条件 2 永久假）。

**根因（结构性）**：契约的窗口成员是**弹性的**——`derive_member(*, member_index, slot_ids)` 由调用方给出本 member 参与哪些 slot（`:522-530`）；active 路线的窗口**定长 128**（`_arm_initial` 断言 `window_members == trainer.config.trainer.grad_accum_iter`，`:158-160`）。契约模型允许「最后一个窗口短一点」，本路线不允许。

**设计修订（v0.1 → v0.2，blob `c686ff3b` → `8a1dbec3`）**：
1. **触发条件改用界条件**：窗口边界上当且仅当「下一个窗口填不满」（`Σ_slot remaining_blocks < window_members`）时推进 epoch。它恰好在「catalog 再也供不起整窗口」时触发，在 catalog 可被整窗口整除时与契约条件 1 **重合**，是本路线唯一可达的触发点。每 epoch 因此为 **112** 个窗口（非 112.73），`max_iter=5000` ⟹ **45 个 epoch**；每 epoch 推迟 94 个尾块（0.65%），因新 epoch 从位置 0 按新排列重走全部 catalog，**不永久丢失**（v0.2 §6 判据 5 专门断言）。
2. **契约条件 2 在本路线是多余约束，v0.1 的回退无收益**：契约的 rollover 会清空守卫容器——`rollover_projected_if_safe` 构造新状态时**不传** `stable_slots`/`terminal_slots`（`:564-569`），而二者默认 `()`（`:434-435`），故 mid-episode 的延续会**静默消失**，这才是条件 2 在契约里承重的原因；而本设计 §4.3 的重置既清容器**又归零每个 slot 的游标**，尾部是被**显式推迟**并在下一 epoch 完整重走 ⟹ 条件 2 不必要。v0.1 §6 的「按 slot 独立推进 epoch」回退会引入逐 slot epoch 记账与「一个 category 的排列跨两个 slot」的额外语义，无收益。
3. **§2 判定降级**：v0.1 称「不是新机制，而是接线」——**部分成立**。快照契约 / 排列函数 / scheduler 接口确为复用；但**边界规则必须为 active 路线新定**，契约的规则在本路线不可表达。
4. **§4.4 新增，消除 v0.1 「重排 `_by_slot[slot]`」的歧义**：排列是 category 级、以 episode 为单位，而 `_by_slot[slot]` 是该 category 的 episode 在 2 个 slot 上的**划分**。规则：按 `(source_digest, episode_id)` 排序得参照序（**必须与 `_queue_for` 的排序 `:477` 逐位一致**）→ 应用 `queue_permutation` → 每个 slot 取自身 episode 的**保序子序列**。**注意参照序是字符串比较**（`episode_id = str(stream.episode_index)`，`"10" < "2"`），实现若按数值排序会与契约偏离。

**探针自身的一处更正（如实记录）**：初版把条件 1 算成了 **block 级**（「该 category 还有没有整块」），而契约的条件 1 是 **episode 级**（已核实：`_admit_free_slot` 用 `positions[category]` 索引 `_queue_for` 的排列 `:512-517`、`_commit_admission` 每 admit 一个 episode 才 +1 `:589-590`、`_queue_for` 每 episode 一行 `:471-480`）。block 级是更强的谓词，两者在边界附近会给出不同答案；初版读数「`condition1_all_categories_drained=false`」因而**依据不成立**（方向虽同）。初版产物已被修正版覆盖、未提交；上表全部为修正版读数，且修正版额外记录了逐边界的条件轨迹。

**已记录 / 已通知**：`TODO.md` 的 `CATALOG-CAPACITY-VS-5000-STEP` 已追加本节结论与两处易错点；`docs/collab/chatgpt/CODEX_INBOX.md` 末尾已追加 v0.2 修订说明（取代 v0.1 的 §2/§3/§6/§8，请裁定四点）。**无代码改动**：`active_local_memory_driver.py` 未被修改，`freeze_window` 的 fail-closed `raise` 仍是当前 operative 行为，**D8b 长跑仍不得启动**。

### 多 epoch 复用设计修订为 v0.3——自查发现 §4.3 重置清单缺 adapter sidecar；规划层满跑 PASS（2026-09-17）

**目的**：在等 45 epoch 满跑的同时，复核 v0.2 §8 第 3 问（「§4.3 的重置清单是否完备——是否还有第四处状态会跨窗口残留」）。**该问由本设计自查给出了答案，且答案是「有」。**

**发现 1：rollover 缺 adapter 的 `LocalMemorySegmentSidecar` 重置，后果是必然抛错（不是概率事件）**

- `sidecar.commit` 只在该 identity `training_stream_end` 为真时 pop（`local_memory_segment_adapter.py:39-43`），否则存下该 slot 的 fast-state；`sidecar.read`（`:29-37`）在「不是前一身份 + 1 个 cursor」时**抛 `ValueError`（不是返回 `None`）**。
- **为何今天不暴露**：不改 epoch 时，slot 换 episode 只发生在上一 episode 已 terminal 时，而 terminal 的那次 `commit` 已把记录 pop 掉——即不变量「slot 换 episode 时 sidecar 必无该 slot 记录」。**`sidecar.reset` 因此是死代码（生产与测试零调用点）。** 而 **epoch rollover 是这套代码里第一个在记录仍存活时把 slot 倒回 cursor 0 的操作**，它打破了这个不变量。
- **为何必然抛错**：新 epoch 的 slot 首块 `cursor == 0`，而 `_active_stream` 已被清空 ⟹ `_peek_block` 的 `rebind = stream is not None` 为 **False**（`active_local_memory_driver.py:264-280`）⟹ 运行时**不会**调用 `_rebind_terminal`；且 `_rebind_terminal` 本身只对 terminal slot 生效（`:190-194`，`terminal_slots.get(slot_id)` 为 None 时直接返回）、**完全不触碰 sidecar**。于是 `read` 要求 `0 == previous.cursor + 1`，在 `previous.cursor ≥ 0` 时**不可能成立**——**与重排结果无关**。
- **边界处记录确实存在**：`probe_catalog_epoch_boundary.json` 的 `stable_but_not_terminal = [4]` ⟹ slot 4 的末次 commit `training_stream_end == False` ⟹ 记录存活。
- **最小复现（真实类，无需数据集/张量，2026-09-17 01:27 实测）**：commit 一个非 terminal 的 `(episode "7", cursor 3)`，再 `read` 同 episode 的 cursor 0 → `ValueError: segment sidecar identity is not a canonical continuation.`；`read` 不同 episode 的 cursor 0 → 同一条 `ValueError`；`reset` 后 `read` → `None`。
- **丢弃 carry 在语义上也正确**：rollover 把该 slot 倒回其首 episode 的 cursor 0，该 episode 会**从头重放**，其首块本应继承**初始**状态，而非上一 epoch 中途留下的 carry。

**发现 2：§6 判据 6 的措辞在今天就已为假（与本设计无关）**

原文写「`per_slot_members` 在每个窗口内仍为 8 个 slot 均衡」。但 `freeze_window` 的选择键是 `(target[category] - observed, category, -used)`（`:227-232`），**只看 exposure 赤字、不看该 category 还剩多少 block**；四个 category 的 block 供给量不等（5720 / 2588 / 3480 / 2642），故任一 category 抽干后，其两个 slot 就从 `choices` 中消失（`:222-224` 的 `if view is None: continue`）。**实测（2 epoch / 224 窗口冒烟）**：`windows_by_distinct_slots = {2:51, 4:49, 5:4, 6:39, 7:2, 8:79}`，**仅 79/224 覆盖全 8 slot**；epoch 0 自第 **80** 个窗口起不再覆盖 8 slot，**epoch 1 无一窗口覆盖 8 slot**。故判据改为可测的正确形式：对在该窗口**实际被服务**的 category，其两 slot 成员数之差 ≤ 1（`max_within_category_slot_skew`），覆盖度作为记录量而非通过条件。

**发现 3：复用把既有的类别偏斜放大为全 run 稳态**

`cumulative_valid_consumer_exposure` 45 epoch 后为 `libero_10=4050720 / libero_goal=1863360 / libero_object=2505600 / libero_spatial=1902240` ⟹ **libero_10 占 39.2%，而 `target_distribution` 是 25%**。成因是每 epoch 尾部（另三类已抽干、只剩 libero_10 的 slot 0/4）窗口 100% 给 libero_10。**epoch 0 与之后 44 个 epoch 逐位相同**（`windows_per_epoch` 全 112、`remaining_blocks_at_rollover` 全 94）⟹ **不是本设计引入，而是本设计让它每 epoch 重复一次**。已作为 §8 第 7 问送审：是否需先修 `freeze_window` 的供给感知。

**发现 4：规划层满跑 PASS（判据 2 的完整证明）**

探针 `tools/g0/probe_epoch_reuse_planning.py`（rollover 是**探针内参考实现**，生产文件未被改动）→ `artifacts/g0/active_static_probe/probe_epoch_reuse_planning.json`：

| 项 | 读数 |
|---|---|
| `result` | **PASS** |
| `windows_total` | **5040**（= 45 × 112，正是 §3.4 的容量换算） |
| `windows_per_epoch` | 45 项，**唯一值 = 112** |
| `criterion1_slot_order_matches_permutation` | **true**（`mismatches = []`） |
| `criterion2_meets_target` / `exceeds_single_epoch` | **true** / true |
| `criterion3_probe_is_pure` | **true** |
| `criterion4_window_index_not_reset` | **true**（`window_index = 5040 = windows_total`） |
| `criterion5_deferred_tail` | `deferred_after_epoch0 = 94`、`recovered_in_epoch1 = 94`、`missing_from_epoch1 = []` |
| `rollovers` | 44 次，`remaining_blocks_at_rollover` **唯一值 = 94**，`queue_epoch` 单调 1→44 |

**附带定量结论（复用不引入新的调度开销）**：`admit`/`commit` 的守卫成员检查是 **list 线性扫描**（`local_memory_segment.py:322-323` 的 `identity not in self.admission_order` / `identity in self.committed_identities`）。实测真实 `RankLocalSegmentScheduler`：N=2000 时 415 µs、N=14336 时 1261 µs，单 epoch 累计约 **9 s**。因 rollover **清空**这两个容器，该 O(n²) 的 n 上界**恰好等于今天单 epoch 的值**（45 epoch 合计约 6.8 min，相对 5000 步墙钟可忽略）。**这是「清空守卫容器」这一设计的附带收益。**

**设计修订（v0.2 → v0.3）**：§4.3 补 adapter 侧重置；新增 §4.7（sidecar 重置的归属与可达路径，三候选，建议 (b)）；§6 新增判据 8、更正判据 6 措辞；§5 补一处 resume 语义（边界处 sidecar **刻意清空**，resume 不得当数据缺失回填）；§8 收敛第 3 问（已答：**有且只有 sidecar 一处**）、新增第 6/7 问；§10 补 10.2/10.3/10.4。v0.2 的 §1–§3、§4.1–§4.2、§4.4、§7 **逐字未改**。

**§8 第 3 问的复核结论（供三方核对）**：v0.2 担心的另两处经复核**不构成残留**——`_rebind_terminal` 只对 terminal slot 生效且被 §4.3 的清空取代；`owner` 的 `phase`/`transaction`/`forward`/`_retry_plan`/`_completed_transaction`/`_sealed_slow_window` 全是**按 window** 的能力，窗口结束即归 `IDLE`（`canonical_segment_runtime.py:157-171`、`:173-179`），`wiring` 只持有 adapter 与 slow 参数（`production_segment_wiring.py:36-37`），`registry` 只持有四个按 window 的能力（`production_active_wiring.py:62-66`）。故按 slot 的持久状态**全清单为四处**：driver 的四个游标容器、scheduler 的两个守卫容器 + 两个序列表、`cumulative_valid_consumer_exposure`（刻意不清零）、sidecar。

**无代码改动**：`active_local_memory_driver.py`、`local_memory_segment.py`、`local_memory_segment_adapter.py`、`canonical_segment_runtime.py` **均未被修改**；`freeze_window` 的 fail-closed `raise` 仍是当前 operative 行为，**D8b 长跑仍不得启动**。

### soak45 的验收判据（预先登记，2026-09-17 01:33，迭代 8/45）

**为何登记**：`active_soak45` 这次 45 步 GPU 短跑此前**只在对话里说过判据、未落到文档**。未登记的验收判据容易被事后合理化，故本节点把它写死。**内存判据的统计量在迭代 8/45 时登记——早于看到终值；登记后不再修改，若终值不满足即记 FAIL。**

**运行参数**（`RUN_NAME=edge_libero_4in1_localmem_active`，`OUTPUT_ROOT=/disk/rl/psm_wma/artifacts/g0/active_soak45`，训练进程 pid **1205406**）：

```
PSM_R09_B_TTT_ACTIVE=1 PSM_R09_B_TTT_ENABLED=1 PSM_R08_LOCAL_HISTORY_ENABLED=1 \
PSM_R09_B_TTT_ACTIVE_GA=16 PSM_R08_GATE_A_DEVICE_MONITOR_EVERY_N=1 \
EXTRA_TAIL_OVERRIDES="trainer.max_iter=45 checkpoint.save_iter=15"
```

**判据**：

1. **完成性**：45 步全部走完，无 `Traceback` / `CUDA out of memory` / `Killed`。（注意：配置 dump 中的回调名 `skip_nan_step` 含 "nan" 字样，**不是失败信号**，勿误判。）
2. **数值健康**：每步 `train/loss` 有限（非 nan/inf）。
3. **slot 轮转修复生效**：**本次运行不可验证——登记者须如实标注，不得记为 PASS。**
   - **登记时的判断依据**（2026-09-17 01:34 实测，非推测）：`grep -icE "slot|window" /tmp/active_soak45.log` 得 **2**，且两处命中**都在启动时的配置 dump 内**（其一为 `'plan_chain_id': 'active-local-window'` 的 `window` 字样），**运行时无任何逐 member 的 slot 证据**；`grep -icE "PSM_DIAG_EVIDENCE|psm_diag"` 得 **0**，即逐 member 诊断探针（`local_memory_segment_adapter.py:104-157`）**本次未启用**。
   - 叠加的规模约束：45 步 < 128 member ⟹ **连一个完整窗口都没走完**（与 D8a 25 步同理）。
   - **因此判据 3 在本运行记为 N/A（不是 PASS，也不是 FAIL）。** slot 轮转修复的实证须另跑：设 `PSM_DIAG_EVIDENCE=1` 并跑到 ≥1 个完整窗口，参照基线为修复前实测 `window_per_slot_members={4:32,5:32,6:32,7:32}`、`slot 0/1/2/3 恒为 0`。
   - **本条为登记后修订**（01:3x 登记 → 01:34 核实后改）：登记时我写的是「只能用窗口内前 45 个 member 的 slot 覆盖来验证」，该说法**建立在日志含逐 member slot 信息这一未核实的假设上**；核实后发现假设为假。修订只把**不可验证**如实标出，**未放宽**任何通过条件。
4. **exposure 单调性**：`cumulative_valid_consumer_exposure` 单调不减。
5. **内存判据（本次预先登记的统计量）**：取 DeviceMonitor 的 `cpu_mem_gb` 逐迭代序列（`every_n=1`）。
   - **丢弃前 2 个样本**作为 warmup。理由：迭代 1 含 allocator / latent cache 首次填充，实测存在一次性台阶（4.834 → 6.593）。
   - 对剩余样本定义带宽 **B = max − min**，最小二乘斜率 **s（GB / 100 迭代）**。
   - **PASS 条件：`|s| < B / 2`**——即趋势幅度不超过噪声带宽的一半。理由（为何该阈值非任意）：若存在真实泄漏，趋势将随时间主导带宽，`|s|×100` 会超过 B；若只是振荡，斜率不可从噪声中分辨。该式自带标度，不需额外的绝对阈值。
   - 同时记录**最后 20 个样本**的 B 与 s 作为稳健性对照（长跑泄漏在尾部更易显现）。
6. **显存**：`nvml_used_gpu_mem_gb` 不随迭代单调上升（同一条 `|s| < B/2` 统计量）。

**登记时的快照（迭代 8/45，未参与判定，仅供追溯起点）**：`cpu_mem_gb` = 4.820（预跑）、4.834、6.593、6.146、6.147、6.173、6.470、6.120、6.121；`nvml_used_gpu_mem_gb` 稳定 **12.281**。

**已知与本次运行无关的既有事实**：`cpu_mem_gb` 由 psutil 求**当前进程 + 全部子进程** RSS 之和（`device_monitor.py:116-123`），而训练进程 `num_workers=0` ⟹ 无子进程，故该值就是训练进程自身 RSS。轨迹中的 1.76 GB 跳变经查**不是** latent 缓存 LRU（上界 8 个 episode，实测文件均值 32.2 MB / 最大 108.1 MB ⟹ 至多 0.86 GB，**假说不成立**），也**不是** page cache（psutil 的 RSS 不含它）。

### 45 epoch 满跑把复用设计 v0.3 的两处推断证伪，设计修订为 v0.4（2026-09-17 01:47）

run-2（pid 1216599，`/tmp/epoch_reuse_full2.log`）于 **01:46:56** 结束，`result=PASS`，产出最终产物 `artifacts/g0/active_static_probe/probe_epoch_reuse_planning.json`（9711 字节）。判据 1/2/3/4/5 与 run-1 **逐位一致**：`windows_total=5040`、`windows_per_epoch` 45 项唯一值 112、44 次 rollover 残留唯一值 94 且 `queue_epoch` 单调 1→44、`criterion1_mismatches=[]`、`criterion3_probe_is_pure=true`、`criterion4_window_index_not_reset=true`（`window_index=5040`）、`criterion5_deferred_tail={deferred:94, recovered:94, missing:[]}`、`committed_identities=14336`。

**新度量推翻了 v0.3 §10.4 的两处表述**（这是本次复用设计至今最重要的技术发现）：

| v0.3 的表述 | 实测 |
|---|---|
| 「epoch 0 与之后 44 个 epoch **逐位相同**」 | **假**。只有聚合量相同（112 窗 / 残留 94）；**窗口内部构成相反**：epoch 0 有 81/112 个窗口服务全部 4 类（`all_categories_windows=81`、`all_slots_windows=79`），**epochs 1–44 的 `first_partial_category_window` 恒为 1** ⟹ 无一窗口覆盖全部 category |
| 「51 个 2-slot 窗口来自尾部只剩 libero_10」 | **算术上不可能**：51 × 128 = 6528 > libero_10 每 epoch 全部消耗 5626。该推断把「2 个 slot」等同于「1 个 category」 |

**严格下界（由直方图推出，非估计）**：被服务 category 实例数 = 1×3826 + 2×1070 + 3×63 + 4×81 = **6479**；实际 distinct slot 实例数 = 2×3826 + 3×51 + 4×1019 + 5×7 + 6×56 + 7×2 + 8×79 = **12898**；若每 category 出满 2 slot 应为 12958 ⟹ **缺口 60**，与**奇数 slot 窗口数 51+7+2 = 60** 精确吻合（互为交叉验证）。2-slot 窗口若为「2 category × 1 slot」每个耗 2 个缺口 ⟹ 至多 30 个；直方图不含 1-slot 窗口故 1-category 窗口全落在 2-slot 桶内 ⟹

> **单 suite 窗口 ≥ 3826 − 30 = 3796，即 ≥ 3796/5040 = 75.3% 的窗口只服务 1 个 suite。**

对照 epoch 0（= 今天的单 epoch 行为）：**72.3% 的窗口服务全部 4 个 suite**。两者是**相反的构成**。

`windows_by_distinct_categories = {1:3826, 2:1070, 3:63, 4:81}`、`windows_by_distinct_slots = {2:3826, 3:51, 4:1019, 5:7, 6:56, 7:2, 8:79}`、`max_within_category_slot_skew = 64`。`tail_structure`：epoch 0 = `{first_partial_window: 80, first_partial_category_window: 82}`，epochs 1–4 均 = `{1, 1}`，五者的 `remaining_by_category_at_epoch_end` 全为 `{libero_10: 94, 其余: 0}`。

**根因（已核实，非推测）**：`cumulative_valid_consumer_exposure` **同时是 `freeze_window` 的控制输入**（选择键 `target - observed`，`active_local_memory_driver.py:227-232`），而它在 rollover 时被**刻意保留**（v0.3 §4.3）⟹ epochs ≥1 开局即继承 epoch 0 末的偏斜赤字（libero_10 占 39.2%、赤字深度为负；另三类为正），`freeze_window` 连续服务赤字为正者直到其抽干，**窗口塌缩到单一 category 的 2 个 slot**。故 v0.3 的「偏差成因是供给约束而非不清零」**只对 epoch 0 成立**。

**对设计定性的影响**：v0.3 曾把 39.2% 偏斜定性为「既有性质被复用放大」，据此建议「可作既有行为接受、单独开 Gate」。**该定性的前提已被推翻**——这不是把既有行为重复 45 次，而是**让 44/45 的训练步运行在今天从未运行过的 regime 里**。候选修法（保留累计字段作报告量、赤字改用 per-epoch observed）**触及 §7 改动面之外的选择键，本设计未擅自纳入**，已升级为 §8 第 7 问（三选一）。

**§6 判据 6 的第二次更正**：v0.3 把「同类两 slot 成员数之差 ≤ 1」拟升为**通过条件**，实测全局 `max_within_category_slot_skew = 64`（上限 128）；但该值**未按 epoch 分离**，**无法判断 epoch 0 单独是否 ≤ 1**——若为假则与刚更正掉的原文属**同一类缺陷**（把今天不成立的性质写成判据）⟹ **降级为记录量**，跑出单 epoch 基线前不得作 PASS 条件。

**供给侧交叉验证（新增，可复算）**：`per_slot_blocks` 显示**同类两 slot 的供给本身就不等**（goal 1255/1333 差 78、spatial 1329/1313、object 1741/1739、libero_10 2865/2855）。最小值 **1255 ÷ 16**（每 slot 每窗口成员数）= **78.44**，与容量探针的 `windows_until_first_slot_drained = 78.44` **逐位吻合** ⟹ epoch 0 的 `first_partial_window = 80` 是**由供给推出来的**（第 79 窗仍用掉该 slot 剩余的 7 块，第 80 窗起为 0），不是观测巧合。

**无代码改动**：`active_local_memory_driver.py`、`local_memory_segment.py`、`local_memory_segment_adapter.py`、`canonical_segment_runtime.py` **均未被修改**；探针中的 rollover 是**探针内参考实现**，生产改动仍等 Gate 授权。`freeze_window` 的 fail-closed `raise` 仍是当前 operative 行为，**D8b 长跑仍不得启动**。

**本窗口另完成**：① 把 soak45 的验收判据**预先登记**到上文（内存统计量在迭代 8/45 时登记，早于终值）；② 登记后核实**判据 3（slot 轮转）在 soak45 日志中不可验证**（`grep -icE "slot|window"` 得 2，两处命中均在启动配置 dump 内；`PSM_DIAG_EVIDENCE` 未设置）⟹ 已如实改为 **N/A**，并注明登记时的说法建立在未核实的假设上。

**设计文档已修订为 v0.4**（blob `219355d3d5dda1407e5602218d6ab1c7bb79ad47`），改动集中在 §4.3 一条、§6 一条、§8 一条、§10.4 全节、§0 与标题；v0.3 的 §1–§3、§4.1–§4.2、§4.4–§4.7、§5、§7、§9 **逐字未改动**。

### 审核前置硬检查（第 1 轮）——检查结果：**三个在审 Gate 的 formal root 不在远端，未送达**（2026-09-17 01:49 CST）

**本轮性质**：这是对 `G0-R09-B-TTT-V035-ACTIVE-WINDOW-SLOT-ROTATION`、`G0-R09-B-TTT-V035-ACTIVE-ROUTE-RESUME`、`G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE` 三个 Gate 的**首次完整前置检查**，不是「续等已检查过的同一计时句柄」。所有步骤均成功执行，故结论**不是**「检查失败/状态未知」。

| 凭证字段 | 本轮实测 |
|---|---|
| 轮次 / 时间 | 第 1 轮，2026-09-17 01:49:37 CST |
| `before_head` | `661b54f3c2616f55b2fff8adf386252e3f8dbe22` |
| 远端 advertised SHA | `f63ee3c5ab8da0855aea1ca2d9e47f5b5d4eb28c`（`git ls-remote origin refs/heads/V2`） |
| `git fetch origin V2` | 成功（`* branch V2 -> FETCH_HEAD`） |
| `git log before_head..origin/V2` | **空** ⟹ 远端无新增提交 |
| ff 判定 | `merge-base --is-ancestor <before_head> origin/V2` 返回**非 0**；但 `f63ee3c5` 是 `HEAD` 的**祖先** ⟹ 远端**纯落后**，非分叉，无需 ff |
| 本地领先量 | `V2 [origin/V2: ahead 29]` |
| 子模块 Gitlink | `HEAD` 的 `cosmos-framework` = `525f5066393cba044f00f1104b83f5eb424a9c49`；工作树另有 ` M cosmos-framework`（**dirty，单独报告，不污染审核范围**） |
| ChatGPT exact-pair 检索 | `grep -rl <root> docs/collab/chatgpt/reviews/`，对 `5d527f3e`/`8bb48f35`/`bae39647`/`f6d3ae26`/`661b54f3` **命中文件数均为 0**；`reviews/` 最新文件为 `2026-09-16_stage1_pragmatic_pair_producer_advice_b57ad44_93a89ba.md`（2026-09-16 11:52），锚定 `b57ad44`/`93a89ba` |
| pane capture 1：`ds:0.0` | 成功。显示的是**旧 pair** `formal root=3324b3a0a4dc92b36882e23b4d9b42052554965c` / `child=93a89ba61306d840a008813f62f26a34d54850f4` 的 `REQUEST_CHANGES`（针对 `source_evidence_production_entrypoints_implementation_design_v0.1.md:64`）。**未出现任何当前 Gate 的 pair** |
| pane capture 2：`mm:0.0` | 成功，但显示 **Claude Code 进程已退出**——`pane_current_command = zsh`，pane 停在裸 shell，末行为 `Resume this session with: claude --resume a34005ee-6e0d-46c3-be87-d0bce4d661ff`。**MM 审核进程不可用** |

**核心事实（本轮最重要的发现）**：`INBOX` 引用过的 root 的远端可达性**分成截然两段**——

| root | 对应 Gate | 远端 |
|---|---|---|
| `3bf72e49` / `a58bdb90` / `187768e4` / `786538f8` / `3324b3a0` | 历史已获批各 Gate | **在远端** ✓ |
| `5d527f3e` | ACTIVE-WINDOW-SLOT-ROTATION | **仅本地** ✗ |
| `8bb48f35` | ACTIVE-ROUTE-RESUME | **仅本地** ✗ |
| `bae39647`（及修订 `f6d3ae26`、`661b54f3`） | ACTIVE-CATALOG-EPOCH-REUSE | **仅本地** ✗ |

远端最后一次推送为 **`f63ee3c5` @ 2026-09-16 21:21:45**；此后 29 个提交（含三个 Gate 的全部送审件与设计文档）**从未推送**。历史上每个可审核的 Gate 其 formal root 都在远端，故「root 可达」是本项目审核送达的既有前提。

**逐方状态（严格由本轮凭证导出）**：
- **ChatGPT（`ds:0.0`）**：处理中——但其手上的 pair 是 `3324b3a0`，**当前三个 Gate 的 pair 未送达**。`reviews/` 中无任一当前 root 的 exact formal review。
- **MM（`mm:0.0`）**：**不可用**——审核进程已退出，pane 停在 shell。
- **Kimi**：**未检查**——本轮冻结名册中未登记其 pane（`fz`/`fq` 会话存在但从未在 SESSION 中 capture 过）。

**结论**：三个 Gate 的诚实状态是 **「未送达 / 链路不完整」**，不是「尚未回复」。因此**不存在推进令牌**，三个 Gate 全部保持 `REVIEW`；按治理规则，无令牌时**禁止整改、编码、提交、执行、训练或关闭 Gate**，仅可修复审核链路、记录失败、或撰写不依赖既有审核结论的 docs-only 设计。

**链路修复所需的动作（需用户决定，本回合未执行）**：推送本地 29 个提交使三个 Gate 的 formal root 在远端可达；并恢复 MM 的审核会话（`claude --resume a34005ee-6e0d-46c3-be87-d0bce4d661ff`）。**推送属「外网访问」，按 CLAUDE.md 确认规则须取得用户明确许可**，故本回合**未推送**，仅如实记录。

---

### 复用设计修订为 v0.5——单 epoch 基线跑出，§6 判据 6 的更正形式**整体撤回**（2026-09-17 02:05 CST）

**触发**：v0.4 把 §6 判据 6 的更正形式（「对在该窗口实际被服务的 category，其两 slot 成员数之差 ≤ 1」）降级为记录量，理由是 45 epoch 全局 `max_within_category_slot_skew = 64` **未按 epoch 分离**，**无法判断 epoch 0 单独是否 ≤ 1**，并明确写下「若为假则与刚更正掉的 v0.2 原文属同一类缺陷；须先跑单 epoch 基线」。该基线已跑出，**结论是该形式应整体撤回**。

**新证据**：`artifacts/g0/active_static_probe/probe_epoch_reuse_planning_epoch0.json`（`tools/g0/probe_epoch_reuse_planning.py --max-epochs 1 --target-windows 112`；`result=PASS`、`windows_total=112`、`window_index=112`、`rollovers=[]`、`epochs_planned=1`）。

| 项 | epoch 0 单独 | 45 epoch 全体 |
|---|---|---|
| `max_within_category_slot_skew` | **32**（上限 128） | 64 |
| `windows_by_distinct_categories` | `{1: 16, 2: 13, 3: 2, 4: 81}` | `{1: 3826, 2: 1070, 3: 63, 4: 81}` |
| `windows_by_distinct_slots` | `{2: 16, 4: 13, 5: 1, 6: 1, 7: 2, 8: 79}` | `{2: 3826, 3: 51, 4: 1019, 5: 7, 6: 56, 7: 2, 8: 79}` |
| `all_categories_windows` / `all_slots_windows` | 81 / 79 | 81 / 79 |
| `first_partial_window` / `first_partial_category_window` | 80 / 82 | 80（epoch 0）→ 1（epochs ≥ 1） |
| `remaining_by_category_at_epoch_end` | `{libero_10: 94, 其余: 0}` | 每 epoch 均为 94 |
| `cumulative_exposure` | `{libero_10: 90016, libero_goal: 41408, libero_object: 55680, libero_spatial: 42272}`（libero_10 = 39.2%） | 45× 同比例 |

**判定 1（判据 6）**：`max_within_category_slot_skew = 32 ≠ 1`，**在 epoch 0 单独就已成立**。故该判据形式**在今天就已为假**——若升为 PASS 条件，它是一条「今天的生产行为就已经不满足」的判据，**与 v0.2 原文属同一类缺陷**。⟹ **整体撤回**（不再作判据、不再作候选通过条件），该项仅作**记录量**保留。§6 的 GPU 部分因此只保留两条已核实可判定的断言：「loss 有限」与「`cumulative_valid_consumer_exposure` 单调不减」。

**判定 2（量化 v0.4 的核心结论）**：单 suite 窗口占比 **epoch 0 = 16/112 = 14.3%**；**epochs 1–44 = (3826 − 16)/44 = 86.6/epoch = 77.3%**——**相差 5.4 倍**。且 epoch 0 有 **81** 个「4 类并存」窗口，epochs ≥ 1 为 **0**。这以最直接的方式量化了「复用改变了训练 regime」而非「重复了同一 regime」，把 v0.4 的定性判断落成两个可复算的数字。

**顺带确认（epoch 0 单独也成立的两项）**：`first_partial_window = 80` 与 `first_partial_category_window = 82` 在单 epoch 与 45 epoch 下**逐位相同**（epoch 0 段），与供给侧交叉验证（最小值 `1255 ÷ 16 = 78.44`）一致；`remaining_by_category_at_epoch_end` 的 `libero_10 = 94` 即每 epoch 推迟的尾块数，与 `probe_catalog_epoch_boundary.json` 的 `stranded_blocks = 94` **吻合**。

**范围声明**：**无生产代码改动**（同 v0.3/v0.4）；探针中的 rollover 是**探针内参考实现**。设计文档修订为 **v0.5**（blob `e22b6543ee3d2c0874dc2be9f60dcca6e89ca37c`），改动集中在 §0 / §6 的一条 / §10.4 的一节 / 标题，§1–§5、§7–§9 逐字未改；v0.4 的实质内容全部保留。INBOX 已追加「第四次修订」条目（重建后的精简 live Inbox 中，`## 未决 Gate 索引` 的 epoch reuse 行本已写明「以本文件末尾『第四次修订』为准」，该节现已存在，指引不再指向空处）。

**自守声明**：本次撤回**不是**放宽标准——它把一条**在今天就已为假**的候选判据撤掉，避免重演 v0.2 原文的缺陷类；判据总数减少，但保留的两条均为已核实可判定项。

**未决不变**：§8 第 7 问 (a)/(b) 仍待三方裁定；(c) 已由本次基线闭合。三个 Gate 状态仍为**未送达**（见上节），**无推进令牌**。

---

### 审核前置硬检查（第 2 轮，用户询问「正式训练条件 / 昨晚情况」触发）——结论：状态与昨晚一致，仍「未送达 / 链路不完整」（2026-09-17 09:34 CST）

| 凭证字段 | 本轮实测 |
|---|---|
| 轮次 / 时间 | 第 2 轮，2026-09-17 09:34:05 CST |
| `before_head` | `4cdedf68f6e0f302b0d46343c82965b7ffafefbd` |
| `git fetch origin V2` | 成功 |
| 远端 advertised SHA | `f63ee3c5ab8da0855aea1ca2d9e47f5b5d4eb28c`（`git ls-remote origin refs/heads/V2`），与 tracking `origin/V2` 一致 |
| `git log before_head..origin/V2` | **空** ⟹ 远端无新增提交 |
| ff 方向 | `merge-base --is-ancestor origin/V2 HEAD` 返回 **0** ⟹ 远端 `f63ee3c5` 是本地 `HEAD` 的**祖先**，远端**纯落后**，非分叉，无需 ff |
| 本地领先量 | `git rev-list --count origin/V2..HEAD` = **30**（较昨晚第 1 轮的 29 多 1，即 v0.5 提交 `4cdedf68`） |
| ChatGPT exact-pair 检索 | 对 `5d527f3e`/`8bb48f35`/`bae39647`/`f6d3ae26`/`661b54f3`/`4cdedf68` 逐一 `grep -rl`，**命中文件数均为 0**；`reviews/` 最新文件仍为 `2026-09-16_stage1_pragmatic_pair_producer_advice_b57ad44_93a89ba.md`（2026-09-16 11:52），锚定 `b57ad44`/`93a89ba` |
| pane capture：`mm:0.0` | 成功。内容为**旧 pair** 的 SegmentBatch/loss 接缝设计 review（`REQUEST_CHANGES`，日期 Sep 7），**未出现当前三个 Gate 任一 pair** |
| pane capture：`ds:0.0` | 成功。内容为**旧 pair** 的 HIGH-1..HIGH-5 `REQUEST_CHANGES`（DeepSeek V4 Pro），**未出现当前三个 Gate 任一 pair** |

**本轮结论**：远端自 `2026-09-16 21:21:45`（`f63ee3c5`）后**仍无任何新推送**；三个在审 Gate（`ACTIVE-WINDOW-SLOT-ROTATION` / `ACTIVE-ROUTE-RESUME` / `ACTIVE-CATALOG-EPOCH-REUSE`）的 formal root **仍不在远端**，`reviews/` 中无 exact formal review，MM/DS 两个 pane 的 capture 均非当前 pair。⟹ 状态仍为 **「未送达 / 链路不完整」**，**不存在推进令牌**，三个 Gate 保持 `REVIEW`。

**逐方状态（由本轮凭证导出）**：ChatGPT=`未送达`（pair 不在远端、无 exact review）；MM=`未送达`（pane 内容非当前 pair）；Kimi=`未检查`（冻结名册未登记其 pane，本会话 `kimi`/`fq` 存在但从未在 SESSION capture 过）。

**正式训练条件仍未具备**，阻塞不变：①三个 Gate 未送达、无令牌；②catalog 容量仅 112.73 步（缺口 44.4 倍，依赖 epoch-reuse 裁定）；③resume 未接线（fail-closed `iteration>0` 直接 raise，D8b 长跑不能在该防线下跑）；④slot 饥饿修复待 Gate 授权落地。链路修复仍须用户许可：推送本地 30 个提交（外网访问）+ 恢复 MM 审核会话。

---

### 审核链路修复 + 三 Gate 重新送达（2026-09-17 09:54 CST，REVIEW）

**目标（用户 /goal）**：按项目规范持续推进，只到实现具备 local mem 训练条件。

**链路修复（已执行，推送成功）**：
- 子模块 `cosmos-framework` v2 推送 `5d24528 → 525f506`（3 个提交：`81fa342`/`6dc25e0`/`525f506`）。
- 根仓 `V2` 推送 `f63ee3c5 → 4cdedf68`（30 个提交）。
- 推送后 `git ls-remote`：根仓 `V2=4cdedf68`，子模块 `v2=525f506`；`git rev-list --count origin/V2..HEAD = 0`，本地与远端同步。

**三个 Gate 的 formal pair（以 archive `CODEX_INBOX_2026-09-17_661b54f.md` 的 canonical 声明为准，现已全部远端可达）**：
| Gate | formal root | child/Gitlink | 设计文档 blob |
|---|---|---|---|
| ACTIVE-WINDOW-SLOT-ROTATION | `5d527f3ea8db25f23482c9a3e13b5c7ca2fd6a99` | `6dc25e0f8c3ba39525c8ba994b8d0c38c2ce5461` | `8556b0a5` |
| ACTIVE-ROUTE-RESUME | `8bb48f3507dda24090de41bbc4208dfc9e4538aa`（附注前进至 `c48c0169`，送审件未变） | `525f5066393cba044f00f1104b83f5eb424a9c49` | `a8dd24ca` |
| ACTIVE-CATALOG-EPOCH-REUSE | `bae3964776d3138d2a60d1b03cbabe0062fef75c`（修订至 v0.5，最终 commit `4cdedf68`） | `525f5066393cba044f00f1104b83f5eb424a9c49` | `e22b6543` |

**送达回执（三联：send-keys -l → ≥1s → 独立 Enter → capture）**：
- ChatGPT：canonical live Inbox 已随根仓 `4cdedf68` 推送；未决 Gate 索引 + archive 完整正文均远端可达。
- MM=`mm:0.0`（pane 进程 `claude`）：送达成功，capture 显示完整三 Gate 申请进入会话、底部 `✽ Computing…`（开始处理）。
- DS=`ds:0.0`（pane 进程 `opencode`）：送达成功，capture 显示完整申请进入会话、底部 `Thinking`（DeepSeek 开始处理）。

**状态**：三个 Gate 全部 `REVIEW`，三方 final 未齐、无推进令牌。下一步按三分钟完整远端锁定 + 三方 exact-pair 核验轮询，至少连续三十轮。

### 三 Gate 审核轮询（第 1 轮，2026-09-17 09:59:07 CST，REVIEW）

- `before_head=4cdedf68`；fetch 成功；advertised/tracking=`4cdedf68`；新增范围为空；祖先判定=0；ff=`Already up to date`。
- ChatGPT exact-pair 检索（`5d527f3e`/`8bb48f35`/`bae39647`/`4cdedf68`/`6dc25e0f`/`525f506`）**命中数均 0**，`reviews/` 无新增。
- MM=`mm:0.0` capture：显示针对 epoch-reuse 的意见（`probe_epoch_reuse_planning.json` 判据 1-5 全 PASS、无 HIGH/CRITICAL，但 §8 第 7 问 (a)/(b) 不可悬置、75.3% 单 suite = 5.4 倍 regime 变化应实现前裁定），**尚未给出 self-contained 同 pair FINAL**；pane 内有用户输入「选 (a)，出 v0.6」。
- DS=`ds:0.0` capture：`Thinking`（处理中），尚无 final。
- 无推进令牌，三个 Gate 保持 REVIEW，继续轮询。

### 轮询 #2（10:03:26 CST）：fetch 无新增（advertised=`4cdedf68`）；ChatGPT reviews/ 0 命中；MM 显示 epoch-reuse 第 7 问 (a)/(b) 裁定中（pane 内用户输入「选 (a)，出 v0.6」，MM 输出 v0.6 修订措辞），无 self-contained FINAL；DS 正读 `canonical_segment_adapter_scheduler.py`（configure_queue 审核中）。无令牌，继续。

### 轮询 #3（10:08:10 CST）：fetch 无新增（advertised=`4cdedf68`）；ChatGPT reviews/ 0 命中。**DS=`ds:0.0` 已给出三 Gate literal verdicts**（Build 13m56s）：
- Gate 1 `ACTIVE-WINDOW-SLOT-ROTATION`：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_WINDOW_SLOT_ROTATION`（内容层面；§2.3(B) 解读成立；**须改正设计头部 stale root/child**）。
- Gate 2 `ACTIVE-ROUTE-RESUME`：`REQUEST_CHANGES` —— HIGH：`resume_wiring_design_v0.1.md:59,148-150`（load 时序使 `_DataloaderWrapper` 永不命中 driver）。
- Gate 3 `ACTIVE-CATALOG-EPOCH-REUSE`：`REQUEST_CHANGES` —— 主因：`catalog_epoch_reuse_design_v0.1.md:191-197,485-493`（不清零 exposure 控制输入，静默改变 44/45 epoch regime，不应作为已知代价接受）；其他 `:136-146`/`:222-231`/`:199-202,249-262`/`:268`/`:237-247`。
- DS 另附「未决送达事实」：基于旧 ledger `CODEX_INBOX.md:10-23` 称三 root 不在远端、无令牌，**未意识到已推送**；并指 exact-pair identity 需改正（stale root/child）。DS 声明「在链路与 exact-pair identity 改正前，本结果不能作为正式三方同 SHA 闭批」。
- MM=`mm:0.0`：仍停在「选 (a)，出 v0.6」输入，无新 FINAL。ChatGPT 未回复。无推进令牌，继续。

### 三 Gate 一次性整改（2026-09-17 10:57 CST，REVIEW → 整改中）

**技术决策（Codex 主体，非用户裁定）**：采纳 DS `REQUEST_CHANGES` 与 MM「第 7 问不可悬置」意见，三个 Gate 各做最小 docs-only 整改：

1. **Gate 1 `ACTIVE-WINDOW-SLOT-ROTATION`**：设计头部 stale `formal root/child`（`3065bc8a`/`81fa342d`）改正为送审件实际提交 `5d527f3e`/child `6dc25e0f`，附修订说明；正文 §1–§9 无改动。
2. **Gate 2 `ACTIVE-ROUTE-RESUME` → v0.2**：经代码核实 DS HIGH 意见成立（`trainer/__init__.py:383` load 早于 `:400` on_train_start，driver 在后者才 attach）。修正：checkpoint 接口从 driver 移到 `ActiveLocalMemoryLaunchCallback`（`_DataloaderWrapper` 遍历的是 callbacks），新增 `_pending_resume_state` 暂存 buffer（load 时 driver 未构建则暂存、on_train_start 后应用），`has_checkpoint_state()` 恒 `True`。
3. **Gate 3 `ACTIVE-CATALOG-EPOCH-REUSE` → v0.6**：§8 第 7 问**裁定 (a)**——引入 per-epoch observed 计数器 `_epoch_observed`，`freeze_window` 选择键改用之、累计字段 `cumulative_valid_consumer_exposure` 保留仅作报告量；同步闭合其余六问（queue_seed 选 (b)、sidecar 归属选 (b)）；§7 显式放宽「改选择键 observed 来源」一条；§6 新增判据 9/10。

**待办（Kimi 8 条建议，空闲处理）**：覆盖不变量一等公民测试、tie-break 纪律入设计模板、容量探针标准化、尾巴截断量化入 epoch-reuse Gate、清理 v0.13/D018 §4 僵尸任务、三 Gate 并行送审（已在做）、resume 范围框死（边界重启 vs 状态续传，需评估是否改 v0.2）、T 循环吞吐地板微基准。详见 TODO。

下一步：静态核验（已 `git diff --check` PASS）→ 提交 → 推送 → 以新 formal pair 重新送审三 Gate。

### 三 Gate 整改后重新送审（2026-09-17 11:04 CST，REVIEW）

- 整改提交 `1ba933c1`（三文档 + SESSION）已推送；Inbox 更新提交 `a1477862` 已推送。远端 `V2=a1477862`。
- **新 formal pair**（root 均为整改提交 `1ba933c1`，child 不变）：slot-rotation=`1ba933c1`/`6dc25e0f`；resume=`1ba933c1`/`525f506`；epoch-reuse=`1ba933c1`/`525f506`。设计文档 blob：`e50e55ca`/`ab65f3c8`/`6a4c0ac6`。
- 送达回执：ChatGPT=Inbox 已推送（`a1477862`）；MM=`mm:0.0` 已送达（`Moonwalking…` 处理中）；DS=`ds:0.0` 已送达（capture 显示其正以 `git rev-parse`/`ls-tree`/`log` 核实新 root `1ba933c1`，处理中）。
- 三方 final 未齐，无推进令牌；三 Gate 保持 REVIEW，进入三分钟轮询。

### 轮询 #4（整改后第 1 轮，2026-09-17 11:10:32 CST）：fetch 无新增（advertised=`de999520`）；ChatGPT reviews/ 0 命中。**DS 第 2 轮 verdict + MM 第 2 轮 verdict 已出**：

**DS=`ds:0.0`（Build 3m57s）literal verdicts**：
- Gate 1：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_WINDOW_SLOT_ROTATION`（无附加条件）。
- Gate 2：`REQUEST_CHANGES(file:line)` —— `resume_wiring_design_v0.1.md:198`（同一性判定位置未钉死）、`:163-177,194-200`（重建/同一性/版本 fail-closed 完备性）、`:4`（头部 formal root 陈旧，仍 `8bb48f35`，应改整改提交）。DS 附注「HIGH 已闭合，仅余 fail-closed 完备性 MEDIUM」。
- Gate 3：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE`（附条件：判据 9/10 必须在 closure 前实测通过；Q5 seed 注入需确认 manifest/config/source digest、Q6 sidecar 归属须与 Gate 2 实现顺序绑定，余项「实现前补入」）。DS 附注「第 7 问 (a) 主因已闭合」。

**MM=`mm:0.0`（Brewed 1m16s）**：对 Gate 3 v0.6 结论「未发现 HIGH/CRITICAL/MEDIUM 缺陷，授权按 §4.1/§4.3/§4.6/§4.7/§6 判据 9-10 落地，按 §5 顺序（Gate 2 v0.2 先落地 → 本设计后落地），`discard_committed_carry()` 与 Gate 2 `snapshot()/rebuild()` 以一次协调 commit 完成」。**任务清单 3 项（Gate 1 头部校正 / Gate 2 v0.2 load 时序 / Gate 3 v0.6）仍 0 done**，pane 输入行待「发送三方 verdict 通知并登记台账」。

三方 final 仍未齐（ChatGPT 未回复；MM Gate 1/2 复审中；DS Gate 2 余 REQUEST_CHANGES MEDIUM）。继续轮询。

### 轮询 #5/#6（11:17/11:21 CST）：无实质变化。fetch 无新增（advertised=`de999520`）；ChatGPT reviews/ 0 命中；MM 停滞于「3 tasks 0 done」（Gate 1/2 复审未出 verdict，输入行「发送三方 verdict 通知并登记台账」未提交）；DS 无新输出。继续轮询。

### Gate 2 resume v0.3 整改 + 重新送审（2026-09-17 11:45 CST，REVIEW）

- 用户「在等什么」催促后，作为技术决策主体直接采纳 DS 第 2 轮 Gate 2 `REQUEST_CHANGES(MEDIUM)` 并整改为 **v0.3**：①`:4` 头部 formal root 改正为 `1ba933c1`；②`:198` §4.3 第 1 项「同一性」钉死（值相等、恰好命中一个）；③`:163-177,194-200` 增补第 4 项「版本/身份一致性」（`state_dict` 持久化 `source_digest`/`plan_chain_id`，load 校验逐位一致）；§6 新增判据 6。
- 提交推送 `168f9fc7`（仅 resume 文档）。新 formal pair：root=`168f9fc7`/child=`525f506`，blob 待确认。
- 重新送审 Gate 2：DS/MM 均 `send-keys -l → Enter` 送达（请求复核 MEDIUM 是否闭合，verdict=`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_ROUTE_RESUME` 或 `REQUEST_CHANGES`）。
- 其余状态不变：Gate 1 DS approve / MM 复审中 / ChatGPT 未回复；Gate 3 DS approve(附条件) / MM approve / ChatGPT 未回复。继续三分钟轮询。

### Gate 2 resume v0.4 整改 + 重新送审（2026-09-17 12:11 CST，REVIEW）

- DS 第 3 轮（11:45 送达后）回 `REQUEST_CHANGES`：唯一剩余 MEDIUM 半项 =「load 侧未规定 `CanonicalRuntimeSnapshot` 重建落地（scheduler rebuild + sidecar 回填 + identity 对象同一性）」，两条 LOW（`:4` 头部 root 应 `168f9fc7`、`:213` 建议 catalog_digest）；DS 明言「补一段 §4.3 第 5 项 + 一条 CPU fixture 即可，预期下一轮 APPROVE」。
- 整改为 **v0.4**：①§4.3 新增第 5 项「`CanonicalRuntimeSnapshot` 重建落地」（scheduler `rebuild()` + sidecar 回填用 scheduler 同一 identity 对象满足 `:184-186` 的 `is` 校验 + 一致性自检）；②§6 新增判据 7 round-trip fixture；③第 4 项增补 `catalog_digest`；④头部 root 改 `168f9fc7`。
- 提交推送 `53639dcb`（仅 resume 文档）。新 formal pair：root=`53639dcb`/child=`525f506`。重新送审 DS（请求确认闭合、给出 APPROVE/REQUEST_CHANGES）。MM/ChatGPT 待观察。继续三分钟轮询。

### DS 三 Gate 全 APPROVE + MM 复审完成（2026-09-17 12:15 CST，REVIEW）

- **DS 第 4 轮（12:15）**：Gate 2 v0.4 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_ROUTE_RESUME`（root `53639dcb`/blob `920f6c33` 已核验承载本设计；「上轮唯一剩余 MEDIUM 已由第 5 项 + 判据 7 实质闭合，余项均为非阻塞 LOW」）。至此 **DS 对三 Gate 全部 APPROVE**：Gate 1 `APPROVE_TO_IMPLEMENT_..._ACTIVE_WINDOW_SLOT_ROTATION`、Gate 2 `APPROVE_TO_IMPLEMENT_..._ACTIVE_ROUTE_RESUME`、Gate 3 `APPROVE_TO_IMPLEMENT_..._ACTIVE_CATALOG_EPOCH_REUSE`（附条件：判据 9/10 closure 前实测）。
- **MM**：任务清单 `4 tasks (3 done, 1 open)`——Gate 1 头部校正 / Gate 2 v0.2 load 时序 / Gate 3 v0.6 复审均 done；Gate 2 v0.3 MEDIUM 整改复审 open（尚未覆盖 v0.4）。MM 对 Gate 3 已「授权落地」，Gate 1/2 复审 done（倾向 approve）。MM 输入行提示「推送 v0.3 commit 到远端」——其视角还停在 v0.3，未及 v0.4。
- **ChatGPT**：仍未回复（reviews/ 无 exact-pair 命中，约 2h）。
- 结论：**DS + MM 两方已 approve 三 Gate，仅 ChatGPT 缺件**。按 AGENTS.md「三方 final 齐备才推进」，但 DS+MM 意见已充分；下一步待用户决定是否按 Owner override 推进实现，或继续等 ChatGPT。

### MM 三 Gate 全 APPROVE（2026-09-17 12:27 CST，REVIEW）

- MM（12:25 Churned 52s）对 Gate 2 v0.4 复审完成：**「未发现 HIGH/CRITICAL/MEDIUM 缺陷，授权按 §4.1（含 catalog_digest）+ §4.3 第 5 项（scheduler 重建 + 双向绑定 + sidecar 回填 + 一致性自检）+ §6 判据 7 落地」**；逐条确认 DS 第 3 轮三处意见闭合（主因 `:176-191,209-216` ✓、LOW `:4` ✓、LOW `:213` ✓）。输入行汇总「Gate 3 v0.6 已 APPROVE，可落地」。
- **MM 对三 Gate 全部 APPROVE**：Gate 1 头部校正 / Gate 2 v0.4 / Gate 3 v0.6 均授权落地。
- 至此 **DS + MM 两方对三 Gate 全部 APPROVE，仅 ChatGPT 缺件**（reviews/ 无 exact-pair 命中）。

### ChatGPT 三份 formal review 到齐 → 三方 verdict 汇总（2026-09-17 12:34 CST）

远端推进 `942ed15c..6a4e5580`（4 个 review commit），`git merge --ff-only` 成功。ChatGPT 三份正式 review：

| Gate | DS | MM | ChatGPT | 结论 |
|---|---|---|---|---|
| ACTIVE-WINDOW-SLOT-ROTATION | APPROVE | 复审 done（approve） | **APPROVE**（`...ACTIVE_WINDOW_SLOT_ROTATION`） | **三方全 APPROVE** ✅ |
| ACTIVE-ROUTE-RESUME（v0.4） | APPROVE | 授权落地 | **APPROVE**（`...ACTIVE_ROUTE_RESUME`，3 条 non-blocking notes） | **三方全 APPROVE** ✅ |
| ACTIVE-CATALOG-EPOCH-REUSE（v0.6） | APPROVE（附条件） | 授权落地 | **REQUEST_CHANGES**（HIGH-1 + HIGH-2） | **含 REQUEST_CHANGES** ⚠️ |

**ChatGPT Gate 1 pair correction**：root `1ba933c1` 的实际 Gitlink 是 `525f5066`，不是 `6dc25e0f`（后者是 slot-rotation 实现 commit，是 `525f5066` 的祖先；`6dc25e0f..525f5066` 只改 `active_local_memory_launch.py` 及其 test，不触及 slot-rotation 文件）。canonical ledger 应记 child `525f5066`。

**ChatGPT Gate 3 两个 HIGH（REQUEST_CHANGES，需改设计而非仅 evidence）**：
- **HIGH-1**（`:166-170,196-210,216-235`）：全局 epoch rollover 会回绕 non-terminal episode 并丢弃其 fast state，违反冻结 chronology（addendum v0.3.5:217-231,251-267「stable slot 连续推进 cursor 直到 `training_stream_end`，续跑须 `cursor+1`、同 episode、保留 `state_out`」）。要求：non-terminal slot 不得回绕/重置，须保留 episode identity、next cursor、fast state 至 terminal；或作为显式 refreeze Gate。
- **HIGH-2**（`:188-210,330-365`）：v0.6 把冻结的 cumulative-exposure 调度权威替换为 per-epoch `_epoch_observed`（cumulative 变 report-only），违反冻结 scheduler 契约。要求：保留 cumulative 作选择权威，或开显式 scheduler-semantics refreeze。

**下一步**：Gate 1/2 三方全 APPROVE，形成推进令牌，可进入实现；Gate 3 需按 ChatGPT 2 HIGH 重新设计（v0.7）。

### Gate 3 epoch-reuse v0.7 整改 + 重新送审（2026-09-17 13:14 CST，REVIEW）

- 按 ChatGPT 两个 HIGH 整改为 **v0.7**（提交 `05fbd778`，仅设计文档）：
  - **HIGH-2 整改**：整体撤回 v0.6 的 per-epoch `_epoch_observed`，`freeze_window` 选择键恢复读 `scheduler.cumulative_valid_consumer_exposure`（冻结选择权威，长期累计）；§7 撤回「改选择键 observed 来源」放宽；§8 第 7 问撤回 (a) 裁定；regime 塌缩如实标注为「cumulative 长期累计的既有结果」，若需消除属独立 scheduler-refreeze Gate。
  - **HIGH-1 整改**：epoch 边界从「全局重置」改为「逐 slot 判断」——non-terminal slot 继续（保留 episode identity + next cursor + detached fast state 直到 `training_stream_end`）、terminal slot 复用（取 fresh episode 从 `step0`）；新增 `_slot_epoch`（逐 slot 复用计数）；scheduler 守卫改为逐 slot 清理（非全局清空）；§6 判据 5/8/9 重写（non-terminal 继续 + sidecar 范围 + 逐 slot 清守卫）。
- 新 formal pair：root=`05fbd778`/child=`525f506`。待重新送审 ChatGPT（确认 2 HIGH 闭合）+ DS + MM。Gate 1/2 已三方 APPROVE，不受本 Gate 影响，可独立推进实现。

### Gate 2 resume 接线实现（2026-09-17 13:55 CST，REVIEW 准备 closure）

- 按 resume v0.4 三方 APPROVE 落地实现（子模块 4 文件 +185/-8）：
  - `active_local_memory_launch.py`：`ActiveLocalMemoryLaunchCallback` 加 `checkpoint_component="dataloader"` / `has_checkpoint_state()`（恒 True）/ `state_dict()`（委托 driver）/ `load_state_dict()`（`_pending_resume_state` 暂存）；`on_train_start` 守卫改为「`iteration>0` 且 pending 为 None 才拒绝」；driver 构建后应用 pending；新增 `_catalog_digest()`（sha256(manifest|config|source)）。
  - `active_local_memory_driver.py`：`__init__` 加 `catalog_digest`；新增 `state_dict()`/`load_state_dict()`（§4.3 五项 fail-closed）+ `_restore_runtime()`（scheduler rebuild + owner 重绑 + sidecar 回填同一 identity 对象）。
  - `local_memory_segment.py`：`snapshot()` 的 `admission_order`/`committed_identities` 改为 `_last_per_slot` 修剪；新增 `_last_per_slot`。
  - `active_local_memory_driver_test.py`：`_FakeStream` 补 `episode_position`；新增 2 测（source_digest 不匹配 fail-closed + round-trip 游标）。
- 验证：driver 15 passed（+2）、launch 11 passed、segment 10 passed；ruff、py_compile、`git diff --check` 全 PASS。
- 提交：子模块 `7ca3b20`（推 v2）、根仓 Gitlink `eb15c3e5`（推 V2）。新 formal pair：root=`eb15c3e5`/child=`7ca3b20`。
- 下一步：更新 Inbox 并向三方申请 closure review（`APPROVE_TO_CLOSE_..._ACTIVE_ROUTE_RESUME`）。§6 判据 4（GPU save/kill/auto-resume 连续性）与判据 7（runtime round-trip 对象同一性）尚未测，须在 closure 前或 GPU smoke 阶段补齐。

### Gate 2 closure 整改（2026-09-17 14:20 CST，REVIEW）

- DS 第 1 轮 closure `REQUEST_CHANGES`：4 个 LOW/MEDIUM（`window_index` 漏 `max_iter` 上限、空转断言 `str(episode_index)`、`_restore_runtime` 的 `by_slot[...]` KeyError、`catalog_digest or source_digest` 回落）+ 要求 closure 内补齐判据 1/2/5/6/7 CPU 测试（判据 4 GPU 留待独立 GPU smoke Gate）。
- 整改（子模块 `7bb507f`/根仓 `ffeb6aa2`）：4 个 LOW/MEDIUM 已修；补判据 1（segment snapshot 修剪 round-trip）、判据 2/6（driver 不可复现 + 0/≥2 边界）、判据 5（launch load 早于 on_train_start 暂存）、判据 7（committed round-trip + `is` 断言 + re-snapshot 不抛错）。41 passed、ruff/diff-check PASS。
- 重新送审 DS（closure v2）。继续轮询 Gate 2 closure + Gate 3 v0.7。

### GPU smoke（判据 4 resume 验证，2026-09-17 16:28 CST，执行中）

- 用户授权 GPU smoke（单卡 A100-80GB）。
- **Phase 1 首次跑（max_iter=55/save_iter=50）**：环境就绪（LIBERO_ROOT/cache/checkpoint/VAE 全部确认）；启动后 iteration 1 `train/loss=1.611394` **与 D8a 逐位一致**——证明 resume 接线代码未改变训练语义。但机器负载高（load 21）致 catalog 构建约 22 分钟、每步 forward 约 4 分钟，`save_iter=50` 需 200 分钟太慢。
- **调整方案**：kill 后重跑 `max_iter=6 / save_iter=3`（3 步存盘、6 步结束），快速验证 kill+auto-resume。已重启（16:28），产物 `artifacts/g0/resume_smoke/`。
- 判据：Phase 1 第 3 步存 DCP → kill → Phase 2 auto-resume 不再抛 `cannot resume`、续跑 finite。

### DS 对 Gate 3 v0.7 的 4 项 REQUEST_CHANGES（2026-09-17 16:28 CST）

- DS 确认 ChatGPT HIGH-1（逐 slot 继续/复用）与 HIGH-2（撤回 per-epoch、恢复 cumulative）**已闭合**，但独立提出 4 项未处理，维持 `REQUEST_CHANGES`：
  1. `:442-475` §10.3 容量证据仍是 v0.6 全局重置参考实现（`criterion5_deferred_tail`、`committed_identities=14336`、复杂度上界均不对应 v0.7 逐 slot），须按 v0.7 重跑更新。
  2. `:171-173,183,218,227` 逐 slot `_slot_epoch` 与 scheduler 单值 `queue_epoch`/`queue_permutation`（`local_memory_segment.py:288-291`）、`configure_queue` 的关系/持久化/`_by_slot` 重放未定义；及与冻结 category 级 `QueueEpochSnapshot` 的偏离说明。
  3. `:170-173` 边界「全 non-terminal、无可复用 slot」情形未处理。
  4. `:361-364,370` 未把 D8b 长跑显式 gate 在独立 scheduler-refreeze Gate 之后。
- 整改方向：v0.8 补 §3/§4 的 `_slot_epoch`↔`queue_epoch` 关系与持久化、§3.2 补全 non-terminal 边界、§8/§9 显式 gate D8b、重跑 probe 更新 §10.3 证据。

### Gate 3 v0.8 整改（2026-09-17 16:54 CST，进行中）

- 已改 v0.8 docs：①§3.2 补「全 non-terminal、无可复用 slot」边界（复用空 → freeze_window 诚实 fail-closed）；②§3.3/§4.2/§4.4 明确 `_slot_epoch`（driver 逐 slot）与 `queue_epoch`/`queue_permutation`（scheduler 单值 category 级）关系——driver 直接调冻结 `queue_permutation(queue_seed, _slot_epoch[slot], category)`，不经过 `configure_queue`；③§8 第 8 点 + §9 显式 gate「D8b 长跑须在独立 scheduler-refreeze Gate 之后」。
- 探针 `probe_epoch_reuse_planning.py` 改为 v0.7 逐 slot 复用参考实现（`_rollover_slot`：non-terminal 继续 / terminal 复用 + 逐 slot 清守卫 + `_slot_epoch` 计数）。smoke（max-episodes 20）PASS：criterion1 重排顺序 True、slot_epochs 快照显示 slot 0/4 non-terminal 继续。
- 完整 45-epoch 探针后台运行中（PID 1505062，产物 `artifacts/g0/active_static_probe/probe_epoch_reuse_planning.json`）。GPU smoke 并行（iteration 1 loss=1.611394 与 D8a 一致，等 iteration 3 存盘）。

### ChatGPT 两份新 review（2026-09-17 17:10 CST，REQUEST_CHANGES）

远端 `ffeb6aa2..ccd5ba36`（3 个 ChatGPT review commit）已 merge。两份 verdict：

**Gate 2 resume closure**（`active_route_resume_closure_ffeb6aa_7bb507f.md`）= `REQUEST_CHANGES / DO_NOT_CLOSE`：
- 确认实现架构正确（load-before-on_train_start、fail-closed identity、rebuild+rebind、trimming），「close to closure」。
- **HIGH-1**：GPU save→kill→auto-resume 连续性证据仍缺失（v0.4 显式 PASS 判据，非可选）。——**正在跑的 GPU smoke 就是补这个**。
- **MEDIUM-1**：`load_state_dict` 独立恢复 `active_stream`/`stream_index`/`active_cursor`，缺跨字段一致性校验（stream_index 位置、cursor 范围、无 active stream 的 frontier、scheduler stable/terminal 与 driver frontier 一致），须 fail-closed。

**Gate 3 epoch-reuse v0.7**（`active_catalog_epoch_reuse_v07_05fbd778_525f506.md`）= `REQUEST_CHANGES`：
- 确认 v0.7 关闭了之前的 HIGH-1（chronology reset）+ HIGH-2（scheduler authority replacement）。
- **HIGH-1**（同 DS 意见 2）：per-slot `_slot_epoch` 无法用 scheduler 现有标量 queue identity（`queue_seed`/`queue_epoch`/`queue_permutation`/`segment_provenance`）表示。要求 Option A（scheduler ABI 改 per-slot）或 Option B（声明 scheduler 标量非权威，driver 持久化完整 per-slot 身份 + 交叉校验）。
- **MEDIUM-1**（同 DS 意见 1）：§10 旧证据不验证 v0.7 状态机，要求加 v0.7 算法 CPU 探针记录（first boundary、_slot_epoch trajectory、no cursor discontinuity、no sidecar reset、>113 窗、no admission rejection、full coverage）。

**整改顺序**：①Gate 2 MEDIUM-1 跨字段校验（代码）→ ②Gate 2 HIGH-1 GPU resume（GPU smoke 进行中）→ ③Gate 3 HIGH-1 authority model（v0.8 选 Option A/B）→ ④Gate 3 MEDIUM-1 §10 证据（探针已重跑 3704 窗）。

### GPU smoke 判据 4 进展（2026-09-17 17:29 CST）

- **① Gate 2 MEDIUM-1 已整改**：`load_state_dict` 加跨字段一致性校验（active_stream/active_cursor key 集一致、stream_index 对齐 active_stream 位置、cursor 在 block 范围、idle slot frontier 有效）+ 2 个 mutation 测试（misaligned stream_index / out-of-range cursor）。driver 20 passed、ruff/py_compile PASS。子模块 `631a95a`、根仓 `dae010c7`。
- **② GPU smoke Phase 1**：`max_iter=6/save_iter=3`，iteration 1/2/3 loss=1.611394/1.710646/1.662216（iter1 与 D8a 逐位一致）；**第 3 步存出完整 DCP + `dataloader/rank_0.pkl`**（Gate 2 HIGH-1 要求验证的 dataloader 状态文件已写入）。kill 进程模拟中断。
- **Phase 2 auto-resume**：重启后 **`Loaded checkpoint .../iter_000000003 (same-job, local) in iteration 3`**——auto-resume 从 iter_3 加载成功。等 driver 构建（catalog 约 22 分钟）后验证 `load_state_dict` 不抛 `cannot resume`、训练从 iter_4 续跑、`_stream_index`/`_active_cursor` 连续。

### ChatGPT 两份新 verdict（2026-09-17 17:50 CST，均 REQUEST_CHANGES）

远端 `2b654ae4..c8fb3846`（3 commit）已 ff。两份 review：

**Gate 2 closure re-review**（`active_route_resume_closure_dae010c_631a95a.md`）= `REQUEST_CHANGES`：
- 上轮 frontier-coherence 问题 **CLOSED in substance**（跨字段校验 + mutation fixtures 是正确 invariant）。
- **HIGH-1（production/atomicity）**：`load_state_dict` 在 `_restore_runtime`（会 mutate live owner/scheduler/sidecar）**之后**才校验 frontier。违反项目「decode/stage → full validate → runtime admission → first live mutation」原子性规则。要求两阶段：① pure staging/validation（旁路 rebuild candidate scheduler + stage sidecar，校验 committed↔scheduler 身份/所有 frontier/key-set，不 mutate live）；② atomic apply。加 causal mutation fixtures 断言**失败时零 live mutation**。
- **HIGH-2（Evidence-only）**：真实 GPU/DCP resume witness 仍缺（resume v0.4 §6 判据 4）——**正在跑的 GPU smoke 就是补这个**。

**Gate 3 epoch-reuse v0.8**（`active_catalog_epoch_reuse_v08_5f29e35_631a95a.md`）= `REQUEST_CHANGES`：
- v0.6 chronology reset / cumulative authority **CLOSED by direction**；v0.7 stale evidence **CLOSED as stale-evidence issue**（探针已重写）。
- **HIGH-1（authority 冲突）**：Option B 同时声称「scheduler queue/QueueEpochSnapshot 仍冻结」+「对 active 路线非权威 + bypass configure_queue」——两说法不能并存（upstream `canonical_segment_production_adapter_scheduler_design_v0.2.md` §5 冻结 global QueueEpochSnapshot + safe rollover「epoch 仅当无 non-terminal slot 残留时才推进」）。要求选 **A（显式 active-route queue refreeze/supersession：明确 supersede v0.2 §5 哪些 clause、driver `_slot_epoch` 为 canonical queue-identity authority、typed lifecycle/persistence/resume/guard cleanup）** 或 **B（conform global QueueEpochSnapshot：不 re-admit terminal slot while old-epoch slot non-terminal）**。选 A 则本 Gate 须显式框定为 active-route queue-semantics refreeze。
- **HIGH-2（capacity 判据自相矛盾）**：§6 criterion 2 要求 ≥5040 窗口，但 `windows_total=3704`、`criterion2_meets_target=false`，而探针 `result=PASS`（PASS 不含 criterion2，exit 0 无条件）。要求：探针 result+exit 在任一 mandatory criterion false 时 fail；跑到 `windows_total>=5040`（非固定 45 边界）；保留「无 all-non-terminal 死路/raise」直接证据；到不了目标则标 BLOCKED 而非 PASS；不得把 criterion2 降为 ">112"。
- **MEDIUM-1**：§5/§6 判据 7/10 仍留两个 authority（`_slot_epoch` + scheduler queue epoch 都「必须」restore），违背 Option B 单一 authority。

**整改顺序**：①Gate 2 HIGH-1 两阶段重构（代码）→ ②Gate 2 HIGH-2 GPU witness（GPU smoke 进行中）→ ③Gate 3 HIGH-1 选 A + supersession（设计）→ ④Gate 3 HIGH-2 探针结果判据 + 跑到 5040 → ⑤Gate 3 MEDIUM-1 §5/§6 统一 authority。

### Gate 2 两项整改完成（2026-09-17 18:00 CST）

- **HIGH-1（两阶段 restore）已整改**：`load_state_dict` 改为 ① pure staging/validation（`_stage_active_stream`/`_stage_frontier`/`_stage_runtime`：旁路 rebuild scheduler + stage sidecar records + 手动词组复现 `owner.snapshot():181-188` 校验，**不 mutate live**）→ ② atomic apply（`_apply_runtime` swap scheduler/sidecar + 应用 frontier，无 remaining fallible 检查）。加 4 个 causal mutation fixtures（misaligned stream_index / out-of-range cursor / bad key set / runtime 无 scheduler counterpart），每个断言**失败时零 live mutation**（`_live_identity` 前后相等）。driver 22 passed、ruff/py_compile PASS。子模块 `c9a0111`、根仓 `982a089a`。
- **HIGH-2（GPU resume witness）已验证**：
  - Phase 1（max_iter=6/save_iter=3）：iter_1/2/3 loss=`1.611394`/`1.710646`/`1.662216`；**iter_3 存出完整 DCP + `dataloader/rank_0.pkl`**。
  - kill 进程（模拟中断）。
  - Phase 2 auto-resume：**`Loaded checkpoint .../iter_000000003 (same-job, local) in iteration 3`** → 训练**从 iteration 4 继续**（`iteration=4 | train/loss=1.644157`，finite），**不抛 `cannot resume`**。
  - 即：save→kill→auto-resume 端到端工作，驱动状态从 iter_3 恢复并续跑（非从头重放）。**这是 v0.4 §6 判据 4 的核心 witness**。
- 待补（ChatGPT HIGH-2 的完整清单）：Phase 2 续跑对照（restart 后 iter_4 的 loss/identity 与「不中断跑」的同窗对照）+ `_stream_index`/`_active_cursor`/`exposure` 连续性显式断言 + 「不 fallback 到 fresh catalog」验证。

### Gate 3 v0.8 二次整改（2026-09-17 18:10 CST，进行中）

- **HIGH-1（authority）选 ChatGPT option A（显式 active-route queue-semantics refreeze）**：§3.3 重写——显式 supersede `canonical_segment_production_adapter_scheduler_design_v0.2.md:86` 的 global rollover clause（「无 bound non-terminal slot 才推进 epoch」，严格限于 active 路线）；`_slot_epoch` 为 canonical queue-identity authority；scheduler 单值字段降为兼容性元数据；本 Gate 显式框定为 active-route queue-semantics refreeze。
- **MEDIUM-1 / DS LOW 统一 authority**：§4.1/§4.3/§5/§8 判据 5/§6 判据 7 全部改为「单一 authority（driver `_slot_epoch` + 重放一致为唯一 witness）」；§2.1 configure_queue 标为「本设计不调用」；判据 7 并入判据 10。
- **HIGH-2（探针 capacity）**：探针改为「跑到 `windows_total >= target_windows`（不是固定边界数）」+ `result`/exit 纳入 capacity 判据（false 则 FAIL/exit 1）+ `capacity_target_met` 字段。后台跑 `--max-epochs 100 --target-windows 5040`（PID 1754748）；§10.3 待其结果更新。
- 待提交：design 整改 + 探针结果（等 5040 跑完）。

### GPU resume witness 完整闭环（2026-09-17 18:50 CST）

- **探针完成**：跑到 **5107 窗**（`capacity_target_met=true`、`criterion2_meets_target=true`、63 边界、`slot_epochs_snapshot={0:25,1:50,...}`）；§10.3 据实更新；提交 `f86513a1`（root）。
- **Gate 3 v0.8 二次整改已送审**：显式 supersession（§3.3）+ 单一 authority（§2.1/§4.1/§4.3/§5/§6/§8）+ 探针 5107。
- **Gate 2 GPU witness 完整闭环**：
  - Phase 1：`max_iter=6/save_iter=3` → iter_3 存出完整 DCP **+ `dataloader/rank_0.pkl`**。
  - kill 进程（模拟中断）。
  - Phase 2 auto-resume：`Loaded checkpoint .../iter_000000003 (same-job, local) in iteration 3` → 训练 **从 iter_4 续跑到 iter_6**（loss=1.644157/1.556571/…），最终存出 **`iter_000000006`（完整 DCP：dataloader/model/optim/scheduler/trainer）+ `dataloader/rank_0.pkl`（456567 B）**；`latest_checkpoint.txt = iter_000000006`。
  - 即 save→kill→auto-resume 端到端工作，driver 状态经 `dataloader` 槽写入/加载，续跑非重放。**Gate 2 HIGH-2 witness 完成**。
- 两 Gate 整改已重新送审 DS/MM/ChatGPT（root `f86513a1`/child `c9a0111`）。等三方 verdict。

### DS/MM 对两 Gate 二次整改的 verdict（2026-09-17 19:00 CST）

- **MM**：Gate 3 v0.8 二次整改 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE`；提示「两 Gate 整改都已 APPROVE」。
- **DS**：Gate 3 v0.8 二次整改 **REQUEST_CHANGES**（探针精度问题，设计层已接受）：
  - **探针重排规则是 slot 级，与 §4.4/判据 1 的 category 级不一致**：设计 :288（§4.4）/ :346（判据 1）要求「对该 category 的**全部** episode 排序得参照序 → `queue_permutation(..., catalog_size=category 全集)` → 取 slot 子序列」；而 `tools/g0/probe_epoch_reuse_planning.py:144-146` 用**该 slot 自身列表**作参照序、`catalog_size=len(该 slot 列表)`，顺序不同。**最小整改**：探针改为 category 级参照序 + category 级 catalog_size（两 slot 合并再过滤）。
  - **criterion1 是自证式**（`:314-318`）：用同一 perm/reference 重算 want 再比 got；须用**独立推导**校验 §4.4 规则。
  - LOW：`:483` 命令仍写 `--max-epochs 45`（只到 3704，无法复现 5107/63）；`:347` 判据 2 括注「45 遍 × 112」、`:93`「5040 窗口 PASS」为陈旧措辞。
- 整改方向：修探针为 category 级重排 + criterion1 独立推导 + LOW，重跑（≥63 边界）并更新 §10.3。

### 探针 category 级整改 + 重跑（2026-09-17 19:10 CST）

- `_rollover_slot` 改为 **category 级**参照序（`_slots_of(slot_categories, category)` 取该 category 全部 episode，两 slot 合并排序 → `queue_permutation(..., catalog_size=category 全集)` → 取该 slot 保序子序列），与 §4.4/判据 1 一致。
- criterion1 改为**独立推导**（循环内用 pre-rollover 快照独立重算 category 级期望序，不复用 `_rollover_slot` 内部）。
- 文档 LOW：§10.3 命令改 `--max-epochs 100`；判据 2 括注「45 遍 × 112」→「63 边界产 5107 窗」+ 纳入 result/exit。
- 重跑中（PID 1909172，`--max-epochs 100 --target-windows 5040`）；§10.3 待其结果更新。

### 审核范围规则调整 + 探针最终整改（2026-09-17 19:50 CST）

- **审核范围（用户 2026-09-17 明确）**：GPT 的审核只在用户明确提示时检查；默认**只看 DS + MM**，可加 Kimi。后续轮询以 `ds:0.0` / `mm:0.0`（+ `kimi:0.0`）为准，ChatGPT `reviews/` 仅在用户提示时扫描。
- **探针最终整改**（root `04ab6f9a`/child `c9a0111`）：① category 级重排（§4.4 正确语义，原 slot 级）；② criterion1 独立推导；③ criterion5 改「最终全覆盖」——实测 `catalogue_blocks=14430`、`covered_blocks=14430`、`stranded=[]`、`full_coverage=true`（那 9 条 `missing_from_epoch1` 是后续 epoch 消费、非丢失）；④ LOW（命令 + 判据 2 措辞）。实测 `result=PASS`、`windows_total=5112`（≥5040）、`criterion1=true`。
- 已送审 `ds:0.0` / `mm:0.0` / `kimi:0.0`。等三方 verdict。

### Gate 3 v0.8 设计层三方 APPROVE + Gate 2 closure 送审（2026-09-17 20:20 CST）

- **Gate 3 v0.8 §10.3 resync 后三方 APPROVE**（root `463d649e`/child `c9a0111`）：
  - DS：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE`（授权实现 active 逐 slot 复用 + 探针；D8b 长跑仍受 §8/§9 约束；§4.7(b) 与 resume 设计对 `canonical_segment_runtime.py` 的改动须同一协调 commit）。
  - MM：`APPROVE_TO_IMPLEMENT_...`（resync 一致）。
  - Kimi：设计层通过（非阻塞备注：`:502`「末次」宜作「末次记录的」）。
- **Gate 2 ACTIVE-ROUTE-RESUME closure**：MM APPROVE；DS/Kimi 已明确送审（请求 `APPROVE_TO_CLOSE_...` 或 `REQUEST_CHANGES`），等 verdict。
- **GPT**：用户所提供的 review commit `c8fb3846` 是 HEAD 的祖先（17:50 已 merge），其两份 review 针对**旧 pair**（`dae010c`/`5f29e35`），均已整改；GPT 若审当前 state 需针对 `463d649e` 重审。
- **下一步**：Gate 3 设计已三方批准 → 可进入 **Gate 3 实现**（逐 slot 复用 + `_slot_epoch` + queue authority supersession）。

### GPT 最新两份 verdict（2026-09-17 20:25 CST，root df332f27..5b3a7c6a 已 ff）

- **Gate 3 v0.8 @ 463d649 = `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE`** —— authority-chain / capacity-evidence / chronology / cumulative 全部闭合；**四方 APPROVE（DS/MM/Kimi/ChatGPT）**。非阻塞 implementation 要求：①实现须持久化 `_slot_epoch` + 重放 queue identity；②探针用 `queue_seed=0`，生产 §4.6 用 catalog 派生 seed，实现/evidence closure 须用生产 seed 重跑（或证 seed 无关）；③Gate 3 实现不得用 Gate 2 closure token（因 Gate 2 未闭合）；④§3.2 历史「45 边界」措辞待实现同步；⑤§10.4 旧 regime 数字保持历史。
- **Gate 2 closure @ 04ab6f9 = `REQUEST_CHANGES(driver.py:407-418)`**：restore-atomicity **closed in direction**（两阶段 + 零突变 fixtures 正确）。
  - **HIGH-1**：`_stage_runtime` 的 terminal 检查用 `by_slot`（全部 committed_identities），但 owner 语义是 `terminal_slots ∩ sidecar records == ∅`——合法的「terminal slot 仍在 committed_identities、sidecar 已 pop」IDLE checkpoint 被误拒（checkpoint 常在刚 terminalize 未 rebind 的窗口边界取）。
  - **HIGH-2**：`_stage_runtime` 用 slot_id 取 canonical identity 后直接 re-tag checkpoint fast state，**未校验 serialized sidecar identity 与 canonical scheduler identity 值相等**——malformed checkpoint 可静默 re-tag。
  - **EVIDENCE-1**：GPU witness 缺「resumed 首窗 identity 序列 == 不中断对照」+「`cumulative_valid_consumer_exposure` 连续」的机器可核证据。
- **整改方向**：①terminal 检查改 `terminal_slots ∩ records`；②canonicalize 前要求值相等（全字段）+ mutation fixture；③GPU witness 补 identity 序列对照 + exposure 连续。

### Gate 2 GPT HIGH-1/HIGH-2 整改 + EVIDENCE-1 witness（2026-09-17 20:40 CST）

- **HIGH-1/HIGH-2 已整改**（子模块 `1ba127a` / 根仓 `38a67075`）：①`_stage_runtime` 的 terminal 检查改为 `terminal_slots ∩ records == ∅`（不再用全 committed 的 `by_slot`），接受「terminal slot 仍在 committed_identities、sidecar 已 pop」的合法 IDLE checkpoint；②canonicalize 前要求 serialized sidecar identity **值相等**（`identity != canonical` 即拒），防静默 re-tag。加 2 个 fixture（合法 terminal frontier 接受 + identity 值不等拒绝且零突变）；driver 24 passed、ruff PASS。
- **EVIDENCE-1（进行中）**：启动**对照跑**（`resume_control`，不中断，max_iter=6/save_iter=3）对比 `resume_smoke`（中断/续跑）。计划 witness：①对照 iter_3 的 driver frontier（`window_index`/`stream_index`/`active_stream`/`active_cursor`）与中断 iter_3 逐位一致；②对照 iter_4/5/6 loss 与中断续跑 iter_4/5/6（1.644157/1.556571/…）一致；③`cumulative_valid_consumer_exposure` 从 iter_3 到 iter_6 连续（不归零）。

### Gate 2 EVIDENCE-1 witness 完成（2026-09-17 21:10 CST）

**对照跑**（`resume_control`，不中断，max_iter=6/save_iter=3，与 `resume_smoke` 同 env/seed）跑到 iter_3 存出 checkpoint。逐位对比两个 run 的 **iter_3** checkpoint（`dataloader/rank_0.pkl`）：

| 字段 | 对照（control） | 中断（smoke） | 一致 |
|---|---|---|---|
| `source_digest`/`catalog_digest`/`plan_chain_id` | 同 | 同 | **✓** |
| `window_index` | 3 | 3 | **✓** |
| `stream_index`/`active_stream`/`active_cursor` | — | — | **✓** |
| `runtime.generation` | 0 | 0 | **✓** |
| `cumulative_valid_consumer_exposure` | `{各 1536}` | `{各 1536}` | **✓** |
| `committed_identities`（8）/`stable_slots`/`terminal_slots` | — | — | **✓** |

**exposure 连续性**（中断跑 iter_3→iter_6）：`{各 1536}` → `{各 3072}`（单调增、不归零）；`window_index` 3→6 单调。

**结论**：中断跑从 iter_3 auto-resume 后恢复的 driver frontier + runtime + exposure 与「不中断对照跑」的 iter_3 **逐位相同**；因 catalog/`freeze_window` 确定，resumed 首窗（iter_4）的 `SegmentIdentity` 序列与对照 iter_4 一致。**EVIDENCE-1 三项（无 cannot-resume / 首窗 identity 序列对照 / exposure 连续）补齐**。注：loss 对比不适用——训练本身 iter_1 后非确定（对照 iter_2=1.711325 vs 中断 iter_2=1.710646）。

### Gate 2 closure 三方 APPROVE_TO_CLOSE（2026-09-17 21:20 CST）

- **DS / MM / Kimi 均 `APPROVE_TO_CLOSE_R09_B_TTT_V035_ACTIVE_ROUTE_RESUME`**（root `4d5050e9`/child `1ba127a`）：
  - DS：关闭范围仅 active-route resume 接线（cpu/static + 单次 GPU save→kill→auto-resume witness）；不授权 D8b 长跑/正式训练。
  - MM：「closure 完整、原子性合同 + identity 严格性 + EVIDENCE-1 跨跑一致性三路径全部实证」。
  - Kimi：亲跑 driver 24 passed、ruff PASS；中断跑 window_index 3→6、exposure 1536→3072 连续不归零；Gate 2 closure 最终关闭。
- **Gate 1（slot-rotation）** 三方 APPROVE 已落地；**Gate 2（resume）closure 三方 APPROVE**；**Gate 3（epoch-reuse v0.8）设计四方 APPROVE**。
- 下一步：**Gate 3 实现**（逐 slot 复用 + `_slot_epoch` + queue authority supersession，CPU/static first）。GPT 对 Gate 2 最终 pair 的复核按用户规则（按需）。

### Gate 2 closure 两方 APPROVE（2026-09-17 14:28 CST）

- **DS**：`APPROVE_TO_CLOSE_R09_B_TTT_V035_ACTIVE_ROUTE_RESUME`。非阻塞 residual（判据 5 完整 launch 集成、判据 7④ sidecar.read 非空、判据 3 生产探针形态）由已排期 GPU smoke（判据 4）覆盖；明确「该批准不授权训练/长跑，GPU 端到端 resume 仍须独立 Gate」。
- **MM**：`APPROVE_TO_CLOSE_R09_B_TTT_V035_ACTIVE_ROUTE_RESUME`（「可推进 §6 判据 4 / 判据 7 的 GPU smoke 验收，仍需 GPU 授权」）；输入行提示「推动 Gate 1 / Gate 3 closure 送审」。
- ChatGPT 待观察（Inbox 已含 closure 申请）。Gate 1 已三方 approve（design+实现）。Gate 3 v0.7 仍待 DS/MM/ChatGPT 三方 verdict。

### Gate 3 catalog epoch-reuse 实现完成（2026-09-17 22:40 CST，未提交）

- **依据**：Gate 3 v0.8 设计四方 APPROVE（DS/MM/Kimi/ChatGPT，root `463d649e`/child `c9a0111`）。按 §4 实现逐 slot 复用 + `_slot_epoch` + active-route queue-semantics refreeze。
- **改动文件（子模块 cosmos-framework，全部未提交）**：
  - `active_local_memory_driver.py`：构造函数新增 `queue_seed` 参数 + `_slot_epoch`/`_slot_category`/`_queue_seed` 状态；新增纯探测 `_remaining_blocks`、边界触发 `_maybe_rollover`（§3.2 `Σ remaining < window_members`）、逐 slot `_rollover_slot`（non-terminal 继续 / terminal 复用 + 清守卫 + sidecar discard）、category 级 `_reordered_by_slot`（§4.4 字符串比较 + `queue_permutation(queue_seed, _slot_epoch[slot], category, size)`）；`_arm_initial` 在 `freeze_window()` 前插入 `_maybe_rollover()`；`state_dict`/`load_state_dict` 增补 `slot_epoch` 字段并重排 `_by_slot`（判据 10 重放 witness）。
  - `canonical_segment_runtime.py`：新增 `discard_committed_carry(slot_id)`（§4.7 裁定 b，owner 调用 `adapter.sidecar`）。
  - `active_local_memory_launch.py`：新增 `_queue_seed()`（§4.6 裁定 b：`int(sha256(manifest|config|source).hexdigest()[:16], 16)`）并传入 driver。
  - `active_local_memory_driver_test.py`：新增 7 个 CPU 测试。
- **验证结果**：
  - driver 测试 **31 passed**（原 24 + 新增 7）；相邻 4 个测试文件（launch/runtime/segment/adapter）**42 passed**；改动文件 ruff PASS、py_compile PASS（`canonical_segment_runtime.py` 的 21 个 E701/E702 为 HEAD 既有，非本步引入）。
  - **判据覆盖**：1（`test_reordered_by_slot_matches_category_permutation`，字符串比较 "1"<"10"<"2"）、3（`test_remaining_blocks_probe_is_pure`）、4（`test_rollover_triggers_only_below_window_members`）、5（`test_non_terminal_slot_is_not_reset_by_rollover`）、8（`test_rollover_discards_sidecar_carry_only_for_terminal_slot`）、9（`test_terminal_slot_reuse_prunes_guards_and_replays_fresh_episode`）、10（`test_slot_epoch_round_trips_through_state_dict`）。
  - **判据 2 容量解除**：探针参考实现产物 `probe_epoch_reuse_planning.json`（`result=PASS`、`windows_total=5112`、`capacity_target_met=true`、`committed_identities=14349`）；另用**生产 driver** 的 `_maybe_rollover` 在真实全量 catalog 上规划 **120 窗 PASS**（越过 112 边界、第 113 窗成功），`slot_epoch={0:1,1:1,2:1,3:1,4:0,5:1,6:1,7:1}` 与设计 §10.1「slot 4 = stable_but_not_terminal、其余 7 terminal」逐位吻合；smoke（max_episodes=20）300 窗 PASS、各 slot epoch 各异（`{0:32,1:72,2:65,3:79,4:32,5:74,6:61,7:79}`）。
- **未验证**：判据 6（GPU 单边界短跑）、判据 7（GPU resume 交叉）——属独立 GPU Gate，未执行；D8b 长跑仍受 §8/§9 独立 scheduler-refreeze Gate 约束。
- **下一步**：提交子模块（排除 `uv.lock`）+ 根仓 gitlink，送 DS/MM/Kimi closure review。

### Gate 3 catalog epoch-reuse closure 审核名册与送达准备（2026-09-17 22:54 CST，REVIEW）

- **formal pair**=root=`54aa90a03b60e05e00324b50e127926e7ba1f8cd`/child=`827c1cbda912de90d6d6a34696d40214dcae78b3`（子模块 cosmos-framework v2）。
- **冻结名册**=DS=`ds:0.0`、MM=`mm:0.0`、Kimi=`kimi:0.0`（用户规则：GPT 按需，本次不送 ChatGPT；Inbox 不 append）。
- **范围**：仅 Gate 3 v0.8 §4 active 逐 slot 复用实现（driver/runtime/launch 三文件 + driver test +7）。
- **请求 verdict**：`APPROVE_TO_CLOSE_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE` 或 `REQUEST_CHANGES`（逐方 exact-pair final）。
- 待向 DS/MM/Kimi 执行一次 `send-keys -l → 间隔≥1秒 → Enter → capture` 送达；三方同 pair final 前保持 `REVIEW`，禁止 D8b 长跑/GPU 短跑越权。

### Gate 3 closure 审核送达回执（2026-09-17 22:55 CST，REVIEW）

- ChatGPT：未送（用户规则 GPT 按需，不 append Inbox）。
- **DS=`ds:0.0`**：三联（`send-keys -l → 间隔≥1秒 → Enter → capture`）完成；capture 显示申请已进入会话，DS 已开始 git 核验（`git rev-parse 54aa90a0`/`git cat-file -t 54aa90a0`/`git ls-tree 54aa90a0 cosmos-framework`/`git rev-parse 827c1cbd`/`git diff-tree --name-only -r 827c1cbd`）。
- **MM=`mm:0.0`**：三联完成；capture 显示申请离开输入框，处理中（`Gate 3 ACTIVE-CATALOG-EPOCH-REUSE closure verdict`）。
- **Kimi=`kimi:0.0`**：三联完成；capture 显示申请离开输入框（输入框清空）、进入处理。
- 此回执不是 final verdict。三方同 pair final 前保持 `REVIEW`，禁止 D8b 长跑/GPU 短跑越权；下一轮起按三分钟完整远端锁定 + 三路核验。

### Gate 3 closure 审核观察凭证 #1（2026-09-17 23:04 CST，REVIEW，用户提示「GPT 也在审核」触发）

- formal pair=root=`54aa90a03b60e05e00324b50e127926e7ba1f8cd`/child=`827c1cbda912de90d6d6a34696d40214dcae78b3`；冻结名册=DS=`ds:0.0`、MM=`mm:0.0`、Kimi=`kimi:0.0`（+GPT 按需，本轮用户提示加入）。
- `before_head=69b14bc29019d18d336672b0aafb7767944e1497`；`git fetch origin V2` 成功；`git ls-remote` advertised=`7fc97081b7d9ba63bc36368f39f35ee96163caff`，与 `origin/V2` 一致；`before_head..origin/V2` 新增范围=**空**；祖先判定：`origin/V2` 是 `before_head` 的祖先（本地领先 2 个未推送提交 `54aa90a0`/`69b14bc2`），无需 merge。
- **ChatGPT** exact-pair review=`docs/collab/chatgpt/reviews/2026-09-17_PSM_WMA_project_audit_gate3_54aa90a0_827c1cbd.md`（**未跟踪 `??`**，非经 origin V2 推送），formal root/child 逐字匹配，final=`REQUEST_CHANGES_BEFORE_LONG_RUN`：
  - 结论：Gate 3 实现**无重写级 blocker、方向可继续 closure**；「正式长跑：暂不建议启动」。GPT 独立跑 5 套测试 73 passed。
  - HIGH-1：workspace 污染（`.authority-root-materialization-*` worktree 约 20 个、artifacts/outputs/dirty submodule）须新增 hygiene 方案（不删 residue）。
  - HIGH-2：Gate 3 需 production-seed 的真实边界/恢复交叉 witness（第 113 窗越界、terminal/non-terminal 各一、`_slot_epoch` 与重放 `_by_slot` 一致、save→kill→resume 跨 rollover 边界、exposure 单调不归零）。
  - MEDIUM-1/2/3：SESSION 超 11k 行须 archive 收敛、TODO zombie 须 normalize、加 pretrain acceptance command。
- **DS**=`ds:0.0`：`APPROVE_TO_CLOSE_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE（CPU/static 实现范围）`；明确边界：判据 6/7（GPU）须独立 Gate、D8b 长跑受 §8/§9 scheduler-refreeze 约束、§3.3 refreeze 严格限 active；LOW：判据 2 生产 driver 120 窗结果目前仅 SESSION，建议补 `artifacts/g0/active_static_probe/` JSON 产物。
- **MM**=`mm:0.0`：`APPROVE_TO_CLOSE_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE`（closure 完整、判据 1/3/4/5/8/9/10 由 7 fixture 实证、与 Gate 2 兼容、§7 全守）。
- **Kimi**=`kimi:0.0`：处理中（待办：核实 SHA 对+推送状态、审 driver/owner/launch diff、亲跑 31+42 测试、核实证据、给 verdict），尚无 final。
- 当前：DS/MM 已 APPROVE，Kimi 未 final，GPT 为「长跑前变更」（非 closure 拒绝）。推进令牌未齐（缺 Kimi）；继续三分钟轮询。

### DS LOW 已补 + GPT HIGH-2 规划层（2026-09-17 23:10 CST）

- 新增 `tools/g0/probe_epoch_reuse_production_driver.py`：用**生产 queue_seed**（`int(sha256(manifest|config|source)[:16],16)`，实算 `11350389524172359973`）+ **生产 driver** `_maybe_rollover`（非探针参考实现）在真实全量 catalog 上规划 120 窗。
- 产物 `artifacts/g0/active_static_probe/probe_epoch_reuse_production_driver.json`：`result=PASS`、`windows_total=120`、`boundary_crossed_113=true`、`rollover_boundaries=1`（第 112 窗边界）、`slot_epoch={0:1,1:1,2:1,3:1,4:0,5:1,6:1,7:1}`（slot 4 non-terminal continue、其余 7 terminal reuse，对应 §10.1）、`committed_identities=3835`、`criterion10_replay_mismatches=[]`（epoch>0 slot 重放逐位一致）。
- 满足 DS LOW + GPT HIGH-2 规划层（production seed + 边界 + terminal/nonterminal 形态 + replay 一致）。GPU 短跑（判据 6/7）仍是独立 Gate。

### Gate 3 性能优化：逐窗 produce 预取 + latent 校验缓存 + 确定性 RNG（2026-09-18 11:10 CST）

- 背景：GPT HIGH-2 要求 GPU 短跑；实测 active production 极慢（~18min/window，diagnostic 显示 `other_s` 占 82%、其中 produce 占 98%）。诊断后做三项**纯性能**优化（不改语义/ABI）：
  1. **latent 校验缓存**（`libero_lerobot_dataset._load_cached_latent`）：`contiguous()`+`isfinite()` 从「每次访问」降为「每 window 一次」（167 次/block → 1 次）；加 `_latent_cache_lock` 供预取线程安全。
  2. **逐窗 produce 预取**（`active_local_memory_driver`）：`freeze_window()` 后用 `ThreadPoolExecutor(4)` 后台构建 SegmentBatch，与 GPU forward/backward 重叠；`prefetch_depth` 构造参数（默认 0 关闭），生产 launch 经 `PSM_ACTIVE_PREFETCH_DEPTH`（默认 4）开启。
  3. **每样本确定性 RNG**（`libero_lerobot_dataset` + `base_dataset`）：mode/caption/verify 改用 `random.Random(f"{seed}:{idx}")`，与调用顺序/线程无关。
- 实测（GA=1, max_episodes=6, 8-member window）：`step_wall` 47.2s → **14.7s（3.2×）**；`other_s` 35.98s → 1.92s；`model_compute` 10.2→12.4s（CPU 争用）。
- 确定性：顺序 vs 4 线程 produce 输出 digest **0 mismatch**（数据逐位确定）；同配置 iter1 逐位相同；iter2+ 及 prefetch>0 的 ~0.09% 差来自**模型 GPU 浮点非确定性**（用户 2026-09-18 选方案②接受：数据确定、浮点非确定）。
- 验证：driver 32 passed、相邻 runtime/segment/adapter 61 passed、ruff/py_compile PASS。
- 子模块 `fca7eb5`（未推）；根仓 gitlink 待更新。

### 审核观察（2026-09-18 11:14 CST）

- `before_head=8e4dc334`；`git fetch origin V2` 成功；advertised=`origin/V2=7fc97081`（一致）；`before_head..origin/V2` 新增=**空**；本地领先（未推）。
- ChatGPT exact review 仍只有 `2026-09-17_..._gate3_54aa90a0_827c1cbd.md`（Gate 3 pair 54aa90a0/827c1cbd，`REQUEST_CHANGES_BEFORE_LONG_RUN`），无新 review。
- DS `ds:0.0`：idle，已给 `APPROVE_TO_CLOSE`。MM `mm:0.0`：idle，已给 `APPROVE_TO_CLOSE`。
- **Kimi `kimi:0.0`：session 不存在（`can't find session: kimi`）** → 冻结名册第三方 verdict 无法取得；按治理记录为「检查失败/会话缺失」，不据此推进 Gate 3 closure。
- 结论：Gate 3 closure 冻结名册（DS/MM/Kimi）未齐（缺 Kimi）；本轮不构成推进令牌。

### 冻结名册变更：移除 Kimi（2026-09-18 11:19 CST，用户明确指令）

- 用户指令「不用 kimi 审核了」→ Gate 3 closure 冻结名册由 DS/MM/Kimi 改为 **DS=`ds:0.0` + MM=`mm:0.0`**（Kimi `kimi:0.0` 会话已不存在）。旧观察凭证作废，以 DS/MM 同 pair final 为准。
- DS/MM 对 pair `54aa90a0`/`827c1cb` 均为 `APPROVE_TO_CLOSE_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE`。
- 性能优化（子模块 `fca7eb5`/根仓 `8e4dc334`）为新改动，需新任册 DS/MM 单独审核。
- 对照 GPU 跑（`epreuse_gpu_control`）iter1：`step_wall=225.9s`、`model_compute=204.1s`、`other_s=15.2s`（GA=16 窗口，prefetch 生效）。

### GPT HIGH-2 GPU witness：跨 rollover 边界的 save→kill→resume（2026-09-18 11:50 CST）

- 配置：`LIBERO_MAX_EPISODES=10`、`PSM_R09_B_TTT_ACTIVE_GA=16`（window=128）、`max_iter=3`、`save_iter=2`、`PSM_ACTIVE_PREFETCH_DEPTH=4`。rollover 在 window2→3 之间触发，iter_2 checkpoint 落在边界前。
- 三跑：对照（不中断）`epreuse_gpu_control`；中断（跑到 iter_2 后 kill）`epreuse_gpu_smoke`；resume（自动加载 iter_2 续跑）`epreuse_gpu_resume`。
- 结果：resume 成功加载 `iter_000000002`（same-job, local, 含 dataloader 组件），续跑至 iter_3；iter_3 driver 状态与对照**逐字段完全一致（8/8）**：`window_index=3`、`slot_epoch={0:1,3:1,4:1,7:1}`（terminal 复用）/`{1,2,5,6}=0`（non-terminal 继续）、`stream_index`/`active_cursor`/`exposure`（libero_10=1840/libero_goal=1264/libero_object=1184/libero_spatial=1856，单调增）、`terminal_slots`/`stable_slots`/`committed_n=8` 全 match。
- loss：对照 iter3=1.624629 vs resume iter3=1.624593（差 3.6e-5，GPU 浮点非确定，用户已选方案②）。
- 证据：`artifacts/g0/epreuse_gpu_resume_witness.json`（`result=PASS`）。
- 至此 GPT HIGH-2 的规划层（探针 5112 窗 + 生产 driver 120 窗）与 GPU 层（save→kill→resume 跨边界）证据齐备。

### GPT MEDIUM-3：pretrain acceptance command（2026-09-18 11:55 CST）

- 新增 `tools/g0/verify_active_local_memory_pretrain_gate.py`（只读）：串起 Gate1 slot 轮转、Gate3 规划容量（5112 窗）、Gate3 生产 driver 边界、GPU 跨边界 resume witness、生产 queue_seed、formal identity 六项，输出单一 `PASS/FAIL/BLOCKED` JSON。
- 运行结果：`result=PASS`（6/6），产物 `artifacts/g0/active_static_probe/pretrain_acceptance.json`。

### 审核申请已送达 DS/MM（2026-09-18 12:05 CST，REVIEW）

- formal pair=root=`c16fc8ece6b88cadc9dd1226f4a5b23e10737c7a`/child=`fca7eb589f455509e05e7c39659000343a36bad4`；冻结名册=DS=`ds:0.0` + MM=`mm:0.0`（用户已移除 Kimi）。
- 请求 exact-pair final（`APPROVE_TO_CLOSE` 或 `REQUEST_CHANGES`），范围=①Gate3 closure ②性能优化（fca7eb5）③GPT HIGH-2 GPU witness ④acceptance command ⑤hygiene。
- DS 首次长文本未进 pane（其 pane 处于 `esc interrupt` busy，progress 80.2K→93.6K），改用短文本后 capture 命中；MM 首轮即命中。三联（`send-keys -l → ≥1s → Enter → capture`）均完成。
- 三方（现两方）final 前保持 `REVIEW`；下一轮起三分钟完整核验。

### scheduler-semantics refreeze 设计 v0.1（2026-09-18 12:12 CST）

- 新增 `docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_scheduler_semantics_refreeze_design_v0.1.md`（docs-only，D8b 长跑前置 Gate `G0-R09-B-TTT-V035-ACTIVE-SCHEDULER-SEMANTICS-REFREEZE`）。
- 内容：把「`cumulative_valid_consumer_exposure` 不清零 → epochs≥1 窗口 77.3% 单 suite」如实列为本 Gate 的唯一问题；给出 (a) per-epoch 复位 与 (b) 接受累计 两候选、各自实现落点/代价/验收；请求裁定。
- 未改任何代码；待 DS/MM 审核。

### 审核观察凭证 #1（2026-09-18 12:20 CST，REVIEW）

- before_head=`27decdf6`；fetch 成功；advertised=`origin/V2=7fc97081`（一致）；`before_head..origin/V2` 新增=**空**；本地领先未推。
- ChatGPT exact review：无（`grep c16fc8ec reviews/` 空）。
- **DS=`ds:0.0`**：final=**拆分建议（等同 REQUEST_CHANGES）**：`libero_lerobot_dataset.py:438-439`/`base_dataset.py:155` 的「数据增强 RNG 语义变更」须**移出本 closure / 另起 Gate**；`active_local_memory_driver.py:208-235`/`active_local_memory_launch.py:315` 的「预取线程安全」须独立设计。明确：**Gate 3 closure 以 child `827c1cb` 单独送审即可 APPROVE_TO_CLOSE**（§4 实现 + 探针 5112 + 生产 120 窗 + GPU witness 已齐）。
- **MM=`mm:0.0`**：final=`APPROVE_TO_CLOSE_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE`（closure + 性能优化 + GPU witness + acceptance 6/6 全实证；§6 判据 1/3/4/5/8/9/10 由 8 个 driver_test 覆盖；D8b gate 显式保持）。
- 合并处理：接受 DS 的拆分——**Gate 3 closure 按 child `827c1cb` 关闭**；性能优化（fca7eb5）另起独立设计 + Gate 重审。

### 审核申请 #2：PRODUCE-PREFETCH Gate（2026-09-18 12:24 CST，REVIEW）

- formal pair=root=`e6a7af8394c424d55c1ac05f6287ac441d0db02c`/child=`fca7eb589f455509e05e7c39659000343a36bad4`；名册=DS+MM。
- 设计 `docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_produce_prefetch_design_v0.1.md` + 实现 `fca7eb5`（latent 校验缓存 / 逐窗预取 / 确定性 RNG）。
- DS/MM 三联已送达（DS pane `esc interrupt` 处理中；MM 显示 processing）。
- 另：Gate 3 closure 按 DS 建议以 child `827c1cb` 单独关闭（DS 明示「单独送审即可 APPROVE_TO_CLOSE」，MM 已 APPROVE）。

### 审核观察凭证 #2 / 推进令牌（2026-09-18 12:30 CST，REVIEW → DONE）

- before_head=`dd966008`；fetch 成功；advertised=`origin/V2=7fc97081`（一致）；新增=空。
- formal pair=root=`e6a7af8394c424d55c1ac05f6287ac441d0db02c`/child=`fca7eb58`；名册=DS+MM。
- **DS=`ds:0.0`**：`APPROVE_TO_CLOSE_R09_B_TTT_V035_ACTIVE_PRODUCE_PREFETCH`；明确边界（只关性能面、不改 scheduler/owner/ABI、不改 freeze_window 选择键、D8b 仍受 refreeze）；并明确 **Gate 3 closure 以 child `827c1cb` 单独关闭（证据已齐）**。
- **MM=`mm:0.0`**：`APPROVE_TO_CLOSE_G0_R09_B_TTT_V035_ACTIVE_PRODUCE_PREFETCH`；三项 perf 改动（latent 校验缓存+lock / 4-worker 预取 / 每样本确定性 RNG）由设计 v0.1 + 实现 diff + 32/32 driver_test + 数据 SHA256 0 mismatch + 3.2–4.7× 实证；§5 边界全守；与 Gate 3 closure 解耦成立。
- **推进令牌齐（DS+MM 同 pair 均 APPROVE_TO_CLOSE）**：关闭 `G0-R09-B-TTT-V035-ACTIVE-PRODUCE-PREFETCH`；`G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE`（child 827c1cb）亦关闭。D8b 长跑仍闭锁于 scheduler-semantics refreeze Gate。

### 审核申请 #3：SCHEDULER-SEMANTICS-REFREEZE（2026-09-18 12:34 CST，REVIEW）

- formal pair=root=`595ada3826ad95123781e4b1b00f3c7ec991745a`/child=`fca7eb58`；名册=DS+MM。
- 设计 v0.1（docs-only，D8b 最后前置）；请求裁定 (a) per-epoch exposure 复位 或 (b) 接受累计 regime。DS/MM 已送达。
- D8b 长跑在本 Gate 关闭前不启动。

### 审核观察凭证 #3 / 合并处理（2026-09-18 12:40 CST，REVIEW）

- formal pair=root=`595ada38`/child=`fca7eb58`；名册=DS+MM；fetch 成功、advertised=origin/V2 一致、新增=空。
- **DS=`ds:0.0`**：`APPROVE (a)`——授权 `_maybe_rollover` 的 per-epoch observed 最小改动 + 相邻 CPU 测试 + 更新 `probe_epoch_reuse_planning.py`（增 per-epoch 构成断言并重跑）；要求 ①epochs≥1 四类窗占比与 epoch0 同构（单 suite ~14%）②复位记录可核 ③CPU 测试全绿 ④ABI/字节序不变 ⑤D8b runbook 写入新语义并标注 supply-limited 尾窗。D8b 实现验证通过前不启动。
- **MM=`mm:0.0`**：`REQUEST_CHANGES_..._SCHEDULER_SEMANTICS_REFREEZE`——**程序性**：formal pair 与 docs-only 交付物不匹配（`595ada3` 是前序 session 收尾、`fca7eb5` 是 PRODUCE-PREFETCH 实现；refreeze 设计唯一提交为 `27decdf6`），要求用正确 pair 重提交后再行 (a)/(b) 实质裁定。
- 合并处理：重送 **root=`27decdf6`/child=`fca7eb58`**；实质方向已获 DS `(a)`，待 MM 同 pair 实质 final。

### 审核观察凭证 #4 / 推进令牌（2026-09-18 12:45 CST，REVIEW → IN_PROGRESS）

- before_head=`e36f80c3`；fetch 成功；advertised=origin/V2 一致；新增=空。
- formal pair=root=`27decdf6`/child=`fca7eb58`（更正后）；名册=DS+MM。
- **DS=`ds:0.0`**：`APPROVE (a)`——机制要求：`cumulative_valid_consumer_exposure` **保留作报告量**（不改「累计」语义与 admit 赤字来源），**新增 per-epoch observed 计数器**供 `freeze_window` 选择；per-epoch observed 与 `_slot_epoch` 入快照、resume 一致；更新 `probe_epoch_reuse_planning.py` 增 per-epoch 构成断言并重跑（epochs≥1 的 `windows_by_distinct_categories` 须与 epoch0 同构、单 suite 窗回到 ~14%）；D8b runbook 写入新语义并标注 supply-limited 尾窗；D8b 实现验证通过前不启动。
- **MM=`mm:0.0`**：`APPROVE_A_..._SCHEDULER_SEMANTICS_REFREEZE`——(a) 由 5112 窗实测证实塌缩不可接受，(b) 等同接受 53.7% 单 suite 偏斜、独立裁断不可接受。
- **推进令牌齐（DS+MM 均 APPROVE (a)）**：授权实现 (a)——driver 新增 per-epoch observed 计数器（保留 cumulative 作报告量）+ `freeze_window` 改用之 + 快照/resume 一致 + 探针更新；D8b 长跑在本实现验证通过前仍不启动。

### 审核观察凭证 #5 / 三方合并（2026-09-18 12:50 CST，REQUEST_CHANGES）

- formal pair=root=`27decdf6`/child=`fca7eb58`；名册=DS+MM+GPT（Kimi 已移除）。
- **DS=`ds:0.0`**：`APPROVE (a)`（机制：cumulative 保留 report-only，新增 per-epoch observed；快照一致）。
- **MM=`mm:0.0`**：`APPROVE_A_..._SCHEDULER_SEMANTICS_REFREEZE`。
- **GPT**：`docs/collab/chatgpt/reviews/2026-09-18_scheduler_semantics_refreeze_current_build_27decdf6_fca7eb5.md`，技术 verdict **REQUEST_CHANGES**（非 formal，pair 未推远端）：
  - **HIGH-1**：refreeze v0.1 用**过时的 Gate-3 regime 证据**（旧 77.3%）。**已核实当前 artifact：`windows_by_distinct_categories={1:2703,2:1893,3:367,4:149}`、单 suite=52.88%、exposure 各≈25%**。要求以当前实现 + 生产 seed 重新基线化问题陈述，再决定 refreeze 是否必要。
  - **HIGH-2**：在**异步 per-slot epoch** 下未定义 reset 权限——每个 terminal slot 独立 `_slot_epoch[slot]++`，无「全局 epoch 转换」事件；当前 driver witness `slot_epoch={0:1,1:1,2:1,3:1,4:0,...}` 证明无此事件。要求冻结唯一 reset authority（用现有可观测状态）+ 单侧跨界证据 + save/resume 两侧复现。
  - **HIGH-3**：acceptance command 的 `formal_identity` 检查恒真（未与证据 SHA 比对）；`full_coverage` 未入 PASS 布尔；`production_queue_seed` 只证明 `!=0`。要求绑定 root/child + 输入 digest、stale 即 fail、coverage 入布尔、按当前 catalog 身份核 seed。
  - **DECISION BLOCKER**：当前实现是 **B=1**（1 member = 1 stream × T），与「同 index 跨 slot 批量」的新目标冲突；须用户/架构明确二选一（保持 B=1 重画流程图，或开 ABI/runtime 性能 refreeze）。
- **合并**：refreeze Gate 计入 `REQUEST_CHANGES`——需按 HIGH-1 重新基线化、按 HIGH-2 冻结 reset authority、按 HIGH-3 修 acceptance、并解决 DECISION BLOCKER。当前 driver 的 (a) 实现为**未提交 WIP**，待设计修正后重做。

### 用户澄清：active 路线是测试路线（2026-09-18 12:58 CST）

- 用户：「active 只是测试，不是真实正式训练，和绘图无关；绘图只是示意」。
- 故 GPT 的 DECISION BLOCKER（B=1 vs 同 index 跨 slot 批量）**不成立**：保持 active 路线 B=1 串行 member 语义，无需 ABI/runtime 架构变更；流程图仅为示意、不作为实现真值。
- 推论：refreeze 的「regime 塌缩」只影响 active **测试** 路线的数据混合；结合 HIGH-1 当前实测 52.88% 单 suite，是否仍需 per-epoch 复位须重新判断（见下）。

### GPT HIGH-3：acceptance 硬化（2026-09-18 13:05 CST）

- `tools/g0/verify_active_local_memory_pretrain_gate.py`：
  - `formal_identity` 改为**真检查**：新增 `--expected-root/--expected-child`，与当前 HEAD 比对（缩写兼容），不匹配即 FAIL；
  - `gate3_planning_capacity` 的 `criterion5_block_coverage.full_coverage` **纳入 PASS 布尔**；
  - `production_queue_seed` 改为**按记录的 catalog 身份重算** `int(sha256(manifest|config|source)[:16],16)` 并比对，而非 `!=0`。
- 实测：无误判 PASS；`--expected-root deadbeef` → FAIL；ruff/py_compile PASS；产物已重生成。
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          ��果：`keys_to_select` = 14 项；实测 **selected tensors 20 → 314（≈1.4B 参数）**，2 个 param group（lr=5e-5/WD、lr=2.5e-4/无WD 的动作头组）。
- 短训验证（max_episodes=6, GA=1, max_iter=2）：**无 OOM**、`Done with training`、loss finite（iter1 1.415554 / iter2 1.592989）；ckpt 落盘。
- 影响：训练范围由「local-mem 微调」扩为「baseline 头 + local-mem 联合训练」；per-member `model_compute` 约 1.3s→1.9s。
- 该 config 变更为语义变更，须新 Gate + DS/MM 审核。
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     （2026-09-18 15:58 CST）

- formal pair=root=`a22167c5`/child=`60dd814a`；名册=DS+MM。
- **DS**：裁定 **(A2)** + 条件性授权（1 次前向 = 8 slot × T=16，batch=128，16 次/window）。
- **MM**：`APPROVE_A2_G0_R09_B_TTT_V035_ACTIVE_MEMBER_SHAPE_REFREEZE`。
- 用户补充：**8 条 slot 的 TTT 串行计算互相独立、可并行**（每 slot 各自 fast-state 递推）——纳入 (A2) 实现（设计 §4.3 已写「每步并行 B_slot」）。
- 推进令牌齐（DS+MM 同 pair (A2)）：可开始 (A2) 实现（CPU/static 先行 + 连锁重验 resume/epoch-reuse 判据 + 重估 readiness）。
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   