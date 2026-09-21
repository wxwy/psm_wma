# PSM-WMA E003 WINDOW-H16 Training Execution — Current Lock

- Date: 2026-09-21
- Status: READY TO RETEST GATED SMOKE AFTER ABI REMEDIATION
- Code-bearing root lock: `fffe651b9fad0ef15772573da014b01042c93a4a`
- Child lock: `d5de2b2f823a68bf7aab9b21d57f4610cd5a4429`
- Method: E003 native sliding-window history, H=16
- Owner directive: WINDOW-H16 may start now. GRU-H16 / H32 / TTT retraining are not part of this execution.

## 1. Decision

WINDOW-H16 is ready to launch.

Do **not** jump directly into a long formal run. Use this gate sequence:

1. current-lock static/CPU checks
2. FSDP8 5-step smoke
3. reload the smoke checkpoint and run one closed-loop episode
4. if both runtime gates pass, continue the **same output namespace** into formal training with auto-resume

The formal ceiling is 5000 optimizer steps. It is a ceiling, not a required endpoint; the owner may stop at any checkpoint.

## 2. Current implementation identity

The first FSDP8 smoke exposed a cached multi-vision ABI mismatch before iteration 1. The WINDOW transform has now been remediated in child `d5de2b2f823a68bf7aab9b21d57f4610cd5a4429` so every cached vision item carries exactly one latent as `[latent]`, while pixel placeholders remain bare tensors. See `docs/build/PSM-WMA_E003_WINDOW_H16_cached_multivision_ABI_remediation_2026-09-21.md`.

WINDOW-H16 research semantics are unchanged. This current lock supersedes all earlier WINDOW task SHA pairs.

## 3. Frozen WINDOW-H16 semantics

- `PSM_HISTORY_MODE=window`
- horizon: H=16 completed causal steps
- historical observations: full-spatial single-frame causal VAE latents
- historical executed actions: clean action conditioning
- no visual96 pooling
- no GRU compressor
- no Local 1x32 token
- no TTT fast-weight state
- current WAM item stays current-clean / future-noised
- history vision and action share the causal source-frame clock
- fully conditioned history vision items are excluded from diluting target vision loss
- formal run name: `edge_libero_4in1_window_history_h16`

## 4. Lock verification

Before execution:

```bash
cd /disk/rl/psm_wma
git fetch origin
git checkout V2
git pull --ff-only origin V2
git submodule update --init --recursive

git rev-parse HEAD
git -C cosmos-framework rev-parse HEAD
```

Expected:

```text
code-bearing root = fffe651b9fad0ef15772573da014b01042c93a4a
child             = d5de2b2f823a68bf7aab9b21d57f4610cd5a4429
```

The checked-out V2 HEAD may be a docs-only descendant of the code-bearing root. Require `git merge-base --is-ancestor fffe651b9fad0ef15772573da014b01042c93a4a HEAD` to exit 0 and require the child SHA to equal `d5de2b2f823a68bf7aab9b21d57f4610cd5a4429`. If the child differs, report before training.

## 5. Phase 0 — targeted checks

```bash
cd /disk/rl/psm_wma/cosmos-framework

.venv/bin/python -m pytest -q \
  cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset_local_history_test.py \
  cosmos_framework/data/generator/action/utils/transforms_test.py \
  cosmos_framework/model/generator/algorithm/loss/flow_matching_history_test.py \
  cosmos_framework/inference/local_memory_policy_test.py \
  cosmos_framework/simulation/libero/local_memory_client_test.py
```

Also:

```bash
.venv/bin/python -m py_compile \
  cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_edge_all.py \
  cosmos_framework/data/generator/action/utils/transforms.py \
  cosmos_framework/model/generator/omni_mot_model.py \
  cosmos_framework/inference/local_memory_policy.py
```

Acceptance:

- targeted tests pass
- compile checks pass
- no WINDOW contract/import regression

## 6. Phase 1 — FSDP8 5-step smoke

Use a fresh namespace:

```bash
export WINDOW_OUTPUT_ROOT=/disk/rl/outputs/psm_wma_e003_window_h16_fsdp8
```

Launch:

```bash
cd /disk/rl/psm_wma
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7

PSM_HISTORY_MODE=window \
NPROC_PER_NODE=8 \
LIBERO_ROOT=/disk/rl/data/LIBERO_LeRobot_v3 \
OUTPUT_ROOT="$WINDOW_OUTPUT_ROOT" \
DISABLE_AUTO_RESUME=1 \
EXTRA_TAIL_OVERRIDES="trainer.grad_accum_iter=16 trainer.max_iter=5 checkpoint.save_iter=1 trainer.logging_iter=1" \
bash scripts/train_history.sh
```

Expected effective-batch contract:

```text
16 native samples / rank / forward
x 8 ranks
x GA 16
= 2048 consumers / optimizer update
```

Acceptance:

- 8-rank FSDP forward/backward completes
- resolved history mode = `window`
- resolved H = 16
- GA = 16
- finite losses
- no NaN / Inf / OOM / NCCL failure
- no Local-token / GRU / TTT route active
- `iter_000000005` exists
- record wall time and peak GPU memory

## 7. Phase 2 — reload + one closed-loop smoke

Checkpoint:

```text
$WINDOW_OUTPUT_ROOT/cosmos3_action_libero/action_sft/edge_libero_4in1_window_history_h16/checkpoints/iter_000000005
```

Run:

```bash
cd /disk/rl/psm_wma

PSM_HISTORY_MODE=window \
TASK_SUITES="libero_spatial" \
TASK_IDS="0" \
NUM_TRIALS=1 \
MAX_STEPS=220 \
NUM_STEPS=30 \
scripts/eval_history.sh \
"$WINDOW_OUTPUT_ROOT/cosmos3_action_libero/action_sft/edge_libero_4in1_window_history_h16/checkpoints/iter_000000005"
```

Acceptance:

- server reports `history_mode=window`
- `memory_kind=native_window`
- horizon = 16
- step0 history empty
- later requests contain only bounded causal tail
- executable action chunk remains 16 target actions
- no server/client/runtime error

Smoke SR is not a research conclusion.

## 8. Phase 3 — formal training

Only after Phases 1 and 2 pass.

Continue the same namespace and **do not** set `DISABLE_AUTO_RESUME=1`:

```bash
cd /disk/rl/psm_wma
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
export WINDOW_OUTPUT_ROOT=/disk/rl/outputs/psm_wma_e003_window_h16_fsdp8

PSM_HISTORY_MODE=window \
NPROC_PER_NODE=8 \
LIBERO_ROOT=/disk/rl/data/LIBERO_LeRobot_v3 \
OUTPUT_ROOT="$WINDOW_OUTPUT_ROOT" \
EXTRA_TAIL_OVERRIDES="trainer.grad_accum_iter=16 trainer.max_iter=5000 checkpoint.save_iter=100 trainer.logging_iter=1" \
bash scripts/train_history.sh
```

Execution rules:

- 5000 is the ceiling, not a forced stopping point
- do not stop automatically at iter2800 or iter3000
- report checkpoint/loss/wall-time/memory periodically
- do not change H, GA, rank count, or route semantics without owner approval
- if source/config modification is needed, stop, preserve logs, commit separately, and report the new root/child pair before restart

## 9. What to report to owner

At minimum:

- actual root/child SHA
- Phase 0 pass count
- exact smoke command
- resolved H / ranks / GA / effective batch
- smoke checkpoint path
- finite loss confirmation
- wall time / peak GPU memory
- reload/eval smoke PASS/FAIL
- formal training start command
- current formal iteration/checkpoint
- any failure root cause

Write ds_pro execution feedback to:

`docs/collab/chatgpt/DS_PRO_FEEDBACK_E003_WINDOW_H16_2026-09-21.md`

## 10. Deferred

Do not start in this task:

- GRU-H16
- H32
- TTT retraining
- WINDOW evaluation sweep before owner selects a checkpoint
