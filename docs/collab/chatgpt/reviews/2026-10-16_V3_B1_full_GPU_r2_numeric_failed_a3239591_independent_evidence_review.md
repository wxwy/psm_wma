# PSM-WMA V3 — B1 Full GPU r2 Numeric Gate：首轮独立 Evidence Review

**Date:** 2026-10-16  
**Reviewer:** GPT — independent Code / Evidence / Gate  
**Exact reviewed diagnostic formal implementation:** Root `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0` / Child-Gitlink `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`. GitHub diagnostic branch remains at this Root. **Formal pair unchanged; no repeated implementation review.**  
**Frozen SOURCE:** `b159f45906f7261d028aecc226ab7f2bb9807eb9` / `937066ffd90f2bf783ad4fbb4909e9c0b8922982`.  
**Frozen TARGET:** `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`.  
**Owner r2 policy hash:** `bcb9f8d699c0ce6c79d54cf5bb213c157665798c38dae9daeb6b4a1607e63fda`.  
**Original B0 DCP fp:** `2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999`.  
**Evidence source:** Owner-pasted DS_PRO 2026-10-16 report `V3 B1 GPU 批量执行与冻结 r2 数值比较结果（a3239591）` plus direct GitHub reading of exact `v3_gateb1_compare.py`, `v3_gateb1_metrics.py`, `v3_gateb1_fsdp_capture.py`, `v3_gateb1_native_driver.py`, `v3_gateb1_authority.py`, frozen r2 design. The remote Desktop Commander device is OFFLINE; GPT has **not** independently read the reported 168MB comparator JSON, 595GB tensor captures, transient monkey-patch script, or job logs. Reported counts are not presented as personally rerun verification.  
**Formal Gate verdict:** **`REQUEST_CHANGES` — B1 GPU NUMERIC NON-PARITY AS REPORTED / UNRESOLVED CAUSE; NO GATE CLOSE.** This is **not** a proven Packed128 production code bug; no basis to change frozen Owner thresholds or launch Gate M/Formal30k.

## 1. Verified frozen comparison semantics

- `tools/gates/v3_gateb1_compare.py:79-116` validates exact source/target Root/Child, profile/repeat/rank/iter, full/terminal, per-Consumer identity and stochastic+CFG site hashes **before** numerical metrics. `165-217` requires both P0/P1 and both repeats, compares **64 cross-leg rank-step pairs + 64 same-leg repeat audits**, and still emits `gpu_gate_approved=false` even if all candidate metrics pass.
- `tools/gates/v3_gateb1_metrics.py:83-125` requires same dtype and shape; **original freezes fail-closed on `numel()==0`**; per-element AND relL2 AND cosine for non-nearzero, one-sided nearzero fails; `184-226` enforces six metrics per selected FQN (gradient, ΔP, ΔM1, ΔM2, absolute M1/M2), and all 4 FP32 fast state tensors for every active slot. `229-248` handles scalar loss; no aggregate pass can hide a failing FQN.
- Exact `v3_gateb1_authority.py:17-65` remains unchanged: FP32 gradient and Local Fast State relL2 <=0.002, BF16 gradient <=0.03, FP32 ΔP/ΔM1 <=0.03, FP32 ΔM2 <=0.05, strict elementwise/cosine and loss tolerances.

## 2. Observed DS claims and why B1 cannot close

DS reports:
- All **8 independent 8×H100 two-step jobs exit0**; total **128 JSON + 128 PT**, ~595GB; all 128 lightweight DCP restore witnesses byte-identical `faf63ff224969b5585419bd4432fa9e554ffdf0742831c7a3a2f9972a3c8411b`; original latest stays iter1300; 49/49 sorted stat witnesses unchanged. These support success of execution/restore **as reported**, not numeric parity or independent byte verification by GPT.
- Original comparator initially aborted on **empty FSDP local shards**, including rank4–7 `net.local_memory_runtime.core.slot_queries` tensors shape `(0,64)`. DS then used **uncommitted `/tmp/psm_v3_b1_owner_compare.py` monkey-patch of `compare_tensor`** treating same-dtype/same-shape/both-empty as equal; DS reports Owner quote “都为0，视为一致” but an exact independent approval provenance/receipt is **not attached in this report**. This changes comparator behavior relative to pinned original code, even if mathematically reasonable for a truly empty local shard. Never label the patched output a byte-identical execution of unmodified frozen comparator; request code/scope/provenance for future audit. The numeric policy hash alone does not authenticate the wrapper.
- Despite this only-empty allowance, **`all_candidate_thresholds_pass=false`**. DS reports **64/64 cross-leg** and **64/64 same-leg-repeat** compared cases failing; **60,119 / 241,152** FQN metric cells passing (~24.9%), **1,774 / 2,000** Fast State cells passing (88.7%), plus Loss mismatches. Several nonempty norm/gradient/optimizer tensors fail by a large margin (top ΔM2 relL2 ~1.09 cross-leg, 1.11 repeat); `llm2action.bias` and rank0–3 nonempty `slot_queries` also fail. **It is therefore impossible to close B1 by reinterpreting only-empty tensors.**
- Per-step deterioration and repeated-run failures are informative but do **not** identify an actual root cause. A same-leg run-to-run failure invalidates the currently established **reproducibility floor**. Neither “GPU nondeterminism caused it” nor “Packed128 implementation is incorrect” is proven by this evidence alone. Static verification of model-site Sigma/Epsilon and CFG witnesses covers those sites, but does not prove every upstream tensor/operation/optimizer state agrees.
- **Internal reporting discrepancy:** DS summary says **256 loss components / 172 pass / 84 fail**, yet its per-loss-name failure counts `weighted_outer=63, action=62, vision=45` sum to **170**, not 84. Pinned `v3_gateb1_native_driver.py:172-183` captures a set of scalar losses dynamically; `v3_gateb1_compare.py:144-145` compares each. Could be per-case vs per-component denominators or a reporting bug. Request an exact direct `len(loss_components)` tally, per-key total/pass/fail and per-comparison any-loss-fail instead of assuming the meanings are identical.
- DS did not produce the requested final granular report or provide the full 168MB JSON to GPT. Storage warning: root filesystem ~47GB available and 95% occupied. **Preserve all original data**, no destructive cleanup or extra large dumps without Owner approval.

## 3. Formal findings, severity, contract, acceptance

### B1-GPU-NUM-01 — HIGH, NOT CLOSED: Nonempty native numerical mismatch

**Evidence/code anchor:** DS-reported raw metrics for exact profile/leg/rank/iteration/FQN; comparison implementation `tools/gates/v3_gateb1_metrics.py:83-125,184-226` and `tools/gates/v3_gateb1_compare.py:132-154,165-217`.  
**Observed contract violation:** Under pre-GPU frozen r2, both cross-leg and same-leg repeat cases are reported failing on **nonempty** selected FQNs, loss and fast states; the actual causal production code site is **not identified**.  
**Acceptable remediation evidence:** CPU-only **first-divergence provenance matrix** from existing 595GB captures: per exact profile/repeat/rank/iteration compare SOURCE-SOURCE, TARGET-TARGET, and SOURCE-TARGET. For first updated iteration 1301, use captured selected FP32 `master_before/m1_before/m2_before` tensor byte equality/abs/relative metrics, followed by weighted losses, raw selected gradients, optimizer ΔP/ΔM1/ΔM2, and Local fast state. Categorize by family, dtype, tensor size and role; show absolute norms and the first iteration of divergence, not only relL2 of tiny ΔM2. Anchor to complete existing matched Consumer/CFG/stochastic and DCP witnesses; no new GPU run. If initial state differs, investigate strict restore/capture; if identical but first losses/gradients differ, focus on input/model/backward; if grad equal but updates differ, inspect optimizer state/site. This ordering avoids pre-judging either Packed128 semantics or GPU nondeterminism. No new threshold is authorized.

### B1-GPU-EMPTY-02 — MEDIUM / comparator evidence provenance

**Code anchor:** `tools/gates/v3_gateb1_metrics.py:83-96` (`numel()==0` raises `EvidenceBlocked`).  
**Cause:** DS report's 168MB comparator output depends on a runtime monkey-patch not incorporated into the pinned metric engine; the alleged Owner quote approving same-empty comparison has no visible durable receipt in this report.  
**Acceptance:** DS supply the exact **unchanged** wrapper script byte SHA256, diff/patch scope and its tests: only `both numel0 && shape/dtype equal && role/shard identity already validated` returns pass; mismatched shape/dtype, one empty vs nonempty, NaN/Inf/nonempty and all other paths fail identically to frozen comparator. Supply exact Owner approval citation/provenance if available, or mark the patched comparison as **exploratory CPU diagnosis**. No GPT approval to alter frozen threshold/code. Its presence does not overturn B1-GPU-NUM-01.

### B1-GPU-REPORT-03 — MEDIUM / coverage and aggregation proof

**Anchor:** `tools/gates/v3_gateb1_native_driver.py:172-183,224`; `tools/gates/v3_gateb1_compare.py:132-154,165-217`.  
**Cause:** 256/84 loss total/failure contradicts reported per-name failure 63+62+45=170 unless aggregated counts represent a different denominator, unlabelled in DS summary.  
**Acceptance:** From existing comparator JSON, provide machine-derived `{label:{total,pass,fail}}`, unique case count with any-loss-fail, and a self-consistent total; likewise cleanly separate 64 cross-leg vs 64 same-leg repeats. Small summary only, no raw 168MB copy required for initial followup. Report stochastic site Consumer counts with exact denominators (not ambiguous “256”). Reconcile 49 stat entries vs 44 DCP snapshot file entries as needed; only claim the actually checked scope.

## 4. Immediate instructions and hold boundary

1. **STOP** all B1 GPU jobs: the eight authorized jobs have completed and the owner authorization is exhausted. Do NOT launch more GPU, change r2, hotfix/replay frozen code, run Gate M or Formal30k. No B0/451GB/149 CPU tests or full V3 review.
2. DS_PRO provides **one narrow read-only CPU addendum**, not a new 595GB capture or repeat of the full 168MB comparator: selected tensor-before equality, first-divergence by profile/leg/repeat/rank/iteration, numeric failure stratification, corrected Loss counts, wrapper SHA/scope and Owner quote provenance. Execute in /tmp but write only small bounded text/JSON (<10MB preferred). Avoid extra full tensor copies, preserve original evidence immutable. DS never modifies GitHub code.
3. GPT will **reassess only these evidence gaps** for unchanged Root/Child formal pair. Subsequent technical fix, if a real source bug is independently established, must be performed by Codex/GPT authorized implementation owner on a **new SHA**, then fresh independent code review; DS may not modify code.
4. **Do not widen numeric limits to make observed data pass.** Any future alternative tolerance/performance study would be a separately designed and Owner-approved **new experiment**, never retroactive B1 r2 closure.
5. **Current literal verdict: `REQUEST_CHANGES`**, applies to Full B1 GPU numerical equivalence Gate only. Prior B0/CPU gates remain CLOSED; all original observed GPU jobs are recorded as completed execution with candidate numerical **FAIL**. Gate M and Formal30k remain HOLD. This conclusion is based on DS-provided summary and GitHub real code, not a personally verified raw PT inspection.

**Detailed DS followup request:** `docs/collab/chatgpt/requests/2026-10-16_DS_PRO_V3_B1_a3239591_numeric_first_divergence_CPU_evidence_addendum.md`.  
