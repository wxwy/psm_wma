# Local Memory TTT 1×32 — iter2800 LIBERO 4-Suite Evaluation

Recorded: 2026-09-20  
Method: Local Memory TTT  
Memory readout: `K_local=1`, `local_dim=32`  
Training checkpoint: `iter_000002800`  
Evaluation: LIBERO closed-loop, 10 trials/task, 10 tasks/suite, 4 suites  
Total: **331/400 = 82.75%**

## Training loss

![Local Memory TTT 1x32 training loss](./localmem_ttt_1x32_training_loss_iter3288.webp)

Figure provenance from the supplied training-loss plot:
- title: `PSM-WMA Local Memory A2: single-step loss (run 09:54, FSDP off, worker=12, 3288 points)`
- series: `raw_last_group_loss (single-step)` and `moving avg (10)`
- image stored as a 960 px WEBP conversion of the supplied PNG for repository size; no numerical reconstruction.

## Suite summary

| Suite | Successes | SR |
| --- | ---: | ---: |
| libero_spatial | 94/100 | **94.0%** |
| libero_object | 97/100 | **97.0%** |
| libero_goal | 68/100 | **68.0%** |
| libero_10 | 72/100 | **72.0%** |
| **Overall** | **331/400** | **82.75%** |

## Native Cosmos iter2800 comparison

| Suite | Native Cosmos iter2800 | Local TTT 1×32 iter2800 | Delta |
| --- | ---: | ---: | ---: |
| libero_spatial | 96% | 94% | -2 pp |
| libero_object | 99% | 97% | -2 pp |
| libero_goal | 76% | 68% | -8 pp |
| libero_10 | 58% | 72% | **+14 pp** |
| **Overall** | **82.25%** | **82.75%** | **+0.50 pp** |

This records observed results only. Same-checkpoint Local-on/off remains the direct action-path attribution experiment.

## libero_spatial — 94/100

| Task | Result | Instruction |
| ---: | ---: | --- |
| 0 | 10/10 | pick up the black bowl between the plate and the ramekin and place it on the plate |
| 1 | 9/10 | pick up the black bowl next to the ramekin and place it on the plate |
| 2 | 10/10 | pick up the black bowl from table center and place it on the plate |
| 3 | 10/10 | pick up the black bowl on the cookie box and place it on the plate |
| 4 | 7/10 | pick up the black bowl in the top drawer of the wooden cabinet and place it on the plate |
| 5 | 9/10 | pick up the black bowl on the ramekin and place it on the plate |
| 6 | 9/10 | pick up the black bowl next to the cookie box and place it on the plate |
| 7 | 10/10 | pick up the black bowl on the stove and place it on the plate |
| 8 | 10/10 | pick up the black bowl next to the plate and place it on the plate |
| 9 | 10/10 | pick up the black bowl on the wooden cabinet and place it on the plate |

## libero_object — 97/100

| Task | Result | Instruction |
| ---: | ---: | --- |
| 0 | 10/10 | pick up the alphabet soup and place it in the basket |
| 1 | 9/10 | pick up the cream cheese and place it in the basket |
| 2 | 10/10 | pick up the salad dressing and place it in the basket |
| 3 | 10/10 | pick up the bbq sauce and place it in the basket |
| 4 | 10/10 | pick up the ketchup and place it in the basket |
| 5 | 9/10 | pick up the tomato sauce and place it in the basket |
| 6 | 10/10 | pick up the butter and place it in the basket |
| 7 | 9/10 | pick up the milk and place it in the basket |
| 8 | 10/10 | pick up the chocolate pudding and place it in the basket |
| 9 | 10/10 | pick up the orange juice and place it in the basket |

## libero_goal — 68/100

| Task | Result | Instruction |
| ---: | ---: | --- |
| 0 | 1/10 | open the middle drawer of the cabinet |
| 1 | 10/10 | put the bowl on the stove |
| 2 | 10/10 | put the wine bottle on top of the cabinet |
| 3 | 5/10 | open the top drawer and put the bowl inside |
| 4 | 9/10 | put the bowl on top of the cabinet |
| 5 | 2/10 | push the plate to the front of the stove |
| 6 | 7/10 | put the cream cheese in the bowl |
| 7 | 7/10 | turn on the stove |
| 8 | 8/10 | put the bowl on the plate |
| 9 | 9/10 | put the wine bottle on the rack |

## libero_10 — 72/100

| Task | Result | Instruction |
| ---: | ---: | --- |
| 0 | 7/10 | put both the alphabet soup and the tomato sauce in the basket |
| 1 | 10/10 | put both the cream cheese box and the butter in the basket |
| 2 | 9/10 | turn on the stove and put the moka pot on it |
| 3 | 5/10 | put the black bowl in the bottom drawer of the cabinet and close it |
| 4 | 10/10 | put the white mug on the left plate and put the yellow and white mug on the right plate |
| 5 | 10/10 | pick up the book and place it in the back compartment of the caddy |
| 6 | 8/10 | put the white mug on the plate and put the chocolate pudding to the right of the plate |
| 7 | 10/10 | put both the alphabet soup and the cream cheese box in the basket |
| 8 | 0/10 | put both moka pots on the stove |
| 9 | 3/10 | put the yellow and white mug in the microwave and close it |

## Source result path

`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/outputs/train_local_memory_a2/cosmos3_action_libero/action_sft/edge_libero_4in1_localmem_active/sim_test/iter_000002800/sim_test/iter_000002800/`

Raw server-side per-episode files were not copied into this artifact.
