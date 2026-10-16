# PSM-WMA V3 — Codex Packed128 Fresh 独立设计审核的 GPT 增量复审与实施裁决

**Date:** 2026-10-16  
**Reviewer:** GPT independent design/code/evidence/Gate reviewer  
**Review target:** Codex report `docs/collab/codex/reviews/2026-10-16_V3_Packed128_Fresh_Training_Independent_Plan_Review.md`, committed `72c32e07b1335dfe6877bc7ac7edddc861637c32` (docs-only, previous HEAD `6d41a2d...`). GitHub report read directly; 1-file documentation-only change independently verified.  
**Production implementation (unchanged):** Root `2f4dec43eb6b1e35b33a99d844d67813df5922a6` / Child/Gitlink `1d56320c08c56b0f8dd248919d152d81ae12ea7b`. This incremental **design-finding review is NOT re-review of unchanged formal production implementation**.  
**Frozen B1 diagnostic:** `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0` / `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`, historical r2 GPU numerical FAIL preserved.  
**V3 Fresh prior design:** `docs/collab/chatgpt/designs/2026-10-16_V3_Packed128_DROID_Fresh_staged_training_route_PROPOSAL.md`.  
**Design disposition:** `REQUEST_CHANGES` **on the new Fresh route's executable plan only**. Codex's direction supported; four safety/continuity issues and executable route must be closed before a true fresh100->resume500 training run. A new design/implementation candidate and independently observed behavior will need fresh scoped review. **No GPU / formal training approval issued.**

## 1. Contract interpretation and severity matrix

| Finding | GPT adjudication | Must block Packed128 new Fresh? |
|---|---|---|
| C-P0-03 Sync DCP rank-local Sidecar completion not checked before `latest`, pointer not atomic | **CRITICAL / P0; verified actual code path** | **YES: before first formal DCP save** |
| C-P0-04 Strict same-job RNG rank missing silently skipped; deterministic-seeding overwrites restored RNG | **HIGH / P0; first definite, second conditional but real** | **YES: before any formal Resume** |
| C-P0-05 Ordinary Fresh lacks pre-write nonempty-namespace rejection; Resume can overwrite old config before validation | **HIGH / P0; verified actual write order** | **YES: before launch** |
| C-P0-02 No formal execution boundary 100/101 preserving schedule/config; existing stop-after is diagnostic fresh-only | **HIGH / P0; verified CLI vs existing Trainer hook** | **YES: for staged formal100/101; do not use kill as substitute** |
| C-P0-01 No runnable Index8 selector in current corrected Phase5; default packed128 is real | **MEDIUM / P1 interface contract** | **NO for new Packed128-only Fresh safety; YES for eventual V3 dual-route completeness** |
| C-P0-06 Real FSDP Local Slow grad/action semantic and full/partial/aux objective | **HIGH / P0 EVIDENCE-only unless concrete defect found** | **YES for first native-step functional health**, no speculative production rewrite |
| EVAL E1 / storage / config identity | **Storage/canonical launch P0 operations; EVAL E1 independent Gate** | Storage + immutable semantic config YES; full eval queue not prerequisite of initial 100-step save; required before trusted SR |

The user explicitly requires *both modes present in V3, Packed128 default*. Report correctly reveals current Phase5 only implements the default half. Do not claim dual-route compliant. But do not inject an unverified Index8 dispatch into the production pair as a prerequisite of first Packed128 Fresh; implement this contract in a **separate compatibility change/Gate**, with independent SHA and test. If user later insists on both in one formal training pair before launch, request scope decision before merging; no implicit fallback is ever allowed.

## 2. Direct code/contract verification of current blockers

### C-P0-03 — CRITICAL: incomplete DCP may be advertised as latest

- **Code:** Child `cosmos_framework/checkpoint/dcp.py:1165–1199,1231–1261`, `cosmos_framework/checkpoint/base.py:231–243`, `cosmos_framework/utils/easy_io/backends/local_backend.py:107–112,132–134`.
- **Root cause:** DCP shared model/optim/scheduler/trainer operations run, then each rank independently `_save_as_pkl` for its `dataloader/rank_<rank>.pkl`; `save_state_dict_worker` immediately lets rank0 publish `latest_checkpoint.txt` upon completing its own writes without a post-sidecar success collective. Rank7 may still be writing or may fail. Dataloader and latest local writes use direct open('wb'/'w'), not atomic per-file publication. Successful same-job completion requires all 8 rank sidecars; latest-alone is insufficient.
- **Acceptance:** For new job's **synchronous-local DCP profile**, each rank writes sidecar into a unique temporary file, flush/fsync as relevant, atomic os.replace in same filesystem; preserve exact serialized payload. Aggregate success/failure across all 8 ranks with bounded distributed failure semantics. Publish a versioned completion marker and atomic same-filesystem latest pointer **only after all expected model/optim/scheduler/trainer plus 8 rank sidecars are complete, readable and proven**. Any single rank failure/late write leaves prior complete latest untouched. No generic `easy_io` global behavior change, no interference with async/object-store path. If fatal rank process dies, job must fail without falsely promoting latest, bounded by process-group timeout. Test delayed rank7, failed rank, torn temp files/pointer, post-crash reopen, no premature latest and no hanging. Full 8-rank Save→Resume is still a later separately authorized GPU Gate.

### C-P0-04 — HIGH: strict RNG isn't actually strict under missing rank + conditional reseed

- **Code:** Child `cosmos_framework/checkpoint/dcp.py:929–955`, `cosmos_framework/utils/generator/rand_state.py:11–39`, `cosmos_framework/trainer/__init__.py:287–300,323–331`.
- **Root cause:** Missing `rng_state_<rank>` means DCP loader excludes it and continues; deterministic-algorithms-enabled path resets global seed after checkpoint load, overriding a previously restored per-rank RNG. A non-bitwise numerical training path still needs **exact stored RNG/state resume semantics**, especially consumer-keyed CFG and scheduling identity; retrospective B1 repeat tolerance does not remove this requirement.
- **Acceptance:** Warm-start only model from DROID can legitimately have no training RNG. Strict **same-job** resume requires rank-specific RNG metadata **all leaves** (torch CPU/CUDA, numpy length/bytes, Python length/bytes), all 8 ranks; missing whole key or one leaf fails BEFORE any continued consumer. Preserve valid saved RNG after load even if deterministic algorithm mode enabled; keep explicit Fresh seeding. Tests both modes, all missing/partial cases, consistent next random sample, and existing successful strict resume. Do not broaden to unsafe loading of old Index8 checkpoint or modify historical DCP files.

### C-P0-05 — HIGH: Fresh/Resume namespace and canonical config ownership

- **Code:** Child `examples/psm_wma_robocasa_corrected_phase5.py:393–415,419–456,603–633`, `cosmos_framework/trainer/__init__.py:138–145`.
- **Root cause:** `--phase fresh` is checked against existing namespace only in bounded-diagnostic branch; ordinary fresh can construct Trainer which writes config.pkl/yaml **before** safe same-job latest incompatibility is noticed. On Resume, existing config may likewise be overwritten prior to exact source identity check.
- **Acceptance:** Atomic single-owner new namespace/claim before any Trainer/logger/config output and before model/DCP writes (rank0 claim + rank-wide fail-closed synchronization). Fresh rejects all existing nonempty directories, symlinks/alias and concurrent claims without changing one byte; Resume first verifies actual stored immutable resolved semantic authority/digest and job path, only then appends new attempt/log in separate namespace without clobbering canonical original config. Check checkpoint latest/digest and source/target mapping. Must use exact new formal Root/Child not V3 docs HEAD.

### C-P0-02 — HIGH: formal100 / 101 execution boundary with stable 30k schedule

- **Code:** Child `examples/psm_wma_robocasa_corrected_phase5.py:393–416,537–594,664–684`, `cosmos_framework/trainer/__init__.py:287–300,344–352,424–435`.
- **Root cause:** Current `--stop-after-iter` is fresh bounded-only, `bounded_` namespace and diagnostic-only checkpoint cannot be resumed as formal. Setting max_iter100 alters LR scheduler cycle and config digest; hard kill at latest100 may race sidecar writes.
- **Acceptance:** Add **formal execution-until** integer, separate from `max_iter=30000, warmup=500, save_iter=100` and semantic digest; support Fresh→100 and same-job Resume→500 while checking the first resumed 101 update inside the **same resumed job**. Runner already has `_execution_max_iter`, reuse it if possible; stop only after complete optimizer/Local commit and full DCP save/finish (if at save boundary). Reject limits <=already-completed iteration, >max, mid-GA, foreign/diag namespace. Note: if stop at 101, existing Trainer automatically saves an extra iter101 DCP; allow planning disk accordingly. No diagnostic stop checkpoint imported into formal. Only new job, no old Index8 migration.

### C-P0-01 — MEDIUM: explicit Index8 selection absent

- **Code:** Child `examples/psm_wma_robocasa_corrected_phase5.py:57,537–595`, `cosmos_framework/model/generator/mot/local_memory_grouped_window.py:162–208`; Frozen Index8 exists independently in earlier exact Root/Child but not a selectable branch in current Phase5. V3 Packed128 path fixed and no silent Index8 fallback detected.
- **Disposition:** Maintain eventual dual-mode requirement. Isolate native-layout flag/default, true Index8 callback/transaction/weighted objective, digest/Checkpoint identity and telemetry consistency on an independent compatibility branch/Gate. Test that explicit mode runs, unspecified packed, exception never auto fallback, full/partial and cross-layout resume rejects. Do NOT merge into the first formally frozen new Packed128 training pair unless user explicitly approves and the compatibility code receives its own full acceptance. V2 A2 success and older frozen Index8 code are references, not proof of a new combined selector.

### C-P0-06 & P1 hidden semantics/config

- **Code:** V3 `cosmos_framework/model/generator/mot/local_memory_grouped_window.py:69–95,162–243`; `cosmos_framework/trainer/local_memory_grouped.py:257–326`; `examples/psm_wma_robocasa_corrected_phase5.py:199–235,250–287`.
- **Evidence Gate not default code rewrite:** full/terminal per-rank actual counts and loss coefficients, native Action/Vision/aux presence, CFG/masks raw15/state15/horizon16, Local Prefix S0/continuation, each rank eligible **nonempty** Local slow shards and true post-update optimizer/fast-state behavior. V3 sums `n_member/n_window * native_total`; V2 weighted aux differently in terminal partial. Existing evidence doesn't prove actual nonzero Dense aux; **observe before modifying objective**. Prevent stale index/prefix/episode carry. Freeze semantics-bearing resolved config (loss coefficients, normalization, precision, optimizer WD/skip patterns, seed/deterministic, native-layout, RNG mode) **without hashing allowed execution budget, phase, exact load_path** in the same-job invariant; full resolved config still archived separately. Evaluate early 1–2 task real action/controller/online-Local ABI on separately authorized stage, don't infer from loss. `off|required` currently available; `init` not automatically.
- **Storage admission**: DS last reported ~47GB free at root with ~595GB prior B1 evidence; get live durable-volume/free/quota and commit to retention plan for `save_iter=100`, potential 300 complete checkpoints. Do not delete old B1 or original DCP without Owner authorization.

## 3. Recommended implementation sequence and fresh-review fences

1. **Batch F0, candidate formal implementation:** fail-closed Fresh/Resume namespace, canonical corrected-Phase5 launcher identity, schedule-independent formal execution-until and semantic config identity. Child implementation/test only, root Gitlink update after Child commit; scoped CPU negative + regression. Stop for independent DS CPU Evidence and GPT fresh incremental review.
2. **Batch F1, candidate formal implementation:** synchronous DCP all-rank completion+atomic local latest/sidecars and strict per-rank RNG+no post-restore reseeding; tightly scoped to the new corrected Phase5 profile where possible, no global backward-compat break. Include delayed/failing rank CPU distributed negative. New Root/Child exact SHA, DS fresh evidence, GPT fresh review. No GPU yet.
3. **S0 readiness Evidence**, can be prepared in parallel READ-ONLY by DS: actual output disk capacity and new namespace, pinned index/cached VAE/official DROID/8 rank model and config, baseline Action/Mask/terminal+Aux contract; no old B0/451GB reinspection. Do not fold Codex E1/E2/T1/P1 unrelated optimization into frozen training pair.
4. **GPU gate separately Owner-authorized:** use two stage training jobs at most: true Fresh→100 (first 2–3 step in-process health witnesses), then strict same-job Resume→500 with 101 pre-update RNG+Local/Optimizer continuity check; interim stop after 100 only after **all ranks successfully finalized the DCP**. Early small controller/Local on/off functional sim before long-run. No required new Index8/packed per-FQN parity.
5. **P1 compatibility followup:** separately implement explicit Index8 opt-in to meet final V3 dual-route contract, never silently modify a running Fresh pair, never classify loss of Index8 as resolved just because the helper exists. Can proceed in parallel without merging into new formal training version.

Every change of formal implementation Root or Gitlink needs independent fresh code/evidence review; changed docs HEAD doesn't. **No S0 CPU PASS, GPU training, DCP write, new Fresh/resume Owner authorization has yet been granted by this document.**

## 4. Formal literal and persistence

**`REQUEST_CHANGES`** — Fresh route **design/implementation readiness**; not a new verdict against the unchanged old B1 code, nor an automated stop authorization on already completed historical execution. Existing B0/451GB data and CPU Gate remain CLOSED; historical B1 numerical parity FAIL stays unchanged. Any required code implementation by Codex must be separately approved/committed, DS independent read-only tests, GPT review. Full V3 repo audit deferred.

**Codex implementation request:** `docs/collab/chatgpt/requests/2026-10-16_CODEX_V3_Fresh_P0_safe_start_DCP_RNG_execution_budget_staged_remediation.md`.
