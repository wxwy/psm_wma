# Owner 授权交接 — DS_PRO 独立 CPU70 + GPU4–7 EvalV2 Hardware Canary

- 日期：2026-11-01（CST）
- **Owner 已在当前 ChatGPT 会话明确一次性授权**：（A）新 GPU 资源策略 **DS_PRO 独立 70 项 CPU Gate**，并且（B）A 通过后**同次授权**继续 GPU4–7 的真实 Hardware Canary，**不需要第二次 Owner 放行**。
- 执行者：**DS_PRO（训练服务器）**；GPT 仅负责审阅回执，Codex 仅在单独返修任务中修代码。此文件是 Owner 授权的**投递与执行说明**，**不是已开始执行或已通过 Canary 的证明**。
- **Frozen Formal Pair**：Root `4b581493db805c92964cb27e740c736db87c0329`，Child/Gitlink `9a8cd6183424bfce245fbca393ca25ed59919ea6`，候选 `v3-eval-v2-render-media-20261101`。GPT 资源策略独立 Code Gate 已 `APPROVE_CODE`；旧 RM-M01 CPU Gate 已以 Python 3.13（205/206）+ Python3.12 pidfd（1/1）分解释器口径关闭。
- GPT 详细 Gate：`docs/collab/chatgpt/reviews/2026-11-01_V3_EvalV2_Owner_GPU_Resource_Policy_4b581493_9a8cd618_APPROVE_CODE.md`。
- 作者 CPU70 Evidence：`docs/collab/codex/evidence/2026-11-01_eval_v2_owner_gpu_policy_author_cpu/`。

## 绝对运行边界

1. GPU4–5 = CUDA Action Servers；GPU6–7 = EGL Simulator。**GPU0–3 完全排除**，不能分配或探测。GPU4–7 上**已有训练照常运行**；Owner 明确决定可共存。禁止把其他 CUDA 进程/显存占用作为 Gate，也**不查询、不管理、不暂停、不杀掉**其他 GPU 任务。只可查询目标 GPU4–7 的**物理 index/UUID/PCI 身份**，在真实运行中记录**本次作业自己的**结果/进程/显存数据（若接口已有）；不要主动枚举其他用户进程。
2. **不得**更改当前运行的 No-TTT 训练、旧 `out2`、任何现存 DCP/Checkpoint、日志/MP4、模型、共享工作树/YAML、Root V3 或官方 Child；不得启动旧 `out2` Resume。测试必须在**独立 checkout** 使用新 Formal Pair，所有临时数据与各阶段输出放新目录、不可与任何源/已有 Run 重叠。
3. 启动解释器：Coordinator 使用已验证的 `PYTHON=/usr/bin/python3.12`（pidfd + yaml + requests）；**从 YAML 真实已验证路径**分别指定 `server_python`（CUDA Action Server）和 `sim_python`（RoboCasa Simulator），不可因为曾在 Python3.13 sim venv 跑 CPU 测试就擅自把它当作 CUDA Server 环境。不要在真实 GPU 运行中继承 CPU-only `CUDA_VISIBLE_DEVICES=""` 等禁用选项；Simulator 的 CUDA 隔离由生产链路负责。
4. **本次授权只包括 CPU70、三个渐进 Canary 和其诊断/自有进程清理**；不授权正式 18×50=900 EP、正式 V3 合并、新代码修复、任意 GPU0–3 操作或对旧 Run 补跑。阶段故障则停在该阶段，报告证据，不自动扩大并发或改算法/协议。
5. 对测试创建的子进程使用已有注册 ownership + pidfd 安全收尾；**禁止 `killall` / 宽泛 `pkill` / 信号发往未核实身份进程**。如发生 OOM、SIGABRT、EGL Context/PCI 失配、FFmpeg 存活残留或无法安全回收：**立即停止后续阶段并保留现场证据**，不触碰他人训练任务。

## A. DS_PRO 独立 CPU Gate（先完成；未过则不启动 GPU）

在独立 clean Root/Child checkout 锁定上面的 SHA；记录 `git rev-parse HEAD`、`git ls-tree HEAD cosmos-framework` 和两个 `git status --porcelain`（测试前后 clean）。使用 DS 现成 Python3.13 仿真环境执行以下**精确 70 项**（不复用 Codex 的结论）：

```bash
export ROOT=/PATH/TO/ISOLATED_ROOT_AT_4b581493
export EV=/PATH/TO/NEW_INDEPENDENT_CPU_EVIDENCE
export PY13=/PATH/TO/VERIFIED_PYTHON313/bin/python
export PYTHONPATH="$ROOT:$ROOT/scripts:$ROOT/cosmos-framework"
export CUDA_VISIBLE_DEVICES="" COSMOS_DEVICE=cpu MUJOCO_GL=osmesa PYOPENGL_PLATFORM=osmesa
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
cd "$ROOT"
"$PY13" -m pytest --noconftest -c /dev/null -q -s -p no:cacheprovider --rootdir="$ROOT" \
 tools/v3/eval_v2_batch_tests/owner_gpu_resource_policy_test.py \
 tools/v3/eval_v2_batch_tests/render_mapping_test.py \
 tools/v3/eval_v2_batch_tests/render_devices_test.py \
 tools/v3/eval_v2_production_tests/entry_test.py::test_config_and_resource_gates_no_protected_writes \
 tools/v3/eval_v2_production_tests/entry_test.py::test_shared_gpu_has_no_occupancy_admission_but_retains_missing_device_safety \
 --basetemp="$EV/pytest_tmp" --junitxml="$EV/junit.xml"
```

另做 Ruff check、format check、py_compile（针对新生产和三份测试；使用 Python3.13/Ruff 0.12.7）。保存原始 stdout/stderr、JUnit、命令、环境、Root/Child SHA、静态日志、源码 before/after 状态。**准入条件为实际收集 70、70 passed、0 failure/error/skip，静态 PASS、身份 clean**。否则 `FAIL` 或 `BLOCKED_ENV`，**停止，不启动 Canary**。旧 RM-M01 206 项无需重跑。

## B. GPU Hardware Canary（CPU A PASS 后，已经获得 Owner 同次授权）

**真实输入准备**：使用 `configs/eval/robocasa_eval_v2_split_render.example.yaml` 作模板，在隔离源和正在运行的训练工作树**以外**配置已验证的只读 checkpoint/config/dataset/vendor、真实 `server_python`、`sim_python`、非占用本 Run 的 `base_port`，以及三个各自不同、此前**不存在**且不会覆盖旧 Run 的 `output_dir`。维持：`execution_profile: phase_b`、`local_memory_mode: required`、`render_backend: egl`、`save_rollout_mp4: true`、`rollout_mp4_first_n_per_task: null`、`save_generated_video: all`、`seed: 0`、`prediction_steps: 30`、`guidance: 1.0`。其他模型/ABI 参数按已有正式评测要求不变。旧 GPU reserve 字段可以保留，**不做准入判断**。

GPU 阶段前仅核对 GPU4–7 选定 index→UUID→PCI 和实际服务器/仿真解释器、YAML 解析结果；**不检查别的进程或 GPU 显存占用**。用同一 YAML，按阶段用 CLI 参数覆盖：

| 阶段 | Action Server | EGL 渲染 | Phase B Sim/Batch | 任务与 Episode | 目的 |
|---|---|---|---|---|---|
| H1 | GPU4 ×1 | GPU6 | `--sims-per-gpu 1 --max-infer-batch-size 1`（M1/B1） | dataset 中真实有效的 1 task × 1 EP | PID/PCI/真实 EGL Context、Local-TTT、预测、真实全视频与 cleanup |
| H2 | GPU4–5 ×2 | GPU6–7 | `--sims-per-gpu 2 --max-infer-batch-size 2`（M2/B2） | 4 个真实不同 task × 1 EP | 两 Server、四 Slot、并行 Session/Media/owner cleanup |
| H3 | GPU4–5 ×2 | GPU6–7 | `--sims-per-gpu 8 --max-infer-batch-size 2`（M8/B2） | 16 个真实不同 underlying task × 1 EP；如需进一步验证稳定性，可保持同配置在另一个新 Run 复测，但不扩大到正式900 | 目标 16 Sim 并发实际观测、GPU 共存稳定性、全 MP4 负载/吞吐 |

对每一阶段，**先 dry-run，核对解析后的 `physical_slots`、`render_slots`、GPU/任务数/新 `output_dir`、模态与 media policy，再使用相同参数启动 `fresh`**。命令语法（`--tasks` 的真实类名从 dataset `extras/dataset_meta.json` 获取，不要捏造）：

```bash
# 在独立 checkout，准备真正运行时先取消 CPU-only CUDA_VISIBILITY 等禁用环境。
export PYTHON=/usr/bin/python3.12
bash scripts/run_robocasa_eval_v2.sh dry-run --config /EXTERNAL_PATH/eval_v2_canary.yaml \
  --gpus 4 --render-gpus 6 --execution-profile phase_b \
  --sims-per-gpu 1 --max-infer-batch-size 1 --tasks ACTUAL_TASK_A \
  --episodes 1 --output-dir /NEW_EXCLUSIVE_PATH/H1
# 验证打印结果与非覆盖目标，再把 dry-run 改为 fresh，其他参数保持相同。
```

H2 CLI 使用 `--gpus 4,5 --render-gpus 6,7`、`M2/B2` 和四个真实 Task；H3 使用同组 GPU、`M8/B2` 和 16 个真实 Task。每个阶段新路径独立 `fresh`，不在任何旧 `out2` 或训练目录内。不要因模型 SR=0 而误认基础设施失败；看的是 Core/Episode 有效性及真实链路成功。

**逐阶段必须收集的硬件/协议证据**：
- 真正使用的 Root/Child/Manifest digest、resolved YAML、起动命令及 `PYTHON`/`server_python`/`sim_python` 三解释器、GPU index/UUID/PCI、EGL 枚举物理映射与 **actual Context proof**。
- GPU4–5 Server 加载、GPU6–7 EGL 初始化、Actor/Session/Local-TTT Prefix/Adapt、真实 replan/B1/B2 Batch、各物理 Slot 的 `task/episode` 与排队情况；H3 **需要证明16个 Slot 确实参加，而不只是配置里写16**。
- 每 EP 有效 Core、success/failure 原样、prediction count、每次 replan 对应的 Generated MP4、Rollout MP4；逐个确认文件非空且**真实可解码**，媒体结果与 replan 记录匹配，不仅检查文件名。
- 有界 Media/FFmpeg encoder/feeder 清理、Coordinator owned actor 子进程安全回收、`media_process_fault`、`process_cleanup_failed`、Local Reset ACK；停止后无**本次 Run 自己的**残留进程。不允许信号触碰其他作业。
- 真实错误与延迟：SIGABRT / `mjr_readPixels`、EGL 错误、CUDA OOM、GPU driver/Xid（仅本作业相关证据）、FFmpeg EBADF、超时、replan latency p50/p95、推理/渲染 FPS 或等价 throughput、每阶段 wall time/EP/h、**仅本作业自身**显存峰值（有既有 telemetry 则记录，无则标 unavailable，不得以读取其他任务数据代替）。
- 与原有训练共存时，不以 GPU 上存在训练为失败条件；如果真实冲突造成 Canary fault，记录错误并**只停止自己的新 Run**，不得管理其他训练。

**各阶段准入 / 停止条件**：CPU A FAIL/BLOCKED → 不启动 H1；H1 未完成有效 Core 或关键设备/媒体/安全闭环 → 停止，不启动 H2；H2 出现未回收自身进程、无法安全证明物理映射、真实驱动故障或必选媒体不可解码 → 停止，不启动 H3；H3 完成后**停止交报告**，不自动进入正式 18×50，也不自动合并 V3。模型任务成功率不作 Infra Canary 的硬阈值。

## C. DS_PRO 交付与 GPT 回传

独立 CPU 结果：`PASS/FAIL/BLOCKED_ENV` + JUnit 原始证据；硬件每阶段单独 `PASS/FAIL/BLOCKED_ENV`、完整命令、日志/Manifest、GPU/EGL proof、Episode Core、Media files/ffprobe、Process 清理及吞吐统计、路径和样例 MP4。失败须明确 first error 与准确源 `file:line`（若可确定），区分模型不会任务、实际 EGL-CUDA 并发冲突、Media fault、配置/源码错误。

把交接回执写在隔离候选的 DS 协作证据目录，或向 Owner/GPT 提交绝对路径；不得覆盖已有证据。**不提交生产代码改动**。若发现代码缺陷则报告给 GPT 再交 Codex 狭义修复，不能自行跳过测试或改 Gate。

> **执行权限状态**：Owner 两项均已授权，DS_PRO 收到该 handoff 后可以 CPU→H1→H2→H3 串行执行；执行者须在真实服务器上完成。GPT 只是提交授权文档，不表示已对远程服务器实际启动任务。
