# GPT → DS_PRO — V3 Gate B1-S1 numerical/stochastic/FSDP capture CPU acceptance

Date: 2026-10-14
Owner priority: V3 whole-repo audit deferred; execute B1 work first.
Isolated diagnostic branch: wxwy/psm_wma:v3-gateb1-numeric-implementation-20261014
Exact candidate: pin full branch HEAD at execution and report SHA, do not assume legacy B0 ec9d SHA.
Production Index8 Root b159f45906f7261d028aecc226ab7f2bb9807eb9 / Child 937066ffd90f2bf783ad4fbb4909e9c0b8922982 and Packed128 Root c4731bca1a590663db88bd6cd74dbcf9fd513a85 / Child c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686 are IMMUTABLE.

Role: DS_PRO executes validation-only. CPU static/synthetic tests only, never edit model/trainer/production/diagnostic code. NO GPU, torchrun, full dataset preflight, 451GB offline dataset revalidation, B0 repetition, DCP model load, optimizer training, migration or Formal30k.

In a clean detached diagnostic checkout with Python 3.13, torch 2.10, Ruff and pytest; HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES='' LD_LIBRARY_PATH='' PYTHONDONTWRITEBYTECODE=1:

Run, with exact exit codes logged:

python -m py_compile tools/gates/v3_gateb1_metrics.py tools/gates/v3_gateb1_stochastic.py tools/gates/v3_gateb1_fsdp_capture.py tools/gates/v3_gateb1_dcp_transient.py tools/gates/test_v3_gateb1_metrics.py tools/gates/test_v3_gateb1_stochastic.py tools/gates/test_v3_gateb1_fsdp_capture.py tools/gates/test_v3_gateb1_dcp_transient.py

python -m pytest -q tools/gates/test_v3_gateb1_metrics.py tools/gates/test_v3_gateb1_stochastic.py tools/gates/test_v3_gateb1_fsdp_capture.py tools/gates/test_v3_gateb1_dcp_transient.py

ruff check tools/gates/v3_gateb1_metrics.py tools/gates/v3_gateb1_stochastic.py tools/gates/v3_gateb1_fsdp_capture.py tools/gates/v3_gateb1_dcp_transient.py tools/gates/test_v3_gateb1_metrics.py tools/gates/test_v3_gateb1_stochastic.py tools/gates/test_v3_gateb1_fsdp_capture.py tools/gates/test_v3_gateb1_dcp_transient.py

Expected 68 CPU synthetic tests PASS. The author's local environment passed 68 with torch CPU and py_compile, but Ruff was unavailable.

Verify these independently:
- All optimizer-selected FQNs in Generation/Action/Local covered; per-FQN gradient, FP32 DeltaParameter, DeltaM1, DeltaM2 and absolute moments; missing FQN, missing/None grad, skipped step, wrong shard identity, nonfinite, bad dtype or wrong tiny update must FAIL.
- FSDP read-only snapshot before/after optimizer boundary never mutates model; requires loaded FP32 master-or-parameter and FP32 Adam moments; rank and shard identity retained.
- P0 fixed vision/action sigma, P1 production-equivalent waver/shift sigma sampled per consumer, keyed eps independent of reorder and RNG domain; source B0 CFG canonical seed is cfg_dropout / caption / python_cfg; condition_mask is a separate site. All unknown distributions and incomplete diffusion_forcing plans fail CLOSED.
- Actual GPU model-site hooks and full 8-rank FSDP DCP loading are NOT implemented: never call this B1 GPU-ready.

Submit ONE report DS_PRO_V3_GateB1_S1_CPU_metrics_stochastic_capture_2026-10-14.md with SHA, test counts, Ruff/compile, negative tests and first errors; return for ONE GPT incremental review. No full V3 audit.

Remaining separately scoped B1 implementation: strict 4-component iter1300 native DCP load, transient Local sidecar digest translation and 2-step GA2 direct callbacks, complete sigma/epsilon/CFG site injection, real 8xH100 Full×P0/P1 and Terminal×P0/P1. Numeric criteria not ratified by Owner. B1 GPU, Gate M, Formal30k HOLD; B0 CLOSED.

Additionally validate the new strict DCP transient seam using CPU fake Checkpointer only. It must require all five components (model/optim/scheduler/trainer/dataloader), same-job strict resume, exact original iter1300 path, callback exactly once, and source/target rank0 digest conversion in memory; restore callback method on failure. Do not load real DCP or initialize a model. Confirm hash snapshot mocks reject tampering and no DCP is written. CPU test count 68. This **does not constitute real DCP load PASS**.
