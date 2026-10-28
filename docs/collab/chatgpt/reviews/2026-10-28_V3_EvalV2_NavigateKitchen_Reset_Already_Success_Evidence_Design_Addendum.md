# Evaluation V2 evidence/design addendum — NavigateKitchen reset-already-success contamination

Date: 2026-10-28. Scope: **new user-supplied DS_PRO incident evidence + next Design Gate acceptance only**, NOT a fresh technical review, production patch, GPU simulation acceptance, or historical Episode correction.

## Exact repository context

- Current unchanged Evaluation V2 r1 design formal target: Root `dc750f8e258d10a33e7a195cf907926b1c98bd7f` / Child+Gitlink `746c5cf2f2324104a62fb71510343aa40d3976c5`. Formal Design Gate status remains `REQUEST_CHANGES`; root/child pair **has not changed**.
- Current Child `cosmos_framework/simulation/robocasa/closed_loop_eval.py:303-305`: `env.reset()` then Local session `begin`; `:396-421` executes an actual `env.step` and only then calls `check_success(env)`; `:216-220` suppresses any `_check_success` Exception by returning False (already a separately documented problem).
- Author/DS evidence refers to actual RoboCasa vendor runtime `robocasa_sim_venv_20261023`, dataset run `g1_iter12000_4task5ep_genall_20261023_085955`, invocation `1793097086121956697_2544066_8cc97e20`, batch `batch_f870aa005fba4dc291b6589536a63862`. Reviewer did NOT execute /tmp probe, read its log, or inspect the remote saved Episode.
- Public official RoboCasa `robocasa/environments/kitchen/atomic/kitchen_navigate.py` was read separately: `_setup_kitchen_references` rejects source/target fixtures with `fixture_pairwise_dist <=1.0`, sets `target_pos,target_ori = compute_robot_base_placement_pose(target_fixture)`, and `_check_success()` tests base-to-target XY <=0.20m plus orientation cosine >=0.98. Source URL: https://github.com/robocasa/robocasa/blob/main/robocasa/environments/kitchen/atomic/kitchen_navigate.py . This public latest source corroborates the **mechanism**, but is NOT proof that the installed vendored build is byte-identical.

## Submitted real-runtime evidence and separate inference

DS_PRO **reports** physical reproduction: `seed=695376856`, sampled `layout/style=2/2`, Drawer→Microwave, after `env.reset()` initial base `[0.722,-1.1183,0]`, target `[0.85,-1.08,0]`, distance `0.1336m`, heading `cos=1.0000`, initial `_check_success()==True`. A single zero-motion action leaves success true and reward1, `env_done=false`, matching observed Episode success `steps=1`/`replans=1`. Six reported control seeds (0,1,2,3,12345,777777) did not show initial success. Neither those six controls nor this one failure establishes its dataset-wide prevalence.

**Interpretation**: Strong evidence of a **degenerate/pre-solved initial scene**, so this Episode has no evidence of navigation skill. The evaluation harness faithfully follows the environment's post-step success signal; that by itself is not a simulator crash or an incorrect implementation of its success predicate. However V2's *scene-admission protocol* currently lacks a reset-time already-success guard. The wording “every possible policy necessarily succeeds” is too strong (a policy could move away before the first check); accurately, **a zero-motion action can succeed**.

## D4 — HIGH: Initial-success scene admission required in Eval V2 before real policy control

### Frozen recommended contract

- **At the boundary immediately after `env.reset()` and before first model query/action, before Local-TTT session `begin` if feasible**, call a **strict** environment success predicate for scene validity. This is not the policy success observation and must not use reward, `env_done`, predicted trajectory or completion latency.
- If initial success is **False**: scene is admissible; continue the normal Episode, with post-action `env._check_success()` as sole scientific task-success authority.
- If initial success is **True**: emit `DEGENERATE_INITIAL_SUCCESS` as a *rejected candidate scene*, not `success`, `behavioral_failure` or a permanently completed Episode. It does **not** advance logical Episode Index, does **not** send policy actions or update Local-TTT, and must not consume one of the 50 valid Episode slots. Record Task, logical index, reset attempt number, seed/stream, actual prompt, layout/style and optional fixture/pose diagnostics when available; retain diagnostic evidence. Resample a fresh legitimate scene, as latest Owner has explicitly said **exact original scene reproduction is unnecessary**.
- Predicate exception/nonboolean => scene/preflight error, **not** False. Avoid silent retrying actual model errors as degenerate scenes.
- **Bound** maximum scene-admission attempts per logical Episode, freeze threshold/limit in manifest. Upon exhaustion: `SCENE_ADMISSION_EXHAUSTED` as an explicit Invalid/blocked Episode, never silently mark success/failure; no infinite retries.
- **After admissibility**, no further “easy scene” filtering and no minimum-distance threshold unless a separate explicitly approved scientific-protocol change. A genuine post-action first-step success from an initially unsatisfied scene is valid. A post-action `behavioral_failure` is valid and must NOT be resampled.
- Never modify vendored RoboCasa source for this Gate or suppress the environment's native post-action success authority.
- Record the complete scene-admission/rejection distribution for all Tasks, and distinguish `accepted_episode_count` from `rejected_initial_success_scene_count`. This **changes effective scene sampling** and must be versioned and declared in fresh900 manifests and reports; cannot claim numerical equivalence with older unfiltered RoboCasa SR or automatically rewrite any old431 results. For comparisons across policies, apply identical admission/filter protocol.
- Keep previous Owner Episode-level Resume decision: valid preceding Episodes immutable; interrupted logical Episode restarts on newly sampled scene, no exact RNG replay. Accepted precheck must be executed for each fresh candidate.
- Media/ffmpeg remains diagnostic only under C, unrelated to this issue.

### Gate acceptance

1. **CPU injected scene tests**: `reset_check True → rejected/retry → reset_check False → accepted`; zero model calls/actions/Local-TTT mutations for rejected candidate; no logical index increment until valid Episode; after accepted, success/failure via post-step env predicate. Exception or invalid type fail closed.
2. **Resume tests**: ep0–36 valid prefix byte-identical; ep37 rejected initial-success once then newly sampled/processed; ep38–49 continue; exact50 unique valid results. A legitimately failed Episode must not be retried; a media error must not change result.
3. **Bound/error tests**: repeated initial-success up to attempt limit yields explicit blocked/Invalid, no endless loops or post-Invalid Episode; retry/stream metadata and counters correct across restart. Rejected scene cannot be confused with committed invalid execution. Atomicity required for scene-attempt records.
4. **Native Canary separate GPU authorization**: examine real RoboCasa `NavigateKitchen` using the provided seed and control seeds, compare the strict precheck with the vendor's original `_check_success` as read-only, establish calling it on reset does not mutate RNG/physics or interfere with Local-TTT; verify new scene resampling covers the intended valid Task target and doesn't touch upstream training/Checkpoint/vendor. The supplied DS probe is a reported witness, **not** GPT executed Canary.

### Interaction with prior design blockers

- D1 process faults scoped/resolved, D2 initial transaction crash safety, D3 Episode-only Resume/new scenes allowed **remain open** on unchanged r1 design pair. D4 scene admission adds a new review acceptance point for the NEXT formal design pair; no fresh r1 verdict is issued.
- In particular, do NOT re-impose the now-superseded “Episode37 must recreate same scene or require SHA256 per-Episode deterministic seed” condition.

Status: **OWNER INCIDENT EVIDENCE REPORTED / SOURCE MECHANISM CORROBORATED / D4 DESIGN ACCEPTANCE PROPOSED / NOT CODE REVIEW / NO GPU AUTHORIZATION**.
