# DS_PRO — F0 REG-01 / TEST-02 focused independent CPU revalidation

Date: 2026-10-16. Read-only execution / external Evidence only. No production edits, dependency changes, GPU, torchrun, real DCP/model/data loads or training.

Exact Root implementation: **`9e51c94a6d5dba41bd37423b9db8e634ca433789`**. Child/Gitlink: **`7cae7c3049310ccc3b7e44ce9769534e152d1f26`**. Candidate branch in both repositories: `v3-f0-reg01-fixture-20261016`. Later docs HEAD is not the formal implementation Root.

Scope authority: `docs/collab/chatgpt/requests/2026-10-16_CODEX_V3_F0_b3b64732_reg01_and_fullenv_fixture_minimal_remediation.md` and GPT's `REQUEST_CHANGES` on `b3b64732/0fb7f587`. The old verdict remains. Author report: `docs/collab/codex/reviews/2026-10-16_V3_F0_REG01_TEST02_minimal_remediation_author_handoff.md`; logs/tracebacks under `docs/collab/codex/evidence/2026-10-16_V3_F0_REG01_TEST02_author_cpu/`.

Safely prepare a clean detached validation checkout at the exact Pair. No reset/clean/force or overwrite of existing work. If unsafe, BLOCKED. Use a new external Evidence directory; preserve all prior DS evidence and original worktrees/DCP/B1. Set writable external HF/Matplotlib/pycache directories, `CUDA_VISIBLE_DEVICES=''`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`. Disable pytest cache or write it externally. Use established environments; no package installs.

## 1. Version / source boundary

Record exact Root/Child/Gitlink and clean status. Child parent must be `0fb7f587f56048a8ffaa12e2fdb7891abc0fb021`; diff is exactly:

- `examples/psm_wma_robocasa_corrected_phase5.py`: move the same missing-Index ValueError guard before Namespace.
- `examples/psm_wma_robocasa_phase5_f0_test.py`: isolated external Megatron fixture, complete synthetic parallel config and two new negative/isolation tests.

Original Phase5 regression file, production Trainer/DCP/RNG/Local/optimizer and launcher must remain unchanged. Inspect that, within `preflight`, Namespace still runs before `_load_runtime()`/data/config/Trainer/writes when Index is provided; the existing main/distributed startup protocol is unchanged. Confirm Packed128 and 30000/500/100 untouched. Frozen baseline contract SHA256 remains `8f3e6d3c617e428e1142578266849f7da4f99390403678e732fc7470201b7fcd`.

## 2. Mandatory actual V2 full-dependency environment

This environment is unavailable locally to the author; synthetic collision proof is not its substitute. Use the **same V2 full-dependency Python** that produced the nine failures, but execute **new candidate source** from the validation Child (do not edit or check out V2 source). Record Python/pytest/torch/Megatron versions and source/environment paths, without secrets. Fresh shell/subprocess per test run; no fake global import state carried between commands.

Run the unchanged original regression with repository CPU setup:

```bash
python -m pytest --num-gpus=0 -q -p no:cacheprovider -o addopts= \
  examples/psm_wma_robocasa_corrected_phase5_test.py::test_formal_and_resume_require_accepted_index_before_data_open \
  --junitxml="$EVIDENCE/original_index_regression.xml"
```

The original function asserts Fresh and Resume missing-Index ValueError. No assertion edits or expected-exception relaxation. Also rerun the existing Phase5 CPU suite if the established environment can collect it; keep the prior legitimate asset skip explicit. Any new failure stops acceptance.

Create `[pytest]`-only config under external Evidence, then run the full F0 file and a separate nine-case selection using that **same full-dependency Python**:

```bash
python -m pytest --noconftest -c "$EVIDENCE/pytest.ini" -q -p no:cacheprovider \
  examples/psm_wma_robocasa_phase5_f0_test.py --junitxml="$EVIDENCE/fullenv_f0.xml"
python -m pytest --noconftest -c "$EVIDENCE/pytest.ini" -q -p no:cacheprovider \
  examples/psm_wma_robocasa_phase5_f0_test.py::TrainerTests --junitxml="$EVIDENCE/fullenv_trainer9.xml"
```

All **nine named TrainerTests** in author `scoped_probe.json` must actually execute and pass with zero skip/xfail. No reduced selection, removed tests, uninstalled Megatron or changed production runtime. Entire new suite must pass. New suite has 28 test methods; pytest9 author output has 32 additional unittest subtests /60 JUnit cases. Record actual runner counts and plugin behavior; do not force old 56 or assume identical collected counts across pytest versions.

## 3. Minimal V3 environment / static checks

Using established V3 minimal Python, rerun direct `python examples/psm_wma_robocasa_phase5_f0_test.py -v` and full-file pytest with the external empty config above. Verify new real-CLI missing-Index precedence for Fresh/Resume and no file/mtime or runtime-init changes; accepted-Index Namespace/symlink/identity negatives still pass. Confirm host module restoration and Megatron-present branch in the isolated fixture. Record all nine assertions remain intact.

Ruff must be 0.12.7. In Child:

```bash
ruff check examples/psm_wma_robocasa_corrected_phase5.py \
  examples/psm_wma_robocasa_phase5_f0_test.py \
  examples/psm_wma_robocasa_corrected_phase5_test.py cosmos_framework/trainer/__init__.py
ruff format --check examples/psm_wma_robocasa_corrected_phase5.py \
  examples/psm_wma_robocasa_phase5_f0_test.py \
  examples/psm_wma_robocasa_corrected_phase5_test.py cosmos_framework/trainer/__init__.py
python -m py_compile examples/psm_wma_robocasa_corrected_phase5.py \
  examples/psm_wma_robocasa_phase5_f0_test.py \
  examples/psm_wma_robocasa_corrected_phase5_test.py cosmos_framework/trainer/__init__.py
```

No need to reinstall dependencies or repeat old B0/451GB/B1 numerical experiments. Prior accepted two-process Gloo, real config preflight/serialization and persistent-volume evidence may be reused only after recording unchanged source boundaries and preserved artifacts. New acceptance must explicitly close both regression and actual full-environment test failures; missing environment => BLOCKED, never substitute minimal-env PASS.

Return exact Pair, commands/cwd/environment/tool versions/RCs, changed-file list, logs/JUnit/tracebacks, no-skip nine-case names/counts, old-file witnesses and evidence-reuse rationale. Stop after CPU report for GPT Fresh Incremental Review. **No F1 until F0 new-pair APPROVE_TO_CLOSE; no GPU or training authorization.**
