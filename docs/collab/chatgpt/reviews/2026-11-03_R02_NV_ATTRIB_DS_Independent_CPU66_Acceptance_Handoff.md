# GPT → DS_PRO：R02 NV_ATTRIB 格式修复后的独立 CPU66 Gate

**状态：GPT format-only Code Gate `APPROVE_CODE`；只授权 DS 独立 CPU/Ruff/身份验收。GPU Canary、正式 V3 合并与训练均不在此交接范围。**

## A. 唯一测试身份

- Formal Root：`46c08127b2a13155bb22204069a1456cb01424d7`
- Formal Child/Gitlink：`1069fe78841228cadbbfbe6afbd767eaed6225da`
- Root/Child 两仓候选分支：`v3-eval-v2-r02-format-20261103`。
- Author Evidence、Review 和 Canonical Inbox 在**后续 docs HEAD** 上；绝不能拿 docs HEAD 替代 Formals。
- 上一旧 Pair `286573d2/37558dcc` 已有 DS 功能66 PASS但 Ruff format FAIL；其结果不能复用为新 Pair 的正式验收。本次新 Pair 仅 format-only，完整 AST 与之前逐字一致，作者 CPU66/Ruff PASS。
- 新 review：`docs/collab/chatgpt/reviews/2026-11-03_R02_NV_ATTRIB_46c08127_1069fe78_Format_Only_Incremental_Code_Gate_APPROVE_CODE.md`。

## B. DS 独立验收（隔离干净 checkout，不碰其它任务）

DS 选一个全新独立 checkout 和外部证据目录，**禁止在训练/旧 R02/H2/H3/out2/NoTTT/正在运行的共享 checkout 上 checkout/pull/reset/clean**。可在已有单独、无污染且确实干净的 dedicated review checkout 中 `git fetch`；或新建独立 clone。下面环境变量路径由 DS 用本机实有路径填写，不能照搬 `/ABS`：

```bash
set -euo pipefail
export ROOT=/ABS/NEW_ISOLATED_NV_FORMAT_ROOT
export EVID=/ABS/NEW_DS_NV_FORMAT_CPU66_EVIDENCE
export PY313=/ABS/EXISTING_ROBOCASA_SIM_PYTHON313/bin/python
export BR=v3-eval-v2-r02-format-20261103
test ! -e "$ROOT"
git clone --no-checkout --single-branch --branch "$BR" https://github.com/wxwy/psm_wma.git "$ROOT"
git -C "$ROOT" checkout --detach 46c08127b2a13155bb22204069a1456cb01424d7
git -C "$ROOT" submodule update --init --checkout cosmos-framework
test "$(git -C "$ROOT" rev-parse HEAD)" = "46c08127b2a13155bb22204069a1456cb01424d7"
test "$(git -C "$ROOT" rev-parse HEAD:cosmos-framework)" = "1069fe78841228cadbbfbe6afbd767eaed6225da"
test "$(git -C "$ROOT/cosmos-framework" rev-parse HEAD)" = "1069fe78841228cadbbfbe6afbd767eaed6225da"
test -z "$(git -C "$ROOT" status --porcelain)"
test -z "$(git -C "$ROOT/cosmos-framework" status --porcelain)"
test ! -e "$EVID"
mkdir -p "$EVID"
cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/scripts:$ROOT/cosmos-framework"
export CUDA_VISIBLE_DEVICES=""
export COSMOS_DEVICE=cpu
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTEST_ADDOPTS=""
export MUJOCO_GL=osmesa
export PYOPENGL_PLATFORM=osmesa
"$PY313" -m pytest --noconftest -c /dev/null -q -p no:cacheprovider \
  tools/v3/eval_v2_batch_tests/render_devices_test.py \
  tools/v3/eval_v2_batch_tests/render_mapping_test.py \
  --basetemp "$EVID/pytest_tmp" --junitxml "$EVID/junit.xml" \
  > "$EVID/pytest.log" 2>&1
ruff --version | tee "$EVID/ruff_version.log"
ruff check cosmos-framework/cosmos_framework/simulation/robocasa/render_devices.py \
  tools/v3/eval_v2_batch_tests/render_devices_test.py \
  > "$EVID/ruff_check.log" 2>&1
ruff format --check cosmos-framework/cosmos_framework/simulation/robocasa/render_devices.py \
  tools/v3/eval_v2_batch_tests/render_devices_test.py \
  > "$EVID/format_check.log" 2>&1
"$PY313" - <<'PY'
import ast
from pathlib import Path
for name in (
    "cosmos-framework/cosmos_framework/simulation/robocasa/render_devices.py",
    "tools/v3/eval_v2_batch_tests/render_devices_test.py",
):
    ast.parse(Path(name).read_bytes(), filename=name)
print("SYNTAX PASS")
PY
git -C "$ROOT" status --porcelain
git -C "$ROOT/cosmos-framework" status --porcelain
```

要求保存全部命令、环境/Python/Ruff版本、Root/Child/Gitlink source identity、源码 SHA256、测试前后 clean 和原始 JUnit/日志；**Ruff 必须0.12.7**。不同可兼容 Python3.13 patch version 可备注，但不得隐瞒依赖差异。独立 CPU **66/66 PASS、0 failed/error/skipped**，Ruff check + format --check PASS，AST PASS，两仓无 dirty，方能报 `DS_INDEPENDENT_PASS`。不满足则 `FAIL` 或 `BLOCKED_ENV`，给第一条 traceback、停止；不自行更改生产/测试代码。禁止用作者66通过作为DS通过。

## C. 下一 Gate 未授权

DS 完成 CPU 后 **STOP 回 GPT/Owner**。新的 R02 CloseFridge×1EP GPU6 Action Server / GPU4 EGL、M1/B1、iter_000020000、save_generated_video=all、全新输出命名空间 `R02_1ep_nv_attrib_v2` 等真实测试**需要 Owner 另行授权并释放 GPU4/6 上 Owner 的 gpu_load_sim 占用**；原 R02 失败目录与原 R01历史仍需保留。进入 ENV_READY/Reset，实际 EGL PCI 唯一匹配、MP4/receipt/ACK/summary、exit0 是 GPU Gate 的内容，不是这次 CPU 结果。

没有授权 900EP、B2、正式 V3合并、GPU0–3、训练/NoTTT/out2/旧H2/H3/模型或历史产物变更。
