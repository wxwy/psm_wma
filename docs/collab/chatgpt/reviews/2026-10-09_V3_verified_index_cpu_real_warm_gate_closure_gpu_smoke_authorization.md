# PSM-WMA V3 — Verified Dataset Index CPU / Real Cold-Warm Gate Closure

Date: 2026-10-09
Reviewer and final gate owner: GPT/Codex
Evidence origin: DS_PRO, training-server read-only execution report (raw logs reside on DS server)
**Verdict: VERIFIED_DATASET_INDEX_CPU_AND_REAL_WARM_GATE = ACCEPTED / GREEN at documented scope.**
**Next authorized action: ONE fresh bounded 8xH100, 3-optimizer-step diagnostic; formal30k still NOT AUTHORIZED.**

## Precise implementation being accepted

- DS executed on **Root `c4086107df7175da68b457c30abbba16def92ecc` / Child+Gitlink `4923e494a8bb0e1e18d7943ae00bd17f71498d88`**, child clean and root with explicitly allowed MM notes / DS evidence (reported 46 items).
- The previous bookkeeping-only Root `e5f0dcbadfbbff57dac8fbf046fed810f8237daa` added a Review and CODEX_INBOX; no implementation, test, or Gitlink changes. This closure adds only another Review / inbox entry. For subsequent GPU execution, pin **the exact resulting Root branch HEAD** and Child `4923e494a8bb0e1e18d7943ae00bd17f71498d88`; do not silently use the tested historical Root as `--expected-root`.
- Candidate Root branch: `v3-persistent-dataset-index-pair-20261009`; Child branch: `v3-persistent-dataset-index-20261009`.
- Neither production `V3` nor `v3-local-ttt` is promoted, touched, or approved for changes.

## Review of DS_PRO's CPU and real corpus evidence

### A. Targeted CPU GREEN

- Round 3, exact implementation: `ruff format --check` all 8 files, **8 already formatted (exit 0)**; `ruff check` all 8, **all checks passed (exit 0)**. Reported logs: `/tmp/psm_wma_v3_r3_ruffformat.log`, `/tmp/psm_wma_v3_r3_ruffcheck.log`.
- Targeted Round 2 pytest results carried forward by report: **151 passed (1 skipped)** and **52 passed (1 skipped)** in distinct test invocations, according to DS's summary at `/tmp/psm_wma_v3_pair2_tests.log`. The only incremental Child difference from its preceding `97c09d7b` was +6/-3 Ruff formatting of `robocasa_verified_index_test.py`, no behavioral code or test assertion change.
- Ruff version and raw pytest logs were not independently downloaded or re-executed by reviewer; above is acceptance of DS's direct execution evidence. Historical code/static gates are not rerun.

### B. Single-process cold index creation PASS

- Builder output `INDEX_BUILT`, no torchrun/GPU, wall **1213.56 s** (20m18s), max RSS **6,752,988 KB**.
- **9,126** accepted episodes; **2,085,331** windows; **2,231,347** absolute rows; **9,126** episode bindings.
- File counts: **9,126** cache .pt witnesses, **18** selected source parquet witnesses, **3** metadata witnesses.
- Receipt: 6,450,901 B; row mapping: 35,701,680 B.
- `cache_manifest_sha256=8e63c73b4e07cdbebd6427d9efdd3f2d8b293ecd10511cae25a55c6566f6db88`
- `cache_corpus_digest=0e0c05d09722dc7e65da868326ded3cc23a0885e4ed8841e3fbad1ab2e41fac3`
- `source_binding_digest=f91b0b477a048beb439f1d73e7414f6b1d2a0307eee54c858d6cd8503ea19020`
- Cold SourceReader stages in seconds: episode binding 659.262, row mapping 361.541, LeRobot initialization 184.286, reader total 1206.809. 
- External indexed artifact: `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-verified-index-r1/`; must remain unchanged.
- DS logs: `/tmp/psm_wma_v3_cold_build_r1.log`.

### C. Warm read-only + corrected Phase5 preflight PASS

- Existing-index read-only check returned `INDEX_VALID`, verify logic 1.62 s, process wall 5.06 s.
- Single-process Phase5 `--preflight --dataset-index-root` returned exit 0 and `verified_index_hit=true`, wall **202.10 s**.
- Same cache, source, DROID DCP and model witnesses as frozen formal authority. `config_digest=70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37` exact match; episodes 9,126, exact DS Root/Child/Gitlink lock.
- Preflight intentionally supplied `--stop-after-iter 3` along with `--preflight`: this is a *bounded diagnostic preflight only*, not three executed optimizer iterations. It retains configured formal `max_iter=30000/warmup=500/save_iter=100` and frozen digest.
- Warm stages in seconds: index verify 0.709; catalog 0.910; source reader binding 2.475; row map 0.0009; LeRobot init 184.813; source reader total 188.980; full Dataset init 191.157. The single-process elapsed also includes other preflight/model/config checks.
- Comparable source reader initialization improved **1206.809 -> 188.980 s (~6.39x / 84.34% lower)**; episode binding **659.262 -> 2.475 s (~266x)**; row mapping **361.541 -> 0.0009 s**, leaving LeRobot/HF init (~185 s, ~97.8% of warm SourceReader) the principal bottleneck.
- DS logs: `/tmp/psm_wma_v3_verify_existing_r1.log`, `/tmp/psm_wma_v3_warm_preflight_r1.log`.

## Strict evidence boundaries (not false claims)

- DS reported no torch.load mentions in plain logs. This is **not** an instrumented count of cache .pt calls; absence of log entries alone cannot establish a dynamic zero. Code-path audit, targeted synthetic blocking test, and measured warm timings are consistent with and support bypass of *bulk cold cache scanning*. Do not call this a fully instrumented proof on 9,126 real episodes.
- The report did not separately supply real corpus paired cold/warm raw sample/Local segment tensors; synthetic parity tests plus unchanged formal source/cache/config digests supply relevant compatibility evidence. This missing extra real pairwise evidence is documented, not fabricated.
- Reported row-map digest was truncated in the narrative; `INDEX_VALID` checked against the receipt's actual full hash. No claim of independently rehashing 451GB: large .pt/source parquet files are bound by stat witnesses, metadata by SHA.
- Cold Builder wall (1213.56s) versus Warm Phase5 full preflight wall (202.10s) are not identical end-to-end procedures. Speedup is asserted **only** for the comparable source-reader phases.
- The reported Round 3 tests were limited to Ruff check/format; previous targeted pytest evidence was carried forward across test-only formatting. Do not describe the tests as freshly rerun on Round 3.

## Bounded 8xH100 Gate authorization and STOP rules

**Authorize ONE fresh 8xH100 run of `CORRECTED-V3-FORMAL-SCHEDULE-BOUNDED-GPU-TELEMETRY-SMOKE`** after DS syncs this Review's exact final Root HEAD / pinned Child (docs-only Root delta requires no repeated CPU, Cold Build, or Warm Load).

Required:
- `HF_HUB_OFFLINE=1`, Child-source `PYTHONPATH` to override old editable installs, one existing worktree, unchanged external index; no refetch/rebuild of 451GB cache.
- `--phase fresh --stop-after-iter 3 --dataset-index-root <existing index> --job-name bounded_<new_unique_namespace>`.
- `--max-iter 30000 --warmup 500 --save-iter 100 --t 16 --b 8 --ga 2 --k 4 --world-size 8`.
- Official `Cosmos3-Edge-Policy-DROID-dcp` base and matching frozen source/cache model authority. `--expected-root` is **the new Root HEAD from this review commit**, `--expected-child=4923e494a8bb0e1e18d7943ae00bd17f71498d88`; Gitlink must equal Child; child clean, allowed MM/DS root dirt only.
- Preflight `config_digest=70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`. Any invalid receipt, authority mismatch, surprise .pt-cold-scan signature, wrong SHA, unexpected root dirt or OOM -> **stop**. No override of safety checks.
- No training beyond iter3; no retry with relaxed flags, no resume of diagnostic DCP. Preserve all Evidence.
- Return exit code, bounded_stop `completed_iteration=3`, exactly 3 rank0 per-step complete telemetry records with finite loss/grad/LR, Local frontier/commit and optimizer step counts; third-step CUDA/memory/norm data, per-rank startup and peak RSS/VRAM and wall breakdown, no extra iter4.
- Confirm diagnostic final DCP `iter_000000003` has model/optim/scheduler/trainer and all eight dataloader rank state files. Label **DIAGNOSTIC_ONLY_DO_NOT_RESUME**.

**Still prohibited:** formal30k fresh or resume; candidate promotion to production; any permanent source edits by DS; worktree reset/clean or replacement of MM notes/evidence.

## Final disposition

Close this targeted **Dataset Index CPU + real cold/warm initialization Gate** on the reported execution scope. Review the bounded GPU evidence separately before considering a formal training authorization. Do not redo the VAE exact-window audit, earlier optimizer readiness, 20-minute index Cold Build, or unchanged static tests solely because Root has new documentation commits.
