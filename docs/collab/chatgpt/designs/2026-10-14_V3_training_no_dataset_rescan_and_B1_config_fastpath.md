# V3: training startup without whole-dataset verification; B1 config-only fast path

Date: 2026-10-14
Author: GPT, incorporating Owner proposal
Status: ACCEPTED_DESIGN_DIRECTION / IMPLEMENTATION_NOT_DONE / B1_GPU_HOLD
Frozen comparison SOURCE: Root b159f45906f7261d028aecc226ab7f2bb9807eb9; Child 937066ffd90f2bf783ad4fbb4909e9c0b8922982.
Frozen comparison TARGET: Root c4731bca1a590663db88bd6cd74dbcf9fd513a85; Child c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686.
B0 remains APPROVE/CLOSED. No old iter1300 DCP or latest checkpoint mutation.

## Policy

Owner suggests no data checking at training time. GPT agrees in the precise sense: zero dataset-wide integrity rescans during startup, Resume or per-step. Full cache/source/index validation belongs to offline dataset construction and acceptance, once per accepted immutable revision. Training directly trusts the accepted index/manifest/receipt to locate and read requested samples. Never silently rebuild a cold index or auto-rescan the dataset. Ordinary requested-sample read errors fail loudly. Keep shape, finite, Local prefix, consumer identity, valid-mask, gradient and FSDP runtime assertions: these are computation safety checks, not repeated dataset audits. Require trusted offline artifact provenance/read-only mounts so skipping runtime re-verification does not silently change the data authority.

DS reported preflight terminated during verified-index file verification after 1h41m59s with RSS 58GB. The full verification cost is unacceptable for startup; its exact RSS causality was not separately profiled and must not be claimed.

## Confirmed redundant paths beyond verify_files

1. cosmos_framework/data/generator/action/datasets/robocasa_verified_index.py:116-168: open hashes row map and unconditionally invokes verify_files; verify_files enumerates source meta, loops cache payload and selected source data stat, hashes source metadata and cache manifest.
2. cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache.py:144-165,313-323: RoboCasaExactWindowCacheCatalog unconditionally invokes _audit_files. It stats each expected episode payload and glob-enumerates tasks/*/episodes/*.pt. Removing verify_files ALONE does not yield no-scan startup.
3. cosmos_framework/data/generator/action/datasets/robocasa_exact_window_source.py:217-225: SourceReader stats each selected parquet. Other metadata and library constructors may incur additional eager scans; separately inventory before claiming zero dataset-wide I/O.
4. examples/psm_wma_robocasa_corrected_phase5.py:412-474: preflight eagerly instantiates all of these even when the only intended output is optimizer/model resolved config. Avoid that heavy path for B1 numeric-criteria readout.

## Implementation contract (requires new implementation SHA and review)

Provide explicit trusted-fast training load path for the previously accepted immutable index. In this mode, skip every O(N file) directory glob, per-file stat, hash, cold index rebuild or source-meta enumeration in all participating components. Strict full verification remains an explicit offline acceptance mode, never automatically called at training start or Resume. The trusted path consumes receipt schema/authority and memory-mapped row-map and manifest data; do not re-hash every payload. Do not silently replace missing data or skip faulty requested samples.

Tests must prove trusted startup calls zero whole-dataset verification operations, while offline strict mode still rejects manipulated fixture files. Validate one real requested sample and the CPU consumer/payload identity contract without changing data order or Local scan. Benchmark startup wall/RSS separately from model loading. Changes belong in a new isolated implementation pair: do not amend either B1 frozen Source or Target Child SHA or reset the old Formal30k writer to make a test pass.

## B1 NUMERIC CONFIG readout: avoid preflight entirely, no production patch needed

DS Lane B is Owner-DEFERRED, not failed. DO NOT rerun the 1h42 preflight. Instead, in separate isolated Source and Target pinned Python processes:

- Use actual corrected_phase5.parser to construct the exact frozen arguments and call actual corrected_phase5._load_config(args).
- Read only the already-accepted small cache dataset_manifest.json for vae_encode_contract and instantiate original CorrectedRoboCasaPolicyContract directly. Call actual corrected_phase5.overlay_config(config,args,contract,resume_checkpoint=None).
- Read only the B0-accepted verified index receipt.json for cache_manifest_sha256, cache_corpus_digest and source_binding_digest. Create a read-only minimal descriptor exposing these three authority values, then call the original matching-child corrected_phase5.config_digest(descriptor,config,b_stream=8,active_ga=2,witnesses=model_witnesses(edge,base_checkpoint)).
- Mark this as receipt-based authority reconstruction, NOT a full preflight or runtime optimizer state proof. Require source config digest 70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37 and target digest 1ab2bbe4df9954467bb0acf0d371dce40dff8bd04cfa3c81ca0ec6fe76a94b4a. If any digest mismatches, BLOCKED.
- Output fully resolved optimizer weight_decay, weight_decay_skip_patterns, keys_to_select, LR multipliers, model precision/master/reduce config, rectified-flow loss_scale, action_loss_weight, sample_level_loss_averaging, exclude_fully_conditioned_items, sigma distribution and shift, LBL coeff, callbacks, GradScaler, scheduler and pre-existing B0 provenance. The reading process must never call VerifiedExactWindowIndex.open, RoboCasaExactWindowCacheCatalog or LeRobotDatasetMetadata.
- CPU only; no model initialization, DCP model load, GPU, torchrun, producer execution, source/checkpoint mutation, new dataset acceptance run or production code edits. Submit one consolidated report to GPT.

This is enough to unblock B1 criteria evidence without consuming training startup or modifying the B1 frozen pair. It is NOT a replacement for eventual real FSDP8 loaded optimizer/parameter dtype witnesses.

## Gate boundaries

B0 CPU APPROVE/CLOSED; B1 threshold values not frozen; B1 GPU comparator not implemented/authorized; Gate M checkpoint migration and Formal30k iter1301 HOLD. No automatic GPU/training authorization follows from this change of preflight strategy.
