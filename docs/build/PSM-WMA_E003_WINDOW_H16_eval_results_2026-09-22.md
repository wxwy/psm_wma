# PSM-WMA E003 WINDOW-H16 Evaluation Results

Date: 2026-09-22  
Method: `window16 / native_window`  
Status: recorded evaluation result

## Evaluation protocol

- LIBERO suites: `libero_spatial`, `libero_object`, `libero_goal`, `libero_10`
- 10 tasks per suite
- 10 trials per task
- 100 episodes per suite
- 400 episodes per checkpoint
- Evaluated checkpoints: iter 200 / 400 / 600 / 800
- Episode step caps in the supplied result:
  - spatial: 220
  - object: 280
  - goal: 300
  - libero_10: 520

## Main SR curve

| Checkpoint | spatial | object | goal | libero_10 | Total |
|---|---:|---:|---:|---:|---:|
| iter_000000200 | 3/100 (3%) | 0/100 (0%) | 3/100 (3%) | 0/100 (0%) | **6/400 (1.5%)** |
| iter_000000400 | 13/100 (13%) | 1/100 (1%) | 6/100 (6%) | 0/100 (0%) | **20/400 (5.0%)** |
| iter_000000600 | 29/100 (29%) | 21/100 (21%) | 6/100 (6%) | 0/100 (0%) | **56/400 (14.0%)** |
| iter_000000800 | 50/100 (50%) | 68/100 (68%) | 40/100 (40%) | 2/100 (2%) | **160/400 (40.0%)** |

Overall learning curve:

```text
iter200  1.5%
iter400  5.0%
iter600 14.0%
iter800 40.0%
```

## iter_000000800 task-level SR

### libero_spatial — 50/100

| Task | SR |
|---:|---:|
| 0 | 7/10 |
| 1 | 5/10 |
| 2 | 8/10 |
| 3 | 6/10 |
| 4 | 0/10 |
| 5 | 3/10 |
| 6 | 6/10 |
| 7 | 8/10 |
| 8 | 2/10 |
| 9 | 5/10 |

### libero_object — 68/100

| Task | SR |
|---:|---:|
| 0 | 9/10 |
| 1 | 8/10 |
| 2 | 9/10 |
| 3 | 4/10 |
| 4 | 8/10 |
| 5 | 1/10 |
| 6 | 10/10 |
| 7 | 8/10 |
| 8 | 10/10 |
| 9 | 1/10 |

### libero_goal — 40/100

| Task | SR |
|---:|---:|
| 0 | 0/10 |
| 1 | 6/10 |
| 2 | 8/10 |
| 3 | 0/10 |
| 4 | 3/10 |
| 5 | 0/10 |
| 6 | 8/10 |
| 7 | 5/10 |
| 8 | 10/10 |
| 9 | 0/10 |

### libero_10 — 2/100

| Task | SR |
|---:|---:|
| 0 | 0/10 |
| 1 | 0/10 |
| 2 | 2/10 |
| 3 | 0/10 |
| 4 | 0/10 |
| 5 | 0/10 |
| 6 | 0/10 |
| 7 | 0/10 |
| 8 | 0/10 |
| 9 | 0/10 |

## Recorded observations

1. WINDOW-H16 shows a strong training-time rise from 1.5% at iter200 to 40.0% at iter800.
2. By iter800, `libero_object` is strongest at 68%, followed by `libero_spatial` at 50% and `libero_goal` at 40%.
3. `libero_10` remains the clear bottleneck at iter800: only task 2 succeeds (2/10), all other tasks remain 0/10.
4. The result should be treated as the WINDOW-H16 checkpoint curve; it does not by itself establish superiority over Native / GRU / TTT until matched-checkpoint comparisons are recorded.

## Source

Owner-supplied detailed task-level evaluation result:
`window16 (native_window, required) 详细 task 级 SR 测试结果`, generated 2026-09-22 15:25:06.
