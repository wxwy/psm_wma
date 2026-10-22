import os,json,subprocess,pathlib,hashlib,xml.etree.ElementTree as ET
root=pathlib.Path('/workspace/psm_wma/cosmos-framework');parent=root.parent
out=pathlib.Path('/tmp/psm-v3-g1-cross-pair-20261022/final-r1');out.mkdir(exist_ok=False)
py='/workspace/.venvs/psm-wma-cpu/bin/python';ruff='/workspace/.venvs/psm-wma-cpu/bin/ruff'
files=['examples/psm_wma_robocasa_corrected_phase5.py','examples/psm_wma_robocasa_g1_cross_pair_resume_test.py']
env=os.environ.copy();env.update(PYTHONPATH=str(root),CUDA_VISIBLE_DEVICES='',HF_HOME='/workspace/.cache/huggingface',MPLCONFIGDIR='/workspace/.cache/matplotlib',PYTHONPYCACHEPREFIX='/tmp/psm-v3-g1-cross-pair-20261022/pycache',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
commands=[('ruff_check',[ruff,'check',*files]),('ruff_format',[ruff,'format','--check',*files]),('syntax',[py,'-m','py_compile',*files]),('shell',['bash','-n',str(parent/'scripts/train_v3_packed128_staged.sh')]),('pytest',[py,'/tmp/psm-v3-g1-cross-pair-20261022/pytest_cpu.py','--noconftest','-c','/tmp/psm-v3-g1-cross-pair-20261022/pytest.ini','-q','-s','-p','no:cacheprovider',*['examples/psm_wma_robocasa_g1_cross_pair_resume_test.py','examples/psm_wma_robocasa_phase5_f0_test.py','examples/psm_wma_robocasa_effective_config_test.py'],'--junitxml='+str(out/'pytest.xml')]),('child_diff',['git','diff','--check']),('root_diff',['git','-C',str(parent),'diff','--check'])]
gate={'scope':'G1_ITER8900_OWNER_CROSS_PAIR_RESUME_AUTHOR_CPU_ONLY','base_root':'1fc28effe9e33a2e6522f6ffe60c55c68f8b367c','base_child':'35b0ea1ccee9ee26653ed6589c484f0997d1c586','gpu':False,'production_assets':False,'real_dcp':False,'bootstrap':'Only isolate eager unrelated Dataset registry. Original CPU Local restore/planner/state class bodies, small core dimensions, real Torch; no model/CUDA import factory.','environment_overrides':{k:env[k] for k in ['PYTHONPATH','CUDA_VISIBLE_DEVICES','HF_HOME','MPLCONFIGDIR','PYTHONPYCACHEPREFIX','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','OMP_NUM_THREADS','MKL_NUM_THREADS']},'commands':[],'author_checks_passed':False}
for name,cmd in commands:
 with (out/(name+'.log')).open('w') as log:result=subprocess.run(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
 gate['commands'].append({'name':name,'command':cmd,'cwd':str(root),'returncode':result.returncode});(out/'gate.json').write_text(json.dumps(gate,indent=2)+'\n');print(name,result.returncode,flush=True)
 if result.returncode:raise SystemExit(result.returncode)
gate['child_source_sha256']={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in files}
gate['root_source_sha256']={'scripts/train_v3_packed128_staged.sh':hashlib.sha256((parent/'scripts/train_v3_packed128_staged.sh').read_bytes()).hexdigest()}
gate['junit']=[item.attrib for item in ET.parse(out/'pytest.xml').iter('testsuite')];gate['author_checks_passed']=True
(out/'gate.json').write_text(json.dumps(gate,indent=2)+'\n');print(gate['junit'],flush=True)
