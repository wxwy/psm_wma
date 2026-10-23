#!/usr/bin/env bash
set -euo pipefail
cd /workspace/psm_wma
sources=(
 scripts/eval_robocasa_18task_queue.py scripts/robocasa_eval_config.py
 scripts/robocasa_eval_progress.py scripts/robocasa_eval_video_view.py
 tools/v3/eval_robocasa_queue_identity_test.py tools/v3/robocasa_eval_config_test.py
 tools/v3/robocasa_eval_progress_test.py tools/v3/robocasa_eval_video_view_test.py
 cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval.py
 cosmos-framework/cosmos_framework/utils/rollout_progress.py
 cosmos-framework/cosmos_framework/utils/rollout_progress_test.py
)
/workspace/.venvs/psm-wma-cpu/bin/ruff --version
/workspace/.venvs/psm-wma-cpu/bin/ruff check --config cosmos-framework/.ruff.toml "${sources[@]}" > /tmp/psm-v3-live-progress-20261023/ruff_check.log 2>&1
/workspace/.venvs/psm-wma-cpu/bin/ruff format --check --config cosmos-framework/.ruff.toml "${sources[@]}" > /tmp/psm-v3-live-progress-20261023/ruff_format.log 2>&1
env PYTHONPYCACHEPREFIX=/tmp/psm-v3-live-progress-20261023/pycache /workspace/.venvs/psm-wma-cpu/bin/python -m py_compile "${sources[@]}" > /tmp/psm-v3-live-progress-20261023/syntax.log 2>&1
/workspace/.venvs/psm-wma-cpu/bin/python /tmp/psm-v3-live-progress-20261023/source_checks.py
git diff --check
git -C cosmos-framework diff --check
