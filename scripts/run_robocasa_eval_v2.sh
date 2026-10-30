#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export PSM_REPO="${PSM_REPO:-$(cd -- "${script_dir}/.." && pwd)}"
exec "${PYTHON:-python}" "${script_dir}/robocasa_eval_v2_cli.py" "$@"
