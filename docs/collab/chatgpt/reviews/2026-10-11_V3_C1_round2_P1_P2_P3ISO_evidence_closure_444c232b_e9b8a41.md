# PSM-WMA V3 C1 Round2 — P1/P2/P3-ISO Evidence Closure

**Date:** 2026-10-11
**Formal Pair:** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e`; Child/Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
**Formal Evidence Verdict:** `C1_ROUND2_PASS / G0_4_ISOLATION_CLOSED`
**Remaining State:** `C1_REAL_8H100_DCP_LOAD_PENDING / D1_E_F_HOLD / FORMAL30K_STOPPED`

## Reviewed authoritative material

- Earlier G0 finding: `docs/collab/chatgpt/reviews/2026-10-11_V3_C1_G0_evidence_only_review_444c232b_e9b8a41.md`.
- Round2 execution contract: `docs/collab/chatgpt/reviews/2026-10-11_V3_C1_round2_parallel_P1_P2_P3_snapshot_prep_authorization_444c232b_e9b8a41.md`.
- Latest user-transferred DS report: `docs/collab/chatgpt/evidence/2026-10-11_V3_C1_Round2/DS_PRO_2026-10-11_C1_P1_P2_P3ISO_owner_relay.md` (summarized with disclosure; original `/tmp` JSON not independently inspected).
- Fixed Child direct source read: `cosmos_framework/trainer/__init__.py:138-145,265-288`; `cosmos_framework/utils/config.py:200-207`; `cosmos_framework/checkpoint/base.py:60-70,161-188,213-225`; `cosmos_framework/checkpoint/dcp.py:758-865`; `examples/psm_wma_robocasa_corrected_phase5.py:238-315,408-504,558-588`; `cosmos_framework/trainer/local_memory_grouped_resume.py:93-200,203-253`. No new formal implementation pair and no duplicate full code review.

## Independent incremental decisions

**P1 PASS:** Production `preflight` full digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37` matches frozen target. All previously required DCP structure, config/source fingerprints and version identities reported consistent. Current scope does not require full giant shard SHA256 reread.

**P2 PASS:** All 8 rank copied sidecars validated with trusted `pickle` from the same recognized checkpoint (not arbitrary untrusted bytes); schema/iteration=800/profile/data+config digests/slot-frontier/terminal/fast-state CPU tensors pass. Original user report also documents next two GA members with segment_id1600/1601 and per-rank n_window witnesses. **No claim of true GPU live fast-state restore.**

**P3-ISO PASS / former G0-4 blocker CLOSED:** Entire iter800 shadow copy is a separate job directory: 44 files, source/target distinct inode/realpath, no symlinks, correct latest pointer, small SHA and sizes match. Pinned Child's `GroupedLocalMemoryTrainer.__init__` writes config to `JobConfig.path_local` and Checkpointer's `save_dirname` is derived from same path; setting `IMAGINAIRE_OUTPUT_ROOT` to shadow root and `config.job.name=formal_verified_index_30k_shadow` keeps such writes confined to shadow. Actual same-job selection in `keys_to_resume_during_load` consults shadow `save_dirname/latest_checkpoint.txt` and reports source `warm_start=False`, not `load_path` warm start.

**Clarifications:** Shadow job's diagnostic name `formal_verified_index_30k_shadow` intentionally differs from original job name, but production digest function omits job name and P1 already proved frozen train-config digest. The future load should re-assert full digest after construction under shadow name and never call an arbitrary original path as `output_root`. CPU P3 report details small-file SHA/size; it does *not* establish independently identical content of every large shard, so DCP actual load remains the enforcement point.

**Open actual resources:** External `robotwin_server` occupies approx 45.6–47.3GB of each H100; available 33.8–35.5GB is a snapshot, not an unconditional resource reservation. A fail-closed runtime budget and coordination are required before starting load-only; no foreign process may be killed, evicted, or altered.

**G0 overall:** G0-1/2/3 previously PASSED within their respective scopes; G0-4 now closed by P3-ISO. Hence `G0_CLOSED` for safe diagnostic preparation only.

## Next permitted action

Separate scoped authorization is recorded at `docs/collab/chatgpt/reviews/2026-10-11_V3_C1_round3_8xH100_strict_shadow_load_only_authorization_444c232b_e9b8a41.md`: a single 8-rank Load-only using the exact Shadow Job and frozen code, with CPU monitoring in parallel, no train loop and no mutating original Formal job. It is **not** C1_RESTORE_PASS until DCP five-component strict restoration, RNG, Local live tensors and P2 future frontier comparison actually PASS.

No further Batch1/GateA/dataset/verified-index/VAE CPU revalidation; C1 may proceed with new Gate constraints only. D1/E/F, original Formal30k Resume and all fresh/training behavior remain HOLD.
