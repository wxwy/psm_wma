# Issue24 Stage3A — RoboCasa 1 Policy Server ×1 Sim A/B/C iter15000 3-repeat Performance Gate

**Verdict: PASS_REPEATED_EXPERIMENT_EVIDENCE — Three valid isolated fresh episodes per arm, real H100.**

This is a bounded system-performance repeatability report, not a benchmark-generalization or robot task success Gate. No production implementation or official V3 merge, no training, and no 900EP suite.

## 1. Frozen identity and fair controls

Formal implementation Root `8a17c3db6a2e571b67e6a149638f9d7922a704d5`; Child/Root Gitlink `00f30235da6ffb085a9304ef6501ede509203092`. Both source checkouts remained clean. Source work and existing PR25 / PR7 remain draft, not merged.

All runs actual RoboCasa `CloseFridge` episode0, seed **4603**, same frozen iteration **iter_000015000**, one actual GPU6 Policy Server, one GPU4 EGL Sim, server inference batch max1, action horizon16, 30 UniPC steps, exact 900-step official horizon. A = a separately trained No-TTT checkpoint at iter15000 / `off`; B = original Local-TTT iter15000 / Policy-owned `server_vae` history T16; C = the *exact same trained checkpoint as B* / actual GPU4 shared Wan Bvae1/wait0 historical feature and Policy16×T1 Local-TTT.

The deployment contract **requires** A/B `batch_wait_ms=1`, C `batch_wait_ms=0`; this tiny unavoidable control difference is retained and disclosed. C has an additional genuine Wan Worker sharing GPU4 with Sim; A/B do not. The new six runs use NVIDIA-only EGL ICD in process environment; one historical A first attempt without this ICD selection was invalid at startup and excluded from the three qualified episodes, as already documented. No identity or vendor checks were disabled.

The first valid A/B/C runs were preserved and reused. Six fresh additional runs ran serially to avoid GPU contention, alternating order **r2 A→B→C, r3 C→B→A**. All six new Exit=0, complete, valid1/1 each, invalid0, clean_execution=true, results_qualified=true. Every one of the 9 valid total runs completed exactly900 executed actions, 57 Replans, 56 historical transitions (B/C), and official horizon. The robot task outcome is valid failure for **all9 episodes**: successes 0/3 each; repeated same seed is not a multi-seed generalization claim.

## 2. Actual nine-run Episode performance

Times in seconds are actual episode elapsed, not fresh command launch/asset preflight or model startup. The **single expected valid episode per run** is 900 steps; no synthetic extrapolation.

| Arm | Repeat1 | Repeat2 | Repeat3 | Mean | Sample SD | Valid task SR |
|---|---:|---:|---:|---:|---:|---|
| A No-TTT | 88.1959 | 92.5172 | 94.5058 | **91.7396** | 3.2260 | 0/3 |
| B original Local-TTT server_vae | 164.9639 | 162.0878 | 156.1443 | **161.0653** | 4.4978 | 0/3 |
| C optimized Local-TTT sim_shared_vae B1 | 144.2559 | 127.3781 | 133.9067 | **135.1802** | 8.5107 | 0/3 |

B vs C per matching repeat delta C−B: **−20.7080**, **−34.7097**, **−22.2376** seconds. Average C−B **−25.8851s**, sample SD **7.6805s**. C reduces complete Episode elapsed by **16.07%** using (Bmean−Cmean)/Bmean and increases matched hardware throughput by **Bmean/Cmean ≈1.1915×** (mean of three per-repeat ratios =1.1940×). All three comparisons improved.

A vs B average Episode extra time +**69.3257s**; this is an engineering runtime overhead comparison but **A uses differently trained weights**, so not a same-weight ablation.

## 3. Per-request Replan latency, 55 steady-state requests each episode

Discard first two cold/warmup Replans from each run, then compute each run's own P50/P95; report **arithmetic mean of the three per-run quantiles**. Do not confuse with pooled quantiles across165 requests.

| Per-run metric | A No-TTT | B original LocalTTT | C shared-VAE LocalTTT |
|---|---:|---:|---:|
| First request mean | 13489.764ms | 12564.171ms | 12987.409ms |
| Steady Replan P50 run1 | 611.658ms | 1269.938ms | 1517.911ms |
| Steady Replan P50 run2 | 598.890ms | 1311.730ms | 1158.325ms |
| Steady Replan P50 run3 | 597.738ms | 1284.294ms | 1147.333ms |
| **Mean of three P50** | **602.762ms** | **1288.654ms** | **1274.523ms** |
| **Mean of three P95** | **699.371ms** | **1315.647ms** | **1410.071ms** |
| Pooled 165-point P50 | 600.746ms | 1292.846ms | 1161.278ms |
| Pooled 165-point P95 | 639.595ms | 1319.918ms | 1538.566ms |

C−B matched per-run steady P50 differences: **+247.973ms, −153.405ms, −136.961ms**, arithmetic mean **−14.131ms** with SD **227.138ms**. C's per-request latency is highly **nonstationary**, as already established by the independent fixed-input sampler profile: there is no credible claim of a **consistent** Replan speedup from this 3-repeat data. Both pooled and per-run metrics are preserved and explicitly labeled; pooled statistics overweight the specific fast/slow portions inside each episode.

## 4. Stage timing P50 averaged across the three runs

Reported values are the mean of three separately measured within-run 55-request medians. Trace names and timing scopes differ by mode. Do **not** sum nested spans/P50 into fictional critical-path latency.

| Actual recorded stage | A | B | C |
|---|---:|---:|---:|
| Policy-side historical VAE per frame | N/A | **4.823ms** | absent / encoded_steps0 |
| Historical payload prepare per Replan (includes history encode) | N/A | **167.018ms** | absent |
| Root batch_prepare_ms | 0.017ms | **203.359ms** | 0.018ms |
| C feature_prepare_ms (includes fast update) | absent | absent | **86.899ms** |
| FastWeight update | absent | **36.049ms** | **82.338ms** |
| Current-frame VAE | **4.357ms** | **4.274ms** | **5.370ms** |
| Policy native generation | 548.382ms | **983.919ms** | **1100.706ms** |
| Transaction native_generation_ms | 556.501ms | **989.747ms** | **1117.228ms** |
| Policy Queue | 0.189ms | 0.296ms | 0.107ms |

Actual cumulative old historical encode in B = **896 policy frames per run** (56×16). In C = **0 policy historical VAE frames**, while maintaining **896 Local-TTT adapted steps per run and 56 Prefix injections**; in A both 0. This is not an unloaded/disabled C memory path: real Wan Worker B1 and Local-TTT functionality were independently verified.

The apparent run1 C slow-generator regime remained nonstationary in later repeats: C's three within-run Native Generation P50s **1353.806, 1006.405, 991.472ms**, compared with B **973.027, 1006.005, 990.208ms**. Consistent with earlier true DCP GPU6 fixed-input alternating probe showing B vs C native generation no intrinsic algorithmic penalty. The extra C T1 fast update execution is real, but it does not prevent C's actual Episode-level improvement.

## 5. Strongest behavioral parity evidence

For **each of the 3 individually matched B/C run pairs**, on-disk authoritative actions were independently loaded and compared:

- all900×15 `predicted_raw15`: `max_abs=0`, bit-exact;
- all900×12 `submitted_env12`: `max_abs=0`, bit-exact;
- all57×16×15 Policy generated Action Chunk: `max_abs=0`, bit-exact.

Thus B/C hold the same checkpoint, seed, task and **exact action outputs for all three pairs**; no claim is made about exact byte-identity of every RGB observation without independently comparing the RGB archive. A uses another model and is not supposed to generate the same actions.

## 6. Original auditable data

The source-locked local evidence folder on authorized `data` machine:

`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue24_stage3a_ABC_iter15000_3repeats_20261109/`

Contains frozen `experiment_manifest.json`, `driver_status.log`, six original `fresh_*.log/.exit`, six run directories with original sealed Actor config / canonical 900 actions / 57 predictions / media & cleanup / run summary, and `aggregate_three_repeats.py` (reviewer-only postprocess script). The three historical valid runs remain in their prior immutable dirs as referenced by manifest.

Audited machine-readable aggregate:
`ABC_iter15000_three_repeat_stats.json`
SHA256 **`dade842a46411d3355694fc7b2c8942cbb80a29d4049cca3e033c89d1eef7885`**.

Aggregation script asserts all Formal SHA, config provenance, full successful clean execution, canonical Replan/Action source indices, full historical evidence and B/C 3× bit-exact parity. It saves per-run quantiles, pooled 165 sample quantiles, means, SDs, raw sha256 references, and every pairwise time delta.

## 7. Decision boundaries

**`PASS_REPEATED_EXPERIMENT_EVIDENCE`** for single Server × single Sim timing comparison. Based on three matched real runs, C is **~16.1% faster in complete Episode elapsed** (B/C same trained Local-TTT checkpoint and exact actions), without implying statistically established gains across different tasks or seeds. On P50 Replan C≈B across three runs, C p95 average is worse due intermittent slow regime; do not claim C consistently reduces request latency.

No further CPU governor/NUMA/Kernel root-cause chase is required for this engineering decision. No new full 900EP suite, no Stage3B B8 Action parity, no train, no official V3 merge or PR25/PR7 merge. Reviewer did not alter the other user's GPU4–7 workloads visible after the six completed runs; successful program exit and all owned process cleanup were independently confirmed by each run's formal summary.

**The sample average and raw result file are the intended decision basis, not any single fast/slow profile.**
