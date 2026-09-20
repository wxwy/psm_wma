# Local Memory TTT 1×32 — iter3000 LIBERO 4-Suite Evaluation

Generated: 2026-09-20 15:42 CST  
Recorded: 2026-09-20  
Method: Local Memory TTT  
Memory readout: `K_local=1`, `local_dim=32`  
Training checkpoint: `iter_000003000`  
Evaluation: LIBERO closed-loop, 10 trials/task, 10 tasks/suite, 4 suites  
Total: **358/400 = 89.5%**

## Suite summary

| Suite | Successes | SR |
| --- | ---: | ---: |
| libero_spatial | 94/100 | **94.0%** |
| libero_object | 97/100 | **97.0%** |
| libero_goal | 79/100 | **79.0%** |
| libero_10 | 88/100 | **88.0%** |
| **Overall** | **358/400** | **89.5%** |

## Local TTT 1×32 iter2800 comparison

| Suite | Local TTT 1×32 iter2800 | Local TTT 1×32 iter3000 | Delta |
| --- | ---: | ---: | ---: |
| libero_spatial | 94% | 94% | 0 pp |
| libero_object | 97% | 97% | 0 pp |
| libero_goal | 68% | 79% | **+11 pp** |
| libero_10 | 72% | 88% | **+16 pp** |
| **Overall** | **82.75%** | **89.5%** | **+6.75 pp / +27 successes** |

Observed task-level changes iter2800 → iter3000:
- `libero_goal`: task03 5→10, task05 2→10, task09 9→10; task00 1→0.
- `libero_10`: task00 7→10, task02 9→10, task03 5→9, task06 8→10, task08 0→4, task09 3→8.

Remaining weak spots:
- `libero_goal/task00`: 0/10 — open the middle drawer of the cabinet
- `libero_goal/task07`: 3/10 — turn on the stove
- `libero_10/task08`: 4/10 — put both moka pots on the stove

## libero_spatial — 94/100

| Task | Result | Instruction |
| ---: | ---: | --- |
| 0 | 10/10 | pick up the black bowl between the plate and the ramekin and place it on the plate |
| 1 | 10/10 | pick up the black bowl next to the ramekin and place it on the plate |
| 2 | 10/10 | pick up the black bowl from table center and place it on the plate |
| 3 | 10/10 | pick up the black bowl on the cookie box and place it on the plate |
| 4 | 9/10 | pick up the black bowl in the top drawer of the wooden cabinet and place it on the plate |
| 5 | 10/10 | pick up the black bowl on the ramekin and place it on the plate |
| 6 | 9/10 | pick up the black bowl next to the cookie box and place it on the plate |
| 7 | 6/10 | pick up the black bowl on the stove and place it on the plate |
| 8 | 10/10 | pick up the black bowl next to the plate and place it on the plate |
| 9 | 10/10 | pick up the black bowl on the wooden cabinet and place it on the plate |

## libero_object — 97/100

| Task | Result | Instruction |
| ---: | ---: | --- |
| 0 | 10/10 | pick up the alphabet soup and place it in the basket |
| 1 | 10/10 | pick up the cream cheese and place it in the basket |
| 2 | 9/10 | pick up the salad dressing and place it in the basket |
| 3 | 8/10 | pick up the bbq sauce and place it in the basket |
| 4 | 10/10 | pick up the ketchup and place it in the basket |
| 5 | 10/10 | pick up the tomato sauce and place it in the basket |
| 6 | 10/10 | pick up the butter and place it in the basket |
| 7 | 10/10 | pick up the milk and place it in the basket |
| 8 | 10/10 | pick up the chocolate pudding and place it in the basket |
| 9 | 10/10 | pick up the orange juice and place it in the basket |

## libero_goal — 79/100

| Task | Result | Instruction |
| ---: | ---: | --- |
| 0 | 0/10 | open the middle drawer of the cabinet |
| 1 | 10/10 | put the bowl on the stove |
| 2 | 10/10 | put the wine bottle on top of the cabinet |
| 3 | 10/10 | open the top drawer and put the bowl inside |
| 4 | 10/10 | put the bowl on top of the cabinet |
| 5 | 10/10 | push the plate to the front of the stove |
| 6 | 8/10 | put the cream cheese in the bowl |
| 7 | 3/10 | turn on the stove |
| 8 | 8/10 | put the bowl on the plate |
| 9 | 10/10 | put the wine bottle on the rack |

## libero_10 — 88/100

| Task | Result | Instruction |
| ---: | ---: | --- |
| 0 | 10/10 | put both the alphabet soup and the tomato sauce in the basket |
| 1 | 10/10 | put both the cream cheese box and the butter in the basket |
| 2 | 10/10 | turn on the stove and put the moka pot on it |
| 3 | 9/10 | put the black bowl in the bottom drawer of the cabinet and close it |
| 4 | 10/10 | put the white mug on the left plate and put the yellow and white mug on the right plate |
| 5 | 7/10 | pick up the book and place it in the back compartment of the caddy |
| 6 | 10/10 | put the white mug on the plate and put the chocolate pudding to the right of the plate |
| 7 | 10/10 | put both the alphabet soup and the cream cheese box in the basket |
| 8 | 4/10 | put both moka pots on the stove |
| 9 | 8/10 | put the yellow and white mug in the microwave and close it |

## Completion note

`libero_10` was initially incomplete: tasks 0/1/3/6/8 had data; tasks 2/4/5/7/9 were missing. The missing tasks were filled on 2026-09-20 14:56–15:39 CST using 7 parallel clients on ports 8003–8009, one task per GPU, with `--resume` and `max_steps=520`.

## Source result path

`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/outputs/train_local_memory_a2/cosmos3_action_libero/action_sft/edge_libero_4in1_localmem_active/sim_test/iter_000003000/`

Raw server-side per-episode files were not copied into this artifact.
