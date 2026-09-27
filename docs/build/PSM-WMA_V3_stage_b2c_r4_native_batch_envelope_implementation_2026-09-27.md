# V3 B2-C R4 native batch envelope implementation（2026-09-27）

- Gate: `V3-STAGE-B2C-R4-NATIVE-BATCH-ENVELOPE`；状态：CPU/static 完成，待 ds 真实 RTX4090 S1 验证。
- 起点：run04 execution pair root `4c128e6ad104f736e4a6cfef63b39ba0b3d662a0` / child `f8b81133f22ab01197b7b36003207cf5cfeb2e41`；run04 原始 `result.json` 为 consumer0 `native_forward` 的 `TypeError: int + list`，保留不改、不重跑。
- 实现 child：`8984ceb065df231da6fdf9708322b7eae29af08a`，仅 `examples/psm_wma_robocasa_local_s1.py` 与 `_test.py`。

## 根因与改动

原 harness 直接把 `custom_collate_fn([payload])` 交给 `OmniMoTModel.training_step`，其 `text_token_ids` 等多条目字段仅有单层列表。正式 `JointDataLoader` 会执行 `_get_next_sample` 与 `_update_output_batch`，再交付每样本、每条目的双层封装；模型的 `_load_and_tokenize_text_data` 按该封装遍历。R4 在 harness 内复用这两个现有方法构造单 consumer native batch，并在真实资产 CPU preflight 逐项核对 text、RGB video、64D action、raw15 action_raw。未修改 common dataloader、OmniMoT、B0/B2-B、Stage-A 配置或算法常量。

## CPU/static Evidence

- V3 child `.venv`，GPU 不可见的十文件合并 suite：**208/208 PASS**；新测试调用真实 `OmniMoTModel._load_and_tokenize_text_data` 与 `PackedSequenceBuilder.pack_text_tokens`，覆盖 run04 的报错路径和 EOS 打包。
- Stage-A 合同独立进程：**24 passed、2 skipped、10 subtests passed**；与 Local 梯度 suite 分进程运行。
- 真实资产 CPU preflight：`/tmp/cx_v3_b2c_r4_preflight_20260927_01/result.json` 为 PASS；429 帧、16 个 payload、raw15，consumer0 152-token SHA256 与 run04 一致，CUDA trace 为 `[]`。
- 修改的两文件 Ruff check/format、child/root `git diff --check` PASS。未运行 GPU；CPU preflight 不证明 native backward 或 optimizer/fast-state commit。

## ds 单次 run05 交接

前置：root Gitlink 指向 child `8984ceb065df231da6fdf9708322b7eae29af08a`，root/child checkout 与提交号一致；确认输出目录不存在。工作目录 `/disk/rl/worktrees/cosmos-framework-v3`，使用该目录现有 `.venv`，1×RTX4090 24GB。输入为冻结 Stage-A one-step DCP/config、CloseFridge ep0/cursor0 raw15/RGB 与对应 Wan latent cache；不访问外网，不替换输入，不自动降级 T=16 或重试失败运行。

```bash
env -u WORLD_SIZE -u RANK -u LOCAL_RANK CUDA_VISIBLE_DEVICES=0 COSMOS_DEVICE=cuda LD_LIBRARY_PATH=/disk/rl/worktrees/cosmos-framework-v3/.venv/lib/python3.13/site-packages/nvidia/cu13/lib PYTHONPATH=. /disk/rl/worktrees/cosmos-framework-v3/.venv/bin/python examples/psm_wma_robocasa_local_s1.py --output /disk/rl/worktrees/psm_wma-v3/artifacts/v3/stage_b2c_4090_s1/run05
```

产物仅在新 `run05/`：`result.json`、`cuda_memory_trace.json`、`stdout_stderr.log`。PASS 要求 native 16 consumer 的 finite loss/Local gradients、恰一次 optimizer step、fast-state/frontier commit、host 不变且无 OOM；任一失败即停止并保留完整原始证据，不自动重跑。ds 仅执行和报告，不修改生产代码或提交。B2-C 是否关闭依据 run05 实际 Evidence 决定；此交接不授权 8×H100 正式训练。
