# DS_PRO — iter8900 RoboCasa Queue offline guardrails blocker: new Pair targeted CPU → real canary → 4×5

日期：2026-10-21。Owner/DS 原始请求：正式 Queue 未包含 `--no-guardrails`，离线 Guardrail1 下载失败；DS 在 GPU2/port8900 用手工 CLI 禁用 guardrails 的 canary 已观察到模型加载成功和 `/info` 协议正确（**DS-attested；GPT 未读取目标机原始日志**）。此请求是 **iter8900**，不能与之前 iter4000 的评测输出混用。

## 1. 新精确源码身份

- **Implementation Root** `ba91ebb7de2555cd1ff2a290d0af5ee43a8a3ee6`
- **Child / Gitlink** `35b0ea1ccee9ee26653ed6589c484f0997d1c586`（未变）
- **Queue Blob** `72ad7e2b94b31cbfd7a8af0a1eaff92127ffa7ae`
- **Queue test Blob** `d6a52d35b79e1d8636f36583c4122c483a3b3afa`
- Diff from V3 docs-only HEAD `2f75ed0ced577fab75a08a89343f202003f7445b` to new formal source Pair: **production +1 line** `"--no-guardrails",` added to each worker's server_command; **test +1 line** `self.assertEqual(command.count("--no-guardrails"), 1)` in normal 1/2/4 worker synthetic queue test. No other changed file. Source was pushed to V3 and independently read back at exact SHA.
- New Root changes `evaluation_manifest` source digest even though no other frozen protocol changed. **Always use fresh output namespace** and clone/check out correct exact Pair. No DS machine local unpushed commit (e.g. `e8e0132a`) is part of formal source.

## 2. Scope / frozen real assets

- Real G1 Job frozen config file:
`/mnt/data1/data_v2_0617/psm_wma_v3_packed128_runs_fresh_g1_20261019/psm_wma_v3/corrected_phase5/packed128_droid_fresh_g1_20261019/config.yaml`
sha256 `f87e2e49c6931ce7dc32b467aa3f8026269f5ad255216e1cdd8fafb1d7e7374e`.
- **Checkpoint for THIS eval**: same job `checkpoints/iter_000008900`; CLI passes **parent iter root** (containing `model/`), not `iter/model` to Queue. `iter8900/model` .metadata + nonempty DCP shards were reported by DS; actual model success only after real new-Queue canary.
- Four metadata classes exactly `CloseFridge, TurnOnSinkFaucet, PickPlaceSinkToCounter, NavigateKitchen`, `/mnt/data1/data_v2_0617/robocasa365_eval_meta/{Task}/20250816/lerobot/extras/dataset_meta.json` (DS to verify actual paths/unique class).
- Remain Local-TTT `required`, `local_memory_max_sessions=1` per Worker; State15/raw15, `left_wrist`, raw base, H_pred16, R16, chunk16, 20fps, num_steps30/guidance1/seed0, max64. Do not change frozen training Config32; Queue explicit `--action-chunk-size 16`.
- Disabling optional generative guardrails is **offline RoboCasa evaluation only**. This is not permission to alter safety policies/defaults for other model serving contexts. Child default `guardrails=True` remains untouched.
- No GPU inventory `nvidia-smi` requirement. Owner controls training and GPU assignment; DS never terminates unrelated processes or G1 training.

## 3. DS first targeted CPU check, BEFORE new-Queue GPU

Use an isolated **clean detached** Root/Child worktree pinned to exact above SHA/Gitlink; don't reset/clean/force or replace original current worktree. With `CUDA_VISIBLE_DEVICES=''`, offline dependencies and external pycache/Evidence:

```bash
python tools/v3/eval_robocasa_queue_identity_test.py \
  QueueIntegrationTests.test_four_tasks_five_episodes_complete_on_one_two_or_four_workers -v

ruff check --config cosmos-framework/.ruff.toml \
  scripts/eval_robocasa_18task_queue.py tools/v3/eval_robocasa_queue_identity_test.py
ruff format --check --config cosmos-framework/.ruff.toml \
  scripts/eval_robocasa_18task_queue.py tools/v3/eval_robocasa_queue_identity_test.py
python -m py_compile scripts/eval_robocasa_18task_queue.py tools/v3/eval_robocasa_queue_identity_test.py
```

Acceptance: 1/2/4 Worker synthetic 4Task×5 complete and new one-per-worker `--no-guardrails` assertion GREEN, other `--action-chunk-size 16` assertions remain GREEN; Ruff/format/syntax RC0; no leaked processes/threads; correct Root/Child/Blob. **No need to repeat 107/18 or other old tests**. If any CPU FAIL, STOP and send raw evidence; do not launch GPU.

## 4. Real GPU canary (only Owner-released GPU2 if still assigned)

Earlier DS manually ran on GPU2/port8900 with `--no-guardrails`; don't mistake that for a new Queue run. If GPU2 remains Owner-released for this run, DS may execute **new Queue** Stage A with a single CloseFridge task and one real Episode; otherwise await Owner to reassign. No `nvidia-smi` resource inventory requested. Ensure no leftover **DS-owned** manual canary server still listens on selected port; do not kill foreign listeners. Existing Queue fail-closed port/PID/`/info` gates must remain intact.

Variables: `ROOT_WORKTREE` (new exact code Pair), `CHECKPOINT` (iter8900 parent), `CONFIG_FILE` (frozen G1), `SINGLE_TASK_DATASET_ROOT` (unique single-class metadata root, not 4-class root), `SMOKE_OUTPUT_DIR` (empty new directory), `SERVER_PYTHON` (actual Cosmos venv), `SIM_PYTHON` (actual independent robocasa/robosuite venv), `BASE_PORT` (unused), `OWNER_RELEASED_ONE_GPU=2` only if Owner still allocated GPU2.

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

**Canary Pass** only if model real load and `server_info.json` checkpoint canonical `iter8900/model` / config / chunk16 / raw15/state/required/64/fps20/seed0/steps30/guidance1 all match; actual Local-TTT `/predict` transaction runs; 1 real simulator result has typed `success` or `behavioral_failure`, **not** `runtime_error`; RC0, no worker errors and video actually playable. A behavioral failure (SR0/1) is allowed for infrastructure smoke. On any error STOP and report; don't blindly run 20.

## 5. Formal 4Task × 5Episode (after real smoke PASS)

Use **another empty new output namespace** `MAIN_OUTPUT_DIR`, exact same model/Config/Root/Child and all frozen protocol settings. GPU list can be a single Owner-allocated GPU2 (serial one Worker); do not use other unallocated GPUs.

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

Acceptance: real `evaluation_manifest` and `screening_summary.json.status=COMPLETE`, `total_trials=20`, every task exactly5 records, `worker_errors={}`, no `runtime_error`, each 5 real nonempty playable MP4s; report per-task SR, step count, replan count and errors/Local-TTT evidence where available. Never reuse prior iter4000 or pre-flag Root/digest/partial episodes. The legacy Queue runs simulator through `subprocess.run` **without an overall subprocess wall-clock timeout**; watch progress and only terminate its owned evaluation PIDs if stalled, preserving logs.

Stop/feedback: new Pair SHA, test commands/RC, real canary `/info` and model/Local outputs, 20 actual results/MP4 hashes/logs and any exceptions to GPT/Owner. No modifications to Child/trainer/DCP/Config/Checkpoint/other training processes.
