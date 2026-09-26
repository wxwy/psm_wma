# PSM-WMA RoboCasa Base Physics Diagnostics

Date: 2026-09-25

Status: IMPLEMENTED / RUNTIME DIAGNOSTICS VALIDATED ON 18-TASK SMOKE

## Ownership

Production code, launchers, configs, and formal tests are owned by the GPT/ChatGPT build side.

ds_pro is validation-only. It may:

- run the evaluator;
- execute MuJoCo probes;
- compute statistics;
- generate artifacts and reports;
- keep temporary probe code under /tmp or evidence copies under artifacts/.

ds_pro must not modify or commit production source, launchers, configs, formal tests, or the root Gitlink.

If local ds_pro production-code changes are discovered, preserve its artifacts/reports and restore production files to the current GPT/ChatGPT formal root/child pair.

## Why diagnostics were added

The calibrated linear base decoder is a held-out empirical inverse, not a physics-exact inverse.

Live probes established that:

- bm0/bm1/bm2 slot and sign are correct in the ego frame;
- observed completed ego-dy contains real yaw/reference-point coupling;
- small side commands can fail to reverse observed motion because of friction and inertia;
- training labels contain the same observed coupling, so Local-TTT evidence must remain training-parity.

Therefore decontamination is evaluation-only and must never be fed back into the Local-TTT evidence stream.

## Production diagnostics

RoboCasa closed-loop action records now include a base_diagnostics object per executed step.

Recorded fields include:

- base decoder contract version;
- control mode / base-active flag;
- predicted ego dx/dy/dz;
- predicted relative yaw;
- decoded base_motion[0:4];
- completed ego dx/dy/dz;
- completed relative yaw;
- estimated yaw-coupled side displacement (0.21 * completed yaw);
- decontaminated_side_dy = completed_dy - 0.21 * completed_yaw;
- side-command dead-zone flag using |bm1| < 0.25;
- sign agreement for predicted dy and decoded bm1 against both raw completed dy and diagnostic decontaminated dy.

Episode summaries include:

- base-active / arm-active step counts;
- side-deadzone count and fraction;
- decoded bm0/bm1/bm2 distribution;
- sign-agreement summaries;
- count of arm-active steps with non-zero base commands;
- count of non-zero bm3 commands.

Task summaries aggregate the critical contract counters.

## Frozen invariants

The diagnostics must not modify:

- compose_left_wrist RGB pixels;
- state16;
- canonical action20;
- completed_action20 used by Local-TTT evidence;
- Local-TTT session/ack/reset semantics;
- calibrated decoder slot/sign.

RGB contract is explicitly labeled as training_matched_vertical_flip_v1. This describes train/eval parity; it is not a claim that pixels are world-upright.

Base decoder is labeled target_atomic_calibrated_linear_v1_20260924. This is a held-out calibrated linear inverse, not a physics-exact inverse.

## ds_pro runtime validation

Use the formal evaluator without modifying source code.

Required checks:

1. base_decoder_version appears in episode/task/final JSON;
2. base-active and arm-active counts agree with raw action records;
3. arm_active_nonzero_base_steps == 0 under calibrated mode;
4. bm3_nonzero_steps == 0 under calibrated mode;
5. decoded bm0/bm1/bm2 remain within [-1,1];
6. side_deadzone_fraction is reported when base-active steps exist;
7. raw completed dy and diagnostic decontaminated dy are both present;
8. Local-TTT evidence bytes/shape remain unchanged by diagnostics;
9. existing mp4/mp4_pred outputs remain intact.

Do not optimize or change the decoder during validation. Return evidence and failure cases to GPT/ChatGPT for any code change.


## 2026-09-26 full-smoke result

The production evaluator with control-mode diagnostics completed all 18 `atomic_seen` tasks at one rollout per task.

Hard counters:

- `bm3_nonzero_steps = 0` for every task;
- `arm_active_nonzero_base_steps = 0` for every task;
- no assertion failure;
- no infrastructure error.

Control-mode output was strongly bimodal:

- 16/18 tasks remained saturated near -1 and never activated the base;
- NavigateKitchen remained saturated near +1 and was base-active for 450/450 steps;
- CloseFridge switched between the two modes and was base-active for 116/900 steps;
- no completed task showed control values hovering near the zero threshold.

Therefore the diagnostic evidence does not support changing the control threshold.

The main remaining question is model/training behavior: why only a subset of atomic tasks produce positive base control. This is not a decoder contract failure.

This smoke validates the emitted diagnostic counters and runtime contract. It did not independently byte-compare Local-TTT evidence against a pre-diagnostics build, so do not reinterpret the diagnostic-only decontamination as part of training evidence.

See `docs/build/PSM-WMA_RoboCasa_atomic_seen_smoke_full_2026-09-26.md`.
