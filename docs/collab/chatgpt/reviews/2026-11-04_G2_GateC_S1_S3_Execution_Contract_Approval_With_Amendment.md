# GPT Review — G2 Gate C S1–S3 exact three-episode execution contract

Date: 2026-11-04 (Asia/Shanghai).  
**Decision: APPROVE_BOUNDED_EXECUTION_CONTRACT_WITH_MANDATORY_TRIGGER_CORRECTION**.  
This is a review/authorization of the exact limited contract **not an execution record**. No server jobs were launched in this review.

Contract: `docs/collab/codex/requests/2026-11-04_G2_GateC_S1_S3_Exact_ThreeEpisode_Execution_Contract.md` at commit `445d177365396bbc5952c3fdc9b59aea459c5caa`.

Formal source Root: `3eb8b334150018212ae1f51afb5e954b83fa1186`  
Formal Child/Gitlink: `1069fe78841228cadbbfbe6afbd767eaed6225da`.

Prerequisite S0 frozen selection and budget: `docs/collab/chatgpt/reviews/2026-11-04_G2_GateC_S0_Exact_Selection_Budget_Readonly_Freeze_PASS.md` at commit `cd143c4bf6322a39cb7855772a944d45a49ffcf8`.

## Approved scope (only after fresh server preflight)

S1–S3 permitted **within one 45-minute shared outer timeout with owned process group** (TERM at 2685s, kill 15s later), one sequential CPU/OSMesa process, `CUDA_VISIBLE_DEVICES=''`, process-local library/cache paths, numeric threads1. No EGL/GPU or global edits.

Freeze the original S0 selection manifest **without regenerating bytes**:
- `CloseFridge` local0/global502 full **429** frames (samples0,214,428).
- `NavigateKitchen` local0/global2022 full **177** frames (samples0,88,176).
- `PickPlaceCounterToCabinet` local0/global4038 full **246** frames (samples0,123,245).
- Exactly **852** source frames / **1704** camera frames / **18** sampled two-camera native geometry checks (first/middle/last of all three).
- Mapping SHA256 `aa884820494a17f50b41a8a8c2bfa6b6fda11babbbef31c449c1c0ce850e09ed`, selection SHA256 `10d668ee42b5145a8cad09878c331ef940b06d91a6a9666ae85434b61c225926`.
- Proposed new cache `/mnt/data1/data_v2_0617/g2_rgbd_pose/gpt_gate_c_candidate_s0_20261104`; new evidence `/tmp/g2_gate_c_s1_s3_3eb8_20261104`; **both must be absent at fresh preflight**, otherwise stop rather than delete/reuse.
- Data format `uint16_mm`/chunk32, current original RGB references, exact source state-frame indexing and K/Pose; unchanged geometry criteria >=16 matched rays and max optical-Z error <=0.01m, unchanged original RGB metrics as nonblocking diagnostic. External visual alignment for new scenes is required before Gate C final PASS. No previous Owner approval automatically applies.

Export each exact episode sequentially with the established per-ID CLI and frozen manifest as membership/identity guard; verify entire cache, sample native geometry, generate server-local contour/occlusion previews; repeat each same export once to obtain **3/3 SKIPPED_VERIFIED** and unchanged immutable episode hash snapshot. Require wall time, per-command peak RSS, disk/free space, compression, actual throughput. New outputs/evidence only; no modifications to old results/caches, active worktrees, scripts/model/training, V3 or N100.

## REQUIRED correction to S1 interruption trigger (no production-code change)

The proposed contract says to send SIGTERM only after both cameras' first **durable NPZ chunks and a matching complete durable `frames.jsonl` progress row** are observed.

**Source audit:** `tools/g2/rgbd_pose/cache.py` explicitly fsyncs each completed NPZ chunk in `flush(camera, number)` (around lines323–335) but writes `frames.jsonl` rows into a buffered binary file (around line349 onward) without `flush/fsync` until the entire episode loop ends (around lines405–408). Therefore, an intermediate `frames.jsonl` row cannot be **asserted durable** from the existing implementation, and waiting for proven row durability may make the injection impossible.

**Contract interpretation amended:**
1. Detect the unique new owned `.staging/<uuid>` for `NavigateKitchen` 2022; verify process ownership by full command, PID, start-time and expected cache path, and ensure committed destination/COMPLETE still absent.
2. Wait for **both cameras' first complete, closed, fsynced chunk files** (for indices0–31, `chunk_000000.npz`; file stability/readability may be checked), and the owning Python process still alive. An existing `frames.jsonl` row can be logged as an *unverified buffered progress observation*, but is **not a required durable checkpoint or invariant**.
3. Only then send **one** SIGTERM to the exact confirmed Python PID (not a shell/timer PID, never a shared/unrelated process group), record event/exit and uncommitted staging, then perform exactly one same-identity retry from frame0. A SIGTERM-interrupted attempt need not generate `.failed/failure.json` because normal Python exception handling may not run; retain its `.staging` directory as raw evidence. Do not call this *partial-chunk resume*: it is a clean full-episode restart after an interrupted attempt.
4. If the observation window closes/episode commits before a safe signal, mark deliberate-recovery evidence **INCONCLUSIVE**, do not repeatedly inject or invent an exit143. Other completed exports may be reported, but Gate C cannot be called fully PASS without the agreed recovery witness. Unplanned failures stop the run.

This is a limited **review-time correction of an observational prerequisite**, not a source-code change or permission to alter success criteria. The executor should record the amendment alongside the runner command and SHA before launch.

## Decision and stopping rules

**APPROVE** the exact bounded contract **with the above mandatory S1 clarification**, subject to new preflight of exact clean source/Child, mapping/selection SHA, no existing output directories, actual disk capacity reserve >=1GiB and one outer owned deadline. If any prerequisite differs, **DO NOT START**; return BLOCKED.

Full Gate C result remains pending until separate server native S1–S3 proof, then the new per-scene human visual review and a follow-up acceptance. Author/GPT Code Gate and old six-frame Gate B PASS are already closed; do not rerun them just for S1.

**Not authorized:** N100/full corpus export, extra fourth task, Stage-2/nav_sg or Global PSS, source edits, GPU/EGL fallback, V3 merge, training/model/DCP, modifying previous reports, unbounded retries or relaxing any geometric standards.

Raw media/Depth/NPZ/source XML/server scripts remain on DS host. Only small text summaries/hashes/paths may be shared through GitHub.
