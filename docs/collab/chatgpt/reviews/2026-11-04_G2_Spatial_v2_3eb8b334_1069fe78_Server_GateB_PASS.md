# GPT independent server validation — G2 spatial-v2 Gate B PASS

Date: 2026-11-04 (Asia/Shanghai). Formal source pair **Root `3eb8b334150018212ae1f51afb5e954b83fa1186` / Child+Gitlink `1069fe78841228cadbbfbe6afbd767eaed6225da`**. **Verdict for the limited previously Owner-reviewed six-frame episode: `SPATIAL_REPLAY_CHECKS_PASS`, native verifier exit code 0.** No claim that Gate C or N=100 is accepted. This is new independent physical evidence under `acceptance_policy=g2_stage1_spatial_v2`, not a rewrite of the earlier `PHYSICAL_REPLAY_NOT_ACCEPTED` old-contract report.

## Provenance and isolation

- Code Gate prior review: `docs/collab/chatgpt/reviews/2026-11-04_G2_Spatial_v2_3eb8b334_1069fe78_Incremental_Code_Gate_APPROVE_CODE.md`, docs-only commit `544b656b5b8fd2f2a0219b90f90207442daf4ef0`.
- Independent isolated read-only server checkout `/tmp/g2_spatial_v2_gpt_3eb8_20261104`; exact Root and Gitlink verified; `git status --porcelain` **0 lines** after test.
- Simulator: `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/robocasa_sim_venv_20261023/bin/python` with previously verified native RoboCasa/robosuite/MuJoCo versions, CPU software OSMesa, process-scoped locally available `libOSMesa`, private copied Numba prewarm cache, `CUDA_VISIBLE_DEVICES=''`. No GPU or EGL path.
- Read-only source, prior complete cached 3-frame episode (2 cameras): `/mnt/data1/data_v2_0617/g2_rgbd_pose/gpt_gate_b_r2_20261104_0630/tasks/CloseFridge/episodes/episode_000502`. Underlying RoboCasa365 target-atomic CloseFridge original local episode0 → Flat global episode502, indices0,214,428.
- **Only a new independent report and stdout** were written to `/tmp/g2_spatial_v2_gpt_20261104_evidence/spatial_v2_report.json` and `verify_stdout.log`. Report size **42134 bytes**. Previous report `/tmp/g2_gpt_gateb_r2_20261104_0630/physical_report_r2.json` remains present (size40777 bytes, prior modification date unchanged). Cache files have no modification in this last 30min audit. Original RGB, Depth, XML, videos, arrays, logs and images were not copied out of the server.

## Native result from original unchanged sources

The executable was invoked as `python -m tools.g2.verify_robocasa_rgbd_pose` under the exact formal checkout, `--replay --frames 0,214,428`, existing cache/roots, `--state-index-policy frame_index`, frozen `--geometry-atol-m 0.01 --min-ray-samples 16 --rgb-mae-max 5`, and `--owner-visual-review-ref` referring to the Owner's exact f634 review.

```text
VERIFIER_EXIT=0
status = SPATIAL_REPLAY_CHECKS_PASS
acceptance_policy = g2_stage1_spatial_v2
spatial_alignment_gate = PASS
spatial_alignment_scope = AUTOMATED_CHECKS_ONLY_VISUAL_REVIEW_EXTERNAL
geometry_gate = PASS
cache_integrity = PASS
runtime_matches_export = True
evidence_kind = SERVER_NATIVE_REPLAY
photometric_diagnostic = {"status":"FAIL","blocking":false,"mae_max":5.0,
                          "checked_camera_frames":6,"failed_camera_frames":5}
owner_visual_review = {"status":"EXTERNAL_RECORD_REFERENCED",
                       "verified_by_tool":false,"provenance_reference": "<f634 Owner review>"}
```

| Frame | Camera | Spatial | Ray count | Max ray optical-Z error (m) | RGB MAE, diagnostic only |
|---:|---|---|---:|---:|---:|
| 0 | robot0_agentview_left | PASS | 128 | 0.00357717455 | 7.0520 |
| 0 | robot0_eye_in_hand | PASS | 128 | 0.00299264513 | 2.2656 |
| 214 | robot0_agentview_left | PASS | 128 | 0.00376592402 | 7.4288 |
| 214 | robot0_eye_in_hand | PASS | 128 | 0.00264084473 | 12.9463 |
| 428 | robot0_agentview_left | PASS | 128 | 0.00442333850 | 8.8456 |
| 428 | robot0_eye_in_hand | PASS | 128 | 0.00088040627 | 9.9256 |

All 6 independent geometry checks PASS with the unchanged 1cm/16-rayer criteria. The photometric MAE5 condition still FAILs for 5/6, correctly recorded as nonblocking. Actual prior human visual conclusion is an **external Owner observation** limited to these six frames; the tool does not verify or automatically infer Owner PASS. Re-rendered RGB is not a training replacement; official original RGB remains the source.

## Gate status / next boundary

- **Code Gate** for `3eb8b334/1069fe78`: APPROVE_CODE (separate review).
- **Spatial-v2 Gate B for the existing CloseFridge six-frame sample:** **PASS** in native replay, plus separately recorded Owner RGB–Depth contour/occlusion visual acceptance. The legacy original photometric-hard report still accurately says `PHYSICAL_REPLAY_NOT_ACCEPTED` under prior acceptance rules.
- **Gate C:** PENDING, not executed/accepted. Proposed bounded 3–5 **full** episodes from **distinct** real task classes, verify actual mapping selection IDs and mapping SHA, disk/time budget, full cache integrity, first/middle/last independent geometry, separate human visual review of new RGB–Depth scenes, restart/idempotency and throughput/RSS/storage. Must be independently authorized with exact selected manifest and resource boundaries before batch export.
- **N=100, V3 merge, nav_sg/Global PSS, training, checkpoint/DCP and GPU operations:** NOT AUTHORIZED by this report. No production source or active training checkout changed.

This is a **docs-only evidentiary successor**. The native test used Formal Root `3eb8b334150018212ae1f51afb5e954b83fa1186`; any subsequent report commit does not replace it.
