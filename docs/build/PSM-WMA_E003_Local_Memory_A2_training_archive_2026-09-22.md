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

## Comparison-fairness adjudication

The primary E003 matching criterion is **training sample amount**.

Use this hierarchy:

```text
1. effective consumers / optimizer update
2. total consumers seen at compared checkpoint
3. method-specific compute / latency / VRAM reported separately
```

Current recipes:

```text
A2         ~= 2048 consumers / optimizer update
WINDOW-H16  = 2048 consumers / optimizer update
```

At a matched iter3000 checkpoint:

```text
both ~= 6,144,000 training consumers seen
```

Do not let the different microbatch counts redefine the experiment:

```text
A2 microbatches=2
WINDOW microbatches=16
```

is an implementation difference caused by the methods' different internal compute structures, not the primary fairness axis.

Preferred wording for future reviews:

> **sample-count aligned first; compute cost reported separately.**

Exact token-level FLOPs need not be forced equal. A2's TTT/driver overhead and WINDOW's longer native context are part of the actual cost of each method.
