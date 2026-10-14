# GPT -> DS_PRO — Trusted dataset startup, ONE CPU-only acceptance batch

Date: 2026-10-14
Scope: CPU_ONLY / EXECUTOR_VALIDATION_ONLY. Existing 451GB offline acceptance is final. Do NOT rerun it or B0, and do NOT invoke GPU, torchrun, training, migration or Formal30k.

Exact candidate root branch wxwy/psm_wma:v3-trusted-dataset-startup-20261014.
Exact candidate child branch wxwy/cosmos-framework:v3-trusted-dataset-startup-20261014 at SHA 1d56320c08c56b0f8dd248919d152d81ae12ea7b. Pin root HEAD and verify its cosmos-framework Gitlink matches this SHA. Parent child is 8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1. Work only in new clean isolated checkout.

## Parallel lanes, one report

Lane A (parallel): capture root/child status SHA, py_compile and Ruff on six modified child Python files in the implementation contract. Record tool versions and all exits. Do not apply ruff --fix.

Lane B (parallel, synthetic-only): run:
python -m pytest -q cosmos_framework/data/generator/action/datasets/robocasa_verified_index_test.py cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache_test.py cosmos_framework/data/generator/action/datasets/robocasa_exact_window_source_test.py examples/psm_wma_robocasa_corrected_phase5_test.py

All tests must use small generated fixtures only, never actual dataset full scan. Verify strict default rejects tampering (synthetic only), verified index trusted open skips full verify_files and row map content rehash, trusted Catalog skips _audit_files, SourceReader skips _preflight_metadata and selected file path filesystem checks. Verify that sample identity and action/state tensors remain identical and a missing requested payload fails loudly. Formal/resume missing verified index must fail before dataset load. No source/target B1 change.

Lane C (parallel read-only): inspect child diff against 8f3672d1. Confirm only four production files + two test files, no data construction order/RNG/optimizer/memory behavior changed. Audit remaining external LeRobot metadata initialization separately; do not equate necessary reading to a full validation. Check accepted receipt/manifest authority is unchanged, but do not re-verify 451GB payloads. If easy, in parallel carry out the separate B1 numeric-config metadata-only receipt from prior GPT instructions without calling full preflight.

Produce ONE report DS_PRO_V3_TRUSTED_DATASET_STARTUP_CPU_GATE_2026-10-14.md: exact root+child SHA/Gitlink, all exits, synthetic cases and negative test counts, real code inspection, no-scan evidence, remaining startup heavy constructors and any first stack. Return once for GPT single independent incremental review.

Failure in a lane blocks only dependents. Do not edit code, disable checks in tests, mutate checkpoint, merge/promote root into live V3 or start GPU. Current code is candidate only; formal training remains HOLD until separate Gate clearance. B0 is CLOSED and is not to be rerun.
