# PSM-WMA Local Memory v0.3.5 Canonical Native Consumer Runtime Implementation 设计 v0.1

**日期**：2026-09-11  
**状态**：P0 docs-only implementation design；未经本文件 formal root/child 三方批准，不得修改 child 或执行项目代码  
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-CONSUMER-RUNTIME-IMPLEMENTATION-DESIGN`  
**事实前置**：source audit v0.1 formal `d554ee6498c4d4facd60cf688beec77c86ea8705` / child `08775da2e73e352ebb1497548de5909baab8c2dc` 已三方关闭

## 1. 目标、非目标与冻结范围

目标是将 `omni_mot_model.py:1408-1447` 中“carrier preflight → typed scan → safe preparation → hard-stop”的 canonical-production 分支，最小接到已有 Cosmos **native** pack/noise/denoise/loss 与 trainer 的 one-backward seam。它必须使 `[B_stream,T]` 的有效 consumer 以 stream-major gather 成为真实 native sample population；不是把 synthetic adapter、旧 row-wise history 或 zero-PAD 伪装为生产路径。

批准后的 implementation 白名单仅可包括：

```text
cosmos_framework/model/generator/omni_mot_model.py
cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py
cosmos_framework/trainer/__init__.py
cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py
cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py
cosmos_framework/model/generator/omni_mot_model_test.py
```

若现有 native loss 需要另一文件才能暴露 per-instance terms，必须 fail closed、另起 design Gate；不得偷偷扩大白名单。此 Gate 即使批准也只授权 child 的 CPU/static synthetic implementation，不授权真实 data/cache/checkpoint I/O、CUDA/GPU、torchrun、runtime-sidecar、训练、评测、推理或 LIBERO4IN1。

## 2. 唯一 canonical native continuation

### 2.1 Identity-preserving gather

`CanonicalRawRowCarrier.preflight()` 保持 `canonical_segment_production_adapter.py:97-126` 的唯一 PAD/valid authority。每个 `consumer_valid=True` 项的 stable identity 为 `(slot_id, episode_id, consumer_step)`；carrier 的 stream-major traversal 是唯一 gather 顺序。

在 `omni_mot_model.py::_canonical_production_segment_forward()`：

1. 保持 CP pre-scan reject、Local-neutral carrier 检查、typed `adapter.scan()` 与 `expected.identities == result.gathered.identities`；
2. `prepare_native_inputs()` 只输出 exact gathered working batch，禁止 row replay、重排、重新 bind、重采样、zero-PAD 或调用 `_inject_local_history()`；
3. `_prepare_canonical_production_inputs()` 把 `result.gathered.local_prefixes` 与同 index 的 gathered `SequencePlan` 绑定：absent 是 `None` / `has_local_memory=False`，present 是精确 `[K_local,32]`；然后以既有 `get_data_and_condition()` 与 `_pack_input_sequence()` 形成 native pack；
4. pack 后所有 native modality owner-index、sample count、sequence-plan count 与 carrier traversal 必逐一回映射到同一 stable identity。任何 duplicate、遗漏、cross-sample prefix、`actual_n_valid != request.member.planned_n_valid` 均在 forward/noise/backward 前 abort typed scan，零 commit。

`mot/memory_prefix.py:50-86` 的 sparse `list[Tensor|None]`/offset ABI 保持唯一 Local Prefix ABI；不得新增 dense zero-token 适配器。

### 2.2 Native forward 与 loss split

hard-stop 只可由一个 private canonical-native continuation 替代。它必须复用 ordinary path现有顺序：native pack → native noise → `denoise()` → native modality loss，但不得回落到 ordinary `training_step()`，避免再次注入 row-wise Local History。

该 continuation 需把真实 native modality结果以 typed `CanonicalNativeLossSplit` 交给 adapter，不能从最终 scalar 反推：

```text
consumer_identities == gathered traversal identities
actual_N_valid == planned_N_valid[mu]                 # before objective/backward
L_consumer_mu = exact mean over gathered real consumers
L_aux_mu      = native non-consumer-mean auxiliary terms
```

若 vision/action/sound native loss 不能暴露与 sample owner 对齐的 per-instance term，或 load-balancing term 无法显式与 consumer mean 分开，continuation 必须 raise typed contract failure；这不是允许整体 `total_loss` 乘 valid fraction 的理由。

## 3. Objective、recovery 与 trainer ownership

`CanonicalGAWindowPlan.objective()` 仍是唯一 loss algebra owner。normal：

```text
N_window = sum(planned_N_valid)
GA_effective = GA
L_backward_mu = planned_N_valid[mu] / N_window * L_consumer_mu
              + 1 / GA_effective * L_aux_mu
```

suffix recovery 仅接收 frozen uncommitted suffix，继承 plan-chain identity、`attempt=1`、其 own `N_window` 和 `GA_effective=len(suffix)`；不 nested/replay/rebind/resample。每个 member 在 native objective 前验证 actual==planned。`N_window<=0`、identity/digest mismatch、attempt-1 transient、non-finite、native forward/backward error均 typed terminal fail-closed。

trainer 只在 `psm_canonical_native_forward` capability 分支做一次：验证 capability → plan objective → `grad_scaler.scale(objective).backward()` → typed commit。该分支不可再经过 ordinary `loss / grad_accum_iter` (`trainer/__init__.py:551-561`)；普通非-Local 路径保持不变。现有 `trainer/__init__.py:959-972` 的“enabled scaler reject 后 scale”矛盾必须在 implementation 中消除：以一条经过验证的 GradScaler route 取代，任何 skip 的 scheduler/optimizer 后果只记录为后续 GPU/runtime Gate，不可由 CPU/static seam假称已证明。

## 4. 生命周期、legacy 隔离和显式不实现项

成功 backward 前任何失败必须 `abort_native_forward/abort_scan` 并保持 frozen scheduler/transaction/frontier/queue/exposure/W_fast 无 mutation；成功后才 `prepare_commit/commit_success`。一个 successful capability 只能消费一次。

以下旧路径可保留为其既有测试/历史兼容，但 canonical route 必须旁路且不得共享 mutating owner：

| 保留 authority | canonical 旁路对象 | 隔离断言 |
| --- | --- | --- |
| `CanonicalBatchScheduler`、typed transaction/recovery、carrier preflight | `_inject_local_history()` 的 row-wise `local_memory` 与 `psm_local_memory_active` registry | canonical data batch 为 Local-neutral 到 gather attach；foreign marker/capability fail closed。 |
| sparse `MemoryPrefixContext` | old `canonical_local_memory_segment` marker/lifecycle | canonical capability 的 object identity、one-shot receipt、abort/commit 不可被旧 marker消费。 |

本 Gate 不实现也不宣称：真实 producer/dataloader/weighted exposure、optimizer/LR GradScaler-skip semantics、single-GPU memory/throughput、checkpoint refreeze、sidecar/resume、DDP/world-size、LIBERO4IN1。它们均保留独立 Gate。

## 5. CPU/static 验收与产物

只能用 CPU/meta lightweight mock 与既有 synthetic seams；不调用真实 tokenizer/VAE/pack CUDA 或真实 data。新增定向测试必须证明：

1. mixed `[B_stream,T]` carrier 的 PAD 不进入 gather/noise/loss/prefix，stream-major identity 逐阶段不变；
2. S0 的 prefix absent、non-S0 present `[K_local,32]`，投影后 sample offsets 与 `[N_valid,K_local,2048]` 对齐，无 zero token；
3. foreign/reordered/duplicate carrier、prefix 或 modality owner 在 native capability 前拒绝且 scan/frontier/transaction 零 mutation；
4. normal 非等 valid-count 与 suffix recovery分别证明 typed objective精确系数、actual==planned 和 one scale/one backward，普通分支没有参与第二次 `/GA`；
5. native preparation/forward/loss/backward 任一 synthetic exception均 abort；成功 capability only-once commit；
6. CP、alternate attention dispatch、three-way/flex/multi-control Memory Prefix 不支持时 fail closed。

必须产出：定向 pytest、Ruff、`py_compile`、child/root `git diff --check` 的真实结果；若任一需 GPU/real I/O 才能证明，标 `DEFERRED / NOT PROVEN`，不执行。

## 6. 审核请求

请回复唯一 verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_CONSUMER_RUNTIME_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。批准只授权第 1 节白名单的 CPU/static synthetic implementation；不授权生产数据路径、真实 I/O、GPU、torchrun、sidecar、训练、评测、推理或 LIBERO4IN1。
