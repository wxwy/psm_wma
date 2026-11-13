# G2 P0/P1/P2 final pre-promotion gates — 2026-11-13

**State: independent integration PASSED. Formal V3 not modified. Full producer stopped.**

Source branch base: V3 f29b01d3235a7fbfd8e17727b8edaf2155957b35. Original nav_sg 9734d2e0e261a47efbd00f5de78ec6c1a983557b remains unchanged.

## 1. Matched complete Worker A/B: OpenDrawer episode_003029 / Layout 5

Same official RoboCasa source episode, same GPU 7, CPU nice 15 / ionice idle, identical immutable plan row, sequential real original-source Worker runs. Independent output and work roots. Experimental optimized run was first, original v1 production Worker second. Both returned complete formal receipt with 36/36 sampled states.

| Stage | Original v1, seconds | P0+P1+P2, seconds |
| --- | ---: | ---: |
| Source | 5.54 | 5.26 |
| Metadata | 1.88 | 1.87 |
| Grid | 1.52 | 1.52 |
| Native GT | 12.84 | 12.73 |
| Direct Prepare | 0.18 | 0.17 |
| Direct Native Room/SG | 5.21 | 5.75 |
| Direct Bundle | 0.42 | 0.41 |
| Visual Roster | 1.91 | 2.56 |
| Snapshots | 100.29 | 103.76 |
| Color | 83.63 | **not executed** |
| Native Color Only | 8.25 | **not executed** |
| F27 | 194.47 | **78.76** |
| **Total episode** | **416.29** | **213.06** |

**Complete Worker speedup 1.9539x**; 203.23 seconds saved in this one paired run, F27 speedup 2.4691x. This is one paired episode measurement, not a statistically representative 9,126-Episode throughput estimate.

P1 FULL=10 states, ARROW_ONLY=26, REUSE_ALL=0. New compact v2 has 66 materialized PNG and 78 direct one-hop references (old v1: 144 materialized PNG). Approximate directory sizes using du -sh: old 26 MiB, new 12 MiB.

Strict source-dataset comparison: **36/36 independent Scene Graph JSON objects content-identical**, 144/144 views resolvable, 90 PNG byte-exact and 54 PNG with 1,245 differing RGB pixels total, maximum one image 57/198,534 (0.0287%). User H1 previously accepted these subpixel/edge changes as visually indistinguishable under the explicit <1 mm / <1 degree policy; these images are not claimed bit-exact.

Source fingerprint: fd5964e567868b7f787851fe55f4383e2e6c7a7b8aa1f44a568b9ca753802258.

Server evidence:
- optimized log: /tmp/g2_p012_fullworker_20261113_second/episode_003029.log
- original log: /tmp/g2_p012_matched_baseline_20261113/episode_003029.log
- complete dataset A/B: /tmp/g2_p012_material_direct_20261113/results/opendrawer_003029_fullworker_v1_v2_paired.json

## 2. Second distinct full original-source Worker completed

CloseFridge episode_000569 / Layout 7 (earlier PASS): optimized 256.86 seconds vs 511.41-second historical old run; the historical ~1.99x comparison is not same-load paired. Complete source-bound Room/SG and 17 spatial states, 17/17 Scene Graphs byte-content identical, all 136 view links valid. Original Color and native_color_only stages were absent in the optimized Worker (not merely bypassed inside F27). User separately passed H1 after inspecting the largest 468-pixel side-view difference.

## 3. Real v1/v2 mixed Resume

An isolated temporary dataset copy combined a published v1 CloseFridge Episode 569 and a pinned v2 NavigateKitchen Episode 2022. OpenDrawer Episode 3029 was absent to simulate pending work.

- Plan completion checker accepted v1 with either capability setting, and v2 only when explicit v2 capability was enabled.
- Actual manual Worker CLI returned G2_EPISODE_REUSE for both completed v1 and v2; did not create the configured work directory.
- Disabling v2 capability refused the completed v2 output, instead of silently accepting it.
- Forged source fingerprint refused; a direct image ref pointing to a current/future state was refused EVEN after rewriting the COMPLETE.json manifest SHA to match the corrupted manifest. Original bytes restored and revalidated.
- The derived pending queue contained only missing Episode 3029.

## 4. Exact original 9,126 plan, read-only resume preflight

The candidate executed action **plan**, never run or work, with its explicit scene-event-index, sim-direct-material, sim-color-only, sim-direct-geometry-only, lazy-texel-decode and resume flags, using the original immutable plan and original production output paths.

**PASS: 9,126 source Episodes / 202 already complete v1 / 8,924 pending / 18 tasks / 10 layouts / 92 immutable batches**, production_started=False. No original plan rewrite, no production Worker launch.

Log: /tmp/g2_p012_9126_resume_dryrun_20261113.log

## 5. Full regression and H1

**916 Python tests passed, 0 skipped** when real NavigateKitchen MJCF was provided explicitly, including all source texture parity tests. **Four Viewer Node smoke tests passed**: Island directions, no flicker, local folder browsing, indexed v2 image source resolution. Prior 19/19 F27 Lazy Texture GPU output equivalence PASS.

User H1 accepted NavigateKitchen, OpenDrawer, and the largest CloseFridge 468-pixel difference: visibly indistinguishable. Numeric differences remain in the A/B records.

## 6. Remaining promotion boundary

The opt-in experimental branch is review-ready but has **not** been merged to formal V3. The original nav_sg ROS1 native RGB-D pathway remains unchanged. Original production still has 202 successful v1 Episodes; full queue remains stopped.

**Unmeasured:** user-requested 8 Workers per production GPU, up to 32 concurrent workers across GPUs 4–7. The 1.9539x single-Worker measured speedup should not be extrapolated directly to 32-way throughput; run a bounded concurrency smoke before full restart. No 9,126-job production run was started.

**Work-root isolation:** after approval and eventual promotion, keep the immutable original plan/output roots to reuse 202 completed v1 Episodes, but use a NEW temporary work root to avoid colliding with partially completed v1 F27 stage receipts from the earlier interrupted run. Do not overwrite or delete v1 work/evidence automatically.
