# PSM-WMA Local Memory v0.3.5 Canonical Native Consumer Runtime Implementation 设计 v0.2

**日期**：2026-09-11
**状态**：P0 docs-only remediation；须本文件 formal root/child 三方同 SHA 批准后，才可修改已列出的 child CPU/static 范围
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-CONSUMER-RUNTIME-IMPLEMENTATION-DESIGN`

## 1. Supersession、范围与不变约束

本文件仅整改 v0.1 formal `3e058eb418c63188856fa3d36667227561ca3a91` / child `08775da2e73e352ebb1497548de5909baab8c2dc` 的 ChatGPT 两项 design-only HIGH；v0.1 的 stream-major carrier identity、sparse `list[Tensor|None]` prefix、typed native per-instance split、normal/suffix objective、legacy isolation、six-file whitelist 和全部禁止范围保持 binding。

implementation whitelist 不变：

```text
cosmos_framework/model/generator/omni_mot_model.py
cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py
cosmos_framework/trainer/__init__.py
cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py
cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py
cosmos_framework/model/generator/omni_mot_model_test.py
```

只授权 single-process/world-size-1 CPU/static synthetic implementation。任何真实 data/cache/checkpoint I/O、CUDA/GPU、torchrun、native real forward/loss/backward、optimizer/scheduler step、sidecar、训练、评测、推理和 LIBERO4IN1 继续禁止。

## 2. HIGH-1 remediation：scaler / optimizer pre-scan admission

v0.1 所谓“移除 enabled-scaler reject”的表述失效。该 CPU/static Gate 的唯一安全 admission 是：

```text
if isinstance(optimizer, torch.optim.Optimizer): reject before callbacks/model-forward/scan
if grad_scaler.is_enabled(): reject before callbacks/model-forward/scan
```

因此 canonical-production 只能接收 non-Optimizer CPU/static test double 与 disabled `GradScaler`（或等价 disabled wrapper）。`grad_scaler.scale(objective).backward()` 只证明一次 scale/一次 backward 的结构；disabled wrapper 的合法 no-op 不构成 enabled AMP、unscale、step、skip、zero-grad 或 slow-LR lifecycle 支持。

`_run_canonical_native_backward()` 继续拒绝 enabled scaler，且不改变既有 pre/post-mutation commit failure semantics。移除 real-optimizer reject、接纳 enabled scaler、或实现/声称 scaler skip、optimizer/LR disposition，均只能在独立 runtime/GPU Gate 审核后进行。

新增 direct CPU/static witnesses 必须对 real `torch.optim.Optimizer`、enabled scaler 分别证明：在 callback、model-forward、native prepare、core scan 之前拒绝；scheduler/transaction/frontier/scan/retry bookkeeping 与 Local slow gradients均零 mutation。

## 3. HIGH-2 remediation：distributed pre-scan admission

在 dedicated distributed Gate 前，canonical-production 的唯一 admitted topology 是 single-process/world-size-1 CPU/static。它必须在 scan/native work 前 fail closed 拒绝：

```text
DDP wrapper
FSDP wrapper
initialized distributed process group
world_size != 1
data-parallel configuration
context parallelism
```

此 guard 同时位于 trainer production entry 与 model canonical pre-scan 所能观察的边界，避免已经进入 `distributed.ddp_sync_grad(...)`、native model-forward 或 core scan 后才拒绝。CPU/static witnesses 对每种 unapproved topology 注入 test double，断言 callback/model-forward/core scan 未进入，且 scheduler/transaction/frontier/scan bookkeeping 为零 mutation。

后续 distributed Gate 才可冻结并移除该 guard；必须同时定义 global `N_window`、DDP/FSDP gradient averaging、`_sample_level_loss_scale`/all-reduce owner、rank-local fast state、resume sidecar 及 world-size-change fail-closed。不得从本 Gate 推断任何 distributed 支持。

## 4. 继承的 canonical continuation和验收

hard-stop replacement 仍只能沿 v0.1 的唯一 continuation：carrier preflight 的 stream-major gather → exact sparse Local Prefix attach → native pack/noise/denoise/loss → typed `CanonicalNativeLossSplit` → `CanonicalGAWindowPlan.objective()` → disabled-scaler one backward → typed one-shot commit。任何 `actual_N_valid != planned_N_valid`、identity/owner mismatch、per-instance loss缺失、recovery attempt=1 transient、数值/outer failure均 fail closed/abort。

除 v0.1 的六项验收外，实施必须新增第 2、3 节 admission witnesses。真实 packer、VAE、tokenizer、CUDA 或 data 不得调用；若证明需要它们，记 `DEFERRED / NOT PROVEN` 并另起 Gate。

## 5. Verdict

请求唯一 verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_CONSUMER_RUNTIME_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。批准仍仅覆盖 six-file CPU/static synthetic implementation；不授权真实运行、GPU、optimizer step、distributed、sidecar 或训练。
