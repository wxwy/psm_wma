# PSM-WMA V3 F0 Safe Start — REG-01 / TEST-02 独立 CPU Evidence Closeout

**Date:** 2026-10-16  
**Independent reviewer:** GPT — Code / Evidence / Gate  
**Gate name:** `V3_F0_SAFE_START_EXECUTION_BUDGET_CPU_GATE`  
**Formal verdict literal:** **`APPROVE_TO_CLOSE` — F0 CPU ONLY.**  
**Bound implementation Root:** `9e51c94a6d5dba41bd37423b9db8e634ca433789`  
**Bound implementation Child / Root Gitlink:** `7cae7c3049310ccc3b7e44ce9769534e152d1f26`  
**Candidate branch:** `v3-f0-reg01-fixture-20261016`, documentation HEAD at review time `5fbbeca8fd589b4f2fcaa018f1585bbb65531832` (**not** the formal Root).  
**Current origin/V3 at gate review start:** docs HEAD `4c2b138326e26ba0e4d17b7fc21178ffa2088d94`, still with old production Child `1d56320c08c56b0f8dd248919d152d81ae12ea7b`; F0 implementation **not** merged into V3 mainline.

**Review character:** Formal implementation pair unchanged since prior scoped technical review. This is **EVIDENCE-ONLY closure**, not another code-diff/whole-repo review or another CPU test execution.

## 1. Authority / prior open findings

- Frozen F0 implementation contract: `docs/build/PSM-WMA_V3_F0_safe_start_execution_budget_contract_2026-10-16.md` (author/DS bound SHA256 `8f3e6d3c617e428e1142578266849f7da4f99390403678e732fc7470201b7fcd`).
- GPT new-pair technical increment already completed: `docs/collab/chatgpt/reviews/2026-10-16_V3_F0_9e51c94a_7cae7c30_REG01_TEST02_incremental_review_pre_DS.md` (prior `REQUEST_CHANGES — EVIDENCE-ONLY`).
- Codex author handoff: `docs/collab/codex/reviews/2026-10-16_V3_F0_REG01_TEST02_minimal_remediation_author_handoff.md`, author minimal CPU success not treated as independent evidence.
- Independent DS_PRO report supplied 2026-10-16: `DS_PRO — V3 F0 REG-01 / TEST-02 新 SHA 独立 CPU 复验报告`, clean detached pair, exact commands/exit codes/JUnit paths and independent B/C/D reuse explanations. Raw remote test logs remain on DS server under `/tmp/psm_v3_f0_r2_accept_20261016/`; the remote computer is OFFLINE and GPT did not claim to personally open them. Review uses DS independent reported evidence plus the previously completed GitHub source/frozen-contract review.

## 2. Same-pair evidence supplementation — CONTRACT → OBSERVATION → VERDICT

| Required condition / previous blocker | Independent reported observation and source | Verdict |
|---|---|---|
| Exact new formal pair + clean identity | Root `9e51c94a...` detached, Root Gitlink `7cae7c30...`, Child HEAD exact `7cae7c30...`; both porcelain empty | **PASS**, independently GitHub pair also verified |
| F0-REG-01 missing-index-before-namespace for Fresh **and** Resume | Unchanged original `test_formal_and_resume_require_accepted_index_before_data_open` in full V2 env: **1 passed**, RC0; required `ValueError: dataset-index-root` precedes namespace reads | **CLOSED** |
| Entire impacted original Phase5 regression | V2 full Cosmos/Megatron env: **61 collected, 60 passed, 1 asset-dependent skip, 0 failures, RC0** | **PASS**, skip recorded rather than hidden |
| F0-TEST-02 real full-dependency Megatron fixture import | V2 full env: **28 F0 methods passed, 0 failed, 0 skipped**, RC0; original **nine TrainerTests** explicitly appear as nine XML testcase elements, all passed with no skip/xfail | **CLOSED** |
| F0 V3 environment coverage | V3 environment F0 suite **28 passed**, no failed/skipped, RC0; direct unittest also 28 tests OK in both envs | **PASS** |
| Grouped Trainer impacted regression | V2 full env **27 passed**, 0 failed/skipped, RC0 | **PASS** |
| Modified source static | Changed two files Ruff check, Ruff format --check, py_compile all RC0 | **PASS** |
| Prior B: real 2-rank Gloo, all-rank preflight config/digest & writer failure propagation | Earlier independent B evidence exact F0 contract, both ranks PASS and no hang; new Child merely reorders missing-index guard and test fixture; on valid index the same functions and Trainer are byte-unchanged | **REUSED / VALID**; no repeated process run required |
| Prior C: genuine accepted-index preflight + full config serialization + Fresh100/Resume500 identity | Earlier real-config C evidence, matching accepted index; identity/digest/serializer routines unchanged, B/C caller supplies valid index | **REUSED / VALID** |
| Prior D: persistent filesystem mkdir/flock, unchanged old config bytes/mtime | JobLifecycle/lease/check_job_namespace logic byte-unchanged by new Child; only no-index failure precedence changed | **REUSED / VALID** |

**Count interpretation:** Pytest console `28 passed` and 28 XML testcase entries are the independent case count. The JUnit XML root `tests=60` includes unittest `subTest` bookkeeping under pytest9 and **is not 60 unique test methods**. Do not add the unittest, pytest and XML counts together or claim missing tests because their counting conventions differ.

**No skip workaround:** Report explicitly confirms the nine previously failing named `TrainerTests` actually ran in the *same V2 full-dependency environment* with zero skip/xfail. Installed real Megatron is present, while the synthetic external dependency fixture intentionally shields imported Trainer tests from fake `torch.dtype` conflicts; this is evidence for the scoped test harness, not a claim to have run real training.

## 3. Formal closing decision

- Previous F0-REG-01: **CLOSED**, original unmodified regression now passed.
- Previous F0-TEST-02: **CLOSED**, all nine real full-env tests passed.
- New production blockers in the unchanged formal pair: **none identified** by the reviewed scope.
- Previously accepted B/C/D witnesses remain valid for their **unchanged** actual contracts. No test repetition is required when only same-pair additional evidence is supplied.
- **Literal F0 verdict = `APPROVE_TO_CLOSE`**, bound exclusively to Root `9e51c94a6d5dba41bd37423b9db8e634ca433789` / Child `7cae7c3049310ccc3b7e44ce9769534e152d1f26`. This supersedes the earlier `REQUEST_CHANGES` for *this same F0 formal pair* based on new evidence, without retroactively changing the earlier review's factual status when it was issued.

## 4. Strict non-authorization / remaining independent gates

**This CPU verdict does not authorize:** GPU, torchrun, real DROID model load, real full DCP save/load, Fresh/Resume training, Formal30k, Gate M, old Index8→Packed128 numerical equivalence, B0/451GB dataset recertification, E1 or Index8 compatibility. Historical B1 frozen r2 GPU parity remains **NUMERIC FAIL / REQUEST_CHANGES** and its ~595GB evidence untouched.

**Next permitted implementation workflow:** Codex may start a **new isolated F1 candidate** based on approved F0 formal pair, under the already frozen scope `docs/collab/chatgpt/requests/2026-10-16_CODEX_V3_Fresh_P0_safe_start_DCP_RNG_execution_budget_staged_remediation.md`:

1. Synchronous DCP safe publication: all-rank sidecar completion and fail-closed collective, locally atomic per-rank sidecars and `latest` pointer, completion marker; failure never advertises partial DCP, do not alter old history/non-local async behavior.
2. Strict per-rank Python/NumPy/Torch/CUDA RNG state and no post-resume deterministic reseeding; DROID model-only Fresh may remain without prior training RNG.
3. New Child and Root/Gitlink exact formal pair, Codex scoped CPU negatives then DS independent clean detached verification then GPT **FRESH incremental code/evidence review**. F1 is **not** approved by this F0 verdict, only allowed to proceed as a code candidate.

**Other prerequisites before any later new Fresh GPU approval:** real durable-volume space + bounded checkpoint retention plan (previous DS's B1 native PT evidence shards are not an authentic DCP checkpoint size); native Packed128 full/terminal loss/mask/action/local FSDP functional evidence and actual first Fresh100 DCP→Resume500 GPU Gate on its own Owner authorization. Do not assume current root free space is sufficient or delete old B1 evidence.

**Canonical persistence:** Append this verdict to `docs/collab/chatgpt/CODEX_INBOX_2026-10-15_CONTINUATION.md` because original Inbox is near its limit. Formal closure requires BOTH detailed review and canonical entry.
