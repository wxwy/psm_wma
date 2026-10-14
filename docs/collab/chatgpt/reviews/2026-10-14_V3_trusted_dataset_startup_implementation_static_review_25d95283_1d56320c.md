# GPT implementation review: trusted dataset startup, ZERO full dataset revalidation

**Date:** 2026-10-14
**Reviewer:** GPT
**Verdict:** HOLD — IMPLEMENTED_IN_ISOLATED_PAIR / CPU_EXECUTOR_GATE_PENDING
**Candidate Root SHA:** 25d95283317b1c1f3715f57a5335d290db130241 (wxwy/psm_wma:v3-trusted-dataset-startup-20261014)
**Candidate Child/Gitlink SHA:** 1d56320c08c56b0f8dd248919d152d81ae12ea7b (wxwy/cosmos-framework:v3-trusted-dataset-startup-20261014)
**Parent live V3 docs Head:** 9dbaabfadf3b9b8153a9ac3b7d981446f0ef69e1 / Gitlink 8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1. Do not confuse live V3 docs HEAD with candidate implementation SHA.
**Owner authority:** existing RoboCasa dataset has already passed offline acceptance and **must not be fully reverified again**. Training/Resume should bypass all global dataset-wide integrity walks. No B0 retest or GPU authorization.
**Independent scope:** implementation deltas from parent live child 8f3672.. to 1d563..; no re-review of B1 frozen Index8/Target production comparison SHAs.

## Implementation diff/contract review

GitHub exact compare showed **six** touched Child Python paths, and exactly three Root paths (child Gitlink + proposal design + DS CPU request). No model weights, training loss, TTT scan, RNG, optimizer, scheduler, FSDP, B1 frozen comparator or DCP files changed.

| Child changed file | Source behavior, direct review | Contract |
|---|---|---|
| cosmos_framework/data/generator/action/datasets/robocasa_verified_index.py | open gains strict-by-default bool verify_files; trusted=False skips row mapping content sha and whole files verify, reads only receipt schema | No startup full stat/hash walk; explicit offline tooling retains strict verifier |
| cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache.py | trusted index bypasses _audit_files global per-episode stat/glob; stats file_audit_performed=False and completeness_scope identifies trust | No fake live file audit PASS while using offline receipt |
| cosmos_framework/data/generator/action/datasets/robocasa_exact_window_source.py | trusted index bypasses _preflight_metadata rglob, selected parquet path realpath/stat per Episode; still logical traversal rejection, accepted binding, requested sample read failure | No O(N file path audit; no blind data substitution |
| examples/psm_wma_robocasa_corrected_phase5.py | fresh/resume preflight refuses missing prebuilt --dataset-index-root; explicit verify_files=False; logs trusted mode and index_open_ms | No cold index rebuild; exact 451GB data offline acceptance reused |
| robocasa_verified_index_test.py | three small fixture regressions for no-walk on trusted, sample identity/value parity, missing requested payload fail, nonbool flag rejected | CPU synthetic-only, NO production offline re-validation |
| corrected_phase5_test.py | formal/resume missing-index guard with real t/b/ga/k/world_size geometry set (fixed in second child patch) | Early fail-closed |

**Known scope:** Constructors for LeRobotDatasetMetadata/LeRobotDataset still load metadata/index data that training needs and may take time. This patch specifically eliminates redundant dataset-wide **integrity re-verification**, not all legitimate reader initialization or all memory allocation. No claim that 1h42 start is now instant without measuring the new path. Real 451GB file system acceptance must NOT be rerun.

## Checks and incomplete evidence

- New candidate Root 25d95283317b1c1f3715f57a5335d290db130241 Gitlink points to Child 1d56320c08c56b0f8dd248919d152d81ae12ea7b, remote checked.
- Child compare 8f3672..1d563.. = exactly six intended files. Root compare V3-base..candidate = Gitlink + two docs only.
- One premature test fixture object omitted formal geometry; identified and fixed before final candidate identity was frozen.
- **Actual py_compile, Ruff and real pytest in DS environment NOT YET executed; GitHub commit has zero check-runs.** Local Python AST smoke of representative constructs does not replace testing complete source. Therefore no acceptance APPROVE until independent DS CPU executor report and follow-up GPT evidence-only review on SAME exact pair.

## DS handoff and strict boundaries

Single test request in candidate Root:
docs/collab/chatgpt/requests/2026-10-14_DS_PRO_V3_Trusted_Startup_CPU_One_Batch_Acceptance.md

DS should batch exact-SHA py_compile + Ruff, existing synthetic VerifiedIndex/Cache/Source/Phase5 test files, source-vs-target impact check and zero-global-check negative assertions. **DO NOT run offline full dataset audit**, B0 re-tests, real 8xH100 training, torchrun, Nsight, DCP migration, Gate M or Formal30k. Capture first failures without editing code; one report. After green + GPT review candidate is eligible for promotion into live V3; its exact new formal pair then requires separate Code Gate closure. Meanwhile live V3 HEAD and Gitlink remain unchanged and GPU/H3F training stays HOLD.

**Disposition:** owner-requested optimization is implemented and committed in isolated Root+Child; code readiness is conditional on independent CPU validation, not claimed completed.
