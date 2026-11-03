# R02 EGL NVIDIA CUDA Attribute → PCI 运行时映射：实施及 DS 独立验收交接

**日期：2026-11-03｜状态：IMPLEMENTED / PENDING_DS_CPU + GPT_CODE_GATE；无硬件实测 PASS。**

## 1. 精确候选代码身份

- Root Formal implementation：`286573d2d592cbd7449930e6e93f188a3a9b037d`
- Child/Gitlink：`37558dcc71682304f3de1848923e6cedb9b77837`
- Root 与 Child 独立候选分支：`v3-eval-v2-egl-nvidia-attrib-20261103`
- 生产基准（未被此次候选修改）：V3 Root `324d6983a068424a0c0c60ad6a94e512e39ed96c` / Child `c93f2abf4fb27d36176ff8db094379a853cec796`
- 新版**取代旧未验收的** `v3-eval-v2-egl-index-fallback-20261103`。旧版允许 `egl_index_unverified_v1`，此新版**不使用该路径**：唯一物理身份不成立即拒绝；没有写死物理 PCI 或 GPU index 数组。
- Formal diff：仅 Child `cosmos_framework/simulation/robocasa/render_devices.py`、Root `tools/v3/eval_v2_batch_tests/render_devices_test.py`、Root Gitlink；不改 Cosmos/Local/TTT/Action/训练/SR、媒体 ACK 或输出路径。
- **开发者没有登录 DS 服务器运行 pytest、CUDA/EGL 或 R02；不能把代码提交当作通过测试、APPROVE_CODE 或 ENV_READY。** 下一步由 DS 独立 CPU Evidence 支撑 GPT 增量 Code Gate。

## 2. 真实问题与修复

DS 之前在 NVIDIA 570.211.01 host 上实测：`eglQueryDevicesEXT` 有8个设备，但 `eglQueryDeviceStringEXT` 的 DRM 字符串全 NULL；正确使用 `eglQueryDeviceAttribEXT(device, EGL_CUDA_DEVICE_NV=0x323A, &EGLAttrib)`，8/8 设备均成功获得 CUDA 设备 handle 0..7。EGL4=CUDA4=nvidia-smi GPU4 的单次独立探针仅为**这次主机事实**，不写为全机通用等式。

新代码：
1. `EGLDevices._cuda_device` 正确调用 `eglQueryDeviceAttribEXT`，DRM 字符串缺失并不影响 CUDA 属性查询；保留原先可用的 DRM→PCI 选择。
2. 仅在初始化需要该身份时，启动 **1 次短时、无模型加载的独立 Python/CUDA Driver 子进程**，以 `cuInit / cuDeviceGet / cuDeviceGetPCIBusId` 建立实际 CUDA handle→PCI 映射。这个独立查询进程会临时取消其**自身环境**的 `CUDA_VISIBLE_DEVICES`，原 Simulator Worker 的 `CUDA_VISIBLE_DEVICES=""` 不变；只查 PCI，不创建 CUDA context/模型，不触碰其它任务。
3. 将 NVIDIA EGL 枚举条目绑定到上面的 CUDA PCI，和 Root 既有 `resources.gpu_identity(render_gpu)` 的 nvidia-smi PCI 比较。只有唯一匹配才设置真实 `MUJOCO_EGL_DEVICE_ID`；missing/duplicate/DRM-CUDA冲突 fail-closed。
4. 校验回执仍为 `egl_physical_pci_v1` / `physical_identity_verified=true`，并记录所选 EGL handle、CUDA handle；**不以 EGL index == nvidia-smi index 作为证明**，也不使用 Host 固定映射。
5. 后续 Reset 的 `verify_current` 只查是否存在真实 EGL Context 与所选 EGL handle；有 CUDA/PCI 属性则进一步比较。不再每次 Reset 全量枚举或重新启动 CUDA→PCI 查询；驱动若无法返回显示器设备 handle，则明确 `context_device_handle_verified=false`（不能伪称重新核对过 GPU），但不得隐瞒 Context 实际存在性。

EGL API 依据：Khronos EGL_NV_device_cuda 定义 `EGL_CUDA_DEVICE_NV` 为 `eglQueryDeviceAttribEXT` 属性（不是字符串）；CUDA handle 可与 CUDA API 结合使用。基础约束：本代码不创建任何服务器特定配置或静态 PCI 映射。

## 3. DS 独立 CPU 回归 —— **先执行，不使用 GPU**

请只在一个新的、干净 detached Root/Child checkout 上执行；绝不切换正在运行的训练工作树、此前 R01/R02 工程、H2/H3、NoTTT/out2。下面路径由 DS 按本机实际权限选择，禁止照搬 `/ABS` 占位符启动：

```bash
set -euo pipefail
export ROOT=/ABS/NEW_ISOLATED_R02_NV_EGL_CODE
export EVID=/ABS/NEW_ISOLATED_R02_NV_CPU_EVIDENCE
export PY313=/ABS/EXISTING_SIM_VENV/bin/python
export BR=v3-eval-v2-egl-nvidia-attrib-20261103
test ! -e "$ROOT" || { echo "ROOT_EXISTS_STOP"; exit 2; }
git clone --single-branch --branch "$BR" --no-checkout https://github.com/wxwy/psm_wma.git "$ROOT"
git -C "$ROOT" checkout --detach 286573d2d592cbd7449930e6e93f188a3a9b037d
git -C "$ROOT" submodule update --init --checkout cosmos-framework
test "$(git -C "$ROOT" rev-parse HEAD)" = "286573d2d592cbd7449930e6e93f188a3a9b037d"
test "$(git -C "$ROOT" rev-parse HEAD:cosmos-framework)" = "37558dcc71682304f3de1848923e6cedb9b77837"
test "$(git -C "$ROOT/cosmos-framework" rev-parse HEAD)" = "37558dcc71682304f3de1848923e6cedb9b77837"
test -z "$(git -C "$ROOT" status --porcelain)"
test -z "$(git -C "$ROOT/cosmos-framework" status --porcelain)"
test ! -e "$EVID" || { echo "EVID_EXISTS_STOP"; exit 2; }
mkdir -p "$EVID"
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
for name in (
    "cosmos-framework/cosmos_framework/simulation/robocasa/render_devices.py",
    "tools/v3/eval_v2_batch_tests/render_devices_test.py",
):
    ast.parse(Path(name).read_bytes(), filename=name)
print("AST PASS")
PY
```

验收：**全部收集到的定向 tests 0 failed/error/skipped**，Ruff/format/AST PASS；两仓 before/after clean，Root/Gitlink/Child 和源文件 SHA不变。收集原始 JUnit、pytest.log、Ruff/format日志、Python/Ruff版本、差异与调用参数。出现 FAIL/BLOCKED_ENV 必须保留第一条原始 traceback、退出码和根因候选，**DS 不得自行修改生产或测试源码来使它通过**。

## 4. R02 GPU 1 Episode —— **待 GPT Code Gate 和 Owner 释放资源后**

这不是 CPU 阶段自动授权。仅当 CPU PASS、GPT 独立增量 Code Gate APPROVE、Owner 确认 GPU4 和 GPU6 上其本人启动的 `gpu_load_sim` 已释放并授权此次 Fresh Run 后，DS 才执行：

- 与此前 R01/R02 相同的真实 Sim Python、Server Python、checkpoint `iter_000020000`、asset_manifest、`sg video` + `sg render` EGL wrapper；不要改共享环境/驱动或旧结果。
- 新输出目录 `R02_1ep_nv_attrib`（必须不存在，不删除或覆盖原失败 `R02_1ep` / `R02_1ep_v2`），Fresh Config 从已修正 `asset_manifest` 的 R02 YAML 拷贝至**全新配置文件**。
- 运行命令（在新 Root 的 checkout 中执行，`CFG` 和 `EVAL_OUTPUT_DIR` 使用真正的新绝对路径）：

```bash
bash scripts/run_robocasa_eval_v2.sh dry-run --config "$CFG" \
  --execution-profile phase_b --local-memory-mode required \
  --gpus 6 --render-gpus 4 --render-backend egl \
  --sims-per-gpu 1 --max-infer-batch-size 1 --batch-wait-ms 20 \
  --media-spool-max-jobs 4 --media-spool-max-bytes 536870912 \
  --media-drain-timeout-s 300 --tasks CloseFridge --episodes 1 \
  --output-dir "$EVAL_OUTPUT_DIR"
# 干净 preflight + Owner 授权后：使用相同命令将 dry-run 改为 fresh，
# 并通过已验证的 sg video/render wrapper 执行。
```

R02 Gate：`ENV_READY`、所选 EGL Device 身份与预计 GPU4 PCI唯一一致（记录 EGL/CUDA/PCl/当前Context Proof）、Episode正常执行、Core/SR qualified、Video all模式下 Replan=MP4=VIDEO_SAVED Receipt=Server ACK、`media_summary.status=COMPLETE`、程序`exit=0`、owned processes/Encoder clean；禁止把原失败 R02 /旧 R01 exit1 文件覆盖成新结果。

**DS CPU完成后 STOP 回报 GPT/Owner；未授权 GPU自动运行、正式 V3 合并、900EP、B2/共享 NoTTT/out2/Checkpoint/历史媒体操作。**
