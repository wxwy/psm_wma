# V3 Stage B2-C R1-B Tiny FSDP Micro-Smoke — Harness Implementation

- Gate `V3-STAGE-B2C-R1B-TINY-FSDP-MICRO-SMOKE`，状态 `REVIEW`；此记录不构成 GPU 执行批准或 closure。
- 唯一设计 authority：root `544bbe0976aa60e935eee431350b20f38c47f28c` 的 `PSM-WMA_V3_stage_b2c_r1b_tiny_fsdp_micro_smoke_design_v0.1_2026-09-27.md`。
- R1-A closure formal pair：root `cae1c4bf5d681f93228a9b1a5c74e14d1b5acee4` / child `558f364efaf6704c9d65037c17ec250a9331be8a`，verdict `APPROVE_TO_CLOSE_V3_STAGE_B2C_R1_FSDP_LOCAL_SCAN`。
- 本轮 child `8029b5ff002a350d22ee955db0463cc2e2d3665a` 已推送 `v3-local-ttt`；root Gitlink 指向该 SHA。ChatGPT 设计/审核；用户 owner/最终裁决；cx 实现；ds 执行/测试。

## 范围

child 只新增 `examples/psm_wma_local_fsdp_scan_micro_smoke.py` 与对应 `_test.py`，不改 production。tiny owner 只持有 `LocalMemoryRuntime`、`local_memory2llm`、`local_memory_modality_embed` 共 165312 个 Local 参数。GPU 路径限定 WORLD_SIZE=1/rank0，使用训练模式 `ParallelDims(1,1,1,cp=1,cfgp=1)`、CUDA FP32 master、root `fully_shard` 与 `MixedPrecisionPolicy(param_dtype=BF16,reduce_dtype=FP32,cast_forward_inputs=False)`，并注册 `scan_local_memory`。它检查 FSDP 后 DTensor 参数、普通 Tensor evidence、S0/present/fast-state 合同及两项非零 Local 梯度，按阶段记录 CUDA allocator 统计，失败写 JSON 并销毁所创建进程组；不执行 optimizer step。

不实例化或读取 Edge、VAE、DCP、RoboCasa；不使用 `.to_local()`、ignored params、inference mode 或 FSDP 关闭路径。运行时要求 `PSM_WMA_V3_ROOT`，从当前 Git HEAD 与 root Gitlink 锁定 formal pair；输出目录必须全新。

## CPU/static Evidence

- V3 `.venv/bin/python`，`CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu LD_LIBRARY_PATH='' PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1` 下，B0/B1/B2-A/B2-B/B2-C/R1-A/R1-B 十一文件隔离 suite：**216/216 PASS**，4 项 GPU 测试 deselected。
- 独立 `--preflight --output /tmp/cx_v3_b2c_r1b_preflight_20260927_01`：PASS；`result.json` 显示 165312 参数和训练模式 DP enabled，`cuda_memory_trace.json` 为空。预检不初始化 CUDA/进程组。
- 两个新增文件 Ruff check/format PASS；child 与 root `git diff --check` PASS。

## 后续执行边界

GPU micro-smoke 尚未运行。fresh review 后才可由 ds 使用一处全新 `artifacts/v3/stage_b2c_r1b_micro/<unique-run>/` 目录执行单次 RTX4090 命令，并提交 result/memory/gradient Evidence。该结果还需独立审核；即使 R1-B 通过，也不自动授权 B2-C run02。run01 原始 Evidence 未改、未重跑。
