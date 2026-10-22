# PSM-WMA V3 — G1 iter8900 Owner cross-pair Resume 主线整合增量审核

日期：2026-10-22
事件：Owner 已自行启动 G1 Resume 后，明确请求“合并到V3分支吧”。
角色：ChatGPT执行 **GitHub远端代码合并 + 精确增量验证**；不操作训练进程、GPU/Checkpoint/Config/JobIdentity/服务器工作树。

## 1. 精确版本

- **新 Formal V3 Implementation Root：`56412b6070011ca995f9007398a9184cc4092b6b`**
- **Child/Gitlink：`7dd696efb4807e7338a5e420db2a1ede6cec67d0`**；子仓`wxwy/cosmos-framework`。
- 主线Merge Parent：`9321ec204d9deb50be22971a8de4f4d3feb067ce`，mode160000 Gitlink原值`35b0ea1ccee9ee26653ed6589c484f0997d1c586`。
- 源 Candidate：Root `38d385ba73ba991eddbfb99a74111fece744a7d3` / Child `7dd696ef...`；隔离分支`v3-g1-cross-pair-resume-20261022`，**保持原状**，未用其HEAD直接覆盖 V3。
- 父V3 tree `5f0233b2ad01170bbbe5ac1b9c573358956112cd`，新源码Merge tree `6e01675ab33dc7400eef10ec02207bf7304f6d89`。
- 新Launcher Git Blob `0514c1baab4a543c702f7033d765b810c038ab16`，旧V3原Blob `391405c2216a8572b8512de526e7c3b4bc7b87ca`。
- RoboCasa评测 Queue Git Blob **未改变**：`72ad7e2b94b31cbfd7a8af0a1eaff92127ffa7ae`。

## 2. Merge差异与来源

GitHub `compare_commits(9321ec...→56412b...)`仅返回：
1. `scripts/train_v3_packed128_staged.sh`：+11/-3，从仅两个固定参数扩展为可选第三项`--owner-authorized-g1-cross-pair-resume`；仍要求`phase=resume`及固定G1 Job Name才能传参；原两参数入口保留，Owner实际启动训练始终手动。
2. `cosmos-framework`：唯一Gitlink指向已单独审查并修复teardown的一项 Child `7dd696ef...`。

**没有其他 Root 文件改动。** Root `docs` tree SHA在Merge前后相同，未覆盖先前G1/BatchA/BatchB review/request/Inbox；Eval Queue Blob也未改变；Child版本在源候选中已被单独审查，含G1历史digest/8rank sidecar校验以及`monkeypatch.setenv("HF_HUB_OFFLINE","1")` fixture修复。新Merge没有重新编辑这些Child源码，也未重新运行GPU。

保留Child代码里的：
- `verify_root_child_lock()` 核查**运行时**真实Root HEAD=`--expected-root`、Child HEAD=`--expected-child`且Gitlink=Child，Child clean；
- `check_job_namespace()` 在显式仅G1 override时验证旧Frozen来源`e0121d34…/2d128ed5…`和非来源训练语义；
- 历史旧`config_digest`/Launch、8份Sidecar/SegmentProvenance以及 full training model/optim/scheduler/trainer state恢复检查；
- 旧Canonical Config/Job Identity/DCP不动。
- `--preflight`仍是直接Child Python单进程入口，不经Launcher；Launcher`resume 30000 ...`会真实启动8×torchrun。Owner已启动的训练不应被主线Merge干扰。

## 3. Incremental verdict 与Evidence限制

**Formal merge/source-integrity Gate：`APPROVE` — 新 V3 Root `56412b...` / Child `7dd696ef...`。** 
已独立查证远端V3 HEAD=`56412b...`、Child Branch SHA与主线Gitlink=`7dd696ef...`、两处精确Diff、Launcher Blob、Queue Blob及旧docs完整保留。合并是以V3最新Parent的树为基础，GitHub `update_ref`以`expected_sha`做非强推更新，防止覆盖外部并发提交。

**不以本次Merge冒充新的目标机CPU/GPU Evidence通过**：新Child一行teardown测试修复在Github有直接代码验证，但目标机`pytest`无遮蔽teardown复验原始日志尚未由本次GPT获得；用户已自行启动Resume，仅由Owner确认执行，GPT无目标服务器运行证据、不判断训练是否已经正确恢复。上轮DS 37项真实G1文件只读和合成115+32仅是原执行环境Evidence；同G1 Resume强校验在运行时仍可能fail closed。

**运行提示：**
- 现已启动的隔离训练按其本次真实worktree原Commit继续：禁止为了追V3 Head进行`git checkout/reset/pull/submodule update`或变更`EXPECTED_ROOT`环境变量，导致全rank不同source。
- 如**未来**另行在V3主线完整Root `56412b...`上执行，则`EXPECTED_ROOT=56412b6070011ca995f9007398a9184cc4092b6b`、`EXPECTED_CHILD=7dd696efb4807e7338a5e420db2a1ede6cec67d0`（但本Owner override只准原iter8900起点，不是9000/10000再次Resume自动许可）。
- 此次Remote Git Merge没有授权任何GPU、训练启停或存量训练文件迁移；Batch A/Batch B独立源码分支仍未合入V3，Batch C可配置Owner Launcher仍未交付。

**综上：Merge已正式完成；新Formal源码Pair为56412b/7dd696；数据/训练执行Gate和实际Model Restore结果与此次远端整合严格分离。**
