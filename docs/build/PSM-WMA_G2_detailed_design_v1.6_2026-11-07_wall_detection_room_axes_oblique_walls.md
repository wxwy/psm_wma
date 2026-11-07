# PSM-WMA G2 详细设计 v1.6（讨论稿）：实体墙/开放边界、Room 局部轴与斜墙投影

- 日期：2026-11-07；项目 `wxwy/psm_wma:V3`。
- 状态：源码只读核查与技术建议；没有执行墙面检测、生成正交图或训练。几何规则与异常条件仍需真实图片验证。
- 继承 [v1.5 Island 作为 Room 派生资产分组、Object 仍直接挂 Room](./PSM-WMA_G2_detailed_design_v1.5_2026-11-07_room_island_view_assets.md)、[v1.2 单一 3D 欧氏 BBox 距离 d](./PSM-WMA_G2_detailed_design_v1.2_2026-11-07_single_3d_bbox_distance.md)、[v0.8 Sim/Real 共用渲染输入契约](./PSM-WMA_G2_detailed_design_v0.8_2026-11-07_sim_real_renderability_contract.md)。

## 1. nav_sg Room 划分不提供“真实四面墙”保证（SOURCE-CONFIRMED）

当前源码 `mapping_8_3/mapping/`：
- `src/room_pipeline/room_pipeline.cpp:553-574`: SDF/ESDF/GVD→拓扑图→节点语义→Room 聚类→Room Builder。
- `src/room_pipeline/room_pipeline_room.cpp:344-413`: Room = 拓扑节点 `cluster_id` 分组；`Room.center` 和 `Room.boundary_hull_2d` 不是物理墙。
- `src/room_pipeline/room_pipeline_room.cpp:681-724`: `boundary_hull_2d` 是**拓扑节点二维凸包**，没有墙的几何语义；不可当 Wall segments。
- `launch/params_{sim,real}/room_pipeline_params.xml`: `source=esdf_grid`, `clustering_method=topocut`, `geometry_only=false`, `feature_projection=room_similarity`。因此开放式客餐厅可根据语义或几何证据分成两个 Room，也可能保持一个；不存在“四墙包围才算 Room”的代码硬条件。
- `src/room_pipeline/room_pipeline.cpp:977-1020` 的 `/room_pipeline/wall_mask` 是占据切片的 RGB 伪彩可视化，不是 `wall_id/normal/geometry`。
- `include/mapping/utils/floor_segmenter.h` + `src/utils/floor_segmenter.cpp:295-329` 已有 3D Occupancy→高度切片 `SLICE_UNKNOWN/FREE/OCCUPIED`，真机和仿真配置中 `room_pipeline/floor_segmenter/slice_height_above_floor=1.6m`。
- 尚**没有**原生的 `physical_wall` vs `open_boundary` 完整二值/三态分类与有限 3D WallSegment API；需要最小适配器。

## 2. 简单的真实墙面检测（PROPOSED）

**不新增学习式 wall classifier，不依赖 Room 凸包画墙。**

1. 用已检测的 Floor/Ceiling 高度，抽取多个 3D 占据切片（如离地0.5/1.5/2.2m，实际高度需随室内净高自适应），得到同一 XY 的 free/occupied/unknown 证据。一个 1.6m 切片只够当墙候选，不够区分冰箱、落地大柜和真正建筑墙。
2. 从多切片的一致狭长占据结构提取连续竖直表面（可先 2D 线段拟合，再用 3D 柱/平面支持检查；可复用 OpenCV/PCL 的线段/RANSAC 平面拟合）。墙的近似条件：面法向接近水平、具有较大高度及连续长度、从 room 内侧能观察到实体面；需要与已知高柜、门窗开口、unknown 区分，不能仅凭高度强行判墙。
3. 仅对 Room 边界附近候选及相关可见墙面输出真实 `WallSegment(id, polygon/3D finite extent, inward_normal, confidence, evidence, adjacent_room_uids)`，与 Room 拓扑分界分别存储。一个真实墙可能关联两个 Room，且 Room 一侧也可能完全没有墙。
4. 对两个 Room 接壤的局部分界：真实墙证据充分→`physical_wall`；未检测到墙且两侧均已知 free 并几何连通→`open_boundary`；其他→`unknown`。**不把没有看到墙一律判成开放。**
5. 如果高柜紧贴墙遮住整个表面，当前彩色地图不保证能看到真实墙。该区域可标 `unknown/occluded` 并继续保留高柜对象，不能为了渲染生成 MuJoCo 特权的假墙；需要真实墙结构证明才能将它标成 wall。

本阶段只是空间几何证据分析，不产生 Costmap、底盘可通行标签或路径规划。采用的占据切片已在 nav_sg 内，代码改造是 WallSegment 提取与结果 ABI；实际误检率/速度必须验收。

## 3. 固定方向是 Room 的局部坐标，不必是 World X/Y

**规则**：同一个 Room 保存稳定 `T_world_room`，Room 正交四方向视图始终为 `±X_room, ±Y_room`。训练/真机共用这个坐标约定，并保留 `view_transform,meters_per_pixel,wall_id/segment_refs,validity`。

- 世界轴对齐矩形房间：`R_world_room ≈ I`；正常输出四个 Room 方向。
- **整体斜置矩形房间**：用较长/可信的真实墙面拟合 dominant direction，将 `Room X` 对齐主墙切向、`Room Y` 为其法向正交方向；四图随 Room Frame 旋转，无需新增图槽。主轴方向的180°歧义需使用固定世界坐标和稳定 ID 消歧，不允许每个 Episode 随机翻转。
- 开放式 Room：方向槽仍四个，但一侧可能是开放边界，不构造虚拟墙；开放方向的墙面属性图可为空/unknown，保留 validity/mask。**是否让开放方向显示其他房间对象不是已确认功能。**
- **单面斜墙/不规则房间**：四个 Room 方向仍保留，几何可按实际世界三维形状从这四方向投影，墙可能被缩窄或斜看，不应宣称获得该墙无畸变真实立面。若某墙严重斜向造成有效像素不足，可单独按墙面 inward normal 做真正 wall-local 的正交 `(u,z)` 投影作校验/后续备选；是否改写四槽 ABI 或引入额外投影，不在本轮冻结。
- **若要对真实斜墙单独制作正立面**：取墙面世界单位法向 `n`（指向室内），竖直轴 `e_z=(0,0,1)`，水平轴 `u = normalize(e_z × n)`（符号选取一致）；沿 `-n` 正交向墙面投影，图像轴用 `(u,e_z)`。此时 1m 墙面水平距离对应固定像素距离，真正正对墙。
- 若 Rooms 不是凸的（L 形）、有不平行墙段，不能用一个矩形旋转假装全部四墙均被完整正面覆盖；这时重点输出已知真实墙段及其 normal/coverages，而不是发明不存在的墙。

## 4. 连接距离 d 与斜墙（重要）

沿用用户已冻结的**唯一三维 BBox 最短欧氏距离阈值** `connected(A,B) = distance_bbox_3d(A,B) < d`，候选 `d=0.30m`。

**但斜墙的 Axis-Aligned Bounding Box 可能占据非常大的空白矩形**。例如一条 45° 的斜墙若只用世界 XY AABB，可能让远离真实墙面的物品也具有接近零的包围盒间距，产生错误连接。建议：
- 斜墙用**有限、贴合墙面方向的 OBB**（仍是 BBox）或由有限墙段组成的几何包围体；
- 墙和物体仍使用**最短三维欧氏距离**，**只有一个 d**，不重新引入分别的 X/Y/Z 距离阈值；
- 如果首轮仍用简单 AABB 快速候选筛查，对斜墙必须进行 wall-local OBB 最近距离复核；不得把离墙很远的物体因 AABB 空白区域误连接成墙归属；
- 墙端点、门洞、墙面高度和 unknown 必须保留真实有限范围，不使用无限墙平面。

## 5. 最小验收（NOT_RUN）

1. 普通矩形 Room：四个物理墙段、四方向图以及 Floor/Island 归属正确。
2. 开放客餐厅：Room 可以被分为两块但交界处 `open_boundary`，不输出虚拟墙 RGB；若分成同一 Room 也应由同一流程保持物理 wall 识别不受 Room 聚类标签影响。
3. 整体斜置矩形 Room：Room Frame 相对 World 旋转后四图对应真正墙立面、视图顺序稳定。
4. 仅单面斜墙：同一房间四卡槽输出不强造第四面墙；对比在最近 Room Cardinal 方向和沿墙法向本地正投影的几何压缩。
5. 斜墙 AABB 远距离误连接回归：固定 d 下 OBB/有限墙面几何复核必须拒绝与真实墙远离的物体。
6. 真机来源：同一真实 ColorCloudMap + SDF/Occupancy 可产生实际 WallSegment 和四方向图；未观察到的墙面与高柜背面标 `unknown`。

**本文件是下一轮源码适配与数据审查输入，未承诺当前 nav_sg 已实现 WallSegment 检测，也未冻结新模型或训练。**
