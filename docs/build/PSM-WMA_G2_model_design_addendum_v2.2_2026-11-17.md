# PSM-WMA G2 v2.2：模型侧设计补充与已确认决策

日期：2026-11-17。状态：**Owner 已确认本文列明的模型主线；本文是设计与实施依据，不是实现完成或实验通过报告。**

配套任务：[模型侧增量构建计划 v1.0](PSM-WMA_G2_model_build_plan_v1.0_2026-11-17.md)。

## 0. 一页结论

本阶段验证 Full Map＋GT task grounding 下，任务相关全局空间信息能否改善已有 RoboCasa G1 Local-TTT 策略。当前 Atomic episode 视为一个子任务；不引入 Agent 本体、开放词汇对象检索、对象 embedding、额外对象渲染或新的任务状态机。

```text
子任务初始化
  原始指令＋GT任务实体＋初始可信SG事实
                       ↓
               一份静态增强指令
                       ↓ 同一formatter/tokenizer；R1/R2关闭idle_frame文本
               冻结Cosmos UND文本前向
                  ├─ 逐token上下文hidden → 语言适配 → 64个任务查询
                  └─ 各层GEN可用文本K/V ──────────────────┐
                                                        │
当前场景                                                 │
  必选俯视图＋任务对象关联的有效view                        │
    ↓ 逐view冻结Wan Encode1缓存                           │
  完整空间latent网格＋类型／投影几何／patch位置              │
    ↓ 任务查询读取视觉，2轮cross-attention＋memory SA＋FFN   │
  64×512 Global tokens → 独立projector＋Global模态标识      │
    ↓ 每层GEN生成Global K/V                               │
                                                        ↓
Local-TTT → 原有Local projector → Local K/V ──→ 全部GEN层联合读取
当前局部观测／state15／去噪视频与动作 ──────────→ Cosmos动作输出
```

首版采用**记忆查询先读语言，再读视觉**，不是 view patches 先读取语言。后者仅为备选对照。

代码在现有 G1 上增量扩展：G1/R1/R2 是配置，不是三套 Dataset、Trainer、Formatter、Policy Server 或 attention 实现。Global Reader 等新增职责可独立模块化；公共机制必须复用。

## 1. 决策效力、范围与源码身份

### 1.1 与已有文件的关系

- 保留 [G2 v2.0详细设计](PSM-WMA_G2_detailed_design_v2.0_2026-11-16.md)，不静默改写历史决定。
- 保留 [离线准备v2.1补充](PSM-WMA_G2_offline_data_preparation_addendum_v2.1_2026-11-16.md)。本文仅覆盖与后续 Owner 决定冲突的模型及数据接口条款，尤其是静态增强文本、双俯视图和共享formatter。
- 离线代码任务为 [Issue #54](https://github.com/wxwy/psm_wma/issues/54)，逐view VAE核心为 [#52](https://github.com/wxwy/psm_wma/issues/52)／[PR #53](https://github.com/wxwy/psm_wma/pull/53)。模型工作不重复建设这些模块，也不直接改写其在途分支。
- 用户明确：同意已讨论部分不代表认可所有细节已经完整。本文件把已确认决定、推荐实现和待实测项分开。

### 1.2 本次归档前核实的基线

| 对象 | 固定身份／说明 |
|---|---|
| 根仓／目标分支 | `wxwy/psm_wma:V3` |
| 本次文档基线 | `fe1089fb925d86697bebd9bef18608d9c9eae87b` |
| Cosmos Gitlink | `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2` |
| nav_sg历史检查基线 | `70eb7b447e65d793b0ebe18b258291ce46f057c1`；不是本次重新验证的运行版本 |
| G1历史来源核对 | `2d128ed5a07601cdd424974f99b67832eafeeb41`；仅用于定位历史prompt行为 |

开工时再次读取实际V3与Gitlink，不回退新增提交。文档提交不是生产实现SHA，历史CPU／GPU结果不能算到本次模型模块上。

### 1.3 两种阶段命名必须区分

- `DATA_A → DATA_B → DATA_C`：全局信息离线构建 → state15单独转换归一化 → 全部离线数据对齐。由另一会话推进。
- `TRAIN_A → TRAIN_B`：短阶段Global-only适配 → Global＋GEN联合微调。属于本文模型训练安排。

模型CPU fixture与模块构建可先推进；真实端到端训练样例需要DATA_C或等价已验证小样例。不能用合成输入宣布真实数据已经对齐。

### 1.4 证据标记与解释原则（2026-11-17 来源核查增补）

为避免把外部论文中的**架构启发**写成已经验证的 G2 结果，本文采用四级来源：**[Sxx] 固定版本项目源码/实测归档**（可确认既有实现和数值）、**[Pxx] 外部论文/官方文档**（可支持一般方法与工程约束）、**[O] Owner 在本项目中明确确认的取舍**（确定首版合同但不等于文献最优）、**[V] 需本项目实验验证的假设**。详细出处、原文支持范围、不能推出的结论与检查项见第 16 节。

尤其要区分：**“有论文采用查询式读取”与“G2 采用 64×512、读两轮、该 LR 能提高 RoboCasa 成功率”不是同一个证据层级**。后者是已确认的首版实验起点 [O/V]，不应使用外部引用冒充已在 G2 上获得实证。

## 2. 已确认决策表

| ID | 已确认内容 |
|---|---|
| M-D01 | 复用现有G1代码与基础设施；旧配置行为兼容，新配置启用新能力 |
| M-D02 | 所有有效view离线独立单帧Wan Encode1；模型不把方向当时间，也不使用Local Visual96代替空间网格 |
| M-D03 | 按任务实体关联选图，必选俯视图；不存在方向不占有效token，多Island不设固定四图槽 |
| M-D04 | 同时生成带／不带机器人底座标识俯视图；训练／推理一次选择一种，默认带标识 |
| M-D05 | 视觉token绑定类型、view级投影几何和patch级位置；不把所有元数据塞进语言 |
| M-D06 | Reader主线为记忆查询先读取语言，再读取视觉；逐patch先读语言只作备选 |
| M-D07 | K_global=64，hidden=512，8 heads，head_dim=64，FFN=2048 |
| M-D08 | 语言读取1轮；视觉读取2轮，每轮含memory self-attention与FFN；不做全量视觉patch self-attention |
| M-D09 | 子任务开始时生成一份增强指令，整个子任务不更新；初始事实明确标为初始上下文 |
| M-D10 | Reader和GEN使用同一有效文本；复用冻结UND最终post-norm逐token hidden，不新增语言模型 |
| M-D11 | 一次文本前向服务Reader hidden与GEN文本K/V是接线目标，需验证RoPE、归一化、packing及FSDP语义 |
| M-D12 | Global与Local独立projector／模态标识，全部GEN层K/V联合注入；不新增Global—Local直接attention |
| M-D13 | Global是当前场景读出，不递推累计；Local保留历史累计与内层fast-state更新 |
| M-D14 | G1 model-only warm-start，完整继承Local；不是沿用G1 optimizer／游标的same-job resume |
| M-D15 | TRAIN_A仅训练Global；TRAIN_B训练Global＋GEN；UND／VAE／Local外层始终冻结 |
| M-D16 | Global峰值LR=5e-5；TRAIN_B GEN=1e-5；动作适配=5e-5；R1相同GEN分组LR |
| M-D17 | A→B保留Global optimizer和数据/RNG/Local流状态，新解冻GEN参数单独预热 |
| M-D18 | 文本dropout=0.1；Reader与主干共享决定；不加Global／Local整支路随机dropout |
| M-D19 | 首版guidance=1；去文本样本保留GT选图，不宣称完全无任务条件 |
| M-D20 | 同Session跨replan缓存；无跨Session共享；一次去噪请求内条件固定；保留无缓存参考路径 |
| M-D21 | 首批R0历史参考＋R1匹配输入无Global＋R2完整G2；只新增R1/R2两条正式训练 |
| M-D22 | 主比较同总有效样本预算，辅助比较同GEN更新次数；运行成本另报 |
| M-D23 | R1/R2训练推理均删除idle_frame文本字段，不是设0；旧G1配置保留原行为 |
| M-D24 | 正式checkpoint、训练预算、有效batch、预热/衰减和评测清单经小样例后固定，不在本文拍定 |

## 3. 数据接口：只消费已验收资产，不接管离线生产

### 3.1 选图与身份

`selected_views(t) = mandatory_top(variant,t) ∪ union(views_of(entity,t))`。

任务实体来自该episode/子任务初始化的GT绑定；当前成员关系、图片版本和几何从当前逻辑空间状态读取。对象身份固定不意味着视图集合固定。保留整张选中图的上下文，不裁掉其他物体。

不硬编码10张图或固定Island数量。一个batch内不同样本图数不同，可packing或padding＋mask；padding不能变成真实视觉证据。任务无明确对象时的保底规则由已验收数据合同提供，不能由模型临时猜测。

R1不开Global时不应打开view latent大文件、载入Reader或计算无用视觉条件。共享样本身份、静态文本和state15仍然一致。

### 3.2 最小逻辑输入合同（名称是设计接口，不声称已有ABI）

| 部分 | 必需含义 |
|---|---|
| 样本身份 | episode/scene/subtask、当前decision frame、数据与对齐版本 |
| 文本 | original instruction、静态enhanced instruction、template/source identity、最终tokens及dropout结果 |
| 视觉项 | view_id、room/island关联、top variant、image content/owner identity、latent记录及recipe |
| 几何项 | 实际图片对应的投影版本、当前成员关系版本、图像resize/pad映射、有效区域 |
| 状态 | 经DATA_B验证的state15与归一化身份；模型侧不重新设计动作编码 |
| Local | 现有合法历史证据及事务身份；保持已有causal更新 |
| 监督 | 原有当前／未来latent和raw15动作目标；不得当成Global输入 |

当前帧t、使用的空间状态s、实际图片owner帧r分别保存。使用不晚于t的合法状态；图片和SG分别解析引用。模型不再计算1mm/1°更新阈值，不将无实体目录误判为无状态。

数据根仍为既定`robocasa365-target-atomic-6views/tasks/<task>/episodes/<episode>/`，view latent在`vae_cache/`按逻辑view一文件。模型依赖显式reader返回的tensor/索引，不依赖生产CLI或目录glob猜测。

### 3.3 双俯视图

配置语义：`top_view_variant: with_robot | without_robot`，默认`with_robot`。一次只输入其中一种，不默认双图一起输入。两个版本独立编码/索引，不能从latent中减掉箭头。

无标识图按场景view内容更新规则处理；机器人移动本身不产生箭头更新。有标识图另包含底座标识更新。两图共享的投影几何可以复用，但内容和latent身份不能混同。请求版本不存在时明确错误，不静默降级；缓存、训练配置和checkpoint均绑定variant。

## 4. 空间token组织与几何编码

每张图的VAE输出为`[C,H_z,W_z]`，实际shape和dtype从已验收recipe读取。固定Child接口的latent通道为48、空间压缩因子为16；256方图对应16×16仅是该recipe下的预期，不是对所有输入的硬编码。[S01]

首版保留每个latent格点为一个token，不预先做整图均值、逐图摘要或Island摘要。这是为保留空间位置、避免压缩前丢失局部结构所作的本项目选择 [O/V]；用有限latent读取大量输入的结构思路可参考 Perceiver／Perceiver IO [P01][P02]，但相关论文没有验证本项目使用 Wan VAE 网格的具体效果：

```text
x[i,p] = P_img(z[i,p]) + E_type(i) + F_geom(m[i]) + PE(i,p)
各项均为512维；相加，不是拼成2048维。
```

### 4.1 已确认的含义

- `type`：视图范围/类别与方向，不是图片在输入列表中的序号。
- `geom`：view级投影位置、方向与真实画幅宽高，不是物体表面法向或逐像素真实XYZ。
- `PE`：patch在原有效画幅中的位置；物理尺度来自几何，不把padding当额外场景空间。
- Room/Island原始ID用于绑定与分组，不学习随机实体编号的跨场景语义。
- 同一场景用稳定world/scene参考，不随机器人移动旋转全图。底盘数值规范由DATA_B与几何输入共同核对。

### 4.2 推荐的最小数值实现，尚需ABI/样例定稿

类型可拆为scope与direction两个可学习表，输出512维后相加；scope须覆盖实际floor/room/island层级，不因当前单厨房样例假定永远一个Room。该类别拆分是结合本项目实际view语义设计 [O/V]，并非 Perceiver／Transformer 论文给出的现成 sixview 枚举。

几何候选为`m=[o(3),right(3),up(3),forward(3),extent_u(1),extent_v(1)]`，共14维，经小型MLP变为512维，附加给该图所有tokens。`o`应由producer真实reference frame、uv_min和投影约定导出，不能拿对象中心或单位矩阵代替。观察方向不是物体表面法向。长度/位置归一化系数与MLP隐藏宽度未冻结。

patch锚点用resize/padding的逆映射得到有效画幅中的二维位置，再作二维sin/cos位置特征＋线性投影。正余弦位置特征参照 Transformer 的位置表示思路 [P05]，Perceiver 使用位置/Fourier 特征处理结构化输入提供架构参考 [P01]；**二维坐标定义、逆映射与频率、mask规则均是G2的项目适配，不是论文直接规定**。频率数量和边界mask规则需在M01定稿。完全padding token屏蔽；部分覆盖以确定、共享规则处理。不得按像素颜色是否白色判断padding；VAE感受野不等于严格独立小矩形。

若使用投影平面坐标，它只表示`o+a*extent_u*right+b*extent_v*up`，沿forward仍有未定深度；不伪称逐patch物体XYZ。首版不因此要求新的depth/normal输入或重新编码VAE。

几何/类型/PE参数均注册为正式模块，参加Global optimizer和checkpoint。输入元数据保持独立，调整几何编码不使已冻结VAE结果失效。

## 5. Global Reader：已确认主线与精确层数

设`X=[M,512]`为本样本选中图像patch集合，`H_text=[L,D_text]`为冻结UND最终归一化特征，`T=P_text(H_text)=[L,512]`，`R0=[64,512]`为可学习查询。

```text
语言阶段（1个block）
  R_task = R0 + CA(Q=R0, K=T, V=T)
  R_task = R_task + FFN(R_task)

空间block 1（独立参数）
  R1 = R_task + CA(Q=R_task, K=X, V=X)
  R1 = R1 + SA(R1)
  R1 = R1 + FFN(R1)

空间block 2（独立参数）
  R2 = R1 + CA(Q=R1, K=X, V=X)
  R2 = R2 + SA(R2)
  R2 = R2 + FFN(R2)

G = final_norm(R2)                  # [64,512]
M_G = global_projector(G) + e_G     # [64,D_model]
```

伪代码省略pre-norm等实现细节；具体norm/激活沿既有适用组件明确记录，不偷加全量patch SA。全部Reader attention为8头、每头64维，FFN中间维度2048。**512维／8头／FFN2048正好对应经典Transformer Base的宽度配置 [P05, Table 3]，但本项目的Global Reader是不同输入、不同监督目标，沿用这组数值仅是合理起点 [O/V]，不是已有G2最优结果。**两个空间block不默认共享参数。

语言只读1轮，不在第二视觉block重新跑UND。第二次视觉读取使用已包含第一轮场景证据的查询；这提供再次读取的能力，不预先保证模型学到特定推理步骤。**迭代读取**受 Perceiver [P01] 启发，**指令感知的查询**可参考 InstructBLIP [P03]，**轻量查询适配冻结特征**可参考 BLIP-2 [P04]；这三者与当前架构并非逐层一一对应，尤其没有证据证明“一轮语言＋两轮视觉”优于一轮或三轮 [O/V]。

64是整个选中场景共享输出预算，不是每张图64、每对象1个或固定图配额。所有query均可读全部有效视图patch，memory SA只发生在64个tokens间。这里采用有限latent bottleneck并让其再次读取输入，参考 Perceiver [P01]、Perceiver IO [P02]；**64这一具体数量是本项目的容量／代价折中 [O/V]，两篇论文没有给出RoboCasa上64个空间记忆token最优的证据**。注意力位置配对规模约`K*L + 2*K*M + 2*K*K`，是由注意力矩阵形状得到的渐近估算 [P01][P02]；不等同实测时延。

Global每次由静态任务查询和当前X重新读出，不以上一时刻G作为递归输入。历史由Local承接。

备选（不作为默认实现）：`view patches读语言 → 查询压缩 → memory SA`。用 Query 来自哪一侧区分交互方向，参考标准cross-attention定义 [P05]；InstructBLIP的指令感知查询 [P03]只为第三种主线提供类比，不是G2两方案直接A/B。没有直接实验证明它与主方案谁更好；不为其提前增加大规模配置组合或新缓存。

## 6. 静态语言、共享formatter与UND复用

### 6.1 子任务级静态增强文本

当前Atomic episode开始时，依据原始任务、该次GT任务绑定及初始可信SG事实生成一份文本。后续窗口、物品位姿、机器人移动均不刷新。明确写“初始空间上下文”，不把旧坐标称为当前坐标。不把训练窗口起点当作新的子任务起点。

SG、view、state仍动态更新；只冻结文本，不冻结世界。在线评测使用当前rollout初始化的GT与初始SG，不用专家后续轨迹。未来Agent切换子任务时再建立新静态文本；动态文本维护不在本阶段。

### 6.2 共享文本协议

在现有`ActionPromptJsonFormatter`与`ActionTransformPipeline`增量增加配置，不复制G1/R1/R2三种formatter。[S02]

R1/R2明确**不输出idle_frame字段**，不是设为0。旧G1配置维持原行为。其他模块真正需要的idle统计保留，真实动作标签不变。

背景事实：历史G1与当前exact-window路径从待预测action15计算idle_frames，再由JSON formatter写入文本；服务端此前固定给0。[S02-S04] 这说明新静态文本协议必须显式处理该字段，不证明历史效果必然受损。

保留合法固定配置（视点、分辨率、帧率、计划horizon等）时，训练/服务使用同一构造函数与确定序列化。不使用未来动作统计、真实完成步数、窗口起始帧或当前SG变化改变文本。时长要用明确的计划配置，不能被额外clean state行误算。具体合法固定字段和数字格式由小样例审计确定。

不要以为设置非JSON的`append_idle_frames=False`就自动关闭JSON字段：必须控制formatter本身并检查最终tokens。

### 6.3 文本特征

使用同一有效token序列的UND最终post-norm`[B,L,D_text]`，保留多个文本tokens，正确屏蔽padding；不是词表logits、单句池化向量、初始embedding查表或新SigLIP模型。其返回能力来自现有源码 [S05]；固定编码器＋轻量可训练适配可参考BLIP-2 [P04]，但BLIP-2使用的视觉编码器不同，**不能据此认为Wan VAE latent自然拥有已对齐的文本语义**。首版语言适配可从norm＋线性投影到512开始 [O/V]。

UND参数冻结，但语言适配与Reader训练。冻结的文本前向不生成额外推理文字，不调用API，不再加载第二份完整Cosmos。

### 6.4 一次UND前向同时服务Reader与GEN

前置执行文本分支，输出token hidden和各层GEN可用文本K/V；随后构建Global，再执行GEN。UND不读Global，故不存在语义循环。

这不是现成接线：固定源码`reasoner_forward`返回hidden，现有请求内缓存主要在第一次去噪时填充。[S05-S07] 新接口需复用正确权重和公共attention，校验RoPE位置、UND→GEN key norm、head布局、packing offsets、pad、dtype、sample隔离与FSDP forward注册。

禁止把reasoner原始K/V未经转换就塞入GEN缓存。若相关GEN侧norm/adapter在TRAIN_B可训练，只能缓存其之前的冻结量或在当前参数下重新应用，不能以“文本冻结”为由detach这部分梯度。

实现先有参考路径，优化路径对照hidden/KV/输出/梯度；不复制整套UND Transformer。文本计算共享不得破坏已有G1默认路径。

## 7. 全层Global／Local联合K/V

Global经独立projector与模态标识后进入与Local相同的主干宽度；D_model从加载配置读取。当前Edge参考为2048、28层、16Q头/8KV头/head_dim128，但实现不硬编码这些数值。[S08]

每个GEN层沿token维组装：

```text
K_read = [K_Global ; K_Local ; K_Text ; K_NativeGEN]
V_read = [V_Global ; V_Local ; V_Text ; V_NativeGEN]
O_GEN = attention(Q_GEN, K_read, V_read)
O_UND = causal_attention(Q_Text, K_Text, V_Text)
```

Global和Local只有外部K/V，无主干Query；当前视觉、state和去噪变量的GEN Query可以读取二者。当前视觉/state是clean输入，不代表深层hidden不变化。无Global→Local或Local→Global独立attention；主干多层完成融合。

使用各层既有GEN K/V投影与规范化，不新增独立主干attention头。这是从项目当前Local-only prefix与两路GEN投影实现推导的最小增量 [S07][S09]；**全部GEN层注入Global属于Owner批准的G2试验方案 [O/V]，并非InstructBLIP或Perceiver已验证的最佳层覆盖范围**。Global几何在Reader中表达；不把Global伪装成文本或视频时间步，不改变原生token的RoPE/位置编号、目标mask、噪声和loss。

扩展现有`MemoryPrefixContext`，分别表达每样本Global/Local presence、长度、offsets，不能简单把Global塞入Local张量并增大k_local。[S09] 覆盖none、local-only、global-only、both及混合batch，保留原生padding segment。Global关闭时真正缺席，不留下64个零token。

注意：零Value或小projector并不保证开启Global后输出等于旧模型；额外Key仍改变softmax分母。首版不为初始严格等价新增复杂门控。Global-off在同输入/同权重下必须回归原路径；Global-on的随机初始化扰动由TRAIN_A与实测管理。

## 8. 初始化、训练参数和损失

### 8.1 G1 warm-start

R1/R2使用同一份经核实的G1 Local-TTT checkpoint。完整载入GEN、UND、原有适配器及Local encoder/core/projector/初始fast参数。新增Global模块独立初始化；只允许预先列明的新参数缺失，不使用无边界strict=False忽略所有错误。

原fresh配置会跳过local_memory，[S10] G2不得照搬。G2重新建立optimizer/scheduler/计数与数据流；不导入G1 optimizer或未结束episode的fast state。G2自身恢复则使用G2完整状态，二者显式区分。

### 8.2 训练范围

| 模块 | TRAIN_A | TRAIN_B | R1 |
|---|---|---|---|
| VAE／UND | 冻结 | 冻结 | 冻结 |
| Global视觉/语言适配、几何/type/PE、queries、Reader、projector、modality | 训练 | 训练 | 不创建 |
| GEN主干及其他生成适配 | 冻结 | 训练 | 训练 |
| action2llm／llm2action／action_modality_embed | 冻结 | 训练 | 训练 |
| Local外层参数与独立projector | 冻结 | 冻结 | 冻结 |
| Local episode内fast state | 继续更新 | 继续更新 | 继续更新 |

GEN冻结只关参数梯度，不能把其forward置于no_grad，否则Global无法通过动作损失学习。这是PyTorch autograd中requires_grad与no_grad模式的区别 [P07]，不是经验性猜测。Local内部需要普通grad模式更新fast tensor，不能因外层冻结被inference_mode覆盖。[S11][P07] 局部不必要的高阶图优化必须另验数值，不改inner算法或因果顺序。

沿用当前G1动作/视频生成loss及既有权重，不增加Global重建、语言生成或额外监督目标。raw15与EEF10语义不改；state15使用DATA_B定义的新前五维，仅在G2对应配置启用。

### 8.3 已确认峰值学习率

| 参数组 | TRAIN_A | TRAIN_B | R1 |
|---|---:|---:|---:|
| Global | 5e-5 | 5e-5 | 无 |
| GEN非动作组 | 冻结 | 1e-5 | 1e-5 |
| 动作适配三组 | 冻结 | 5e-5 | 5e-5 |

Local inner_lr继续继承已验证G1配置，既有基线为0.1，不应用外层倍率。[S11][S13] **Global 5e-5、GEN 1e-5、动作5e-5这三个峰值是G2的新训练假设 [O/V]；不是对G1优化器数值的直接照抄，也没有论文证明其在本任务最优。**optimizer类型、betas、eps、weight decay、clip等优先沿已验证共享G1设置；若有必要改变需明确列出，本文未新定值。参数组必须互斥完整，每个训练参数恰好出现一次。

### 8.4 A→B切换与恢复

TRAIN_A固定预算结束，不要求SR先达到G1，不因几个batch loss下降临时改计划。Global开始时预热；B中新解冻GEN/动作组独立预热。保留Global权重、optimizer moment/step、数据游标、RNG及当前Local fast state，不把阶段切换当environment reset。

切换只在完整optimizer/GA/既有Local事务边界发生；所有FSDP ranks一致决定。FSDP2对参数分片、forward钩子、optimizer DTensor有明确约束 [P08]；这些文档只支持正确接线/同步的工程必要性，不意味着阶段切换自动保留moment和Local状态，仍需本项目实测。无论通过预注册参数组还是受控重建实现，都须证明Global状态无损、新组首次状态正确、未激活组没有隐式weight decay。新增分布式collective路径必须一致，不因某rank没有Global或dropout而死锁。

保存stage、各组更新步数、scheduler相位、trainable集合、optimizer状态、loader frontier、RNG、Local sidecar与source identities。测试切换前后中断恢复，不能只恢复总step猜阶段。

## 9. 条件dropout与CFG

TRAIN_A/B均使用0.1文本dropout（沿用现有RoboCasa/G1配方，不是从CFG论文推导出的最佳概率 [S14][P06]）；每个consumer样本产生一次决定，Reader和Cosmos共用同一有效文本。原始任务与增强上下文一起丢弃，不独立抽样、不在activation checkpoint重算时再抽一次。

空文本时Global仍读取相同GT选图。使用主干真实空文本条件；若无有效token，显式跳过该次语言attention贡献，不用all-masked softmax制造NaN。不能把正常hidden乘零就称等价。

保留GT选图意味着仍有任务定位信息，所以称“去文本条件”，不称完全unconditional。不额外随机删除view、Global或Local。

首版guidance=1，只跑条件预测（与当前Policy Server默认及GEN在guidance=1时跳过额外文本CFG的分支吻合 [S15]；CFG方法背景见[P06]，但不能据此断言guidance=1在G2成功率最优 [O/V]）。未来启用CFG时，去文本分支须用空文本任务查询重新构造Global，不能共用完整文本的Global输出；图像冻结latent可共享。无文字/有文字缓存身份必须不同。训练dropout不改变子任务级静态文本资产。

## 10. 推理缓存与状态生命周期

固定权重推理首版支持同Session跨replan复用（项目自定推理优化 [O/V]，不是Perceiver或BLIP-2提供的现成能力；现有请求内文本K/V能力仅能作为增量复用入口 [S06]）：逐view latent、UND hidden与GEN文本K/V、语言适配与任务查询、Global输出/投影及各层Global K/V。保留cache-off参考路径；不做跨Session/跨机器共享，不以缓存覆盖作为正确推理的前提。

| 改变 | 应有行为 |
|---|---|
| 仅当前相机／数字state／Local更新，Reader输入不变 | Global与语言可复用；Local走自己的更新 |
| 选中图片更新，包括with_robot箭头变化 | 重读Global；语言复用 |
| without_robot且仅底盘运动，图片/几何不变 | Global可复用 |
| selected_view集合或实际几何/分组编码改变 | 重读Global |
| 未选中view更新且未影响选图/输入 | 不使Global无谓失效 |
| 同episode换子任务 | 更新文本/绑定/选图/Global，不自动清空Local |
| episode reset | 清理执行流状态，Local重新初始化 |
| 更换checkpoint或相关配置 | 相关缓存失效 |
| 请求重试 | 不重复累计同一执行历史，不破坏既有commit/abort |

缓存key绑定实际tokens/位置规则、模型和Reader版本、top variant、稳定排序的view IDs、图像内容版本及实际输入元数据版本；不能只用episode或任务字符串，也不无条件加入每步递增frame导致全部失效。

每次replan先解析一个不可变逻辑输入快照，整个去噪请求不替换它。旧owner图可以合法引用；不要求所有图在同一物理帧重画。

不缓存主干全部GEN深层K/V：当前视觉/state会与去噪变量交互，静态输入不意味着中间量静态。显存／CPU／句柄有界，淘汰后正确重算；并发session不串用。容量、淘汰数值和性能阈值待测。

训练仅复用已冻结确定计算；所有可训练Global输出与主干相应K/V不能跨optimizer更新复用。TRAIN_A即使GEN权重冻结，Global输入也变化，不能复用脱离当前图的旧Global K/V。

## 11. 最小实验与比较口径

| 组 | 语言/state | Local | Global |
|---|---|---|---|
| R0 | 历史G1输入 | 原机制 | 无；已有参考，不新增训练 |
| R1 | 静态增强文本＋真实Pose5 state15；idle文本关 | 外层冻、内层运行 | 真正关闭 |
| R2 | 与R1相同 | 与R1相同 | 本文完整主线 |

R1/R2从同一G1初始化。这一配对/对照方案是为隔离Global增量而制定的本项目实验设计 [O/V]，并无外部论文给出这组R1/R2的直接实验结果。R2有A期S_A和B期S_B；R1持续训练GEN，保存S_B与S_A+S_B两个检查点。主比较同总有效训练样本预算，辅助同GEN更新次数；批大小/GA不同时按真实consumer和sample计数换算，不用名义step掩盖差异。R1主比较拥有更多GEN更新，是较强基线；等样本不等算力，GPU时间、显存、参数更新历史单独报告。

两组共享数据划分、prompt、state、Local证据/reset、action horizon、replan、去噪步数与guidance。评测必须使用同一明确场景/初始状态清单；只有相同seed字符串不足以证明场景一致。在线地图来自各自实际rollout，不播放专家未来空间状态。

报告task级和总体SR、样本数、配对胜负转换、超时/失败、服务故障、执行步数、首轮/稳态及cache hit/miss的P50/P95延迟、显存与训练预算。小样例仅证明功能与数值，不能证明SR增益。

R1对R0反映新语言/state/继续微调的合并效果，不分别归因；R2对R1检验Global增量。未来首选双俯视图的训练匹配消融；结构1/3、K与层数搜索后置。临时关闭已训练Global只是依赖性诊断，不替代正式R1基线。

## 12. 共享工程结构

| 现有扩展点 | 增量职责 |
|---|---|
| data/.../robocasa_exact_window_cached_sft.py、robocasa_exact_window_policy.py、原Local producer | 在当前样本身份与索引上增加空间输入/静态文本/state配方，不复制基础Dataset |
| action/utils/json_formatter.py、transforms.py | 新文本配置、idle输出控制、训练服务统一序列化 |
| model/generator/mot/ | 新Global Reader等职责模块；扩展memory_prefix和既有two_way attention边界 |
| unified_mot.py／cosmos3_vfm_network.py／omni_mot_model.py | UND文本准备、native载体、Global/Local联合路由及采样接线 |
| 当前GroupedLocalMemoryTrainer与训练入口 | 阶段、参数组、恢复与统计，不创建R1/R2平行训练循环 |
| inference/与现有action_policy_server_robocasa.py | 同Session Global缓存、实际在线空间输入、原有事务复用，不新建第二Policy服务 |
| 根仓g2库 | 适配已验收空间资产／在线生产结果；不让模型反向import tools/CLI |

推荐新增文件名允许作者依当前树调整。核心要求是依赖方向和唯一实现：离线reader不加载VAE/ROS/MuJoCo；model只消费tensor/小型元数据；共享model模块不反向依赖inference服务。确有共同配置与规范化函数时放可导入公共库，不复制到两个入口。

## 13. checkpoint与配置身份

新checkpoint记录Global开关/结构、type/geom/PE ABI、文本协议/idle策略、UND来源与冻结、VAE recipe、top variant、state15 recipe、阶段与参数组、dropout、cache schema、数据/划分身份及init checkpoint。D_model等由实际模型读取。

旧checkpoint用旧配置仍可载入；Global-off不消费新的随机初始化、不改变旧RNG/序列/Local行为。G1→G2只允许明确的新Global键初始化，不重置旧模块。G2同job恢复必须严格校验完整结构/数据/阶段；不通过修改identity文件把语义变化伪装成续训。

所有新增可训练模块进入nn.Module/state_dict/FSDP/optimizer，不能藏在Dataset、全局dict或临时CUDA tensor中。每个配置开关都有actual config输出和测试，不只写在YAML里。

## 14. 尚待ABI细化或实测的事项

| 项目 | 如何收口；不重开已确认主线 |
|---|---|
| geometry字段、归一化、PE频率、有效patch mask | 对接DATA_A/B真实元数据与小样例；不需要重训VAE |
| norm/激活/初始化尺度、语言投影内部细节 | 最小共享实现、梯度/数值检查；不偷偷增加新架构 |
| UND前置与native K/V等价、FSDP冻结/解冻 | 参考/优化两路径CPU＋真实GPU/分布式验证 |
| 稳定G1 checkpoint的精确路径与SHA | 核对评测、权重完整性及配置；不称历史iter27700必为当前最佳 |
| S_A/S_B、有效batch/GA、预热/衰减 | 固定源码小样例测资源与有效consumer后预先定稿 |
| 梯度裁剪/优化器低层设置/生成步数 | 继承并核对实际G1配置，变化单独记录 |
| cache容量、并发资源、吞吐目标 | 测hit/miss与单/多Session，不承诺未知提速 |
| 正式评测场景/样本量/选择规则 | 在查看正式测试结果前固定，保留配对证据 |

上述不阻塞独立模块的实现与CPU测试，但不能在真实输入缺失时假称端到端通过。正式训练参数文件未定稿前不启动R1/R2正式训练。

## 15. 来源定位与事实边界

下列固定源码是本设计的接口依据，不代表本次重跑过全部项目。编号为文档内引用。

- [S01 Wan接口](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/model/generator/tokenizers/wan2pt2_vae_4x16x16.py)：T=1/压缩因子/latent_ch。
- [S02 共享formatter](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/data/generator/action/utils/json_formatter.py#L83) 与 [transform](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/data/generator/action/utils/transforms.py)：原JSON及idle行为。
- [S03 exact-window样本](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft.py#L128)：由action15计算idle_frames。
- [S04 Policy Server](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/scripts/action_policy_server_robocasa.py#L1314)：推理formatter路径。
- [S05 reasoner hidden](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/model/generator/mot/unified_mot.py#L1874)：独立UND前向与最终norm。
- [S06 当前请求内缓存](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/model/generator/mot/inference_text_kv_memory.py)：非现成跨replan缓存。
- [S07 K/V与normalization](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/model/generator/mot/unified_mot.py#L760)：UND→GEN norm、RoPE、外部prefix投影。
- [S08 Edge参考配置](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/model/generator/reasoner/nemotron_3_dense_vl/configs/Nemotron-2B-Dense-VL.json)。
- [S09 Local prefix上下文](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/model/generator/mot/memory_prefix.py)：Local-only长度／presence假设需要增量扩展。
- [S10 G1训练入口](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/examples/psm_wma_robocasa_corrected_phase5.py#L865)：参数组、LR倍率与fresh跳过local_memory。
- [S11 Local fast-state实现](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/model/generator/mot/local_evidence.py#L195)：inner grad mode和外层/fast-state区分。
- [S12 G2投影/箭头](https://github.com/wxwy/psm_wma/blob/fe1089fb925d86697bebd9bef18608d9c9eae87b/g2/views/robot_pose_marker.py#L24)：真实底盘frame及像素映射；state转换不能盲用同名base。

本文确认的是设计。模型代码、真实梯度、缓存等价、训练速度及SR均需配套构建计划逐项交付，不能引用离线VAE的通过结果替代。

## 16. 参数、结构与外部依据的逐项溯源（2026-11-17 增补）

### 16.1 判读方法与证据强度

- **项目原始事实 [S]**：固定提交的代码/归档报告直接支持已有参数、具体行为、接口形状；不能从源码推断尚未进行的G2实验效果。
- **外部研究 [P]**：证明某种一般架构、机制或工程规则存在可行先例；**不等于**G2所选具体超参数已得到RoboCasa实证，也不等于不同论文使用相同模型、输入或损失。
- **Owner确认 [O]**：使该选项成为本项目首版执行合同，后续代码须尊重；**不是**对效果最优的事实判断。
- **待实测 [V]**：需要真实数据、真实模型、闭环任务与匹配基线才能形成判断。尚未测试时不得写“效果更好、最优、必然提速”。

### 16.2 关键结构和数值来源矩阵

| 设计项 / 首版值 | 可复核依据 | 为什么选择 | 证据边界与下一步验证 |
|---|---|---|---|
| Wan单帧网格：48通道、空间下采样16倍 | 项目固定tokenizer [S01] | 保留每个latent网格位置，避免先平均成Local Visual96 | **实现事实**，不证明latent具备现成的文字对齐；真实shape、padding由recipe验收 |
| 可变多视图→固定输出 | Perceiver迭代cross-attention [P01]；Perceiver IO固定latent/灵活query [P02] | 允许M随选图变化而K固定 | **结构借鉴**，论文任务不等于RoboCasa |
| Reader采用查询先读语言、再读视觉 | InstructBLIP instruction-aware Q-Former [P03]；BLIP-2 Q-Former [P04]；Perceiver [P01] | 在压缩前就让读取查询获得任务条件，避免所有M个patch逐一对长文本attention | **类比而非相同网络**；与patch先读语言的方案尚无本项目直接A/B |
| 每patch完整latent投影，不先逐图摘要 | 当前G2需保留空间布局的项目目标 [O]；高维输入有限查询压缩 [P01][P02] | 尽可能不在语言参与前增加无监督摘要瓶颈 | 不保证小物体细节已经被VAE保留，需在真实场景验证 |
| **K_global=64**（全场景共享） | 结构可行性来自[P01][P02]；**数值来自Owner确认的工程折中** [O/V] | 在32/64/128候选范围选择中间起点，避免一开始增加过长GEN前缀 | **没有文献直接证明64在G2最优**；首轮只用64，后续必要时容量消融 |
| **hidden=512、heads=8、head_dim=64、FFN=2048** | Transformer Base对应 d_model=512/h=8/d_k=64/d_ff=2048 [P05, Table 3]；Edge主干参考2048 [S08] | 采用成熟且算术一致的内部宽度，再独立投影到主干2048；避免Reader所有层直接用2048 | **这是可解释的初始化规模先例，不是机器人World Model容量证明**；测实际显存、梯度、任务效果 |
| **语言读取1轮＋视觉读取2轮＋2次64-token SA/FFN** | 迭代查询/多轮读入参考Perceiver [P01]；指令条件查询参考InstructBLIP [P03] | 第二轮查询含第一轮场景证据，可回读原始patch | **具体轮数是Owner确认的G2起点**，论文没有证明该组合最优；与单轮对照后置 |
| 不新增全视觉patch SA | Perceiver的非对称读入/latent bottleneck [P01][P02]；注意力基本运算 [P05] | 避免M×M，利用64个tokens做跨图交互 | **计算量公式为结构推导**：约 K·L+2K·M+2K²；不等于GPU实测延迟 |
| type/geom/patch PE三项相加 | Transformer位置编码思想 [P05]；Perceiver的位置/Fourier特征 [P01]；本项目正交投影数据接口 [S12] | 保持视图身份、空间画幅及图内位置分离，不依赖逐像素深度 | **具体14维geom、二维sin/cos频率、padding mask等属于项目自定义 [O/V]**，不得说是论文直接提供 |
| 不给patch假想表面法向或真实XYZ | 本项目正交投影几何约束 [S12] | 投影平面＋方向缺沿射线深度；避免不真实三维标签 | 属于几何可辨识性约束，不是模型测得的表面真值 |
| 冻结UND、取post-norm逐token hidden | 现有reasoner返回hidden [S05]；冻结编码器＋轻量查询适配的先例BLIP-2 [P04] | 复用同一份Cosmos语言计算和文本身份 | **已有源码能力≠Reader/GEN联合前置一次计算已实现**；需数值/FSDP parity [S07][P08] |
| Global/Local独立投影、每层GEN K/V | 本项目Local前缀 [S09]、MoT内GEN投影/归一化 [S07]；标准attention [P05] | 尽量复用现有路由；不把Global伪装成更大的Local | **注入所有层是Owner选择 [O/V]，没有外部文献在本模型证明最优层范围** |
| TRAIN_A只训Global；TRAIN_B再开GEN | 现有参数分组/Local流程 [S10][S13]；PyTorch自动微分冻结语义 [P07] | 先排查新增分支，再让主干适配；保留G1能力作为起点 | **两阶段优于端到端一次训练尚未验证**；不得用no_grad截断Global梯度 |
| **Global 5e-5 / GEN 1e-5 / action 5e-5** | 历史G1 local profile基础LR=5e-5 [S13]；正式阶段动作组采用5×倍率 [S10] | 新分支可较快学习，已训练GEN更新谨慎，动作适配相对快速 | **G2数值是新建议并获Owner确认 [O/V]，不是照抄G1，也不是论文推荐值**；实际G1动作5×5e-5=2.5e-4，新G2动作5e-5，需防混淆 |
| Local inner_lr=0.1继续沿用 | 固定Local core与profile [S11][S13] | 内层fast更新率与外层LR分开，冻结slow不关闭inner | 旧代码事实；是否在G2联合训练后仍最合适需看验证 |
| A→B保留moments/RNG/Local frontier、FSDP同步 | 现有训练/恢复合同 [S10][S11]；FSDP2文档 [P08] | 避免阶段切换误当作一次重启/重置 | 属于**必须实现并测试的工程协议**，FSDP文档不直接保证我们已有代码完成 |
| 文本dropout=0.1，Reader与GEN同一决定 | 历史RoboCasa配方/default [S14]；CFG原理 [P06] | 延续原始训练设定，并保持两条文本路径条件一致 | 论文解释有条件/无条件训练；**0.1并非论文针对G2给出的最优概率**；GT选图仍泄露部分任务定位，不是严格无条件 |
| guidance=1首版单分支 | 当前Policy Server默认值及生成分支 [S15]；CFG理论背景 [P06] | 先避免额外分支和CFG搜索改变实验解释 | 不代表guidance=1对RoboCasa效果最佳；若以后开启CFG，空文本Global需分别构建 |
| 同Session跨replan条件缓存 | 项目已有请求内文本缓存 [S06]；固定文本、view版本索引与依赖关系 | 稳定输入可复用、图片/几何变化按实际依赖失效 | **新工程优化，非已有完成能力**；cache-on/off需数值对照，显存/延迟需实测 |
| R0/R1/R2匹配基线与双预算口径 | 项目因果归因设计 [O/V]；历史G1评测档案 [S16] | 识别Global带来的增量，不把新state/增强语言的贡献错归因 | 无外部论文替代配对实验；相同样本预算≠相同计算预算，需报告两个口径与实际资源 |
| 双俯视图默认with_robot、静态增强文本、关闭idle字段 | Owner项目决策 [O]；原formatter与G1/服务行为 [S02-S04] | 保留可控定位实验、训练推理同构、避免未来action统计进入静态文本 | **项目特定合同**，不对应外部论文参数；top两版正式配对消融后置 |

特别提醒：Transformer Base论文中的 `dropout=0.1` 与本项目的**文本条件整体丢弃概率 0.1**不是同一种操作，二者**不得混作一个引用依据**。同理，Transformer Base的 `N=6` 也不是本项目视觉读取2轮的依据。

### 16.3 外部一手来源及其准确适用范围

**[P01] Perceiver: General Perception with Iterative Attention** — Jaegle et al., 2021，原文 https://arxiv.org/abs/2103.03206 。支持：用少量latent queries跨注意力迭代提取高维输入特征，避免全部原始输入之间的全连接注意力；可结合位置/Fourier特征。**不支持**直接断言本项目Wan 48通道网格、两轮视觉读取或64个query会达到更高SR。

**[P02] Perceiver IO: A General Architecture for Structured Inputs & Outputs** — Jaegle et al., 2021，原文 https://arxiv.org/abs/2107.14795 。支持：灵活查询/固定latent瓶颈处理可变输入输出，输入规模的可扩展组织。**不支持**“每张图必须给多少token”、固定64、或全部GEN层prefix的最优性。

**[P03] InstructBLIP: Towards General-purpose Vision-Language Models with Instruction Tuning** — Dai et al., 2023，原文 https://arxiv.org/abs/2305.06500 。支持：instruction-aware Query Transformer从视觉编码器提取任务相关特征，说明“任务影响查询再提取视觉”有先例。**差异**：论文使用预训练视觉-语言模块/Q-Former，不是当前的Wan VAE＋RoboCasa动作损失；没有直接比较本项目第一种与第三种Reader。

**[P04] BLIP-2: Bootstrapping Language-Image Pre-training with Frozen Image Encoders and Large Language Models** — Li et al., 2023，原文 https://arxiv.org/abs/2301.12597 。支持：固定预训练组件与小型可训练查询/适配模块的工程路线。**差异**：预训练步骤、编码器和监督目标不同；不能拿BLIP-2效果当作未做视觉语言对齐的Wan VAE已经具备对象语义的证明。

**[P05] Attention Is All You Need** — Vaswani et al., 2017，原文 https://arxiv.org/abs/1706.03762 （具体数值见正文 **Table 3: base**：d_model=512、h=8、d_k=d_v=64、d_ff=2048；位置编码见§3.5）。支持：Q/K/V attention公式、对应宽度先例与sin/cos位置编码的基本思想。**不支持**这些参数在G2机器人动作生成中的最优性，也不支持把论文Transformer整体架构照搬。

**[P06] Classifier-Free Diffusion Guidance** — Ho & Salimans, 2022，原文 https://arxiv.org/abs/2207.12598 。支持：联合训练有条件/无条件预测，以及推理时组合这些预测的一般机制。**不支持**直接决定G2的dropout=0.1或guidance=1为最优，也不保证GT任务选图时得到真正无任务信息的unconditional分支。

**[P07] PyTorch Autograd Mechanics** — PyTorch官方文档 https://docs.pytorch.org/docs/stable/notes/autograd ，重点“Locally disabling gradient computation / Setting requires_grad”。支持：冻结叶参数与整个forward进入 `torch.no_grad()` 的区别；即便GEN权重不训练，也必须保留动作loss到可训练Global输入的反向路径。另见 https://docs.pytorch.org/docs/stable/generated/torch.no_grad 。

**[P08] PyTorch FSDP2 fully_shard** — PyTorch官方文档 https://docs.pytorch.org/docs/stable/distributed.fsdp.fully_shard.html ，重点“User contract / FSDP hooks / register_fsdp_forward_method”。支持：parameter shard/DTensor、forward hook、optimizer构建与集体通信的约束。**不支持**不经真实运行就宣称新增UND前置forward和阶段解冻已兼容现有G1 FSDP2。

### 16.4 项目固定版本参考的补充条目

原第15节的 [S01]–[S12] 继续有效。本节补充直接对应数值和实测范围的来源：

- **[S13] 历史G1基础LR/Local配置**：固定Child的 `examples/psm_wma_robocasa_local_s1.py`，`LR=5e-5` 与 `overlay_local_config`，https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/examples/psm_wma_robocasa_local_s1.py#L33-L37 、 https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/examples/psm_wma_robocasa_local_s1.py#L475-L495 ；与正式训练入口[S10]的动作组 `5.0` 倍率结合解读，不能直接误写成G1动作峰值也是5e-5。
- **[S14] G1/RoboCasa文本dropout代码配置**：固定 `robocasa_exact_window_cached_sft.py` 中 `cfg_dropout_rate=0.1` 默认和transforms的真实传递，https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft.py#L175-L215 ；另见 RoboCasa原配方 https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_robocasa_nano.py#L170-L185 。**正式run的有效展开值仍需读取其冻结config**。
- **[S15] 在线服务guidance与采样分支**：固定 `action_policy_server_robocasa.py` 默认 `guidance=1.0`，https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/scripts/action_policy_server_robocasa.py#L497-L508 ；采样仅在 `guidance!=1.0` 需要文本CFG，https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/model/generator/omni_mot_model.py#L4200-L4222 。新项目仍须验证其他后处理路径不会额外生成分支。
- **[S16] G1历史评测归档（非匹配消融）**：R03 `iter20000` 454/900 https://github.com/wxwy/psm_wma/blob/875ad79189a4aaa903849b6a5a4cea0eaf62e523/docs/eval/reports/2026-11-04_R03_900EP/README.md ；R07 `iter27700` 580/900 https://github.com/wxwy/psm_wma/blob/875ad79189a4aaa903849b6a5a4cea0eaf62e523/docs/eval/reports/2026-11-05_R07_900EP/audit_summary.json 。报告明确运行环境、采样和源码等存在差异，**不能将历史SR差直接归因Local或当作G2训练结果**。

### 16.5 引用审计与实施作者执行要求

1. A/B/C/D四路Codex实现时，对每个因研究启发而选用的默认参数记录：引用编号、固定源码版本或论文、实际配置、与论文的差异、数值依据、对应的待验证测试；不得只写“参考Perceiver”而省略具体计算/输入输出。
2. 对任何改动且与已确认默认值不同的几何规范、初始化、mask、norm、FSDP/optimizer分组，先说明对原有合同的影响；实验数值优化必须有受控结果，不能用论文名义替换Owner决策。
3. 除已经确认的初始默认值外，warmup/decay、S_A/S_B、token数消融、真正的资源预算仍属于M08/M09样例后定稿；样例/模拟测试不能宣称正式H100闭环性能或SR已验证。
4. **不要将 [P01]–[P08] 解读为八篇针对PSM-WMA的对照研究。**这些是当前结构设计的公开依据和工程规则，最终科学结论依赖相同G1初始化、R1匹配基线、R2完整系统的可复验闭环证据。
