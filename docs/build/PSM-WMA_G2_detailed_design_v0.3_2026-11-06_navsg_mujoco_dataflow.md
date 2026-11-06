# PSM-WMA G2 详细设计 v0.3（工作草案）：nav_sg 原生数据流与 MuJoCo GT 替换边界

日期：2026-11-06。项目：`wxwy/psm_wma:V3` / `wxwy/nav_sg:G2`。状态：**讨论中的设计草案；不授权实现、训练、渲染、仿真或合并**。本轮依据真实服务器 `nav_sg` PR #4 代码的只读核查形成。仍以 **Full Map + MuJoCo GT Update** 为第一优先级。

## 0. 用户最新约束，覆盖 v0.1/v0.2（CONFIRMED）

- **暂时撤销“只有较大/通常固定的物体进入 SG”这一约束**。先真实表达所有适合的语义实体和空间关系，包括固定设施、抽屉部件、小物件与机器人操作对象。不要在构图阶段为 Cosmos 手工筛对象。
- **大/小物件筛选后置到 Cosmos 空间读出**（BEV、空间 token、关系上下文、任务查询等）；具体是否仅保留“大锚点”、筛选粒度与预算待独立设计。
- 历史多角度观测 RGB 图库降级为**备选调研**，不作为当前 Full-GT 数据构建和模型训练的前置条件。原始 Left 观察保留为原有观测、冷启动/未来感知链路和审计资料。
- 当前只聚焦 **nav_sg 内部数据流**，明确 MuJoCo 可以替代哪些**上游感知/状态来源**，哪些 nav_sg 构图与关系能力值得复用，以及缺少哪些真实接口；不在本轮设计 Agent、人体动态干扰或历史图库采集。
- 四种初始化状态（Full / Partial / Cold Pre-scan / Cold Zero）× 两种维护方式（MuJoCo GT / nav_sg RGB-D）仍是两条独立轴。本轮只做 Full + GT 设计。

这里的“所有实体都允许进入 SG”并不是规定必须把所有 MuJoCo Geom 建成图节点。实体与部件归属应按有意义的**物理/语义实例**映射、合并，且可用关系库保留容器内部等关系；是否表现为 SG node/part/attribute 需要统一 schema，但不按“尺寸大才允许建图”。

## 1. 已核实的原生 nav_sg 数据流（SOURCE-CONFIRMED）

路径以 `mapping_8_3/mapping/` 为根。

### 1.1 几何支路

```text
Depth/Camera Pose (or LiDAR/pose)
  -> MapROS::processMappingFrame()
  -> DepthImageProvider / LidarProvider
  -> PCL XYZ world cloud
  -> MapROS::processMappingCloud()
  -> SDFMap3D::inputPointCloud(cloud, sensor_pos)
        5cm voxel downsample + optional outlier removal
        raycast occupancy HIT/MISS from sensor_pos
  -> inflated occupancy / ESDF
  -> RoomPipeline::process()
        updateGvd() -> updateGraph() -> computeSemantics()
        -> runClustering() -> updateGraph2D() -> buildRooms()
  -> Rooms / GVD / spatial topology
```

源码：`src/map_ros.cpp:857-928,1060-1120,3094-3107`；
`src/sdf_map3d.cpp:200+`；
`src/room_pipeline/room_pipeline.cpp:553-592`。

**关键禁忌**：原生 `SDFMap3D::inputPointCloud` 按**某个传感器原点**沿每条测量光线更新 HIT/MISS。把**完整厨房所有表面点**从某个伪造 `sensor_pos` 发进去，会错误地在墙/柜体后方写入 free，且表面点不代表闭合实体内部占据。不能把完整 mesh surface PCD 当成普通单帧 RGB-D 观测送这个函数。

### 1.2 对象/语义支路

```text
RGB + Depth + Pose
  -> YOLOE detection phrase / mask + SigLIP2 embedding
  -> MapROS::buildSiglipObjectResults()
        mask-index -> world cloud + initial voxelization
  -> ObjectMap3D::integrateObservations()
        DBSCAN, matching, new hypothesis, lifecycle, voxel fusion
  -> confirmed ObjectClusters (point cloud, embedding, centroid, bbox ...)
  -> SceneGraphManager::update(rooms, ObjectClusters, RoomPipeline)
        requires confirmed, nonempty cloud
        assigns room via queryRoomAt(centroid XY)
        stores room UID, centroid, AABB, existence ...
  -> Building / Room / Object hierarchy
```

源码：`src/map_ros.cpp:1611+,1858-1969,2224-2239`；
`src/object_mapping/object_map3d.cpp:984-1055,1111-1163`；
`src/scene_graph/scene_graph_manager.cpp:60-120`。

**关键限制**：`ObjectObservation` 原生结构仅有 `cloud, has_embedding, embedding, room_uid`，无类别字符串和 GT 实例 ID；`SceneGraphObject` 也无完整语义类别或自身状态字段。现有 `getClusters/getSceneGraph` 服务以确认的、携带 embedding 的 Cluster 为核心。**不能给所有 Oracle 实例伪造相似度 embedding/用伪造 Hypothesis 碰运气以绕过限制**。

### 1.3 SG 与对象间关系不是同一模块

- C++ `SceneGraphManager` 当前主要为 Building→Room→Object 层级，以及 room 邻接/room_contains_object；不是完整的 `on/inside` 关系引擎。
- `g2/semantic/relations.py` 对 `on/inside` 另做基于**真实当前观测**支持面/开放腔体的严格推断；它需要当前 native instance 几何、真实观测边界与 label/role 支持，闭合抽屉内部不能仅凭 GT 先验通过其“observed” Gate。它属于 G2 的 Python 证据包部分，尚非 C++ SGManager 自动生成的全部关系。
- Full-GT 路线可以在 nav_sg G2 侧实现 **GT Relation Builder**，复用关系输出 schema 与时序事件存储，但**不得假装当前观察型 Python 关系推断会直接接受 Oracle 体素得到所有 `on/inside`**。
- 当前固定 Episode 实证只有 building node、无可用房间/对象间关系；不能把本次 GT 设计写成已验证的原生功能。

## 2. 推荐的 MuJoCo 替换点：双通道，避免重复识别（PROPOSED）

```text
MuJoCo model.xml + meshes + ep_meta + state[t]
                  |
            GT Scene Extractor
                  |
       +----------+-----------+
       |                      |
 Geometry Channel        Instance/State Channel
       |                      |
collision/visual geometry  persistent semantic instance_id
solid occupancy/free       category / owner / body/geom/part
surface samples optional   T_world_instance / articulation
       |                   state delta / timestamp / provenance
       v                      v
   nav_sg GT Map Adapter    nav_sg GT Object Adapter
       |                      |
Occupancy + ESDF/GVD     Object/Part State (Known/Confirmed)
       |                      |
       +---------+------------+
                 v
        nav_sg SG Builder
     Room/Spatial topology + object hierarchy
                 |
          GT Relation Builder
     on/inside/contains/adjacent/part_of ...
                 |
     Temporal SG + Relation Event Store
                 |
       Cosmos readout (BEV/context)
       [entity selection happens HERE]
```

**建议的责任划分**

| 模块 | MuJoCo 已经能提供 | nav_sg 保留/新增 |
|---|---|---|
| 几何资产 | MJCF mesh/box/cylinder、各 geom 世界变换、物理结构 | GT 体素/占据导入到 nav_sg，后续 ESDF/GVD/空间拓扑；按需导出 PCD |
| 实例/类别 | fixture 对象类别与原始 object 类别、body/geom 所属，稳定 source IDs | GT Object Adapter -> nav_sg 规范实例 ID、类目、部件、几何/状态 |
| 对象前端 | Oracle 已知物体，不需要检测/DBSCAN/相似度归并 | **跳过** YOLOE、SigLIP2、ObjectMap3D 的感知预处理/track/Hypothesis；保留未来感知路径 |
| Room/Graph | 场景完整几何，部分 metadata 布局信息 | 优先复用 RoomPipeline/SGManager；单厨房可用明确的 Kitchen/Room anchor 兜底并记录来源 |
| 关系 | 实例、容器形状、joint state、位姿、接触/几何可计算的来源 | nav_sg G2 内构造 GT relation evidence -> 同一 Relation Store、状态版本与导出 schema |
| 动态 | MuJoCo 逐帧 GT qpos/关节/位姿 | 稀疏状态增量 + 受影响实体与关系局部重算、版本索引 |
| Cosmos 输入 | 不从 MuJoCo 直接给政策答案/未来状态 | nav_sg 时间 t 的空间状态/关系读出；后续选择/压缩大/小实体 |

**不要用颜色作为语义权威**。彩色点云可作为可视化产物，主接口需显式 `instance_id`, `class`, `part`, `provenance`；一个物体可能由多个 visual/collision geoms 构成，一个关节也不应被当成独立语义物体。对 Object 的“固定/动态/非刚体”分类需要按 Body/Joint 与运行状态处理。

## 3. 点云还是体素：建议分工，而不是二选一

**Authoritative Source**：MuJoCo 完整几何（mesh/primitives）、稳定身份、关节状态、物体位姿。GT 语义实例表是单独的数据，不嵌在 `xyzrgb` 点里。

- **供 Occupancy/ESDF/GVD**：体素占据/空闲栅格更契合 nav_sg 的空间建图。GT voxelization 要区分 surface/solid/free/unknown，关注薄板、开口、抽屉腔体、collision vs visual geometry 的偏差。GVD 房间构建需要正确的 free/occupied，不是只有 surface hits。
- **供对象节点几何与几何关系**：保留每实例 Mesh/Primitive + 变换，可选采样对象级点云/PCL 和 AABB/OBB。对象点云不应作为唯一真值；内部 `inside` 与接触支撑 `on` 应基于几何体体积、容器腔体、关节状态和必要接触判据综合计算，不只根据质心或 bbox。
- **供 nav_sg RViz 现有可视化**：可以由 GT 实例点云生成按 Object ID 分色的显示数据，但该图像是导出产物，不应反向决定 Object 的语义 ID。
- **供动态高效存储**：static geometry 存一次；动态部分存 `object_id -> T_world/JointState`。按需重算移动部件的 voxel 切片；稳定期间复用版本。不能用把所有动态物体变动压成每帧完整厨房 voxel copy。

## 4. GT Relation Builder 的最小判据（PROPOSED，待核验）

- `part_of`、`attached_to`：来自已核实的 Body/Geom/Fixture 归属；不能只依字符串前缀猜。
- `on(object,surface)`：物体支撑接触/近接、法向/高度、XY 支撑域覆盖、稳定性等，避免只是 AABB 靠近就判 `on`。
- `inside(object,container)`：使用容器实际内腔/开口、物体几何占比、关节状态；关闭抽屉中的物体可在 Full-GT 下得知，不能强迫通过仅观察型的“当前四面边界可见”Gate。
- `adjacent/left_of` 等按所需语义定义参考坐标系与尺度；不是当前最小范围必须生成全部关系。
- 内部包含关系可以只存在 Relation Store 而非 SG 图可视边；SG/Relation/State 共享稳定 ID、事件时间、provenance，避免离散图与时序关系不一致。
- `GT` 与 `Observed` 是两种**证据来源和可信边界**；不要把 Oracle 的内部可知关系当作 nav_sg 感知效果。

## 5. 最小导入 Schema 草案（PROPOSED）

```text
SceneFrameGT:
    scene_identity, episode_id, frame_index, timestamp
    coordinate_system=world, asset_manifest_hash, state_hash
    objects[
        instance_id, class_id/name, fixture_or_object_ref,
        geom_ids[], body_ids[], parts[], T_world_instance,
        bbox / geometry_ref, articulation,
        active, provenance="mujoco_gt"
    ]
    spatial_map_ref: occupied/free/unknown + grid origin,resolution,bounds
    deltas_since_previous: changed_instances[] / changed_joints[]
```

建议导入结果标准化到 nav_sg 共用的 `SceneEntity/SceneState/RelationEvent` ABI，不把 GT 标签写进感知型 SigLIP embedding；未来 Cold Start 由 YOLOE/Depth/ObjectMap3D 输出相同逻辑层 ID/状态，**两个 backend 在“规范场景实体/状态”层汇合**。

单厨房导入应显式保留合法 room ID。当前 RoomPipeline 从少量视角的 free/occupied 构建常未形成房间，GT 完整占据可改善输入，但不保证 GVD 自动给出 Kitchen；允许基于明确 metadata 的室内区域作为 GT fallback，别以“room=0 个”阻塞整个 SG。

## 6. 时序数据流与验收（PROPOSED，尚未执行）

先单 Episode（已有校验的 global 5077/local 36），检查：

1. 用既有官方状态恢复，`model.xml.gz + ep_meta + states[0]` 建立完备实例目录；标注所有 geom→实例/部件映射和类别来源。不要以 task instruction 或未来动作确定关系。
2. S0 生成 GT 占据/空闲地图；对比渲染 RGB-D 的可见表面、实体实例/几何与 SDFMap3D/RoomPipeline 结果，检查内腔/薄壁以及物体与机器人排除策略。
3. 输出 nav_sg 可读取的 GT 实例列表；验证可以在**不运行 YOLOE、SigLIP2、DBSCAN 和 tracker** 的情况下构建带类别与几何的 SG；检查每个实例的稳定 ID、Room 归属，不强制 `has_embedding=true`。
4. 核对初始 `on/inside` 关系，确保抽屉/工具等物体和 Fixture 部件引用正确，且没有未根据几何证据的关系。
5. 顺序恢复轨迹逐帧状态：物体/抽屉移动时产生 sparse delta 与 relation events，非机器人状态不变时帧复用稳定版本；不保存全厨房全量 voxel/完整 SG 快照。
6. 渲染与数据用于验收，不给 Cosmos 另建专门历史图像库。任务时刻 t 的空间状态不读取 t+1 及之后的源。
7. 仍保留正常 nav_sg RGB-D 冷启动路径用于后续 GT vs Perception 对照，验收结果必须注明 `source=mujoco_gt`。

**本稿不是生产实现**；所有 S0/GT map 生成、native GT adapter、GT relations、时序 Gates 均为 NOT_RUN。最小工程切入建议优先基于已存在的 `SDFMap3D`、`RoomPipeline`、`SceneGraphManager` 及 G2 Python 关系模块做小适配，不重新设计 Cosmos 主干或构建第二套并行 SG。

## 7. 与旧材料的明确覆盖

本稿覆盖 v0.2 中“大小和稳定性决定 SG 入图资格、以及只有大实体才有 SG 节点”的表达；覆盖 v0.1/v0.2 中历史 RGB 是当前 G2 训练必需来源的假设。**历史视觉研究保留为备选**，在 [历史视觉 OPTIONAL 调研](./PSM-WMA_G2_historical_visual_memory_OPTIONAL_survey_v1.0_2026-11-06.md) 中独立维护。

下一步集中讨论两件相连的接口设计：**GT Occupancy/Free 导入方式**和**GT Instance/State 导入方式**。不要跳过这两个接口直接讨论 Cosmos 历史视角选图。


## 8. 跨 Episode 的静态场景图复用（PROPOSED；2026-11-06 补充）

**结论：每条 Episode 需要独立的初始状态、关系与时序增量记录，但不需要独立重复存储整份静态 SG。** 共享须按严格场景静态身份判定，不可仅凭任务名或 layout/style ID 决定。

共享模板 SceneTemplate(scene_template_id) 包含：
- 静态几何和资产、Room/Space、Fixture 实例 ID、类别、固定位置、部件结构、静态拓扑。
- 跨 Episode 可共享的固定几何缓存、GT 占据/空闲基图、RoomPipeline 静态空间结构。
- 不包含特定 Episode 的可移动物体位置、抽屉开度、目标物、机器人姿态或变化后的关系。

Episode(eid) 独立保存：
- scene_template_id 引用共享模板；
- InitialState S0：当前 Episode 的可移动物件、放置关系、门/抽屉关节状态以及完整当前空间知识（Full-GT）；
- Delta[t]：仅变化物体的 Pose、Joint 和关系 Event；
- FrameIndex[t]：以模板 + S0 + 截至 t 的 Delta 重建当前逻辑 SG 和关系状态。
- Cosmos 时刻 t 的空间输入按需从逻辑 SG_t/Relation_t/State_t 读出。即使内部接口要求完整快照，也只需按需在内存物化，不必每 Episode 在磁盘复制全图。

**共享判据和边界**

1. scene_template_id 建议基于归一化的静态场景指纹（Fixture/Asset 身份、几何、固定 Pose、关节/部件拓扑、Room 结构和需要一致的材质/资产版本）。layout_id 和 style_id 只能作候选分组，不能替代静态等价核验。
2. 完整 MJCF 的文件 hash 不是理想的模板键，因为包含机器人和可移动目标物等 Episode 差异；同一个模板可引用多个 MJCF 变体。相同 Mesh 资产可以跨不同模板进一步复用。
3. 区分固定 template_instance_id 与 episode_instance_id，建立显式映射；不要把 ObjectMap3D 的逐次聚类 ID 当成跨 Episode 不变的 GT ID。
4. 关系也分为静态结构关系和 Episode 动态关系；inside/on 等必须按该 Episode 初始状态和更新计算，不把一个 Episode 结尾状态自动传给另一个独立 Episode。
5. 几何占据需要区分静态模板与动态物体 overlay，更新移动物体时不能保留旧位置的幽灵占据。
6. 只有数据明确表示多个 Episode 为同一世界连续运行且没有重置，才能跨 Episode 继承动态状态。当前 RoboCasa365 独立示教不可默认如此。

**真实数据抽查（只读，尚非完整等价 Gate）**：

在当前服务器 PickPlaceDrawerToCounter/20250820 目录：
- 原始 local episode_000033、episode_000034、episode_000037 的 layout_id=4、style_id=4、Fixture 数都是 79，按 fixture_name→(cls,pos,rot) 计算的 SHA256 摘要前缀均为 f059669ff0919596；但操作目标类别、干扰物体不同，完整 MJCF 内容也不同。
- episode_000036 的 layout_id=1、style_id=1、49 个 Fixture，摘要 c114632585f4f421，与上述不是同一已发现布局候选。
- 以上仅证明模板复用的实际候选存在；尚未比较所有 Mesh/Geom/Material/Joint 和关节初始状态，不能直接宣布可以共享。

本节仅记录设计建议与只读局部检查；没有执行地图缓存构建、静态全量等价验收、训练和仿真。


## 9. 本次证据范围

原生源码及真实运行查验：`wxwy/nav_sg` 独立 PR #4 服务器候选目录 `mapping_8_3/mapping`、`g2/semantic/relations.py`，2026-11-06。路径可追溯；非当前生产分支原地修改。

- SDFMap3D `inputPointCloud`：`src/sdf_map3d.cpp:200+`；
- RoomPipeline `process`：`src/room_pipeline/room_pipeline.cpp:553-592`；
- ObjectMap3D `integrateObservations`：`src/object_mapping/object_map3d.cpp:984-1055`；
- SceneGraphManager `update`：`src/scene_graph/scene_graph_manager.cpp:60-120`；
- G2 observed relation gates：`g2/semantic/relations.py:319+,387+,507+`；
- Scene export：`src/room_pipeline/room_pipeline_export_scene_graph.cpp`。

以上证明原生代码接口和 GT 的缺口，**不等于已完成 GT API 或 GT 关系引擎**。
