import os,sys,json,hashlib,subprocess,time
from pathlib import Path
root=Path('/workspace/psm_wma'); out=Path('/tmp/psm-v3-eval-v2-r2-20261028')/sys.argv[1];out.mkdir(parents=True,exist_ok=False)
files=sorted(root.glob('tools/v3/episode_eval_v2_prototype/*.py'))
source={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
env=os.environ.copy(); env.update(CUDA_VISIBLE_DEVICES='',COSMOS_DEVICE='cpu',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(root),HF_HOME='/tmp/psm-v3-eval-v2-r2-20261028/cache/hf',MPLCONFIGDIR='/tmp/psm-v3-eval-v2-r2-20261028/cache/mpl',XDG_CACHE_HOME='/tmp/psm-v3-eval-v2-r2-20261028/cache')
argv=['/workspace/.venvs/psm-wma-cpu/bin/python','-m','pytest','--noconftest','-c','/dev/null','--rootdir='+str(root),'-p','no:cacheprovider','-q','-s','-x',*sys.argv[2:],'--junitxml='+str(out/'junit.xml')]
(out/'command.json').write_text(json.dumps({'argv':argv,'cwd':str(root),'timeout_seconds':600,'environment':{k:env[k] for k in ['CUDA_VISIBLE_DEVICES','COSMOS_DEVICE','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','PYTHONDONTWRITEBYTECODE','PYTHONPATH','HF_HOME','MPLCONFIGDIR','XDG_CACHE_HOME']}},indent=2))
(out/'source_sha256.json').write_text(json.dumps(source,indent=2));start=time.monotonic()
with (out/'pytest.log').open('w') as log:
    try:
        r=subprocess.run(argv,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600);code=r.returncode
    except subprocess.TimeoutExpired:code=124
result={'exit_code':code,'wall_seconds':time.monotonic()-start,'frozen_sources':source=={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(out/'exit.json').write_text(json.dumps(result));print(json.dumps(result));print((out/'pytest.log').read_text()[-9500:]);sys.exit(code)
