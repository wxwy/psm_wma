# R02 EGL 模式简化 — DS_PRO 独立 CPU + 真实仿真验收任务

日期：2026-11-03。Owner 需求：不要再先做 EGL4↔GPU4 单独探针；提交通用代码后让 DS 直接验收。**只针对候选隔离分支，不合入官方 V3，不动模型/训练/媒体协议。**

## 1. 冻结新 Formal Candidate

- Root `fce487b1aba9e851f00937d4bd54a7f99d872980`；Child/Gitlink `dff087368e3a5015a7df69052713b7c6938a853a`。
- 两仓隔离分支：`v3-eval-v2-egl-index-fallback-20261103`。
- 官方 V3 原 Root `324d6983a068424a0c0c60ad6a94e512e39ed96c` / Child `c93f2abf4fb27d36176ff8db094379a853cec796` 不受影响。
- 源码范围仅：Child `cosmos_framework/simulation/robocasa/render_devices.py`；Root `tools/v3/eval_v2_batch_tests/render_devices_test.py` 和 Child Gitlink。
- **这是一版 GPT 编写的候选代码，未在目标机执行 pytest/GPU，尚无独立 DS PASS 或新的 APPROVE_CODE，切勿误记为已验收。**

## 2. 设计边界：常规 EGL 选择，不再用 DRM 字符串作硬门槛

- 能从 EGL DRM 取得与指定物理 PCI 一致的唯一设备时，仍保持原来的严格物理选择模式 `egl_physical_pci_v1`。
- NVIDIA EGL 无法提供 DRM query API / 字符串时：按**配置的 render_gpu_id 作为 EGL ordinal**选择，使用 `MUJOCO_EGL_DEVICE_ID`，无须另行探针或写死 PCI 地址。仅要求此 ordinal 确实在 EGL 枚举内；如该位置已知是其他物理 PCI，拒绝冲突。无可用设备/重复明确身份依然拒绝。
- fallback 协议标志 `egl_index_unverified_v1`，`physical_identity_verified=false`、`actual_device=null`；绝不伪称已证明 `nvidia-smi` GPU4 对应 EGL4。
- 初始化后仍检查当前 EGL Context 是否存在；若驱动能报告实际 EGL Device handle，再检查 handle 与所选枚举设备一致；驱动不提供 handle 时只记录 `context_verified=true`（有 Context）及 `context_device_handle_verified=false`，**不把 Context 创建成功当成 GPU4 物理定位验证**。
- 这种简单回退与常见 MuJoCo 设置等价；**不保证跨机器的 EGL ordinal == nvidia-smi GPU index**。用户明确偏好简化并接受这一标注，而不是再建设复杂 GPU 身份框架。
- 不能影响 OSMesa、SR、Action/Local、model、Media、训练等路径；不访问其他 GPU 任务，不杀掉 `gpu_load_sim`。

## 3. DS_PRO — 首先独立 CPU 回归（无需 GPU/单独 EGL 探针）

在**全新隔离干净的** Root+Child checkout，使用精确 Formal Pair，绝对不能切换/污染训练或旧 R02 checkout：

```bash
set -euo pipefail
export ROOT=/ABS/NEW_ISOLATED_EGL_CANDIDATE_ROOT
export EVID=/ABS/NEW_DS_EGL_CPU_EVIDENCE
export PY313=/ABS/KNOWN_PYTHON_313_WITH_PYTEST_AND_PROJECT_DEPENDENCIES
git -C "$ROOT" rev-parse HEAD
git -C "$ROOT" rev-parse HEAD:cosmos-framework
git -C "$ROOT/cosmos-framework" rev-parse HEAD
test "$(git -C "$ROOT" rev-parse HEAD)" = "fce487b1aba9e851f00937d4bd54a7f99d872980"
test "$(git -C "$ROOT" rev-parse HEAD:cosmos-framework)" = "dff087368e3a5015a7df69052713b7c6938a853a"
test "$(git -C "$ROOT/cosmos-framework" rev-parse HEAD)" = "dff087368e3a5015a7df69052713b7c6938a853a"
test -z "$(git -C "$ROOT" status --porcelain)"
test -z "$(git -C "$ROOT/cosmos-framework" status --porcelain)"
test ! -e "$EVID" && mkdir -p "$EVID"
cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/scripts:$ROOT/cosmos-framework"
export CUDA_VISIBLE_DEVICES=""
export COSMOS_DEVICE=cpu
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTHONDONTWRITEBYTECODE=1
export MUJOCO_GL=osmesa
export PYOPENGL_PLATFORM=osmesa
"$PY313" -m pytest --noconftest -c /dev/null -q -p no:cacheprovider \
  tools/v3/eval_v2_batch_tests/render_devices_test.py \
  tools/v3/eval_v2_batch_tests/render_mapping_test.py \
  --basetemp "$EVID/pytest_tmp" --junitxml "$EVID/junit.xml" \
  > "$EVID/pytest.log" 2>&1
ruff check cosmos-framework/cosmos_framework/simulation/robocasa/render_devices.py \
  tools/v3/eval_v2_batch_tests/render_devices_test.py > "$EVID/ruff.log" 2>&1
ruff format --check cosmos-framework/cosmos_framework/simulation/robocasa/render_devices.py \
  tools/v3/eval_v2_batch_tests/render_devices_test.py > "$EVID/format.log" 2>&1
"$PY313" - <<'PY'
import ast
from pathlib import Path
for path in (
    "cosmos-framework/cosmos_framework/simulation/robocasa/render_devices.py",
    "tools/v3/eval_v2_batch_tests/render_devices_test.py",
):
    ast.parse(Path(path).read_bytes(), filename=path)
print("AST PASS")
PY
```

接受标准：两个 test 文件**全部用例通过、零 failed/error/skipped**；Ruff/format/AST PASS；两仓 Root/Child/Gitlink/测试前后 SHA 和 clean 无变化。保留 JUnit、stdout、命令、Python/Ruff版本和源码指纹。测试出现失败，真实追溯最早堆栈并回报，不由 DS 修改代码或绕过断言。

## 4. DS_PRO — CPU PASS 后执行一次 R02 真实 GPU 1EP（不跑额外探针）

前提：Owner 先确认已手动释放 GPU4 和 GPU6 上的 `gpu_load_sim`，并允许使用；DS **不得**自行停止/查询其它在跑训练与 GPU0–3 的进程。旧 `R02_1ep` 失败产物保留；从原已补齐 `asset_manifest` 的 YAML 复制**全新 YAML**，绑定新的输出目录（例如 `R02_1ep_v2`），保留旧 R01/R02/H3/out2 不改；已有 `sg video` + `sg render` EGL vendor wrapper 继续沿用。

```bash
# 在独立候选 Root，按服务器已验证的 cfg/server/sim Python 与 Group wrapper。
bash scripts/run_robocasa_eval_v2.sh dry-run --config "$CFG" \
  --execution-profile phase_b --local-memory-mode required \
  --gpus 6 --render-gpus 4 --render-backend egl \
  --sims-per-gpu 1 --max-infer-batch-size 1 --batch-wait-ms 20 \
  --media-spool-max-jobs 4 --media-spool-max-bytes 536870912 \
  --media-drain-timeout-s 300 --tasks CloseFridge --episodes 1 \
  --output-dir "$EVAL_OUTPUT_DIR"
# Owner 已放行且干净预检后，将上方 dry-run 改为 fresh。
```

R02 首要目标：Worker 不因 `EGL DRM PCI identity unavailable` 在 environment_initialization 阻塞，能进入 ENV_READY、Reset、执行 1 Episode，进程正常清理；`save_generated_video=all` 时应有 exit0、Core/SR qualified、Replan/MP4/Receipt/ACK一致、`media_summary.status=COMPLETE`，失败给第一条原始错误和路径。**不要把 fallback 的 `physical_identity_verified=false` 自动判成 Gate FAIL，也不要把它称为物理 GPU4 已验证。**

DS 在各阶段失败即停止，提交 `DS_CPU_EGL_PASS/FAIL/BLOCKED_ENV`、`R02_1EP_PASS/FAIL/BLOCKED_RESOURCE` 和原始日志/证据路径给 GPT/Owner。**禁止自动启动900EP、B2压测或正式V3合并**；本候选以独立DS反馈后才能再决定代码 promotion。
