# V3 r2 Batch 1 — GPT Evidence Review, partial closure and narrow remediation

**Date:** 2026-10-11
**Formal verdict:** `REQUEST_CHANGES` — **Evidence-only** for B3 cross-variant Segment parity and D0 full-worker parity/cold benchmark; no evidenced new production implementation blocker.
**Current subgate status:** `B1_PASS_REPORTED_SCOPE / B2_PASS / B3_EVIDENCE_OPEN / C0_PASS_STRUCTURAL_ONLY / D0_EVIDENCE_OPEN / FORMAL30K_RESUME_HOLD`.
**Formal implementation pair unchanged:**
- Root `444c232b976e80ac68cde9e7370e73b9f6410f0e`
- Child / Root Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
- Gate A remains CLOSED; no repeated same-pair code review.

## Evidence authority and limits

- Frozen Gate B: `docs/collab/chatgpt/reviews/2026-10-10_V3_r2_gateB_real_data_pipeline_parity_authorization_444c232b_e9b8a41.md`; Batch1 C0/D0 authorization: `docs/collab/chatgpt/reviews/2026-10-10_V3_r2_batch1_parallel_B_C0_D0_execution_authorization_444c232b_e9b8a41.md`.
- This independent review checks the **owner-relayed DS_PRO report** and the pinned production code/contract; DS original `/tmp` JSON is not available in this session. Source transcription `docs/collab/chatgpt/evidence/2026-10-11_V3_Batch1_DS/DS_PRO_2026-10-10_V3_B1_B2_B3_C0_D0_combined_report.md` is attributed to DS_PRO, not presented as original raw JSON. The owner previously accepted DS's raw-evidence judgment for Gate A; this report is accepted on its stated fields, **not upgraded into claims about fields that were omitted**.
- Real corpus, real verified-index and real producer were used by DS per its report: 18 tasks, 9,126 episodes, 2,085,331 windows. No fresh Index build, VAE recomputation, model load or training is requested.

## Independent dispositions

### B1: PASS for explicitly reported 4-sample/4-config input comparison, minor metadata clarification
- Ten reported field groups (latent, raw/padded action, tokens, global row, SequencePlan, caption, image_size, key, start) have exact cross-config SHA256 agreement according to DS_PRO; 00/01/10/11 were used and actual real samples were selected.
- Please append the **task-class and episode mapping** of indices `0,7,1042665,2085330`, and whether auxiliary idle/fps/domain/mode/latent-source-frame indices were compared or simply inherited unchanged. Do not claim an unmeasured model visual-token/crop/temporal behavior; under frozen Gate B it can be deferred to actual-model Gate.
- LOW nonblocking accounting ambiguity at `docs/collab/chatgpt/evidence/2026-10-11_V3_Batch1_DS/DS_PRO_2026-10-10_V3_B1_B2_B3_C0_D0_combined_report.md:37`: DS calls noncompact resized storage `3,129,600B dense fp32`, inconsistent with `[3,17,192,320]` at uint8 (3,133,440B) or fp32 (12,533,760B). Ask DS to report actual tensor dtype, logical shape, storage bytes and whether the measured value was another quantity. **Not a reason to rerun B1 if existing probes contain the facts.**

### B2: PASS
- A real Episode cache MISS/HIT and Episode switch were reported, with raw Latent/action equivalence and no visible identity isolation violation. Default cache capacity does not require a contrived eviction to establish this narrow hit/miss read parity. Any untriggered eviction/error paths remain unclaimed.

### B3: Evidence-only BLOCKER — cross-toggle outputs and native same-index order absent
- **Severity: HIGH (evidence-only, no production bug alleged).**
- **Evidence location:** `docs/collab/chatgpt/evidence/2026-10-11_V3_Batch1_DS/DS_PRO_2026-10-10_V3_B1_B2_B3_C0_D0_combined_report.md:62`; frozen contract `docs/collab/chatgpt/reviews/2026-10-10_V3_r2_gateB_real_data_pipeline_parity_authorization_444c232b_e9b8a41.md:46-50`.
- **Root cause:** The DS report proves true predecessor causality, legal valid masks, three terminal remainders and first GA structure by re-reading real raw items, **but does not explicitly exhibit `OFF/OFF` versus `ON/ON` equality for the same nine selected SegmentBatch objects, nor a `gather_exact_window_same_index` cross-slot ordering witness**. A valid causal Segment in one configuration is not proof of zero semantic drift between configurations.
- **Acceptance:** DS addendum must bind the same selected requests/seed in reference and optimized paths and provide all-nine segment equality of identity/slot/member/cursor/valid masks, current/evidence visual96, action evidence and native token/SequencePlan payload, and at least one native same-index gather order comparison. Existing JSON may already contain these; report the fields if they exist, otherwise run a **small read-only supplemental probe** on only these real segments. No full dataset scanning or Trainer/GPU.

### C0: PASS — structural DCP candidate, not strict recoverability
- **Evidence:** `docs/collab/chatgpt/evidence/2026-10-11_V3_Batch1_DS/DS_PRO_2026-10-10_V3_B1_B2_B3_C0_D0_combined_report.md:70`. Latest pointer reads `iter_000000800`; iter700 and iter800 are structurally viable candidates with 4 DCP components, nonempty required model/optim/trainer payload and eight rank sidecars. iter200–600 lacking `optim` are **not** full same-job resume candidates.
- **Independent code cross-check:** pinned Child `cosmos_framework/checkpoint/dcp.py:1177-1199` uses `CustomSavePlanner(dedup_save_to_lowest_rank=True)` for all components, explaining the rank0-only Scheduler payload and 0-byte rank1–7 shards. The DS probe's blanket `structurally_complete=false` is overconservative for replicated Scheduler bytes, **provided** the per-component DCP metadata and rank0 data are present as reported.
- This only closes **C0 filesystem inventory**. It does not prove that `iter800` loads, that every model/optim tensor exists, or that scheduler/RNG/Local/dataloader state can be strictly reconstructed. **C1 remains unauthorised** pending Gate B's required parity and a separately scoped strict-load protocol. `latest_checkpoint.txt` must not be altered.

### D0: Evidence-only BLOCKER — only first cross-worker fingerprint and warm-cache timings
- **Severity: HIGH (evidence-only, no production bug alleged).**
- **Evidence location:** `docs/collab/chatgpt/evidence/2026-10-11_V3_Batch1_DS/DS_PRO_2026-10-10_V3_B1_B2_B3_C0_D0_combined_report.md:86`; frozen contract `docs/collab/chatgpt/reviews/2026-10-10_V3_r2_batch1_parallel_B_C0_D0_execution_authorization_444c232b_e9b8a41.md:49-53`.
- **Root cause:** `order_ok=true` within each 48-segment run, `unique_fingerprints=true` and `cross_config_first_segment_fp_identical=true` do **not** entail exact equality for remaining 47 segment tensor/identity results. Also all three configurations measured 0 Episode loads/misses, hence cold/warm comparison is not established; wall measurements reflect the already-warmed cache and main-thread materialisation, not cold-source prefetch benefit.
- **Acceptance:** Compare **all 48 aligned cross-worker Segment fingerprints or exact deterministic tensors and per-segment identities/chronology** for workers0/2/4, not just the first; report the all-equal aggregate + first mismatch if any. Report current warm timings as such. If existing recorded fingerprints suffice, **no rerun**. If not, a **bounded real CPU-only supplementary** run may be used; add separate isolated cold-cache reads with a fresh reader per worker setting (no cache sharing across settings) and actual peak RSS/wall, without pretending this predicts GPU performance. Do not enable optimizer, DCP or Trainer.
- **Performance interpretation:** Warm-cache numbers of 5.92 vs 3.87 vs 1.36 segments/s do *not* justify a general slowdown theorem; for current conservative formal Resume choose `num_workers=0` until D0/D1 prove benefit. There is no frozen minimum speedup threshold; numerical parity is the true hard gate.

## Further execution authority / next steps

- **Do not reopen B1/B2 or repeat all Batch1.** DS_PRO is authorised to provide a targeted evidence-only **B3+D0 addendum** using existing probe outputs if available, or narrow CPU-only real-data comparisons if missing. Also clarify B1 sample task mapping and storage measurement using existing outputs where possible. All commands/reports remain outside tracked worktree; DS does not edit production code/tests or Git history.
- No new formal implementation pair; no repeated Gate A or full fresh technical review.
- Stop dependent C1, D1 GPU, E/F simulation/screening and Formal30k until their separate Gate authorizations. The owner's frozen config digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37` has not been measured in a real strict Resume preflight.
- If missing a required parity field in existing JSON, DS reports that explicitly; never silently mark `PASS`, mask a mismatch, or reconstruct synthetic Evidence. A real mismatch is `FAIL`, missing required evidence is `BLOCKED`. Return one narrow addendum to GPT; GPT can submit DS report and final verdict to GitHub directly without Codex.
