#!/usr/bin/env bash
# 13-ckpt smoke sweep 完成后的一键触发器。
#
# 本次调用会依次：
#   1. 校验所有 smoke .done（默认 13 个：iter_2600 → iter_200，不含 2800）
#   2. 汇总跨 iter × suite SR 趋势 → artifacts/g0/13ckpt_smoke_summary.json
#                                 + artifacts/g0/13ckpt_smoke_summary.md
#   3. 触发 libero_90 cache build（后台 nohup + sentinel 幂等）
#   4. 打印后续计划提示：
#        - libero_90 cache merge
#        - HF upload #32（待仓库拍板，不自动）
#        - canonical R06 baseline #21（待用户授权，不自动）
#
# 幂等：完成一次后写 artifacts/g0/.post_smoke_done.lock；重复调用会跳过。
# 若只想跑某一步，传 PHASE=summary|build|todo 单独执行。
set -uo pipefail

REPO_ROOT="/disk/rl/psm_wma"
COSMOS_ROOT="$REPO_ROOT/cosmos-framework"
RESULTS_ROOT="${RESULTS_ROOT:-$COSMOS_ROOT/results/libero_closed_loop_4in1_acceptance_4090_smoke_v1}"
ARTIFACTS="$REPO_ROOT/artifacts/g0"
LOCK="$ARTIFACTS/.post_smoke_done.lock"
PHASE="${PHASE:-all}"

CKPT_ITERS_DEFAULT=(2600 2400 2200 2000 1800 1600 1400 1200 1000 800 600 400 200)
REQUIRED_SUITES=(libero_spatial libero_object libero_goal libero_10)
# iter_2800 是 10-trial acceptance（acceptance_4090 父目录），按 MP4 后缀真值
# 单独放最上面，标 trials=10，与下方 1-trial smoke 数据明确区分
EXTRA_TOP_ROWS='[{"iter": 2800, "label": "iter_2800 (10-trial acceptance)", "trials": 10, "spatial": 0.96, "object": 0.99, "goal": 0.76, "libero_10": 0.58, "_4in1_avg": 0.8225, "_source": "libero_closed_loop_4in1_acceptance_4090，按 MP4 _success/_fail 后缀"}]'

log() { echo "[$(date '+%F %T')] [auto-post-smoke] $*"; }

mkdir -p "$ARTIFACTS"

summarize_smoke() {
  local out_json="$ARTIFACTS/13ckpt_smoke_summary.json"
  local out_md="$ARTIFACTS/13ckpt_smoke_summary.md"
  log "汇总跨 iter × suite SR → $out_json"
  "$COSMOS_ROOT/.venv/bin/python" - "$RESULTS_ROOT" "$out_json" "$out_md" "${CKPT_ITERS_DEFAULT[@]}" <<'PY'
import json
import sys
from pathlib import Path

results_root = Path(sys.argv[1])
out_json = Path(sys.argv[2])
out_md = Path(sys.argv[3])
iters = [int(x) for x in sys.argv[4:]]
suites = ["libero_spatial", "libero_object", "libero_goal", "libero_10"]

table = {}
for it in iters:
    iter_dir = results_root / f"iter_{it:09d}"
    row = {"iter": it, "present": iter_dir.is_dir()}
    for s in suites:
        p = iter_dir / s / "summary.json"
        try:
            d = json.loads(p.read_text())
            row[s] = round(float(d["overall_success_rate"]), 4)
        except FileNotFoundError:
            row[s] = None
    rates = [r for r in (row.get(s) for s in suites) if r is not None]
    row["_4in1_avg"] = round(sum(rates) / len(rates), 4) if rates else None
    table[f"iter_{it:09d}"] = row

# 把 iter_2800 (10-trial acceptance) 放到最上面，与 1-trial smoke 区分
import json as _json
extra = _json.loads('''[{"iter": 2800, "label": "iter_2800 (10-trial acceptance)", "trials": 10, "libero_spatial": 0.96, "libero_object": 0.99, "libero_goal": 0.76, "libero_10": 0.58, "_4in1_avg": 0.8225, "_source": "libero_closed_loop_4in1_acceptance_4090，按 MP4 _success/_fail 后缀"}]''')
extra_table = {f"iter_{r['iter']:09d}": r for r in extra}
ordered = {**extra_table, **table}

out_json.write_text(json.dumps(ordered, indent=2, sort_keys=True) + "\n")

lines = ["# ckpt smoke SR 趋势", "", f"results_root: `{results_root}`", ""]
lines.append("| iter | spatial | object | goal | libero_10 | 4in1-avg | trials |")
lines.append("|---|---|---|---|---|---|---|")
for k, r in ordered.items():
    trials = r.get("trials", 1)
    label = r.get("label") or k.replace("iter_", "iter_")
    def fmt(v): return "—" if v is None else f"{v:.3f}"
    lines.append(f"| {label} | {fmt(r.get('libero_spatial'))} | {fmt(r.get('libero_object'))} | {fmt(r.get('libero_goal'))} | {fmt(r.get('libero_10'))} | {fmt(r.get('_4in1_avg'))} | {trials} |")
lines.append("")
lines.append("> 顶部 iter_2800：**10-trial acceptance** 真值（按 MP4 后缀），不是 smoke。")
lines.append("> 其余 12 iter：**1 trial/task smoke**（stdev≈50%），角色 = checkpoint screening / 趋势筛选。")
lines.append("> 全部**不**作为 canonical R06 baseline（按 2026-08-26 用户口径冻结）。")
out_md.write_text("\n".join(lines) + "\n")
print("summarized", len(table), "iters")
PY
  log "  -> $out_json + $out_md"
}

check_all_smoke_done() {
  local it iter_dir
  for it in "${CKPT_ITERS_DEFAULT[@]}"; do
    iter_dir="$RESULTS_ROOT/iter_$(printf '%09d' "$it")"
    if [[ ! -f "$iter_dir/.done" ]]; then
      log "!! iter=$it 未完成 (.done 缺失)；中止自动流程"
      log "   缺：$iter_dir"
      return 1
    fi
  done
  log "13/13 smoke .done 校验通过"
}

trigger_libero_90_build() {
  local build_done="$ARTIFACTS/.libero_90_cache_build_done"
  if [[ -f "$build_done" ]]; then
    log "libero_90 cache build sentinel 已存在，跳过：$build_done"
    return 0
  fi
  local out_dir="/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1/libero_90"
  if [[ -d "$out_dir" ]] && [[ -n "$(ls -A "$out_dir" 2>/dev/null | grep -v '\.json$' | head -1)" ]]; then
    log "!! $out_dir 已有非空产物，仍启动 build（NUM_SHARDS=5 / BACKGROUND=0 串行等待）"
  fi
  log "触发 libero_90 cache build（BACKGROUND=0 同步等待，避免占用前台）"
  BACKGROUND=0 NUM_SHARDS=5 \
    bash "$REPO_ROOT/tools/g0/launch_parallel_cache_build_libero_90.sh"
  log "libero_90 cache build 完成；下一步：merge"
  log "  python3 $REPO_ROOT/tools/g0/merge_latent_cache_shards.py --output-root /disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1/libero_90"
}

print_followups() {
  cat <<EOF

=== 后续计划（不自动，等用户决定）====================================
1. libero_90 cache merge（build 完成后必须）：
     python3 $REPO_ROOT/tools/g0/merge_latent_cache_shards.py \\
       --output-root /disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1/libero_90

2. #32 libero_90 latent cache 上传 HF（待仓库拍板）：
     仓库尚未拍板，本脚本不自动上传。
     决策点：dataset 名 / 私有 / 公开 / 分卷。

3. #21 canonical R06 baseline 400-episode clean acceptance（待用户授权）：
     单 ckpt + g=1.0 + num_steps=30 + max_episode_steps=700 +
     4 suite × 10 task × 10 trial = 400 episodes + no memory/agent/RL。
     等用户明确授权后单独启动；不与 smoke sweep 共用 driver 避免参数耦合。

4. 13-ckpt smoke 选型建议（ckpt × 4in1-avg + 稳定性）：
     见 $ARTIFACTS/13ckpt_smoke_summary.md
====================================================================
EOF
}

case "$PHASE" in
  summary)
    summarize_smoke
    exit 0
    ;;
  build)
    trigger_libero_90_build
    exit 0
    ;;
  todo)
    print_followups
    exit 0
    ;;
  all)
    if [[ -f "$LOCK" ]]; then
      log "lock 已存在：$LOCK；跳过自动流程。如需重跑，删除 lock。"
      log "可单独跑 PHASE=summary|build|todo"
      exit 0
    fi
    if ! check_all_smoke_done; then
      exit 2
    fi
    summarize_smoke
    trigger_libero_90_build
    echo "$(date -Iseconds) post_smoke auto flow done" > "$LOCK"
    print_followups
    log "完成；lock 已写：$LOCK"
    ;;
  *)
    log "未知 PHASE=$PHASE（all|summary|build|todo）"
    exit 2
    ;;
esac