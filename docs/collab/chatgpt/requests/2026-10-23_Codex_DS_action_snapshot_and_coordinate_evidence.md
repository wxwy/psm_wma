# Codex / DS：提交动作快照与坐标口径的窄范围处理

日期：2026-10-23。
依据：docs/collab/chatgpt/reviews/2026-10-23_DS_B5_B6_action_aliasing_evidence_review.md。
开发锚点为当前V3，已审test-only Formal Root ee53cbe1c25ff174f0d92a92e51e901ec6436c18 / Child c9f21040f462a114d597fc83773cb9b6a9e96214；本指令的文档HEAD不能当Implementation SHA。
这是一项独立的动作审计快照加固，不替代正在进行的5项夹具CPU复验；不修改G1训练、Checkpoint、动作解码/scale/归一化、控制器数学或Vendor锁。无GPU/模型/真实Kitchen/仿真执行授权。

## 一、为何需要改记录，而不是改控制

旧robosuite普通MobileBaseJointVelocityController会通过NumPy切片原地修改env.step的入参xy。历史Child35b0和当前Childc9的run_policy均先step，再读取env_action写submitted_env12，故旧日志可能记录的是修改后的控制器坐标表示而非环境入口命令。
已查canonicalize_raw15_for_env用独立数组产生pre-step canonical，LocalMemoryClient.record_completed使用它，因此这条路径没有证明TTT历史污染。
当前正式Vendor1ac174的Legacy类两个分支都复制action。不能把旧环境的别名行为当作新Vendor必然的故障；调用侧仍应自行保证submitted_env12字段的时点契约。

## 二、Codex最小实现与验收合同

### 允许的生产变更

优先只改Child cosmos_framework/simulation/robocasa/closed_loop_eval.py中run_policy的审计边界及相关窄范围测试：
1. 完成现有decode/canonicalize后、调用env.step之前，为审计取得独立的env12值快照；字段submitted_env12明确表示env.step入口命令。
2. 仍仅在env.step成功返回后写completed action记录并调用原Local-TTT record_completed，不能为了“提前记录”把执行前动作标为已完成。
3. 给环境的动作数值、类型、顺序、调用次数以及现有模式/clip逻辑全部不变；保持canonical raw15的独立pre-step来源。
4. 环境可以继续按原实现修改自己的入参；不要把原数组强行设成只读，不要在step后写回pre-step值。旧controller的goal_qvel可引用该对象，写回会改变实际目标。
5. 如保留post-step值作诊断，必须另字段清楚命名为post_env_step_argument，不能冒称controller内部最终命令或实际qvel。该附加字段不是强制交付，避免无必要扩大schema。
6. 默认不改Root的整体结果验证规则、生产timeout、Vendor、推理/训练算法；如有必要给审计记录增加阶段/来源标识，说明最小关联改动并保持旧日志原样不可覆盖。

### 必需CPU回归（不加载真实Kitchen）

通过真实run_policy控制流测试，而非仅测试array.copy：
- fake env.step捕获入口值，随后原地旋转base xy，再正常返回；JSONL/on_action的submitted_env12必须等于捕获的入口值，预测和canonical不变，Local-TTT记录必须仍是原canonical。
- fake env修改整个入参数组或内部保留其引用，进一步修改后已写记录仍不漂移；不要回写环境持有的引用。
- env.step抛异常：没有伪造completed action或Local-TTT completed evidence，原有cleanup及异常传播不被破坏。
- 未修改入参的正常环境保持原输出；arm/base gate、clip、zero/非零heading和合法rot6d raw15 roundtrip遵守原容差。
- 证明修复前至少一个mutable-env场景红、修复后绿；仅跑相邻Child测试与有实际接线变化的Root测试，不能为该记录改动重跑全仓或修改2项已修复fixture。

提交新Child、Root Gitlink及精确差异、作者CPU/Ruff/格式/语法结果，交GPT只针对该新增量审核。不得修改当前活动G1工作树，DS仍从V3自行拉取。不以文档请求宣布生产修复已经完成。

## 三、DS只对已有证据做最小补充

1. theta来源：说明B5所用theta来自独立保存的base姿态/控制器状态，还是由同一对predicted/submitted二维向量反求。后者零残差主要支持旋转可拟合，不是独立航向测量；标明方法，不强求重跑仿真。
2. 同步语义：predicted/canonical和旧日志里的post-step submitted属于同一个source_step，不同坐标表示和调用阶段。用canonical[:4]或decode(canonical)得到接口层gate/clip后命令用于同口径幅值对比；不要更改历史JSONL。按Run及源码/依赖版本区分4-task、18-task和未来新Vendor实验。
3. 单位：base planar/yaw是归一化控制命令，不写成位姿差分或真实m/s；对xy旋转比较逐步二维L2范数，yaw/torso分别统计；不要把x/y逐通道mean_abs增长当增益，也不要混合未clip与clip后的范数。
4. gripper=0.033需明确含义与比较字段，不能同时声称所有通道零误差。报告旧B1“完全train/eval一致”、B4的20D/native_window等不适用说法需标记为已修正/待证，不能保留互相矛盾的权威结论。
5. B7已正确撤销归零证明根因，但同观测模型诊断要用真实有效示教窗口及因果历史；物理干预使用相同完整初态并允许后续观测分岔。PickPlace示教样本可从现有G1 cache/index准备，不因失败rollout为空而先重跑仿真。

## 四、既有进度不倒退

- AGENTS环境索引已于4a1ab5fa补上，不重复请求写入；源码缺失/离线bundle为已过期状态。
- ee53/c9的5项fixture复验仍由DS在原慢CPU环境按已发指令继续。本B报告本身不是新的A复验通过证明。
- 只记录诊断与提出最小记录修复，不能由此要求停止训练、改旧Checkpoint、重训或恢复归一化/增益。真正模型推理与正式仿真仍由Owner手动决定。
