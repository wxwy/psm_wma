# PSM-WMA V3 F1 — DS_PRO CPU Evidence Review (Same Formal Pair, Evidence-only)

**日期：**2026-10-16  
**审核：**GPT / independent Evidence & Gate reviewer  
**Gate：**`V3_F1_SYNC_LOCAL_DCP_STRICT_RNG_CPU_GATE`  
**Frozen Formal Implementation Root：**`6ebf8998a7935f2ad690bb547c5db5e5a4322e6d`  
**Frozen Child/Gitlink：**`2d128ed5a07601cdd424974f99b67832eafeeb41`  
**Candidate branch：**`v3-f1-checkpoint-rng-20261016` (docs head `ccfd900bc35fcd39ca9953aa7aa55b85398300ad` is NOT formal Root).  
**Current main V3 before record：**docs HEAD `c9ee16a348e6ac32927558965a05e3409a15813a`, old production Child remains `1d56320c08c56b0f8dd248919d152d81ae12ea7b`; F1 is not merged.  
**Frozen contract：**`docs/build/PSM-WMA_V3_F1_sync_checkpoint_strict_rng_contract_2026-10-16.md`, SHA256 `aa3f7c6db2bdf5a7c193de1398b7ff1aa81b59b08554552f6fa86fc3e2748185` (author-supplied SHA, frozen across this Evidence turn).  
**Prior F1 code/technical review on EXACT same pair：**`docs/collab/chatgpt/reviews/2026-10-16_V3_F1_6ebf8998_2d128ed5_sync_checkpoint_strict_rng_pre_DS_incremental_review.md` (commit `540f3842e0df301334cea86703c58a4d34e038b0`). **Formal pair unchanged: no repeat technical source/diff audit.**  
**Current DS Evidence basis：**Owner-uploaded generated paste `DS_PRO — V3 F1 同步 Checkpoint / 严格 RNG 独立 CPU 验收报告 — 2026-10-16` (129 source lines). Original DS server XML/log artifacts `/tmp/psm_v3_f1_accept_20261016/` and target-volume fixtures not directly available: Desktop Commander device is offline. Counts and behavioral observations below are explicitly **DS-reported**, not GPT independently rerun or byte-read.  
**Formal verdict literal: `REQUEST_CHANGES` — EVIDENCE-ONLY.** All reported core CPU DCP/Gloo/publish/RNG behavior is accepted within its stated scope, but **two frozen acceptance requirements are not demonstrated by this report**. No new proven production-code defect. F1 not yet `APPROVE_TO_CLOSE`; do not start GPU/Fresh/Formal30k.

## 1. New DS observations that close previously missing evidence

| Evidence requirement | DS report observation | Incremental disposition |
|---|---|---|
| Real CPU DCP/Gloo integration (F1-EVID-01) | In V2 full-dependency Python **29/29 F1 tests**, V3 Python **29/29**, both RC0, 0 failed/skipped. 14 real two-process Gloo scenarios; source/iteration disagreement, delayed rank, sidecar/component/marker/pointer failure, hard-exit and bounded 10.05s stall. DCP component write failure fails by bounded Gloo timeout rather than instant shared exception, which is within the frozen fail-no-success semantics. | **CLOSED FOR CPU 2-RANK / DS-reported** |
| Save order and independently readable pointer (F1-EVID-01/04) | On actual `/mnt/data` ext4 synthetic fixtures, visible complete `iter_000000001/002` with four DCP components, per-rank sidecars, `complete.v1.json`, stable pointer. Delayed rank before ack did not publish, release did. Separate stdlib reader checks pointer, marker, metadata SHA, shard extent/size, sidecar SHA. Old/latest untouched on injected failures; no staging residue on success. | **CLOSED FOR CPU synthetic state / DS-reported** |
| Strict per-rank RNG & two-rank restoration (F1-EVID-02) | All 18 `rng_state_0/1` required tensor leaves with correct schema; 2-rank synthetic CPU model/optim/scheduler/Local restored after deliberate mutation; Python/NumPy/Torch next draws exact per rank, `rng_restored_from_same_job=true`. Missing leaf/cross-rank mismatch fail-closed; deterministic Trainer resume skip-reseed test PASS. | **CLOSED FOR CPU / DS-reported** |
| New implementation exact identity | GitHub checked `6ebf8998...` Root tree Gitlink=`2d128ed5...`, F1 branch unchanged. DS reports clean detached Root/Child. | **PASS for formal identity** |
| Test accounting | 29 test methods in each of two envs; pytest9 JUnit header 50 includes subtests, XML 29 testcase. No multiplying two runs or counting 50 independent methods. | **CONSISTENT** |

**Remaining boundaries:** The CPU test uses a stand-in for CUDA RNG, two ranks rather than 8×H100/FSDP, and small synthetic DCP objects. Metadata and size checking do not hash all large model/optimizer shard bytes. The frozen CPU Gate can accept these limitations; the separate later Owner-authorized GPU Save→Resume Gate must cover real CUDA/FSDP/Optimizer/Local state. New F1 does not retroactively close B1 strict numeric parity.

## 2. Outstanding blockers — specific required evidence, no code change assumed

### F1-EVID-03 — MEDIUM / CPU: Actual full Cosmos config factory not proven

- **Code/evidence location:** `examples/psm_wma_robocasa_corrected_phase5.py:585–590`; production `cosmos_framework/trainer/__init__.py:178–184`; F1 test `cosmos_framework/checkpoint/dcp_local_safety_test.py:797–834`. DS report §4.4.
- **Root cause / factual gap:** DS cites `test_corrected_phase5_selects_safe_class_without_changing_formal_schedule`, but the test builds **synthetic `SimpleNamespace` config**, patches `overlay_local_config`, and assigns `SafeLocalDistributedCheckpointer` explicitly. It verifies class selection and schedule, **not** actual complete TOML/Hydra `load_experiment_from_toml` → `Config.validate/freeze` → `LazyConfig.save_pkl/yaml` → framework `instantiate(config.checkpoint.type,...)` with the real resolved Class target and compatible parameters. A separate `from cosmos_framework.checkpoint.dcp import SafeLocalDistributedCheckpointer` is only an import, not factory instantiation. Thus claim “真实 Cosmos 配置实例化” is stronger than the visible cited test.
- **Frozen acceptance contract:** DS request `docs/collab/chatgpt/requests/2026-10-16_DS_PRO_V3_F1_sync_checkpoint_strict_rng_CPU_acceptance_6ebf8998.md` §C explicitly requires `CPU-only configured preflight/serialization`, actual SafeLocal factory profile and strict sync local mode, with Fresh100/Resume500 semantic digest preserved.
- **Acceptance:** Provide compact **real full-dependency** read-only Phase5 `--preflight` evidence on this exact pair with accepted Index (no data rescan, no model tensor/DCP content read); assert exact SafeLocal target, async=false, strict=true, resolved config validate/freeze, canonical config serialized/reloaded and Fresh100/Resume500 semantic digest invariant. For the **factory** claim, separately show a real framework `instantiate` invocation on an isolated tiny CPU-Gloo 1–2-rank synthetic job/checkpointer config without production model/DCP accesses, or supply equivalent established full-dependency actual constructor/callback assertion. If actual instantiation requires GPU/production I/O, report the limitation explicitly rather than recasting a mock as proof. No new CUDA test authorized.

### F1-EVID-05 — MEDIUM / CPU: Affected full-dependency regressions and Ruff CHECK are not reported

- **Code/evidence location:** DS report §4.5/§5; exact frozen DS request §C/§D. Production F1 Child modified `dcp.py`, `trainer/__init__.py` and corrected `phase5.py`; its positive test `dcp_local_safety_test.py` does not cover legacy async/DCP distill with full Cosmos imports.
- **Root cause / factual gap:** DS provides **F1 new tests 29/29 in V2 and V3**, a particular deterministic Trainer test, `ruff format --check` and `py_compile` four files. It does **not** report execution/RC/JUnit for the specifically required full-dependency affected existing suite:
  `examples/psm_wma_robocasa_corrected_phase5_test.py`,
  `cosmos_framework/trainer/local_memory_grouped_test.py`,
  `cosmos_framework/trainer/local_memory_grouped_resume_test.py`,
  `cosmos_framework/checkpoint/dcp_distill_test.py`.
  Nor does §5 report independent `ruff check`, or six-file format/syntax as originally directed. Earlier F0 CLOSED remains valid for its old exact pair, but a new F1 changed production DCP/Trainer/Phase5 and needs **scoped regression** evidence; this does not re-open full B0/F0 or any historical GPU comparison.
- **Frozen acceptance:** DS instruction §C/§D above.
- **Acceptance:** DS supply actual affected existing suite **full-dependency** commands, RC/JUnit and legitimate skip names/reasons (if already executed, send the missing logs/summary, no unnecessary re-run); static `ruff check`, `ruff format --check`, `py_compile` for the six named F1+affected files with RC0. If full existing suite is blocked by asset/environment, report exact BLOCKED component and cause; do not silently claim PASS or skip an unrelated failure. Only this incremental affected test matrix, no B0, dataset-wide 451GB, previous 149 tests or historical B1 GPU jobs.

## 3. Formal disposition and next action

- **Current F1 gate on same formal pair: `REQUEST_CHANGES` — EVIDENCE-ONLY.** No code changes requested or justified solely from the present DS report; large majority of CPU failure-path risks are already covered.
- **DS_PRO next:** One narrow addendum addressing **only F1-EVID-03 and F1-EVID-05**, with exact commands/RC/JUnit and factory/serialization/config witness; original F1 DCP/Gloo/RNG + target-volume 14-scenario Evidence remains valid, do **not** rerun those tests. Existing F1 acceptance request remains canonical; new follow-up request `docs/collab/chatgpt/requests/2026-10-16_DS_PRO_V3_F1_EVID03_EVID05_CPU_addendum_6ebf8998.md` restricts the remaining scope.
- **On new Evidence, same Root+Child:** GPT performs **Evidence-only closure**, no re-review of unchanged production technical code. A concrete new real config/legacy regression failure must be escalated to a production blocker and Codex-only new SHA remediation.
- **No F1 CPU closure means F1 remains HOLD** for new training. Even later `APPROVE_TO_CLOSE` closes only CPU gate; it does not authorize 8×H100, DROID Fresh, real DCP, Formal30k, Gate M, index8 compatibility or B1 numeric parity. Independent storage capacity based on **actual DCP**, not historical B1 numerical `rank*.pt`, and an Owner retention plan still needed.
