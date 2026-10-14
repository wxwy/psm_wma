# GPT → DS_PRO: Gate B1 native GA2 + scoped model-site RNG implementation, ONE CPU-only Gate

Date: 2026-10-14
Role: DS_PRO validation-only; no production changes.
Candidate branch: wxwy/psm_wma:v3-gateb1-numeric-implementation-20261014
Candidate EXACT CODE SHA: 5aa79a73a4c6f1a424fa0a9476e1ce52ae9e9361
Pre-existing B1 numeric/DCP/capture branch parent: 778eb096d700cabd7be93b1ab2313382bbf2ca7c
Frozen B1 SOURCE Index8 Root b159f45906f7261d028aecc226ab7f2bb9807eb9 / child 937066ffd90f2bf783ad4fbb4909e9c0b8922982.
Frozen TARGET Packed128 Root c4731bca1a590663db88bd6cd74dbcf9fd513a85 / child c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686.

**One narrow CPU-only implementation acceptance, NOT permission to run native GPU.** Keep existing B0 CLOSED. No full V3 audit; no repeated 451GB offline dataset acceptance; no full preflight; no CUDA/torchrun/real model/DCP load; no migrations or Formal30k.

## Code under test

Six new exact-path Python files, all under tools/gates:
- v3_gateb1_native_driver.py: NativeTwoWindowDriver calls the frozen production GroupedLocalMemoryTrainer.training_step directly for GA0/GA1 across 1300→1301 and 1301→1302; scoped model.training_step, trainer._observe_grouped and _zero_grad instance hooks; verifies exact Native forward counts and Consumer provenance; captures pre_optimizer gradients and post_optimizer moments BEFORE actual zero_grad; source native index-major/target slot-major and true partial count; native read-only initialization seam build_loaded_native_bridge.
- v3_gateb1_model_sites.py: instance-specific _get_train_noise_level_vision/action and _add_noise_to_input hooks, per native ConsumerKey. TorchDispatchMode redirects ONLY native aten.randn calls inside noising (no global torch.randn monkeypatch). Requires exact vision/action shapes, resolved video distribution, per-consumer shift, model iteration, no extra unknown sensor/random sites, and checks hook counts/restores on errors.
- v3_gateb1_producer_cfg.py: per-request native Transform text CFG uses B0 canonical scoped_python_cfg_rng on ConsumerKey; serial num_workers=0 required, transform and producer methods restored in finally.
- Corresponding test_v3_gateb1_native_driver.py, test_v3_gateb1_model_sites.py, test_v3_gateb1_producer_cfg.py.

## Commands (isolated clean checkout)

Use the existing Python 3.13 / torch 2.10 CPU project venv:
HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES='' LD_LIBRARY_PATH='' PYTHONDONTWRITEBYTECODE=1

python -m py_compile tools/gates/v3_gateb1_native_driver.py tools/gates/v3_gateb1_model_sites.py tools/gates/v3_gateb1_producer_cfg.py tools/gates/test_v3_gateb1_native_driver.py tools/gates/test_v3_gateb1_model_sites.py tools/gates/test_v3_gateb1_producer_cfg.py

python -m pytest -q tools/gates/test_v3_gateb1_native_driver.py tools/gates/test_v3_gateb1_model_sites.py tools/gates/test_v3_gateb1_producer_cfg.py

ruff check --no-cache tools/gates/v3_gateb1_native_driver.py tools/gates/v3_gateb1_model_sites.py tools/gates/v3_gateb1_producer_cfg.py tools/gates/test_v3_gateb1_native_driver.py tools/gates/test_v3_gateb1_model_sites.py tools/gates/test_v3_gateb1_producer_cfg.py

Expected local author result: 23 passed, py_compile exit0; Ruff NOT locally executed and remains DS Gate item.

Negative cases: missing iter1300 Local pending restore; wrong FSDP8 B8 T16 GA2; missing Native calls; mismatched source-index / target slot-major position; S0 prefix misbinding; missing/extra epsilon/vision sigma/noiser; unknown LiDAR/Radar/Sound; model video sigma shift/distribution drift; out-of-range CFG frame; producer workers>0; required rollback of all instance methods on exceptions. Distinguish fake CPU event simulation from genuine FSDP8 execution.

## B1 remaining before any GPU authorization

This code is a real *instance-hook/GA2 execution seam* but **not yet a fully assembled stand-alone 8-rank CLI** with an accepted-index no-scan datasource for the two frozen child implementations. Full 4-component native DCP load is implemented as a helper but only CPU fake-tested; FSDP8 cannot be claimed. Actual model stochastic coverage outside _add_noise_to_input and source/target BF16 attention/numerical differences still need an independent readiness audit. Owner must ratify numeric thresholds before GPU.
Terminal×P0/P1 and Full×P0/P1 all mandatory; no B1 GPU, Gate M, Formal30k authorized.

Give ONE report DS_PRO_V3_GATEB1_NATIVE_GA2_MODELSITE_CFG_CPU_2026-10-14.md with actual exact HEAD, six blob hashes, 3 exit codes, test counts, and file:line first blocker if any. Do not edit any production/Harness files in DS role.

Implementation cleanup after initial coding: the final code SHA above removes unused code/import-like locals from two production modules and one test; author reran 23 CPU mock tests and py_compile successfully, all six pushed Git blobs matched local git hash-object. DS verifies Ruff independently. Later docs-only commits do not change implementation SHA.
