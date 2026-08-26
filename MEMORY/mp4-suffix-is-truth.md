---
name: mp4-suffix-is-truth
description: 验收评测的 SR 真值在 MP4 文件后缀（_success/_fail），不在 summary.json 的 task_results.successes 字段；spatial suite 有 MP4 bug 让 summary.success 被错误标成 False（实际 policy 成功）
metadata:
  type: project
---

# MP4 后缀是真值，summary.json success 字段会被污染

## 关键发现（08-26 用户指正）

- `libero_closed_loop_4in1_acceptance_4090/iter_000002800/libero_spatial/summary.json` 写 SR=**0.48**
- 同一目录 MP4 后缀统计：**95/99 = 0.96**
- worker_task_001.log 显示 ep1-8 "success=False steps=0 elapsed=522s"（机器人原地不动）
- 但 task_001/mp4/ 目录里 episode_000-009 全是 `_success.mp4`
- **MP4 后缀才对，summary.success 是错的**

## 受影响范围

| suite | summary.json | MP4 后缀 | 状态 |
|---|---|---|---|
| libero_spatial | 0.48 | 0.96 | ❌ summary 被污染 |
| libero_object | 0.99 | 0.99 | ✅ 一致 |
| libero_goal | 0.75 | 0.76 | ✅ 一致 |
| libero_10 | 0.58 | 0.58 | ✅ 一致 |

**bug 只影响 spatial suite**（task #29 备注"MP4 bug 污染修复"指的就是 spatial）。

## 根因（推测）

- task_results.episode_results[].success 字段在合并 summary 时被错误标记
- MP4 文件后缀是渲染时独立写入的（基于仿真环境 success 信号），不受污染
- task #29 修复的方向就是按 MP4 后缀重算 success

## 怎么用

1. **查 SR 必须按 MP4 后缀**，不信 summary.json 的 success 字段
2. 验证方法：`ls libero_spatial/tasks/task_*/mp4/*/episode_*_success.mp4 | wc -l` vs `total mp4`
3. spatial 是已知污染 suite，其他 suite 数据可信

## 工具脚本

```bash
# 按 MP4 后缀统计 suite SR
for suite in libero_spatial libero_object libero_goal libero_10; do
  for task in $results/$suite/tasks/task_*; do
    for mp4 in $task/mp4/*/episode_*_success.mp4; do echo success; done
    for mp4 in $task/mp4/*/episode_*_fail.mp4; do echo fail; done
  done | sort | uniq -c
done
```

## 相关

- [[iter2800-spatial-sr-dirty-data]]：之前的错误判断（说"MP4 bug 不影响 summary"是错的）
- [[eval-result-directory-roles]]：8 个父目录的角色标注
- task #29：MP4 bug 修复说明（基于后缀重算 success）