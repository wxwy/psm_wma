# R09-B2 P3 GPU-only Optimizer Inventory Runbook v0.1

**状态**：REVIEW。仅申请一次有界 GPU inventory；未获三方 `APPROVE_TO_RUN_GPU_ONLY_P3_GATE` 前不得执行。

## 目的与边界

本 Gate 只在同一张 GPU 上分别构造 `recurrent` 与 `ttt_fast_weight` 的生产 model/optimizer，并读取 `ModelWrapper.state_dict()` 与 `OptimizersContainer.state_dict()` 的 schema。它用于关闭 B2 的实际 optimizer-membership 阻塞；不读取训练数据或 checkpoint，不运行 dataloader、VAE、forward、backward、optimizer/scheduler step、训练、评测或推理。

唯一例外是 recipe 实际的本地 Edge processor 构造。collector 在任何 HF/Transformers 导入前强制本地路径、六个配置资产与 offline 环境；任一缺失或远端 binding 都 fail-closed。

## 冻结输入与资源

- 工作目录：`/disk/rl/psm_wma`。
- Python：`/disk/rl/psm_wma/cosmos-framework/.venv/bin/python`。
- 单卡：`CUDA_VISIBLE_DEVICES=0`；worker 要求恰好一张可见 CUDA 卡，禁止 distributed。
- 显存 stop gate：每个 backend 在 model、optimizer、两份 production DCP schema 后均检查 peak，超过 **28 GiB** 立即失败。attempt-3 已在 `OptimizersContainer.state_dict()` 后实测 25.28 GiB 并被原 24 GiB gate 终止；28 GiB 只为同一 inventory 路径保留约 2.7 GiB 余量，不扩大允许操作范围。
- Edge processor：`/localdisk-tmp/models/Cosmos3-Edge-Policy-DROID`。
- Base DCP 路径：`/localdisk-tmp/models/Cosmos3-Edge-Policy-DROID-dcp`（仅环境/recipe 路径；禁止 load）。
- Wan VAE 路径：`/localdisk-tmp/models/wan22_vae/Wan2.2_VAE.pth`（仅环境/recipe 路径；`load_vision_tokenizer=false`，禁止 VAE 构造）。
- LIBERO 根：`/disk/rl/data/LIBERO_LeRobot_v3`（仅环境/recipe 路径；禁止 dataloader/视频/latent cache 读取）。
- TOML：`cosmos-framework/examples/toml/sft_config/action_policy_libero_edge_all.toml`。
- 运行令牌：精确字符串 `APPROVE_TO_RUN_GPU_ONLY_P3_GATE`；collector 拒绝其他值。

## 唯一执行命令

```bash
cd /disk/rl/psm_wma
CUDA_VISIBLE_DEVICES=0 \
PYTHONPATH=/disk/rl/psm_wma/cosmos-framework \
EDGE_POLICY_CHECKPOINT=/localdisk-tmp/models/Cosmos3-Edge-Policy-DROID \
WAN_VAE_PATH=/localdisk-tmp/models/wan22_vae/Wan2.2_VAE.pth \
BASE_CHECKPOINT_PATH=/localdisk-tmp/models/Cosmos3-Edge-Policy-DROID-dcp \
LIBERO_ROOT=/disk/rl/data/LIBERO_LeRobot_v3 \
/disk/rl/psm_wma/cosmos-framework/.venv/bin/python \
  tools/g0/collect_r09_b2_p3_gpu_inventory.py \
  --root /disk/rl/psm_wma \
  --toml cosmos-framework/examples/toml/sft_config/action_policy_libero_edge_all.toml \
  --output artifacts/g0/r09/b2/p3_gpu_inventory_attempt5/p3_gpu_inventory.json \
  --edge-checkpoint-path /localdisk-tmp/models/Cosmos3-Edge-Policy-DROID \
  --wan-vae-path /localdisk-tmp/models/wan22_vae/Wan2.2_VAE.pth \
  --base-checkpoint-path /localdisk-tmp/models/Cosmos3-Edge-Policy-DROID-dcp \
  --libero-root /disk/rl/data/LIBERO_LeRobot_v3 \
  --d005-record artifacts/g0/r09/b2/p3_gpu_inventory_attempt5/p3_gpu_inventory_d005.json \
  --approved-run-token APPROVE_TO_RUN_GPU_ONLY_P3_GATE \
  --max-peak-gib 28
```

顶层 collector 只按固定顺序派生两个独立子进程：`recurrent` 与 `ttt_fast_weight`。任一子进程非零、未写合法 JSON 或 JSON `status!=PASS` 时，父进程先写 aggregate/D005 和已获得的 stdout/stderr/partial JSON，再立即返回；后续 backend 不会启动。它们的 JSON 分别写为 `p3_gpu_inventory_recurrent.json` 与 `p3_gpu_inventory_ttt_fast_weight.json`；顶层 aggregate 与 D005 写入上述 attempt-5 路径。parent 会在写 D005 前拒绝已存在或 Git 已跟踪的 aggregate/D005/backend 路径，既有 attempt evidence 不得覆盖。不得追加 `--worker-backend`，不得重试、改参数或更换 GPU。

每个 isolated worker 在 production model config 解析前仅内部切换到 `root/cosmos-framework`，使 recipe 的相对 model JSON 路径与常规框架启动语义一致；TOML、环境路径和 D005 仍为命令中冻结的绝对/根目录记录。

## 判据与失败分流

PASS 要求：两个 worker 均 `PASS`；GPU/world-size/offline processor/source/D005 provenance 全部匹配；生产 optimizer group、model DCP、optimizer DCP 的 stable-name membership 一致；TTT five-member state 不持久化；cross-backend diff 只含 verifier allowlist 的 recurrent-only 参数。

任一非零退出、`BLOCKED`/`FAIL` JSON、峰值超过 28 GiB、GPU 不止一张、任何网络/远端 tokenizer、任何数据/VAE/checkpoint I/O、任何 forward/backward/step 都是 FAIL：立即停止，不重跑，保留 stdout/stderr、D005 与已写 JSON 供审计。

运行后只允许执行同提交下的 verifier，并向 ChatGPT、MM、Kimi 申请 closure；不得由此推进 B2-T、P4/P5 或其他 Gate。
