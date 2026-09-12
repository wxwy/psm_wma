# PSM-WMA Authority Root PASS 线性化设计 v0.10

**日期**：2026-09-12  
**状态**：docs-only；待三方复审。  
**Gate**：`G0-R09-B-TTT-V035-PASS-LINEARIZATION-DESIGN`

本文件 supersede v0.9 的 §3 pre-swap drift 测试语义，关闭其 exact-pair 唯一 HIGH。v0.9 的单一 terminal-state cell、A/B/C crash table、v0.8 对外 ABI、internal capability、permanent fail-stop、四文件 CPU/static 范围及全部禁止范围保持。

## 1. 单一 authority terminal-state cell

`EvidenceCommit`与私有`AcceptedPass`不独立持有可变 `committed/issued/consumed` boolean/enum。pre-commit 时创建一个不可变 `AuthorityTerminalState` 实例：

```text
PENDING = {accepted=False, rollback_enabled=True, preserve_refs=False,
           witness_returnable=False}
ACCEPTED = {accepted=True, rollback_enabled=False, preserve_refs=True,
            witness_returnable=True}
```

每个 issued witness/commit/pass共享同一 authority-owned cell 引用。唯一语义提交是一次不可抛出的指针替换：`terminal_state = ACCEPTED`。`EvidenceCommit.committed`、AcceptedPass issued/consumed、rollback allowed、preserve refs与witness return eligibility全部仅从该cell派生；不存在独立 consume 写入。`AcceptedPass.consume()`只检查 `terminal_state.accepted` 并返回，不改变状态。

任何 `BaseException`/process interruption 只能发生在 pointer swap 前（完整 PENDING）或后（完整 ACCEPTED），不会出现字段组合。CPU/static必须在所有可见边界注入普通/custom/`BaseException`，证明只可观察 PENDING 或 ACCEPTED。

## 2. guard、terminal state与崩溃窗口

v0.7 的 guard ordering 在此显式替换：guard transition 是最后一个 fallible pre-state action；其成功不等于 acceptance。其后立即进行单一 pointer swap，期间不允许 callback/I-O/allocation/validation。

| 窗口 | durable guard/evidence/refs | terminal state | restart 动作 |
|---|---|---|---|
| A：guard transition 前 | guard存在；refs可为owned candidate或已rollback | PENDING | 既有 rollback/retry lease 规则 |
| B：guard transition 成功后、pointer swap前 | guard缺失、final Evidence-v1存在、refs为最后owned/observed状态 | PENDING | deterministic permanent fail-stop；不得retry/close/train；只允许 `PASS-CLOSURE-RECOVERY-DESIGN` |
| C：pointer swap后、return前/后 | guard缺失、final Evidence-v1存在、refs为最后owned/observed状态 | ACCEPTED | preserve refs；若进程丢失同样 permanent fail-stop，禁止自动推断或重放 |

restart detection只依赖 exact combination：guard存在→A；guard缺失且候选 evidence bytes存在→B/C 不可由path区分，**一律 fail-stop**。不允许把 Evidence-v1、refs或path verifier反推 acceptance；recovery Gate 才能人工区分B/C。

## 3. ref witness：observation-only 的明确边界

选择 **observation-only witness**。`AcceptedPass`绑定的唯一 ref 事实是 pointer swap **之前最后一次** local/remote `== candidate` 精确观察及其时间/endpoint。该最后观察之后不再有 ref I/O、namespace lock或额外验证；pointer swap只消费这个历史 witness。因此无论外部 drift 发生在最后观察后、pointer swap前，还是 swap后，均不改变该历史事实，也不撤销已准备的 transition。

这不是对“当前 refs exact”的声明：后续任何 ref check 一旦发现与 candidate 不同，均定义为 external corruption，必须 fail-stop/recovery；不得静默接受为当前 exact refs、自动修复或 rollback 已 ACCEPTED terminal state。pre-swap drift在其发生瞬间不可被 authority 观察，故不能要求 PENDING 分支检测或回滚；只有在它发生于最后观察**之前**且该观察失败时，既有 pre-state rollback 才适用。

保留 exact-old CAS 只证明本activation的创建/删除 ownership；不把它误称为跨外部actor的namespace lock。后续 consumer/restart需要当前 ref truth时必须单独读取并在不一致时fail-stop；不得从此 witness 推断当前 namespace。

## 4. 验收与范围

后续仅四root文件temporary CPU/static implementation必须验证：

1. 所有 acceptance/ref/rollback/witness属性由一个terminal-state cell派生，无独立semantic state write；
2. A/B/C每个crash窗口的guard/evidence/refs与restart predicate；B/C均不可自动retry/close/train；
3. guard transition前后、pointer swap前后每个BaseException injection只得到PENDING或ACCEPTED；
4. last exact observation**之前**的local/remote drift令pre-state validation失败并按既有rollback；last observation**之后**（含pointer swap前）drift可按历史 witness进入ACCEPTED，但任意后续ref check必须报告external corruption/fail-stop，且不得rollback该 ACCEPTED cell；
5. v0.8 ABI、opaque private capability、path observation-only ABI不回归。

请求唯一 verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PASS_LINEARIZATION_CPU_STATIC`或`REQUEST_CHANGES(file:line)`。三方同SHA前禁止实现、真实source/candidate/ref/evidence、child/runtime、CUDA/GPU、训练、评测、推理或LIBERO4IN1。
