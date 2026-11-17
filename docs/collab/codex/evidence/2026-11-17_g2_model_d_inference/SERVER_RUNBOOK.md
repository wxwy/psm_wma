# Existing server command / integration inputs — NOT_RUN

This uses `cosmos_framework.scripts.action_policy_server_robocasa`, not a new
service or a new smoke CLI. Only its parser/help was executed on CPU; see
[parser output](cli-parser/help.log) and [exact parser probe](cli-parser/probe.py).
The probe disables startup init and never constructs ActionModelService.

**BLOCKED for real execution until the actual online provider and validated
model identity/hooks factory exist.** Do not substitute fixture/expert data.
B must bind the final integrated Root/Child first. D's author gate tested
Child6991142 with B7e888f2; B's later3a5c6259 is not covered by that 361 claim.

## Required inputs

Use the existing compatible execution environment; no installation or upgrade.
Run in the **final integrated Child cwd**. All variables below are execution-side
inputs, not values chosen by this candidate:

| Variables | Meaning / verification |
|---|---|
| G2_PYTHON, G2_DEVICE | Existing GPU interpreter and one authorized visible model device, world_size=1 |
| G2_CHECKPOINT, G2_CONFIG | Local verified checkpoint and its exact G2 config; complete inherited Local, actual state15/text/top recipes |
| G2_EMA_FLAG | Exactly `--use-ema-weights` or `--no-use-ema-weights`, matching the selected verified weight tree |
| G2_HOOKS_FACTORY | Existing importable `module:function(service)` returning G2ModelHooks using real versions and native mRoPE mode |
| G2_PROVIDER_FACTORY | Existing current-rollout `module:function(service)` implementing snapshot/load_view, initial GT/static text and exact content/mask provenance |
| G2_OWNER_TOKEN_FILE | Existing private bounded coordinator capability file, never print its contents |
| G2_RUN_LEASE, G2_MANIFEST_DIGEST, G2_SLOT_ID | Existing Session coordinator's run, SHA256 manifest and one physical Slot assignment; do not invent them |
| G2_SEED, G2_STEPS, G2_FPS | Frozen same-runtime parity inputs/settings; guidance remains1, native H16/raw15/max64 |
| G2_PORT, G2_TIMEOUT_S, G2_LOG | Owned endpoint, original bounded prediction timeout and new independent log path |
| G2_CACHE_FLAG | Exactly `--g2-cache-enabled` or `--no-g2-cache-enabled` |
| G2_CACHE_SESSIONS, G2_CACHE_ENTRIES, G2_CACHE_CPU_BYTES, G2_CACHE_GPU_BYTES, G2_CACHE_HANDLES | Finite tested cache bounds; account for all pinned B1/mixed-B conditions plus model/provider working memory |

Loader versions required by G2ModelHooks are listed in the handoff; a path/task
name is not a checkpoint digest. The factory forwards only B's public model
methods. As a construction example (not a supplied production asset factory):

```python
return G2ModelHooks(service.model, versions=verified_loader_versions,
                    use_float_positions=actual_native_position_mode,
                    top_variant=loaded_top_variant)
```

For B's3a5c6259 successor, the loaded model must have `_diffusion_cache is None`:
G2 rejects unvalidated diffusion-layer residual caching. Configure this through
B's actual finalized model config; do not invent an override name or globally
disable old G1 optimizations. The service has no optimizer/GA flag. The execution
side GA=1 requirement applies to C/B's training smoke, not to a new server flag.

## B1 / cache on-off command template

NOT_RUN. First verify every required variable above; unset input is a blocker.
Use a fresh owned invocation/log, and the existing coordinator/protocol:

```bash
CUDA_VISIBLE_DEVICES="$G2_DEVICE" PYTHONPATH=. \
"$G2_PYTHON" -m cosmos_framework.scripts.action_policy_server_robocasa \
  --checkpoint-path "$G2_CHECKPOINT" --config-file "$G2_CONFIG" "$G2_EMA_FLAG" \
  --host 127.0.0.1 --port "$G2_PORT" \
  --local-memory-mode required --local-memory-max-sessions 1 \
  --history-source server_vae --action-chunk-size 16 --raw-action-dim 15 --max-action-dim 64 \
  --transaction-profile b1 --transaction-owner-token-file "$G2_OWNER_TOKEN_FILE" \
  --transaction-run-lease "$G2_RUN_LEASE" --transaction-manifest-digest "$G2_MANIFEST_DIGEST" \
  --transaction-slot-id "$G2_SLOT_ID" --transaction-timeout-s "$G2_TIMEOUT_S" \
  --g2-profile g2_r2 --g2-hooks-factory "$G2_HOOKS_FACTORY" \
  --g2-provider-factory "$G2_PROVIDER_FACTORY" "$G2_CACHE_FLAG" \
  --g2-cache-max-sessions "$G2_CACHE_SESSIONS" --g2-cache-max-entries "$G2_CACHE_ENTRIES" \
  --g2-cache-cpu-bytes "$G2_CACHE_CPU_BYTES" --g2-cache-gpu-bytes "$G2_CACHE_GPU_BYTES" \
  --g2-cache-handles "$G2_CACHE_HANDLES" \
  --guidance 1 --seed "$G2_SEED" --num-steps "$G2_STEPS" --fps "$G2_FPS" \
  --no-run-validation > "$G2_LOG" 2>&1
```

Cache-off changes only G2_CACHE_FLAG for the matched run, with the same fixed
source/weights/input snapshot/RNG/settings and reset/Local evidence protocol.
Record actual resolved settings via existing `/info`, stage hit/miss and raw
outputs; do not pool cache hits/misses or call host timings GPU acceleration.
Physical cache parity has NOT_RUN status; predeclare same-runtime numerical
criteria before comparison, rather than relaxing tolerance after a failure.

R1: load an actual R1 Global-off config/checkpoint, set `--g2-profile g2_r1` and
omit the provider option. R1 must not construct Reader or read Global payload.
Changing only a label on an R2 checkpoint does not establish an R1 baseline.

## Mixed Session B2 delta

Use the same existing server command, but replace the three B1 settings with:

```text
--local-memory-max-sessions 2
--transaction-profile batch
--transaction-slot-ids "$G2_SLOT_IDS" --transaction-max-batch-size 2 --transaction-batch-wait-ms 20
```

Remove `--transaction-slot-id`. G2_SLOT_IDS is the coordinator's exact two-slot
comma-separated list. Keep one model device/rank. The cache must fit all active
member pins; eviction is not permission to drop live conditions. The original
batch API owns ordering, deadline, media, Local candidates and publication.
The existing shared-VAE feature profile can be integrated separately; this
template makes no new actual feature-provider/GPU validation claim.

## Bounded execution acceptance

Execution side should freeze a small actual input list and limit it to the
agreed representative decisions (including reset/task switch, at least three
replans, image/geometry/mask changes, top variants in their matched configs,
and B1 plus one real mixed batch). Keep initial GT binding and all map versions
causal to each run. Empty/full text conditions must have separate Global keys.
Use original Session End/cleanup and original deadline; no additional service,
expert playback or replacement Local scheduler.

PASS requires actual checkpoint/config/source verification, declared numeric
parity, expected stage reuse/invalidation, same request conditions throughout
denoising, no extra Local update on retry, correct mixed routing and proven
owned cleanup. Missing assets/factory/provider => BLOCKED; unsupported multi-rank
or guidance !=1 => reject; exception/NaN/parity/source/cleanup failure => FAIL
with evidence retained. Real latency/memory and closed-loop outcomes remain
separate measurements. This document grants no GPU/training/evaluation launch.
