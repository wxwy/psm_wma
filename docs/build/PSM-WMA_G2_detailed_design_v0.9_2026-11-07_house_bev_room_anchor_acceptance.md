# PSM-WMA G2 详细设计 v0.9（讨论稿）：整屋双正交图、房间全向图及锚点验收

- 日期：2026-11-07；仓库 `wxwy/psm_wma`，分支 `V3`。
- 性质：用户确认的设计边界 + 下一轮候选验收规格；**未冻结确切高度、角度、相机 FOV、锚点数量或模型输入张数**，不授权全量构建、仿真运行或训练。
- 继承 [v0.7](./PSM-WMA_G2_detailed_design_v0.7_2026-11-07_orthographic_bev_canonical_views.md)、[v0.8](./PSM-WMA_G2_detailed_design_v0.8_2026-11-07_sim_real_renderability_contract.md) 与 [v0.4 缓存](./PSM-WMA_G2_detailed_design_v0.4_2026-11-06_spatial_view_latent_cache.md)。
- 目标是用一次代表性 RoboCasa 厨房视觉审查收敛 **上下正交空间图 + 规范房间全向图** 的真实参数；所有图像仍须能够由真机 nav_sg 的有颜色几何地图生成。历史真实 Left 图库独立 OPTIONAL。

## 0. 当前确认约束

1. ColorCloudMap 的 RGB-D→`PointXYZRGB` 体素融合已存在，RViz 可以显示真实 RGB 彩色点云；不需要把整个 nav_sg 从 XYZ 重构成 RGB。真机/仿真配置的彩色云**发布**目前设 2Hz，这是第一版可以接受的地图可视状态更新量级，但不等于融合吞吐或 SG 的更新频率。参见 [彩色点云审计](./PSM-WMA_G2_colored_pointcloud_10Hz_vs_3DGS_audit_2026-11-07.md)。
2. 房屋/大部分布局缓慢变化；小物件的当前位姿、部件和关系由 SG/State 高频更新。**视觉旧图仍可能包含已移动小物件的旧位置**，必须在 Version/Time 中标记，不得用旧视图覆盖较新的 SG 事实。
3. **不新增底盘 Costmap/Traversability 学习标签**。几何/空间视图保留地板、墙、物品大小、位置、高度和未知区域；如何移动由 Cosmos 学习。离线相机锚点的几何空闲测试不等于导航规划。
4. 房间全向图是**共光心规范虚拟相机**，只参考 Left 实际高度；不要求 Left 安装偏移、机器人旋转、机械臂入镜或 Left 原始 FOV 一致。图片是三维地图的合成视角，**不是历史相机观测**。
5. 正交/房间规范图最终必须共用一个可由 GT 和真实 nav_sg 彩色点云生成的 3D→2D renderer ABI；L2 图像、L3 frozen latent 都离线构建并绑定场景/帧版本；训练只读缓存。SG 对象不按大小提前过滤。

## 1. 整屋上下正交图：应先冻结哪些空间规则

- **nav_sg 真实数据边界**：当前 `ColorCloudMapWorker` 发布给 RViz 的彩色点云经过 `vis_filter_max_z` 高度裁剪（`src/utils/color_cloud_map_worker.cpp:425-445`）；验证上层视图时必须使用未被显示过滤截断的底层彩色点云快照，或显式调整导出范围。不能从 RViz 当前只显示的低层点云推断高柜/吊柜不存在。地图真机 2cm 与仿真配置 5cm 叶尺寸也须在渲染质量比对时单独记录。
- 地图框架：固定 World XY；一个 SceneTemplate 的全部 Episode 共用 XY bounds（含必要外边距）、轴朝向与米/像素比例；两张视图逐像素 XY 对齐。房间坐标可另外提供与 World 的变换，机器人底盘位姿作为独立输入，不因它移动而重绘整屋图。
- 分界高度 `h_split`：从训练对象实际 Left 光心的**世界高度**作为第一个候选。当前已核实 episode_000036 `ep_meta.cam_configs.robot0_agentview_left.pos=[-0.5,0.35,1.05]` 是相对 `mobilebase0_support` 的局部安装位置，不可以直接宣称世界高度恒为 1.05m；须用对应 MJCF/状态正向运动学求出实际参考高度。
- Lower：裁剪 `z<h_split` 的已知三维几何，从 `h_split` 往 `-Z` 做正交投影，生成真实几何/彩色表面视图与深度/高度和 validity 参考。
- Upper：裁剪 `z>=h_split` 的已知三维几何，从 `h_split` 往 `+Z` 做正交投影。注意该图主要看到上方物件的**底部/朝下表面**，不一定能解释它们的顶部和柜子内部。天花板/屋顶/门板的显示与裁切要写入渲染配方。
- 不通过“把名字和 bbox 画在 XY 平面”替代三维几何/颜色投影；也不需要完整摄影级 Mesh 纹理。当点云稀疏时，允许使用有明确 half-size/Depth test 的 point/surfel splatting，并保留尚未观察到的空洞为 unknown。
- 几何裁剪可能产生不完整的物体断面。候选检查 `h_split = actual_left_height`、略高、略低，人工对照工作台/柜体和地板的真实性，最后再定参数；阈值具体增量 OPEN，不提前锁死。
- 下/上各自沿射线看到的是该高度切片里最近的表面；正交不消除同一 XY 多层的内部遮挡。依赖 SG/Relation 额外表达 inside/on/part_of 等事实；不可把颜色图单独当世界真值的完整表示。

## 2. 房间规范相机的锚点：两个阶段选择

### 2.1 自动候选（所有候选基于相同三维地图，不需要底盘导航图）

1. 从 nav_sg Room 的 `center`、`boundary_hull_2d` / Room 区域、3D occupied/known/free 中得到近中心有效候选。Room `center` 可能是骨架图节点平均而不是自由空间中的可放置相机位置；无 Room 时先按已知厨房几何/房屋空间生成临时 Room，单厨房不因房间算法当前没有结果就阻塞原理验证。
2. 固定相机光心 `z=h_camera`（参考当前模型 Left 世界高度），确保该光心及近裁剪处于**已知自由空间**、不位于墙/柜/物体内部；必须能在当前地图由已知几何计算，此处不要求整机可达性，因为这是一台虚拟相机，而不是机器人巡视历史。
3. 初选若干个中心附近位置，包括空间几何中心、有效自由区靠中心的位置，以及有较多几何净空的候选；不一味选择离障碍最远的点（可能偏房间角落），也不盲选 Room.center。
4. 用低分辨率 room view depth / 彩色 RGB / validity / 实例标签或几何采样，评价每个候选对已知墙、台面、工作区、柜门及上下层区域的有效覆盖、近处截断、遮挡、缺失面积与图片之间冗余。**只能评价该 backend 当前已知的三维表面**；GT 完整地图允许满覆盖，真机不能借不可见 GT 表面评分。
5. 优先选一个靠中心、空域合法、视觉覆盖好的主锚点；若中心位置遮挡严重才增加第二锚点，不要求每个 Room 永远恰好一个。
6. 静态 SceneTemplate 锚点/房间绝对坐标可以跨 Episode 共享；图像版本仍随当前对象状态/颜色地图变化。Partial/Cold 时在可用已知地图范围内选有效锚点，标 unknown。

### 2.2 角度/FOV/pitch 三维度分开验证

- 全向图基准 `r=45°`，八张 `yaw=[0,45,90,135,180,225,270,315]`，训练可选索引 `[0,2,4,6]` 得到每 90° 四张；也可另建更密（如 22.5°）候选库，冻结前不可全部缓存为长期训练输入。
- `yaw=0°` 绑定稳定 Room X 轴（与主要墙面平行），全局保存 `T_world_room`，若房间不规则或 Room axis 不稳定，则以 World +X 为确定性回退，保证相同 SceneTemplate 的 0° 不漂移。
- **FOV 与 r 不混同**：当前原始 Left 的 `fovy=60°` 是校验样例的实际元数据，但不是虚拟相机的最终 FOV。可以先比较 60°、80° 或 90° 的候选，注意同样画幅下 FOV 越大远处小物品所占像素越少。对正方形图片 horizontal FOV ≈ vertical FOV；一般长宽比不同需用真实投影公式计算。
- **上下观察补偿**：仅水平 yaw 旋转不能解决吊柜上层或地面漏看。若缺口来自垂直 FOV，可为少数方向补充 `pitch=±20°` 左右候选，而不是一开始对所有 8 个 yaw 都拍三层俯仰、编码 24 张。
- **临近遮挡**：相机中心离柜子很近造成贴脸大幅截断时，通常移动锚点比继续减小 r 更有效；一处实物遮挡无法通过同一光心 yaw 密采样解决，才考虑第二锚点。
- 被保留的每图必须有 `room_id,anchor_id,T_world_camera,yaw,pitch,FOV,scene_version,color_map_version,render_recipe,validity`，并标明是 `synthetic_room_view`。

## 3. 2Hz Colored Map 与高频 SG 的视图语义

- 静态彩色表面地图可以按已观测内容约 2Hz 发布/更新供空间视图使用，但 SG/运动对象及关系可能更高频。**这两个时间戳与版本必须分离**。
- 若 SG 已知一只碗从 A 移到 B，彩色地图仍显示其原位置，此时不能继续把旧像素当成当前碗位置。可选方式：在图像中对已知移动实例旧区域标 invalid/unknown，或若有与实例绑定的 object-centric 颜色点子图，按新位姿更新对应表面；首版建议从版本/失效标记做起，不为追求即时画质建立大系统。
- Cosmos readout 可以同时拿 `view_color_timestamp`、`sg_state_timestamp`、`stale/unknown mask`；所有空间图与关系数据按源时间解释。若实际视图像素不能及时更新，不应无标记输入过期内容。
- 需要独立评估 ColorCloudMap Worker 实际融合处理率、2Hz ROS PointCloud 发布率和 Global View 更新/Encoder 成本；当前 2Hz 参数只能证明发布节流设置，不能推断系统承载能力。

## 4. 最小视觉审查 Gate（NOT_RUN）

使用已校验的 RoboCasa `PickPlaceDrawerToCounter/episode_000036`，**先审图，再冻结大规模 L2/L3 cache**：

A. 导出同一场景的 World-aligned Lower/Upper at 3 nearby candidate heights，配世界坐标/height/depth/unknown 审计图，检查水平位置一致与台面/高柜/层板是否被错误截断。

B. 从 Room.center 附近采样 5~9 个候选锚点，在原始 Left 相对高度（经 world pose 恢复）布置规范共光心虚拟相机，先做低分辨率 `r=45°`、`FOV=60°/80°`、单 pitch。记录锚点在三维场景的位置合法性、每张图可见实例/区域、像素规模、空洞比例和遮挡。5~9 与 60/80 仅是样本 Gate 的起点，不是最终固定参数。

C. 找出最大的未覆盖部分，针对性单独增加 pitch、调整 FOV 或第二锚点，对比实际新增有效可见区域；不要为每件物品一律拍多角度。

D. 输出一张视觉审核板（上下正交 RGB、height/depth、room anchor candidate positions、最终方向图接触表、缺失指标），给用户检查。若真实 nav_sg 彩色点云无法复现 GT renderer 的图类型，当前视图方案不能进入 Cosmos 正式缓存。

E. 通过图像/可生成性检查后再定义 Global reader ABI、每样本 4/8 张、选定编码器与 L2/L3 cache；训练期不能实时渲染。

本轮仅讨论与记录，没有执行任何渲染、代码或训练。
