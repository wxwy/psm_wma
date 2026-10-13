# GPT → DS_PRO: V3 Packed128 Gate B0 CPU Comparator Candidate Validation

Date: 2026-10-13. Owner decision 2 = A: authorize **isolated B0 code + CPU only**. No GPU, torchrun, model training, DCP writes, migration, or formal resume.

## Branch & provenance

Independent root branch: `v3-gateb-comparator-b0`. This is a **new diagnostic implementation**, NOT the frozen `c4731bca / c8dabbb3` Packed128 production pair. Formal `V3` and child Gitlink remain untouched by this branch.

- SOURCE / Index8: root `b159f45906f7261d028aecc226ab7f2bb9807eb9`, child `937066ffd90f2bf783ad4fbb4909e9c0b8922982`.
- TARGET / Packed128: root `c4731bca1a590663db88bd6cd74dbcf9fd513a85`, child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`.
- Never import FSP child `8f3672d1` in these paired checks. Check `__file__`, Git HEAD, root Gitlink.

Files provided in branch:
- `tools/gates/v3_packed128_gateb_compare.py` — B0 plan/schema/RNG/read-only CPU preflight, `paired-run` intentionally blocked.
- `tools/gates/v3_gateb_numerics.py` — proposed per-FQN numerical metric implementation for CPU tests. **Not Owner-frozen thresholds.**
- `tools/gates/test_v3_packed128_gateb_compare.py` — CPU-only tests and negative controls.

## Execution boundaries

All real checkpoint, raw/cache/index, model config paths are **read-only**. The harness only writes its JSON report under a *new* `/tmp` directory. `HF_HUB_OFFLINE=1`, `CUDA_VISIBLE_DEVICES=''`, `LD_LIBRARY_PATH=''`, no network. No `torchrun`, Nsight, GPU, CUDA allocation, production code/edit, checkpoint/`latest_checkpoint.txt` edit, or formal worktree `checkout/pull/reset`.

**Important:** This is a **CPU B0 candidate**, not completed Gate B0/B1. The GPU model/load/Gradient parity path is deliberately not implemented or authorized. The code does not call `Trainer.train` or `Checkpointer.save`.

## DS step 1 — isolated static & unit verification

Clone/fetch this *independent branch* in a separate diagnostic worktree, leaving the Formal30k tree untouched. From the diagnostic root:

```bash
export HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES='' LD_LIBRARY_PATH=''
export VENV=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv
"$VENV/bin/python" -m py_compile tools/gates/v3_packed128_gateb_compare.py tools/gates/v3_gateb_numerics.py tools/gates/test_v3_packed128_gateb_compare.py
"$VENV/bin/python" -m pytest -q tools/gates/test_v3_packed128_gateb_compare.py
"$VENV/bin/ruff" check tools/gates/v3_packed128_gateb_compare.py tools/gates/v3_gateb_numerics.py tools/gates/test_v3_packed128_gateb_compare.py
```

All exit 0 required. If Ruff unavailable, report BLOCKED_LINT; do not claim PASS. Preserve all commands/exits.

## DS step 2 — real iter1300 CPU source/schema/plan checks, one leg at a time

Use separate **preexisting pinned source/target root+child worktrees**; never modify their Gitlinks or launch `train.py`. Export paths below from the frozen 2026-10-13 DS report (verify physical files). `CHECKPOINT` must be the original Formal `.../checkpoints/iter_000001300`, not iter1400. `DIAG_ROOT` is the independent branch checkout containing this tool.

```bash
export HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES='' LD_LIBRARY_PATH=''
export VENV=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv
export DIAG_ROOT=/tmp/ds_pro_v3_gateb_b0_source_20261013  # point to isolated branch checkout
export SOURCE_CHECKPOINT=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/outputs/psm_wma_v3/corrected_phase5/formal_verified_index_30k/checkpoints/iter_000001300
export DATASET_INDEX_ROOT=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-verified-index-r1
export SOURCE_ROOT=/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic
export CACHE_ROOT=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-left_wrist-exact_window
export EDGE=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID
export VAE=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth
export BASE_CHECKPOINT=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID-dcp
export SOURCE_DIGEST=70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37

# Source leg; PYTHONPATH is the actual pinned child, NOT the diagnostic branch's child.
export PYTHONPATH=/tmp/ds_pro_v3_gateb_index8_20261013/child
cd "$PYTHONPATH"
"$VENV/bin/python" "$DIAG_ROOT/tools/gates/v3_packed128_gateb_compare.py" \
  --mode cpu-plan-only --leg index8 \
  --root-worktree /tmp/ds_pro_v3_gateb_index8_20261013/root \
  --child-worktree /tmp/ds_pro_v3_gateb_index8_20261013/child \
  --source-checkpoint "$SOURCE_CHECKPOINT" --source-config-digest "$SOURCE_DIGEST" \
  --dataset-index-root "$DATASET_INDEX_ROOT" --source-root "$SOURCE_ROOT" \
  --cache-root "$CACHE_ROOT" --edge "$EDGE" --vae "$VAE" \
  --base-checkpoint "$BASE_CHECKPOINT" --num-workers 0 --steps 2 \
  --hash-all-shards --verify-payloads \
  --output-dir /tmp/ds_pro_v3_gateb_b0_index8_result_20261013

# Target leg, never during Source leg import in same Python process.
export PYTHONPATH=/tmp/ds_pro_v3_packed128_cpu_20261013/child
cd "$PYTHONPATH"
"$VENV/bin/python" "$DIAG_ROOT/tools/gates/v3_packed128_gateb_compare.py" \
  --mode cpu-plan-only --leg packed128 \
  --root-worktree /tmp/ds_pro_v3_packed128_cpu_20261013/root \
  --child-worktree /tmp/ds_pro_v3_packed128_cpu_20261013/child \
  --source-checkpoint "$SOURCE_CHECKPOINT" --source-config-digest "$SOURCE_DIGEST" \
  --dataset-index-root "$DATASET_INDEX_ROOT" --source-root "$SOURCE_ROOT" \
  --cache-root "$CACHE_ROOT" --edge "$EDGE" --vae "$VAE" \
  --base-checkpoint "$BASE_CHECKPOINT" --num-workers 0 --steps 2 \
  --hash-all-shards --verify-payloads \
  --output-dir /tmp/ds_pro_v3_gateb_b0_packed_result_20261013

"$VENV/bin/python" "$DIAG_ROOT/tools/gates/v3_packed128_gateb_compare.py" \
  --mode compare-cpu-reports \
  --reference-report /tmp/ds_pro_v3_gateb_b0_index8_result_20261013/gateb0_index8.json \
  --target-report /tmp/ds_pro_v3_gateb_b0_packed_result_20261013/gateb0_packed128.json
```

The checkpoint's exact physical path must first be confirmed by DS. These command paths are **configuration templates**, not claims they exist. `--hash-all-shards` rehashes 32 large files per leg; budget for CPU I/O and note costs. `--verify-payloads` runs full CPU materialization/CFG replay on two windows of eight ranks and may be expensive. Both are necessary to claim complete source immutability and CPU transformed-payload parity; without them the report remains plan/schema-only.

If actual runtime hits an unsupported Native payload type, inconsistent FSDP collective rhythm, missing model files, or other validation error, stop and return first traceback. Do NOT edit harness, child source or source DCP; GPT handles remediations. `--mode paired-run` is **blocked by code** until a separately approved B1 runner exists.

## Gate B0 evidence requirements

Report filename: `DS_PRO_V3_PACKED128_GATE_B0_CPU_ACCEPTANCE_2026-10-13.md` under separate evidence output. Include:

- diagnostic branch exact HEAD; source/target exact root+child/gitlink; import module `__file__` and environment;
- three py_compile, Ruff, pytest commands with exit codes and full first failure;
- original source metadata and 32 shards: sha256 before/after; eight source sidecar rank/profile/schema, nested config digest;
- per-rank two-window member_counts, terminal partial and 8rank index active collective rhythm;
- source and target CPU Native transformed payload equality; cfg Python global RNG unchanged; target translation only in memory;
- negative tests / fail-closed guard; no GPU or checkpoint writes;
- explicitly list untested `actual FSDP8 DCP load`, `real model forward/backward`, `P1 distribution-matched sigma`, `per-FQN gradients`, `numerical parity`.

**Closure is GPT's separate independent review**, not the executor's self-approval. B0 CPU does NOT authorize B1 GPU or Gate M. Stop after reporting.
