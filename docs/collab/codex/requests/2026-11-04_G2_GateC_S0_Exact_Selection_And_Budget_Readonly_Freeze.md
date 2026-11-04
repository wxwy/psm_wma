# G2 Gate C S0 — exact selection and size/resource freeze

Date: 2026-11-04 (Asia/Shanghai). This is a **source-read-only preparation
handoff**, not authorization for rendering, export or full Gate C execution.

## Closed prerequisites and exact source

- Formal Root `3eb8b334150018212ae1f51afb5e954b83fa1186` /
  Child-Gitlink `1069fe78841228cadbbfbe6afbd767eaed6225da`.
- Code APPROVE: `544b656b5b8fd2f2a0219b90f90207442daf4ef0`.
- Native six-camera Gate B PASS: `df3d2c5027ab40da8b953a7c5f8ee5b8a703fe41`.
  All6 ray checks PASS/128 matches, native exit0, immutable prior reports;
  RGB5/6 diagnostic FAIL remains nonblocking, human evidence remains external.
- Existing plan:
  `docs/build/PSM-WMA_G2_Spatial_Acceptance_v2_and_GateC_Plan_2026-11-04.md`.

Do not re-run121 tests or the six-frame replay to gather this metadata. No
production change or new Formal Pair is needed. The author cloud has no callable
server connection and has not read/copied the mapping or other server files.

## S0 work on the server

Use the existing exact, clean isolated formal checkout from the Gate B report,
or a new isolated checkout if it is occupied/dirty. Never update active shared
worktrees, reset/clean/force, install dependencies or edit production. Read the
server `github-fetch-proxy` skill before any newly necessary fetch.

1. Read current `flat_v3_mapping.parquet` under
   `/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic/`.
   Record its SHA256 and current schema/identity. Reuse existing
   `tools.g2.rgbd_pose.source.mapping_episodes`; no LeRobotDataset construction
   or new sampler is needed. Do not copy the Parquet out of the server.
2. Propose **three full episodes from three distinct actual underlying task
   classes** initially (a reviewed plan may use up to five). CloseFridge
   local0/global502 is a known candidate anchor, subject to a fresh mapping
   match. Pick the other candidates from real mapping/source availability,
   not names/IDs in synthetic tests or evaluation logical episode numbers.
   Do not assume N100 membership, default seed42 or per-task global numbering.
3. For each candidate, verify actual local/global IDs, full `length`, both
   half-open row intervals, resolved source dataset and native camera H/W.
   Resolve ambiguity explicitly or return BLOCKED_SOURCE; never choose the
   first recording directory silently. The known Gate B indices0/214/428 are
   **sampled indices**, not proof of the full episode length. In particular,
   do not substitute three frames or infer length429 without source evidence.
4. Create a small selection manifest **on the server** using the existing
   `psm_wma_rgbd_episode_selection_v1` schema/global_episode_index namespace,
   current mapping SHA and the proposed exact task/global-ID members. Record
   manifest SHA256/path; templates or guessed IDs are not a frozen selection.
5. Run only the existing export CLI's `--dry-run` with this manifest, native
   left+wrist cameras, `frame_index`, `uint16_mm/chunk32`, and **no --frames**.
   Use the already documented command and3–5/distinct-task/full-length guard.
   This reads nonvisual sources and must create no renderer or output cache.
   Retain the plan/exit in a fresh external text-evidence directory. Report
   source/Flat identity failures rather than starting an export.
6. Record the proposed new cache filesystem's available bytes and timestamp,
   available host memory, total episode/frame/camera counts and the dry-run
   `uncompressed_array_bytes_estimate`. For uint16 plus valid masks the array
   estimate is sum over frames/cameras of `3*H*W + 41*4 + 8` bytes; it excludes
   JSON/NPZ overhead. Do not extrapolate the old three-frame compression ratio.
   A conservative *proposal* is `2*array_estimate + 1GiB` free-space budget,
   preserving the existing1GiB reserve; freeze actual numbers for review.
7. Propose explicit CPU/process/thread and wall-time limits for the later run,
   reusing the validated CPU OSMesa environment. Existing timing may be cited;
   unavailable estimates remain UNKNOWN. No new cold-start/render experiment,
   EGL/GPU switch, GPU-job query, resource cleanup or deletion is authorized.

Temporary validation/evidence/selection files may be written externally on
the server; source recordings, code, configs and existing caches stay unchanged.

## Minimum response before any Gate C execution decision

Return non-sensitive **text summaries**, not server files or reversible payloads:

| Required item | Freeze content |
| --- | --- |
| Identity | Formal Root/Child/Gitlink, source clean, mapping SHA, selection SHA and server-local paths |
| Exact members | Task class, local/global episode ID, actual full frame count, camera H/W and source-binding result for each of3–5 distinct tasks |
| Scale | Total frames, camera-frames, raw-array estimate and proposed disk ceiling; current free bytes/timestamp |
| Resources | CPU OSMesa/interpreter provenance, proposed process/thread/wall-time limit and unresolved fields |
| Read-only plan | Dry-run exit/summary, full-episode and count guard PASS, no renderer/cache creation |

The manifest, raw mapping, scripts, RGB/Depth/images/video/XML/NPZ and complete
server files remain on the server. Only necessary aggregate/status/ID/hash text
is handed back for the Owner/GPT review. Do not claim S0 is complete while IDs,
lengths or capacity are unverified.

After this freeze, request the separate exact bounded Gate C execution decision.
It still requires full cache export/integrity, per-episode sampled geometry and
new documented RGB/Depth visual alignment, idempotent skip/recovery and measured
time/RSS/storage. No automatic batch start, Gate C PASS, N100, V3 promotion,
nav_sg/Global PSS, model/training/DCP or historical-result modification.
