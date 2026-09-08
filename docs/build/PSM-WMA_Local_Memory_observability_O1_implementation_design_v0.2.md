# PSM-WMA Local Memory Observability O1 Implementation Design v0.2

**日期**：2026-09-08
**状态**：docs-only remediation；待三方同 SHA 审核
**取代范围**：本版只 supersede v0.1 的 §3--§5 selector-source、leaf-boundary 与 grouped grad aggregation/acceptance 描述；v0.1 的范围、legacy compatibility、禁止项和其余 acceptance 原样继承。

## 1. 前置与整改目标

v0.1 formal root=`024ade385887dfc3abc149df1cc30b3ae4fa8c06`/child=`333792e845fe3b15ba4d8af8f34f704de2a79fa2` 的 ChatGPT review `a3e3b6b` 给出 `REQUEST_CHANGES`：只归约 `grad_sq_sum` 不能区分全局没有 selected grad 和 selected grad 恰为零。本版只消除该分布式语义歧义；不授权 O1 实现或任何运行时动作。

未来允许的实现文件仍精确为：

```text
cosmos_framework/callbacks/norm_monitor.py
cosmos_framework/callbacks/norm_monitor_test.py
```

callback defaults、TOML/Hydra recipe、trainer、model/runtime、optimizer、checkpoint、dataset、W&B backend 和 Local Memory 计算路径均不在范围内。禁止真实 I/O、CUDA/GPU、torchrun、训练、评测、推理、P4/P5、B2-T 和 LIBERO4IN1。

## 2. Selector source 与匹配边界

`NormMonitor(parameter_selector_groups=None)` 必须保持 v0.1 的 legacy `moe_gen/k_norm_und_for_gen` predicate、EMA exclusion、metric key、数值及 collectives 不变。

custom mode 的 `LOCAL_SLOW_SELECTOR_GROUPS` 必须由 canonical `config_checkpoint_contract.SELECTORS` 的四个 inventory roots 派生或在 construction-time fail-closed 校验为与其相同的 immutable copied mapping，避免独立硬编码漂移：

```text
encoder        -> local_history_runtime.encoder.
core           -> local_history_runtime.recurrent_backend.
projector      -> local_memory2llm.
modality_embed -> local_memory_modality_embed
```

前三项是 module-prefix，只匹配 `name.startswith(root)`；`modality_embed` 是 `canonical_slow_inventory()` 的单一 leaf parameter，只匹配 `name == root`，不得以无尾点的裸 prefix 匹配其它参数。未匹配项忽略，`net_ema` 在两种模式均排除；任一 parameter 多组匹配、空 root、非法 group name 或外部 mapping mutation 均 fail closed。

## 3. 每组单 collective 的 packed payload

custom group mode 对每个 group 每统计周期恰好进行一次 `dist.all_reduce(..., SUM)`。该 collective 的 float32 packed local payload 固定为：

```text
[param_sq_sum, grad_sq_sum, grad_present_count]
```

- `param_sq_sum`：该 rank 所选 parameter local-shard float32 square sum；
- `grad_sq_sum`：仅对 `param.grad is not None` 的所选 parameter local-shard float32 square sum；
- `grad_present_count`：该 rank 中 `param.grad is not None` 的 selected parameter 数，作为 float32 的精确非负整数 witness。

rank0 在该 single SUM 后按全局 packed payload 输出：

```text
local/slow/<group>_param_l2 = sqrt(param_sq_sum)
grad_present_count == 0     -> 不输出 local/slow/<group>_grad_l2
grad_present_count > 0      -> local/slow/<group>_grad_l2 = sqrt(grad_sq_sum)
```

因此 selected grad 全为零时 `grad_present_count > 0` 且 `grad_sq_sum == 0`，必须输出精确 `0.0`；没有 selected grad 时才省略 key。不得用 `grad_sq_sum` 推断 presence。payload 不含 parameter/gradient bytes，不 gather/full_tensor；每个 parameter 只能纳入一个 group，且不增加 legacy aggregate、per-parameter aggregate 或其它 group collective。

现有 `total_param_l2_norm` / `total_grad_l2_norm`、per-parameter stats、activation hooks、logging cadence 与 `wandb.run is None` 行为保持不变。O1 不启用 Local selectors，只有显式传入 `LOCAL_SLOW_SELECTOR_GROUPS` 才产生 `local/slow/*`；recipe enablement 仍属于 O5。

## 4. CPU/static acceptance

相邻 CPU tests 只能测 selector validation 和 pure scalar packed-payload aggregation helper；不初始化 CUDA、distributed process group、W&B 或 S3。

1. `None` selector groups 的 legacy selected/unselected/EMA exclusion、metric key 和 aggregate 行为不变；
2. 四个 canonical names 精确归 encoder/core/projector/modality_embed；未知和 fast-state name 排除，modality leaf 不误配同前缀名称；
3. overlap、空 root、非法 group name、source mismatch 和调用方后续 mutation 均 fail closed；
4. synthetic per-rank payload fixtures验证：全局无 grad 省略 grad key；全局存在但全部零 grad 输出 `0.0`；mixed-rank 仅部分 rank 有 grad 仍输出正确 L2；普通非零 grad 输出正确 L2；
5. 每 group 一次 packed SUM 的 helper 输入/输出、无重复 parameter 计数及 legacy `NormMonitor` tests 均 PASS。

相关 pytest、两文件 `py_compile`、child/root `git diff --check` 必须 PASS。上述 CPU fixtures 不得宣称 real distributed/GPU logging 或训练已经验证。

## 5. 下一步

本版仅在 ChatGPT、MM、DS 对同一 formal root SHA 批准后，才授权 O1 两文件 CPU/static implementation。O2--O5、任何 production wiring、真实 I/O、GPU/CUDA/torchrun、训练、评测、推理、P4/P5、B2-T 和 LIBERO4IN1 仍须独立 Gate。
