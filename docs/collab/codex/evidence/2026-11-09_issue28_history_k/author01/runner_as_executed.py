"""Exact clean pair, scoped Issue28 CPU checks; no old 900/965 or GPU gate."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET

BASE_ROOT = '9b1756f9099955d6637743f8ad2fa0ee54987b7a'
BASE_CHILD = '60b252d05157b2753d2caebae32b11c878504bbe'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root-worktree',required=True,type=Path)
parser.add_argument('--expected-root',required=True)
parser.add_argument('--expected-child',required=True)
parser.add_argument('--baseline-child',required=True,type=Path)
parser.add_argument('--evidence-dir',required=True,type=Path)
args = parser.parse_args()
root, baseline, out = args.root_worktree.resolve(), args.baseline_child.resolve(), args.evidence_dir.resolve()
child = root/'cosmos-framework'
if out.exists() or out.is_relative_to(root) or out.is_relative_to(baseline):
    parser.error('NEW external evidence directory required')
out.mkdir(parents=True)
state = dict(gate='ISSUE28_SCOPED_AUTHOR_CPU_SYNTHETIC_MODEL_ENV_DEVICE_KERNEL', status='BLOCKED', steps=[])
def save(name,value):
    (out/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def git(repo,*argv):
    return subprocess.check_output(['git','-C',str(repo),*argv],text=True).strip()
def identity():
    return dict(root=git(root,'rev-parse','HEAD'),child=git(child,'rev-parse','HEAD'),
        gitlink=git(root,'rev-parse','HEAD:cosmos-framework'),root_status=git(root,'status','--porcelain=v1'),
        child_status=git(child,'status','--porcelain=v1'),baseline_child=git(baseline,'rev-parse','HEAD'),
        baseline_status=git(baseline,'status','--porcelain=v1'))
def fingerprint():
    hashes = {}
    for repo,prefix in [(root,''),(child,'cosmos-framework/')]:
        for name in git(repo,'ls-files').splitlines():
            if (name.startswith(('scripts/','tools/','configs/')) if repo == root else name.startswith('cosmos_framework/')):
                if Path(name).suffix in ('.py','.toml','.yaml','.json'):
                    hashes[prefix+name] = hashlib.sha256((repo/name).read_bytes()).hexdigest()
    return hashes
try:
    for sha in (args.expected_root,args.expected_child):
        if re.fullmatch('[0-9a-f]{40}',sha) is None:
            raise ValueError('full SHA required')
    initial = identity()
    expected = dict(root=args.expected_root,child=args.expected_child,gitlink=args.expected_child,
        root_status='',child_status='',baseline_child=BASE_CHILD,baseline_status='')
    save('identity_before.json',initial)
    if initial != expected:
        raise ValueError('clean exact pair/baseline required')
    if importlib.metadata.version('ruff') != '0.12.7':
        raise ValueError('Ruff0.12.7 required')
    env = dict(os.environ)
    overrides = dict(CUDA_VISIBLE_DEVICES='', LD_LIBRARY_PATH='', COSMOS_DEVICE='cpu',
        OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',
        PYTHONPATH=os.pathsep.join(map(str,(root,child,root/'scripts'))),
        PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTEST_ADDOPTS='',
        HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',
        HF_HOME=str(out/'cache/hf'),XDG_CACHE_HOME=str(out/'cache/xdg'),MPLCONFIGDIR=str(out/'cache/mpl'),
        RUFF_CACHE_DIR=str(out/'cache/ruff'),TRITON_CACHE_DIR=str(out/'cache/triton'))
    env.update(overrides)
    save('environment.json',dict(python=sys.version,platform=platform.platform(),
        packages={n:importlib.metadata.version(n) for n in ('torch','pytest','ruff','numpy','omegaconf')},
        overrides=overrides,tools={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__),Path(__file__).with_name('dense_parity_probe.py'))}))
    before = fingerprint()
    save('source_before.json',before)
    static = []
    for repo,base in [(root,BASE_ROOT),(child,BASE_CHILD)]:
        static.extend(str(repo/n) for n in git(repo,'diff','--name-only',base,'HEAD').splitlines() if n.endswith('.py'))
    save('static_files.json',static)
    def run(name,command,*,cwd=root,environment=env,timeout=300):
        record = dict(name=name,command=command,cwd=str(cwd),timeout_s=timeout)
        state['steps'].append(record)
        state['status'] = 'RUNNING'
        save('gate.json',state)
        start = time.monotonic()
        with (out/(name+'.log')).open('w') as log:
            result = subprocess.run(command,cwd=cwd,env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
        record.update(exit_code=result.returncode,seconds=time.monotonic()-start)
        save('gate.json',state)
        print(name,record['exit_code'],round(record['seconds'],2),flush=True)
        if result.returncode:
            raise RuntimeError(name+' failed; raw log retained')
    run('import_origin',[sys.executable,'-c','import cosmos_framework,torch; print(cosmos_framework.__file__); '
        'print(torch.__version__,torch.version.cuda); assert torch.version.cuda is None; '
        f'assert cosmos_framework.__file__.startswith({str(child)!r})'])
    run('ruff_check',[sys.executable,'-m','ruff','check',*static])
    run('ruff_format',[sys.executable,'-m','ruff','format','--check',*static])
    for filename in static:
        ast.parse(Path(filename).read_text(),filename)
    state['syntax_files'] = len(static)
    c = 'cosmos-framework/cosmos_framework/'
    groups = dict(
        sparse=[c+'inference/robocasa_history_k_test.py',c+'simulation/robocasa/sim_shared_vae_history_k_test.py',
            'tools/v3/eval_v2_batch_tests/history_k_test.py'],
        local_and_transactions=[c+'inference/'+n+'_test.py' for n in ('local_memory_online',
            'robocasa_local_memory_policy','robocasa_feature_evidence','robocasa_batch_transactions',
            'robocasa_dual_mode','robocasa_session_transactions','robocasa_shared_policy_batch')]
            +[c+'simulation/robocasa/eval_v2_transactions_test.py',c+'scripts/robocasa_feature_http_test.py',
                c+'scripts/action_policy_server_robocasa_phase6_test.py'],
        worker_and_sim=[c+'inference/'+n+'_test.py' for n in ('robocasa_vae_protocol','robocasa_vae_worker',
            'robocasa_vae_client','robocasa_vae_daemon')]+[c+'simulation/robocasa/sim_shared_vae_client_test.py'],
        root_topology=['tools/v3/eval_v2_batch_tests/'+n+'_test.py' for n in ('shared_vae','shared_vae_topology',
            'shared_vae_routing','shared_vae_streaming_m16')])
    save('test_scope.json',groups)
    combined = ET.Element('testsuites')
    totals = dict(tests=0,failures=0,errors=0,skipped=0)
    for name,tests in groups.items():
        run(name,[sys.executable,'-m','pytest','--noconftest','-c','/dev/null','--rootdir='+str(root),
            '-p','no:cacheprovider','-o','markers=level: CPU level\ngpus: GPU count',
            '-q','--basetemp='+str(out/(name+'_tmp')),'--junitxml='+str(out/(name+'.xml')),*tests])
        suites = list(ET.parse(out/(name+'.xml')).getroot().iter('testsuite'))
        counts = {key:sum(int(s.attrib.get(key,0)) for s in suites) for key in totals}
        state[name] = counts
        if counts['tests'] == 0 or any(counts[k] for k in ('failures','errors','skipped')):
            raise RuntimeError('zero failures/errors/skips required: '+name)
        combined.extend(suites)
        for key in totals:
            totals[key] += counts[key]
    ET.ElementTree(combined).write(out/'junit.xml',encoding='utf-8',xml_declaration=True)
    probe = Path(__file__).with_name('dense_parity_probe.py')
    for label,repo in [('old',baseline),('new',child)]:
        penv = dict(env,PYTHONPATH=str(repo))
        run('dense_'+label,[sys.executable,str(probe),str(out/('dense_'+label+'.json'))],cwd=repo,environment=penv)
    equal = json.loads((out/'dense_old.json').read_text()) == json.loads((out/'dense_new.json').read_text())
    save('dense_parity.json',dict(bit_equal=equal,baseline_child=BASE_CHILD,new_child=args.expected_child,
        same_probe_sha256=hashlib.sha256(probe.read_bytes()).hexdigest(),real_Wan_DCP_Action=False))
    if not equal:
        raise RuntimeError('default dense K16 bit parity failed')
    after = fingerprint()
    final = identity()
    save('source_after.json',after)
    save('identity_after.json',final)
    if before != after or initial != final:
        raise RuntimeError('source/identity changed during scoped CPU Gate')
    state.update(status='PASS',source_unchanged=True,junit=totals,dense_K16_bit_equal=True,
        no_old900_or965_rerun=True,GPU_Wan_DCP_RoboCasa_SR_training='NOT_RUN',independent_review='NOT_CLAIMED')
except Exception as error:
    state.update(status='FAIL' if state['steps'] else 'BLOCKED',error=repr(error))
    (out/'error_traceback.log').write_text(traceback.format_exc())
save('gate.json',state)
print(json.dumps(state,indent=2),flush=True)
raise SystemExit(0 if state['status']=='PASS' else 1)
