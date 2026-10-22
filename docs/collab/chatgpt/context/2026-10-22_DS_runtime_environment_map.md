# DS目标机环境地图（2026-10-22；供AGENTS索引）

这是路径/来源索引，不是生产实施Pair、可直接执行的配置或真实环境PASS证明。目标机事实来自Owner转交DS报告；GPT未登录该主机验证。V3是当前开发分支，活动G1训练仍保持其启动时的隔离源码，禁止为同步V3修改活动worktree。

## 1. 目录职责与已知状态

| 对象 | 路径/身份 | 说明 |
|---|---|---|
| Root代码仓 | wxwy/psm_wma，分支V3；DS简称psm_wma_v3 | 最新报告本地HEAD8610ad88、旧origin/V3引用111ef240；完整绝对Root路径需现场git --show-toplevel，不猜 |
| Child代码仓 | wxwy/cosmos-framework，Root/cosmos-framework | DS旧本地HEAD35b0ea1c；不是目标c9f21040 |
| Batch C r2验收Pair | Root a4b22b929175e462b6a8db57ad2abee7e220dd37 / Child c9f21040f462a114d597fc83773cb9b6a9e96214 | 本次DS尚无对象，需离线交付后新隔离checkout；不能把任意docs HEAD或旧树当实施版 |
| 历史G1验证worktree | /mnt/data1/data_v2_0617/dspro_g1_cross_pair_resume_20261022/root | 历史验收目录；不是已证明的当前训练cwd，不覆盖 |
| G1训练输出根 | /mnt/data1/data_v2_0617/psm_wma_v3_packed128_runs_fresh_g1_20261019 | frozen identity/config/DCP资产；内部psm_wma_v3目录不是Git代码仓 |
| G1 Job | 上述根/psm_wma_v3/corrected_phase5/packed128_droid_fresh_g1_20261019 | 不修改canonical config、identity、历史checkpoint；本次不启动或重启 |
| 历史评测根 | /mnt/data1/data_v2_0617/dspro_iter8900_eval_ba91ebb7 | formal_4task_x5ep和formal_18task_x5ep_8gpu是两个不同Run，分别统计 |
| 数据集 | /mnt/data1/data_v2_0617/robocasa365_official/v1.0 | target/atomic下18 underlying classes；不要把语言phrasing当任务 |
| 旧RoboCasa editable | /mnt/data1/data_v2_0617/robocasa_repo | DS报告1.0.1 @6f90063c0ec2b9916bbd977368b54c98d9c2d908，tracked clean，untracked资产另计 |
| 旧robosuite editable | /mnt/data1/data_v2_0617/robosuite_repo | tag824ac14cefcfb7ec125fe5eb2e0bad7364466154+4未提交补丁+1备份；不作为新正式Vendor |
| 目标Vendor | 1ac174585293ed998ffc9cf73e47439798cf6f6c | Root third_party/robosuite_patches锁文件可离线重建；不是Root/Child对象或上游可fetch的公开commit |
| 历史Server/Sim Python | /mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python | 先前DS声明同一venv；本轮实际sys.executable/import origins需明确，不能凭目录名断言 |
| conda robocasa | 环境名由DS报告，绝对解释器路径未证实 | 环境名不作为版本或运行权威，不安装进活动训练环境 |
| 依赖取证 | /mnt/data1/data_v2_0617/dspro_batchB_vendor_readonly_20261022/evidence | 原5件版本/补丁证据 |
| 新B报告 | 历史评测根/iter8900_diagnosis_followup_B_report_20261022.md | 控制器/段统计/配对方案，含待纠正推论 |
| 新A报告 | 历史评测根/batchC_r2_CPU_acceptance_BLOCKED_20261022.md | 源码未送达、测试未执行，不是测试失败 |

此前实际依赖报告MuJoCo wheel/native3.3.1、NumPy2.2.5。数据生成metadata记录RoboCasa0.5.1/robosuite1.5.2/MuJoCo3.3.1，但生成Git commit未知；不得把metadata版本或default JSON当训练与实际评测逐字节/物理等价证明。

## 2. 关键源码与动作布局

固定历史执行Child35b0ea1c的simulation/robocasa/eval_utils.py：
- raw15模型动作：[base_motion4, control_mode1, eef_pos3, eef_rot6d6, gripper1]。
- submitted env12：[eef_pos3, eef_rotvec3, gripper1, base_motion4, control_mode1]。
- decode_15d_to_env12 / canonicalize_raw15_for_env；base在mode>0时逐通道clip，否则清零；不能拿canonical20或ego路径替代。

G1冻结Child2d128ed5的ExactWindowCachedDataset/OfficialRoboCasaPolicyAdapter调用官方转换helper。观测源state16与模型state15不是同一布局；报告中的state16为base_pos3/base_quat4/eef_rel_pos3/eef_rel_quat4/gripper2，模型state token须依真实adapter转换，不能直接喂原16维。状态前缀与padding不计入预测动作统计。没有统计归一化不意味着控制器没有[-1,1]到目标增量的scale。

Controller相关：
- robosuite/controllers/config/robots/default_pandaomron.json的具体位置以实际仓为准；元数据字段需同运行时resolved配置分开记录。
- robosuite/controllers/composite/composite_controller.py 的HybridMobileBase选择desired/achieved。
- robosuite/controllers/parts/arm/osc.py 的scale_action、compute_goal_pos、compute_goal_ori。
- RoboCasa6f90063c的robocasa/environments/kitchen/kitchen.py在给定controller_configs的PandaOmron路径重写base type为JOINT_VELOCITY_LEGACY。
- 旧DS临时Controller别名和新的正式Legacy类不是同一个已验实现；当前“全链正确”不能由default JSON推导。

## 3. 当前Batch C r2验收缺件

DS未取得精确Root/Child对象；results_test.py与processes_test.py缺失；Queue测试只有旧树版本；新review/runbook在本地不可达。当前为SOURCE_DELIVERY_BLOCKED。先交完整来源，不靠拷两个文件补旧仓。

三个合成CPU测试不等于真实Kitchen测试；真实Vendor安装与physics Gate另行验证。Vendor产物缺失应在vendor工作目录核查，不能在Root仓git cat-file后直接判定其应存在。

离线交付与诊断对账指令：docs/collab/chatgpt/requests/2026-10-22_Codex_DS_BatchC_offline_delivery_and_diagnostic_reconciliation.md。

## 4. AGENTS追加入口（待Codex docs-only写入）

建议在AGENTS.md追加：

> 2026-10-22 DS环境索引：读取 docs/collab/chatgpt/context/2026-10-22_DS_runtime_environment_map.md。路径与依赖状态按DS报告标明，不把训练输出目录当Git仓、不把旧editable当新Vendor。当前Batch C r2的精确Root/Child离线送达是CPU验收前置；不覆盖活动G1工作树。

本文件已建立索引内容，不声称AGENTS入口、Canonical Inbox或离线bundle已经由GPT写入/生成。后续补入口必须保留原文并按最新Blob防并发覆盖。
