# Batch C integration inspection (Codex internal CPU review)

Date: 2026-10-22. Inspection only; this is not GPT/DS Gate approval. Source was still being integrated while inspected.

## Verified boundaries

- Root starts from current merged V3 and preserves G1/A/B rather than selecting an old isolated candidate.
- Configuration uses strict schema, duplicate-key-safe YAML, CLI > YAML > defaults, typed/frozen protocol checks, explicit task subsets, one slot per GPU and a hard eighteen-class meaning for `tasks=all`.
- Config parsing performs no output mutation, and preserves venv executable symlinks. `--list-tasks` does not require a model checkpoint or working simulator environment.
- Runtime preflight receives the launch environment's actual PYTHONPATH; actual Simulator receives the same PYTHONPATH. CUDA selection and EGL differ intentionally and are not runtime-digest fields. The Child independently invokes the same pinned runtime probe before vendor/environment creation and checks its digest and official task horizons.
- Model DCP identity remains model-only; no inference requirement was added for `optim/`.
- Default lifecycle is still per-task, with explicit chunk16, required Local-TTT, max_sessions1, process-group ownership, strict /info, cancellation and task/episode budgets inherited from A.
- Task attempts have new directories, digest/attempt/episode-bound audit records and full-media validation before completion; partial attempts are retained and restarted from episode zero.
- Raw runtime probe stdout/stderr is outside the immutable evaluation manifest. Resume still binds exact source/runtime/checkpoint/config/protocol identities.
- Root lease was changed to O_NOFOLLOW plus regular-file checking following this inspection. Dry-run now shows each GPU's CUDA environment and actual base_port+worker mapping.
- Root finalization now passes the original task deadline into media validation rather than granting a fresh per-file task budget.

## Findings communicated to parent

1. Default generated-video manifest initially had Root `records` versus Child `videos` field mismatch. Current source now consistently uses `videos` and verifies schema/status/digest/attempt/replan/source-step correspondence. Resolved in integration.
2. Earlier dry-run gave every task the base port without CUDA environment, despite reporting distinct GPU slots. Parent corrected this to per-worker commands/environment.
3. Earlier `.run.lock` opened a possible symlink. Parent changed it to O_NOFOLLOW with regular-file validation.
4. Earlier post-simulator media decoding could exceed the original task wall budget. Parent/results agent added a shared deadline.
5. Completion ordering remains worth closing before source freeze: Queue finalization published `attempt.json` COMPLETE before writing `process_cleanup.json`. An I/O failure on the latter leaves a complete attempt while the invocation fails. Recommendation: write cleanup evidence before publishing COMPLETE and require/validate it for a skipped task. Parent was notified; re-read final diff to confirm resolution.

## CPU evidence executed by this agent

```
CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 \
PYTHONPYCACHEPREFIX=/tmp/psm-v3-batch-c-20261022/config/pycache \
/workspace/.venvs/psm-wma-cpu/bin/python -m pytest \
  --noconftest -c /dev/null -p no:cacheprovider -q \
  tools/v3/robocasa_eval_config_test.py \
  --junitxml=/tmp/psm-v3-batch-c-20261022/config/junit.xml
```

Latest: 70 passed, 0 failed/skipped. Ruff0.12.7 check and format pass for config module/tests. `bash -n scripts/run_robocasa_eval.sh` passed. Logs are in this directory.

No GPU, real Action Server, real simulator, real DCP, live G1 filesystem or network model assets were used. This inspection does not substitute for complete author integration tests, GPT review or DS independent CPU acceptance.

## Final source follow-up

Re-read the integrated Queue, all configuration/results helpers and the complete Child production diff after parent fixes:

- Completion ordering is now closed: Queue writes `process_cleanup.json` before `finish_attempt()`, and result validation requires both clean server/simulator witnesses before accepting or skipping an attempt.
- Task attempts now bind `Task/attempt_NNNN`, not just `attempt_NNNN`, in results, every action/prediction record and generated-media manifests. Cross-task copied evidence cannot inherit a sibling's matching attempt number.
- Actual Simulator `runtime_attestation.json` is required and its complete canonical body digest is rechecked during result validation/Resume.
- Final review discovered another operational mismatch: locked robosuite uses `CACHE_NUMBA=True`; without an external `NUMBA_CACHE_DIR`, actual controller JIT would create `.nbi/.nbc` under the locked source, making the following task fail the intentional dirty-source gate. Queue now uses a run-scoped external temporary cache for Numba/Matplotlib/XDG, preserves an explicit Owner HF_HOME or selects the external fallback, and passes the same context to server and simulator. The gate was preserved, not weakened.
- New actual CPU regression `tools/v3/robocasa_eval_cache_test.py` compiles an on-disk `@numba.njit(cache=True)` function, checks its real numerical result and real `.nbi/.nbc` creation in the external cache, then checks tracked Git source bytes and status remain clean. Environment tests verify cache redirection, explicit HF_HOME preservation and no environment-builder writes. **3 passed in 1.96s**; log/JUnit `cache-pytest.log` / `cache-junit.xml` in this directory. This used `PSM_NUMBA_PYTHON=/workspace/.venvs/psm-robocasa-vendor-cpu/bin/python` to select the already-installed CPU-only Numba environment; no skip or mocked compiler.
- Final review also identified decoder-grandchild cleanup: killing a Python decoder group without reaping adopted FFmpeg descendants could leave zombies under the Queue's existing subreaper. The source now reuses `OwnedProcess` for decoder ownership, bounded cleanup and PGID-specific reaping. Parent is adding the nested-decoder CPU regression; this reviewer did not duplicate the full integration suite.

**Final internal source assessment: no additional confirmed blocker found in the reviewed production paths after these fixes.** This is bounded internal author-team inspection, not an official independent GPT review or DS execution verdict. Parent's final focused regressions and exact committed-source checks remain required before submitting the new Pair.
