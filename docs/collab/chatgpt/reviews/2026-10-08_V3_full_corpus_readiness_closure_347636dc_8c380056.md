# V3 Corrected Full-Corpus Readiness closure

Date: 2026-10-08

## Formal pair reviewed

- root: `347636dce5cd33ad5a538183595e6cda893354aa`
- child/Gitlink: `8c3800565f66cfbce2929264f1c2a7854137482e`
- root Gitlink independently verified to resolve exactly to child `8c380056...`.

Fresh pair-level review:
- relative to prior reviewed training root `b04fc2d4...`, root changes are documentation, data-prep tooling, audit tooling and acceptance tooling;
- production child/training implementation remains unchanged at `8c380056...`;
- no new model/trainer/inference implementation is introduced by this root transition.

## Verdict

`ROUND3_PARITY_AUDIT_TOOL_REVALIDATED`

`PHASE3P5_NUMERIC_COMPATIBILITY_GATE_CLOSED`

`CORRECTED_V3_FULL_CORPUS_8XH100_FRESH_ITER0_TO_ITER1_CLOSED_WITH_OBSERVABILITY_DEBT`

`ITER1_SHORT_RUN_CHECKPOINT_DIAGNOSTIC_ONLY_DO_NOT_RESUME`

`FORMAL30K_NOT_AUTHORIZED`

Next authorization:

`APPROVE_CORRECTED_V3_FORMAL30K_CONFIG_AND_TELEMETRY_READINESS_ONLY`

No optimizer step is authorized by that next Gate.

## 1. Round3 audit tool

Accepted:
- isolated `tools/v3` unittest: 11/11 PASS;
- z0 claimed 3/3/0 reproduced;
- visual96 claimed 3/3/0 reproduced;
- incompatible schema fails closed.

This closes the Round3 statistics-tool revalidation requested for this readiness round.

## 2. Full-corpus preflight

Accepted:
- clean root/child/Gitlink lock;
- full corrected cache manifest/corpus/source-binding digests match Phase3.5 authority;
- 9126 episodes;
- snapshot10 exercises real cached latent hits with `cached_latent_required=true`;
- readiness config digest for the intentionally short run: `ef6ca297`.

The short-run digest is not the formal30k digest and is not valid resume authority for formal training.

## 3. 8xH100 fresh iter0->1

Accepted evidence:
- fresh namespace;
- official DROID DCP warm-start with training state disabled;
- world_size=8, T16, B8, GA2, K4;
- exactly one completed optimizer iteration;
- process exit 0;
- checkpoint trainer iteration=1;
- optimizer 314 parameter groups, all step=1;
- exact optimizer inventory: 294 generation + 20 Local;
- Local optimizer moments nonzero for all 20 Local tensors;
- generation optimizer moments nonzero;
- all 569 model tensors finite, zero non-finite elements;
- grouped forward/backward observer passed;
- memory remained bounded and no OOM occurred.

### Observability debt

The run did not persist direct outer/action/vision/inner loss values or direct gradient-norm values because the corrected entrypoint clears callbacks and does not emit per-iteration loss telemetry.

This does not require repeating this expensive one-step readiness run: successful forward/backward accounting, a completed optimizer step, nonzero finite Adam state on the exact inventory, and finite post-step model tensors are sufficient to close the update-path readiness objective.

However, missing per-step loss/gradient telemetry is a blocker for formal long training observability and must be closed before formal30k authorization.

## 4. One-step scheduler NaN

Accepted as a bounded short-run artifact only:
- `max_iter=1`, `warmup=1` makes the scheduler decay denominator zero;
- checkpoint scheduler `_last_lr=[nan,nan,nan]`;
- base learning rates were valid for the actual optimizer step;
- post-step model tensors remain fully finite.

Therefore:
- this does not invalidate the completed iter0->1 update;
- the resulting checkpoint is **not resumable authority**;
- do not use it for same-job resume or formal30k;
- formal30k uses non-degenerate schedule `max_iter=30000`, `warmup=500`.

## 5. Phase3.5 numeric compatibility Gate

Threshold authority:
`docs/build/PSM-WMA_V3_phase3p5_numeric_compatibility_gate_v1.0_2026-10-08.md`

Frozen threshold:
`max_abs <= 0.0625`.

Held-out final selection satisfies the frozen requirements:
- OpenCabinet ep2522: starts 0/69/139;
- TurnOnMicrowave ep8077: starts 0/49/98;
- SlideDishwasherRack ep6555: starts 0/54/109;
- 3 distinct held-out underlying task classes;
- 9 exact windows;
- dry-run PASS with matching cache/source/VAE authority;
- thresholded real probe PASS;
- global pre-crop max_abs = 0.046875 <= 0.0625;
- post-crop within threshold;
- z0 within threshold;
- all selected windows finite;
- no tolerance auto-escalation or fallback.

Verdict:
`PHASE3P5_NUMERIC_COMPATIBILITY_GATE_CLOSED`

The prior exact-threshold mismatch remains historical evidence and is not rewritten.

The Owner-refrozen Phase3.5 supplemental obligation is now satisfied. No further 3-task/9-window parity Gate is required before formal long training.

## 6. Next authorized Gate

Only:
`CORRECTED-V3-FORMAL30K-CONFIG-AND-TELEMETRY-READINESS`

Required work before any formal30k optimizer step:

1. Freeze and preflight the intended formal schedule/config:
   - max_iter=30000;
   - warmup=500;
   - intended save cadence;
   - full corrected cache + matching flat source;
   - exact official DROID DCP fresh initialization;
   - config digest must be the formal30k digest (reported current target: `70e9867f`), not `ef6ca297`.

2. Restore rank0 per-step training telemetry without changing numerical semantics:
   - iteration;
   - outer/action/vision/inner loss;
   - grad norm;
   - generation / action / Local grad components if available;
   - fast_state_norm;
   - fast_update_norm;
   - lr min/max;
   - step wall time;
   - peak GPU memory;
   - epoch/frontier as applicable.

3. CPU/static validation that telemetry is observational only and does not alter optimizer inventory, loss scaling, Local transaction, resume state or data ordering.

4. Fresh pair-level review if child/root changes are required to wire telemetry.

This Gate does not authorize formal30k training.

After telemetry/config readiness closes, the next recommended execution Gate is a bounded fresh formal-schedule burn-in before authorizing the full 30k run.
