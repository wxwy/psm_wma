# G2-D author CPU/static evidence

Fixed Child **6991142cb94256f497347db40f58ad0ee3f482aa**, tree
`0cd9a38a2aadae13f203850cdbd6fc263926f08b`; D-only review base
`3bdfaa64af45a42eb2b5adde582505d33a5f08f2`.
[Handoff and interfaces](../../reviews/2026-11-17_G2_Model_D_Inference_Handoff.md),
[Child Draft #16](https://github.com/wxwy/cosmos-framework/pull/16).
Root baseline/Gitlink and all A/B/C dependencies are in [receipt.json](receipt.json).
Root Gitlink remains the formal V3 value; it does not select the D candidate.

## Final result — count once

**361 passed, 0 failed/error/skipped; 17 modules, 39.69s.**
75 are D-owned new cases; all are included in 361, not added to it.

- [Original JUnit](raw/final-01/junit.xml), [pytest stdout](raw/final-01/pytest.log),
  [shell exit 0](raw/final-01/exit-status.txt).
- [Environment](raw/final-01/environment.json): Python3.12.14,
  Torch2.10.0+cpu, pytest9.0.2; Ruff0.12.7. No dependency installation/upgrade.
- [11-file strict Ruff](raw/final-01/ruff.log),
  [legacy file with inherited I001 excluded](raw/final-01/ruff-legacy.log),
  [12-file format](raw/final-01/format.log), [syntax](raw/final-01/syntax.log),
  [diff check](raw/final-01/diff-check.log).
- The one I001 diagnostic is byte-identical in
  [review base](raw/final-01/baseline-I001.log) and
  [candidate](raw/final-01/current-I001.log); no other lint exception.
- **1,114 tracked Python SHA256 entries** in
  [before](raw/final-01/source-before.sha256) /
  [after](raw/final-01/source-after.sha256) are identical, and
  [fixed-source verification](raw/final-01/fixed-source-verify.log) matches the
  clean final Child. Receipt records all 12 D files and 26 unchanged A/B/C blobs.

Tests execute real production Session/Batch/Local CPU transactions and the
actual C native text helper. Small B UND/GEN-KV and A Reader/projector tests use
an explicit CPU reference at the normal attention dispatcher boundary. The
service diffusion output is a kernel fixture; real CPU Local state is compared
exactly. This is not a real checkpoint/CUDA/rollout or speed result.

## Reproduce

Run from the fixed D Child checkout (not the unchanged Root Gitlink):

```bash
PSM_G2_D_PYTHON=/workspace/.venvs/psm-wma-cpu/bin/python \
  bash ../docs/collab/codex/evidence/2026-11-17_g2_model_d_inference/run_g2_d_cpu.sh \
  ../work/g2-d-rerun
```

[CPU runner](run_g2_d_cpu.sh) lists all 17 modules and exact arguments. It fixes
single CPU threads and empty CUDA_VISIBLE_DEVICES, with no network/assets.
PASS requires no failure/error/skip; keep new rerun directories separate.
[Static runner](run_g2_d_static.sh) lists the exact scoped checks; its comparison
step expects a previously captured source-before.sha256 in the target directory.
The [captured receipt builder](finalize_g2_d_evidence.py) is the author's
workspace orchestration, not a model or deployment entry point.

The managed CPU environment lacks pytest-custom_exit_code/xdist required by the
root conftest. Final commands explicitly use `-c /dev/null --noconftest`; every
selected test still runs and its assertions remain intact. The 19 warnings are
retained (legacy marker/dependency warnings), not reported as skips.

## Preserved earlier attempts — do not sum

| Files | Actual outcome / interpretation |
|---|---|
| raw/cache-unit.log | Collection exit4: missing custom exit-code plugin; no tests executed |
| raw/cache-unit-02.log/.xml | Collection internal error: missing xdist hook; no test PASS claim |
| raw/cache-unit-03.log/.xml | 13 passed at initial cache-only source; cache warnings retained |
| raw/conditions-01.log/.xml | 40 passed, development source |
| raw/service-01.log/.xml | 2 failed/13 passed: new fixture assumed image_size had 2 rather than 4 entries; corrected fixture and inspected/fixed service use of post-pad prompt dimensions |
| raw/regression-01/ | 256 passed, earlier fixed initial D source |
| raw/reader-cache-01.log/.xml | 2 passed/27 deselected: A Reader-specific supplement only |
| raw/native-text-01.log/.xml | 74 passed, native C token/interface supplement |
| raw/public-hooks-01.log/.xml | 39 passed, B-public/A/C supplement |

These sources/selections overlap and precede the final gate. Only final-01 is
the final 361-case claim. No failed log was relabeled or deleted.
Original failure trace/log whitespace is preserved byte-for-byte; Root diff-check
therefore warns on raw/cache-unit.log and raw/service-01.log/.xml. Source and
authored documentation checks pass; raw evidence is not reformatted to silence it.

## NOT_RUN / integration limits

Actual rollout provider/initialization GT provenance, real checkpoint/Wan/Cosmos,
DATA_B state15 and DATA_C alignment, GPU BF16/compiled parity, native real actions
and all denoising velocities, GPU latency/memory, true online Sessions, simulation,
closed loop/SR, real FSDP/distributed cache, training and formal evaluation are
NOT_RUN. D multi-rank condition runtime explicitly rejects entry. Current loader
versions/factory and provider must be supplied and verified by B/execution side.

Cache budgets bound owned tensor payload/metadata and handles; they are not an
OS RSS or CUDA reserved-memory hard cap. Model/provider/temporary working memory
and deployment sizing need execution-side measurement. Host stage timings do
not constitute GPU performance evidence. Independent review is not claimed.
