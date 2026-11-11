# G2 RoboCasa Visual Source Z-Buffer 实验与验收范围

日期 2026-11-11。状态：EXPERIMENTAL / H1=PENDING_HUMAN / training_ready=false。适用 RoboCasa MuJoCo Full Map GT；不构成真机 RGB-D 能力证明。

## 1. 根因

nav_sg/g2/gt/mujoco_scene.py 的 extract(geometry="collision") 输出 Collision Mesh，负责原生 10cm occupancy、Room、Scene Graph 和关联连接。10mm 彩色体素来自 g2/offline/direct_source.py 的 Visual Geom。旧版 g2/views/render_connections.py 使用 Collision Mesh 做彩色 View Z-buffer，再用 Visual RGB 体素做 15mm、30mm 最近邻补色，因此在两者不重合处产生柜门中心和黑色边框。

真实 Episode 005077 的 entity_1 对应 Collision 9300 个投影像素；10mm 原始 Visual 彩色点云能在全部 9300 个投影格子中提供同 native owner 的颜色，旧最终 View 仍有 484 个像素黑色且 color_valid=false。entity_4 为 9301/9301 但缺 484；entity_27 为 6300/6300 但缺 358；entity_28 为 2100/2100 但缺 134。Visual/Collision 两种深度来源在这些点约有 25mm 的偏差。旧 A/B 的“Collision 深度/Owner 未变”不是 Visual View 颜色完整性的独立证据。

## 2. 新增可选路径

新模块 g2/views/visual_mesh_zbuffer.py：

- 由已认证的 MuJoCo 模型闭包、Visual Geom 角色表和逐帧真实 FullPhysics 状态，构造各个 Visual Geom 的原始几何。每个 geom 独立保存 source_visual_geom_index，不再用 Collision Mesh 作为 RGB View 深度真值。
- 用 GPU 正交网格对 Visual Mesh 做最近可见表面 Z-buffer，得到可见 Visual Geom、深度和 native owner。
- 独立对 10mm 原生 ColorCloudMap 做 per-pixel 近深度 RGB 采样。仅在 native owner 相同、可见 Visual Geom 具有已验证有效颜色来源、色体素与该 Visual 面深度差不超过 10mm 时认定 color_valid=true。不会根据分类、旧 RGB 或不同对象的颜色推测未知材质。
- 正交几何 NPZ 除深度和 native owner 外，新增 source_visual_geom_index，方便日后按材质分析错误的可见性。
- 透明原始 Visual Geom 进入独立 Alpha 模块，按透明深度和不透明 Visual 深度判定前后。背景有可靠不透明 RGB 时可做颜色 Alpha 合成诊断；未知背景用棋盘图表示 UNKNOWN，不能视为真实场景颜色。
- 现有 10cm Collision 导航地图、Room footprint、Scene Graph 和物体关系原样保留。只是修正 View 的可见性来源，未新建第二套持久 occupancy 地图。

入口保留原有默认行为，必须明确指定新渲染选项：

python -m g2.offline.episode render --inputs VERIFIED_INPUTS.json --prepared VERIFIED_PREPARED --native-output VERIFIED_NATIVE --output NEW_OUTPUT --backend gpu --visual-mesh-source

## 3. 实证

- Layout1 Episode 005077：完整 459 帧中按约 2Hz 取 47 个状态，47/47 实际回放，141 张实际 RGB View 生成，训练就绪仍为 false。
- Layout10：15/15 个真实状态，由同一组代码验证通过。
- Native ColorCloudMap 的独立 10mm CPU/GPU per-pixel 投影：3 帧 × 3 View 的 RGB/Owner/Depth/valid 严格一致；此测试不构成完整 Visual Mesh 可见性 Oracle。
- 既有 G2 测试 + 新源视图/透明 alpha/owner错配/源帧不一致等测试，隔离候选内 616 PASS；正式提交后需再次在服务器校验。
- 真实性能参考：Layout1 47 状态旧 Collision + RGB 补色 106.23 秒，新 Visual GT 候选 129.47 秒；Layout10 的 15 状态约 78.05 秒。这不是严格受控同机空载 A/B，且离在线 2Hz 目标仍有距离。

## 4. 严格阻塞 Gate

1. 原生 ColorCloudMap 当前完整标注 native owner，却不完整保留 source Visual Geom/material ID。同一个 native owner 的多材质/重叠面仍需 geom/material 级独立认证；只有视觉几何与 RGB 属于同一 MuJoCo 源模型还不够。
2. 一些未绑定到 native owner 的 visual geoms，例如 outlet、light switch 和 front wall，不能未经证据被提升为 Room Wall/Object。它们的前景遮挡尚需审计。
3. 透明部分只有原始材质已验证且几何可见的独立 Alpha 路径；多层透明、混合 Alpha、折射仍缺。UNKNOWN 背景的棋盘诊断图绝不可进入训练缓存。
4. OpenCabinet 的 3 个 sRGB 纹理层板来源颜色还没有独立验证，必须保留 UNKNOWN，不可从别的同 owner 表面借色。
5. 必须对 source-projected 可见色、最终有效 RGB、误丢色、误添色、geom 材质、深度、owner 和 Alpha 做逐对象独立 Oracle 和 Layout1/Layout10 人眼验收。颜色已匹配不等于全局遮挡完成。
6. 未来真机 Cold Start/Partial Map 的 View 必须直接从传感器持久 RGBD/surfel 地图获得 Visual 几何，不允许依赖 MuJoCo 的 GT Mesh。

## 5. 状态边界

新路径仅做显式 opt-in 实验，不改变既有消费者默认输出。H1=PENDING_HUMAN，training_ready=false，不启动全量 9126 Episode View 生产。二进制验收证据在服务器 .g2_acceptance/episode_005077_full_2hz_20261111/diagnostics/source_visual_mesh_*，GitHub 仅保存源文件、测试和可重现报告。
