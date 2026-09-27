# V3 Stage B2-C R1-A FSDP Local Scan — Implementation Record

- Gate `V3-STAGE-B2C-R1-FSDP-LOCAL-SCAN`，状态 `REVIEW`；此记录不是 closure。
- 唯一设计 authority：root `b5404e9896892b2156e2cca11ef64db871b34def` 的 `PSM-WMA_V3_stage_b2c_r1_fsdp_local_scan_remediation_design_v0.1_2026-09-27.md`。
- 被整改的 harness formal pair：root `3c125a51af39bfcadeeeb02f83795784e23a1d66` / child `7de65c8e752c47359786e5ff2535a8d3cd5ddced`。run01 原始 Evidence `artifacts/v3/stage_b2c_4090_s1/run01/` 未修改或重跑。
- 本次 child `558f364efaf6704c9d65037c17ec250a9331be8a`，已推送 `v3-local-ttt`；root Gitlink 指向该 SHA。ChatGPT 设计/审核；用户 owner/最终裁决；cx 实现；ds 执行/测试。

## 实现

child 只修改 `cosmos_framework/model/generator/mot/` 下四个生产文件：`cosmos3_vfm_network.py` 新增模型持有的 `scan_local_memory`，它调用同一 `local_memory_runtime.encoder/core`；`parallelize_vfm_network.py` 在 root FSDP 包装且 Local 启用后注册该 forward method；`local_memory_segment_adapter.py` 接受可选模型 scan callable；`local_memory_native_segment.py` 让 production relay 走该 callable，并在 Local 参数为 DTensor 而缺少注册能力时提前拒绝。另新增 `local_memory_fsdp_scan_test.py`。

无 Local 参数副本、ignored params、post-DCP 参数替换、inference-mode shortcut。B0 sidecar/transaction、B2-B serial gradient relay、Local 165312 slow 参数 inventory、harness 样本与资产路径保持不变。

## CPU/static Evidence

在 `/disk/rl/worktrees/cosmos-framework-v3`，使用现有 V3 `.venv/bin/python`、`CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu LD_LIBRARY_PATH='' PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`，运行 B0/B1/B2-A/B2-B/B2-C harness、新 R1-A 与 VFM parallelization 共十文件 `pytest -c /dev/null --noconftest -p no:cacheprovider -m 'not GPU' -q --disable-warnings`：**205/205 PASS，4 GPU tests deselected**。测试覆盖注册开关/次数、模型对象 identity、S0/terminal padding、输出/梯度与直接 B0 路径一致、成功提交与失败不发布、缺注册的 DTensor fail-closed。

五个改动文件 Ruff format PASS；除 `cosmos3_vfm_network.py` 提交前已存在的 I001 import 排序债务外，Ruff clean。该文件排除 I001 后 clean，本次未重排整个 upstream import block。child/root `git diff --check` PASS。

## 后续边界

本轮无 GPU、R1-B tiny micro-smoke、完整 RTX4090 S1、trainer、DCP save、eval 或 server。R1-A CPU/static 结果不能证明实际 FSDP2 CUDA 生命周期；需 fresh review 后才能按设计进入 R1-B，run02 仍需另行授权。
