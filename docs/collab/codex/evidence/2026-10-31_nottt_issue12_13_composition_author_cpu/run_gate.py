"""Freeze exact composition objects and run six synthetic CPU receiver cases."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = 'b260290ef09ef25a8a41259aef153df5efff3369'
CONSOLE = '24dbb677f7a60eeab6934c44352c7e00fa6d9b36'
PORT = 'c66ade95b044d3664cd782d43d7917a604425db3'
CFORMAL = 'baf1b5bf46853e9849a91518803b9738fc216235'
PYTHON = ['scripts/no_ttt_console.py', 'tools/v3/no_ttt_console_test.py',
          'tools/v3/matched_no_ttt_entry_test.py', 'tools/v3/no_ttt_workers_entry_test.py',
          'tools/v3/no_ttt_async_port_test.py', 'tools/v3/no_ttt_integrated_entry_test.py']
SHELL = ['scripts/train_v3_matched_no_ttt.sh', 'scripts/train_v3_matched_no_ttt_4gpu.sh']
INHERITED = {name: CONSOLE for name in PYTHON[:4] + SHELL}
INHERITED['tools/v3/no_ttt_async_port_test.py'] = PORT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-worktree', type=Path, required=True)
    parser.add_argument('--expected-root', required=True)
    parser.add_argument('--expected-child', required=True)
    parser.add_argument('--evidence-dir', type=Path, required=True)
    args = parser.parse_args()
    root, out = args.root_worktree.resolve(), args.evidence_dir.resolve()
    child = root / 'cosmos-framework'
    if out.exists() or out.is_relative_to(root):
        parser.error('new EXTERNAL evidence dir required')
    out.mkdir(parents=True)
    state = dict(status='BLOCKED', gate='AUTHOR_MINIMAL_ISSUE12_13_COMPOSITION_CPU', steps=[],
                 real_gpu=False, real_data=False, real_model=False, real_dcp=False,
                 training=False, actual_torchrun=False, pool_spawn=False,
                 historical49_43_58_301_rerun=False, gpu_performance_rerun=False)

    def save(name, data):
        (out / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

    def git(where, *words):
        return subprocess.check_output(['git', '-C', str(where), *words])

    def sha(where, *words):
        return git(where, *words).decode().strip()

    try:
        identity = dict(root=sha(root, 'rev-parse', 'HEAD'), child=sha(child, 'rev-parse', 'HEAD'),
                        gitlink=sha(root, 'rev-parse', 'HEAD:cosmos-framework'))
        state['identities'] = identity
        assert identity == dict(root=args.expected_root, child=args.expected_child, gitlink=args.expected_child)
        assert args.expected_child == CFORMAL
        assert not sha(root, 'status', '--porcelain=v1') and not sha(child, 'status', '--porcelain=v1')
        assert importlib.metadata.version('ruff') == '0.12.7'
        assert sha(root, 'rev-parse', 'HEAD^') == BASE
        inherited = []
        for name, donor in INHERITED.items():
            selected = sha(root, 'rev-parse', f'{args.expected_root}:{name}')
            approved = sha(root, 'rev-parse', f'{donor}:{name}')
            assert selected == approved, name
            assert git(root, 'ls-tree', args.expected_root, name).split(b'\t')[0] == git(root, 'ls-tree', donor, name).split(b'\t')[0]
            inherited.append(dict(path=name, donor=donor, blob=selected))
        names = sha(root, 'diff-tree', '--no-commit-id', '--name-only', '-r', args.expected_root).splitlines()
        allowed = set(PYTHON + SHELL + ['SESSION.md', 'TODO.md', 'cosmos-framework',
                    'docs/build/PSM-WMA_V3_NoTTT_Issue12_13_Minimal_Composition_2026-10-31.md'])
        assert set(names) == allowed
        protected = {}
        for name in ('cosmos_framework/evaluation', 'cosmos_framework/inference', 'cosmos_framework/simulation',
                     'cosmos_framework/model', 'cosmos_framework/checkpoint', 'cosmos_framework/configs'):
            observed = sha(child, 'rev-parse', f'{CFORMAL}:{name}')
            assert observed == sha(child, 'rev-parse', f'0ae313e329d290fc6b8a50fda1112820fb7ac485:{name}')
            protected[name] = observed
        root_trees = {}
        for name in ('configs', 'third_party', 'tools/v3/eval_v2_production_tests', 'docs/collab/chatgpt/reviews'):
            selected = sha(root, 'rev-parse', args.expected_root + ':' + name)
            assert selected == sha(root, 'rev-parse', BASE + ':' + name)
            root_trees[name] = selected
        save('object_audit.json', dict(status='PASS_AUTHOR_COMPOSITION_OBJECT_AUDIT',
             root=args.expected_root, child=CFORMAL, gitlink=CFORMAL, baseline=BASE,
             root_inherited=inherited, inherited_root_paths=len(inherited), inherited_root_production_paths=3,
             whole_child_unchanged_from_approved_port=True, protected_child_trees=protected,
             protected_root_trees=root_trees, root_changed_paths=names))
        watched = PYTHON + SHELL

        def hashes():
            return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in watched}

        before = hashes()
        save('source_sha256.json', before)
        for name in PYTHON:
            ast.parse((root / name).read_text(), filename=name)
        state['syntax_python_files'] = len(PYTHON)
        env_values = dict(
            CUDA_VISIBLE_DEVICES='', COSMOS_DEVICE='cpu', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
            PYTHONDONTWRITEBYTECODE='1', LD_LIBRARY_PATH='', PYTEST_ADDOPTS='',
            OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
            HF_HOME=str(out / 'cache/hf'), MPLCONFIGDIR=str(out / 'cache/mpl'),
            XDG_CACHE_HOME=str(out / 'cache/xdg'), RUFF_CACHE_DIR=str(out / 'cache/ruff'),
            PYTHONPATH=os.pathsep.join(map(str, (root, child, root / 'scripts'))))
        env = {**os.environ, **env_values}
        for name in ('RANK', 'WORLD_SIZE', 'LOCAL_RANK', 'LOCAL_WORLD_SIZE', 'MASTER_ADDR', 'MASTER_PORT'):
            env.pop(name, None)
        save('environment.json', dict(python=sys.version, overrides=env_values,
             versions={k: importlib.metadata.version(k) for k in ('torch', 'pytest', 'ruff')},
             note='4GPU launcher symbolically sets CUDA_VISIBLE_DEVICES4,5,6,7, but executable is CPU torchrun substitute; torch.version.cuda is asserted None.'))

        def run(name, command, timeout=60):
            step = dict(name=name, argv=command, cwd=str(root), timeout_s=timeout)
            state['steps'].append(step)
            state['status'] = 'RUNNING'
            save('gate.json', state)
            print('[NoTTT composition CPU] ' + name, flush=True)
            started = time.monotonic()
            with (out / (name + '.log')).open('w') as log:
                result = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
            step.update(exit_code=result.returncode, seconds=time.monotonic() - started)
            assert result.returncode == 0, name

        run('bash_syntax', ['bash', '-n', SHELL[0]])
        run('bash_syntax4', ['bash', '-n', SHELL[1]])
        run('shellcheck', ['/tmp/psm-nottt-console-20261031/tools/bin/shellcheck', *SHELL])
        run('ruff_check', [sys.executable, '-m', 'ruff', 'check', *PYTHON])
        run('ruff_format', [sys.executable, '-m', 'ruff', 'format', '--check', *PYTHON])
        run('composition', [sys.executable, '-m', 'pytest', '--noconftest', '-c', '/dev/null', '-q', '-s', '-x',
                           '-p', 'no:cacheprovider', '--rootdir=' + str(root),
                           'tools/v3/no_ttt_integrated_entry_test.py',
                           '--basetemp=' + str(out / 'cases'), '--junitxml=' + str(out / 'junit.xml')], 480)
        suites = ET.parse(out / 'junit.xml').getroot().findall('.//testsuite')
        totals = {k: sum(int(s.get(k, '0')) for s in suites) for k in ('tests', 'failures', 'errors', 'skipped')}
        state['totals'] = totals
        assert totals == dict(tests=6, failures=0, errors=0, skipped=0), totals
        assert before == hashes()
        assert not sha(root, 'status', '--porcelain=v1') and not sha(child, 'status', '--porcelain=v1')
        state.update(status='PASS', source_unchanged=True)
    except BaseException as exc:
        state.update(status='FAIL', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        save('gate.json', state)
    print(json.dumps({k: v for k, v in state.items() if k != 'steps'}, indent=2))


if __name__ == '__main__':
    main()
