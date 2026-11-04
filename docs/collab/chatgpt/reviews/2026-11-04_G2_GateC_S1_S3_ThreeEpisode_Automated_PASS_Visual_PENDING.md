# G2 Gate C S1–S3 — independent native execution: AUTOMATED PASS / VISUAL PENDING

Date: 2026-11-04. Execution on the authorized DS server by GPT. **All machine steps finished successfully; final Gate C remains PENDING human visual review of the new task scenes.**

## Exact approval and identity

- Approved production Formal Root: 3eb8b334150018212ae1f51afb5e954b83fa1186; Child/Gitlink: 1069fe78841228cadbbfbe6afbd767eaed6225da. Isolated source checkout remained clean.
- Original Gate C S0 freeze: cd143c4bf6322a39cb7855772a944d45a49ffcf8; separate execution approval and mandatory durable-chunk correction: d3374c0e35c6d8bfc308b45c399b48cd3870f0f3.
- Codex's local d4edb96b push previously failed. GPT directly synchronized the agreed durability correction to the remote contract in docs commit **59beb9fe5b3e893d6b86254f00524672638bd49f**; this is a different commit and should not be represented as a successful push of local d4edb96b.
- Mapping SHA256 aa884820494a17f50b41a8a8c2bfa6b6fda11babbbef31c449c1c0ce850e09ed; exact frozen selection manifest SHA256 10d668ee42b5145a8cad09878c331ef940b06d91a6a9666ae85434b61c225926. Both checked before run.
- One sequential CPU OSMesa process, CUDA_VISIBLE_DEVICES empty, 1 numeric thread/library, one shared 45-minute ceiling (timeout TERM at 2685s, KILL after 15s), no EGL/GPU.
- Server-local scripts SHA256: Python afdd36e4202279d8a0887ff74740df1f9bf9b8fe979b2492c6809ee343f14bcb; shell 8eac14ccd9ed5d486f576e1f17da300bf2cb0613f80e46191e83c83687c8ea51. Runner PID/command/group/start-time stored in evidence.
- Runner end status exit **0**, result **AUTOMATED_S1_S3_PASS_VISUAL_PENDING**.

## S1 — three full episodes and controlled one-time interruption

| Real underlying task | Local / global | Full frames | Physically sampled indices | Export | Compressed NPZ payload bytes |
|---|---|---:|---|---|---:|
| CloseFridge | 0 / 502 | 429 | 0,214,428 | EXPORTED, complete integrity PASS | 24,730,834 |
| NavigateKitchen | 0 / 2022 | 177 | 0,88,176 | planned SIGTERM, one full restart EXPORTED, integrity PASS | 10,787,869 |
| PickPlaceCounterToCabinet | 0 / 4038 | 246 | 0,123,245 | EXPORTED, complete integrity PASS | 10,988,607 |
| **Total** | **3 classes** | **852** | **9 frames × 2 cameras = 18 checks** | **3/3** | **46,507,310** |

Cameras: robot0_agentview_left and robot0_eye_in_hand, each 256×256. Original RoboCasa RGB is the reference; new metric Depth uint16_mm, K/Pose, chunk32. No temporal frame subset was used during full episode export.

S1 recovery witness: only owned NavigateKitchen Python PID **3771150**, start ticks **1616194008**, had both camera initial NPZ chunks closed and checked, each containing frames 0–31. Staging path remains under new cache: .staging/c7b11bfb670048e390c1b2241f27eb4e. One SIGTERM delivered 2026-11-04 11:10:57 UTC to the verified owned PID; exit **-15**, episode 2022 not committed at interruption. No durability claim was made for buffered frames.jsonl. Exactly one same-identity retry **from frame0**, not partial-chunk continuation, completed all 177 frames with no duplicate commit and no CloseFridge hash drift. Uncommitted staging (~1.7 MB) preserved; no unexpected retry.

## S2 — full offline and independent native spatial verification

- Full committed-cache verification **3/3 PASS**, all 852 source frame indices unique/contiguous, two cameras, all chunk hashes/quantized values/manifest/COMPLETE checked.
- Independent native sampled spatial checks **18/18 PASS** (6 per task), 128 matching rays per camera/frame (threshold at least16), max optical-axis Z errors less than 0.01m; fresh/cached depth, K/Pose, runtime and reprojection rules unchanged.

| Task | Checks | Maximum ray Z error | Minimum opaque-eligible pixels | Photometric MAE > 5 cases |
|---|---:|---:|---:|---:|
| CloseFridge | 6/6 PASS | 0.004423339 m | 37,549 | 5/6 |
| NavigateKitchen | 6/6 PASS | 0.004660357 m | 19,479 | 1/6 |
| PickPlaceCounterToCabinet | 6/6 PASS | 0.003915728 m | 46,154 | 0/6 |
| **Total** | **18/18 PASS** | **0.004660357 m** | | **6/18 diagnostic FAIL** |

Original-video RGB MAE, PSNR and SSIM are preserved as **nonblocking photometric diagnostics**. No retouching or replacement of the original RGB.

Server-only generated original-RGB / metric-Depth / red-Depth-edge overlay contact sheets:
- /tmp/g2_gate_c_s1_s3_3eb8_20261104/visual/RGB_Depth_Contours_CloseFridge_000502.png — SHA256 0914468dddb5a352b318f7171a87533c29e145985c8d5447186f7d97da6d5934
- /tmp/g2_gate_c_s1_s3_3eb8_20261104/visual/RGB_Depth_Contours_NavigateKitchen_002022.png — SHA256 e1ad87c705b96e82a87e1490017e8c278fa6ce72ae578651a1b62c91efdf34cc
- /tmp/g2_gate_c_s1_s3_3eb8_20261104/visual/RGB_Depth_Contours_PickPlaceCounterToCabinet_004038.png — SHA256 501f46188944b78e0b3a2ab08bee83484727a71c25ebcb4e75528727113fec2e

**Owner/independent visual review remains PENDING**. The tool wrote visual/review_pending.json with per-scene task/ID/frames/cameras/cache export digests, report/image hashes; did not assert automatic visual PASS.

## S3 — exact skip, hashes and measured budget

- Same three per-ID exporter commands repeated once: **3/3 SKIPPED_VERIFIED**, without new replay/environment construction, all immutable committed episode payload/manifest/COMPLETE hashes unchanged. Expected new run logs only.
- Total machine elapsed **329.99 seconds (~5min30s)** across S1 + S2 + S3 including startup, aborted attempt, re-export, all integrity/native checks, visualization and skip verification; lower than one shared 45-minute ceiling.
- Full successful export command wall times: CloseFridge 106.32s, NavigateKitchen restart 54.80s, PickPlaceCounterToCabinet 59.38s; deliberate interrupted attempt 26.91s separately.
- Native physical sampled verification wall: 20.22s / 23.67s / 22.84s (global 502/2022/4038).
- Raw-array bytes 335,313,120; committed compressed NPZ bytes **46,507,310**, observed compression ratio **7.2099:1**. Not extrapolated from the earlier three-frame probe.
- Peak observed RSS: interrupted NavigateKitchen ~5,051,668 KiB; completed native 2022 via process time ~5,034,344 KiB. Other rendering ~4.36–4.41 million KiB. Host GPU not used.
- Committed task storage 47,675,013B; preserved interrupted staging 1,703,729B; entire new cache 49,389,714B; evidence approximately 4,400,574B at summary time. Filesystem free before 137,644,716,032B, after 137,577,525,248B; 1GiB reserve maintained.
- Successful frames divided by successful export command wall ~3.86 fps, including intentional-abort wall ~3.44 committed fps during S1, divided by total all-S1–S3 machine wall ~2.58 frames/sec; distinguish metrics and no real-time performance claim.
- No unplanned failures, no production code alteration, no V3 main merge.

## Evidence and next boundary

Server-only immutable cache root:
  /mnt/data1/data_v2_0617/g2_rgbd_pose/gpt_gate_c_candidate_s0_20261104

Server-only evidence folder:
  /tmp/g2_gate_c_s1_s3_3eb8_20261104

Key reports: final_machine_summary.json, s2_spatial_summary.json, s1_interruption_witness.json, runner_identity.json, individual S2 native/offline reports under reports/, full visual contact sheets under visual/.

**Decision:** Gate C machine execution **AUTOMATED PASS; final Gate C PENDING visual alignment confirmation for these newly sampled scenes**. Do not infer the earlier six-frame Owner approval for NavigateKitchen/PickPlace. Owner should check RGB-vs-Depth contours, moving object positions and occlusions in all three sheets. Record exact task/global IDs/frame/camera and review provenance externally before final Gate C closure. No N100/V3 promotion/nav_sg/Global PSS/training/DCP/GPU authorization follows automatically.

No original RGB, Depth arrays, NPZ, videos, images, raw Parquet/XML or server scripts were transferred off server. This GitHub file is text-only.