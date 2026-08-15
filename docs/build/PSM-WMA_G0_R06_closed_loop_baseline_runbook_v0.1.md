# PSM-WMA G0-R06 LIBERO Closed-Loop Baseline Runbook v0.1

- 状态：draft（执行验收通过后升 reviewed）
- 作者：Kimi（DOC-R06 认领）；代码修改归 Codex（本 Runbook 当前不需要代码改动）
- 日期：2026-08-15
- Gate 任务：G0-R06（TODO.md）；前置 G0-R05 PASS 已满足

## 1. 目标与判据

目标：建立 `Cosmos3-Edge-Policy-DROID -> LIBERO` 的 closed-loop baseline，链路真实可重复，
不是 R05 tiny-overfit，不使用 RoboLab/Isaac。

闭环定义：MuJoCo 实时渲染 observation → HTTP policy server → action → `env.step`，
逐步驱动仿真；**禁止用 R12 离线 latent 缓存替代实时观测**，只复用同一视觉/VAE 契约
（uint8 → [-1,1] 归一化、image_size=256、causal temporal VAE，见 MEMORY/DECISIONS.md D010）。

PASS 必须同时满足：

1. 环境链：libero/robosuite/mujoco import PASS；EGL 离屏渲染 smoke PASS；
2. 服务端：policy server 加载 baseline checkpoint 成功，`/info` 与 `/predict` 健康；
3. 请求级：每个 `/predict` 返回 action chunk，全部元素 finite；
4. 闭环：所有 episode 的 `env.step` 无异常跑完（达到 success 或 max_steps）；
5. 任务级：`overall_success_rate > 0`（SR > 0，至少 1 个 episode success=true）；
6. 可重复：固定 seed/init state 下重跑同一 task 的 episode，step 轨迹长度与首 chunk action
   数值一致（容差 0，deterministic 服务端 seed 固定）；
7. 机器可读 Gate JSON 落盘，status 字段与上述判据一致。

FAIL：链路全部跑通但 SR == 0（诚实记录，不得把 R05 loss/forward PASS 当闭环 PASS）。
BLOCKED：ImportError / 环境缺失 / 渲染失败 / 接口不匹配，记 BLOCKED_<原因> 并保留现场。

已知风险（诚实前置声明）：zero-shot baseline 的 domain 5（libero）action projection 行
在发布 checkpoint 中未经过 LIBERO 训练（R03 冻结结论：R04 训练时才重初始化 domain 5 行），
因此 SR>0 并不保证；若 FAIL，结论是“zero-shot 基线不成立”，不是工程链路失败。

## 2. 前置资产（全部本地，无外网）

| 资产 | 路径 | 说明 |
|---|---|---|
| baseline checkpoint | `/gemini/code/models/Cosmos3-Edge-Policy-DROID` | 原始 HF 推理包，zero-shot baseline（见 §3 选型） |
| action stats | `cosmos-framework/cosmos_framework/data/generator/action/normalizer_stats/libero_native_frame_wise_relative_rot6d.json` | 服务端 denormalize 用 |
| policy server 环境 | `/root/venvs/psm_wma_py313_cu128`（py3.13 + torch 2.10 cu128） | GPU 推理侧 |
| 仿真环境 | `/gemini/code/RLinf/.venv`（py3.11 + torch 2.6.0 + mujoco 3.8.1 + robosuite 1.4.1 + libero 0.1.0 editable + bddl 3.6.0） | 闭环客户端侧，只读引用，不修改 |
| LIBERO 资产 | `/root/.libero/config.yaml` → benchmark_root `/gemini/code/psm_wma/.r06_sim_pkgs/libero/libero` | bddl_files/init_files(libero_10 全套），pip wheel 0.1.1 资产 |
| 评测脚本 | `cosmos-framework/cosmos_framework/simulation/libero/closed_loop_eval.py` | HTTP client + env loop |
| 服务端脚本 | `cosmos-framework/cosmos_framework/scripts/action_policy_server_libero.py` | HTTP policy server |
| EGL 渲染库 | `/opt/orion/orion_runtime/gpu/opengl/libEGL.so.1` | 无 /dev/dri、无 libOSMesa,EGL 为唯一可用后端（已 smoke 验证） |
| GPU | 单张 A100 40GB(Orion 虚拟化） | server 推理 + EGL 渲染共用 |

## 3. Baseline checkpoint 选型（冻结）

- **R04 checkpoint(`iter_000000020`）不可用**：20 步诊断性训练，不构成正式 baseline。
- **R05 checkpoint 禁止使用**：tiny-overfit 4 样本拟合，无泛化意义（用户明确禁止）。
- **选定：`Cosmos3-Edge-Policy-DROID` 原始推理 checkpoint,zero-shot baseline**。
  请求 `domain_name="libero"`（domain_id=5），动作契约 10D `frame_wise_relative` rot6d，
  chunk 16(Nano LIBERO 合同），图像 256。
  该选择与 SESSION.md“Edge-Policy-DROID -> LIBERO 合同”一致；SR 期望未知，见 §1 风险声明。

## 4. 复用入口与最小改动

- 复用 `closed_loop_eval.py` 现有 serial 路径（`num_envs=1`)、`ActionEnvironmentClient`、
  `_framewise_action_to_delta`、`_remap_gripper`、init states 加载，不改评测脚本。
- 复用 `action_policy_server_libero.py` 现有 CLI(HF checkpoint 直载、domain 路由、
  stats denormalize)，不改服务端脚本。
- 本 Gate 唯一可能需要的新代码：`tools/g0/collect_r06_gate.py`(Gate JSON 汇总，Codex 实现，
  Schema 见 §7)。若直接复用 eval `summary.json` + 独立断言即可满足判据，则不新增。

## 5. 精确命令

### 5.0 前置 smoke（已 PASS，2026-08-15）

```bash
# 导入链（RLinf venv,无外网,CPU)
PYTHONPATH=/gemini/code/psm_wma/cosmos-framework /gemini/code/RLinf/.venv/bin/python -c "
import torch; from cosmos_framework.data.generator.action.libero_pose_utils import ...;
from cosmos_framework.data.generator.action.pose_utils import convert_rotation;
from cosmos_framework.data.generator.action.viewpoint_utils import DEFAULT_VIEWPOINT_TEMPLATES"
# 结果:torch 2.6.0+cu124,三个模块 import OK,convert_rotation rot6d→matrix OK

# EGL 渲染 smoke(MUJOCO_GL=egl,Orion opengl 库,无模型)
MUJOCO_GL=egl PYOPENGL_PLATFORM=egl LD_LIBRARY_PATH=/opt/orion/orion_runtime/gpu/opengl \
/gemini/code/RLinf/.venv/bin/python - <<'EOF'
# OffScreenRenderEnv(libero_10 task0 bddl,256x256) → seed(0) → set_init_state(init[0])
# → agentview_image [256,256,3] uint8 → 5 步 dummy action env.step → 图像变化确认
EOF
# 结果:RENDER SMOKE PASS(图像 [256,256,3] uint8 range 0-248,step 后图像变化)
```

### 5.1 启动 policy server（GPU,py313)

```bash
cd /gemini/code/psm_wma/cosmos-framework
PYTHONPATH=/gemini/code/psm_wma/cosmos-framework \
IMAGINAIRE_OUTPUT_ROOT=/gemini/code/psm_wma/artifacts/g0/r06/server_runtime \
nohup /root/venvs/psm_wma_py313_cu128/bin/python \
  -m cosmos_framework.scripts.action_policy_server_libero \
  --checkpoint-path /gemini/code/models/Cosmos3-Edge-Policy-DROID \
  --host 0.0.0.0 --port 8001 \
  --seed 0 --num-steps 30 --guidance 1.0 --fps 20 \
  --action-chunk-size 16 --max-action-dim 64 --raw-action-dim 10 \
  --action-stats-path /gemini/code/psm_wma/cosmos-framework/cosmos_framework/data/generator/action/normalizer_stats/libero_native_frame_wise_relative_rot6d.json \
  > /gemini/code/psm_wma/artifacts/g0/r06/policy_server.log 2>&1 &
```

启动判据：日志出现模型加载完成且无 Traceback;`curl http://localhost:8001/` 返回 200;
`/info` 返回 checkpoint 路径与采样参数。失败 → BLOCKED_SERVER_LOAD。

### 5.2 最小闭环评测（渲染/客户端，py311)

```bash
cd /gemini/code/psm_wma/cosmos-framework
PYTHONPATH=/gemini/code/psm_wma/cosmos-framework \
MUJOCO_GL=egl PYOPENGL_PLATFORM=egl LD_LIBRARY_PATH=/opt/orion/orion_runtime/gpu/opengl \
/gemini/code/RLinf/.venv/bin/python \
  cosmos_framework/simulation/libero/closed_loop_eval.py \
  --server_url http://localhost:8001 \
  --task_suite libero_10 --task_ids 0 \
  --num_trials_per_task 3 \
  --seed 0 \
  --camera agentview --image_size 256 --env_image_size 256 \
  --action_horizon 16 --action_dim 10 \
  --action_space frame_wise_relative --rotation_space 6d \
  --gripper_mode zero_one --warmup_steps 10 \
  --initial_states_path DEFAULT \
  --num_envs 1 \
  --save_gifs --gif_fps 20 \
  --output_dir /gemini/code/psm_wma/artifacts/g0/r06/eval_task0 \
  2>&1 | tee /gemini/code/psm_wma/artifacts/g0/r06/eval_task0.log
```

固定参数：suite=libero_10,task_ids=0,3 episodes,seed=0,init states=DEFAULT（官方 init file
前 3 条）,warmup=10,max_steps=520(libero_10 默认）,serial(num_envs=1)。

### 5.3 Gate 汇总（CPU)

`tools/g0/collect_r06_gate.py`（若新建，由 Codex 实现）读取：
`eval_task0/summary.json`、per-episode action JSON、policy_server.log、eval_task0.log、
两次重复运行的产物，输出 `artifacts/g0/r06/R06_libero_closed_loop.json`。

## 6. 输入输出 Schema

- 请求：`{"image": base64_png(256x256), "prompt": task_language, "domain_name": "libero", "image_size": 256}`
- 响应：`{"action": [[10 floats] x 16], "video": [b64...]（可空）}`;action 全部 finite。
- eval `summary.json`:`task_suite/total_episodes/total_successes/overall_success_rate/
  selected_task_ids/action_space/rotation_space/action_dim/task_results[episode_results{
  episode,success,steps,error,elapsed_s}]`。
- Gate JSON:`schema_version, gate="G0-R06", status(PASS/FAIL/BLOCKED_*), failures[],
  checks{env_import, render_smoke, server_health, actions_finite, episodes_completed,
  sr_positive, reproducibility}, sr{per_task, overall}, run_config{固定参数全集},
  resources{gpu_peak, wall_time}, provenance{repo_commit, cosmos_commit, checkpoint_path,
  checkpoint_sha?, timestamps, argv}`,失败时附 `error_classification`。

## 7. 断言（Gate collector 机器判定）

1. summary.json 存在且 total_episodes == 3、无 "Skipped due to failed expert demo";
2. 全部 episode `error == null` 且 steps > warmup_steps;
3. per-episode action JSON 全部数值 finite、每条 action len==10;
4. overall_success_rate > 0;
5. 同配置第二次运行的首 episode：首 chunk 第 0 条 action 与第一次 max_abs_diff == 0
   （服务端 seed=0 固定、deterministic 采样路径）;
6. server 日志无 Traceback/OOM;eval 日志无 EGL/MuJoCo 错误。

## 8. 失败分流

| 症状 | 分类 | 动作 |
|---|---|---|
| libero/robosuite/mujoco import 失败 | BLOCKED_ENV | 保留 traceback，报告缺资产清单 |
| EGL context 创建失败 | BLOCKED_RENDER | 试 MUJOCO_GL 显式 egl + Orion 库路径；仍失败则报告 |
| server 加载 checkpoint 失败/OOM | BLOCKED_SERVER_LOAD | 记录峰值显存，40GB 不够则报告资源缺口 |
| /predict 返回空 action 或 HTTP 错误 | FAIL_INTERFACE | 记录响应体，查 domain/stats 契约 |
| action 含 NaN/Inf | FAIL_NONFINITE | 保留 per-episode action JSON |
| 链路全绿但 SR=0 | FAIL_SR_ZERO | 诚实记录；结论为 zero-shot baseline 不成立 |
| 两次运行首 chunk 不一致 | FAIL_NONDETERMINISTIC | 记录 diff，查采样 seed 路径 |

## 9. 产物

- `artifacts/g0/r06/policy_server.log`、`eval_task0.log`、`eval_task0/summary.json`、
  `eval_task0/actions/task_000/episode_*.json`、`eval_task0/gifs/…`(.gitignore 忽略）、
  重复运行目录 `eval_task0_repeat/`、`R06_libero_closed_loop.json`。

## 10. 回填字段

- SESSION.md「正在进行」表 DOC-R06/G0-R06 行 + 「验证记录」;
- TODO.md 状态流转（IN_PROGRESS → REVIEW → DONE 或 BLOCKED);
- `docs/build/log/kimi_operation.log` 追加执行记录；
- 审查/执行报告：`docs/build/PSM-WMA_REVIEW-G0-R06_closed_loop_2026-08-15.md`（执行后回填）。
