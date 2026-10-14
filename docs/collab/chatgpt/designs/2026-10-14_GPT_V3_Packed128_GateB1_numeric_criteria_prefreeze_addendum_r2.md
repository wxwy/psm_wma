# V3 Packed128 Gate B1 — 数值判据预冻结增量方案 r2

**Date:** 2026-10-14
**Author:** GPT
**Status:** PROPOSED / OWNER_NUMERIC_FREEZE_PENDING / B1_HARNESS_NOT_IMPLEMENTED / GPU_NOT_AUTHORIZED / GATE_M_HOLD
**Basis:** GPT Gate B0 APPROVE ec9d162b; original Round2 §6 and B1 r1; GPT incremental evidence review 2026-10-14_V3_Packed128_GateB1_DS_PRO_numeric_criteria_evidence_review_corrected_phase5_authority.md.
**Comparator SOURCE:** Index8 Root b159f45906f7261d028aecc226ab7f2bb9807eb9 / Child 937066ffd90f2bf783ad4fbb4909e9c0b8922982.
**Comparator TARGET:** Packed128 Root c4731bca1a590663db88bd6cd74dbcf9fd513a85 / Child c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686.

## 1. Correct config authority (not H3-E or H3-F)

The actual iter1300 producer/B1 comparison is examples/psm_wma_robocasa_corrected_phase5.py. Its config_digest hashes native_batch_layout and runtime resolved optimizer/mesh/cache/schedule. examples/psm_wma_robocasa_h100.py:213-224 hashes a different Stage-A/H3E authority and has no native layout term; it CANNOT independently explain the Source vs Packed digest split. Same for H3F. The code diff between the exact Child SHAs contains FIVE changes within cosmos_framework plus SIX within examples (11 total), including corrected_phase5 and telemetry.

Source-derived recipe candidates pending two exact-pair resolved-config witnesses:
- experiment action_policy_robocasa_edge inherits action_policy_robocasa_nano optimizer weight_decay=0.05, LR base 5e-5, beta=(0.9,0.99), eps=1e-8; adds per-FQN weight_decay_skip_patterns for action projections. NOT generic sft_config.weight_decay=0.
- EDGE_MODEL_CONFIG has loss_scale=10.0, action_loss_weight=10.0, train_time_video_distribution=waver, train_time_action_distribution=logitnormal and independent_action_schedule=False, image_loss_scale=None, normalize_loss_by_active=False, lbl coeff None. NOT generic loss_scale=1.0.
- Precision bf16 and configured FSDP fp32-master/bf16-reduce do not by themselves prove actual param.grad dtype, Loss scalar dtype, master-parameter presence or loaded optimizer state. Those require B1 runtime probes.

Until the exact CPU preflight readouts arrive, all these are source-derived EXPECTATIONS, not yet approved runtime invariants. Actual current LR (after warmup at iter1301) must be loaded from scheduler, not set equal to nominal base.

## 2. Three distinct conditioning and stochastic mechanisms

1. Text CFG dropout (NOT inference guidance scale): text_tokenizer.py:52-54,101-106 uses Python random.random() with configured cfg_dropout_rate=0.1, replacing sample caption with blank text. Witness CFG decision, caption bytes and token IDs per Consumer.
2. Vision/Action condition_mask: flow_matching.py:90-129 marks clean versus noised frames and contributes to per-instance loss denominator. Witness mask and valid_count exactly, separately from text CFG.
3. Sigma and epsilon: omni_mot_model.py:2138-2608 and diffusion/rectified_flow.py. Real video flow has configurable waver distribution plus shift; action schedule shares vision sigma unless independent_action_schedule=True. Match exact ConsumerKey and stochastic site for P0 FIXED and P1 MATCHED_STOCHASTIC; no per-native-batch RNG assumptions.

Consumer-count weighting gives mathematically equal objectives ONLY IF loss is per-instance additive and batch-independent; flow_matching.py:158-166 active-only normalization, optional sample-level rank scaling, MoE load-balancing aux and interactions among packed tokens can break unconditional algebraic equivalence. Verify actual resolved switches and individual loss components; unknown active batch-dependent component => BLOCKED.

## 3. Numerical metric definitions (all still UNFROZEN proposals)

For every selected optimizer FQN and tensor role: A=SOURCE, B=TARGET, d=B-A, n=numel. Evaluate metrics FP64 but report real dtype/shard/FQN. Relative L2 = ||d||2/max(||A||2,||B||2,eps_role sqrt(n)); elementwise pass requires |d_i| <= atol_role + rtol_role |A_i| for every element. For normal vectors require elementwise AND relativeL2 limit AND cosine minimum. For both near-zero vectors cosine N/A and require maxAbs <= atol AND RMS(d) <= eps_role; exactly one nearzero is immediate FAIL. NaN/Inf, dtype/FQN/shape mismatch, missing required gradient/optimizer state => FAIL. All FQNs and family groups must individually pass; no average-only acceptance.

### Round2 candidate thresholds A — Loss, Gradient, Local-TTT Fast State

| Role | FP32/FP64 | BF16 gradient |
|---|---|---|
| Loss scalar | atol 1e-6, rtol 1e-5 | atol 2e-2, rtol 2e-2 |
| Grad / Fast State element | atol 1e-6, rtol 1e-4 | atol 2e-2, rtol 2e-2 |
| Grad / Fast State relL2 | <= 2e-3 | <= 3e-2 |
| Grad / Fast State cosine | >= 0.9999 | >= 0.999 |
| Grad / Fast State norm floor (per element) | 1e-7 | 2e-5 |

Four Local Fast State tensors use the FP32 rules; original sample/caption/mask/identity are exact discrete comparisons.

### NEW optimizer update candidate thresholds B — strictly pre-GPU, not yet frozen

Compare *increments*, never only large full weights/states:
- DeltaP = P_after - P_before, authoritative FP32 master copy when present; report visible BF16 weight copyback separately.
- DeltaM1 = exp_avg_after - exp_avg_before; DeltaM2 = exp_avg_sq_after - exp_avg_sq_before. Compare both the absolute moment states (with FP32 gradient role limits) AND their increments (below); accumulated 1300-step large moments must not conceal incorrect updates.
- Unknown/absent FP32 master path or missing moment tensors => BLOCKED until actual optimizer implementation is explicitly audited; no fallback to relative full-weight comparison.

| FP32 increment role | element atol | element rtol | per-FQN relL2 limit | cosine minimum | norm-floor eps |
|---|---:|---:|---:|---:|---:|
| DeltaP (master parameter) | 1e-9 | 3e-2 | 3e-2 | 0.999 | 1e-10 |
| DeltaM1 (Adam first moment) | 1e-8 | 3e-2 | 3e-2 | 0.999 | 1e-9 |
| DeltaM2 (Adam second moment) | 1e-12 | 6e-2 | 5e-2 | 0.995 | 1e-13 |

These candidate values were proposed WITHOUT seeing any V3 GPU residual. Do not adopt without the Owner and passing CPU negative fixtures. BF16 visible weights and non-FP32 masters need a separately justified policy before GPU readiness. Every optimizer-selected FQN (generation/action/local) must be covered.

Discrete contracts: Consumer identity/validity/prefix S0 absence/transform token bytes/CFG decisions/identically keyed sigma+epsilon bytes, optimizer FQN inventory and step integer, Local frontier/sidecar/scheduler, GradScaler enabled/skipped-step and model per-field tensor geometry must match exactly. Scheduler/optimizer scalar LR must have identical configured semantics, and numerical scalar comparison if necessary uses atol 1e-12 rtol 1e-9. Two consecutive post-iter1300 steps, two same-witness repeat runs/leg, all four combinations Full×P0, Full×P1, Terminal×P0, Terminal×P1. Run2run within the same declared limits, otherwise BLOCKED_UNSTABLE.

### Mandatory CPU negative tests before numerical freeze

- Initial FP32 weight ~1000; SOURCE tiny nonzero DeltaP=1e-5, TARGET DeltaP=0. Whole-weight comparison would appear similar but DeltaP test MUST fail.
- Old accumulated m1/m2 large, one side nonzero DeltaM1=1e-3 or DeltaM2=1e-6, other zero => MUST fail despite similar absolute state.
- Low but nonzero BF16 gradient vs zero => MUST fail by one-sided nearzero/relativeL2 even if loose elementwise BF16 atol would pass.
- Missing action/local selected FQN, absent shard, null required grad, nonfinite, mismatched CFG/token/mask or noise, untracked site, active aux or non-additive loss must independently FAIL/BLOCK.
- Fail-close on wrong Root/Child, ConfigDigest, dataloader state translation, checkpoint mutation or forbidden save.

## 4. Controlled execution

1. DS_PRO one batch of CPU-only read-only CONFIG RECEIPT on the **corrected_phase5** pinned Source and Target: actual SHA/import path, fully resolved optimizer / model precision / loss / RF train-time distributions and shifts / LBL / trainer callbacks / grad scaler / selected key lists / scheduler / config_digest (including native layout), and complete 11-file diff manifest. No models instantiated, no GPU and no training.
2. GPT verifies response and completes code-level CPU negative metric tests; obtains Owner threshold signoff. This may be developed alongside isolated B1-S1 implementation ONLY IF implementation authorization is granted; no automatic GPU.
3. New real FSDP8 B1 Comparator (NOT CPU B0 paired-run) must receive exact-new-SHA independent code review of strict 4-component load, in-memory sidecar translation, original callback/GA2 semantics, site-complete RNG, delta/moment metrics and safety barrier.
4. Separate Owner GPU approval then enables 8×H100 FOUR-combination bounded proof. B1 numerical PASS is required before separate Gate M migration and Formal30k iter1301 approval.

**State:** B0 APPROVE/CLOSED; B1 design only; numeric thresholds NOT Owner frozen; B1 GPU, Gate M, Formal30k HOLD.
