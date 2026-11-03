import ast
import datetime
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path('/workspace/psm-wma-eval-r02-format')
CHILD = ROOT / 'cosmos-framework'
OUT = Path('/tmp/psm-eval-v2-r02-format-20261103')
PYTHON = '/workspace/.venvs/psm-wma-cpu/bin/python'
RUFF = '/workspace/.venvs/psm-wma-cpu/bin/ruff'
OLD_ROOT = '286573d2d592cbd7449930e6e93f188a3a9b037d'
OLD_CHILD = '37558dcc71682304f3de1848923e6cedb9b77837'
FILES = [
    'cosmos-framework/cosmos_framework/simulation/robocasa/render_devices.py',
    'tools/v3/eval_v2_batch_tests/render_devices_test.py',
]
TESTS = [FILES[1], 'tools/v3/eval_v2_batch_tests/render_mapping_test.py']
EXPECTED = [
    '358fb64f5178a0d296b882eb56c69bceaa0e3ba13222bfd45dee7d452a5b4219',
    '868359a0f626ce7dbc8fe6ee31223778b63f45901cd01a75b67152ab02247f77',
]
ENV = dict(os.environ)
ENV.update({
    'CUDA_VISIBLE_DEVICES': '', 'COSMOS_DEVICE': 'cpu', 'LD_LIBRARY_PATH': '',
    'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1',
    'MUJOCO_GL': 'osmesa', 'PYOPENGL_PLATFORM': 'osmesa',
    'PYTHONDONTWRITEBYTECODE': '1', 'PYTEST_ADDOPTS': '',
    'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
    'PYTHONPATH': f'{ROOT}:{ROOT / "scripts"}:{CHILD}',
    'HF_HOME': str(OUT / 'cache/hf'),
    'MPLCONFIGDIR': str(OUT / 'cache/matplotlib'),
    'XDG_CACHE_HOME': str(OUT / 'cache/xdg'),
    'RUFF_CACHE_DIR': str(OUT / 'cache/ruff'),
    'TMPDIR': str(OUT / 'tmp'),
})
for name in ('cache/hf', 'cache/matplotlib', 'cache/xdg', 'cache/ruff', 'tmp'):
    (OUT / name).mkdir(parents=True, exist_ok=True)


def write(path, value):
    path = OUT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    assert not path.exists(), f'refusing evidence overwrite: {path}'
    if not isinstance(value, str):
        value = json.dumps(value, indent=2, sort_keys=True) + '\n'
    path.write_text(value)


def run(name, args, expected=0, cwd=ROOT):
    result = subprocess.run(args, cwd=cwd, env=ENV, capture_output=True, text=True)
    write(name + '.log', result.stdout + result.stderr)
    write(name + '.command.json', {
        'args': args, 'shell_display': shlex.join(args), 'cwd': str(cwd),
        'returncode': result.returncode, 'expected_returncode': expected,
    })
    print(name, 'exit', result.returncode, flush=True)
    assert result.returncode == expected, result.stdout + result.stderr
    return result.stdout


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()


def identity():
    return {
        'root': git('rev-parse', 'HEAD'),
        'child': git('rev-parse', 'HEAD', cwd=CHILD),
        'gitlink': git('rev-parse', 'HEAD:cosmos-framework'),
        'root_status': git('status', '--porcelain'),
        'child_status': git('status', '--porcelain', cwd=CHILD),
    }


def asts(phase):
    result = {}
    for index, name in enumerate(FILES):
        data = (ROOT / name).read_bytes()
        tree = ast.dump(ast.parse(data), include_attributes=False)
        write(f'{phase}/source_{index}.txt', data.decode())
        write(f'{phase}/ast_{index}.txt', tree + '\n')
        result[name] = {
            'sha256': hashlib.sha256(data).hexdigest(),
            'ast_sha256': hashlib.sha256(tree.encode()).hexdigest(),
        }
    write(f'{phase}/fingerprints.json', result)
    return result


stage = sys.argv[1]
if stage == 'before':
    ident = identity()
    assert ident == {'root': OLD_ROOT, 'child': OLD_CHILD, 'gitlink': OLD_CHILD,
                     'root_status': '', 'child_status': ''}, ident
    write('before/identity.json', ident)
    write('environment.json', {
        'python': sys.version, 'python_executable': sys.executable,
        'packages': {n: importlib.metadata.version(n) for n in
                     ['ruff', 'pytest', 'numpy', 'scipy', 'Pillow', 'requests', 'PyYAML']},
        'overrides': {k: ENV[k] for k in [
            'CUDA_VISIBLE_DEVICES', 'COSMOS_DEVICE', 'LD_LIBRARY_PATH',
            'HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'MUJOCO_GL',
            'PYOPENGL_PLATFORM', 'PYTHONDONTWRITEBYTECODE', 'PYTEST_ADDOPTS',
            'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
            'PYTHONPATH', 'HF_HOME', 'MPLCONFIGDIR', 'XDG_CACHE_HOME',
            'RUFF_CACHE_DIR', 'TMPDIR']},
        'scope': 'CPU synthetic boundary doubles only; no real EGL/CUDA/model/robot',
    })
    assert run('before/ruff_version', [RUFF, '--version']).strip() == 'ruff 0.12.7'
    values = asts('before')
    assert [values[f]['sha256'] for f in FILES] == EXPECTED
    run('before/format_check', [RUFF, 'format', '--check', *FILES], expected=1)
    for i, name in enumerate(FILES):
        run(f'before/format_diff_{i}', [RUFF, 'format', '--diff', name], expected=1)
    print('EXACT BASELINE + DS SOURCE HASHES + FORMAT RED2 CONFIRMED')
elif stage == 'format':
    for i, name in enumerate(FILES):
        run(f'format/file_{i}', [RUFF, 'format', name])
    after = asts('after')
    before = json.loads((OUT / 'before/fingerprints.json').read_text())
    equal = {f: before[f]['ast_sha256'] == after[f]['ast_sha256'] for f in FILES}
    assert all(equal.values()), equal
    write('after/ast_parity.json', {'status': 'PASS', 'files': equal})
    run('after/ruff_check', [RUFF, 'check', *FILES])
    run('after/format_check', [RUFF, 'format', '--check', *FILES])
    run('after/root_diff_check', ['git', 'diff', '--check'])
    run('after/child_diff_check', ['git', 'diff', '--check'], cwd=CHILD)
    print('AST IDENTICAL; RUFF CHECK + FORMAT PASS')
elif stage == 'cpu':
    before = identity()
    assert not before['root_status'] and not before['child_status'], before
    assert before['child'] == before['gitlink']
    write('final/identity_before.json', before)
    command = [PYTHON, '-m', 'pytest', '--noconftest', '-c', '/dev/null', '-q',
               '-p', 'no:cacheprovider', *TESTS, '--basetemp', str(OUT / 'pytest_tmp'),
               '--junitxml', str(OUT / 'final/junit.xml')]
    run('final/pytest', command)
    tree = ET.parse(OUT / 'final/junit.xml')
    cases = tree.findall('.//testcase')
    assert len(cases) == 66, len(cases)
    assert len({(c.attrib['classname'], c.attrib['name']) for c in cases}) == 66
    assert not tree.findall('.//failure') and not tree.findall('.//error')
    assert not tree.findall('.//skipped')
    run('final/ruff_check', [RUFF, 'check', *FILES])
    run('final/format_check', [RUFF, 'format', '--check', *FILES])
    after = identity()
    write('final/identity_after.json', after)
    assert before == after, (before, after)
    write('final/gate.json', {
        'status': 'AUTHOR_CPU_PASS', **before, 'tests': 66, 'distinct_tests': 66,
        'failures': 0, 'errors': 0, 'skips': 0, 'gpu_executed': False,
        'ast_format_parity': 'PASS', 'ruff_version': '0.12.7',
        'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'not_independent_DS_or_GPT_approval': True,
    })
    print('CLEAN EXACT PAIR CPU66 PASS; ZERO FAIL/ERROR/SKIP')
else:
    raise ValueError(stage)
