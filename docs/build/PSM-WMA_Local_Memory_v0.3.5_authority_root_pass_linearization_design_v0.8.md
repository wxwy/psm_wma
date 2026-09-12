# PSM-WMA Authority Root PASS 线性化设计 v0.8

**日期**：2026-09-12  
**状态**：docs-only；待三方复审。  
**Gate**：`G0-R09-B-TTT-V035-PASS-LINEARIZATION-DESIGN`

本文件 supersede v0.7 的 `AcceptedPass` 对外返回/生命周期表述，关闭其 exact-pair review 的三项 HIGH。v0.3--v0.6 的 raw bytes/OID、fixed-ref lease、四文件 allowlist、Evidence-v1 bytes ABI 与全部禁止范围保持；本文件不授权实现、真实操作或 child 改动。

## 1. 公共 ABI 与状态机

`publish_candidate(request, candidate, binding, git, finalizer=None)` **保持 v0.6 ABI**：成功只返回 exact `PublicationWitness`；finalizer return 永远忽略。它不返回 `AcceptedPass`，外部调用方不能持有、复制、pickle、缓存或重放 capability。

`AcceptedPass` 是 authority 私有、预分配的 `_NonSerializable` 状态对象，精确状态：

```text
prepared -> issued -> consumed
prepared -> expired                 (任一 pre-issuance failure)
issued -> consumed                  (唯一允许路径)
```

对象在 pre-commit 时已绑定：当前 activation identity、exact `PublicationWitness`、candidate revision、binding digest、sealed evidence FD `(dev,ino)`、evidence SHA-256 与 local/remote exact-candidate witness。构造、copy、pickle、替换 activation、重复 issue/consume、错误 witness/FD/ref binding 一律 pre-issuance `AuthorityRootError`。

activation 从 authority dispatch 开始，到内部 `consume()` 完成或 pre-issuance cleanup 完成才结束；不会把尚可使用的 capability 返回给 activation 外部。

## 2. 唯一总状态转换

在所有 fallible 事项完成后，authority 只允许一次无 I/O、无 callback、无 allocation、无 validation 的 total transition：

```text
prepared AcceptedPass + sealed EvidenceCommit + exact refs
  -- total_transition -->
issued AcceptedPass + committed EvidenceCommit + preserve-refs branch selected
  -- immediate internal consume -->
consumed AcceptedPass + exact PublicationWitness returnable
```

`AcceptedPass`在 pre-commit 阶段预分配并完成所有字段验证；`total_transition`只能写既有对象的内部 enum/boolean 字段，不能抛出。transition 与 `EvidenceCommit.committed=True`、rollback-boundary exit decision 在同一 authority dispatch 内完成。之后不允许 `_rollback`。

紧接 transition 的 `consume()`同样为 total、one-shot 内部状态翻转；它不调用外部代码，也不做 I/O。只有完成 consume 后 `publish_candidate` 才可返回 witness。所有 post-transition finalizer exception、logging/reporting/caller exception 都在 rollback boundary 外，保留 refs，且不能使 capability 回到 prepared/expired。

因此不变量为：

```text
consumed AcceptedPass <=> issued AcceptedPass <=> committed EvidenceCommit
  <=> preserve-refs branch selected <=> exact PublicationWitness may return
```

`verify_evidence_path()`仍是纯 bytes/guard 观察；它不得创建、issue、consume 或替代任何上述状态。

## 3. Closure 与崩溃语义

本设计选择 ChatGPT 允许的**永久 fail-stop**模型，避免伪造可重建 authority：

| 崩溃窗口 | durable refs/evidence | 允许动作 |
|---|---|---|
| issuance 前 | guard可见，rollback或未发布 | normal retry按既有 lease 规则 |
| issuance 后、内部 consume 前 | 理论不可观察：两步均为同一同步 dispatch 内 total transition | 不允许插入 callback/I/O/cancellation point |
| consume 后、正常 return 前或之后 | refs preserve，Evidence-v1 bytes可审计，但无可重建 acceptance capability | 自动 retry、自动 close、自动训练均永久禁止；只能进入新的人工 `PASS-CLOSURE-RECOVERY-DESIGN` Gate |

process loss不能由 pathname verifier、candidate refs 或 Evidence-v1 bytes反推“authority acceptance”。它是显式 terminal fail-stop；任何后续恢复必须由独立 docs-only Gate 冻结新的人工证据/权限，不属于本 Gate。

## 4. CPU/static 验收

后续四文件实现必须以 temporary directory/local bare remote 覆盖：

1. ABI仍返回 exact `PublicationWitness`，无对外 `AcceptedPass`；copy/pickle/replay/activation外访问均拒绝；
2. pre-allocation/binding 任一失败发生在 guard transition 前，refs rollback、capability=`expired`；
3. transition/consume 无 mockable I/O 或 callback，断言 `prepared→issued→consumed`、无 capability 时绝不 preserve refs；
4. post-transition ordinary/custom/`BaseException` 不 rollback，preserve refs，capability保持 consumed；
5. evidence/guard pathname 替换只影响观察 API，不影响已 consumed capability/ref终态；
6. process-loss fixture只产生 permanent fail-stop marker/result，不允许同process外重建或 retry。

请求唯一 verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PASS_LINEARIZATION_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。三方同 SHA 批准前禁止修改 authority/adapter/test、真实 source/candidate/ref/evidence、child/runtime、CUDA/GPU、训练、评测、推理或 LIBERO4IN1。
