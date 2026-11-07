# PSM-WMA G2 详细设计 v0.8：仿真—真机空间视图可生成性约束

日期：2026-11-07。状态：**用户确认的硬约束 + 设计建议**；未冻结具体渲染算法/视图配置，不授权代码、渲染、训练或评测。该文件补充并在冲突处覆盖 [v0.7 上下正交与规范方向视图](./PSM-WMA_G2_detailed_design_v0.7_2026-11-07_orthographic_bev_canonical_views.md)、[v0.5 可渲染地图](./PSM-WMA_G2_detailed_design_v0.5_2026-11-06_renderable_spatial_bev.md) 与 [v0.4 空间 latent cache](./PSM-WMA_G2_detailed_design_v0.4_2026-11-06_spatial_view_latent_cache.md)。

## 0. 最重要原则（OWNER-CONFIRMED）

> **所有向 Cosmos 提供的 BEV、上下正交图、房间中心多方向/多俯仰视图，都必须能以真实世界 nav_sg 的实际建图产物为源生成。**

MuJoCo 的作用是替代仿真阶段的**感知来源**，提供完整 GT 的几何、实例、姿态、关节与关系；不能成为模型端独占的、真实 nav_sg 无法生成的**图像渲染接口**。不因 Full Map + MuJoCo GT 优先而放松这一限制。

此处“可以生成”含义：在真实场景中 nav_sg 已经建成相应几何/外观/空间状态后，同一读取器能够在相同视图协议下产生空间图像；**不意味着**真实感知必须像 MuJoCo 一样完整、每个像素都正确，或当前 nav_sg 已经具备完成实现。

模拟训练中可利用完美 GT 作为 Full Map 理想上限，但真实路径要支持部分覆盖、遮挡、深度空洞与未知；这些不能被虚构为已观察的空闲区域或颜色纹理。

## 1. 从两个后端到同一渲染接口（PROPOSED）

```text
                  MuJoCo (GT backend)      nav_sg (RGB-D perception backend)
                     Mesh/primitive             RGB-D fused 3D geometry
                     class/instance/pose        estimated class/instance/pose
                     material/texture*          observed surface color*
                           │                           │
                           v                           v
                     GT Map Adapter            Perceived Map Adapter
                           └────────────┬──────────────┘
                                        ▼
                                Canonical Spatial Map
                        3D geometry + state + identity + relations
                           color/appearance (optional / mask)
                           known/unknown / evidence provenance
                                        │
                                        ▼
                               Shared Spatial View Renderer
                         lower orthographic + upper orthographic
                           room-anchored canonical 360° views
                                        │
                                        ▼
                           L2 image/geometry + validity/visibility
                           L3 frozen image-encoder latent cache
                                        │
                                        ▼
                                   Cosmos (Global path)
```

*材料/纹理不应是生成视图的必备字段：感知地图可能仅具 RGB-D 观察到的表面颜色；真实缺失色彩时应该有一致的几何渲染后备样式与显式有效性信息。**

**主输入不得默认直接使用 MuJoCo 原生渲染器生成的真实 RGB、或 MuJoCo 专属的封闭 Mesh/纹理渲染功能**，除非验证 nav_sg 的现实路径通过相同的规范几何/外观表示也可以生成同类型视图。MuJoCo 原生渲染可做独立的 GT 对照和人工核验，但不能未经共通性检验就作为训练缓存的正式输入。

## 2. 当前 nav_sg 的真实能力与尚存缺口（SOURCE-CONFIRMED，2026-11-07 追加纠正）

**更正**：2026-11-07 进一步核查，nav_sg 早已包含独立的 `ColorCloudMap` 真彩色 RGB-D 融合功能，先前把系统笼统称为“只有 XYZ，缺乏颜色融合”是不完整的。应区分两条现有支路：

- `mapping_8_3/mapping/include/mapping/utils/color_cloud_map.h` 及 `src/utils/color_cloud_map.cpp`：`pcl::PointCloud<pcl::PointXYZRGB>` + 体素 `VoxelAccum(sr,sg,sb,w)`，通过 RGB 图像与像素索引的世界点云在 voxel 级融合真实 RGB，`toPointCloud()` 导出。不是伪彩。
- `src/utils/color_cloud_map_worker.cpp` 和 `src/map_ros.cpp`：独立异步 RGB/Depth/Pose worker，按配置发布 `/color_cloud_map`；real/sim 参数 XML 默认启用、发布 2Hz，真机/仿真体素叶分别 0.02m/0.05m。当前 `g2/offline/replay_robocasa.py` 明确禁用彩色云，故这条路径还未进入现有 G2 离线构建证据。
- `include/mapping/object_mapping/object_cluster3d.h`：**另一条语义对象链** 的 `ObjectCluster3D::cloud` 仍为 `pcl::PointCloud<pcl::PointXYZ>`；`object_map3d_visualizer.cpp` 可按 cluster ID 生成 RGB(A) 伪颜色，但那不是观测 RGB。
- `include/mapping/scene_graph/scene_graph_manager.h`：`SceneGraphObject` 主要为 room/cluster/centroid/AABB/prob，没有直接引用颜色、姿态版本或带纹理表面；当前 ColorCloudMap 没有自动与对象实例、SG、关系及任意 room camera 的渲染器对齐。
- `src/map_ros_visualizer.cpp` 的 RViz 点云显示不等于已具有任意规范虚拟相机的 RGB 新视角渲染。仅存在颜色点云也不能保证隐藏面被观察、遮挡和空洞可合理恢复。

**修正后的技术缺口不是“从零实现 RGB-D 彩色点云”**，而是：彩色点云与 SG/实例/时序状态的绑定、移动对象旧 voxel 撤销、低空洞的正交/房间虚拟相机投影渲染、缓存/latency。绝不能因为 ColorCloudMap 已有就宣称 10Hz 或完整三维 RGB 视图已通过 Gate。

详细源码/2Hz 与 ≥10Hz 性能/3DGS 对比归档：[彩色点云与 10Hz/3DGS 专项审计](./PSM-WMA_G2_colored_pointcloud_10Hz_vs_3DGS_audit_2026-11-07.md)。

不要把一个 PointXYZ 按语义标签着色当作“真实彩色场景”；未来空间图像必须来自已知真实颜色表面或显式 geometry-only recipe，并对未知/未见区域保留有效性标记。

## 3. 三类当前候选视图的现实可生成性要求

| 视图 | 从 nav_sg 哪些实际产物生成 | 现实限制及必要补充 |
|---|---|---|
| Lower Orthographic | 3D Occupancy/点云/表面几何 + z 切分 + 正交投影 | 可做真实几何/高度/实例图；下层可见性和空洞必须区分；不需要独立 costmap |
| Upper Orthographic | 同源 3D geometry + 上层裁剪 + +Z 正交投影 | 上层实体曾未被观测或表面遮挡时只能显示已知表面/unknown；不能以 MuJoCo GT 暗中补出未见柜内纹理 |
| Room Canonical Views（固定锚点 yaw/pitch/FOV） | 3D 几何/颜色/状态，投影、深度测试、相机内外参 | 可以做几何投影视图；**要有真实外观 RGB 需要地图保存颜色/可渲染表面**；离线合成新视点可能有空洞、遮挡缺失，不能默认为完美摄影级照片 |

独立问卷：顶部固定 perspective 备选也必须遵守本条。是否选择高位相机或正交/透视投影是 renderer 的参数，不能把“真机机器人曾拍到该视角”当作前提；它可以从已经构建的三维地图**合成**，但缺少的表面仍无法合理重现。

- 参考 Left 高度只是 room camera 初始参数，不要求 Left 实际到场或机械臂进入房间规范图。
- SG 构建阶段不按大/小物体删实体；哪个物体出现在读出由 renderer 可见性与后续 Global 模态预算决定。
- 不另建导航 Costmap/Traversability 标签。3D 几何忠实表达地面/墙/物体和高度，底盘位姿独立条件化，能否通行由策略学习。

## 4. 建议共享中间表示，不依赖原始图像类型（PROPOSED）

```text
SpatialSceneFrame:
    scene_template_id, episode_id, frame/timestamp
    coordinate_world + room_frames + version_id
    occupied/free/unknown (if available)
    surfaces: xyz, optional rgb / normal / geometry_support / validity
    entities: stable_id, class, geometry_ref, pose, parts, joint/state
    relations: ref to typed temporal relation store
    visibility_evidence: observed / reconstructed / gt / unknown
```

关键是同一份`SpatialSceneFrame` Schema 可由 GT Adapter 或 Perception Adapter 生成，由同一个 `render(scene, view_spec)` 出图。

- 真机的 appearance 必须有来自 RGB-D 的表面观测证据，不可由 GT 资产填写；
- 可见性、空缺像素、未见空间和全场景 GT 需要显式区分，可在 L2 同步保存 validity/coverage/depth/instance 等通道；
- **不要让 MuJoCo 的 mesh/texture 作为 Stage A 编码器的隐含特权输入**，而训练时只给 RGB-D 点云的真机系统无法复现；
- 如果希望训练时既有完美 Oracle 视图又能部署，可以将 GT 几何通过相同 `SpatialSceneFrame` 和 renderer 成像；以后再显式增加感知噪声/缺失视图训练，与 Full-GT Oracle 结果区分报告。

## 5. 共同缓存规则与 Sim/Real 一致性 Gate

- L2/RGB/geometry/validity、L3 frozen-encoder latent 采用**同一 view_recipe**，绑定投影、裁剪高度、yaw/pitch/FOV、房间锚点、尺寸、光照/着色规则与空间状态；不能仿真用高保真 Mesh RGB，真机临时改成语义框图且仍叫同一种输入。
- 离线训练全部 precompute L2/L3，复用状态/视图版本，绑定 G1 exact frame index；训练期间不能恢复 MuJoCo/render/encode。
- 真机或在线 sim 不可能提前拥有所有 rollout 未来状态的图缓存；需要同一 renderer 的**增量生成 + frozen encode + 版本复用**。这与离线训练速度优化是不同问题。
- Room 方向图的规范虚拟锚点、45° 或更密集 yaw、独立 pitch/FOV 均是共用视图规格，**不能选择只有 MuJoCo 原生摄像机 API 才能执行而真实点云投影无法表达的显示规则**。
- **门槛 A：可生成性**。用 nav_sg 导出的真实 RGB-D/点云/体素，在离线重放中实际生成 Lower/Upper/Room View（不是只理论声称可生成）。
- **门槛 B：投影一致性**。同一已知几何的 GT 与 perception 路径，用同一个 renderer 的输出坐标、尺寸和几何拓扑相对位置一致；未知缺失内容可以不同，但必须标注。
- **门槛 C：训练输入合同**。所有图像类型在 GT 和 nav_sg 后端有同名同结构的 L2/L3 ABI（包含 modality/validity），可按相同 Global Reader 编码。不要求两条支路像素完全一致，但不允许一方独占特征字段。
- **门槛 D：真实延迟和信息保真**。测真机端更新地图→视图→latent 的成本、几何空洞对可视图的影响。若房间 360° RGB 代价过高或全是空洞，则先将此模态降级备选，而不是强求合成好看的不存在图像。

## 6. 最新取舍摘要

- **Owner confirmed**：所有空间视图都必须在真实世界能用 nav_sg 产物生成。这是 G2 视图方案与缓存方案的硬门槛。
- **Source confirmed（2026-11-07 修正）**：nav_sg 自带基于 RGB-D 的 `ColorCloudMap<PointXYZRGB>` 真彩色体素融合和 ROS 发布，另有 `ObjectMap3D<PointXYZ>`/SG 语义链；**缺口是两支路的关联、动态更新和任意规范相机新视角渲染**，不是完全没有 RGB。完整 Room RGB 视图质量/≥10Hz 仍未经实测。
- **Proposed**：两个来源共享 `Canonical Spatial Map → Shared Spatial View Renderer → L2/L3`。先复用现有 ColorCloudMap 的真实颜色表面作为候选渲染输入，与 SG/State 绑定后核实 Lower/Upper/Room 新视角的空洞、动态更新及延迟；是否成为 P0 取决于真机可生成性和性能 Gate。
- **Still open**：现有 RGB-D 彩色体素与 SG 实例/动态状态如何对齐、从现有彩色点云到规范视图的孔洞及画质、动态 voxel 撤销、≥10Hz 实际时延、unknown mask、上下剖切高度和编码器选型。
- **Not authorized**：任何生产构建、真机渲染、GPU 训练或数据全量编码。

本稿覆盖此前“只要 MuJoCo 可渲染即可把图片作为 Cosmos 主输入”的表述，明确 Sim/Real 图像可生成性和共用 ABI 是入选视图模态的前置验证。
