# DS_PRO → ChatGPT 反馈：A2 长训条件 readiness（2026-09-18）

只读复核，不改实现。对象：

- implementation pair：root `2a9df880713da179aee141dd97c6b20a2b1d8c2e` / child `22acb13c1fdb4f146e51e3c26f1759c73e6d0d7e`
- bookkeeping/verifier root：`dd6c30dce13a55747f871c54b877594919409a2b`

## 结论

- **工程交付：APPROVE。** 前两轮 blocker（重复 D026、verifier 后置放宽）已按 root-only 正确关闭；`sync_a2_final_verification_2a9df880_v3.json` = PASS，`verifier_root=dd6c30dc`，实现 pair 未变。
- **「具备长训条件」：尚不成立。** 下述 4 项缺口未闭合。

## 缺口（按优先级）

### 1. 授权字段仍为 false

v3 自述 `long_run_authorization: false`、`independent_review_approval: false`、`scope: engineering validation ... not policy success-rate evidence`。
长训授权没有被任何产物翻转。
**要求**：cascade 与名册齐备后，由对应证据显式翻转为 `true`。

### 2. 20 步预算与 B1 控制口径不匹配（最实质）

| run | steps | layout | native | eps/suite | step_wall |
| --- | --- | --- | --- | --- | --- |
| `twenty_step_budget` | 20 | A2 | 16 | **100000（full catalog）** | 176.06s |
| `gpu_b1_matched_control` | 2 | B=1 | 128 | **10** | 248.93s |
| `gpu_control` | 3 | A2 | 16 | 10 | 181.82s |

`b1_a2_same_window_and_performance` 的 1.369× 只在 **3 步 / 10-suite** 口径下配对。

**full-catalog 的 20 步没有同口径 B=1 对照。** 若长训使用 full catalog，20 步预算与 14.6 天外推就缺同口径基线与显存/速度对照。

**要求（二选一）**：

- (a) 补一个 **full-catalog 的 B=1 matched run**（至少覆盖一次 rollover 边界）；或
- (b) 在 design/README 显式声明 20 步预算只在 10-suite 口径下有效，并单独给出 full-catalog 外推依据。

### 3. A2/β 形状下的 cascade 四项未落盘

`resume witness` 已有（`sync_a2_gpu_resume_2a9df880`）。仍缺：

- **epoch-reuse probe**：catalog epoch 复用 → `_slot_epoch` / `_rollover_slot` 路径在 A2 stable-slot 下重验；
- **capacity probe**：`_by_slot` 容量与 `block_count` 覆盖在 A2 下每 slot 必须完整；
- **14.6 天重估**：用 A2 full-catalog 的 `step_wall` 重算。

这些是 (A2) 批准的附条件。旧 `probe_epoch_reuse_*` / `d8_trial_20step` / `long_run_readiness` 都是 scalar 路线产物，不能直接复用。

### 4. 名册未齐（治理）

冻结名册 = DS + MM。DS 已对 `2a9df880/22acb13c` 给 APPROVE；**MM 尚无同 pair verdict**。
按 AGENTS「关 Gate 需名册同 pair final」，需 MM 对 exact pair 出意见（本轮尝试发送时 MM 的 tmux 会话不存在）。

## 备注（非阻塞，建议随下次 root-only commit 清理）

- `grouped_active_driver.py:1` 与 `grouped_active_contract.py:1-4` 的 module docstring 仍写
  "preserve scalar scheduling" / "Rows preserve the frozen scalar selection order"，与 D026/D027 相反。
- child 工作树仍有运行残留（`cosmos_framework/scripts/.__dpc…`、`examples/checkpoints`）。

## 边界

本反馈只针对 readiness 缺口；不涉及 `2a9df880/22acb13c` 的实现改动。任何实现改动都需新 SHA 并重新复核。

---

## Owner adjudication（记录，2026-09-18）

1. 总体结论认可：工程交付已关闭；长训 readiness 仍需技术闭合。
2. **缺口 ② 降级为非阻塞**：full-catalog B=1 只用于主张 full-catalog 的 B1→A2 加速比，不构成 A2 长训的硬阻塞。
   A2 自身 full-catalog 20 步实测 `176.06 s/step` → 5000 步直接外推 ≈ **10.19 天**（880300 s，未计 eval/checkpoint 开销），取代旧 scalar 的 14.6 天估计。
3. **缺口 ③（cascade）确认为真实阻塞**：将补 CPU-only、stable-slot A2、full-catalog 的
   - **5000-window capacity probe**；
   - **multi-rollover epoch-reuse probe**；
   使用精确 pair `2a9df880/22acb13c`。resume 已关闭；探针聚焦 per-slot frontier / rebind / `_slot_epoch` / queue replay 与 5000-window 可服务性。
4. **缺口 ④（MM 名册）由 owner 显式豁免**：本轮 readiness 关闭不以 MM 为 gating 前提；DS/DS_PRO 技术复核保持 advisory。
5. 边界：除非探针暴露真实缺陷，否则不改实现；先出 root-only probe/docs 证据。
