# PSM-WMA G2 详细设计

## 任务驱动的全局空间记忆、SG 语言增强与 Cosmos 联合条件注入

- **版本：** v2.0
- **日期：** 2026-11-16
- **状态：** 讨论收敛稿；已确认原则与推荐实现、未决项分别标记，非全量设计冻结。
- **适用范围：** PSM-WMA V3 / RoboCasa target-atomic。本稿的 G2 指全局空间记忆构建阶段，不指历史训练验收中同名的 Resume Gate。
- **交付边界：** 本文是设计文档，不表示相关代码已经实现、测试通过或获得训练启动授权。本轮不修改代码、数据集、Gitlink，不启动训练。
- **归档位置：** `wxwy/psm_wma` 的 `V3` 分支，`docs/build/PSM-WMA_G2_detailed_design_v2.0_2026-11-16.md`。本次仅归档设计文档，不变更生产代码、数据或 Gitlink。

---

## 目录

1. 目标、范围与总体结论
2. 决策状态与本会话修订
3. 现有系统与源码事实
4. 端到端架构和模块职责
5. 数据身份、时序与资产解析
6. 候选对象召回与未来 Agent 接口
7. 对象—视图索引及任务驱动选图
8. 多视图预处理与几何元数据
9. Global Spatial Encoder / Reader
10. SG 事实组织与增强语言指令
11. raw15、state15 与机器人定位
12. Cosmos 中的 Q/K/V 及 Local / Global 联合注入
13. 训练与部署缓存、更新和一致性
14. 数据接口、代码接线与伪代码
15. 分阶段实施与验收
16. 实验设计、风险与未决项
17. 单样本示例与讨论问题追踪
18. 固定版本来源

---

# 1. 目标、范围与总体结论

## 1.1 用人话说明本阶段要做什么

当前已经有一条产生全局场景视图和 Scene Graph（SG）的数据链。下一阶段的重点不是继续生成更多图片，而是解决：机器人执行一个具体子任务时，应该从场景记忆中读取什么、怎样读取，以及这些信息怎样真正影响动作。

当前 Atomic 指令可以看作未来 Agent 派发给底层策略的一条子命令。系统先根据子命令在 SG 中召回相关对象；同一份候选结果分成两路：一路提取可信事实，补充原始语言指令；另一路查找对象关联的空间视图，选出“必选俯视图＋候选对象关联的有效视图”。无关墙面和其他 Island 不进入本次 Global Reader，但它们仍属于完整场景记忆，继续保存和维护。

选中的图片先经过冻结图像编码器，产生可离线缓存的空间特征；再由可训练 Global Reader 结合方向、物理尺度、空间位置及任务语言，输出有限数量的 Global tokens。Global 与已有 Local-TTT 保持独立，只在 Cosmos 生成路径的 K/V 条件集合中汇合。当前观测和机器人 state 继续使用原生输入通路。

语言承担任务语义和可信场景事实；结构化几何承担确定的坐标与尺度；数字 state 承担快速变化的机器人状态。不能要求一段长文本替代全部地图、投影几何和机器人位姿，也不能仅因这些信息来自不同支路，就认为它们无法通过 attention 建立联系。

本阶段先证明这套机制是否有用。Agent 本体、复杂任务拆解、跨 Episode 学习、新动作条件世界模型、RSI 和完整真实部署不作为这一轮前置条件。未来 Agent 替换子任务来源，而尽量不改变下游检索、选图、Global Reader 和动作接口。

## 1.2 本阶段目标

| 目标 | 要达成的结果 |
|---|---|
| G-01 | 全局空间信息进入动作路径，可通过输入干预和闭环实验验证其作用。 |
| G-02 | 保持 G1 当前观测 latent、raw15 动作和 Local-TTT 因果语义。 |
| G-03 | 按任务相关对象选择视图，支持缺失方向和多个 Island，不固定输入 6＋4 张。 |
| G-04 | 离线训练读取预先准备的资产；部署根据生产端更新标识增量处理并复用缓存。 |
| G-05 | 明确区分 Full Map GT 特权信息与真实 nav_sg 感知信息，不将前者的效果表述成真实感知能力。 |

## 1.3 不做的事情

本轮不重写 nav_sg 物理场景图，不因挂图片而引入新的物理 Island 父节点，不恢复此前暂缓的细粒度容器/抽屉关系算法，不在训练中重做 1 mm、1° 或 2 Hz 更新判定，不把候选筛选器做成任务规划器，也不把可训练 Global Reader 的输出预先缓存固定。

历史 Left RGB 图库是后续可选路线，不是当前依赖。Local-TTT 的证据写入、长期状态累计和因果顺序先保持不变。完整地图不会因某张图在本次任务中未被读取而删除相关资产。

# 2. 决策状态与本会话修订

## 2.1 状态约定

- **C｜已确认：** 用户明确同意的原则或要求，后续实现须遵守。
- **P｜推荐方案：** 为落实原则提出的实现建议，尚未逐项冻结。
- **O｜未决项：** 编码前仍需明确的结构、参数或接口选择。
- **F｜源码事实：** 固定版本源码或本会话已检查产物中的实际行为。
- **D｜后置：** 当前不作为前置依赖。

**用户对一段内容的赞同，只覆盖该段明确表达的内容，不等于认可方案已完整，也不自动冻结未展开的细节。** 本稿中新 Schema、函数名和模块划分若未标为 F，均为拟议接口。

## 2.2 已确认决策

| 编号 | 决策 | 直接约束 |
|---|---|---|
| C01 | 首轮使用当前 RoboCasa target-atomic | 不把 Composite、Agent 本体或新 WM 混入首轮。 |
| C02 | Global 与 Local 是独立支路 | 原始证据不先拼接后共用同一个编码器。 |
| C03 | 全局信息必须进入动作路径 | 不能只用于可视化或旁路摘要。 |
| C04 | 训练优先读取预存图像与冻结特征 | 不在训练 step 内恢复仿真、跑 nav_sg 或重新渲染。 |
| C05 | 不存在的视图不输入 | 不读图、不跑 VAE、不生成有效 token；batch padding 仅为内部实现。 |
| C06 | 俯视图必选，其他图按候选对象关联读取 | 取有效视图并集并去重，不固定 10 图。 |
| C07 | 场景完整维护，模型读取可以稀疏 | 未选中不等于从地图删除。 |
| C08 | 首版按对象—视图归属选图 | 归属不等于可见；不因目标可见像素为零自动删图。 |
| C09 | 训练直接消费离线更新与引用结果 | 不再判断物体是否移动，不重新执行阈值规则。 |
| C10 | 动作继续使用 raw15 | 不改回 ego20，不改变既有动作解码和执行语义。 |
| C11 | 当前任务可视为未来 Agent 子命令 | 当前允许规则组织文本，保留 Agent 接口演进空间。 |
| C12 | 不变的语言和 view 计算应尽可能复用 | 缓存按真实依赖失效，不能复用过期条件。 |
| C13 | 原始任务保持完整，SG 只补充事实 | 不通过 oracle 指定唯一目标，不写入未来结果或虚构关系。 |
| C14 | 候选为空或关联不完整时有明确保底 | 无对象导航等正常情形可扩大到相关 Room；数据损坏不能被保底掩盖。 |

## 2.3 推荐但尚未整体冻结的内容

| 编号 | 推荐方向 | 未决边界 |
|---|---|---|
| P01 | state15 = 底盘 Pose5＋EEF10，保留 z | Pose5 表示方向已讨论；frame、归一化和训练/推理映射仍需确认。 |
| P02 | 等比缩放到 256×256 白色画布 | 编码器兼容性及小物体保真需验证。 |
| P03 | 将方向、分组、米制几何绑定对应 view 的 patch | 最小字段和具体编码方式待定。 |
| P04 | Global 在强压缩前或过程中使用任务语言 | Reader 结构、任务特征来源待定。 |
| P05 | 首轮保持 Local-TTT 算法不变 | 语言条件 Local 后置，避免混杂实验变量。 |
| P06 | 首轮保留俯视箭头，同时提供真实 state15 | 箭头必要性通过独立消融判断。 |
| P07 | Global 独立适配后作为 GEN 的 K/V-only prefix | 需要真实接线与数值、梯度验收。 |
| P08 | GT 标签召回与感知 embedding 召回统一候选输出 | 分数类型和阈值分别管理。 |

## 2.4 本会话修订

“所有视图全部输入”已被“俯视图＋候选对象关联视图”替代；固定 6＋4 槽位不再作为输入合同。raw15 已由用户明确，因此早先围绕 ego20 state 包装的旁支不进入本轮方案。

关于 1 mm 几何误差和 2 Hz 采样的解释，仅属于生产来源和诊断背景，不增加训练侧的重复更新判定。将 YOLOE 泛称为对象 embedding 来源的说法，纠正为 YOLOE 检测/分割、SigLIP2 编码和 ObjectMap3D 持续维护。

“把元数据写入文本”不是图像绑定的唯一方式；“在 projector 前做语言 attention”的关键，应理解为重要信息被有损压缩之前介入，而不是要求原始 VAE 通道直接与文本计算 attention。

# 3. 现有系统与源码事实

## 3.1 引用基准

| 工程 | 本稿引用的固定观察基准 |
|---|---|
| wxwy/psm_wma | `46fa72029faf1750b68aa3baae4e51d9b156f172` |
| wxwy/cosmos-framework | `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2` |
| wxwy/nav_sg | `70eb7b447e65` |

这些是本会话核对过的来源定位基准，不宣称为所有远端的实时最新 HEAD，更不是新 Global 已通过验证的 formal pair。源码引用见第 18 章。

正式工作目录为 `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3` 和同级 `nav_sg`；视图根为 `/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-6views`。本稿以用户“数据已准备好”的声明作为接线前提，没有重新统计全库完成率。

## 3.2 已有能力和缺口

| 领域 | 已有 F | 仍需实现 |
|---|---|---|
| 资产 | SG、有效方向图、Island 图、帧引用 | 与训练样本统一连接的 G2 catalog |
| 对象—视图 | renderer 的 `native_entity_ids`、Island 的 `member_entity_ids` | 保留到训练可读 sidecar 的反向索引 |
| 几何 | renderer 的参考系、投影方向、mpp、画幅信息 | compact 包缺失字段的定点补齐 |
| 语言 | 原始 caption、JSON formatter、tokenizer、服务端文本链 | 候选召回、可信事实整理和统一增强 |
| Local | Local-TTT 和 GEN K/V prefix | 扩展联合注入且保持原语义 |
| Global | 已有设计与空间资产 | 冻结特征缓存、Reader、adapter、训练/服务入口 |
| state15 | 当前为 5 个零＋EEF10 | 两端同步替换 Pose5 |
| 缓存 | 请求内 text-KV 和部分 Local 投影复用 | Global 缓存及必要的跨 replan 作用域 |

相关事实来源：[S04–S11]。不能因为图片已经生产，就声称空间特征缓存、Global 分支和闭环收益已经完成。

## 3.3 SG 能表达什么

当前 GT SG 包含实体标签/类别、Room 归属、BBox、BBox 中心、墙根关联、floor/upper 分组和 Island ID。这里的 `centroid` 按 BBox 上下界平均计算，不是质量质心或点云均值。[S05]

Room 的 `contains` 表示层级归属，不自动代表物品位于冰箱/抽屉内部；连接距离不等于接触或支撑；`floor_member` 不等于直接放在地板上。当前源明确标注 `semantic_on_inside = NOT_OBSERVABLE_FROM_SOURCE_BBOX`，不能据此自动生成 on/inside、开闭、抓持、任务完成等事实。[S05]

原生感知链有对象 SigLIP2 特征和代表性原型库；当前 Full Map GT 导出不会伪造视觉 embedding。两者需要统一接口，但必须保留来源区别。[S13–S15]

# 4. 端到端架构和模块职责

## 4.1 总体数据流

```text
原始 Atomic 指令 / 未来 Agent 子任务
                  |
           SG 候选对象召回
             /           \
            v             v
      可信事实提取     对象—视图索引
            |             |
      增强语言指令    俯视图＋关联有效图
            |             |
      Cosmos 文本    冻结视觉特征＋几何
            |             |
            |       任务条件 Global Reader
            |             |
            |       Global 独立 projector
            |             |
            +-------> Cosmos GEN <--------+
                         ^                |
                  当前观测＋state15    既有 Local-TTT
                         |
                   raw15 action chunk
                         |
                    执行 / 状态更新
```

对象召回和选图先于 Global Reader。Reader 可以使用稳定的原始子任务语义，不要求把整份数值 SG 再编码一遍。

## 4.2 职责隔离

**生产/地图层**决定对象、成员、图片和几何何时更新，并提供逻辑帧映射。训练不复制它的更新算法。

**读取/组织层**解析合法当前状态、召回候选、选择视图并整理事实。不承担动作规划，不运行模型来伪造事实。

**学习层**运行可训练 geometry/task adapter、Global Reader、projector 和策略训练，不跨 optimizer step 复用旧的可学习输出。

**服务/执行层**管理当前 rollout 状态、Session 隔离、缓存和请求一致性。不能读取专家未来轨迹的缓存冒充自身当前环境。

## 4.3 Local 与 Global 的分工

Local 按已完成历史证据持续更新；Global 对持续维护的空间场景做任务相关读取。“Global”描述空间覆盖与可访问的记忆，不意味着把所有历史帧输入模型，也不要求另做一个 TTT 写入器。

当前主干可以同时读语言和 Local，所以语言已经能影响动作如何使用 Local。让语言直接控制 Local 写入或读出，是另一项算法修改，首轮后置。

# 5. 数据身份、时序与资产解析

## 5.1 时间身份只在索引层处理

`t` 为当前策略决策帧；`s` 为选中的已生产空间状态帧；`r` 为实际落盘的 PNG/SG owner 帧。它们可以不同：t=16 使用 s=10 的状态，而图像因为未变化仍引用 r=0。

```text
(task, shard, episode, start_frame=t)
    -> spatial_state_id / source_frame=s
    -> resolved SG
    -> logical view IDs
    -> each image / frozen feature owner ref
```

训练不重新比较是否移动，也不重新做 1 mm 判定。若既有 catalog 未覆盖全部 G1 consumer，在离线准备阶段建立过去或当前的合法映射，例如最后一个 `source_frame <= t`；不四舍五入到未来。映射验证后，训练直接查表。

现有样例的 2 Hz 是生产事实，不在训练里再实现一套采样器。生产几何误差用于追溯，不成为每个训练 step 的新计算。

## 5.2 引用解析

PNG 复用 `resolve_indexed_png`，SG 复用 `resolve_scene_graph`。纯引用状态可以没有目录；不能据目录不存在判断样本不存在。PNG 和 SG 可以有不同 owner，必须分别解析，并保留逻辑当前状态身份。[S06]

## 5.3 与 G1 连接及错误分类

G1 accepted corpus / exact-window identity 继续决定样本范围。G2 按相同 key 和 start_frame 连接，不覆盖现有 `video_latent`，不更改原始 task 的 source-binding，不因缺件悄悄删掉样本。

| 情况 | 处理 |
|---|---|
| 某方向本来不存在 | 正常不输入。 |
| 有效图未被本次选择 | 正常不加载。 |
| manifest 声明存在但文件/特征缺失 | 数据错误，不当成不存在。 |
| 必选俯视图缺失 | 必需条件错误，不用白图替代。 |
| 配置显式关闭 Global | 明确执行基线/消融，不产生 Global token。 |

## 5.4 三层 ready

L2 ready 是图片和 SG 已生产；L3 ready 是选定冻结编码器的特征和索引就绪；Model ready 是 Loader、Reader、prefix、state、服务和 checkpoint 一致接通。不能将三者合并。

对于原生产摘要中的 `training_ready:false`，不能原地改成 true 冒充训练就绪。应以独立 G2 catalog/readiness 清单记录新增字段、来源和已通过的检查。

# 6. 候选对象召回与未来 Agent 接口

## 6.1 子任务接口

当前接收完整 Atomic 指令；未来 Agent 可以附加对象短语、source/target/reference 角色和 Room 范围。原文始终保留。解析有歧义时，保留多个候选和未知角色，不用成功判定器、隐藏 task target ID 或未来演示结果单选目标。

## 6.2 nav_sg 的复用边界

原生链为 YOLOE 检测/分割、SigLIP2 视觉/文本编码、ObjectMap3D 对象记忆。`object_nav_query_node._match_objects` 已有文本编码、cosine、relevancy 和排序；direct 模式可不调用 LLM。[S13–S14]

复用的是特征规范和检索机制，不能照搬全部导航过滤逻辑。例如结构物过滤可能排除 manipulation 所需的柜体/台面；原代码的部分 inside/on_top_of 筛选是启发式，不可升级成语言事实。

文本和对象视觉向量必须使用兼容的同一编码器/权重/归一化。同维度不代表同语义空间，不能直接拿 Cosmos AR hidden 与 SigLIP2 对象特征算 cosine。

## 6.3 GT 与感知两条路线

| 来源 | 首版方法 | 边界 |
|---|---|---|
| Full Map GT | 类别/标签、多词短语、受控别名；必要时冻结文本编码器做文本—文本召回 | 当前没有真实对象视觉 embedding，不冒充视觉 grounding。 |
| 真实感知 nav_sg | 查询文本与持久化 SigLIP2 对象视觉特征跨模态召回 | 阈值和分数语义需标定；不能保证复杂关系和否定都正确。 |

二者输出同一种 CandidateSet，但携带不同 `backend` 和 `score_type`。当前若需要外观消歧，可另加离线对象视觉特征，不作为首版必备。[S15]

## 6.4 推荐召回步骤

1. 提取多词实体短语，尽可能保留角色；不把 `blender lid` 简化成只匹配 `blender`。
2. 先规范标签，再受控别名，最后语义召回。
3. 对操作对象、目标位置和参考物分别检索，取候选并集。
4. 多实例保留原始 ID，不把最高相似度当唯一事实；低置信和未找到显式输出。
5. 对象移动时通常只更新几何/归属；名称 embedding 不必重算。对象新增、标签/特征变化或子任务变化时更新相关检索缓存。

例如“把杯子放到盘子旁边”至少需要杯子和盘子两个实体角色，不能只用整句一个向量保留排名第一的物体。

## 6.5 两次语言处理及 Global 语言来源

第一次处理原始子任务中的实体语义，用于 SG 召回；第二次将增强后的完整指令送入 Cosmos tokenizer / AR-UND 路径。两者用途与表示空间不同，不应强行合并。

若 Global Reader 使用任务向量，应明确来源。推荐优先评估复用已加载的冻结 SigLIP2 文本侧，对完整原始子任务计算稳定向量，再用 trainable adapter 条件化 queries。对象短语和整句可批量编码；这是本地计算，不是在线生成式 API，但也不能宣称必然只发生两个编码调用。

复用 Cosmos AR hidden 也是候选，不过会增加梯度、时序和缓存依赖。最终只选一条清楚的主路径，不默认叠加多个任务编码器。

# 7. 对象—视图索引及任务驱动选图

## 7.1 多对多派生索引

```text
object_id -> associated logical view_ids
view_id   -> member object_ids
```

一个对象可关联多图，一张图也可关联多对象。推荐作为与 SG 同版本的 sidecar；也可挂对象 `view_refs` 属性，但不修改 Building→Room→Object 物理层级。Island 仍是空间分组和独立视图资产集合。

## 7.2 索引从哪里来

优先复用 renderer 实际成员：Room 方向图依据墙根关联；Island 图依据当前岛成员；upper 图使用对应生产集合。已有 `native_entity_ids` 和 `member_entity_ids` 是基础。[S04]

本会话抽查的 compact 包只有 SG、图片和引用，不能假定已带完整 `view.json`。补齐顺序是：先检查保留的生产 manifest/审计元数据；仍缺失时，按同版本成员规则与当前 SG 做受控重建，并用少量样本核对 renderer 成员。

不能按图片文件名猜对象归属，也不能用新规则无声重算旧资产。优先补 sidecar，不默认重渲染全库；不能恢复的字段列为缺件。

## 7.3 选择公式

设 B 为必选俯视集合，C 为候选实体，A(o) 为对象关联图，E 为当前实际存在的图：

```text
V_selected = B union ((union over o in C of A(o)) intersect E)
```

单厨房主线通常只有一个必选 floor_top。多 Room 时，B 应依据真实资产组织确定。历史设计的共享 House top/up 与源码中的 room-scoped refs 需要在 catalog 显式映射，不能强行把所有场景写成同一个 `2+4R+4I` 公式。[S03–S04]

选图按逻辑 view ID 去重，规范顺序为俯视优先，其余按 Room、分组、方向排序。同一图被五个对象召回，只输入一次。PNG 内容相同但几何不同的逻辑视图，不能合并语义；底层冻结特征 blob 可以共享。

**没有 +X，就不读取 +X 图片、不运行其编码、不生成有效 token。** batch 内为对齐尺寸使用的 padding 必须被 mask 排除。

## 7.4 多 Island、完整图和预算

候选涉及哪个 Island，就加入其当前关联的有效方向图；无关 Island 不进入本次 Reader，完整资产仍保留。选中的是整张图，不能默认裁掉或抹除非候选物体。周边物体、障碍和背景保留为上下文，不默认新增目标高亮，更不能借 oracle 高亮。

N 张输入图、M 个有效 patch、K_global 个输出 token 是三个不同预算。首版优先保留全部关联图；若超预算，明确报告数量与覆盖，再讨论分组/分块，不静默删除某个 Island 或必要视角。

## 7.5 归属不等于可见

membership 表示对象属于该视图的渲染集合；visibility 表示最终存在可见像素。首版按 membership 筛选。杯子被柜门挡住时，柜门图仍可能有价值，不能因为杯子像素为零删图。

membership 改变时更新索引，即使 PNG 恰好没变；图片改变也不必意味着成员变更。两个版本分开管理。

## 7.6 保底和错误分流

无明确对象的导航、候选为空或候选没有可用关联图时，推荐保底“俯视＋相关 Room 有效图”，输出原因。多 Room 范围暂不冻结；单厨房按当前 Room。

声明存在的图丢失、必要坐标缺失或身份错配属于错误，不能用 fallback 掩盖。必选俯视缺失时停止该输入构造，不制造空白替代。显式 Global-off 基线单独处理。

# 8. 多视图预处理与几何元数据

## 8.1 预处理候选

每张图独立等比例缩放、居中填入 256×256 白色画布：`s=min(256/W,256/H)`。保存确定取整后的宽高、四边 padding 和有效矩形。不要多图拼贴，也不要把空间方向排列成视频时间轴。

569×326 原图约变为 256×147 有效区域。mask 根据预处理几何生成，不靠检测白色像素，因为墙面/台面也可能白色。完全 padding 的 patch 屏蔽；边缘 latent 的 VAE 感受野可能混合 padding，按固定规则检查。

256 是候选而非已验证最终尺寸，需检查编码器兼容和小物体/箭头保真。元数据不能恢复缩小后消失的视觉细节。

## 8.2 元数据最低内容

| 类别 | 字段 | 作用 |
|---|---|---|
| 类型 | view_type、direction、projection_kind | 类型/方向 embedding |
| 分组 | room_id、group_type、island_id | 索引、同组关系、分组几何 |
| 米制几何 | origin、right/up/forward axes、extent_u_m、extent_v_m | 图像位置、方向、真实宽高 |
| 栅格规范 | native W/H、mpp、pixel_center_rule | 精确像素/投影平面映射 |
| 图像变换 | resize shape、padding、valid rect | 恢复 patch 对应原图位置和有效性 |
| 版本 | geometry/membership/image versions | 缓存与来源；不默认输入神经网络 |

**真实物理宽、高必须包含。** 它们是投影画幅覆盖范围，不一定等于墙到墙尺寸或实体 BBox。W=569、mpp=0.01 时，完整像素单元覆盖宽约 5.69 m，而最左/最右像素中心相距约 5.68 m；实施时统一边界和中心规则。

## 8.3 如何与图像绑定

```text
X[i,p] = P_img(Z[i,p])
       + E_type(type_i)
       + F_geom(metric_geometry_i)
       + PE(patch_location_i_p)
```

各项投影到相同 Reader 维度。第 i 张图的全部 patch 携带第 i 张图的类型和几何，不要求模型从长文本中猜描述对应哪张图。

Room/Island 原始字符串 ID 用于索引，不具有跨场景固定物理含义。分组可用结构、同组 bias 或组几何表达；若采用样本内 group embedding，需明确可变组数、置换和容量。首版优先类型＋几何＋显式同组信息。

缩放/padding 常用于计算正确坐标与 mask，不必全部作为额外 token 输入。连续数值携带单位和固定归一化规范。必要字段缺失不能填零冒充已知原点。

## 8.4 投影几何的能力边界

```text
p_plane = origin + u_m * right_axis + v_m * up_axis
ray(lambda) = p_plane + lambda * forward_axis
```

没有深度的正交 RGB 像素只确定投影平面位置与一条射线，不能推出物体唯一三维坐标。每像素 XYZ 若需要，必须另有深度/几何证据，当前不强制新增。

只写“+X 视图”能说明类型，但不能说明画幅在哪里、多大、是否翻转、Island 怎样裁切。数字 state 要与地图精确对应，还需原点、方向、尺度以及一致的参考系。

## 8.5 时间字段与俯视箭头

版本/时间用于索引和缓存，默认不把递增 frame_id、绝对时间戳或每步 age 放入网络，否则静态条件也随时变化。需要陈旧程度时另设明确状态信号。

首轮保留现有箭头，并输入数字 Pose5。箭头是否被理解需要训练与干预验证，不是因为画上去就自然获得定位能力。检查缩放/编码后是否仍可辨认，以及箭头方向和数字 pose 是否一致。

箭头可能来自最近空间采样时刻，state 来自当前决策时刻。按既有生产合同消费，不重新判阈值；当前数字 state 是当前位姿来源，不能为追求表面对齐读取未来图。

将来去箭头应使用干净底图或正确重渲染，不能简单涂抹已覆盖像素后当成真实背景。

# 9. Global Spatial Encoder / Reader

## 9.1 两级编码

**Stage A：冻结，可缓存。** 每张空间图独立编码成带空间布局的 Z_i。Wan VAE 单帧 Encode1 是优先评估候选，不是已冻结结论。编码器权重、预处理、dtype 和输出布局共同形成 recipe；不能复用原 G1 latent 来代表新图片。[S16]

**Stage B：可训练。** 逐 patch 投影、元数据绑定、任务条件读取和压缩，输出有限的 Global tokens。Reader、geometry/task adapter、queries、projector 若可学习，就必须参与当前训练计算。

K_global 不等于图像数量，也不等于 K_local。patch 数及空间下采样根据真实编码输出测量，不能仅凭输入 256 猜 shape。

## 9.2 语言应在强压缩前或过程中介入

对象召回决定“哪些图值得看”；Reader 的任务条件决定“这些图中保留什么”。同一冰箱的开与关可能选中相同图，但重点和动作不同。

推荐最小候选：

```text
T_task = E_task(original_subtask)
Q_task = learned_queries + P_task(T_task)
G = Reader(Q=Q_task, K=X_selected, V=X_selected)
```

逐 patch projector 只是通道映射，不必然减少 patch 数，所以可以先投影再与语言交互。无需原始 VAE 通道直接对语言做 attention。真正要避免的是任务无关的过强压缩提前丢失细节，再期待后面语言恢复。

Global 在主干中是 K/V-only，没有 Query；其自身不会进入 Cosmos 后再读取语言更新。因此需要的任务相关性应在 Reader 内形成。

## 9.3 Reader 备选

| 方案 | 做法 | 取舍 |
|---|---|---|
| R-A | 任务 queries 直接读元数据绑定后的选中 patch | 推荐先评估，结构集中；M 大时计算增加。 |
| R-B | 每图先与语言交互，再跨图融合 | 更充分但更多模块，尚未证明必要。 |
| R-C | Room/Island 中间表征，再跨组读取 | 扩展大场景自然，但中间压缩可能丢细节。 |
| R-D | 无语言通用压缩，主干再融合语言 | 简单对照，可能遗漏任务相关局部信息。 |

R-A 是推荐起点，不是已批准实现。层数、K_global、D_global 与任务特征来源列为未决；不默认同时堆叠三种 Reader。

## 9.4 可变长度、mask 与预算

输入可使用 ragged packing 或 batch padding。不存在的图没有有效 token；padding 在 attention、池化、梯度统计中惰性，不能污染结果。不同样本的 patch 必须隔离。Global 明确关闭走缺席分支，全 mask 不得产生 NaN 或默认零图。

俯视必选不等于手工提高其注意力权重。图像数量和 patch 数影响容量分配，需要观察，不保证网络自然学到理想平衡。

令 M=sum(P_i)，纯 query-to-patch 交互量约随 K_global*M 增长；若加入全 patch self-attention，则还会有 M*M 项。主干额外 K/V 缓存可估算为：

```text
bytes ~= 2 * num_layers * K_global * kv_heads * head_dim * dtype_bytes
```

还需加入 CFG 分支、Session 并发及其他缓存。这是估算，不是实测显存。最终配置依据实际吞吐、延迟和显存决定。

# 10. SG 事实组织与增强语言指令

## 10.1 输入、输出与来源

输入为原始子任务、当前 resolved SG 和候选对象集合。输出同时包括可审计的事实列表与增强文本，由同一事实对象生成，避免文本无法追溯。

保留原始 `task` / `ai_caption` 身份。建议另建 `original_instruction`、`scene_context`、`augmented_instruction`，在原 source-binding 校验完成后再增强。不能为加入 G2 删除 source/policy caption 一致性断言。

## 10.2 事实白名单

| 可表达内容 | 必须保留的限制 |
|---|---|
| label、category、实例 ID | ID 是指代，不是唯一任务目标真值。 |
| Room/Island 归属 | Island 是资产分组，不是容器。 |
| BBox 中心/尺寸和参考系 | 不称作质心、接触点、抓取点。 |
| 有来源的关系和状态 | 不从距离直接推出 on/inside。 |
| 多候选、未找到、未知 | 不为语言流畅而删除歧义。 |

没有证据的开闭、抓持、容器内部、抽屉层级、成功与后续动作顺序，不进入增强文本。

## 10.3 通用组织，不逐任务手写行为

推荐统一字段/短句模板：原始目标＋相关对象事实＋必要的已证实关系和歧义。模板处理可变实体与属性，不给每个 task class 写动作流程。

```text
Task: Put the cup next to the plate.
Scene context (world frame; metres):
- cup_A: room=R0; bbox_center=(...); bbox_size=(...).
- cup_B: room=R0; bbox_center=(...); bbox_size=(...).
- plate_A: room=R0; bbox_center=(...); bbox_size=(...).
Ambiguity: cup_A and cup_B are both candidates.
```

这是格式示例，不是真实 Episode 标注。排序、数字精度和格式固定，不因字典遍历顺序或无关 SG hash 改变导致文本频繁更新。

自然语言流畅不是首版首要指标；可信、稳定和训练/服务一致更重要。未来 Agent 可提供结构化子任务，本层仍只补事实，不重新规划。

## 10.4 复用现有 formatter

当前链为 `task -> ai_caption -> ActionPromptJsonFormatter -> tokenizer -> text_token_ids`，服务端也有 JSON prompt 构造。formatter 可扩展，但服务端尚未自动传递 G2 上下文。[S11]

建议训练/推理共用同一事实构造和 prompt 函数。可评估复用 `relabel_prompt` 的扩展位置，但只写专用 scene_context，不覆盖原 description，不引入未来 next/grip 标签。具体字段名在接口冻结时确定。

先保留完整原任务，再按预算组织事实；不能依赖 tokenizer 末尾截断兜底。若需省略，记录对象/字段及原因。候选放不下时扩大预算或明确裁剪策略，不声称全部上下文都已提供。

## 10.5 快速位姿不放进慢变文本

默认不每步将底盘 x/y/yaw 写进 prompt，也不把所有物体位置改成“机器人左前方”等随运动变化的句子。稳定 world/scene 几何写入事实，快速 pose 通过 state15。

原任务包含相对方向时保留原句，只有明确参考系后才解析，不能把任意“左”自动解释为世界轴或机器人轴。

# 11. raw15、state15 与机器人定位

## 11.1 动作不改，state 维度保持 15

raw15 是当前项目 canonical 15D 动作：底层原始 action 前五项，加 EEF10 编码。仿真器底层原始数组与 canonical raw15 的维度不同，既有转换保持不变。[S10]

| 索引 | raw15 action | 推荐 state15 |
|---|---|---|
| 0:3 | base motion 前三项控制量 | 底盘 x、y、z |
| 3 | base motion 第四项控制量 | sin(yaw) |
| 4 | control_mode | cos(yaw) |
| 5:8 | 末端平移增量 | 现有末端位置 |
| 8:14 | 末端旋转增量 rot6d | 现有末端姿态 rot6d |
| 14 | gripper 动作 | 现有 gripper 状态 |

state15 = Pose5＋EEF10；保留 z。两者同维度只是沿用输入包装，不要求同一槽位有相同物理语义。预测动作、动作归一化/解码和执行接口不改。

## 11.2 当前零填充与需改入口

当前 exact-window policy adapter 明确构造 `zeros(5)+state10`；服务端按有效动作宽度校验 state，并将其放在 clean action 条件行。[S10–S11]

必须同步修改训练 exact-window 路径、相关适配器、在线状态构造和服务校验，不只改某个 Dataset。旧 checkpoint 在零填充分布下训练，推理时直接换真实底盘值不能算完成适配；需新 state 条件训练。G2 warm-start 和严格 same-job resume 分开。

## 11.3 原始 state 到 Pose5

源码将 `observation.state` 解释为 16 维：base position `[0:3]`、base quaternion xyzw `[3:7]`、base-relative EEF position `[7:10]`、EEF quaternion xyzw `[10:14]`、两指关节位置 `[14:16]`。state15 不是截断原数组：base 转为 Pose5，末端 quaternion 转 rot6d，夹爪沿用已有汇总。[S10]

原始 base frame 与箭头使用的 `mobilebase0_wheeled_base` 是否相同，需要核查。箭头的物理前方使用 body local +X，不能拿移动关节轴代替。[S12]

如源 state 是另一个锚点：

```text
T_world_chassis = T_world_source * T_source_chassis
forward_world = R_world_chassis * [1,0,0]
yaw = atan2(forward_world_y, forward_world_x)
Pose5 = [x,y,z,sin(yaw),cos(yaw)]
```

用少量真实帧核对数字 pose、renderer 投影和箭头，然后固定 Pose5Builder。坐标单位、quaternion 顺序、yaw 正方向、归一化由同一 recipe 管理。

## 11.4 为什么视图名称不足以对齐

两个 Room 的 +X 图方向相同，但原点、裁切范围和尺度不同。同一世界坐标的机器人在两张图中的位置不同。Island 图还可能按自身 BBox 裁切。因此只写 +X 不够，必须提供数值投影几何或先统一转换。

world/scene 与 room 参考系仍待选择。推荐从稳定 scene/world 米制坐标评估；若转到 Room，state 和全部 view 几何一起变换，且多 Room 的参考选择不能无声跳变。不要对每个 Island 独立归一化却不提供实际尺度。

## 11.5 state 怎样与地图融合

state token 在 GEN 产生 Query，可读语言、当前视觉、Global 和 Local；动作 tokens 也可读 state。多层交互后，动作 Query 受当前位姿影响，从同一地图 K/V 读取不同内容。独立输入不等于割裂。

空间坐标一致只是让问题可学习，不保证 Transformer 自动掌握精确变换。箭头提供辅助直接对应，首轮保留；必要性通过消融判断。

默认不让快速 pose 进入 Global Reader，避免机器人每移动一步就使全部 Global 输出失效；快速 state 与慢地图先在主干融合。带箭头俯视本身仍可能随移动更新，不能将它当纯静态图。

## 11.6 state projector

优先评估沿用 clean action token / action2llm；已有条件位置可区分 state 与待生成动作。若绝对位姿和动作控制共享投影出现可复核问题，再比较独立 state projector。无论选哪种，外部 state 保持 15 维，不因此改变 raw15。

# 12. Cosmos 中的 Q/K/V 及 Local / Global 联合注入

## 12.1 当前路径

本节以固定版本、普通 two_way WAM 为准，不推广到所有 Cosmos 模式。

语言经 tokenizer/embedding 进入 UND causal 流；当前视觉、state 和正在去噪的视频/动作进入 GEN。clean condition 表示给定输入且不承担对应生成目标损失，不表示内部 hidden 不再变化。[S08]

Local 是外部 K/V-only prefix，经过独立 local_memory2llm 和模态 embedding；每层使用该层 GEN K/V 投影与归一化，但没有 Local Query，也不在主干逐层读取语言后更新自己。[S07–S08]

## 12.2 读取权限

| Query 来源 | 语言 | 当前视觉/state | 去噪视频/动作 | Local | Global（新增） |
|---|---|---|---|---|---|
| 语言 UND | 因果 | 否 | 否 | 否 | 否 |
| 当前视觉 GEN | 是 | 是 | 是 | 是 | 是 |
| 当前 state GEN | 是 | 是 | 是 | 是 | 是 |
| 动作/视频 GEN | 是 | 是 | 是 | 是 | 是 |
| Local prefix | 无 Query | 无 Query | 无 Query | 无 Query | 无 Query |
| Global prefix | 无 Query | 无 Query | 无 Query | 无 Query | 无 Query |

读取去噪变量不是读取未来真实执行结果。训练的未来 target latent 不得作为 Global evidence。

## 12.3 联合组装

```text
M_G = global_projector(G) + global_modality_embedding
M_L = local_projector(L)  + local_modality_embedding

K_read = [K_Global ; K_Local ; K_Text ; K_NativeGEN]
V_read = [V_Global ; V_Local ; V_Text ; V_NativeGEN]
O_GEN  = softmax(Q_GEN * K_read^T / sqrt(d)) * V_read
O_UND  = causal_attention(Q_Text, K_Text, V_Text)
```

各层按既有 GEN 机制产生 K/V，沿 token 维组合，不是拼宽 feature 通道。公式按信息类别解释，不承诺 PackedSequence 的物理内存布局完全相同。Global→Local 顺序固定，原生文本/GEN 位置编码和索引按原机制保持。

独立性体现在证据、Reader、adapter、模态和状态管理；投影后可复用本层 GEN K/V 参数，不必另造整套 attention 头。Global/Local 不加扩散噪声，不作为重建目标，不承担新的动作监督损失。prefix 放在前面也不会自动获得空间坐标含义，几何应先在 Reader 中编码。

## 12.4 不能只扩大 K_local

当前 MemoryPrefixContext、缓存检查仍有 Local-only 长度、presence 和形状假设。不能把 Global 直接拼进 Local tensor 冒充更大的 K_local。

明确每样本 Global/Local 是否存在、各自长度、总 offsets。覆盖 none、local-only、global-only、both 及同 batch 混合；不跨样本串读；关闭 Global 不留下零 prefix，也不改变原 Local 结果。

训练、服务、CFG 和 prefix cache 中的固定长度假设一起检查。既有不支持的 context parallel、CUDA graph、multiview 等路径保持原边界，不能因添加 Global 默认开放。

## 12.5 两次语言融合的分工

Reader 中任务条件决定“压缩保留什么”；主干 GEN attention 决定“据此如何行动”。Global prefix 无 Query，不会进入主干后主动读取 view 描述。

若采用文字描述 view 元数据，也要有明确 view identity，并在压缩前交给 Reader。结构化几何可以直接绑定 patch，不必全部写进语言。

## 12.6 参数和 checkpoint

Reader、geometry/task adapter、learned queries、Global projector、modality embedding 应注册为正式模块，进入优化器、FSDP 和 checkpoint，不藏在 Dataset 或临时对象中。

G1 warm-start 是新增结构初始化，不是 same-job resume。新 checkpoint 记录开关、encoder identity、Reader 架构、Pose5 recipe、prompt 模板和索引版本。G2-off 保留旧输入和恢复语义。

# 13. 训练与部署缓存、更新和一致性

## 13.1 更新由 producer 决定

离线使用 manifest 实体文件/引用和逻辑状态；部署使用 nav_sg / renderer 的对象、成员、视图和几何更新标识。训练不重算位移、角度、遮挡或阈值。

引用说明资产内容可复用，但不能成为所有缓存唯一依据：任务切换、选图集合改变、投影几何变化，即使 PNG 不变也可能需要重算 Reader。

## 13.2 缓存依赖

| 缓存 | 关键依赖 | 失效事件 |
|---|---|---|
| 冻结视觉特征 | 图片内容、encoder、preprocess、dtype | 图更新或编码 recipe 改变 |
| 文本/对象检索向量 | 文本/对象特征、encoder identity | 指令、标签或特征变化 |
| 候选集合 | 查询、对象集合/特征和限制 | 对象加入/移除或查询变化 |
| 选图 | candidates、membership、有效图集合 | 关联或图存在性变化 |
| 场景文本 | 选用事实、模板、数字格式 | 实际文本内容变化 |
| 语言逐层 K/V | 最终 token、模型/位置/CFG recipe | 文本或相关配置变化 |
| Global Reader 输出 | 有序视图、特征、几何、任务、Reader 参数 | 任一依赖变化 |
| Global 逐层 K/V | Global 输出、主干相关参数/精度 | 输入或模型变化 |
| Local prefix | 已完成历史状态及 Local 参数 | 遵守既有 Local 推进机制 |

不要把 request_id、递增 frame_id、raw SG hash 放进所有内容缓存键。它们用于追溯，未必是计算输入；反之也不能只看“全是引用”而忽略任务变化。

## 13.3 训练缓存边界

冻结图像特征、确定性元数据、候选/事实文本和 token IDs 可以离线准备。可训练 Reader、projector 和 K/V 投影每步按当前参数计算，保留梯度。

同图被多样本使用不等于可复用上个 optimizer step 的 trainable 输出；同一步内共享计算也要考虑 dropout 和图生命周期，首版不为此增加复杂路径。语言网络只有完全冻结且计算确定时才可评估深层缓存。

## 13.4 推理缓存边界

缓存 K/V 仍然需要新的 Query 计算 attention：

```text
O_t = Attention(Q_t, K_cached, V_cached)
```

机器人移动后 state/观测/动作 Query 改变，可从同一地图 K/V 读出不同结果，不必重算静态文本。

当前视觉/state 深层 hidden 在 GEN 中受去噪变量影响，不能仅凭 clean 输入没变缓存其所有层 K/V。独立 Global Reader＋K/V-only prefix 不被快速 GEN 状态反向改写。[S08]

现有实现主要为请求内 text-KV/prefix 复用，请求结束清理；跨 replan/Session 缓存是新增实现，需要容量、身份与失效管理，不能宣称已有。[S09]

## 13.5 更新事件

| 事件 | 应更新 | 可保留 |
|---|---|---|
| 只移动机器人 | state15；按 producer 标识更新俯视箭头图；联合 Reader 可能重算 | 其他冻结图特征、稳定 prompt |
| 相关物体移动 | 受影响图/几何/事实；归属变化则重选图 | 无变化视图特征 |
| 无关物体移动 | 完整地图仍维护；若改变选中整图则更新其特征 | 与模型输入依赖无关的计算 |
| 子任务切换 | 候选、选图、任务向量、最终文本、对应 Reader/KV | 不变图片的冻结特征 |
| PNG 不变但成员/几何改变 | 选图或 Reader/KV | 该图片冻结特征 |

带箭头 floor_top 随机器人变化，不能等同纯静态底图。首先使用已有标识，后续再决定是否分离底图和箭头。

## 13.6 请求一致性与 rollout

一个 action chunk 的多步去噪固定同一份任务、SG、视图、几何、Global 和 Local snapshot；新地图版本下一次 replan 生效。

新条件进入请求 identity/retry hash。失败重试、结束和 reset 不串用 Episode/Session。在线 rollout 只能读自身当前环境，不按同一 t 去读专家轨迹缓存。

## 13.7 CFG 与任务条件

文本 dropout/CFG 时明确 Global 任务向量是否一起变为空条件，否则“无语言”分支仍通过 Global 获取任务文本。可保持场景图但去掉 task query，或采用显式联合 dropout，具体待定。

选图本身也依赖任务；即使任务向量置空，仍可能保留选择信息。这可定义为“去掉文本条件”的 CFG，但不能称完全无任务条件。是否改变选图是另一项设计，不默默混用。

cond/uncond 的文本 K/V、Reader 输出和 prefix cache 分开。guidance=1 的功能 smoke 不替代 CFG 验证。

# 14. 数据接口、代码接线与伪代码

## 14.1 总则

以下结构和路径为拟议接口。实现可调整文件拆分，但保留语义；离线与在线共用读取/选图/事实/Pose5 逻辑，SourceAdapter 分别提供数据。

运行对象携带 Episode/Session 身份，资产携带来源与 recipe。继续使用已有 Episode 内路径校验，不通过新字段开放任意文件读取。

## 14.2 核心结构

| 结构 | 必要内容 |
|---|---|
| SubtaskSpec | task_id、original_text、可选 entity_queries/roles、来源 |
| SpatialBinding | episode_key、decision_frame、spatial_state_id、source_frame、source_mode |
| CandidateSet | entity_id、role、query、backend、score_type、score、validity |
| ViewAsset | logical_view_id、type/group、exists、image/feature refs、geometry、版本 |
| ObjectViewIndex | object_to_views、view_to_objects、membership_version、source_recipe |
| GlobalSelection | selected IDs、mandatory IDs、candidate IDs、selection_reason |
| SceneContext | 原任务、事实、歧义、最终文本及 recipe/hash |
| PolicyCondition | 原生观测、state15、文本、Global 输入、Local 既有私有入口 |

## 14.3 机器可读示例

以下字段形状用于讨论，实体和数值是示例；`pending_*` 不能进入正式训练。

```json
{
  "schema": "g2_policy_context_v1",
  "source_mode": "full_map_gt",
  "episode_key": "example_episode",
  "decision_frame": 16,
  "spatial_state_id": 1,
  "source_frame": 10,
  "task": {
    "id": "subtask_0",
    "original_text": "Put the cup next to the plate."
  },
  "candidates": [
    {"entity_id": "cup_A", "role": "source", "backend": "gt_label"},
    {"entity_id": "plate_A", "role": "reference", "backend": "gt_label"}
  ],
  "selected_view_ids": [
    "room:R0:floor_top",
    "room:R0:island:I0:plus_X",
    "room:R0:island:I0:minus_X"
  ],
  "mandatory_view_ids": ["room:R0:floor_top"],
  "selection_reason": "OBJECT_VIEW_UNION",
  "pose_recipe": "pending_pose5_recipe",
  "global_recipe": "pending_global_recipe",
  "original_instruction_preserved": true
}
```

源模式在新接口中可规范化，但同时保留 producer 原始模式及来源映射；不将 GT 和 perception 合并成无差别来源。

```text
view_geometry:
  reference_frame_id
  origin_xyz_m
  right_axis_xyz, up_axis_xyz, forward_axis_xyz
  extent_u_m, extent_v_m
  native_width_px, native_height_px, meters_per_pixel
  pixel_center_rule
  resize_width_px, resize_height_px
  pad_left_px, pad_top_px, pad_right_px, pad_bottom_px
  geometry_version
```

逻辑 view ID 稳定、版本更新；不同 view 可共享 feature blob，但保留各自 geometry。引用哈希与语义身份分开。

## 14.4 伪代码

```python
# 设计伪代码，不代表这些函数已经存在。
def build_context(sample_key, subtask, source, recipes):
    binding = source.lookup_binding(sample_key)
    sg = source.resolve_scene_graph(binding)
    views = source.resolve_view_catalog(binding)
    membership = source.resolve_object_view_index(binding)
    assert_same_episode(binding, sg, views, membership)
    assert binding.source_frame <= sample_key.decision_frame

    queries = parse_or_accept_entity_queries(subtask)
    candidates = retrieve_candidates(queries, sg, recipes.retrieval)
    selected = select_related_views(candidates, views, membership)
    if selected.needs_fallback:
        selected = select_room_fallback(binding, views, selected.reason)
    selected = add_required_floor_top(selected, views)
    selected = dedupe_and_canonical_order(selected)
    validate_required_assets(selected)

    facts = extract_supported_facts(sg, candidates)
    prompt = format_scene_context(subtask.original_text, facts)
    pose5 = build_pose5(source.current_robot_state(sample_key), recipes.pose)
    state15 = concat(pose5, source.existing_eef10(sample_key))
    return Context(
        binding=binding, candidates=candidates, selected=selected,
        original_subtask=subtask.original_text,
        prompt=prompt, state15=state15,
    )


def forward_global(context, frozen_store, model):
    # 训练要求冻结特征命中，不能隐式运行 renderer/nav_sg/VAE。
    features = frozen_store.gather(context.selected.feature_refs)
    x = model.bind_view_metadata(features, context.selected.geometry)
    task = model.encode_task(context.original_subtask)
    return model.global_reader(x, task)  # 可训练，保留梯度
```

固定示教指令推荐离线构建 context catalog，训练 Loader 直接查表，避免每 step 重新编码检索文本、解析整个 SG。在线按依赖变化调用同一语义逻辑。

训练 state 来自当前样本，在线来自自身当前观测；训练 feature store 禁止隐式编码 fallback，在线则允许按更新标识编码变化的选中图。

## 14.5 开关与配置

| 域 | 关键配置 |
|---|---|
| Global | enabled、reader_kind、k_global、global_dim |
| 选图 | object_view_union、require_floor_top=true |
| 文本 | sg_text_enabled、template_version、token_budget |
| 状态 | base_pose_enabled、pose_frame、pose_recipe |
| 编码 | encoder ID、weights digest、preprocess digest、dtype |
| 检索 | backend、encoder identity、alias/threshold recipe |
| 缓存 | 训练 cache_required、request cache、session cache |
| 诊断 | selection reasons、cache metrics、context audit |

不使用一个 `g2=True` 无差别打开所有变量。未测的 K/维度/阈值不伪设为已批准默认。

## 14.6 模块与复用入口

| 层 | 拟议模块 | 复用/修改位置 |
|---|---|---|
| 根仓 g2 | context/schema、resolve | 原 SG/PNG resolver、accepted sample key |
| 根仓 g2 | object_view_index | renderer members 和 Island 成员 |
| 根仓 g2 | retrieval、selection | nav_sg 语义编码/检索，不照搬行为启发式 |
| 根仓 g2 | prompt、pose | 原 caption、EEF10、箭头参考系 |
| 离线工具 | build_global_feature_cache | 图片和内容 hash，不重新渲染 |
| Cosmos 模型 | global_spatial、联合 prefix carrier | memory_prefix、network、unified_mot、attention |
| Cosmos 数据 | G2 adapter/collate | exact-window SFT、Local canonical producer |
| Cosmos 服务 | G2 request/context adapter | policy server、session/batch transactions |
| 配置/保存 | Global/Pose5 recipe | FSDP/optimizer 参数注册、DCP |

两仓均有 g2 包，继续隔离 import origin，不将两根目录混入同一个 PYTHONPATH。

## 14.7 服务 API

现有 transaction payload 字段集合严格，新字段需要版本化接入，客户端不能直接任意附加。把新上下文纳入 identity、幂等和重试校验，保留 raw15/state15 和 Local 协议。

具体传图片、冻结特征还是可信 context 引用依部署拓扑决定；不能默认客户端共享服务端路径，也不能把大张量转 JSON 塞进现有小请求。

# 15. 分阶段实施与验收

## 15.1 实施原则

先关闭影响正确性的少数设计项，做最小垂直切片。每步产出可检查结果，不把文档批准当运行通过，不把 CPU shape 测试当闭环收益。下面是待执行计划，本轮未启动。

## 15.2 六个批次

| 批次 | 具体动作 | 交付物 | 完成判据 |
|---|---|---|---|
| A 数据接口 | 检查样例 refs、成员、几何和 pose 来源，定位缺失字段 | 字段覆盖表、单样本 context、坐标对照 | 可直接读取范围与缺件来源明确，不猜测。 |
| B 语义读取 | 共享 schema、召回、索引、选图、事实模板、Pose5Builder | 增强文本＋选图名单/原因＋state15 | 俯视必选、并集去重、歧义保留、两端同构。 |
| C 冻结编码 | 确认 encoder/preprocess，少量保真检查，生成独立 feature catalog | recipe、parity/保真证据、L3 索引 | 内容复用正确，训练 cache-only 可读。 |
| D 模型接线 | Reader、projector、联合 prefix、数据/服务和 DCP | 新配置、CPU 测试、有限 batch 前反向 | off/local-only 不回归，global/both 梯度和隔离正确。 |
| E 真实贯通 | 当前状态更新、请求固定、缓存、少量训练/恢复 smoke | 一条可追踪闭环、loss/grad、缓存/恢复记录 | 无未来缓存、无静默缺件；缓存数值符合声明。 |
| F 匹配实验 | 最小对照，任务级 SR、延迟和资源 | 主结果、逐任务失败证据 | 区分 state/视觉/文本贡献，不只报告 loss。 |

A/B 不需要训练模型。C 的全量缓存必须在编码器与预处理选择后进行，避免为未选方案提前做多套全量缓存。

## 15.3 验收矩阵

| ID | 场景 | 检查 |
|---|---|---|
| T01 | +X 不存在 | 不读取、不编码、不生成有效 token。 |
| T02 | 声明存在的图丢失 | 明确失败，不当作不存在。 |
| T03 | 多对象关联同一图 | 去重，保留完整图和候选来源。 |
| T04 | 多 Island | 只选相关岛，不固定一个 Island。 |
| T05 | 无候选/导航无对象 | 明确 fallback，俯视必选。 |
| T06 | 对象遮挡 | membership 保留，不凭像素为零删图。 |
| T07 | 纯引用状态无目录 | resolver 正确读取，SG/PNG 不同 owner 可用。 |
| T08 | 图片相同、几何不同 | 共享 blob 不合并逻辑身份。 |
| T09 | t/s/r 不同 | 不读未来，不重做更新判定。 |
| T10 | 尺寸与 padding | 长宽比、米制范围、中心和 mask 正确。 |
| T11 | 底盘 frame 与箭头 | 多位置/方向一致，保留 z，有变换证据。 |
| T12 | 同义、多实例、多实体 | 候选覆盖，不借 oracle 单选。 |
| T13 | bbox 与 on/inside | 未证实关系不进文本。 |
| T14 | 四种 Memory 组合 | none/local/global/both 及混合 batch 不串读。 |
| T15 | Global 关闭 | 原配置同输入行为保持。 |
| T16 | 参数训练 | Reader/adapter/projector 有有限梯度与更新。 |
| T17 | 任务/选图变，PNG 不变 | 对应 Reader/KV 失效，冻结特征复用。 |
| T18 | 机器人移动 | 新 state、按标识刷新俯视、稳定 prompt 命中。 |
| T19 | optimizer/resume | 不复用旧 trainable 输出，参数与 recipe 完整。 |
| T20 | retry/reset/CFG | Session 身份和分支隔离，无缓存污染。 |

这是二十类检查，不要求新增二十个独立训练实验；可用少量组合 fixture 覆盖。

## 15.4 是否真正用到了 Global

attention 权重只是诊断，不足以证明动作依赖。需要选中图内容/几何干预，检查 Global tokens 与动作变化；改动未选中且不影响召回/选图的资产，应没有直接作用。

训练检查梯度和参数更新，闭环比较任务表现。屏蔽/替换输入可能是分布外诊断，不把一次动作变化直接等同于成功率因果收益。

## 15.5 性能与数值

训练记录 N、M、特征读取耗时、Reader/主干耗时、显存峰值和吞吐。在线记录冷启动、稳定状态、机器人移动、相关物体变化和子任务切换五类请求，避免只报高命中情况下的平均值。

缓存对照固定权重、完整条件、seed 和精度路径；沿用既有严格数值要求。需要容差时必须明确理由与数值界限，不自行放宽。不预先承诺固定速度倍数或毫秒数。

# 16. 实验设计、风险与未决项

## 16.1 最小主实验

| 实验 | Local | 底盘 Pose5 | Global 视觉 | SG 文本 | 作用 |
|---|---|---|---|---|---|
| E0 | 既有 | 旧零填充 | 关 | 关 | G1 参考 |
| E1 | 相同 | 开 | 关 | 关 | 隔离底盘状态影响 |
| E2 | 相同 | 开 | 开 | 关 | 视觉增益 |
| E3 | 相同 | 开 | 关 | 开 | 文本增益 |
| E4 | 相同 | 开 | 开 | 开 | 完整 G2 |

E2 仍需 SG 候选和对象—视图索引，只是关闭 SG 增强文本，不能称完全不用 SG。E1–E4 使用相同 raw15、样本范围、预算、初始化策略和评测 seed 计划。

旧 E0 如果训练条件不同，只是历史参考，不能直接用于严格因果比较。新增 state15 也需要训练，不把直接替换旧 checkpoint 的输入当作适配结果。

## 16.2 后续消融

主结果后再比较任务相关选图与全有效图、语言条件 Reader 与通用 Reader，以及箭头＋state/仅 state/仅箭头。删除输入可能需要匹配训练或适配，不只在推理删掉后就下定论。

不对 encoder、分辨率、K、Reader、检索和 projector 做全因子搜索。先小样本诊断必要变量，关键实验数量保持在项目资源约束内。

## 16.3 风险控制

| 风险 | 控制 |
|---|---|
| 召回遗漏同时删掉图与文本 | 多实体召回、保留歧义、fallback、候选覆盖统计。 |
| GT 能力被误当真实部署 | source_mode/backend/分数类型分开报告。 |
| compact 元数据缺失 | 定点补 sidecar，无法恢复时列缺件。 |
| 小物体在 256 中丢失 | 检查关键局部，必要时调整分辨率，不靠文字补像素。 |
| 提前强压缩 | 任务语言在压缩前/中介入。 |
| state 与图坐标错位 | 复用投影定义，以真实多帧验证。 |
| 任务变但缓存不失效 | 键包括任务、选图、几何等真实依赖。 |
| 缓存可训练输出 | 只缓存冻结计算，保留本步梯度。 |
| 缺少俯视图被白图代替 | 明确错误；未知地图模式另行设计。 |
| 启发式关系升级为事实 | 来源白名单，拒绝未经证实关系。 |

## 16.4 未决项与关闭动作

| ID | 未决问题 | 推荐起点 | 关闭依据 |
|---|---|---|---|
| O01 | 成员/投影元数据怎样补齐 | 复用 renderer 产物 | 样例覆盖、可恢复范围和来源。 |
| O02 | 冻结 encoder/preprocess | 先评估 Encode1＋等比 256 | 保真、shape/parity、成本。 |
| O03 | Reader、K_global、D_global | 任务 queries 读选中 patch | 输入规模、有限前反向与性能。 |
| O04 | Reader 任务语言来源 | 优先复用已加载冻结文本侧 | 语义能力、梯度和缓存依赖。 |
| O05 | GT/感知检索、模板预算 | 原生机制＋别名＋通用模板 | 代表性指令召回与误召回。 |
| O06 | Pose5 frame/归一化/projector | 稳定 scene/world，原 clean state 通路 | 底盘/箭头 frame 实证，两端同构。 |
| O07 | 跨请求缓存和容量 | 先请求内，再跨 replan | 命中失效、重试/reset、内存。 |
| O08 | CFG/dropout | 显式条件语义 | 分支一致、无错误任务条件声明。 |
| O09 | 多 Room 与超预算集合 | 单厨房先全部关联有效图 | 实际数量分布，不静默删目标。 |

未决项不重开已确认约束。讨论 Reader 不等于重新允许输入不存在的图；讨论 state 不改变 raw15。

# 17. 单样本示例与讨论问题追踪

## 17.1 完整流程例子

假设任务“把杯子放到盘子旁边”，候选 cup_A/cup_B 属于 Island 0，plate_A 属于 Island 1；冰箱和搅拌机与当前任务无关。

召回保留两个杯子和盘子，不借 oracle 单选。关联返回 Island 0 的 +X/−X/+Y，以及 Island 1 的 +X/+Y。最终是 floor_top＋五张有效 Island 图，共六张；不存在方向不输入，冰箱墙图不读取，完整资产仍保存。

每张图加载自己的 feature ref、几何和版本；不同尺寸使用同一预处理 recipe，同时保留真实物理范围。Reader 以原始任务语义从这些有效 patch 读取，输出 K_global tokens。

文本保留原始任务和三个对象的可信事实，标明杯子歧义。state15 为当前 Pose5＋EEF10；Global、Local、文本、观测和 state 在主干中共同影响 raw15 输出。

执行后只移动机器人，按 producer 标识更新俯视特征，其他图与稳定文本复用。若 Agent 改为关闭冰箱，重新召回/选图/组织文本，已有冻结图特征无需重新编码。

该例为设计示例，不是真实 Episode 标注或成功率证据。

## 17.2 问题追踪

| 用户关注 | 对应章节 |
|---|---|
| 赞同不代表完整冻结 | 第 2 章，C/P/O/F/D 分开 |
| 当前 Local/语言/视觉/state 怎样组 KV | 第 12 章 |
| 不同图尺寸和物理宽高 | 第 8 章 |
| 元数据怎样与对应图关联 | 8.2–8.4 |
| 语言何时进入 Global | 9.2–9.3、12.5 |
| Local 是否也要关注语言 | 4.3、12.1，首轮不新增算法变更 |
| +X 不存在是否还输入 | 5.3、7.3、T01 |
| 多 Island 是否需要固定槽 | 7.4 |
| 对象管理关联图、俯视必选 | 第 7 章 |
| nav_sg embedding 与同义召回 | 第 6 章 |
| 两次语言处理与 Agent 子任务 | 6.1、6.5、10.3 |
| 离线更新是否训练重判 | 第 5 章、13.1 |
| 不变语言/view 能否缓存 KV | 第 13 章 |
| raw15 和 state15 | 第 11 章 |
| 只给视图名称是否能对齐 | 8.4、11.4 |
| 机器人箭头是否必要 | 8.5、11.5、16.2 |

## 17.3 首个实际构建动作

先做批次 A：选少量真实样本覆盖单对象、多实例、多 Island 和无明确对象四类情况，输出同一份 Context 清单，包含原始指令、候选、对象—视图关系、必选/选中图、SG/图像 refs、可用几何及 state15 来源。

这一步量化接口缺口，不训练、不全量重渲染。随后冻结 encoder、Reader 和坐标三个关键选择，再做共享读取模块与模型接线。

# 18. 固定版本来源

以下来源用于区分已有事实与拟议方案。新 Schema、模块、伪代码、阶段和测试项属于设计，不是已实现能力。行号以固定 ref 为准。

**[S01] 本会话用户决策。** 包括“同意不代表方案完整”、raw15、不存在方向不输入、训练直接消费生产更新、当前任务作为未来 Agent 子任务、俯视必选与候选对象关联选图。最新选图方案已获用户赞同。

**[S02] G2 技术调研 v1.0，第九章。** 独立 Global Encoder、Atomic 任务和事实补充，不提前冻结未决细节。
[来源 S02](https://github.com/wxwy/psm_wma/blob/46fa72029faf1750b68aa3baae4e51d9b156f172/docs/build/PSM-WMA_G2_technical_survey_v1.0.md)

**[S03] Room/Island 资产设计 v1.5。** Island 独立四方向，物理层级不改，存储与一次读取分开。
[来源 S03](https://github.com/wxwy/psm_wma/blob/46fa72029faf1750b68aa3baae4e51d9b156f172/docs/build/PSM-WMA_G2_detailed_design_v1.5_2026-11-07_room_island_view_assets.md)

**[S04] 渲染成员与几何，render_connections.py:262–329。** native_entity_ids、Island members、参考系及有效图标记；成员不等于最终可见像素。
[来源 S04](https://github.com/wxwy/psm_wma/blob/46fa72029faf1750b68aa3baae4e51d9b156f172/g2/views/render_connections.py#L262)

**[S05] GT SG 摘要，atomic_6views_snapshots.py:55–90。** 字段、BBox 中心与 NOT_OBSERVABLE。
[来源 S05](https://github.com/wxwy/psm_wma/blob/46fa72029faf1750b68aa3baae4e51d9b156f172/g2/offline/atomic_6views_snapshots.py#L55)

**[S06] PNG 和 SG resolver。** scene_view_event_index.py:262–287；scene_graph_compact_v3.py:572–658。
[PNG 来源 S06a](https://github.com/wxwy/psm_wma/blob/46fa72029faf1750b68aa3baae4e51d9b156f172/g2/offline/scene_view_event_index.py#L262)
[SG 来源 S06b](https://github.com/wxwy/psm_wma/blob/46fa72029faf1750b68aa3baae4e51d9b156f172/g2/offline/scene_graph_compact_v3.py#L572)

**[S07] Local prefix，memory_prefix.py:50–125。** Local-only 形状、独立投影、模态 embedding 和 offsets。
[来源 S07](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/model/generator/mot/memory_prefix.py#L50)

**[S08] 当前主干 attention。** UND causal、GEN 路由与外部 prefix K/V。
[attention.py:355](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/model/generator/mot/attention.py#L355)
[unified_mot.py:811](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/model/generator/mot/unified_mot.py#L811)
[cosmos3_vfm_network.py:1642](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/model/generator/mot/cosmos3_vfm_network.py#L1642)

**[S09] 请求内缓存及清理。** 不代表已有跨 Session Global 缓存。
[inference_text_kv_memory.py](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/model/generator/mot/inference_text_kv_memory.py#L1)
[omni_mot_model.py:4599](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/model/generator/omni_mot_model.py#L4599)

**[S10] raw15/state15 构造及原始 state 布局。** exact_window_policy.py:197–227；robocasa_lerobot_dataset.py:69–76,415–440,531–545。
[精确窗口 S10a](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/data/generator/action/datasets/robocasa_exact_window_policy.py#L197)
[原始布局与 EEF S10b](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/data/generator/action/datasets/robocasa_lerobot_dataset.py#L69)

**[S11] 文本 formatter、服务入口与严格请求字段。**
[json_formatter.py:83](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/data/generator/action/utils/json_formatter.py#L83)
[action_policy_server_robocasa.py:1314](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/scripts/action_policy_server_robocasa.py#L1314)
[robocasa_session_transactions.py:416](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/inference/robocasa_session_transactions.py#L416)

**[S12] 机器人箭头实际底盘 frame 和像素投影。** robot_pose_marker.py:24–76。
[来源 S12](https://github.com/wxwy/psm_wma/blob/46fa72029faf1750b68aa3baae4e51d9b156f172/g2/views/robot_pose_marker.py#L24)

**[S13] YOLOE 与 SigLIP2 分工。** yoloe_siglip_local.py:122–181,254–277,318–352。
[来源 S13](https://github.com/wxwy/nav_sg/blob/70eb7b447e65/ObjectNav-mapping-only/vlm/yoloe_siglip_local.py#L254)

**[S14] 对象检索、direct/LLM 分支和对象持久化 embedding。** query_node.py:262–312,314–365,378–445；object_cluster3d.h:44–69。
[检索来源 S14a](https://github.com/wxwy/nav_sg/blob/70eb7b447e65/mapping_8_3/siglip_features/scripts/object_nav_query_node.py#L262)
[对象记忆 S14b](https://github.com/wxwy/nav_sg/blob/70eb7b447e65/mapping_8_3/mapping/include/mapping/object_mapping/object_cluster3d.h#L44)

**[S15] GT 导出不伪造视觉 embedding。** g2/gt/README.md:190–195。
[来源 S15](https://github.com/wxwy/nav_sg/blob/70eb7b447e65/g2/gt/README.md#L190)

**[S16] 空间图像与 latent cache 设计 v0.4。** 冻结编码与可训练 Reader 分离、独立 G1/G2 cache、rollout 不读示教未来。
[来源 S16](https://github.com/wxwy/psm_wma/blob/46fa72029faf1750b68aa3baae4e51d9b156f172/docs/build/PSM-WMA_G2_detailed_design_v0.4_2026-11-06_spatial_view_latent_cache.md)

---

## 最终主线

**完整场景持续维护；子任务召回对象；俯视图必选，其余按对象关联读取；几何随图绑定；任务语言指导 Global 压缩；可信 SG 事实补充原始任务；state15 提供底盘与机械臂当前状态；Global 与已有 Local 在 Cosmos GEN K/V 中汇合，raw15 动作接口不变。**

已确认原则已记录，推荐结构与未决项已列出。本文没有将讨论结论升级成“生产代码已完成”或“全部细节已冻结”。

---

## 2026-11-16 补充：Issue52 单帧 VAE 缓存的独立构建合同

本节记录本文归档后 Owner 在 [Issue #52](https://github.com/wxwy/psm_wma/issues/52)
明确的新决定，仅收口冻结图像特征的数据准备边界。它优先于正文中此前对
Episode 整包或“只编码当前任务所选图”的建议，不改写历史讨论，也不冻结
Global Reader、语言增强、state15/Pose5、主干 K/V 或训练接线等未决项。

1. **所有有效空间 View 都离线编码**，即使当前任务暂时不读取。模型的任务驱动
   稀疏读取和离线资产覆盖是两件事；选图不能裁剪缓存生产范围。
2. 复用现有 Cosmos Wan VAE 的独立单帧 Encode1 与公共
   `vision_encoder.normalize_uint8_item`。单样本输入 `[1,3,1,H,W]`，冻结、
   eval/no-grad、非 streaming，不跨图保留编码状态；保存完整空间 latent
   `[C,H_z,W_z]`，不套用 G1 17 帧窗口、left+wrist 拼图或 Local Visual96 池化。
3. **每个 Episode 内，每个逻辑 View 一个独立 `.pt` 数值文件**，内部保存全部实际
   图片版本及 logical state/frame→physical owner/record 的索引。不是每张 PNG
   一个文件，也不是整个 Episode 一个数值大包。多个 Room/Island 保持原身份。
4. 严格消费原有 `view_pngs/view_refs`，中途不存在的 View 显式 absent，不补旧图、
   不编码、不生成有效 token；声明存在但 PNG 缺失/损坏是错误。当前状态与实体
   图片 owner 的身份分别保留，不按图像内容重算 1mm/1°/采样规则。
5. 新缓存只写 `episode/vae_cache/`，有自己的 manifest 和 COMPLETE；原 PNG、
   箭头、SG、episode_manifest.json 与原 COMPLETE 不改。按 View 原子发布，
   严格来源/recipe 一致才恢复，同目标写入互斥。读取时只打开选中的 View 文件，
   使用有界文件级 lazy cache，不在每次训练读取时扫描全 Episode。
6. 等比白底 256×256 与 FP32 存储是初始真实样例候选，**不是生产最优配置冻结**。
   实际 latent 空间形状由编码输出确认；pixel valid rectangle 来自 resize/padding
   几何，不由白色像素猜测。低精度、B>1 混批、数值/图像质量与吞吐须各自实测。
7. 入口位于 `tools/g2/`，业务位于 `g2/latent_cache/`。builder、encoding、storage
   分离，训练读取不加载 VAE/Policy/MuJoCo/ROS/在线服务；未来在线 G2 可复用同一
   预处理与 Encode1 接口。Cosmos 通用核心不反向导入 Root tools。

本轮交付限代码、CPU fixtures、文档与独立 Draft PR。真实 VAE/GPU 样例、原图与
decode 的人眼检查、生产配置冻结及全量编码属于后续独立授权 Gate，不能从
fake encoder 测试升级为真实编码验收。实现和复现说明见
[Issue52 缓存 runbook](PSM-WMA_G2_spatial_view_vae_cache_2026-11-16.md)。
