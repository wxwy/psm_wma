import hashlib,json,os,subprocess,sys
from pathlib import Path
root=Path('/workspace/psm_wma');base=Path('/tmp/psm-v3-eval-cache-20261027');run=base/sys.argv[1];run.mkdir(exist_ok=True)
tests=sys.argv[2:] or ['tools/v3/robocasa_input_verification_test.py','tools/v3/robocasa_input_verification_cli_test.py','tools/v3/robocasa_resume_store_test.py','tools/v3/robocasa_resume_components_test.py','tools/v3/robocasa_eval_config_test.py']
source=['scripts/robocasa_episode_resume/model_identity.py','scripts/robocasa_resume_store.py','scripts/robocasa_resume_cli.py','scripts/robocasa_input_verification.py','scripts/v3_evaluation_identity.py']
hashes={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in source+tests}
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',COSMOS_DEVICE='cpu',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',HF_HOME=str(base/'cache/hf'),MPLCONFIGDIR=str(base/'cache/mpl'),XDG_CACHE_HOME=str(base/'cache'),PYTHONPATH=str(root/'scripts')+os.pathsep+str(root))
command=[sys.executable,'-m','pytest','--noconftest','-c','/dev/null','--rootdir='+str(root),'-p','no:cacheprovider','-q','-s','-x',*tests,'--junitxml='+str(run/'junit.xml')]
(run/'command.json').write_text(json.dumps({'cwd':str(root),'argv':command,'env':{k:env[k] for k in ('CUDA_VISIBLE_DEVICES','COSMOS_DEVICE','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','PYTHONDONTWRITEBYTECODE','HF_HOME','MPLCONFIGDIR','XDG_CACHE_HOME','PYTHONPATH')}},indent=2));(run/'source_sha256.json').write_text(json.dumps(hashes,indent=2))
with (run/'pytest.log').open('x') as out: result=subprocess.run(command,cwd=root,env=env,stdout=out,stderr=subprocess.STDOUT,timeout=600)
assert hashes=={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in hashes}
(run/'exit.json').write_text(json.dumps({'exit_code':result.returncode,'frozen_sources_unchanged':True}));print(json.dumps({'run':str(run),'exit_code':result.returncode}));raise SystemExit(result.returncode)
