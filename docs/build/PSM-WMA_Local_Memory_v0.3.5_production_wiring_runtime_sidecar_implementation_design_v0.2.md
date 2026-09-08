# PSM-WMA Local Memory v0.3.5 Production Wiring 与 Runtime Sidecar 实现设计 v0.2

**日期**：2026-09-08  
**状态**：docs-only remediation；待三方重新审核；未授权代码、真实 I/O、GPU 或训练  
**Supersedes**：v0.1（formal root `f3d74c0`）仅作为 source-audit 框架；本版为唯一 implementation-ready design。  
**任务/Gate**：`G0-R09-B-TTT-V035-PRODUCTION-WIRING-RUNTIME-SIDECAR-DESIGN`

## 1. 唯一 authority 与精确范围

本版以 detailed addendum v0.3.5、production-migration v0.2 和已关闭 v0.5 formal pair `90e34f4 / d05f14e` 为 authority。仅在本文件获同 SHA `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_WIRING_CPU_STATIC` 后，允许实施下列八个 child 路径；全部未列路径不变且不得调用：

1. 新建 `cosmos_framework/model/generator/mot/production_segment_wiring.py`：`CanonicalSegmentWiring`、`CanonicalSegmentForward`、`build_segment_batch_for_test`，纯 in-memory bridge；
2. 新建 `cosmos_framework/model/generator/mot/production_segment_wiring_test.py`；
3. 修改 `cosmos_framework/model/generator/omni_mot_model.py`：仅新 private `_canonical_local_memory_segment_forward(data_batch, sequence_plans)`；
4. 修改 `cosmos_framework/model/generator/omni_mot_model_test.py`（若不存在则新建相邻同名 test）；
5. 修改 `cosmos_framework/trainer/__init__.py`：仅新 private `_run_canonical_segment_backward(...)` 与 `training_step()` 的受控分支；
6. 新建 `cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py`；
7. 修改 `cosmos_framework/model/generator/mot/local_memory_segment_adapter.py`：仅允许为 coordinator 增加只读 `pending` inspection；scan/commit ABI、sidecar schema不得改；
8. 修改其相邻 test 仅补生产 bridge fixture。

禁止修改 config/default/recipe/registry/optimizer selector/dataset/manifest/checkpoint/C6/`ttt_lifecycle.py`/`production_runtime_adapter.py`/`runtime_authority.py`，也禁止真实 data/cache/checkpoint I/O、GPU、torchrun、训练。

## 2. 唯一 selector 与 supersession

canonical segment path 不新增配置键：仅在 `data_batch["canonical_local_memory_segment"] is True` 时由 `OmniMoTModel._canonical_local_memory_segment_forward` 进入；否则保留现有语义。该 test-only marker 只能由 `build_segment_batch_for_test` 构造，生产 dataloader不得写入，故本 Gate 不使实际训练路径可达。

优先级精确为：

```text
local_ttt_enabled is False -> 原 disabled route，绝不构造 wiring/adapter/TTTLifecycle
local_ttt_enabled is True and canonical_local_memory_segment is True
  -> canonical wiring；不得调用 _ttt_local_memory_tokens，不得构造 _ttt_lifecycle，
     不得调用 TTTLifecycle.process_sample
local_ttt_enabled is True and marker absent
  -> 保持旧 _ttt_local_memory_tokens 路径，不改变其行为
```

这是一条 test-only coexistence bridge，不是对旧 production route 的授权替换；真正 dataloader selector/config 另起 Gate。

## 3. 精确对象 ABI 与调用序

`CanonicalSegmentWiring.__init__(adapter: CanonicalLocalMemorySegmentAdapter)` 只持有 in-memory adapter。`prepare(segment: SegmentBatch, identity: SegmentIdentity, transaction: LocalMemoryTransaction) -> CanonicalSegmentForward` 调用 `adapter.scan` 一次并返回 frozen `CanonicalSegmentForward(payloads: tuple[Any,...], locals: tuple[Tensor|None,...], identities: tuple[tuple[int,str,int],...], result: SegmentScanResult)`；其字段仅来自 `SegmentScanResult`，不复制 opaque payload。

`OmniMoTModel._canonical_local_memory_segment_forward` 接收 `data_batch["canonical_segment"]: SegmentBatch`、`["canonical_identity"]: SegmentIdentity`、`["canonical_transaction"]: LocalMemoryTransaction`、`["canonical_wiring"]: CanonicalSegmentWiring`，先 `prepare`，再以 stream-major gathered payload/local token **恰好一次**调用既有 native training forward helper；其返回 `(output_batch, primary_consumer_mean, auxiliary_loss, actual_n_valid, wiring_forward)`。`actual_n_valid == len(payloads) == sum(segment.consumer_valid)`，S0 local=None，PAD 不出现。此 test-only helper 不读取/写入 filesystem。

trainer 仅在 output 含 `canonical_segment_forward` 时调用 `_run_canonical_segment_backward(plan, member_index, primary_consumer_mean, auxiliary_loss, actual_n_valid, transaction, identity, wiring_forward, clear_slow_grads)`；成功后唯一执行 `wiring.adapter.commit(identity, result, transaction=transaction)`。其他 output 维持既有 `loss / grad_accum_iter` 路径。

## 4. 精确 loss ABI

`primary_consumer_mean_i` 是 native forward 返回的、仅对该 microbatch gathered valid consumers求 mean 的标量；`auxiliary_loss_i` 是 native forward 显式返回的额外标量，不存在时强制 `torch.zeros_like(primary_consumer_mean_i)`。`N_valid_i=actual_n_valid`，`N_valid_window=plan.n_window`，`GA_effective=plan.ga_effective`，且执行前 `transaction.validate_success` 强制 `N_valid_i==plan.planned_n_valid[i]`。

唯一 backward scalar：

```text
L_i = (N_valid_i / N_valid_window) * primary_consumer_mean_i
      + auxiliary_loss_i / GA_effective
```

在任何缩放前对 `primary_consumer_mean_i` 作 finite predicate；canonical branch 不得再除 `grad_accum_iter`、不得二次 backward。full valid 且 `N_valid_i` 相等时主项严格退化为 `primary_consumer_mean_i / GA_effective`。异常、non-finite、identity/count mismatch、backward error、GradScaler skip 一律不 commit state；existing v0.5 taxonomy/clear_slow_grads owner不变。

## 5. coordinator 生命周期与 sidecar 边界

coordinator 在 test fixture 中每个 synthetic GAWindowPlan 创建一次；只允许一个 open `CanonicalSegmentForward`。`prepare` 后 failure/skip 调用 `adapter.commit` 必须失败；成功 backward 后 commit；terminal success 由 adapter 删除 slot state。下一 microbatch重新创建 coordinator但复用同一 in-memory sidecar；state graph不得跨 microbatch。不得新增任何 save/load、resume、rank/world-size、checkpoint identity 或持久化字段。

## 6. CPU/static 验收

1. `[B=2,T=3]` fixture经 exact selector 证明 legacy lifecycle未构造；stream-major gather、S0=None、PAD零 forward token、opaque identity保持。
2. spy native forward只调用一次，输入仅 `(payloads, locals)`；不得构造 state/dt/age。
3. 两成员 unequal-valid plan：显式 mean `p0,p1` 验证 `N0/Nwindow*p0 + N1/Nwindow*p1`，aux 项仅 `/GA_effective`；full batch退化为每成员 `/GA_effective`，无 `/grad_accum_iter`。
4. successful backward 后才 sidecar commit；forward/backward/nonfinite/count/identity/skip失败保留 prior carry、零写。
5. disabled selector不构造 wiring/adapter/lifecycle，native output/loss/input gradient parity。

仅准许 `LD_LIBRARY_PATH='' .venv/bin/python -m pytest` 指定 CPU tests、指定 `py_compile`、child/root `git diff --check`。不运行模型、数据、cache、checkpoint、GPU 或训练。

## 7. 审核请求

请求三方对本 docs-only formal pair 返回 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_WIRING_CPU_STATIC` 或 `REQUEST_CHANGES`（附 `file:line`）。任何批准仍不授权 runtime-sidecar persistence、真实 I/O、GPU smoke 或 LIBERO4IN1 training。
