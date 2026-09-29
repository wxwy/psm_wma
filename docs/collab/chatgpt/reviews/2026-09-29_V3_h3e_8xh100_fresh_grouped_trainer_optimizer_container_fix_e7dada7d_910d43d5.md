# PSM-WMA V3 — H3-E fresh2 grouped trainer OptimizersContainer fix

- Date: 2026-09-29
- Previous formal pair: `9bb0d9160f95a1df8081a7c18de3516f0273acfa` / `b858106897c17b39888fc1df2b72b189bab5827a`
- New formal root: `e7dada7d3aff98af110e0bde5e038a09fef8ec82`
- New formal child/Gitlink: `910d43d514dfb21aff84b9aaf1db484807f2ff57`
- Status: **H3E_8XH100_FRESH_ITER1_BLOCKED_FIXED_PENDING_REVALIDATION**
- Authorization: **fresh iter0 -> iter1 may be rerun after CPU/static + preflight revalidation**

## Fresh2 evidence

The previous harness-side optimizer-container fix was confirmed effective.

On all eight H100 ranks, fresh2 completed:

- optimizer construction and H3-E selected-parameter inventory;
- 32 native forwards / rank;
- 32 native backwards / rank;
- finite native losses around 14.7–14.9;
- no OOM;
- no CUDA error;
- no NaN/Inf;
- peak allocated about 7.9 GiB / rank and reserved about 9.98 GiB / rank.

The run then failed deterministically in
`GroupedLocalMemoryTrainer._require_finite_gradients` before the optimizer step because that
framework method still assumed a plain optimizer and accessed `optimizer.param_groups`
directly.

Both failed fresh OUTs are valid evidence and must remain untouched.

## Root cause

The trainer receives the framework `OptimizersContainer`, whose public optimizer collection is
`.optimizers: list[torch.optim.Optimizer]`.

The grouped trainer's finite-gradient guard had not been updated for this framework type.

## Fix

`cosmos_framework/trainer/local_memory_grouped.py` now defines
`_optimizer_parameters(optimizer)`:

- `OptimizersContainer` -> iterate all `.optimizers`;
- plain optimizer -> treat as a single optimizer;
- walk every inner `param_groups`;
- deduplicate parameters by object identity while preserving order;
- reject an empty container;
- reject an inner optimizer lacking `param_groups`;
- reject an empty selected-parameter set.

`_require_finite_gradients` now consumes this normalized parameter list, preserving the
existing semantics:

- at least one selected gradient must be present;
- sparse/non-finite gradients mark the step bad;
- distributed bad-state reduction still propagates failure across ranks;
- a bad step raises before optimizer/fast-state publication.

## Regression coverage

`local_memory_grouped_test.py` adds trainer-level coverage for:

- ordinary PyTorch optimizer;
- an actual `OptimizersContainer` shell with two inner optimizers;
- union/dedup-compatible parameter enumeration;
- empty container rejection;
- malformed inner optimizer rejection;
- finite gradients across container inners;
- non-finite gradient rejection through a container.

The H3-E harness-side container regression remains in place as a separate layer.

No geometry, optimizer selection, Stage-A/B1 authority, manifest, Local algorithm, H3-E
fresh/resume iteration contract, or H3-F 30000-step budget was changed.

## Revalidation and fresh3

ds must validate the exact new pair with:

1. `cosmos_framework/trainer/local_memory_grouped_test.py`;
2. `examples/psm_wma_robocasa_h100_test.py`;
3. Ruff check/format on the four touched/relevant files;
4. `git diff --check`, root/child clean;
5. exact-pair H3-E read-only preflight.

If green, rerun only fresh iter0->iter1 with a new OUT/job, e.g.:

`/mnt/data1/data_v2_0617/psm_wma_v3_h3e_fresh3_e7dada_910d`

Do not delete/reuse:

- `psm_wma_v3_h3e_fresh_db081_b430`;
- `psm_wma_v3_h3e_fresh2_9bb0_b858`.

Owner authorization for 8-GPU co-resident functional smoke remains in force. Resume iter1->iter2
and H3-F 30000-step training remain unauthorized until fresh iter1 closes.
