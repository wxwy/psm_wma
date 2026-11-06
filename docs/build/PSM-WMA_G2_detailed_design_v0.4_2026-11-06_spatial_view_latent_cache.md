# PSM-WMA G2 详细设计 v0.4（工作草案）：空间视图与 Latent Cache

- 日期：2026-11-06。
- 范围：**Full Map + MuJoCo GT Update** 的离线训练数据生产、时序空间读出、空间视图生成、冻结编码器 latent cache，以及与 V3 cache-first 训练契约的绑定。
- 状态：**Owner 新确认的硬需求 + PROPOSED 实施方案**；未冻结具体视图类型、编码器、Token budget、分辨率或超参数，不授权执行实际缓存构建、训练、仿真或生产代码更改。
- 前置设计：[G2 v0.3：nav_sg 与 MuJoCo 数据流](./PSM-WMA_G2_detailed_design_v0.3_2026-11-06_navsg_mujoco_dataflow.md)。
- 既有 V3 契约：[Corrected V3 v3.0](./PSM-WMA_V3_Local_TTT_on_latest_Cosmos_RoboCasa_detailed_design_v3.0_2026-10-04.md)、[Phase3 cache-hit](./PSM-WMA_V3_phase3_cached_latent_sft_model_cache_hit_design_v1.0_2026-10-05.md)、[Phase1B source-binding](./PSM-WMA_V3_phase1b_cache_source_binding_design_v0.4_2026-10-05.md)。

## 1. 训练侧硬需求（OWNER-CONFIRMED）

1. **训练期间必须快速读取空间条件**：不逐步启动/恢复 MuJoCo、不在线跑 nav_sg、不重建 Scene Graph、不渲染 BEV 或空间多视角，也不对这些图像实时调用冻结视觉编码器。
2. **不仅缓存 BEV 的本地图像，也要缓存其 latent**。若启用房间中心各朝向视图、工程三视图等空间读出，也须预先生成各自图像及 latent cache；它们不是训练时附带实时渲染的选项。
3. **可利用时序复用**：SG/State 和空间视图无变化时多个训练帧可以指向同一个 render/latent；物体位姿、关节及空间读出内容变化时需要更新。
4. 此前保留的 **原始 Left+Wrist 视频的 V3 latent cache、严格帧索引与 Local-TTT 语义不变**；G2 是新增独立空间条件缓存，不覆盖原有 G1 video_latent。
5. 尚未决定最终是否用房间中心多方向视图或三视图，需在详细设计中作为正式候选及相关缓存预算考虑。**历史 Left RGB 图库仍是另一条 OPTIONAL 路线，当前不是前置条件。**

## 2. 四层缓存：昂贵操作全部发生在离线生产阶段（PROPOSED）

```text
Raw MJCF/Mesh + per-Episode MuJoCo states + ep_meta + V3 identity
    |
    v
[L0] Scene/Asset/Instance Truth (shared scene template + Episode S0)
    |
    v   nav_sg GT Map/Object/Relation adapters；按 t 更新
[L1] Temporal PSS/SG/Relation State + frame→version mapping
    |
    v   canonical spatial renderer (no learner)
[L2] Raster spatial views: BEV, optional room directional or tri-planar
    |   image ref + view/projection metadata + state/source/time
    v   frozen vision tokenizer/encoder ONCE per unique content+recipe
[L3] Spatial latent blob store + causal per-Episode frame→view_latent index
    |
    v
Train DataLoader: join existing accepted V3 cache key/start_frame
    + original current-policy video_latent
    + current spatial latents (L3; if configured)
    + current Relation/Spatial scalar tokens
    -> trainable Global Spatial Encoder/Adapter -> Cosmos Action Path
```

L0 与 L1 解决正确性，L2 解决可解释的空间输入及回归测试，L3 解决训练吞吐；训练时不能再动态求上述 L0–L3。**在线仿真不是离线训练**：在实际 rollout 时可由当前实际 SG 增量生成/编码发生变化的视图、稳定版本复用 latent；绝不能读取离线示教未来轨迹的缓存。

L2 与 L3 是不同的缓存资产：L2 用于可视审计/改编码器/重建缓存；L3 用于高吞吐训练。是否额外保存无损数值格式、图片压缩与分片格式待实测，不在这里定成单文件/每帧一图。

## 3. BEV 和房间多视图要分别定义（PROPOSED）

**BEV**：从带语义实例和关系的 PSS 得到一张统一尺度/坐标系的俯视空间读出；在图中表达实际可解释的几何、实例、房间/区域，必要时还可叠加对象高度/占据或状态颜色。关系/隐藏容器内部事实也可通过独立 Relation Tokens 保留，**不要指望一张俯视图表达所有 inside/part_of**。哪些对象在最终 BEV 中可见/筛选，属于**读出配置**，不能回头删除原始 SG 的实体。

**空间多视图不是“历史机器人 Left 照片”**，属于对 PSS 当前已知几何和状态作的**合成空间投影视图**。因此它的合法性由地图表示和投影规范决定，而不是此前 OPTIONAL 历史 Left 的机器人可达性约束。必须记录 `view_type, anchor_room_id, projection_matrix, canonical_frame, current_scene_version`。未来 nav_sg 感知更新模式必须使用同一个 renderer 与已知内容边界，不能把只有 MuJoCo 才能生成的真实照片作为现实感知已有的条件。

不同“多视图”需避免混为一谈：

| 候选 | 明确定义 | 优点/风险 |
|---|---|---|
| V0: BEV-only | 一个固定世界坐标／房间锚点的 top view | 最小工程与计算量，先验证空间条件；上下遮挡/关节细节可能被压掉 |
| V1: room-centered directional | 在房间自由空间中选稳定中心/锚点，固定相机参数，按约定几个 yaw 方向生成语义/几何视图 | 有更多侧面/容器结构；视角数量和房间中部遮挡影响成本 |
| V2: orthographic tri-view | 固定 top/front/side，即 XY/XZ/YZ 投影，严格绑定世界/房间坐标轴 | 可保留部分高度层次；沿投影轴重叠、遮挡、长宽比例问题需明确 |
| V3: BEV+少量补充视角 | 在固定 BEV 上增加 V1 或 V2 的有用视图 | 较强空间表达但有多图 Token 成本 |

**“房间中心各方向”与“工程三视图”并非同一种数据形式**；需单 Episode 看实际图像并核对信息差异后再冻结选哪一种。所有被选的方案均需 L2+L3 cache。无需立即为全部候选在全数据集生成多套 cache。

建议首先明确采用固定世界/房间参考 BEV、**机器人 pose/朝向单独作为状态 Token/可选 Overlay**。若把随机器人运动旋转的 ego-BEV、实时机器图标/轨迹直接画进 BEV，那么即使厨房静止，机器人移动也会导致每帧图像变化，大幅破坏缓存复用。若未来采用 ego-centric BEV，缓存键必须包含机器人位姿、crop/rotation/trajectory，不能错误复用。

为减小 sim→perception 差异，推荐 L2 首先做**基于 SG/占据/语义的固定规则空间渲染**（同一 renderer 可用于 GT 和 nav_sg 来源），而非直接依赖 MuJoCo 专属高保真 RGB 纹理渲染的房间视图。是否需要真实材质/视觉是单独实验。

## 4. 缓存去重：按输出状态与视图计算，不是仅按 SG 边变化（PROPOSED）

每条 Episode 帧 `t` 需要有逻辑空间版本，用对象位姿、关节、关系状态和 renderer 依赖计算实际的视图版本：

```text
Frame/Consumer(episode,t)
   -> scene_state_version(t)
   -> active_view_specs (BEV, room_id:view_yaw, tri-view...)
   -> view_key = H(scene_template, relevant_state/objects, view_config,
                   world projection, renderer version, target shape)
   -> l2_blob_ref
   -> latent_key = H(l2_content_hash, frozen_encoder_weights,
                     preprocess, dtype/precision, encoder_recipe)
   -> l3_blob_ref
```

- 同一状态/视图重复出现：共享 L2 与 L3；即使 Episode 不同，**只有完整 render 内容和 recipe 可证明相同时**才跨 Episode 共享。单纯同 layout/style 不足够。
- 一个物体在同一台面移动但 on 关系不变：空间视图如受影响仍需更新；关节改变但渲染未涉及该区域时，可复用其他 room/view latent。
- 先用状态版本/视图依赖集避免**重复渲染**，然后用图像 hash 避免**重复编码**；仅用完整 RGB hash 能节省编码但无法省渲染。
- 对位置容差/视觉等价的近似复用属于有误差的压缩，默认不要静默启用；需要通过空间几何误差和模型输入偏差 Gate。先保证正确映射。
- 静态模板可跨 Episode 共享基图，但动态 overlay 变化必须更新对应视图，不把整个厨房的可见/空间内容与原始场景模板混同。
- **场景状态版本 != 关系版本 != BEV 内容版本**。关系标签可能改变而图像没变，Relation Token 仍须刷新；图片会变而 SG 拓扑不变时，图片 cache 也需重建。
- Full-GT 当前帧所有已知环境事实可以纳入输入，但绝不能读取 `t+1` 或未来 GT 状态；未来视觉监督 latent 也不进入当前空间条件。

## 5. 两级编码缓存：区分 frozen image tokenizer 和 trainable global reader

当前 V3 是 `left+wrist` 像素横拼后经过官方 resize/pad，并以 **17 帧 exact window** 经 Wan VAE 编码成 `video_latent=[5,48,H_lat,W_lat]`；其中后四组是未来时序压缩监督部分，Local 只消费 current 第一组。

**G2 不可把 BEV 和 room-view 当作 17 帧视频或直接拼接进现有 `video_latent`。** 多视图在这里代表空间维度，不是时间维度。

建议：
1. **Stage A（冻结且可缓存）**：BEV/每个 room spatial view 的像素图经明确的 frozen encoder 变成 `spatial_view_latent`。可优先评估是否复用现有 Wan VAE 的 **T_pixel=1 / Encode1** 来编码静态空间图（需要独立 preprocess/canvas 和实际 parity Gate）；也可比较固定图像编码器的空间特征，但类别/高度/几何信息在压缩后是否保真需要验证。不能直接声称已有 G1 exact-window latent 能复用这些新图片。
2. **Stage B（训练期间必须保持可学习）**：独立 Global Spatial Encoder/Adapter 接收 L3 `spatial_view_latent`，再结合任务、Room/view 元数据、关系 Tokens，以有限的 Global 条件进入 Cosmos 动作路径。**如果 Stage B 有 trainable 参数，绝不能把它的输出在训练前缓存固定下来**，否则梯度无法按新参数更新。

必要时 Stage A 可以只提供冻结的低级空间特征，Stage B 再学习时空与任务关联。必须验证 Stage A 是否保留足够语义、像素位置信息及重要物体状态；不能仅因为已缓存而假定对 Cosmos 有用。

L3 数值 dtype 与压缩方式以 Gate 结果决定；可考虑 fp16/bf16 存储减少 I/O，但不能未经实测把现有 fp32 视觉 ABI 改成新 dtype，也不能仅靠张量 shape 推断其语义。

## 6. 与 G1 训练窗口/缓存的一致绑定（PROPOSED）

现有 V3 的 accepted cache catalog 是训练 corpus membership authority，Phase1B/3 以 `(episode key, start=t)` 绑定 raw source，保持 `window_frame_indices`、`latent_source_frame_indices`、`cache_corpus_digest`、`source_binding_digest` 等 exact identity。

新增 G2 必须建立**独立 spatial cache catalog/index** 并对 G1 已接受的样本键做严格覆盖验证，不能因为 G2 cache 缺图而静默缩小现有训练集、隐式在线生成或回退到别的 Episode。

```text
G1 accepted (task/shard/episode, start_frame=t)
  + current vision VAE cache (existing, exact 17-frame)
  + G2 spatial_state/relations at SOURCE frame t
  + spatial_views_l3[(episode,t,view_spec)]
  => one canonical training sample
```

- `t` 对应**动作决策时刻的当前环境状态**，不是 window 末端 `t+16`；对 Local-TTT 每帧消费还应按其实际已完成 observation/current latent 时序绑定，不能假定只有 replan 帧用空间信息。Consumer 类型与所需帧集合要在接线设计中冻结。
- G2 spatial cache 的帧集合只覆盖所需 consumer，但必须可对任意请求时刻准确映射；空状态变更时可多帧指向同一 blob。
- 新增 `spatial_latent` 独立 ABI（可变 view 数需 mask/slot），不修改现有 `video_latent` 的 rank、17 帧 window/监督含义或 Collate/Packing；具体 transport seam 待源码设计和 CPU parity Gate 冻结。
- 提供 `source_frame_index`、`state_version`、`view_config_digest`、`encoder_digest`、`view_latent_refs` 与形状/数值元数据；加载时 fail-closed，记录缺件、重复、错帧和资源预算。

## 7. 磁盘组织和吞吐策略（PROPOSED）

逻辑索引可以是 `(episode,t,view_spec) -> latent_ref`，底层不要为相同状态的 100 帧生成 100 个独立文件。可通过**内容寻址 blob + 分片块/索引**组织，具体 LMDB/Zarr/Arrow/Parquet+binary shard 等按集群实测确定，不预先锁定技术栈。

- 主图 L2 与 L3 使用独立 asset manifest，空间渲染 recipe、SceneTemplate/Overlay/Model、encoder checkpoint/hash、resize/pad、归一化、顺序、dtype 等必须不可变绑定。
- 读样本时仅进行 O(1) 左右的索引查找、小张量 gather、固定轻量 metadata 组装；不扫描 RoomPipeline，不读取 Mesh，不解码原始 GT 轨迹以重新算视图。
- 尽量把一个空间视图 bundle 的多个 view latent 顺序或近邻存放，减少 8 卡多进程随机读取压力；共享只读 cache，按需 memmap/prefetch，配合当前数据生产者/packing，不能因新 IO 并发破坏 G1 既有 Canonical producer 语义。
- 统计 unique `scene_state_version`、unique view render、unique L3 blob、帧复用率、磁盘大小、cache hit/miss、每 rank load latency、GPU 空转与 DataLoader 吞吐。判断优化收益以真实迭代吞吐而非仅文件大小为准。
- Offline 生成一组标准检查图供人眼核验：同 frame BEV/每方向与 GT SG/关系投影对齐；检查小物件移动、抽屉开关、容器内部和地图坐标，RGB/depth/关系一致。

## 8. 在线仿真与离线训练的不同执行要求（PROPOSED）

- **离线训练**：必须 L3 cache hit；无动态 GT restore/render/frozen encode fallback。Cache 不匹配直接失败，遵守现有 cache-first 风格。
- **在线 SR 评测**：动作后环境是真实 rollout 的当前状态。Full+GT 从当前 simulator state 获得最新 SG，使用**与离线相同的 spatial renderer + frozen encoder**；若同一视图版本未变化，复用上一 latent；变化时增量渲染/Encode1。不能把专家离线 `(episode,t)` 的空间 latent 作为当前 rollout 同步状态，因为两条轨迹可能在同一 t 已不同。
- **后续 nav_sg 感知维护**：仅替换 PSS 生成来源，下游 renderer、encoder、Global Reader 尽量不变；未知未观测空间与 Full-GT 真值区别不能用同样的可见内容伪装。

在线渲染与冻结编码可能影响推理时延，需单独测量；离线缓存带来的训练吞吐提升不能被当作在线推理免费。合理的实际系统可进一步约束视图变更频率、增量局部更新与 inference cache，但不允许把过期状态无标记地送入策略。

## 9. 讨论顺序与最小验证 Gate（NOT_RUN）

建议先确定 **(1) BEV 坐标系与对象语义编码、(2) 房间多方向 vs 工程三视图的定义与是否需要、(3) 冻结视觉编码器选择、(4) 数据加载与模型 ABI**。在此之前不应全数据集生成所有候选缓存。

第一轮只选一个已验证 RoboCasa Episode，构造 L0/L1 时序状态，从合法状态序列生成 BEV + 两种多视图的小样本，不训练，检查对齐、稳定段缓存复用、移动段版本变化、隐藏关系未失真、视图是否确实增加高度/结构信息、冻结编码后的关键信息保留。

确认选型后，按 G1 accepted cache corpus 做覆盖检查、批量 L2、批量 L3、CPU DataLoader 严格索引核验；接入模型后验证一小批真实 cache hit，计算 VAE/编码器调用为零、梯度仍流向 Global 分支、Local 与视频监督未变，再进行正式训练与 SR 对照。以上均为建议，不能表述为已经实施通过。

## 10. 本轮设计决定摘要

- **CONFIRMED**：训练必须预存空间视图与对应的 latent，视图扩展也必须缓存，优先训练吞吐；同一环境状态复用缓存，时序索引要正确。
- **PROPOSED**：L0–L3 分层、固定坐标 BEV 与机器人状态分离、按 view 内容复用、Room directional / tri-planar 作为候选、frozen Stage A + trainable Stage B、严格 G1 identity join 与在线增量 encode。
- **OPEN**：最终采用哪些视图、语义/几何图层、空间分辨率和 K、Encoder 具体架构、数据 shards、耗时预算、Global 接线与哪些 Local consumer 需要 G2。
- **DEFERRED**：原机器人 Left 历史图库、Agent、Partial/Cold Start 具体配置。

未修改 V3 生产训练链路、现有 video_latent 资产或 nav_sg PR；未启动 cache builder。
