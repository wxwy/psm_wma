# GPT → DS_PRO: B1 numerical-config receipt, trusted index metadata only (NO dataset verification)

**Date:** 2026-10-14
**Purpose:** replace deferred heavy corrected_phase5.preflight config probe; complete B1 criteria evidence in ONE CPU-only batch.
**Status:** AUTHORIZED_CPU_READONLY_RECEIPT / NO_GPU / NO_PRODUCTION_CODE_CHANGE / B0_CLOSED.
**Review:** docs/collab/chatgpt/designs/2026-10-14_V3_training_no_dataset_rescan_and_B1_config_fastpath.md.

Owner direction: training startup should NOT perform ANY dataset-wide verification. DS's earlier full Phase5 preflight was intentionally stopped after 1h41m59s and 58GB RSS during VerifiedExactWindowIndex.verify_files. This event is DEFERRED, not failed dataset. **Do not rerun full preflight, warm index file verification, Catalog._audit_files or SourceReader construction.**

## Exact frozen comparison

SOURCE Index8 Root b159f45906f7261d028aecc226ab7f2bb9807eb9 / Child 937066ffd90f2bf783ad4fbb4909e9c0b8922982.
TARGET Packed128 Root c4731bca1a590663db88bd6cd74dbcf9fd513a85 / Child c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686.
Each leg must use its own clean detached root/child Python process (separate PYTHONPATH and import module __file__). Never modify either frozen checkout, old iter1300 DCP/latest or formal worktree.

## Single-batch CPU-only fast authority reconstruction

Use existing B0-accepted files and paths:
- verified-index receipt.json at the frozen verified-index root; read ONLY this one metadata file, not its file witness list's paths;
- dataset_manifest.json at frozen cache root; read ONLY this manifest, not its episode .pt files;
- Edge model config.json and base-DCP model/.metadata via original corrected_phase5.model_witnesses (small metadata only);
- original corrected_phase5.py module for each leg.

Run in a new /tmp-only DS diagnostic script (NOT a production edit) separately for each leg:

1. Under offline CPU-only env, use original corrected_phase5.parser().parse_args(...) with frozen t=16,b=8,ga=2,k=4,world_size=8,max_iter=30000,warmup=500,save_iter=100,num_workers=0,phase=fresh and the verified frozen paths. Do NOT call preflight(args), main(), Trainer.train(), GPU, Index.open or CacheCatalog.
2. Call original module._load_config(args), not a guessed hand-made optimizer config.
3. Load the original dataset_manifest.json JSON as metadata. Directly create the original CorrectedRoboCasaPolicyContract(vae_encode_contract=manifest["vae_encode_contract"]), which validates only the VAE/tokenizer schema and does not initialize data/source readers.
4. Call original module.overlay_config(config,args,contract,resume_checkpoint=None) so the actual Phase5 production method resolves model/tokenizer/optimizer/scheduler while never loading dataset.
5. Load only the trusted B0 receipt.json JSON. For config_digest, construct a tiny read-only attribute descriptor with:
   manifest_digest = receipt["cache_manifest_sha256"]
   cache_corpus_digest = receipt["cache_corpus_digest"]
   source_binding_digest = receipt["source_binding_digest"]
   This is an explicit **receipt-derived authority** — not a claim of a new full preflight/catalog. Calculate digest with the original module.config_digest(descriptor,config,b_stream=8,active_ga=2,witnesses=module.model_witnesses(args.edge,args.base_checkpoint)).
6. Require actual SOURCE digest = 70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37; actual TARGET = 1ab2bbe4df9954467bb0acf0d371dce40dff8bd04cfa3c81ca0ec6fe76a94b4a. If either differs, BLOCKED, do not adjust config constants, try legacy digest or modify source.
7. Serialize the complete resolved fields: optimizer_type, keys_to_select, LR, multipliers, betas, eps, weight_decay, weight_decay_skip_patterns/fused; rectified flow loss_scale, action_loss_weight, image_loss_scale, normalize_by_active, exclude_fully_conditioned_items, sample_level_loss_averaging, independent_action_schedule, shift, video/action/image sigma distributions, LBL coeff; model precision and configured FSDP master/reduce dtype; GradScaler config, callbacks, GA, max_iter, warmup, save_iter, scheduler LR cycle; source/target native layout existence/value and full exact import/Gitlink SHA.
8. Compare both results: only layout+digest should legitimately vary within the same selected field inventory. Source-data CFG dropout 0.1 is **source-derived** from B0/recipe, do not pretend the manifest-only resolver executed TextTokenizer. CFG text-caption dropout is not vision/action condition_mask. A parsed config does NOT witness real-loaded FSDP parameter.grad, Adam moments, optimizer runtime LR, or B1 training stochastic coverage.
9. Write one JSON per leg and one comparison report to a NEW /tmp evidence directory. Save JSON SHA256 and wall/RSS readout. No data content verification or per-episode filesystem operations, and do not hash all row-map or 451GB cache files. No rerun of B0.

**Allowed parallel:** static 11-file diff/source-line provenance receipt and script preparation. **Serial:** source then target only for resolved-config reads, followed by comparison. Do not have multiple workers inspect large datasets.

## Evidence quality & stop rules

- Record all commands, exact SHA/root/child/imports, config values, receipt path, timings, exit status and first exception.
- If even this minimalist read-only path unexpectedly triggers VerifiedIndex.open, Catalog._audit_files, SourceReader or dataset filesystem sweep, stop and report BLOCKED. Do NOT locally monkeypatch production functions, delete any assertion, use CUDA, start a new training job or reintroduce full preflight.
- If any expected config differs, report the exact actual value + active source of override, without guessing or changing the frozen pair.
- After this one batch, provide one report: DS_PRO_V3_B1_PHASE5_TRUSTED_CONFIG_READOUT_2026-10-14.md. GPT will review once.

**No Owner numeric thresholds frozen; no B1 runtime harness implemented; GPU/torchrun/Nsight, Gate M migration and Formal30k remain HOLD.**
