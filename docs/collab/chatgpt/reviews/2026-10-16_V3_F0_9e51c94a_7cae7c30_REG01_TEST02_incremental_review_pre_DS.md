# PSM-WMA V3 F0 REG-01 / TEST-02 — fresh incremental review (pre-DS evidence)

**Date:** 2026-10-16  
**Reviewer:** GPT, independent code/evidence/Gate auditor  
**Gate:** `V3_F0_SAFE_START_EXECUTION_BUDGET_CPU_GATE`  
**Exact formal implementation Root:** `9e51c94a6d5dba41bd37423b9db8e634ca433789`  
**Exact Child/Gitlink:** `7cae7c3049310ccc3b7e44ce9769534e152d1f26`  
**Isolated candidate branch:** `v3-f0-reg01-fixture-20261016` (doc successor `5fbbeca8fd589b4f2fcaa018f1585bbb65531832` is not formal implementation SHA).  
**Prior reviewed F0 pair:** `b3b64732efb225c3ee08b1d9f317a90228112b29` / `0fb7f587f56048a8ffaa12e2fdb7891abc0fb021`, verdict `REQUEST_CHANGES`.  
**Current origin/V3 docs HEAD on review:** `ef9dd04464c8ac1ad08257b1f7cefb9ce7edea0b` with production Child still `1d56320c08c56b0f8dd248919d152d81ae12ea7b`. No F0 production merge.  
**Scope verdict: `REQUEST_CHANGES` — EVIDENCE-ONLY.** No new confirmed production-code blocker in this narrow diff; **independent DS_PRO real full-dependency CPU verification remains mandatory**. This is not `APPROVE_TO_CLOSE`, GPU training permission, or F1 implementation approval.

## 1. Contract, prior blocker, actual diff

Primary frozen F0 design/acceptance: `docs/build/PSM-WMA_V3_F0_safe_start_execution_budget_contract_2026-10-16.md` (author-reported SHA256 `8f3e6d3c617e428e1142578266849f7da4f99390403678e732fc7470201b7fcd`). Prior GPT review: `docs/collab/chatgpt/reviews/2026-10-16_V3_F0_b3b64732_0fb7f587_DS_independent_CPU_fresh_incremental_review.md`. Repair request: `docs/collab/chatgpt/requests/2026-10-16_CODEX_V3_F0_b3b64732_reg01_and_fullenv_fixture_minimal_remediation.md`.

GitHub directly verified:
- Child `7cae7c30` is **direct child** of `0fb7f587`, changing exactly `examples/psm_wma_robocasa_corrected_phase5.py` (+2/-2) and `examples/psm_wma_robocasa_phase5_f0_test.py` (+56/-1). Original `examples/psm_wma_robocasa_corrected_phase5_test.py` and production Trainer/DCP/RNG/Local/FSDP/optimizer/launcher remain unchanged.
- Root new formal `9e51c94a` pins exact Child and merges preceding candidate history with latest V3 **review/documentation** records; no other Root production code change. Verify Root had two parents (`3b0c5d9c...`, `ef9dd044...`), not a new algorithm path.
- Author handoff `docs/collab/codex/reviews/2026-10-16_V3_F0_REG01_TEST02_minimal_remediation_author_handoff.md` and `gate.json` / `scoped_probe.json` are available on candidate docs commit. Author reports 28 test methods +32 subtests / **60 JUnit cases**, Ruff/format/compile all exit0 on minimal CPU environment. Their synthetic Megatron collision fixture is **not** the DS V2 full-dependency environment and must not be presented as its result.

## 2. Blocker disposition and exact code findings

### F0-REG-01 (previous MEDIUM production): **STATIC CODE CLOSED; independent regression Evidence PENDING**

**Location:** Child `examples/psm_wma_robocasa_corrected_phase5.py:739–757`; existing original regression `examples/psm_wma_robocasa_corrected_phase5_test.py:777–788`.

**Original cause:** `check_job_namespace` in `preflight` preceded mandatory `dataset_index_root is None` guard; missing accepted index plus missing Resume identity produced `FileNotFoundError` instead of the specified index `ValueError`.

**Observed change:** Exact same old ValueError branch moved to beginning of `preflight` *before* `check_job_namespace` and still before `_load_runtime`, actual dataset/index open, Trainer and any write. Existing regression source/pytest assertions are byte-unchanged. New `test_missing_index_precedes_namespace_read_and_runtime_for_fresh_and_resume` covers a foreign identity and verifies no namespace-read or runtime-init branch and unchanged on-disk bytes/mtime.

**Contract assessment:** Correctly restores error precedence without weakening fresh namespace protection once an Index is supplied. No concrete production blocker remains from this diff. **Acceptance still requires DS actual complete-env original pytest test PASS**, unchanged.

### F0-TEST-02 (previous MEDIUM test/evidence): **STATIC FIX PLAUSIBLE; independent real-env Evidence OPEN**

**Location:** Child `examples/psm_wma_robocasa_phase5_f0_test.py:117–174,716–747`.

**Original cause:** Test's fake `torch` ModuleType polluted a real Megatron import whose annotations evaluated `torch.dtype`; nine `TrainerTests` failed before executing expected assertions in the prior DS V2 full-dependency environment. Not a proven production-code error.

**Observed change:** Fake `megatron` + `megatron.core` provided in the same bounded `patch.dict(sys.modules, ...)` sandbox, with a stub `parallel_state.initialize_model_parallel` that drives the imported Trainer's Megatron-present branch and avoids importing real Megatron against fake torch. Constructor negative gets the required synthetic `model_parallel` fields. New `FixtureIsolationTests` confirms host Megatron modules are not imported and preexisting `sys.modules` identities are restored. Nine original test names/assertions have not been removed or weakened; no production Trainer source modification.

**Contract assessment:** Fix is restricted to test infrastructure and matches the reported cause. Nonetheless the author explicitly lacks the actual full V2 environment. **Only DS repeating the full F0 suite and all nine TrainerTests in the same established V2 interpreter can close this Evidence gap**. No skip/xfail/test-selection workaround.

## 3. Independent DS gate required, without unnecessary reruns

Codex already published the exact suitable scoped DS request:  
`docs/collab/chatgpt/requests/2026-10-16_DS_PRO_V3_F0_REG01_TEST02_CPU_reverification_9e51c94a.md` (candidate docs successor). Reuse it rather than manufacturing a duplicate.

DS acceptance on clean detached **new exact** `9e51c94a / 7cae7c30`:
1. Confirm Gitlink/source two-file diff/parent, preserve all old jobs/worktrees/evidence; full V2 environment actual versions and `PYTHONPATH` to new Child, not to V2 source.
2. Original `test_formal_and_resume_require_accepted_index_before_data_open` unchanged **PASS**, Fresh and Resume. Full existing Phase5 suite if dependencies allow, legitimate asset skip separately recorded. Accepted Index + foreign namespace must continue fail-closed.
3. **Full new F0 file** in established V2 Megatron environment, no failures/skip; **all nine** named `TrainerTests` must actually run/pass. In parallel V3 minimal environment direct unittest+pytest, Ruff0.12.7 check/format and Python syntax. Count actual runner cases; no 28+60 double counting.
4. Prior DS two-real-CPU-Gloo, genuine configured preflight/serialization and persistent-volume mkdir/flock are accepted for unchanged corresponding production code; DS should identify why reuse is valid, **not rerun them without a new evidence gap**.

If DS reports any new production behavior regression, re-open scoped code finding and return to Codex (fresh Child+Root SHA required). If new pair all required tests GREEN, GPT should only adjudicate these two gaps for **this same formal pair**, not repeat the unchanged technical review.

## 4. Separate storage and safety boundaries

Previous DS estimated a ~37.6GB *DCP* using B1 8×rank PT numerical evidence files; those were NOT formal Checkpointer.save outputs. Correct future disk capacity with metadata-only actual prior iter1300 DCP sizes and an Owner-approved bounded retention plan, **not** with this F0 code gate. No unapproved deletion of original B1 ~595GB evidence or checkpoint/Index/DROID assets.

**Gate currently `REQUEST_CHANGES` — EVIDENCE-ONLY**, no new production fix requested now. **F1 DCP all-rank atomic publication/RNG strict restore stays HOLD** until F0 new-pair formally closes. No GPU, real DCP, Formal Fresh/Resume, Gate M, or Index8 compatibility authorization via this verdict.
