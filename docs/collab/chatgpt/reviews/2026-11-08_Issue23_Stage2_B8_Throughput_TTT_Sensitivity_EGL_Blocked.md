# Issue23 Stage2 — Real Wan B1/B4/B8 throughput, trained Local-TTT/Action sensitivity, EGL access Gate

**Verdict: `PARTIAL_STAGE2_EVIDENCE`; `BLOCKED_OS_DRM_PERMISSION` for real 16Sim/EGL; original `NUMERICAL_EXACT_B8` still NOT PASSED; `Stage3/merge` NOT AUTHORIZED.**

Date: 2026-11-08 UTC/CST. Owner explicitly approved further Stage2 tests after human visual B8 reconstruction PASS. Formal isolated source unchanged: Root `3ab4578475d8df5ce93b7bde6c4f2073a46f777e`, Child+Gitlink `0a2119782fb5078fee3359f9ef7383d788744458`. Latest official V3 at verification Root `7b8b733e1f585bb44a0eac7c14ad545c29355a86`, still Child `1ca308055fc41fb69efaeb9efaa23808f164a18e`; PR6 remains Draft/unmerged. No existing checkpoint/GPU0–3 training/production source was modified. No networking to external image upload.

## 1. Dedicated GPU4 true Wan BF16 VAE, warmed throughput (not Sim)

RoboCasa365 target-atomic genuine 256×512 left+wrist composites, 32 frames/trial. For each B in {1,4,8}, 4 warmed batches then 7 **interleaved** measured trials, same loaded real frozen Wan VAE, same Stage1 `LoadedWanEncode1`, CUDA event around just `tokenizer.encode`, and walltime around full adapter (source verification, preprocess, copy, encode and Visual96 to CPU), exclusive GPU4.

| Actual B | Adapter full wall median/32-frame | Adapter frames/s | VAE CUDA encode median/32-frame | Kernel frames/s |
|---|---:|---:|---:|---:|
| 1 | 233.695ms | 136.9 | 123.630ms | 258.8 |
| 4 | 122.051ms | 262.2 | 43.670ms | 732.8 |
| 8 | **110.457ms** | **289.7** | **38.028ms** | **841.5** |

B8 vs B1 ~**2.12×** whole adapter / **3.25×** CUDA encoder improvement. B8 still differs numerically from B1 on H100 BF16; this throughput Gate does not waive prior exact-zero requirement. No EGL contention or full Policy generation included.

## 2. Trained DCP Local-TTT/Action response to B8 BF16 evidence

GPU6, *actual* Local-TTT iter15000 checkpoint and config under `outputs/local_ttt_robocasa_raw15/...`, real RoboCasa365 16-frame sequences, `scan_local_memory` (create_graph=False, T16) and 30-step native UniPC Policy sampling with exact same current observation/seed. A fixed deterministic **synthetic raw15 action tensor** is injected in both arms (no real executed action or closed-loop SR claim); 3 cases (two consecutive RGB windows, two action seeds). B1→B8 observed max across cases:

- Visual96 `max_abs=0.01034189760684967`.
- FastState parts `max_abs=0.00024708639830350876`.
- final Prefix `max_abs=0.0018797218799591064`.
- native denormalized final `Action[16,15]` `max_abs=0.03011929988861084`. Per case Action relative RMS differences **0.4869%–0.6020%**, native Action reference replay(B1→B1) exactly0.
- Per-case action max differences `0.0301193`, `0.0177335`, `0.0182785`. Thus effect propagates, is not random generation noise, and cannot be asserted harmless. No blow-up in these 3 controlled samples, but no full-task SR/closed-loop behavior has been demonstrated.

## 3. Genuine Stage1 Worker/Unix IPC 16-client *offline* test

A single loaded genuine Wan VAE worker (GPU4), real `SharedVAEWorker` + `UnixVAEServer` and `LocalVAEClient`. 16 separate *Python threads* acting as offline Session clients (NOT 16 isolated actual simulator processes), four recorded images each =64 frames total. Mock Owner `owner_complete` pre-authorized the replayed frames; **does not authenticate successful future env.step in production**. Actual native batch hist/latency, signed feature receipt, ACK, End and zero retained buffers checked.

| VAE B/wait | Actually selected batches | 64-frame end-to-end FPS | Client-side latency median |
|---|---|---:|---:|
| B1,0ms | {1:64} | 4.61 | 9374.6ms |
| B4,5ms | {4:15,2:2} | 12.73 | 3001.2ms |
| B8,5ms | **{8:7,6:1,2:1}** | **17.05** | **2516.7ms** |

**Caveat:** absolute throughput/latency are strongly affected by *single-process 16 Python-thread workload*, control-lane polling, CPU/base64 IPC, and are not credible estimates of isolated multi-process Sim throughput or 1×1 deployment latency. Evidence only supports that real Stage1 Worker under simultaneous *offline* requests forms B8, maintains session identity/cleanup, and relative microbatch effectiveness exists. B8 worker does not substitute for genuine RoboCasa EGL step contention measurement.

## 4. Real Sim/EGL attempt blocked by OS device permissions

Actual RoboCasa vendor `CloseFridge` `make_env/reset`, tried GPU4 first and GPU7 as alternative. Actual physical index/PCI lookup: GPU4 mapped EGL index11; vendor's current EGL enumeration exposed only indices0–9 and rejects11. GPU7 maps EGL index8, passed index bounds but initialization failed (permission denied). Verified under current service login `robo-shenzhen` uid1004, groups ONLY `robo-shenzhen`; DRM devices `/dev/dri/renderD132/134/135` owned `root:render mode0660`, `/dev/dri/card8` `root:video mode0660`, every direct OS open returned `EACCES` (errno13). Actual vendor log: `libEGL warning: failed to open /dev/dri/renderD135: Permission denied`. No real Env reset succeeded, no 16Sim/EGL live contention, no live SR.
**Do not** infer GPU4/5 render impossible forever from this login's device enumeration; fix OS group/ACL access via authorized administrator, re-establish login session and repeat physical EGL attestation/one-Sim smoke *before* 16Sim. No sudo/chmod/chgrp/PCI bypass used.

## 5. Raw evidence, final status and next Gate

All raw scripts/logs/JSON locally on authorized `data`:

- `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/v3_issue23_stage2_perf_20261108/wan_benchmark.json` and `actual_worker_ipc_offline_16clients.json` (and scripts/logs).
- `.../_gpt_independent_gates_20261104/v3_issue23_stage2_sensitivity_20261108/local_ttt_sensitivity.json` and script/log.
- `.../_gpt_independent_gates_20261104/v3_issue23_stage2_sim_contention_20261108/smoke/slot_00.json`, `smoke_gpu7/slot_00.json`, and vendor log/isolated harness.

Final GPU4–7 all 0MiB. Source Root/Child worktrees still clean.

**Gate status summary:**
- Owner B8 RGB reconstruction **PASS** on inspected 8 example frames (previous Gate).
- Warmed real VAE B4/B8 **THROUGHPUT MEASURED**.
- Real Local-TTT and native Action **SENSITIVITY MEASURED, NONZERO**; 3 fixed-input cases do **not** prove action safety or SR invariance.
- Stage1 real Worker Unix IPC **OFFLINE CONCURRENCY MEASURED**, not live 16Sim.
- Actual 16Sim EGL + VAE contention **BLOCKED_PERMISSION**.
- Strict numerical exact0 **still FAIL for B4/B8** (preregistered contract unchanged).
- Single 1Policy×1Sim NoTTT vs LocalTTT P50/P95/P99 and paired SR **NOT_RUN**; Stage3 Policy feature ingestion/official V3 merge **NOT APPROVED**.

Before official Stage2 closure or any Stage3, require environment access restoration, real EGL sim baseline vs sim+Worker co-residency, then independent reviewed downstream numerical/functional tolerance and paired closed-loop evidence.

Issue comment source: https://github.com/wxwy/psm_wma/issues/23#issuecomment-6716199069
