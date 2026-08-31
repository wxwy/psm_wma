# R09-B2 P3 GPU-only Optimizer Inventory Gate 方案 v0.1

**状态**：DRAFT；仅请求方案审核，禁止执行 GPU。

## 目标

解除 P0 中“实际 full-recipe optimizer membership”这一项阻塞。该 Gate 只在单卡 GPU 上构造同一 LIBERO recipe 的 recurrent 与 `ttt_fast_weight` 两个 backend，读取真实 model parameter、optimizer param-group/state 和只读 DCP-compatible state schema；不训练。

## 冻结执行面

- 单进程、`CUDA_VISIBLE_DEVICES=<单卡>`；无 distributed/FSDP 初始化、无 dataloader、无 VAE/tokenizer/data/base-checkpoint 加载。
- 仅允许 model/optimizer 构造、`named_parameters`、`named_buffers`、optimizer `param_groups`/`state`、`model.state_dict()` 和 `optimizer.state_dict()` 的只读 schema 遍历。
- 禁止 forward、backward、`optimizer.step`、scheduler step、DCP save/load、checkpoint 写入和任何训练 callback。
- 运行前记录 GPU UUID、显存水位、root/submodule/Gitlink、recipe/collector/verifier/source SHA；运行后断言 GPU 无新 checkpoint 文件且进程退出。

## 机器可验证的 PASS 合同

1. verifier 内置不可由 artifact 覆盖的 `ALLOWED_RECURRENT_ONLY_PREFIXES=("local_history_runtime.recurrent_backend.",)`；artifact 的声明必须逐项相等。
2. `selector_optimizer_exclusions` 必须为空；resolved selector stable-name 集合必须与实际 optimizer membership 全等。
3. 每个 optimizer object 反向映射唯一 model parameter；group 的 stable name/numel/dtype/lr/weight_decay 全等；selected trainable 参数无遗漏或重复。
4. optimizer state 逐 stable name 记录 eligibility、state keys 和 tensor metadata；不执行 step 时 initial state 为空只能标为 `not_materialized=true`，并与 eligibility 集合一致。
5. 读取 `model.state_dict()` 与 `optimizer.state_dict()` 的只读 persistent-key schema；五个 TTT runtime 成员 `W`、`pending_evidence`、`last_evidence`、`initialized`、`segment_progress` 不得出现。
6. recurrent/TTT 共同 selector/optimizer/DCP state 必须相等；仅内置 recurrent prefix 可作为 recurrent-only 差异。任何 TTT-only 或额外 recurrent-only key 失败。

## 资源、停止条件与产物

- 资源上限：单卡、无 batch、无训练；若显存超过 24 GiB、出现权重/checkpoint/forward/backward/step、或任一 schema 不可只读取得，立即退出为 `BLOCKED` 并保留 JSON/log。
- 产物：`artifacts/g0/r09/b2/p3_gpu_inventory.json`、对应 verifier JSON、只读日志和 D005-lite execution record。
- PASS：两 backend 的上述六项全部通过。FAIL：任何 hard gate 不成立。BLOCKED：无法在冻结执行面取得真实对象；不得 synthetic fallback。

## 审核请求范围

本方案仅请求 `APPROVE_TO_IMPLEMENT_GPU_ONLY_P3_GATE`。即使批准实现，GPU 执行仍须另行请求 `APPROVE_TO_RUN_GPU_ONLY_P3_GATE`。不授权 B2-T、P4/P5、训练、评测、推理、closed-loop、SR、多卡、长训或 backend freeze。
