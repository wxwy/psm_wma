# Corrected V3 — Formal30k Config + Telemetry Targeted CPU Closure

Date: 2026-10-09
Reviewer: ChatGPT — independent incremental code/Evidence review

## Exact formal implementation pair

- Root: `cd9c362555e9ebf447da3a90f7cbf43a572c6153`
- Child / Gitlink: `bf79d4a0d0db9f5c10eb3486236cdfaaf1a12c73`
- Gate: `CORRECTED-V3-FORMAL30K-CONFIG-AND-TELEMETRY-READINESS`
- Frozen metric contract: `docs/build/PSM-WMA_V3_corrected_formal30k_training_telemetry_contract_2026-10-09.md`
- Previous implementation candidate: root `d68cc72276455cd9648eae30c25302373793d35a` / child `801e58efd1d8908c1e18be9b27999422125098bb`

Root's Gitlink at the implementation commit has been independently verified to equal the child SHA above. Review/bookkeeping commits authored after this implementation SHA are not replacement formal targets.

## Verdict

`APPROVE_FORMAL30K_CONFIG_AND_TELEMETRY_READINESS`

**Gate status: CLOSED, scoped to formal30k configuration freeze + corrected Phase5 telemetry implementation + targeted CPU/static acceptance only.**

`TELEMETRY_TARGETED_CPU_GREEN`

`FORMAL30K_TRAINING_NOT_AUTHORIZED`

No new GPU run, real checkpoint resume, 30k run, or online inference acceptance is implied by this closure.

## Previously closed evidence (not reopened)

1. Full corrected target-atomic exact-window cache, B3/B4/B5, 9126 episodes.
2. Phase3.5 held-out three-task/nine-window numerical compatibility.
3. 8xH100 full-corpus fresh iter0->1 optimizer readiness. Its short-run DCP is still diagnostic-only and **must never be resumed as formal30k**.
4. Formal30k config preflight: `max_iter=30000`, `warmup=500`, `save_iter=100`, T16/B8/GA2/K4/world_size8, official DROID DCP fresh init, digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`.

The telemetry-only change does not alter the fields included in the frozen semantic config digest.

## Latest exact-pair remediation diff and independent review

Between the Round2 child `801e58...` and accepted child `bf79d4a...` only these paths change:

- `examples/psm_wma_robocasa_corrected_telemetry_test.py`: two lines of `nn.init.ones_` for fixture encoder weight/bias. The fixture has six encoder tensor elements plus two deterministic core query elements, so the existing `sqrt(8)` parameter-L2 expectation now has a deterministic and correct basis. The existing `pre_optimizer` native-forward/backward cardinality guard remains unchanged.
- `examples/psm_wma_robocasa_corrected_telemetry.py`: only Ruff-specified expression formatting; no computational change.

No last-round changes to `GroupedLocalMemoryTrainer`, `GroupedLocalMemoryWindow`, model, loss scaling, fast update, optimizer, scheduler, sampling, cache, or DCP ownership. The implementation base remains the reviewed passive observer/timer instrumentation introduced earlier in this telemetry Gate.

Frozen metric and timing contract is satisfied at the targeted CPU/static level: detached valid-consumer-weighted loss aggregation, Local mean/max/count, rank-local total/generation/action/Local norm breakdown, 100-step slow-parameter norms and sampled CUDA events, synchronous data-prepare timing, separated post-commit logging and checkpoint timing. This is not a claim of **measured** on-GPU timing precision, nor of globally reduced FSDP gradient norms.

## DS_PRO actual-target-runtime evidence accepted

DS_PRO tested the exact root/child/Gitlink triple on the existing training-server project directory using Python 3.13.11 / torch 2.10.0+cu128 / pytest 9.0.2 / Ruff 0.12.7:

- `examples/psm_wma_robocasa_corrected_telemetry_test.py`
- `examples/psm_wma_robocasa_corrected_phase5_test.py`

Result: **37 passed / 1 skipped / 0 failed**, 16.00 s.
- The one skip is the optional real-asset environment-variable-dependent snapshot test, outside this Gate.
- `ruff format --check` on the three previously failing files: **3 files already formatted**.
- Prior round on unchanged non-format functionality: Ruff check PASS and py_compile PASS; no reason to repeat previously green unrelated checks.
- The exact pair and root Gitlink match, child worktree is clean; pre-existing root `SESSION.md`/`TODO.md` modifications and untracked evidence files were preserved. No DS production-code modification, upload or commit.

Raw execution reports are DS-local:
- `/tmp/psm_wma_v3_telemetry_r3_pytest.log`
- `/tmp/psm_wma_v3_telemetry_r3_ruff_format.log`
- Prior Ruff-check/py_compile reports remain on DS's training server.

The review independently checks final GitHub diff/provenance; it does **not** falsely claim to have independently rerun DS's test commands or accessed DS's local logs.

## Historical blockers

- Round1: grouped observer fixture did not model native cardinality — **CLOSED**.
- Round2: parameter-L2 assertion used random encoder weights — **CLOSED** with deterministic fixture.
- Round2: three remaining Ruff formatting differences — **CLOSED** per Round3 report.
- No current blocker remains within the **targeted telemetry CPU/static** Gate.

## Promotion / next authorization

Promote the exact candidate child by non-forced fast-forward `v3-local-ttt` -> `bf79d4a...`, and the root candidate including this review and canonical Inbox bookkeeping by non-forced fast-forward `V3`. The promotion SHA of root may differ from `cd9c...` because adding review/Inbox does not change the accepted implementation pair. Verify root Gitlink remains `bf79d4a...` after promotion.

DS_PRO should continue on a **single existing local project directory**, preserving root MM-owned files; no new worktree, code edits or uploads.

The next possible Gate is a separately authorized **bounded, fresh formal-schedule execution** using actual `max_iter=30000, warmup=500` without resuming the diagnostic iter1. This closure is not an authorization to execute that Gate and does not authorize formal30k.
