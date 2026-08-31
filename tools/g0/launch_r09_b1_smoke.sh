#!/usr/bin/env bash
# R09-B1-G 的两阶段、单卡、可审计启动契约；默认执行，DRY_RUN=1 仅打印。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FRAMEWORK="$ROOT/cosmos-framework"
PYTHON="$FRAMEWORK/.venv/bin/python"
VENV_BIN="$FRAMEWORK/.venv/bin"
: "${LIBERO_ROOT:=/disk/rl/data/LIBERO_LeRobot_v3}"
: "${LIBERO_LATENT_CACHE_ROOT:=/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1}"
: "${WAN_VAE_PATH:=$FRAMEWORK/examples/checkpoints/wan22_vae/Wan2.2_VAE.pth}"
: "${R09_B1_WORK_ROOT:=/localdisk-tmp/r09-b1-gpu-smoke}"
ARTIFACT_ROOT="$ROOT/artifacts/g0/r09/b1"
GATE_A_ROOT="$R09_B1_WORK_ROOT/gate_a_rebuilt"
B1_ROOT="$R09_B1_WORK_ROOT/b1_ttt"
GATE_A_CHECKPOINT="$GATE_A_ROOT/cosmos3_action_libero/action_sft/edge_libero_4in1/checkpoints/iter_000000002"
B1_CHECKPOINT="$B1_ROOT/cosmos3_action_libero/action_sft/edge_libero_4in1/checkpoints/iter_000000005"
GATE_A_LOG="$GATE_A_ROOT/logs/action_policy_libero_edge_all_sft.log"
B1_LOG="$B1_ROOT/logs/action_policy_libero_edge_all_sft.log"
GATE_A_SIDECAR="$ARTIFACT_ROOT/gate_a_rebuild_d005.json"
B1_SIDECAR="$ARTIFACT_ROOT/b1_smoke_d005.json"
B1_PROBE="$ARTIFACT_ROOT/runtime_probe.json"
GATE_A_SMOKE_PROFILE="smoke_batch1_gate_a"
GATE_A_SMOKE_PROFILE_MAX_SAMPLES=1
GATE_A_SMOKE_PROFILE_GRAD_ACCUM=1
B1_SMOKE_PROFILE="smoke_batch2_b1"
B1_SMOKE_PROFILE_MAX_SAMPLES=2
B1_SMOKE_PROFILE_GRAD_ACCUM=1
GPU_NAME="$(/usr/bin/nvidia-smi --query-gpu=name --format=csv,noheader | /usr/bin/head -n 1)"
GPU_TOTAL_MEMORY_MIB="$(/usr/bin/nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | /usr/bin/head -n 1 | /usr/bin/tr -d ' ')"
[[ "$GPU_NAME" == *"A100"* && "$GPU_TOTAL_MEMORY_MIB" -ge 80000 ]] || { echo "需要 A100-80GB，实际为 $GPU_NAME / ${GPU_TOTAL_MEMORY_MIB}MiB" >&2; exit 1; }

readonly -a UNSET_ENV=(
    PSM_R09_A1_PROBE_OUTPUT PSM_R07_RUNTIME_PROBE_OUTPUT PSM_R07_PARITY_OUTPUT
    PSM_R07_PARITY_TENSOR_OUTPUT PSM_R08_GATE_A_PROBE_OUTPUT
    PSM_R08_GATE_B_PROVENANCE_OUTPUT ONLINE_VAE_PROBE_OUTPUT LIBERO_MAX_EPISODES
)

run_phase() {
    local phase="$1" input_checkpoint="$2" output_root="$3" output_checkpoint="$4"
    local log_file="$5" sidecar="$6" expected_steps="$7" b1_enabled="$8" probe="$9" profile="${10}" max_samples="${11}" grad_accum="${12}" history_evidence="${13}"
    local overrides="trainer.max_iter=${expected_steps} trainer.logging_iter=1 checkpoint.save_iter=${expected_steps} checkpoint.load_training_state=False dataloader_train.max_samples_per_batch=${max_samples} trainer.grad_accum_iter=${grad_accum}"
    local -a command=(env)
    local name
    for name in "${UNSET_ENV[@]}"; do command+=(-u "$name"); done
    command+=(
        "PATH=$VENV_BIN:$PATH" "CUDA_VISIBLE_DEVICES=0"
        "NPROC_PER_NODE=1" "PSM_R08_LOCAL_HISTORY_ENABLED=1" "PSM_R08_LOCAL_HISTORY_HORIZON=16"
        "PSM_LOCAL_DUMMY_ENABLED=0" "PSM_LOCAL_DUMMY_DIM=32" "PSM_LOCAL_DUMMY_MODE=normal"
        "PSM_R08_HISTORY_MODE=normal" "PSM_R09_A1_ENABLED=0" "PSM_R08_GATE_B_CAPTURE_ONLY=0"
        "LIBERO_ROOT=$LIBERO_ROOT" "LIBERO_LATENT_CACHE_ROOT=$LIBERO_LATENT_CACHE_ROOT"
        "LIBERO_LATENT_CACHE_VERIFY_RATIO=0" "LIBERO_NUM_WORKERS=0" "LIBERO_PREFETCH_FACTOR=4"
        "PSM_R09_B1_TTT_ENABLED=$b1_enabled" "PSM_R09_B1_PROBE_OUTPUT=$probe"
        "BASE_CHECKPOINT_PATH=$input_checkpoint" "OUTPUT_ROOT=$output_root" "DISABLE_AUTO_RESUME=1"
        "EXTRA_TAIL_OVERRIDES=$overrides" bash examples/launch_sft_action_policy_libero_edge_all.sh
    )
    local resolved_command
    printf -v resolved_command '%q ' "${command[@]}"
    local command_argv_json
    command_argv_json="$("$PYTHON" -c 'import json, sys; print(json.dumps(sys.argv[1:]))' "${command[@]}")"
    "$PYTHON" "$ROOT/tools/g0/write_r09_b1_d005.py" \
        --root "$ROOT" --phase "$phase" --output "$sidecar" --command "$resolved_command" --command-argv-json "$command_argv_json" \
        --checkpoint "$input_checkpoint" --libero-root "$LIBERO_ROOT" --cache-root "$LIBERO_LATENT_CACHE_ROOT" \
        --run-root "$output_root" --log "$log_file" --output-checkpoint "$output_checkpoint" \
        --probe "$probe" --expected-steps "$expected_steps" --gpu-name "$GPU_NAME" --gpu-total-memory-mib "$GPU_TOTAL_MEMORY_MIB" --path "$VENV_BIN:$PATH" \
        --profile "$profile" --profile-max-samples "$max_samples" --profile-grad-accum "$grad_accum" --history-evidence "$history_evidence"
    printf 'R09_B1_RESOLVED_COMMAND phase=%s: %s\n' "$phase" "$resolved_command"
    if [[ "${DRY_RUN:-0}" == "1" ]]; then return; fi
    (cd "$FRAMEWORK" && "${command[@]}")
}

write_b1_history_evidence() {
    local overrides="trainer.max_iter=5 trainer.logging_iter=1 checkpoint.save_iter=5 checkpoint.load_training_state=False dataloader_train.max_samples_per_batch=${B1_SMOKE_PROFILE_MAX_SAMPLES} trainer.grad_accum_iter=${B1_SMOKE_PROFILE_GRAD_ACCUM}"
    local -a command=(env)
    local name
    for name in "${UNSET_ENV[@]}"; do command+=(-u "$name"); done
    command+=(
        "PATH=$VENV_BIN:$PATH" "CUDA_VISIBLE_DEVICES=0"
        "NPROC_PER_NODE=1" "PSM_R08_LOCAL_HISTORY_ENABLED=1" "PSM_R08_LOCAL_HISTORY_HORIZON=16"
        "PSM_LOCAL_DUMMY_ENABLED=0" "PSM_LOCAL_DUMMY_DIM=32" "PSM_LOCAL_DUMMY_MODE=normal"
        "PSM_R08_HISTORY_MODE=normal" "PSM_R09_A1_ENABLED=0" "PSM_R08_GATE_B_CAPTURE_ONLY=0"
        "LIBERO_ROOT=$LIBERO_ROOT" "LIBERO_LATENT_CACHE_ROOT=$LIBERO_LATENT_CACHE_ROOT"
        "LIBERO_LATENT_CACHE_VERIFY_RATIO=0" "LIBERO_NUM_WORKERS=0" "LIBERO_PREFETCH_FACTOR=4"
        "PSM_R09_B1_TTT_ENABLED=1" "PSM_R09_B1_PROBE_OUTPUT=$B1_PROBE"
        "BASE_CHECKPOINT_PATH=$GATE_A_CHECKPOINT" "WAN_VAE_PATH=$WAN_VAE_PATH" "OUTPUT_ROOT=$B1_ROOT" "DISABLE_AUTO_RESUME=1"
        "EXTRA_TAIL_OVERRIDES=$overrides"
    )
    "${command[@]}" "$PYTHON" "$ROOT/tools/g0/verify_r09_b1_first_batch_history.py" \
        --root "$ROOT" --output "$ARTIFACT_ROOT/b1_first_batch_history.json" --overrides "$overrides"
}

mkdir -p "$ARTIFACT_ROOT"
run_phase gate_a_rebuild "$FRAMEWORK/examples/checkpoints/Cosmos3-Edge-Policy-DROID-dcp" "$GATE_A_ROOT" "$GATE_A_CHECKPOINT" "$GATE_A_LOG" "$GATE_A_SIDECAR" 2 0 "" "$GATE_A_SMOKE_PROFILE" "$GATE_A_SMOKE_PROFILE_MAX_SAMPLES" "$GATE_A_SMOKE_PROFILE_GRAD_ACCUM" ""
[[ "${DRY_RUN:-0}" == "1" ]] && exit 0
[[ -d "$GATE_A_CHECKPOINT/model" ]] || { echo "缺少 Gate-A-compatible rebuilt checkpoint: $GATE_A_CHECKPOINT" >&2; exit 1; }
write_b1_history_evidence
run_phase b1_smoke "$GATE_A_CHECKPOINT" "$B1_ROOT" "$B1_CHECKPOINT" "$B1_LOG" "$B1_SIDECAR" 5 1 "$B1_PROBE" "$B1_SMOKE_PROFILE" "$B1_SMOKE_PROFILE_MAX_SAMPLES" "$B1_SMOKE_PROFILE_GRAD_ACCUM" "$ARTIFACT_ROOT/b1_first_batch_history.json"
[[ "${DRY_RUN:-0}" == "1" ]] && exit 0
"$PYTHON" "$ROOT/tools/g0/verify_r09_b1_smoke.py" \
    --root "$ROOT" --initial-checkpoint "$GATE_A_CHECKPOINT" --final-checkpoint "$B1_CHECKPOINT" \
    --gate-a-log "$GATE_A_LOG" --log "$B1_LOG" --probe "$B1_PROBE" \
    --gate-a-sidecar "$GATE_A_SIDECAR" --training-sidecar "$B1_SIDECAR" \
    --expected-root-revision "$(git -C "$ROOT" rev-parse HEAD)" \
    --expected-submodule-revision "$(git -C "$FRAMEWORK" rev-parse HEAD)" \
    --expected-gitlink-revision "$(git -C "$ROOT" ls-tree HEAD cosmos-framework | awk '{print $3}')" \
    --output "$ARTIFACT_ROOT/smoke_contract.json"
