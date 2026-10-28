import hashlib,json,os,subprocess,sys
from pathlib import Path
r=Path('/workspace/psm_wma');b=Path('/tmp/psm-v3-eval-v2-20261028');run=b/sys.argv[1];run.mkdir(exist_ok=False)
files=sorted((r/'tools/v3/episode_eval_v2_prototype').glob('*.py'));h={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',COSMOS_DEVICE='cpu',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(r),OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',HF_HOME=str(b/'cache/hf'),MPLCONFIGDIR=str(b/'cache/mpl'),XDG_CACHE_HOME=str(b/'cache'))
command=[sys.executable,'-m','pytest','--noconftest','-c','/dev/null','--rootdir='+str(r),'-p','no:cacheprovider','-q','-s','-x','tools/v3/episode_eval_v2_prototype','--junitxml='+str(run/'junit.xml')]
(run/'command.json').write_text(json.dumps({'cwd':str(r),'argv':command,'env':{k:env[k] for k in ('CUDA_VISIBLE_DEVICES','COSMOS_DEVICE','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','PYTHONDONTWRITEBYTECODE','PYTHONPATH','OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','HF_HOME','MPLCONFIGDIR','XDG_CACHE_HOME')}},indent=2));(run/'source_sha256.json').write_text(json.dumps(h,indent=2))
with (run/'pytest.log').open('x') as out:p=subprocess.run(command,cwd=r,env=env,stdout=out,stderr=subprocess.STDOUT,timeout=300)
assert all(hashlib.sha256((r/k).read_bytes()).hexdigest()==v for k,v in h.items());(run/'exit.json').write_text(json.dumps({'exit_code':p.returncode,'frozen_sources_unchanged':True}));print(json.dumps({'run':str(run),'exit_code':p.returncode}));raise SystemExit(p.returncode)
