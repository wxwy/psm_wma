# PSM-WMA Temporal Local Memory Canonical Training & Runtime Contract v0.3.7

**日期**：2026-09-08  
**状态**：docs-only remediation design；待同一根仓/child SHA 的独立审核；未授权代码、GPU、真实 checkpoint I/O、训练、评测或推理  
**适用分支**：根仓 `V2`  
**当前 child 基线**：`80aec090688e3c710c41e1dfd86b6500773db2c7`

## 1. 目的与继承关系

本文件仅替代
`PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.6.md`
的 §4、§5、§6 中 GA-window 失败、valid-count 绑定和慢梯度事务的语义。
v0.3.6 其余全部 chronology、`S_t <- e_(t-1)` ABI、`training_stream_end`、sparse
Local-absent、feature-disable、runtime-sidecar 与禁止范围保持原样有效。

本版响应 ChatGPT 对 v0.3.6（root `bc252114b6799559a172a3061677562c8df565a2`，
Gitlink `80aec090688e3c710c41e1dfd86b6500773db2c7`）的唯一 HIGH：先前没有冻结
GA-window 后续成员失败时固定分母、已累计 slow gradient 和已提交 fast chronology
之间的事务边界。它不授权 child/runtime/packer/trainer 代码修改，也不授权任何真实
数据、cache、checkpoint I/O、CUDA、torchrun、训练、评测或推理。

## 2. 不可变 `GAWindowPlan`

每个 slow-gradient accumulation window 在执行其第一个 Local-path backward 前，必须由
rank-local `WeightedDeficitScheduler` 构造一个不可变的 `GAWindowPlan`：

```text
window_id
members[mu] = ordered segment identity
              (slot_id, episode_id, cursor/start_step, segment_id,
               manifest/config/source-identity digest)
planned_N_valid[mu] > 0
N_window = sum(planned_N_valid[mu])
```

`members` 的顺序、identity 与 `planned_N_valid` 都是 frozen metadata，不以 tensor
预加载来计数。`N_window <= 0` 必须在任何 forward/backward 前 fail closed。一个 member
实际进入 Cosmos gather/loss seam 后，必须在其 backward 前断言：

```text
actual_gathered_N_valid[mu] == planned_N_valid[mu]
```

不相等属于 transaction failure；该 member 在 failure 前不得贡献 slow gradient 或
fast-state/cursor/exposure commit。不得通过修改本 window 的分母、补塞其他 sample、换
episode 或随机重排来“修正”该不等式。

正常路径的唯一 objective 仍是：

```text
L_backward_mu = (planned_N_valid[mu] / N_window) * L_consumer_mu
              + (1 / GA) * L_aux_mu
```

Local path 的该 objective 已由 segment-loss seam 唯一缩放，禁止 trainer 再除
`grad_accum_iter`；非 Local path 保持旧行为。

## 3. GA-window 事务与失败路径

一个 member 只有在其 valid inner transition/candidate `W_fast` 有限、未缩放 native
model loss 有限、`actual==planned`、outer backward 正常返回并通过 identity 校验后，才
可以提交该 member 的 detached `W_fast`、cursor、queue 与 exposure。此前成功 member 的
fast chronology commit 是 consumption-authoritative，**绝不因为之后 member 失败而回滚**。

下列任一事件是 `GAWindowPlan` 的 transaction failure：load/decode/cache identity failure、
inner non-finite、`actual!=planned`、forward exception、native-loss non-finite 或 backward
exception。发生在 member `mu` 时必须按以下固定次序处理：

1. 当前 `mu` candidate abort：其 `W_fast`、cursor、queue、exposure 和 rebind 状态保持
   failure 前值，且不得 partial commit；
2. 已成功 `0..mu-1` 的 fast chronology/cursor/exposure commit 保留；它们不 replay、不
   rollback、不换 episode；
3. 立刻清零/丢弃本 window 已累计的全部 slow `.grad`；本 window 不得调用 slow
   optimizer step 或 `slow_lr_scheduler.step()`；
4. 本 window 剩余 `mu+1..GA-1` members 一律不执行（不能在旧 `N_window` 下继续）；
5. 在安全异常处理边界重新从当前**已提交** scheduler 状态构造新 `GAWindowPlan` 与新
   `N_window`。未提交的当前/剩余 segment 只可按原 slot、episode、cursor、identity 的
   确定性重送进入新 window；不得随机 replay、rebind、resample、跳过或以其他 episode
   填充。

若同一 frozen identity 的 deterministic redelivery 再次触发 load/decode/cache identity
failure，或 identity digest 改变，run 必须 fail closed 并保留失败证据；不得无限重试。
具体 retry budget、异常分类与终止码是下一 CPU/static implementation design 的冻结项，
但不得改变上述“partial slow window 丢弃、fast commit 保留、未提交 identity 不变”的
算法语义。

`GradScaler` skip 不是上述 transaction failure：它只发生在一个完整、无上述 failure 的
window 的 slow step 判定点。其既有语义不变：保持所有已成功 fast chronology commit，清
slow grads，不执行 slow optimizer 或 `slow_lr_scheduler` step；新 window 正常重新规划。

## 4. 必需的 CPU/static acceptance fixtures

后续 CPU/static implementation design 至少须把下面 fixture 冻结为可运行测试，且不访问
真实 cache/checkpoint/data：

1. **全成功**：每 member `actual==planned`，验证加权 objective、单次 slow optimizer/LR
   step、每个 fast chronology commit 与下一 window 计划；
2. **首 member failure**：`mu=0` 在 backward 前或中失败，验证无 fast commit、`.grad`
   全零、optimizer/LR iteration 不变、余 member 未运行，以及 deterministic 新计划的
   `N_window`；
3. **后续 member failure**：至少一个 member backward/commit 成功后，`mu>0` 失败，验证
   前序 fast state/cursor/exposure byte-identical 保留，当前及余 member 未提交，`.grad`
   全零、optimizer/LR iteration 不变，且新计划只重送未提交 identities；
4. **planned/actual mismatch**：在 gather/loss seam 注入不等，验证在该 member backward 与
   fast commit 前 fail，遵循第 3 节 partial-window 清理；
5. **identity mutation/retry failure**：验证不会以 rebind/resample 掩盖异常，第二次同一
   identity failure 或 digest 不同必须 fail closed。

fixture 必须同时观察 fast-state bytes、scheduler cursor/exposure/queue、slow `.grad`、
optimizer iteration、slow LR scheduler iteration、执行过的 member identity 序列和新 window
denominator。真实训练、GPU、P4/P5、B2-T 与 LIBERO4IN1 不属于这些 fixture 的范围。

## 5. Gate 与批准请求

本版是唯一允许送审的 v0.3.7 docs-only remediation design。只有 ChatGPT、MM、DS 对同一
root SHA 和上述 child Gitlink 均给出该 Gate 的正式批准，才可新建下一步 CPU/static
implementation design；仍不等于批准实现代码、真实 I/O、GPU 或训练。
