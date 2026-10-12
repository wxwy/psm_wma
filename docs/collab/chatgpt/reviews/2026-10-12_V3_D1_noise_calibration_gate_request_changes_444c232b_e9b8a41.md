# PSM-WMA V3 — D1 paired GPU Pre-step Noise-calibration Verdict Review (incremental evidence only)

**Date:** 2026-10-12
**Formal implementation pair (unchanged):** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e`; Child+Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
**Formal verdict:** **`REQUEST_CHANGES`** for D1 numerical Gate. **Do not accept** `D1_PRESTEP_PASS（噪声校准）`.
**Gate state:** `C1_RESTORE_PASS/C1_CLOSED / D1_PRESTEP_NOT_PASSED / D1_FROZEN_TOL_FAILURE_REPORTED / E_F_HOLD / FORMAL30K_STOPPED`.
**Prior frozen D1 comparator authority:** `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_paired_8H100_shadow_prestep_numeric_execution_authorization_444c232b_e9b8a41.md`, section C, plus `docs/collab/chatgpt/reviews/2026-10-12_V3_D1_artifact_collision_conditional_clean_pair_rerun_authorization_444c232b_e9b8a41.md`, which permitted only fixed tolerance and exception-controlled attempt02, not post-hoc statistical substitution.
**Latest DS owner-relayed report:** `docs/collab/chatgpt/evidence/2026-10-12_V3_D1_gpu/DS_PRO_2026-10-12_noise_calibrated_prestep_owner_relay.md`. GPT has not independently read DS original /tmp numerical files/scripts.

## Durable positives (accept within reported scope)

1. Both 8×H100 8-rank processes ran one GA window, with no optimizer/scheduler step or DCP save, `window_aborted=True`.
2. Member losses `0.6411292552947998` / `0.5503689646720886` reported **bit-exact**; RNG and Local candidate tensor hashes / committed slots reported equal; strong **positive evidence** against large forward or Local candidate divergence.
3. Rank-separated v2 persisted tensor files report 0 SHA mismatch; original Formal30k checkpoint/job STOPPED and unchanged; 8×H100 process local peak ~11.4GiB/rank reported.
4. These do **not** prove all required `Generation/Action/Local` FSDP2 shard gradients pass frozen per-dtype criteria.

## Finding D1-G1 — Post-hoc noise substitution violates frozen parity contract

**Severity: HIGH, Evidence/acceptance-contract blocker.**
**Artifact/location:** DS `docs/collab/chatgpt/evidence/2026-10-12_V3_D1_gpu/DS_PRO_2026-10-12_noise_calibrated_prestep_owner_relay.md` sections "frozen comparator" and "post-hoc noise calibration"; CPU numerical report `/tmp/ds_pro_v3_d1_r1/gpu_run/comparator_rank0.json` / `noise_calibrated_verdict.json` (exact JSON line locations not exposed in owner relay).
**Observed:** Frozen Comparator reported **263 FAIL, 2 BLOCKED** under preapproved fp32 gradient `atol=1e-6,rtol=1e-4`; raw mode-comparison Gate therefore failed in the accepted literal, irrespective of run completion. Noise-calibrated PASS was proposed **after** observing those results and is a different acceptance method that was not authorized in the frozen scope.
**Root cause:** Replacing a prespecified per-shard gradient tolerance test with an ex post per-FQN/run variance comparison (without a separately frozen equivalence margin, statistical design and independent validation).
**Frozen contract violated:** explicit `FAIL/BLOCKED/UNVERIFIED` must not count as `D1_PRESTEP_PASS`, and numeric tolerances may not be enlarged after GPU result.
**Acceptance:** Preserve original comparator FAIL/BLOCKED and its frozen thresholds; report the noise study separately as exploratory. Any future stochastic-equivalence gate must first freeze statistical estimand, rank/FQN coverage, equivalence margin/CI and run protocol **before** collecting independent new evidence. Do not overwrite the original D1 verdict.

## Finding D1-G2 — Noise-baseline and all-rank scope insufficient

**Severity: HIGH, Evidence scope blocker (not a production-code bug).**
**Artifact/location:** `docs/collab/chatgpt/evidence/2026-10-12_V3_D1_gpu/DS_PRO_2026-10-12_noise_calibrated_prestep_owner_relay.md` section "DS post-hoc noise calibration"; `/tmp/.../noise_calibrated_verdict.json` and rank0 comparator (raw line N/A).
**Observed:** Sampled first64 elements used across most pairings, full v1-valid Reference only 211/296 rank0 fields, v1 Optimized previously only 7/296 full persisted valid files; no reported all-rank full-tensor same-mode noise baseline. The "N=211 FQNs" are correlated model features, **not 211 independent repeat experiments**. 6/211 fields had cross-mode difference >2× reference same-mode; 88/211 >1×, so a blanket "all gradients within baseline" is also unsupported. v1/v2 uses altered external code versions.
**Root cause:** treating limited, possibly confounded per-FQN distribution similarity as a statistical equivalence test, and attributing all 263 failures to NCCL/FSDP2 without isolation evidence.
**Acceptance:** Use existing full v2 eight-rank files to reconstruct frozen comparator results rank0–7 and explicit numerator/denominator/first failure per rank/group/FQN/dtype. Separately enumerate every v1/v2 noise comparison's **full-file-valid vs sampled-only** scope, true replicate count, script identity, and outliers. State `NOISE_EXPLANATION_UNPROVEN` if existing data cannot distinguish mode bias from run variance; no new GPU without independent authorization.

## Finding D1-G3 — Execution provenance + source identity unclosed

**Severity: MEDIUM, Evidence/authority deviation.**
**Artifact/location:** external `/tmp/ds_pro_v3_d1_r1/h1/no_step_harness.py` (v2 hash prefix 834af9f8…), `h3/launcher.py` (v2 prefix 8d633889…), `gpu_run_v1_corrupted_rank_overwrite` and v2 reused `gpu_run/*_attempt_01`; original v1 writer defect was reported at `no_step_harness.py:231`. Exact current code line not in relayed evidence; do not fabricate.
**Observed:** Frozen authority SHA values (H1 `e854f7a4...`, H3 `9b615b01...`, H2 `3e84d2c6...`) differ from reported actual script prefixes; no full hash/diff/semantic-scope proof. Earlier exception authority required **distinct attempt02** and specifically said not to rename original attempt01; DS describes archiving/renaming v1 and reusing attempt01. This affects strict provenance and may confound same-mode v1↔v2 noise comparison.
**Acceptance:** CPU-only reconstruct actual full SHA and timeline for each launch, exact code diffs pinned→v1→v2, cmd/env changes, and original attempt01 archival manifest/path witnesses. Mark protocol deviations, do not rewrite source history or claim same-code stochastic replicate until numerical/loader callback equivalence is proven.

## Finding D1-G4 — Two all-zero gradient provenance BLOCKED items remain

**Severity: MEDIUM, diagnostics-only evidence blocker.**
**Artifact/location:** `/tmp/ds_pro_v3_d1_r1/gpu_run/comparator_rank0.json`, FQN `net.action2llm.bias.weight` and `net.llm2action.bias.weight`.
**Observed:** DS says both have full-zero `.grad`, equal SHA, but comparator's provenance rule labels BLOCKED. Equal zero tensor data alone is not a proof of true `param.grad` source. Conversely, a global rule requiring `weight_sha != grad_sha` may falsely reject legitimate equal tensors.
**Acceptance:** On existing immutable v2 tensors and rank JSON, check `grad_present`, `source="param.grad"`, model FQN/rank identity, tensor shape/dtype/SHA, and exact comparator blocking predicate. Report separately `BLOCKED_RESOLVED` or `BLOCKED_RETAINS`, without post-hoc relaxing numerical tolerance; any comparator semantics adjustment requires documented source/test change and must not erase original result.

## Verdict / minimal next step

**`REQUEST_CHANGES` on D1 Evidence/acceptance; `C1_CLOSED` remains unaffected.** There is **no evidenced production numerical bug**, but equally **no warranted assertion of frozen gradient parity**. The "263 comparator FAIL" belong to the formal comparator outcome; it is not proved they are genuine mode-induced gradient defects. Do not characterize as either definitively NCCL noise or definitively model bug.

Allow **one CPU-only parallel incremental analysis** via `docs/collab/chatgpt/reviews/2026-10-12_V3_D1_existing_GPU_evidence_parallel_CPU_adjudication_authorization_444c232b_e9b8a41.md` (N1 frozen per-rank comparator+blocker; N2 noise scope+script/attempt lineage). No repeat Gate A/B/C1 or another 8×H100 job on the strength of this report. D1 remains open, Original Formal30k Resume/E/F HOLD. If the owner later requests stochastic tolerance as a different objective, freeze a new statistical Gate prospectively and keep this failed frozen Gate on record.

This verdict binds **only** the existing Formal implementation pair and D1 Evidence scope; no new implementation review performed.
