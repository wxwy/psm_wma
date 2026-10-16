# PSM-WMA V3 — Packed128 DROID Fresh 分段训练路线（PROPOSAL）

**日期：2026-10-16**  
**Author:** GPT / technical-route review  
**状态：PROPOSAL / NOT_GPU_AUTHORIZATION / NOT_FORMAL_GATE_VERDICT。** 当前明确的是工作路线选择，不构成新 GPU Training、Formal30k、DCP 写入的 Owner 执行批准。代码改动由 Codex，新 SHA DS 独立 CPU/GPU Evidence，GPT 做独立 Gate 评审。

## 0. 现状与路径分叉

- V2 当前 Root `b13024456e313b545871a0d5de07f5495848f4e3` / Child `e3dc9ecce0a4a7223245dc4f5b5efde7b709fd92`，历史 V2 A2 8×A100 LIBERO 长训至 iter3288、iter3200 Checkpoint、iter3000 LIBERO 358/400=89.5%（Owner-archived evidence，非 V3 RoboCasa 结果）。详见 `artifacts/g0/localmem_ttt_a2_training_full_record_iter3288_2026-09-22.md` 与 `2026-10-16_V2_A2_Packed128_training_reference_for_V3_Fresh_training.md`。
- V3 已冻结 B1 原诊断 Root `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0` / Child `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`；Frozen SOURCE `b159f459.../937066ff...`，Frozen Packed128 TARGET `c4731bca.../c8dabbb3...`。8 GPU jobs all completed, but strict Owner-frozen r2 cross-implementation and same-leg repeat numerical parity **FAIL**. This historical Gate remains `REQUEST_CHANGES` and is **not retrospectively approved, bypassed or reinterpreted**.
- Formal old Index8 iter1300 DCP is immutable and should not be used for silent cross-layout same-job Resume. `Gate M` migration route stays HOLD, but an **independent Fresh-from-DROID experiment does not depend on old migration**.
- GitHub remote `V3` at planning time: docs HEAD `c4671424cd3505819d827a08aa9550bb79e42d8c`, production implementation baseline Root `2f4dec43eb6b1e35b33a99d844d67813df5922a6` / Child-Gitlink `1d56320c08c56b0f8dd248919d152d81ae12ea7b`. Current Child is 13 commits ahead of frozen B1 Target Child and has trusted startup/consumer keyed RNG, prefetch and telemetry changes. **Before any new execution, recheck remote, choose and freeze ONE exact production implementation pair, obtain fresh scoped Gate.** Do not use docs HEAD in place of implementation identity and do not merge Codex E1/E2 work without its own acceptance.

## 1. New thesis and what constitutes evidence

**V3 Fresh Packed128 is a separately specified algorithm/training path, not an attempt to recreate the same gradient as old Index8 at iter1300.** The required evidence is:
- Correct actual batch semantics: `T=16`, `B_stream=8`, `GA=2`, `K_local=4`, 8×H100 FSDP8, `raw15/state15`, horizon16, left_wrist/use_state, exact previous offline-accepted index/cached VAE.
- Model: native Cosmos3-Edge DROID action policy initial weights; Generation/Action/Local slow optimizer FQNs exactly selected; `S0` lacks a Local prefix and later consumers receive the correct episode state; no cross-episode/cross-slot stale carry.
- Valid-consumer weighting and native Action/Vision/aux losses, including `full` and `terminal_partial` counts; high-level old V2 Native group control supports architecture but its replicated Local params, LIBERO action ABI and full-T16 assumptions do **not** prove new V3 distributed behavior.
- Actual optimizer/FSDP update; all-rank nonfinite detection and nonempty Local slow gradients where expected; candidate fast state published only after real optimizer success; no masked-in 0-loss bug.
- A complete, isolated **fresh formal Checkpoint save then strict same-job resume** of model/optimizer/scheduler/trainer and 8 rank dataloader/Local Sidecar/frontier, at correct iteration with no replay/skip or changed DCP identity.
- Fixed-seed RoboCasa task-level rollout and Local-TTT ablations; Loss reduction or inner loss alone does not prove online memory contributes to SR.

## 2. Phased execution plan and gates

| Stage | Scope | Acceptance / STOP | Owner role |
|---|---|---|---|
| S0 — freeze/preflight & lightweight semantic risk gate | Choose new exact V3 formal pair; fresh namespace; inspect only prior B1 JSON metadata and relevant code for source/token/raw15/valid-mask/Local prefix/real aux and terminal weighting; check disk quota | Root+Child/Gitlink clean; accepted index reused without rescan; no action-codec/layout mismatch; no observed empty/nonempty Slow parameter accounting bug; enough separate durable space for >=2 real DCP checkpoints + in-progress writes with margin; any mismatch or capacity failure => STOP | Codex code only if real bug; DS read-only preflight; GPT narrowed code/evidence gate |
| S1a — fresh bounded native 3-step | Diagnostic-only DROID fresh, same formal training config geometry, `--stop-after-iter 3`, distinct `bounded_` namespace; permit only with new Owner GPU approval | Actual all-8 ranks finite native outputs/grads; exact consumer IDs/Local prefix/action & vision losses; sampled nonempty Local slow gradients and optimizer updates; correct group counts; zero persistent pollution. **No diagnostic checkpoint may become formal Resume source.** | DS GPU test, GPT focused result |
| S1b — true Fresh Formal 1–100 | New clean formal job `--phase fresh`, official DROID DCP, `max_iter=30000,warmup=500,save_iter=100`; unchanged index/cache. Complete first real iter100 checkpoint, stop safely **after** verified save/latest | 8 rank model/optim/scheduler/trainer+rank dataloader Local/frontier, complete DCP; no checkpoint-size/symlink/metadata inconsistency; avoid stopping in active save; no out-of-disk | Owner manual training authorization; DS runs/monitors; GPT Save Gate |
| S1c — same-job Resume 100→101 | New worktree same SHA, same formal job namespace; `--phase resume` strict from latest; no restoration patch/bypass | 100→101 continuity, Local frontier/cursor, optimizer step+LR, sidecar, all8 ranks verified; actual loss finite; no replay/skip; failure blocks further Formal30k | DS independent evidence; GPT Resume Gate |
| S2 — 101→500 training-health | Preserve exact config and new job; rank0 every-step observer + lower-cadence all-rank health audits; model stays packed | finite action/vision/outer, local inner/fast updates within sensible bounds, genuine nonzero action/Local slow grads on eligible shards, no invalid consumers/epoch reuse; throughput/VRAM measured **on real workload**, not predicted; stable DCP | DS monitoring; GPT only on anomalies |
| S3 — 500→2000 task-performance screening | At 500 run 18 underlying RoboCasa target-atomic tasks ×1 fixed seed screening (not statistical SR); at 2000 expand to matched tasks with multiple seeds and action/pose/unit checks | Action decoder yields valid simulator commands and no systematic invalid actions; one bad early SR does not automatically imply bug, but persistent 0-SR combined with failed task decoding/semantic witnesses STOP; no RL/RECAP rescue of 0-SR baseline | DS eval; GPT analyzes task-level, video/error evidence |
| S4 — 2000→30000, model+ablation | If S3 promising, continue stable job; periodic fixed test at ~5k,10k,20k,30k and regular DCP; preserve result provenance; `required`, `off`, and `init` only if explicitly supported/independently validated | SR trend, per-task failure recovery, online TTT incremental value (required vs init), learned Local path (init vs off), wall/VRAM/consumers per update; stop if no learning + broken functional path; quantify evidence even if never reaches30k before final deadline | Owner continue/stop, DS evaluation, GPT scientific final review |

**Initial runtime selection:** Prefer latest accepted V3 production Child `1d56320c...` over obsolete frozen B1 Target if narrow updated pair review passes, but **first 100 steps choose conservative `num_workers=0`, `full_segment_prefetch=False`, and unchanged native transform behavior**, rather than simultaneously introducing an opt-in keyed RNG/full prefetch configuration. If speed is inadequate, an optimization experiment gets a new config/implementation Gate rather than silently changing the live job.

**No mandatory full B1 numerical pairwise r2 check for a new Fresh learning-validity Gate.** The old B1 verdict remains preserved and is not a claim that actual FSDP/local differences are harmless. S0/S1 explicitly guard the same semantic unknowns at lower cost.

## 3. Hidden/silent failures requiring direct checks

| Hidden failure not detected by ordinary training loss | Directed witness |
|---|---|
| wrong RoboCasa frame/base/action coding, wrong horizon or vision alignment | source→model→simulator action codec/shape/pose roundtrip with known episodes; no full dataset rescan |
| masked-out or mis-normalized action/vision loss / auxiliary double-weight | real native output component presence and member/terminal effective count; controlled small fixture |
| Local-TTT learns as a decorative branch only | `S0 None`, continued prefix, nonempty Slow gradient & update and fast carry; later required/init/off task-level |
| FSDP empty shards hide all-rank missing Local grads or unsynced parameter state | per-rank selected-FQN/local shard role accounting, explicitly separate legitimate `numel=0` from absent gradient |
| episode/slot sidecar cross-contamination | episode ID/cursor/frontier/terminal rebind audits; never combine unverified episode states |
| good loss but corrupt Save→Resume | actual full formal iter100 DCP, 8 rank sidecars, strict 101 continuation and correct scheduler/optimizer step |
| apparent throughput improvements from truncated telemetry denominator | retain old step-wall scope and separately measure post-commit telemetry/end-to-end; no silent metric relabel |

## 4. Calendar / resource-management guidance

Hard delivery context is ~2026-11-30. Provisional execution targets (not runtime promises):
- Oct16–20 S0/S1a, plan exact SHA and free durable disk/output; GPU authorization separately.
- Oct20–24 S1b/S1c formal100 Save→Resume and S2 to500.
- Oct24–Nov5 S3 fixed-seed RoboCasa evaluation and to~2000, concurrently validate evaluation queue Codex E1 before trusting all-task summaries.
- Nov5–Nov23 S4 longer training + checkpoints and task-level evaluations paced by observed step p50/p95, not guessed GPU speed.
- Nov24–Nov30 freeze results, required/off/init ablations (if available), replay demos, technical report and final V3 full audit. Training may need to stop earlier than 30k to preserve evidence/working demo if measured ETA conflicts with deadline.

Storage: DS reported root only ~47GB available while B1 raw evidence occupies ~595GB. Before S1b allocate **new durable output with enough space for at least two observed-size Checkpoints plus staging/logs and safety margin**. Do not delete, rename or overwrite B1 evidence without separate Owner authorization; record original DCP and new job as distinct namespaces.

## 5. Explicit scope boundaries and role assignments

- **Owner:** decide accept proposal and separately authorize new exact formal-pair GPU Fresh/Save/Resume and long-run continuation; may adjust *new* prospective experiment metrics, but cannot change historical r2 evidence verdict.
- **GPT:** independent scoped design/code/Evidence/Gate review. New implementation SHA => fresh incremental review; same SHA and additional Evidence => only missing-scoped acceptance.
- **DS_PRO:** independent READ-ONLY CPU/GPU verification and report; no GitHub production code modifications. Can issue stop/error evidence and run Owner-authorized isolated jobs.
- **Codex:** only approved production code fixes + CPU tests; currently independent E1/E2/T1/P1 workflow does not automatically merge into the chosen Formal30k pair.
- No B0/451GB repeat, no unrelated V3 full-repo review before final stage, no old B1 source/target alteration, no silent Index8 iter1300 cross-layout migration, no early `Gate M`/Formal30k approval in this **proposal**.

**Planning decision recommendation:** `B1 strict parity path = archived technical FAIL`; `new independent Packed128 Fresh learning+Save/Resume+real SR route = proposed critical path`. No training was launched by creating this document.
