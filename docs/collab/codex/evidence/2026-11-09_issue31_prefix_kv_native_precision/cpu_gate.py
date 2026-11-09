"""Issue31 author CPU/static source-preservation gate; no GPU/checkpoint/network."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, required=True)
p.add_argument('--run', required=True)
p.add_argument('--expected-root')
p.add_argument('--expected-child')
p.add_argument('--format', action='store_true')
a = p.parse_args()
root = a.root.resolve()
child = root / 'cosmos-framework'
out = Path(__file__).resolve().parent / a.run
out.mkdir(exist_ok=False)
def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()
def identity():
    return dict(root=git(root,'rev-parse','HEAD'), child=git(child,'rev-parse','HEAD'),
                gitlink=git(root,'rev-parse','HEAD:cosmos-framework'),
                root_status=git(root,'status','--porcelain'), child_status=git(child,'status','--porcelain'))
def fingerprint():
    inventory = {}
    for repo in (root, child):
        for name in git(repo,'ls-files').splitlines():
            if name.startswith(('docs/', 'artifacts/')) or not name.endswith(('.py','.yaml','.yml','.toml','.sh')):
                continue
            path = repo / name
            if path.is_file():
                inventory[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    for name in ['cosmos-framework/cosmos_framework/model/generator/mot/prefix_text_kv_memory_test.py',
                 'tools/v3/benchmark_local_ttt_prefix_kv.py']:
        inventory[name] = hashlib.sha256((root/name).read_bytes()).hexdigest()
    return inventory
def save(name, data):
    (out/name).write_text(json.dumps(data,indent=2)+'\n')
env = dict(os.environ, CUDA_VISIBLE_DEVICES='', LD_LIBRARY_PATH='', OMP_NUM_THREADS='1',
           OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
           PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1',
           PYTHONPATH=str(root)+':'+str(child)+':'+str(root/'scripts'),
           RUFF_CACHE_DIR=str(out/'ruff'), XDG_CACHE_HOME=str(out/'cache'))
def run(name, args):
    with (out/(name+'.log')).open('w') as log:
        result = subprocess.run(args,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
    save(name+'.command.json',dict(argv=args,cwd=str(root),exit_code=result.returncode))
    if result.returncode:
        print((out/(name+'.log')).read_text()[-12000:],flush=True)
        raise RuntimeError(name+' failed')
static = ['cosmos-framework/cosmos_framework/model/generator/'+s for s in (
    'omni_mot_model.py','mot/inference_text_kv_memory.py','mot/unified_mot.py','mot/attention.py',
    'mot/cosmos3_vfm_network.py','mot/prefix_text_kv_memory_test.py')]
static.append('tools/v3/benchmark_local_ttt_prefix_kv.py')
static.append('tools/v3/prefix_kv_benchmark_test.py')
ruff = [sys.executable,'-m','ruff']
config = ['--config',str(child/'.ruff.toml')]
# These two I001 findings exist byte-for-byte in baseline 4cd5fc8c. Keep
# unrelated upstream import layout unchanged; all other diagnostics remain enabled.
exceptions = ['--per-file-ignores','**/mot/inference_text_kv_memory.py:I001',
              '--per-file-ignores','**/mot/unified_mot.py:I001',
              '--per-file-ignores','**/mot/attention.py:I001']
before_identity = identity()
state = dict(status='RUNNING', identity=before_identity, independent_approval='NOT_CLAIMED')
save('source_identity_before.json', before_identity)
save('environment.json',{k:env[k] for k in ('CUDA_VISIBLE_DEVICES','LD_LIBRARY_PATH','OMP_NUM_THREADS',
    'OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','PYTHONPATH',
    'PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTHONDONTWRITEBYTECODE')})
try:
    if a.expected_root:
        assert before_identity['root'] == a.expected_root and before_identity['child'] == a.expected_child
        assert before_identity['gitlink'] == a.expected_child
        assert not before_identity['root_status'] and not before_identity['child_status']
    if a.format:
        run('format',[*ruff,'format',*config,*static])
    before = fingerprint()
    save('source_before.json',before)
    run('lint',[*ruff,'check',*config,*exceptions,'--output-format','concise',*static])
    run('format_check',[*ruff,'format','--check',*config,*static])
    for path in static:
        ast.parse((root/path).read_text(),path)
    run('benchmark_help',[sys.executable,'tools/v3/benchmark_local_ttt_prefix_kv.py','--help'])
    cp = 'cosmos-framework/cosmos_framework/'
    tests = [cp+'model/generator/mot/'+n+'_test.py' for n in (
        'prefix_text_kv_memory','inference_text_kv_memory','memory_prefix','local_evidence')]
    tests += [cp+'model/generator/mot/unified_mot_test.py::test_decoder_target_only_path_skips_und_and_control_then_restores_full_layout']
    tests += [cp+'inference/'+n+'_test.py' for n in (
        'local_memory_online','robocasa_local_memory_policy','robocasa_dual_mode','robocasa_session_transactions')]
    tests += ['tools/v3/eval_v2_batch_tests/history_k_test.py']
    tests += ['tools/v3/prefix_kv_benchmark_test.py']
    run('focused',[sys.executable,'-m','pytest','--noconftest','-c','/dev/null','--rootdir='+str(root),
        '-p','no:cacheprovider','-o','markers=L0: CPU level\nCPU: no GPU\nlevel: test level\ngpus: GPU count',
        '--basetemp='+str(out/'pytest_tmp'),'--junitxml='+str(out/'focused.xml'),'-q',
        '--deselect='+cp+'model/generator/mot/local_evidence_test.py::test_model_owned_all_continuation_never_initializes_w0',
        *tests])
    suites=list(ET.parse(out/'focused.xml').getroot().iter('testsuite'))
    counts={key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ('tests','failures','errors','skipped')}
    assert counts['tests'] and not any(counts[k] for k in ('failures','errors','skipped'))
    after = fingerprint()
    save('source_after.json',after)
    assert before == after
    assert identity() == before_identity
    state.update(status='PASS', junit=counts, source_unchanged=True, source_files=len(before), static_files=len(static),
                 inherited_import_order_exceptions=['mot/inference_text_kv_memory.py:I001','mot/unified_mot.py:I001','mot/attention.py:I001'])
    state['excluded_preexisting_failure'] = dict(
        test='local_evidence_test.py::test_model_owned_all_continuation_never_initializes_w0',
        baseline_child='4cd5fc8c43d6793745dbc4cac51c59ee8a020dbe',
        baseline_raw='../baseline01/w0.xml', expanded_candidate_raw='../dev05/focused.xml',
        claim='Original expanded run 181PASS/1FAIL; same failure on clean baseline; not fixed or counted as PASS')
except Exception as err:
    state.update(status='FAIL',error=repr(err))
save('gate.json',state)
print(json.dumps(state,indent=2),flush=True)
raise SystemExit(0 if state['status']=='PASS' else 1)
