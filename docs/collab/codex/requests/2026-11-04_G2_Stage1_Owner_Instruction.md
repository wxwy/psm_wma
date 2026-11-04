建议 Codex 现在只实现 G2 第一阶段：RoboCasa365 target-atomic → RGB-D/Pose 离线缓存构建。

不要同时接入 nav_sg，也不要修改 Cosmos 训练链路。先完成可靠、可复用的导出工具，并通过单 episode 验证，再扩展到 N=100 数据集。

下面的指令可以直接交给 Codex。

# Codex — PSM-WMA V3 G2 Stage-1：RoboCasa365 RGB-D/Pose 离线导出实现

## 一、任务目标

基于已经完成的 DS_PRO G0–G4 可行性核查，在 PSM-WMA V3 分支实现正式的 RoboCasa365 target-atomic RGB-D/Pose 离线缓存构建工具。

目标链路：

```
RoboCasa365 target-atomic 原始数据
    │
    ├── states.npz
    ├── model.xml.gz
    ├── ep_meta.json
    └── dataset_meta.json
           │
           ▼
    RoboCasa/MuJoCo 状态恢复
           │
           ├── 原始 RGB（复用，不重复编码）
           ├── 渲染米制 Depth
           ├── 相机内参 K
           └── 逐帧相机外参 T_world_camera
           │
           ▼
    RGB-D/Pose 离线缓存
           │
           ▼
    下一阶段 nav_sg 建图（本次不实施）
```

本次只负责 Stage-1，不涉及 nav_sg、ROS、Scene Graph、PSS/BEV 生成或 Cosmos 训练修改。

## 二、当前已确认的现场证据

DS_PRO 已完成以下核查：

1. 原始数据：RoboCasa365 target-atomic，18 类任务、9,126 episodes。
2. 所有 9,126 条原始 episode 均存在 `states.npz`、`model.xml.gz`、`ep_meta.json`。
3. Flat V3 存在 `flat_v3_mapping.parquet`，共 2,231,347 帧。
4. 已抽样证明 Flat V3 与原始 parquet 的 `observation.state` 完全一致。
5. 已通过官方 `reset_to` 路径成功恢复 CloseFridge episode_000000。
6. 该 episode 的 t=0/214/428，已成功生成两路 RGB、Depth、K、Pose。
7. 重渲染 RGB 与原始 RGB 的 MAE 约 1.05–2.07。
8. 用户已经人眼检查并确认原始 RGB、重渲染 RGB、Depth 灰度及伪彩色视觉对齐。
9. 当前 Depth 几何交叉验证仍有坐标约定问题需要正式关闭。

参考 DS_PRO 已验证的临时实现：

```
/tmp/g3_full.py
/tmp/g3_diag.py
/tmp/g3_out/
```

原始数据目录：

```
/mnt/data1/data_v2_0617/robocasa365_official/v1.0/target/atomic/
```

Flat V3：

```
/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic/
```

上述路径为 DS 现场证据，不允许硬编码为程序唯一可用路径。

## 三、代码位置和职责边界

目标分支：`wxwy/psm_wma` 的 `V3`。

建议新增：

```
tools/g2/
    export_robocasa_rgbd_pose.py
    verify_robocasa_rgbd_pose.py
    test_rgbd_pose_export.py
```

允许根据现有代码组织适当调整，不要求机械地拆成三个文件。

必须优先复用：

- RoboCasa 官方场景和状态恢复接口；
- robosuite / MuJoCo 深度渲染接口；
- 已有的 Flat V3 episode 选择与映射逻辑；
- `tools/g0/` 中必要的数据索引工具。

不要复制一套已有的 episode 选择算法。

不得修改：

- `cosmos-framework` 模型及训练代码；
- V3 训练 recipe；
- 现有数据集及 checkpoint；
- 原版 RoboCasa / robosuite 底层；
- nav_sg；
- V2 分支及其他正在运行的工作区。

遵循根仓库 `AGENTS.md` 的分工、审查及提交规范。Codex 负责正式实现和 CPU/静态检查，DS_PRO 负责服务器运行验证。

## 四、核心功能要求

### F1：准确选择与映射 episode

支持通过参数传入：

- 原始数据路径；
- Flat V3 数据路径；
- 输出缓存目录；
- task class；
- episode ID 或 episode selection manifest；
- 相机列表；
- depth 存储格式；
- 可选的任务/episode 分片参数。

优先直接使用 `flat_v3_mapping.parquet` 建立：

```
task_class
global_episode_index
local_episode_index
frame_index
source_state_index
```

必须与现有 N=100 训练集的真实 episode 选择一致，不能重新随机抽样。

正式输出必须能追溯回原始 episode 和 frame。

### F2：恢复场景并渲染 Depth

采用 DS 已成功验证的官方恢复路径：

1. 根据原始 dataset metadata 创建仿真环境。
2. 加载对应 `model.xml.gz` 和 `ep_meta.json`。
3. 按原始 `states.npz` 逐帧恢复仿真状态。
4. 通过 robosuite / MuJoCo 接口渲染 Depth。
5. 将 Depth 转换为米制距离。
6. 获取对应相机的内参和逐帧外参。

优先 state replay，不采用 action replay。

复用环境时必须正确恢复每个 episode 的模型、对象配置及状态，不允许跨 episode 残留。

支持原始数据存在的三路相机：

- `robot0_agentview_left`
- `robot0_agentview_right`
- `robot0_eye_in_hand`

初始运行验证以 DS 已经成功测试的 left + eye_in_hand 两路为主，其他相机按需要启用。

不要默认为所有相机共享同一个外参。

### F3：相机坐标与 Depth 正确性

重点修复临时验证代码中的坐标约定问题。

MuJoCo/OpenGL 相机坐标和图像像素坐标必须明确转换：

- OpenGL 相机 X 向右、Y 向上、-Z 向前；
- 图像像素 v 向下；
- 用于 nav_sg 的相机位姿和 Depth 表达必须具有明确约定。

验证反投影时，不允许直接将 `(v-cy)/fy` 当成 OpenGL 相机 Y 坐标而忽略符号。

应明确区分：

- OpenGL depth buffer；
- 米制 optical-axis Z-depth；
- 射线距离；
- `T_world_camera_gl`；
- `T_world_camera_cv`（如果导出 OpenCV optical frame）。

不要将两种相机坐标矩阵混用。

必须修复并复测几何验证脚本，确认 K、Depth、Pose 的一致性。

如果继续使用 `mj_ray`，需要正确处理其几何过滤、静态物体、不可见几何体等语义，避免把错误的射线测试当成 Depth 错误。

### F4：缓存格式

第一版建议：

- Depth：优先评估无损压缩的 `uint16` 毫米表示；
- 相机内参：float32；
- 相机外参：float32；
- RGB：优先保存原始视频引用和帧映射，不重复编码全部 RGB；
- 元数据：JSON manifest；
- invalid Depth：显式记录有效性，不将无效像素静默编码为有效距离。

对于 `uint16`：

- 明确有效距离范围；
- 检查溢出；
- 转换为米后验证量化误差；
- 如实际 Depth 超过可表示范围，应报错或采用明确的回退策略，不允许静默截断。

实际缓存格式由最小实验选择，不预设无损压缩一定具有明显空间收益。

### F5：断点恢复与失败隔离

保持简单实现，不构建复杂任务调度框架。

要求：

- 以 episode 为最小导出单元；
- 单 episode 成功后原子提交；
- 已完成且验证通过的 episode 可以跳过；
- 失败 episode 不污染完整缓存；
- 重跑不会生成重复数据；
- 输出可追溯的 manifest 和简短日志。

支持按 task/episode 分片，后续可以使用多进程运行。

第一版无需实现复杂的分布式调度、动态负载均衡或多 GPU 框架。

## 五、验收测试

### Gate A：静态与 CPU 测试

Codex 完成：

- 代码语法、import、lint；
- episode 映射与选择测试；
- 数据格式 round-trip 测试；
- Depth 量化误差测试；
- K/Pose 坐标变换测试；
- episode 重跑幂等性测试；
- 输出不完整时的错误处理。

要求测试不修改真实原始数据。

### Gate B：单 episode 实际恢复

交由 DS_PRO 在训练服务器运行。

测试：

```
Task: CloseFridge
Episode: 000000
Frames: 0, 214, 428
Cameras:
  robot0_agentview_left
  robot0_eye_in_hand
```

需要返回：

- 原始 RGB vs 重渲染 RGB 的 MAE/PSNR/SSIM；
- Depth 有效像素比例、min/median/max；
- K 和 Pose 合法性；
- 腕部相机位姿变化；
- corrected backprojection 几何误差；
- 缓存读取与转换精度；
- manifest/frame 映射一致性。

用户已完成人眼对齐验证，正式测试重点放在数值正确性及稳定性，不需要重复大规模输出 PNG。

### Gate C：少量完整 episode

Gate B 通过后，再运行 3–5 条不同任务的完整 episode。

验证：

- 全帧输出完整；
- 不发生累计 frame 偏移；
- episode 间独立；
- 输出缓存可以重新读取；
- 重复执行结果一致；
- 吞吐和存储占用；
- 不会占满磁盘或干扰现有训练。

Gate C 完成前不得启动 N=100 批量导出。

## 六、特别关注两个已知风险

### R1：时间戳偏移

DS 报告原始 states 与 parquet 时间戳存在约 0.5 秒偏移，但按帧索引恢复后的 RGB 已高度一致。

正式实现应使用经过验证的 episode/frame 映射，不依靠 timestamp 推导索引。

需要解释时间戳差异，但不要仅因为 timestamp 不同就人为偏移 state index。

### R2：全量成本

全量 9,126 episodes、2,231,347 frames 的原始 Depth 缓存可能超过数百 GB。

当前不需要一次处理全部数据。

正式批量任务以现有 target-atomic N=100 训练 episode 集合为准。

输出容量估算应使用真实选中帧数和实际压缩比，而不是凭 episode 平均长度估算。

## 七、交付要求

请先完成正式代码实现、静态/CPU 测试，并提供：

1. root / child Git commit 和代码改动清单；
2. 新增工具的使用说明；
3. Stage-1 输入/输出 schema；
4. Gate A 测试结果；
5. 可以交给 DS_PRO 执行的 Gate B 精确命令；
6. 失败处理与回滚方式；
7. 尚未验证的风险。

按照项目现有协作规范提交实现和审核材料。

**不允许将 Codex 的静态测试通过宣称为实际 Depth 恢复通过。**

Gate B、Gate C 需要 DS_PRO 使用服务器实际数据验证。

所有原始 RGB、Depth、视频、缓存和可逆编码数据必须保留在服务器，不得通过 ChatGPT 或其他外部通道传输。跨会话只返回必要的非敏感文本统计与审核结论，报告不得超过 100,000 字。

## 八、范围控制

本阶段不实施：

- nav_sg 接口；
- Scene Graph 构建；
- BEV/PSS；
- Global Spatial Encoder；
- Cosmos 输入修改；
- G2 训练；
- 大规模分布式导出系统。

最终目标只有一个：

**提供一个经过验证、可重复运行、能与 Flat V3 训练帧严格对齐的 RoboCasa365 RGB-D/Pose 离线导出工具。**

完成 Gate A 后提交审核，等待 Gate B 现场测试结果，再决定是否进行批量构建。

我的建议是把单 episode 几何数值验收设为必须关闭的 Gate，同时不再重复开展大规模可行性调查。

Codex 做完实现后，我们先审核代码，再给 DS 精确的运行命令。DS 验收通过后直接推进 N=100 缓存构建，避免把项目拖入无休止的工具开发。