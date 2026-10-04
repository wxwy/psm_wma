# PSM-WMA V3 Local-TTT on Latest Cosmos3 RoboCasa
## Detailed Design v3.0

- 日期：2026-10-04。
- 状态：Owner 已逐项确认功能设计；本版本完成文稿复核并发布，**不是实现验收或训练启动批准**。
- 目标：以 latest official Cosmos3 RoboCasa/raw15 为 host，移植 V2 已验证的 Local-TTT，恢复 Policy/Local 共用 composite current latent 的单一视觉来源。
- 本轮范围：设计文档、文档索引、review、canonical handoff；不修改生产代码，不更新 child gitlink，不接触训练服务器、数据集或 checkpoint。
- 本轮发布前 root：`5f6552adfcde1e6596f421aefb2d21f58cfb8a4b`；所绑定的现有 child/gitlink：`c00a014444083c7c554fff7626f48cceaf5c5c31`。该 child 仍是**待整改实现**，不得因新设计发布而视为已符合本设计。
- 本轮 GitHub 核实的官方 main：`NVIDIA/cosmos-framework@cf5d68c00d97ccd2480a2320ed652b92dec63102`；V2 功能参考：`wxwy/cosmos-framework@e3dc9ecce0a4a7223245dc4f5b5efde7b709fd92`。后续实施固定 exact upstream SHA，不跟随浮动 main 静默升级。

**生效与覆盖规则**：本设计以本会话后半段 Owner 的逐项确认为依据，覆盖此前 v1.0/v1.1 中将 B1 双相机 causal-endpoint 视为正式 Local ABI、继续使用 iter500、以及相应 streaming/18-task 执行 Gate 的结论；早期草案中 N=100、原始数据集主导 corpus、要求先训练 native 模型等条目均不再生效。历史文档、代码和实验产物保留，不静默改写历史。

**角色**：Owner 负责最终技术决策；ChatGPT 是唯一代码修改、commit/push、gitlink 更新及 Gate 下发者；ds/ds_pro 仅执行经授权的测试、采集 evidence 和反馈，不得修改生产代码或正式测试。旧 AGENTS/ledger 中冲突的角色条款以此处记录的最新 Owner 指令为准。

## 0. 术语、来源与复核说明

本文保留已确认草稿的 1–61 项组织，并修正表达歧义，不引入新的算法或实验方向。

| 符号 | 含义 | 默认值/约束 |
|---|---|---|
| `H_pred` / `chunk_length` | Policy 一次生成的动作数量 | 16；训练需匹配 cache |
| `R` / `replan_steps` | 仿真器在下一次推理前实际执行的动作数量 | 16；允许 4/8 等，`1 <= R <= H_pred` |
| `T` / `ttt_tbptt_steps` | 训练时截断可微 fast-update 链的 segment 长度 | 16，可配 32 等；与 H_pred、R 独立 |
| `Z_t` | 以 source frame t 为起点的完整 exact-window latent | `[5,48,H_z,W_z]`，当前 H_pred=16 |
| `z_t = Z_t[0]` | t 时刻当前 composite frame 的 latent | `[48,H_z,W_z]` |
| `v_t` | 从 z_t 提取的 Local visual96 | `[96]`，V2 的 `(1,2)` adaptive average pooling |
| `a_t` | t 时刻的 canonical raw15 动作记录 | 与 pre-action z_t 配对；不是 state token |
| `W0` / `W_t` | 可学习通用初始化 / 某 slot 的 episode 内 fast state | W0 是 slow parameter，W_t 是 runtime tensor |
| `p_s` | 供 consumer s 使用的 Local prefix | 只能来自 source step `< s` 的 completed evidence |

官方现有 CLI 的 `--action-horizon` 可能表示 R，而训练配置中的 horizon 常指 H_pred：adapter 必须显式映射两者，日志同时打印，不能因名称相近把它们或 T 绑为同一参数。

来源标识：`[O]` 为本会话 Owner 已确认的目标；`[V2]` 为已读取的 V2 源码功能；`[UP]` 为固定官方 SHA 的实现；`[G]` 为待后续 Gate 证明的运行时性质。设计成立不等于 `[G]` 已通过。

# 1. 背景与目标

V2 已完成 Local-TTT 训练及 RoboCasa 仿真，Owner 观察到有行为效果但效果不理想；随后官方 Cosmos3 增加 RoboCasa/raw15 支持，因此需要升级 host，同时继承 V2 Local-TTT 功能。[O]

```text
latest official Cosmos3 RoboCasa host
+ official raw15 action/state/eval support
+ V2 Local-TTT 功能
= Corrected V3
```

raw15 是本项目已选的动作表示，不把“官方支持”写成已证明本项目 SR 足够高；实际效果仍由训练及行为评测验证。

# 2. Authority 划分

Latest Cosmos3 负责 RoboCasa loader、camera/action/state、Wan VAE、policy/flow matching、packing、FSDP/DCP、server、simulator 和 action decoder。[UP]

V2 提供 Local evidence、W0/fast update、K/Q/V、Local prefix、inner/outer 关系、episode continuity、slot isolation、TBPTT、reset/replay/transaction/resume 的功能语义。[V2]

优先使用官方扩展点；接口可以改变，不能另造一套 Local 视觉语义。H_pred/R 默认 16、cache-first 等是 Owner 明确批准的项目配置，不盲目继承官方默认 32。

# 3. 当前 V3 错误路线处理

iter500 已被 Owner 明确排除为 Corrected V3 的正式模型或初始化来源。[O]

```text
退出 active route：left -> VAE，wrist -> VAE -> latent concat -> B1 visual96
目标 route：       [left | wrist] pixel concat -> canonical VAE -> current z_t
```

不再继续训练、修复或评测 iter500 来代替 Corrected V3；checkpoint、日志、MP4 和既有 review 全部保留作历史证据。本决定不是文件删除授权，也不将 0/18 的所有原因都归因于这一项编码错误。

B1 双相机 H5 Local cache、episode endpoint 映射、为该表示引入的 Local streaming inference 退出正式链路；保留历史代码不意味着继续使用。

# 4. Corrected V3 初始化

从经核实版本和权重标识的官方 `Cosmos3-Edge-Policy-DROID` / direct-DROID 基础 checkpoint 出发，直接训练 `RoboCasa + raw15 + Local-TTT`。[O]

“支持 raw15 配置”不等于该 DROID checkpoint 已在本项目 RoboCasa corpus 上微调；必须记录权重 revision/hash、action domain/head 的加载规则及新增 Local 参数初始化。

不要求先单独训练 native RoboCasa SFT，再将它作为 Local 模型的前置权重；native 训练是后续可选对照，不是 prerequisite。

# 5. Camera / Visual Authority

每个 observation 使用 `agentview_left | wrist`，按官方 `left_wrist` 顺序先在像素宽度上拼接，再走共同的 resize/pad、归一化与 Wan VAE。[UP][O]

Policy 与 Local 共享同一 z_t 定义，不分别对两相机做 VAE、不做 latent-level camera concat、不复制 preprocessing。

源图像常为两张 256×256；VAE 实际 canvas 和 latent 空间大小必须来自已验证的 cache/preprocessing metadata，不能把未经过 resize 的 256×512 当成所有现有 cache 的固定输入尺寸。

# 6. Offline VAE Training Contract

默认 H_pred=16，每个训练 anchor t 使用 17 帧 exact window：`t..t+16`；按该 window 重新开始的 causal VAE 编码得到 `Z_t=[z_t, f_t,1, f_t,2, f_t,3, f_t,4]`。[O][V2]

`z_t` 是当前帧 latent；后四个是该 window 内未来观测的时序压缩 latent，不是四张相互独立的未来单帧编码。

这不同于“从 episode 第 0 帧累计编码后取 floor(t/4) endpoint”，两者不得混用；dtype、canvas、VAE 权重及 encode 配置由 cache manifest 和 parity Gate 校验。

# 7. Policy Visual Consumption

训练时 Policy 以 z_t 为 clean observation conditioning，未来四个干净 latent 提供官方 flow-matching 路径的加噪来源和监督来源。[O]

保持官方 noise schedule、prediction parameterization、condition/loss masks：监督 target 由干净 latent 与 noise 按官方目标构造，不能因为文中称为“label”就擅改成预测干净 x0 的 MSE。

当前 latent、future latent、action target、state token 必须由 sequence plan 明确区分；不得将真实未来视觉当成推理 conditioning。

# 8. Local Visual Consumption

Local 只用 `z_t = Z_t[0]`，不使用后四个 future latent。[O][V2]

唯一 visual96 authority 保持 V2 的计算和 flatten 顺序：

```python
v_t = F.adaptive_avg_pool2d(z_t.unsqueeze(0), output_size=(1, 2)).flatten()
# z_t: [48,H_z,W_z] -> v_t: [96]
```

不得替换为 B1 的 `mean48 + RMS48`：两者即使同为 96D 也不是相同特征。相同 `(episode,t)` 的 Policy 与 Local 从同一 cache entry/同一 current encoder 输出取 z_t；Local 在 consumer s 使用的是已经完成的 source `t=s-1`，不是拿 z_s 错配 a_(s-1)。

# 9. Inference Visual Contract

仿真器只提供当前实际 observation；`[left|wrist]` 经与训练一致的 preprocessing 后，以 `T_pixel=1` 在线 VAE 得到 z_t。[O]

不编码未知的未来 RGB，不为 Local 保留 episode-long causal VAE history，不将独立双相机编码或 B1 endpoint 引回正式链路。

这里禁止的是**未来真实观测的编码/输入**；官方联合 action/video sampler 若需要 future latent 的 noise slots、shape placeholders 或自己预测未来 latent，仍按官方实现保留，它们不是“知道未来”。

# 10. Offline Cache 与 Online VAE 的关系

两者是同一 composite 视觉定义的离线/在线执行方式，不是两套视觉表示。[O]

正常训练默认直接读 cache；显式的 online 编码能力用于 parity、诊断或单独指定的 online 运行模式，不能因 cache 缺失、损坏或不匹配而自动 fallback。

同一 RGB 的 `Encode17(window)[0]` 与 `Encode1(current)` 必须通过实际 VAE 数值 parity；因果性支持这一设计，但不能替代对分辨率、padding、dtype、encode 配置及真实数值的核验。[G]

# 11. Training Corpus Authority

指定的本地 latent cache 目录及其 manifest 是训练样本 authority；不从原始 RoboCasa 全集反向决定训练集合。[O]

流程：`cache accepted catalog -> exact identity -> 配套 action/state/text`；原始数据只补齐非视觉字段和诊断所需 RGB，不引入 cache 外训练样本。

不硬编码 N=100，也不硬编码 9036 个 episode。Owner 当前提供的是 target-atomic cache corpus；实际数量必须扫描、验证、打印后才能声明。cache 中未声明且不存在的样本不属于本 run；manifest 已声明却缺失的文件则是错误，必须停止，而不是悄悄缩小 corpus。

# 12. Corpus Identity

每个训练 key 至少绑定 source dataset/revision 或等价 fingerprint、task class、episode（含必要 shard/task 命名空间）、start frame、window indices 和 latent identity。

指令 phrasing 与 underlying task class 分开；不能把 shard-local episode id 当全局唯一，也不能靠目录改名或同一序号推定 source/cache 是同一段轨迹。

对配套 action/state/text 不匹配、缺失、越界、窗口中断、重复 key 均 fail-closed。需要 t-1 evidence 的 anchor 必须有可验证的同 episode 前驱；不得用最近 endpoint、插值、上一条可用样本或 synthetic reset 掩盖缺口。

# 13. Training Corpus Logging

rank0 启动前打印并保存：cache_root、schema、manifest/corpus digest、declared/discovered/accepted 数量、task class 数、episode 数、exact-window 数、有效 consumer 数、缺失/重复/损坏统计、每 task 的 episode/window 数及 min/max。[O]

能从 metadata 得到 source unique-frame 数时一并报告；不能把重叠 window 的 `17 × window_count` 当成唯一源帧数。有效 consumer、PAD、调度尾段和实际覆盖量分开统计，不用优化器 step 数冒充数据量。

同一统计写入 run 的不可变配置快照及 readiness evidence；invalid/rejected 非零不默许带病训练。没有外部完整性参考时只声明“该 cache corpus 内部完整”，不能宣称已覆盖官方全集；不扫描原始数据集来改变 corpus。

# 14. RoboCasa Raw Action

已核实的官方 source loader 读取 base-first 原始 12D：`[base_motion4, control_mode1, eef_delta_pos3, eef_delta_axisangle3, gripper1]`。[UP]

VAE 只编码视觉，不自动把 action 转成 15D；本次不接触训练服务器，现有 cache 是否另附 action/state 及其 schema 仍须在 corpus Gate 读取确认，不能凭“已离线 VAE”猜 action 格式。

默认按 cache identity 获取官方 raw12；若文件明确存了 canonical raw15，必须经 schema/version 校验后复用，禁止重复旋转转换或仅靠维度猜测语义。

# 15. Official raw12 → raw15

复用官方 RoboCasa action authority，将 EEF 的 axis-angle3 转 matrix 再转 rot6d6；base_motion4、control_mode1、EEF translation3、gripper1 按 loader 合同保留。

```text
raw15 = [base_motion4, control_mode1, eef_delta_pos3, eef_delta_rot6d6, gripper1]
```

同一 action conversion 供 Policy target 与 Local action evidence 使用；不额外做 ego 位姿差、dt/速度反演或新建一套预转换 action dataset。训练默认 `action_normalization=None`；padding 到模型 max_action_dim 不改变 canonical raw15 宽度。

# 16. Robot Current State

`use_state=True`，复用官方 state parsing：从当前 observation.state16 提取 EEF position3、quaternion 转 rot6d6、gripper opening1，形成 10D。

raw15 host 下前补 5 个零，得到 `state15=[0,0,0,0,0, EEF_pos3, EEF_rot6d6, gripper_opening1]`；base 当前 pose/velocity 没有作为有效 state 值输入。

该 state 是当前 EEF 状态，不是 delta action，且不是完整 robot16 直接透传；具体坐标系、quat 顺序和夹爪差值全部沿用官方实现。

# 17. State Token 在 Policy 中的作用

H_pred=16 时 canonical action sequence 为 `[state15_t, a_t, ..., a_(t+15)]`，shape `[17,15]`，之后可按官方规则 pad 到 max_action_dim。

state 行走同一个 action2llm，是 clean conditioning token、sigma=0、不加噪且排除在 action loss 和实际执行 chunk 之外。[UP]

训练/推理都必须提供一致的 state；缺失不能补成另一种语义，也不能把第 0 个 state 行当第一条可执行 action。

# 18. State 不进入 Local Evidence

Policy 条件包括 prompt、current vision latent、state15 和已完成历史生成的 Local prefix。

Local evidence 保持 V2 的视觉+动作：`(v_t, a_t)`，不另加当前 robot state，不把 state row、action padding 或未来 target 拼入 Local encoder。[O]

# 19. Local Evidence 定义

一条 evidence 就是“执行前我看到什么，以及这一步我真正提交并执行了什么动作”：`e_t=(v(z_t), executed_raw15_t)`。

它不是 reward、success label、未来视频或整段预测 action；执行动作是否成功完成任务不影响该动作已经执行的事实。

raw15 指 canonical 命令表示，实际 env.step 接收 env12；必须区分预测 raw15、官方 decoder 实际提交的 env12，以及为 Local 留下的 canonical action 记录，详见第 46 项。

# 20. Evidence Chronology

```text
obs_t -> z_t -> choose a_t -> official decode -> env.step 成功返回
      -> 记录 completed (z_t, a_t 的已执行命令表示)
      -> inner update 得到 W_(t+1)/prefix
      -> 可用于 obs_(t+1) 及以后 consumer 的 policy
```

consumer s=0 没有 previous evidence，保持 V2 的 Local-neutral/no-prefix cold start；s>0 时最迟 source 只能为 s-1。

严禁 `(z_(t+1),a_t)` 或 `(z_t,a_(t-1))` 错配；env.step 尚未返回时可暂存 pre-observation，但不能将它计为已完成 evidence。

# 21. Predicted Action 不等于 Evidence

Policy 生成 H_pred 条 action，仿真只执行前 R 条，则只有实际完成的 R 条或遇到 done 前的更短前缀成为 evidence。

未执行预测、失败/取消的命令以及 state row 不得更新 memory；episode 提前结束不得为了凑齐 segment/R 强行再执行动作。

# 22. Local Evidence Encoder

保持 V2 的 visual96/action15 -> evidence feature -> K/Q/V 映射结构与数值定义；action projection 输入由旧 ego20 改为 raw15。[V2][O]

evidence_dim、TTT dim、fast hidden、K、inner_lr 是显式配置；已确认默认优先使用 V2 实验设置，不把某个默认值误写为不可变算法语义。

所有共享映射均为 slow parameters；forward 的广播/并行不能混合不同 slot 的值或改变每条样本的 inner 步长。

# 23. Learnable W0

W0 是 checkpoint 中可训练的 fast learner 初始化，包含 V2 fast MLP 的 in/out weight 和 bias，属于 slow parameters。

每个新 episode 从同一份 W0 建立自己的 fast-state 副本；训练首段的初始化操作必须保留通向 W0 的 autograd 路径，推理只建立运行时副本。

# 24. Fast Weight Update

沿用 V2：`prediction=FastMLP(K_t;W_t)`，inner loss 是 prediction 与 V_t 的按特征均值平方误差，`W_(t+1)=W_t-inner_lr*grad_W(inner_loss)`。

多 slot 时各行是独立 learner；保持 V2 的 row-mean 后求和等数值口径，不能多除一个 B_stream 使 inner_lr 随 batch 缩小。

更新后的 state 用 Q/slot queries 读出 Local tokens；训练保留可微 inner update，推理仍须计算 inner gradient，但不构造供 outer backward 的高阶图。

# 25. inner_lr

默认 `inner_lr=0.1` 是 V2 实验起点，不是理论最优值；作为配置保留，允许后续独立消融。

用 inner_loss、fast_update_norm、fast_state_norm、更新相对量和行为效果判断稳定性；不能直接拿它与 Adam 的 5e-5 比较。本文不启动 0.01/0.03/0.1 消融。

# 26. Local Prefix

Local 读出的 K 个 tokens 经 Local→Policy projection 和 modality embedding 进入 host 的 action-producing path，不是仅计算一个无关 auxiliary loss。

consumer s 的 prefix 来自 completed source `<s`，与当前 z_s、prompt、state_s 一起用于 policy；当前尚未执行的 a_s 不得先写入 prefix 形成环。

需要 matched-input intervention/gradient evidence 证明接线和作用；非零 prefix/fast state 不能单独证明任务已学会。

# 27. Inner / Outer Training

inner 用已完成历史更新 episode fast state；outer 保持官方 policy 的 action/vision flow-matching 目标及 loss mask。

outer 在保留的 TBPTT 图内通过 Local prefix 与 inner-update 链学习 W0、evidence/KQV、Local mappings，同时训练批准的 generation/action 参数。

不另将 inner_loss 直接加权塞进 outer objective，除非 V2 的固定实现确实如此且经单独对齐；不得创造新辅助任务。

# 28. Outer Optimizer 更新什么

训练的功能边界保持 V2-semantic generation + Local；Reasoner/understanding 分支冻结。

已确认 generation 选择语义：`moe_gen`、`time_embedder`、`vae2llm`、`llm2vae`、`action2llm`、`llm2action`、`action_modality_embed`；`language_model.*_moe_gen` 属 generation，不得被冻结 non-generation language_model 的规则误排除。

Local 包括 W0、evidence encoder、K/Q/V、slot queries、Local→Policy projector/modality embedding；旧 `evidence_encoder/ttt_core` 与新 `encoder/core` 仅作显式名字映射，不因名字变更漏训。

沿用已确认 FusedAdam、lr=5e-5、weight_decay=0.05，action2llm/llm2action/action_modality_embed 使用 5x lr multiplier；去重共享参数，记录每组实际 inventory、量及梯度。任何因 upstream weight tying/权重加载而必须改变的例外须在实现 mapping 单独列明。

# 29. Fast Wt 不由 Outer Optimizer 直接管理

W_t 是 inner update 生成的 runtime tensor，不作为新的 nn.Parameter 注册或加入 optimizer param group。

W0 及 shared mappings 跨 episode 学习；optimizer 更新 W0 后，正在进行的 episode 继续自己的 carry，不能偷偷用新 W0 覆盖 W_t。

# 30. Episode 生命周期

`episode start -> clone W0 -> completed evidence 连续更新 W -> done/reset 丢弃 W_t`。

cold start 可按 V2 延迟物化 W0，首个无 evidence consumer 仍无 Local prefix；新 episode 不继承上一 episode 的 tokens/cursor/fast state。

# 31. T / TBPTT

T 默认16，可配32等，表示训练梯度截断和 segment 组织长度；不是 VAE temporal compression、action 预测长度或重规划频率。

T 的有效实现、tail/PAD 和 detach 边界由同一 training runtime 管理；不能在 core、producer、trainer 中各写一套计数而互相漂移。

# 32. T 不是 Memory Reset

segment 结束后保存 W_T 的数值，detach 后作为下一 segment 初值继续；不回到 W0，不清除 episode memory。

推理不存在 outer TBPTT，不因 T=16/32 重置 W；若实现分批 scan 以控制内存，也不能把 T 当作 episode memory horizon。

# 33. 为什么使用 TBPTT

不截断会保留更长的 outer credit-assignment 路径，但代价是更长的可微 inner-update 图、显存及计算开销，并不保证更好优化或更高 SR。

T 是 credit assignment 与资源/稳定性的配置折中；forward memory 连续性不因该折中丢失。本文不引入跨 segment 重连 W0 的替代梯度技巧。

# 34. 多 Slot

每个 slot 独立维护 episode identity、source cursor、W_t、pending/committed 状态和 reset 生命周期。

slot 可以处于不同 episode/不同时间位置；进度不必对齐到相同全局 t。跨 slot 的 memory 泄漏或 owner 重绑定污染必须在测试中 fail-closed。

# 35. Batch 与 Slot

B_stream 默认8（可配置），跨 slot 的同一局部 scan index 组成 batch；每行独立执行 fast update。

batch 是并行计算单位，slot 才是 memory owner。GPU/rank、训练 slot、评测 worker 不是同一概念，日志和 checkpoint identity 需分别命名。

# 36. Outer Loss 如何跨 Slot 工作

各 slot 有独立 W_t，但共享 W0、mappings 和 host trainables；梯度在共享 slow parameters 上按固定 reduction/GA/DDP 规则累计。

loss 应显式声明有效 consumer 的分母、PAD mask、不同 segment 有效长度的权重；`sum_i L_i` 只是示意，不授权将既有 mean reduction 改成 sum 或重复除以 GA/world_size。

保持已确认的 B_stream/GA 组织可配置，当前参考 B_stream=8、GA=2；mesh 的 shard/replicate 实现可适配官方 H100/FSDP，但不得改变统计和梯度尺度。

# 37. W0 与 TBPTT

首段由可微 W0 初始化，首段 outer loss 可回传 W0；carry 在 segment commit 时 detach 后，后续段的 loss 不再沿已截断历史回传该 W0。

后续段仍训练当前用到的 shared mappings 与 host 参数；W0 主要得到 episode 首个有效 TBPTT 段的梯度，不声称所有 late-episode loss 都能回到 W0。

不同 slot 的新 episode 对共享 W0 的梯度汇总；测试同时覆盖首段可达和 continuation 的历史梯度被切断。

# 38. Segment / Episode

episode 按 T 切片且按时间顺序推进；segment 是计算/梯度边界，不是记忆边界。

尾段、PAD、有效 consumer 计数及调度丢弃必须按移植的 V2 行为显式核对并报告，不能因为固定 batch shape 静默掉数据，亦不能用 PAD 动作更新 W。

# 39. Checkpoint 中的 W0

model checkpoint 保存 W0、Local slow mappings 和所需 host 参数；记录确切 config、source/cache identity 和 parameter namespace。

V2 key 到 latest-host key 的映射必须可审计；当前不转换或覆盖任何历史 checkpoint。正式模型导出不包含训练 slot 的 W_t。

# 40. Training Resume 中的 Wt

为连续恢复训练，在独立 runtime/dataloader checkpoint component 中保存各 slot 的 detached W_t、episode/cursor、queue/epoch/frontier 等状态，和 model/optimizer/scheduler 使用同一已提交边界。

```text
iter_xxxxx/
  model/          # W0 + shared trained parameters
  optim/          # 按官方 DCP 实际命名
  scheduler/
  trainer/        # 按官方格式保留 RNG/scaler 等
  dataloader/     # 独立 rank/slot runtime Wt + frontier
```

这是组件划分，不强制每个 W_t 一个文件；复用官方 DCP/per-rank 机制。未完成事务不发布为可恢复 snapshot，model 与 runtime iteration/config/corpus 不匹配须停止。

# 41. 推理不加载训练 Wt

部署加载 model 中的 W0 和 slow parameters，不加载训练的 optimizer、scheduler 或训练 slot runtime。

每个 eval episode 独立从 W0 开始；这是训练恢复与模型推理两种不同加载模式，不可混淆。

# 42. action_horizon / chunk_length 默认

所有项目 training/server/eval launcher 的公开默认值统一16，但分别命名 H_pred 与 R：training/server 的 chunk_length 对应 H_pred，eval 的 action_horizon/replan_steps 对应 R。

resolved config 必须打印 `H_pred=16, R=16, T=...`；从 checkpoint 提取配置与 CLI 显式值发生冲突时应报错，不能悄悄保留官方默认32。

仅做默认值适配，不以此要求修改不属于本项目入口的所有 upstream 全局默认。

# 43. 为什么当前默认16

当前本地 exact-window cache 的17帧/5 latent 定义对应 H_pred=16；不允许直接拿该 cache 填充33帧/9 latent 的 H_pred=32训练合同。

将来更改 H_pred 需要匹配 cache 或显式 online 模式与相应设计/数据校验；本轮不安排新 cache 构建或32-horizon实验。

# 44. Policy Horizon 与 T 独立

`H_pred=16,T=32` 合法；改变 T 不改变 cache 的17帧窗口或Policy每次输出16动作。

R 也独立于 T；不得添加 `R<=T` 或 `R必须等于T` 的语义限制。若内部 scan API 有 max-segment 限制，用保持顺序和 W 连续的执行分块处理，不重置记忆。

# 45. Inference Action Horizon

每次得到 H_pred 个动作，只执行前 R 个（默认16，可设置4/8）；新的 policy 调用前必须完成对应已执行 evidence 的顺序更新。

可以每实际 step 做 Local update 而不重跑 Policy，也可以在下一 replan 前按相同次序补齐全部 inner updates；后者须以固定 slow params、逐帧独立 encoding、相同运算与 transaction 为前提，测试其 fast state/token 与逐步方式一致。

每个 obs_t 的 z_t 由统一 current-encoder/cache 管理：在同一步已被 policy 编码的 current frame，Local 后续复用该输出；chunk 中间无 policy 调用的 observation 也单独 T_pixel=1 编码。不得为了批处理将连续观测拼进 VAE 时间维。

# 46. raw15 → RoboCasa env12

必须复用官方 decoder，不能把“都叫12D”误当成数据集与仿真器排列相同：

```text
source raw12: [base4, mode1, eef_pos3, eef_axisangle3, grip1]
policy raw15:[base4, mode1, eef_pos3, eef_rot6d6, grip1]
env12:       [eef_pos3, eef_rotvec3, grip1, base4, mode1]
```

固定官方 decoder 还包含 rot6d 正交化、mode 阈值化、base/gripper 限幅、arm-only 时 base 置零；不删除这些处理，也不另加 planner/FSM/控制补丁。[UP]

“互逆”验证指合法 command/rotation 域内语义一致，不是对任意神经网络输出逐字节可逆。记录 predicted_raw15 和实际 submitted_env12；Local 的 executed_raw15 必须与 decoder 后实际提交命令语义一致，不能把被裁剪/置零前的值误称为已执行值。该 canonicalization 接线在 action Gate 核验，复用官方 slice/rotation authority，不自行反演机器人执行后的物理位姿。

# 47. Corrected V3 Training Architecture

```text
cache catalog -> source identity -> prompt_s / state_s / action targets_s
       |
       +-> Z_s -> z_s ---------------------> clean policy vision
       |       -> future4 -> noise/target -> native FM vision path
       |
       +-> Z_(s-1)[0] = z_(s-1) -> v_(s-1)
                                  + executed raw15_(s-1)
                                  -> inner update W_(s-1) -> W_s
                                  -> Local prefix p_s

(prompt_s, z_s, state_s, p_s, native noised targets)
                    -> official policy -> outer loss
                    -> allowed shared slow parameters
```

s=0 没有 previous evidence，p_0 absent；图中的上一帧 Local 输入与当前 Policy 输入显式错开一个 completed transition，不存在未来泄漏。

# 48. Corrected V3 Inference Architecture

```text
episode start -> W0 (Local-neutral first query)
obs_t -> [left|wrist] -> preprocess -> Encode1 -> z_t
prompt_t + z_t + state_t + committed history prefix -> policy chunk
execute selected actions one at a time:
  retain pre-action z_t -> official decoder -> env.step -> completed e_t
  -> sequential Local inner update -> next W / prefix
next replan uses latest obs and all completed prior evidence
end/reset -> discard episode state
```

Policy 联合预测所需 noise/output slots 不是未来 ground truth；Local 只读真实当前/已完成历史 latent。

# 49. Cosmos-Framework 修改原则

优先零修改官方本体，将 PSM compatibility layer、配置和 Local modules 放在项目扩展层，通过 public API、subclass、wrapper、callback 或官方注册点接入。[O]

不能用隐蔽 monkey patch/多份 copied forward 假装零修改；必须能解释调用流、参数所有权和梯度路径。复用 V2 算法不等于整体复制旧 framework。

# 50. 什么时候允许改 Cosmos-Framework

只有必要 extension seam 确实缺失、且外部扩展无法保证正确语义时，才列出最小 upstream patch：具体 file/symbol、原因、替代方案、off-mode不变证据及未来维护方法。

先在逐文件 mapping 中提交该例外，Owner 对齐后才实施；本次文档提交不执行这类 patch，不更新 gitlink 或重建分支。

# 51. 不允许重复实现的功能

raw loader、camera compose、raw12/raw15/state转换、Wan normalization/encoding、action decoder、server transport、simulator及FSDP/DCP都以官方为单一实现来源。

新增代码限于缺失的 cache overlay、Local功能和必要接线；共享函数集中管理，不能训练一份、cache builder一份、推理又一份。

# 52. 必须移植的 V2 功能

包括 LocalEvidenceEncoder、ContinualTTT core、learnable W0、K/Q/V/slot queries、Local prefix及projection、episode/slot lifecycle、TBPTT、inner/outer梯度、transaction、reset/replay和runtime resume。

还需迁移 V2 exact-window cached-policy seam：相同 cache entry供Policy与Local使用，cache-hit时不重新编码placeholder RGB；保持visual96的 `(1,2)` average-pool，而不是只维持96这个shape。

# 53. Training Defaults

```text
vision_source=cache                    # 正式训练必选本地cache，无自动fallback
camera_set=left_wrist                  use_state=True
use_base_action=True                   base_encoding=raw
action_dim=15                          action_normalization=None
H_pred/chunk_length=16                  eval R/replan_steps=16
TTT T=16 (configurable)                 K_local=4 (configurable)
inner_lr=0.1 (configurable)             B_stream=8, GA=2 (configurable)
Local visual=current composite z only  Reasoner=frozen
```

TTT dim=64、fast_hidden=256、evidence_dim=256、local_dim=32是继承V2实验的参考默认；具体实例须打印，不以固定参数总数替代inventory验证。既有H100 shard8/replicate1是可沿用的基础设施配置，不意味着恢复旧mesh或改变算法。

# 54. Rank0 Training Logging

启动打印完整corpus统计及权重revision/config摘要、H_pred/R/T、camera/use_state/raw15、每组trainable/frozen参数与W0 shapes；未知统计不填假常数。

per-step rank0日志包含iter、outer/total、action/vision loss、inner_loss_mean、fast_state_norm、fast_update_norm、grad_norm、各组lr、step_s、peak_GPU_GB；缺少native某loss时明确not applicable，不伪造0。

其他rank仍可保存各自evidence，但不重复刷屏；累计样本曝光量与unique corpus分别报告。

# 55. Training Readiness Gate

以下是后续验收要求，不是已通过结果，也不是自动执行令牌。

| Gate | 必须证明的行为 |
|---|---|
| A Corpus | cache-first catalog、manifest/identity、实际数量、缺件/重复/越界 fail-closed、完整统计落盘 |
| B Vision | matched RGB的offline Z_t[0] vs online Encode1 parity；Policy/Local同源；Local不读future4；cache-hit的VAE encode调用为0 |
| C Action/state | 官方raw12->raw15->env12顺序/旋转/mode/clipping；state15 clean/no-loss/no-execution；executed evidence语义 |
| D Local CPU | V2 matched fixture；W0初始化、T可配置、slot独立、episode carry、PAD/tail、reset、changed-bytes retry |
| E Gradient | 首段outer能到W0及required映射；continuation不跨detach；required gen/action/Local组梯度；Reasoner冻结；reduction/GA尺度 |
| F Resume | 同步model/optimizer/runtime/frontier；保存和恢复W_t；身份/iteration不匹配拒绝；model-only推理不加载训练W_t |
| G GPU | direct-DROID+Local短readiness、finite loss/grad、VAE调用与峰值显存、DCP保存及10->11恢复 |
| H Closed loop | R=4/8/16的两次replan、48/128步；completed-only evidence、当前帧复用、state/decode、reset/replay、bounded memory |

连续长训前需各Gate的exact pair直接evidence。无任务成功的短smoke只能说明工程链路，不替代SR；也不要求先完成native独立训练。

数值容差必须依据dtype、运算及已知reference误差预先说明；观测性probe不算PASS，不得事后把容差调大到刚好覆盖缺陷。

# 56. Formal Training

在实现及readiness被单独批准后，从固定官方direct-DROID初始化直接训练Local-TTT主线，不经过iter500或native中间checkpoint。

训练总步数、保存间隔、early行为检查点和runtime路径是启动Gate参数；本设计不自行恢复旧30k job，不在此预授权新长训。

# 57. Evaluation Contract

默认 left_wrist、use_state、raw15、H_pred=16、R=16、Local required；支持R=4/8等对比并记录完整resolved config。

保留8卡8worker/slot共享待测任务队列的目标：每GPU一个常驻server及一个active env，任务结束reset后领取下一个，复用官方rollout而不新增另一套decoder或success checker；具体调度文件mapping另行验收。

每task/episode记录success、done_steps、replans、prefix、adapted_steps、fast-state/update norms、inner loss、latency、error、MP4及exact root/child/checkpoint/corpus/seed。结果区分behavioral fail和runtime error，不能跳过失败task抬高SR。

18-task×固定seed可作screening，不冒充正式leaderboard；保留失败视频、按task汇总和人工行为观察。server显存需区分allocated/reserved/进程用量，不能仅凭一次峰值断言泄漏或根因。

# 58. Ablation

Native latest Cosmos raw15对照，以及T、K、inner_lr消融都可在主线稳定后单独批准；不是正式Local训练前置任务。

比较时固定corpus、初始化、训练预算、seed及R/H_pred，并区分改变算法与改变资源预算；本轮不执行任何消融。

# 59. 明确禁止的回归

不得出现Local单独相机VAE/latent concat、B1 mean+RMS冒充V2 visual96、未来真实latent进入Local、predicted未执行动作入memory、错误t/t-1配对、segment清空memory、slot污染、silent cache fallback、默认H_pred漂回32、R绑到T、state行变action、训练W_t进入部署初始化。

不得以参数shape相同宣称功能等价，也不得以telemetry GREEN替代行为正确。旧iter500/B1路线及其执行Gate不复活；历史产物不删除。

# 60. 实施顺序

本次只发布设计，随后仍先提交逐文件mapping和必要upstream seam例外清单，按已对齐范围实施：

```text
Phase 0: exact upstream/V2对照 + 文件mapping + 现有cache只读schema核验
Phase 1: cache-driven corpus/catalog与启动统计
Phase 2: 官方raw15/state及H_pred/R默认16接线
Phase 3: shared offline latent / online current编码与cached-policy seam
Phase 4: V2 Local core/producer/prefix兼容移植
Phase 5: gradient/slot/TBPTT/transaction与checkpoint/runtime resume
Phase 6: 官方server/eval接线 + 可配置R + 队列/结果汇总
Phase 7: CPU/parity/GPU/closed-loop readiness evidence
Phase 8: Owner/ChatGPT单独下发正式训练Gate
Phase 9: 正式行为评测和后续消融
```

每步记录复用authority、修改范围、已验证/未验证项和exact pair；ds只执行，不自行修代码。此顺序不授权为方便迁移而破坏旧分支、重写历史或重做数据。

# 61. 最终设计一句话

**Corrected V3 = 固定最新官方Cosmos3 RoboCasa/raw15 host + V2的episode-persistent Local-TTT；cache目录决定训练corpus，Policy训练用current及加噪future目标，Local永远只用同源current composite latent和已执行raw15，H_pred/R默认16而TBPTT的T独立可配，W0进入模型、W_t只服务episode及训练resume。**

---

## 附录 A：源码依据与尚待验证边界

这些是本次设计对照依据，不是对训练服务器真实数据或新实现的运行证明。

| ID | 固定来源 | 相关位置/支撑内容 |
|---|---|---|
| UP1 | NVIDIA/cosmos-framework `cf5d68c00d97ccd2480a2320ed652b92dec63102` | `cosmos_framework/data/generator/action/datasets/robocasa_lerobot_dataset.py`：`_compose_left_wrist`、`_build_frame_wise_action`、`_build_initial_state`、`__getitem__`；pixel concat、raw15、state15 |
| UP2 | 同UP1 | `cosmos_framework/simulation/robocasa/eval_utils.py:23-114`：`rot6d_to_matrix`、`decode_10d_to_env12`、`decode_15d_to_env12`；arm-first env排列、mode/clipping |
| UP3 | 同UP1 | `cosmos_framework/scripts/action_policy_server_robocasa.py`：state/chunk config解析、`_build_action_input`；官方server接线参考 |
| V2-1 | wxwy/cosmos-framework `e3dc9ecce0a4a7223245dc4f5b5efde7b709fd92` | `cosmos_framework/data/generator/action/datasets/canonical_local_memory_producer.py:170-176`；同cache latent[0]和adaptive_avg_pool2d(1,2) |
| V2-2 | 同V2-1 | `cosmos_framework/data/generator/action/datasets/robocasa_lerobot_dataset.py:363-515`；exact_window_v1、cache读入及video_latent输出 |
| V2-3 | 同V2-1 | `cosmos_framework/model/generator/omni_mot_model.py:4525-4625`；cached-latent绕过VAE和显式parity路径 |
| V2-4 | 同V2-1 | `cosmos_framework/model/generator/mot/local_evidence.py`：W0、initial_state、step_projected_many；`local_memory_segment_adapter.py:39-44` detached carry |
| V2-5 | 同V2-1 | `cosmos_framework/model/generator/mot/active_local_memory_launch.py:226-282`、`checkpoint/dcp.py`；dataloader/runtime独立checkpoint组件 |
| O | 本会话逐项Owner确认 | cache-first corpus、弃用iter500、default16、state仅Policy、直接训练Local、优先零upstream修改、日志数据量 |

原始库支持某功能不代表项目已经接好；旧child存在某行为不把它自动提升为设计authority。后续implementation mapping需列出实际复用的symbol、必要patch及对应该项Gate。

## 附录 B：本次复核修订清单

1. 将H_pred、R、T拆开，统一默认16但不混淆含义。
2. 将“推理未来latent不存在”限定为没有未来ground-truth编码；保留官方预测/noise slots。
3. 将v_t公式精确写回V2 adaptive_avg_pool2d(1,2)，拒绝B1 mean/RMS替代。
4. 修正训练图中的时间索引：consumer s的Local只用s-1 completed transition。
5. 修正env12字段顺序及官方mode/clipping处理，去掉任意输出严格互逆的过强承诺。
6. 保留cache-first，同时区分manifest缺件错误、实际accepted corpus与未经证明的官方全集完整性。
7. 固定actual spatial shape来自cache metadata；不把源256×512直接等同VAE canvas。
8. 补回显式online能力，但保持默认cache且无隐式fallback；缓存与Policy当前latent复用不等于重复在线VAE。
9. 补齐8GPU常驻server/任务队列、训练corpus日志、optimizer功能清单、角色及旧Gate覆盖关系。
10. 明确本次只提交设计：未运行新训练/仿真/parity；未宣称当前child合格，未删除iter500或数据。
