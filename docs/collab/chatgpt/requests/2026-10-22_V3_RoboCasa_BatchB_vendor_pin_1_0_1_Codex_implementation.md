# Codex Batch B — 正式版本选型与物理兼容修复实现要求（Owner执行的RoboCasa Eval）

日期：2026-10-22
本任务是 DS_PRO 新依赖版本报告后的正式构建方向，依据审核文件：
`docs/collab/chatgpt/reviews/2026-10-22_V3_RoboCasa_BatchB_runtime_dependencies_1_0_1_version_selection_evidence_review.md`。
Scope：**Batch B vendor+physics+runtime provenance only**。Batch A task/session/timeouts及 Batch C manual CLI尚在独立源码分支；不得直接把三个Child/Gitlink强拼，后续组合必须新Pair Gate。
**全部工作先在隔离分支进行**。不得直接修改训练机脏editable`robosuite_repo`、真实G1冻结Config/Checkpoint/Trainer或数据，不启动GPU/仿真；所有真实环境E2E需Owner另行授权。

## 1. 确定下来的版本基线（不得再问Owner二选一）

正式目标是**RoboCasa365 target-atomic的官方评测协议**，不是试图在新版本里重现未经证明的2025原采集环境：

- **RoboCasa evaluator**：`1.0.1`，固定公开Git可解析完整 commit `6f90063c0ec2b9916bbd977368b54c98d9c2d908`，不是不具备Git标识的0.5.1，也不要猜`v1.0.1` tag（当前无）。
- **robosuite patch BASE**：上游`v1.5.2` release commit `824ac14cefcfb7ec125fe5eb2e0bad7364466154`；**最终正式执行HEAD**必须是其上另一个清洁的、可复现、行为正确的vendor fork精确commit，或受控补丁集 SHA+严格安装/校验哈希。此Tag原件在RoboCasa1.0.1中缺关键语义；不可把原Tag当最终可运行head。
- **MuJoCo** Python wheel+native库均 `3.3.1`；**NumPy** `2.2.5`。RoboCasa固定6f90063的`robocasa/__init__.py` 明确assert二者及robosuite>=1.5.2；Runtime必须证实`mujoco.mj_versionString()==3.3.1`、版本及实际import路径。
- **训练数据来源元数据（单独字段）**：18/18 `extras/dataset_meta.json`记载 RoboCasa `0.5.1`、robosuite `1.5.2`、MuJoCo `3.3.1`。**RoboCasa0.5.1 Git SHA UNKNOWN**，不可硬编码虚构/自动回滚/把版本字符串当GitTag。2025-08文件目录日期早于robosuite v1.5.2正式GitHub release `2025-12-24`，需将`recorded_version`和`capture_time_git_commit`拆开，不得冒称2025年录制时使用了2025年12月正式tag。
- RoboCasa官方v1.0.1的evaluation task horizon扩大1.5×，保留官方target split、10 target kitchens、target object set、每Task官方horizon/seed。不能为追求SR回退旧horizon。
- 只读来源报告本地：`/mnt/data1/data_v2_0617/dspro_batchB_vendor_readonly_20261022/evidence/`；其 `robosuite_4patches.diff` 据DS报告SHA256 `dbe9a0d9ccdcc1052b9bddbcfe5235205461292b762cc2fac2f92a706365e74c`、大小2096 bytes。GPT并未读取到此本机原始diff，不得声称内容逐字节验证过。Codex应在能访问时核查，或依据相同Tag已知四处补丁文本独立实现正确vendor diff。

## 2. 要求的4个补丁不能只接受参数不实现语义

必须交付**可独立测试的物理等价/ABI相容证据**，并说明原patch与最终实现差异：

1. `robosuite/controllers/parts/controller_factory.py:173`：
   - RoboCasa PandaOmron指定`JOINT_VELOCITY_LEGACY`；DS的临时别名映射到普通`MobileBaseJointVelocityController`不足以证明旧数据所用前进轴语义。
   - 按官方后续`LegacyMobileBaseJointVelocityController`的forward-axis条件与action reorder语义做**完整正确的 backport**或经可重复性证明选择后继vendor commit，记录class type/axes/source、保证base动作的forward/lateral/yaw执行合同不漂移。
2. `robosuite/environments/base.py:740`：
   - 模型/Sim尚未构造以及二次close时`_destroy_sim`不得抛未定义属性错误；保留安全清理，测试未创建/已创建/已回收状态。
3. `robosuite/environments/manipulation/manipulation_env.py:147`：
   - `load_model_on_init=False` 不只是Signature，多层继承 `ManipulationEnv→RobotEnv→MujocoEnv` 必须真正延迟`_load_model`/`_initialize_sim`到首次Reset；确保RoboCasa原Kitchen构造/随机scene布置合同与后续reset一致。
4. `robosuite/models/tasks/task.py:63-64`：
   - `enable_multiccd=True`、`enable_sleeping_islands=False` 必须实传到`MujocoWorldBase`和生成的MuJoCo Model/option，不可丢弃参数；测试最终真实模型flag值/编译结果，而非仅不抛TypeError。

## 3. 最小交付组件

- **确定性的 vendor 来源实现**：在可控隔离的`robosuite` fork固定新40位HEAD，或 Root项目`third_party/robosuite_patches` patchset + pinned base SHA、patch SHA256与完全可复现的构建/安装指令。禁止pip最新master、禁止对DS现有dirty worktree静默patch或reset/clean、禁止运行时monkeypatch。尽可能不需要网络，允许指定本地清洁clone/cache。
- **版本化依赖验收/manifest**：在Batch B自身小型preflight可只读验证`sys.executable`、真实robosuite/robocasa/MuJoCo/NumPy`__file__`/Python metadata/native mj_version、HEAD/tree status与patch摘要；`robocasa@6f90063`、`robosuite@<new patched commit>`、MuJoCo3.3.1、NumPy2.2.5；dirty tracked/untracked源或无法辨别import origin直接BLOCKED。不得将普通数据集资产untracked误认成Git源码修改，应明确对来源路径与允许资产类型的可信审计规则（任何不明untracked脚本/代码仍拒绝）。
- **评测identity**：保存`evaluation_runtime`版本权威与`dataset.recorded_generation_versions`以及`dataset.generation_git_commit=UNKNOWN`两个独立块。真实评测运行中不得靠输入配置伪称对方Python导入的Module是真正固定版本；需要运行侧manifest由实际解释器返回，并绑定digest与完整审计证据。
- **回归/物理 ABI**：CPU unit 对Controller/factory/签名和Option链路有正反例；有Owner后续明确授权时真实`PandaOmron`的CloseFridge、NavigateKitchen`create_env/reset/step`，base forward/lateral/yaw动作相对实物body axis/EEF state camera obs与原训练raw15→env12解码合同的对照；task reset/scene object split/官方horizon/seed可验证。不得用模型SR0.05优化条件取代物理一致验证。
- **作者证据**：新 exact Git Root/Child vendor pin SHAs，变更文件列表+精确diff，full CPU logs/命令/RC、Ruff/syntax/静态，以及（若已授权）真实env体例witness；未执行真实environment时必须注明Gate仍未完全闭合，不能声称正式benchmark PASS。

## 4. 与 Batch A/C 的交付顺序

先独立Batch B Candidate与对应CPU/static source Gate；在此基础上 Batch C 手动launcher须支持Owner设定GPU/tasks/episodes/video modes/超时/输出，并在`--dry-run`时CPU-only核查依赖SHA与metadata来源。Batch A + B + C合并必须新的 Root/Child/Gitlink Vendor Formal Pair及独立代码/目标机CPU/Owner真实canary验收，不是“分别通过所以全链等于通过”。不需要停止G1 30k，绝不更改历史Checkpoint/Config/JobIdentity。
该安排**不妨碍Codex开始固定1.0.1+正确vendor兼容实现**，无需让DS重新寻找不存在的0.5.1 Tag。若后续取得可信0.5.1完整commit，作为可选旧数据复现实验另开对照Gate，不自动改变当前官方评测baseline。
