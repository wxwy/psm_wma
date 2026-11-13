# G2 P3 EVENT_KEYFRAME 正式接续记录

状态：**P3 源码推广、正式 32-worker 接续与首份新产物验收 PASS**。9,126-episode 全量生产仍在进行中；以下完成数为明确时刻的现场快照，不代表全量已完成。

## 当前现场

截至 **2026-11-14T01:21:14.933674+08:00**，原计划共 9,126 条，已完成 **804**；其中本次接续后完成 **11** 条，均为 EVENT_KEYFRAME。现场仍有 **32 个 worker（GPU 4/5/6/7 各 8）**，全部带 --sg-event-index。

588、621 两条既有 native_gt 几何导出失败本轮各重试两次后仍失败；其余队列继续执行。失败条目不计入 COMPLETE，也未修改原计划予以排除。

## 正式源码与验收依据

| 项目 | 精确版本或结果 |
|---|---|
| P3 实现源码 | 2662bc7947cad878cf752bd0aba6733cae0346a3 |
| V3 推广及实际启动 HEAD | f36b78b39f8ab4f6317e01bd2192c9899ae887d6 |
| nav_sg G2 | 9734d2e0e261a47efbd00f5de78ec6c1a983557b |
| Cosmos Gitlink / checkout | d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2 |
| G2 CPU Gate | 953 PASS；0 failure / error / skip；141 个源码文件 Gate 前后哈希不变 |
| 正式源码绑定 | 10 个变更源码/测试文件 SHA256 与最终 Gate 完全一致 |
| 审核 | docs/collab/chatgpt/reviews/2026-11-14_G2_P3_2662bc79_EVENT_KEYFRAME_APPROVE_CODE.md |

本提交只更新运行记录与任务账本，P3 生产源码不变。服务器仅 fetch / fast-forward 同步，没有在服务器 commit / push。g2、atomic_6views_run、episode、scene_graph_compact_v3 导入路径均落在正式 psm_wma_v3。

nav_sg 服务器 HEAD 与 GitHub G2 ref 已经通过 connector 独立核对为同一版本。本次尝试刷新服务器 origin/G2 时旧 VS Code askpass socket 失效，因此没有以旧 tracking ref 的 ahead 提示判定源码差异；本轮 nav_sg 源码未变。

## “不更新就不建帧目录”的最终契约

每个采样状态仍在 episode_manifest.json 中保留一行，保存当前 frame、timestamp、GT row identity、source SG hash、实际解析 SG hash，以及视图与 SG 的实体文件引用。

- 有任一实体 PNG 或 SG 写入时，才创建该状态的 state_* 目录。
- 所有视图和 SG 均复用时，只写 manifest 行，对应状态目录不存在是合法产物。
- SG EVENT_KEYFRAME 复用最近实际保存的 SG；不写 per-frame delta。首帧、视图 FULL、语义/结构/未知字段变化，或几何误差达到 1 mm 时写新 SG。
- bbox / centroid 使用三维欧氏差，connection 白名单距离使用绝对差；复用误差必须严格小于 1 mm。比较锚点是最近实体 SG，避免累计漂移。
- 机器人箭头以最近实际绘制的 floor marker 为锚点，平移 1 mm / 转角 1° 累计触发更新。
- 当前身份字段逐帧内联，不能继承被引用 SG 的旧 frame/time/GT identity。阈值内几何复用不声明与当前 raw SG 数值完全相等。

旧 v1/v2/v3 合法完成产物由 resume 保留，旧 lossless converter 仍保持逐数值恢复语义。本轮没有将既有产物全部重打包。上述省文件行为针对最终发布目录；上游 SG 计算与私有 v2 中间打包阶段仍存在，正常成功 worker 会清理自己的 work 子目录。

## 独立真实 Gate 与正式首份产物

| 验证项 | 独立真实 Gate：CloseFridge / 569 | 正式生产：CloseFridge / 812 |
|---|---:|---:|
| 采样状态 | 17 | 16 |
| 实际状态目录 | 5 | 7 |
| 无目录引用状态 | 12 | 9 |
| SG 实体 / 引用 | 5 / 12 | 7 / 9 |
| SG delta 文件 | 0 | 0 |
| 实体 PNG / 图片引用 | 40 / 96 | 49 / 63 |
| 逻辑 PNG | 136 | 112 |
| 当前帧身份 | 17/17 与独立原始来源一致 | 16/16 解析值与当前 manifest identity 一致 |
| 几何误差 | 独立 raw 对比实测最大 0.088902 mm | manifest 声明最大 0.601831 mm，边界/哈希/解析校验 PASS |
| 最终验收 | CPU、独立 raw、PNG 字节、真实 Viewer Node PASS | 完整 v3 validator、plan completion、目录/引用/metadata PASS |

必须区分两列的证据强度：569 的误差来自独立原始 SG 对比；812 的几何数值是生产记录中的声明误差，验收检查其界限与发布契约，没有冒称再次独立比较已清理的 raw 工作产物。

812 的无目录 state IDs 为 2、3、4、5、6、7、8、9、15。其 manifest SHA256 为 6d9a15edac0604dc811ce96ca6683839aaefa493fecf8ebf03540840259f8734。全部 112 个逻辑 PNG 引用可解析，SG 的 source identity 与 plan 匹配。

前置详细证据：[P3 SG EVENT_KEYFRAME Gate](P3_SG_EVENT_KEYFRAME_GATE_20261114.md)。本次机器可读运行证据：[production resume JSON](P3_SG_EVENT_KEYFRAME_PRODUCTION_RESUME_20261114.json)。

## 排空与接续

旧调度器 PID 1894179 只暂停派发，已有 worker 自然完成；01:05:01–01:11:11 CST 排空耗时 370.32 秒，最终保留 793 个完成 episode。随后终止已无子任务的旧 dispatcher，再同步正式 V3。

固定计划 index.json SHA256 前后及接续后均为：

```text
f1dfcc5243a466a1c1a885e407fade7ef860eb72079494f3cc7dc90334283643
```

新 dispatcher PID **2177485**，01:12:23 CST 在原 tmux **g2_view / %245** 启动；完成旧结果校核后，01:16:20 CST 观察到 32 个正式 worker。01:20:06 CST 首份新产物完成，01:20:09 CST 消费/发布检查退出码 0。

实际启动命令：

```bash
bash /mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/.g2_atomic_6views_prod/launch_v3_p3_resume_20261114.sh
```

关键运行路径：

- 正式 root：/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3
- 正式 nav：/mnt/data/shenzhen/szrobot/logs/.tmp_backup/nav_sg
- 固定计划：/mnt/data1/data_v2_0617/robocasa365_v3_flat/.g2_atomic_9126_plan_20261113
- 最终输出：/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-6views
- 新 work root：/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_atomic_6views_v3_9126_work_20261114
- 日志：/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/.g2_atomic_6views_prod/logs/g2_p3_resume_20261114.log
- 原始运行验收证据：/tmp/g2_p3_finish_20261114/evidence/production_verified.json

launcher 的 HEAD guard 应随已核对的纯文档 fast-forward 更新；实际执行源码仍以上述 2662bc79 的源码指纹为准。GPU 0–3 不参与此次 G2 队列；marker 外观参数与旧生产省略参数时的默认值逐项一致。

## 独立未关闭问题：588 / 621 collision mesh

独立只读排查确认旧运行已经出现相同失败，且新旧 source receipt 的源文件 SHA 与 source_model_closure_sha256 一致：

| Episode | 旧日志错误行 / 最终失败行 | Source model closure SHA256 |
|---|---|---|
| 588 | 101913、102264 / 102295 | baba06ab64d99784b2a8687fe0b6c9afda1ccf342ac0fa24059eebd519e61151 |
| 621 | 111224、111958 / 111996 | 687ab55fc98da34c147a9bba4bcd2928306330fe59c5e2bf669cf5eecada362f |

旧日志位于正式 root 的 .g2_atomic_6views_prod/logs/full_9126_p012_manual_resume_20261113.log。新旧均输出 Oracle export failed: degenerate mesh face；失败发生在 native_gt collision 导出，早于 F27 / P3 打包。

nav_sg/g2/gt/mujoco_scene.py 的 validate_mesh 对叉积模长 <=1e-14 的任一面拒绝整个 mesh，随后还要求闭合和一致定向。这个条件同时包含真正零面积面和正面积但极小的面，当前错误信息没有 geom / mesh / face 上下文，因此尚不能认定可无损剔除。

后续独立任务先定位面与面积分布，再决定严格零面积冗余面处理或数值判定修正；继续保持闭合、一致定向和保留内腔的 solid-angle winding 契约。不能直接删除全部小面或替换凸包。本轮没有为通过数据而放宽这些检查，也没有修改源资产。
