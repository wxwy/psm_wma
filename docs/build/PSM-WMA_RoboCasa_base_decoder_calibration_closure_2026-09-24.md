# PSM-WMA RoboCasa Base Decoder Calibration Closure

Date: 2026-09-24

Status: IMPLEMENTED / RUNTIME-VALIDATED ON FULL 18-TASK SMOKE

## Evidence source

ds_pro completed RoboCasa I/O Contract Verification Gates A–G against the formal target-atomic dataset and live RoboCasa simulator.

Key conclusions:

- observation contract is EXACT: left/wrist cameras, left|wrist composition, state16 ordering, transform geometry, and NL prompt source;
- arm/gripper/control action path is EXACT;
- bm0/bm1/bm2 slot and sign are EXACT in the robot ego frame;
- the old world-frame interpretation that called bm0/bm1 a slot/sign mismatch is superseded;
- the old static x20 base inverse has the correct direction but suboptimal gain;
- raw base_motion[3] is identically zero over the formal training subset and must be fixed to zero at evaluation.

## Formal calibrated inverse

Canonical base feature:

```
x = [ego_dx, ego_dy, relative_yaw]
```

Formal target-atomic episode-held-out inverse:

```
u = clamp(A @ x + b, -1, 1)
```

with:

```
A = [
  [28.84,   0.396,   0.0438],
  [-0.104, 29.53,   -0.396 ],
  [-0.0951,-5.776,  15.91  ],
]
b = [0.039, -0.0076, -0.0014]
```

The fourth simulator base command is fixed:

```
base_motion[3] = 0.0
```

because the formal training subset contains zero non-zero values for raw base_motion[3].

## Held-out evidence

Base-active pairs: 87,013 across 965 episodes.

Episode-level split:

- train: 772 episodes / 69,625 pairs
- held-out: 193 episodes / 17,388 pairs

Held-out MAE:

| Decoder | bm0 | bm1 | bm2 |
|---|---:|---:|---:|
| legacy x20 | 0.2082 | 0.2095 | 0.0864 |
| calibrated full matrix | 0.1408 | 0.1342 | 0.0396 |
| diagonal-only | 0.1408 | 0.1813 | 0.0394 |

The full matrix is retained because it materially improves held-out bm1 while preserving the strong bm0/bm2 performance.

After clamp [-1,1], full-matrix MAE remains best:

- bm0: 0.1302
- bm1: 0.1284
- bm2: 0.0375

## Implementation

Child:

`cosmos_framework/simulation/robocasa/closed_loop_eval.py`

Formal default `base_decode_mode` is now `calibrated`.

Behavior:

- control_mode < 0: base_motion is forced to zero;
- control_mode > 0: calibrated A@x+b inverse is used and clamped to [-1,1];
- base_motion[3] is always zero in calibrated mode;
- EEF/gripper/control decoding remains unchanged.

Legacy diagnostic modes remain available:

- `velocity`: prior x20 heuristic
- `delta`: direct state-delta command
- `zero`: disable base motion

Root launcher:

`scripts/eval_robocasa.sh`

Default:

`BASE_DECODE_MODE=calibrated`

## Regression coverage

`cosmos_framework/simulation/robocasa/closed_loop_eval_test.py`

Added assertions that:

- calibrated mode reproduces the frozen matrix/bias mapping;
- bm3 is exactly zero even when canonical base-z is nonzero;
- arm-active control keeps all four base commands zero.

## Runtime acceptance

Closed on 2026-09-26 by the full atomic_seen runtime smoke:

- 18/18 tasks completed;
- `LOCAL_MEMORY_MODE=required`;
- `BASE_DECODE_MODE=calibrated`;
- `REPLAN_STEPS=1`;
- `NUM_TRIALS=1`;
- no infrastructure error;
- `bm3_nonzero_steps == 0` across all completed tasks;
- `arm_active_nonzero_base_steps == 0` across all completed tasks;
- base-active execution was exercised by NavigateKitchen and CloseFridge.

This validates the calibrated decoder's runtime contract. It does not establish official RoboCasa SR because this was a one-rollout-per-task diagnostic smoke with replan=1.

See:

`docs/build/PSM-WMA_RoboCasa_atomic_seen_smoke_full_2026-09-26.md`
