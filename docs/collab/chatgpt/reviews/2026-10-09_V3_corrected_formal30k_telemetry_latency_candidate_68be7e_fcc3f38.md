# V3 corrected formal30k telemetry + latency — implementation handoff

Date: 2026-10-09
Status: CANDIDATE_IMPLEMENTED / TARGETED_CPU_VERIFICATION_PENDING

## Implementation pair

Root implementation candidate:
`68be7e67a674a986bc58b9af2ccbbee876041c90`

Child/Gitlink:
`fcc3f38a2fd38bffb02905b842b3369bf5408f98`

Branches:
- root: `v3-corrected-telemetry-pair-20261009`
- child: `v3-corrected-telemetry-20261009`

Root PR: https://github.com/wxwy/psm_wma/pull/2
Child PR: https://github.com/wxwy/cosmos-framework/pull/3

The production `V3` and `v3-local-ttt` branch tips have **not** been moved.

## Effective code changes from last approved child 8c380056

1. `examples/psm_wma_robocasa_corrected_telemetry.py`
   - rank0 per-committed-step loss, Local fast, norm and latency record;
   - detached per-consumer aggregation with no `.item()` on native forward/backward;
   - GPU/DTensor rank-local gradient L2 by total, generation, action subset,
     Local and Local submodules;
   - missing/nonfinite gradient tensors;
   - 100-step slow-parameter L2 and low-frequency CUDA events;
   - CPU host data_prepare/collate/transfer/Local scan/forward/backward/optimizer;
   - explicit `data_wait_ms=null` because the corrected producer is synchronous;
   - checkpoint save recorded separately, only on successful save.
2. `examples/psm_wma_robocasa_corrected_phase5.py`
   - binds the observer; preserves `config.trainer.callbacks={}`;
   - connects the first GA trigger timer and the read-only DCP save wrapper.
3. `cosmos_framework/trainer/local_memory_grouped.py`
   - read-only context-manager timer wrappers at existing operation boundaries.
   - metric forwarding excludes per-consumer `bool(torch.isfinite(...))`
     synchronization; scalar selection stays observational.
4. `cosmos_framework/model/generator/mot/local_memory_grouped_window.py`
   - wraps the unchanged `adapter.scan` with an optional Local scan timer.
5. Two targeted test files for aggregation, staged timing, no native `.item()`,
   100-step sampling, rank0 success logging, callback ownership, checkpoint timing.

No mathematical change to model forward, loss scaling, inner update, gradient
backward formula, optimizer/scheduler step, Local commit, DCP state or sample
order is authorized or intended.

## Frozen logging contract

`docs/build/PSM-WMA_V3_corrected_formal30k_training_telemetry_contract_2026-10-09.md`

`outer_loss`, Action/Vision raw scalar means and constant-weight contributions
when valid, aux gen/und, Local inner/fast mean-max-count, 8 grad groups,
nonfinite/missing gradients, 100-step parameter norms, host stage timing,
100-step CUDA event timing, step wall/throughput, peak VRAM and checkpoint time.

Interpret GPU event estimates as current-stream elapsed samples, not true
device utilization. Interpret gradient/parameter norms as rank0-local shards,
not globally reduced FSDP norms.

## Verification status

- GitHub remote diff and exact root Gitlink verified.
- Ephemeral GitHub Actions CPU smoke attempt 1: syntax PASS; Ruff check PASS;
  Ruff formatting did not match, unit tests were not executed.
- Subsequent ephemeral smoke attempts: GitHub Actions `startup_failure`
  (no jobs), therefore **not usable as passing evidence**.
- GitHub default pre-commit workflow historically cannot install pinned
  `rumdl==0.1.62`; do not infer a source failure from that dependency issue.
- No CUDA execution or real train step was attempted.
- Therefore current candidate is NOT READY for formal30k promotion.

## Only necessary targeted tests

On a runtime with current V3 dependencies and an isolated candidate pair:

```bash
python -m pytest -q \
  examples/psm_wma_robocasa_corrected_telemetry_test.py \
  examples/psm_wma_robocasa_corrected_phase5_test.py

python -m py_compile \
  examples/psm_wma_robocasa_corrected_telemetry.py \
  examples/psm_wma_robocasa_corrected_phase5.py \
  cosmos_framework/trainer/local_memory_grouped.py \
  cosmos_framework/model/generator/mot/local_memory_grouped_window.py

ruff check \
  examples/psm_wma_robocasa_corrected_telemetry.py \
  examples/psm_wma_robocasa_corrected_telemetry_test.py \
  examples/psm_wma_robocasa_corrected_phase5.py \
  cosmos_framework/trainer/local_memory_grouped.py \
  cosmos_framework/model/generator/mot/local_memory_grouped_window.py
ruff format --check \
  examples/psm_wma_robocasa_corrected_telemetry.py \
  examples/psm_wma_robocasa_corrected_telemetry_test.py \
  examples/psm_wma_robocasa_corrected_phase5.py \
  cosmos_framework/trainer/local_memory_grouped.py \
  cosmos_framework/model/generator/mot/local_memory_grouped_window.py
```

If Ruff format fails, the code owner must apply the formatting and commit a
new child SHA; DS does not modify production code. Once targeted tests PASS,
GPT performs a fresh incremental review of the final exact pair and promotes
child/root. No full historical suite or GPU iter1 rerun is warranted solely
for observability changes.

Formal30k training remains unauthorized.
