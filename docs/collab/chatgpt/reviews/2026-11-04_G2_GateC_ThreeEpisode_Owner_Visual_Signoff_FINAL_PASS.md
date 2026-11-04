# G2 Gate C — three full episodes: Owner Visual Acceptance and FINAL PASS

**Date:** 2026-11-04 (China project working date).  
**Final verdict:** **GATE_C_PASS — exact three-episode, sampled-native-geometry + explicit external visual acceptance**. This is a **separate immutable sign-off record**, not a modification of any previous `VISUAL_PENDING` or old-contract report.

## Authorities, provenance and scope

- Formal production Root **3eb8b334150018212ae1f51afb5e954b83fa1186**; Child/Gitlink **1069fe78841228cadbbfbe6afbd767eaed6225da** (unchanged, isolated candidate).
- S0 frozen selection/budget: `docs/collab/chatgpt/reviews/2026-11-04_G2_GateC_S0_Exact_Selection_Budget_Readonly_Freeze_PASS.md` (commit `cd143c4bf6322a39cb7855772a944d45a49ffcf8`).
- Gate C execution contract: `docs/collab/codex/requests/2026-11-04_G2_GateC_S1_S3_Exact_ThreeEpisode_Execution_Contract.md`, remote reviewed durable-chunk correction commit `59beb9fe5b3e893d6b86254f00524672638bd49f`, authorization `d3374c0e35c6d8bfc308b45c399b48cd3870f0f3`.
- Independent, completed machine-side Gate C evidence: `docs/collab/chatgpt/reviews/2026-11-04_G2_GateC_S1_S3_ThreeEpisode_Automated_PASS_Visual_PENDING.md` (commit **5f647bb7c8b65f232a12c25b421c8c6cc9ef9de6**).
- **Owner first-person visual confirmation in the current PSM-WMA project conversation** (2026-11-04): **“三条 的 Depth 边缘均贴合原始 RGB 的物体轮廓、相对位置和机械臂遮挡关系”**. This is an **explicit human observation**, not an automated tool claim or a fabricated `verified_by_tool=true`. It applies only to the three review sheets and their sampled frames/cameras listed below.
- Original official RoboCasa365 target-atomic **RGB remains the source**; newly rendered RGB was a nonblocking *photometric diagnostic*, not a replacement for original RGB and not a color-corrected output.

## Frozen, individually bound visual sign-offs

Each server-local PNG displays **original RGB / newly cached depth pseudocolor / red Depth discontinuity contours over original RGB** at the full-episode first, middle and last selected frames for both native 256×256 cameras (`robot0_agentview_left`, `robot0_eye_in_hand`). All paths below remain on the authorized DS server; no raw media was uploaded to GitHub or transferred to ChatGPT.

| Task | Local / global ID | Full episode frames | Visually reviewed sample frames | Preview SHA256 | Native sampled report SHA256 | Cache export digest |
|---|---|---:|---|---|---|---|
| CloseFridge | 0 / 502 | 429 | 0,214,428 × 2 cameras | `0914468dddb5a352b318f7171a87533c29e145985c8d5447186f7d97da6d5934` | `b6c581093a571f70999b049a27b55149aeb1cc92fec84ca0db44f4389c264a49` | `5c553ef09e3c918d296c66f51412f6257f85d5458b197c6a062bc4bb366834de` |
| NavigateKitchen | 0 / 2022 | 177 | 0,88,176 × 2 cameras | `e1ad87c705b96e82a87e1490017e8c278fa6ce72ae578651a1b62c91efdf34cc` | `ef553dca83f3ff22c6b262ca8f73b25af9c7b3a6d853fc9252cbb3d865179a26` | `b8bf83d941b344b3da6d3c1ae345e71f241f11c3888929a625736f61737856ee` |
| PickPlaceCounterToCabinet | 0 / 4038 | 246 | 0,123,245 × 2 cameras | `501f46188944b78e0b3a2ab08bee83484727a71c25ebcb4e75528727113fec2e` | `2375f5827a00803eff587a3df004dcde9b7603d95c6603211dfcad9e9aaad185` | `19f6e6f21c120216749bd1d10515e10497a436f749b239140713c28f61dcb655` |

All preview-image and native-report SHA256 values above were independently verified against the original server-local `visual/review_pending.json`; all three pairs matched at sign-off.

Server preview paths:
- `/tmp/g2_gate_c_s1_s3_3eb8_20261104/visual/RGB_Depth_Contours_CloseFridge_000502.png`
- `/tmp/g2_gate_c_s1_s3_3eb8_20261104/visual/RGB_Depth_Contours_NavigateKitchen_002022.png`
- `/tmp/g2_gate_c_s1_s3_3eb8_20261104/visual/RGB_Depth_Contours_PickPlaceCounterToCabinet_004038.png`

## Why Gate C can now close

| Gate requirement | Evidence | Verdict |
|---|---|---|
| Source/mapping membership frozen | 3 real underlying classes; mapping SHA256 `aa884820494a17f50b41a8a8c2bfa6b6fda11babbbef31c449c1c0ce850e09ed`; selection SHA256 `10d668ee42b5145a8cad09878c331ef940b06d91a6a9666ae85434b61c225926` | PASS |
| Three **complete** episode exports | 429 + 177 + 246 = **852** source frames / **1,704** camera frames, original RGB + uint16-mm Depth/K/Pose; full source/cache integrity and hashes | PASS |
| Real native spatial checks | First/middle/last sampled frames, two cameras each: **18/18 PASS**, **128 rays/group**, max optical-Z error **0.004660357 m** (≤ 0.01m criterion) | PASS |
| Explicit human RGB–Depth alignment | Owner specifically confirms alignment of edge contours, relative object positions and robotic arm occlusion relationships for all three task sheets | **PASS (external Owner observation)** |
| Planned interruption recovery | One owned NavigateKitchen SIGTERM after two fsynced first 32-frame NPZ chunks; exit -15 and one complete restart from frame0, unique full commit | PASS |
| Verified cache reuse and budgets | **3/3 SKIPPED_VERIFIED** with original payload hashes unchanged; 329.99s total machine work, no GPU, CPU OSMesa, memory/disk under budget | PASS |
| Re-rendered RGB photometric diagnostic | **6/18 MAE>5** retained as nonblocking diagnostic under `g2_stage1_spatial_v2` | RECORDED (not a blocking failure) |

**Closure result:** **G2 Stage-1 Gate C is now PASS for the exact three representative complete episodes**. The earlier machine report remains literally `AUTOMATED_S1_S3_PASS_VISUAL_PENDING` as its historically correct snapshot; this later independent human sign-off completes the acceptance chain. Likewise the original pre-v2 photometric-hard Gate B failure report is preserved as a historical verdict, not overwritten.

## Data, limits, next gate

- Native compressed sensor payload: **46,507,310 bytes** (~46.5 MB, 7.2099× raw-array compression), with complete committed output at `/mnt/data1/data_v2_0617/g2_rgbd_pose/gpt_gate_c_candidate_s0_20261104`.
- Original cache and immutable evidence are retained; uncommitted staging from the deliberate SIGTERM is preserved separately as recovery evidence. The exact runner, snapshots, aggregate geometry checks, logs and preview images remain server-only in `/tmp/g2_gate_c_s1_s3_3eb8_20261104`.
- Gate C is a **representative, bounded 3-task test**; it does not prove every pixel/frame in every RoboCasa episode or validate full N100 membership. Physical ray checks were sampled, not all-frame.
- **Not authorized by this final Gate C report:** new 100-episode-per-task export, V3 merge, nav_sg/Scene Graph data conversion, GPU/EGL training, training checkpoint changes, unattended monitoring. The next action is a separately bounded N100 **exact selection/membership and production resource plan**, followed by its own execution approval.
- Do not use `owner_visual_review` in any old machine report as evidence of automated human PASS. This sign-off is the separate external acceptance record, with named task/scope and exact image/report evidence bindings.

**Final sign-off provenance:** User explicitly confirmed the three representative visual checks in this current conversation, and GPT recorded the confirmation after independently checking that all three server-local preview PNG and associated native report hashes still matched the frozen per-scene machine evidence.