# PSM-WMA G2 详细设计 v1.0（讨论稿）：Floor / Ceiling / Wall 连接归属驱动的正交视图

- 日期：2026-11-07；仓库：`wxwy/psm_wma:V3`。
- 状态：用户新提议、已确认的关系传递规则与工程建议。**视图选型尚未完成实物渲染验收，不属于 frozen 实现授权。**
- 继承：[G2 v0.3 nav_sg/MuJoCo 数据流](./PSM-WMA_G2_detailed_design_v0.3_2026-11-06_navsg_mujoco_dataflow.md)、[v0.4 L2/L3 预缓存](./PSM-WMA_G2_detailed_design_v0.4_2026-11-06_spatial_view_latent_cache.md)、[v0.8 仿真-真机共用可生成性](./PSM-WMA_G2_detailed_design_v0.8_2026-11-07_sim_real_renderability_contract.md)、[v0.9 早期上下高度切分及 room 全向图候选](./PSM-WMA_G2_detailed_design_v0.9_2026-11-07_house_bev_room_anchor_acceptance.md)。
- **最新取舍（PROPOSED）**：以**连接归属驱动的 Floor Top View + Ceiling/Other Up View + 4 Wall Orthographic Elevations** 为优先实验；原房间中心 45°×8 透视方向图降为候选/对照。覆盖 v0.9 中“以 Left 高度固定剖分上下图”及“Room.center 锚点/八方向视图作为 P0”的默认选择。
- SG 建图仍保留有意义的全部实例/部件，不做“大型物件才可进入 SG”的筛选；根连接的筛选只在 Spatial View Renderer 读出阶段发生。
- **不建人工导航 Costmap/Traversability 标签**，底盘/机器人相对空间位置由几何和当前 state 表示。所有视图必须能从真实世界 nav_sg 彩色几何 + 关系数据生成；MuJoCo GT 不允许变成训练期独享的视觉模态。

## 1. 用户核心设定：连接筛选与传递

1. 与**地板**直接或沿有效连接链间接相连的物品，进入**俯视 Floor View**。
2. 不属于地板连接链的物品，进入**仰视 Upper View**；天花板作为该图真实的背景，需保留可用的已观测 ceiling surface（未知部分保持 unknown）。
3. 每面墙各生成一个从室内向该墙看的**正交立面 Wall Elevation**，图中只保留该面墙与**直接或经有效连接链间接相连**的物品；该墙自身是背景。
4. **关键传递规则（用户明确补充）**：若 A 与地板/墙直接相连，且 B 与 A 有有效连接，那么 B 同样属于该地板/墙。可沿 `A→B→C` 任意有限层级递归传播。物品容器内的物体也属于容器所连接的根节点，不要求直接与根表面接触。
5. 一物体可能同时具有地板和某面墙归属，允许在 Floor View 与 Wall View 分别出现；视图不是互斥的“物体必须只存一份”分类。但 Floor vs Upper 的缺省划分优先使用 `has_floor_affiliation`，未知归属必须标注，而不能误当无遮挡背景。

### 1.1 连接不等于欧氏接近或所有物理碰撞

**推荐的读出方向为 child → parent**，parent 表示其支撑/承载/固定连接的结构或实体：

- `attached_to`, `fixed_part_of`（结构连接）。
- `supported_by` / 成立的 `on`（稳定承载）。
- `contained_in` / 成立的 `inside`（物品在容器中，即使未直接接触根节点）。
- 关系来源：MuJoCo GT 的 Fixture/Body/Geom/Joint 归属与接触、位置几何，或真实 nav_sg 对结构/支撑/包含的观测估计。GT 也不能只拿所有 MuJoCo Body 的 `worldbody` 父亲当作“实体彼此相连”。
- **不沿** `adjacent`, `near`, `left_of`, `in_same_room` 传播；短暂碰撞/机器人夹爪抓取也不自动赋予地板/墙连接。
- **不能跨结构根传播**：虽然每面墙在物理上接触地板，地板/墙/天花板三类根表面之间的建筑结构边不用于跨根归属传播。否则“墙贴地板 ⇒ 所有墙挂物品属于 Floor”会使筛选方案失效。
- 本轮传播的是派生属性 `root_affiliation(object)`，**不是声明 `on` 和 `inside` 等语义关系在逻辑上全都满足传递律**。
- 跨动态帧 `root_affiliation` 按有效时序关系更新。机器人操作中的 in-transit 物体可以带旧归属/动态占位版本或失效标记，避免接触在数帧间抖动造成 Floor/Upper 图像反复闪烁；具体临时归属规则待小样本决定。

### 1.2 示例：多层链式归属

```text
Floor_0
  └── Counter_A [supported_by Floor_0]
        └── Plate_B [on Counter_A]
              └── Spoon_C [inside Plate_B]
```

=> `Counter_A`, `Plate_B`, `Spoon_C` 都得到 `root_affiliation=Floor_0`，应纳入 Floor View。

```text
Wall_North
  └── Cabinet_D [attached_to Wall_North]
        └── Shelf_E [fixed_part_of Cabinet_D]
              └── Cup_F [on Shelf_E]
```

=> `Cabinet_D`, `Shelf_E`, `Cup_F` 都得到 `root_affiliation=Wall_North`，纳入北墙立面图。若不另外属于 Floor，亦纳入 Upper View。

注意：Cup_F 是否在视觉上被柜门遮住，不改变 GT 连接归属；但正交渲染依旧可能看不到它，**语义已知≠视觉已见**，须由 SG/Relation 保留完整事实。

### 1.3 最小无循环传播算法（建议）

```python
for obj in entities:
    membership[obj] = empty_set()

for root in (floor_roots + wall_roots + ceiling_roots):
    for child in descendants_over_allowed_typed_links(root):
        membership[child].add(root.id)

floor_view = {obj for obj in entities if any(r.kind == 'floor' for r in membership[obj])}
upper_view = {obj for obj in entities if not any(r.kind == 'floor' for r in membership[obj])}
wall_i_view = {obj for obj in entities if wall_i.id in membership[obj]}
```

实现必须排除跨根边，使用 `visited` 防循环，并将无法确定是否相连的对象标为 `unknown_affiliation`（Full-GT 仍需显示未归属实体的原因）。floor/ceiling/wall 根表面本身是**视图背景/边界的特殊层**，不作为普通对象沿建筑连接关系扩散。

## 2. 基于现有 ColorCloudMap 的渲染要求

- **共同输入**：`colored geometry/PointXYZRGB + per-instance identity + current pose/part + typed relation edges + roof/floor/wall surface identities`。
- **Floor View**：沿 `-Z` 正交投影地板及其连接归属子树，真实 RGB 由所选几何表面投影、depth test、点扩展产生。地图位置/范围与 world XY 对齐；不能把名字/Box 画成唯一空间图。
- **Upper View**：沿 `+Z` 正交投影未归地板的实体及 ceiling 背景；如果真实彩色地图尚未观察到高处/天花板，保留 unknown/validity，而不是合成特权纹理或默认白色顶棚。
- **每面 Wall Elevation**：从屋内向对应墙法向做**正交投影**；横轴为该墙平面内固定方向 `u`，纵轴为世界 `z`；保留该墙平面的已知颜色/几何作为背景，投影其连接归属的物体/部件，其他墙及不属于该墙的前景对象被过滤。应保存 `T_world_wall`、尺寸/米像素比、wall_id 和独立深度/unknown，防止看似同墙但位置错乱。
- 不用人造相机在房间中心转向，也不需要固定 FOV、r、pitch 或锚点位置；立面图是**与墙绑定的正交空间属性**，可由 GT 与真实 nav_sg 相同的几何投影 renderer 生成。
- 对四面墙的默认设定**仅适用于近似矩形/四面明确墙体的厨房**。L 形、多墙段、门洞或倾斜墙面应允许多于四个 wall segment 和 `wall_id`，而不是硬造四张错误的墙图。第一轮先针对真实矩形布局生成四张。

## 3. 与原房间中心多方向图对比

| 维度 | 四面墙正交立面（优先候选） | 固定锚点 yaw=45°×8 透视（备选） |
|---|---|---|
| 数据表达 | 每墙 `u,z` 的稳定投影，便于定位 | 真实相机外观，更接近照片 |
| 相机选择 | 不需 anchor、FOV、pitch、r | 需找合法 anchor 与覆盖检查 |
| 遮挡 | 可只渲染墙连接子图，减少其他结构挡墙 | 家具、近景遮挡明显 |
| 对象范围 | **只保留根连接链**；独立地面家具主要靠 Floor 图，侧面外观可能缺失 | 同视点可同时看到地面与挂墙物件的侧面 |
| 核心工程难点 | **墙面分段/实例 ID 与 typed support/attachment/containment 传播** | 选择锚点/视角与未知表面重渲染 |
| 缓存规模 | 典型 1 Floor + 1 Upper + 4 Walls = 6 图 | 典型 2 + 8 = 10 图（如同时保留上下图） |
| 真机可生成性 | 依赖真实 nav_sg 空间/颜色、可识别墙面与根连接关系 | 依赖真实 nav_sg 空间/颜色、新视角几何完整度 |
| 适合当前目标 | **更适合相对位置/房屋结构/长期记忆** | 更适合外观和泛化视觉描述 |

**推荐四墙正交作为当前首要研究方案**，但不能宣称其总体工程实现天然更简单：它省掉相机配置选址，却增加墙面 root 与连接关系质量要求。当前 Full-GT 可以借 MuJoCo 标注做关系上限；真机需要由 nav_sg 对可观测几何结构建立同一类根归属。若根归属/墙段在真实 nav_sg 不可靠，则该方案在 Full-GT 中的完美表现不足以满足 Sim/Real 可生成性 Gate。

## 4. 源码限制（已核实，不冒充现成能力）

- 原生 `nav_sg` 已有真正的 `ColorCloudMap<PointXYZRGB>`，但 `ObjectMap3D` 与彩图当前分支未完成稳定 object RGB/体素与实例绑定；该集成仍需实施。
- 当前 `Room` 提供 center/boundary_hull_2d/voxel footprints，但 `room_pipeline/wall_mask` 并非“四面墙各自的带 ID 平面”：其发布代码 `mapping_8_3/mapping/src/room_pipeline/room_pipeline.cpp:977-1020` 实际是自由/占据/未知二维切片伪彩点云。**四墙/多段墙的 plane normal、geometry bounds、stable ID 尚需从已有三维几何/Room 边界解析或估计。**
- 当前 G2 观察型 `on/inside` 关系推断有严格观测边界要求，不能被当成真实 RGB-D 下“全部支撑与墙固定关系已知”的现成功能。Full-GT 的连接和关系可以由 MuJoCo 直接供给上限；后续感知 backend 的根归属/未知情况需独立验收。
- 用于仰视的 Ceiling 颜色不能从 `ColorCloudMapWorker` 的 RViz 显示高度裁剪后点云恢复，应读取未裁剪的底层地图或开启相应高度数据来源。
- 物体移动后，关系归属改变会影响视图成员集合；彩色云低频（当前 ROS 发布 2Hz）但 SG 高频的版本差必须有 stale/unknown 标记，不能继续把旧 RGB 位置当作当前事实。

## 5. 缓存与最小结果验证（NOT_RUN）

- **L2/L3 全部离线预生成**：每个 `(scene_version, view_id, root_affiliation_version, renderer_recipe)` 映射到正交图/冻结视觉 latent。静态墙/地板背景可以跨 Episode 缓存；受影响物体和关系发生变化时更新包含该对象的视图。
- 原 G1 exact-window cache corpus 与 `start_frame=t` 绑定不变；训练时无动态 MuJoCo、nav_sg、视图渲染或冻结编码器。仿真闭环从 rollout 当前 PSS 生成/复用空间图，不读取示教未来缓存。
- 第一轮仅一个已验证厨房 Episode：从 GT Scene/Relation 提取 Floor/Ceiling/Wall 根节点，递归显示每张图收纳的实体清单、投影彩色云、正交 Floor/Upper/Wall 四面图、未知像素和时间版本；抽查 `counter→plate→spoon` 与 `wall→cabinet→shelf→cup` 的多层传递、结构根隔离以及物体移动后的版本。
- 同时用一版原 8 张 yaw RGB 作为小样本直观对照（不全量编码），重点看清楚地板物体是否缺少侧面、四墙是否干净/内容有用、低高层遮挡和真机 colored point 数据是否足够。
- 需用户进一步确认的参数：根连接类型及临时动态物品归属，非矩形房间 wall segmentation，墙视图中 floor-root 兼 wall-root 的重叠表示，以及是否至少保留一张额外的未筛选房间视觉图补充外观。

**本次为新方案与已确认“连接传递”规则的设计记录，不代表四墙图已正式选型或完成渲染/训练。**
