# PSM-WMA E003 — Local Memory A2 Training Archive Note

- Date: 2026-09-22
- Status: ARCHIVED
- Canonical summary: `artifacts/g0/localmem_ttt_a2_training_full_record_iter3288_2026-09-22.md`
- Machine-readable summary: `artifacts/g0/localmem_ttt_a2_training_full_record_iter3288_2026-09-22.json`
- Loss figure: `artifacts/g0/localmem_ttt_1x32_training_loss_iter3288.webp`

## Key frozen facts

- 8×A100-80GB FSDP8
- A2 active Local-Memory TTT
- B_stream=8
- TBPTT=16
- configured max_iter=5000
- owner stopped at iter3288
- last saved checkpoint iter3200
- raw_last_group_loss 16.35 -> 0.790
- mean step wall approximately 16.4s
- iter2800 SR 331/400 = 82.75%
- iter3000 SR 358/400 = 89.5%

## Compute-comparison adjudication

Do not adopt the simplistic statement that A2 and WINDOW-H16 are incomparable merely because their microbatch counts differ.

The current recipes are aligned at the effective consumer/update budget:

```text
A2        ~= 2048 consumers / optimizer update
WINDOW-H16 = 2048 consumers / optimizer update
```

This makes them a reasonable matched training-scale comparison.

At the same time, do not claim exact FLOP equality without measurement:

- A2 pays recurrent/TTT/driver overhead
- WINDOW pays much larger transformer-context cost from full-spatial H16 history

Therefore use:

> **training-budget/sample-count aligned; token/FLOP profile not strictly identical.**

This is the preferred wording for future reviews and reports.
