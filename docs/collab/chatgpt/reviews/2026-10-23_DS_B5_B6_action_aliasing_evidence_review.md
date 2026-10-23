# DS B5/B6 增量诊断：动作数组别名、记录时点与正式 Vendor 差异

日期：2026-10-23；输入为 Owner 最新粘贴的 DS B 报告（报告原日期2026-10-22，新增 B5/B6/B7）。
类型：新诊断 Evidence 接收与日志语义处理决定；不是重审未变化的 Batch C / fixture Formal Pair，不重新宣布整个仿真/训练链通过。
本轮起始直接读取远端 V3 HEAD：17755791aaf4363d06c2f4285fc914a4cdf859b6。当前已审 test-only Formal Root ee53cbe1c25ff174f0d92a92e51e901ec6436c18 / Child-Gitlink c9f21040f462a114d597fc83773cb9b6a9e96214；Vendor 可重建产物1ac174585293ed998ffc9cf73e47439798cf6f6c。
历史分析对象仍是 iter8900 formal_18task_x5ep_8gpu，中断的旧运行，历史 Child35b0ea1ccee9ee26653ed6589c484f0997d1c586及robosuite tag824ac14cefcfb7ec125fe5eb2e0bad7364466154加DS四处临时补丁；不是已在新Vendor下完成的正式评测。

## 1. 证据级别与主要裁决

DS报告逐帧584条base记录符合旋转关系、残差0、clip41步、统计重分布及12891条其他通道检查。GPT本轮没有读取目标机原始JSONL、这些/tmp统计脚本或执行模型/物理仿真；不冒称独立重算了584条数据。
GPT独立读取了固定历史及当前Child动作解码/step/日志/Local-TTT代码、旧robosuite控制器与复合控制器、当前版本化Vendor patch。源码证实旧环境存在足以解释B2/B3差异的动作数组原地修改路径；旧记录中的submitted_env12不一定是调用env.step入口时的值。

处理决定：
- 接受“历史B2/B3不一致可以由控制器原地修改+step后读取日志解释”的源码机制，撤销将逐通道均值变大视为只裁剪路径本身出错的解释。clip不增大绝对值的数学关系仍成立，但旧日志不是其原先假设的pre-step快照。
- 需要把submitted_env12的记录语义固定为env.step入口值；仅增加独立快照和回归测试，不改控制器旋转、动作解码、增益、归一化或Local-TTT历史定义。
- 这次发现不是已证明的模型欠拟合唯一根因，也不是已证明的整个执行链无误。目标状态/物理速度仍未由命令统计证明。
- 重要：新Vendor的Legacy类已在两个轴分支中复制action，此历史问题不能直接推广为固定正式Vendor必然重现。当前Child仍依赖环境“不改入参”的隐式假设，快照是稳定记录契约的窄范围加固，不借此重新否定已验C01/C02或无限扩大Gate。

## 2. 已核对的三段代码与别名传播

1. ARISE-Initiative/robosuite@824ac14.../robosuite/controllers/composite/composite_controller.py:237-264：HybridMobileBase.set_goal里 action = all_action[start_idx:end_idx]，随后调用controller.set_goal(action)。对NumPy数组，该切片可共享父数组存储。
2. 同commit的robosuite/controllers/parts/mobile_base/joint_vel.py:159-220：普通MobileBaseJointVelocityController.set_goal根据curr_theta-init_theta，原地赋值action[0]、action[1]，再self.goal_qvel=action。旧DS patch把JOINT_VELOCITY_LEGACY别名到此普通类，来源为DS现场报告，不将此别名当作正式新Vendor实现。
3. 历史Child35b0...的simulation/robocasa/closed_loop_eval.py:283-326及当前Childc9f...对应run_policy段（约343-381）：先canonicalize_raw15_for_env(a,False)，再env.step(env_action)，随后on_action用np.asarray(env_action).tolist()写submitted_env12。因此旧controller修改可穿回日志读取的同一数组。

应描述为“同一source_step的不同坐标表示/调用阶段”，不是不同时间帧或必然发生timestep错位。
在旧普通类的约定下，xy变换是R(-theta)；yaw/torso不经过此xy旋转。均值/mean_abs逐坐标可增加或减少，纯旋转仅保证逐步二维L2范数不变。比较时先对原始预测执行相同gate/clip，再比较同坐标系；不能用未裁剪predicted与旋转后数组直接断言范数守恒。
raw15 base通道应称原生归一化控制命令（平面速度、yaw及独立torso通道），不能再次统称位姿差分或线速度增量。

## 3. Local-TTT历史未沿这条路径被污染

当前及历史canonicalize_raw15_for_env均用新的np.zeros(15,dtype=float32)构造canonical，把pre-step env12分量逐一拷入；canonical不是env_action的视图。round-trip检查在进入env.step前完成。
run_policy在env.step成功返回后调用local_memory_client.record_completed(0, pre_composite, canonical_raw15)，不是传入可能已经被环境改写的env_action。
当前simulation/robocasa/local_memory_client.py:73-96把这份raw15转换为列表，存入executed_action/source_step历史。
因此，仅凭本次env_action被控制器原地改写，不能推断历史raw15污染、Checkpoint损坏、训练无效或需要重训。该结论限已查这条路径，不代表所有状态/历史一致性都已实测。
不要把canonical重新用post-step数组构造，亦不要把旧body/接口坐标命令强行转成init坐标送给训练模型；那会改变历史合同而不是修日志。

## 4. 正式Vendor与旧临时补丁不同

Root ee53...的third_party/robosuite_patches/0001-robocasa-1.0.1-compatibility.patch:1-110显示：
- Factory对JOINT_VELOCITY_LEGACY返回独立LegacyMobileBaseJointVelocityController；普通JOINT_VELOCITY仍是原普通类。
- Legacy的y-forward分支先np.copy重排；另一个分支明确action=action.copy()后再旋转。
- 两分支的轴处理和旋转约定也不应与旧普通类笼统视作相同。

故DS B6“两个名称映射同一个类”的结论只对其旧dirty editable环境成立，不能用于当前Vendor1ac174或用于证明train/eval完整等价。数据生成只有版本记录、无精确生成源码SHA的证据边界仍保留。
本轮没有安装或运行新Vendor，不证明其已在目标机器被实际加载；也不因为新Vendor有copy而免除调用方对日志时点的明确定义。

## 5. MEDIUM-DIAG-04：submitted_env12记录契约依赖可变的step入参

位置：Child c9f.../cosmos_framework/simulation/robocasa/closed_loop_eval.py的run_policy decode→env.step→on_action段；旧35b0...同样存在。
根因：保存的是step返回后同一个数组的内容，而字段名和前序统计将其当成提交到环境入口的命令。当前Root scripts/robocasa_eval_results.py:383-394只检查动作向量长度/有限值/步数，不能证明两种时点相同；不要求为此泛化为所有控制器的物理模型验证。
影响：旧运行的动作对账、逐坐标幅值统计与潜在replay可能使用不一致的边界语义。没有证明它直接降低策略SR；在新正式Legacy的已查复制路径中，不应再由同一底盘写入导致该污染。
验收范围：在调用step前为审计创建独立值快照，step成功后才写完成记录；异常时不能为未完成动作伪造evidence_completed或TTT提交。原来的env.step输入数值/调用顺序和物理行为不变；不要在step后将被修改的数组写回pre-step值，因为旧controller.goal_qvel可能保留了该数组引用。
可选post-step诊断字段仅命名为post_env_step_argument等，不能未读内部controller就称controller_command/actual_velocity。旧日志保持原样、以版本/运行来源标注其语义，不原地“修复”历史Evidence。

## 6. DS报告仍需的小范围澄清（无需重跑整轮）

1. B5说“逐step解出theta”。若theta是从同一对predicted/submitted向量反求，零残差主要是旋转拟合结果；只有来自独立记录的base姿态/控制器状态并按同一步对齐，才是独立验证航向的证据。请补theta数据来源、算法、零范数处理及误差精度。无需拒绝已有源码机制，也不要求重新跑仿真。
2. “非base通道全部精确一致”后写gripper=0.033（归一化），需说明它是最大差、幅值还是缩放参数，以及所比较的字段；非零差不能同时称全通道零误差。
3. B1的train/eval完全一致、B4的canonical20/native_window及state16可直接使用等旧表述仍与当前raw15/实际adapter边界冲突，需把旧段标为被后续修正，而非前后并存。
4. B7撤销归零可证明漂移根因是正确修正，但B4仍不能用改变controller配置后“同输入重查模型”来证明闭环因果。先做有效示教窗口上的模式/幅值配对；真实干预实验使用相同完整初态、允许观测自然分岔，不强制整个rollout共享相同观测。
5. 18任务中11空+9非空的统计集合仍应列出唯一task名说明；不得混合历史4-task与18-task运行的分母。

## 7. 既有状态与后续责任

AGENTS环境索引已在4a1ab5faf54adfff8be460f850f132c86a3a46d7补录，源码已同步的2026-10-23地图替代旧离线送达要求，本轮不重复追加。
Batch C fixture-only修复ee53/c9已通过源码及作者5项验证；截至本附件，没有新增DS修复后5项现场报告，整体CPU Gate仍PENDING_DS_DELTA，附件中A报告“已通过”不可替代具体结果。旧181+72和新作者5项不合并伪装成DS全绿。
Codex只处理上述日志快照的独立窄范围改动与CPU mutation test；新Child改动以后形成新精确Pair并做相应增量审查，不改当前G1或Vendor。
DS补齐报告口径/来源，按既有命令继续5项fixture复验。模型同观测配对推理、真实Kitchen/Owner手动canary属另外后续范围。本轮没有GPU、训练、仿真或Checkpoint操作。
