# PSM-WMA G2 详细设计 v0.6：分层正交空间 BEV + 房间锚点多方向视图（讨论方案）

- 日期：2026-11-06；项目：`wxwy/psm_wma:V3`。
- 性质：**Owner 提议与文献对照后的讨论稿**；用户提出的候选方案不等于已冻结的最终选型；不授权生产代码修改、渲染、训练或评测。
- 上位继承：[v0.3 原生 nav_sg/MuJoCo 数据流](./PSM-WMA_G2_detailed_design_v0.3_2026-11-06_navsg_mujoco_dataflow.md)、[v0.4 预计算 L2/L3 空间缓存](./PSM-WMA_G2_detailed_design_v0.4_2026-11-06_spatial_view_latent_cache.md)。
- **取代 v0.5 的过强推断**：BEV 不必以“纹理写实照片”为第一目标。它的首要任务是 metric 位置、可通行区域与机器人/目标相对姿态；仍必须从真实 3D 地图/占据/几何通过物理投影生成，**不允许只从名称、质心、BBox 画示意图**。真实外观与侧面几何由房间方向 RGB 视图补足。保留 v0.5 可渲染场景资产、几何/实例对齐及缓存契约，不再强制 BEV photorealistic 作为唯一形式。
- 历史真实 Left 观察图库仍是 OPTIONAL，与固定房间锚点的合成 reference views 不同。

## 1. 研究目标与两类互补读出

```text
nav_sg Canonical 3D Spatial World (GT or eventual perceived)
 |--- true geometry/occupancy and real free space
 |--- object instance/part pose, relations, scene version
 |
 |--- Map readout: metric + navigability (primary)
 |     -> downward orthographic projected geometry below split height
 |     -> 2D traversability / robot-clearance map (independent channel)
 |     -> optional upward/upper-layer orthographic geometry above height
 |     -> aligned visual/height/instance channels -> L2 -> frozen L3 cache
 |
 |--- Room visual readout: room-centric viewpoint attributes
       -> free-space anchor at nominal robot-Left height
       -> yaw ∈ {0°, r°, ..., 360°-r°}
       -> Left-like camera intrinsic/FOV/resolution/pitch convention
       -> independent RGB view frames (not temporal sequence)
       -> room: [anchor, yaw, pose, state, camera config, RGB/L3]
                 ↓
         Trainable Global Spatial Reader -> Cosmos Action Path
```

1. 主 BEV 面向 XY 空间、相对位置和移动路径，不为“好看”的 3D 透视牺牲度量一致性。
2. 房间多方向视图面向真实表面、外观、开口、立面、局部上下层线索，不直接作为可通行性判据。
3. SG 的全部实体保留，筛哪些信息送给 Cosmos 属于 view/readout 设计，不在 nav_sg 构图时按大小丢掉实体。

## 2. 用户提出的 BEV 方案对比（USER-PROPOSED + ANALYSIS）

### A. 以 robot Left 参考高度 h_split 进行下视／上视的正交投影

- **下视**：对 `z<=h_split` 的几何裁剪、再沿 `-Z` 正交投影。仅把相机放到这个高度而**不做高度裁剪**不能排除高于相机的几何干扰；裁剪应绑定显式规则。
- **上视**：对 `z>=h_split` 的几何裁剪、沿 `+Z` 正交投影。它自然看到高处物体的下侧，并非无歧义地显示柜顶物体/内部，仍可能受天花板或高层遮挡；按需去 ceiling 并记录策略。
- **正交投影并不消除同一 XY 上的几何遮挡**；它只是确保 XY 比例一致。至少保持可选 height/depth/instance 通道，以及必要的上/下范围信息，不能只存两张 RGB 就认为 3D 关系完整。
- 机器人左相机高度是一个有意义的候选分层平面，但不是全环境的普适障碍阈值。物体从上层向下垂挂、底盘通过但机械臂碰撞等，需要分开建模。

### B. 顶部斜视／广角透视

- **Perspective projection** 可展示房间远处墙体/设施侧面，但不自动穿透不透明物体；同一位移在不同深度对应不同像素尺度，会削弱位置关系的稳定表达。
- 若所谓“透视”指 X-ray/半透明对象或移除遮挡，则属于**额外绘图模式**，不是透视投影的自然结果。可标注为单独 `render_policy`，但不应作为主 metric 导航 BEV。
- 推荐最多作为人工审阅/额外补充，不作为第一版主地图 latent。

### C. 建议的最小主 BEV 选择（PROPOSED）

优先 `world-aligned orthographic XY base map`，配 **base traversability/costmap channel**，可选 geometry/height/semantics/instance layers。上层正交图只在首个样本证明能补充高柜、吊柜、悬挂物、层板等信息后启用，**不先把所有视图硬编码成必选三视图**。

*可通行性是几何碰撞性质，不是从 RGB 颜色推断。* 由三维 free/occupied + 底盘 footprint、必要的整机垂向/扫掠占据、安全余量等计算。最低限度分开：
- `base_traversability`：当前固定底盘/观察姿态能安全移动区域；
- `upper_obstacle / clearance`：高于一般底盘、但可能影响整机通过或操作的障碍层；
- `unknown`：未来 perception/Cold 的未观测区域，不能渲染成真实空闲区。
“投影地面空白”不能自动被视为可以通行，也不能把悬空家具投影成整列永久不可通行。

底盘姿态/位置单独作为 `(x,y,z,sin(yaw),cos(yaw))` 等状态条件，地图固定在世界/房间坐标，可缓存复用；若后续要求直接 overlay robot marker，单独生成轻量 overlay/读出，不令静止地图因每帧机器人运动而重算 frozen BEV latent。

## 3. 房间中心 360° 方向图：参数化、可下采样（USER-PROPOSED）

- 对每个 `room_id` 选 `anchor_pose`，高度尽量匹配原 `robot0_agentview_left`；朝向 `yaw_k=yaw_0+k*r`，`k=0,...,360/r-1`。要求 r 能整除 360 或明确定义余数/不均匀角度问题；先用 45° = 8 张作为候选源。
- **0° 应绑定稳定且可复现的房间坐标框架**：优先以主要墙面/建筑长边定义室内正交轴，`yaw_0=room_frame +X`；记录 `T_world_room` 及与全局 world +X 的夹角，180° 对称的符号由确定性规则（如更接近 world +X）消歧。房间不规则/斜墙时可直接使用严格定义的全局坐标轴，不能在同一数据集随 Episode 自由漂移。
- **45° 完整 8 图**：角度 0,45,90,135,180,225,270,315；**90° 稀疏 4 图**：固定索引 0,2,4,6，不重渲染也不重编码。适当的 mask + yaw embedding 保持两个训练配置的方向身份一致。
- 图像可与 Left 保持相同 K/FOV、尺寸、畸变预处理及安装倾斜 convention；但注意“同参数”不等于“同拍摄来源”。
- **关键几何细节**：若真正让整台机器人原地转向，Left 相机常有相对底盘的非零水平偏置，旋转时相机**光心并不固定在房间几何中心**，所以 8 图不是严格单光心全景。图像可作为 8 个带独立相机 Pose 的 room view attributes；不能直接宣称能无缝拼接成同一光心 panorama。
- 如果只要真正固定中心的 Room Canonical Views，可以用与 Left 内参/高度一致的**虚拟相机**从固定中心旋转；但其来源必须是 `synthetic_room_canonical`，不应标成“机器人实际 Left 观察”；该虚拟视图可不包含机械臂。若严格要求由真实机器人 Left 拍摄，则按机器人可达配置/碰撞/旋转时机械臂遮挡拍摄，保留机器人，自然产生不严格共光心的视图。**两者如何选定仍 OPEN**。
- Room 的几何中心/所有点平均值未必处于可通行自由空间，也不一定能放下整个机器人。采集锚点建议从 room free-space/ESDF 中挑选可达、净空较好且近中间的点，不允许默认质心合法。L 形/狭长房间可能需要第二锚点，但首轮先一锚点并记录观察覆盖缺口。
- 使用原 Left 安装 pitch/相机光轴时，yaw 扫描只改变朝向，不保证水平 360° 扫描覆盖所有高度；不在首轮自动加俯仰网格。若高/低物体长期缺失，再显式增加可配置 pitch/elevation 视角。
- Room 视图建议绑定 `(scene_version, room_id, anchor_id, yaw_idx, r, camera_recipe, provenance)`。这是按房间组织的**规范化空间快照**，不同于传统“机器人过去某次走过拍下的历史照片”。
- 实际物体移动可能改变某些房间视角里的 RGB；固定视角不意味所有帧复用同一张静态图片。根据可见覆盖和状态版本局部更新各个受影响 view 的 L2/L3 缓存，或先用准确的 scene-state change 判定。

## 4. 文献/开源实践对照（2026-11-06 搜索）

1. **HOV-SG（RSS 2024）**：从 3D 点云构造楼层 BEV histogram，做房间区域分割；同时用 RGB-D observation 在房间层积累多个代表视图的 CLIP embedding。它支持**度量 BEV 和 room-view 特征分开组织**，但不是我们这种“固定房间中心每 45° 一张”的直接复现。论文/项目：https://hovsg.github.io/ ；https://arxiv.org/abs/2403.17846 。
2. **Nav2 Voxel Layer / Traversability**：维护 3D voxel occupancy 并投影到 2D costmap；区分障碍高度并结合机器人 footprint/inflation。证明可通行层应由三维几何的碰撞读出，而非从高保真俯视 RGB 直接估计。官方文档：https://ros-navigation.github.io/mkdocs.nav2.org/jazzy/configuration_and_development/configuration_guide/core_servers/costmap_plugins/voxel/ 。
3. **Matterport3D Simulator / R2R VLN**：在可导航 viewpoint 上进行 heading/elevation 离散采样，经典配置为 12 个 30° heading × 3 个 elevation = 36 个 single-view images；项目还提供过预计算的 ResNet view features。它支持**多方向 RGB + heading identity + 预编码 cache** 的工程可行性，但不意味着 8 图足够，也不表示这些视角总在房间中心。官方代码：https://github.com/peteanderson80/Matterport3DSimulator 。
4. **3D-Mem（CVPR 2025）**：保存少量 co-visible 的 Memory Snapshots，辅助探索/推理，说明多图补充几何关系的价值；它属于历史观察记忆而非固定房间中心规范图，不可混为同一个已验证方法。论文：https://openaccess.thecvf.com/content/CVPR2025/html/Yang_3D-Mem_3D_Scene_Memory_for_Embodied_Exploration_and_Reasoning_CVPR_2025_paper.html 。

这几项共同支持的不是某个精确角度或 BEV 高度配置，而是三种表征各负其责：**2D/2.5D 地图用于 metric 与行走；室内 RGB 多方向视图提供外观与立面；SG/Relation Store 提供身份、层级和包含事实。**

## 5. Cosmos & Cache 的共用接口（仍为 PROPOSED）

与 v0.4/v0.5 的 L2 原始图像 + L3 冻结编码器 latent + trainable Global Spatial Reader 一致。第一版候选：

```text
GlobalSpatialSample(episode, t):
    bev_lower_latent_ref
    traversability_map_latent_or_channel_ref
    bev_upper_latent_ref_optional
    room_views[(room_id, anchor_id, yaw_idx, image/latent_ref)]  # 8 or 4 via subset
    room_view_mask, camera_recipe, yaw_sin_cos, T_world_room, T_world_anchor
    robot_state_current, relevant_relations_at_t
```

- 只渲染和编码**实际决定启用**的视图。首轮可在一个 Episode 为 A/B 方案生成小样本供人眼检查；方案冻结后再批量生成全训练集，不要一口气建所有候选的大规模 latent cache。
- 对于 45° 先缓存 8 张，模型训练可选择 4/8 子集，不需要额外生成第二套 90° 图片；不同 `r` 或 view order 属于明确的实验 recipe。
- 固定世界/房间 BEV、room anchor 视角有利于跨稳定状态复用；房间视图仍要随物品变化更新，不能只有 S0 的图而漏掉后续变化。
- Frozen image encoder 的输入必须带 view type、方向/参考坐标元数据；多视图**不是时间连续视频**。不得把 8 张 yaw 图串成 G1 17-frame VAE 视频序列，改变 Local/Policy 视频监督定义。
- 原有 G1 cache-first corpus authority、Exact source frame t、current observation 和 raw action target 不改变；新增 L2/L3 按 (episode, t, view) 严格绑定，不用未来 GT 轨迹给当前 policy condition。
- 仿真 SR 评测实际 rollout 时从当前地图生成对应视图；不得按帧读取专家示教的未来 S0/Delta cache。在线缓存与离线训练不同，这个成本须单独验收。

## 6. 当前推荐与 OPEN 项

**推荐的第一优先尝试**：一张**真实三维几何投影的 world/room-fixed 下层 BEV**，配一张**独立计算的 traversability map/channel**；上层 orthographic 视图作为信息缺失时的可选补充。每房间一个 valid anchor、45° 采样 8 张 Left-like 方向 RGB，训练子集 4/8；房间与 world 轴绑定并记录 Pose。小样本视觉审查之后，再决定是否全量生成并缓存。

当前 OPEN：
1. 上下两张分层正交图是否确有独立增益；图像 height split 高度是否选 Left 高度还是机器人结构高度。
2. 房间方向图究竟要求**真实整机 Left** 还是**左相机内参/高度匹配的固定中心合成相机**；此处关系到机械臂遮挡、能否严格同光心和冷启动可迁移性。
3. 非规则房间如何定义稳定 room frame/anchor；8 图可见覆盖是否足够。
4. 在 BEV 的可通行表达中如何区分 base-passable、whole-robot-feasible、unknown，及机器人姿态单独编码方式。
5. 三维渲染 recipe、分辨率、图层、frozen encoder 及 Global Adapter 的模型 ABI。

此稿没有执行新的生产代码、仿真渲染或模型训练；属于对用户候选进行技术判断和外部方法对照，不把建议写成已确认冻结项。
