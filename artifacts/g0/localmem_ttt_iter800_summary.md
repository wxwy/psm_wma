# Local Memory TTT — LIBERO iter_800 Evaluation Summary

Date recorded: 2026-09-20

## Provenance

- Method: Local Memory TTT
- Training checkpoint: `iter_000000800` / 800 training steps
- Evaluation: LIBERO closed-loop
- Trials: 10 trials per task
- Suites: `libero_object`, `libero_spatial`, `libero_goal`, `libero_10`
- Total episodes: 400
- Total successes: 259
- Aggregate success rate: **64.75% (259/400)**
- Evidence status: **user-reported result recorded from project chat; raw per-suite `summary.json` files were not attached or independently re-verified at recording time.**

## Suite Summary

| Suite | Success Rate | Successes / Episodes |
| --- | ---: | ---: |
| libero_object | **90%** | 90 / 100 |
| libero_spatial | **88%** | 88 / 100 |
| libero_goal | **68%** | 68 / 100 |
| libero_10 | **13%** | 13 / 100 |
| **Overall** | **64.75%** | **259 / 400** |

## libero_object — 90% (90/100)

| Task | SR | Result | Instruction |
| ---: | ---: | ---: | --- |
| 0 | 80% | 8/10 | pick up the alphabet soup and place it in the basket |
| 1 | 100% | 10/10 | pick up the cream cheese and place it in the basket |
| 2 | 100% | 10/10 | pick up the salad dressing and place it in the basket |
| 3 | 100% | 10/10 | pick up the bbq sauce and place it in the basket |
| 4 | 100% | 10/10 | pick up the ketchup and place it in the basket |
| 5 | 80% | 8/10 | pick up the tomato sauce and place it in the basket |
| 6 | 90% | 9/10 | pick up the butter and place it in the basket |
| 7 | 50% | 5/10 | pick up the milk and place it in the basket |
| 8 | 100% | 10/10 | pick up the chocolate pudding and place it in the basket |
| 9 | 100% | 10/10 | pick up the orange juice and place it in the basket |

## libero_spatial — 88% (88/100)

| Task | SR | Result | Instruction |
| ---: | ---: | ---: | --- |
| 0 | 100% | 10/10 | pick up the black bowl between the plate and the ramekin and place it on the plate |
| 1 | 100% | 10/10 | pick up the black bowl next to the ramekin and place it on the plate |
| 2 | 100% | 10/10 | pick up the black bowl from table center and place it on the plate |
| 3 | 100% | 10/10 | pick up the black bowl on the cookie box and place it on the plate |
| 4 | 60% | 6/10 | pick up the black bowl in the top drawer of the wooden cabinet and place it on the plate |
| 5 | 30% | 3/10 | pick up the black bowl on the ramekin and place it on the plate |
| 6 | 90% | 9/10 | pick up the black bowl next to the cookie box and place it on the plate |
| 7 | 100% | 10/10 | pick up the black bowl on the stove and place it on the plate |
| 8 | 100% | 10/10 | pick up the black bowl next to the plate and place it on the plate |
| 9 | 100% | 10/10 | pick up the black bowl on the wooden cabinet and place it on the plate |

## libero_goal — 68% (68/100)

| Task | SR | Result | Instruction |
| ---: | ---: | ---: | --- |
| 0 | 0% | 0/10 | open the middle drawer of the cabinet |
| 1 | 90% | 9/10 | put the bowl on the stove |
| 2 | 100% | 10/10 | put the wine bottle on top of the cabinet |
| 3 | 70% | 7/10 | open the top drawer and put the bowl inside |
| 4 | 100% | 10/10 | put the bowl on top of the cabinet |
| 5 | 0% | 0/10 | push the plate to the front of the stove |
| 6 | 70% | 7/10 | put the cream cheese in the bowl |
| 7 | 80% | 8/10 | turn on the stove |
| 8 | 90% | 9/10 | put the bowl on the plate |
| 9 | 80% | 8/10 | put the wine bottle on the rack |

## libero_10 — 13% (13/100)

| Task | SR | Result | Instruction |
| ---: | ---: | ---: | --- |
| 0 | 20% | 2/10 | put both the alphabet soup and the tomato sauce in the basket |
| 1 | 30% | 3/10 | put both the cream cheese box and the butter in the basket |
| 2 | 20% | 2/10 | turn on the stove and put the moka pot on it |
| 3 | 10% | 1/10 | put the black bowl in the bottom drawer of the cabinet and close it |
| 4 | 20% | 2/10 | put the white mug on the left plate and put the yellow and white mug on the right plate |
| 5 | 20% | 2/10 | pick up the book and place it in the back compartment of the caddy |
| 6 | 0% | 0/10 | put the white mug on the plate and put the chocolate pudding to the right of the plate |
| 7 | 10% | 1/10 | put both the alphabet soup and the cream cheese box in the basket |
| 8 | 0% | 0/10 | put both moka pots on the stove |
| 9 | 0% | 0/10 | put the yellow and white mug in the microwave and close it |

## Notes

This file records the reported evaluation result without reinterpretation. For a formal Evidence claim, bind these numbers to the exact checkpoint/config/inference protocol and preserve the raw suite-level `summary.json`, per-episode outputs, and media artifacts.
