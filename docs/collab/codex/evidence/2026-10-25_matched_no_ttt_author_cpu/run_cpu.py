import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path('/workspace/psm_wma')
child = root / 'cosmos-framework'
base = Path('/tmp/psm-v3-matched-no-ttt-20261025')
run = base / sys.argv[1]
run.mkdir(exist_ok=False)
tests = [
    'cosmos_framework/trainer/matched_no_ttt_test.py',
    'examples/psm_wma_robocasa_matched_no_ttt_test.py',
    '../tools/v3/matched_no_ttt_entry_test.py',
    'examples/psm_wma_robocasa_corrected_phase5_test.py',
    'examples/psm_wma_robocasa_phase5_f0_test.py',
    'examples/psm_wma_robocasa_effective_config_test.py',
    'cosmos_framework/trainer/local_memory_grouped_test.py',
    'cosmos_framework/trainer/local_memory_grouped_resume_test.py',
    'cosmos_framework/model/generator/mot/local_memory_grouped_window_test.py',
    'cosmos_framework/model/generator/mot/robocasa_exact_window_local_test.py',
    'examples/psm_wma_robocasa_corrected_telemetry_test.py',
    '../tools/v3/remaining_optimizations_test.py',
    'examples/psm_wma_robocasa_native_test.py',
    'cosmos_framework/inference/robocasa_local_memory_policy_test.py',
    'cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft_test.py',
    'cosmos_framework/model/generator/omni_mot_cached_vision_test.py',
]
assert len(tests) == len(set(tests)) == 16
env = dict(os.environ, CUDA_VISIBLE_DEVICES='', COSMOS_DEVICE='cpu', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
    OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1',
    HF_HOME=str(base/'cache/hf'), MPLCONFIGDIR=str(base/'cache/mpl'), XDG_CACHE_HOME=str(base/'cache'),
    TRITON_CACHE_DIR=str(base/'cache/triton'), WANDB_MODE='disabled',
    PYTHONPATH=os.pathsep.join([str(child), str(root/'scripts'), str(root/'tools/v3')]))
for key in ('RANK', 'WORLD_SIZE', 'LOCAL_RANK', 'LOCAL_WORLD_SIZE', 'MASTER_ADDR', 'MASTER_PORT'):
    env.pop(key, None)
command = [sys.executable, '-m', 'pytest', '--noconftest', '-c', '/dev/null', '-p', 'no:cacheprovider', '-q',
           '-o', 'markers=level:CPU contract', *tests, '--junitxml='+str(run/'junit.xml')]
(run/'command.json').write_text(json.dumps({'cwd': str(child), 'argv': command,
    'env': {key:env[key] for key in ('CUDA_VISIBLE_DEVICES','COSMOS_DEVICE','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE',
    'OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','PYTHONDONTWRITEBYTECODE','HF_HOME','MPLCONFIGDIR',
    'XDG_CACHE_HOME','TRITON_CACHE_DIR','WANDB_MODE','PYTHONPATH')}},indent=2))
paths = [child/p for p in tests]
paths += [child/p for p in ('cosmos_framework/trainer/matched_no_ttt.py',
    'examples/psm_wma_robocasa_matched_no_ttt.py', 'examples/psm_wma_robocasa_corrected_phase5.py',
    'examples/psm_wma_robocasa_effective_config.py','cosmos_framework/utils/training_audit.py')]
paths += [root/p for p in ('scripts/train_v3_matched_no_ttt.sh','scripts/serve_v3_matched_no_ttt.py',
    'configs/eval/robocasa_matched_no_ttt.example.yaml')]
hashes={str(p.resolve().relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
(run/'source_sha256.json').write_text(json.dumps(hashes,indent=2))
with (run/'pytest.log').open('x') as out:
    result = subprocess.run(command, cwd=child, env=env, stdout=out, stderr=subprocess.STDOUT, timeout=900)
assert hashes == {str(p.resolve().relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
(run/'exit.json').write_text(json.dumps({'exit_code':result.returncode, 'frozen_sources_unchanged':True}))
print(json.dumps({'run': str(run), 'exit_code':result.returncode}),flush=True)
raise SystemExit(result.returncode)
