"""Frozen old-config RED / real new CLI GREEN; synthetic CPU metadata only."""
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

BASE = '0ab13951d640d50ea2c9c8812817bf3009eae7b5'
PROD = 'scripts/robocasa_eval_v2/config.py'
TEST = 'tools/v3/eval_v2_batch_tests/tasks_cli_test.py'
REGRESSION = 'tools/v3/eval_v2_batch_tests/config_test.py'
PLAN = 'docs/build/PSM-WMA_V3_EvalV2_CLI_Tasks_All_Fix_2026-10-31.md'
RED_NODE = TEST + '::test_public_dry_run_cli_and_yaml_all_emit_same_18_task_plan_without_runtime'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root-worktree', required=True, type=Path)
    p.add_argument('--expected-root', required=True)
    p.add_argument('--expected-child', required=True)
    p.add_argument('--evidence-dir', required=True, type=Path)
    a = p.parse_args()
    root, out = a.root_worktree.resolve(), a.evidence_dir.resolve()
    child = root / 'cosmos-framework'
    if out.exists() or out.is_relative_to(root):
        p.error('NEW external evidence dir required')
    out.mkdir(parents=True)
    state = dict(status='BLOCKED', gate='AUTHOR_EVALV2_CLI_TASKS_ALL_CPU', steps=[],
                 real_gpu=False, real_model_data_DCP=False, simulation_training_or_active_job=False)

    def save(name, value):
        (out / name).write_text(json.dumps(value, indent=2)+'\n')

    def git(repo, *args):
        return subprocess.check_output(['git', '-C', str(repo), *args])

    def text(repo, *args):
        return git(repo, *args).decode().strip()

    try:
        identities = dict(root=text(root, 'rev-parse', 'HEAD'), child=text(child, 'rev-parse', 'HEAD'),
                          gitlink=text(root, 'rev-parse', 'HEAD:cosmos-framework'))
        state['identities'] = identities
        assert identities == dict(root=a.expected_root, child=a.expected_child, gitlink=a.expected_child)
        assert text(root, 'rev-parse', 'HEAD^') == BASE
        assert a.expected_child == '6c83596d6a259e89c4cd3e79424024983426ac3d'
        assert not text(root, 'status', '--porcelain=v1') and not text(child, 'status', '--porcelain=v1')
        assert importlib.metadata.version('ruff') == '0.12.7'

        def tree(s):
            return {row.split(b'\t', 1)[1].decode(): row.split(b'\t', 1)[0].decode()
                    for row in git(root, 'ls-tree', '-rz', s).split(b'\0') if row}

        before_tree, after_tree = tree(BASE), tree(a.expected_root)
        changed = {n for n in before_tree.keys() | after_tree.keys() if before_tree.get(n) != after_tree.get(n)}
        assert changed == {PROD, TEST, PLAN, 'SESSION.md', 'TODO.md'}, changed
        other = (before_tree.keys() | after_tree.keys()) - changed
        assert all(before_tree.get(n) == after_tree.get(n) for n in other)
        old_config = git(root, 'show', BASE + ':' + PROD)
        new_config = (root / PROD).read_bytes()
        assert old_config.replace(b'cfg["tasks"] = a.tasks.split(",")',
                                  b'cfg["tasks"] = "all" if a.tasks == "all" else a.tasks.split(",")', 1) == new_config
        save('scope_audit.json', dict(status='PASS_ONE_LINE_ONLY', root=a.expected_root,
             child=a.expected_child, baseline=BASE, changed_paths=sorted(changed),
             production_changed_paths=[PROD], one_line_production_fix=True,
             other_root_objects_unchanged=len(other), whole_child_unchanged=True,
             discovery_scheduler_identity_runtime_training_unchanged=True))

        watched = [PROD, TEST, REGRESSION, 'scripts/robocasa_eval_v2/cli.py', 'scripts/robocasa_eval_v2/identity.py']

        def hashes():
            return {n: hashlib.sha256((root/n).read_bytes()).hexdigest() for n in watched}

        frozen = hashes()
        save('source_sha256.json', frozen)
        for n in (PROD, TEST):
            ast.parse((root/n).read_text(), filename=n)
        state['syntax_python_files'] = 2
        overrides = dict(CUDA_VISIBLE_DEVICES='', COSMOS_DEVICE='cpu', HF_HUB_OFFLINE='1',
             TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1', LD_LIBRARY_PATH='',
             PYTEST_ADDOPTS='', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
             HF_HOME=str(out/'cache/hf'), MPLCONFIGDIR=str(out/'cache/mpl'),
             XDG_CACHE_HOME=str(out/'cache/xdg'), RUFF_CACHE_DIR=str(out/'cache/ruff'),
             PYTHONPATH=os.pathsep.join(map(str, (root, root/'scripts', child))))
        env = {**os.environ, **overrides}
        for n in ('RANK', 'WORLD_SIZE', 'LOCAL_RANK', 'LOCAL_WORLD_SIZE', 'MASTER_ADDR', 'MASTER_PORT'):
            env.pop(n, None)
        save('environment.json', dict(python=sys.version, overrides=overrides,
             versions={n: importlib.metadata.version(n) for n in ('pytest', 'ruff')}))

        def run(name, command, expected=0, timeout=120):
            step = dict(name=name, argv=command, cwd=str(root), timeout_s=timeout, expected_exit=expected)
            state['steps'].append(step)
            state['status'] = 'RUNNING'
            save('gate.json', state)
            print('[EvalV2 tasks CPU] '+name, flush=True)
            started = time.monotonic()
            with (out/(name+'.log')).open('w') as log:
                result = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
            step.update(exit_code=result.returncode, seconds=time.monotonic()-started)
            assert result.returncode == expected, name

        run('ruff_check', [sys.executable, '-m', 'ruff', 'check', PROD, TEST])
        run('ruff_format', [sys.executable, '-m', 'ruff', 'format', '--check', PROD, TEST])
        red_dir = out/'red_old_config'
        red_dir.mkdir()
        old_path = red_dir/'config.py'
        old_path.write_bytes(old_config)
        save('red_source_binding.json', dict(old_root=BASE, old_path=PROD,
             old_blob=text(root, 'rev-parse', BASE+':'+PROD), old_sha256=hashlib.sha256(old_config).hexdigest(),
             frozen_test_root=a.expected_root, frozen_test_blob=text(root, 'rev-parse', a.expected_root+':'+TEST),
             frozen_test_sha256=frozen[TEST],
             unchanged_cli_blob=text(root, 'rev-parse', a.expected_root+':scripts/robocasa_eval_v2/cli.py'),
             unchanged_discovery_blob=text(root, 'rev-parse', a.expected_root+':scripts/robocasa_eval_v2/identity.py'),
             method='load exact old config Git blob in sys.modules before importing unchanged production CLI and frozen new regression; no source/assertion edits'))
        bootstrap = red_dir/'bootstrap.py'
        bootstrap.write_text(
            'import importlib.util,sys,robocasa_eval_v2,pytest\n'
            f'spec=importlib.util.spec_from_file_location("robocasa_eval_v2.config",{str(old_path)!r})\n'
            'module=importlib.util.module_from_spec(spec)\n'
            'sys.modules[spec.name]=module\nspec.loader.exec_module(module)\n'
            'robocasa_eval_v2.config=module\nraise SystemExit(pytest.main(sys.argv[1:]))\n')
        flags = ['--noconftest', '-c', '/dev/null', '-q', '-s', '-x', '-p', 'no:cacheprovider', '--rootdir='+str(root)]
        run('red', [sys.executable, str(bootstrap), *flags, RED_NODE,
                    '--basetemp='+str(out/'red_tmp'), '--junitxml='+str(out/'red.xml')], expected=1)
        red_cases = list(ET.parse(out/'red.xml').getroot().iter('testcase'))
        assert len(red_cases) == 1 and red_cases[0].find('failure') is not None
        assert red_cases[0].find('error') is None and red_cases[0].find('skipped') is None
        failure = ''.join(red_cases[0].find('failure').itertext())
        assert 'only RoboCasa365 Target Atomic-Seen tasks are supported' in failure
        assert hashes() == frozen
        state['red_old_config_expected_failure'] = True
        run('green', [sys.executable, '-m', 'pytest', *flags, TEST, REGRESSION,
                      '--basetemp='+str(out/'green_tmp'), '--junitxml='+str(out/'junit.xml')])
        suites = list(ET.parse(out/'junit.xml').getroot().iter('testsuite'))
        totals = {k: sum(int(s.get(k, '0')) for s in suites) for k in ('tests', 'failures', 'errors', 'skipped')}
        assert totals == dict(tests=29, failures=0, errors=0, skipped=0), totals
        state['totals'] = totals
        assert hashes() == frozen
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
