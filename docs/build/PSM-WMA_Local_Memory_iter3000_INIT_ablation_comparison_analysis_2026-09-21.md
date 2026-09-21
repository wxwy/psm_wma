# PSM-WMA Local Memory — iter3000 INIT Ablation Comparison Analysis

- Date: 2026-09-21
- Status: RESULT FROZEN / ANALYSIS RECORDED
- Checkpoint: `iter_000003000`
- Canonical result artifact:
  - `artifacts/g0/localmem_ttt_1x32_iter3000_required_init_off_ablation_summary.md`
  - `artifacts/g0/localmem_ttt_1x32_iter3000_required_init_off_ablation_summary.json`

## Decision-level summary

The W0-frozen INIT ablation is complete and changes the interpretation of the Local Memory gain.

Measured:

```text
Off      70.0%
Init     87.5%
Required 89.5%
```

The correct decomposition is:

```text
Init - Off      = +17.5 pp
Required - Init =  +2.0 pp overall
Required - Init = +12.0 pp on LIBERO-10
```

## Mechanism interpretation

INIT must not be described as a static or constant memory token.

Checkpoint-learned W0 already contains a dataset-level learned prior. At inference, completed transition evidence generates a dynamic query and reads W0:

```text
(z_(t-1), a_(t-1))
        ↓
evidence encoder
        ↓
query projection
        ↓
Read(W0, q_(t-1))
        ↓
Local Memory Prefix m_t
        ↓
Cosmos current observation z_t
```

REQUIRED adds the episode-specific write:

```text
W_t = Update(W_(t-1), k_(t-1), v_(t-1))
m_t = Read(W_t, q_(t-1))
```

Thus:

- W0 = dataset-level learned associative prior
- dynamic q = transition-conditioned retrieval
- ΔW_t = episode-specific online persistent adaptation

A useful conceptual form is:

```text
W_t = W0 + ΔW_t
```

where INIT sets ΔW_t=0.

## Scientific interpretation

The aggregate LIBERO result alone does not establish a large global benefit from ΔW_t because REQUIRED and INIT differ by only 2 pp overall.

However, the suite trend is structurally important:

```text
Spatial   -4 pp
Object    -2 pp
Goal      +2 pp
LIBERO-10 +12 pp
```

Current hypothesis:

> Fast-weight online adaptation is task-complexity dependent. Simple LIBERO tasks are often solvable using the dataset-level W0 prior plus latest-transition retrieval; longer multi-stage tasks expose more value from episode-specific persistent state.

This is a hypothesis supported by the observed trend, not a final causal proof.

## Consequence for benchmark design

Do not de-prioritize fast weights solely because aggregate LIBERO Required≈Init.

Instead, future benchmarks should deliberately increase:

- horizon
- partial observability
- state aliasing
- irreversible subgoal transitions
- need to remember which subgoals have already been completed
- need to retain information no longer visible in z_t

LIBERO-10 is currently the strongest signal in this direction.

## Next experiment

WINDOW-H16 remains the next key control.

It tests whether the gains attributed to learned Local memory can be reproduced by giving Cosmos direct access to raw recent history:

```text
z[-16] ... z[-1] | z0 z1 z2 z3 z4
```

Interpretation matrix:

- WINDOW≈INIT≈REQUIRED → recent context access dominates
- INIT>WINDOW → learned retrieval/compression is useful
- REQUIRED>INIT>WINDOW → episode-specific online persistent write adds value beyond raw recent context
- WINDOW>REQUIRED → current TTT update/compression loses useful historical information

## Follow-up analysis without rerunning episodes

When raw episode-level matched outcomes are available, compute Required-vs-Init paired transitions for:

- all 400 episodes
- LIBERO-10 100 episodes

and run a paired test such as McNemar. This would separate the observed +2 pp overall / +12 pp LIBERO-10 trends from seed-level variance.
