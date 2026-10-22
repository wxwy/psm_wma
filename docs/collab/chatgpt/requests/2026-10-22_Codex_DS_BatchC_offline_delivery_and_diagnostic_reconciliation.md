# Codex / DS_PRO：Batch C r2 源码离线交付与慢动作报告对账

日期：2026-10-22。
关联分析：docs/collab/chatgpt/reviews/2026-10-22_DS_source_delivery_BLOCKED_and_slowmotion_B_evidence_review.md。
状态：源码交付阻塞；不是新增生产缺陷。以下是交付/核验安排，不授权GPU、真实仿真、模型推理、训练启停或活动环境安装。

## A. Codex：提供可供Owner转交的真正离线包，不重复修代码

正式验收对象不变：
- Root a4b22b929175e462b6a8db57ad2abee7e220dd37
- Child/Gitlink c9f21040f462a114d597fc83773cb9b6a9e96214
- Vendor可重建产物1ac174585293ed998ffc9cf73e47439798cf6f6c

DS本地旧Root8610ad88、Child35b0ea1c，GitHub代理失败，两个测试文件与新review/runbook不存在。不能只让DS再次fetch，不应复制新测试到旧生产代码树。

请Codex从其已具备精确提交的环境，生成并实际交付：
1. Root Git bundle，包含正式Root及其运行/身份核验所需对象与历史；Child独立Git bundle，包含c9f21040及所需历史。不要用只有工作树文件的ZIP冒充完整Git来源。
2. bundle manifest：完整目标SHA、Root Gitlink、bundle SHA256、大小、refs和是否存在prerequisite对象。优先自包含；若为增量必须枚举并证实DS已有每个prerequisite，不能仅说“基于最新V3”。
3. 在作者新空目录独立导入两个bundle，检出精确Root/Child，确认HEAD/Gitlink/文件Blob和工作树clean，运行最小只读导入检查。不得依赖作者其他clone的alternates；不得漏掉身份检查所需Git对象。
4. 原审核文件和DS验收指令以单独文档包交付，附SHA及其归档commit。它们不在Formal Root时，不要复制进入正式Root工作树造成dirty；DS在外置目录读取：
   - docs/collab/chatgpt/reviews/2026-10-22_V3_RoboCasa_BatchC_r2_a4b22b92_c9f21040_incremental_review.md
   - docs/collab/chatgpt/requests/2026-10-22_DS_PRO_BatchC_r2_a4b22b92_C01_C02_CPU_acceptance.md
   - 作者commands.json / source_checks.json / gate.json及适用的CPU依赖版本说明。
5. 将文件通过Owner可访问的附件或已批准传输位置实际交付；仅提交“包位于作者/tmp”的文字不等于DS已收到。不要在对话索取或粘贴PAT，不打包模型、数据集、私钥、凭据及活动训练目录。

Vendor不是根仓或子仓的现有Gitlink对象。单独在vendor仓核对或由锁文件在新隔离目录重建；如本轮只是原定三个合成CPU测试，按测试实际依赖执行，不将完整真实Kitchen安装前置化。若交vendor包，同样附base/patch/tree/commit和独立重建证据。

本次交付不要求改变生产源码或创建新Formal Pair；后续docs HEAD不替代a4/c9。若打包发现真实对象缺失，明确报告，不能重做git init/commit生成不同SHA冒充原版。

## B. DS：包到位后执行原有定向CPU合同

只在新的独立验证目录导入，不改当前G1工作树、旧评测证据或dirty vendor。先记录收到文件的SHA256，再检查各自正确repo的Root/Child/Gitlink和clean状态；不要在Root仓查vendor SHA后据此宣布vendor损坏。

源码和实际CPU依赖到位后，运行已发runbook的三个文件：
- tools/v3/robocasa_eval_results_test.py
- tools/v3/robocasa_processes_test.py
- tools/v3/eval_robocasa_queue_identity_test.py

预期183项顶层测试 +72 subtests（以真实JUnit为准），再做指定Ruff/格式检查。缺Python依赖另列ENVIRONMENT_BLOCKED，不安装进运行中的训练venv；没有执行就是TESTS_NOT_RUN，不能写FAIL/PASS。

仅收到两份测试文件或一份review不足以正式验收；必须具有与合同一致的完整相关源码及来源。不要重复全盘fsck/无界网络重试；在当前SOURCE_DELIVERY_BLOCKED下等交付证据发生实质变化再继续。

## C. DS：已有JSONL的最小对账，不新增仿真

1. 把formal_4task_x5ep和formal_18task_x5ep_8gpu分别命名Run-A/Run-B，逐个task/episode列文件绝对路径、SHA256、记录数量、最后source_step、outcome/是否中断、筛选条件。不得混用39.69%和35.6%为checkpoint改善/退化。
2. 核对“11个全空+9个非空=20”与18 underlying classes不一致的计数；列unique task、重复导出/目录、空文件。
3. 对B2/B3的NavigateKitchen r02(103 base帧)、r01(144帧)、r03(120帧)，以完全相同(record file, episode, source_step)键逐行比较predicted_raw15[:3]和submitted_env12[7:10]，检查abs(submitted)<=abs(predicted)+浮点容差及decode合同。r02表中0.107→0.146、r01加权0.10965→0.156目前不可能由clip解释；先报告实际差异与统计来源，不能自行改动作代码。
4. 给R的精确定义（平均单位方向长度还是加权位移比）以及零向量处理；高R不等于证明模型意图。base命令非零不等于物理移动；模式占比不同不等于相同状态下的分类错误率。
5. B1区分default JSON、dataset metadata、Kitchen运行时override、最终Controller class及具体Git源码。纠正canonical20/native_window与本次raw15执行来源未闭合的问题，不能用旧V2片段解释G1。仅凭metadata相同不声称train/eval控制器全部一致。

## D. B4只改设计，暂不执行

首先恢复原目标：在G1有效示教窗口上做同obs/state/goal与因果Local-TTT历史的prediction-vs-GT比较；PickPlace失败rollout全空不阻止示教取样。先证明输入样本包含完整相机/状态、精确时序、标签与cache/index身份，不能用有损MP4/init.png默认替代模型原输入，也不能泄漏未来标签进TTT。

输出EEF置零使累计量降低是数学必然，不证明物理漂移；改变controller desired/achieved也不会在同一输入下直接改当前模型预测。若改历史后再查模型，应标历史条件敏感性而非物理干预。

将三个问题拆开报告：
- 配对策略：同GT模式下的mode confusion、幅值/方向、base帧EEF泄漏与不同checkpoint。
- 目标递推：同已记录动作条件下算参考目标变化，仅标条件性风险。
- 后续真实干预：Owner另行授权后，从相同完整环境/控制器/策略初态一次只改一个因素，允许观测自然分岔，实测EEF相对base偏移、goal tracking、导航进度/碰撞/成功率。

## E. 文档补录

环境地图已另存 docs/collab/chatgpt/context/2026-10-22_DS_runtime_environment_map.md。Codex在收到本交接后仅以docs-only提交向现有AGENTS.md追加该文件入口，不覆盖原协作规范；同时按项目规则追加canonical Inbox交付/报告状态。前轮Batch C r2技术APPROVE的Detailed review已存在，若Canonical entry仍缺，只补记录，不重复代码审核。GPT本轮没有宣称AGENTS/Canonical入口已改完。

完成离线交付后，Codex报告实际附件/可达位置、包hash与导入验证；DS再做接收与CPU验收。全过程不干扰当前G1训练。
