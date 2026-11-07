# PSM-WMA G2 详细设计 v1.3（讨论方案）：中央孤岛组件的正交侧视补充

- 日期：2026-11-07。状态：**方案讨论/推荐，尚未实测和冻结**；没有生产代码、仿真或训练执行。
- 与 [v1.0 六张正交视图](./PSM-WMA_G2_detailed_design_v1.0_2026-11-07_root_affiliation_orthographic_wall_views.md)、[v1.2 单一 d BBox 连接](./PSM-WMA_G2_detailed_design_v1.2_2026-11-07_single_3d_bbox_distance.md)、[v0.8 真机可生成约束](./PSM-WMA_G2_detailed_design_v0.8_2026-11-07_sim_real_renderability_contract.md)、[v0.4 L2/L3 Cache](./PSM-WMA_G2_detailed_design_v0.4_2026-11-06_spatial_view_latent_cache.md) 相容。
- **新问题**：房屋中央独立的岛台/桌柜，与所有墙面和其他大件相距超过 d，Floor 正交俯视虽显示其 XY 形状，四墙正交立面只显示墙归属物品，因此岛台侧面的抽屉、柜门、立面外观丢失。

## 1. 主张（PROPOSED）

保留一张 Floor、一张 Upper、每墙一张正交立面作为固定空间描述；对**没有任何墙归属、但具有值得补充的立面结构的独立物体组**，按需添加一组正交侧视 `IslandComponentViews`。

对矩形房屋 + 一个中央岛台的例子：

```text
House Views: FloorTop + Upper + Wall_N/S/E/W = 6 base views
Island Component 1 (freestanding island cabinet, including drawers, plates)
  +Y side view | -Y side view | +X side view | -X side view = 4 optional views
```

全部来自同一 canonical colored 3D geometry/SG/Relations，GPU 点/surfel 正交投影，不用恢复房间中心虚拟相机、无需 FOV/pitch/r 或屋内可达锚点。四张只是一组**非墙归属的侧面补充**，不改变 SG 中所有对象应保留的原则。

## 2. 孤岛候选：特别禁止经 Floor 根将全房间连在一起

**构建方式**：
1. 从全部物品实例中（**排除地板、墙、天花板三个建筑根作为中继节点**）建立物品—物品近邻图，唯一连边判据 `distance_bbox_3d(A,B)<d`，`d=0.30m` 为待验候选。
2. 取这张**纯物体图**的连通分量。台面上盘子、抽屉等若有近邻连接则自然同组；不能通过共同接触 Floor 根将一张桌子和数米外的冰箱合并。
3. 对每个组件求当前 wall root membership。**没有任何 Wall membership** 的组件是孤岛候选；若与墙通过其他物品近邻递归相连，暂时仍视作该 Wall 的成员（沿用 v1.2）。
4. 并非所有孤立杯子/小件都必须生成四侧视。对候选组是否“需要侧面图”，可在**读出阶段**依据三维尺寸、立面是否包含柜门/抽屉/把手、任务/可见性等确定；此条件应先观察样本后选择，不能据此删除 SG 中的对象。第一轮先以独立岛台/桌柜为目标，保留所有孤岛候选及原因供审核。
5. 一个大型岛台内部若因为深度信息空缺而未能与其台面物件通过 d 归到同组，记录 `unknown`，后续可用明确 `part_of/inside` 的证据辅助**诊断**，但未经确认不改变唯一 `d` 连接判据。

**注**：孤岛不等于“与地板相隔很远”；中央岛台本身通常接触地板，恰是有 Floor membership、没有 Wall membership 的情况。无需另造空间中心定义。

## 3. 视图定义

- 默认 4 个**固定世界/房间正交方向**，沿 `±X,±Y` 朝向该组件，用相同的世界 Z 作为图像纵轴。若房间坐标轴已与墙面正交，可直接复用与四墙立面的同一朝向体系。
- 视图覆盖范围用组件完整世界 AABB/固定投影 BBox + 合理边界确定；固定物理尺度/米-像素比与元数据 `T_world_component, view_axis, projected_extent, pixel_scale, scene_version`，不要将每个组件任意拉伸至同样尺寸导致学习错误尺度。
- 只画组件自身的可见彩色表面及受其空间归属的子物件（背后没有“墙面背景”则标有效背景/unknown）。真正遮挡的柜内物体由 SG/Relation tokens 表达，不假装正交视图能穿透门板。
- 一个组件旋转可能改变世界轴下的侧视内容；统一相机轴保持世界系有利于与 Floor 位置对齐。若以后需要严格“抽屉正面”，可另研究对象自身 OBB 主轴，但不应首轮复杂化。
- 被移动/拆分的组件要更新 per-frame membership/图像版本；稳定组件的 L2 渲染图和 L3 latent 按同一 view+scene-state 缓存复用；ColorCloudMap（2Hz 发布）与 SG 高频状态分开标注新鲜度，不能让旧图像假装动态位置已刷新。
- 原 Full-MuJoCo GT 和真机 nav_sg ColorCloudMap/SG 必须通过**相同正交点/表面渲染器**生成此类视图，保持 unknown/missing evidence 显式。只使用来自真实地图可形成的数据，不可将 MuJoCo 独有纹理资产作为隐藏模态。

## 4. 与之前房间中心八方向图的取舍

| 方案 | 优势 | 代价 | 建议 |
|---|---|---|---|
| 把孤岛前景也放进四面墙的图片 | 不增加图片数量 | 容易遮挡墙面、混合空间深度，破坏 wall-only 语义 | 不推荐主线 |
| 房间中心 45°×8 透视 | 自然视角、看起来像照片 | 仍可能被岛台挡住/相机在岛台内部，需要锚点/FOV/pitch 设计 | 保留备选 |
| **孤岛组四正交侧视** | **直接补齐缺失的柜门/抽屉立面信息、无需屋内锚点、对齐固定 XY 轴** | 每个候选组件可能新增 4 图，输入数量可变；仍有对象表面遮挡和现实点云空洞 | **优先试验** |

建议输入为 `base_house_views[6] + optional_island_groups[N,4]`，数量由数据决定；训练阶段可以用 mask/slot 及可配置数量预算决定输入哪些组，**不要求完整 SG 对象数量受预算影响**。也可稍后将每组 4 图汇总成 2×2 的可视审核板，但不能未经分辨率测试就把压缩拼图的单 latent 代替四张独立编码。

## 5. 最小可视审核（NOT_RUN）

在同一个已对齐的 RoboCasa 厨房先取一个真的自由立式柜体/岛台：
1. 输出 3D d 连通组件、Wall seed 列表、Floor seed 列表，验证其因**无墙 affiliation** 被识别为岛屿，不会因 Floor 当中继而连全厨房。
2. 导出该组四张世界轴正交侧视，检查柜门/抽屉、把手、台面和周围小件是否有可辨认形状和真实 RGB/unknown；同时看原四墙是否没有它。
3. 选另一个只有单杯子的孤岛候选，确认它可以**不新增四张**且保留 SG/Top View 的存在。
4. 统计全数据候选分量个数与每 Episode 需要的视图成本、L2/L3 cache 大小；不要未确认就全量生成。
5. 若少量真实孤岛对象仍无法从彩色点云恢复可辨别的抽屉正面，先研究物体状态/几何表面质量、视图缺口与 SG 辅助，再考虑更高质量表面表示/3DGS，而不是重新设计整个 navigation map。

## 6. 结论

**当前推荐**：`House Floor + Upper + Four Wall Elevations + Sparse Island Component Orthographic Elevations`。这是对六视图的按需补齐，不是全面返回 360° 相机取景方案。最终是否用全部四向、如何控制 N、何种组件才值得出图，仍待真实样本视觉验收。
