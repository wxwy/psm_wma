# PSM-WMA V3 F0 Safe Start — DS_PRO Independent CPU Evidence + GPT Fresh Incremental Review

**Date:** 2026-10-16  
**Gate:** `V3_F0_SAFE_START_EXECUTION_BUDGET_CPU_GATE`  
**Independent reviewer:** GPT (Code / Evidence / Gate).  
**Formal implementation target:** **Root `b3b64732efb225c3ee08b1d9f317a90228112b29` / Child-Gitlink `0fb7f587f56048a8ffaa12e2fdb7891abc0fb021`**.  
**Implementation branch:** `v3-f0-safe-start-20261016`; branch HEAD with Codex docs `3b0c5d9cbda8ad7ce3b5adc64d420651f9e3996a` is NOT the formal Root.  
**Base implementation:** previous V3 code Root `2f4dec43eb6b1e35b33a99d844d67813df5922a6`, Child `1d56320c08c56b0f8dd248919d152d81ae12ea7b`. At review, current `origin/V3` remains docs HEAD `a1a47b36d10f1974ba0fb7cec872b1976c9c6838` (its Child remains old), with no F0 production merge.  
**Frozen contract:** `docs/build/PSM-WMA_V3_F0_safe_start_execution_budget_contract_2026-10-16.md`, author-reported SHA256 `8f3e6d3c617e428e1142578266849f7da4f99390403678e732fc7470201b7fcd`.  
**Author report:** `docs/collab/codex/reviews/2026-10-16_V3_F0_safe_start_execution_budget_author_handoff.md`.  
**Independent DS evidence report:** Owner-pasted `DS_PRO — V3 F0 独立 CPU 验收：四项证据完成 — 2026-10-16`. Executor raw scripts/XML under remote `/tmp/psm_v3_f0_accept_20261016` and `/mnt/data/...evidence_d_20261016` were NOT directly opened by GPT; result counts/RCs are reported DS evidence, while source/contract/diff below independently fetched from GitHub.  
**Formal verdict: `REQUEST_CHANGES` (F0 CPU ONLY).** One confirmed production error-precedence regression and one test-harness full-environment compatibility evidence blocker. All other independently reported F0 CPU witnesses are preserved; no GPU/real DCP/training verdict.

## 1. Precise incremental diff, no all-repo audit

GitHub verified Root implementation `b3b64732...` has Child Gitlink `0fb7f587...`. Root implementation commits relative to `a1a47b36...`: `scripts/train_v3_packed128_staged.sh` new, `docs/build/PSM-WMA_V3_F0_safe_start_execution_budget_contract_2026-10-16.md` new, `SESSION.md` and `TODO.md` append, and the Gitlink update. Child is **one direct commit** above `1d56320c...` and changes exactly:
1. `cosmos_framework/trainer/__init__.py` (+39/-8), lifecycle config writer / committed execution budget.
2. `examples/psm_wma_robocasa_corrected_phase5.py` (+385/-52), F0 namespace/resume identity/semantic config/budget.
3. `examples/psm_wma_robocasa_corrected_phase5_test.py` (+65/-19).
4. `examples/psm_wma_robocasa_phase5_f0_test.py` new.

Frozen B1 SOURCE/TARGET and diagnostic implementations, B0/index validation and official DCP unaffected. No implicit Index8 fallback introduced; current corrected Phase5 Packed128 is still the default. Index8 explicit opt-in remains separate P1 compatibility work, not F0's implementation scope.

Scoped code inspection independently confirmed new F0 APIs and default:
- `phase5.py:129,139–181,223–357`: Packed128 identity; fail-closed Fresh namespace and Resume SHA/config checks; rank0 atomic mkdir/launch advisory flock and immutable launch snapshots; all-rank preflight error/identity agreement.
- `phase5.py:701–739,862–925,932–1003`: `--formal-execution-until` separate from 30000/500/100 schedule; bounded diagnostics remain separate; Trainer run uses `_execution_max_iter`.
- `trainer/__init__.py:143–162,304–317,386–389,423–464`: optional distributed lifecycle writer, bounded committed optimizer execution and save/finalize/barrier before success message.
- Root `scripts/train_v3_packed128_staged.sh`: sealed 8-rank corrected Phase5, workers0, B8/T16/GA2/K4, fresh/resume and budget; historical H3F launcher untouched.
No additional confirmed production defect was established from these scoped changes **other than F0-REG-01**, and actual configured runtime/distributed test compatibility remains as reported below.

## 2. DS_PRO CPU evidence acknowledged, not overclaimed

DS reports exact clean detached Root/Child pair, gitlink, unchanged historical worktrees, no GPU/DCP/model.
- **F0 dedicated tests:** V3 minimal env direct unittest 26/26 and pytest/JUnit 56/56, exit0; V2 full-dependencies env pytest 39 passed, 9 failed (48 collected). These are the same method/subtest coverage under different environments, **not 26+56 distinct test behaviors**.
- **Existing impacted suites:** Phase5 59 passed, 1 failed, 1 skipped, exit1; Grouped Trainer 27 passed, exit0; all changed Python py_compile, Ruff check/format and root launcher bash syntax pass.
- **Real CPU Gloo 2-process:** `_agree_preflight` errors/config SHA agreement, rank0 full JobLifecycle writer, error broadcast to peer upon duplicate Fresh claim, bounded process exits, DS reported PASS. Both ranks report config digest `5bf2192905e421d43fd285406fa790562140bfa9b59f403b054398c07f3ae201`.
- **Real configured Phase5 metadata-only preflight:** accepted index, no full scan; 9126 episodes, `execution_stop_after_iter=100`, resolved digest `5bf21929...`; full `config.pkl` (90,518B), `config.yaml` (15,505B) actual serialization + readback. Fresh100/Resume500 **semantic** identity digest `a85594d3435e47c86bfe31f3935857891e4e43d4f14daeebe332fe7cd2ef7ac4` equal. **This is not actual same-job DCP Resume or GPU training.**
- **Real target persistent-volume synthetic directory:** observed true concurrent mkdir one-winner, flock EWOULDBLOCK while lease held then acquisition after release, adversarial existing canonical file hashes unchanged. DS reported PASS.
- **No authority to run F1, GPU, real DCP, dataset rescan, old B1 or Formal30k** from these results.

## 3. CURRENT BLOCKER: F0-REG-01 — MEDIUM / PRODUCTION error-precedence regression

**Locations:** Child `examples/psm_wma_robocasa_corrected_phase5.py:739–755` and existing regression `examples/psm_wma_robocasa_corrected_phase5_test.py:777–788`.  
**Observed:** F0 moved `check_job_namespace(args)` to `preflight` first line (740); with `--phase resume`, missing `--dataset-index-root` and no F0 identity, it raises FileNotFoundError from `v3_job_identity.json` read **before** the mandatory missing-index ValueError. Existing `test_formal_and_resume_require_accepted_index_before_data_open` fails.  
**Root cause:** Two otherwise fail-closed validation checks were reordered without preserving original mandatory verified-index input precedence. This is an error-contract/diagnosability regression, **not** evidence of unsafe checkpoint writes, data leakage or a broken Packed128 forward.  
**Frozen contract:** The accepted `--dataset-index-root` is a mandatory source-identity input and must be rejected by formal Fresh AND Resume before dataset open and any namespace/config writes. Existing test's exact failure type/message/priority must be preserved unless separately authorized to change.  
**Acceptance:** Codex places a cheap explicit `dataset_index_root is None` validation before `check_job_namespace(args)`, keeping both checks **before** `_load_runtime()`, dataset materialization and all writes. Fresh/Resume with missing Index and absent/foreign job identity each raise the expected index validation error, existing regression passes unchanged; when Index is present, existing namespace rejection, symlink and wrong-sha/digest tests still fail closed. No weakening Root/Child identity, no revising old test to mask regression, no modifications to historical jobs. Minimal source diff preferred.

## 4. CURRENT BLOCKER: F0-TEST-02 — MEDIUM / TEST-HARNESS + independent full-env acceptance

**Location:** Child `examples/psm_wma_robocasa_phase5_f0_test.py:117–167`, particularly local `_trainer_module` synthetic `ModuleType("torch")` injection `sys.modules` lacking `torch.dtype`; DS-reported Megatron `megatron/core/dist_checkpointing/mapping.py:83`.  
**Observed:** In V2 complete dependency environment nine TrainerTests import failures all `AttributeError: module 'torch' has no attribute 'dtype'`; same author fixture passes V3 minimal env without Megatron. Static inspection confirms fake module lacks dtype. DS's real CPU Gloo/Phase5 serialization witnesses do not imply these nine tests were successfully exercised under Megatron.  
**Cause:** External-dependency fixture pollutes import resolution; no evidence the actual training torch module lacks `dtype`. This is currently **tests/Evidence-only**, not a proven production defect.  
**Acceptance:** Codex makes synthetic import sandbox compatible with the established *full-dependency* environment, without weakening production/test asserts, skipping Megatron, removing the nine cases, or modifying runtime CUDA behavior. Prefer isolating the scoped imported trainer from third-party Megatron instead of leaking incomplete fake torch into actual third-party modules, or use a minimal complete type-compatible stub only when justified. F0 dedicated tests must be **all GREEN** in full V2 env; V3 minimal env also GREEN; real 2-process Gloo and config Preflight DS evidence remain valid unless source fix impacts their contracts. Test fixture changes create a **new Child/Root implementation pair** and require fresh targeted review; prior GREEN evidence can be reused only for unaffected scope, not declared new-code PASS.

## 5. OPERATIONAL EVIDENCE CORRECTION, not F0 CPU implementation blocker: STORAGE-C01

**Source:** DS §7 (read-only filesystem information): `/mnt/data` 7TB / ~223GB available; `/mnt/data1` ~338GB, `/` ~46GB; old B1 595GB native capture retained.  
**Finding HIGH before new GPU/Fresh checkpoint:** DS estimated “one 8-rank DCP ≈37.6GB” from eight ~4.7GB `packed128_P0_FIXED_repeat0/rank*.pt` native **B1 evidence captures**, NOT an actual DCP checkpoint. Original B1 8 job captures did not call Checkpointer.save. The 37.6GB value, 223/37.6=5–6 saved checkpoints, and 300×37.6GB ≈11TB cannot be treated as authoritative DCP sizing. They may overestimate or underestimate because true DCP captures *different* model/optimizer/scheduler/trainer/per-rank Local components.  
**Acceptance:** DS read-only metadata-only sum (`du -sb`/safe path+size inventory) of legitimate original iter1300 full DCP and representative component sizes (without hashing all shard bodies/reopening old B0). Separate DROID base size. If new Fresh changes trainable FQN/optimizer geometry, mark the previous DCP size only as a **provisional bound**, not exact. After first **authorized** F1-safe Fresh DCP, use *that* actual on-disk C to set retention and margin; at 30000/save100 up to ~300 saves require an explicit Owner-authorized bounded retention/archival strategy. Reserve enough for at least **two complete + one in-progress** checkpoints, logs/eval and buffer; don't delete any old B1 595GB evidence or original DCP without separate Owner approval. Quota-tools missing or lack of sudo alone does not prove all user/project quotas disabled. `/mnt/data` current reported free is not a promise about future space.

## 6. Disposition and next scope

- **Formal verdict on F0 `b3b64732.../0fb7f587...`: `REQUEST_CHANGES`**. Strong positive DS functional evidence B/C/D acknowledged. **Cannot `APPROVE_TO_CLOSE` while existing impacted regression fails and full-env TrainerTests 9 errors remain.**
- Implementer **Codex only**: fix one precedence error in `phase5.py`, repair test harness in `phase5_f0_test.py`, and add/maintain focused negative tests; do not alter Packed128 Native/optimizer, DCP/RNG F1, frozen Source/Target/B1 or performance knobs. New Child commit and updated Root Gitlink needed; no force push/V3 overwrite.
- DS_PRO **read-only** new-pair scoped independent tests: existing Phase5 missing-index regression, full V2 Megatron 56-case F0 tests, V3 minimal checks, any impacted root/child F0 tests, Ruff/syntax/Gitlink, plus real preflight/Gloo only if source diff touches shared contract. Reuse original B/C/D as unchanged-scope evidence after documenting diff impact; **do not** re-run old B0/451GB/149 B1 suites.
- GPT must fresh incremental review the **new exact Root/Child** once Codex presents the fixes, then decide `APPROVE_TO_CLOSE` or further `REQUEST_CHANGES`. Only after closing F0 may Codex start separately scoped F1 DCP/RNG implementation. No GPU training or original iter1300 migration authorization follows from F0.
- S0 storage estimate correction is parallel evidence work; no unapproved data deletion, no trained ckpt saves until F1 is accepted and separately authorized.

**Review persistence:** This report plus an append-only entry in `docs/collab/chatgpt/CODEX_INBOX_2026-10-15_CONTINUATION.md` form the formal verdict (V3 continuation replaces the filled original Inbox).
