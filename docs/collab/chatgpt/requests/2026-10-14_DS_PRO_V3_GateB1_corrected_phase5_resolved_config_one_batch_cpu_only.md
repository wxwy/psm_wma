# GPT → DS_PRO: Gate B1 numerical prefreeze — one-batch CORRECTED_PHASE5 resolved-config CPU receipt

**Date:** 2026-10-14
**Scope:** CPU only, read-only, one consolidated report. **NOT a B0 re-validation**; B0 approved and closed, do not rerun. **NO GPU / torchrun / Nsight / model or optimizer native DCP load / training / migration / formal resume**.
**Authority:** GPT independent review docs/collab/chatgpt/reviews/2026-10-14_V3_Packed128_GateB1_DS_PRO_numeric_criteria_evidence_review_corrected_phase5_authority.md; numeric prefreeze r2 addendum docs/collab/chatgpt/designs/2026-10-14_GPT_V3_Packed128_GateB1_numeric_criteria_prefreeze_addendum_r2.md.
**Frozen comparator SOURCE:** Index8 Root b159f45906f7261d028aecc226ab7f2bb9807eb9 / Child 937066ffd90f2bf783ad4fbb4909e9c0b8922982.
**Frozen comparator TARGET:** Packed128 Root c4731bca1a590663db88bd6cd74dbcf9fd513a85 / Child c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686.

## Why only this batch

Your previous 2026-10-14 B1 static report mistakenly used examples/psm_wma_robocasa_h100.py/H3F as active B1 config_digest authority, generic sft_config weight_decay=0 and loss_scale=1, and did not distinguish caption CFG dropout from flow condition_mask. These are **B1 numeric-evidence** errors, not bugs in the frozen production training code. The real iter1300 writer and B1 counterpart are examples/psm_wma_robocasa_corrected_phase5.py on each frozen child. Correct Phase5 digest directly includes native_batch_layout, optimizer actual weight_decay, resolved schedule/mesh/cache, unlike H3E digest.

**This round is one complete independent source/config correction only**, not new B0 tests or a GPU run.

## Lane A — file authority + exact comparison (parallel with staging Lane B)

In a safe read-only Git checkout, compare the full exact child trees 937066ff... → c8dabbb3... and give all eleven changed files (five under cosmos_framework, six under examples), file SHA and whether each affects model/trainer/data, config/digest, telemetry or tests. Include exact source/target NATIVE_BATCH_LAYOUT value and the frozen actual corrected_phase5 config_digest function. H100/H3F entry/geometry/digest should be recorded as historical *different* experiment, not substituted for Phase5.

No code changes or commits.

## Lane B — both corrected Phase5 CPU resolved-config receipts (serial to avoid shared source/cache I/O)

Use the isolated original B0 pinned, clean read-only worktrees. Source root/child: /tmp/ds_pro_v3_gateb_index8_20261013/root and /child. Target root/child: /tmp/ds_pro_v3_packed128_cpu_20261013/root and /child. Check all 40-digit SHA and Gitlink, no dirty child, actual module __file__.

Use the existing B0 verified asset paths:
- SOURCE_CHECKPOINT (reference ONLY): /mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/outputs/local_ttt_robocasa_raw15/psm_wma_v3/corrected_phase5/formal_verified_index_30k/checkpoints/iter_000001300
- DATASET_INDEX_ROOT: /mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-verified-index-r1
- SOURCE_ROOT: /mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic
- CACHE_ROOT: /mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-left_wrist-exact_window
- EDGE: /mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID
- VAE: /mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth
- BASE_CHECKPOINT: /mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID-dcp

Use parent Cosmos .venv (python 3.13.11) with HF_HUB_OFFLINE=1, CUDA_VISIBLE_DEVICES='', LD_LIBRARY_PATH='', PYTHONDONTWRITEBYTECODE=1 and PYTHONPATH set **for each separate pinned child process**. No internet. No training. Execute the *existing native* examples.psm_wma_robocasa_corrected_phase5.parser().parse_args / preflight(args) for each leg using --phase fresh (not --phase resume), --preflight, --root-worktree / pinned exact expected Root/Child SHA, --dataset-index-root (avoid cold index building), --source-root, --cache-root, --edge, --vae, --base-checkpoint, --output-root in a new harmless /tmp namespace and formal config values: --t 16 --b 8 --ga 2 --k 4 --world-size 8 --max-iter 30000 --warmup 500 --save-iter 100 --num-workers 0. Do NOT use --snapshot10, --stop-after-iter, --audit-missing-grads or execute main training path.

You may create a temporary **/tmp-only read-only probe** that directly calls preflight() and serializes the returned report/config fields; DO NOT edit files in either pinned checkout. If stdout probes use PyTorch imports, ensure no CUDA context/tensor created.

Capture in a machine-readable JSON per leg with exact complete sha:
- config_digest from *actual* corrected_phase5 preflight; native_batch_layout from the corresponding entry; import __file__, Root/Child/Gitlink and trust digest/cache manifest/source; require old 70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37 and target 1ab2bbe4df9954467bb0acf0d371dce40dff8bd04cfa3c81ca0ec6fe76a94b4a.
- optimizer: optimizer_type, actual weight_decay, weight_decay_skip_patterns, keys_to_select as fully resolved, betas, eps, fused, base LR and per-key LR multipliers. Clarify Stage-A H3F vs corrected selected FQN selectors.
- rectified_flow_training_config: loss_scale, action_loss_weight, image_loss_scale, normalize_loss_by_active, exclude_fully_conditioned_items, sample_level_loss_averaging, shift, shift_action, video/image/action train_time_distribution, independent_action_schedule, causal_training_strategy, train_time_weight; if missing field explicitly mark MISSING (never silently use false/zero).
- model: precision, fsdp_master_dtype, fsdp_reduce_dtype, dp_shard_degree, dp_replicate_degree, context_parallel, lbl.coeff_und/gen and method, vision_gen/action_gen.
- trainer/checkpoint: trainer callbacks after overlay, grad_scaler_args, grad_accum_iter, max_iter, save_iter, warmup, scheduler cycle and all LR ratios, checkpoint.strict_resume, load_training_state under fresh. Note: do NOT claim FSDP per-parameter grad/moment actual dtypes until real B1 GPU load.
- source/target critical fields other than native_batch_layout should be identical. If unexpected values diverge, BLOCKED rather than masking them as expected.
- actual CFG caption dropout from text_tokenizer.py:101–106 and resolved source dataset cfg_dropout_rate=0.1; separately report condition_mask semantically (clean/noisy) and sigma/noise sites; do not relabel condition_mask as CFG.

Hash each CPU resolved JSON (sha256). Save only to new /tmp evidence folder, no source/checkpoint edits. If preflight cannot safely run without writing an output path, do not use that path; emit clear BLOCKED and first stack. No GPU.

## Lane C — consistency + one consolidated report

Compare source/target resolved fields, with only expected native layout/config digest differences. Compare config weight_decay with source recipe 0.05 and Edge loss_scale 10.0; if runtime disagrees, report value and active override source and do not guess. Verify if exclude_fully_conditioned_items, sample_level_loss_averaging and aux are effectively off, as required for the simple per-consumer objective proof. Reuse the already closed B0 8rank/2window/partial/CFG CPU payload witness; do not rerun B0.

Write ONE DS_PRO report:
docs/collab/chatgpt/DS_PRO_V3_GATEB1_CORRECTED_PHASE5_RESOLVED_CONFIG_ONE_BATCH_2026-10-14.md (or /tmp equivalent, then owner-paste), with Lane A/B/C statuses, command exits, actual JSON sha, full config authority fields, source code file:line, first failure stack and any remaining B1 GPU-only questions. Return once for ONE GPT incremental review.

**No B1 numeric freeze occurs from this report alone.** Owner still chooses actual pre-registered threshold table (including master DeltaP/Adam moments), and separate Owner authorization is required for real FSDP8 GPU. Gate M/formal iter1301 remain HOLD.
