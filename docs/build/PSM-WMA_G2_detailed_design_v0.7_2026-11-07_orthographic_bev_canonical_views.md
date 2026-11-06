# PSM-WMA G2 详细设计 v0.7（讨论稿）：上下正交 BEV 与自适应房间规范视角

- 日期：2026-11-07（北京时间，承接 2026-11-06 讨论）；主仓 `wxwy/psm_wma:V3`。
- 状态：**用户澄清约束 + 尚待确认的实现建议**，并非 frozen 选型；本轮仅更新文档和讨论，不运行仿真/渲染、cache builder 或训练。
- 继承：[G2 v0.3 nav_sg/MuJoCo 数据流](./PSM-WMA_G2_detailed_design_v0.3_2026-11-06_navsg_mujoco_dataflow.md)、[v0.4 L2/L3 cache](./PSM-WMA_G2_detailed_design_v0.4_2026-11-06_spatial_view_latent_cache.md)；**本稿在相冲突的视图选择/通行标签/相机设置上覆盖 [v0.6](./PSM-WMA_G2_detailed_design_v0.6_2026-11-06_layered_bev_room_directional_views.md)**。
- 当前优先实验仍为 **Full Map + MuJoCo GT Update**。SG 不按“大物件”预先筛节点；空间视图输入不等于过去的机器人 Left 历史相册（后者另作为 OPTIONAL）。

## 1. 用户澄清与本轮正式约束

1. **高位透视备选**是真正的 perspective projection，采用与房间/整个屋子绑定的固定相机位姿，不随机器人移动；并非透明/X-ray。不作为本轮首选，但继续保留可对比选项。普通透视仍存在视线遮挡且在不同深度的像素尺度不同。
2. **优先上下平行/正交空间视图**：以机器人 Left 光学安装高度作为切分高度的候选，对上、下三维几何做可核验的投影，主要为 XY 相对位置与真实空间布局服务。
3. **不额外维护 Costmap/Traversability Map 或手工导航可行性标签**。只维护准确的房屋格局、墙壁/物品真实几何、状态和高度，是否能通过以及如何通过交给模型学习。下文选择虚拟相机位置用到的局部自由空间检测是**离线取景校验**，不是持久化导航成本图或规划路径输出。
4. **房间方向图为规范虚拟相机**。借鉴 Left 的只是**高度**；并未要求使用 Left 的安装偏移、内参、FOV、俯仰角、图像尺寸，也不要求实际机器人执行转向或相机中存在机械臂。方向视图标记 `synthetic_room_view`，不是 `robot0_agentview_left` 录制图。
5. **方位与采样密度可调**：0° 绑定稳定房间/世界绝对参考轴并与墙体正交轴对齐；间隔 r 可配置。45° 的八张可按固定子集抽成 90° 四张，但单锚点、单俯仰、45° 不保证覆盖狭长空间、近距离设施和上下层对象；视角覆盖需实测并可补视角。
6. 所有最终选用的 BEV、上下层图、房间方向 RGB 均离线产生 L2 图像 + L3 冻结编码器 latent cache，按 scene-state/view/content 复用；Cosmos 训练不运行 MuJoCo、nav_sg 或 renderer。

## 2. 主 BEV：几何驱动的上下正交投影（PROPOSED）

```text
nav_sg canonical geometry / MuJoCo GT visual/collision geometry
                 │ 统一 world XY、实例/部件、时间状态
                 ├── z < h_split：真实几何裁剪 -> -Z orthographic -> LowerMap
                 └── z >= h_split：真实几何裁剪 -> +Z orthographic -> UpperMap
                  (same XY extents, axes, pixel scale; independent depth/height)
                 ↓
             2D spatial view L2 RGB + aligned geometry/depth/instance
                 ↓
             Frozen Spatial Encoder -> L3 cache
```

- 不是把 Object 名称、bbox、质心手工画成示意图；投影依据真实 mesh/primitive/occupancy。可选择纹理表面、实例颜色或高度等固定 render policy，**主定位功能优先于照片级画质**。
- **h_split 是视图切片参数而不是通行高度判断阈值**。Left 高度只是一个起始候选；若切开工作台/柜门造成难以理解的截断，采用多高度候选或分层表征后再冻结。
- Lower/Upper 每个像素仅能直接看到沿该投影方向的最近表面；正交本身不能消除同一 XY 的遮挡。Upper 看见的可能是柜子底部，不等价于“把高层物体从上往下看”；需保留 depth/height 和可选分层 mask 以防误解。
- 天花板/屋顶是否剔除、墙是否剖切，必须标为显式 renderer policy，不能静默隐藏与实体识别有关的信息。
- 本 Full-GT 条件下可以区分真实地面、物体占据、上方悬空结构和空隙，但**不需要把空白区域强制编码为 passable/impassable 标签**。没有水平投影中的占据不等于能通过；模型根据几何与本体状态学运动约束。
- 地图世界/房间坐标固定，不跟随机器人移动旋转；机器人 pose/yaw 在 state/Global 输入独立表示，避免静止环境每帧重渲染。
- **待验证**：参考高度的上下图是否足以同时表达柜体高低层、桌下空间、地面入口，以及关键 inside/stacked 关系；不能用两张 RGB 取代 Relation Store。

## 3. 房间规范虚拟相机：候选锚点的选择机制（PROPOSED）

**先按房间定义固定参考系，再自动选择取景锚点，不硬用几何中心。**

现有 nav_sg `Room` 包含 `center` 和 `boundary_hull_2d`，RoomBuilder 也维护 room voxel/2D labels；它们可作为候选区域和初始化中心线索，但不是合法相机位置的充分证明。Full-GT 中必要时可用完整几何/房间结构辅助界定空间。Source（只读）：
- `mapping_8_3/mapping/include/mapping/room_pipeline/room_pipeline_room.h:40-59`
- `mapping_8_3/mapping/src/room_pipeline/room_pipeline_room.cpp:350+`。

**给定一个 Room 的自动候选流程**：

1. 获取 room 的二维空间范围/地板、静态几何和 `h_camera`（参考 Left 光心高度），在靠近几何中心的区域采样有限候选 `(x,y)`。在被工作台占据的质心处不能直接生成相机。
2. 在完整三维几何中检查相机光心及其必要近裁剪包络不与墙、柜体、障碍实体相交，且位于 room 内有效空域。虚拟相机不要求有真实机器人底盘、转身轨迹或机械臂碰撞；该几何检查**不等于新建导航 Costmap**。
3. 对每个合法候选，低分辨率渲染一组 `yaw`/可选 `pitch` 的 Depth/GT-instance mask，计算真实可见几何/实例/区域覆盖率、图像截断与重复量。**覆盖量不必全由照片 RGB 像素主观打分**；场景来源与几何实例已知，计算可自动化。
4. 选择一个靠近中心且能覆盖较多互补区域的主锚点；不要简单取“离障碍最远”的点（那可能在角落，也不要单纯最大化中心度而忽略遮挡）。
5. 若单锚点的覆盖不足，再比较：加宽 FOV、补 yaw 细分、补上下 pitch、增加第二锚点；每次增加都要显示实际新增内容/像素质量和资源成本。复杂房间可有第二锚点，但首轮先评估必要性。
6. Anchor、Room frame、camera config 与选择理由应在 SceneTemplate 下稳定缓存，跨拥有相同静态模板的 Episode 尽量复用；动态物体改变后应按当前状态更新对应视图内容，不能误复用旧版本。

建议用可解释的确定性覆盖评分：
`score = coverage_of_visible_region + diverse_geometry_views - truncation - severe_occlusion - redundancy - centrality_penalty`。
权重、采样间距和评价阈值留待单场景实际审阅后确定，不提前变成黑箱视角规划器。对物体分组计算覆盖时不能把“封闭柜内本不可见的内部表面”当作单视点应该拍到的目标；覆盖不足需区分几何不可见与图像质量差。

## 4. 房间方向图：r、FOV、pitch 解耦（PROPOSED）

- 初始化的标准角度示例 `r=45°`，yaw=0,45,90,135,180,225,270,315；`r=90°` 的四图为索引 0,2,4,6，使用同一 `0°` 和相机 recipe。0° 建议与房间主要墙面轴平行，且记录 `T_world_room`；如无法稳定定义 room frame，则明确统一采用 world +X，不允许同一模板随 Episode 随机漂移。
- **只参考 Left 的高度**，虚拟相机的 FOV、相机 pitch、分辨率都可独立选择并保存为 `camera_recipe`。默认不能声称“和 Left 同 K/FOV/安装姿态”。
- **yaw 间隔与水平 FOV 的关系**：如果 FOV_h<r，同一光心方向扫描必有角度空隙；即使 FOV_h>=r，近处大物件的截断、严重遮挡也可能让图不可用。因此角度覆盖条件仅是底线，不能代替实际几何可见性测试。
- **上下覆盖是另一维度**。在固定 yaw 的相机俯仰偏低时，可能遗漏高柜/吊柜；相机俯仰偏高时可能遗漏地面/抽屉低层。不要靠减少 yaw 间隔解决高度缺口。候选：一个中性 pitch + 少量向上/向下 pitch，只在实际需要时增加。
- **FOV 并非越大越好**：过宽可能令小物件只有极少像素、畸变/尺度变化明显。先通过 Depth/Mask 缺口检查判断“是缺角度、缺俯仰，还是空间锚点被遮挡”，再选择加 yaw、pitch、FOV 或第二锚点。
- 相机可在中心处静止旋转，所有方向严格共光心（只改变 yaw/pitch）。输出是规范房间视觉属性，不能称为机器人 Left 历史观察，也不必保留机械臂。
- 如训练侧只消费 4/8 views，不能删掉不同 view 的角度/pose 身份；每张图保存 `room_id,anchor_id,yaw,pitch,FOV,camera_pose,scene_version,view_recipe_hash`，由 mask 在固定顺序中区分缺失。

## 5. 缓存策略与闭环边界（继承 v0.4）

```text
SceneTemplate + Episode S0 + GT scene_version(t)
    -> spatial projection lower/upper, room camera renders (L2)
    -> frozen vision encoder per unique image/view recipe (L3)
    -> (episode,t,room/view) -> latent reference
    -> Global Spatial Reader + Cosmos
```

- 在离线建立参考视图时可做**低分辨率几何候选评估**，只对确认进入最终候选库的 yaw/pitch/anchor 进行正式分辨率 L2 渲染与 frozen L3 编码；无需把每张被淘汰候选都编码并存储。
- 第一轮按 45° 产生 8 个规范基础槽。若要更密集数据，可单独定义 `r=22.5°` 候选库，90°/45° 模式可由整除索引子集得到；实际保存的视图、显存/磁盘/CPU 开销需量化。
- 下/上视图可能不随机器人移动变化，Room view 固定在锚点；非机器人环境发生状态/遮挡变化时，受影响的 L2/L3 content cache 必须重建，而稳定部分按 state/view/render hashes 复用。
- 仿真 rollout 不使用专家示教同 t 的缓存假装当前视觉；必须从 rollout 当前 SG/Geometry 更新必要空间视图/latent（相同内容可复用）。如果视图过密导致在线推理过慢，先比较少量子集的 SR/时延，不要为追求“完整 360°”不加控制。

## 6. 需要讨论确认的四项，以及最小实验

**建议先做一个代表性厨房、只读仿真小样本，而不是立刻冻结全量训练输入。**

1. `h_split`：Left 光学高度是否使上下正交图的柜体/台面产生严重切面；是否更需要上层 Height/Instance 通道而非另一张 RGB。
2. `anchor`：房间几何中心、最近的有效自由空间点，以及可见覆盖最好的候选位置三者差异究竟有多大；是否需要第二锚点。
3. `r/FOV/pitch`：单锚点 45°×8、90°×4 的具体画面；遗漏属于水平 FOV 过小、垂直 FOV 过小、近处遮挡，还是空间锚点错误。评估额外 pitch 与增大 FOV 的信息增益。
4. `readout`：先比较 Lower BEV + 8 views 和 Lower+Upper + 8 views 的图像互补性，不因“上下两张都能渲染”就自动判定两张都应输给 Cosmos。

产物建议：一页视觉审核板（lower/upper，房间示意位置仅作 audit，候选 yaw contact sheet，depth/instance coverage、anchor xyz、FOV/pitch、每视角缺口原因）以及相应 cache hit/reuse 估算。图片用于人眼确认，正式训练的 BEV 仍来自真实三维投影。

**当前未执行渲染/测试**。这份文档只是将最新用户澄清落实为可检验、可配置的设计路线，等待按单场景结果逐项确认。
