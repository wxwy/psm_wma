# R09-B1 TTT Runtime Preflight Runbook v0.1

**状态**：IN_PROGRESS；本文件只准备独立实施申请。未授权 production runtime/config 改动、CPU/GPU 执行、训练或评测。

**前置关闭**：`G0-R09-B-SOURCE-AUDIT`（B0 independent CPU contract）已由 ChatGPT、MM、Kimi `APPROVE_TO_CLOSE_B0`，post-closure provenance hygiene 亦已三方通过。唯一 canonical B0 artifact 是根仓 commit=`4e85ba8` 的 `artifacts/g0/r09/b0_ttt_contract.json`，其 recorded clean root=`685ca9a`、submodule/Gitlink=`ee1b78d`；`f4ca0fc`/`a9b7443` 仅是历史 initial-generation provenance。

## 1. 目的与严格范围

B1 仅把已验证的 `TTTLocalMemoryBackend` 接到当前 Local history runtime 的 temporal-compressor 插槽，并做一次独立审批后的、单卡有界 A1-style smoke。它不改变 causal history schema、`LocalEvidenceEncoder` 输入、每 sample 一个 Local token、`local_memory2llm`、native vision/action loss、packing、mRoPE、数据集、VAE/cache 契约或 shared Cosmos MoT。

实现前必须保持默认关闭；关闭时模型构造、训练配方与 A1 recurrent 路径逐项不变。启用必须是显式、仅 B1 使用的 opt-in，且不得改变其他 R07/R08/A1 启动的行为。

持续禁止：多卡、长训、matched SR、backend freeze、RoboTTT/shared-MoT 代码导入、Global/Agent/RL，以及跨 batch/worker/episode/sample 的 fast-state 共享。

## 2. 已核验入口和 B1 差异

| 事项 | 当前入口 | B1 约束 |
| --- | --- | --- |
| production backend 构造 | `cosmos-framework/cosmos_framework/model/generator/omni_mot_model.py:302-313` | 只替换第三个 `LocalHistoryRuntime` 构造参数；encoder/readout/adapter 位置不变。 |
| runtime 调用 | `cosmos-framework/cosmos_framework/model/generator/mot/local_evidence.py:253-300` | 继续调用同一 `replay(evidence, mask)` contract，输出 `[B,1,32]`、`present[B]`；不得将 fast state跨 outer forward保存。 |
| B0 backend | `local_evidence.py:202-250` | 无 `nn.Parameter`；state 为 W/pending/last/initialized/progress；token/state/evidence 都是 detached。 |
| A1 allowlist | `action_policy_libero_edge_all.py:189-195` | prefix 列表不扩为第五项；B1 必须记录实际匹配参数，而不是假定 recurrent backend 仍有 GRU 参数。 |
| A1 runtime probe | `callbacks/r09_a1_runtime_probe.py:52-90` | `.cell` 和两成员 GRU state 专属，不能用于 TTT；B1 需新增或明确泛化为五成员 state probe。 |
| A1 checkpoint verifier | `tools/g0/verify_r09_a1_smoke.py:116-168` | GRU 专属的新增四 tensors、16 tensors/142,784 elements、encoder nonzero grad 均不可复用为 B1 PASS 条件。 |

## 3. B1 必须先冻结的静态合同

在任何 runtime 接线前，三方必须审查以下最小实现设计：

1. **选择机制**：新增一个仅 B1 opt-in 的 backend selector；默认仍构造 `RecurrentLocalMemoryBackend`。不得靠修改环境默认值或替换现有 R08/A1 路径来选择 TTT。
2. **类型与接口**：`LocalHistoryRuntime` 只依赖 `replay` contract；若为表达两种 backend 扩宽类型注解，改动限于该本地模块，不能引入新依赖或改变公开数据接口。
3. **state 生命周期**：production forward 必须仍从 `replay(..., state=None)` 开始；不得将 B0 state 放到 model field、dataloader、optimizer、DCP、callback、worker 或 episode cache。B0 的 `reset_mask` 保留 CPU contract 覆盖，但本 B1 不以它创建跨 forward carry。
4. **optimizer 与梯度**：B0 的 detach 是已经冻结的语义。因此 B1 不得要求 encoder 经 TTT token 得到非零梯度，也不得把 A1 的 `optimizer_matches_targets`/active-group nonzero 条件原样当 PASS。实现后必须机器可读列出：实际 optimizer 参数名、三条既有 prefix 的匹配集合、TTT backend parameter count=0、每组 gradient present/finite/nonzero，以及对 encoder 无 TTT 回传的证明。任何新增 slow parameter、第五个 allowlist key、或 native loss 经 adaptation 回传，均为 FAIL。
5. **checkpoint warm-start/schema**：只能复用 A1 Gate-A 的 model-only warm-start，而非假设 A1 final GRU checkpoint 与 parameter-free TTT schema 严格相容。B1 verifier 必须从实际 DCP metadata 派生新增/删除/公共 tensor 集，硬断言公共 frozen tensors逐位不变、TTT fast state未序列化；不得写死 A1 的 GRU 四 tensors或 16/142,784 数字。
6. **intervention**：复用 `PSM_R08_HISTORY_MODE=normal|zero|shuffle`，只改变 history payload；无 history 的 non-Local 输入、sequence-plan、pack layout 与固定权重均保持 A1 既有不变量。

任一项不清楚时，停止于静态 REVIEW，不进入 GPU。

## 4. 拟议分轮验收（均需另行批准）

### B1-S：静态接线与定向 CPU coverage

允许范围仅为 B1 selector、Local runtime 的最小类型/构造改动、TTT 专用 runtime probe/verifier 单元测试及 recipe opt-in 解析测试。PASS：默认 recurrent 路径测试不回归；opt-in 构造实际是 TTT；TTT state 不注册参数且不跨 forward；实际 optimizer membership/gradient contract 按 §3.4 输出；A1 专属 probe 不再被误用于 TTT。

失败分流：selector 默认行为变化、TTT state 被注册或持久化、A1 GRU 断言被静默放宽，均为 FAIL，不申请 GPU。

### B1-G：单卡有界 runtime smoke

仅在 B1-S 三方通过、且用户再次确认 GPU 命令后执行。复用 A1 Gate-A 的 model-only warm-start、LIBERO 4-suite data/cache、batch、loss、precision、checkpoint 形式、固定 seed 与 Normal/Zero/Shuffle capture。唯一变量是 B1 TTT opt-in。启动前 D005 sidecar 必须记录完整命令、root/submodule/Gitlink、checkpoint、cache、GPU、输出路径和资源上限。

PASS 至少要求：

- bounded step 数与 loss/action loss 全 finite；
- runtime probe 确认实际 backend 为 TTT、五成员 state schema/bytes 与 B0 exact、state/token/graph detach 和每-forward fresh-state；
- TTT backend `named_parameters()`、optimizer 与 DCP state 均为空；实际 optimizer membership 仅来自既有三个参数组，且完整记录梯度事实；
- final DCP 公共 frozen tensors逐位不变，任何变化仅能落在批准的既有 Local slow 参数；
- Normal/Zero/Shuffle 三次同一 final checkpoint、同一 runtime，所有 non-history invariants exact，并各自产生 machine-readable provenance/capture；
- VAE/cache 与数据 provenance 与 Gate-A 相同，无 online VAE fallback。

GPU 资源、具体步数、checkpoint、日志和 JSON 路径在本 runbook 中不预授权；任一触发前需独立启动告知并获得 `APPROVE_TO_RUN_B1_SMOKE`。

## 5. B1 机器可读证据

计划新增独立 `artifacts/g0/r09/b1/`，不得覆写 A1 或 B0 artifact。每份最终 JSON 必须带：

```json
{
  "schema_version": "r09_b1_ttt_runtime_v1",
  "training_source": {"root_revision": "", "submodule_revision": "", "gitlink_revision": "", "checkpoint": ""},
  "runtime": {"backend": "ttt_fast_weight", "state_members": {}, "state_bytes": 0, "fresh_state_per_forward": false},
  "optimizer": {"parameter_names": [], "prefix_matches": {}, "backend_parameter_count": 0, "gradient_summary": {}},
  "checkpoint": {"added": [], "removed": [], "frozen_common_bitwise": false, "fast_state_serialized": false},
  "captures": {"normal": {}, "zero": {}, "shuffle": {}, "non_history_invariants_exact": false},
  "provenance": {"root_clean": false, "submodule_clean": false, "gitlink_matches_submodule": false, "command_sha256": "", "tool_sha256": ""},
  "status": "PASS|FAIL"
}
```

所有 shape、parameter names/count、step 数、loss 数值和显存由运行回填；不得把 A1 数字预写成 B1 事实。

## 6. 本轮审核请求

本文件完成静态校验后，只请求 ChatGPT、MM、Kimi 给出 `APPROVE_TO_IMPLEMENT_B1` 或 `REQUEST_CHANGES`。该批准最多允许 B1-S 的最小代码与 CPU 验证；它不批准 GPU，B1-G 仍需独立 `APPROVE_TO_RUN_B1_SMOKE`。
