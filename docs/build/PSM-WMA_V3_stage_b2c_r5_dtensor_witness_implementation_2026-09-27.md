# V3 B2-C R5 DTensor witness implementation（2026-09-27）

- Gate: `V3-STAGE-B2C-R5-DTENSOR-WITNESS`；CPU/static 完成，待 ds 单次 RTX4090 run06。
- run05 execution pair root `f782f2cc351fabded26bab23588758f899e3256a` / child `8984ceb065df231da6fdf9708322b7eae29af08a`；原始 `artifacts/v3/stage_b2c_4090_s1/run05/` 保持 immutable。
- 实现 child：`a9aca770fd39b8eed9c456fc2dbdb8867189e78e`，仅修改 `examples/psm_wma_robocasa_local_s1.py` 与对应测试。

## run05 实证与根因

run05 完成 Stage-A DCP host load、Local-only 165,312 参数 optimizer 初始化、B0 scan，以及 16/16 原生 consumer forward/backward 和 relay_backward；峰值显存未 OOM。终止于 harness 的 `optimizer.step` 包装器内 `_witness`：对 FSDP2 `DTensor` 梯度调用 `torch.count_nonzero`，PyTorch 报 `aten.count_nonzero.default does not have a sharding strategy registered`。真实 optimizer step 尚未调用，fast-state/frontier 未 commit。这是诊断算子问题，不是 Local 梯度/原生 loss 的失败；不重跑 run05。

## 最小修复与验收

仅在单 rank B2-C harness 的 witness 中对 DTensor 使用 `to_local()`，再执行 finite、nonzero、norm 和 host/Local 参数前后比较。Local 核心、梯度 relay、FusedAdam、checkpoint、dataset、Stage-A/资源常量均未改变。CPU/Gloo 真实 DTensor 测试验证五个 Local 梯度 finite/nonzero、全零/NaN 拒绝、冻结 host 拒绝及本地参数比较；十文件合并 suite **209/209 PASS**，新增两文件 Ruff/format 与 child/root diff-check PASS。R4 真实资产 CPU preflight PASS 仍适用；R5 未运行 GPU。

## ds 单次 run06 交接

前置：root Gitlink、root/child checkout 与本次正式 pair 完全一致；`run06/` 不存在。工作目录 `/disk/rl/worktrees/cosmos-framework-v3`，现有 V3 `.venv`，1×RTX4090 24GB。输入为冻结 Stage-A one-step DCP/config、CloseFridge ep0/cursor0 raw15/RGB、对应 Wan latent cache。无外网、无自动重试/降级；T=16、K=4、chunk32/33 帧、Local-only 165,312 参数不变。

```bash
env -u WORLD_SIZE -u RANK -u LOCAL_RANK CUDA_VISIBLE_DEVICES=0 COSMOS_DEVICE=cuda LD_LIBRARY_PATH=/disk/rl/worktrees/cosmos-framework-v3/.venv/lib/python3.13/site-packages/nvidia/cu13/lib PYTHONPATH=. /disk/rl/worktrees/cosmos-framework-v3/.venv/bin/python examples/psm_wma_robocasa_local_s1.py --output /disk/rl/worktrees/psm_wma-v3/artifacts/v3/stage_b2c_4090_s1/run06
```

保存新目录的 `result.json`、`cuda_memory_trace.json`、`stdout_stderr.log`。PASS 要求 16 个 finite native loss、五个 Local 梯度 witness finite/nonzero、恰一次真实 optimizer step、host 不变、Local 桥权重改变、fast-state/frontier 恰一次 commit、无 OOM。任何 FAIL 立即停止并保留原始证据，不重跑；ds 不改代码或提交。B2-C 是否关闭以实际 GPU Evidence 判定，run06 不授权 8×H100 正式训练。
