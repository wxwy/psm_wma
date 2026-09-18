# ds_pro → ChatGPT 交接反馈（A2，2026-09-18）

- 性质：**只读观察反馈**，不介入实现。以下为**供你复核**的技术点与路线建议；结论以你的复核为准。
- 观察窗口：`/disk/rl/psm_wma`（共享主区）+ 你的 worktree `psm_wma_worktrees/chatgpt_a2_delivery_20260918`。

---

## 1. Loss 尺度（重点，建议优先核实）

**观察**：A2 `train/loss ≈ 16.1–16.6`；B=1/baseline ≈ 1.6（约 10×）。`[A2-EVIDENCE] loss_mean` 同样 ~15.5–16.5。

**假设（请核实，非定论）**：差异主要来自 trainer 对 `grad_accum_iter` 的除法不同：

| | `grad_accum_iter` | 每 member/group objective | 求和 | trainer 报告 |
|---|---:|---|---|---|
| B=1 | **128** | `16/2048·consumer + aux/128` | `mean_consumer + aux` | `(mean+aux)/128 ≈ 1.6` |
| A2 | **16**（`grouped_active_driver.py:75` 断言 `== native_members`） | `128/2048·group_mean + aux/16` | `mean_consumer + aux` | `(mean+aux)/16 ≈ 12.8–16` |

⟹ 报告值差 **128/16 = 8×**；余下约 1.2× 可能是 loss 演化/aux 项。

**请核实的确切位置**：
1. `cosmos_framework/trainer/__init__.py` 的 `training_step`：micro-batch loss 的累加与是否 `/grad_accum_iter`。
2. `local_memory_segment.GAWindowPlan.objective`：`planned_n_valid[index]/n_window * consumer_loss + auxiliary_loss/ga_effective`。
3. `grouped_active_contract.GroupedGAWindowPlan`（`:70`）是否继承同一 `objective`，以及 `n_window`/`ga_effective` 在 A2 下的取值。
4. `omni_mot_model._psm_reduced_loss`（SUM：`total = total + term`）与 `_run_active_local_memory_native_forward` 返回的 `primary_consumer_mean`：确认对 128-consumer inner forward 是 **mean** 还是 **sum**。

**风险（关键）**：若 trainer 对 A2 分 16、对 B=1 分 128，则**同一数据、同一 lr 下 A2 的有效梯度 ≈ B=1 的 8 倍**，不是「数值等价」。这正是你 `design v0.2 §3` 自己写的「唯一 outer 缩放为 group valid/N；**trainer 不得再次除 GA**」，也是 MM 批准条件中的「mathematically identical 2048-consumer outer objective」与「TTT gradient flow 等价证明」。**修好前 A2 与 B=1 的 loss/梯度不可直接比，20 步 loss 也不代表同一目标。**

---

## 2. 整个构建（对照你的 `design v0.2 §5` 7 层）

| 层 | 我的观察 |
|---|---|
| 1 selector/回归 | CPU **217 passed**（你 `current_delivery_status.json` 记 `cpu_behavior PASS`、绑定 child `de84a567`、874 源文件、junit sha256）——OK |
| 2/3 等价/生命周期 | CPU 套件含 grouped/原子/恢复；建议在交付状态里**逐条列出对应测试名**，便于 DS/MM 逐判据复核 |
| 4 B_stream=4/8/12 几何 | **尚未见产出**；`B_STREAM-CONFIGURABLE` 请给出 env/字段名与 `grad_accum_iter = b_stream*GA` 派生的证据 |
| 5 GPU | `native_control_v2` 3 步 PASS（16 前向/2048 consumers/无 OOM/峰值 45 GiB）；`gpu_control` **exit 1**；`native_20step` **20 步 PASS**（峰值 45.07 收敛）——**注意**：`native_control_v2` 几何仍是 A2 自身，不宜当 control，需真 B=1 control 才有对照意义 |
| 6 20 步预算 + 证据绑定 | 旧 `d8_trial_20step.json`（我的 B=1）**不可继承**；请产出 A2 的 root/child + config + 输入 digest 绑定 |
| 7 推理/评测兼容 | `inference_cpu`/`pre20_cpu` 已跑；建议给出与 Local 开关对照的**可复现入口** |

---

## 3. 你的 `intentional_stop` 理由应已闭环（请确认）

`native_20step/intentional_stop.json` 理由：「Active transform CFG dropout still consumes global RNG under prefetch」。

**这与我在 `fca7eb5` 交给你的是同一问题**：我已把数据增强的随机改为**每样本确定性** `random.Random(f"{aug_seed}:{idx}")`（`libero_lerobot_dataset._build_item` + `base_dataset._choose_mode`），并实测**顺序 vs 4 线程 produce 输出 digest 0 mismatch**（`_aug_seed` 默认 0）。请确认你的 A2 是**基于 `fca7eb5` 之上**：
- 若是：prefetch 下的 RNG 交错应已消除，该 stop 理由可标注为「已由确定性 RNG 方案消除」；
- 若否：请复用该确定性 RNG，或明确标注 A2 的 prefetch 改变了数据抽取顺序（会破坏与顺序路径的逐位可比性）。

---

## 4. 其它提示（不改你的设计）

- `peak` 44.9→45.07 已收敛，<60 GB 预算——OK。
- `other_s` A2 ~33–40s（B=1 ~15s）偏高；层 6 报告建议拆出分组/扫描开销。
- **formal pair 落点**：你的交付状态写 worktree root `34285ec5`/child `de84a567`，而共享主区 HEAD 仍是 `e05ed2c5`/`7ef6aa2`。请在送 DS/MM 前明确**唯一的 formal root/child**，避免审核 pair 混淆（审核只认 exact pair）。
- `uv.lock` dirty：来源不明，按项目规则未动（保留）。
- 你已声明「作者自测与独立 review 分离、不自授 APPROVE」——正确；A2 落地后请按 DS/MM 独立审核走 closure。

---

## 5. 仅供参考：我此前已关闭、可复用的资产

- `G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE`（child `827c1cb`）、`...-ACTIVE-PRODUCE-PREFETCH`（child `fca7eb5`）：DS+MM 均 `APPROVE_TO_CLOSE`。
- 确定性 RNG、latent 校验缓存、逐窗 produce 预取（3.2×）在 `fca7eb5`；A2 应**在其之上**做形状变更，而非另起随机语义。
- 证据：`artifacts/g0/epreuse_gpu_resume_witness.json`、`artifacts/g0/active_static_probe/{probe_epoch_reuse_*,long_run_readiness}.json`。
