# G2 P0+P1+P2 — 32 concurrent Worker production-configuration resource gate
Date: 2026-11-13

**Gate: PASS. 32/32 completed, zero failures, zero resource aborts.**
**This was an isolated bounded real-original-source smoke test, NOT resumption of the formal 9,126 Episode production.**

## Configuration and source integrity

- 4 × NVIDIA H100 80GB: GPU 4, 5, 6, 7.
- **8 concurrent real RoboCasa Worker processes PER GPU**, 32 total; 32 independent ROS master ports 22100–22131.
- Each process executed the actual pinned official-plan "work" codepath with P0 Lazy Texel, P1 GT 1 mm / 1 degree event-indexed Views, P2 direct MuJoCo material and source-bound native geometry/Room/SG. No color nor native_color_only stages.
- Exactly 32 **distinct Episodes**, representing **all 18 task classes and all 10 scene Layouts**.
- The samples intentionally favor SHORT Episodes to complete the bounded smoke: **417 spatial states across 32 jobs (13.03 per Episode)** compared with 25.8 average spatial states in the complete 9,126 source. This is a resource and isolation gate, NOT a statistically representative throughput benchmark for the whole dataset.
- User training GPUs 0–3 were not assigned G2 work, and existing formal v1 output/plan were never modified.
- CPU processes nice=15, ionice idle, OPENBLAS/OMP/MKL/NUMEXPR_NUM_THREADS=1. No automatic retries or fallback to different episodes.
- Distinct, immutable official Plan rows (source fingerprints) for every Episode; output root and work root were independent new pressure-test paths.

## Results

| Metric | Evidence |
| --- | --- |
| Workers launched | 32 |
| Max simultaneously active | **32** |
| Per-GPU simultaneous workers at launch | **4:8 / 5:8 / 6:8 / 7:8** |
| Source Worker successful exits | **32** |
| Failed exits | **0** |
| Timeouts / resource watchdog aborts / OOM | **0** |
| All 32 complete receipts and v2 Manifest SHA + exact source fingerprint validated | **PASS** |
| Frame ordering and 2 Hz sampled state counts | **PASS** |
| Every per-frame gzip Scene Graph readable and bound to the correct source frame | **PASS** |
| Every materialized PNG exists as a regular file | **PASS** |
| Every indexed PNG is a direct prior-state reference within the same Episode, with a physical owner | **PASS** |
| Total bounded batch elapsed | **365.1 seconds** |
| Peak reported NVIDIA GPU 4 memory | **777 MiB** |
| Peak reported NVIDIA GPU 5 memory | **887 MiB** |
| Peak reported NVIDIA GPU 6 memory | **915 MiB** |
| Peak reported NVIDIA GPU 7 memory | **819 MiB** |
| Resource abort | **none** |

Memory/disk watchdog maintained at least 200 GiB MemAvailable and safe disk buffers under both /mnt/data and /mnt/data1. Current system resources were comfortably above these guards. Because GPU usage is sampled periodically, reported VRAM numbers are **sampled maxima**, not instantaneous hardware high-watermark measurements.

Complete original structured evidence:
- /tmp/g2_p012_32smoke_20261113/selection.json
- /tmp/g2_p012_32smoke_20261113/orchestrator.py
- /tmp/g2_p012_32smoke_20261113/monitor.log
- /tmp/g2_p012_32smoke_20261113/status.json
- /tmp/g2_p012_32smoke_20261113/result.json
- /tmp/g2_p012_32smoke_20261113/workers/*.log
- compact generated samples: /mnt/data1/data_v2_0617/robocasa365_v3_flat/.g2_p012_32smoke_20261113

## Disk outlook and limitations

At production preflight, /mnt/data1 had about 151 GiB free for the original output root. The 32 compact v2 samples averaged approximately **0.422 MiB per sampled spatial state (median)** or **0.472 MiB per spatial state (simple mean)**. With 8,924 pending episodes / 227,865 spatial states, crude global extrapolations were about **94–105 GiB**; a task-weighted sample extrapolation was about **111 GiB**. These are not conservative upper bounds; a worst-sample scaling produces >150 GiB. Disk free space must be monitored throughout the full run, and original 202 completed v1 Episodes must not be overwritten.

The actual **same-episode paired original-source Worker A/B** remains OpenDrawer/episode_003029: 416.29 s old v1 vs 213.06 s P0+P1+P2, **1.9539×** speedup. The 32 short-sample stress result should not be presented as the performance estimate for the full production dataset.

## Promotion decision

The 32-worker requested resource/concurrency configuration has now passed a bounded end-to-end smoke, complementing the earlier 916 Python tests, four Viewer Node tests, two independently completed original-data source Workers, 1.95× same-input A/B, original 9,126-plan read-only Resume check, v1/v2 mixed Resume, and user human H1 visual approval.

Promotion to formal V3 is now technically eligible, subject to a clean Draft PR review, unchanged original nav_sg implementation, explicit source and output isolation, and a new v2 work-root. The formal immutable plan, the original output root and 202 existing completed v1 Episodes must be preserved.
