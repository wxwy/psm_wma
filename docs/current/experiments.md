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

The final result table should distinguish:

| Variant | History span | History representation | Local token | Persistent episode state | Purpose |
|---|---|---|---:|---:|---|
| Native Cosmos / `none` | none | current observation only | — | — | no-memory baseline |
| E003-WINDOW-H16 / `window` | last 16 steps | native full-spatial clean vision latents + clean executed actions | — | — | strongest bounded-history control without extra learned compression |
| E003-GRU-H16 / `gru` | last 16 steps | zero-state GRU replay -> `1 x 32` | ✓ | — | matched compact learned-history control |
| Local Memory TTT / `ttt` | full episode | fast weights -> `1 x 32` readout | ✓ | ✓ | main persistent-memory model |
| Same-checkpoint history off | checkpoint-trained | history path removed at inference | off/absent | off | direct action-path attribution |

Primary interpretation order:

1. `window` vs Native — benefit of bounded recent history without an extra compressor.
2. `gru` vs `window` — effect of compressing the same bounded H16 history to one 32-D token.
3. `ttt` vs `window` — whether episode-level persistent memory adds value beyond direct H16 history.
4. same-checkpoint on/off — whether the trained history path actually changes action generation.

The TTT comparison is not a strict persistence-only ablation because its
representation/update mechanism also differs. `ttt_tbptt_steps=16` is graph
truncation only; TTT fast state persists across segments for the whole episode.
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