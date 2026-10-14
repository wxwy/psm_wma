# GPT → DS_PRO — V3 B1 end-to-end torchrun Comparator CPU readiness, one batch

Date: 2026-10-14
Scope: B1 stand-alone CODE+SYNTHETIC CPU acceptance ONLY, no actual GPU execution/torchrun, no real DCP loading, no full V3 audit.
Owner priority: postpone full V3 audit; B0 CLOSED; already accepted 451GB RoboCasa dataset MUST NOT be reverified.
**EXACT CODE SHA:** 4ca4710271936b286643d36ebeb41d0baeff7057 on wxwy/psm_wma:v3-gateb1-numeric-implementation-20261014.
This is a standalone **diagnostic** root, NOT the V3 production root or new frozen comparator leg. Docs commits after the CODE SHA are bookkeeping only.
Historical B1 SOURCE: Root b159f45906f7261d028aecc226ab7f2bb9807eb9 / Child 937066ffd90f2bf783ad4fbb4909e9c0b8922982.
Historical TARGET: Root c4731bca1a590663db88bd6cd74dbcf9fd513a85 / Child c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686.
V3 live trusted-startup Child 1d56320c08c56b0f8dd248919d152d81ae12ea7b remains separate; no source/target substitutions.

## What is now implemented
- tools/gates/v3_gateb1_run.py: --mode prepare (CPU-only, no data payload walk); --mode execute hard-denies unless separate explicit Owner GPU approval JSON binds exact CODE SHA, frozen pair, checkpoint fingerprint and frozen numeric thresholds. Rank0–7, CUDA world-size exactly 8, output only isolated /tmp evidence. Model/init, original four-component DCP, Local sidecar in-memory digest translation and two native GA2 steps use existing source/target code; no Trainer.train(), no Checkpointer.save(), nor formal namespace writes.
- tools/gates/v3_gateb1_no_rescan.py: temporary original Child class entrypoint adapters skip verified-index file walk, cache catalog glob/stat and SourceReader per-Episode path stat; after context restoring original frozen methods. Keep in-memory bindings and requested-sample failures.
- tools/gates/v3_gateb1_same_job.py: temp same-job source selector from original iter_000001300, strict 5-component DCP and NO SAVE; restore methods on exception.
- tools/gates/v3_gateb1_native_driver.py: exact native GroupedLocalMemoryTrainer.training_step for 1300→1301, 1301→1302, per-GA/Consumer index-major vs slot-major and Full/Partial; captures true callbacks before step and before zero-grad.
- tools/gates/v3_gateb1_model_sites.py / v3_gateb1_producer_cfg.py: native model per-consumer sigma, epsilon (scoped aten.randn) and Python text CFG transform keyed witnesses, mask and valid geometry, fail-closed missing/extra sites.
- tools/gates/v3_gateb1_compare.py: CPU paired JSON/PT postprocess for 8 ranks x 2 steps x P0/P1 x repeat0/1, canonical per-Consumer witnesses, all selected-FQN gradients, local fast state, FP32 master DeltaParameter and Adam moments, only candidate-tolerance verdict. Owner numeric thresholds still NOT FROZEN.

## Single independent CPU gate, no heavy assets

Pin a clean detached worktree at EXACT SHA 4ca4710271936b286643d36ebeb41d0baeff7057; record git status and object tree. Use existing Python 3.13.11 / torch 2.10 / pytest / Ruff venv with:
CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 LD_LIBRARY_PATH='' PYTHONDONTWRITEBYTECODE=1.

Execute from the diagnostic root checkout (never original frozen Root):
1. py_compile for all tools/gates/v3_gateb1_*.py and tools/gates/test_v3_gateb1_*.py (exclude B0 test; B0 CLOSED).
2. Ruff check --no-cache for the same B1 implementation/test files; no ruff --fix by DS.
3. python -m pytest -q tools/gates/test_v3_gateb1_*.py — synthetic small CPU tests only; new code local author result 70 passed, prior B1 68 tested separately; full B1 combined expected 138 if no environment differences. Report actual count, never invent.
4. CPU-only CLI negative: python tools/gates/v3_gateb1_run.py --mode prepare on a tiny synthetic isolated minimal frozen-identity fixture (no source dataset); or use the included --mode prepare mocked test if fixture unavailable. Confirm --mode execute without Owner auth is blocked *before CUDA/model/data* and --mode prepare performs zero dataset-wide validation.
5. Review exact new code diff relative previous CODE SHA 5aa79a73a4c6f1a424fa0a9476e1ce52ae9e9361, especially 7 new components/test pairs and the last bugfix file sha: v3_gateb1_run.py blob 16b2518d3e764a921878f569a2761685cc35b279; test_v3_gateb1_run.py blob e00c7563df01b35f221ec0afc06e07da4fcd6705. Verify all new files imported and gate contract fail-closes missing per-Consumer Sigma/Epsilon/CFG, skipped optimizer step, missing DCP component/Local state.
6. Static check full 8-rank production ABI against BOTH frozen Child versions, locate any original model RNG sites not covered by model-site hooks; do not silently substitute a new Child SHA nor claim GPU readiness on mocks. Verify the actual frozen per-sample resolution/CFG loader does not rely on a write to original DCP/latest pointer.
7. Enumerate remaining unresolved CPU-vs-GPU ABI hazards and first error by file:line. Do not change code.

Save one DS report under /tmp or docs/collab with exact CODE SHA, commands/exits, Ruff/pytest, authoritative SHA/ABI, and decision candidates. Do not run GPU/torchrun/Nsight, real DCP FSDP model load, 451GB offline data acceptance, Gate M or Formal30k. No follow-up B0 audit.

B1 remains GPU_NOT_AUTHORIZED until final GPT review, complete stochastic site coverage and Owner ratification of numeric acceptance table; real GPU P0/P1 Full/Terminal must receive separate Owner permission.
