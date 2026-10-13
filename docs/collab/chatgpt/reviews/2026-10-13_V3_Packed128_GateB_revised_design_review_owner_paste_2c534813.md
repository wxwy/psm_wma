# Independent review — V3 Packed128 Gate B revised comparator and iter1300 migration design

**Date:** 2026-10-13  
**Reviewer:** GPT — independent design / evidence / Gate auditor  
**Submitted artifact:** DS_PRO user-pasted `V3 Packed128 Gate B（GPU 梯度等价）与 iter1300 跨布局迁移 · 修订方案` (2026-10-13), exact attachment SHA256 **`2c534813a8f832365248fabba8342c6d4084719c1754cddd07d451cf9eac5798`**, 414 logical content lines. The claimed project report path `docs/collab/chatgpt/DS_PRO_V3_PACKED128_GATE_B_AND_ITER1300_MIGRATION_REVISED_PLAN_2026-10-13.md` is **NOT present** on `origin/V3` at audit time; review binds to that pasted exact source digest, not an invented design commit SHA.  
**Frozen implementation comparator:** Index8 Root `b159f45906f7261d028aecc226ab7f2bb9807eb9` / Child `937066ffd90f2bf783ad4fbb4909e9c0b8922982`; Packed128 Root `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / Child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`.  
**Non-target full prefetch:** Root `d45712a37318357ba2f57bde3d0f1f448aabbbd9` / Child `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`; CPU Gate C0 remains CLOSED and is not reopened by this report.  
**Verdict:** **REQUEST_CHANGES** for Gate B *design readiness* and cross-layout migration *design readiness*. No runtime/GPU test or implementation verdict. No change in formal implementation pair; no repeated code audit.

## Previous blocker disposition (incremental)

- Previous B1 (wrong mixed Index8 root/child): **CLOSED**. DS §1–2 correctly pins the real formal Index8 producer `b159f459/937066ff` and standalone Packed `c4731bca/c8dabbb3`.
- Previous B2 (new target digest must not equal old source digest): **CONCEPT ACCEPTED, end-to-end design still BLOCKED** as B-GPU01 and B-MIG01 below. DS correctly recognizes native layout in config_digest and forbidden direct strict restore.
- Previous B3 (unjustified `1e-6` universal numeric thresholds): **PARTIALLY REMEDIATED**. DS proposes datatype splits and D1 references, but comparator requirements still lack deterministic witnesses, valid near-zero handling and calibrated FQN-group reductions; see B-GPU02/B-GPU04.
- Previous B4 (16 vs 17 checkpoint profile tuple): **CLOSED at supplied-evidence level**. DS provides 17-element raw tuples rank0 starts 0, rank7 starts 7; source `cosmos_framework/trainer/local_memory_grouped_resume.py:31–52` independently confirms 17-field profile. Raw DCP sidecars were not directly available to GPT; claim is DS reported, not GPT re-run.
- Previous B5 (exact Native calls): **CLOSED as full-member shape contract** — 2 forwards/2 backwards per successful GA2/rank in Packed mode. DS still incorrectly treats 256/2048 as unconditional *valid* consumers even for terminal partial; see B-GPU05.

## Current blockers (only new or incompletely closed)

### B-GPU01 — HIGH — Gate B execution is circular with not-yet-implemented migration; supplied commands cannot load old iter1300

- **DS location:** §2.2 lines 54–55; §6.2 lines 160–162; §8 T2/T12 lines 236/246; §9.1 lines 263–310; §12 lines 392–395.
- **Source:** `examples/psm_wma_robocasa_corrected_phase5.py:303–317` obtains resume from `<output-root>/psm_wma_v3/corrected_phase5/<job-name>/checkpoints/latest_checkpoint.txt`; `:386–409` makes `--stop-after-iter` fresh-only and forbids resume of bounded names. `cosmos_framework/trainer/local_memory_grouped_resume.py:119–124,170–181` enforces source-vs-target digest. No Gate B portable cross-layout resume API exists in pinned target.
- **Cause:** §2.2 requires target `--phase resume` via a **controlled migration path**, while §12 forbids implementing that migration before Gate B passes. The two proposed `--phase resume --job-name gateb_*` jobs have **no pre-existing valid same-job latest/DCP**. The source Index8 DCP cannot pass Packed digest checks.
- **Frozen contract violated:** separate numerical **no-production-write** comparator from later one-time checkpoint publish/migration. No bypass/forgery of strict resume; no owner-authorized GPU execution yet.
- **Acceptance:** redesign Gate B as an isolated, reviewed *transient* pair-state comparator (matched initial weights/optimizer/Local state and frozen consumer witnesses, no target-DCP publication); independently demonstrate old original-pair strict DCP load under its own source namespace only when separately authorized. Remove Gate B T2/T12 target strict cross-layout restore until subsequent migration Gate. Provide real bounded 2-step harness entrypoint/config/run matrix and guard that neither comparator can write old DCP, target migration namespace or formal pointer. Move CLI resume examples under migration-only chapter, or replace with actually executable comparator commands following harness review.

### B-GPU02 — HIGH — same global RNG seed/state cannot guarantee matched per-consumer sigma/noise/CFG across Index8 and Packed128

- **DS location:** §6.3 lines 164–171 and §8 T4 line 238: same 8-rank RNG restoration, per-consumer exact noise/mask, plus six cross-layout RNG fields BIT_EXACT; no explicit working injection scheme.
- **Source:** `cosmos_framework/model/generator/omni_mot_model.py:1409–1440` samples per-batch vision/action timesteps; old `cosmos_framework/model/generator/mot/local_memory_grouped_window.py` @`937066ff` iterates indices and calls native loss/backward per index (old lines 131–150), while Packed `c8dabbb3` uses one slot-major call/member (new lines 191–208). `cosmos_framework/model/generator/mot/robocasa_exact_window_local.py:346–383` performs prompt transform during member materialize; model RNG consumption before the following GA can perturb global Python/Torch state.
- **Cause:** reshaped call count/batching changes RNG draw schedule. A shared seed or restoring the same RNG snapshot does not establish same per-consumer noise, sigma or CFG, nor bitwise equality of post-step global RNG state. Identical random inputs and identical end-of-step native RNG state are different requirements.
- **Acceptance:** specify an exact consumer identity-keyed random witness (all relevant stochastic draw sites and tensor shapes, CFG masks, vision/action sigma, noise, any stochastic model op), captured/replayed identically on both sides *before F/B* or injected into isolated harness, with explicit no-missing-consumer validation. Compare native RNG continuation **within each mode** for repeatability; do not require naturally bit-exact post-step RNG streams **across layouts**, unless an explicit RNG consumption-preserving mechanism is implemented and proved. Show no accidental main/worker RNG mutation. Avoid production code changes for comparator.

### B-MIG01 — HIGH — migration sidecar extra keys and nested provenance need schema-safe treatment

- **DS location:** §10.3–10.5 lines 340–361, especially §10.4 line 354 proposing `migration_source` in sidecar “or manifest”, and line 351 “restamped sidecar”.
- **Source:** `cosmos_framework/trainer/local_memory_grouped_resume.py:99–124` requires **exact top-level sidecar key set**; `:168–181` also requires `SegmentProvenance.config_digest == target config_digest` for **each** saved active record; `:125–166` validates slot/frontier chronology.
- **Cause:** adding `migration_source` to existing top-level `rank_*.pkl` state makes strict restore fail even if digest is correct; replacing just the top-level `config_digest` without updating and validating each nested `SegmentProvenance` also fails.
- **Acceptance:** freeze external `MIGRATION_MANIFEST.json` as *sole new metadata schema*, do not append fields to exact-key sidecars unless explicitly versioning/reviewing a separate schema change. Define source-first validation then verified translation for top-level digest **and each active record's nested provenance digest**, preserving all other identity, manifest, source, frontier, scheduler and fp32 fast-state bytes/values; verify destination with unchanged `restore_grouped_local_state` strict authority in isolation. Define atomic publish and source-byte invariants. Implementation and real load remain later authorized Gate.

### B-GPU03 — MEDIUM — weighted auxiliary/reduction equality is asserted without freezing actual runtime loss configuration

- **DS location:** §6.4 lines 173–176 and §8 T5 line 239.
- **Source:** Packed `cosmos_framework/model/generator/mot/local_memory_grouped_window.py:200–208` uses `loss * member_count/window_count`, old Index8 groups per-index weights. `cosmos_framework/model/generator/omni_mot_model.py:2010–2040` can scale sample-level loss and compute additional batch-level MoE LBL auxiliary; `cosmos_framework/model/generator/utils/load_balancing_stats.py:18–24` defaults LBL coefficients to None, but final resolved model config remains an execution authority.
- **Cause:** `n_member/n_window * L_native` matches true per-consumer means only if each relevant loss component's reduction is sample-additive and any batch-dependent aux/global scaling is absent or correctly accounted for. Current plan cannot presume total/action/vision/inner/aux equality from outer weighting alone.
- **Acceptance:** inspect **resolved exact recipe/config at both pinned pairs**: loss normalization, LBL coeff/method, sample_level_loss_averaging and any MoE aux; register whether aux is truly OFF, or provide separate mathematically sound reference/gradient comparator for active aux. Record weighted *component* losses and same optimizer-gradient objective; fail closed on unmatched terms.

### B-GPU04 — MEDIUM — numeric tolerance rule underspecified for near-zero FQNs and stochastic zero/noise calibration

- **DS location:** §7.2–7.3 lines 214–227 and §8 T6/T11.
- **Cause:** existing D1 `atol+rtol` per-element comparisons do not directly define per-FQN relative-L2/cosine pass criteria; undefined cosine/relative error on near-zero or zero gradients; K=3 times run2run envelope is effectively zero when same-mode reruns are deterministic. Two reruns per mode alone do not estimate a stable per-FQN noise quantile. Actual grad storage dtype may not equal forward BF16.
- **Acceptance:** preregister exact per-FQN (or frozen family aggregation) formulas with a fixed absolute floor/epsilon for near-zero, cosine defined/not-applicable criteria, elementwise and norm thresholds, group aggregation, FP32 vs BF16 by **actual grad dtype**, and a fixed numerical/non-stochastic floor for K-envelope zero cases; differentiate baseline deterministic parity from repeated-run variation. Never choose/adapt tolerance after seeing cross-mode residuals.

### B-GPU05 — MEDIUM — 256/rank and 2048/step are ceilings, not unconditional valid-consumer counts

- **DS location:** §6.1 lines 153–156, §8 T3 line 237.
- **Source:** `cosmos_framework/model/generator/mot/robocasa_exact_window_local.py:270–292` sets `valid_count = min(T, remaining)` and `member_counts=sum(valid_count)`; Packed `local_memory_grouped_window.py:193–208` weights actual member counts.
- **Cause:** terminal partial may produce fewer than 128/member and 256/rank. Gate B anchored to iter1300 has not shown that next two planned windows are fully populated. A strict 2048-valid-consumer requirement can falsely fail valid terminal cases or tempt dropping partial consumers.
- **Acceptance:** first assert actual read-only `plan.member_counts` per rank for the frozen test windows; require exact equality across both sides and `0<n_window<=256` per rank, not unconditional 256; still exactly 2 native calls for successful GA2; add at least one explicit terminal-partial parity witness or state separately scoped follow-on.

### B-DOC01 — MEDIUM — claimed canonical request missing is inaccurate for origin/V3; revised design not yet frozen in repo

- **DS location:** introduction line 7, §1.1 line 28, §13 lines 404–409.
- **GitHub evidence:** `origin/V3` **does** contain `docs/collab/chatgpt/requests/2026-10-13_DS_PRO_revise_GateB_index8_packed128_checkpoint_migration_plan.md`, fetched directly; the pasted revised-plan path returned 404. The local Formal30k root `b159f459` is **not current origin/V3 HEAD**; distinguish frozen execution worktree vs docs branch HEAD.
- **Acceptance:** DS checks exact `origin/V3` in isolated docs checkout and records HEAD, request blob, actual plan artifact commit SHA. Commit corrected design under canonical repo path without touching implementation pair or formal training tree. Do not pretend that an uploaded report has a design SHA that is not yet committed. The supplied exact attachment SHA256 is temporary review identity.

## Scope and decision

**Current recommendation:** `REQUEST_CHANGES` for revised Gate B and migration **design**. This does not overturn prior Packed128 **Gate A CPU approval** or Full Segment Prefetch **C0 CPU closure**. Previous B1/B4 and exact-native-count wording are closed. Current implementation is not adjudicated defective by this *design* review.

**No GPU Gate B authorization; no torchrun, real DCP loading/migration, checkpoint writes, Formal30k change, actual training/inference or Nsight.** The original iter1300 remains the only future continuation source; failed iter1400 excluded. Priority is a small, executable, fail-closed *numerical-only* comparator and owner-reviewed harness design, then separately gated GPU execution; thereafter migration implementation/validation and iter1301 formal continuation. Full Segment Prefetch performance remains nonblocking and separately gated.

**Suggested remediation handoff:** `docs/collab/chatgpt/requests/2026-10-13_DS_PRO_V3_GateB_round2_design_remediation.md`.
