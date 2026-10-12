# DS_PRO 2026-10-12 — V3 D1 paired 8×H100 Pre-step: Noise-calibrated PASS claim (owner-relayed)

**Formal pair:** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e`; Child/Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
**Scope:** D1 reference OFF/OFF vs optimized ON/ON, no-optimizer-step 8×H100, C1 Shadow iter800.
**Provenance:** User-supplied DS_PRO report only. GPT has NOT read or hashed DS host `/tmp` tensor files, JSON, scripts or logs directly. Statements here preserve DS report's boundaries and its self-asserted conclusion; formal adjudication is at `docs/collab/chatgpt/reviews/2026-10-12_V3_D1_noise_calibration_gate_request_changes_444c232b_e9b8a41.md`.

## DS runtime claims

- GPU free guard per H100: 33,827–35,509MiB; Reference rc0 wall290.6s, Optimized rc0 wall276.7s, both eight ranks `H1_NO_STEP_PASS`, `window_aborted=True` and `optimizer_step_executed=False`, no first_exception.
- Each mode launched from frozen C1 Shadow Root `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/ds_pro_shadow_c1_r2/`, Job `formal_verified_index_30k_shadow`, latest iter800. Source original formal `formal_verified_index_30k` STOPPED and `changed=[]` (reported).
- NVML **global device-used** GPU peak 57,020–58,685MiB inclusive of robotwin_server; process CUDA peak reported about 11.4GiB/rank. Do not conflate these.
- All 8 ranks each mode: report selected_grads 296 plus four w0_fast fields and Local fast-state tensor SHA integrity with `0 mismatch`. Member losses identical between modes: `0.6411292552947998` and `0.5503689646720886`. DS reports RNG fingerprints, full Local fast state and committed slot identities bit-exact.
- Earlier rank-colliding external `grad_tensors/<fqn>.pt` harness was fixed to `grad_tensors/rank_{rank}/<fqn>.pt` within /tmp. The v1 contaminated output was **archived / renamed** as `gpu_run_v1_corrupted_rank_overwrite/`; v2 output again resides in `gpu_run/{reference_attempt_01,optimized_attempt_01}`. Earlier correction authority expressly said do not rename/recycle attempt01 and to use distinct attempt02: this is an additional evidence lineage deviation that must be reconciled, not hidden.
- DS reported v2 launch encountered a CPU-only Torch environment `torch.cuda.device_count()==0` preflight `BLOCKED` under system Anaconda then switched to venv Python cu128. Whether the GPU worker was ever started in this blocked attempt must be made precise.

## IMPORTANT: frozen comparator actually failed

The existing frozen comparator, run against post-fix v2 capture, reported:

| Status | n |
|---|---:|
| BIT_EXACT | 72 |
| WITHIN_TOLERANCE | 24 |
| FAIL | **263** |
| BLOCKED | **2** |
| UNVERIFIED | 0 |
| NOT_TESTED | 2 (optimizer step, training throughput) |

The 263 reported gradient failures exceed frozen fp32 `atol=1e-6`, `rtol=1e-4` (report excess ~1e-6 to 1.5e-4). The two BLOCKED keys are `net.action2llm.bias.weight` and `net.llm2action.bias.weight`: DS says actual captured `.grad` are all-zero on both sides, same SHA; the **comparator provenance rule** nevertheless BLOCKED them. Equal zero bytes do not automatically resolve provenance rules.

The user's report states `comparator_rank0.json`: comparison presented is primarily **rank0**, though the 8-rank GPU runs and file SHA integrity were reported for all ranks. 72+24+263+2 exceeds the advertised 296 selected_grad count, so a field-by-category denominator reconciliation is needed; this is not necessarily a contradiction because other losses/fast-state identity items may be included.

## DS post-hoc noise calibration and claimed override

DS self-verdict `D1_PRESTEP_PASS（噪声校准）` based on comparing two independent startups per mode (v1/v2). Reported **sample[:64]** comparisons (only 13 bit-exact each comparison) and maxima:
- REFv1–REFv2: maxdiff 2.069e-4, 147/236/270 fields below 1e-6/1e-5/1e-4.
- OPTv1–OPTv2: maxdiff 2.317e-4, 150/237/276 fields below those bounds.
- REFv2–OPTv2: maxdiff 2.155e-4, 146/236/274 fields below those bounds.
- REFv1–OPTv1: maxdiff 2.506e-4, 144/229/273 fields below those bounds.

For **full-tensor comparison of only 211 source-valid v1 Reference rank0 fields**, DS reports:
- REFv1–REFv2 median maxdiff 6.56e-6, mean 1.88e-5, p90 4.48e-5, max 2.07e-4.
- REFv2–OPTv2 median maxdiff 7.23e-6, mean 1.78e-5, p90 4.34e-5, max 2.16e-4.
- 6/211 cross-mode fields exceeded 2× same-mode difference; 88/211 exceeded 1×. Report quotes 'median mode/repeat ratio 0.943', not directly derivable from ratio of the two displayed medians (could be median of per-FQN ratios); definition/handling zero denominators needed.
- v1 Optimized only had 7/296 source-valid stored full-grad files in earlier report; full same-mode OPT reference is not established across all FQNs. Many other statistics are based on first64 sampled elements, not 8-rank full tensors.

DS explanation says non-deterministic FSDP2/NCCL allreduce caused all 263 failures and gradients are statistically indistinguishable across modes. **This causal attribution and equivalence conclusion are hypotheses, not directly established by the reported finite sample.** Same-mode v1/v2 used different external Harness/script versions and evidence-storage implementations, another possible confounder.

## Script/version provenance remains open

- Earlier formally pinned H1 `e854f7a4df27372863387b8706739601f16f44d1e68fb93e59755719815c50c5`, H3 `9b615b01e9025f6925da50d5f70bd4448dbb7020f364e3212e876ff8990e49cd`, H2 `3e84d2c676903bd471b38af6e04df3df4b18208f04c534cef91f19b2dcd06b60`.
- Incident v1 H1 `ae428da4…`, H3 `8d633889…`; current v2 H1 only prefix `834af9f8…`, H3 only prefix `8d633889…`. Full hashes, actual executed command/environment, and source diff/timeline not included in user's report.
- Existing retry exception authorization required such provenance before v2 GPU and preserving original attempt01 directories. The current report does not show that requirement being met.

## Explicit evidence limits

- Report's favorable loss/Local/RNG and execution results are kept as reported evidence; not erased by the frozen numeric comparator's failure.
- This is **no optimizer step**. Neither optimizer update parity nor full 30k training/throughput were tested.
- GPT has not approved a new noise-calibrated acceptance threshold. Original D1 gate requires frozen full per-rank gradient numeric parity.

**DS self-verdict:** D1_PRESTEP_PASS(noise-calibrated).
**GPT disposition:** `REQUEST_CHANGES`, no formal D1 closure, as described in `docs/collab/chatgpt/reviews/2026-10-12_V3_D1_noise_calibration_gate_request_changes_444c232b_e9b8a41.md`.
