# PSM-WMA Local Memory v0.3.5 — active 路线 produce 性能优化设计 v0.1

- 状态：**设计（独立 Gate）**。回应 DS 对 `fca7eb5` 的拆分要求：把「数据增强 RNG 语义变更」与「逐窗 produce 预取 / latent 校验缓存」从 Gate 3 closure 中移出，单独冻结与审核。
- 上游：Gate 3 closure 拆分意见（DS `ds:0.0`，2026-09-18）；GPT Gate 3 review HIGH-2。
- 建议 Gate：`G0-R09-B-TTT-V035-ACTIVE-PRODUCE-PREFETCH`。

---

## 1. 问题（实测）

active 路线正式训练极慢：GA=16 时 **18min/窗口（128 member）**。诊断（临时探针，已移除）：

| 组成 | 占墙钟 |
|---|---|
| `_payload`（逐帧 `_build_item`+`_transform`） | 63% |
| `_visual_summary`（latent pool） | 11% |
| `model_compute`（GPU forward/backward） | 22% |
| scan+misc | 1% |

即 **produce 占 `other_s` 的 98%**，GPU 78% 时间空闲——CPU 造数据与 GPU 计算**完全串行**。

## 2. 三项改动（子模块 `fca7eb5`）

### 2.1 latent 校验缓存（`libero_lerobot_dataset._load_cached_latent`）

**现状**：命中原 LRU 后仍每次对 `[5,48,12,20]` 张量做 `contiguous()`+`isfinite().all()`+两次
`torch.equal`；每 block 约 167 次访问（本帧 + local-history + 相邻 member 重复）。

**改动**：每个 window 的校验结果缓存于 `cache_item["_validated_windows"][start_frame]`，只在
首次访问校验一次；随后返回 `clone()`（保持「每次调用得到独立张量」的既有语义）。
加 `_latent_cache_lock`，使预取线程并发访问 episode 缓存结构安全（`torch.load` 与校验在锁外，
并发重载同一 episode 仅冗余、不错误）。

### 2.2 逐窗 produce 预取（`active_local_memory_driver` + `active_local_memory_launch`）

**改动**：`freeze_window()` 后立即用 `ThreadPoolExecutor(prefetch_depth)` 后台按 member 顺序构建
SegmentBatch；`_produce` 取 future（未就绪则阻塞），并持续保持 `prefetch_depth` 个在途。

- `_rebind_terminal`（唯一 scheduler 变更）仍在主线程按序执行；`producer.produce` 只依赖冻结计划的
  `(stream, cursor)`，**不依赖 scheduler 状态**，因此可安全并行。
- `prefetch_depth` 为构造参数（**默认 0 = 关闭**）；生产 launch 经 `PSM_ACTIVE_PREFETCH_DEPTH`
  （默认 4）开启。默认关闭保证既有 CPU/contract 测试（并发 produce 会打乱 `produced` 顺序）不受影响。

**实测**：GA=16 窗口 `step_wall` 18min → **3.8min**；GA=1 窗口 47.2s → 14.7s；`other_s` 35.98s → 1.92s。

### 2.3 每样本确定性 RNG（`libero_lerobot_dataset._build_item` + `base_dataset._choose_mode`）

**现状**：`_choose_mode()`、`verify` 的 `random.random()`、caption 的 `random.choice()` 用**全局**
`random`。串行时顺序固定；预取多线程下抽取交错 → 每样本 mode/caption 组合改变。

**改动**：每样本派生 `rng = random.Random(f"{self._aug_seed}:{idx}")`，mode/verify/caption 均取自它；
`_choose_mode(rng=None)` 向后兼容（`mode != "joint"` 时仍直接返回 `self._mode`）。

## 3. 正确性与确定性

- **数据逐位确定**：顺序 produce vs 4 线程 produce，对 8 个 `(episode,cursor)` 的
  `consumer_visual_summary`/`evidence_*`/`consumer_payload`（含 caption/token ids）求 SHA256，
  **0 mismatch**。同配置连跑两次 iter1 loss **逐位相同**（1.414341）。
- **浮点非确定（既有，非本改动引入）**：iter2 起及 `prefetch>0` 时 iter1 有 ~0.09% loss 差，来自
  **模型 GPU 浮点归约的时序敏感性**；已在同配置对照（probe6 vs probe7：iter1 相同、iter2/3 漂移
  1e-4）证明与数据无关。用户 2026-09-18 裁定**接受**（数据确定、浮点非确定）。
- 不改 `SegmentBatch`/`SegmentIdentity`/`GAWindowPlan` ABI；不改 `freeze_window` 选择语义。

## 4. 验收

1. driver 32 passed（含新 `test_prefetch_builds_the_same_window_members_as_sequential`）；相邻
   runtime/segment/adapter 61 passed；ruff/py_compile PASS。
2. 顺序 vs 多线程 produce 输出 digest 0 mismatch（确定性）。
3. 实测 `step_wall` GA=16 窗口 ≤ 4min（3.2–4.7×）。
4. `prefetch_depth=0`（默认）下行为与改动前一致（既有测试不改即通过）。

## 5. 禁止/边界

- 不改 scheduler/owner/ABI；不改 `freeze_window` 选择键结构；不改冻结契约文件。
- 预取不引入新的数据版本：同一 `(stream,cursor)` 的 SegmentBatch 与串行路径逐位相同。
- D8b 长跑仍受 scheduler-semantics refreeze Gate 约束；本 Gate 只关闭性能面。
