# V3 Gate B1 — r2 数值阈值 Owner 正式冻结（GPU 前）

**Date:** 2026-10-15  
**Authority:** Owner 在当前会话明确答复“都同意，执行”，同意 r2 数值判据与 B1-GPU-IO-01 修复。  
**Status:** **OWNER_NUMERIC_THRESHOLDS_FROZEN_R2 / GPU_NOT_AUTHORIZED**。数值标准批准 **不是**真实8×H100运行授权。  
**Frozen policy schema:** `psm_v3_gate_b1_r2_owner_numeric_policy_v1`  
**Policy SHA256 (sort_keys=True/separators=(',',':'), UTF-8 canonical JSON):** `bcb9f8d699c0ce6c79d54cf5bb213c157665798c38dae9daeb6b4a1607e63fda`。  
**Implementation location:** isolated diagnostic `tools/gates/v3_gateb1_authority.py`; code SHA **`46e9cc0e5dc97a1f7f813b2a332b095aa1062a4a`**, Child/Gitlink `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`. This implementation is a **candidate awaiting DS_PRO CPU verification and GPT new-formal-pair review**, not yet an APPROVED GPU Gate.  
**Baseline:** `docs/collab/chatgpt/designs/2026-10-14_GPT_V3_Packed128_GateB1_numeric_criteria_prefreeze_addendum_r2.md` and frozen Round2 §6; no GPU discrepancy observed before freezing.

## 1. Frozen numeric limits — exact r2 values

Every selected optimizer FQN must PASS individually, for both legs, eight ranks, both post-1300 GA2 steps, P0 and P1, Full and Terminal Partial, two independent same-witness repeats. No aggregate/mean hiding a failed FQN.

| Role / observed dtype | element atol | element rtol | per-FQN relative L2 maximum | cosine minimum | per-element norm floor |
|---|---:|---:|---:|---:|---:|
| Selected Gradient FP32/FP64 | 1e-6 | 1e-4 | 2e-3 (0.2%) | 0.9999 | 1e-7 |
| Selected Gradient BF16 | 2e-2 | 2e-2 | 3e-2 (3%) | 0.999 | 2e-5 |
| Local-TTT Fast State (each of FOUR FP32 tensors/slot) | 1e-6 | 1e-4 | 2e-3 | 0.9999 | 1e-7 |
| FP32 Master ΔParameter | 1e-9 | 3e-2 | 3e-2 | 0.999 | 1e-10 |
| FP32 Adam ΔM1 | 1e-8 | 3e-2 | 3e-2 | 0.999 | 1e-9 |
| FP32 Adam ΔM2 | 1e-12 | 6e-2 | 5e-2 | 0.995 | 1e-13 |

Loss scalar (each active weighted component): FP32/FP64 **atol 1e-6 / rtol 1e-5**; BF16 scalar **atol 2e-2 / rtol 2e-2**. The current diagnostic weighted-loss capture converts to FP32 for comparison; it therefore uses the **stricter FP32 thresholds** on the observed captured scalar. A future implementation must not silently claim BF16 native-loss accuracy from FP32 capture alone.

Use FP64 for diagnostic math. Elementwise for all i: `abs(T_i-S_i) <= atol + rtol*abs(S_i)`; for non-nearzero tensors require **elementwise AND relative L2 AND cosine**. Both near-zero: no cosine; require maxAbs ≤ atol AND RMS(delta) ≤ norm floor. One-sided near-zero is **FAIL**, as are missing FQN/gradient, unexpected dtype or shard, NaN/Inf, missing action/local/generation family, unsupported optimizer master/moment or mismatched identity.

Optimizer tests measure **increments** ΔP/ΔM1/ΔM2 (not only full before/after values), and compare absolute moment states as well; huge initial weights or accumulated moments must not conceal an erroneous tiny update. For FSDP only actual selected local-shard FQNs count, and all required FQN inventory must be complete.

## 2. Discrete / stochastic / run stability (strict exact)

Consumer/slot/episode/GA/member/validity/Local prefix S0 absence, source original binding, CFG transform/token payload, matched per-Consumer Vision/Action Sigma/Epsilon, condition-mask hash, source checkpoint, strict Local sidecar/iteration, optimizer step integer and scheduler discrete state must match **exactly**. P0 fixed and P1 matched-stochastic BOTH required; Full and Terminal Partial BOTH required per profile. Two independent repeats per leg use **the same frozen numeric limits** and exact input witness hashes; unstable repeat is `BLOCKED_UNSTABLE` even if cross-leg aggregate loss appears close.

Scheduler/LR numerical scalar tolerance: `atol 1e-12, rtol 1e-9` where floating comparison is needed; discrete counters exact. GradScaler is disabled in frozen config; skipped-step/GradScaler state unexpectedly enabled must FAIL-CLOSED.

## 3. Hard owner boundary

- **No posthoc threshold widening**, no re-freezing based on actual CUDA differences, no substituting other FQN or pair. Unexpected dtype/site/optimizer behavior => BLOCKED and independent root-cause review, not silent tolerance adjustment.
- Sound generation/independent sound scheduling remain disabled and attention dropout=0 for this Gate. If effective runtime differs, FAIL-CLOSED before interpreting results.
- Frozen SOURCE Index8 Root `b159f45906f7261d028aecc226ab7f2bb9807eb9` / Child `937066ffd90f2bf783ad4fbb4909e9c0b8922982`.
- Frozen TARGET Packed128 Root `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / Child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`.
- Original B0 DCP full-shard fingerprint `2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999`. Original `iter_000001300`, latest and 451GB corpus remain unchanged.
- A **future separate Owner GPU receipt** must bind exact future accepted diagnostic implementation SHA, frozen SOURCE/TARGET pair, B0 fingerprint and `numeric_policy_sha256=bcb9f8d6...` and explicitly authorize bounded 8×H100. No such GPU authorization is conferred by this document.

**B1 CPU old code Gate CLOSED. New `46e9cc0e...` DCP/numeric implementation is waiting for independent DS CPU test + GPT incremental review. Gate M/30k Formal resume HOLD.**
