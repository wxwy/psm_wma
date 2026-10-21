# DS_PRO — V3 iter4000 真实 RoboCasa staged GO（Owner 释放 GPU 后执行）

日期：2026-10-21
任务：在 Owner 信任 DS 独立 CPU 验收且自主管理 GPU 释放的前提下，执行 **真实 Action Server+Local-TTT+RoboCasa Simulator**，从一条真实 smoke episode 逐级到四任务×五 Episode。
**本指令现为准备就绪/conditional GO；尚未收到 Owner 提供的实际空闲 GPU ID 与明确“已经释放、开始执行”通知时绝对不得启动 GPU。**

## Source 与资产不可变身份

- **Implementation Root** `306d235046fe5d578503beb17a56f5c0eb0f5634`。
- **Child/Gitlink** `35b0ea1ccee9ee26653ed6589c484f0997d1c586`。
- **HIGH-07 Queue Blob** `4916918aca412a0abc6cb00e28f6053a351e07d8`。
- **Existing G1 Config** `/mnt/data1/data_v2_0617/psm_wma_v3_packed128_runs_fresh_g1_20261019/psm_wma_v3/corrected_phase5/packed128_droid_fresh_g1_20261019/config.yaml`，expected SHA256 `f87e2e49c6931ce7dc32b467aa3f8026269f5ad255216e1cdd8fafb1d7e7374e`；模型 Checkpoint 是同一 Job 下 `checkpoints/iter_000004000`（**CLI 传父 checkpoint 根，不要传 model/ 目录**）。
- **DATASET_ROOT**：此前 DS 真实 four-task metadata 来源 `/mnt/data1/data_v2_0617/robocasa365_eval_meta`（运行前只读确认实际完整路径，四底层类 exactly `CloseFridge, TurnOnSinkFaucet, PickPlaceSinkToCounter, NavigateKitchen`）。
- 使用已验证 clean detached Root/Child exact SHA（可以沿用 `/mnt/data1/data_v2_0617/dspro_verify_iter4000_306d2350_20261021/root` 如果它仍然 clean 并正确绑定上面两个 SHAs）。不得将文档 HEAD 作为 Implementation；禁止升级 Child 或替换权重。
- **Server Python**：真实 Cosmos3 推理 venv；**sim Python**：独立 RoboCasa/robosuite venv，两者不能混用。DS 自行填入已核验的真实绝对路径，不得猜测或更改全局环境。
- 冻结 G1 `config.yaml/config.pkl/v3_job_identity.json`、Checkpoint、训练进程保持原样；不读取/补写 `optim/` 作为 model-only 推理前置。Queue 已包含 `--action-chunk-size 16` 和严格 `/info` 判定，无需再向命令行人为加 override。
- 新 Root/Child 形成独立 evaluation identity；Smoke 与 Formal 必须两个**从未使用过的全新输出目录**，不得跨旧 Root/digest拼接 results 或用 `--resume` 处理 partial episodes。

## 前置的 Owner GPU 控制

Owner 明确说由其本人决定何时停训练、释放指定 GPU。本轮 **不得执行 GPU inventory/`nvidia-smi` 或替 Owner 结束训练**。只有 Owner 通过直接消息明确告知 DS **“GPU <具体ID>已腾出，可以开始本次评测”** 后，才执行下面 GPU 命令。若只释放一张 GPU，允许串行跑20 Episode；若释放两张，用两个独立 GPU/Worker。不能靠共用仍在训练的 GPU 冒险。端口由 Queue 自检，不允许抢占未知原 Listener。

## Stage A — 真实 1 Episode smoke（强制）

在 Owner 指定的 **一张**已释放 GPU 上，用真实队列而非假 HTTP Fixture 完成 1 Task×1 Episode：
- 真实模型 `iter_000004000/model` 加载 + `/info` 校验；
- 严格 local `required`、`max_sessions=1`、PID/port 所有权校验；
- RoboCasa 实际 `/predict`、Local-TTT 在线 session 更新、真实仿真动作消费及错误分类；
- `server_info.json` 的 checkpoint `.../iter_000004000/model`、config、chunk16/raw15/state/64/fps20/numsteps30/guidance1、required；
- 一条 `results.json` with `outcome` `success` 或 `behavioral_failure` （行为失败不阻止算 infra smoke PASS）、不得是 `runtime_error`；实际 MP4 非零且可解码（视频失败/环境错误要显式反馈）。
- 使用官方数据目录下唯一底层 Task（建议 `CloseFridge`）真实 `lerobot` 父根作为 `--dataset-root`，确保仅一个 `extras/dataset_meta.json`，`--expected-tasks 1 --num-test-episodes 1`。先证明输入资产 exact；别虚构路径或把四任务根传入 expected1。

在 Root worktree 手工运行模板（**必须先填所有变量及得到 Owner 放行**）：

```bash
cd "$ROOT_WORKTREE"
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
"$SERVER_PYTHON" scripts/eval_robocasa_18task_queue.py \
  --checkpoint-path "$CHECKPOINT" --config-file "$CONFIG_FILE" \
  --dataset-root "$SINGLE_TASK_DATASET_ROOT" --output-dir "$SMOKE_OUTPUT_DIR" \
  --server-python "$SERVER_PYTHON" --sim-python "$SIM_PYTHON" \
  --gpus "$OWNER_RELEASED_ONE_GPU" --base-port "$BASE_PORT" \
  --expected-tasks 1 --num-test-episodes 1 --action-horizon 16 \
  --seed 0 --num-steps 30 --guidance 1.0 --timeout 600
```

Gate A 失败、无正确 server_info、返回 RC!=0、有 `runtime_error`、`worker_errors`、MP4 无效、模型不加载或真 Local-TTT 不可用时，**STOP，保留所有日志且只终止本次评测拥有的进程，不继续20 Episode**。不能把模型行为失败 `behavioral_failure` 当作基础设施报错。

## Stage B — 正式 4 Task × 5 Episode（Gate A 绿后可连续执行，无需重新跑 CPU Gate）

使用**新的** MAIN_OUTPUT_DIR（不同于 Smoke），与 Stage A 同 Root/Child/Checkpoint/Config；four-task dataset root 完整 exact 4 task；Owner 实际释放的一张或两张 GPU explicit list，Queue 各 Worker 一 GPU、一 Action Server、一 Serial Local session slot，模型和仿真各用自己的 Python venv。逐 Task 5 Episode，合计**20条真实结果**：

```bash
cd "$ROOT_WORKTREE"
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
"$SERVER_PYTHON" scripts/eval_robocasa_18task_queue.py \
  --checkpoint-path "$CHECKPOINT" --config-file "$CONFIG_FILE" \
  --dataset-root "$DATASET_ROOT" --output-dir "$MAIN_OUTPUT_DIR" \
  --server-python "$SERVER_PYTHON" --sim-python "$SIM_PYTHON" \
  --gpus "$OWNER_RELEASED_GPU_IDS" --base-port "$BASE_PORT" \
  --expected-tasks 4 --num-test-episodes 5 --action-horizon 16 \
  --seed 0 --num-steps 30 --guidance 1.0 --timeout 600
```

- `ROOT_WORKTREE` 必须绑定 **新 Pair**，`CHECKPOINT` 传 iter 根，`CONFIG_FILE` 传冻结 Config 原绝对路径；
- 不改 seed/sampler/Local mode/State/raw15/H16/R16/camera left_wrist/base raw/sampling30/fps20/contrast条件；
- CLI `--gpus` 显式指定，只能是 Owner 提供已释放的 GPU ID（`"0"` 或 `"0,1"` 为语法示例，不宣称这些 GPU 当前空闲）。`BASE_PORT` 使用未被其它服务占用的端口，Queue 会检查；
- 无错误时 `screening_summary.json.status=COMPLETE`，`total_trials=20`、四个 task 各5且 `worker_errors={}`，`sr` 是真实20条的平均而非 CPU fixture 0.6。必须无 `runtime_error` / task `error`，视频真实非空可解码。每 Task 返回真实 SR/done_steps/replans/Local-TTT 数据（可提供时）、真实动作日志及失败原因。
- 已完成整个 Task 的 same-identity resume 才能用 `--resume`；partial Episode不可复用，错误/中断时优先停下确认后再以全新 namespace 重跑，禁止跨 Output/Root/digest 合并成绩。

## 运行中限制与汇报

- `--timeout 600` 并非 Queue `subprocess.run()` 的进程级 wall-clock watchdog。DS 必须监督日志；遇到 GPU OOM、异常、长时间无进展等情况，按自己拥有的 Server/Queue/Simulator PID 有序停止并报告，不得自动重启/全局 pkill。
- 整个执行期间不修改 G1 原始文件，不做训练 job resume/migrate/optim 修复，不切换 Local required→off、不篡改冻结 config32。所有日志/中间结果要保留。
- **Stage A** 实际 /info、model load、Local-TTT、episode和视频的证据；**Stage B** 完整 Eval manifest、server_info.json/server_process.json、各 Task results/rollout MP4、logs、screening_summary.json、命令/版本/退出码及异常/失败分类。返回 GPT/Owner；如失败，STOP 而不是继续扩大修复范围。

## 正式 Gate 性质

同 Formal Pair 的代码 CPU/static Gate 早已 `APPROVE`；Owner 对 DS 独立 CPU 原始日志存档执行了 waiver，所以 Evidence Gate 标记 `CLOSED — OWNER_ACCEPTED_DS_ATTESTATION`，**未声称GPT已打开本机压缩包**。本请求允许 DS **准备** staged execution，实际 GPU 许可须 Owner 告知确切卡号与已释放状态；直到此通知前 `NOT_EXECUTED`。
