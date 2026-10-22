# G1 iter8900 RoboCasa 慢动作：DS统计归档与独立解释修正

日期：2026-10-22。
类型：新增运行行为 Evidence / 模型诊断记录，不是当前 Batch C 的重复代码审核，不改变既有 implementation verdict，不修改生产源码或运行中的G1。

## 0. 来源与版本边界

Owner 人眼观察既有仿真 MP4：动作很慢，但方向看起来有意义。DS_PRO 提供逐任务训练 action 标准差、formal_4task_x5ep 已执行 predicted_raw15 标准差及若干源码检查。

本轮接收时远端 V3 docs HEAD 为 c2d8359f918e6880a2c67847b817884a726fe4f9；当前 formal Batch C Root a2f3a6a367395b2f2a6006cfc4e7c9effa606713 / Child-Gitlink c9f21040f462a114d597fc83773cb9b6a9e96214 未变。历史 iter8900 仿真按前一 DS 报告绑定 Root ba91ebb7de2555cd1ff2a290d0af5ee43a8a3ee6 / Child 35b0ea1ccee9ee26653ed6589c484f0997d1c586；训练冻结 Child 为 2d128ed5a07601cdd424974f99b67832eafeeb41。不要把旧 MP4 和统计记到新的 Batch B patched vendor 或 Batch C 实现名下。

所有逐帧统计、配置实际值、action_stats_path=null、空文件状态和肉眼观察均按 Owner/DS 提供的信息归档。GPT没有读取本机原始 MP4、Parquet、JSONL，没有独立重新计算它们的均值/标准差；本轮独立计算仅使用所提交的汇总数字。接受DS现场取证，不另要求上传证据包。以下引用的指定Git源码已经由GPT直接读取。

历史输出：/mnt/data1/data_v2_0617/dspro_iter8900_eval_ba91ebb7/formal_4task_x5ep/；训练分布来源为DS所述v3_flat和flat_v3_mapping.parquet。该四任务旧环境仍包含仓外robosuite兼容补丁，不能把其物理语义视为已由Batch B验收。

## 1. 归档的原始统计（DS提供，未重新采样）

### 训练记录

| task | episode范围（DS） | 帧数n | EEF translation std (x,y,z) | base m0,m1,m2 std | mode统计 |
|---|---|---:|---|---|---|
| CloseFridge | 502–1014 | 155443 | 0.5206, 0.5090, 0.2443 | 0.0452, 0.0496, 0.0042 | arm(-1)=151219, base(+1)=4224 |
| NavigateKitchen | 2022–2521 | 72786 | 0.2043, 0.0309, 0.0635 | 0.5158, 0.5054, 0.4938 | arm(-1)=6187, base(+1)=66599 |
| PickPlaceSinkToCounter | 5542–6042 | 194952 | 0.3198, 0.3537, 0.3980 | 0, 0, 0 | arm(-1)=194952 |
| TurnOnSinkFaucet | 8620–9125 | 113688 | 0.2389, 0.3510, 0.1516 | 0.0012, 0.0190, 0.0004 | DS称几乎全arm，未给完整计数 |

### 已执行模型输出 predicted_raw15

| task | 输出action数n | EEF translation std | base m0,m1,m2 std | raw control_mode mean |
|---|---:|---|---|---:|
| CloseFridge | 4500 | 0.2304, 0.1891, 0.0747 | 0.0455, 0.0093, 0.0056 | -0.877 |
| NavigateKitchen | 2250 | 0.2080, 0.1640, 0.1013 | 0.1554, 0.2768, 0.1687 | -0.241 |
| PickPlaceSinkToCounter | 4500 | 0.0375, 0.0404, 0.0539 | 0.0019, 0.0026, 0.0027 | -1.002 |
| TurnOnSinkFaucet | 2873 | 0.0691, 0.1345, 0.0615 | 0.0020, 0.0031, 0.0031 | -1.004 |

### 按以上四位小数重新计算 model_std / train_std

| task | EEF std比值 | base std比值 |
|---|---|---|
| CloseFridge | 0.4426, 0.3715, 0.3058 | 1.0066, 0.1875, 1.3333 |
| NavigateKitchen | 1.0181, 5.3074, 1.5953 | 0.3013, 0.5477, 0.3416 |
| PickPlaceSinkToCounter | 0.1173, 0.1142, 0.1354 | 未定义，训练分母全0 |
| TurnOnSinkFaucet | 0.2892, 0.3832, 0.4057 | 算术值1.6667, 0.1632, 7.7500，但分母极小，且base几乎未激活，不宜用作能力尺度 |

这些数是分布标准差比，不是逐帧动作幅值比、速度比或因果缩放系数。n是相关时间序列中的帧数，不是独立成功率试验数。

## 2. 可支持的代码结论：两个具体怀疑得到有力排除

### 2.1 inspected raw分支无二次差分

历史Child35b0的 cosmos_framework/simulation/robocasa/eval_utils.py：decode_10d_to_env12将EEF translation直接赋值至env[:3]，仅将rot6d转回rotvec；decode_15d_to_env12处理base clipping、模式门控和字段重排；canonicalize_raw15_for_env构造与实际submitted env12可round-trip的canonical raw15。没有对上一帧action相减或np.diff。

训练冻结Child2d128的 OfficialRoboCasaPolicyAdapter.convert（robocasa_exact_window_policy.py）直接调用RoboCasaLeRobotDataset._build_frame_wise_action，再拼接 action12[:,:5] 和arm10，加入独立state token；没有在raw15分支重新做时间差分。真实G1读取链应记录为 ExactWindowCachedDataset → OfficialRoboCasaPolicyAdapter → ActionTransformPipeline，而非只用遗留Dataset构造参数作依据。

因此，“这里又做了一次动作差分”不是已核对路径支持的解释。结论边界是这些处理路径，不等于所有控制器/坐标/仿真环节均已被证明无误。

### 2.2 未发现遗漏训练统计反归一化，但应区分三层尺度

训练Adapter对平移/base命令不做统计归一化；DS现场config报告action_normalization=null。历史Server的_load_action_normalization_stats在action_stats_path is None时直接返回；_denormalize_action在没有对应统计tensor时原值返回。DS报告server_info的stats path为null，与该代码路径一致。

应区别：
1. 数据集/模型统计归一化，例如mean/std或min/max；本G1路径未发现启用。
2. 原生控制器输入命令常以[-1,1]范围表达；“没有模型统计归一化”不意味着原action是米/弧度或无量纲缩放。
3. OSC/controller将输入clip/scale为目标增量并产生力矩；这属于控制器职责，与训练统计denormalization不是同一步。

因此不支持直接给Server加min/max反归一化或统一放大输出。DS称“比例不恒定所以一定不是归一化bug”的论证不成立：逐通道仿射变换a_j=s_j*z_j+b_j本来就有不同s_j；在不同观测分布上，std比更不能识别变换是否遗漏。支持no-op正确性的依据是实际代码/配置与数据合同，而不是跨通道比值相近。

## 3. 必须修正的结论与解释

### DIAG-SLOW-01：std收缩不等于平均幅值或速度收缩

std(a)=sqrt(E[(a-Ea)^2])；RMS(a)=sqrt(std(a)^2+mean(a)^2)。一个恒定0.2的动作std可以为0，但幅值不为0。当前只有std，不能计算mean(abs(a))、RMS、3D范数或每帧真实位移。

PickPlaceSinkToCounter三通道std约0.114–0.135，是强烈的输出分布收窄线索，且与Owner的慢动作观察相符；可以把“低运动输出/停滞”列为优先验证假设，但不能写成已证明速度仅训练的1/8。

NavigateKitchen的EEF std并未整体收缩（约1.02/5.31/1.60）；不能用一句“模型全部输出缩小”概括四任务。其控制模式和底盘门控更关键。

### DIAG-SLOW-02：NavigateKitchen mode mean不能证明与训练模式分布一致

训练base(+1)帧占比由DS计数可得66599/72786=91.4997%，相应二值mode均值为+0.829995。模型raw mode均值-0.241不是直接可比较的二值比例。

代码真实门控：m=1[predicted_raw15[4] > 0]；submitted_env12[11]=2m-1；submitted_env12[7:11]=m*clip(predicted_raw15[0:4],-1,1)。因此即使模型输出非零base_m，mode<=0时实际底盘命令也完全被清零。门控是明确设计，不是本轮发现的实现bug。

仅若模型mode严格为±1，-0.241才对应(1-0.241)/2=37.95%的base占比；目前它为连续回归值，其他任务均值甚至略低于-1，所以不能把37.95%当实际占比。一个全部输出-0.241的序列base占比可以为0，另一些正负混合序列可有相同均值。

最高优先统计：predicted mode>0比例、submitted env12[11]>0比例、mode直方图/分位数/接近零比例、base使能连续段、base原始命令被门控清零的比例，以及base-mode条件下命令幅值。必须逐episode和任务阶段看，不能仅凭整体均值宣布与示教分布一致。若base开启率明显低于任务需求，底盘慢可能同时来自“少开底盘”和“开底盘时命令偏小”。

### DIAG-SLOW-03：标准差乘0.05不是实测每步位移

robosuite v1.5.2 OSC构造默认translation output范围±0.05、input范围±1，但目标机具体controller设置需实际读取。0.0375×0.05=0.001875m，只能在实际scale相符时解释为某一维**目标增量的标准差**，并非每步实际移动1.9mm。

真实位移还取决于控制模式、坐标系、插值、跟踪误差、接触和动力学。需要同一参考系下的EEF/base pose前后差或环境状态记录才能证明物理速度。模式关闭、环境碰撞或Legacy轴差异不能由raw15值单独排除。

### DIAG-SLOW-04：不同state/phase分布不能用于因果归因

示教覆盖成功任务的全部阶段；失败rollout可能多数停在初始接近或接触阶段。由其造成的state occupancy、模式比例、动作方向/幅值差异可同时是低SR的原因和结果。当前比较不是相同观测下的target-vs-prediction配对实验。

进一步，DS的v3_flat全帧统计需与G1实际verified index/cache包含的episode子集、H16窗口有效帧、状态前缀剔除、padding/idle/loss mask和采样权重核对；不要先假定所有映射帧就是G1训练目标的有效分布。数千同一episode帧不等于数千独立实验。

“保守/欠拟合/低能量策略、状态分布外、阶段停滞、动作模式误判”可作为待检验假设；不能仅凭低action loss或std比，把因果结论锁定为欠拟合。Flow Matching也不能被简化成“因为MSE所以必然输出平均动作”。

### DIAG-SLOW-05：旧运行依赖和空JSONL仍限制推论

旧formal_4task_x5ep运行使用临时robosuite兼容补丁，先前HIGH-10所指Legacy controller、延迟初始化与CCD选项语义尚未在该旧环境闭合。命令流上看不到二次差分或统计归一化缺失，**不等于实际物理执行链完全正确**。新的patched vendor及真实Kitchen验证可能影响行为，不能用本轮统计关闭旧环境不确定性。

18任务运行某些rollout actions.jsonl为0字节，表示没有留下成功完成env.step的行动记录（可能首次预测失败、超时、中断等），不是“模型输出全零”，也不是对应任务纯策略低SR的证据。其runtime_error/steps=0必须从有效策略行为统计中分离，同时明确报告基础设施失败数；不能把空文件作为零动作样本填入std。

## 4. 后续最小诊断顺序（非自动执行许可）

### A. 先利用已有JSONL做只读统计，不需新GPU或修改训练

1. 精确绑定历史Root/Child/Checkpoint/config/vendor补丁、4任务COMPLETE来源，与18任务失败来源分开。
2. 对同一条已完成action，比较predicted_raw15、canonical_executed_raw15、submitted_env12：EEF translation应数值直传（浮点容差内）；base差异按mode门控/clip逐项解释；报告最大abs residual、clip比例、门控清零比例。不把全部字段宣称恒等，rotation/gripper确有合法重编码或clip。
3. 每任务/每episode报告mean、std、mean_abs、RMS、p50/p90/p99绝对值、零附近比例、动作3D范数、方向抵消/符号翻转、控制模式比例和连续段。base幅值须同时报告全帧与base-active条件；arm任务分别看有效阶段。不要把米、rad与无量纲mode混成一个总范数。
4. 核对v3_flat范围与实际训练cache/index；训练目标与推理输出按同一raw15布局和有效动作帧比较，绝不将绝对state token混进delta统计。
5. 看env rolloutXX.mp4，而非generated预测视频；核对视频fps、有效帧数、simulation 20Hz及动作数，区分仿真运动慢、视频播放慢、真实推理wall time慢。实际pose/physical speed只有日志确实记录时才算，不能从std反推。

### B. 仅在Owner另行授权时做最小配对和真实物理验证

在正确固定Vendor/Kernel依赖的环境中，沿既有Batch C验收后真实canary流程，不临时修改Decoder。选少量相同示教状态/图像、正确state token、同语言/Local-TTT时间顺序与历史上下文，比较预测与真实target的幅值/方向/mode；与闭环rollout区分teacher-forced诊断，不偷用未来信息。若支持多次采样，记录固定seed及离散度而非凭单样本归因。没有开新训练或改变G1的许可。

后续较晚checkpoint用完全相同eval环境/固定初始条件/协议比较，才能判断继续训练是否改善。当前运行的G1不因这份补充诊断而停训、换归一化、加gain、改loss、改action_horizon或引入Agent/RL补救。

## 5. 本轮可发布结论

ACCEPTED_OBSERVATION：Owner观察动作缓慢且方向有意义；DS显示三项arm任务的EEF输出标准差明显小于所比较的示教分布，NavigateKitchen的base标准差较小。
SUPPORTED_NARROW_EXCLUSION：在已核对raw15训练适配和执行解码路径中没有二次差分；训练统计归一化未启用、Server无stats的no-op与之相符。
NOT_ESTABLISHED：不能由此排除所有仿真/控制/状态分布问题，不能把std比等同实际幅值或速度比，不能把mode均值当base频率，不能直接证明欠拟合是唯一根因。
NEXT_PRIORITY：NavigateKitchen actual base activation + gated command statistics；PickPlaceSinkToCounter mean_abs/RMS及阶段匹配；correct vendor物理验证继续独立推进。

此记录不新增训练或代码整改阻断Gate，不推翻Batch C C01/C02的既有REQUEST_CHANGES，也不改变Batch B真实Kitchen未闭合状态。只归档、修正分析与建议最小后续只读证据，不启动任何测试或GPU。

## 6. 本轮直接核对的源码与外部定义

- 历史仿真解码：https://github.com/wxwy/cosmos-framework/blob/35b0ea1ccee9ee26653ed6589c484f0997d1c586/cosmos_framework/simulation/robocasa/eval_utils.py （decode_10d_to_env12 / decode_15d_to_env12 / canonicalize_raw15_for_env）
- 历史Server：https://github.com/wxwy/cosmos-framework/blob/35b0ea1ccee9ee26653ed6589c484f0997d1c586/cosmos_framework/scripts/action_policy_server_robocasa.py （_load_action_normalization_stats / _denormalize_action）
- 冻结G1真实Adapter：https://github.com/wxwy/cosmos-framework/blob/2d128ed5a07601cdd424974f99b67832eafeeb41/cosmos_framework/data/generator/action/datasets/robocasa_exact_window_policy.py
- 冻结G1缓存数据链：https://github.com/wxwy/cosmos-framework/blob/2d128ed5a07601cdd424974f99b67832eafeeb41/cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft.py
- 原raw动作重编码：https://github.com/wxwy/cosmos-framework/blob/2d128ed5a07601cdd424974f99b67832eafeeb41/cosmos_framework/data/generator/action/datasets/robocasa_lerobot_dataset.py
- 固定v1.5.2 OSC默认值：https://github.com/ARISE-Initiative/robosuite/blob/824ac14cefcfb7ec125fe5eb2e0bad7364466154/robosuite/controllers/parts/arm/osc.py
- 官方OSC参数定义：https://robosuite.ai/docs/source/robosuite.controllers.parts.arm.html
- 官方控制器缩放语义：https://robosuite.ai/docs/simulation/controller
