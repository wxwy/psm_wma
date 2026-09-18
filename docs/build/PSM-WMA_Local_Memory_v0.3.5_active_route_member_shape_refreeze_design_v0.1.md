# PSM-WMA Local Memory v0.3.5 — active 路线 member 形状 refreeze（option (A)：跨 slot 批量前向）设计 v0.1

- 状态：**设计（独立 Gate，D8b 长训前的性能阻塞）**。本文件只做 docs-only 决策冻结；无代码改动。
- 上游：`..._functional_active_route_implementation_design_v0.1.md:102-142,369-390`（当时选项 **(B)**：1 member = 1 stream × T，B=1）；GPT 2026-09-18 DECISION BLOCKER（用户当时判「active 只是测试路线、不 refreeze」，现用户要求以 (A) 提升训练速度）。
- 建议 Gate：`G0-R09-B-TTT-V035-ACTIVE-MEMBER-SHAPE-REFREEZE`。

---

## 1. 问题（实测）

同工作量（两条路线每 optimizer step 都是 **2048 样本**：baseline `128×1×GA16`；active `128 member × 16 consumer`）下：

| 指标 | baseline | active（现，B=1） | 比 |
|---|---:|---:|---:|
| `step_wall_s` | 110.0 | **254.1** | **2.31×** |
| `model_compute_s` | 88.98 | **232.1** | **2.61×** |
| **MoT 前向次数 / step** | **16**（每次 128 样本） | **128**（每次 16 样本） | **8×** |
| GPU util | 100% | 7–62% | — |

根因：active 每 optimizer step 发起 **128 次小前向**（每次 `batch=ttt_tbptt_steps=16`，来自 `custom_collate_fn([payload for payload in inputs.payloads])`，`omni_mot_model.py:1452`），而 baseline 只 16 次（每次 128）。同一样本总量下，前向调用次数多 8×、每次 GEMM 小 8× ⟹ kernel 启动开销主导、GPU 利用率低。

**阶段分解（每 member，实测）**：阶段 1 TTT fast-state 串行 16 步（`local_evidence.py:746` 的 `for index in range(steps)`，~0.12 s）→ 阶段 2 MoT 前向+反传（~1.76 s）。

## 2. 目标

**把同 T-index 的多条 slot 的 consumer 拼进同一次 MoT 前向**，使每 optimizer step 的 MoT 前向次数由 128 降为 **16**、每次 batch 由 16 升为 **128**（与 baseline 同形）；同时 TTT 由「逐 slot 独立串行 16 步」变为「多 slot 并行、每步各推进一次」。

## 3. 建议形状（待裁定）

**候选 (A1) —— 1 次前向 = B_slot × 1 个 T-step**：在 T 步上迭代 16 次，每次取「8 条 slot 各自的第 t 个 consumer」组成 `batch=8`，喂 MoT；TTT 同步推进 8 条 slot 的 fast-state。

**候选 (A2) —— 1 次前向 = B_slot × T 个 consumer**：一次装 8×16=128，但 TTT 的 16 步仍是串行，只是把 8 条 slot 的每步并行。

> 两者都把「前向次数」降到 16/window(每 slot 每组 16 步)。**(A1)** 的 batch 是 8，**(A2)** 的 batch 是 128。用户表述倾向 (A1)「每次 8 个 sample，执行 16 次」。**请裁定 (A1) 或 (A2)。**

## 4. 需要改动的面（ABI/runtime/performance）

1. **member 形状**：`SegmentBatch`/`ActiveWindowMember`/`GAWindowPlan.members` 由「1 slot×T」变为「B_slot×1(或 T)」；`SegmentIdentity` 每 member 变为 B_slot 个（或按行）。
2. **driver `freeze_window`**：按「同 T-index 跨 slot」组批；`window_members` 的账（128）与 batch 的关系重算；`_peek_block`/`_commit_block` 的 frontier 语义不变（每 slot 仍逐 member 推进）。
3. **TTT/scan**：从「逐 member 串行 16 步」改为「每步并行 B_slot」；fast-state 结构按行排列。
4. **producer**：按 B_slot×T 产出 `[B_slot, T, ...]` 的 `SegmentBatch`（不再 `[1, T]`）。
5. **model forward**：`_run_active_local_memory_native_forward` 的 collate 由「1 slot 的 T 个 payload」改为「B_slot 行的 payload」。
6. **resume/checkpoint**：`_slot_epoch`/frontier/exposure 语义不变，但快照字段按新形状调整。

## 5. 冻结边界

- 不改 `queue_permutation`/`QueueEpochSnapshot` 字节序；不改 free-window 的 category-deficit 选择键结构。
- 不改 TTT 算法本身（`local_evidence` 的数值口径）；只改批处理形状与调用次数。
- 不改 evidence/consumer 的来源口径（仍由 canonical producer 从 exact-window cache 构建）。

## 6. 预期收益与风险

- **收益**：MoT 前向 128→16；GPU 利用率 7–62% → 接近 baseline；预计 `step_wall` 从 254 s 降到 ~120–150 s 量级（**待实测**，非承诺）。
- **风险**：ABI 变更面大（SegmentBatch/SegmentIdentity/member/plan）；fast-state 跨 slot 并行的正确性；resume 形状一致；需重跑既有 32+ 判据与 GPU witness。

## 7. 请求 verdict

1. 裁定形状：**(A1)** 还是 **(A2)**？
2. 是否授权按上述 §4 的面实现（CPU/static 先行 + GPU 单边界 + 性能对照 baseline），并重跑全部既有判据？
3. 明确：本 Gate 只处理「member 形状/性能」，不改 TTT 算法/选择语义/regime 决策。
