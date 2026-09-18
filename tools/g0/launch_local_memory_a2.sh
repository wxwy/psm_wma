#!/usr/bin/env bash
# Bounded, offline A2 smoke/budget launcher. No dependency installation.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CHILD="$ROOT/cosmos-framework"
OUT="${1:?usage: launch_local_memory_a2.sh OUTPUT_DIR MAX_ITER SAVE_ITER [fresh|resume]}"
MAX_ITER="${2:-3}"; SAVE_ITER="${3:-2}"; MODE="${4:-fresh}"
[[ "$OUT" = /* ]] || OUT="$ROOT/$OUT"
[[ "$MAX_ITER" =~ ^[1-9][0-9]*$ && "$SAVE_ITER" =~ ^[1-9][0-9]*$ ]] || exit 2
[[ "$MODE" = fresh || "$MODE" = resume ]] || exit 2
if (( MAX_ITER > 100 )); then
  echo 'This entrypoint is bounded to 100 steps; long-run authorization is separate.' >&2; exit 2
fi
if [[ "$MODE" = fresh && -e "$OUT" ]]; then
  echo "Fresh output already exists; refusing to overwrite: $OUT" >&2; exit 2
fi
[[ -x "$CHILD/.venv/bin/python" ]] || { echo 'Missing existing .venv' >&2; exit 2; }
exec 9>/tmp/psm_wma_chatgpt_a2_gpu.lock
flock -n 9 || { echo 'GPU already held by another A2 run' >&2; exit 2; }
USED="$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1 | tr -d ' ')"
if (( USED >= 512 )); then
  echo "BLOCKED_RESOURCE: GPU has $USED MiB allocated; refusing to compete with another run." >&2
  exit 75
fi
mkdir -p "$OUT"
cd "$CHILD"
export PATH="$CHILD/.venv/bin:$PATH" PYTHONPATH="$CHILD"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 WANDB_MODE=disabled TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}" MKL_NUM_THREADS="${MKL_NUM_THREADS:-4}"
export PYTHONHASHSEED=42
export LIBERO_ROOT="${LIBERO_ROOT:-/disk/rl/data/LIBERO_LeRobot_v3}"
export LIBERO_LATENT_CACHE_ROOT="${LIBERO_LATENT_CACHE_ROOT:-/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1}"
export EDGE_POLICY_CHECKPOINT="${EDGE_POLICY_CHECKPOINT:-/disk/rl/models/Cosmos3-Edge-Policy-DROID}"
export BASE_CHECKPOINT_PATH="${BASE_CHECKPOINT_PATH:-$CHILD/examples/checkpoints/Cosmos3-Edge-Policy-DROID-dcp}"
export WAN_VAE_PATH="${WAN_VAE_PATH:-$CHILD/examples/checkpoints/wan22_vae/Wan2.2_VAE.pth}"
export LIBERO_LATENT_CACHE_VERIFY_RATIO=0 LIBERO_NUM_WORKERS=0 LIBERO_PREFETCH_FACTOR=1
export LIBERO_MAX_EPISODES="${LIBERO_MAX_EPISODES:-10}"
export PSM_R09_B_TTT_TBPTT_STEPS=16
export PSM_R08_LOCAL_HISTORY_ENABLED=1 PSM_R09_B_TTT_ENABLED=1 PSM_R09_B_TTT_ACTIVE=1
export PSM_R09_B_TTT_MEMBER_LAYOUT="${PSM_R09_B_TTT_MEMBER_LAYOUT:-a2}" PSM_R09_B_TTT_B_STREAM="${PSM_R09_B_TTT_B_STREAM:-8}"
export PSM_R09_B_TTT_ACTIVE_GA="${PSM_R09_B_TTT_ACTIVE_GA:-16}"
export PSM_ACTIVE_PREFETCH_DEPTH="${PSM_ACTIVE_PREFETCH_DEPTH:-4}"
export PSM_ACTIVE_METRICS_PATH="$OUT/metrics.jsonl"
if [[ "${PSM_A2_NATIVE_VALIDATION:-0}" = 1 ]]; then
  export PSM_A2_POSTTRAIN_VALIDATION_PATH="$OUT/native_validation.json"
else
  unset PSM_A2_POSTTRAIN_VALIDATION_PATH
fi
export TOML_FILE=examples/toml/sft_config/action_policy_libero_edge_all_localmem_active.toml
export RUN_NAME=edge_libero_4in1_localmem_active
export OUTPUT_ROOT="$OUT" IMAGINAIRE_OUTPUT_ROOT="$OUT"
export NPROC_PER_NODE=1 MASTER_PORT="${MASTER_PORT:-29571}"
export EXTRA_TAIL_OVERRIDES="trainer.max_iter=$MAX_ITER checkpoint.save_iter=$SAVE_ITER trainer.logging_iter=1"
export DISABLE_AUTO_RESUME=1
[[ "$MODE" = fresh ]] || export DISABLE_AUTO_RESUME=0
export A2_LAUNCH_ROOT="$ROOT" A2_LAUNCH_MAX_ITER="$MAX_ITER" A2_LAUNCH_MODE="$MODE"
ATTEMPT="$(date -u +%Y%m%dT%H%M%SZ)"
export A2_LAUNCH_RECORD="$OUT/launch_$ATTEMPT.json"
.venv/bin/python - <<'PY'
import hashlib, json, os, subprocess, sys
from pathlib import Path
root=Path(os.environ['A2_LAUNCH_ROOT']); child=root/'cosmos-framework'
def git(where,*args): return subprocess.check_output(['git',*args],cwd=where,text=True).strip()
names=git(child,'ls-files','cosmos_framework','examples/toml/sft_config/action_policy_libero_edge_all_localmem_active.toml').splitlines()
code={n:hashlib.sha256((child/n).read_bytes()).hexdigest() for n in names if (child/n).is_file()}
record={'root':git(root,'rev-parse','HEAD'),'child':git(child,'rev-parse','HEAD'),'python':sys.version,
        'mode':os.environ['A2_LAUNCH_MODE'],'max_iter':int(os.environ['A2_LAUNCH_MAX_ITER']),
        'tracked_code_sha256':code,'dirty':git(child,'status','--short','--untracked-files=no')}
if record['dirty']:
    raise SystemExit('Commit the isolated code before GPU validation; dirty tracked source refused.')
keys=['LIBERO_ROOT','LIBERO_LATENT_CACHE_ROOT','EDGE_POLICY_CHECKPOINT','BASE_CHECKPOINT_PATH',
      'WAN_VAE_PATH','LIBERO_MAX_EPISODES','PSM_R09_B_TTT_MEMBER_LAYOUT','PSM_R09_B_TTT_B_STREAM',
      'PSM_R09_B_TTT_ACTIVE_GA','PSM_ACTIVE_PREFETCH_DEPTH','OMP_NUM_THREADS','MKL_NUM_THREADS',
      'PSM_R09_B_TTT_ACTIVE','PSM_R09_B_TTT_ENABLED','PSM_R08_LOCAL_HISTORY_ENABLED','EXTRA_TAIL_OVERRIDES','PSM_A2_NATIVE_VALIDATION','PSM_A2_POSTTRAIN_VALIDATION_PATH']
record['environment']={k:os.environ.get(k) for k in keys}
from importlib.metadata import version
record['packages']={k:version(k) for k in ['torch','transformers','numpy','omegaconf','hydra-core']}
inputs={}
for suite in ['libero_10','libero_goal','libero_object','libero_spatial']:
    for base, suffix in [(os.environ['LIBERO_ROOT'],'meta/info.json'),
                         (os.environ['LIBERO_LATENT_CACHE_ROOT'],'dataset_manifest.json')]:
        path=Path(base)/suite/suffix
        if not path.is_file(): raise SystemExit(f'Missing input metadata: {path}')
        inputs[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
record['input_metadata_sha256']=inputs
record['input_binding_scope']='Dataset info and exact-window cache manifests; no claim of full checkpoint-byte hashing.'

Path(os.environ['A2_LAUNCH_RECORD']).write_text(json.dumps(record,indent=2)+'\n')
print('A2 launch identity:',record['root'],record['child'])
PY
set +e
bash examples/launch_sft_action_policy_libero_edge_all.sh > "$OUT/process_$ATTEMPT.log" 2>&1
RC=$?
printf '%s\n' "$RC" > "$OUT/exit_$ATTEMPT.txt"
tail -20 "$OUT/process_$ATTEMPT.log"
exit "$RC"
