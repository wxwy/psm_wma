import os,json,subprocess,pathlib,hashlib,xml.etree.ElementTree as ET
root=pathlib.Path('/workspace/psm_wma/cosmos-framework')
out=pathlib.Path('/tmp/psm-v3-config-truth-20261021/final-r3-lock-aligned');out.mkdir(exist_ok=False)
py='/workspace/.venvs/psm-wma-cpu/bin/python';ruff='/workspace/.venvs/psm-wma-cpu/bin/ruff'
files=['examples/psm_wma_robocasa_corrected_phase5.py','examples/psm_wma_robocasa_effective_config.py','examples/psm_wma_robocasa_effective_config_test.py','examples/psm_wma_robocasa_corrected_phase5_test.py','examples/psm_wma_robocasa_phase5_f0_test.py']
env=os.environ.copy();env.update(PYTHONPATH=str(root),CUDA_VISIBLE_DEVICES='',HF_HOME='/workspace/.cache/huggingface',MPLCONFIGDIR='/workspace/.cache/matplotlib',PYTHONPYCACHEPREFIX='/tmp/psm-v3-config-truth-20261021/pycache',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
commands=[('ruff_check',[ruff,'check',*files]),('ruff_format',[ruff,'format','--check',*files]),('syntax',[py,'-m','py_compile',*files]),('pytest',[py,'/tmp/psm-v3-config-truth-20261021/pytest_cpu.py','--noconftest','-c','/tmp/psm-v3-high07-20261021/pytest.ini','-q','-s','-p','no:cacheprovider','examples/psm_wma_robocasa_effective_config_test.py','examples/psm_wma_robocasa_phase5_f0_test.py','--junitxml='+str(out/'pytest.xml')]),('diff_check',['git','diff','--check'])]
gate={'scope':'FUTURE_PHASE5_CONFIG_TRUTH_AUTHOR_CPU_ONLY','base_child':'2d128ed5a07601cdd424974f99b67832eafeeb41','root_base':'ab1f277e8cec125abeb24b2850eac3e555b47522','gpu':False,'real_server_or_simulator':False,'production_assets':False,'bootstrap':'Only bypass eager unrelated datasets/__init__.py, load original cache/serializers; original contract AST with fixed tokenizer fixture and real Torch CPU','environment_overrides':{k:env[k] for k in ['PYTHONPATH','CUDA_VISIBLE_DEVICES','HF_HOME','MPLCONFIGDIR','PYTHONPYCACHEPREFIX','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','OMP_NUM_THREADS','MKL_NUM_THREADS']},'commands':[],'author_checks_passed':False}
for name,cmd in commands:
 with (out/(name+'.log')).open('w') as log:result=subprocess.run(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
 gate['commands'].append({'name':name,'command':cmd,'cwd':str(root),'returncode':result.returncode});(out/'gate.json').write_text(json.dumps(gate,indent=2)+'\n');print(name,result.returncode,flush=True)
 if result.returncode:raise SystemExit(result.returncode)
gate['source_sha256']={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files}
gate['junit']=[item.attrib for item in ET.parse(out/'pytest.xml').iter('testsuite')];gate['author_checks_passed']=True
(out/'gate.json').write_text(json.dumps(gate,indent=2)+'\n');print(gate['junit'],flush=True)
