# PSM-WMA G2 详细设计 v0.1
## 空间记忆初始化、时序场景维护与历史视觉训练数据

- 日期：2026-11-06。
- 主仓/分支：`wxwy/psm_wma:V3`；感知建图组件：`wxwy/nav_sg:G2`。
- 文档状态：**工作草案，已确认决定与待确认建议分开列出**。不是 frozen/locked 设计，不是实现完成或训练启动授权。
- 本次授权范围：记录已讨论设计并继续讨论 Full Map + MuJoCo GT Update 的历史多角度/状态图像；不修改生产代码、Gitlink、数据缓存，不启动渲染、训练或仿真，不改现有 PR/生产任务。
- 上位背景：[G2 技术调研 v1.0](./PSM-WMA_G2_technical_survey_v1.0.md)。该调研保留历史比较；其“详细设计暂缓”以及“全部空间上下文必须由单 Episode nav_sg 冷启动生成”的范围，按本文中用户新确认决定更新。旧冻结 V3/Local-TTT 文档不静默改写。

## 0. 状态标记与范围

- `CONFIRMED`：用户已明确确认，后续设计应保留。
- `PROPOSED`：本稿为继续讨论给出的工程建议，不等于用户冻结或代码实现授权。
- `OPEN`：尚需确认、实测或与现有 Cosmos 接口对齐。
- `DEFERRED`：已记入需求，但本轮不展开。

当前优先回答：**假设场景结构与动态维护完全正确，给 Cosmos 提供完整空间记忆和历史视觉，能否改善动作策略？** 因而先推进 `Full Map + MuJoCo GT Update`，隔离检测/聚类/关联误差。nav_sg 的 YOLOE + RGB-D 建图仍有价值，作为冷启动和感知更新路径保留，不因启用 GT 路径而废弃。

G2 仍以 Cosmos 训练数据和动作条件为中心，Agent 后置。既有原始动作、时间戳、当前观测、Local-TTT 和已验证训练/评测契约不由本稿直接改动。

## 1. 两个独立维度（CONFIRMED）

### 1.1 四种初始记忆条件

| 初始化条件 | 含义 | 初始记忆来源与范围 |
|---|---|---|
| Full Map | 假设机器人已在同一场景长期运行、充分探索；遮挡/容器内部物品的身份和包含关系也可能已知 | 仿真阶段可从 MJCF、Mesh、初始状态、语义元数据生成完整结构与关系；这是明确的理想记忆条件 |
| Partial Map | 只探索部分区域/实体/关系，尚未达到 Full | 是无图/巡视冷启动的知识积累中间状态；可从 Full 数据源派生，但隐藏策略必须同时约束地图、关系与历史视觉 |
| Cold Start / Pre-scan | 没有旧记忆；允许先在房间游走、观察，但不移动/操作物品，再开始任务 | 扫描过程中同步构建地图与历史图像；不能透视封闭容器，不能把未见内部物品注入记忆 |
| Cold Start / Zero | 无旧地图、无旧图像记忆；直接开始任务 | 从当前及随后 Left RGB-D/语义观察逐步积累 |

Partial 与 Full 是覆盖程度，不是只能严格顺序进入的离散阶段；Pre-scan 是初始化历史的获取程序，所得地图可能仍只覆盖部分实体。不能只用单一覆盖率混淆空间覆盖、对象覆盖、关系覆盖与容器内部探索。

### 1.2 两种运行期间维护方法

| 更新方法 | 场景状态/关系变化来源 |
|---|---|
| MuJoCo GT Update | 仿真非机器人实体的真实几何、位姿、关节/状态和按明确判据派生的关系 |
| nav_sg Update | Left RGB-D + YOLOE/SigLIP + 原生对象关联/几何与关系维护 |

这不是给 Full Map 新增一个第五初始化条件，而是对四种初始化条件都可选择的维护轴。配置必须显式区分 `initial_memory_mode` 与 `update_backend`。

四种初始化 × 两种维护 = 八个可比较条件，**不意味着八个模型或本轮必须运行八组训练**。仿真按各条件分别报告 SR。混合训练比例、课程顺序、固定视觉 Token 数尚未冻结；此前 40/40/20 等建议不是决定。

`Full-Frozen` 只可作为后续可选消融，不是第三种主维护方法。本轮只处理 Full + GT；Full + nav_sg、Partial、Pre-scan、Zero 的具体实现依次后置。

### 1.3 GT 与知识边界（CONFIRMED / OPEN）

Full + GT 本来就是允许完整初始结构、隐藏物体关系及完美动态维护的特权信息实验，不必为了模拟真实探索而先运行整套感知系统。报告中必须明确这个假设，不能称为未经特权信息的真实机器人能力。

对 Partial/Cold + GT，需另行确认“新增已知对象”和“维护已知对象”各自的可见性范围，避免 GT 更新第一步直接把 Partial/Cold 填满。本轮记录此问题为 OPEN，不擅自冻结具体遮挡门槛。

任何条件都不能读取未来动作、未来状态、Episode 最终结果作为时刻 t 的输入。完美当前状态与未来答案泄漏是不同问题。

## 2. 统一时序场景与关系存储（CONFIRMED）

统一逻辑组成：

1. `SceneAssets`：固定资产、对象实例/部件、局部 Mesh/点云、类别来源、结构层级。
2. `InitialState`：Episode 初始非机器人对象位姿、门/抽屉等关节状态，以及初始关系。
3. `ObjectStateDeltas`：仅变化实体的状态增量；刚体几何不随每帧位姿复制。
4. `RelationEvents`：关系出现、解除、有效性改变；不把每次位姿变化当作关系拓扑变化。
5. `FrameStateIndex`：每帧指向可重建的场景状态版本和关系版本。
6. `CaptureStore + ObjectCaptureIndex`：历史图像和对象/关系的多对多关联。

场景图与关系存储可以分离。`inside(object, drawer)` 可只保留于 Relation Store，按需展示；“图上没有这条线”不能等同于系统不知道包含关系。

### 2.1 用户提出的十秒示例

- 0–5 秒仅机器人移动，非机器人状态未变化：各帧复用 S0。
- 5–7 秒操作物体：运动期间按训练帧率记录变化实体的位姿/关节增量，各帧指向对应版本；不复制全场景 Mesh 或完整关系表。
- 7–10 秒物体静止：复用最后稳定场景版本。

这是例子，不是硬编码时间窗口。实际依赖真实非机器人变化检测；被碰动的其他物体、关节变化、物理微振动/缓慢漂移也须有明确定义。阈值应以最终重建误差约束，并与上一次已记录状态比较，防止逐帧小变化累计漏记。

### 2.2 两个必须分开的变化时钟

**场景结构不变，不代表图像不变。** 机器人移动、相机位姿、手臂遮挡、阴影等都可能改变画面。因此 SceneState 版本去重与 Capture 关键帧筛选必须分开。

只监测非机器人实体足以决定场景结构版本的前提，是灯光/材质等外观配置固定且非几何状态已纳入合同；这不允许据此复用任意 RGB。RGB 缓存键还需要相机、渲染选项、机器人可见性与完整相关渲染状态。

`on/inside` 的建立/解除要有明确几何/接触/容器判据及容差，MuJoCo 的 body parent 不等于所有空间包含关系。抽屉关节带动内部物体的世界位姿变化，也不能漏记。细则 OPEN。

## 3. 当前 Full + GT 的训练数据目标（CONFIRMED）

- 从当前 Episode 对应的完整 MJCF、资产、初始 state 和语义元数据建立 S0；不能只依赖 task 名称、layout_id 或 style_id 把不同随机对象/布置的 Episode 当成同一地图。
- 建立所有非机器人实体的稳定实例 ID/部件映射；Geom/Body 数量不等于对象数量。元数据里泛化的 Accessory 类需要可审计的细类映射，缺失时不能伪装成完美类别。
- 从 Episode 时刻 t 的 GT 状态维护当前图/关系；动作标签保持原始轨迹定义，输入不得读 t 之后的内容。
- 历史多角度/状态图像作为空间记忆的视觉证据，供既有规划中的 Global Spatial Encoder/全局条件分支读取；不在本轮重新设计 Agent。
- 保留当前策略原有相机/视频配置。Left-only 是目前 nav_sg 建图的决定，不自动要求修改 Cosmos 原始 Left/Wrist 输入。

## 4. Full + GT 的历史图像：建议区分三种来源（PROPOSED）

### 4.1 初始多视角参考库：`initialization_reference`

恢复确切 S0，在同一场景状态下从不同虚拟相机视角渲染，作为 Full Map 假设下预先可用的视觉记忆。

- `available_from=0`；`source_state_ref=S0`。
- `capture_kind=initialization_reference`；`synthetic=true`；不是原录制机器人真实拍摄历史。
- 不需要为了得到这些图像，先驱动机器人完整巡游整个厨房；虚拟相机直接采样即可。无需证明每个视角之间存在一条已经执行的机器人轨迹。
- 但建议主版本相机位于可通行/可观察的空间，遵守不穿墙、不置于实体内部、真实遮挡和有意义的物体像素大小等条件，以免图像本身带来额外不必要的域差异。
- 不使用未来操作目标的位置、动作轨迹或成功结果决定初始相机/初始图片。

**这是一个仿真训练数据构造假设，不是还原真实过去发生过的事件。** 可把它当“长期运行后拥有的视觉参考库”的替身，但不能生成伪造的真实历史时间戳或连续运动视频。

### 4.2 容器/关节参考状态库：`prior_state_reference`

Full Map 可以知道关闭抽屉内有什么，但从关闭抽屉状态外部旋转相机不能拍到内部。建议在**独立副本**中设置可见状态（如打开抽屉/柜门），生成带原始出处的状态参考图。

- `source_state_ref=reference_state_r`，与当前主场景状态不同；记录 reference articulation、被改动实体、生成配方和可达/碰撞检验状态。
- 初始化已允许长期经验的 Full 模式下，可声明这些参考图 `available_from=0`，但标为合成的先验参考，不伪装为原轨迹某帧。
- 图像可用于物体外观、容器内部结构、被声明为参考状态的空间证据。不能凭“打开抽屉参考图”把当前主地图的 closed 状态改为 open。
- 不能只改 joint qpos 就假设内容物自动正确随动；需要检查物体相对容器变换、碰撞和物理一致性。临时参考状态构建失败时不伪造有效图。
- 若合法开门视角仍看不见某物，可保留 GT 结构/关系和 `visual_reference_missing`。可选生成独立物体外观图，但其用途只能是 appearance，不是当前场景位置/关系证据。
- 去墙、透明柜门、隐藏遮挡物、把相机放进封闭实体的“透视”图片不进入主参考图集合；若研究需要，只能作为单独标记的 oracle appearance 条件。

### 4.3 Episode 内真实观测：`episode_observation`

复用已存在的 Left RGB 帧及配套 Depth/K/Pose；按截至 t 的历史获取关键帧，而非另存所有相同图像。

- 这些是真实任务轨迹中的观察；`source_frame_index<=t`、`available_from<=t`。
- 机器人移动可新增视角，即使 SceneState 未变也可以新建 Capture。
- 物体移动/关节变化时，优先保留首次可见、接触/抓取改变、释放、稳定等关键时刻的有效画面。
- GT 每帧更新并不意味着每一帧都对所有对象重新渲染多视图。先用原始图像补充真实过程视觉。
- 若未来选择在任务时刻 t 从额外虚拟视角渲染当前状态，必须标为 `oracle_current_reference`，且在模拟评测中提供同等来源/频率；不能训练特权多视角、评测只给 Left 却声称输入条件一致。本轮不把这一扩展冻结为默认。

三种来源共用 Capture schema，但 provenance、可用时间和可表达的状态含义不能混淆。

## 5. 图像获取：共享场景视角优先，按覆盖缺口补拍（PROPOSED）

### 5.1 MuJoCo/robosuite 能力边界（外部资料核验）

MuJoCo 的抽象相机与渲染/模拟状态相分离，支持 free/tracking/fixed 等相机、离屏渲染和 RGB/深度读回；robosuite 支持 RGB、Depth、element/instance/class 分割输出。相机不是“每物体必须配置的一台永久物理设备”。可复用少量渲染上下文、逐个切换相机参数。[R1–R4]

实际实现必须以服务器已固定 MuJoCo/robosuite 版本做小样本验证，不升级仿真环境来迁就最新在线示例。完整相机 pose/fov 设置可以通过当前可用固定相机或底层相机接口实现；自由相机的 lookat/azimuth/elevation 并不等价于任意 roll 的 6DoF 相机。[R1]

### 5.2 候选相机与选择

第一版采用确定性的数据构建规则，不新训练视角选择模型、不扩展 Agent：

1. 根据已知场景 GT，按工作区/台面/炉具/柜体生成一组共享广角候选，覆盖环境上下文。
2. 用真实渲染的实例 mask 检查哪些对象被看见，以及像素面积、截断程度、观测方向等。
3. 仅对小物体、细长物体、遮挡区域或容器内部补充近景/俯视/斜视候选。
4. 同一对象至少保留可用图像，不强求所有对象同样数量；避免机械生成每物体一圈 360° 包含墙后无效视角。
5. 在预算内保留带来新对象、新方向或新状态信息的视图；相似视角用较清晰/较少截断者替代。

具体相机数量、半径、俯角、像素面积阈值及每样本 K 为 OPEN，先由固定 Episode 小样本决定，不把建议数字当成已验证最优设置。

### 5.3 不用 YOLOE 判断 Full-GT 参考图片里有哪些物体

对同一 state、camera 配置渲染 RGB + depth + element segmentation，把 `(objtype, geom_id)` 经已核验的 geom→body/part→semantic instance ID 映射合并，得到每个对象在图片中的 mask。MuJoCo geom ID 不是天然语义 Object ID，结构部件/visual geom/collision geom 的归属必须处理；不把简单名称前缀视作完备证明。[R2–R4]

一张图若同时含台面、烤面包机、按压瓶，它就是一个 Capture，由三个对象引用，而非生成三份 RGB。

可见像素数不等于可见表面积比例。基础版记录 `visible_pixels`、图像占比、bbox、边缘截断、对象相对相机方向与无遮挡的深度一致性；如需 `visible_fraction`，必须定义分母，例如同视角无其他遮挡时的投影像素或几何表面样本，不能随意用 mask/frame_area 冒充物体可见比例。

透明玻璃、细杆、反光/贴图以及几何分割与 RGB 可辨识程度不一致的情况须单独标注；拥有 GT mask 不代表 RGB 中一定清晰可识别。

### 5.4 历史语义与图像时间不可倒置

当前状态渲染成“旧相机视角”，仍是当前状态的图片，不是旧照片。历史图必须从它所引用的旧 state 恢复并渲染。禁止将 `latest_scene_state` 回填给所有历史 Capture。[R1–R3 提供状态/渲染机制；此处为本项目设计约束]

## 6. Capture 与 Object 的共享存储（CONFIRMED / PROPOSED FIELDS）

共享观察帧、多对象复用这一原则已确认；以下字段名为建议。

### 6.1 Capture 主表

```text
capture_id
scene_instance_id
capture_kind                  # initialization_reference / prior_state_reference / episode_observation
source_state_ref              # 主时序版本或独立 reference state
source_frame_index            # 原真实帧才有，不伪填
available_from                # 训练/评测允许读取的时刻
camera_pose_world, intrinsics, image_shape
rgb_asset_ref, depth_asset_ref, segmentation_asset_ref
render_recipe_hash, asset_manifest_hash, content_hash
robot_visibility_policy
```

### 6.2 多对多对象索引

```text
(capture_id, object_id, observed_object_state_ref)
mask_ref / bbox
visible_pixels, truncation, view_direction_in_object_frame
valid_scope                   # appearance / pose_at_capture / relation_at_capture / articulation_reference
source_kind, quality_flags
```

一张图片可以有多个 object-state 绑定。图像里物体 A 后来移动，不意味着 B、C 的旧外观证据都无效；应在对象关联/用途层判定适用性，而不是粗暴删除整张图，也不能把 A 的旧位置当作当前事实。

### 6.3 三层节省

1. **默认共享**：按 Capture 存一份原图；Object 表只存引用和 mask，不按物体复制完整 RGB。
2. **精确复用**：完整渲染键相同的结果复用；实际 RGB content hash 相同可共享底层 blob，但逻辑 Capture/状态/时间记录不能丢失。
3. **覆盖筛选**：近重复视角按质量/覆盖增益保留代表图；不因 RGB 接近就合并不同状态的打开/关闭、小物体位移或遮挡变化。

Crop 默认以 `(capture_id, crop_box/mask)` 表示，按需生成。若缓存视觉特征或 VAE latent，缓存键需绑定图像 hash、crop/preprocess、编码器/权重版本，不覆盖原视觉证据。

## 7. 地图逐帧，图像按事件/视角变化采集（PROPOSED）

位姿/关节增量是低维序列，可在变化期间逐帧维护；视觉参考库不要求在同频率拍全场景多视图。

在用户十秒示例中：

- 0–5 秒：S0 不变；初始化多视图复用。Left 观察因机器人移动而变化，可选新增关键帧。
- 5–7 秒：保存实际物体状态增量；用现有 Left 视频/Depth 为操作过程提供历史图像，保留事件前后与有新增可见性时的关键帧。
- 7–10 秒：复用稳定场景版本；原对象外观图仍可有用，但旧位姿/旧包含关系需标注时间。新状态视觉不足可标缺失，或在已单独声明的 GT 参考视图模式补渲染，不假装为 Left 真观测。

场景中的非机器人位置不变不能保证 RGB bitwise 不变：摄像机、机器人几何/阴影、灯光/材质也影响缓存。建议初始化参考库采用固定的 renderer/光照及明确机器人可见性配方；隐藏机器人若采用，只能在 reference view 标记，不能悄悄改变真实 Episode 图像。

## 8. Full-GT 参考图库的最小实例（PROPOSED）

以本会话已核实的 global 5077/local 36 为设计样例，用户人工确认任务为从抽屉取出打蛋器放到台面；详细数据身份以 existing Depth manifest 与 raw ep_meta 为准。

- `C_workarea`：台面中景，可能同时包含台面、烤面包机、刀架、按压瓶等；GT segmentation 决定实际出现的实例，不按文字列表强加图像内容。
- `C_shelf`：架板及杯子；多个杯子分别有 instance ID，但共享 RGB。
- `C_drawer`：在有可见内腔的当前 S0 或独立合法 reference articulation 下，包含抽屉和打蛋器。按 S0 还是参考状态分别标记。
- `C_stove`：炉具及部分邻近设施，按实际可见性建立索引。
- 移动后的 Left 真实帧、抓取前后、放置后的真实帧逐步进入 Episode history。

这些不是新的人工语义预测，不需要让 YOLOE 再验证 GT 对象名；却仍需要保证渲染与实例 mask 的几何绑定、当前/历史状态和可用时间一致。Full GT 可以拥有当前不可见对象及关系；有结构记忆并不强制每个对象都有无挡高分辨率照片。

## 9. 面向 Cosmos 的输入边界（CONFIRMED / OPEN）

初始化参考图库、关系存储和每帧状态版本属于 PSS 数据源；样本组装读取 `Memory(t)`：

```text
原始任务指令 + 当前原始观测/本体状态
+ 截至 t 的 Local history（既有契约不改）
+ 由 S_t/RelationStore 读出的 BEV/空间条件
+ 由 Capture/Object 索引选取的历史或参考 RGB 及必要元数据
-> 原始 action target / action chunk
```

- G2 既有方向为独立 Global Spatial Encoder/条件支路，不在此冻结新的网络结构、相机位置编码、Token 数、分辨率或 loss。
- 多角度图片是同一状态的不同 view，**不是**连续时间帧。不得把一圈虚拟相机视角当作真实运动视频直接塞入原生时间轴；如使用 video VAE/多图编码，必须定义 view/time 区分与 mask，避免制造不存在的动态。
- 存储库的照片数、每个对象索引照片数、单次 Cosmos 输入图片数是三个不同预算；训练输入不需要把全厨房图库每次全送入。
- 图像筛选属于 PSS 数据维护/读出，不另起复杂 Agent 或学习式视角筛选项目。具体检索权重/格式 OPEN。
- 不用将要执行动作的真值目标 ID、未来位姿或 Episode 成败挑选 t 时刻的图片；任务文字和当时已知状态可以作为合法查询条件。
- Segmentation/GT 类别可用于离线索引与监督，但不默认把带真值标签文字叠加的 RGB 作为策略视觉输入。是否直接输入深度/分割是单独网络实验，不由本稿自动新增。
- Episode 初始 Full 图与参考库必须在仿真评测时用相同 recipe 提供。评测后续状态来自实际 rollout，不来自原示教未来轨迹。结果只能解释为该信息条件下的 SR。
- 固定评测 seed/场景配置、policy、输入预算、更新频率等，用于分别比较初始化覆盖与维护误差；不把更多视觉 Token 的收益全归因于结构记忆。

## 10. 最小验证范围（PROPOSED；未启动）

第一轮只对一个已知 Episode 创建 Full-GT 数据契约/人工可审阅小样本，不全量渲染，不训练，不要求 Agent。

### 数据与时间检查

- S0 身份（model/asset/metadata/state）准确；初始渲染副本不改变主回放状态。
- 逐帧状态可从基图+增量重建；静止期间共享版本，移动/关节变化不遗漏。
- 历史 state、参考 state、当前 state 不混用；所有可用图像满足声明的 availability，未来删除测试不能改变较早样本。
- 全局关系 GT 与视觉证据独立标记；完整关系并非每条都必须画在 SG 中。

### 渲染与存储检查

- 同一 state/camera 的 RGB、metric depth、geom/instance mask 对齐；正确处理 renderer 深度单位/非线性转换、坐标系和背景无效值。
- 已确认的实例与 body/geom 合并稳定，不把碰撞几何、可视几何、机器人辅助 marker 当成独立厨房物品。
- 一张图的多个对象确实共用同一 RGB blob；不同状态版本不会因像素近似而错误合并。
- 关门参考图不能展示本不可见的内部；开门副本不改变主 SceneState。图像不足如实标记。
- 相机采样不依赖未来动作目标；检查相机与几何相交、近裁剪、物体像素太小等无效候选。

### 人工验收

查看真实实例分色点云/资产、场景/关系状态、图片的实例 mask、来源状态与多对象引用，判断初始 Full 图是否完整、时序状态是否正确、参考图片是否含合理上下文。该验收不能由测试数量替代；当前全部 Full-GT 实现/数据 Gate 为 NOT_RUN。

## 11. 后续条件与暂缓需求

### Partial / Pre-scan / Zero（已确认方向，实现后置）

Partial 需同步限制地图节点、关系和图片，否则删除对象节点却留下暴露其身份/位置的图片会破坏实验条件。优先按可见历史前缀或区域覆盖构造；具体方法未冻结。

Pre-scan 仅游走观察、不操作物体，同时积累图像；不能把打开容器的参考库无条件提供给此模式。Cold Zero 无旧记忆。

nav_sg 更新路径继续保留。当前感知前端点云过滤/语义误差是该支路的工程问题，不应阻塞理想 Full-GT 数据路径，也不因此把感知链路废弃。

### 物品被人移动（DEFERRED）

记录为后续“记忆过时/冲突/容错”需求。暂预留时间、来源、有效性、last_seen/last_confirmed、关联证据；**本轮不实现 Agent 主动验证、搜索、纠错或日常人类干扰策略**。

### 原生对象点云可视化（DEFERRED）

nav_sg 已有对象分色点云发布能力；后续补充原生结果导出与验收，不另造替代 ObjectMap3D 的点云构建器。本轮不因讨论图库而重跑感知数据。

## 12. 仍需讨论的选择（OPEN）

1. 是否采用“初始共享场景多视图 + 可见性补拍 + 容器参考状态 + 任务真实 Left 关键帧”作为第一版。
2. 抽屉/柜门状态参考图的允许状态、物理一致性与使用范围；appearance-only 物体图是否必要。
3. 单 Episode 参考图存储预算与每样本 K，分辨率及 patch/latent 读入方式。
4. GT 状态/关系变化容差与 keyframe 抽样规则；相机/机器人变化触发照片但不触发 SceneState 时的索引逻辑。
5. 其余初始化条件的 GT 更新可见性边界；训练混合比例和 SR 评测计划。

上述问题不要求本轮一次全部确定。当前只先收敛第 1–2 项。

## 13. 一手技术资料（仅支持 API 能力，不替代本项目验证）

- [R1] MuJoCo 3.2.3 Visualization：抽象/底层相机、离屏渲染、mjvScene/mjrContext；https://mujoco.readthedocs.io/en/3.2.3/programming/visualization.html
- [R2] MuJoCo 3.2.3 Simulation：mjModel/mjData、状态副本、模拟数据与恢复；https://mujoco.readthedocs.io/en/3.2.3/programming/simulation.html
- [R3] MuJoCo 3.2.3 API Types：geom/body/相机与状态类型；https://mujoco.readthedocs.io/en/3.2.3/APIreference/APItypes.html
- [R4] robosuite Renderers / Sensors / Environment：RGB/Depth/实例、类别、元素分割及相机参数；https://robosuite.ai/docs/modules/renderers.html ；https://robosuite.ai/docs/modules/sensors.html ；https://robosuite.ai/docs/simulation/environment.html

资料核查日期：2026-11-06。版本化 MuJoCo 页面用于约束 API 概念；本次没有核验服务器当前安装包版本或运行渲染。本稿中的流程、表结构和采样策略是设计，不是已交付功能。

## 14. 本次变更记录

- 首次建立 G2 独立详细设计工作草案，完整记录四种初始化、两种维护、Full+GT 优先、增量状态/关系版本、多对象共享 Capture、历史图像来源与待确认规则。
- 纠正把 Full-GT/Full-nav_sg 当新地图类型的旧表述；纠正把 GT 知识与未来泄漏混同的表述。
- 明确新提出的虚拟相机/容器状态/图库预算只是建议，未冻结或授权实施。
- 只发布文档和索引，不修改 G1/V3 生产代码、任何模型/数据、nav_sg PR #2/#4 或服务器任务。
