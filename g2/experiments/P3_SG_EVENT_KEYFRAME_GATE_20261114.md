# G2 P3：SG 事件关键帧与无目录帧验收
日期：2026-11-14 CST

## 本轮完成的行为

SG 与非俯视图共享物品变化事件。首帧和场景 FULL 保存完整 SG；关系、结构或几何保护也可单独触发 SG 新关键帧。其余状态中，bbox 端点、质心和连接距离相对最近实际 SG 关键帧的误差严格小于 1 mm 时，直接引用该 SG，不为微小浮点变化写增量文件。

机器人底盘 marker 使用平移 1 mm / 转角 1° 门槛，相对上次实际绘制累计；场景 FULL 重绘也会更新机器人 anchor。每帧 frame_id、timestamp_ns、GT row hash 保留在 episode_manifest.json。所有视图和 SG 都复用时，这一帧只有索引，最终输出不创建 state 目录。

新生产模式为 EVENT_KEYFRAME，允许受限几何复用，不能称其数值始终与 raw SG 一致。source_scene_graph_sha256 绑定当前 raw SG；scene_graph_sha256 绑定实际读取的 SG；scene_graph_max_geometry_error_m 记录误差。原有 LOSSLESS 转码和旧 v3 解码继续可用。

## 固定源码

- Implementation root: `2662bc7947cad878cf752bd0aba6733cae0346a3`
- Base V3: `664678fd91c23bfd16505380d0d3db6cf9f15ad6`
- Cosmos child/Gitlink: `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`（未修改）
- nav_sg G2: `9734d2e0e261a47efbd00f5de78ec6c1a983557b`（未修改）
- 10 个 P3 源码/测试文件的服务器、实现侧和 GitHub 内容一致，完整指纹见同目录 JSON。
- 独立静态复核覆盖机器人阈值、SG 格式及守卫、无目录帧、Viewer 消费；没有未关闭的阻断缺陷。

## 实际验收结果

| 项目 | 结果 |
|---|---|
| 最终 G2 CPU suite | **953 passed；0 failed / error / skipped**，35.23 s |
| Gate 前后源码 | **141 文件哈希不变** |
| 真实输入 | CloseFridge / global episode 569 / layout 7 / 152 原始帧 |
| 固定采样 | 17 states：0,10,...,150,151 |
| 实际原始源 Worker | 完整 source→native Room/SG→snapshots→F27，exit 0 |
| 新机器人策略 | LAST_DRAWN_FLOOR_MARKER，0.001 m / 1° |
| View 事件 | 5 FULL，12 REUSE_ALL |
| 最终实体 SG | **5** |
| 最终 SG delta 文件 | **0** |
| SG 引用状态 | **12** |
| 最终 state 目录 | **5** |
| 完全复用且没有 state 目录 | **12** |
| 当前帧身份 | **17/17 精确一致** |
| 原始 SG 数值完全一致 | 5 个关键帧 |
| 阈值内复用几何 | 12 状态，最大三维/距离误差 **0.00008890237660085534 m ≈ 0.089 mm** |
| 逻辑视图 | **136/136** 与实际 F27 输出字节一致 |
| 实体 PNG / 图片引用 | **40 / 96** |
| Viewer | 当前实体图、引用图、无目录帧与 island 路径均可解析 |
| v3 completion / resume | 通过 |
| 最终脚本退出码 | 0 |

第一次全量 CPU 验证为 937 PASS、2 optional real-asset tests skipped；随后提供本次真实 rebased MJCF，最终 953/953 含所有新增 EVENT 边界用例通过，零跳过。

真实 Worker 先生成了包含新机器人阈值的 F27 产物，耗时 275.81 s；随后仅修改 SG 打包策略并复用同一份 F27 产物验收，无需重复仿真。F27/robot/source/native 源码在这两步间未改。此任务与正式 32 workers 共享 GPU4，时间不是独占条件下的吞吐基准。

## 格式与读取契约

Manifest 级字段：

- `sg_geometry_policy = EVENT_KEYFRAME`
- `sg_geometry_error_bound_m = 0.001`
- `sg_geometry_reference_policy = LAST_PHYSICAL_SG_KEYFRAME`
- `sg_frame_metadata_policy = INLINE_FRAME_METADATA_WITH_DIRECT_SG_BODY_REFS_V1`

每个采样状态始终保留行，包含原始 frame、当前帧身份、view_pngs/view_refs、scene_graph/scene_graph_ref、raw 与 resolved SG hashes、实际几何误差。

- 全部复用：view_pngs 为空，view_refs 均直达已有实体图片；scene_graph_ref 直达实体 SG；不创建该 state 目录。
- 只有图片更新：只为新图片创建目录；SG 仍可引用。
- 只有 SG 更新：保存新 SG；图片保持引用。
- 两者更新：按实际资源写入。

`resolve_scene_graph(root, state_id)` 返回存储的 SG 几何加当前帧身份。它校验实际恢复图 hash。Viewer 只显示图片/视频，不显示 SG；其 viewPath 已按物理 owner 读取，不能把“当前帧没有目录”当成缺图。Python SG reader 负责 SG 引用解析。

## 边界与回归覆盖

几何复用只允许已知米制字段：bbox_min、bbox_max、centroid 按三维欧氏距离；connection distances_m、direct_bbox_gap_m、distance_m 按绝对差。每个量必须严格 <1mm，达到阈值即保存新 SG。复用不移动 SG anchor，防止慢速累计漂移被永久忽略。未知字段变化、关系/房间/拓扑/字段形状变化触发新关键帧；非有限源拒绝发布。SG 独立更新不会改写真实 view update_mode。

测试覆盖 0.085mm 噪声、阈值边界、多轴欧氏误差、累计漂移、connection 距离、语义/未知/结构变化、raw 与 resolved hashes、旧 lossless/legacy v3、keyframe/delta 直接引用、缺文件、自身/前向/链式引用和符号链接拒绝。

## 生产范围与限制

新入口需显式 `--sg-event-index`，沿用 P0/P1/P2 前置开关。生产接续保持 GPU4,5,6,7，每卡8 workers，原9126计划、原输出根、resume、最多2次attempts。新 work 根与旧工作区分开。

完成性检查兼容合法旧 v1/v2/v3。因此 resume 会保留已完成旧产物，不会把全量目录重新生成或统一迁移；不能宣称所有旧 episode 均已采用新策略。只有新产物按本轮规则写入。原生 nav_sg / RGB-D / 10cm 导航链路和 Cosmos 训练代码不在修改范围。

当前优化减少最终产物文件和目录。上游仍先生成每帧完整 SG，发布仍经过私有临时 v2 校验，不能据此宣称已消除全部中间 IO 或 SG 计算。所有真实数据、图像与中间证据保留在服务器。

## 原始证据与复现入口

服务器工作根：`/tmp/g2_p3_finish_20261114`

- `run_completion_gate.sh`：CPU/Viewer 与17-state真实源 Worker
- `real_closefridge_569.log`：真实运行日志
- `run_event_gate.sh`：最终 CPU、真实产物 EVENT 重打包与 Viewer 验证
- `verify_real_event_package.py`：独立 SG 几何误差、源身份、136视图逐字节、12无目录帧验证
- `evidence/event_cpu.xml`、`evidence/event_cpu.log`
- `evidence/real_event_validation.json`
- `evidence/event_source_before.json`、`evidence/event_source_after.json`
- `evidence/event_node.log`、`evidence/event_gate_exit.json`
- `real_event_output/tasks/CloseFridge/episodes/episode_000569`

机器可读汇总：`g2/experiments/P3_SG_EVENT_KEYFRAME_GATE_20261114.json`。
生产排空、同步与新完成样本证据属于后续运行接续记录，不由本 Gate 的 PASS 代替。
