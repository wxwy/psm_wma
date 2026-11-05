"""Issue19 F1 exact-pair author CPU runner; no server/GPU access."""

import ast
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

ROOT = Path('/workspace/psm-wma-g2-depth-v2')
OUT = Path('/tmp/g2_issue19_f1_20261105_author_cpu/final')
FORMAL = '5e6903b9dd09828f725dc61dcd6e98012fae87b3'
CHILD = '1069fe78841228cadbbfbe6afbd767eaed6225da'
BASE = '8d3a5b297d9b3339c16a873a7e1e04941a20a745'
TESTS = ['tools/g2/test_depth_zero_sentinel.py', 'tools/g2/test_rgbd_pose_export.py',
         'tools/g2/test_spatial_photometric_policy.py', 'tools/g2/test_cache_root_preflight.py']


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot():
    return {'head': git('rev-parse', 'HEAD'), 'status': git('status', '--porcelain=v1'),
            'child_gitlink': git('ls-tree', 'HEAD', 'cosmos-framework').split()[2]}


OUT.mkdir(parents=True, exist_ok=False)
before = snapshot()
save('git_before.json', before)
assert before == {'head': FORMAL, 'status': '', 'child_gitlink': CHILD}, before
env_keys = ['PYTHONPATH', 'CUDA_VISIBLE_DEVICES', 'MUJOCO_GL', 'COSMOS_DEVICE',
            'PYTHONDONTWRITEBYTECODE', 'PYTEST_ADDOPTS', 'HF_HUB_OFFLINE',
            'TRANSFORMERS_OFFLINE', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
            'MKL_NUM_THREADS', 'HF_HOME', 'MPLCONFIGDIR', 'XDG_CACHE_HOME', 'NUMBA_CACHE_DIR']
save('runtime.json', {'python': sys.version, 'executable': sys.executable,
                     'platform': platform.platform(),
                     'packages': {p: importlib.metadata.version(p) for p in
                                  ['numpy', 'pyarrow', 'scipy', 'pytest', 'ruff', 'mujoco']},
                     'environment': {k: os.environ.get(k) for k in env_keys},
                     'native_robocasa': False, 'gpu_used': False,
                     'server_data_accessed_or_transferred': False})
files = git('ls-files', 'tools/g2').splitlines()
files.append('docs/build/PSM-WMA_G2_Depth_ZeroSentinel_v2_and_SevenEpisode_Transition_2026-11-05.md')
bindings = {p: {'git_blob': git('rev-parse', f'HEAD:{p}'), 'sha256': sha(ROOT / p)} for p in files}
save('source_bindings.json', bindings)
changed = git('diff', '--name-only', BASE, FORMAL).splitlines()
assert all(p.startswith('tools/g2/') or p in ['SESSION.md', 'TODO.md', files[-1]] for p in changed)
(OUT / 'implementation.diff').write_text(git('diff', BASE, FORMAL) + '\n', encoding='utf-8')

PREVIOUS = 'fbe578908a840a5f4e5b351f1c2e8fb019def6e5'
source_delta = git('diff', '--name-only', PREVIOUS, FORMAL, '--', 'tools/g2').splitlines()
assert set(source_delta) == {'tools/g2/rgbd_pose/cache.py', 'tools/g2/test_rgbd_pose_export.py', 'tools/g2/test_cache_root_preflight.py'}
old_tree = ast.parse(git('show', PREVIOUS + ':tools/g2/test_rgbd_pose_export.py'))
new_tree = ast.parse((ROOT / 'tools/g2/test_rgbd_pose_export.py').read_text())
assert [ast.dump(n) for n in ast.walk(old_tree) if isinstance(n, ast.Assert)] == [ast.dump(n) for n in ast.walk(new_tree) if isinstance(n, ast.Assert)]
red_dir = Path('/tmp/g2_issue19_f1_20261105_author_cpu/red')
red_result = json.loads((red_dir / 'result.json').read_text())
red_frozen = json.loads((red_dir / 'frozen_before.json').read_text())
assert red_result == {'tests': 5, 'failures': 5, 'errors': 0, 'skipped': 0, 'frozen_inputs_unchanged': True}
assert sha(ROOT / 'tools/g2/test_cache_root_preflight.py') == red_frozen['files']['tools/g2/test_cache_root_preflight.py']
save('incremental_scope.json', {'previous_formal_root': PREVIOUS, 'source_delta': source_delta, 'original_assertions_unchanged': True, 'regression_unchanged_from_red': True, 'previous_independent_review': '99ad0de0249a660d46642c3ae849129733b3c503', 'native_rerun': False, 'expected_old_code_red': red_result})

commands = [
    ('pytest', [sys.executable, '-m', 'pytest', '--noconftest', '-c', '/dev/null',
                '-q', '-p', 'no:cacheprovider', *TESTS,
                '--basetemp', str(OUT / 'pytest_tmp'), '--junitxml', str(OUT / 'junit.xml')]),
    ('ruff_check', [sys.executable, '-m', 'ruff', 'check', 'tools/g2']),
    ('ruff_format_check', [sys.executable, '-m', 'ruff', 'format', '--check', 'tools/g2']),
    ('ast', [sys.executable, '-c',
             'import ast,pathlib; paths=sorted(pathlib.Path("tools/g2").rglob("*.py")); '
             '[(ast.parse(p.read_text(encoding="utf-8"),filename=str(p)),print("PASS",p)) for p in paths]; '
             'print("AST files:",len(paths))']),
    ('diff_check', ['git', 'diff', '--check', BASE, FORMAL]),
]
save('commands.json', {'cwd': str(ROOT), 'commands': [{'name': n, 'argv': a} for n, a in commands]})
steps = []
started = datetime.now(timezone.utc).isoformat()
for name, command in commands:
    with (OUT / (name + '.log')).open('w', encoding='utf-8') as stream:
        code = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT).returncode
    steps.append({'name': name, 'returncode': code})
    print(name, 'PASS' if code == 0 else f'FAIL({code})', flush=True)
    if code:
        break
after = snapshot()
save('git_after.json', after)
unchanged = before == after and all(sha(ROOT / p) == b['sha256'] for p, b in bindings.items())
counts = {}
per_file = {}
if (OUT / 'junit.xml').exists():
    xml = ET.parse(OUT / 'junit.xml').getroot()
    cases = xml.findall('.//testcase')
    counts = {'tests': len(cases), 'failures': len(xml.findall('.//failure')),
              'errors': len(xml.findall('.//error')), 'skipped': len(xml.findall('.//skipped'))}
    names = {p: {node.name for node in ast.parse((ROOT / p).read_text()).body
                 if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')} for p in TESTS}
    for p in TESTS:
        per_file[p] = sum(c.attrib['name'].split('[')[0] in names[p] for c in cases)
    assert sum(per_file.values()) == len(cases)
passed = (len(steps) == len(commands) and all(s['returncode'] == 0 for s in steps)
          and unchanged and counts.get('tests') == 181
          and all(counts.get(k) == 0 for k in ['failures', 'errors', 'skipped']))
save('gate.json', {
    'schema': 'psm_wma_g2_issue19_f1_author_cpu_v1', 'status': 'PASS' if passed else 'FAIL',
    'started_utc': started, 'ended_utc': datetime.now(timezone.utc).isoformat(),
    'formal_root': FORMAL, 'child': CHILD, 'gitlink': CHILD, 'remediation_parent': BASE,
    'branch': git('branch', '--show-current'), 'changed_files': changed,
    'steps': steps, 'junit': counts, 'per_file_tests': per_file, 'source_unchanged': unchanged,
    'scope': 'AUTHOR_SYNTHETIC_CPU_NOT_INDEPENDENT_NATIVE_ACCEPTANCE',
    'not_run': ['real CloseFridge global736/local234 frames73,74', 'GPU/EGL/RoboCasa',
                'seven legacy episodes validation/migration', 'production resume', 'V3 merge'],
})
sys.exit(0 if passed else 1)
