# PSM-WMA V3 — H3-E fresh launch blocker: OptimizersContainer harness fix

- Date: 2026-09-29
- Previous formal pair: `db08117786a2483ca5cc7f4b58a0c3518e78bccc` / `b43097c74982f13e67c071ece729c7b6929cad52`
- New formal root: `9bb0d9160f95a1df8081a7c18de3516f0273acfa`
- New formal child/Gitlink: `b858106897c17b39888fc1df2b72b189bab5827a`
- Status: **H3E_8XH100_FRESH_ITER1_BLOCKED_FIXED_PENDING_REVALIDATION**
- Authorization: **fresh iter0 -> iter1 may be rerun after CPU/static revalidation**

## Failure evidence

The first co-resident 8×H100 fresh launch failed deterministically on all ranks before any
optimizer step.

Exception:

`AttributeError: 'OptimizersContainer' object has no attribute 'param_groups'`

The failure occurred in the H3-E harness optimizer-inventory witness after
`model.init_optimizer_scheduler` returned the framework's `OptimizersContainer`.
The harness incorrectly assumed a plain `torch.optim.Optimizer`.

The failure was not caused by OOM, CUDA reset, non-finite loss/gradient, grouped data, Stage-A
assets, B1 cache, or the H3-E training algorithm.

The partial failed OUT is evidence and must remain untouched.

## Fix

The H3-E harness now imports the framework `OptimizersContainer` and centralizes optimizer
parameter discovery in `_optimizer_parameter_ids`.

Behavior:

- if given an `OptimizersContainer`, iterate every item in `.optimizers`;
- otherwise treat the object as a single optimizer;
- union the parameter identities from every inner optimizer `param_groups`;
- fail closed on an empty container, missing `param_groups`, or an empty selected set.

The existing selected-name, host-key, Local-parameter-count, and `requires_grad` inventory
checks remain unchanged.

A regression test uses an actual `OptimizersContainer` shell with two inner PyTorch
optimizers and verifies union semantics, direct single-optimizer compatibility, and empty
container rejection.

No training geometry, asset authority, manifest, Stage-A checkpoint, B1 cache, Local-TTT
algorithm, H3-F 30k budget, or H3-E fresh/resume iteration budget changed.

## Revalidation

Before GPU rerun, ds must verify on the exact new pair:

- H3-E pytest: expected 12 passed;
- ruff check PASS;
- ruff format --check PASS;
- git diff --check PASS;
- root/child clean;
- H3-E preflight still returns 9036 catalog, frozen manifest/config digests, and 8-slot native
  batch contract.

## GPU rerun authorization

After CPU/static revalidation, rerun only fresh iter0→iter1.

Use a **new OUT/job name**. Do not delete or reuse the failed OUT:

`/mnt/data1/data_v2_0617/psm_wma_v3_h3e_fresh_db081_b430`

Suggested new output root:

`/mnt/data1/data_v2_0617/psm_wma_v3_h3e_fresh2_9bb0_b858`

The owner has authorized co-resident use of all eight H100s. Treat the run as functional
integration evidence, not isolated performance evidence.

Same-job resume and H3-F 30000-step training remain unauthorized until fresh iter1 closes.
