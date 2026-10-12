# DS_PRO — D1 paired 8×H100 Pre-step: rank-colliding evidence artifacts (owner-relayed)

**Received:** 2026-10-12. **Formal pair:** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e`; Child/Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
**Job:** `formal_verified_index_30k` original STOPPED, target C1 isolated Shadow `iter_000000800`.
**Provenance:** Owner forwarded DS_PRO status report. GPT has not directly inspected the server's `/tmp` Python source, JSON, tensor files, or GPU logs. Observations below are DS assertions, not GPT's independent re-run. The original Gate authority is `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_paired_8H100_shadow_prestep_numeric_execution_authorization_444c232b_e9b8a41.md`.

## Successful runtime properties (reported)

- GPU resource guard: 8×H100 each free 33,827–35,509 MiB, threshold ≥25,000 MiB.
- Reference OFF/OFF: `LAUNCH_OK rc=0`, 279.3s. Optimized ON/ON: `LAUNCH_OK rc=0`, 265.3s, sequential. H3 `H3_GPU_RUN_PASS`, 8 ranks × 2 modes `H1_NO_STEP_PASS`, `window_aborted=True`, `optimizer_step_executed=False`, no recorded first_exception.
- `member_losses` both modes equal bitwise, reported members `[0.6411292552947998, 0.5503689646720886]`. This is a real favorable **loss** signal but is NOT by itself full-gradient parity.
- NVML global GPU peak used 57,020–58,685 MiB/card (includes external robotwin_server); original Formal30k manifest `changed=[]`, latest `iter800`, config source hashes stable.
- Local candidate fast-state tensor files 0 bad SHA (both modes).
- Per-rank JSON in-memory `.grad` source SHA/sample and w0_fast full values reportedly valid prior to file persist.

## HIGH evidence defect — H1 artifact collision

- **Reported exact site:** `/tmp/ds_pro_v3_d1_r1/h1/no_step_harness.py:231`
- **Reported code:** `rel = f"grad_tensors/{_sanitize(fqn)}.pt"`
- **Causal path:** Rank not included; eight ranks of the same mode write to the same `<attempt_dir>/grad_tensors/<sanitized-fqn>.pt`. Last writer replaces another rank's file. In-memory per-rank gradient hash and its JSON may still reflect the pre-clobber values, while persisted `.pt` is from a different rank.
- **Reported same-rank persistence matches:** Reference 211/296, contaminated 85/296 (rank3×53, rank1×27, rank2×4, rank6×1). Optimized 7/296, contaminated 289/296 (rank2×100, rank1×60, rank4×62, rank5×32, rank7×35). Optimized w0 files 0/4 integrity; Reference w0 4/4.
- DS reports every mismatching persisted `.pt` SHA equals **some other rank's** recorded in-memory SHA for that FQN; none unmatched. This is compelling causal evidence for last-writer corruption of **measurement files**, not production gradient computation.
- Example: `input_layernorm_moe_gen.weight` file SHA `c8ba124c…` reportedly belongs to rank1; rank0 memory SHA `89df8529…`.
- Comparator findings based on corrupted files (e.g. `layer13 v_proj` max excess `2.620e-05`, `net.action2llm.bias.weight` BLOCKED) **have no valid numerical inference**; superseded pending clean evidence. Must not register as production defects.
- No full tensor tolerance proof from overwritten files; surviving JSON in-memory SHA remains useful as a bit-exact fast-path **if** it is independently shown to be computed on each rank before writes, with complete per-rank selected inventory and identical shape/dtype/actual grad source.

## Critical provenance warning — diagnostic script hash drift

Earlier formal D1 authorization pinned external scripts:
- H1 Harness: `e854f7a4df27372863387b8706739601f16f44d1e68fb93e59755719815c50c5`
- H3 Launcher: `9b615b01e9025f6925da50d5f70bd4448dbb7020f364e3212e876ff8990e49cd`
- H2 Comparator: `3e84d2c676903bd471b38af6e04df3df4b18208f04c534cef91f19b2dcd06b60`

New DS report instead displays abbreviated current H1 `ae428da4…` and Launcher `8d633889…`. These prefixes are inconsistent with frozen hashes. DS must provide exact **full hashes**, source diffs/provenance, and when/why scripts changed. No inference that H1/H3 are byte-identical to authorized scripts is allowed. This is a separate evidence/authority concern independent of tensor file collision.

## Limits / current Gate

**`D1_PRESTEP_UNVERIFIED / REQUEST_CHANGES_EVIDENCE_ONLY`** for numeric gradient parity; runtime reference+optimized *completed*, but failed artifact retention. This is not a demonstrated production code failure. C1 remains CLOSED; original Formal30k remains STOPPED. DS proposes A complete two-mode retry, B weakened partial acceptance, or C asymmetric retry. GPT selection and conditional authorization at `docs/collab/chatgpt/reviews/2026-10-12_V3_D1_paired_GPU_artifact_collision_evidence_review_444c232b_e9b8a41.md`, `docs/collab/chatgpt/reviews/2026-10-12_V3_D1_artifact_collision_conditional_clean_pair_rerun_authorization_444c232b_e9b8a41.md`.
