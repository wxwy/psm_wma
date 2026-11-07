# G2 专项源码审计：原生彩色点云、10Hz 路径与 3DGS 方案比较

- 日期：2026-11-07。
- 状态：**只读源码核查 + 文献调研 + 待验证性能目标**；未运行实际 RGB-D/ROS/渲染/编码基准测试，未修改生产代码，也不授权部署。
- 目标：澄清 nav_sg 真实彩色点云能力与缺口，评估端到端空间记忆更新频率 ≥10Hz、相对于在线 3D Gaussian Splatting 的维护与渲染成本。
- 源码：服务器独立 nav_sg PR#4 审查副本 `mapping_8_3/mapping/` 和 `g2/offline/replay_robocasa.py`。不是当下真机实时数据的实测统计。
- 关联：[G2 v0.8 sim-real view contract](./PSM-WMA_G2_detailed_design_v0.8_2026-11-07_sim_real_renderability_contract.md)。

## 1. 源码审计的更正：原生 nav_sg 已有真彩色 3D Point Cloud

此前 v0.8 中简单说“nav_sg 只有 XYZ，不具备彩色地图”是**不完整甚至误导**的，需要修正：

| 路径 | 当前 C++ 数据结构 | 来源与用途 |
|---|---|---|
| `ColorCloudMap` | `std::unordered_map<VoxelKey,VoxelAccum>` + `pcl::PointCloud<pcl::PointXYZRGB> cloud_cache_` | **已有**实际 RGB-D 点/像素匹配、按体素融合真实 R/G/B、`toPointCloud()`；不是按语义 ID 涂色 |
| `ColorCloudMapWorker` | ProjectedPointCloud + BGR8 + pose；异步单槽最新帧 | 已有 map worker、`/color_cloud_map` ROS `sensor_msgs::PointCloud2` 发布器 |
| `ObjectMap3D` | `pcl::PointCloud<pcl::PointXYZ>` | 对象身份/几何/语义特征，**不自动共享** ColorCloudMap 的真实颜色 |
| `ObjectMap3DVisualizer` | 发布端把对象 XYZ 装为 `pcl::PointXYZRGBA` | 按 cluster ID 决定 hue，仅可视化伪颜色，不是物体 RGB |
| `SDFMap3D` | 独立占据/ESDF | 维持空间几何与自由区，不等于纹理渲染 |

源码引用（审查副本）：
- `include/mapping/utils/color_cloud_map.h:19-87`；`src/utils/color_cloud_map.cpp:166-265,319-327`；
- `include/mapping/utils/color_cloud_map_worker.h:26-175`；`src/utils/color_cloud_map_worker.cpp:124-142,242-265,393-448`；
- `src/map_ros.cpp:390-458,1347-1350`；
- `src/object_mapping/object_map3d_visualizer.cpp:84-205`。

**配置证据**：
- `launch/params_sim/voxel_mapping_params.xml:70-81`：`enable_color_cloud_map=true`，`voxel_leaf=0.05m`，`pub_rate=2Hz`，`enable_prune=false`；
- `launch/params_real/voxel_mapping_params.xml:69-84`：同样开启，`voxel_leaf=0.02m`，`pub_rate=2Hz`，`enable_prune=false`；
- 当前 `g2/offline/replay_robocasa.py` 内部参数覆盖 `enable_color_cloud_map=false`，所以不能把其他部署的彩色云功能直接当作当前离线 G2 已有输出；
- `config/mapping*.rviz` 有多组 `RGB8/AxisColor/FlatColor/Intensity` PointCloud2 显示，是否确实显示 `/color_cloud_map` 要看实际加载配置和运行时订阅，RViz 中“彩色”不一定是实际 RGB；
- `vis_filter_max_z` 在彩色云发布过程中用于删除高于阈值的点，此为**发布显示过滤**，不是证明底层一定没有高处几何；做上下正交/高柜视图时必须绕过或重设此限制。

因此准确工程判断是：**RGB 色彩采集/体素融合/发布已存在，下一步需要把现有彩色云与 SG/可渲染场景对齐，并实现持久快照/增量更新/虚拟相机投影，而不是从零设计 XYZRGB。**

## 2. 10Hz 的“更新”必须给出 end-to-end 定义

目前能证明：
- `ColorCloudMap::integrate` 每次处理 ProjectedPointCloud，按 voxel key 插入或更新颜色；是近似随观测点数增长的增量成本，无必须运行的神经优化。
- Worker 异步，`enqueue` 只留最新一个 RGB/Depth/Pose；当消费较慢可丢中间帧以限制积压，**不等于不会产生输入到地图的延迟**。
- `pub_rate_hz` 默认 2Hz，但限制的是**已融合地图的 ROS 发布**；不能推断内部融合必然 2Hz，也不能把改成 10Hz 视为通过性能验收。
- 2Hz 发布当前会对`cloud_cache_`全量复制，生成一个高度过滤后的副本，再转换 PointCloud2；成本随累计点数增长，10Hz 反复整图传输可能成为瓶颈。
- `enable_prune=false` 意味着**既有颜色体素不会因为物体移动而自动从旧位置删除**。`prune()` 仅按距离 sensor_pos 删除地图远处点，并非逐对象位置撤销。
- `ColorCloudMap::VoxelAccum` 仅有 RGB 均值、权重、cloud_index，没有当前实例 ID / Last Seen / deletion evidence。动态物体、遮挡更新等需另外设计，与 ObjectMap3D/SG 状态同步。

对“≥10Hz 更新”建议区分：
A. `RGB-D→最新地图增量`（10Hz 或以上）；
B. `地图/SG 的状态版本及更新延迟`（10Hz 目标，至少新状态反映≤100ms 的预算）；
C. `固定房间视图或上下 BEV 的最新 latent`（是否严格每100ms全部重生成？）；
D. `RViz/ROS 全地图可视化发布`（无需与 A-C 同频率，2Hz 可保留）。

最关键的是 C：若每次 10Hz 都要重绘并编码 `8 room views + 2 orthographic`，即每秒最多100张图像输入编码器，还要兼顾策略推理，**远比 10Hz 仅更新几何或单张 BEV 困难**。因此推荐事件驱动的 per-view 脏标记与缓存：Room canonical view 固定，不因机器人底盘移动自动失效；非机器人对象运动仅标记可能被改变的 view；没变化的 latent 复用，但有变化的目标必须控制 stale age。

## 3. 端到端 10Hz 的首轮性能 Gate（PROPOSED，全部 NOT_RUN）

**目标**：在用户最终确定的机器人算力/分辨率、真实场景和语义检测配置下，逐帧记录 source acquisition timestamp → map integrated timestamp → SG version timestamp → rendered view timestamp → L3 encoded timestamp → Cosmos consumption timestamp。

具体统计：P50/P95/P99 时延、steady-state delivered FPS、输入帧丢弃率、每视图 stale age、点数/体素数、缓存 hit、平均/最大需要重编码的 views、CPU/GPU/内存峰值、publish/serialization 耗时。每条指标至少跨一个稳定场景和一个机器人推动物品的动态片段，区分静态好看与真正可用的动态更新。

本稿**没有实测时间**。可将单次地图状态新鲜度≤100ms、P95 end-to-end view+encode≤100ms 当作严格验收愿景，但不能以 10Hz / 2Hz 参数配置替代实测。若无法同时满足，优先 10Hz 实体状态/场景变化更新，空间视图逐区域/视角事件驱动，RViz 显示降频，不让大点云序列化占满实际推理预算。

优化顺序：
1. 不改语义主干：沿用 ColorCloudMap 的 RGB-D→voxel 颜色融合；G2 离线处理只需明确开启/复用并验证 Frame/Depth 绑定；
2. 给 color voxel 与 SG object/geometry 维护明确一致的世界帧/时间/几何映射和显示审计；
3. 把全量云 `toPointCloud → filter → toROSMsg` 从策略热路径移出，支持无需整图 ROS 发布的局部增量/共享只读快照；
4. 增加对动态移动实体受影响区域的颜色 voxel 清理/替换，保留静态背景，不以距离裁剪替代运动维护；
5. 用低分辨率视图和 GPU splat/z-buffer 渲染器验证 Lower/Upper/room canonical views 的洞与遮挡，按变化只更新受影响 view；
6. 最后评估 frozen visual encoder 共享 GPU 时的 latency，上述优化能否在特定真机 GPU/NPU 资源下成立。

工程量估计（仅经验级，相对于已有代码，**不等于实测工时**）：
- **已有颜色功能启用/查看/验证**：很小，不需重构点云全链路；
- **彩色云直接输出一张简单 BEV**：小至中等，取决于坐标和空洞处理；
- **与 SG 实例绑定 + 动态移动撤销 + per-view 增量新视角渲染 + L3 在线编码**：中等至较大，必须经过硬件 Gate；
- **如果要求高品质、低空洞、完备物体背面/柜内渲染**：单靠稀疏点云不足以保证，需要 surfel/TSDF/mesh 或 3DGS 类表示，工程和维护成本更高。

## 4. 3DGS 与彩色点云：构建、维护、渲染三项分开比

| 比较项 | 原生 ColorCloudMap（RGBD voxel→XYZRGB） | Gaussian Splatting / Gaussian SLAM |
|---|---|---|
| 初始化 | 累积点、采样 RGB、哈希融合，无 SGD | 从点/Depth 初始化 Gaussians 后可能优化位置、协方差、外观/透明度等 |
| 新观测融合 | 增量哈希写入，计算与接受点数相关 | 新高斯、重访图像、优化/剔除，可有稳定/不稳定分区的高效实现 |
| 移动物体 | 需要显式擦除/迁移旧 voxel 和关联 SG 实例 | 需要显式对象实例/动态 gaussian 管理或对旧高斯作删除/更新 |
| 新视角画质 | 快但稀疏点易出现 holes/锯齿、背景未知 | 连续 splatting 通常更平滑、照片级真实感更好 |
| 新视角 render throughput | GPU point splat 具潜力，但当前仓库无标准独立点云任意视角 renderer 和真实 FPS | 静态已优化 GS 的 GPU rasterizer 通常很快，有不少≥30fps研究结果 |
| 当前项目适配 | **color module 已有**；需要绑定语义与动态更新 | 需引入新表示、优化循环、系统身份/关系桥接、GPU/内存预算 |
| 语义/空间使用 | XYZ 测距明确，容易与 Occupancy/SG 对齐 | 可输出 depth/mesh proxy，但每个 Gaussian 的位置不等于有严格表面/occupancy 保证 |

**公开一手结果：不同论文、硬件与测试条件不能机械比较**
- Kerbl et al., SIGGRAPH 2023 原始 3DGS：≥30fps，1080p 渲染（*静态已优化地图的纯渲染*），https://doi.org/10.1145/3592433
- Matsuki et al., CVPR 2024 Gaussian Splatting SLAM：完整**单目在线** SLAM 约 3fps，https://openaccess.thecvf.com/content/CVPR2024/html/Matsuki_Gaussian_Splatting_SLAM_CVPR_2024_paper.html
- SplatMAP, 2025：RTX A6000 上约3.74fps，峰值14.96GiB，完整 near-real-time SLAM 统计，https://doi.org/10.1145/3728310
- FGS-SLAM, IROS 2025：论文报告 Replica/TUM RGB-D 平均36FPS，特殊稀疏+稠密架构的整体系统指标；不能由此推定所有3DGS的物体动态更新和多方向latent均达到36FPS，https://ieeexplore.ieee.org/document/11247035
- RTG-SLAM, 2024：根据稳定/不稳定 Gaussians 与局部像素优化，强调有界在线开销，https://arxiv.org/abs/2404.19706

**判断**：`GS 渲染快但持续维护通常更复杂` 是合理概括，却不能简化成“所有 GS 必然不能 10Hz”。相对于已经有彩色云的 nav_sg，本阶段更应先验证高吞吐 colored surfel/point splat + 动态擦除 + 统一 L2/L3 renderer；3DGS 暂作为在新视角 RGB 质量/空洞问题明显时才引入的增强路线。真正的瓶颈可能不是 point render，而是**整图复制/ROS 发布、语义/几何关联和冻结编码器**。

## 5. 与 G2 sim-real 视图约束对齐

原 G2 v0.8 文档“nav_sg RGB 外观融合缺失”的判断已经因本次源码复核而修正：**Colored XYZRGB 具有真实 RGB 值，可以直接为“真实世界 nav_sg 可生成”提供基础来源。** 不过它不等于摄影级虚拟视点复原，更不等于已有该能力在动态操控状态下满足10Hz。

主数据源：`Canonical geometry + state + color (if observed) + known/unknown`；GT 模式可以由原 MuJoCo 几何在同一 canonical contract 上构造，Perception 模式通过 ColorCloudMap/SpatialMap 给出相同 ABI；两条路径都必须显式地标记未知/不可见区域，不可在真机侧暗补 GT。

空间视图渲染器要优先支持几何表面/彩色点/颜色缺失回退，并可接入后续可选 surfel/TSDF/GS。**使用 3DGS 不应反向改变 nav_sg 的全部 SG/关系主数据结构**；可以只替换画图质量层。

当前结论：不宜为了高画质，先把已具备彩色 RGBD 融合的 nav_sg 全面重写成 GS。先跑一条真实 colored map→固定正交 BEV + room camera view + frozen encode 的端到端性能与质量 Gate，再决定是否需要 GS。
