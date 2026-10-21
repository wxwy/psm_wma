import os,json,subprocess,pathlib,hashlib,xml.etree.ElementTree as ET
root=pathlib.Path('/workspace/psm_wma')
out=pathlib.Path('/tmp/psm-v3-high07-20261021/final')
out.mkdir(exist_ok=False)
py='/workspace/.venvs/psm-wma-cpu/bin/python';ruff='/workspace/.venvs/psm-wma-cpu/bin/ruff'
files=['scripts/eval_robocasa_18task_queue.py','tools/v3/eval_robocasa_queue_identity_test.py']
env=os.environ.copy();env.update(PYTHONPATH=str(root/'cosmos-framework')+os.pathsep+str(root/'scripts')+os.pathsep+str(root),CUDA_VISIBLE_DEVICES='',HF_HOME='/workspace/.cache/huggingface',MPLCONFIGDIR='/workspace/.cache/matplotlib',PYTHONPYCACHEPREFIX='/tmp/psm-v3-high07-20261021/pycache',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
commands=[('ruff_check',[ruff,'check','--config','cosmos-framework/.ruff.toml',*files]),('ruff_format',[ruff,'format','--check','--config','cosmos-framework/.ruff.toml',*files]),('syntax',[py,'-m','py_compile',*files]),('pytest',[py,'-m','pytest','--noconftest','-c','/tmp/psm-v3-high07-20261021/pytest.ini','-q','-s','-p','no:cacheprovider',*['tools/v3/eval_robocasa_queue_identity_test.py','tools/v3/remaining_optimizations_test.py'],'-k','queue or identity or screening or evaluation or resume','--junitxml='+str(out/'pytest.xml')]),('diff_check',['git','diff','--check'])]
gate={'scope':'ITER4000_HIGH07_AUTHOR_CPU_ONLY','base_root':'271984989dfd1151180905084c72817f74477e57','child':'2d128ed5a07601cdd424974f99b67832eafeeb41','gpu':False,'real_simulator':False,'production_assets':False,'environment_overrides':{k:env[k] for k in ['PYTHONPATH','CUDA_VISIBLE_DEVICES','HF_HOME','MPLCONFIGDIR','PYTHONPYCACHEPREFIX','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','OMP_NUM_THREADS','MKL_NUM_THREADS']},'commands':[],'author_checks_passed':False}
for name,cmd in commands:
 with (out/(name+'.log')).open('w') as log: result=subprocess.run(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
 gate['commands'].append({'name':name,'command':cmd,'cwd':str(root),'returncode':result.returncode})
 (out/'gate.json').write_text(json.dumps(gate,indent=2)+'\n')
 print(name,result.returncode,flush=True)
 if result.returncode:raise SystemExit(result.returncode)
gate['source_sha256']={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files}
gate['junit']=[item.attrib for item in ET.parse(out/'pytest.xml').iter('testsuite')]
gate['author_checks_passed']=True
(out/'gate.json').write_text(json.dumps(gate,indent=2)+'\n')
print(gate['junit'],flush=True)
