# Independent review — iter1300 DCP static evidence, Packed128 Gate B design, and cross-layout migration

Date: 2026-10-13
Formal implementation pair unchanged: Root c4731bca1a590663db88bd6cd74dbcf9fd513a85 / Child+Gitlink c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686. Current V3 docs HEAD is not a new implementation target. The prior Packed128 Gate A CPU approval stays CLOSED, no repeated code audit of 9 changed files.
Evidence receipt: docs/collab/chatgpt/evidence/2026-10-13_V3_packed128_native/DS_PRO_2026-10-13_iter1300_static_and_GateB_plan_owner_relay_review_receipt.md

## Independent verdict (scoped, not a GPU authorization)

Task 1 — iter1300 STATIC CHECKPOINT COMPLETENESS: PASS / EVIDENCE ACCEPTED (owner-relayed DS evidence, not GPT native DCP load). Four component metadata readable, all32 .distcp shard CRCs pass, eight sidecars iteration1300, trainer/scheduler counters aligned, latest pointer points1300, old config_digest consistent. This supports choosing iter1300 only; does NOT prove restore in target runtime.
Task 2 — Gate B GPU comparison design: REQUEST_CHANGES (three substantive source/authority contract violations).
Task 3 — Index8-to-Packed128 migration design: REQUEST_CHANGES (new digest and Strict Resume workflow contradiction).
Packed128 overall GPU/formal deployment remains HOLD; Gate B unapproved and not executed.

## Current blockers — evidence-specific, NO new production bug proven

**B1 HIGH — wrong exact source Root and baseline identity.**
- Location: DS report §2.2 lines105–109; source root gitlinks.
- Root cause: DS assigns Packed128 Root c4731bca to old Index8 Child5ac9. GitHub shows c4731bca pins new c8dabbb3. Actual live Index8 Formal used b159f459/937066ff (checked Gitlink). If choosing a more recent index8 comparator it is separate e730e306/5ac9a904; old 9370 to 5ac changes telemetry code.
- Frozen contract: each paired run binds an actual root + child + source provenance, and iter1300 must be tied to original producing code, not the new Gitlink.
- Closure: DS write a three-row authority table (original checkpoint producer, optional later Index8 comparator, Packed128 candidate), exact Root/Child/why selected. Build two independent pinned checkouts; do not claim same formal Root for two different Gitlinks.

**B2 HIGH — impossible Packed128 digest equality and strict same-job resume.**
- Location: DS report §3.1 line146, §3.3 line154, §2.5 lines125–128; source examples/psm_wma_robocasa_corrected_phase5.py:57,204,303–317 and cosmos_framework/trainer/local_memory_grouped_resume.py:120–125,172–180.
- Root cause: new Packed128 adds native_batch_layout to config_digest; old source digest is 70e9867f...df37. Both Local top-level config_digest and saved SegmentProvenance.config_digest are matched against new current digest, hence Packed128 cannot Strict Resume old iter1300 as proposed. A new run digest equal to old is NOT a safe condition, it is evidence old layout executed or digest spoofed.
- Frozen contract: original DCP bytes/digest immutable; target new layout has its own honest config digest; failure must be fail-closed, not blanket skip or fake rehash.
- Closure: split (i) Gate B numerical comparator (no mutation to production/old DCP; validated model/opt state loaded into isolated paired test harness, not advertised as successful packed strict resume) from (ii) Owner-authorized one-time migration bootstrap that verifies full old state, records exact old/new digest lineage and intentionally materializes a NEW target-format checkpoint under NEW namespace; then verify ordinary strict resume from that target checkpoint starts iteration1301. Restore old formal Pair against old DCP separately for native restore proof.

**B3 MEDIUM — predeclared numerical thresholds not tailored to actual BF16/FSDP packing.**
- Location: DS report §2.4 lines115–123; source cosmos_framework/model/generator/omni_mot_model.py:1370+ and local_memory_grouped_window.py packed backward.
- Root cause: draft demands loss rel<=1e-6 and gradient max-abs<=1e-6 plus elementwise Fast State equality in distributed BF16, while Index8 vs Packed128 changes packing, kernel reduction and stochastic invocation shapes. That is not a scientifically justified blanket threshold, and a same seed by itself does not pin per-consumer sigma/noise/dropout.
- Frozen contract: parity must compare SAME consumer identities/prefixes/initial states, random tensors, and selected optimizer FQN gradient groups without false failure or adaptive threshold shopping.
- Closure: DS propose reproducible per-consumer (rank, episode, absolute step) sigma/noise/dropout witnesses, fixed-input deterministic/FP32 reference and actual BF16/FSDP comparisons; pre-register separate total/per-group relative L2, cos and near-zero absolute checks; deterministic Local scan state should match under equal initial states and inputs, with numeric tolerances declared before running. Report rankwise raw maxima and full selected FQN coverage, not just averaged grad_norm. Keep optimizer state comparison separate from grad parity.

**B4 MEDIUM — reported profile tuple lacks required per-rank component.**
- Location: DS report §1.6 line69; source cosmos_framework/trainer/local_memory_grouped_resume.py:27–50 (_profile).
- Root cause: DS summary shows a 16-element value starting (8,0,8,2,...) while _profile() has 17 elements and begins (rank, world_size=8, seed=0, b_stream=8, active_ga=2,...). Report simultaneously asserts all eight profiles identical and profile[0]=rank. Likely omission of rank in summary, not proof of broken DCP.
- Frozen contract: each rank-local dataloader sidecar's profile must match its actual _profile(window), including rank-specific first element. Static byte-level completeness remains accepted but exact per-rank semantic restoration is not proven.
- Closure: DS send raw repr length+first5 fields for rank0 and rank7 (or all8), assert tuple len17 and expected per-rank rank positions without modifying any DCP; if raw content is 16 elements escalate as checkpoint restore blocker. This is a narrow read-only evidence clarification.

**B5 LOW — verify exact two native F/B calls, not 'at least two'.**
- Location: DS report §2.5 line129; source cosmos_framework/trainer/local_memory_grouped.py, corrected_telemetry.py pre_optimizer expected len(plan.members).
- Closure: report exactly 2 forwards, exactly2 backwards,256 valid consumers/rank and single optimizer step for GA2; no batch downshift.

## Nonblockers and further boundaries

- The `native_batch_layout` displayed telemetry string does not literally equal `NATIVE_BATCH_LAYOUT` digest marker; already recorded in Gate A as non-blocking alias; do not produce new Child SHA just to rename before GPU.
- Iter1400 owner-confirmed save failed, never a candidate. Do not spend DS efforts proving an unusable saved directory.
- `.metadata` parse, CRC and per-rank file presence are static consistency only; real torch.distributed.checkpoint load, rank-local FSDP/optimizer state shape and RNG restoration are not yet proven. Files do not need to be re-read merely to repeat static evidence.
- The migration may preserve all old model/optim/scheduler/RNG/local state *values*, but a new native-batch layout necessarily changes RNG consumption after iteration1300. Do not claim bitwise identical further training even if next-step parity under controlled inputs passes.
- Current scoped verdict does not authorize GPU, torchrun, inference, evaluation, production checkpoint writes, any source code changes, latest pointer modification, or formal training resume.

DS remediation request: docs/collab/chatgpt/requests/2026-10-13_DS_PRO_revise_GateB_index8_packed128_checkpoint_migration_plan.md
Root docs-only review commit will append to CODEX_INBOX; this does not change Packed128 formal implementation SHA, so Gate A CPU closure remains valid.