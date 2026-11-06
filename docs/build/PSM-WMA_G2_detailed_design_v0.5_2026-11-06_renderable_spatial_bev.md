# PSM-WMA G2 详细设计 v0.5（工作草案）：BEV 来自可渲染三维空间地图

- 日期：2026-11-06；项目：`wxwy/psm_wma:V3` / `wxwy/nav_sg:G2`。
- **用户明确确认的修正**：Cosmos 的 BEV 必须来源于具有真实几何/外观的三维空间表示，经视角投影或三维渲染得到；**不是用物体名称、中心点、BBox 在 Python 中绘制的语义框图/示意图**。
- 关联：[G2 v0.3 原生 nav_sg / MuJoCo 接缝](./PSM-WMA_G2_detailed_design_v0.3_2026-11-06_navsg_mujoco_dataflow.md)；[G2 v0.4 空间视图缓存](./PSM-WMA_G2_detailed_design_v0.4_2026-11-06_spatial_view_latent_cache.md)。
- 状态：**已确认需求 + 尚待选型的工程建议**。不授权实现/渲染/训练；历史多角度机器人 Left 观察图库仍为 OPTIONAL，和三维地图的合成 BEV 是不同数据来源。

## 1. 正确术语与边界（CONFIRMED）

- **3D Metric/Geometric Map（三维几何/度量地图）**：物体真实几何形状、空间占据、位置、尺度、自由空间。
- **3D Scene Graph（SG）**：实例/部件/区域身份、语义、拓扑和对象关系；只靠名称+坐标不能还原真实外观。
- **Renderable 3D Scene / Map（可渲染三维场景地图）**：在真实几何基础上保留/关联颜色、材质、纹理、法向、可视化几何/运动学姿态等，使图像可以通过摄像机投影和遮挡处理生成。
- **BEV（Bird's-Eye View）** 是从上述三维空间场景按指定俯视投影与显示规则生成的二维**视图**，不是 SG 本体，也不要求它天然是“机器人实际拍摄过的历史图片”。
- 当前用户需要的，是**真实几何与外观的俯视渲染图（photorealistic / visually faithful BEV）**；文字标签、指示框、位置箭头等可另作为**独立可选 overlay**，不能替代主视觉输入。

## 2. 对当前 nav_sg 的实际源码能力核查（SOURCE-CONFIRMED）

2026-11-06 对服务器独立 PR #4 候选只读检查：
- `mapping_8_3/mapping/include/mapping/object_mapping/object_cluster3d.h:27-35`：当前 `ObjectCluster3D::cloud` 为 `pcl::PointCloud<pcl::PointXYZ>`，只有 XYZ，无纹理 Mesh/材质槽。
- `mapping_8_3/mapping/include/mapping/scene_graph/scene_graph_manager.h:29-39`：当前 `SceneGraphObject` 提供 cluster/room/centroid/AABB/existence 等，不存每个实例的可渲染 Mesh/Material。
- `mapping_8_3/mapping/src/map_ros_visualizer.cpp`：现有占据/点云 RViz 可视化不是高保真纹理渲染接口。
- `SDFMap3D` 以 Occupancy/ESDF、射线几何为主。即使得到“带类别的体素”，如没有颜色/外观/可渲染表面，输出仍倾向语义/几何图而非自然场景外观。

**因此不能声称原生 nav_sg 现已可从现有 SG/纯 XYZ voxel 直接渲染出真实俯视 RGB。必须维护可渲染场景资产，或增加依托其数据的渲染适配层。** 不要为了 BEV 把已知的 MuJoCo Mesh/纹理降采样成不可逆的无色点云后丢弃。

## 3. Full Map + MuJoCo GT 数据流建议（PROPOSED）

```text
MuJoCo MJCF + Mesh + UV/Texture/Material + GT Object/Joint Pose
                |
           GT Asset / State Adapter
                |
       nav_sg Canonical Spatial World
           /                     \
  Occupancy/ESDF/GVD          Renderable Scene Assets
  Object IDs, State, SG      Mesh/Primitive + material/texture
  Relations, timestamps      per-instance transforms
           \                     /
              Aligned world state
                      |
                3D BEV Renderer
            top-down orthographic projection
            real surface/shape/occlusion/texture
                      |
            RGB top view + aligned optional
         segmentation/depth/height/normal channels
                      |
               L2 BEV image cache
                      |
         Frozen image encoder (offline)
                      |
              L3 BEV latent cache
                      |
               Cosmos Global path
```

关键划分：
1. **MuJoCo 是 Full-GT 真值数据源**，可直接获得与原始实例几何同源的 visual geometry、材质/纹理、位姿/关节。nav_sg 的空间状态是把同源 GT 几何、身份、关系组织起来的工作表示；渲染的数据必须与 SG 的 frame/t 状态对齐。
2. **Scene Graph 不承担生成 RGB 像素的职责**。它供实例识别、语义与关系查询；真实 BEV 像素来自三维表面渲染。若最后为 Cosmos 筛选对象，也是 readout/overlay 侧而非在 SG 阶段删节点。
3. **优先复用已有三维渲染引擎**：当前 Full-GT 可以用 MuJoCo offscreen renderer 渲染**与 nav_sg 同状态对应的**正交顶视基准图，避免重造大型渲染器。长远应定义与 backend 无关的 `RenderableScene+SceneVersion` 合同，以便 nav_sg 感知路径用融合的彩色点云/纹理网格生成同类视图。可先以 MuJoCo 直渲作为画质/坐标基准，不冒充“现有 nav_sg 已具独立纹理渲染能力”。
4. 若要严格实现“从 nav_sg 空间地图生成”，需要由其规范场景保存对 visual mesh/texture 的引用或保存可重建 RGB 外观的几何纹理/彩色表面，而不是由位置标签重新绘图。**这属于明确的接口缺口**。
5. 不把屏幕截图或静态 SVG 原理图当作 BEV cache 的真实输入证据。要导出当前场景状态的真正 renderer pixel buffer、规范投影/相机参数与时间索引。

## 4. 俯视渲染规则必须明确（PROPOSED）

- **投影**：优先固定世界/房间坐标系顶视正交相机，固定高度/方向/图像物理覆盖尺度与像素尺寸，避免因机器人移动造成重复缓存。旧版 MuJoCo 3.2 MJCF 使用相机 `orthographic=true`，新版本接口可用 `projection=orthographic`；必须按服务器固定安装版本做有效性核验，不能直接复制最新 API 参数。
- **颜色与表面**：使用 visual geometry、UV/texture/material、必要光照与 depth test；不要用 collision geom 的粗糙 Box 去代替原始可视模型（碰撞几何仍用于 occupancy/关系计算）。
- **遮挡**：顶视会遮住下层柜板/容器内部；若提出 roof/ceiling cut-away、分层图或对象透明化，须作为显式 `render_policy`，对应独立缓存键，不可悄悄让图“透视”。Full-GT 关系可完整，但图片不能被错误解释为所有内部物体都可见。
- **空间对齐**：SG/Relation 的 world frame、渲染相机投影、图像横纵轴、机器人 pose 单独 condition，要能对同一物体 3D 世界点进行像素回投；不单纯追求画面好看。
- **两个用途分开**：高保真 RGB top view 作主视觉；必要的 instance mask/depth/height/occupation semantic 作为配准通道供分析或后续模型读出，不将文字框图覆盖 RGB 当唯一训练输入。
- **未来 Cold-Start 一致性**：MuJoCo 拥有完整纹理 Mesh，nav_sg RGB-D 只有已观察表面。可供模型的“真实 BEV”在 GT 与 perception 模式间可能存在画质/可见性分布差异，须明确并后续评测，不可声称两条支路当前等价。

## 5. 高吞吐空间缓存不变（CONFIRMED）

保留 v0.4 的 L0–L3 离线 precompute 思路，但 **L2 不再接受基于名字+坐标绘制的简易 SG 示意图作为主 BEV**。

- L0 规范几何/实例/纹理引用；L1 每 Episode 的时序 SG/Relation/State 索引；L2 真正的顶视渲染 RGB/可选其他配准图；L3 离线 frozen encoder latent。
- 由 `scene_template + episode initial state + state delta + renderer/view recipe` 判定每帧空间视图版本，不因只变化机器人位置就重新渲染固定世界 BEV。位姿变化导致真实图像变化时必须新建对应缓存。
- L2 cache key 必须包含 **visual assets/mesh/material/texture hash、渲染参数、顶视投影/比例、遮挡/裁剪策略、光照配置、有效 SceneState 和视图覆盖范围**。共享 geometry 但纹理不同的 Episode 不能错误复用 RGB/latent。
- L3 继续额外绑定 frozen encoder checkpoint、预处理、latent 维度/dtype 和 cache catalog。训练时候 `(episode,t,view)` O(1) 引用，不运行 MuJoCo/nav_sg/render/Encode。
- 若继续考虑“三视图”，也应当由**同一份可渲染的 3D scene**以不同正交或有定义的摄像机投影生成，而不是分别绘制三套节点示意图。Room-centered directional / orthographic tri-view 不必同时生产，先一例验收内容/画质。

## 6. 仅建议的最小验证（NOT_RUN）

选一条已有严格状态绑定的 RoboCasa Episode：在 S0 时同时导出 MuJoCo 顶视真实 RGB、geom/depth/instance mask、对应 nav_sg SG 状态和位姿，确认工作台、柜体、微波炉、杯子等具有真实轮廓/外观；再选运动帧验证它们位姿与 RGB top view/Mask/SG 共同变化；稳定段 hash/缓存可复用。人工检查真实渲染图片，而非仅检查标签/数值统计。

之后再在 L2 冻结图像输出定义并编码 L3；不要先生成全数据集低质量示意图，后来才发现它不是用户要的输入。

本轮记录的是**可渲染 3D 场景/真实视觉 BEV 的数据契约与技术缺口**，不是可用的 GT 渲染实现或 nav_sg 原生材质/纹理通路已经交付。
