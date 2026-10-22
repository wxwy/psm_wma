# PSM-WMA V3 — Batch B DS_PRO 依赖溯源 Evidence Intake 与正式 Eval Baseline 裁决

日期：2026-10-22
性质：**同一已审源码 Formal Pair 未变化；本轮只接收新 DS 依赖 Evidence 并裁决依赖版本，不重做 V3 训练/Queue 源码技术审核**。
当前远端在本轮启动时 V3 记录 HEAD = `647fa746b07d0a9714a5d99762fd8b5b1e817c3d`（仅 docs，可能被后续提交推进）。前一 RoboCasa Batch A 实现候选 Root `7646d41488a55d5a44ab193520a42c48cf5acc90` / Child `e42a2468672d3ef8fcba708fc19e70daec7c790e` 与 Batch B Vendor 交付不是同一个 Formal Implementation Pair；当前 Vendor 尚未提交新生产代码与vendor patched SHA。

## 1. 本次 Batch B 决策

**正式 RoboCasa365 target-atomic 评测环境以已观测且公开Git可解析的 RoboCasa `1.0.1` / 完整 commit `6f90063c0ec2b9916bbd977368b54c98d9c2d908` 为源基线，不回退到只有版本号、没有可核实完整 commit 的数据生成 `0.5.1`。**

- 官方 RoboCasa 网站更新日志于2026-05-12标注v1.0.1评测horizon统一提高1.5倍，官方Benchmark Overview明确“update to latest version for running evals”，target split使用10个target kitchens和独立target对象；此为选定1.0.1作为**正式Eval**版本的正向依据，不能用生成时记录的0.5.1版本自动替代。
- 已独立从GitHub直接读取 `robocasa/robocasa@6f90063c.../robocasa/__init__.py:1006-1032`：明确assert `mujoco.__version__=="3.3.1"`，`numpy.__version__=="2.2.5"`，要求`robosuite>=1.5.2`，自身`__version__="1.0.1"`。此commit在GitHub可解析，**不依赖不存在的v1.0.1 tag**。
- `robocasa@6f90063c.../robocasa/environments/kitchen/kitchen.py:491,522,639-640` 确实要求`JOINT_VELOCITY_LEGACY`、`load_model_on_init=False`、`enable_multiccd=True`与`enable_sleeping_islands=False`；仅保证参数不报错不等于实现物理语义。
- `robosuite` 兼容修复**起点固定 v1.5.2 Git commit `824ac14cefcfb7ec125fe5eb2e0bad7364466154`**，此为源基线**不是可直接运行的最终正式依赖HEAD**。Codex应选择在隔离fork中新提交经测试的正确4类行为修复，并交精确新vendor commit SHA；或用等价带固定SHA/哈希的可复现patchset，绝不直接使用DS uncommitted dirty editable树作为正式baseline。不可默认从master漂移安装。
- 对比数据：**生成元数据中RoboCasa=0.5.1，仅是数据生成来源字段，不是正式Evaluator应回退的要求**。训练数据包含旧发布时的动作/状态/摄像机几何等事实，评测必须独立验证与模型的raw15/state15/left_wrist/localTTT条件、底盘坐标/LEGACY控制行为、held-out target split、Reset/layout/物理 flag一致。用1.0.1作为Eval不表示已经证实它与0.5.1生成环境逐字节或动力学等价；比较指标应将二者明确分栏记录。

**Version selection decision：`APPROVE`（仅设计层对正式评测依赖baseline选型）；Batch B Vendor production/equivalence Gate：`REQUEST_CHANGES`，尚未提交正确vendor修复/物理证明。** 本文不允许GPU、训练或真实仿真。G1训练冻结资产与原iter8900 DCP不可修改。

## 2. DS_PRO 只读溯源交付的证据级别

DS交付给Owner的文字报告称（现场证据位于目标机本地，尚未通过GitHub或聊天附件提供原始bytes）：
- 实际SIM Python import：robosuite pkg1.5.2 + HEAD等于Tag `824ac14...`，4个tracked dirty patches与1个.bak；RoboCasa pkg1.0.1 + HEAD `6f90063c...`、tracked clean、145个untracked fixture；MuJoCo wheel/native均3.3.1 (`mj_version=331`)，NumPy2.2.5；18/18数据`extras/dataset_meta.json`均声称robocasa0.5.1/robosuite1.5.2/mujoco3.3.1。
- 原始五件文件本地目录 `/mnt/data1/data_v2_0617/dspro_batchB_vendor_readonly_20261022/evidence/`：
  `runtime_imports_versions.txt` SHA256 `4817595cdfe904377b1ac2471dbedc1aff57ae080e72e8fbda6e4a8a18f4ea49`；
  `git_roots_sha_status.txt` SHA256 `a45d6f508006b6097887179b243d7b28aa56a6768c5cbf0bfba1e5e1c0bea755`；
  `robosuite_4patches.diff` SHA256 `dbe9a0d9ccdcc1052b9bddbcfe5235205461292b762cc2fac2f92a706365e74c`，2096bytes；
  `dataset_generation_provenance.txt` SHA256 `f2acf048de2ad37bcf2f47beff86cbc2436b13ea326b6521fc0d2fb1b746f77e`；
  `gate.json` SHA256 `baf180e79891557e788ef372d362b1123dcc9d4be317738bb8bcb51ec3bc1041`。
- GPT**没有**访问到这5件DS本地原始bytes，没有核验它们宣称的sha256或2096bytes完整diff；这些现场结论是**DS-attested evidence**（Owner此前表明信任DS现场CPU取证），**不可**冒充GPT远程原始文件审计。上游v1.5.2 Tag SHA、RoboCasa实际6f90063 Git Commit与初始化关键版本检查由GPT另在公开GitHub独立核实。
- DS报告本地origin/V3 `8610ad88...`、无法fetch不表示远端不存在新docs HEAD；请Codex用可访问远端分支并固定精确Candidate Source Pair，不要求DS用PAT重试push，不安装、不更改依赖环境。

## 3. 新增版本溯源不确定性：MEDIUM-DEP-03

- **Evidence artifact**：`/mnt/data1/data_v2_0617/robocasa365_official/v1.0/target/atomic/**/extras/dataset_meta.json` 18份；DS所述采集日期2025-08-11～2025-08-22；实际仿真robosuite Tag `v1.5.2`、上游官方Release日期**2025-12-24**（GitHub Releases: `ARISE-Initiative/robosuite/releases/tag/v1.5.2`）。
- **Root cause / uncertainty**：所谓“生成环境robosuite1.5.2”元数据版本号出现于目录日期早于官方Tag公开发布时间约4个月。它可能由数据转换/打包时追加，或生产现场采用未正式发布的版本字符串；在缺乏实际生成时Git SHA与原始轨迹环境清单的情况下，**不能认定原始2025-08示教是用2025-12官方tag SHA 824ac14采集**。这一疑点不自动证明数据错误、不能臆测其真正来源。
- **违反的追溯要求**：正式报告必须区别“metadata记载version字符串”与“真实capture-time Git commit证明”；对任何无法证实的原始commit必须记`UNKNOWN`。
- **验收条件**：Codex在env manifest分离 `dataset.metadata_recorded_versions`、`dataset.capture_time_commit=UNKNOWN`、`evaluation_runtime_commit`，如后续取得官方数据生成manifest可独立更新来源链，但不必阻塞可核实的**评测源码**pin开发，不可在论文/内部报告宣称三源与官方Tag逐字节相等。

## 4. 保留当前未关闭的物理兼容Blocker HIGH-10（同FormalPair未变，不重审旧代码）

- **file:line**：DS旧editable `robosuite/controllers/parts/controller_factory.py:173` 将`JOINT_VELOCITY_LEGACY`别名到普通MobileBaseJointVelocityController；robosuite `environments/base.py:740`；`environments/manipulation/manipulation_env.py:147`；`models/tasks/task.py:63-64`。其在DS自述Tag8 824ac14基线上为未提交修改，正式依赖仍无clean fixed commit。旧 HIGH-10 继续OPEN，不能当已经由文字报告解决。
- **Root cause**：上游近期源码专设 `LegacyMobileBaseJointVelocityController` 动态检查forward axis并调整坐标映射，**与**“无条件别名普通Controller”不必等价；DS第3/4处只是接受兼容参数而未将初始化延迟/CCD和sleeping配置下传。
- **验收修复**：Codex在新可重复vendor fork commit或可验证patchset上实现正确LEGACY forward/lateral/yaw语义、完整`ManipulationEnv→RobotEnv→MujocoEnv` lazy-init路径及`enable_multiccd/enable_sleeping_islands→MujocoWorldBase`语义，`_destroy_sim`失效路径幂等；记录具体环境本体PandaOmron、动作spaces、真实model flags、seed、camera、target splits、版本hash。最少CPU/unit+受Owner单独批准真实env create/reset/step和动作映射反例，不能只测“能创建环境”。如引入新robosuite commit或改变物理行为，必须新FormalPair/B Gate并独立对比，不能把旧SR5%升级成正式Benchmark。
- **DS原始完整2096byte diff仍仅在本地**：Codex可以先基于该已描述的4处问题与上游规范设计补丁，但最终要将原始diff归档或source hash核对，**不能声称已核对2096bytes完整hunk**。
- RoboCasa按官方Benchmark v1.0.1进行评测时应保留官方target split（10组target厨房+物品）、官方task horizon（升1.5x），这些protocol和source版本进 immutable evaluation manifest；不能为追求模型SR而改成原0.5.1的旧horizon。

## 5. 后续执行边界

**Codex Batch B可基于明确的runtime baseline `RoboCasa@6f90063...` + `robosuite@824ac14...` patchbase、MuJoCo3.3.1、NumPy2.2.5推进隔离vendor repair与CPU行为测试，交出patched vendor exact SHA/patch hash和相关配置/脚本改动的Root/Child SHA；候选以后接受新Pair独立Gate。**
**DS仅有目标机只读取证，不能自行修改脏仓并声称正式依赖装好。Owner以后手动执行的Batch C统一入口必须锁定真实eval_runtime_git_SHA以及当前`dirty`状态与真实Import路径，不要把不存在的RoboCasa0.5.1 SHA当成pin。**
**本Gate为Design/evidence层版本裁决，不授权GPU、训练、仿真、部署，也不关闭Batch A/G1实现独立Gate。**
