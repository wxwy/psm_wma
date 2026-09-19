# Current Experiment Matrix

## Research question

The current Local Memory stage asks whether causal memory carried across an episode improves long-horizon robot policy behavior compared with current-observation / short-history controls, while keeping the native Cosmos action objective intact.

## Engineering controls already closed

| Experiment | Purpose | Status |
|---|---|---|
| Native grouped-vs-scalar parity | Check A2 regrouping math / gradient scale | PASS |
| B=1 matched control | Throughput and loss-scale control | PASS |
| A2 3-step real GPU | Real forward/backward and memory budget | PASS |
| Exact resume | Restore frontier + fast state consistently | PASS |
| Full-catalog A2 20-step | Real full-catalog stability / timing / memory | PASS |
| 5000-window planning | Capacity + slot-local epoch reuse | PASS |
| Online Local on/off generation | Verify Local path reaches action output | PASS |

These runs are engineering acceptance evidence. They are not the final research ablation.

## Main research comparisons

The final result table should distinguish at least:

| Variant | Current obs | short/recent memory | TTT fast state | Purpose |
|---|---:|---:|---:|---|
| Native Cosmos baseline | ✓ | — | — | no-memory baseline |
| Short-history / recent-memory control | ✓ | ✓ | — | context-length control |
| Local Memory TTT | ✓ | ✓ | ✓ | main Local Memory model |
| Local Memory off at inference | ✓ | checkpoint-trained | off | action-path ablation |
## Primary metrics

For LIBERO closed-loop evaluation, record:

- success rate (SR)
- task/suite breakdown
- trials per task
- rollout steps / failures where available
- checkpoint iteration
- Local Memory mode

Engineering metrics that should accompany training:

- native weighted loss
- Local runtime gradient presence after zero-init warmup
- step wall time
- CUDA peak allocated
- native forwards / update
- valid consumers / update
- resume / slot-epoch telemetry

## Current evidence references

- Engineering verifier: `../../artifacts/g0/sync_a2_final_verification_2a9df880_v3.json`
- Long-run readiness: `../../artifacts/g0/a2_long_run_readiness_2a9df880/a2_long_run_readiness_v1.json`
- Canonical artifact manifest: `../../artifacts/CANONICAL.json`

## Not yet claimed

The 5000-step A2 training result, final LIBERO SR gain, Persistent Spatial State gain and Action-conditioned World Model gain are not yet frozen results.