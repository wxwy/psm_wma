# DS_PRO Task — RoboCasa base decoder coordinate-frame correction + inverse calibration

Date: 2026-09-24

## Why this follow-up exists

The completed I/O report correctly proves observation parity and the arm/gripper/control action path.

However, the report's Gate C conclusion that the base decoder has an x/y slot/sign mismatch must be re-evaluated in the correct coordinate frame.

Training does NOT store world-frame base translation. It computes:

```python
d_world = pos[t+1] - pos[t]
d_ego = R_t.T @ d_world
```

Therefore canonical20[0:3] is ego/base-frame translation.

The live probe reported an initial/runtime base quaternion of approximately
`[0, 0, 0.707, 0.707]` (xyzw), i.e. about +90 degrees world yaw.

At +90 degrees yaw:

- positive ego X maps to positive world Y;
- positive ego Y maps to negative world X.

Thus the reported basis probes

- base_motion[0] -> world Y+
- base_motion[1] -> world X-

are exactly what the CURRENT mapping

- canonical ego dx -> base_motion[0]
- canonical ego dy -> base_motion[1]

would predict.

The high same-index offline correlations (0.911 / 0.878) reinforce this.

Do NOT swap/sign-flip bm0/bm1 unless the coordinate-frame test below disproves this.

## Gate E — explicit world/ego basis proof

For each fresh-reset basis probe from Gate C:

1. record pre base quaternion R;
2. record post-pre world translation d_world;
3. compute d_ego = R.T @ d_world;
4. report d_ego for bm0=+0.5 and bm1=+0.5.

Expected if current slot mapping is correct:

- bm0 probe: d_ego[0] > 0 and |d_ego[1]| << |d_ego[0]|
- bm1 probe: d_ego[1] > 0 and |d_ego[0]| << |d_ego[1]|

Also probe negative commands (-0.5) and verify signs reverse.

For bm2, compute the SAME relative rotation as training:
`R_rel = R_pre.T @ R_post`, then yaw = atan2(R_rel[1,0], R_rel[0,0]).
Verify bm2 sign vs relative yaw sign for +/- probes.

## Gate F — empirical inverse calibration for base-active frames

Use ALL valid base-active consecutive pairs from target-atomic (currently reported 87,013).

Feature vector per frame:

`x = [d_ego_x, d_ego_y, relative_yaw]`

Target command:

`u = raw_action[0:3]`

Evaluate two candidates with train/heldout split by episode (not random frames):

A. current heuristic:
`u_hat = 20 * x`

B. fitted linear inverse:
`u_hat = A @ x + b`

Also evaluate a diagonal-only fit:
`u_hat_i = gain_i * x_i + bias_i`

Report on held-out episodes:

- per-dim MAE / RMSE / max error / corr
- R^2
- saturation fraction after clamp [-1,1]
- 3x3 A and b
- diagonal gains/biases
- whether off-diagonal terms materially improve held-out error

Prefer the simplest mapping whose held-out error is materially better than x20.

Do not fit/evaluate on arm-active frames.

## Gate G — bm3 disposition

The prior report established:

- raw base_motion[3] is identically 0 over the full dataset;
- state base-z one-step delta has tiny nonzero simulation noise;
- live bm3 probe changes base Z/torso.

Therefore current mapping `base_z_delta * 20 -> bm3` is NOT training-command parity.

Verify once more that raw bm3 nonzero fraction is exactly zero across the formal training subset. If yes, verdict should be:

`bm3 = 0.0` at eval.

Do not learn a gain for bm3 from base-z simulation noise.

## Required final verdict

Return:

| Canonical component | Simulator command | Coordinate mapping | Gain mapping | Final status |
|---|---|---|---|---|
| ego dx | bm0 | ... | ... | EXACT slot / CALIBRATED gain |
| ego dy | bm1 | ... | ... | EXACT slot / CALIBRATED gain |
| relative yaw | bm2 | ... | ... | EXACT slot / CALIBRATED gain |
| base z | bm3 | inactive in data | fixed 0 | EXACT training parity |

If Gate E confirms the coordinate-frame analysis, revise the previous report's
"MISMATCH slot/sign" conclusion to "slot/sign aligned in ego frame; magnitude requires calibration."

Do not modify the running formal training process.
Do not change the evaluator decoder until this report is returned.
