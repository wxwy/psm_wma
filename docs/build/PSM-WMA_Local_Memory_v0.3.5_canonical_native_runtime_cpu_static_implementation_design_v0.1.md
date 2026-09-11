# PSM-WMA Local Memory v0.3.5 Canonical Native Runtime CPU/static Implementation 设计 v0.1

**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-RUNTIME-CPU-STATIC-IMPLEMENTATION-DESIGN`
**状态**：docs-only；须由三方对本文件的新 formal root/Gitlink 批准后，才可开启独立 CPU/static implementation Gate。
**前置**：root `5fd23a289c4197a7a8887ec61d318c769f7c90e8` / Gitlink
`c0e6e55cbab00b7d40eccacc0de1c4c91b66f9d9` 的三方
`APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_RUNTIME_CPU_STATIC_IMPLEMENTATION`。

## 1. 实现授权边界

后续 implementation Gate 仅允许 synthetic CPU/static typed-contract；禁止真实 native forward/loss/backward、
真实 data/cache/checkpoint I/O、CUDA/GPU、torchrun、optimizer/scheduler step、training/evaluation/inference、
runtime sidecar/distributed/LIBERO4IN1。`omni_mot_model.py:1434` 与 `trainer/__init__.py:520-523` 必须继续
fail-closed，禁止用删除 guard 或 ordinary `/grad_accum_iter` 落入路径替代实现。

唯一可修改白名单：

```text
cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py
cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py
cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py
cosmos_framework/model/generator/omni_mot_model.py
cosmos_framework/trainer/__init__.py
cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py
```

其中 model/trainer 仅可新增 CPU/static dispatch guard/witness seam；不得让 production marker 可执行真实
pack/noise/model/loss/backward。不得改 scheduler、dataset/collate、packer、config、checkpoint、sidecar、
legacy active-wiring 或其他文件。

## 2. 唯一 typed runtime transaction

复用 `CanonicalProductionAdapter`、`CanonicalProductionSegmentRequest`、
`CanonicalNativePreparedInputs`、`CanonicalProductionCommitCapability` 和
`CanonicalProductionRetryCapability`。新增的 typed runtime capability 必须 object-bind：

```text
exact adapter/request/result/prepared
original CanonicalGAWindowPlan + CanonicalBatchWindowTransaction
member index + frozen member identity + planned_n_valid
normal/recovery plan kind + attempt
per-slot candidate state/prefix identity
one pre-backward / post-backward disposition
```

它不得从 `data_batch`、generic DCP 或 caller supplied counts 重建 authority；foreign/stale/duplicate capability、
carrier/traversal/count/prefix mismatch 一律在任何 simulated backward 前 fail closed。S0 prefix=`None`、PAD 无
carrier/prefix/loss、valid consumer flat order=`b*T+t`，继续复用 adapter 的 exact traversal。

## 3. normal 与 suffix-recovery state machine

normal attempt-0 只调用一次现有 scheduler freeze/admission，生成 immutable `CanonicalGAWindowPlan`。每个
member 仅消费该 object 的相应 index；不得 per-member freeze/admit、resample、recount或第二 transition。

```text
PREPARED(member i) -> BACKWARD_STARTED(i) -> BACKWARD_COMPLETE(i)
-> typed prepare_commit -> typed commit_success -> next frozen member / window complete
```

唯一 retry 入口是 attempt-0 的 declared transient source failure。它只调用现有 exact retry capability，派生
unconsumed suffix；attempt-1 只 `consume_retry()` 一次，保留 original scheduler/transition、identity/order/count。
它不能重写已 committed fast state，成功 suffix member仍只能在 simulated backward success 后恰好一次
detach/commit自身 candidate state。attempt-1 或任意 non-transient/identity/count/nonfinite/backward failure均
terminal，无 attempt-2/new window。

terminal/recovery disposition 必须：保留已 commit fast state；对 failed original transaction 的 controlled partial
slow grads 恰好 discard 一次；抑制 original remaining members和 slow optimizer/LR；recovery success 恰好
reconcile original transition 一次。该 Gate 只由 spy/typed fake 验证，不触达真实 optimizer。

## 4. objective 与 synthetic backward contract

唯一 simulated objective 由 frozen plan 产生：

```text
primary_scale = planned_N_valid[member] / N_window
auxiliary_scale = 1 / GA_effective
objective = primary_scale * primary_consumer_mean + auxiliary_scale * auxiliary_loss
```

normal `GA_effective=GA`；recovery `GA_effective=len(recovery.members)`；各自的
`N_window=sum(planned_N_valid)`。actual 必须在 objective 前等于 planned。full-valid normal witness 必须还原
`(L_consumer+L_aux)/GA`。不能组成 ratio shorthand、二次 `/GA`、ordinary trainer loss division或第二 backward。
`L_inner` 仅影响 candidate fast state，绝不进入 objective。

scaler/optimizer input 只能以 CPU/static sentinel 表示。enabled scaler/real optimizer 等现有 hard-stop仍须在
scan/model/callback/backward 前拒绝；本 Gate 不实现受控真实 scaler disposition。future implementation 需要另行
Gate 才能把 verified objective 接进 native lifecycle。

## 5. 最小 CPU/static 测试矩阵

定向 tests 必须覆盖：

1. normal 多 member 的 single freeze/admission、exact member consumption和 valid count/formula；
2. S0/continued/PAD 的 prefix/state/stream-major identity，跨 stream 无 shared update；
3. 成功 backward 后才 commit/detach，duplicate/foreign/stale capability 零 mutation；
4. attempt-0 在已有 successful member 后 transient：exact suffix、committed prefix retain、partial grad clear 一次、
   recovery `N_window/GA_effective` 和 original reconciliation 一次；
5. attempt-1、identity/count/nonfinite/backward failures terminal、无 suffix/refreeze/admission/new transition/slow step；
6. candidate seam继续 hard-stop、legacy Local payload和 ordinary GA branch不可达；enabled scaler或 optimizer在
   scan 前拒绝。

验证命令在 implementation Gate 批准后冻结为指定 pytest selection、Ruff、target `py_compile`、child/root
`git diff --check`。此设计本身不运行项目代码。

## 6. 请求 verdict

请求：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_RUNTIME_CPU_STATIC
```

或 `REQUEST_CHANGES(file:line)`。即使批准，也只授权上述白名单 synthetic CPU/static implementation；不授权
真实 runtime、hard-stop removal、I/O、GPU、optimizer、sidecar、训练或 LIBERO4IN1。
