# PSM-WMA G2 详细设计 v1.5：房间固定方位图 + Room/Island 独立四向视图资产

- 日期：2026-11-07；项目 `wxwy/psm_wma:V3`。
- **用户确定的修正**：保留房间固定世界／房间坐标 `±X, ±Y` 四方向正交立面；**孤岛图不叠加到这四张 Room/Wall View**（避免遮挡墙面内容），而是额外存储在 **`Room → Island`** 层，每个孤岛各有四张正交侧视图。**存储属性数量可以随孤岛数变化**；不得因此把孤岛图片强行塞入固定 Room 视图。
- 本稿覆盖 [v1.4「把孤岛作为前景投到四墙」](./PSM-WMA_G2_detailed_design_v1.4_2026-11-07_fixed_six_views_island_overlay.md)，恢复 [v1.3 独立孤岛视图](./PSM-WMA_G2_detailed_design_v1.3_2026-11-07_island_component_views.md) 中的分离原则，但明确物理资产层归属于 Island。承继 [v1.2 单一 3D BBox 最短欧氏距离 `d`](./PSM-WMA_G2_detailed_design_v1.2_2026-11-07_single_3d_bbox_distance.md)、[v0.8 真机 nav_sg 必须能生成全部视图](./PSM-WMA_G2_detailed_design_v0.8_2026-11-07_sim_real_renderability_contract.md)、[v0.4 离线 L2/L3 缓存](./PSM-WMA_G2_detailed_design_v0.4_2026-11-06_spatial_view_latent_cache.md)。
- 状态：存储层分离原则已确认；真实视图效果、`d=0.30m` 参数效果、对象归属及 Cosmos 读取预算仍待验证。**本轮仅文档更新，没有构建缓存／修改生产代码／启动仿真训练**。

## 1. 空间视图存储关系

```text
House / SceneTemplate
├── floor_top_view                # 房屋俯视（地板根近邻链）
├── upper_up_view                 # 房屋仰视（非地板归属 + ceiling 背景）
└── Rooms
    └── Room[room_id]
        ├── cardinal_views        # 固定房间属性，不与孤岛合成
        │   ├── +X  (朝 +X 方向正交立面)
        │   ├── -X  (朝 -X 方向正交立面)
        │   ├── +Y  (朝 +Y 方向正交立面)
        │   └── -Y  (朝 -Y 方向正交立面)
        └── Islands
            ├── Island[island_id_0]
            │   ├── object_ids / connection_component_ref / world_bbox
            │   └── views[+X, -X, +Y, -Y]   # 孤岛四张独立侧视
            └── Island[island_id_1]
                ├── object_ids / connection_component_ref / world_bbox
                └── views[+X, -X, +Y, -Y]
```

此处 `Room → Island` 是 G2 的**空间分组和视图资产层级**，不是声称原生 nav_sg C++ `SceneGraphManager` 已有 Island 节点。原生 SG Building→Room→Object 主干可先保持不变，通过 `room_id, island_id, object_ids` 的附属索引链接；未来是否引入正式 Island SG 节点需单独评估，不能为挂四张图片就重写 SG 主干。

## 2. 分组语义和投影规则

- 对象近邻图按当前唯一确定的 `distance_bbox_3d(A,B)<d`，`d=0.30m` 为试验候选；近邻链继续递归传播视图归属。**只在对象-对象之间取连通分量，Floor/Wall/Ceiling 结构根不能当连通中继**。
- 连通分量不属于任何墙根时可作为 Island group；是否给所有极小单件也建一个独立四图属性待用户与实际样本确认，不能因此删除任何 SG 实体或偷偷改动距离规则。中央岛台和其近邻抽屉/置物自然作为一个 group。
- Room 的 `±X/±Y` 立面**只含对应方向墙的几何/直接间接近邻物体**，不含 Island 前景；如果非矩形房间只有不规则墙段，仍以规范 `±X/±Y` 方向资产对齐，物理墙几何需先准确按 Room/Wall identity 分配。
- Island `±X/±Y` 立面按该组几何世界轴正交渲染，画幅覆盖该组当前 BBox 与少量固定安全边界；记录 `world_bbox, center, XY 坐标, m_per_pixel, view_axis`。避免仅因为每岛自动拉伸归一而丢掉绝对尺度或房内位置。
- 图像由同一个真实 Colored 3D Spatial Map / point surfel renderer 生成；GT 与 nav_sg 源统一、unknown/observation 版本合法；不得仅用类别和 BBox 绘示意图。
- Island membership 可随物体移动改变。Asset ID 不应每帧随机重编；首轮可按主要稳定家具/连通分量的规范 ID 建立 `island_id`，并显式记录成员变化/失效。动态归属变化需要更新对应视图的帧/版本引用。

## 3. 训练与推理：固定 Room 视图 ≠ 固定存储中 Island 数

- **完整存储**：每 Room 四张 `cardinal_views` 固定；`islands` 是 0..N 个子组，各有四个方向索引及 L2 图像/L3 frozen latent cache。
- **Cosmos 使用**：不能因为存储有 N 组就默认一次把 `4N` 张全部追加到 Policy；`Room` 的基础视图可固定读取，Island 从 Memory/Reader 依据当前任务和目标做选择或用 padded slots + mask 表示。这是**接口候选**，不等同于已经冻结某种 Agent/规则 TopK 机制，下一步与 Global Encoder 的预算一起确认。
- 训练数据沿用 G1 exact `(episode,t)` identity。Room/Island 的版本和当前对象位姿单独绑定；不需要在训练 step 中渲染/编码；离线 L2/L3 独立内容寻址去重，真机仅从 nav_sg 当前有效地图增量更新相关视图。
- 整屋 `floor_top/upper_up` 与各 Room `cardinal_views` 的组织方式可保持原方案；多房间场景不因 Island 数量变化而添加/删除固定 Room 图槽位。

## 4. 下一步最小视觉确认（NOT_RUN）

在一个有中央独立柜/岛台的场景检查 4 张 Room 立面**不叠岛台**、Island 的 4 张独立视图呈现柜门/抽屉/把手，并保存同一 Island 的世界 BBox 与 Floor Top 对齐。对无孤岛房间：`Room.Islands={}`，而 `Room.cardinal_views` 仍固定四张。验收 2 个孤岛时相同的结构仍成立，仅 `Room.Islands` 多一组属性。与真机 nav_sg 已有彩色点云相同 renderer 的生成能力作为硬约束。

**当前收敛：House floor/up + Room ±X/±Y + Room.Islands[*].±X/±Y（各自独立 L2/L3）**。存储与模型一次性输入的数量是两回事；首要设计意图是保持墙面图无遮挡的语义纯度与孤岛属性的完整性。


## 5. 2026-11-07 源码实证：Island 是虚拟分组，不是物理实体层级

**推荐最终约定**（对前文示意图作语义消歧）：

```text
SceneGraph (physical/semantic entity hierarchy):
Building
  └── Room(room_uid, spatial footprint / semantic label)
        ├── Object_A (island_id = null)
        ├── Object_B (island_id = island_01)
        ├── Object_C (island_id = island_01)
        └── Object_D (island_id = island_02)

Room spatial-view assets (derived index; NOT an additional physical SG parent):
RoomAssets[room_uid]
  ├── cardinal_views: {+X, -X, +Y, -Y}
  └── island_groups
        ├── island_01: {member_object_ids:[B,C], bbox, views:{+X,-X,+Y,-Y}}
        └── island_02: {member_object_ids:[D],   bbox, views:{+X,-X,+Y,-Y}}
```

- `Island` 不代表一个真实物体、机械装配关系或者一个新的结构 parent；它只是同一 Room 下的**空间近邻连通分组 + 独立四向图像资产索引**。实体对象仍是 `Room → Object`。
- 对象的 `island_id` 是**派生属性/关系引用**，允许为空；`RoomAssets.island_groups` 维护 members、可见性/场景版本、四向 L2 与 L3 refs，避免重复拷贝 Object。第一版无需修改 C++ `SceneGraphManager` 的 Building→Room→Object 结构。
- 岛分组由独立对象图的三维 BBox 最近距离 `distance_3d<d` 构成；**不要通过共同 Floor 根把全部家具误归一个大组件**。只有没有任何 Wall 归属的近邻组件是岛候选。
- 当前时序变化可能导致分组拆分/合并；建议保存 `island_id` 的稳定主体锚点/场景版本，并以 per-frame membership 保存变化。正式如何稳定命名仍待确认，不能假设 ObjectMap3D 的 cluster_id 绝对稳定。

## 6. 2026-11-07 源码实证：原生 Room 不要求四面物理墙

当前 nav_sg PR #4 候选源码：
- `src/room_pipeline/room_pipeline.cpp:553-574`：`setupWindow → updateGvd → updateGraph → computeSemantics → runClustering → buildRooms`。**没有**“房间必须由四面墙围住”的判据。
- 真机与仿真 `launch/params_{real,sim}/room_pipeline_params.xml` 当前都设 `source=esdf_grid`、`clustering_method=topocut`、`clustering/geometry_only=false`、`clustering/feature_projection=room_similarity`。即先从已知自由空间构图、受几何瓶颈和视觉语义证据影响，再按 TopoCut 聚类。见 `src/room_pipeline/clusterer/embedding_clusterer.cpp:21-48,86-150` 及 `src/room_pipeline/clusterer/topocut_clusterer.cpp:24-58`。
- `src/room_pipeline/room_pipeline_room.cpp:344-413` 只按 `node.cluster_id` 分组得 Room；`Room` 可有语义标签。它**可能**把开放客餐厅分成 Living Room 与 Dining Area 两个 Room，也可能因证据不足合为一个；不能声称当前算法一定切得正确，或切出来的每个 Room 都至少有三面真实墙。
- `RoomBuilder::computeHull2d`（同文件约 681-724）直接计算拓扑节点 XY **凸包**，不是实际建筑墙面，不可直接据此生成 Wall 正交图。
- `RoomBuilder::detectPortals`（约 728-800）处理**已划分 Room 之间**的跨簇边/瓶颈；当前 real/sim `room/compute_portals=false`，门信息非划分必备条件。对于完全开放的客餐厅，跨区域边界可能不存在物理门。
- `Room` 存 `uid, node_ids, center, label, boundary_hull_2d, portals`，**没有**可靠的四堵墙实例、法向、物理墙颜色几何的内置列表。因此需要单独的 wall-surface/segment 解析映射，不得把 `Room.boundary_hull_2d` 的凸包边冒充四堵墙。

**对固定 ±X/±Y 正交立面的影响**：

- 固定的是**四个方向槽位** `{+X,-X,+Y,-Y}`，并非物理世界每个 Room 都有四堵墙；
- 每个方向保留 `boundary_type = physical_wall | open_boundary | unknown`、`wall_segment_refs[]`、`view_validity` 等元数据。房间/餐厅开放的一侧可以没有真实墙面，不能为凑数创建虚构的墙颜色或壁挂物体；
- 若只允许显示墙面及其 d 近邻链，开放侧的 Room Cardinal View 可能只有空/unknown，该方向保持保留槽位和 mask。是否将开放侧用另一种“面向房间内部的方向立面”显示，属于**待确认的读出规则**，不能未经用户确认自行扩大对象集合、把 Island 叠回 Wall 图；
- 真实墙可斜向或位于同一方向的多个片段；方向槽与 `wall_segment_refs[]` 分开。与邻接 Room 共享的真实墙只存一个物理实体 ID，多 Room 的视图可引用它，不能按各 Room 随意复制不同墙；
- 建议在一个开放客餐厅样例中输出 `nav_sg room_uid/semantic label/cluster footprint` 与 `physical wall segments` 两套覆盖图，再做立面图缓存规范。**本次未运行该开放场景验证**。

以上是对现有 G2 v1.5 的模型语义与源码事实补充，不表示新 SG Island 节点或 Wall 分段已实现。