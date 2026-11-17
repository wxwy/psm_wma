# PSM-WMA G2 模型侧增量构建任务与小样例验收计划 v1.0

日期：2026-11-17。状态：**实施指令／验收规格；本文件发布时不宣称新增模型代码、测试、GPU样例或训练已经完成。**

唯一模型语义依据：[G2模型侧设计补充v2.2](PSM-WMA_G2_model_design_addendum_v2.2_2026-11-17.md)。任务详情是规格，不替代`TODO.md`唯一待办队列；作者开始编码时在TODO认领下列ID，并在SESSION声明文件范围和准确基线。

## 1. 执行边界与起点

Owner 已要求：把已确认设计落实到仓库，在现有G1代码上实施，通过小样例后确定正式运行参数。Codex负责源码、静态/CPU和候选PR；GPT负责设计对齐/独立审核，执行侧负责服务器真实样例。发布Issue不等于编码进程已启动，须有作者ACK和实际提交。

本任务允许在独立Root/Child候选分支增量改造模型、共享数据/formatter、trainer和现有服务所需接口。与离线Issue #54文件认领协调。不是全局禁止修改旧代码，而是禁止复制三套流水线、破坏旧配置或覆盖他人修改。

本次文档基线：Root V3=`fe1089fb925d86697bebd9bef18608d9c9eae87b`，Child/Gitlink=`d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`。开始前重新核实最新V3、Child和相关PR，不以历史SHA覆盖更新。V2冻结，不作为实现分支。

不在本轮文档发布时启动任何训练。真实小样例应在固定候选与CPU通过后，公布命令、环境、资源、输入、输出及判据，由指定执行侧运行；正式R1/R2长训练、全量评测、合并及旧数据删除不因文档通过自动发生。

读取顺序：根AGENTS、SESSION、canonical live Inbox、TODO、MEMORY/DECISIONS、v2.0与离线v2.1、本文与模型v2.2；进入Child读取其AGENTS。执行验证按适用治理技能和最新Owner边界，不重复旧已关闭Gate。服务器不commit/push，不外传私有图像/数据；仓库源码实现，服务器运行固定源码。已有可用环境优先复用，不因写模块随意安装依赖。

## 2. 与另一会话的接口同步（M00）

离线顺序保持`DATA_A → DATA_B → DATA_C`；不要与`TRAIN_A/B`混用。模型模块可先用fixture开发，但真实端到端Gate等待小样例数据对齐。

向Issue #54补充以下已确认新约束，不重写其任务主体：

1. **每个Atomic episode一份静态增强指令**，由子任务初始化GT绑定和初始SG生成；后续物品位置变化不刷新；文本明确标“初始空间上下文”。原v2.1中按当前事实逐状态刷新文本的建议被此决定覆盖。原始caption及来源保留，初始化关系不冒充动态on/inside。
2. **俯视图提供with_robot与without_robot两种版本**。干净底图先生成，再叠加标识得到另一版本；几何一致、内容/更新引用独立。无标识图不因底盘移动而触发箭头更新。具体文件名由producer唯一声明，模型不自行猜新路径。
3. 所有有效view及两种俯视图都按已启用输出profile编码；仍每episode每逻辑view一文件，复用#52/#53，不新建缓存系统。读取只取所选版本与所选图。
4. **idle_frame文本关闭在共享模型formatter实现**，不是离线删除动作标签；离线不用导出未来动作统计作为增强上下文。不要让两个团队分别写一套prompt函数。
5. 接口须返回图片对应投影元数据、当前成员版本、逻辑状态与物理owner、VAE recipe和task binding/source identities。state15转换仍由DATA_B提供，模型只校验/调用其共享实现。

M00输出：短ABI说明、字段所有者和演化版本、缺失字段清单、双方不重叠的文件认领。无需再等待一轮泛化架构审批；具体数据尚缺不阻塞独立Reader/CPU测试。

## 3. 实施任务拆分

| ID | 范围 | 依赖 | 交付状态起点 |
|---|---|---|---|
| G2-M00 | 数据/文本/双俯视图接口及文件归属 | 本文、#54 | TODO |
| G2-M01 | 共享配置、tensor载体、空间元数据与mask规范 | M00 | TODO |
| G2-M02 | 64×512任务查询Global Reader | M01；可fixture | TODO |
| G2-M03 | 共享静态formatter与UND文本准备 | M01 | TODO |
| G2-M04 | 全GEN层Global/Local联合prefix | M02/M03 | TODO |
| G2-M05 | G1 warm-start、两阶段optimizer、FSDP/恢复 | M04 | TODO |
| G2-M06 | 现有服务接入、跨replan缓存和生命周期 | M04；M03 | TODO |
| G2-M07 | 集成CPU/静态/数值与回归验收 | M01–M06 | TODO |
| G2-M08 | 固定源码真实小样例／分布式验证 | M07＋可用对齐数据 | TODO／执行侧 |
| G2-M09 | 参数定稿、R1/R2精确runbook和候选发布 | M08实测 | TODO |

可分多个小提交与stacked Draft PR，但每一步必须有可运行代码/测试，不把同一需求拆成无限审批。一个文件一个作者，Child先发布后Root绑定准确Gitlink；正式V3是否推广另按审核处理。当前任务计划不将未知测试状态标DONE。

## 4. 每项构建内容和验收

### M01：共享配置与载体

在现有model/data/config体系扩展，不把Global隐藏在Dataset临时对象里。配置语义见第6节，最终字段名须映射到仓库规范。

- `global_memory_enabled=false`兼容原模型配置与checkpoint：不创建Reader、不额外消费初始化RNG、不读取view payload。
- 原始样本读取/action/G1 latent/Local流复用。空间输入通过小型provider接口依赖注入，通用Cosmos模型不import根仓`tools`或producer。
- 可变数量view与patch；有序稳定view身份、room/island分组、selected variant、每项latent/geom/source。shape/dtype从recipe验证，不按文件名猜。
- type是类别向量；geom是view级投影/物理尺度；PE是patch位置。14维候选、MLP宽度、位置编码频率/边界mask等需列出确切ABI与样例依据，不伪称已由Owner冻结所有数值。
- 分组ID不变成跨episode语义embedding；图像不是时间序列。正常缺方向不同于已声明文件损坏；异常不得静默跳过。

CPU必须覆盖：1/多view、多Island、mixed-size、late-appearing/absent view、两种top版本、padding/partial mask、缺关键投影字段、错误source/recipe、跨sample隔离；R1证明不打开latent文件。避免同一个决策实现两套离线和在线几何计算。

### M02：Global Reader

建议新增`cosmos_framework/model/generator/mot/global_memory.py`或相同职责的少量模块，复用仓库attention dispatcher，不复制Transformer库、不直接引入另一attention后端。

- 输入完整VAE网格→逐patch共享投影与元数据→1次语言读取＋FFN→2个独立视觉CA/64-token SA/FFN block→final norm/独立输出projector。
- K64、D512、heads8、FFN2048；主干宽度由实际配置取得。无视觉patch全SA、无逐view预摘要、无上一时刻Global递归输入。
- 语言为多个UND contextual tokens；空文本有效处理，不以全mask产生NaN。
- 可学习queries应有可复现而不同的初始化；不能64个完全相同向量导致对称退化。初始化尺度和norm/activation记录，不暗加门控结构。
- 输出及所有模块正式注册，tensor设备/精度跟随模型，支持state_dict和小型CPU fixture。

CPU验收：shape、finite、mask隔离、图像/语言/几何输入影响、所有训练参数在普通非空样本可达梯度、state_dict往返；缺失方向不占真实token；打乱数据的同时正确重排metadata后结果按允许数值误差一致。attention热图或非零梯度不作成功率证据。

### M03：静态prompt与共享UND准备

增量修改现有formatter/transforms、服务prompt构造和UND特征入口。不得复制R1/R2 formatter或新建文本API服务。

- R1/R2 idle字段删除；legacy配置保持原内容。JSON路径必须真实受配置控制，非JSON兼容也验证。
- 非dropout文本只依赖静态子任务和合法固定生成配置。替换未来action、当前窗口、当前SG/state不能改变token IDs。训练与服务一致；按实际token/position缓存。
- 文本dropout=0.1，由consumer唯一抽样，Reader和GEN同步；activation checkpoint重算复用决定。保留GT选图；未新增整支路dropout。
- 复用同一个UND参数实例，前置文本计算返回post-norm多token hidden与GEN可用逐层K/V。不生成新文字，不加载独立语言模型。
- 比较前置文本路径与原生two_way文本分支：位置/类型embedding、RoPE、UND→GEN归一化、GQA维度、packing/pad、dtype及输出。利用已有代码提取共享helper，不能复制完整forward。
- frozen UND可无梯度，但trainable Reader及任何相关trainable GEN norm不得被detach。FSDP注册和collective进入顺序真实验证；不能从Dataset私调FSDP内部模块。

CPU参考：共享formatter新旧golden、完整/空文本、每样本长度不同、没有有效语言token、token count和position一致；相同UND权重的hidden/GEN-KV对应。真实模型数值在M08，mock不能冒充。

### M04：联合prefix

扩展`memory_prefix.py`和现有attention调用点；集中处理各样本Global/Local长度和presence。不能增大k_local冒充两支路；训练/采样/cache中的Local-only假设一并检查。

- 全部GEN层读取Global，独立global projector/modality，复用层内GEN K/V投影。原UND causal、原生RoPE/position与loss mask不变。
- 完整测试none、local-only、global-only、both及同batch混合，varying原生序列长度与pad segment，不串episode。
- Global-off必须走等价旧路径。Global-on零Value不等于off，加入受控测试防止错误初始化等价论证。
- 单样本、packed多样本、训练梯度及推理请求内缓存分支都明确；不因历史B1优化假定全层Global只服务一个session。
- 已有不支持的context-parallel/CUDA graph模式明确拒绝或保留原边界，不能默认宣称全部支持。不能为绕过新错误全局禁用现有优化；先有正确无缓存参考路径。

验收：原Local-only输出/梯度回归，Global输入→动作loss梯度贯通，各层prefix计数正确，样本置换与单独运行对照。数值容差基于相同runtime精度提前记录，不在失败后任意放宽。

### M05：warm-start与训练阶段

复用现有GroupedLocalMemoryTrainer、parameter selector、checkpoint、RNG和Local sidecar机制。一个训练器通过config选择R1/R2及阶段，不复制training loop。

- G1模型权重完整继承，包括Local；仅Global新增键允许初始化。建立新optimizer/scheduler/数据游标，旧G1运行与checkpoint只读。
- TRAIN_A冻结GEN参数但不no_grad其依赖Global的计算；动作/视频loss可以传回Reader。UND/VAE冻结；Local slow params冻，inner fast update依然运行。
- TRAIN_B Global5e-5、GEN1e-5、action2llm/llm2action/action_modality_embed5e-5；R1同GEN分组。所有参数恰好分组一次，冻结参数不能被weight decay偷偷更新。
- 参数冻结/解冻是FSDP和optimizer工程，不只是字符串选择；输出实际named parameter清单、shape/numel/group/lr/requires_grad供检查。
- A→B在完整GA/optimizer事务边界、所有rank同步；保留Global moments/step、loader/RNG/Local frontier，新解冻组独立warmup。不得清空当前episode的Local来简化切换。
- 原loss及权重不改，不引入新辅助监督。Local inner_lr继承原配方。stageA固定预算，除工程错误不以SR门槛无限拖延。
- G2保存/恢复明确stage/各组step/scheduler/配置/数据版本，模型-only warm-start与同job-resume分开。

验收：小模型参数前后diff；A仅Global变化、B仅允许集合变化；Local fast state确有更新而slow tensor不变；连续运行与切换前后中断恢复对照；2rank CPU分布式/实际FSDP场景分开报告。

### M06：服务与缓存

在现有`action_policy_server_robocasa.py`、Session/reset、batch和Local事务上扩展。不另起G2服务，不修改原始deadline/commit/abort语义。

- 服务接收当前rollout的空间输入/可靠引用；不从专家episode未来时刻读数据。当前scene/state和static subtask身份一致。
- 同Session跨replan缓存UND hidden/KV、任务查询、Global tokens及各层K/V；cache-off始终可用且是验收参考。
- key包含weights/recipe/实际tokens与positions、variant、有序selected views与各content/geometry版本；未选中view变动不误失效，Selected集合改变必须失效。
- 一个请求捕获不可变条件快照，去噪中不更换；reset清理；同episode换任务更新语言/Global而非无条件清空Local；请求retry不重复inner更新。
- 多session隔离、有限预算/淘汰/错误恢复；cache命中不改变采样seed/RNG。不要将普通GEN深层中间量当静态条件缓存。
- guidance=1为首版；未来CFG接口不能把G(T)给去文本分支。训练图不使用旧inference cache。

验收：同权重cache on/off逐步输出及动作对照、with/without top、只动机器人/物体/选择/几何、task switch、checkpoint切换、reset/retry/并发/容量淘汰；hit/miss耗时分开。

## 5. 集成验收矩阵（M07–M08）

| Gate | 必须提供的证据 | 不能据此宣称 |
|---|---|---|
| C0 静态/CPU | 类型/格式/语法、现有相关回归、新协议/reader/formatter/prefix/训练阶段/cache测试原始结果 | 真实Wan/Cosmos性能、成功率 |
| C1 原路径兼容 | 相同权重/输入下G1原配置prompt/token/Local/输出回归；R1/R2共同输入一致 | 新state/新文本下也必须与旧G1输出相同 |
| G0 单设备真实样例 | 实际VAE cache、UND、Reader、GEN全路径forward/backward，A/B一次更新，完整梯度与冻结检查 | 正式训练收敛或SR增益 |
| G1 分布式与恢复 | 目标FSDP布局下freeze/unfreeze、mixed batch、共享UND、checkpoint/resume、stage边界、Local状态连续 | CPU mocks证明真实FSDP通过 |
| G2 推理/在线闭环 | 当前rollout空间输入、状态、Local事务、缓存on/off、Session隔离；短代表任务 | 少数episode证明收益或900EP完成 |
| R 参数定稿 | 实测有效consumer/batch、资源、时间、初始化来源、预算/评测清单 | 未测配置称最优 |

### 5.1 最小真实样例选择

推荐从已保留CloseBlenderLid/000000、CloseFridge/000502、NavigateKitchen/002104、PickPlaceDrawerToCounter/005077中选择覆盖静态、机器人位移、物品变化、Island和缺方向的记录，实际source须从DATA_C索引取得。不要求将服务器原始样本上传GitHub。

至少覆盖：初始Local缺席与后续Local存在；3个以上decision windows及更新/引用两类；with/without top；B1与一个真实mixed B>1；正常与空文本。具体样本数/GPU清单由执行runbook固定，不为了凑数量重跑整库。

训练smoke优先遵守当前仓库GA=1约定，不外推正式GA；记录有效consumer而非仅名义batch。先单设备，再用实际分布式布局验证关键路径；可用资源不足时明确NOT_RUN/BLOCKED，不假称8卡通过。

### 5.2 精确执行命令由作者随代码提交

本文件不伪造尚未实现的CLI。M07交付时必须同时提交能直接运行的runbook，列出：

| 字段 | 要求 |
|---|---|
| source | fixed root/child/Gitlink、原始基线diff、干净或明确工作区状态 |
| command | 完整shell命令、cwd、所有关键env、可重复seed |
| runtime | 已验证解释器、Torch/CUDA/attention后端、GPU绑定、FSDP/GA与精度 |
| inputs | checkpoint绝对路径/身份、数据清单/recipe、prompt/state/geometry版本 |
| outputs | 独立日志、JUnit/JSON、profile、checkpoint与失败证据目录 |
| assertions | 在运行前写明的数值、梯度、source、完整性和恢复标准 |
| limits | 有界smoke步数/样本/时长预算，不启动正式R1/R2 |
| result | PASS/FAIL/BLOCKED/NOT_RUN分别记录，失败原日志保留 |

不能将未知参数替换成看似正式的命令并实际执行；不能修改训练运行中的目录或覆盖旧G1权重。

## 6. 最小实验配置和正式参数定稿（M09）

已有已确认默认如下，字段名为语义示例，最终按共享schema映射：

```yaml
model_profile: g2
local_memory:
  outer_trainable: false
  inner_updates_enabled: true
  inherit_g1_recipe: true
global_memory:
  enabled: true                 # R1=false；R2=true
  k_global: 64
  hidden_dim: 512
  num_attention_heads: 8
  ffn_hidden_dim: 2048
  num_language_blocks: 1
  num_visual_blocks: 2
  memory_self_attention_per_visual_block: 1
  full_visual_patch_self_attention: false
  top_view_variant: with_robot
language:
  source: cosmos_und_post_norm_tokens
  und_trainable: false
  scope: static_subtask_initial_context
  reader_and_gen_share_effective_tokens: true
  append_idle_frame_text: false
  cfg_dropout_rate: 0.1
inference:
  guidance: 1.0
  conditional_cache: session_cross_replan
  reference_cache_off_supported: true
optimizer:
  global_peak_lr: 0.00005
  gen_peak_lr: 0.00001
  action_adapter_peak_lr: 0.00005
  preserve_global_state_at_stage_switch: true
```

这些不是可以直接传给旧CLI的已实现参数；作者必须提供配置解析、日志实际展开与测试，避免无效开关。

### 6.1 三组与预算

- R0为历史G1参考，不新增正式训练。
- R1/R2从同一G1初始化，共享新静态文本、state15、Local运行和GEN分组设置；R1无Global。
- R2：S_A Global-only＋S_B Global/GEN；R1：持续GEN训练，保留S_B与S_A+S_B检查点。主比较总有效样本，辅助GEN更新次数；计算成本另报。
- 沿正式数据划分，不按窗口泄漏episode。评测以实际场景/初态清单配对，沿既有官方成功判据，不用专家未来SG。
- 首批只两条训练。with/without标识的训练匹配消融后置；Reader方向/K/层数搜索再后置。

### 6.2 运行前必填，而非现在猜数值

| 参数 | 定稿依据 |
|---|---|
| init_checkpoint与SHA | G1权重/Local完整、配置与可用评测证据；R1/R2同源 |
| geometry ABI、PE及归一化 | 真实producer元数据、DATA_B坐标规范、样例检查 |
| 实际sample/consumer计数、microbatch、GA、FSDP | 峰值显存、梯度正确性及数据等待时间 |
| S_A/S_B和总数据预算 | 先定有效样本预算，再依实际batch换算 |
| warmup与decay | Group-specific update clock；R1/R2口径公开，不用测试集选长度 |
| optimizer低层配置、clip、loss weights | 继承实际G1并冻结显式变化 |
| denoising/replan/horizon与评测清单 | 正式比较双方一致；配置与source可复验 |
| cache预算与GPU拓扑 | 单/多Session、hit/miss实测，不承诺未经测量的加速 |
| 数据版本与产物覆盖 | DATA_C证明完整，两个top variant/静态文本可读 |

M09提交正式runbook与机器可读resolved config，另行进入运行流程；本计划不自动启动长训练或900EP。

## 7. 必须交付的文件与审查方式

每批作者交付：固定源码Root/Child及Gitlink、最小diff、相关既有与新增测试原日志/JUnit、静态检查、输入输出合同、精确复现命令、实际完成范围、未运行项。代码评审与真实数值/性能分开，不把作者自测写成独立验收。

建议每项测试有明确ID，能映射到模型v2.2的M-D01…M-D24。尤其必须有受控旧行为/错误行为negative test：idle字段未关闭、Global伪零关闭、wrong sample offset、跨Session缓存、错top variant、过期trainable cache、stage切换重置Local、warm-start漏载Local。

源身份/训练数据/运行参数冲突时具体说明，保留失败证据；不能为通过Gate而放松样本隔离、未来信息、数值容差或正式数据合同。原生nav_sg、V2、旧G1数据与已完成结果不改。

## 8. 可直接转交Codex的启动指令

> 先完整读取模型设计v2.2与本文，核对最新V3/Gitlink、#52/#53/#54及当前文件认领。按M00→M01/M02/M03→M04→M05/M06→M07顺序，在现有G1共享代码上实现和测试，不再开展一轮泛化设计、不复制R1/R2工程。先给简短ACK、准确基线与首批文件/ABI，随后交实际代码与CPU结果。独立Root/Child候选和Draft PR，不自动合并；服务器真实样例由执行侧在固定源码上完成M08。小样例后定稿M09运行参数，不启动正式训练，不修改并行离线producer；接口差异以Issue #54同步，缺真实资产不阻塞可用CPU模块。未运行项目标NOT_RUN，发布任务不等于执行完成。

本次文档归档只建立实施依据。TODO/SESSION中的实施状态须由真实ACK、代码提交和测试证据更新，禁止仅凭本文件把G2模型标记为已实现。
