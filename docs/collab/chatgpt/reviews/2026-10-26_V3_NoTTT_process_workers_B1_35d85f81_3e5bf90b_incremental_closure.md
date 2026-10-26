# GPT Independent Incremental Review — V3 No-TTT Process Workers HIGH B1 Evidence Closure

- 日期：2026-10-26
- **Formal Root implementation/test target:** `35d85f81ba6925e718a87d721b80686745791c60`
- **Formal Child + Root Gitlink:** `3e5bf90b4eb5fa5cbad9fa7ab62e86bf44c6b07b`
- Candidate Root/Child branch: `v3-nottt-process-workers-20261026`; candidate docs/evidence HEAD `b401bb275c941ba7165e368efc0de95b6cc7e35a` is NOT the formal target.
- Previous GPT-reviewed formal Root `76d1cc70622d3b456a3c388ad98917b7d532890b`, same Child. Its verdict was `REQUEST_CHANGES` with HIGH **Evidence-only** B1.
- Original pre-worker baseline Root `e6ae2084305a8c24d763d82b517984660cc73c30`, Child `923d9c3fd392e6bafbdb1771a292c7b313e6b3dc`.
- Frozen Issue #4 contract: `docs/collab/chatgpt/requests/2026-10-26_Codex_V3_Matched_No_TTT_multiprocess_workers_optin.md` §§2.4,2.6,4.
- Prior review: `docs/collab/chatgpt/reviews/2026-10-26_V3_NoTTT_process_workers_76d1cc70_3e5bf90b_incremental_review.md`.

## Formal verdict

**`APPROVE` — GPT scoped B1 synthetic-CPU Evidence Gate CLOSED for exact Root `35d85f81ba6925e718a87d721b80686745791c60` / Child `3e5bf90b4eb5fa5cbad9fa7ab62e86bf44c6b07b`.**

The previous HIGH B1 Evidence-only blocker is **CLOSED**. No fresh in-scope production or test-code blocker was established. This verdict only accepts deterministic **old workers=0 code → candidate workers=0 code** continuation with **synthetic CPU state**; it does not assert real same-job DCP/CUDA success, enable workers=0→workers>0 migration, authorize V3 merge, GPU/real IO, stopping a live Job or any formal training run. Independent DS_PRO CPU Gate is still pending.

## Minimal reviewed delta and Evidence

1. GitHub compare previous formal `76d1cc70622d...` → current `35d85f81ba...`: only new `tools/v3/no_ttt_legacy_worker0_resume_test.py` (544 lines), SESSION/TODO entries; **no production code, scripts, configs or Child/Gitlink changes**. Following candidate docs/evidence commits do not alter implementation. Thus no full-repo/old implementation re-review.
2. Direct source review: `tools/v3/no_ttt_legacy_worker0_resume_test.py:26-32,74-141,144-254,257-373,376-511,514-540`. The test extracts exact old Root/Child sources via `git archive` (omitting inactive symlinks without following), launches separate Python processes with `PYTHONPATH` pinned to old/candidate Child, verifies imported production Phase5/Trainer module SHA against Git objects, and forces workers=0. The old actual `training_identity`, `config_digest`, `JobLifecycle.write_config` and `NoTTTFrontierCallback.state_dict` create a synthetic old Job under the original `no_ttt_packed128_droid_fresh_30k_world4_ga4` name, including original format `psm_v3_matched_no_ttt_frontier_v1`. New code reads the same canonical identity and old state without changing profile/format/digest/Job namespace.
3. Four logical ranks (CPU sequential, not collective), world4/GA4/T16/B8. Old code saves after two committed optimizer updates, then runs iterations 3/4 uninterrupted; candidate code loads old state and repeats them. Full members 128/128/128/128 and terminal members 128/8/128/8, including epoch transitions in terminal case. Comparison includes actual planner/member positions, source/consumer chronology, transformed payload/action/state/latent/masks, production native collator, weighted toy differentiable Generation loss/pre-zero gradient, toy model, optimizer SGD momentum, scheduler/scaler, trainer iteration, complete Frontier and Python/NumPy/Torch CPU RNG. Tensor values are content-hashed. All original synthetic saved Job files remain read-only and SHA256/mtime/mode unchanged.
4. Six explicit fail-closed negative cases: config semantic, seed semantic, wrong rank profile, Frontier counter, config digest, iteration. Config/seed use production `check_job_namespace`; rank/frontier/digest/iteration use production Frontier restore before native model forward. Negative tests also re-check old Job immutability.
5. Directly checked author original `docs/collab/codex/evidence/2026-10-26_nottt_worker0_cross_code_B1_author_cpu/junit.xml`: eight concrete testcase elements = **8 passed, 0 fail/error/skip**, two parity and six negatives; `pytest.log` says 8 passed/68.54s. Also examined `STATUS.json`, `command.json`, `exit.json`, `B1_WITNESS.json`, `frozen_witness_files.json`, `SHA256SUMS.json`, `shared_authorities_sha256.json`, `protected_paths.json`, author handoff. The evidence folder retains a tar.gz of 65 frozen old/new original witness files, including old eight rank synthetic snapshots and per-version import/result logs; author says real assets/DCP/CUDA were not touched. The independently inspected JSON inventory and high-level witness are consistent with actual test logic. Earlier run01/run02 fixture mistakes remain separate and are NOT counted as passes.
6. Static author tests Ruff0.12.7/format/syntax/hash PASS per `static/checks.json`. This GPT review independently checks repo source and original stored author Evidence, **does not claim independent CPU replay**. Prior 601-pass suite is neither rerun nor aggregated into the new eight tests.

## Blocker disposition

**B1 (previous HIGH, Evidence-only): CLOSED — contract → behavior → evidence.**

- Frozen contract: preexisting workers=0 No-TTT Same-Job Resume and strict rank/Frontier/RNG continuity must survive candidate code changes, without rewriting old identity/checkpoint state.
- Behavior: old-code original-format state is restored and validated by new-code worker0, then next two iterations exactly reproduce old uninterrupted CPU trace for full/partial rank geometry.
- Evidence: exact code-bound subprocess tests, saved snapshots, command/JUnit/import hashes and negative tests above.
- Limitation: synthetic Python `pickle` state and toy SGD scalar model are **not** production DCP/official Cosmos/FusedAdam/FSDP/CUDA-RNG. Closing the synthetic B1 blocker must not be described as safe-to-stop live No-TTT.

No other previously closed findings are reopened for an unchanged production implementation.

## Explicit remaining Gates / operational boundary

1. **DS_PRO independent CPU:** reproduce same exact formal pair on a clean detached Root/Child, run targeted B1 8 cases with new external evidence directory, verify JUnit & SHA, plus source/Frontier/identity checks. Do not mutate live No-TTT/G1/data/old checkpoints.
2. **Owner-authorized real same-Job Resume Gate (workers0→0 only):** read-only verify the *actual* current 4GPU Job identity, canonical config snapshots, latest committed model/optim/scheduler/trainer DCP and all four dataloader rank sidecars; preserve original files and collect independent state witnesses. Perform isolated CPU/real-assets compatibility preflight, then an explicitly authorized bounded 4xGPU resume from a protected checkpoint/namespace with exact data/RNG/gradient/next-iteration continuity checks (including actual CUDA RNG, optimizer/scheduler). Only after this runtime Gate can stopping/upgrading/resuming the live No-TTT be approved. Do **not** alter the active Job today based on synthetic evidence.
3. **workers0→workers1/2/4:** candidate intentionally rejects same-job cross-profile Resume via new `_mpwN_world4_ga4` namespace, strong training semantic identity and separate Frontier format. Original Issue #4 contract forbids silent migration. Any desired active-job migration requires a **separate Owner-authorized frozen design**, dedicated migration Evidence and real DCP acceptance; **not** covered by this APPROVE.
4. Target training Python/Torch private DataLoader spawn lifecycle, real source/cache RSS/IO, physical FSDP/NCCL/GPU native loss/gradient and throughput remain future Gates; worker count need not improve speed because SourceReader remains in parent.

**Scope of this `APPROVE`:** only the exact test-only Root / unchanged Child formal pair and synthetic CPU B1 evidence. Does **not** authorize a V3 merge, real training/inference/evaluation, hardware use, live code deploy, checkpoint migration or killing/restarting existing processes.

## Persistence

Detailed review in `docs/collab/chatgpt/reviews/`; append-only canonical handoff in `docs/collab/chatgpt/CODEX_INBOX.md` is required for this to become a formal verdict.
