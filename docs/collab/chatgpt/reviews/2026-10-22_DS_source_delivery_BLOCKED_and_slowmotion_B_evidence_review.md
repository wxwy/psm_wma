# DS_PRO A/B 报告接收：源码交付阻塞与慢动作诊断边界

日期：2026-10-22。
依据：Owner上传《DS_PRO: iter8900 慢动作诊断跟进 — B 报告》及同文件所附 Batch C r2 CPU BLOCKED 报告。附件19145 bytes，SHA256 f753f730c68d6a8f5d74afec5adba57298907f3bf847150d8df7d01abbb54e9a。
证据级别：目标机路径、帧统计、文件缺失与网络错误由DS报告；GPT未读取服务器JSONL/MP4或执行模型。本轮独立工作仅为附件内部一致性复算、指定历史源码查证及文档记录。

## 1. Formal Pair 未变：不重新审核 Batch C 代码

本轮远端V3起点 d1d640b85bc907ac557138c8aba087a825cabb82，仅作状态记录；正式Batch C r2仍为 Root a4b22b929175e462b6a8db57ad2abee7e220dd37 / Child-Gitlink c9f21040f462a114d597fc83773cb9b6a9e96214，Vendor可重建产物1ac174585293ed998ffc9cf73e47439798cf6f6c。远端scripts/tools/third_party树与已记录r2一致，未重新做实现审核。

A报告是 SOURCE_DELIVERY_BLOCKED / TESTS_NOT_RUN，不是测试FAIL，也不是新的C01/C02生产缺陷。DS没有收到精确Root/Child对象及测试文件，且git ls-remote失败，故没有JUnit/Ruff结果。保持此前代码技术审核结论及独立CPU未完成的边界；不要求Codex再修改C01/C02代码。此前正式review/Canonical Inbox落盘是否齐备属于独立记录事项，本文件不冒称已补齐。

交付责任：Codex打包可验证的精确源码对象和文档，通过Owner能传入目标机的渠道交付；DS在新隔离目录导入、核对完整SHA/Gitlink后再验收。不能只把两个测试文件拷进8610ad88/35b0ea1c旧树，也不能弱化版本锁来通过Gate。

Vendor 1ac174是固定补丁集的本地可重建commit，不是Root仓、Child仓或上游robosuite必须已有的对象。应在正确vendor仓检查，或在新目录依锁文件重建。仅针对C01/C02的三个合成CPU测试文件，不应因尚未安装真实Vendor就提前判定无法运行；以commands.json、测试实际依赖和现场解释器结果区分源码缺失、Python依赖缺失、真实环境未验收。三者不能混成一个阻塞。

## 2. B2/B3 的统计可保留，但不可拼接成同一轮实验

本报告改用 formal_18task_x5ep_8gpu 的中断运行，NavigateKitchen有4个非空episode、1638条动作记录；前次报告使用 formal_4task_x5ep 的5个episode、2250条动作。这不是相同样本，不能把35.6%解释成从39.69%改善/退化，不能套用前轮22.4%的全帧底盘命令比。

附件7段长度之和217+57+87+103+39+73+8=584，与B3的base帧数一致；584/1638=35.6532%。B3每episode的submitted mean_abs按217/144/103/120加权，得到[0.249262,0.348526,0.139894]，与其ALL行舍入一致。该部分内部可复核。

但B2与B3存在待对账处。历史Child35b0ea1c的eval_utils.decode_15d_to_env12对base启用帧执行逐通道clip，故相同帧/通道应满足abs(submitted)<=abs(predicted)，其均值亦如此。附件r02同为103帧：B2 predicted x mean_abs=0.107，B3 submitted x mean_abs=0.146，不能由仅裁剪产生；r01两段57/87帧加权predicted x约0.10965，B3为0.156；r03加权predicted x约0.08182，B3为0.085。不能直接归因为解码bug，先核对文件SHA、episode、source_step、字段、坐标顺序和采样集合。

另有目录计数问题：附件同时写11个任务全空、9个任务非空，合计20而非18。需要列出unique底层task及文件状态，说明是否包含重复导出/历史目录，不能把零字节文件当零动作。

高方向一致性R支持有偏且时间相关的输出，不足以证明模型主动意图或排除偏置噪声。较大submitted base命令证明发出了移动命令，不等于真实base已经移动。示教和rollout的base模式占比差异是状态占用分布差异，不直接等于模式分类错误率。训练对照本轮仅前20ep/3270帧，也不能替代G1实际cache/index分布。

## 3. 控制器语义：缩小可确认范围

报告B1的元数据/default JSON吻合，可支持已列配置字段相同，但不能推出“与训练数据完全一致、无train/eval控制器不匹配”。实际RoboCasa6f90063c的kitchen.py在controller_configs非空且PandaOmron时，会把base type重写为JOINT_VELOCITY_LEGACY；DS旧环境另有将其映射到普通Controller的临时补丁。因此default_pandaomron.json中的JOINT_VELOCITY不代表最终有效类。生成记录RoboCasa0.5.1没有精确生成commit，实际评测RoboCasa1.0.1也不能仅靠同名字段宣称物理等价。

HYBRID_MOBILE_BASE + OSC(delta,base)下desired/achieved目标更新差异，已有固定robosuite源码支持，保留为机制证据。但附件canonical20_to_env12、canonical action20、native_window等引用没有给出与历史raw15正式Pair一致的来源，不能直接移植入G1诊断。历史35b0ea1c的实际路径是canonicalize_raw15_for_env、decode_15d_to_env12；base_mode由raw15[4]>0决定，等于0也走arm门控。请精确绑定所引用文件的repo/commit/blob/函数，不按行号或旧V2片段判断。

r00的217帧EEF带符号和[2.930,-0.816,5.649]，若均为同一desired递推、每步正确缩放且无重置/裁剪差异，乘0.05得到约[0.1465,-0.0408,0.28245]m，范数约0.3208m。这只能作为控制器目标递推的条件性风险估算，不是实测末端位移或漂移，也未证明其导致导航慢。未知缩放变量是否实际使用需追具体控制器，禁止仅因出现未使用局部变量就修改生产控制逻辑。

## 4. B4 当前实验设计不支持所宣称的因果判定

问题定位：附件B4（第104–147行），尤其“同窗口将EEF置0/把更新改achieved后重新查询模型、无需re-simulate”及“累计量降低即可证明漂移主因”。

- 输出后处理置零必然降低所计算的EEF累计量，这是构造结果，不是物理漂移/慢动作因果证据。
- 改环境控制器desired为achieved不会在保持全部模型输入和随机状态不变时直接改变本次模型预测；若改历史动作再输入Local-TTT，则是历史条件敏感性实验，固定观测已不再与该反事实执行历史动力学一致。
- MP4/init.png并不自动具备原始双视图预动作输入、完整state16、精确时序与原始像素，也不是示教专家标签。必须先盘点实际保存内容；同seed重新仿真不能单独保证复现完整物理/控制器/策略状态。
- “同观测诊断”原目标是用G1实际有效示教窗口比较prediction与target，区分条件策略收缩和闭环状态占用差异。PickPlace旧rollout全空不妨碍从已有示教中取有效窗口，不需要以重新生成失败rollout观测作为首个前置。

应拆为三类、不得混报：
1. 示教配对策略诊断：原始obs/state/goal、因果Local-TTT历史、排除state token/padding，固定sampling seed；比较预测与GT的模式混淆、分GT模式的幅值/方向和base帧EEF泄漏。避免未来action/latent标签进入预测前的fast-state更新。
2. 控制器目标递推分析：固定已记录动作，按实际控制器算goal轨迹，原样与base帧EEF平移置零各算一次；仅证明递推量差异，不证明环境位移/成功率。
3. 后续受Owner单独授权的物理干预：从相同完整环境与控制器初态，分别原策略/单一输出干预，或单独的controller更新干预；一次只改一个因素。干预后观测可自然分岔，不再要求同观测。实测EEF相对base偏移、目标跟踪误差、导航进度/碰撞/成功率后才讨论因果。

## 5. 下一步责任

Codex：交付精确源码离线包及文档、只做必要的环境地图/AGENTS入口补录；不为源码同步阻塞新增生产修复。
DS：停止全盘盲搜和反复网络重试，收到包后做新隔离checkout与原定向CPU验收；先对账B2/B3并修正B1/B4文字设计，现有JSONL只读即可，不启动新模型或Kitchen。
GPT：本文件是新增报告的Evidence/实验设计意见，不是同Pair重复实现审核。慢动作结论与Batch C独立CPU Gate分开记录；不授权GPU、安装活动环境、修改G1冻结资产或动作增益。
