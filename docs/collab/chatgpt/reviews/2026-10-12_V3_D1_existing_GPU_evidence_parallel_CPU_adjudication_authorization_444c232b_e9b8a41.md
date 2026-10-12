# DS_PRO — V3 D1 final Evidence adjudication from existing GPU files (CPU-only parallel)

**Date:** 2026-10-12. **Implementation Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`; **Child/Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
**Formal D1 status:** `REQUEST_CHANGES / D1_PRESTEP_NOT_PASSED`; **C1 CLOSED / Formal30k STOPPED**.
**Reference:** `docs/collab/chatgpt/reviews/2026-10-12_V3_D1_noise_calibration_gate_request_changes_444c232b_e9b8a41.md`.
**Intent:** Resolve what the already collected v1/v2 GPU evidence can and cannot establish. This is **not** a newly authorized noise-calibrated PASS Gate and not new GPU training.

## N1 — Frozen criterion, per-rank/full-tensor numerical ledger (CPU-only)

- Read already saved **clean v2** Reference and Optimized eight-rank JSON + full `.grad` and Local candidate tensor files; verify each trusted file's relative path, SHA256, real `param.grad` FQN/rank, selected Optimizer parameter inventory, dtype/shape/numel before comparison. Do **not** use v1 rank-collision tensor files for full numeric proof.
- For all ranks 0..7, all selected Generation/Action/Local fields incl 4 w0, reconstruct frozen comparator outcomes without changing `fp32(loss 1e-6/1e-5, grad 1e-6/1e-4), bf16 (2e-2/2e-2), nearzero both<1e-7`. Record per-rank/group/FQN P0 bit exact / P1 within frozen tolerance / FAIL / BLOCKED / UNVERIFIED with counts and first failure; include the **raw** 263 FAIL + 2 BLOCKED rank0 result in an immutable ledger. Reconcile what the counts 72/24/263/2 include vs selected_grads=296 and why two zero `net.action2llm.bias.weight` / `net.llm2action.bias.weight` were BLOCKED. Check actual `source=param.grad`, grad presence/zero/weight SHA and source predicate; document any diagnostic-only false positive separately, do not silently erase.
- Verify matched input identities: same Shadow iter800, digest, 8-rank RNG/CFG decisions, GA memberships, valid counts, frontier, fast state/Local candidate identities. Real matched member losses should remain recorded as bitwise equal. Do not fake a PASS from sample64 or grad SHA alone unless all required tensors bit-exact.

## N2 — Noise study coverage + execution provenance audit (CPU-only)

- Audit claimed same-mode baseline pairs REFv1↔REFv2 and OPTv1↔OPTv2 separately from between-mode pairs. Report **full-gradient payload** availability and actual compared FQN/rank counts vs first64 sampled-only data, for all 8 ranks, not just rank0. v1 Reference 211/296 and v1 Optimized 7/296 rank0 full files were previously reported valid; mark unmatched data untestable, not PASS.
- Produce exact per-FQN noise ratios, especially 6/211 exceeding 2×, and distinguish `median of per-FQN ratios` from `ratio of medians`. No pseudo-replication: 211 FQNs are correlated features, not 211 random seeds; two starts per mode are insufficient by themselves for an equivalence claim. Do not assert NCCL as sole cause absent evidence.
- Reconstruct full executed external H1/H3/H2 SHA256, script diffs and timeline against formally pinned H1 `e854f7a4df27372863387b8706739601f16f44d1e68fb93e59755719815c50c5`, H3 `9b615b01e9025f6925da50d5f70bd4448dbb7020f364e3212e876ff8990e49cd`, H2 `3e84d2c676903bd471b38af6e04df3df4b18208f04c534cef91f19b2dcd06b60`. In particular, v1 H1 prefix `ae428da4`, v2 H1 prefix `834af9f8`, launcher `8d633889` need exact full values/diff; inspect whether anything beyond output path changes could alter forward/backward/RNG/optimizer/sharding/loader semantics.
- Reconcile v1 attempt01 directories **archived/renamed** versus prior strict prohibition on renaming/reusing attempt01, and any blocked v2 system-Anaconda start. Preserve original file lists/hashes/mtime and actual GPU start count; report execution discipline deviations without inventing missing logs.
- If noise hypothesis unprovable from current evidence, explicit verdict `NOISE_EQUIVALENCE_UNESTABLISHED`, not noise-calibrated PASS. Propose only a *separate prospective* noise-aware Gate if later requested; **do not design/postapprove a new margin in this round**.

## Parallel, safety and handoff

N1/N2 run independently in external unique /tmp directories and may proceed simultaneously, share the already collected immutable v2 Evidence. No GPU/torchrun/model load/new checkpoint/files rewrite, no tensor mutation/production script editing, no dataset/Index/VAE rebuild, no optimizer/scheduler step or original Formal30k Resume. C1 remains CLOSED.

Submit **one** report: `DS_PRO_V3_D1_EXISTING_EVIDENCE_NUMERICAL_AUDIT_2026-10-12.md`, with N1/N2 PASS/FAIL/BLOCKED for *evidence reconciliation only*, frozen comparator overall `FAIL/UNVERIFIED` as appropriate, noise claim scope, per-rank manifest/count table, provenance/first error, Original Formal30k invariance, exact evidence paths/hashes.

**Stop after this report.** No new GPU task without separate GPT authorization. Do not autonomously declare `D1_PRESTEP_PASS`, D1 CLOSED or start formal30k.
