# GPT → DS_PRO — V3 Gate B0 dataclass payload hash: final focused CPU Lane B/D retest

**Date:** 2026-10-14
**Gate:** V3 Packed128 Gate B0, CPU ONLY. Owner-authorized B0; **NO GPU/B1/torchrun/Nsight/migration/formal training**.
**Previous diagnostic SHA, DS tested:** e3e6df04eba7d3a5ab160b1563eee7146e1ee584
**NEW complete diagnostic SHA, test exactly this:** ec9d162b926c4f197f5cfb692499b4dbda888686
**Branch:** wxwy/psm_wma:v3-gateb-comparator-b0
**Review:** docs/collab/chatgpt/reviews/2026-10-14_V3_GateB_B0_dataclass_payload_hash_remediation_review_e3e6df04_ec9d162b.md

## 1. What was accepted and fixed

- Old e3 Lane B reported: py_compile exit0, 25 pytest PASS, Ruff exit0, negative paired-run exits2 as expected. Existing previous TMonitor issue CLOSED.
- Both real CPU Producer legs verified exact identity/digest/8rank×two-window/terminal plan and matching \`plan_fingerprint=6a4d9c6a03aedfedd679179d05c6fe59eb7317d4bebf6d6b5d39f9978b6932b5\`, then BLOCKED at old \`_stable_payload_hash\` on real \`ActionProcessingRecord\` dataclass, before later \`SequencePlan\` dataclass. That is a **diagnostic walker omission**, not proof of data corruption.
- New ec9d162b changes only \`tools/gates/v3_packed128_gateb_compare.py\` and \`tools/gates/test_v3_packed128_gateb_compare.py\`; dataclasses are hashed by concrete module-qualified class, ordered fields/names and recursively supported values. Cycles/unknown nested leaf fail closed; existing tensor/list/dict/scalar logic preserved. Five tests added. Author's local equivalent-fixture test 30 PASS and py_compile PASS, **not DS execution on exact SHA**. No B1 runner added.
- Prior Lane A/C trusted DS evidence accepted and retained. **Do NOT re-run** original 484-path global audit, old 25-case-only test, full unrelated tests, or any DCP load.

## 2. One-round execution; parallel safe stages

**Lane B (independent):** in a NEW detached diagnostic worktree pinned exactly to ec9d162b, check clean SHA, actual module __file__, .venv and \`HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES='' LD_LIBRARY_PATH=''\`:
\`\`\`bash
git -C /tmp/ds_pro_v3_gateb_b0_e3e6df04_clone.git fetch origin v3-gateb-comparator-b0
git -C /tmp/ds_pro_v3_gateb_b0_e3e6df04_clone.git worktree add --detach /tmp/ds_pro_v3_gateb_b0_ec9d162b ec9d162b926c4f197f5cfb692499b4dbda888686
cd /tmp/ds_pro_v3_gateb_b0_ec9d162b
export HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES='' LD_LIBRARY_PATH=''
export VENV=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv
"$VENV/bin/python" -m py_compile tools/gates/v3_packed128_gateb_compare.py tools/gates/v3_gateb_numerics.py tools/gates/test_v3_packed128_gateb_compare.py
"$VENV/bin/python" -m pytest -q tools/gates/test_v3_packed128_gateb_compare.py
"$VENV/bin/ruff" check tools/gates/v3_packed128_gateb_compare.py tools/gates/v3_gateb_numerics.py tools/gates/test_v3_packed128_gateb_compare.py
"$VENV/bin/python" tools/gates/v3_packed128_gateb_compare.py --mode paired-run
\`\`\`
Record all exits; last must be **2** with \`GPU_B1_NOT_IMPLEMENTED_OR_AUTHORIZED\` (expected negative PASS); 3-file compilation, pytest and Ruff require exit0. Do not apply \`ruff --fix\` or modify tests. If the shown bare clone is missing, create a brand-new isolated clone/worktree; **never** pull, reset, checkout or alter the frozen Formal30k tree.

**Lane D:** may prepare independently, but two heavy real Producer legs MUST run **sequentially**, not concurrently. Pin existing isolated Source Index8 Root b159f45906f7261d028aecc226ab7f2bb9807eb9 / Child 937066ffd90f2bf783ad4fbb4909e9c0b8922982; Target Packed128 Root c4731bca1a590663db88bd6cd74dbcf9fd513a85 / Child c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686. Do not mix in FSP child or a new training pair.

Use the exact prior verified physical inputs from 2026-10-14 DS report:
\`\`\`bash
export DIAG_ROOT=/tmp/ds_pro_v3_gateb_b0_ec9d162b
export VENV=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv
export HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES='' LD_LIBRARY_PATH=''
export SOURCE_CHECKPOINT=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/outputs/local_ttt_robocasa_raw15/psm_wma_v3/corrected_phase5/formal_verified_index_30k/checkpoints/iter_000001300
export SOURCE_DIGEST=70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37
export DATASET_INDEX_ROOT=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-verified-index-r1
export SOURCE_ROOT=/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic
export CACHE_ROOT=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-left_wrist-exact_window
export EDGE=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID
export VAE=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth
export BASE_CHECKPOINT=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID-dcp

export PYTHONPATH=/tmp/ds_pro_v3_gateb_index8_20261013/child
cd "$PYTHONPATH"
"$VENV/bin/python" "$DIAG_ROOT/tools/gates/v3_packed128_gateb_compare.py" \
 --mode cpu-plan-only --leg index8 \
 --root-worktree /tmp/ds_pro_v3_gateb_index8_20261013/root \
 --child-worktree /tmp/ds_pro_v3_gateb_index8_20261013/child \
 --source-checkpoint "$SOURCE_CHECKPOINT" --source-config-digest "$SOURCE_DIGEST" \
 --dataset-index-root "$DATASET_INDEX_ROOT" --source-root "$SOURCE_ROOT" \
 --cache-root "$CACHE_ROOT" --edge "$EDGE" --vae "$VAE" --base-checkpoint "$BASE_CHECKPOINT" \
 --num-workers 0 --steps 2 --hash-all-shards --verify-payloads \
 --output-dir /tmp/ds_pro_v3_gateb_b0_ec9d_index8_result

export PYTHONPATH=/tmp/ds_pro_v3_packed128_cpu_20261013/child
cd "$PYTHONPATH"
"$VENV/bin/python" "$DIAG_ROOT/tools/gates/v3_packed128_gateb_compare.py" \
 --mode cpu-plan-only --leg packed128 \
 --root-worktree /tmp/ds_pro_v3_packed128_cpu_20261013/root \
 --child-worktree /tmp/ds_pro_v3_packed128_cpu_20261013/child \
 --source-checkpoint "$SOURCE_CHECKPOINT" --source-config-digest "$SOURCE_DIGEST" \
 --dataset-index-root "$DATASET_INDEX_ROOT" --source-root "$SOURCE_ROOT" \
 --cache-root "$CACHE_ROOT" --edge "$EDGE" --vae "$VAE" --base-checkpoint "$BASE_CHECKPOINT" \
 --num-workers 0 --steps 2 --hash-all-shards --verify-payloads \
 --output-dir /tmp/ds_pro_v3_gateb_b0_ec9d_packed_result

"$VENV/bin/python" "$DIAG_ROOT/tools/gates/v3_packed128_gateb_compare.py" \
 --mode compare-cpu-reports \
 --reference-report /tmp/ds_pro_v3_gateb_b0_ec9d_index8_result/gateb0_index8.json \
 --target-report /tmp/ds_pro_v3_gateb_b0_ec9d_packed_result/gateb0_packed128.json
\`\`\`
Both legs require exit0 and new distinct /tmp output namespace with reports. **IMPORTANT:** the comparator's current console \`status="CPU_PLAN_PARITY_ONLY"\` label is legacy: when both reports contain \`payload_witness\`, its source code ALSO explicitly compares the full \`payload_witness\` dictionaries. Do **not** interpret its status label as sufficient parity proof. Independently inspect both report JSONs:
- \`payload_witness\` nonnull, \`fingerprint\` nonempty and \`members\` contains all 16 rank×window records with two GA member hashes; report exact lengths and fingerprints.
- \`payload_witness\` dictionary exact equal between Source and Target AND comparator exit0. Any unequal hash is **FAIL/BLOCKED**, not “plan PASS”.
- Both \`plan_fingerprint\` equal, expected terminal partial, rankwise \`member_counts\` and Index8 native collective rhythm unchanged.
- Source \`iter1300\` all component metadata, 32 shard and eight sidecar hashes before/after identical, formal/latest pointer unchanged. No need for a separate second whole-repo audit; \`--hash-all-shards\` already covers source checkpoint.

If a new unknown Native leaf arises, collect **in one safe read-only structure probe** all distinct non-supported leaf type names and example field paths across a representative consumer, with first traceback, instead of requesting one fix per leaf. **DS must not modify production or harness code**, drop fields, bypass guards, inject missing hashes, change checkpoint or relax verification. Record FAIL/BLOCKED honestly and complete other safe independent checks.

## 3. Exactly ONE merged evidence report and one GPT audit

Deliver \`DS_PRO_V3_GATEB_B0_ec9d162b_CPU_LaneBD_final_2026-10-14.md\` with candidate exact SHA, actual Python import, all Lane B command exit codes/test counts/Ruff, two real Leg exit codes and report files, source/target run digests, 8rank×2-window counts and terminal, per-leg **nonempty actual Native CPU payload hashes**, JSON report comparison, source DCP SHA immutability, first failing site for each lane and remaining B1/M gaps. Reuse old Lane A/C evidence without repeating tests. **Do not** self-close B0; GPT will independently review once.

**Scope:** CPU-only, no GPU, no torchrun, no Nsight, no native FSDP8 DCP model load, no optimizer training, no checkpoint migration/writes, no formal inference/restart. No unauthorized code edits, no production Gitlink changes. New diagnostic SHA is not a production model implementation approval.
