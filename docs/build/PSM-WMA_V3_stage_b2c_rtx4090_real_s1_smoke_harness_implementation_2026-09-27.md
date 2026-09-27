# V3 Stage B2-C RTX4090 Real S1 Smoke Harness — Implementation Record

- Gate: `V3-STAGE-B2C-RTX4090-REAL-S1-SMOKE`，状态 `REVIEW`；此记录不是 closure。
- 设计 authority：root `ced270eb07bbf9fac321e410f6d1992911d591cb`，`PSM-WMA_V3_stage_b2c_rtx4090_real_s1_smoke_design_v0.1_2026-09-27.md`。
- 前置 B2-B closure pair：root `81fa515593e7cd8e2d4f7d226efb915b17be3b5b` / child `bf6c80e679812b7d2881d6a54aa0b518299e3869`。
- 本次 child：`7de65c8e752c47359786e5ff2535a8d3cd5ddced`（已推送 `v3-local-ttt`）；root Gitlink 指向该 SHA。ChatGPT 设计/审核，用户 owner/最终裁决，cx 实现，ds 执行/测试。

## 实现范围

child 仅新增 `examples/psm_wma_robocasa_local_s1.py`、`examples/psm_wma_robocasa_local_s1_test.py`。harness 固定 CloseFridge ep0/cursor0、单 slot/T16、raw15、policy chunk32/33 frames；Stage-A one-step DCP 载入 host，缺失只允许 Local-Memory namespace 与禁用的 EMA。官方 RoboCasa v3 loader 提供 native RGB/state/raw15 policy payload，B1 H5 cached latent 只提供 Local evidence。复用 B2-B serial relay；Local-only optimizer 选中 165312 slow params，LR 5e-5。运行时记录 CUDA phase 和逐 consumer memory；异常/OOM 写失败 Evidence，不自动降低 T/K/chunk。

## CPU 验证

在 `/disk/rl/worktrees/cosmos-framework-v3` 以 V3 `.venv/bin/python` 执行八文件隔离 suite：**187/187 PASS**。命令：

```bash
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu LD_LIBRARY_PATH='' PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -m pytest -c /dev/null --noconftest -p no:cacheprovider -q examples/psm_wma_robocasa_local_s1_test.py cosmos_framework/model/generator/mot/local_evidence_test.py cosmos_framework/model/generator/mot/local_memory_segment_test.py cosmos_framework/model/generator/mot/local_memory_segment_adapter_test.py cosmos_framework/model/generator/mot/robocasa_latent_evidence_test.py cosmos_framework/model/generator/mot/robocasa_segment_producer_test.py cosmos_framework/model/generator/mot/memory_prefix_test.py cosmos_framework/model/generator/mot/local_memory_native_segment_test.py
```

新增两文件 Ruff check/format PASS；child 和 root `git diff --check` PASS。真实资产 CPU preflight PASS，Evidence：`/tmp/cx_v3_b2c_preflight_20260927_05/result.json`；Stage-A DCP 549 keys、episode 429 frames、16 个 raw15 native payload。命令：

```bash
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu LD_LIBRARY_PATH=$PWD/.venv/lib/python3.13/site-packages/nvidia/cu13/lib PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python examples/psm_wma_robocasa_local_s1.py --preflight --output /tmp/cx_v3_b2c_preflight_20260927_05
```

`LD_LIBRARY_PATH` 指向现有 V3 venv CUDA codec libraries，供 TorchCodec 的 **CPU 视频解码**加载；本次未启动 CUDA。CPU preflight 只验证资产、合同和 payload 准备，不验证模型 materialize、DCP 权重载入、反传或 RTX4090 显存。

## 待执行 Gate

真实 RTX4090 S1 需 fresh review 后由 ds 在独立进程执行，并提交 `result.json`、`cuda_memory_trace.json`、Local 梯度/参数 witness 与事务 witness。cx 本轮未运行 GPU、trainer、DCP save、eval 或 server；不声明 B2-C runtime PASS 或 closure。既有 `artifacts/v3/` 未纳入提交。
