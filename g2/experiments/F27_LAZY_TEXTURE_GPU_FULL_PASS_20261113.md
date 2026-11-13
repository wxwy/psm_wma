# P0 Lazy Texture — real GPU 19/19 full-episode A/B (2026-11-13)

**Status: FULL GPU VIEW PARITY PASS for one RoboCasa Layout 7 Episode.**
**NOT merged to formal V3. Default implementation remains the old eager texture path.**

Source: accepted NavigateKitchen Episode 002022, 19 GT sampling states, F27 GPU EGL on device 7; compiled MuJoCo material mapping unchanged.

Previous attempt under a concurrently running 32-worker production job yielded only 15/19 states before the low-priority 1,100-second cap. After production was stopped, the same separate opt-in candidate successfully regenerated **all 19 states** into a fresh temp directory, with a complete F27 episode_receipt.json.

Comparison through the independently written, read-only real GPU Gate (f27_gpu_view_ab_gate.py), which requires a complete candidate episode receipt:
- 19/19 state receipts and 56 file entries per state.
- 589 raw/unmarked PNG files: exact file SHA256.
- 19 final floor_top.png markers: exact SHA256 after normalizing the original older-appearance baseline from the original raw background and original stored chassis pose using the current game_arrow recipe.
- 3,648 depth/Geom/Face/material/RGB/Alpha/unknown/coverage numeric arrays in 152 NPZ files: elementwise exact, including NaN locations.
- 38 Scene Graph / Surface Registry files: SHA256 exact.
- Semantic view and evidence metadata: exact after removing diagnostic elapsed times and disregarding serialized view-list order.
- **TOTAL MISMATCHES 0. REAL_GPU_A_B_FULL_PASS 19 OF 19 STATES.**

Candidate whole F27 render wall 233.57 seconds, accepted older baseline 259.87 seconds. These are NOT two reruns under controlled identical machine contention and priority, so the 10% difference is not a certified performance improvement.

Earlier full MaterialResolver and small-View gates: 879/879 Python tests PASS; a real texture 2048 squared cache reduced from 96 MiB eager float64 to 12 MiB original source bytes (87.5% less per texture); numeric/alpha/evidence output bit-exact.

Next gate: repeat whole-Episode A/B on a different complex layout, and benchmark matched hardware and contention for accurate throughput before any production promotion. No original nav_sg/native RGB-D changes.

This report is an experimental candidate's evidence only. No changes were made to ongoing (now stopped) 9,126-item output.
