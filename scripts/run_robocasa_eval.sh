#!/usr/bin/env bash
# Owner manually invokes this entry only after the exact implementation Gate is approved.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "${PYTHON:-python}" "${script_dir}/eval_robocasa_18task_queue.py" "$@"
