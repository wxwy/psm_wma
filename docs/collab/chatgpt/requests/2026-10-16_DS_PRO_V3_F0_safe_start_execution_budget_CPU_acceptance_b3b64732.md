# DS_PRO — V3 F0 independent CPU acceptance

Date: 2026-10-16. Role: read-only execution and external Evidence only. Do not edit/commit production source, tests, config, SESSION/TODO or historical evidence.

## Exact candidate Pair

- Root implementation: `b3b64732efb225c3ee08b1d9f317a90228112b29`.
- Child/Gitlink: `0fb7f587f56048a8ffaa12e2fdb7891abc0fb021`.
- Both candidate branches: `v3-f0-safe-start-20261016`; Root V3 remains separate. Later candidate docs HEAD is not the implementation Root.
- Frozen contract: `docs/build/PSM-WMA_V3_F0_safe_start_execution_budget_contract_2026-10-16.md`, SHA256 `8f3e6d3c617e428e1142578266849f7da4f99390403678e732fc7470201b7fcd`.
- Author handoff: `docs/collab/codex/reviews/2026-10-16_V3_F0_safe_start_execution_budget_author_handoff.md`.
- Author Evidence: `docs/collab/codex/evidence/2026-10-16_V3_F0_author_cpu/` (26 methods +30 subtests, not independent acceptance).

Safely lock a clean detached validation checkout without reset/clean/force or covering uncommitted work. Child must exactly match the Root Gitlink. If that cannot be achieved safely, report BLOCKED. Preserve old V3/B1/E1 work, original Formal30k checkpoint/latest and all Evidence. Root ancestry must retain `a1a47b36...`; Child must directly descend from `1d56320c...`.

## CPU-only commands

Use the existing server Python and Ruff 0.12.7; no new dependency install or GPU process is authorized. Create a **new external** Evidence directory, set `EVIDENCE` and `EXACT_ROOT_WORKTREE` explicitly. Set `CUDA_VISIBLE_DEVICES=''`, `COSMOS_DEVICE=cpu`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`. Set `HF_HOME`, `HF_DATASETS_CACHE`, `MPLCONFIGDIR`, `XDG_CACHE_HOME` to existing writable external caches, and `PYTHONPYCACHEPREFIX="$EVIDENCE/pycache"`. Preserve each command and exit code; stop on the first unexplained failure.

In Root, record `git rev-parse HEAD`, `git ls-tree HEAD cosmos-framework`, Child `git rev-parse HEAD` and both `git status --porcelain`; independently verify exact Pair and contract SHA256. Run `bash -n scripts/train_v3_packed128_staged.sh`. **Do not execute the launcher** (its test intercepts Python to inspect arguments without running torchrun).

In Child, run:

```bash
ruff --version
ruff check examples/psm_wma_robocasa_corrected_phase5.py \
  examples/psm_wma_robocasa_corrected_phase5_test.py \
  examples/psm_wma_robocasa_phase5_f0_test.py cosmos_framework/trainer/__init__.py
ruff format --check examples/psm_wma_robocasa_corrected_phase5.py \
  examples/psm_wma_robocasa_corrected_phase5_test.py \
  examples/psm_wma_robocasa_phase5_f0_test.py cosmos_framework/trainer/__init__.py
python -m py_compile examples/psm_wma_robocasa_corrected_phase5.py \
  examples/psm_wma_robocasa_corrected_phase5_test.py \
  examples/psm_wma_robocasa_phase5_f0_test.py cosmos_framework/trainer/__init__.py
python examples/psm_wma_robocasa_phase5_f0_test.py -v
```

Write a temporary `[pytest]`-only config under Evidence and run the same focused suite with JUnit:

```bash
python -m pytest --noconftest -c "$EVIDENCE/pytest.ini" -q -p no:cacheprovider \
  examples/psm_wma_robocasa_phase5_f0_test.py --junitxml="$EVIDENCE/f0.xml"
```

Run existing full-import CPU regressions using the established repository test environment, recording skip reasons separately:

```bash
python -m pytest --num-gpus=0 -q -p no:cacheprovider -o addopts= \
  examples/psm_wma_robocasa_corrected_phase5_test.py \
  cosmos_framework/trainer/local_memory_grouped_test.py \
  cosmos_framework/trainer/local_memory_grouped_resume_test.py \
  --junitxml="$EVIDENCE/existing_cpu.xml"
```

The asset-dependent optional test may legitimately skip; count it explicitly. Missing import/tool/environment is BLOCKED, not evidence of acceptance. Do not change tests or add flags to hide a source failure. No need to rerun B0, dataset-wide 451GB acceptance, old B1 numerical comparators, or whole unchanged V3 review.

## Independent witnesses still required

1. Reproduce real subprocess CLI rejection, two-Fresh race, canonical byte/SHA+mtime preservation, namespace/sidecar/symlink negatives and isolated launch snapshots. Repeat the filesystem cases on the intended persistent output filesystem using **synthetic** directories under new Evidence, never existing jobs. POSIX flock/mkdir semantics must work; unsupported locking is BLOCKED.
2. Inspect exact changed source and author stub boundaries. Independently validate `_agree_preflight` error/digest propagation and optional Trainer writer failure across at least two **CPU Gloo** processes using a temporary probe, not torchrun. No real model or DCP is needed. A synthetic collective stand-in alone does not close this witness. Preserve peer errors and before/after file witnesses. Process death remains a timeout/launcher failure, not an unconditional collective-success promise.
3. Using existing accepted paths only, check actual resolved-config serialization through read-only corrected Phase5 `--preflight` on the exact Pair, `--phase fresh --formal-execution-until 100`, a nonexistent synthetic job name, accepted `--dataset-index-root`, `--num-workers 0`, no snapshot10/full prefetch. This is optional only if already supplied equivalent configured-environment evidence is authoritative; otherwise missing assets => BLOCKED for this witness. It reads metadata/index authority, never loads model/DCP tensors or scans the full corpus. Do not access the original Formal30k DCP. Verify no namespace/config/telemetry was created. Check phase/load-path/budget exclusions and true training-semantic inclusions in the digest. Do not claim this preflight proves GPU training.
4. Check actual Trainer budget/commit/save/finalize negatives, unchanged 30000/500/100 schedule, and explicit off-cadence iter101 save. Existing bounded diagnostics must remain non-resumable. Do not use old formal checkpoints for these tests; synthetic fixtures suffice.

Return one report containing Pair, frozen contract SHA, exact commands/environment/tool versions/exit codes, scoped diff, `gate.json`, pytest/unittest/Ruff/syntax logs, JUnit counts, per-negative output, digest invariance, old SHA+mtime witnesses, target-storage observations and any traceback/BLOCKED reason. Verify the worktrees and historical paths remain unchanged.

## Mandatory stop

Report F0 CPU result and wait for GPT Fresh Incremental Review of this Pair. No F1 implementation, GPU, torchrun, real Fresh/Resume, checkpoint migration, formal evaluation or Formal30k restart is authorized. F1 all-rank checkpoint publication and strict RNG remain unresolved P0 blockers even if F0 is GREEN. DS does not issue GPT verdicts or modify production code.
