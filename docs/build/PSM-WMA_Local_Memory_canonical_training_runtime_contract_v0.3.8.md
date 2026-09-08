# PSM-WMA Temporal Local Memory Canonical Training & Runtime Contract v0.3.8

**日期**：2026-09-08
**状态**：docs-only remediation design；待同一根仓/child SHA 的独立审核；未授权代码、GPU、真实 checkpoint I/O、训练、评测或推理
**适用分支**：根仓 `V2`
**当前 child 基线**：`80aec090688e3c710c41e1dfd86b6500773db2c7`

## 1. 目的与继承关系

本文件替代
`PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.7.md`
中 recovery `GAWindowPlan` 的构造、分母、slow-step 时机和 retry 分类。
v0.3.7 的 immutable identity、planned/actual valid-count 断言、fast chronology
consumption-authoritative commit、partial slow-gradient discard、禁止 replay/rebind/resample
及其余 v0.3.6 继承合同不变。

本版响应 DS 对 v0.3.7 的 `REQUEST_CHANGES`：新 recovery plan 不能只说“从当前已提交
scheduler 状态重新构造”，而必须给出确定的 member 序列、有效 accumulation 长度、分母与
slow optimizer step 条件。本版仍为 docs-only；禁止 child/runtime/packer/trainer 修改、真实
data/cache/checkpoint I/O、GPU/CUDA/torchrun、训练、评测或推理。

## 2. 普通计划与失败快照

普通 `GAWindowPlan` 的 member 数固定为 `GA`，索引域为 `0..GA-1`。在第一个 backward 前：

```text
members[mu]              = frozen ordered segment identity
planned_N_valid[mu]      > 0
N_window                 = sum(planned_N_valid[0:GA])
GA_effective             = GA
attempt                  = 0
```

任何 member 在 backward 前均必须检查
`actual_gathered_N_valid[mu] == planned_N_valid[mu]`。正常 objective 为：

```text
L_backward_mu = (planned_N_valid[mu] / N_window) * L_consumer_mu
              + (1 / GA_effective) * L_aux_mu
```

若 member `mu` 触发可恢复的 transaction failure，执行 v0.3.7 规定的 abort、保留已经
成功 commit 的 `members[0:mu]`、清空整个 partial slow `.grad`、不作 slow optimizer/LR
step、也不运行旧 plan 的剩余 member。此时必须在异常处理边界持久化以下纯 metadata
snapshot，供 recovery 唯一使用：

```text
failed_plan_id, failed_mu, failed_plan_digest,
uncommitted_members = members[mu:GA],
uncommitted_planned_N_valid = planned_N_valid[mu:GA],
committed_prefix = members[0:mu]
```

未提交 suffix 不是新的 scheduler admission，不得丢弃、重排、替换或与新 episode 混合。
已提交 prefix 不属于 recovery plan，绝不以“补足 GA”名义重跑。

## 3. 唯一 recovery `GAWindowPlan`

在同一 process、同一 rank、同一 manifest/config/source digest 下，唯一允许的 recovery
plan 是：

```text
recovery.members                 = snapshot.uncommitted_members
recovery.planned_N_valid         = snapshot.uncommitted_planned_N_valid
recovery.GA_effective            = len(recovery.members) = GA - failed_mu
recovery.N_window                = sum(recovery.planned_N_valid)
recovery.attempt                 = 1
recovery.predecessor_plan_id     = failed_plan_id
```

因此 recovery plan 只包含失败 member 与当时尚未运行的 suffix，顺序、slot、episode、cursor/
start_step、segment id 和 source identity byte-for-byte 等于 failure snapshot；它绝不追加
新 admission 来凑回原始 `GA`。`recovery.N_window <= 0` 或任何 frozen identity/digest 不同
必须 terminal fail closed。

recovery member 的唯一 objective 是：

```text
L_recovery_mu = (recovery.planned_N_valid[mu] / recovery.N_window) * L_consumer_mu
              + (1 / recovery.GA_effective) * L_aux_mu
```

它的分母和 auxiliary 系数只属于 recovery suffix；先前已丢弃 slow gradients 的 committed
prefix 不参与其中。每个 recovery member 仍在 backward 前检查 actual==planned，并在成功
backward 后提交其 fast chronology/cursor/exposure。

仅当 recovery 的所有 `GA_effective` members 都成功 backward/commit 后，才在该安全边界
尝试**恰好一次** slow optimizer step；若 GradScaler skip，则清 slow grads、不 step optimizer/
slow LR scheduler，随后结束 recovery plan。若该 slow optimizer step 成功，才 step
`slow_lr_scheduler` 一次。无论 step 成功还是 skip，下一普通 plan 才可由此时已提交的
scheduler 状态构造，并恢复固定 `GA_effective=GA`。

## 4. 异常 taxonomy、retry budget 与终止码

为消除 implementation design 前的可观察差异，首版固定以下分类：

| failure class | recovery | terminal code |
| --- | --- | --- |
| 同 digest 的可重读 `LOAD_DECODE_TRANSIENT`（仅首次，`attempt=0`） | 创建第 3 节唯一 suffix recovery plan | 无 |
| 同一 identity 第二次 `LOAD_DECODE_TRANSIENT`（`attempt=1`） | 禁止 | `LOCAL_MEM_RETRY_EXHAUSTED` |
| cache/source identity mismatch、manifest/config digest mismatch、planned/actual mismatch | 禁止 | `LOCAL_MEM_IDENTITY_CONTRACT_FAILURE` |
| inner/native-loss non-finite | 禁止 | `LOCAL_MEM_NUMERICAL_FAILURE` |
| forward/backward exception | 禁止 | `LOCAL_MEM_OUTER_FAILURE` |

任一 terminal failure 必须立即清 slow `.grad`、不作 slow optimizer/LR step、不执行任何
remaining member，并写出 `failed_plan_id`、identity、attempt、class、terminal code 与当前
fast/scheduler provenance。它不得以重排、换 episode、重 bind、随机 resample 或静默跳过来
恢复。`GradScaler` skip 不是该表 failure：它只在完整普通或完整 recovery plan 的 slow-step
判定点发生，按第 3 节处理。

## 5. 补充 CPU/static fixtures

v0.3.7 §4 的五类 fixture 继续必需，并增加以下确定性断言：

1. `mu>0` 的 transient failure：recovery `members` 恰为旧 suffix，`GA_effective=GA-mu`，
   `N_window` 只为 suffix planned counts 之和，prefix 不出现；recovery 成功仅 step 一次；
2. recovery GradScaler skip：所有 suffix fast commits 保留、optimizer/LR iteration 不变，
   之后下一普通 plan 恢复固定 `GA`；
3. recovery 内 `actual!=planned`、identity mutation、non-finite 或 outer exception：验证相应
   terminal code、零 slow `.grad`、无 optimizer/LR step、无 remaining member 执行；
4. 第二次同 identity transient load/decode failure：验证 `LOCAL_MEM_RETRY_EXHAUSTED`，且绝无
   第三次 redelivery。

fixture 必须以 member identity 序列、`GA_effective`、`N_window`、fast-state bytes、cursor/
exposure/queue、slow `.grad`、optimizer/LR iteration 和 terminal evidence 作为观察值；不得
访问真实 data/cache/checkpoint 或 GPU。

## 6. Gate

本版是 v0.3.8 docs-only remediation 的唯一审阅对象。只有 ChatGPT、MM、DS 对同一根仓 SHA
和 child Gitlink 均正式批准，才授权新建下一 CPU/static implementation design；实现代码、
真实 I/O、GPU、训练与后续 Gate 继续禁止。
