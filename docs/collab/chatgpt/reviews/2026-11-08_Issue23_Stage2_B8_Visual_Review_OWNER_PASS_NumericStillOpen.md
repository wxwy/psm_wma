# Issue23 Stage2 — B8 VAE reconstruction visual review — OWNER PASS

**Scope verdict: `PASS_VISUAL_RECONSTRUCTION_OWNER_VERIFIED`** (one narrowly defined Gate only)  
**Formal numerical parity status: `BLOCKED_NUMERICAL_PARITY` (unchanged), Stage2 integrated Code/Action Gate: NOT APPROVED.**

Owner statement (2026-11-08): **“人眼核对batch8重建与原图无差异，我觉得可以通过”**. Accept Owner's visual quality signoff as decisive for the RGB reconstruction inspection of eight real sample inputs. Do not present this as claim of byte-identical latent or final Local-TTT Action-path invariance.

### Frozen evidence
- Exact isolated source Root `3ab4578475d8df5ce93b7bde6c4f2073a46f777e`, Child+Gitlink `0a2119782fb5078fee3359f9ef7383d788744458`, unchanged PR6 Draft.
- Genuine Wan2.2 BF16 H100 GPU4, checkpoint SHA256 `20eb789667fa5e60e7516bf509512f6cb61f01b0aa0695eadaea930c13892b36`. Eight recorded RoboCasa365 target-atomic left+wrist 256×512 composites. Original preprocess and postdecode rescale/pad removal were matched.
- Raw assets on authorized data host: `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/v3_issue23_stage2_reconstruction_20261108/`; `review_comparison.html`, `comparison_frames_0_3.jpg`, `comparison_frames_4_7.jpg`, original/reconstructed PNG, `reconstruction_report.json`, `per_frame_metrics.csv`, `batch_independence_report.json`.
- Reconstruction RGB values: original vs B1 average PSNR 30.781dB / SSIM0.95032; original vs B8 average 30.781dB / SSIM0.95031. Reconstructed B1 vs B8 **PSNR54.215dB / SSIM0.99884 / MAE0.210 per8bit channel**. Cross-slot manipulation: B8 slot0 output unchanged when seven peers replaced; B8 repeated exact; B8 permute/restore maxabs0.015625 (cannot infer zero numerical error).
- **Exact numerical parity still not met:** B8 complete pre-crop latent maxabs0.0234375 and Visual96 maxabs0.00713452697 against independent B1. The source contract used strict zero tolerance by default and had no preregistered nonzero tolerance. Owner's visual signoff cannot convert these values to zeros.

### Decision / follow-on
- **Approve visual reconstruction suitability for *continuing Stage2 research*, not as a production substitute.** Stage2 real B8 shared VAE/EGL contention/latency throughput exploration can proceed under existing owner hardware authorization while clearly marking input numeric non-equivalence.
- Gate before production Action Path: fixed-Local-checkpoint B1 vs B8 Visual96 injected into actual `scan_local_memory`, FastState/Prefix/Action diff, paired outcomes/CI where authorized, with explicit functional tolerances reviewed before confirmatory tests. No automatic Stage3 integration from reconstructed RGB alone.
- Keep B1 as bit-exact baseline. No PR6/V3 merge, 900EP/long SR, training, or hidden acceptance-criterion revision.
- Issue23 receipt: https://github.com/wxwy/psm_wma/issues/23#issuecomment-6716034660
