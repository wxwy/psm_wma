# V3 F0 author handoff — DS/GPT review requested

Date: 2026-10-16. This is the implementation author's factual handoff, **not an independent review or GPT verdict**.

| Authority | Exact SHA |
| --- | --- |
| Root implementation | `b3b64732efb225c3ee08b1d9f317a90228112b29` |
| Child implementation / Root Gitlink | `0fb7f587f56048a8ffaa12e2fdb7891abc0fb021` |
| Root parent / unchanged V3 HEAD at publication | `a1a47b36d10f1974ba0fb7cec872b1976c9c6838` |
| Child parent | `1d56320c08c56b0f8dd248919d152d81ae12ea7b` |

Both repositories publish the isolated branch `v3-f0-safe-start-20261016`. No force push, V3 source merge, official Child branch update or frozen B1 change was performed. Later evidence/handoff commits on the Root candidate are documentation only and must not replace the Root implementation SHA in runtime identity.

## Implementation and scope

- Child `examples/psm_wma_robocasa_corrected_phase5.py`: reject existing Fresh namespaces and path aliases; distributed preflight agreement; atomic new directory claim; exclusive launch lease and latest-drift check; immutable canonical configurations, per-launch resolved snapshots and fail-closed semantic identity; schedule-independent `--formal-execution-until`.
- Child `cosmos_framework/trainer/__init__.py`: opt-in Rank0 config writer with shared error; profile-specific committed optimizer/Local boundary validation; fail on premature dataloader/half-GA termination; emit completion only after save/finalize/barrier. Existing Local algorithms and optimizer numerics unchanged.
- Child `examples/psm_wma_robocasa_phase5_f0_test.py`: 26 CPU test methods. Existing `examples/psm_wma_robocasa_corrected_phase5_test.py` explicitly loads the deferred runtime and is normalized by Ruff; its assertions are retained.
- Root `scripts/train_v3_packed128_staged.sh`: new thin corrected Phase5 launcher; sealed 8-rank/T16/B8/GA2/K4/30000/500/100/workers0 profile, no full prefetch, no trailing overrides. Historical H3F launchers untouched. `SESSION.md` / `TODO.md` append-only task records.
- Frozen contract: `docs/build/PSM-WMA_V3_F0_safe_start_execution_budget_contract_2026-10-16.md`; SHA256 in evidence `manifest.json`.

Packed128 stays the actual default; this batch does not supply Index8 compatibility or fallback. The new identity deliberately creates a new stream/checkpoint config digest and rejects historical jobs without the new manifest. Budget/phase/legal load-path changes preserve same-job semantics; exact Root/Child, masks/loss/precision, optimizer rules, seeds and source identity cannot change. No old digest, DCP bytes, r2 threshold or Evidence was rewritten.

## Measured author CPU evidence

Evidence directory: `docs/collab/codex/evidence/2026-10-16_V3_F0_author_cpu/`.
Python 3.12.14, Ruff 0.12.7, pytest 9.0.2; `gate.json` contains exact commands, cwd, overrides, exit codes and source hashes matched against the committed Child.

| Check | Measured result |
| --- | --- |
| Direct unittest CLI | 26 methods passed; includes parameterized subtests |
| Pytest of the same suite | 26 methods +30 subtests passed, 0 failed/0 skipped, 1.77s |
| JUnit | 56 cases = methods + subtests; no additive coverage claim for the two runners |
| Ruff check / format --check | all 4 changed Python files passed |
| Python syntax / Shell syntax | 4 Python files and new launcher passed |
| Minimal CPU environment dependency check / Git diff --check | passed |

Negatives cover old latest/config/evidence/empty/partial jobs, traversal/symlink aliases, two simultaneous Fresh claims, concurrent Resume, latest drift, wrong Root/Child/Layout or canonical config, semantic changes, missing rank sidecar, mixed diagnostic options, invalid/resumed budgets, half-GA, missing commit and save/finalize exceptions. CLI rejection tests execute subprocess entry/preflight and assert old bytes+mtime unchanged. Writer and actual Trainer entry tests use synthetic external dependencies. Phase5 main's budget/lifecycle wiring enters that actual Trainer loop with synthetic assets. Fresh100/Resume500 preserve 30000/500/100; stop101 explicitly saves iter101. Hash/mtime/digest witnesses are in `unittest.log`.

The first development runs exposed incomplete synthetic fixtures (Torch annotation Tensor/no_grad, model config, grouped binding); those fixture omissions were corrected. Final results above supersede those author attempts; no skipped failure or modified assertion was used to obtain PASS.

**Limitations:** this minimal environment has no full Cosmos model dependency stack. Existing full-import Phase5/Grouped Trainer CPU regressions, actual configured-model serialization/preflight, real CPU collectives and target filesystem locking have not been executed here. No real model/optimizer forward, real DCP save/load, dataset scan, GPU, torchrun or training occurred. Author checks cannot close the independent Gate.

## Required next action and stop

DS_PRO request: `docs/collab/chatgpt/requests/2026-10-16_DS_PRO_V3_F0_safe_start_execution_budget_CPU_acceptance_b3b64732.md`.
Please collect independent CPU evidence on the exact clean detached Pair, then request GPT Fresh Incremental Review for the Pair plus frozen contract and CPU Evidence. No whole unchanged V3 re-review is requested. **DS/GPT verdicts remain PENDING.**

F1 is not started. DCP all-rank completion/atomic latest and strict RNG/no-reseed remain P0 blockers. Local/FSDP/loss/action semantics and durable storage remain independent S0 requirements. Do not start F1 until F0 acceptance/review; do not launch new GPU Fresh/Resume, Formal30k or real evaluations from this author handoff.
