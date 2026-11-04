# G2 Stage-1 Gate B — independent real-server diagnostic r2

Date: 2026-11-04. **Formal Root** `a9ffd313770c5344195f415425124a5075e62b2b`; **Formal Child/Gitlink** `1069fe78841228cadbbfbe6afbd767eaed6225da`. Code Gate `APPROVE_CODE` for this pair is separate. **Gate B final verdict: `PHYSICAL_REPLAY_NOT_ACCEPTED` (verifier exit 1)** due to original RGB MAE, even though **all six independent geometry checks PASS**. This report is a docs-only successor, not a new implementation Formal Root.

## Isolation and source identity

- New clean independent sparse checkout `/tmp/psm_g2_gateb_gpt_r2_20261104_0628` (exact SHA and Gitlink verified; active V3/worktrees untouched).
- RoboCasa365 target-atomic CloseFridge local episode0 → Flat global episode **502**; frames 0/214/428; fixed left + wrist cameras.
- Simulator: `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/robocasa_sim_venv_20261023/bin/python`, native robocasa 1.0.1, robosuite 1.5.2, MuJoCo 3.3.1. OSMesa software rendering using process-scoped local libOSMesa, private copy of existing Numba cache, `CUDA_VISIBLE_DEVICES=''`. No GPU/EGL fallback or global configuration edits.
- Dry-run: PASS, one episode, three selected frames, raw/Flat nonvisual identity valid.
- Export: exit0, `EXPORTED`, three frames, two cameras; `uint16_mm` max quantization abs `0.0004999984054417927m`, compressed camera payload `168732 bytes`. New cache path: `/mnt/data1/data_v2_0617/g2_rgbd_pose/gpt_gate_b_r2_20261104_0630/tasks/CloseFridge/episodes/episode_000502`.
- Verification: native `SERVER_NATIVE_REPLAY`, `CACHE_INTEGRITY=PASS`, `runtime_matches_export=True`, `GEOMETRY_GATE=FAIL_OR_INCONCLUSIVE` because overall `passed` also includes failing RGB condition. Independent **per-camera** `mj_ray` geom checks all **PASS**. Actual physical verification exit code **1** and `PHYSICAL_REPLAY_NOT_ACCEPTED`. Report on server: `/tmp/g2_gpt_gateb_r2_20261104_0630/physical_report_r2.json`.

## Six real image checks

| Frame | Camera | RGB MAE (limit <=5) | Matched rays (minimum16) | Max optical-Z ray error m (limit <=0.01) | Ray status |
| ---: | --- | ---: | ---: | ---: | --- |
| 0 | left | 7.0520 | 128 | 0.003577 | PASS |
| 0 | eye_in_hand | 2.2656 | 128 | 0.002993 | PASS |
| 214 | left | 7.4288 | 128 | 0.003766 | PASS |
| 214 | eye_in_hand | 12.9463 | 128 | 0.002641 | PASS |
| 428 | left | 8.8456 | 128 | 0.004423 | PASS |
| 428 | eye_in_hand | 9.9256 | 128 | 0.000880 | PASS |

All six have robust opaque-eligible pixels: **37549, 52304, 40034, 53835, 43576, 61932**, respectively, on 256×256 cameras. Front-face mesh-corrected samples: **99, 92, 97, 128, 95, 128**. Both `rgb_vs_rgbd` and `segmentation_before_after` equal RGB MAE0 for all six, showing no render-mode difference or segmentation context pollution within the current renderer. Cached/fresh poses and runtime match. Time minus Flat video timestamp remains roughly +0.50s/+0.55s; no state-index shift performed.

## Targeted RGB root-cause isolation (independent read-only probe)

Previous DS G3 arrays reside on the server at `/tmp/g3_out`, from earlier replay of the same episode; those had original-video MAE left **1.7465, 1.9548, 2.0694**, wrist **1.5821, 1.2515, 1.0452** at these three frames.

With **the current OSMesa process**:
- Rendering via new `Replay(source)` and via the **old DS G3 constructor kwargs** (remove `controller_configs`, no explicit camera depth/name/size kwargs, otherwise same original XML and states) produces **identical RGB** at every evaluated frame. New/old-kwargs original-video MAE are exactly **7.052/7.429/8.846** left and **2.266/12.946/9.926** wrist.
- Compared to the previously saved G3 rendered RGB arrays, new/current OSMesa RGB MAE is approx left **5.796, 5.994, 7.286**, wrist **1.011, 11.996, 9.303**. Channel-average RGB values are systematically higher in current OSMesa, often by ~5–12 levels (not consistent with a state-frame shift). Current environment kwargs difference therefore **does not explain** the RGB difference. The earlier G3 rendering backend, GL provider/driver and exact photometric runtime provenance remain **unverified**; do not declare EGL as confirmed cause without evidence.
- Earlier server-only Depth/K/Pose comparison remains strong: mean Depth diff ~0.00025m; camera K/GL pose max differences ~4e-6/~2e-7; this is not a full-map independent ray guarantee but supports identical geometry.

## Conclusion and smallest next action

1. The new visibility/mesh-ray checker has now cleared the **six real RoboCasa geometry checks** without changing tolerance; code fix is empirically useful.
2. **Gate B is still FAIL** because original RGB MAE exceeds 5 in five of six checks. Do not downgrade original-video RGB gate, claim `PHYSICAL_REPLAY_PASS`, merge V3, run Gate C or N=100.
3. Next, **without modifying production** first, prove the previous G3 process's rendering backend and photometric configuration using locally retained original logs/valid environment provenance, then compare current OpenGL vendor/renderer/version and material/light state scalar fingerprints. Where that is not reconstructible, run a **single narrowly scoped** controlled rendering experiment in an explicitly reviewed environment, preserving both existing RGB and geometry metrics and not touching active GPU jobs. Changing the threshold, implementing arbitrary brightness correction, or changing simulator state index on the strength of time offsets is prohibited.
4. After the actual photometric cause is established, Codex should propose the minimum justified code or environment correction, with a fresh exact Pair if production code changes. Keep this Gate B report and prior failed reports immutable.

No server RGB, Depth, video, image, NPZ/NPY, scripts or reversible payload was transmitted outside the server. GitHub contains aggregate text numbers and server-local paths only. Code, training assets, old caches and V3 baseline remain unchanged.
