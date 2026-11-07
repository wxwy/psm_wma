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
