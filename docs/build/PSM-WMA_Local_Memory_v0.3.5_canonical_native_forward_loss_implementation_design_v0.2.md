# Canonical Native Forward/Loss Implementation 设计 v0.2

**状态**：docs-only remediation；supersede v0.1 §3.1、§4--§6；须三方新 SHA 批准
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-IMPLEMENTATION-DESIGN`

本文件只关闭 v0.1 formal `6f75365/5d0e037` 的两个 HIGH。七文件白名单、parity-or-fail-closed、多 item/dense source identity、hook order、retry lineage和禁止范围不变；未改 child。

## 1. Cardinality-preserving consumer algebra

令 `N=actual_n_valid`，`J` 是 N 个 gathered consumer identity。每个有有效 token 的 modality `m` 的原生加权 item population 为 `I_m`，`K_m=|I_m|>0`，term 为 `z_i`，唯一 owner 为 `owner(i) in J`。新增 primitive 返回 `weighted_per_instance=[z_i]`，但 legacy `compute_flow_matching_loss()` 继续返回 `(mean(z_i), unweighted_per_instance)`。

```text
c[j,m] = (N / K_m) * sum(z_i for i in I_m if owner(i) == j)
mean(j in J, c[j,m]) == mean(i in I_m, z_i)
u[j] = s * sum_m w_m * c[j,m]
consumer_loss = mean(j in J, u[j]) + dummy_graph_terms
```

`w_m` 是原 modality weight，`s` 是原 sample-level scale；故不等的 `K_vision`、`K_action`、`K_sound` 与 N 仍精确复现 ordinary pre-LBL native means。LBL 继续独立 `auxiliary_loss`，不乘 valid ratio。

对于 absent/no-valid modality，`c[:,m]=0`；legacy singleton graph diagnostic 和 action/sound dummy graph term只加到 scalar `dummy_graph_terms`，绝不产生 fake item、identity或consumer。CPU/static 必覆盖不等 K/N、absent modality、legacy wrapper不变和该等式。

## 2. Field-wise ownership

`CanonicalNativePreparedInputs` 不得冻结浅 dict 即声称 immutable。每个 admitted model-batch field必须有独立 working container；会被 native flatten、normalization或 plan rewrite 的 list、tensor storage、plan、metadata 都不得 alias carrier。carrier model batch、nested rows、source maps、frozen request/plan/transaction保持 object/value不变。测试逐字段施加 native-style rewrite并证明 carrier不变。

## 3. Exact current canonical lifecycle

capability 绑定 exact adapter、request、scan result、transaction和**唯一** `CanonicalProductionCommitCapability`。成功顺序固定：

```text
adapter.scan(request)
capability = adapter.prepare_commit(request, scan_result)  # only once
transaction.mark_backward_started(member_index)
grad_scaler.scale(L_member).backward()                     # once; no /GA
adapter.commit_success(capability)                          # validates/consumes/reconciles
```

不得调用不存在的 `successful_backward()` 或 generic `commit()`；已绑定 capability 后不得再次 `prepare_commit()`。attempt-1 仅 `consume_retry()` 获得 exact request后走同序列，不得重建 plan/transaction或第二 frozen transition。

对 enabled GradScaler 或会触达 real optimizer/scheduler 的 canonical window，本 CPU/static Gate 在**scan、prepare、mark-backward、backward 前** terminal reject：不创建 scan/capability，不触 callbacks、`unscale_`、`step`、scheduler、`update`、zero-grad，frontier/scheduler/transaction零 commit。No-Local ordinary route不变。

## 4. Required witnesses and verdict

新增 witnesses：`N/K_m` 恒等式与 sample-level位置；absent graph-zero无 fake identity；每个 working field无 carrier alias；attempt-0/consumed attempt-1 single prepare/mark/backward/commit；enabled scaler在任何 transaction mutation前拒绝。

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_FORWARD_LOSS_CPU_STATIC
```
