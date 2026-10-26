import hashlib,json,os,subprocess,sys
from pathlib import Path
r=Path('/workspace/psm_wma');base=Path('/tmp/psm-v3-nottt-b1-20261026');run=base/sys.argv[1];run.mkdir(exist_ok=True)
assert not (run/'pytest.log').exists()
p=r/'tools/v3/no_ttt_legacy_worker0_resume_test.py';digest=hashlib.sha256(p.read_bytes()).hexdigest();(run/'test_source.py').write_bytes(p.read_bytes())
env=dict(os.environ,NOTTT_B1_EVIDENCE_ROOT=str(run/'fixtures'),CUDA_VISIBLE_DEVICES='',COSMOS_DEVICE='cpu',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',HF_HOME=str(base/'cache/hf'),MPLCONFIGDIR=str(base/'cache/mpl'),XDG_CACHE_HOME=str(base/'cache'),TRITON_CACHE_DIR=str(base/'cache/triton'),PYTHONDONTWRITEBYTECODE='1',WANDB_MODE='disabled')
command=[sys.executable,'-m','pytest','--noconftest','-c','/dev/null','--rootdir='+str(r),'-p','no:cacheprovider','-q','-s','-x',str(p),'--junitxml='+str(run/'junit.xml')]
(run/'command.json').write_text(json.dumps({'cwd':str(r),'argv':command,'environment':{k:env[k] for k in ('NOTTT_B1_EVIDENCE_ROOT','CUDA_VISIBLE_DEVICES','COSMOS_DEVICE','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','HF_HOME','MPLCONFIGDIR','XDG_CACHE_HOME','TRITON_CACHE_DIR','PYTHONDONTWRITEBYTECODE','WANDB_MODE')},'test_sha256':digest},indent=2))
with (run/'pytest.log').open('x') as out:result=subprocess.run(command,cwd=r,env=env,stdout=out,stderr=subprocess.STDOUT,timeout=600)
assert hashlib.sha256(p.read_bytes()).hexdigest()==digest
(run/'exit.json').write_text(json.dumps({'exit_code':result.returncode,'test_source_unchanged':True}))
print(json.dumps({'run':str(run),'exit_code':result.returncode}));raise SystemExit(result.returncode)
