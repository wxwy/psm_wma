# DS_PRO + Owner — V3 Formal30k 同模式 iter800→正式续训执行授权（手动触发）

**Date:** 2026-10-12
**Exact Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`; **Child/Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
**Formal job:** `formal_verified_index_30k` (NOT C1 Shadow job).
**Scope:** `OWNER_MANUAL_FORMAL30K_SAME_MODE_RESUME`; no Fresh, no history code rollback, no Optimized ON/ON, no parallel experiments. **Only after required CPU preflight and live resource/approval guards PASS** may the owner personally launch the full native formal `--phase resume` job. DS prepares/checks/monitors, **does not auto-launch**.
**R0 CPU Evidence verdict:** `R0_CPU_READINESS_PASS`; **Original D1 strict FAIL remains on record**, optional D1-S HOLD. C1 CLOSED.
**Review:** `docs/collab/chatgpt/reviews/2026-10-12_V3_R0_same_mode_resume_readiness_and_S1_design_review_444c232b_e9b8a41.md`; relayed Evidence `docs/collab/chatgpt/evidence/2026-10-12_V3_R0_S1/DS_PRO_2026-10-12_R0_S1_resume_candidate_owner_relay.md`.

## 0. Runtime identity and chronological acknowledgement

- Historical runtime Child `71e03c8501c94a2ad5fed60955af657d3f945b85` (old dense video) is **not** the exact current implementation; no checkout rollback. Use fixed current `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`, Root `444c232b976e80ac68cde9e7370e73b9f6410f0e` with strict root/child/gitlink equality and Child clean at the training-server checkout. Never substitute GitHub's later docs-only V3 branch HEAD for `--expected-root`; if root checkout is not `444c232b976e80ac68cde9e7370e73b9f6410f0e`, STOP for review, do not reset/clean or silently change SHA.
- Two explicit env vars `PSM_V3_COMPACT_CACHED_VIDEO=0`, `PSM_V3_SHARED_EPISODE_CACHE=0` and CLI `--num-workers 0` (Raw Prefetch axis only); old JointDataLoader 4 workers are a distinct setting and must remain untouched. No new CUDA allocator/FSDP/NCCL environment tuning.
- Formal schedule/geometry frozen: `T16/B8/GA2/K4/world8/Hpred16/raw15/left_wrist/use_state,max_iter30000,warmup500,save_iter100`. Full config digest exact `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37` (compute, do not just assert).
- **Actual earlier work reached iter805, but last DCP is iter800.** Formal resume must replay iter801–805 from 800; owner accepts that those five unsaved updates will be superseded (not recovered). Keep old historical records; new attempt has distinct stdout/stderr logs. No automatic resume from 805 or pretend to be at 806.
- Original `.../psm_wma_v3/outputs/local_ttt_robocasa_raw15/psm_wma_v3/corrected_phase5/formal_verified_index_30k` will be **written** by Trainer constructor (config.yaml/pkl), TelemetryJournal and later new DCP iter900+. Checkpoint iter800 must stay intact; C1 physically copied Shadow iter800 remains recovery source.

## 1. CPU-only synchronous preflight — mandatory before GPU

Use this same argument vector verbatim for both the CPU preflight and subsequent manual torchrun, no `--stop-after-iter` and never `--phase fresh`.

```bash
set -euo pipefail
cd /mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/cosmos-framework
VENV=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin
ENTRY=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/cosmos-framework/examples/psm_wma_robocasa_corrected_phase5.py
export PSM_V3_COMPACT_CACHED_VIDEO=0 PSM_V3_SHARED_EPISODE_CACHE=0
ARGS=(
  --phase resume
  --expected-root 444c232b976e80ac68cde9e7370e73b9f6410f0e
  --expected-child e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c
  --output-root /mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/outputs/local_ttt_robocasa_raw15
  --source-root /mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic
  --cache-root /mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-left_wrist-exact_window
  --edge /mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID
  --vae /mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth
  --base-checkpoint /mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID-dcp
  --root-worktree /mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3
  --dataset-index-root /mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-verified-index-r1
  --num-workers 0 --job-name formal_verified_index_30k
  --t 16 --b 8 --ga 2 --k 4 --world-size 8 --max-iter 30000 --save-iter 100 --warmup 500
)
"$VENV/python" "$ENTRY" "${ARGS[@]}" --preflight | tee /tmp/psm_wma_v3_formal_resume_preflight_20261012.log
```

**Preflight fail closed** unless JSON/report affirm actual root/child/gitlink lock, original Job checkpoint source exact iter800, `execution_scope=full_formal`, `verified_index_hit=true`, config digest exact, correct frozen schedule/Source/Cache/Model identity. `--preflight` does not instantiate Trainer (and must not write original Job). If any value unknown or mismatched, STOP before GPU and send to GPT, **no manual workaround**.

Also *before* GPU: verify no other writer to original Job, Shadow backup still independent, original `latest_checkpoint.txt` and iter800 source metadata/8 sidecars unchanged and small-file SHA baseline recorded; preserve historical stdout/session/progress and journal (no truncation), writable disk space for iter900 DCP (at least ample for ~24GB shard total), no symlink collision. Check all 8 H100 runtime `memory.free>=25000MiB`, external robotwin_server stable, and explicit owner/other workload sharing permission; confirm correct venv CUDA torch and torchrun plus clean Child git SHA. If any guard fails, `RESOURCE_BLOCKED` or `PRECHECK_BLOCKED`, **do not launch**.

## 2. Owner manual full formal Resume — only after all preconditions pass

Owner executes exactly once, in same shell/environment/ARGS after preflight and explicit confirmation:
```bash
RUN_LOG_DIR=/tmp/psm_wma_v3_formal_resume_20261012_attempt01
mkdir -p "$RUN_LOG_DIR"
# One single torchrun, no retries and no resume worker auto-restart.
"$VENV/torchrun" --standalone --nnodes=1 --nproc-per-node=8 --max-restarts=0 \
  --log-dir "$RUN_LOG_DIR" --redirects 3 \
  "$ENTRY" "${ARGS[@]}"
```
Do not copy this command into an unrelated shell without `ARGS`, CWD, VENV, ENTRY and exported flags. Do not change `--expected-root` to current docs-only HEAD or `--expected-child` to historical `71e03c8`. Do not add `--stop-after-iter=801`; actual source restricts it to fresh bounded diagnostic.

This is **a real formally writable, potentially long-running job**, not a single no-step diagnostic. It will overwrite only allowed Original Job config+append logs and save new original DCP at iter900 and subsequent intervals. No concurrent second formal job or Shadow GPU test. DS must not launch automatically; the owner controls start/stop.

## 3. Health monitoring and immediate stop conditions

- At first committed **iter801**, verify it truly loaded iter800 full 5 components and continued after snapshot state, per-rank planner/frontier/fast state never reset, selected inventory total=314, 8 rank no missing/nonfinite selected gradient (where actual telemetry/audit supports), `status=optimizer_committed`, `telemetry_errors=[]`, finite losses/norms, correct LR scheduler epoch; `data_wait_reason=synchronous_producer_no_background_dataloader`, no unexpected DCP/missing keys/NCCL errors. Do not hard fail solely from minor loss changes or approximate quoted 1.3–1.6 range.
- At iter801–805, expect **checkpoint rollback replay**. Make a new-operator-attempt marker and compare new journal with old historical stdout; retain prior original lines. Production `read_train_records` supports replay-aware derived view; do not manually delete historical rows.
- At iter900, validate successful DCP save and `latest_checkpoint.txt` points `iter_000000900`, all 8 rank sidecars and all checkpoint model/optim/scheduler/trainer subfiles exist, no nonfinite/partially saved state and no original iter800 overwrite. Then continue 30k if healthy. If unexplained freeze, OOM, nonfinite loss/gradient, `missing_grad>0` in a required group, rank divergence/Local corruption, identity or resource drift, owner/DS must stop and preserve first exception, per-rank logs/checkpoint metadata. **No auto retry or self-resume**; report to GPT.
- Telemetry grouping is **overlapping**: `selected=314` exclusive generation289/action5/local20; aggregated telemetry generation294 **includes action5**, so `294/5/20` should not be naively summed to319. Do not declare an anomaly from this display-only overlap.

## 4. Handoff

DS returns `DS_PRO_V3_FORMAL30K_SAME_MODE_RESUME_2026-10-12.md` with preflight result, actual owner permission+run command+runtime hashes, first 801–805 snapshots, iter900 save witness when reached, 8 Rank errors/health, resource monitor, before/after Original Job/Shadow DCP manifests and source no-drift evidence. If blocked before start, return guard evidence with `BLOCKED` and leave original Job STOPPED.

**Scope prohibition:** This authorization does not close D1 OFF/ON strict numeric Gate, does not approve D1-S experimental GPU, simulator/E/F, arbitrary new models, or a different formal pair. No production source modifications, frozen recipe tweaks, cross-mode optimization, external job eviction, or automatic repeated resumes.
