"""Issue27 old-source restriction witnesses; CPU/no checkpoint/network/GPU."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,xml.etree.ElementTree as ET
r=Path('/workspace/work/psm-wma-shared-vae-issue27');c=r/'cosmos-framework'
out=Path('/workspace/work/issue27-shared-vae-evidence/red-old-code-02');out.mkdir(exist_ok=False)
env=os.environ.copy();overrides=dict(CUDA_VISIBLE_DEVICES='',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTEST_ADDOPTS='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONPATH=os.pathsep.join(map(str,(r,c,r/'scripts'))),RUFF_CACHE_DIR=str(out/'cache/ruff'),XDG_CACHE_HOME=str(out/'cache/xdg'));env.update(overrides)
(out/'environment_overrides.json').write_text(json.dumps(overrides,indent=2)+'\n')
tests=[r/'tools/v3/eval_v2_batch_tests/shared_vae_topology_test.py',c/'cosmos_framework/inference/robocasa_shared_policy_batch_test.py'];commands=[]
def run(name,argv):
 with (out/(name+'.log')).open('w') as log:p=subprocess.run(list(map(str,argv)),cwd=r,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 commands.append(dict(name=name,argv=list(map(str,argv)),exit_code=p.returncode));return p.returncode
assert run('ruff_format',[sys.executable,'-m','ruff','format',*tests])==0
assert run('ruff_fix',[sys.executable,'-m','ruff','check','--fix',*tests])==0
before={}
for directory,ref,path in [(r,'e58cef1f53d2382d39c871ce5a50e4acdd5ce268','scripts/robocasa_eval_v2/shared_vae.py'),(c,'b0dbd115d03e801ec4d0788c30ee0b0e9655d4db','cosmos_framework/inference/robocasa_batch_transactions.py')]:
 old=subprocess.check_output(['git','-C',str(directory),'show',ref+':'+path]);assert (directory/path).read_bytes()==old;before[str((directory/path).relative_to(r))]=hashlib.sha256(old).hexdigest()
selections=[('root',[str(tests[0])+'::test_shared_topology_is_config_driven_without_single_measurement_arm','-k','2-8-8']),('child',[str(tests[1])+'::test_feature_policy_batch8_uses_real_ready_peers_and_isolated_prefixes'])]
for name,selection in selections:
 code=run(name,[sys.executable,'-m','pytest','--noconftest','-c','/dev/null','-p','no:cacheprovider','-q',*selection,'--basetemp='+str(out/(name+'_tmp')),'--junitxml='+str(out/(name+'.xml'))]);suite=next(ET.parse(out/(name+'.xml')).getroot().iter('testsuite'));assert code==1 and suite.attrib['failures']=='1' and suite.attrib['errors']=='0'
assert 'single-latency C Run' in (out/'root.log').read_text()
assert 'Policy B1/wait0' in (out/'child.log').read_text()
assert all(hashlib.sha256((r/p).read_bytes()).hexdigest()==v for p,v in before.items())
(out/'result.json').write_text(json.dumps(dict(status='RED_EXPECTED',expected_failures=2,old_production_unchanged=True,source_hashes=before,tests_injected=True,test_hashes={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in tests},commands=commands),indent=2)+'\n');print(json.dumps(dict(status='RED_EXPECTED',failures=2,old_production_unchanged=True)))
