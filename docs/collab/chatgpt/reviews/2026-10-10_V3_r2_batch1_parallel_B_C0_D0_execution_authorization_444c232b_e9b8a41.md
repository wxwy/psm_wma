# PSM-WMA V3 r2 — Batch 1 parallel execution authorization: B + C0 + D0

**Date:** 2026-10-10
**Role:** GPT authorizes *independent read-only execution* by DS_PRO. DS_PRO does not change production code.
**Status:** `B_AUTHORIZED / C0_INVENTORY_AUTHORIZED / D0_CPU_PROBE_AUTHORIZED / C1_D1_E_F_RESUME_HOLD`.
**Not a new formal code review or a Gate PASS.** Existing Gate A has already been closed on the owner-accepted DS report.

## Exact frozen implementation target
- Formal Root Implementation: `444c232b976e80ac68cde9e7370e73b9f6410f0e`
- Formal Child/Gitlink: `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
- Later branch HEAD is documentation bookkeeping only; DS must pin the implementation pair safely, without force/reset/clean/overwriting local notes.
- Earlier scoped Gate B contract remains authoritative for B1/B2/B3: `docs/collab/chatgpt/reviews/2026-10-10_V3_r2_gateB_real_data_pipeline_parity_authorization_444c232b_e9b8a41.md`. This document ADDs separate C0/D0 authorizations and defines a single consolidated handoff, rather than replacing or weakening Gate B.

## Batch dependency and scheduling
- **Parallel workstreams:** Gate B (B1/B2/B3), Gate C0 (DCP *filesystem-only* inventory), and Gate D0 (CPU-only raw-window worker parity). They do NOT require serial GPT approval between each independent subtask.
- **Within B:** B1/B2/B3 may be independently prepared and tested, reusing real assets and catalog receipts. Use separate processes when setting process-global `PSM_V3_COMPACT_CACHED_VIDEO` and `PSM_V3_SHARED_EPISODE_CACHE`.
- **C0 can run independently of B**, since it only inspects existing checkpoint filesystem metadata and does not load or mutate DCP.
- **D0 numerical parity may proceed after fixed real sample/plan identities are available**; no need to wait for an intermediate GPT review. For *throughput/RSS numbers* run worker configurations sequentially in an otherwise idle CPU/I/O environment; DO NOT benchmark D0 performance concurrently with B or C0 disk scanning.
- If one subgate FAILS/BLOCKS, retain already collected independent evidence. Stop dependent activities; unrelated read-only inventory can finish. Any global source/Gitlink lock failure or unsafe filesystem state STOPs the entire batch. No "retry until green".

## Common fail-closed execution and preservation
1. DS_PRO only validates, does not modify/commit tracked files, checkpoint, source/cache/index, `SESSION.md`/`TODO.md`, old evidence, launcher, contract, frozen config, or another agent's work. Existing H3-F historical helper `?? scripts/plot_h3f_monitor.py` must remain preserved. Safely pin/restore existing worktree with independent status/hash witnesses; if impossible report `BLOCKED`. Do not invent a new worktree or use `git reset`/`clean`/`force`.
2. Use existing CPU Python environment and offline/local real RoboCasa source, cache and prebuilt verified index. Place *probe scripts and output* outside the tracked worktree, ideally in one new external parent directory with `B/`, `C0/`, `D0/` and `SUMMARY.md`.
3. No `torchrun`, no CUDA GPU test, no model weights/4B Policy load, no optimizer/scheduler step, no checkpoint deserialization/unpickle, no Fresh/Resume, no simulator or full validation screening. Keep `formal_verified_index_30k` stopped.
4. Record exact SHA pair, command/environment/seed/source/index/corpus digests, before/after source Git hashes, any first exception, and independent per-subgate PASS/FAIL/BLOCKED. Report field coverage honestly rather than fabricating missing measurements.
5. Frozen expected training Config Digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37` remains **expected-only** unless a separately authorized real preflight measures it; never claim this batch measures it.

## Gate B — real-data input parity (already authorized, execute in this batch)
Do **not** rebuild Dataset Index, recode full source or re-encode VAE.
- **B1:** fixed real Window identities from at least two underlying RoboCasa task classes, including first/interior/last legal windows. Compare baseline `PSM_V3_COMPACT_CACHED_VIDEO=0; PSM_V3_SHARED_EPISODE_CACHE=0` against optimized `=1; =1`, both with `num_workers=0`. Initialize flags before dataset construction, match real recipe/tokenizer and per-sample RNG seed. Verify exact source/key/frame/row/caption/action-with-state15/idle/latent, native prompt/token IDs, `image_size`, action padding, `SequencePlan`, collate packing and consumer ordering. For shape-proxy video only *physical storage/layout* may differ, not effective model inputs. If without 4B Policy no full visual x0-token/crop/temporal comparison is executable, explicitly defer that part to a later real-model Gate; do not falsely mark it measured.
- **B2:** real shared Episode cache OFF/ON hit/miss/revisit and cross-Episode boundaries, identical returned `read_window` and `read_identity`, no alias-corruption or identity leakage. Never mutate a live shared cache payload; only mutate detached copies when probing safe isolation.
- **B3:** compare first/mid/terminal Local-TTT segments, including a real terminal remainder `valid_count < 16`; two GA members and cross-slot same-index consumer order. Exact matching `SegmentIdentity`, slot/binding/frontier, source/evidence chronology, validity masks, prior executed action, visual summary, transformed payload and per-index order. Use `T=16,B_stream=8,GA=2,world_size=8`, fixed planner seed and frozen raw15/left_wrist/use_state contract. Where necessary, advance the metadata-only planner to locate a terminal candidate but materialize only bounded selected real segments. No training/Local fast-weight update.
- Any required unavailable real asset or terminal coverage `BLOCKED`; any actual mismatch `FAIL`. This is an *input parity* Gate, not a full model Loss/Gradient or dataset-build Gate.

## Gate C0 — read-only Formal30k DCP inventory ONLY (new bounded authorization)
Goal: identify, **without making assumptions such as iter800**, the existing Formal30k `latest_checkpoint.txt` pointer and all structurally plausible last-complete DCP candidates.

Use the existing actual job root corresponding to `formal_verified_index_30k`, whose Phase5 relative layout is
`<ACTUAL_OUTPUT_ROOT>/psm_wma_v3/corrected_phase5/formal_verified_index_30k/checkpoints/`.
Check that root/path against the authentic launch/job history; never create it or switch jobs.

- Record (without modifying) the contents of `latest_checkpoint.txt` and its target; enumerate available `iter_*` directories in descending iteration order. Report `latest_pointer_iteration`, `highest_present_iteration`, and **highest structurally complete candidate** separately.
- Mirror the existing Phase5 `_resume_checkpoint` structural requirements: each candidate should contain nonempty `model/.metadata`, `optim/.metadata`, `scheduler/.metadata`, `trainer/.metadata` and all `dataloader/rank_0.pkl` ... `rank_7.pkl`. Count/check nonempty expected DCP payload shard files per component using current actual format (e.g. `*.distcp`); enumerate missing, zero-sized, unexpected or ambiguous files. Record sizes, timestamps and stable file identity; hash metadata/sidecar bytes if modest, but **do not hash huge model payloads or infer correctness merely from file counts**.
- **Never call `torch.load`, `pickle.load`, DCP load API or open actual model/optimizer tensor payloads for deserialization**. Do not overwrite `latest_checkpoint.txt`, repair partial checkpoints, rename, rotate or delete anything. C0 is filesystem integrity *screening*, not proof of training-state consistency or successful Resume.
- `PASS` when real job identity and all required structural witnesses unambiguously identify at least one viable complete candidate, with pointer discrepancy faithfully reported. If pointer is stale/incomplete, mark `POINTER_MISMATCH` and do not assume automatic recoverability; escalate before C1. Missing required ranks/components, uncertain job directory, or unprovable completeness => `BLOCKED` (not invented PASS). C0 PASS **does not authorize DCP loading**.

## Gate D0 — real-data CPU producer/pre-fetch parity and performance ONLY (new bounded authorization)
Goal: test the optimization touched by async read path without running Trainer/Policy.
- Fix `PSM_V3_COMPACT_CACHED_VIDEO=1`, `PSM_V3_SHARED_EPISODE_CACHE=1`; same real corpus, deterministic `ExactWindowRankPlanner` plan and bounded raw Window/GA member set. Worker count is `AsyncExactWindowRawPrefetcher(num_workers=0/2/4)` semantics, **not** Torch DataLoader worker count. `0` uses the synchronous `producer.prepare` + main-thread `producer.materialize` path; `2`/`4` must exercise actual async producer prepare/read + ordered main-thread materialize path.
- Align same requests by `task_class,episode,flat/start,slot,segment_id,member,index`. Compare consumed order, raw `video_latent`, action/state, source/evidence indices, mask, Segment and any main-thread transformed payload; stochastic transforms must be replayed under identical seed and same main-thread invocation order. Exact deterministic equality expected; no reliance on elapsed-time alignment.
- Measure separately cold/warm observed CPU wall/Windows-per-second, process peak RSS (including worker threads), cache-hit/miss/evictions where available, errors, source I/O counters if available; 2/4 worker perf checks **must not overlap** with other disk-intensive work. Record repetitions/CPU allocation and avoid unsupported speedup claims. No hard throughput speedup threshold is frozen: numerical or consumer-order drift is FAIL, performance may justify selecting workers=0 even if D0 parity PASS.
- Ensure workers are closed/drained after trial and no source files are modified. Do not run GPU, model, training, step optimizer, DCP or `torchrun`.
- `PASS` if all compared windows and chronology/order are equal, no silent errors/leaks, and resource measures are reported honestly. `FAIL` for content/order change; `BLOCKED` if real source unavailable or actual async path cannot be exercised. CPU statistics do not represent 8×H100 training throughput; GPU D1 remains separate.

## Consolidated DS_PRO deliverable
One **Batch1 report**, with clearly separate: `B1`, `B2`, `B3`, `C0`, `D0` statuses and supporting sample IDs/counters. Include:
- Formal pair and code/image/recipe/input asset provenance; pre/post Root/Child status; B input parity witness and C0 checkpoint inventory; D0 exact-parity plus measured CPU/RSS tables.
- Explicit list of real data tests skipped before and which parts are now covered. Frozen config digest still expected-only; C0 only file structure, not recovered parameters/RNG.
- `B_PASS` only if B1-B3 all required cases PASS, `C0_PASS` only if structurally plausible checkpoint identified, `D0_PASS` only if verified real async parity; otherwise exact FAIL/BLOCKED reason. No aggregation hiding a failed subgate.
- DS_PRO sends report via user to GPT; GPT independently checks reported evidence and can persist directly to `docs/collab/chatgpt/evidence/` and `reviews/`, no Codex intermediary.
- **Stop after Batch1**. C1 (real same-job DCP restore), D1 GPU profiling, Gate E Full Policy and Gate F Screening all require their own authorizations and can later be *scheduled* with dependency awareness, not automatically launched. Original Formal30k remains STOPPED and original DCP unchanged.
