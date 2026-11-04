# G2 Stage-1 — independent server Gate B: PHYSICAL_REPLAY_NOT_ACCEPTED

Date: 2026-11-04. Formal Root `b67bc4ca9a2afb1ff26fac0846f8ee7042a589ab`, Child/Gitlink `1069fe78841228cadbbfbe6afbd767eaed6225da`. This is **subsequent hardware/environment evidence**, not a replacement of the earlier `APPROVE_CODE` for the static code Gate. Formal candidate remains isolated; V3 not changed.

## Verdict / scope

**Gate B FAIL / PHYSICAL_REPLAY_NOT_ACCEPTED** (native verifier exit 1). Do not run Gate C, any N=100/full export, merge V3, or change acceptance thresholds. Do not interpret cache integrity PASS, prior user visual inspection, or author CPU83 as physical acceptance. Exact code was tested on the DS server by GPT using Remote Desktop Commander, but separate from the stalled DS agent, in an isolated clean sparse checkout. No GPU was used; no raw RGB/Depth/video/NPZ data or reversible encoding left the server.

## Isolated execution provenance

- CODE_ROOT `/tmp/psm_g2_gateb_gpt_20261104_0520`; exact Root and Gitlink verified; git status clean.
- Simulator: `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/robocasa_sim_venv_20261023/bin/python`; robocasa 1.0.1, robosuite 1.5.2, MuJoCo 3.3.1, numpy 2.2.5, PyArrow 21.0.0.
- `CUDA_VISIBLE_DEVICES=''`, `MUJOCO_GL=osmesa`, `PYOPENGL_PLATFORM=osmesa`, `LIBGL_ALWAYS_SOFTWARE=1`. Local OSMesa library is loaded via **process-scoped** `LD_LIBRARY_PATH` and symlink in temporary evidence dir, and pre-existing warmed Numba cache was **copied** into a private evidence cache. No global Git/environment config, native production source, shared training worktrees, or live jobs changed.
- Original OSMesa attempt lacked library search path and failed `AttributeError: 'NoneType' object has no attribute 'glGetError'`; this is an environment setup issue, superseded by successful local-library GLContext creation and successful export in a **fresh output namespace**.

## Observed test results

- Dry-run PASS, one `CloseFridge` local episode0 mapped to **global episode502**, frames 0/214/428 (20Hz), two cameras left+eye_in_hand; raw/Flat nonvisual mapping and state verification PASS.
- Export CLI **exit0**, episode status `EXPORTED`, 3 frames, two cameras, `uint16_mm` max quantization error `0.0004999984054417927m`; compressed NPZ camera payload **168732 bytes**.
- Physical verifier: `CACHE_INTEGRITY=PASS`; `runtime_matches_export=True`; `evidence_kind=SERVER_NATIVE_REPLAY`; final **`PHYSICAL_REPLAY_NOT_ACCEPTED`**, `geometry_gate=FAIL_OR_INCONCLUSIVE`, exit **1**.

| Frame | Camera | RGB MAE (limit <=5) | mj_ray max optical-Z error m (limit <=0.01) | Matching rays |
| --- | --- | ---: | ---: | ---: |
| 0 | left | 7.0520 | 0.660259 | 127 |
| 0 | eye_in_hand | 2.2656 | 0.022212 | 124 |
| 214 | left | 7.4288 | 0.658640 | 128 |
| 214 | eye_in_hand | 12.9463 | 0.264398 | 124 |
| 428 | left | 8.8456 | 0.163367 | 123 |
| 428 | eye_in_hand | 9.9256 | 0.000815 (**PASS**) | 125 |

All 6 have >=16 matched-ray samples; 5/6 fail the independent geometry max threshold and 5/6 fail RGB MAE threshold. Simulator time minus Flat timestamp = +0.50s at t0 and approximately +0.55s at t214/t428; no state-index correction was applied.

- Actual local report/evidence: `/tmp/g2_gpt_gateb_20261104_0525/physical_report_osmesa.json` and `physical_stdout_osmesa.log`. Cache: `/mnt/data1/data_v2_0617/g2_rgbd_pose/gpt_gate_b_osmesa_20261104_0535/tasks/CloseFridge/episodes/episode_000502`. These **server-only** files must remain on server, and must not be uploaded or converted to a transferable format.

## Additional read-only diagnosis after failure (not a new Gate B trial)

- Compared existing DS G3 arrays in `/tmp/g3_out` locally to newly committed RGB-D/Pose cache, using **only aggregate statistics**. Across six camera/frame pairs, mean absolute Depth difference is ~0.00025m; 95th percentile ~0.000475m. Most max deviations are below 0.001m; only eye_in_hand frames214/428 have isolated outlier pixels >1cm, with >1cm proportions ~1.5e-5 and ~3.1e-5 respectively. K max element differences <=4e-6, GL pose max element differences <=2e-7. This strongly supports that the new **Depth/K/Pose payload agrees with the earlier successful visual G3 probe**. It does NOT substitute for independent geometry validation.
- Compared imageio original RGB decoding with previous OpenCV-decoded source frame for each of six combinations: **MAE=0.0** at exact frame indices. Therefore the unexpected real verifier RGB MAE is not explained by different original-video decoder/frame seeking.
- The older G3 temporary script and new implementation both load original XML and state, but differ in renderer construction options (e.g. new `camera_depths`, explicit camera names/sizes, use of metadata controller configs) and in the new ray-test semantics; the root cause of RGB/geometry FAIL has **not** yet been demonstrated. Original metadata `translucent_robot=False` in both, so do not assert it is the cause.

## Minimum follow-up requested of Codex

1. Keep all observed failed evidence/thresholds frozen; do not overwrite existing server cache/report or weaken numerical thresholds.
2. Compare `tools/g2/rgbd_pose/replay.py:66–146` (renderer environment / RGB), `148–223` (segmentation/ray visibility, ray-vs-Z agreement) against the successful old `/tmp/g3_full.py` and official robosuite APIs. Distinguish **RGB photometric mismatch**, **depth numerical mismatch**, and **ray checker validation artifact**; do not conflate.
3. Add focused regression(s) and smallest justified correction only when supported by reproducible evidence; create **new Formal Root** for code changes, author CPU Gate, and fresh GPT review. Server scripts/data remain on server; only text summaries may be shared.
4. Gate B re-execution requires fresh explicitly accepted candidate and new output/report namespace; no Gate C/N100 until a real `PHYSICAL_REPLAY_PASS` against unchanged numeric standards.

No source fixes or reruns were made by GPT. Root remains b67bc4ca; the GitHub commit carrying this report is **docs-only bookkeeping**, not a new Formal Root.
