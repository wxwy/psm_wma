#!/usr/bin/env bash
# Reuse an existing environment. CPU fixtures/reference kernels only; no install.
set -euo pipefail

: "${G2_C_PYTHON:?Set the existing Python executable}"
: "${G2_C_RUFF:?Set the existing Ruff executable}"
: "${G2_C_EXPECTED_CHILD:?Set the fixed candidate SHA}"
root_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../../.." && pwd)
child_dir=${G2_C_CHILD_DIR:-"$root_dir/cosmos-framework"}
evidence_dir=${G2_C_EVIDENCE_DIR:-"$root_dir/work/g2_c_cpu_run"}
test "$(git -C "$child_dir" rev-parse HEAD)" = "$G2_C_EXPECTED_CHILD"
test -z "$(git -C "$child_dir" status --porcelain)"
mkdir -p -- "$(dirname -- "$evidence_dir")"
mkdir -- "$evidence_dir" # Refuse to overwrite previous evidence.
exec > >(tee "$evidence_dir/console.log") 2>&1
export CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu LD_LIBRARY_PATH=''
export PYTHONPATH="$child_dir" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export G2_C_CPU_EVIDENCE_DIR="$evidence_dir"
cd -- "$child_dir"

"$G2_C_PYTHON" - "$root_dir" "$evidence_dir" <<'PY'
import hashlib, importlib.metadata, json, pathlib, platform, subprocess, sys
root, out = map(pathlib.Path, sys.argv[1:])
def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()
files = sorted(p for p in git('ls-files').splitlines()
               if p.endswith(('.py', '.toml', '.template.json')) or p == 'AGENTS.md')
fingerprints = {p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in files}
(out / 'source_before.json').write_text(json.dumps(fingerprints, indent=2, sort_keys=True) + '\n')
dependency = '6d72d4d252c287fc8060bdc5a8db7f6cf959af1e'
subprocess.run(['git', 'merge-base', '--is-ancestor', dependency, 'HEAD'], check=True)
protected = ['cosmos_framework/model', 'cosmos_framework/inference', 'cosmos_framework/scripts']
subprocess.run(['git', 'diff', '--exit-code', dependency, 'HEAD', '--', *protected], check=True)
changed = git('diff', '--name-only', 'd5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2', dependency).splitlines()
protected_blobs = {p: git('rev-parse', 'HEAD:' + p) for p in changed if p.startswith(tuple(v + '/' for v in protected))}
metadata = {'scope': 'CPU fixtures/reference kernels; NOT real DATA_C/Edge/FSDP/GPU',
            'child': git('rev-parse', 'HEAD'), 'dependency_child': dependency,
            'root': git('-C', str(root), 'rev-parse', 'HEAD'),
            'root_gitlink': git('-C', str(root), 'ls-tree', 'HEAD', 'cosmos-framework'),
            'python': sys.version, 'platform': platform.platform(),
            'packages': {p: importlib.metadata.version(p) for p in ('torch', 'pytest', 'ruff', 'transformers')},
            'source_count': len(files), 'protected_blobs': protected_blobs}
(out / 'runtime_and_protection.json').write_text(json.dumps(metadata, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: metadata[k] for k in ('child', 'dependency_child', 'source_count', 'scope')}, sort_keys=True))
PY

owned_py=(
  cosmos_framework/checkpoint/g2_warm_start.py
  cosmos_framework/checkpoint/g2_warm_start_test.py
  cosmos_framework/data/generator/action/datasets/g2_training_adapter.py
  cosmos_framework/data/generator/action/datasets/g2_training_adapter_test.py
  cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft.py
  cosmos_framework/data/generator/action/utils/json_formatter.py
  cosmos_framework/data/generator/action/utils/transforms.py
  cosmos_framework/data/generator/action/utils/static_task_text.py
  cosmos_framework/data/generator/action/utils/static_task_text_test.py
  cosmos_framework/data/generator/joint_dataloader.py
  cosmos_framework/trainer/__init__.py
  cosmos_framework/trainer/local_memory_grouped.py
  cosmos_framework/trainer/local_memory_grouped_resume.py
  cosmos_framework/trainer/g2_training.py
  cosmos_framework/trainer/g2_training_test.py
  cosmos_framework/trainer/g2_grouped_integration_test.py
  examples/psm_wma_robocasa_corrected_phase5.py
  examples/psm_wma_robocasa_g2_recipe.py
  examples/psm_wma_robocasa_g2_recipe_test.py
)
"$G2_C_RUFF" check "${owned_py[@]}" | tee "$evidence_dir/ruff.log"
"$G2_C_RUFF" format --check "${owned_py[@]}" | tee "$evidence_dir/format.log"
"$G2_C_PYTHON" -m py_compile "${owned_py[@]}"
git diff --check

cat > "$evidence_dir/pytest.ini" <<'INI'
[pytest]
markers =
    L0: legacy CPU mark
    level: legacy level mark
junit_suite_name = g2_c_cpu_fixed
INI
tests=(
  cosmos_framework/data/generator/action/utils/static_task_text_test.py
  cosmos_framework/data/generator/action/utils/transforms_test.py
  cosmos_framework/data/generator/action/datasets/g2_training_adapter_test.py
  cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft_test.py
  cosmos_framework/trainer/g2_training_test.py
  cosmos_framework/trainer/g2_grouped_integration_test.py
  cosmos_framework/checkpoint/g2_warm_start_test.py
  examples/psm_wma_robocasa_g2_recipe_test.py
  cosmos_framework/trainer/local_memory_grouped_test.py
  cosmos_framework/trainer/local_memory_grouped_resume_test.py
  examples/psm_wma_robocasa_corrected_phase5_test.py
  examples/psm_wma_robocasa_phase5_f0_test.py
  cosmos_framework/model/generator/mot/g2_contracts_test.py
  cosmos_framework/model/generator/mot/g2_core_test.py
  cosmos_framework/model/generator/mot/g2_integration_test.py
  cosmos_framework/model/generator/mot/global_memory_test.py
  cosmos_framework/model/generator/mot/global_spatial_test.py
  cosmos_framework/inference/g2_model_hooks_test.py
  cosmos_framework/inference/g2_policy_conditions_test.py
  cosmos_framework/inference/g2_session_cache_test.py
  cosmos_framework/inference/g2_text_kv_cache_test.py
  cosmos_framework/scripts/g2_policy_server_test.py
)
printf '%s\n' "${tests[@]}" > "$evidence_dir/test_modules.txt"
printf '%q ' "$G2_C_PYTHON" -m pytest --noconftest --rootdir="$child_dir" -c "$evidence_dir/pytest.ini" -p no:cacheprovider -q -rs --disable-warnings "${tests[@]}" --junitxml="$evidence_dir/junit.xml" > "$evidence_dir/pytest.command"
printf '\n' >> "$evidence_dir/pytest.command"
"$G2_C_PYTHON" -m pytest --noconftest --rootdir="$child_dir" -c "$evidence_dir/pytest.ini" -p no:cacheprovider -q -rs --disable-warnings "${tests[@]}" --junitxml="$evidence_dir/junit.xml" | tee "$evidence_dir/pytest.log"

"$G2_C_PYTHON" -m examples.psm_wma_robocasa_corrected_phase5 --help > "$evidence_dir/phase5_help.txt"
set +e
"$G2_C_PYTHON" -m examples.psm_wma_robocasa_g2_recipe --check examples/psm_wma_robocasa_g2_recipe.template.json > "$evidence_dir/incomplete_recipe.log" 2>&1
template_status=$?
set -e
test "$template_status" = 2

"$G2_C_PYTHON" - "$evidence_dir" <<'PY'
import hashlib, json, pathlib, subprocess, sys, xml.etree.ElementTree as ET
out = pathlib.Path(sys.argv[1])
before = json.loads((out / 'source_before.json').read_text())
after = {p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in before}
(out / 'source_after.json').write_text(json.dumps(after, indent=2, sort_keys=True) + '\n')
assert before == after
assert not subprocess.check_output(['git', 'status', '--porcelain'], text=True)
root = ET.parse(out / 'junit.xml').getroot()
cases = root.findall('.//testcase')
summary = {'junit_testcases_including_subtests': len(cases),
           'failures': len(root.findall('.//failure')), 'errors': len(root.findall('.//error')),
           'skipped': [{'name': c.attrib.get('name'), 'reason': c.find('skipped').attrib.get('message')}
                       for c in cases if c.find('skipped') is not None],
           'source_before_after_identical': len(before),
           'incomplete_formal_recipe_exit': 2,
           'not_run': ['real DATA_B/C alignment', 'validated full G1 checkpoint', 'full Edge parameter inventory',
                       'CUDA/BF16/FSDP training/resume', 'formal R1/R2', 'full evaluation']}
assert summary['failures'] == summary['errors'] == 0
(out / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
PY
