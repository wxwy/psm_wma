"""Frozen synthetic CPU gate for the No-TTT console boundary only."""
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

BASE = 'cee6f53eef345579c3db1124148f350fd2edc618'
PYTHON = ['scripts/no_ttt_console.py', 'tools/v3/no_ttt_console_test.py',
          'tools/v3/no_ttt_console_boundary_test.py', 'tools/v3/no_ttt_integrated_entry_test.py']
PLAN = 'docs/build/PSM-WMA_V3_NoTTT_Console_Starting_Training_Boundary_2026-10-31.md'


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
        parser.error('NEW external evidence directory required')
    out.mkdir(parents=True)
    state = dict(status='BLOCKED', gate='AUTHOR_NOTTT_CONSOLE_START_BOUNDARY_CPU', steps=[],
                 real_gpu=False, real_job_checkpoint_data=False, training=False, simulation=False,
                 historical84_or_full49_rerun=False)

    def save(name, value):
        (out / name).write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')

    def git(where, *words):
        return subprocess.check_output(['git', '-C', str(where), *words])

    def text(where, *words):
        return git(where, *words).decode().strip()

    try:
        identities = dict(root=text(root, 'rev-parse', 'HEAD'), child=text(child, 'rev-parse', 'HEAD'),
                          gitlink=text(root, 'rev-parse', 'HEAD:cosmos-framework'))
        state['identities'] = identities
        assert identities == dict(root=args.expected_root, child=args.expected_child, gitlink=args.expected_child)
        assert identities['child'] == '6c83596d6a259e89c4cd3e79424024983426ac3d'
        assert text(root, 'rev-parse', 'HEAD^') == BASE
        assert not text(root, 'status', '--porcelain=v1') and not text(child, 'status', '--porcelain=v1')
        assert importlib.metadata.version('ruff') == '0.12.7'

        def tree(sha):
            return {row.split(b'\t', 1)[1].decode(): row.split(b'\t', 1)[0].decode()
                    for row in git(root, 'ls-tree', '-rz', sha).split(b'\0') if row}

        baseline, candidate = tree(BASE), tree(args.expected_root)
        changed = {n for n in baseline.keys() | candidate.keys() if baseline.get(n) != candidate.get(n)}
        assert changed == set(PYTHON + ['SESSION.md', 'TODO.md', PLAN]), changed
        untouched = (baseline.keys() | candidate.keys()) - changed
        assert all(baseline.get(n) == candidate.get(n) for n in untouched)
        old_ast = ast.parse(git(root, 'show', BASE + ':scripts/no_ttt_console.py').decode())
        new_ast = ast.parse((root / 'scripts/no_ttt_console.py').read_text())
        functions = lambda module: {n.name: ast.dump(n, include_attributes=False) for n in module.body if isinstance(n, ast.FunctionDef)}
        old_funcs, new_funcs = functions(old_ast), functions(new_ast)
        preserved = ['_write_all', '_owned', '_signal', '_cleanup', 'main']
        assert all(old_funcs[n] == new_funcs[n] for n in preserved)
        launchers = {p: candidate[p] for p in ('scripts/train_v3_matched_no_ttt.sh', 'scripts/train_v3_matched_no_ttt_4gpu.sh')}
        assert all(launchers[p] == baseline[p] for p in launchers)
        save('scope_audit.json', dict(status='PASS_EXACT_SCOPE', root=args.expected_root, child=identities['child'],
             canonical_base=BASE, changed_paths=sorted(changed), production_changed_paths=['scripts/no_ttt_console.py'],
             all_other_root_objects_unchanged=len(untouched), whole_child_unchanged=True,
             launchers_unchanged=launchers, raw_write_process_cleanup_and_main_AST_unchanged=preserved))

        def hashes():
            return {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in PYTHON}

        before = hashes()
        save('source_sha256.json', before)
        for p in PYTHON:
            ast.parse((root / p).read_text(), filename=p)
        state['syntax_python_files'] = len(PYTHON)
        overrides = dict(CUDA_VISIBLE_DEVICES='', COSMOS_DEVICE='cpu', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
             PYTHONDONTWRITEBYTECODE='1', LD_LIBRARY_PATH='', PYTEST_ADDOPTS='',
             OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
             HF_HOME=str(out / 'cache/hf'), MPLCONFIGDIR=str(out / 'cache/mpl'),
             XDG_CACHE_HOME=str(out / 'cache/xdg'), RUFF_CACHE_DIR=str(out / 'cache/ruff'),
             PYTHONPATH=os.pathsep.join(map(str, (root, child, root / 'scripts'))))
        env = {**os.environ, **overrides}
        for p in ('RANK', 'WORLD_SIZE', 'LOCAL_RANK', 'LOCAL_WORLD_SIZE', 'MASTER_ADDR', 'MASTER_PORT'):
            env.pop(p, None)
        save('environment.json', dict(python=sys.version, overrides=overrides,
             versions={p: importlib.metadata.version(p) for p in ('ruff', 'pytest', 'torch')},
             note='Integration substitutes torchrun with CPU shim; launcher GPU IDs are symbolic, torch.version.cuda None is asserted. No native training/worker pool.'))

        def run(name, command, timeout=60):
            step = dict(name=name, argv=command, cwd=str(root), timeout_s=timeout)
            state['steps'].append(step)
            state['status'] = 'RUNNING'
            save('gate.json', state)
            print('[NoTTT boundary CPU] ' + name, flush=True)
            started = time.monotonic()
            with (out / (name + '.log')).open('w') as log:
                result = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
            step.update(exit_code=result.returncode, seconds=time.monotonic() - started)
            assert result.returncode == 0, name

        run('ruff_check', [sys.executable, '-m', 'ruff', 'check', *PYTHON])
        run('ruff_format', [sys.executable, '-m', 'ruff', 'format', '--check', *PYTHON])
        pytest = [sys.executable, '-m', 'pytest', '--noconftest', '-c', '/dev/null', '-q', '-s', '-x',
                  '-p', 'no:cacheprovider', '--rootdir=' + str(root)]
        run('console', pytest + ['tools/v3/no_ttt_console_test.py', 'tools/v3/no_ttt_console_boundary_test.py',
             '--basetemp=' + str(out / 'console_tmp'), '--junitxml=' + str(out / 'console.xml')], 480)
        run('integration', pytest + ['tools/v3/no_ttt_integrated_entry_test.py',
             '--basetemp=' + str(out / 'integration_tmp'), '--junitxml=' + str(out / 'integration.xml')], 480)
        combined = ET.Element('testsuites')
        totals = dict(tests=0, failures=0, errors=0, skipped=0)
        for name, count in (('console', 40), ('integration', 6)):
            suites = list(ET.parse(out / (name + '.xml')).getroot().iter('testsuite'))
            observed = {k: sum(int(s.get(k, '0')) for s in suites) for k in totals}
            assert observed == dict(tests=count, failures=0, errors=0, skipped=0), observed
            for s in suites:
                combined.append(s)
            for k in totals:
                totals[k] += observed[k]
        ET.ElementTree(combined).write(out / 'junit.xml', encoding='utf-8', xml_declaration=True)
        assert totals == dict(tests=46, failures=0, errors=0, skipped=0)
        state['totals'] = totals
        assert hashes() == before
        assert not text(root, 'status', '--porcelain=v1') and not text(child, 'status', '--porcelain=v1')
        state.update(status='PASS', source_unchanged=True)
    except BaseException as exc:
        state.update(status='FAIL', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        save('gate.json', state)
    print(json.dumps({k: v for k, v in state.items() if k != 'steps'}, indent=2))


if __name__ == '__main__':
    main()
