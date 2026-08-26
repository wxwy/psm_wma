---
name: eval-result-directory-roles
description: 8 个 results 父目录的角色/参数/启动时间全景表；下次查 SR 必须先看是哪个父目录再确认参数
metadata:
  type: reference
---

# eval 结果父目录角色标注（防查错数据）

> 本文件是"哪个目录做了什么"，**不**定义 canonical R06 baseline 的来源。
> canonical R06 baseline 由 runtime plan v0.6 §6 + 用户 2026-08-26 口径冻结决定：
> 单一 ckpt + `guidance=1.0` + `num_steps=30` + `max_episode_steps=700` +
> 4 suites × 10 tasks × 10 trials + no memory/agent/RL，详见 `docs/build/PSM-WMA_G0_runtime_execution_plan_v0.6_aligned.md`。

## 全景表

| 父目录 | 角色类别 | 启动时间 | 参数 | 备注 |
|---|---|---|---|---|
| `libero_closed_loop_4in1` | historical evidence | 8-23 前 | 默认 g=1.0 trials=10 | iter_800/1600/2000，3 ckpt 不全 |
| `libero_closed_loop_4in1_acceptance` | historical evidence | 8-23 18:50 | 默认 g=1.0 trials=10 | iter_2000 spatial partial |
| `libero_closed_loop_4in1_acceptance_4090` | historical evidence | **8-24 22:14** | 默认 g=1.0 trials=10 | **iter_2800 spatial summary=0.48 是脏数据**；按 MP4 `_success/_fail` 后缀重算 ≈ **0.96**；object/goal/libero_10 summary.json 可信；整套作为"closed-loop capability 已成立"的历史证据，不作 canonical baseline |
| `libero_closed_loop_4in1_acceptance_4090_smoke_v1` | checkpoint screening | 8-26 09:21 | 默认 g=1.0 trials=**1** | 13 ckpt 1-trial sweep；纯趋势/筛选用，**不**作为正式 SR |
| `libero_closed_loop_4in1_cfg_4090` | CFG sensitivity diagnostic | 8-25 19:46 | g=2.0 trials=10 | 跨 suite CFG 调参诊断；只有 libero_goal；**不**作为 baseline 引用 |
| `libero_closed_loop_4in1_spatial_cfg_4090` | CFG sensitivity diagnostic | 8-25 11:16 | g=1.5/2.0/2.5 trials=10 | spatial CFG 诊断（g=1.5/2.0/2.5 SR ≈ 0.96-0.97）；**不**作为 baseline 引用；**不**做 suite-specific inference tuning |
| `libero_closed_loop_4in1_iter100` | historical evidence | 8-22 前 | 默认 g=1.0 trials=10 | 仅参考 |
| `libero_closed_loop_4in1_steps12` | historical evidence | 8-23 11:13 | num_steps=**12** | iter_1800 only |

## 查 SR 的强制流程

1. **先看是哪个父目录**（8 个之一）→ 判定角色类别
2. **再看该父目录的参数**（guidance / trials / steps）
3. **判定数据可靠性**：
   - `acceptance_4090/iter_2800` spatial summary.json → **脏**，按 MP4 后缀重算
   - `smoke_v1/*` → 1 trial 不稳，**只**做 checkpoint selection / 趋势参考
   - `spatial_cfg_4090/*` → CFG sensitivity 诊断，**不**作为 baseline 引用
   - `cfg_4090/*` → 跨 suite CFG 诊断，**不**作为 baseline 引用
   - 其他 historical evidence 父目录 → 仅参考，不作结论

## 治本约束（强制）

- **不要**直接读 `find ... -name summary.json` 然后报 SR；必须先核对父目录 + 参数
- **不要**用 suite-specific CFG (`spatial_cfg_4090` / `cfg_4090`) 的最优结果拼成 baseline
  - suite-specific inference tuning 会破坏后续 no-memory vs +Local 的 matched baseline contract
- **不要**把 `acceptance_4090/iter_2800` 整套（旧目录含 spatial summary bug）作为 canonical R06 baseline
  - 它是"closed-loop capability 已成立"的历史证据，spatial 真值按 MP4 后缀重算 ≈ 0.96
  - object/goal/libero_10 summary.json 可信但**不**作为最终 frozen baseline
- **不要**把 13 ckpt 1-trial sweep (`smoke_v1`) 的均值写成 baseline；它是 checkpoint selection
- **canonical R06 baseline 必须由一次 clean 400-episode acceptance 冻结**：
  - 单一 ckpt（按 sweep + 稳定性证据选定）
  - `guidance=1.0`（不调）
  - `num_steps=30`（不调）
  - `max_episode_steps=700`（不调）
  - 同一 prediction/execution/query cadence
  - 4 suites × 10 tasks × 10 trials = 400 episodes
  - `summary.json == MP4 _success/_fail 后缀 == task-level episode success` 三者一致
  - no memory / no agent / no RL
- **R06 当前状态**（用户 2026-08-26 口径纠偏）：
  - closed-loop capability = **PASS**（3 个 suite 已观测非零 SR，链路全通）
  - canonical baseline freeze = **TODO**（待 clean 400-episode acceptance 完成）
  - 完成 clean acceptance 前不标记 `G0-R06 → DONE`，不进入 R07-R09 实质 Memory 实验

## 相关

- [[iter2800-spatial-sr-dirty-data]]：acceptance_4090 spatial 0.48 脏数据细节（事实）
- [[mp4-suffix-is-truth]]：MP4 后缀是真值的全局规则（事实）
- runtime plan v0.6 §6 R06：single no-memory baseline protocol
- task #29：MP4 bug 修复说明（事实记录）
- task #22-25：spatial CFG 诊断（已定位为 diagnostic，**不**作 baseline 引用）