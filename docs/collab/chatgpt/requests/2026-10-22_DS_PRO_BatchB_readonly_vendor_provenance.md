# DS_PRO — Batch B RoboCasa/robosuite/MuJoCo 真实依赖与4处补丁，只读取证

日期：2026-10-22
授权：**只读 / CPU-only / 不启动仿真与GPU / 不改代码或安装环境**。作为 Codex Batch B pinned vendor physics compatibility 的权威输入；核验完成后停止并反馈 Codex/GPT/Owner，不自行修复。不得运行 `git fetch/pull/checkout/reset/clean/apply`、`pip install`、`uv sync`、删除.bak、终止其他PID，不能破坏正在运行的 G1 训练、已有评测输出或本地脏工作树。

## 1. 三种来源不可混淆

A. **上游静态 Tag（GPT 已从 GitHub 验证）**：ARISE-Initiative/robosuite `v1.5.2` -> Git commit **`824ac14cefcfb7ec125fe5eb2e0bad7364466154`**。这不等于 DS 机实际安装的 HEAD/working tree，也不证明 RoboCasa dataset 原始生成用它。
B. **DS 机运行时生效环境（本轮必查）**：实际 `sim_python` import 出来的 robosuite/RoboCasa 源码位置、Git完整 HEAD、tag/父系关系、tracked/untracked 改动，MuJoCo Python包与底层 MuJoCo C 库版本。若 editable 指向别的源码或 wheel 不可追溯，报告 BLOCKED，绝不补造 SHA。
C. **原始示教数据生成环境（独立证据维度）**：检查数据集 `meta/info.json`、`extras/dataset_meta.json` 和已有生成 manifest/README 是否真正记录 robocasa/robosuite/mujoco commit+版本；若没有只能标 `generation_env=UNKNOWN`，不得把本机仿真环境说成原始数据生成环境。不得为核对而重新生成数据或修改官方资产。

## 2. 路径、版本与动态导入来源（仅 read-only）

已知 DS 报告中的路径：`/mnt/data1/data_v2_0617/robosuite_repo/`（脏editable，4个未提交补丁）；
Python示例：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python`（DS此前报告Server/Simulator同venv；以现场实际使用值为准）。
**先核实实测用的 `SIM_PYTHON`；不要推断 RoboCasa Git 根路径。** 以下命令可以直接执行，禁止隐式pip安装：

```bash
export SIM_PYTHON=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python
"$SIM_PYTHON" - <<'PY'
import sys, importlib, importlib.metadata as md, importlib.util
print("sim_python:", sys.executable)
for name in ("robosuite", "robocasa", "mujoco", "numpy"):
    spec = importlib.util.find_spec(name)
    print(name, "origin:", None if spec is None else spec.origin)
    print(name, "search_locations:", None if spec is None else list(spec.submodule_search_locations or []))
    try: print(name, "package_metadata_version:", md.version(name))
    except md.PackageNotFoundError: print(name, "package_metadata_version: NOT_INSTALLED")
    try:
        m = importlib.import_module(name)
        print(name, "actual_file:", getattr(m, "__file__", None))
        print(name, "module_version:", getattr(m, "__version__", None))
        if name == "mujoco":
            print("mujoco_native_mj_versionString:", m.mj_versionString())
    except Exception as e:
        print(name, "IMPORT_ERROR:", type(e).__name__, str(e))
PY
```

从上述 **actual_file** 确定 RoboCasa 和 robosuite 各自所属的 Git 工作树（可用 `git -C <module_parent> rev-parse --show-toplevel`），逐个报告：
- `git rev-parse --show-toplevel`、`git rev-parse HEAD` (完整40位)、`git rev-parse --is-shallow-repository`、`git remote -v`（仅URL，脱敏 token）、`git describe --tags --always --dirty`；
- `git status --porcelain=v1 --untracked-files=all`，明确 tracked 修改、staged 修改、untracked `.bak`；
- `git log -1 --format='%H %ci %s'`，`git ls-tree HEAD` / `git rev-parse refs/tags/v1.5.2^{commit}` (只在本地Tag存在时可解析)，`git merge-base --is-ancestor <tag_sha> HEAD` 的RC；记下实际 robosuite HEAD 是否**恰好等于**Tag基线 `824ac14...`。若没有Tag，标MISSING_TAG，不擅fetch。
- 对 RoboCasa 若仓库无标记 `1.0.1` 的tag，也记录其实际 HEAD 与 Python metadata version，不能按版本号猜SHA。
- MuJoCo 至少报告 `importlib.metadata.version("mujoco")`、`mujoco.__version__`（若有）、`mujoco.mj_versionString()` 和 import路径；`pip show mujoco` 可只读补证（不是必须）。

## 3. 四处 robosuite 补丁必须提取 *实际完整 Git Diff*

以实测 `ROBOSUITE_REPO`（预计 `/mnt/data1/data_v2_0617/robosuite_repo/`）为准，包含 staged/unstaged 相对 HEAD 所有 tracked diff，**不使用用户描述代替文件**：

```bash
RS=/mnt/data1/data_v2_0617/robosuite_repo
# 仅当 RS 已通过 git show-toplevel 与 Python import origin 核实，才运行
git -C "$RS" diff --no-ext-diff --binary HEAD -- \
  robosuite/controllers/parts/controller_factory.py \
  robosuite/environments/base.py \
  robosuite/environments/manipulation/manipulation_env.py \
  robosuite/models/tasks/task.py > /tmp/dspro_batchB_robosuite_4patches.diff
git -C "$RS" diff --no-ext-diff --numstat HEAD -- \
  robosuite/controllers/parts/controller_factory.py \
  robosuite/environments/base.py \
  robosuite/environments/manipulation/manipulation_env.py \
  robosuite/models/tasks/task.py
git -C "$RS" status --porcelain=v1 --untracked-files=all
sha256sum /tmp/dspro_batchB_robosuite_4patches.diff
```

严禁 `git diff --check` 以外的代码改写；如4文件存在untracked而非tracked修改，`git diff HEAD`不包含该文件，应另行**只读**保存原始内容/状态并说明，不能自行把它加入Git。注意 `manipulation_env.py.bak_20261021` 是历史备份，不是正式补丁来源；不要上传可能带私密环境设置的无关文件。若实际diff不是恰好这4处，完整列出差异（含第5处/影响范围），不要改动以符合报告。

Codex 必须获得四份实际patch hunk、文件 sha256与source HEAD，而非只有"替换哪一行"。重点：
- `JOINT_VELOCITY_LEGACY` 不应直接映射普通Controller作为已验证同语义实现；
- `load_model_on_init` 是否沿 `ManipulationEnv→RobotEnv→MujocoEnv` 真正传递；
- `enable_multiccd/enable_sleeping_islands` 是否真正进入 MuJoCo建模配置；
- `_destroy_sim` 是否只为未创建Sim安全退出。
这些是 Batch B 设计待验证风险，不由 DS 擅改patch。

## 4. 数据集生成来源 read-only 检索

围绕 DS 已使用的 dataset root `/mnt/data1/data_v2_0617/robocasa365_official/v1.0/target/atomic`，选择代表性任务如 `CloseFridge` 的 `extras/dataset_meta.json` 和 `meta/info.json`（若存在），只提取 **已经存在的** 版本/commit/生成脚本字段。已有数据生成README/manifest如记录来源commit一并附小段原文+文件sha，不批量扫描视频或载入大数据。
若这些文件只记录 env_args、版本概述而没有精确 git commits，要明确分栏：
`eval_runtime_deps=VERIFIED`, `generation_deps=NOT_RECORDED`。若可找到可信的生成记录，附来源与精确对应的 commit，不做推断性拼接。

## 5. Evidence 交付（只读上传/分享）

输出**新的 Evidence 目录在 DS 自身工作区外/临时目录**，例如
`/mnt/data1/data_v2_0617/dspro_batchB_vendor_readonly_20261022/evidence`，放入：
- `runtime_imports_versions.txt`（含 sim解释器/import origin、MuJoCo native版本）；
- `git_roots_sha_status.txt`（RoboCasa/robosuite 完整HEAD、Tag祖先关系、dirty及remote脱敏）；
- `robosuite_4patches.diff`（完整真实 `git diff HEAD`）及SHA；
- `dataset_generation_provenance.txt`（数据生成源码实际是否可证实）；
- `gate.json`（汇总正反可核验事实、各命令、RC与文件SHA256）。
上传到ChatGPT可访问的GitHub Evidence文件或直接把小文件发给Owner/GPT（勿粘凭据/大量大文件）。若目标机GitHub不可达，优先经Owner转附件，不需要PAT重试。
**STOP**：不运行仿真/模型/训练，不更改robosuite/robocasa仓库或新旧数据集；新证据提交后由 GPT/Codex 决定 pinned fork/patchset 和 CPU/真实控制语义测试。

## 6. 给 Codex 的信息判定

- **已知**上游 robosuite v1.5.2 tag `824ac14cefcfb7ec125fe5eb2e0bad7364466154`，但**当前实际基线**需现场比对 `git rev-parse HEAD` 与该 SHA；
- 当前 RoboCasa Git SHA、MuJoCo版本、完整patch hunks均尚非GPT可核验，必须等 DS read-only提供；
- 若数据生成版本未记录，Batch B 只能按确认的评测runtime来源+严格兼容验证推进，不得说原始示教生成环境已经完全复现。
