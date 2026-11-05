# G2 Stage-1 batch 000 — GPU4/5/6 production stopped on uint16-mm range (not GPU7)

Date: 2026-11-05 11:00 China Standard Time; live server observations UTC 2026-11-05 02:56–03:00.

**Status: STOPPED_NON_SUCCESS; no automatic restart authorized by the run contract.**

## Exact execution and no-change scope

- Formal G2 Root `3eb8b334150018212ae1f51afb5e954b83fa1186`, Child/Gitlink `1069fe78841228cadbbfbe6afbd767eaed6225da`. Clean source checkout, approved prod output root `/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-depth`.
- Exact frozen first cohort: 100 episodes / 24,059 complete source frames, global batch selection SHA256 `8561c81b0382bf79d360f5028d6fa67ab2848589bf77199f9d3f97861e760080`. Cameras `robot0_agentview_left` and `robot0_eye_in_hand`, no Right.
- CPU OSMesa Gate C originally passed 3 tasks. A **separate bounded GPU4 EGL pilot** was then run on 18 preverified camera-frame samples, returning 18/18 geometry PASS, masks identical and Depth P99 difference ~0.5mm. GPU5 and GPU6 each passed a 2-camera EGL native smoke. GPU7 was explicitly **excluded** from production because a GPU7 EGL Depth-buffer test failed twice. GPUs0–3 untouched.
- Producer: GPU4, GPU5, GPU6 **parallel**; 34/33/33 disjoint episodes, 8,156/7,645/8,258 frames. One Python exporter process per GPU at a time; `CUDA_VISIBLE_DEVICES` / `MUJOCO_EGL_DEVICE_ID` exactly respective physical GPU index, `MUJOCO_GL=egl`, one thread per numeric library.
- No 25GiB overall cache cap and **no four-hour global time deadline**, by Owner request. An independent **100GiB minimum free disk reserve** remained enforced by the existing cache writer and supervisor. Server recorded progress at every episode; the planned server 10-minute heartbeat did not fire because the batch stopped within about 80 seconds.
- Scripts are server-local only: `/tmp/g2_full_atomic_batch000_gpu456_20261105.py`, SHA256 `75e8aec29c0edb273d3797fb4743435ef9c157e864211aa602951411e59d7ae5`; shell `/tmp/g2_full_atomic_batch000_gpu456_20261105.sh`, SHA256 `7b4612246b3dc7d5ff5cff4971040487a86fa4ff39a4f81ba96c2da4bbe30d1b`. Tmux session `psm_g2_batch000_gpu456_20261105` was released after the failure.
- Full text evidence `/tmp/g2_full_atomic_batch000_gpu456_20261105/`, launch log `/tmp/g2_batch000_gpu456_launch_20261105.log`, per-GPU logs, immutable verified per-episode JSON receipts, supervisor summary and captured failure. No source code, training, old caches, V3 branch, GPU0–3 or GPU7 altered by the production run.

## Actual first-run result

- **7 / 100 episodes** were successfully committed and verified by the strict full-cache reader, covering **2,353 / 24,059 source frames**. Committed sensor payload **106,087,913 bytes**. Per GPU: GPU4 completed 3; GPU5 completed 2; GPU6 completed 2. Verified output is immutable and should not be deleted or silently regenerated.
- Next target GPU6 `CloseFridge` global episode **736** (local episode234, **230 full frames**) returned CLI exit code **1**, `ValueError: uint16_mm depth overflow/underflow; use explicit float32_m`.
- The failed uncommitted attempt processed **73 rows** (frames0..72), with the first invalid representability at **frame73**. Its evidence remains in the new output's `.failed/0c9a064af0184e5cbbbc62a5afbc80f8`. Two other workers were deliberately terminated, preserving their uncommitted `.staging` evidence.
- Supervisor observed GPU6 nonzero, terminated owned GPU4/GPU5 groups, and exited nonzero. No process from the batch remained running; no automatic retry, change of format, silent clipping or padding occurred.
- At stop, free `/mnt/data1` disk approximately **293,255,356,416 bytes**: disk/size budget was not the cause. The experimental schedule failed due to storage-value range, not available capacity or four-hour deadline.

## Independent read-only root-cause reproduction on BOTH backends

Code contract: `tools/g2/rgbd_pose/geometry.py` `encode_depth` deliberately rejects valid metric Depth values smaller than `0.001m` or larger than `65.535m` for `uint16_mm`, rather than silently clipping. `Replay.render` currently treats finite OpenGL Depth-buffer pixels with raw value below1 as valid; its depth conversion can produce metric far values well above65.535m.

A new **read-only EGL GPU6 replay** of source episode736 frames72/73/74 found:

| Frame | Camera | Valid pixels exceeding 65.535m | Valid metric max | Below 0.001m |
|---|---|---:|---:|---:|
| 72 | left | 0 | 2.789m | 0 |
| 72 | wrist | 0 | 3.558m | 0 |
| 73 | left | 0 | 2.789m | 0 |
| **73** | **wrist** | **25/65,536** | **591.547m** | 0 |
| 74 | left | 0 | 2.789m | 0 |
| 74 | wrist | 230/65,536 | 614.359m | 0 |

**Independent CPU/OSMesa replay** of the same frame73 and frame74 reproduced **exactly 25 and 230** out-of-range wrist pixels and the **same maximum Depth values**. Therefore **this failure is NOT specific to GPU6 or EGL**. The scene's near/far configuration seen in MuJoCo is `model.vis.map.znear≈0.001`, `zfar=50`, `extent≈19.94`; far-range optical-Z values are plausible in the renderer, but not representable as uint16 millimeters. Do not blindly state that the affected pixels are true in-room object surfaces or a GPU driver issue.

## Recommended contract decision before resuming production

The Owner explicitly selected the Gate C format: **compressed NPZ, uint16 millimeters + valid mask, K, GL/CV camera poses and frame indices**, original RGB referenced, no duplicate RGB, two cameras only. Do not silently override the requested format to `float32_m`.

**Preferred minimal path if the Owner accepts a representable-range validity policy:** define `valid_for_uint16_mm = renderer_valid & (0.001 <= depth_m <= 65.535)`, mark excluded far/near pixels invalid and depth=0, **count/report excluded pixels** per frame/camera/episode, do not saturate or wrap. Update renderer/cached spatial-verifier comparison to account for the storage-aware mask and preserve independent ray geometry checks. Add positive and negative tests and reverify with native replay (including episode736 frame73/74) under a new Formal Pair before resuming. This preserves high-precision near-field depth but changes the semantic definition of `valid`, requiring an explicit reviewed change. Establish an alert/budget for unexpectedly large fractions of invalidated pixels.

**Alternative:** output `float32_m` from the existing supported exporter into a **separate, newly approved cache namespace** (not the existing uint16 cache root). This preserves all far valid pixels but changes dtype and potentially substantially increases disk usage; no automatic fallback or mixed-identity files in the existing cache root.

**Neither fix has been implemented or authorized.** The observed failure must remain visible. Existing 7 committed uint16 episodes, failed staging and all prior Gate C evidence are preserved. Before resumed production decide the range policy, review code/validation accordingly, preserve or explicitly migrate existing verified cache identities, and then resume only the **same frozen first-100 cohort** on GPU4/5/6. No new sampling or other batches.

G2 Gate C original 3-episode PASS remains historically valid, but does not prove all 9,126 source episodes are representable in the current `uint16_mm` codec.

An hourly platform monitoring task created when production was underway was disabled after the terminal failure to avoid spurious progress notifications. Server-side monitoring stops with the producer and remains reproducible through saved text logs.
