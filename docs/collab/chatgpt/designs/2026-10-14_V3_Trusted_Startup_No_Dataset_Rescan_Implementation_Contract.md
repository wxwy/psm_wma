# V3 — Trusted dataset startup without re-validation

Date: 2026-10-14
Owner: accepted dataset is already verified offline; no additional full offline acceptance, no full training/Resume dataset rescans.
Status: ISOLATED_IMPLEMENTATION_CANDIDATE / CPU_GATE_PENDING / B1_GPU_HOLD.

## Exact SHA and scope

Root candidate: branch v3-trusted-dataset-startup-20261014, parent V3 9dbaabfadf3b9b8153a9ac3b7d981446f0ef69e1.
Child candidate: wxwy/cosmos-framework branch v3-trusted-dataset-startup-20261014, SHA 1d56320c08c56b0f8dd248919d152d81ae12ea7b, parent current live V3 child 8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1.
Historical B1 frozen SOURCE Index8 b159f459/937066ff and TARGET Packed128 c4731bca/c8dabbb3 are NOT modified by the candidate pair; iter1300 checkpoint/latest remains immutable. B0 ec9d162b CPU closure remains unchanged.

## Behavior

Previously verified immutable Index/Receipt/Manifest is the data authority; do not call whole-dataset stat/glob/rglob/hash verification during training fresh, resume or steps. Missing prebuilt --dataset-index-root fails immediately; no cold fallback.
VerifiedExactWindowIndex.open has explicit verify_files=False training mode; strict default remains for separate offline tooling. Trusted training skips global file verification and row map rehash while retaining receipt schema validation.
RoboCasaExactWindowCacheCatalog trusted mode skips the per-episode cache file audit and logs file_audit_performed=False; corpus authority still comes from accepted receipt.
RoboCasaExactWindowSourceReader trusted mode skips startup source meta episode directory rglob and selected per-episode Parquet resolve/stat; validates logical relative path and accepted binding geometry, and still fails if actually requested data cannot be read.
Training preflight chooses trusted mode and reports verified_index_mode=trusted_offline_receipt_no_rescan. Runtime tensor/identity/mask/fast-state/optimizer/FSDP safety constraints must not be removed.
Strict/offline validation remains available, but do not rerun it on the accepted 451GB cache. Only synthetic tiny fixtures are used to regress strict versus trusted behaviors. LeRobot unavoidable data loading may still be expensive and must be measured separately; this change claims no global DATA VALIDATION walks, not zero metadata I/O.

## Changed child modules

1. cosmos_framework/data/generator/action/datasets/robocasa_verified_index.py
2. cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache.py
3. cosmos_framework/data/generator/action/datasets/robocasa_exact_window_source.py
4. examples/psm_wma_robocasa_corrected_phase5.py
5. cosmos_framework/data/generator/action/datasets/robocasa_verified_index_test.py
6. examples/psm_wma_robocasa_corrected_phase5_test.py

No model, optimizer, RNG, packed layout or Local scan modifications. New production formal pair must receive an independent CPU acceptance before root promotion to V3. B1 GPU and Gate M remain separately held.
