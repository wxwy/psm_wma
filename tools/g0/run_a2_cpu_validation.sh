#!/usr/bin/env bash
# Isolated CPU validation; does not install packages or access model/data files.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${1:-$ROOT/artifacts/g0/chatgpt_a2_delivery/cpu}"
[[ "$OUT" = /* ]] || OUT="$ROOT/$OUT"
mkdir -p "$OUT"
cd "$ROOT/cosmos-framework"
export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
.venv/bin/python -c 'import os, cosmos_framework; assert os.path.realpath(cosmos_framework.__file__).startswith(os.getcwd()+"/"), cosmos_framework.__file__; print(cosmos_framework.__file__)'
TESTS=(
  cosmos_framework/model/generator/mot/grouped_active_runtime_test.py
  cosmos_framework/model/generator/mot/grouped_active_model_test.py
  cosmos_framework/model/generator/mot/local_memory_online_test.py
  cosmos_framework/model/generator/mot/local_evidence_test.py
  cosmos_framework/model/generator/mot/ttt_lifecycle_test.py
  cosmos_framework/model/generator/mot/active_local_memory_driver_test.py
  cosmos_framework/model/generator/mot/active_local_memory_launch_test.py
  cosmos_framework/model/generator/mot/local_memory_segment_adapter_test.py
  cosmos_framework/model/generator/mot/canonical_segment_runtime_test.py
  cosmos_framework/model/generator/mot/local_memory_segment_test.py
  cosmos_framework/model/generator/mot/production_active_wiring_test.py
  cosmos_framework/model/generator/omni_mot_model_test.py
)
export A2_CPU_OUT="$OUT" A2_CPU_HARNESS="$ROOT/tools/g0/run_a2_cpu_validation.sh"
.venv/bin/python - <<'PYCPU'
import hashlib, json, os, subprocess
from pathlib import Path
child=Path.cwd()
def git(*args): return subprocess.check_output(['git',*args],cwd=child,text=True).strip()
names=git('ls-files','cosmos_framework').splitlines()
record={'child':git('rev-parse','HEAD'),'root':subprocess.check_output(['git','rev-parse','HEAD'],cwd=child.parent,text=True).strip(),
        'tracked_code_sha256':{p:hashlib.sha256((child/p).read_bytes()).hexdigest() for p in names if (child/p).is_file()},
        'dirty':git('status','--short','--untracked-files=no'),'harness':os.environ['A2_CPU_HARNESS'],
        'harness_sha256':hashlib.sha256(Path(os.environ['A2_CPU_HARNESS']).read_bytes()).hexdigest()}
if record['dirty']: raise SystemExit('Commit candidate source before binding CPU verification.')
Path(os.environ['A2_CPU_OUT'],'receipt.json').write_text(json.dumps(record,indent=2)+'\n')
PYCPU
set +e
.venv/bin/python -m pytest -q "${TESTS[@]}" --junitxml="$OUT/junit.xml" > "$OUT/pytest.log" 2>&1
RC=$?
printf '%s\n' "$RC" > "$OUT/exit_code.txt"
tail -8 "$OUT/pytest.log"
exit "$RC"
