# R09-B2 P3 实际 Optimizer Inventory 设计 v0.1

**状态**：DRAFT；仅请求方案审核。禁止实现、模型/checkpoint 加载、forward/backward、GPU、训练、评测与推理。

## 1. 目标与边界

P3 解除 B2-P0 的单一阻塞项：以可复验的实际对象清单记录 `recurrent` 与 `ttt_fast_weight` 的 parameter、optimizer 与 optimizer-state membership。它只回答“哪些对象被实际选择、是否可训练、占多少元素、是否进入 optimizer/DCP state”；不比较 loss、不选择 backend，也不构造训练 batch。

P3 不得将 `keys_to_select`、名称 prefix 或 B1 的小型 synthetic module 当作实际 full-recipe 清单。它们只能作为待核对的期望输入。

## 2. 冻结输入与允许执行面

实现获批后，collector 只允许：

1. 用相同根仓/子模块 Gitlink、同一 LIBERO recipe、同一 `PSM_R08_LOCAL_HISTORY_ENABLED=1`，分别解析 `PSM_R09_B1_TTT_ENABLED=0/1` 的完整 recipe；
2. 在 CPU/meta-safe 的只读构造路径中 materialize 与 recipe 完全一致的 Local runtime、adapter 和 optimizer 选择对象；不得加载 base checkpoint、VAE、tokenizer 或数据；
3. 读取 model `named_parameters()`、optimizer `param_groups`/`state` 和 DCP state-dict 的键结构。不得运行 forward、backward、optimizer.step、scheduler.step、保存 checkpoint 或访问 GPU；
4. 输出一份 JSON 与 verifier。构造路径若无法同时满足“实际 full-recipe”与上述无权重/无 GPU 限制，必须 `BLOCKED`，不得降级为 synthetic module 后写 PASS。

P3 的唯一输入 provenance 为 root/submodule/Gitlink、recipe SHA、collector/verifier SHA、解析环境的 Local selector 环境变量及构造模式。所有读到的参数只记录 metadata/hash，不写 tensor sidecar。

## 3. 四层 membership 合同

每个 backend 都必须分别记录以下集合，并以 parameter object identity 关联：

| 层 | 必填字段 | PASS/FAIL 语义 |
| --- | --- | --- |
| `model_parameters` | `name`、`trainable`、`numel`、`dtype`、`selected_by_recipe` | 记录完整实际 selector 影响范围与单独 Local/backend 子集；`selected_by_recipe` 由 resolved `keys_to_select` 和 weight-decay skip 规则共同记录，不得只凭 prefix；同名但不同 object-id 立即 FAIL。 |
| `optimizer_param_groups` | `group_index`、`parameter_names`、每项 `numel`、`lr`、`weight_decay` | 每个 optimizer parameter 必须反向映射到唯一 model parameter；重复或遗漏 FAIL。 |
| `optimizer_state` | `parameter_name`、`state_keys`、每 state tensor 的 shape/dtype/numel、索引语义 | 初始 state 与任何后续 materialization 明确分开。P3 不执行 step，若实际初始 state 为空，必须如实写空并标记 `not_materialized`，不得声称训练后状态为空；artifact 明确其进程内由 parameter object identity 索引、跨运行由稳定名称关联。 |
| `dcp_state` | state-dict key、所属层、参数/optimizer state 映射 | `model.state_dict()`/`optimizer.state_dict()` 的未训练 schema 读取可接受；若 trainer DCP API 会保存、加载、触发设备 materialization 或权重加载，则记录 `BLOCKED`。 |

共同 hard gate：同一名称的 `numel`/dtype 在 model、optimizer 与 DCP 三层一致；任何 optimizer 参数不在 model 或任何 selected trainable model 参数未在 optimizer 时 FAIL。

## 4. 两 backend 的允许差异

共同 Local slow 参数必须以实际 full-recipe 清单相等，而不是凭预期写死。唯一允许差异为：

1. `recurrent` backend 的 `local_history_runtime.recurrent_backend.*` slow parameters 及其 optimizer/DCP state；
2. `ttt_fast_weight` 的 frozen B0 五成员 `W`、`pending_evidence`、`last_evidence`、`initialized`、`segment_progress` 不是 `nn.Parameter`、不是 optimizer parameter、不是 optimizer state，也不是 model DCP persistent state；
3. 两侧 selector 值与其必要的 optimizer allowlist 差异。

TTT 三条预期 selector（`local_history_runtime.encoder`、`local_memory2llm`、`local_memory_modality_embed`）只作为 verifier 的期望集；collector 必须导出实际 matched names、object identity 与 `numel` 后才能 PASS。recurrent 侧同样必须实际导出其 selector 匹配，不能复用 TTT 的三条约束。

## 5. 输出与 verifier

目标 artifact：`artifacts/g0/r09/b2/p3_optimizer_inventory.json`。

```json
{
  "schema_version": "r09_b2_optimizer_inventory_v1",
  "status": "PASS|BLOCKED|FAIL",
  "source": {},
  "execution": {"device": "cpu|meta", "weights_loaded": false, "forward_executed": false},
  "recurrent": {"model_parameters": [], "optimizer_param_groups": [], "optimizer_state": {}, "dcp_state": {}},
  "ttt_fast_weight": {"model_parameters": [], "optimizer_param_groups": [], "optimizer_state": {}, "dcp_state": {}},
  "matched_diff": {"allowed_only": false, "unexpected": []},
  "limitations": []
}
```

verifier 必须拒绝：缺 provenance、任何 synthetic fallback、设备非 CPU/meta、weights/forward/backward/step 已执行、TTT 五成员作为 parameter/optimizer/DCP persistent key、不可反向映射的 optimizer object、重复 parameter、未解释的两侧差异、或把 `not_materialized` optimizer state 误写为训练后结论。它还必须分别列出 `named_parameters`、`named_buffers` 与动态 TTT state；未来若五成员注册为 buffer，不能误报为 parameter 或 dynamic state。

## 6. 方案审核请求与禁止范围

本方案仅请求 `APPROVE_TO_IMPLEMENT_B2_P3` 或 `REQUEST_CHANGES`。即使批准，也只允许 collector/verifier、CPU/meta-safe 定向 tests 与 artifact；不授权 checkpoint/VAE/tokenizer/data 加载、GPU、forward/backward/optimizer step、训练、B2-T、P4/P5、eval/inference/closed-loop、SR 或 backend freeze。
