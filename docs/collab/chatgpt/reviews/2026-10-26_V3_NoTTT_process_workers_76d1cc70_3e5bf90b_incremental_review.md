# GPT Independent Incremental Review — V3 Matched No-TTT true multiprocessing CPU Workers (Issue #4)

- 日期：2026-10-26
- **Formal Root implementation:** `76d1cc70622d3b456a3c388ad98917b7d532890b`
- **Formal Child / Root Gitlink:** `3e5bf90b4eb5fa5cbad9fa7ab62e86bf44c6b07b`
- Candidate branch (Root/Child): `v3-nottt-process-workers-20261026`
- Docs-only handoff HEAD `df2f1ac3e07eec559a6f0c237abb1a8adb60c142` is **not** the formal implementation SHA.
- Baseline Root `e6ae2084305a8c24d763d82b517984660cc73c30` / Child `923d9c3fd392e6bafbdb1771a292c7b313e6b3dc`.
- Frozen acceptance request: `docs/collab/chatgpt/requests/2026-10-26_Codex_V3_Matched_No_TTT_multiprocess_workers_optin.md`.
- **Formal technical verdict: `REQUEST_CHANGES` — Evidence-only blocker for preservation of the *existing active workers=0 No-TTT Job* across the candidate code change.** No independently confirmed Issue #4 production-semantics blocker in the reviewed opt-in multiprocessing implementation. Not GPU/real-DCP approval.

## Incremental code and Evidence reviewed

1. Root `scripts/train_v3_matched_no_ttt_4gpu.sh`, `tools/v3/no_ttt_workers_entry_test.py`; child `cosmos_framework/trainer/matched_no_ttt.py`, `cosmos_framework/trainer/no_ttt_cpu_loader.py`, `cosmos_framework/utils/no_ttt_loader_profile.py`, `examples/psm_wma_robocasa_corrected_phase5.py` and corresponding changed tests. Diff compared to exact baseline Root/Child pair, not docs HEAD or running server checkout.
2. Frozen upstream production authorities checked: `ExactWindowSegmentProducer.prepare/materialize`, `RoboCasaExactWindowCachedDataset.__getitem__`, `RoboCasaExactWindowEpisodeReader`, checkpoint sidecar/identity and existing optimizer/GA/native loss path.
3. Author original `docs/collab/codex/evidence/2026-10-26_nottt_multiprocess_workers_author_cpu/junit.xml` inspected: 606 testcase elements = **601 passed + 5 explicitly skipped**, no error/failure; 42 successful subtests separately recorded. `STATUS.json`, `command.json`, `worker_pid_witness.json` and handoff examined. These are **author CPU**, not independent DS or real DCP/GPU evidence.
4. Real `torch.utils.data.DataLoader` spawn process PIDs, worker1/2/4, main-thread native transforms and packed loss path appear wired. Source snapshot + mmap reader/CPU packet/prefetch/cleanup, profile-isolated new Job, original workers0 argv and old frontier branch are separately present. Parent's serial SourceReader work remains, so **no acceleration claim** is justified.

## Current blocker B1 — HIGH, Evidence-only, original frozen contract §2.4/§2.6

- **Locations:** `cosmos_framework/trainer/no_ttt_cpu_loader_resume_test.py:29-44,64-129`; `cosmos_framework/trainer/matched_no_ttt.py:143-195`; `examples/psm_wma_robocasa_corrected_phase5.py:242-297,438-456`; Root `tools/v3/no_ttt_workers_entry_test.py:59-91`.
- **Observed gap:** Author Fresh100→Resume101/500 uses **only newly created worker>0 same-profile** synthetic checkpoint, scale-reduced T1/B1/GA4 toy model. Launcher test compares old/new **argv**, not old-version persisted Frontier + model/optimizer/scheduler/trainer/RNG + canonical Job identity restored by new-version `workers=0` code. No immutable baseline-version saved state is restored across actual implementation versions. Thus old ongoing `no_ttt_packed128_droid_fresh_30k_world4_ga4` Resume is **plausible statically but unproven**, and the user's stated stopping/restarting requirement is not yet accepted.
- **Frozen contract:** Existing `workers=0` Job's Fresh/Resume/DCP semantics/identity must remain unchanged, and all rank0..3 Frontier and RNG/state must strictly restore (request §2.4, §2.6; contract → behavior → evidence).
- **Acceptance to close (CPU scope):** Capture a *read-only*, frozen synthetic workers0 pre-change state under exact baseline pair and restore it using candidate workers0 code without changing Job name, CLI/config identity, sidecar schema or contents. Exercise four logical ranks, GA4 and at least one full B8/T16/member + terminal case, with exact committed Frontier/cursor/consumer ordering, next-step payload+loss/grad (toy where necessary), model, optimizer momentum, scheduler, trainer iteration, Python/NumPy/Torch CPU RNG parity and unchanged original saved files. Include negative changed-config/seed/rank/frontier cases; verify before native forward and without any real assets. Source SHA and replay commands/JUnit attached. This is **in addition** to already supplied new-worker self-Resume evidence, not a request to rerun all 601 author tests. Actual 4×GPU DCP/CUDA-RNG same-Job Resume remains a separate DS/Owner runtime Gate.

## New Owner operational requirement — separate frozen design Gate, NOT a bug under Issue #4's original scope

Owner additionally requests stopping today's actively running workers0 No-TTT and **continuing it under the new multiprocessing implementation**. This may mean either (A) workers0→workers0 code-version Resume or (B) workers0→workers>0 parameter-change Resume. These are not equivalent.

- **Explicit prohibition in current candidate:** `cosmos_framework/utils/no_ttt_loader_profile.py:59-65` requires a *NEW* `_mpwN_world4_ga4` Job; `examples/psm_wma_robocasa_corrected_phase5.py:259-271` strictly compares saved worker profile; `cosmos_framework/trainer/matched_no_ttt.py:157-185` deliberately separates `psm_v3_matched_no_ttt_frontier_v1` from `psm_v3_matched_no_ttt_loader_frontier_v1`; `scripts/train_v3_matched_no_ttt_4gpu.sh:25-61` enforces namespace. Therefore **workers0→workers>0 with the existing Job/DCP is currently NOT SUPPORTED**, despite author 601 PASS.
- Original frozen Issue #4 specifically forbids silently migrating an active Job and requires a *separately authorized design* before cross-worker-count Resume. Do **not** remove identity checks, replace old DCP/sidecars, use a symlink alias, fabricate an old new-profile Frontier, or restart Fresh in an existing namespace.
- **Next disposition:** Obtain a separate Owner-authorized cross-profile continuation design Gate if goal B is required. It must specify immutable original Job/Checkpoint, new isolated destination namespace and dual-identity provenance, precommit migration authority, exact optimizer/scheduler/trainer/Python+NumPy+Torch+CUDA RNG+rank0..3 Frontier parity, same consumer next-step ordering, atomic abort/retry and rollback semantics, and negative tests before any real migration. Alternatively retain worker0 for the active Job and use a separately fresh mpwN Job only for a performance experiment. Neither path is approved by this static review for production use.

## Non-blocking runtime risk / later Gates

- `NoTTTCpuLoader.finish` performs nonpersistent worker teardown after `MatchedNoTTTWindow.finish` and optimizer success (`matched_no_ttt.py:345-353`, `no_ttt_cpu_loader.py:499-549`). Failed postcommit cleanup poisons the training instance; verify actual 4-rank failure/last-saved-checkpoint recovery semantics in runtime, including no partial durable Frontier or unreaped children. This is **not** presently a demonstrated production bug: optimizer success and data consumption precede the committed Frontier, and the callback rejects a failed instance.
- Private PyTorch `_MultiProcessingDataLoaderIter` / PID lifecycle needs target training Python/CUDA Torch validation. Author tested Torch `2.10.0+cpu`, Python `3.12.14`; no real-asset/RAM/NCCL/FSDP/DCP measurements. Do not interpret author tests as DS independent acceptance.
- Current opt-in path parallelizes CPU raw cache/policy preparation but not parent verified SourceReader snapshots; new worker count may be slower. Measure real host before electing to restart.

## Scope and handoff

- Formal Code/Evidence verdict **`REQUEST_CHANGES`** for the exact candidate pair above; outstanding B1 is **Evidence-only**. Code semantics of the in-scope opt-in worker path have no confirmed blocker from this independent static inspection, subject to any defect exposed by a stronger fixture.
- **Do not stop, checkout/reset the live training worktree, touch old Checkpoints, merge to V3 or run GPU/production data** on this authorization.
- Codex should submit a minimal **B1 test/Evidence remediation candidate** for fresh review only if implementation SHA changes; if source pair unchanged, review the new Evidence separately without repeating source audit. Any cross-profile migration change requires an **independent frozen design Gate first**, not a stealth scope expansion.
- Detailed review plus append-only canonical `docs/collab/chatgpt/CODEX_INBOX.md` are required to form a formal verdict. This verdict does not authorize DS GPU tests, live Resume or training.
