# PSM-WMA G2 详细设计 v1.2：唯一三维 BBox 最短距离连接参数 d

- 日期：2026-11-07。用户已确认：**删除 `d_x`、`d_y`、`d_z`、`d_xy` 的分轴阈值方案。所有实体间连接只以统一的三维最短欧氏距离与同一个参数 `d` 比较。**
- 优先候选 `d=0.30m`，可以配置；`d` 的最优数值仍待实际 RoboCasa 厨房验证。
- 本文在连接定义、根判定和测试参数方面 **覆盖** [v1.1 的双阈值建议](./PSM-WMA_G2_detailed_design_v1.1_2026-11-07_bbox_proximity_root_affiliation.md)。沿用 [v1.0 的 Floor/Upper/四墙正交图](./PSM-WMA_G2_detailed_design_v1.0_2026-11-07_root_affiliation_orthographic_wall_views.md)、[v0.8 Sim/Real 可生成性](./PSM-WMA_G2_detailed_design_v0.8_2026-11-07_sim_real_renderability_contract.md) 和 [v0.4 缓存](./PSM-WMA_G2_detailed_design_v0.4_2026-11-06_spatial_view_latent_cache.md) 中不冲突的部分。
- 状态：连接判据已由用户明确确认；正式数值与投影视觉质量尚待验收，**未修改生产代码/运行仿真/构建缓存或训练**。

## 1. 唯一的连接规则

给两个在相同世界坐标系中的三维 Axis-Aligned Bounding Boxes `A`、`B`：

```text
gx = max(0, A.min_x - B.max_x, B.min_x - A.max_x)
gy = max(0, A.min_y - B.max_y, B.min_y - A.max_y)
gz = max(0, A.min_z - B.max_z, B.min_z - A.max_z)

distance_bbox_3d(A,B) = sqrt(gx*gx + gy*gy + gz*gz)
connected(A,B; d) = (distance_bbox_3d(A,B) < d)
```

相交或接触的 BBox 距离为零。**不能**只看 X/Y 任意一个投影方向，也不能用 `(gx<d) && (gy<d) && (gz<d)` 或前版 `(sqrt(gx²+gy²)<d_xy) && (gz<d_z)` 代替三维欧氏距离。

- `gx=0.25m, gy=0.25m, gz=0` 时，三维距离约 `0.354m`，`d=0.30m` 应拒绝连接。
- `gx=0.20m, gy=0.20m, gz=0` 时，三维距离约 `0.283m`，应接受连接。
- 墙面/地板/天花板也使用**有限真实几何对应的包围体或面片范围**做 3D 最近距离，不把墙延伸为无限平面，也不能额外要求某个固定 XYZ 轴投影先满足阈值。对于非轴对齐的有限墙段，首版可用保守 AABB 初筛；若 AABB 空间空洞导致严重误连接，后续考虑精确几何表面距离作为**精度提升候选**，但用户指定的第一版定义仍是 BBox 距离，不擅自替换。

## 2. 传播、根隔离与多视图归属

- Floor、每个有限 Wall Segment、Ceiling 分别独立作为**根**。根节点之间即使接触也**不形成可传递邻接边**，以免所有墙面与地板一瞬间连成同一根。
- 每个对象与根、对象与对象均根据唯一 `distance_bbox_3d<d` 创建边，**不要求物理安装、支撑或真实接触**。冰箱离北墙不足 d，直接归属北墙；盘子和柜台距离小于 d，可由柜台继续传播连接归属。
- 根归属可沿任意有限长度的**物体—物体**近邻链传递；传播的是 `view_membership(root_id)`，不意味着间接对象到墙面的直接距离也小于 d。
- 一物体允许同时归属于 Floor 和多面 Wall；Floor Top 读 Floor 连通子图，Upper Up 包含不属于 Floor 的实体及 Ceiling 背景，每个 Wall Elevation 只读该 Wall 的连通子图与墙面本身。
- 保留所有 SG 实体，`d` 只控制 Renderer 输出过滤，不对 SG 原始节点做删除。物体移动与 stale 彩色地图需按时间版本处理，不能让过期视图遮盖新的 SG 状态。

**风险和验收**：一个 d 阈值就可能经跨物体的短间隙连接出一个巨型连通分量，导致 Floor/四墙的筛选能力消失。用户坚持可传递，因此不在实现中偷偷限制链深；先展示每张图的入选对象、重叠归属、连通分量大小、Floor/Upper 的比例，用真实厨房选择 d。

## 3. 最小校验测试（待执行）

对一个已对齐的 RoboCasa Episode：
- 单元测试：`0.25/0.25/0` 间隙必须拒绝、`0.20/0.20/0` 必须接受；XYZ 轴置换结果一致，`<d` 的严格边界正确。
- 核查冰箱距北墙、工作台距 Floor、台面与小物件等直接近邻；多级链闭包、建筑根隔离与多重归属。
- 使用 `d=0.30m` 输出 Floor/Upper/四墙共六张（矩形房间）真正 Colored Geometry 的正交图，检查没有因对角近邻而把大范围物件错误合并。
- 如果 `d=0.30m` 发生明显过度连接，再对 `d=0.20/0.25/0.35m` 做单参数灵敏度检查。**不再额外提供双阈值轴向开关。**

## 4. 明确生效的结论

**USER-CONFIRMED**：只保留一个可配置的、旋转坐标轴不改变空间判定意义的三维 BBox 最近距离阈值 `d`。它表达实体间真实三维空间的最短距离，而非投影到某一轴之后的距离。**所有此前 `d_xy,d_z` 推荐均失效。**
