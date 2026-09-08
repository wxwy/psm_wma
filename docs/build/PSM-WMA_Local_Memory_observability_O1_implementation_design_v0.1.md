# PSM-WMA Local Memory Observability O1 Implementation Design v0.1

**日期**：2026-09-08
**状态**：docs-only；待三方同 SHA 审核
**前置**：observability v0.3 root=`7a3f023efcc82446c9bf930a302c5a3edd0043f9`、context child=`333792e845fe3b15ba4d8af8f34f704de2a79fa2` 获 MM、DS `APPROVE_TO_IMPLEMENT_R09_B_TTT_OBSERVABILITY_DESIGN`

## 1. 目的与范围

O1 只将既有 `NormMonitor` 的参数硬编码选择逻辑扩展为显式 selector group，复用其 local-shard L2/max、现有 `dist.all_reduce`、rank0 W&B 和 S3 sink。它不创建 Local telemetry callback、trace sink 或 validator。

允许修改的 child 文件精确为：

```text
cosmos_framework/callbacks/norm_monitor.py
cosmos_framework/callbacks/norm_monitor_test.py
```

不得修改 callback defaults、TOML/Hydra recipe、trainer、model/runtime、optimizer、checkpoint、dataset、W&B backend 或任何 Local Memory 计算路径。不得执行真实 I/O、CUDA、GPU、torchrun、训练、评测或推理。

## 2. 已验证复用入口

`NormMonitor._get_named_parameters()` 已处理 module traversal，`_compute_l2_stats()` 已将 DTensor 转为 local shard，`_compute_and_log_stats()` 已将 shard squared sums/max 通过 existing collective 聚合，并只由 rank0 交给 existing W&B/S3 sink。当前缺口仅是 `_should_track_param()` 固定为 `moe_gen` 或 `k_norm_und_for_gen`，因此 Local slow inventory 无法进入现有统计。

canonical Local slow inventory 的唯一名称来源是 `config_checkpoint_contract.SELECTORS`：

```text
local_history_runtime.encoder.
local_history_runtime.recurrent_backend.
local_memory2llm.
local_memory_modality_embed
```

O1 不读取 fast state、不读取 batch/Local token/payload，不调用 `SegmentBatch`、scheduler、fast update、read 或 write。

## 3. Selector-group contract

`NormMonitor` 新增 optional construction-time `parameter_selector_groups`。其值为 group name 到非空 name-prefix tuple 的 immutable copied mapping；`None` 是默认值，必须保留当前 `_should_track_param()` 的 legacy `moe_gen/k_norm_und_for_gen` 行为、metric key 和聚合数值。

提供 exported immutable constant `LOCAL_SLOW_SELECTOR_GROUPS`：

```text
encoder  -> ("local_history_runtime.encoder.",)
core     -> ("local_history_runtime.recurrent_backend.",)
projector-> ("local_memory2llm.",)
modality_embed -> ("local_memory_modality_embed",)
```

custom group mode 的选择规则：

1. 仅 prefix match 的 parameter 属于该 group；未匹配 parameter 忽略；
2. 每个 parameter 必须最多匹配一个 group；任一 overlap 在 construction 前 fail closed；
3. group name 只能由 ASCII lower-case、digit、`_` 组成；prefix 不能为空；
4. selector 映射复制后不可受调用方 mutation 影响；
5. `net_ema` 名称在 legacy 与 custom mode 均排除。

Custom group mode 只增加按 group 的 shard aggregate；不改变 legacy aggregate 的计算、也不重复对同一 parameter 建立额外 collectives。

## 4. 指标与数据流

对每个 selected group，收集现有 shard-local `sq_sum`，以及存在 grad 时的 grad `sq_sum`；每 group 每统计周期恰好一次 SUM all-reduce。rank0 输出：

```text
local/slow/encoder_param_l2
local/slow/encoder_grad_l2                 # 仅至少一个 selected grad 存在时
local/slow/core_param_l2
local/slow/core_grad_l2
local/slow/projector_param_l2
local/slow/projector_grad_l2
local/slow/modality_embed_param_l2
local/slow/modality_embed_grad_l2
```

L2 为 `sqrt(sum(local shard float32 squares across ranks))`；不得 gather/full_tensor parameter。不存在 grad 的 group 不输出 grad key，不能用 0 伪装“已观测零梯度”。现有 `total_param_l2_norm` / `total_grad_l2_norm`、per-parameter stats、activation hooks、logging cadence 和 `wandb.run is None` 行为保持不变。

O1 不启用 Local selectors：调用方显式传入 `LOCAL_SLOW_SELECTOR_GROUPS` 才产生 `local/slow/*`；recipe enablement 属 O5。

## 5. CPU/static acceptance

相邻 CPU tests 必须只测选择与 scalar aggregation helper，不初始化 CUDA、distributed process group、W&B 或 S3：

1. `None` selector groups 保留 legacy selected/unselected/EMA exclusion；
2. `LOCAL_SLOW_SELECTOR_GROUPS` 对四类 canonical names 精确归组，未知/fast-state name 排除；
3. overlap、空 prefix、非法 group name 均 fail closed；
4. 调用方后续修改原 mapping 不改变 monitor frozen groups；
5. synthetic parameter/gradient fixtures验证每 group L2、无 grad 不输出 grad metric、一个 parameter 不重复计数；
6. existing legacy `NormMonitor` tests（如有）保持 PASS。

代码验收：相关 pytest、两文件 `py_compile`、child/root `git diff --check` PASS。任何 CPU fixture 不得将“测试通过”解释成实际 distributed/GPU logging 或训练已验证。

## 6. 禁止与下一步

本设计批准后仅允许 O1 两文件 CPU/static implementation。O2 token/fast-state telemetry、O3 trace、O4 validator、O5 callback/recipe enablement，以及所有 production、真实 I/O、GPU/CUDA/torchrun、训练、评测、推理、P4/P5、B2-T、LIBERO4IN1 仍须独立 Gate。
