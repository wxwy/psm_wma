# PSM-WMA REVIEW-G0-R06 closed-loop baseline 执行报告

- 日期：2026-08-15
- 执行：Kimi（独立审查 + 执行）；Runbook：`docs/build/PSM-WMA_G0_R06_closed_loop_baseline_runbook_v0.1.md`
- Gate JSON：`artifacts/g0/r06/R06_libero_closed_loop.json`

## 结论

**Gate 状态：FAIL（FAIL_SR_ZERO）**。

所有工程链路断言通过，但验收条件 `SR > 0` 未满足：Edge-Policy-DROID 原始 checkpoint 在
libero_10 task 0（"put both the alphabet soup and the tomato sauce in the basket"）zero-shot
3 个 episode 全部失败，SR = 0/3，同 seed 重跑逐位一致。这是真实、可复现的基线测量结论，
不是工程缺陷。

## 七条判据逐项核验（Runbook §7）

| # | 断言 | 结果 | 证据 |
|---|---|---|---|
| 1 | summary.json 存在、total_episodes==3、无 skipped | PASS | `eval_task0/summary.json` |
| 2 | 全部 episode error==null 且 steps>warmup(10) | PASS | 3×520 步满 rollout，error 全 null |
| 3 | per-episode action 全 finite | PASS（带 deviation，见下） | 3×520×7D 全 finite，abs_max≈2.72 |
| 4 | overall_success_rate > 0 | **FAIL** | 0.0（重跑同为 0.0） |
| 5 | 同 seed 重跑一致 | PASS（超额） | 3×520×7D 逐位一致，max_abs_diff=0.0 |
| 6 | server 无 Traceback/OOM；eval 无 EGL/MuJoCo 错误 | PASS | server 0 ERROR；两侧 eval 日志 0 错误 |
| 7 | Gate JSON 落盘 | PASS | `R06_libero_closed_loop.json` |

## 实际执行的命令与环境（与 Runbook §5 有两处偏差，均已记录）

Policy server（py313/cu128，GPU）:

```bash
cd /gemini/code/psm_wma/cosmos-framework
PYTHONPATH=/gemini/code/psm_wma/cosmos-framework \
IMAGINAIRE_OUTPUT_ROOT=/gemini/code/psm_wma/artifacts/g0/r06/server_runtime \
TRITON_LIBCUDA_PATH=/opt/orion/orion_runtime/gpu/cuda \
/root/venvs/psm_wma_py313_cu128/bin/python -m cosmos_framework.scripts.action_policy_server_libero \
  --checkpoint-path /gemini/code/models/Cosmos3-Edge-Policy-DROID \
  --host 0.0.0.0 --port 8001 --seed 0 --num-steps 30 --guidance 1.0 --fps 20 \
  --action-chunk-size 16 --max-action-dim 64 --raw-action-dim 10 \
  --action-stats-path .../normalizer_stats/libero_native_frame_wise_relative_rot6d.json
```

闭环评测（RLinf venv py3.11，EGL 离屏渲染）：

```bash
cd /gemini/code/psm_wma/cosmos-framework
PYTHONPATH=/gemini/code/psm_wma/.r06_sim_pkgs:/gemini/code/psm_wma/cosmos-framework \
MUJOCO_GL=egl PYOPENGL_PLATFORM=egl LD_LIBRARY_PATH=/opt/orion/orion_runtime/gpu/opengl \
/gemini/code/RLinf/.venv/bin/python cosmos_framework/simulation/libero/closed_loop_eval.py \
  --server_url http://localhost:8001 --task_suite libero_10 --task_ids 0 \
  --num_trials_per_task 3 --seed 0 --camera agentview --image_size 256 --env_image_size 256 \
  --action_horizon 16 --action_dim 10 --action_space frame_wise_relative --rotation_space 6d \
  --gripper_mode zero_one --warmup_steps 10 --initial_states_path DEFAULT --num_envs 1 \
  --save_gifs --gif_fps 20 --output_dir artifacts/g0/r06/eval_task0
```

### 偏差 1：仿真环境来自 RLinf venv（新增事实）

`/root/venvs/psm_wma*` 均不含 mujoco/robosuite/libero/bddl。离线可用来源：
`/gemini/code/RLinf/.venv`（py3.11，torch 2.6.0+cu124，mujoco 3.8.1，robosuite 1.4.1，
libero 0.1.0 editable，bddl 3.6.0）。缺失的 `loguru` 从 py313 venv 拷贝到
`/gemini/code/psm_wma/.r06_sim_pkgs/`（纯 Python，无版本冲突）。
`/root/.libero/config.yaml` 资产路径指向 `/gemini/code/RLinf/.venv/libero/libero/libero/`。

### 偏差 2：server 需 TRITON_LIBCUDA_PATH（首轮 BLOCKED 已归档）

首轮评测 3 episode 全部 steps=0，根因为 server 端 torch.compile → inductor → triton
`libcuda_dirs()` 依赖 `/sbin/ldconfig -p`，而 ldconfig 缓存无 libcuda 条目
（`triton/backends/nvidia/driver.py:22-41`）。修复：server 启动环境增加
`TRITON_LIBCUDA_PATH=/opt/orion/orion_runtime/gpu/cuda`。失败证据归档于
`artifacts/g0/r06/eval_task0_failed_triton/`。建议 Runbook v0.2 把该变量写入 §5.1 正式命令。

### Runbook v0.1 §7.3 措辞偏差

per-episode action 日志记录的是 env 执行的 7D action（10D rot6d 经 client 转换后下发），
并非 raw 10D。raw (16,10) finite 由独立 `/predict` smoke（39.1s 含编译）与 server 日志
193 次请求 `action_steps=16` 零错误佐证。建议 v0.2 拆成两级断言。

## 结果与数据

- 两次运行各 3 episode：全部 520 步满 rollout、error=null、success=False，SR 0/3。
- 重复性：episode_000..002 的 520×7D env action 序列两次运行**逐位一致**（max_abs_diff=0.0）。
- server 推理延迟：193 次 /predict，稳态中位 1714ms/chunk（16 步），首次含编译 39056ms。
- GPU 观测占用 9544 MiB（A100 40GB）。
- 失败模式（GIF 目视）：机械臂全程悬停移动，未抓取/放置任何物体，basket 始终为空——
  典型的 zero-shot 无任务进展，而非动作发散或环境异常。

## 判读

- 链路（实时渲染观测 → server 扩散推理 → action 转换 → env.step → 成功判定）端到端验证通过，
  满足 R06 的“不使用 R12 离线 latent、必须实时闭环”要求。
- FAIL_SR_ZERO 与既有事实一致：R03/R04 已确认发布 checkpoint 的 domain 5（libero）action
  projection 行未经 LIBERO 训练；zero-shot 直接闭环不保证 SR>0。
- R06 验收条件“SR>0”要成立，baseline 选择需要用户重新决策（候选：R04/R05 之后的正式 LIBERO
  SFT checkpoint；R05 tiny-overfit checkpoint 已被用户明确排除）。

## 产物清单

- `artifacts/g0/r06/R06_libero_closed_loop.json`（Gate JSON，status=FAIL/FAIL_SR_ZERO）
- `artifacts/g0/r06/eval_task0/`、`eval_task0_repeat/`（summary、actions、gifs）
- `artifacts/g0/r06/policy_server.log`、`eval_task0.log`、`eval_task0_repeat.log`
- `artifacts/g0/r06/eval_task0_failed_triton/`（首轮 BLOCKED 证据）
- `docs/build/PSM-WMA_G0_R06_closed_loop_baseline_runbook_v0.1.md`（Runbook，建议升 v0.2 修正上述两处）
