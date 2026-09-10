# PSM-WMA Local Memory v0.3.5 Canonical Segment Production ABI Implementation 设计 v0.3

**日期**：2026-09-10
**状态**：P1 docs-only remediation；须本文件新 formal pair 三方同 SHA 批准后才可进入 P2 CPU/static implementation
**任务/Gate**：`G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ABI-IMPLEMENTATION-DESIGN`

## 1. Scope 与 supersession

本文件以 v0.3.5 addendum、P0 audit v0.3 (`395dadf/3a078f2`) 和 P1 v0.2 为 authority，显式 supersede v0.2 的 activation、registered module binding、attempt-1 lineage 与 fp32 fast-state 表述。它只整改 ChatGPT 对 `8257418/3a078f2` 的 3 HIGH+1 MEDIUM；v0.2 已关闭的 typed scan/gather、normal attempt-0 prepared commit、S0/PAD/count、loss/GA、scan owner 和 GradScaler hard stop 均保持不变。

仍只授权 P2 CPU/static design implementation，禁止 child 以外范围、真实 data/cache/checkpoint I/O、CUDA/GPU、torchrun、runtime sidecar、LIBERO4IN1、训练、评测与推理。

## 2. Canonical activation：`local_ttt_enabled` 是严格开关

本 Gate 定义唯一 ordinary No-Local 条件：`config.local_ttt_enabled is False`、没有 canonical request 且没有任何 old canonical/active/row-wise marker。只有此行可进入未改变的 `_get_training_inputs()` ordinary path。

当 `config.local_ttt_enabled is True` 时，model 必须在 `_get_training_inputs()` 前要求同时存在且类型精确的 canonical-production mode declaration 与 `CanonicalProductionSegmentRequest`；缺失、malformed、foreign、重复或不一致任一项都 pre-forward fail closed。任何 legacy row-wise marker、`canonical_local_memory_segment`、`psm_local_memory_active` 或其 capability 与 canonical request 同时出现亦 fail closed。故 `local_ttt_enabled=True + no declaration` 永不调用 `_inject_local_history()` 或 `_ttt_local_memory_tokens()`。

P2 fixture 必逐项证明上述 true/false matrix，特别是 enabled-with-no-declaration 的 legacy zero-call；不得以 declaration 缺失将 enabled TTT 偷换为 No-Local。

## 3. 已注册 encoder/core 的 exact binding

P2 仅在 `OmniMoTModel.build_net()` 现有 `local_history_enabled`/`ttt_fast_weight` 分支中作最小构造修订：当且仅当 canonical `local_ttt_enabled=True`，`net.local_history_runtime.encoder` 必创建为：

```text
LocalEvidenceEncoder(
  evidence_dim=config.local_history_evidence_dim,
  visual_dim=96,
  feature_config=CANONICAL_EVIDENCE_FEATURE_CONFIG,
)
```

同一 `net.local_history_runtime.recurrent_backend` 必为该 build path 已注册的 `ContinualTTTLocalMemoryCore`。构造发生在既有 net materialization/parallelization/optimizer ownership 之前；adapter lookup 只接受这两个对象的 object identity：

```text
encoder is model.net.local_history_runtime.encoder
core is model.net.local_history_runtime.recurrent_backend
encoder.feature_config is CANONICAL_EVIDENCE_FEATURE_CONFIG
```

foreign/reconstructed encoder/core、legacy feature config、None/wrong backend均在 scan 前拒绝。adapter 不得创建、持有或注册独立 trainable encoder/core 副本。P2 CPU/static evidence 必证明 canonical scan 的 gradients 达到这些 exact registered encoder/core slow parameters，且 canonical encoder 未注册 state/dt/age modules。

## 4. fp32 fast-state frontier

`CanonicalProductionFastStateFrontier` 的四个 `ContinualTTTFastState` tensors 是 runtime fast state，fresh、continuation、candidate 和 committed storage 均强制 `torch.float32`。

- fresh：从 exact registered core 的四个 `w0_fast_*` 参数以 differentiable `.to(dtype=torch.float32).unsqueeze(0).expand(...).clone()` 建立，因而 outer gradient 回到已注册 `W_bar_0`；
- continuation：只取 exact slot/episode/source/cursor-1 committed state，所有 tensors 必为 `detach().to(torch.float32).clone()`；
- candidate：scan output 每 tensor 在 commit preflight 时验证 fp32；success storage detach+fp32 clone，terminal retire；
- batch assembly 按 row provenance gather/scatter，不得 alias 任两 slot，mixed fresh/continuation 亦保持逐行 fp32。

P2 evidence 要覆盖四个 tensor的 fresh scan、continuation、success commit、terminal retirement dtype，且 fresh gradient 能达 registered `w0_fast_*`。

## 5. Attempt-0/attempt-1 typed lineage

attempt-0 request 继续要求 `plan is scheduler.freeze_plan(...) result`，并由 scheduler frozen transition 唯一 admission。attempt-1 **不得**再次 `freeze_plan()`、不得 re-admit/resample。

只在 member 0、backward 未开始、explicit transient failure 时，attempt-0 adapter owner 可调用 `transaction.retry_first_member_pre_backward()` 并铸造 `CanonicalProductionRetryCapability`。它捕获 exact original scheduler、attempt-0 plan、original transaction、original frozen `member is plan.members[0]`、retry plan、retry transaction 和 plan-chain id；retry plan 必来自该 original transaction 的 `retry_first_member_pre_backward()`，保留相同 member objects、denominator、GA、queue snapshot、projected exposure 与 frozen scheduler transitions。retry transaction 的 `plan is retry_plan`。

retry capability 只可消费一次，且 scan/backward 前验证所有 identity；foreign/stale/second-retry/member>0/post-backward 一律拒绝。retry success 的 reconcile 仍消费**原** scheduler frozen member transition恰一次，不创建第二 transition/admission。P2 evidence：attempt-1 success、无 duplicate admission/transition、second retry rejection、foreign/stale retry pre-scan rejection。

## 6. 保留的 commit/GradScaler rules

attempt-0 与合法 attempt-1 都沿用 v0.2 typed pre-scan/scan/gather、`NativeConsumerBatch.from_segment` count authority、object-bound prepared reconcile、`mark_backward_started` 紧邻唯一 scaled backward、success-only one-shot commit。P2 仍在 enabled GradScaler/real optimizer boundary 前 hard-stop，terminal+clear+suppress 且 fast-state/scheduler/transaction 零 mutation；No-Local optimizer不变。

## 7. 补充 CPU/static acceptance

除 v0.2 §8 外，P2 增加：

1. `local_ttt_enabled=True` 缺 declaration/request、foreign request、conflict legacy marker均 pre-forward fail，legacy injection/token function zero-call；`local_ttt_enabled=False` ordinary control-flow parity。
2. build-net canonical exact encoder/core identity、canonical feature config、无 state/dt/age registration；scan gradient到 exact registered encoder/core slow params，foreign modules拒绝。
3. fresh/continuation/candidate/commit/terminal 四个 fast-state tensor均 fp32，fresh W0 gradient可达，B>1 无 alias/leak。
4. attempt-1 capability preserves original member/denominator/GA/chain/frozen transition，无 second freeze/admission；success reconcile original transition恰一次，stale/foreign/second retry零 mutation。

验证仍仅定向 CPU pytest、目标 Ruff/`py_compile`、child/root `git diff --check`；P2不读真实I/O、不用GPU。

## 8. Verdict

请求唯一 verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCTION_ABI_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。
