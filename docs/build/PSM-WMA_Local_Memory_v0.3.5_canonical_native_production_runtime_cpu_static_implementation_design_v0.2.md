# PSM-WMA v0.3.5 Canonical Native Production Runtime CPU/static Implementation 设计 v0.2

**日期**：2026-09-11  
**状态**：docs-only remediation；须新 formal root/child 三方同 SHA 批准后才可修改 child。  
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-PRODUCTION-RUNTIME-CPU-STATIC-IMPLEMENTATION-DESIGN`  
**替代关系**：本文件替代 v0.1 的 failure taxonomy；v0.1 其余六文件 whitelist、single-process CPU/static 范围、preparation/loss/objective/recovery/admission 合同和全部禁止项保持 binding。

## 1. 前置与范围不变

前置 approved integration-design pair 是 `ee979172b8bef4709e94fe84ed4ff4e9c711e2e7` / `f49f568923555fe15efe546925cbe6cc9140170e`。v0.1 formal `750410ce0928f2b03b0dadfa3015a22f9f71c7d2` / `f49f568923555fe15efe546925cbe6cc9140170e` 收齐 ChatGPT `REQUEST_CHANGES`、MM/Kimi approve；本版只关闭 ChatGPT design-only HIGH。

允许范围仍严格为 v0.1 第 1 节的 model/adapter/trainer 三个 source 与三个定向 test 文件。禁止 config/checkpoint/sidecar/data/packer/flow-matching/registry 变化，及真实 I/O、CUDA/GPU、torchrun、真实 native forward/loss/backward、optimizer/scheduler step、训练、评测、推理、LIBERO4IN1。

## 2. 唯一、分界明确的 failure taxonomy

不可逆边界是 `CanonicalProductionAdapter.commit_success()` 首次执行 frontier/scheduler/transaction mutation 的时刻；所有实现与验收必须按以下两类严格分流，绝不把 post-mutation failure 写入 pre-boundary 集合：

1. **pre-mutation failure**：missing typed terms、foreign/stale capability、actual/planned count mismatch、duplicate consumption、ordinary second GA scaling、unsupported scaler/optimizer/topology、forward、pre-backward、loss-build、prepare-commit，以及 `commit_success` 的任何首次 mutation 前 validation failure。它们必须在边界前清 controlled Local slow grads、dispose exact forward/commit capability 与 scan、terminalize，并证明 frontier/scheduler/transaction 无 reconcile；不得 retry、reconstruct 或走 legacy/ordinary path。
2. **post-mutation failure**：一旦任何 frontier/scheduler/transaction irreversible mutation 已发生，必须保留 exact commit capability、pending scan provenance、frontier state 与 controlled failure evidence；不得调用 ordinary abort、不得 reconstruction、不得自动 retry 或 attempt-2。它必须以 typed post-mutation failure surface 给调用方，并保持已发生的 mutation 可审计。

normal/recovery 均继续在 mutation 前使用 exact `CanonicalGAWindowPlan.objective()`，并以 non-equal planned valid counts/non-zero auxiliary witness 证明唯一 `planned_n_valid/N_window * consumer_loss + auxiliary_loss/GA_effective`，无 ordinary `/GA` 或 second scaling。suffix recovery 只可消费 public exact capability；已提交 prefix retain，original transition 仅在完整 suffix success 后 reconcile 一次。

## 3. 更新后的验收

除 v0.1 A--D/F 外，E 必须同时证明：

- forward、pre-backward、loss-build、prepare-commit、pre-mutation commit failure：清 controlled grads、exact abort、terminalize、零 frontier/scheduler/transaction reconcile；
- post-mutation injected failure：不调用 abort/reconstruct/retry，保留 exact capability/scan/frontier/transaction provenance 和 typed failure evidence。

模型/adapter/trainer hard-stop、disabled-scaler CPU/static double、S0 `None`、PAD absence 与所有 topology reject 继续有效；本 Gate 不执行任何项目代码。

## 4. Verdict

请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_PRODUCTION_RUNTIME_CPU_STATIC
```

或 `REQUEST_CHANGES(file:line)`。批准仅授权 v0.1 白名单内的 synthetic CPU/static implementation，不授权真实运行。
