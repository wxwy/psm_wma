# G1 iter8900 慢动作跟进：执行动作对齐、幅值与模式的增量证据

日期：2026-10-22。
类型：DS_PRO 新运行统计的证据分析和诊断记录；不是代码整改审核，不改变 Batch C、G1 Resume 或真实物理 Gate，不授权模型推理/仿真/训练。
前序记录：`docs/collab/chatgpt/reviews/2026-10-22_V3_G1_iter8900_slow_motion_diagnostic_evidence_review.md`（初次归档提交 `3cc1c61642b4f30fcd7c4d72f746f52f012d3a81`）。

## 0. 身份与证据级别

本轮读到远端 V3 HEAD `074c3efe78a93ae38a5dabce49c6884ddd227334`；Batch C r2 formal Root `a4b22b929175e462b6a8db57ad2abee7e220dd37` / Child `c9f21040f462a114d597fc83773cb9b6a9e96214` 不因本次文档更新而变化。不重新技术审核此同一 Pair。

本次分析对象仍是旧 iter8900 `formal_4task_x5ep/*/rollout*_actions.jsonl`，按既有 DS 报告属于历史 Root `ba91ebb7de2555cd1ff2a290d0af5ee43a8a3ee6` / Child `35b0ea1ccee9ee26653ed6589c484f0997d1c586`，旧仿真依赖为 robosuite tag `824ac14cefcfb7ec125fe5eb2e0bad7364466154` 加 DS 四处临时未提交兼容修改。不能记为新 Vendor `1ac174...` 或新 Batch C 的运行成果。训练 G1 冻结来源 Child `2d128ed5a07601cdd424974f99b67832eafeeb41`。

逐帧 JSONL/Parquet 数据、max误差、near0、模式计数均由 DS 提供，GPT未重新读取目标机原始文件；接受 DS 现场取证，不重复要求上传或重做整套统计。GPT本轮独立核算汇总比例，并读取固定 robosuite tag 的 HybridMobileBase/OSC 源码。下文严格区分数据现象、源码行为与未证明的因果机制。

## 1. DS 新数据（原样归档）

### 1.1 实际提交动作对齐

- 四任务 EEF translation：`max(abs(predicted_raw15[5:8] - submitted_env12[0:3])) = 0`。
- 底盘裁剪：NavigateKitchen 2.0% 步有 base 输入超过[-1,1]，全部发生于 base-enabled；其他任务0%。这是帧比例，不是被裁掉幅值占比。
- mode<=0门控帧比例：CloseFridge93.4%，NavigateKitchen60.3%，PickPlaceSinkToCounter及TurnOnSinkFaucet均100%。
- DS称四任务被门控帧的 predicted base mean_abs约0.0027、near0_01至少98.9%。这支持被清零的绝大多数值很小，没有大量显著底盘命令被错误关闭的证据；数值小不等于已识别模型语义上的“真实意图”。
- 对齐结果支持已检查的 raw15→canonical→env12 路径没有额外缩小EEF translation，base clipping与既定mode门控符合实现。不要将此推广为控制器/物理/旋转/相机/时序整链路都已证明正确。

### 1.2 全帧 EEF 平移命令 mean_abs

| Task | 示教 | 模型 | model/train（以提交的舍入数字复算） | DS near0_01 |
|---|---:|---:|---:|---:|
| CloseFridge | 0.318 | 0.094 | 0.2956 | 16.2% |
| PickPlaceSinkToCounter | 0.246 | 0.026 | 0.1057 | 47.4% |
| TurnOnSinkFaucet | 0.187 | 0.045 | 0.2406 | 34.0% |
| NavigateKitchen | 0.023 | 0.083 | 不宜与前三项直接作同语义比较：模式混合不同 | 22.2% |

因此三个机械臂任务的平均绝对平移命令约为示教的10.6%–29.6%，不是“都约30%”，也不是之前只有std变化的表述。PickPlace是目前最强的低幅值信号。near0_01必须保留计算定义：逐坐标比例、逐帧mean_abs阈值、L2范数或三维全小于阈值并不相同；阈值命令小不等于实测末端停滞。

### 1.3 导航模式与条件幅值

| 指标 | 示教 | 模型 |
|---|---:|---:|
| base-mode占比 | 66599/72786 = 0.9149974 | 0.3969 |
| base-enabled条件下base mean_abs | 0.320 | 0.165 |
| 占比×条件幅值（命令层proxy） | 0.2927992 | 0.0654885 |
| base-mode下EEF translation | DS称全0 | DS称非零，std约0.165 |

由汇总值：启用占比相对示教为0.43377，启用后幅值相对示教为0.515625，乘积0.22366（约22.4%）。这是同口径、同坐标聚合且使用post-clip命令时的全帧平均绝对底盘命令比例，不是物理速度/位移比例，更不是“完成任务需4.5倍时间”的证明。

若0.165统计的是pre-clip预测值而非submitted env12，结果只可称近似proxy；应使用已有日志的submitted_env12在相同base维度上直接给出实际值。不要仅凭裁剪2%就证明其对mean_abs没有贡献。x/y/yaw的单位语义不同，混合归一化命令均值不能直接转换为m/s。

恒等关系（b取明确固定的底盘维度集合，d为维数）：

`U = E[mean(abs(submitted_base))] = P(mode>0) * E[mean(abs(clip(predicted_base,-1,1))) | mode>0]`

这说明“少开底盘”和“打开以后命令偏小”两因素同时存在于这些旧rollout的命令分布。门控代码没有另行丢弃大量本该执行的显著base命令，不建议调整门控阈值或去掉门控。

## 2. 对前轮诊断状态的更新

- DIAG-SLOW-01：从仅std收窄推进到mean_abs显著降低，三个机械臂任务低命令幅值现象证据增强；仍不等于同观测下欠拟合或真实物理速度缩小。
- DIAG-SLOW-02：已得到实际mode>0比例，不再用control_mean换算。NavigateKitchen旧rollout与示教base-mode占比明显不同；“与训练模式分布一致”的旧表述被本报告正式纠正。
- 二次差分/遗漏训练统计反归一化：此前代码证据仍成立，加上本次日志精确透传，继续不支持用它们解释慢动作；不能无证据给Server加增益或统计denormalization。
- 门控损失：原先需要调查的“非零base输出是否被mode误清零”在已检查帧上不再是主要数值解释；但低mode启用率本身是否为错误决策，仍要同观测/同阶段的标签配对。
- 0字节action文件仍排除，不能填零进入本次幅值或模式统计。

## 3. 新源码核实：训练动作互斥，不等于HYBRID控制器硬互斥

固定源：ARISE-Initiative/robosuite commit `824ac14cefcfb7ec125fe5eb2e0bad7364466154`。

### 3.1 HybridMobileBase并未在base模式自动丢弃arm命令

`robosuite/controllers/composite/composite_controller.py`（Git blob `423f368c18b4e290d7ee12c876a92426bdd865fd`）的 `HybridMobileBase.set_goal`：

- mode>0时为arm controller设置 `goal_update_mode="desired"`；否则设置 `"achieved"`。
- 然后仍然对每个part调用 `controller.set_goal(action)`；该函数没有依据base_mode把arm action置零。

`robosuite/controllers/parts/arm/osc.py`（Git blob `81f19097e555ca2934d2a206b3b35c6dbe6f4bd7`）的 `compute_goal_pos`：

- desired：`goal_pos = self.goal_pos + delta`。
- achieved：`goal_pos = current_achieved_position_in_controller_frame + delta`。
- delta来自OSC的scale_action；目标量不是实测位移。

因此，若历史任务真实运行的是该HYBRID_MOBILE_BASE + OSC(delta)控制器，模型在base-mode下输出非零EEF平移可以持续改变arm目标，而不是“该维未被使用所以无害”。同符号偏差可在连续base段内累计；随机零均值扰动也可能改变目标轨迹，但不能由一项std0.165推断累计量或真实碰撞。必须核对现场有效controller配置与实际目标/状态，才能升级为运行时因果结论。

DS可利用已有metadata/有效controller配置和submitted_env12只读补核：确认composite class、OSC input_type/ref_frame/scale、base-mode连续段中的EEF signed sum、sum_abs与旋转角；不需要为了读源码重新运行整轮仿真。这里不是新增“decoder bug”，也不批准临时在base-mode强制抹掉EEF。

### 3.2 “EEF恒为零”要限定字段

本报告的主要EEF统计是translation `raw15[5:8]` / `env12[:3]`。零旋转在rot6d编码中是单位旋转的两列，例如`[1,0,0,0,1,0]`，并非六个零；夹爪也不自动等于零。不能把训练互斥错误写成“base模式下整个EEF10维向量都应该为0”，也不能如此修改目标或预测。

## 4. 尚未解决的归因限制

1. 示教成功多阶段与闭环失败/停滞访问的状态分布不同；低幅值、模式占比是已测现象，但可能同时是低SR原因和结果。模式决策错误率应在相同观测的gt-mode上衡量，不应把91.5%强制当作所有rollout必须满足的时间比例。
2. DS统计来自v3_flat目标任务全帧，不等于G1实际verified cache/index、有效action loss mask及窗口采样加权分布。每集首帧零action占比<0.1%不足以解释当前数量级差异，但仍应明确抽样索引与分母。
3. state token为独立条件，不能混入预测action的幅值或loss统计；rot6d要以解码旋转角/旋转误差比较，而不是全部通道绝对值。
4. 旧运行有第三方兼容问题；新Vendor需要真实Kernel/控制器/Camera/State与目标厨房验收。新环境可间接改变闭环观测、进而改变mode决策，不能声称它必然修复模型输出。
5. 不是所有模型输出收缩都等同“欠拟合”：条件/历史对齐、推理设置、训练样本覆盖、状态分布偏移等仍待区分。这里不改G1训练计划。

## 5. 下一步最小诊断方案（计划，不自动执行GPU）

### A. 已有日志/配置的只读补核

不再重复全套解码排查；优先补充两项：
- 明确mean_abs和near0_01的维度/时间聚合口径，并从submitted_env12直接计算post-clip U；按每episode报告，不能把连续帧当作独立样本。
- 核对实际HYBRID/OSC配置，对base-enabled帧统计EEF translation mean_abs、解码旋转角、连续base段的目标增量signed sum/sum_abs。字段缺失则报告缺失，不伪造真实姿态。

### B. 同观测配对的离线策略诊断

需要单独安排模型推理资源，Owner未授权前不执行。使用少量固定的G1真实cache/index有效窗口，覆盖示教base-enabled、arm-enabled和mode切换前后阶段；明确task、episode/frame、原始obs/state/caption和action目标。

- 保持历史评测的raw15/state15/left_wrist/H16、模型sampling seed/steps/guidance和预处理不变。
- Local-TTT必须按因果顺序构造历史，只使用当前预测之前已完成的示教obs/actions；未来待评估标签不可进入条件或inner adaptation。冷启动与有历史的query分栏，不能把每个单帧都reset之后的结果当作正常Local-TTT。
- 对齐预测动作chunk的真实起点，剔除独立state token与padding/loss-masked位置。
- 同时评价gt mode与预测mode的混淆矩阵/base recall/arm recall、gt-arm和gt-base条件下的translation/base MAE与幅值比、有效非零动作方向一致性，以及base-mode EEF输出泄漏。
- 可以复用同一小样本比较iter8900与后续已经保存的checkpoint；不改变训练或通过动作增益找好看的结果。

解释：同观测仍低幅值/低base recall → 缩小范围到条件策略/推理或学习问题；同观测基本正确但闭环失败 → 优先查状态访问分布、历史/相机状态对齐和控制交互。单一实验不会证明唯一根因。

## 6. 处置

接受本轮DS证据为慢动作调查的明显进展；不要求停止当前G1、不改解码/增益/归一化/模式阈值、不从现有统计推导RL或Agent补救需求。新记录只更新诊断事实与下一步区分性实验，不新增或关闭任何生产代码/GPU Gate，也不替代尚未完成的Batch C独立CPU/真实环境验收。
