# V3 RoboCasa Batch B r2 — 独立增量源码/CPU审核 (Root891801bf / Vendor1ac174)

日期：2026-10-22
类型：Batch B pinned robosuite/RoboCasa vendor ABI repair **isolated implementation** fresh review。
**Formal code/source+author-CPU Verdict：`APPROVE`，严格仅限此精确隔离Pair和作者合成CPU Evidence。**
**Formal real-RoboCasa environment/equivalence Gate：`REQUEST_CHANGES` — EVIDENCE-ONLY，尚未发生真实Kitchen状态、实例化/reset/step、renderer/camera/physics实测。**
不允许自动合并V3、改变G1 frozen training/Checkpoint、安装到现运行的DS dirty editable vendor repo、启动GPU、Server或仿真。Batch A/G1/C的source/evaluation批准不与此Pair自动合并。

## 1. 精确 SHA 与范围

- Root Implementation `891801bf44736e1eaf44b91377f98c5c5035edd0`，candidate `v3-robocasa-vendor-b-20261022`。
- Child/Gitlink `35b0ea1ccee9ee26653ed6589c484f0997d1c586` **未变化**，已直接核对Root git tree mode160000。
- Vendor基准robosuite官方v1.5.2 `824ac14cefcfb7ec125fe5eb2e0bad7364466154`；确定性本地重建Commit `1ac174585293ed998ffc9cf73e47439798cf6f6c`、tree `195e30cfd5d37289d227a89234bd8bb069792905`。**它不是上游ARISE仓库已发表Commit；公共GitHub该SHA 404完全符合设计**。Authority为Root版本化Lock/Patch SHA/Commit metadata及两次可复现Build证据，不应去上游网络下载1ac174。
- RoboCasa evaluator版本1.0.1，固定Git commit `6f90063c0ec2b9916bbd977368b54c98d9c2d908`；MuJoCo python/native3.3.1，NumPy2.2.5。
- 对比Frozen Design/Evidence：`docs/collab/chatgpt/requests/2026-10-22_V3_RoboCasa_BatchB_vendor_pin_1_0_1_Codex_implementation.md` 和 `docs/collab/chatgpt/reviews/2026-10-22_V3_RoboCasa_BatchB_runtime_dependencies_1_0_1_version_selection_evidence_review.md`。前轮Vendor HIGH-10未提交过正式Vendor实现，不能按过去的4行stopgap宣布已修。
- 新Root相对V3设计docs SHA `d6b2484fa9f4ff5775ea1f13f3fcaf973ce499e8`：只新增 `scripts/robocasa_vendor.py`、`tools/v3/build_robocasa_vendor.py`、`tools/v3/robocasa_vendor_test.py`，以及 `third_party/robosuite_patches/` 下锁文件、368行实际Patch、Provenance/README、许可证/requirements；相关作者Evidence+docs/SESSION/TODO更新。未修改现存Queue/Child/训练器/算法/Optimizer/DCP。当前V3 docs HEAD可因审核记录更新变化，**不能当成这次Implementation SHA**。
- r2取代旧Root `2b14ef1a6b13be0c0dea405231506323594d81f2`，修复新Helper的非ASCII JSON canonical mismatch；Vendor patch/tree/Child与r1保持一致。不可沿用r1 helper Hash当r2。

## 2. Contract→实际production行为增量审核

### HIGH-10 原第三方临时patch缺失正确控制/初始化/物理语义：source修复已CLOSED（非真实physics Gate）

1. **Legacy Controller / axes** — 新 `third_party/robosuite_patches/0001-robocasa-1.0.1-compatibility.patch` 添加独立 `LegacyMobileBaseJointVelocityController`、对应 package export 和Factory branch；直接核对其源码后发现与固定上游引用 `ARISE-Initiative/robosuite@5ce6643f3092639d08f7b0f90ed1c6a84f50552c` 的 Legacy类相符。X轴前进和历史Y轴前进、yaw/heading调整分支分开，避免以前DS将LEGACY指向普通Controller的动作语义偏移。原X/Y、前/侧/左转/右转及非零heading共48 CPU cases使用真实 `set_goal` class体+synthetic Sim状态，不是真实本体电机轨迹。
2. **MujocoEnv lifecycle** — Patch不仅在ManipulationEnv表层接受 `load_model_on_init`，也修改RobotEnv、MujocoEnv的构造和reset逻辑，使False推迟首次创建模型/Sim/renderer并保持默认True eager语义；class/方法AST与固定上游引用吻合。CPU tests执行原类/函数主体、用counting doubles隔离外部Simulator，验证第一次及以后soft/hard reset与seed RNG边界。
3. **_destroy_sim** — 用 `getattr(self,"sim",None)`保护未创建的Sim和二次回收，测试不存在/None/live。
4. **CCD/sleeping** — Task的两个flags真实传至MujocoWorldBase。新World在原有`<option><flag>`中设置`multiccd=enable/disable`而非吞参；实际MuJoCo3.3.1 native tiny XML编译的 `enableflags` 观察到0/16，且没有插入冲突option。MuJoCo3.3.1没有目标sleeping-islands开关，False表达能力不存在、True显式ValueError；不能误用与sleeping不同的`mjENBL_ISLAND`。**不宣称目标Kitchen已用此属性构造完整场景**。
5. Fixed source/provenance `source_provenance.json`存上游AST及Blob哈希，`vendor.lock.json`存base commit、Patch SHA256 `36184d6a5ddaa7371be89ba332f72bc89a18e8d0a7a0e36119e7215f9a465d30`、目标tree/commit+固定Git author metadata以及8个文件base/patched SHA。两个隔离离线Build的 `build.json`见证得到同一Vendor commit/tree。不直接修改DS脏editable树或自动pip安装。
6. **运行时与数据来源** — 新`scripts/robocasa_vendor.py:39-258`用选定Simulator解释器/导入环境动态校验实import`__file__`、module/version、Git HEAD、tracked/untracked/ignored文件、asset inventory、MuJoCo Native/NumPy、官方horizon及Lock、probe脚本 SHA；使用 `git ls-files --others -z` 同时列出被忽略的文件（已独立用临时Git仓验证此命令语义），特殊pyc必须与tracked源码compile code一致。source dirty、unknown .py/script/so、未知asset与库存不符均fail closed。Runtime探针不以参数文件伪造结果。已阅读完整helper及对应测试：没有发现本Batch B source范围的阻断性语义空洞。
7. **r2 Unicode identity** — `scripts/robocasa_vendor.py:28-30` 的 `canonical()`使用 `json.dumps(sort_keys=True, ensure_ascii=False, separators=..., allow_nan=False).encode()`，与未修改的`scripts/v3_evaluation_identity.py:_canonical()`逐项一致。真实legacy `claim_evaluation_run` 的中文任务元数据路径/输出路径 + same-identity Resume + changed-runtime拒绝测试已直接阅读，关闭r1新增Bug。
8. **正式Queue接线边界** — `build_verified_evaluation_identity`及`collect_runtime`是给未来Batch C的API，**本r2未将其接到当前旧Queue或真实sim启动点**；Runtime Hash与来源并不能据此自动验证过去现存评测结果。不可将“新函数存在且CPU pass”说成“已在Owner正式命令中执行fail-closed”。该集成由Batch C独立完成。

## 3. CPU Evidence独立阅读与可信范围

- Codex交接在 `docs/collab/codex/reviews/2026-10-22_RoboCasa_Batch_B_vendor_pin_author_handoff.md` (docs SHA `05ff4283bc70354c5e3bbdddf1af56998b49b68b`)，r2证据位于 `docs/collab/codex/evidence/2026-10-22_RoboCasa_Batch_B_vendor_author_cpu_r2/`；r1原Vendor Build和物理小模型见证位于无`_r2`目录。直接打开 r2 `gate.json`、`final-r2.log/xml`、`static-r2.log`及旧`author_build.json`、`behavior_witness.json`并核对实际源码。
- r2 **110 passed，0failed/error/skip**，JUnit tests=110（不是110+中间轮次或加另一个109）；15.89s；Ruff0.12.7 check/format与语法、patch SHA及重建元数据证据均PASS。原v1.5.2基线预期RED4 case、r1 Unicode错误预期RED1，各自保留；不把预期RED当final GREEN失败。两次重建Vendor commit/tree一致。
- CPU强处：真实Legacy class的forward-axis/非零heading数值；原继承类体的delay/reset；实际MuJoCo3.3.1小XML物理flags编译；离线Git来源与runtime-import负例、dirty/index/untracked/ignored/poisonedpyc；现有immutable eval identity Unicode读写/Resume联动；官方horizon与metadata generation0.5.1/version1.0.1区分。
- **限制**：runtime positive tests使用明确的metadata/registration/import doubles；作者CPU环境全量SIM runtime probe **Expected BLOCKED**（因未实际安装完整RoboCasa/robosuite dependency），并非真实SIM PYTHON输入通过。所有Kitchen create/reset/step、MjData、offscreen render、相机真实图、raw15→env12→PandaOmron实际动力学及官方target场景保持**未执行/未证明**。作者原DS的2096byte stopgap diff尚未读到，只记录DS attested SHA `dbe9a0d9...`，不能说比较了真实四行原Patch的全部原始bytes。

## 4. 后续 Gate 与不混入的责任

- **Source/Author CPU Gate：`APPROVE`**。没有要求Codex在此同一source Pair上再改代码的blocker；DS_PRO可对精确Root891801bf / Child35b0 / reconstructed Vendor1ac17458 做独立纯CPU re-build/runtime-scope复验。
- **Batch B 目标机依赖/真实物理 Gate：`REQUEST_CHANGES`（EVIDENCE-ONLY）**。Evidence源头为候选 patched vendor 与目标机实际环境；未经过Owner授权前不得安装或改任何使用中的venv。须先于真实eval在**隔离新Sim venv / checkout**，做真解释器 `probe_runtime`（非mock）、Git import origin、资产SHA/clean、MuJoCo/native，之后以Owner**单独授权**的真实RoboCasa任务开展CloseFridge/NavigateKitchen PandaOmron Kitchen create/reset/step，关键时点取Camera/State、base axes、CCD compiled model flag、target object/layout split、官方horizon/seed/动作一致性witness。若这些失败须当作新production/physics blocker回报，不吞错声称绿色。
- **Batch C 尚未交付** 用户统一手动Launcher/YAML、任务选择、GPU slots、episodes、环境与generated video和真实runtime两次探针；Batch A另有不同Root/Child，G1 Resume另有不同Child；将来任何合并必须产生新Formal Pair及独立Code/CPU/E2E Gate。无需重复审核本r2 Pair因Review或Inbox产生的docs-only commits。
- **历史诊断SR 1/20** / **18Task首轮INCOMPLETE 85/90**来自DS脏临时补丁，不可成为物理环境已复现的正式benchmark成绩。
- 当前实现和证据均未操作G1冻结资产、模型/GPU/仿真；**本`APPROVE`不授权任何真实执行/部署/合并/训练或重新解释生成环境0.5.1为1.0.1**。

**最终：精确Pair 891801bf /35b0 + Vendor1ac174 的隔离源码与作者CPU实现Gate为 APPROVE；真实物理/正式部署Gate开放并保持 REQUEST_CHANGES。**
