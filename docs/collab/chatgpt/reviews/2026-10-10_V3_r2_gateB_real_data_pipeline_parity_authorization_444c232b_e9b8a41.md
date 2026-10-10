# PSM-WMA V3 r2 — Gate B real-data pipeline parity execution authorization

**Date:** 2026-10-10
**Role:** GPT independent Gate owner; DS_PRO independently executes and reports read-only evidence.
**Status:** `GATE_B_AUTHORIZED_FOR_DS_PRO_READ_ONLY_DIAGNOSTICS / GATE_B_OPEN / RESUME_HOLD`.
**This is a narrowly scoped execution contract, not a new technical review or PASS verdict.**

## Locked code target and rationale

- Formal Root Implementation: `444c232b976e80ac68cde9e7370e73b9f6410f0e`.
- Formal Child/Gitlink: `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
- Existing completed CPU Gate A: `docs/collab/chatgpt/reviews/2026-10-10_V3_r2_gateA_evidence_only_closure_DS_attestation_444c232b_e9b8a41.md`.
- Current V3 branch tip can be a later documentation successor: **pin the implementation SHA, not current docs HEAD**. Formal pair unchanged; do not rescan the same implementation for a duplicate technical verdict.

The dataset definition, manifest, verified index and stored VAE latent values are not being regenerated. However these optimizations change the *consumption* path: `cached_pixel_geometry.py` replaces dense zero video with one-byte-stride shape proxy and bypasses per-sample `VideoResize`; `robocasa_shared_episode_reader.py` introduces rank-local, shared Episode payload references; and `robocasa_async_segment_prefetch.py` can change execution timing when explicitly enabled. Real inputs and downstream metadata can drift even when the source corpus is unchanged.

**Decision: retain only a small REAL-DATA input parity Gate B, not a broad re-audit of the complete dataset.** Skip all full-index rebuild, all-source scans, all-VAE-reencode, new code, model loading, GPU, optimizer, DCP, simulator and training.

## Execution constraints

1. DS_PRO remains executor/observer only. Safe-pin the exact pair in the existing authorized validation workspace without reset/clean/force/overwriting owner notes; otherwise report `BLOCKED`. Preserve historic H3-F `scripts/plot_h3f_monitor.py`, `SESSION.md`, `TODO.md`, prior evidence and stashes. A known historical helper should not be silently removed for this new run. Confirm Root/Child/Gitlink before/after.
2. Use the real prebuilt `VerifiedExactWindowIndex.open` plus actual unchanged `source_root` and `cache_root`. Open read-only; no rebuild or write into the source/cache/index. Do not call the training `--phase resume` or `--stop-after-iter` as a diagnostic. `--preflight --snapshot10` is not a substitute for these A/B parity checks.
3. Set `PSM_V3_COMPACT_CACHED_VIDEO` and `PSM_V3_SHARED_EPISODE_CACHE` **before dataset construction** for each reference/optimized variant. Both default to 1 in committed code. Run both with **`num_workers=0`**; no asynchronous worker tests at Gate B (reserved for Gate D). Reference is (0,0); optimized is (1,1).
4. Match the actual trained dataset contract: `raw15`, `left_wrist`, `use_state`, `fps=20`, `H_pred=16`, `T=16`, `B_stream=8`, `GA=2`, `K_local=4` where relevant, and real tokenizer/prompt recipe. Reset Python/NumPy/Torch RNG to the same seed before matched stochastic transforms (e.g. CFG dropout); don't change frozen recipe semantics solely to force equality.
5. Run CPU-only, read-only external Python probes or existing tests; keep any temporary scripts, log/JSON snapshots and witnesses **outside the tracked worktree**. No production/test modifications, fixture edits, new branch commits, package installs, torchrun, DCP, CUDA or checkpoint decoding.
6. Fail closed on mismatch or missing asset. Preserve first failure, paired witness and exact scope; do not mask a failure with arbitrary floating tolerances or rerun until passing.

## Frozen acceptance contracts

### B1 — same real Window, compact ON/OFF and cache ON/OFF parity

Use deterministic real Window identities from at least 2 different underlying task classes, including first, interior and final legal Window positions; include a case with nonzero idle/action fields if available and record coverage. Use the **same exact identities and source bytes** under both variants.

Compare: `task_class`, episode/flat/start/window/global row indices, latent source frame indices, source and cache digests, `ai_caption`, raw15 action/state, full cached fp32 `video_latent`, idle frames, fps/domain/mode; after native `ActionTransformPipeline`: formatted prompt/text token IDs, padded action/mask/raw dimension, `image_size`, SequencePlan (all fields including vision/action conditioning/time offsets), and after native collate/padding the retained latent/action order. If a CPU-accessible native cached-vision preprocessing method exists without a 4B Policy, compare crop output and temporal positions as well; otherwise explicitly defer to the actual-policy numerical Gate rather than claiming full token parity.

**Required equality:** exact identities, shapes/dtypes, `torch.equal` or bytewise equality for deterministic tensors, token IDs and SequencePlan semantics. Differences allowed only in physical storage/strides/CPU device of the **zero-valued placeholder**, and cache counters/resource timing. Do NOT assert dense video physical layout equals zero-stride proxy. Any functional prompt/geometry/latent/action/sequence mismatch is `FAIL`.

### B2 — Episode cache hit/miss, reuse and alias-isolation

Read a fixed real episode and multiple Window offsets first with shared cache OFF then ON, including repeated reads (hit), another Episode (eviction/miss if capacity permits), and a return to the original. Compare each `read_window` and `read_identity` plus Source/Action payload equality; repeated reads may physically share an immutable backing tensor. Probe that a caller mutating its *own returned per-window copy* (only if safe and on a detached clone) cannot corrupt subsequent reads; **never mutate a shared live cache payload** merely to test isolation. Confirm stable source file/version witness and no cross-episode/slot identity leakage.

**Required equality:** no content, identity, shape, dtype or corruption discrepancies; failure/exception rather than silent drift if the underlying immutable-file witness is invalid. `FAIL` on any counterexample.

### B3 — Local-TTT Segment plan / chronology / consumption parity

Use a fixed deterministic planner seed and the same `ExactWindowRankPlanner`, `ExactWindowSegmentProducer` and `gather_exact_window_same_index`. Compare reference and optimized variants for representative first/middle/terminal segments; specifically cover at least one **terminal remainder with valid_count < T=16**, if real corpus contains one, and otherwise report missing-coverage `BLOCKED` rather than pretend full terminal coverage. Include at least one episode transition and two GA members of the same plan window. No optimizer or Local fast-weight updates.

Compare: slot and episode ID, `binding_epoch`, cursor, `segment_id`, member request identity, `consumer_step`, `evidence_source_step`, validity masks, `evidence_executed_action_prev`, `consumer_visual_summary`, `evidence_visual_summary_prev`, native transformed payloads (action/latent/token/SequencePlan), and cross-slot same-index batch member order. For first consumer, verify no previous-step evidence; for later consumers evidence must match exactly the previous Window/action. Check frontier and plan witnesses without publishing or mutating live training state.

**Required equality:** exact identity/causality/order and deterministic tensors across toggles. All comparison exceptions `FAIL` rather than omit a segment.

## Evidence and verdict

DS_PRO report must name exact Formal Pair, pre/post git status and code hashes, actual immutable `VerifiedIndex` receipt hash, source binding digest, cache corpus/manifest digest, real sample task/episode/start identities, selected terminal remainder witness, config/seed and comparison count. Include per-B1/B2/B3 `PASS`, `FAIL` or `BLOCKED` with first mismatch `file:line` or function/path and shaped/value witnesses. Report B1 cached latent/token/crop/sequence fields that were actually compared; do not claim any unexecuted field tested.

Gate B `PASS` requires all **required** B1/B2/B3 coverage available and exact parity. If a real asset is absent or token/SequencePlan paths cannot be executed, report `BLOCKED`, not a synthetic substitute. After reporting, DS must stop; owner/GPT reviews DS Evidence and separately decides Gate B closure and Gate C authorization.

**Not authorized:** new dataset creation, VAE encoding, CPU test code submission to tracked repo, model weights/4B load, optimizer, GPU/FSDP, DCP/checkpoint read or write, formal30k Fresh/Resume, workers2/4 throughput testing, real-policy simulator or 18-task screening. `formal_verified_index_30k` remains stopped, latest complete DCP iteration still unknown, frozen config digest expected `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37` not newly measured.
