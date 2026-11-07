# PSM-WMA G2 详细设计 v1.4（讨论方案）：固定六视图内覆盖中央孤岛，不增加可变图像数量

- 日期：2026-11-07。性质：**用户反馈后的推荐调整，仍需真实渲染验收，不是已冻结的生产实现**。未执行代码修改、渲染、训练或 Latent Cache 构建。
- 继承 [v1.2 单一三维 BBox 欧氏距离 d](./PSM-WMA_G2_detailed_design_v1.2_2026-11-07_single_3d_bbox_distance.md)、[v1.0 正交六视图](./PSM-WMA_G2_detailed_design_v1.0_2026-11-07_root_affiliation_orthographic_wall_views.md)、[v0.8 真实 nav_sg 可生成性](./PSM-WMA_G2_detailed_design_v0.8_2026-11-07_sim_real_renderability_contract.md)、[v0.4 L2/L3 高吞吐缓存](./PSM-WMA_G2_detailed_design_v0.4_2026-11-06_spatial_view_latent_cache.md)。
- **在视图数量与孤岛表示上覆盖 [v1.3 每个岛额外四视图提议](./PSM-WMA_G2_detailed_design_v1.3_2026-11-07_island_component_views.md)**。用户明确指出 per-island 四图会造成不同房间附带图片数量不一致，不符合期望；因此**不把可变 N×4 图作为主线**。

## 1. 当前推荐：固定 1+1+4 六张视图

- `Floor Top`：含 Floor 根及其基于近邻连接的归属实体；从 +Z 向 -Z 做正交投影。
- `Upper Up`：含没有 Floor 根归属的实体与 Ceiling 背景；沿 +Z 正交向上投影。
- `Wall_North/South/East/West`：每面墙一张固定世界/房间轴正交立面，渲染**本墙背景 + 本墙连接归属实体 + 所有不归属于任何墙的中央/游离孤岛组件**。
- 图像类型/数量和顺序对每个**规则四墙矩形房间**固定，仍由相同 Canonical Spatial World + Shared Orthographic Renderer + L2 image/L3 frozen latent 生成。房屋范围内若不规则墙段超过四面，需要单独定义如何聚合至固定方位，并不能因为本稿宣称所有实际房屋天然是四面墙。

### 精确定义

```python
objects = all_scene_object_instances_excluding_building_roots

# 连边只由 3D BBox 最短欧氏距离给出：
E_obj = {(a,b) for a,b in objects if distance_bbox_3d(a,b) < d}
components = connected_components(objects,E_obj)

# 根节点仅用于赋予标签，不经过 Floor/Wall/Ceiling 根彼此中继：
wall_membership[obj] = set_of_wall_roots_reachable_through_obj_edges(obj)
floor_membership[obj] = is_reachable_from_floor_through_obj_edges(obj)

island_components = {C for C in components
                     if not any(wall_membership[o] for o in C)}

for wall_i in (N,S,E,W):
    members_i = {o for o in objects if wall_i in wall_membership[o]}
    for C in island_components:
        members_i.update(C)
    render_orthographic(wall_i.background, members_i, direction=wall_i.inward_view_axis)
```

每个孤岛不创建自身的新图片，而在四个固定方位的正交图里作为允许的前景实体组出现。一个中央柜体的四面侧面由四方向图共同展示。对于非孤岛物体，仍保留 v1.0/v1.2 的各墙归属语义。

注意：**不能把 Floor 当作组件中继**。因为所有独立落地家具都可能属于 Floor；若经 Floor 连接，则一个中央岛台会错误地“连到”贴墙冰箱，导致孤岛遗漏。Wall/Ceiling 根也不能相互中继。

## 2. 优点与需要明确的代价

**优点**
- 典型四墙厨房固定 `[Floor, Upper, N, E, S, W]` 六张。没有 `6+4N` 的房间间输入数量变化，冻结视觉 encoder 后可预计算固定 L2/L3 latent，Global Encoder 不需要处理随孤岛数量变动的图像槽位数。
- 不选房间中心虚拟相机锚点，也不调 FOV/r/pitch；视图世界/房间正交轴稳定，岛台的抽屉等正/背/左右立面可获像素表达。
- 保留完整 SG/Relation，筛选只在 renderer 的 view membership 阶段；颜色来自现有 nav_sg `ColorCloudMap<PointXYZRGB>` 或 GT 后端统一几何协议，未见表面不能伪造真 RGB。

**代价与边界**
- 岛台可能遮住该墙原有的挂墙/近墙物体；使用深度测试的自然几何遮挡，**不能保证**同图同时清晰展示 wall 子图与岛台图。必须先实图检查；没有必要事前引入多 layer 透明合成。
- 因为额外投影的是全部岛屿，若房间中存在多个独立大型组件，四张墙立面仍可能拥挤；若触发严重遮挡，需要再研究优先显示或层级 mask，先不冻结复杂的视图分层方案。
- 四方位投影是沿 World/Room XY 正交视线，不会凭空恢复 nav_sg 从未观察的柜背纹理；未知/颜色缺失 mask 仍是合法的模型输入信息。
- 如果要把本四墙图称为“墙面自身属性”，内容已经不是**纯粹只含墙附着对象**；推荐名称改为 **Room Cardinal Elevations (Wall + Island)**，明确表达每个方向的房间立面读出，而非把孤岛误写成墙的真实连接成员。
- 动态归属/SG 高频变化时，应以对应 scene+view version 更新/失效受影响 L2/L3；ColorCloudMap 2Hz ROS 发布不等于空间像素完全实时，不能把旧岛台位置继续作为新 SG 状态。

## 3. 第一轮最小验证（NOT_RUN）

用一个已对齐 RoboCasa 厨房，挑选至少一组中央独立柜/岛台：
1. 输出实际`d=0.30m`物体组件、每组件 wall/floor membership，确认中央独立柜是 `no_wall_membership`，而靠北墙冰箱因 `bbox_distance<d` 是 `North`。
2. 对同一 SceneState 渲染 **v1.0 严格墙归属四立面** 与 **v1.4 Wall+Island 四立面**；对照柜门、抽屉是否出现，以及岛台是否遮挡墙物体。
3. 每房间最终仍只有固定六种 view ID，统计图像 L2/L3 总数、最大/平均空间遮挡像素比及 missing/unknown。
4. 若大面积前景遮挡、墙信息丢失，先根据真实失败画面再选简化的显示策略，而不是自行默默生成可变数量孤岛图。

**推荐采纳为下一轮视觉审查候选，暂不将其作为最终固定输入定义。**
