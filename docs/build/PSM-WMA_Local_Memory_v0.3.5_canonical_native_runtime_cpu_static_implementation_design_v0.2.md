# PSM-WMA Local Memory v0.3.5 Canonical Native Runtime CPU/static Implementation 设计 v0.2

**状态**：docs-only remediation；supersede v0.1；须三方新 SHA批准。
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-RUNTIME-CPU-STATIC-IMPLEMENTATION-DESIGN`

## 1. 白名单与补强原因

v0.1 的 six-file scope不能合法表达“已 committed prefix 后的 suffix recovery”：当前
`CanonicalBatchWindowTransaction.retry_first_member_pre_backward()` 仅接受未启动 full window。因此本次仅将
以下两个 scheduler contract 文件加入原六文件白名单：

```text
cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py
cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler_test.py
```

其余 v0.1 whitelist、candidate seam `omni_mot_model.py:1434` 与 trainer `:520-523` hard-stop、synthetic
CPU/static-only 与全部真实执行禁令不变。不得改 dataset/collate/packer/config/checkpoint/sidecar，也不得让
native model/loss/backward、optimizer或scheduler step可达。

## 2. 唯一公开 suffix recovery ABI

`CanonicalBatchWindowTransaction` 新增唯一公开 `derive_suffix_recovery(member_index)`，仅由 exact attempt-0
transaction 调用，且前置为：

```text
attempt == 0
member_index == len(completed_members)
completed_members == range(member_index)
active backward member is None
member_index > 0
declared failure kind == retryable source transient
```

它一次性关闭 original transaction，并产生不可变 typed `CanonicalSuffixRecovery`：

```text
original_plan / original_transaction / original_transition identity
suffix_plan.members == original_plan.members[member_index:]
suffix_plan.attempt == 1
suffix_plan.plan_chain_id == original_plan.plan_chain_id
suffix_plan.N_window == sum(suffix planned_n_valid)
suffix_plan.GA_effective == len(suffix members)
recovery transaction bound only to suffix_plan
```

suffix members保留 original member object、identity、order与 planned count；recovery adapter request 的 local
`member_index` 从零开始，但另绑定 immutable original member index，禁止用新 admission/recount/resample/private
state重建。recovery capability仅可消费一次；attempt-1、member0-before-any-commit、active backward、terminal/
nontransient/count/identity/nonfinite failures均拒绝派生。恢复成功只允许 recovery transaction逐 member reconcile，
并由 one-shot original transition reconciliation receipt 关闭原 transition一次；不得把已 committed prefix再扫描、再写
fast state或再清理。

adapter 的 `CanonicalProductionRetryCapability`/`consume_retry()` 必须扩展为仅消费上述 typed
`CanonicalSuffixRecovery`；保留旧 `retry_first_member_pre_backward()` 的未启动 full-window语义给旧测试，不得将其
误当新 suffix API。任何 foreign/stale/double consume/request-plan-member mismatch 在 scan前 fail closed。

## 3. failure、fast state 与 slow-grad disposition

已完成 prefix members的 post-backward `commit_success()` fast state保持。derive suffix 时原 transaction 只执行一次
controlled partial slow-grad discard，并抑制 remaining original members与 slow optimizer/LR；它不回滚 frontier。
recovery member成功时仍先 simulated backward、后 `prepare_commit/commit_success`。attempt-1任意失败或其他 terminal
failure只 terminalize，不创建新 suffix/attempt-2/normal plan；不得执行 slow step。

S0 `None` prefix、PAD absence、stream-major identity、per-stream continuation和无 ordinary Local payload继续继承
v0.1。scaler/optimizer仍是 pre-scan sentinel rejection；不实现真实 GradScaler Option-B。

## 4. 非退化的强制 scaling witnesses

两条路径均必须用**非等 planned valid counts**与**非零 auxiliary**：

```text
normal:   planned=(2, 5), N_window=7, GA_effective=2, auxiliary!=0
recovery: original planned=(2, 5, 3), committed prefix=member0,
          suffix planned=(5, 3), N_window=8, GA_effective=2, auxiliary!=0
```

每个 member断言精确数值：

```text
planned_n_valid[i] / N_window * primary_consumer_mean + auxiliary_loss / GA_effective
```

并通过 spy 证明没有 ordinary trainer `/grad_accum_iter`、第二 `/GA`、ratio shorthand或第二 backward。full-valid
normal `(L_consumer+L_aux)/GA` 是额外 witness，不能替代上述两个非退化矩阵。

## 5. 请求 verdict

请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_RUNTIME_CPU_STATIC` 或
`REQUEST_CHANGES(file:line)`。批准只授权扩展后的八文件 synthetic CPU/static implementation；不授权真实
runtime/I-O/GPU/forward/backward/optimizer/sidecar/训练。
