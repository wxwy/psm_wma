# G2 P0/P1/P2 — two-GPU bounded concurrency Smoke (2026-11-13)

**Result: PASS; 2 independent original-source Workers concurrent, not a 32-Worker stress test.**

Test isolation: PSM-WMA experimental branch from V3 f29b01d3, original nav_sg Noetic runtime 9734d2e, official pinned 9,126 Episode plan. GPU6 and GPU7 were idle before launch. CPU nice=15 and ionice=idle. Independent ROS master ports 21991 and 21992; separate Episode directories under the same fresh dedicated test root. No formal v1 data, plan or running training was modified.

| Metric | CloseFridge Episode 569 | NavigateKitchen Episode 2022 |
|---|---|---|
| GPU | 6 | 7 |
| ROS port | 21991 | 21992 |
| Original-source Worker exit code | 0 | 0 |
| Complete Episode wall | 250.22 s | 178.02 s |
| Spatial states | 17 | 19 |
| FULL F27 scene states | 5 | 1 |
| Robot-arrow-only states | 12 | 18 |
| Materialized v2 PNGs | 52 | 26 |
| One-hop v2 PNG references | 84 | 126 |
| Independent SG files | 17 | 19 |
| Valid source-plan fingerprint and v2 Resume checks | PASS | PASS |
| Color / native_color_only Stage starts | 0 / 0 | 0 / 0 |

Two Worker output complete markers passed the exact pinned Episode identity and the v2 indexed image resolver. The independent CloseFridge Scene Graph was compared to the original formal v1 for all 17 frames, and all 17 JSON payloads were equal.

Both Worker sources independently completed native Room/SG, dense/Visual roster, Snapshots, GPU F27 and v2 packing. Each Worker used its own Noetic ROS port and did not share another Episode's state/cache. No unexpected resource errors or process failures occurred.

Evidence (server-local):
- /tmp/g2_p012_parallel_smoke_20261113/closefridge_569.log
- /tmp/g2_p012_parallel_smoke_20261113/navigatekitchen_2022.log
- /tmp/g2_p012_parallel_smoke_20261113/output
- /mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_p012_parallel_smoke_20261113 (independent intermediate work)

Boundaries: This demonstrates 2 Workers over 2 H100 GPUs, not the user-requested **8 Workers per GPU / 32 total**. Avoid claiming a 32-way throughput scaling factor. Complete single-Worker matched old/new speed comparison (OpenDrawer Episode 3029, 416.29 s to 213.06 s = 1.9539x) remains the best supported overall performance measurement. The 9,126 producer is still stopped, with 202 pre-existing valid v1 results.

Do not promote or launch the full 8,924 pending queue until the target workers-per-GPU configuration has a resource/concurrency acceptance gate. Use a new work-root when resuming, preserving original v1 intermediate evidence and completed outputs.
