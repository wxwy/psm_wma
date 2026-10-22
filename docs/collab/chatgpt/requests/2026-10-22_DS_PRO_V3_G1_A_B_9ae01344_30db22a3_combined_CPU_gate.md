# DS_PRO — V3 G1 Resume + RoboCasa Batch A/B 主线合并后新 Pair 独立集成 CPU Gate

日期：2026-10-22
角色：DS_PRO只做**CPU/static + 证据**；Owner独占决定G1训练/GPU分配和仿真。**不得改生产代码、不得改变当前运行中G1工作树、不中断训练、不执行新torchrun/GPU、Server或真实Kitchen模拟器。**

## 精确验收对象（不允许用 docs HEAD 代替）

- Root Formal Implementation **`9ae01344ffe82a3b403732aa61cce3dd7fb5055a`**。
- Child/Gitlink **`30db22a3586c0270611753dc2ca0deb10ec27833`**。
- 可离线重建 robosuite Vendor Commit **`1ac174585293ed998ffc9cf73e47439798cf6f6c`**、Tree **`195e30cfd5d37289d227a89234bd8bb069792905`**。其上游 base 是`824ac14cefcfb7ec125fe5eb2e0bad7364466154`；RoboCasa Eval代码`6f90063c0ec2b9916bbd977368b54c98d9c2d908`、MuJoCo3.3.1、NumPy2.2.5。
- Detailed Design+Merge review：`docs/collab/chatgpt/reviews/2026-10-22_V3_G1_BatchA_BatchB_9ae01344_30db22a3_combined_incremental_gate.md`。
- **新组合Pair需要新Evidence**，不能直接以各候选过去的G1 115+32、A 92+61、B 110代替。先前Candidate的有限CPU结果可用作期望回归参照，不重复修改测试逻辑。

## Step 0 — 只读 Source SHA / clean / frozen boundaries

必须从现有**独立clean checkout**获取目标SHA：若服务器无法GitHub fetch或缺 Git Commit对象，报告 BLOCKED；禁止在正在运行的G1工作树上`git reset --hard/pull/checkout/submodule update`。
设置`ROOT_WORKTREE`为此独立Root目录，`CPU_PYTHON`为已有完整CPU依赖解释器，`NEW_EXTERNAL_EVIDENCE`为新证据目录，全部按实际路径指定。

```bash
set -euo pipefail
cd "$ROOT_WORKTREE"
test "$(git rev-parse HEAD)" = 9ae01344ffe82a3b403732aa61cce3dd7fb5055a
test "$(git ls-tree HEAD cosmos-framework | awk '{print $3}')" = 30db22a3586c0270611753dc2ca0deb10ec27833
test "$(git -C cosmos-framework rev-parse HEAD)" = 30db22a3586c0270611753dc2ca0deb10ec27833
test -z "$(git status --porcelain)"
test -z "$(git -C cosmos-framework status --porcelain)"
# 独立证据目录应由DS自己创建在源码/训练namespace之外
mkdir -p "$NEW_EXTERNAL_EVIDENCE"
export CUDA_VISIBLE_DEVICES=''
export PYTHONPYCACHEPREFIX="$NEW_EXTERNAL_EVIDENCE/pycache"
export PYTHONPATH="$ROOT_WORKTREE/cosmos-framework:$ROOT_WORKTREE/scripts"
export HF_HOME="$NEW_EXTERNAL_EVIDENCE/hf" MPLCONFIGDIR="$NEW_EXTERNAL_EVIDENCE/matplotlib"
export NUMBA_CACHE_DIR="$NEW_EXTERNAL_EVIDENCE/numba"
export TRANSFORMERS_OFFLINE=1
```

Source contract: 新Child应保留G1 Child`examples/psm_wma_robocasa_corrected_phase5.py`与`examples/psm_wma_robocasa_g1_cross_pair_resume_test.py`的审过Blob，且Batch A `closed_loop_eval.py` +新生命周期测试与此前审过Blob相等；新Root应保留G1训练launcher，并有Queue/process/vendor/helper/patchset。若源码SHA与本Scope不符，停止，报告详细Diff，不用新HEAD取代本合同。

## Step 1 — G1 CPU 旧语义 + teardown 原生 fixture

使用CPU-only，无真实G1 assets重检/触碰。

```bash
cd "$ROOT_WORKTREE/cosmos-framework"
# 专门验证历史 teardown 问题；必须让 pytest 进程的 HF_HUB_OFFLINE 初始未设置
env -u HF_HUB_OFFLINE CUDA_VISIBLE_DEVICES='' \
  "$CPU_PYTHON" -m pytest -q \
  examples/psm_wma_robocasa_g1_cross_pair_resume_test.py::test_real_preflight_wires_historical_digest_to_report_and_snapshot_producer \
  --junitxml="$NEW_EXTERNAL_EVIDENCE/g1-teardown.xml" > "$NEW_EXTERNAL_EVIDENCE/g1-teardown.log" 2>&1
# 继续完整定向G1回归；若原仓 conftest引起不可控环境变化，保留原始报错，不禁测掩盖
"$CPU_PYTHON" -m pytest --noconftest -c /dev/null -p no:cacheprovider -q -s \
  examples/psm_wma_robocasa_g1_cross_pair_resume_test.py \
  examples/psm_wma_robocasa_phase5_f0_test.py \
  examples/psm_wma_robocasa_effective_config_test.py \
  --junitxml="$NEW_EXTERNAL_EVIDENCE/g1-cpu.xml" > "$NEW_EXTERNAL_EVIDENCE/g1-cpu.log" 2>&1
```

验收：test-only teardown无误报、两个命令RC0、真实记录的全部Case和subtests通过；原冻结 `iter8900`资产仍旧，未运行任何训练。

## Step 2 — Batch A integration CPU

```bash
cd "$ROOT_WORKTREE"
"$CPU_PYTHON" -m pytest --noconftest -c /dev/null -p no:cacheprovider -q -s \
  tools/v3/eval_robocasa_queue_identity_test.py \
  tools/v3/robocasa_processes_test.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval_lifecycle_test.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval_contract_test.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval_phase6_test.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/local_memory_client_test.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/eval_utils_test.py \
  --junitxml="$NEW_EXTERNAL_EVIDENCE/batchA-cpu.xml" > "$NEW_EXTERNAL_EVIDENCE/batchA-cpu.log" 2>&1
"$CPU_PYTHON" -m pytest --noconftest -c /dev/null -p no:cacheprovider -q \
  tools/v3/remaining_optimizations_test.py \
  -k 'screening or identity or episode or runtime_error or partial_video' \
  --junitxml="$NEW_EXTERNAL_EVIDENCE/batchA-regression.xml" > "$NEW_EXTERNAL_EVIDENCE/batchA-regression.log" 2>&1
```

验收：Queue真正产生4 Task×5 synthetics，1/2/8 workers，session poison next task隔离；硬超时、SIGTERM/SIGKILL只回收属于本进程组PID，异常INCOMPLETE、SR null。测试使用短生命周期fake stdlib HTTP processes，不是真实GPU/server/Kitchen。

## Step 3 — Batch B Vendor 可复现重建和CPU真实native小模型

Builder需独立 clean 离线Vendor输出与已有本地基准Git对象；不能pip安装或触碰DS现存dirty editable或活动G1 venv。

```bash
cd "$ROOT_WORKTREE"
"$CPU_PYTHON" tools/v3/build_robocasa_vendor.py \
  --robosuite-cache "$ROBOSUITE_LOCAL_CACHE" --robocasa-cache "$ROBOCASA_LOCAL_CACHE" \
  --output "$NEW_VENDOR_OUTPUT" > "$NEW_EXTERNAL_EVIDENCE/vendor-build.log" 2>&1
test "$(git -C "$NEW_VENDOR_OUTPUT/robosuite" rev-parse HEAD)" = 1ac174585293ed998ffc9cf73e47439798cf6f6c
test "$(git -C "$NEW_VENDOR_OUTPUT/robosuite" rev-parse HEAD^{tree})" = 195e30cfd5d37289d227a89234bd8bb069792905
test "$(git -C "$NEW_VENDOR_OUTPUT/robocasa" rev-parse HEAD)" = 6f90063c0ec2b9916bbd977368b54c98d9c2d908
export PSM_VENDOR_BUILD="$NEW_VENDOR_OUTPUT"
"$CPU_PYTHON" -m pytest --noconftest -c /dev/null -p no:cacheprovider -q \
  tools/v3/robocasa_vendor_test.py \
  --junitxml="$NEW_EXTERNAL_EVIDENCE/vendor-cpu.xml" > "$NEW_EXTERNAL_EVIDENCE/vendor-cpu.log" 2>&1
"$CPU_PYTHON" -m ruff check --config cosmos-framework/.ruff.toml \
  scripts/eval_robocasa_18task_queue.py scripts/robocasa_processes.py scripts/robocasa_vendor.py \
  tools/v3/eval_robocasa_queue_identity_test.py tools/v3/robocasa_processes_test.py \
  tools/v3/build_robocasa_vendor.py tools/v3/robocasa_vendor_test.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval_lifecycle_test.py
"$CPU_PYTHON" -m ruff format --check --config cosmos-framework/.ruff.toml \
  scripts/eval_robocasa_18task_queue.py scripts/robocasa_processes.py scripts/robocasa_vendor.py \
  tools/v3/eval_robocasa_queue_identity_test.py tools/v3/robocasa_processes_test.py \
  tools/v3/build_robocasa_vendor.py tools/v3/robocasa_vendor_test.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval_lifecycle_test.py
bash -n scripts/train_v3_packed128_staged.sh
```

注意：仅实测MuJoCo3.3.1 tiny native XML flag，真实Kitchen与full SIM import不由本Gate证明。DS若没有CPU完整依赖或离线cache，明确`BLOCKED`、不要安装进活动环境、不要skip。

## Step 4 — 结果验收与后续权限

- 记录真实`root/child/vendor` SHAs、git status、所有命令/RC/JUnit、代码/补丁hash、日志与物理小模型Witness；反馈GPT最新组合Pair增量Gate。单个失败STOP，不以旧候选成功取代新组合失败。
- 成功后 GPT只对`9ae01344.../30db22a3...` Gate完成增量closure，无需重新审已有源码历史；任何新的Bug另开最窄Scope整改。
- `Batch C` 统一 YAML/CLI 手动启动/任务/GPU/MP4/预测视频仍未实现；后续出新 SHA 要再做Fresh Review。
- **真实RoboCasa Kitchen/PandaOmron create/reset/step、Legacy base axes、Camera/State和target kitchens/CCD/physics、实际source import/equivalence**是更后Gate，需要Owner明确授权后才进行，不能因为本文CPU pass自动启动仿真。
- 当前运行的G1 Resume**由Owner独立维护**。不得查看GPU库存、暂停或重置活跃工作树，不得用本次主线merged Pair替换训练时工作代码；现有G1 frozen namespace、checkpoint和Config都不许触碰。
