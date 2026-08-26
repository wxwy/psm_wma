---
name: iter2800-spatial-sr-dirty-data
description: acceptance_4090/iter_2800 spatial summary.json SR=0.48 是被 MP4 bug 污染的脏数据；真值 0.96（按 MP4 _success/_fail 后缀）
metadata:
  type: project
---

# iter_2800 spatial SR 数据可靠性

## 关键事实

- `libero_closed_loop_4in1_acceptance_4090/iter_000002800/libero_spatial/summary.json` SR=**0.48** 是 **脏数据**（MP4 bug 污染）
- 真值：**95/99 = 0.96**（按 `libero_spatial/tasks/task_*/mp4/*/episode_*_success.mp4` 统计）
- spatial_cfg_4090 g=1.5/2.0/2.5 同 ckpt 同 10 trial spatial SR=**0.96/0.97/0.97**（与真值一致）
- bug 范围：**只影响 spatial suite**，object/goal/libero_10 summary.json 与 MP4 后缀一致

## 证据

worker_task_001.log 显示 task_001 ep1-8 "success=False, steps=0, elapsed=522s"（机器人原地不动）
但 task_001/mp4/ 目录里 episode_000-009 全是 `_success.mp4` —— 实际 policy 成功了，是合并 summary 时被错误标 False。

## 怎么用

- **不要**用 `summary.json.overall_success_rate` 当 spatial 的真值
- spatial 真值必须按 MP4 后缀重算
- 其他 suite (object/goal/libero_10) summary.json 可信

## 相关

- [[mp4-suffix-is-truth]]：MP4 后缀是真值的全局规则
- [[eval-result-directory-roles]]：8 个父目录的角色标注
- task #29：MP4 bug 修复说明