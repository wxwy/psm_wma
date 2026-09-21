# Local Memory TTT 1×32 — iter3000 Required / Init / Off Ablation

Recorded: 2026-09-21  
Checkpoint: `iter_000003000`  
Status: **COMPLETE — 400/400 valid episodes per mode**

## Experiment question

This matched ablation isolates two contributions:

```text
required - init = incremental contribution of online persistent fast-weight update
init - off      = contribution of learned Local pathway with W0 frozen
```

All evaluation settings are matched except `LOCAL_MEMORY_MODE`:

- `required`: online TTT fast-weight update enabled
- `init`: fast weights frozen at checkpoint-learned W0; real evidence/query/readout preserved
- `off`: Local Memory path disabled

Matched settings:

- NUM_STEPS=30
- guidance=1.0
- fps=20
- action_chunk=16
- action_horizon=16
- num_trials_per_task=10
- num_envs=4

## Suite-level results

| Suite | Required | Init (W0 frozen) | Off | R−I | I−O |
| --- | ---: | ---: | ---: | ---: | ---: |
| libero_spatial | 94/100 | **98/100** | 95/100 | -4 pp | +3 pp |
| libero_object | 97/100 | **99/100** | 88/100 | -2 pp | +11 pp |
| libero_goal | **79/100** | 77/100 | 59/100 | +2 pp | +18 pp |
| libero_10 | **88/100** | 76/100 | 38/100 | **+12 pp** | **+38 pp** |
| **Overall** | **358/400 (89.5%)** | **350/400 (87.5%)** | **280/400 (70.0%)** | **+2.0 pp** | **+17.5 pp** |

## Task-level success counts

### libero_spatial

| Task | Required | Init | Off |
| ---: | ---: | ---: | ---: |
| 0 | 10 | 10 | 10 |
| 1 | 10 | 10 | 9 |
| 2 | 10 | 9 | 10 |
| 3 | 10 | 10 | 10 |
| 4 | 9 | 10 | 9 |
| 5 | 10 | 9 | 10 |
| 6 | 9 | 10 | 9 |
| 7 | 6 | 10 | 8 |
| 8 | 10 | 10 | 10 |
| 9 | 10 | 10 | 10 |

### libero_object

| Task | Required | Init | Off |
| ---: | ---: | ---: | ---: |
| 0 | 10 | 10 | 10 |
| 1 | 10 | 10 | 3 |
| 2 | 9 | 10 | 10 |
| 3 | 8 | 10 | 10 |
| 4 | 10 | 10 | 10 |
| 5 | 10 | 10 | 10 |
| 6 | 10 | 10 | 5 |
| 7 | 10 | 10 | 10 |
| 8 | 10 | 10 | 10 |
| 9 | 10 | 9 | 10 |

### libero_goal

| Task | Required | Init | Off |
| ---: | ---: | ---: | ---: |
| 0 | 0 | 0 | 0 |
| 1 | 10 | 10 | 10 |
| 2 | 10 | 10 | 10 |
| 3 | 10 | 8 | 5 |
| 4 | 10 | 9 | 10 |
| 5 | 10 | 9 | 2 |
| 6 | 8 | 8 | 9 |
| 7 | 3 | 3 | 3 |
| 8 | 8 | 10 | 10 |
| 9 | 10 | 10 | 0 |

### libero_10

| Task | Required | Init | Off |
| ---: | ---: | ---: | ---: |
| 0 | 10 | 8 | 6 |
| 1 | 10 | 10 | 3 |
| 2 | 10 | 10 | 0 |
| 3 | 9 | 8 | 4 |
| 4 | 10 | 9 | 8 |
| 5 | 7 | 5 | 8 |
| 6 | 10 | 9 | 0 |
| 7 | 10 | 10 | 9 |
| 8 | 4 | 1 | 0 |
| 9 | 8 | 6 | 0 |

## Interpretation

### 1. Init is a strong learned retrieval baseline, not a constant-token baseline

`init` freezes the episode fast weights at checkpoint-learned W0, but it still consumes real completed evidence and computes a dynamic query/readout.

At policy time t, the Local route uses the latest completed transition evidence rather than re-encoding the current Cosmos observation:

```text
e_(t-1) = Encoder(z_(t-1), a_(t-1))
q_(t-1) = QueryProj(e_(t-1))
m_t      = Read(W0, q_(t-1))              # init
m_t      = Read(W_t, q_(t-1))             # required
policy   = Cosmos(z_t, m_t)
```

With action-horizon execution, one policy query may consume several newly completed transitions sequentially; the injected Local token is the readout after processing that completed evidence frontier.

Therefore W0 already represents a dataset-level learned associative prior, while q changes with the current completed transition.

### 2. Most aggregate gain over OFF is already present with frozen W0

Overall:

```text
Off      70.0%
Init     87.5%   (+17.5 pp over Off)
Required 89.5%   (+2.0 pp over Init)
```

Measured result: the learned Local pathway plus transition-conditioned W0 retrieval is already very strong on LIBERO.

This does **not** imply that online fast-weight update is unimportant in general.

### 3. Online update signal grows with task complexity in this benchmark

Suite-level Required−Init:

```text
Spatial   -4 pp
Object    -2 pp
Goal      +2 pp
LIBERO-10 +12 pp
```

The strongest positive signal is concentrated in the longer, multi-stage LIBERO-10 suite.

Current working hypothesis:

> W0 captures much of the dataset-level task/state-transition prior; online fast-weight writes become useful when the task requires episode-specific state that cannot be recovered from the current observation plus the latest transition alone.

This hypothesis is consistent with the observed complexity gradient but is **not yet proven** by this benchmark alone.

### 4. Do not over-interpret +2 pp overall as a statistically established global TTT gain

The aggregate difference is only 8 successes out of 400. A paired episode-level Required-vs-Init transition matrix / McNemar analysis should be used before making a global significance claim.

LIBERO-10's +12 pp is a stronger task-complexity signal and should be analyzed separately.

## Implication for the next experiment

WINDOW-H16 is now the most informative matched control:

```text
Off:
  no explicit history pathway

WINDOW-H16:
  raw recent history
  z[-16] ... z[-1] | z0 z1 z2 z3 z4

Init:
  learned W0 + transition-conditioned retrieval
  no episode-specific fast-weight write

Required:
  learned W0 + transition-conditioned retrieval
  + episode-specific online fast-weight write
```

The key comparison becomes:

```text
Required / Init / WINDOW-H16 / Off
```

This separates:

1. access to recent history,
2. learned compression/retrieval,
3. episode-specific online persistent writing.

## Validity

- required: 400/400 valid episodes
- init: 400/400 valid episodes
- off: 400/400 valid episodes
- same checkpoint and matched evaluation settings
- some INIT tasks were resumed after infrastructure failures using the same seeds/settings
- prior incomplete INIT partial results must not be mixed into this canonical summary

Result roots:

- required: `outputs/train_local_memory_a2/cosmos3_action_libero/action_sft/edge_libero_4in1_localmem_active/sim_test/iter_000003000/`
- init/off: `results/libero_local_memory/iter_000003000/{init,off}/`
