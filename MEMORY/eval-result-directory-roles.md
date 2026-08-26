---
name: eval-result-directory-roles
description: 8 个 results 父目录的角色/参数/启动时间全景表；下次查 SR 必须先看是哪个父目录再确认参数
metadata:
  type: reference
---

# eval 结果父目录角色标注（防查错数据）

## 全景表

| 父目录 | 角色 | 启动时间 | 参数 | 备注 |
|---|---|---|---|---|
| `libero_closed_loop_4in1` | 早期 acceptance 测试 | 8-23 前 | 默认 g=1.0 trials=10 | iter_800/1600/2000，3 ckpt 不全 |
| `libero_closed_loop_4in1_acceptance` | 早期 acceptance | 8-23 18:50 | 默认 g=1.0 trials=10 | iter_2000 spatial partial |
| `libero_closed_loop_4in1_acceptance_4090` | 4090 第一次完整 acceptance | **8-24 22:14** | **默认 g=1.0** trials=10 | **iter_2800 spatial 0.48 是脏数据，被 MP4 bug 污染** |
| `libero_closed_loop_4in1_acceptance_4090_smoke_v1` | 当前 13 ckpt 1-trial smoke | 8-26 09:21 | 默认 g=1.0 trials=**1** | 冒烟数据，1 trial 极不稳 |
| `libero_closed_loop_4in1_cfg_4090` | CFG 跨 suite g2.0 | 8-25 19:46 | g=2.0 trials=10 | 只有 libero_goal 一个 suite |
| `libero_closed_loop_4in1_spatial_cfg_4090` | spatial CFG 重测（task #22-25） | 8-25 11:16 | **g=1.5/2.0/2.5** trials=10 | spatial 真数字来源（g=1.5/2.0/2.5 SR 都 96-97%）|
| `libero_closed_loop_4in1_iter100` | 早期 iter100 测试 | 8-22 前 | 默认 g=1.0 trials=10 | 仅参考 |
| `libero_closed_loop_4in1_steps12` | NUM_STEPS=12 测试 | 8-23 11:13 | num_steps=**12** | iter_1800 only |

## 查 SR 的强制流程

1. **先看是哪个父目录**（8 个之一）
2. **再看该父目录的参数**（guidance/trials/steps）
3. **判定数据可靠性**：
   - acceptance_4090/iter_2800 spatial → **脏**，跳过
   - smoke_v1 → 1 trial 不稳，仅作趋势
   - spatial_cfg_4090/g2_0 → spatial 真验收
   - 其他 → 视父目录/任务而定

## 治本约束（强制）

- **不要**直接读 `find ... -name summary.json` 然后报 SR，必须先核对父目录 + 参数
- **不要**用 acceptance_4090 的 spatial/object/goal/libero_10 数据当结论
- spatial 引用必须来自 `spatial_cfg_4090/g{1.5,2.0,2.5}/libero_spatial/summary.json`
- 真验收 4 suite 引用必须来自 `spatial_cfg_4090` (spatial) + `cfg_4090/g2_0` (goal) — object/libero_10 待 smoke_v1 全完后用 10-trial 复测

## 相关

- [[iter2800-spatial-sr-dirty-data]]：acceptance_4090 spatial 0.48 脏数据细节
- task #22-25：spatial CFG 重测发现 g=2.0 提升 spatial SR
- task #29：MP4 bug 修复说明