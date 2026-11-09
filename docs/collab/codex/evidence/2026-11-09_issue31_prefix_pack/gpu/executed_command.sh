set -e
BASE31=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_codex_issue31_prefix_pack_20261109
ROOT31="$BASE31/root2"
CKPT31=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/outputs/local_ttt_robocasa_raw15/psm_wma_v3/corrected_phase5/packed128_droid_fresh_g1_20261019
PY31=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/robocasa_sim_venv_20261023/bin/python
cd "$ROOT31"
env CUDA_VISIBLE_DEVICES=GPU-a785be7c-17dc-117c-c6fa-de6ded5c135b LD_LIBRARY_PATH='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONPATH="$ROOT31:$ROOT31/cosmos-framework:$ROOT31/scripts" "$PY31" tools/v3/benchmark_local_ttt_prefix_kv.py --root-worktree "$ROOT31" --expected-root 18be4a80a5ae4d97bc7d287034d24efab847c496 --expected-child 193627f42f4cd1ba6d563aefb8fa8f9428ecb56d --checkpoint "$CKPT31/checkpoints/iter_000015000" --config-file "$CKPT31/config.yaml" --output-dir "$BASE31/gpu02" --gpu-index 6 --optimization prefix_pack --warmup-pairs 3 --pairs 30 --profile-one > "$BASE31/gpu02.log" 2>&1
