# PSM-WMA Local Memory v0.3.5 Canonical Segment Production ABI Implementation 设计 v0.1

**日期**：2026-09-10
**状态**：P1 docs-only design；须以本文件 formal root/child pair 获三方同 SHA 批准后才可进入 P2 CPU/static implementation
**任务/Gate**：`G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ABI-IMPLEMENTATION-DESIGN`

## 1. Authority、前置与边界

唯一算法 authority 为 `PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md`，特别是 §7、§12、§18、§20.1--§20.2。直接工程 authority 为已三方关闭的 P0 source-ABI audit v0.3（formal root `395dadff0b17ed6206887e372718bb166aa63b40` / child `3a078f28f3d107bb633c932271f86498f7c427f7`）。

本设计只冻结 P2 的 CPU/static production-ABI 接入。它不授权 child 代码、真实 data/cache/checkpoint I/O、CUDA/GPU、torchrun、runtime sidecar、LIBERO4IN1、训练、评测或推理。任何 P2 代码及测试均须另以新 formal pair 三方审核；P2 closure 也不授权 GPU 或训练。

历史 `production_segment_wiring.py`、`production_segment_bridge.py`、`production_active_wiring.py` 及其 row-wise owner/callback 路由仅可保留为 provenance 或 fail-closed 对照，绝不可被 canonical v0.3.5 path 调用、适配或 fallback。

## 2. 目标 production graph 与不变量

```text
frozen CanonicalGAWindowPlan.member[i]
  -> immutable SegmentBatchProducer input [B_stream,T]
  -> one shifted evidence / TTT scan
  -> stream-major flat(b,t)=b*T+t, gather consumer_valid only
  -> native SequencePlan/data payload list + Local Memory Prefix list
  -> one OmniMoTModel native forward
  -> consumer_loss + auxiliary_loss + actual_n_valid
  -> CanonicalGAWindowPlan.objective(...)
  -> exactly one grad_scaler.scale(L_member).backward()
  -> success-only detach/atomic reconcile
```

`S0` 是 native consumer：它计入 row/member/window/actual count，但 Local prefix 必为 `None`。PAD 不产生 payload、plan、prefix、native forward item 或 count。gather 后 identity 必严格为 stream-major `(slot_id, episode_id, consumer_step)`；不得重排以迎合 packer。

每个 native microbatch 对应一个 frozen member，不得将一个 member 拆为多个 native backward，也不得由 trainer 重建 chronology。一个 GA window 仍使用 native `grad_accum_iter` 的 DDP-sync、member clock、optimizer/zero-grad cadence；它不再对 canonical 已 window-normalized objective 进行第二次 `/GA`。

## 3. P2 精确 child 白名单与职责

P2 只能修改下列 child 文件及紧邻的指定测试；任何需要扩展白名单的发现必须 fail closed 并新建设计 Gate：

| 文件 | P2 唯一职责 |
| --- | --- |
| `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py` | 仅复用既有 immutable plan/count/gather/transaction public ABI；不得把 metadata double 变成 dataset 或 runtime owner。 |
| `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py`（新） | 定义 immutable production input/output dataclass、`SegmentBatchProducer`、native payload/Local-prefix assembly 与 fail-closed identity/count validation。 |
| `cosmos_framework/model/generator/omni_mot_model.py` | 新增独立 canonical-production forward 分支；在现有 `_compute_losses()` 的 consumer/auxiliary 边界返回分离标量，绝不改 ordinary path 的 reduction。 |
| `cosmos_framework/trainer/__init__.py` | 新增独立 canonical-production backward dispatcher，复用 DDP/GA outer loop，执行单次 scaled backward 与 success-only transaction disposition。 |
| `cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py`（新） | CPU/static producer, gather, prefix, identity/count 证据。 |
| `cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py`（新） | CPU/static loss algebra、dispatcher/transaction/No-Local evidence。 |

禁止修改 dataset、dataloader、manifest、真实 producer/cache loader、`packers.py`、config、optimizer selector、checkpoint、旧 active wiring、runtime sidecar 或训练入口。若现有 `_pack_input_sequence()` 无法消费 adapter 已验证的 gathered lists，P2 必须显式失败；不得改 `packers.py` 或引入按 PAD 填充的兼容路径。

## 4. Dataclass 与输入输出 ABI

`CanonicalProductionSegmentInput` 是 P2 CPU/static 的唯一 model 入参 capability，字段为：

```text
member: MicrobatchPlanMember                 # exact frozen identity/count authority
segment_batch: SegmentBatch                  # [B_stream,T] chronology evidence container
consumer_payloads: tuple[NativeConsumerPayload, ...]
local_prefixes: tuple[Tensor | None, ...]    # same length; S0=None
consumer_identities: tuple[(slot, episode, step), ...]
actual_n_valid: int
```

构造者 `SegmentBatchProducer.build(input)` 必先调用 `member.validate_batch(segment_batch)`，随后只可从 `consumer_valid` positions 作 stream-major gather；它必须断言五方相等：`member.planned_n_valid == actual_n_valid == len(payloads) == len(prefixes) == len(identities)`。它不加载 cache、不读 manifest、不采样 episode，也不生成 scheduler plan；其 payload 只来自调用者已物化的 in-memory CPU/static fixture。

`CanonicalProductionForward` 必须返回：

```text
consumer_loss: Tensor       # existing native flow terms + existing one-time sample scaling
auxiliary_loss: Tensor      # only existing load-balancing terms
actual_n_valid: int
member_index: int
transaction: CanonicalBatchWindowTransaction
adapter_commit: callable    # post-backward numeric fast-state detach/commit only
```

任何 capability 缺字段、重复/非 stream-major identity、S0 非-None prefix、PAD payload、count mismatch、非有限 scalar 或过时 transaction 均应在 backward 前抛出 `CanonicalSegmentContractError`；不得回退 ordinary path。

## 5. Model 与 native packer seam

`OmniMoTModel.training_step()` 的新分支只在 `config.local_ttt_enabled` 且 data batch 具有精确 `canonical_production_segment_input` capability 时激活；输出键必须为新的 `canonical_production_segment_forward`，不得复用历史 `canonical_segment_forward`。没有该 capability 时 No-Local/ordinary path 必逐行维持现有行为。

adapter 以 gather 后 tuple 的原始顺序建立现有 native `sequence_plans`、`gen_data_clean` 及 per-sample Local-prefix list，并调用现有 `_pack_input_sequence()`；它不得直接调用或复制 `pack_input_sequence()`。P2 必须在 pack 前后证明列表长度和 identity 无变化。`local_memory=None` 表示 S0 prefix absent；禁止零 token、dummy prefix 或混合 S0/PAD 的 sentinel。

模型的 canonical branch 必须在 `_compute_losses()` 已完成所有 flow modality scale 与可选的一次 sample-level scale 后，且在 `:1835-1850` load-balancing 加入点保留独立 scalar：

```text
consumer_loss = scaled flow consumer aggregate
auxiliary_loss = sum(load-balancing terms only)
```

不得对 native `total_loss` 做 valid-count weighting、不得二次 sample/DDP scale；ordinary `_compute_losses()` 返回/调用方语义不变。

## 6. Trainer、GA、异常与提交

在现有 DDP-sync context 内，canonical-production dispatcher 仅接受上述完整 `CanonicalProductionForward`。它按 frozen plan 调用：

```text
L_member = plan.objective(member_index, consumer_loss, auxiliary_loss, actual_n_valid)
grad_scaler.scale(L_member).backward()       # exactly once
```

canonical branch 不得执行 ordinary `loss / grad_accum_iter`。full-valid 每 member 的 consumer 和 auxiliary 系数均为 `1/GA`；不等 valid 时 consumer 为 `N_valid_i/N_valid_window`，auxiliary 始终为 `1/GA`。DDP sync last-member rule、native GA counter、optimizer step 及 zero-grad cadence 必保持现状。

backward 抛异常、non-finite、identity/count failure、未证明 GradScaler outcome 或 post-backward commit failure：transaction 必 terminalize，清该 window slow grads，抑制剩余 members，且不 reconcile scheduler frontier 或 detach fast state。仅 member 0、backward 前、显式 transient source failure 可由 `CanonicalBatchWindowTransaction` 获得 attempt-1；later-member 或已开始 backward 的失败绝不 suffix retry。successful backward 后才执行 `adapter_commit`，再 `transaction.mark_reconciled()`；顺序反转即 fail closed。

P2 不实现真实 optimizer-step/GradScaler telemetry；若 CPU/static shim 无法证明 success/skip 分支，测试只能验证其 fail-closed disposition，真实 Option-B GPU 语义留给 P3 design。

## 7. P2 CPU/static 验收矩阵

1. `B=2,T=3` mixed S0/non-S0/PAD：stream-major gather exact，S0 count/payload 但 `None` prefix，PAD 零 payload/plan/forward。
2. member identity/provenance/count 的 forged、reordered、foreign、stale、duplicate、S0-prefix 和 PAD-leak negatives 均在 backward 前拒绝，且无 transaction mutation。
3. native loss split fixture：full-valid consumer/auxiliary 均为 `1/GA`，绝非 `1/GA^2`；不等 `N_valid` consumer 为 `N_i/N_window`、auxiliary 为 `1/GA`；ordinary No-Local 仍模拟 `/GA`。
4. dispatcher 对一个 member 恰一次 scaled backward；不调用旧 canonical/active dispatcher；DDP member counter 和 optimizer-boundary clock 不变。
5. successful backward 的 `commit -> reconcile` 顺序、first-member pre-backward retry 保持 denominator/index/GA、later/post-backward failure terminalize+clear+suppress。
6. No-Local 不构造 producer、TTT、prefix 或 canonical output key；现有 normal training-step mock 行为不变。

只可运行这些 CPU/static 定向 pytest、目标 `py_compile`、目标 Ruff 与 child/root `git diff --check`。不得在 P2 读取真实 latent/cache/checkpoint 或用 CUDA。

## 8. 后续 Gate

P2 closure 后，才可创建 P3 single-GPU canonical smoke **design**，裁决真实 cache/data materialization、`W_fast` fp32 与 higher-order graph、GradScaler Option-B 观测、显存/吞吐和 stop conditions。runtime sidecar、distributed ownership/world-size change、LIBERO4IN1 training 均仍为独立后续 Gate。

## 9. 审核请求与禁止范围

请求唯一 verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCTION_ABI_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。

本 P1 仅为 docs-only design；明确禁止 child 改动、真实 I/O、CUDA/GPU、torchrun、runtime sidecar、LIBERO4IN1、训练、评测、推理及任何 P3/P4 授权。
