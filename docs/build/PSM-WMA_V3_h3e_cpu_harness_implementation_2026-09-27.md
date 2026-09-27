# V3 H3-E CPU harness 实施记录（2026-09-27）

- 设计依据：`PSM-WMA_V3_h3e_8xh100_integration_smoke_design_v0.1_2026-09-27.md`；child 实施提交 `6c7b1333c94773b2fb6940b530a63eb74b82a753`，root formal SHA 以包含本记录的提交为准。Gate 保持 `IN_PROGRESS`，未运行 GPU。
- child 变更：`examples/psm_wma_robocasa_h100.py`、对应测试，以及 `GroupedLocalMemoryTrainer` 可选 observer（仅 H3-E launcher 启用）。Stage-A one-step DCP warm-start 只 skip `net_ema.` 与 `local_memory`；同 job 恢复由现有 DCP 自动完整载入。8×H100 FSDP、Edge host+Local 165312、GA2×T16、raw15/chunk32/33、18 类 catalog 均 fail-closed；每 rank 保存 loss/梯度/CUDA 显存事件 JSONL、参数清单/提交状态与 DCP/next-identity JSON。
- CPU 验证：13 文件 244/244 + 三文件 23/23，最终观测/DCP 小改定向 13/13；Ruff/format、两仓 diff-check PASS。真实资产诊断 preflight PASS（未提交时仅临时绕过 pair 锁）：18 类 9036 train episode、8-rank 不重不漏、manifest digest `a8cad3f053232b348ea155f15bf79c2c9cf807dedcf39b89e246b17e43f283df`、Stage-A DCP metadata 549 键、CloseFridge ep0 的 8 consumer batch ABI；日志 `/tmp/cx_v3_h3e_preflight.log`。该诊断不代替 formal pair CLI preflight。

ds 在 child checkout 与 root Gitlink 均为 formal pair 后，从 `/disk/rl/worktrees/cosmos-framework-v3` 执行以下命令；`<ROOT_SHA>`、`<CHILD_SHA>` 必须替换成完整提交号，`<OUTPUT_ROOT>` 必须是 root worktree 外的新目录，fresh 与 resume 使用同一值：

```bash
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 LD_LIBRARY_PATH=/disk/rl/worktrees/cosmos-framework-v3/.venv/lib/python3.13/site-packages/nvidia/cu13/lib PYTHONPATH=. .venv/bin/python examples/psm_wma_robocasa_h100.py --phase fresh --preflight --output-root <OUTPUT_ROOT> --expected-root <ROOT_SHA> --expected-child <CHILD_SHA>

PYTHONPATH=. COSMOS_DEVICE=cuda HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 LD_LIBRARY_PATH=/disk/rl/worktrees/cosmos-framework-v3/.venv/lib/python3.13/site-packages/nvidia/cu13/lib .venv/bin/torchrun --standalone --nproc-per-node=8 examples/psm_wma_robocasa_h100.py --phase fresh --output-root <OUTPUT_ROOT> --expected-root <ROOT_SHA> --expected-child <CHILD_SHA>

PYTHONPATH=. COSMOS_DEVICE=cuda HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 LD_LIBRARY_PATH=/disk/rl/worktrees/cosmos-framework-v3/.venv/lib/python3.13/site-packages/nvidia/cu13/lib .venv/bin/torchrun --standalone --nproc-per-node=8 examples/psm_wma_robocasa_h100.py --phase resume --output-root <OUTPUT_ROOT> --expected-root <ROOT_SHA> --expected-child <CHILD_SHA>
```

GPU 门：fresh 必须有每 rank 32 native forward/backward、一次 optimizer/fast-state commit、有限 loss/Local 梯度、iter1 DCP；resume 必须读取同 job iter1 的全部 rank-pkl/slow+optimizer/scheduler/trainer RNG，完成 iter2 并保存 DCP，记录 next identity 与 committed digest。任何 FAIL/OOM 保留原始 Evidence；cx 修复 blocker 后再重新取证，不自动缩小几何。H3-F 正式训练 cadence 仅在本门真实通过后决定。
