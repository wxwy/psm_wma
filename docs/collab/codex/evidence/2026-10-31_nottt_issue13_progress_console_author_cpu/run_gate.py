"""Issue13 author shell/fake-process gate; no actual torchrun, GPU or DCP."""

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

SHELL = ['scripts/train_v3_matched_no_ttt.sh', 'scripts/train_v3_matched_no_ttt_4gpu.sh']
PYTHON = ['scripts/no_ttt_console.py', 'tools/v3/no_ttt_console_test.py',
          'tools/v3/no_ttt_workers_entry_test.py', 'tools/v3/matched_no_ttt_entry_test.py']
TESTS = [PYTHON[1]]
TESTS += ['tools/v3/no_ttt_workers_entry_test.py::' + name for name in (
    'test_true_worker_flags_in_nongit_source_and_unchanged_zero_launcher',
    'test_invalid_loader_or_non_nott_job_options_rejected_before_python',
    'test_launcher_resume_same_job_with_different_worker_count',
    'test_explicit_prefetch_and_nonpersistent_cli_are_real_profile_options')]
TESTS += ['tools/v3/matched_no_ttt_entry_test.py::' + name for name in (
    'test_launcher_exact_world8_matched_contract_without_torchrun',
    'test_launcher_rejects_g1_job_before_any_python',
    'test_world4_ga4_launcher_uses_only_cuda_4567_and_does_not_request_git_sources',
    'test_world4_launcher_runs_from_nongit_root_with_untracked_eval_docs_and_uses_project_venv',
    'test_world4_launcher_rejects_g1_world8_or_wrong_gpus_before_python')]

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', required=True, type=Path)
parser.add_argument('--expected-root', required=True)
parser.add_argument('--expected-child', required=True)
parser.add_argument('--shellcheck', required=True)
parser.add_argument('--evidence', required=True, type=Path)
args = parser.parse_args()
root, out = args.root.resolve(), args.evidence.resolve()
assert not out.exists() and not out.is_relative_to(root)
out.mkdir(parents=True)
state = dict(status='BLOCKED', gate='ISSUE13_AUTHOR_FAKE_SHELL_CPU_ONLY', steps=[], gpu=False,
             real_training=False, real_dcp=False, old_58_301_rerun=False)

def save(name, value):
    (out/name).write_text(json.dumps(value, indent=2)+'\n')

def git(where, *words):
    return subprocess.check_output(['git','-C',str(where),*words],text=True).strip()

def hashes():
    return {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in SHELL+PYTHON}

try:
    child = root/'cosmos-framework'
    state['identities'] = dict(root=git(root,'rev-parse','HEAD'),child=git(child,'rev-parse','HEAD'),
                               gitlink=git(root,'rev-parse','HEAD:cosmos-framework'))
    assert state['identities'] == dict(root=args.expected_root,child=args.expected_child,gitlink=args.expected_child)
    assert not git(root,'status','--porcelain=v1') and not git(child,'status','--porcelain=v1')
    assert importlib.metadata.version('ruff') == '0.12.7'
    before = hashes()
    save('source_sha256.json',before)
    env = {**os.environ, 'CUDA_VISIBLE_DEVICES':'','COSMOS_DEVICE':'cpu','LD_LIBRARY_PATH':'',
           'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','PYTHONDONTWRITEBYTECODE':'1',
           'PYTEST_ADDOPTS':'','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1',
           'PYTHONPATH':os.pathsep.join(map(str,(root,root/'scripts',child))),
           'HF_HOME':str(out/'cache/hf'),'MPLCONFIGDIR':str(out/'cache/mpl'),
           'XDG_CACHE_HOME':str(out/'cache/xdg'),'RUFF_CACHE_DIR':str(out/'cache/ruff')}
    for name in ('RANK','WORLD_SIZE','LOCAL_RANK','MASTER_ADDR','MASTER_PORT','PSM_PHASE4A_CACHE_ROOT','PSM_PHASE4A_SOURCE_ROOT'):
        env.pop(name,None)
    save('environment.json',dict(python=sys.executable,ruff='0.12.7',scope='fake training processes only',
         overrides={key:env[key] for key in ('CUDA_VISIBLE_DEVICES','COSMOS_DEVICE','LD_LIBRARY_PATH','HF_HUB_OFFLINE',
          'TRANSFORMERS_OFFLINE','PYTHONDONTWRITEBYTECODE','PYTEST_ADDOPTS','OMP_NUM_THREADS','MKL_NUM_THREADS',
          'OPENBLAS_NUM_THREADS','PYTHONPATH','HF_HOME','MPLCONFIGDIR','XDG_CACHE_HOME','RUFF_CACHE_DIR')}))

    def run(name, command, timeout=60):
        step=dict(name=name,argv=list(map(str,command)),cwd=str(root),timeout=timeout)
        state['steps'].append(step)
        state['status']='RUNNING'
        save('gate.json',state)
        print(name,flush=True)
        started=time.monotonic()
        with (out/(name+'.log')).open('wb') as file:
            result=subprocess.run(step['argv'],cwd=root,env=env,stdout=file,stderr=subprocess.STDOUT,timeout=timeout)
        step.update(exit_code=result.returncode,seconds=time.monotonic()-started)
        assert result.returncode == 0, name

    for index,name in enumerate(SHELL):
        run('bash_syntax_'+str(index),['bash','-n',name])
    run('shellcheck_version',[args.shellcheck,'--version'])
    run('shellcheck',[args.shellcheck,*SHELL])
    run('ruff_check',[sys.executable,'-m','ruff','check',*PYTHON])
    run('ruff_format',[sys.executable,'-m','ruff','format','--check',*PYTHON])
    for name in PYTHON:
        ast.parse((root/name).read_text(),filename=name)
    state['ast_files']=len(PYTHON)
    run('pytest',[sys.executable,'-m','pytest','--noconftest','-c','/dev/null','-o','addopts=',
                 '-p','no:cacheprovider','--rootdir='+str(root),'-x','-q','-s','--tb=short',*TESTS,
                 '--basetemp='+str(out/'tmp'),'--junitxml='+str(out/'junit.xml')],180)
    suites=list(ET.parse(out/'junit.xml').getroot().iter('testsuite'))
    totals={key:sum(int(s.get(key,0)) for s in suites) for key in ('tests','failures','errors','skipped')}
    assert totals == dict(tests=49,failures=0,errors=0,skipped=0), totals
    state['totals']=totals
    state['source_unchanged']=hashes()==before
    assert state['source_unchanged'] and not git(root,'status','--porcelain=v1') and not git(child,'status','--porcelain=v1')
    state['status']='PASS'
except Exception as exc:
    state['error']=repr(exc)
    if state['status']=='RUNNING':
        state['status']='FAIL'
save('gate.json',state)
raise SystemExit(0 if state['status']=='PASS' else 1)
