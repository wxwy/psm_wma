# PSM-WMA v0.3.5 Authority Root Real Adapter / Execution Request 设计 v0.4

**日期**：2026-09-12
**状态**：docs-only；待三方复审。
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`

本 addendum supersede v0.3 的 §2、§4、§5 中 evidence linearization 与 failure ABI；v0.3 的四文件 allowlist、opaque capability、exact raw bytes/OID、fixed-ref exact-old lease、所有其他 nested ABI 与禁止范围保持有效。

## 1. 单一 PASS linearization point

`publish_candidate(..., finalizer=...)` 仍在既有 authority-module `try/except` 内调用 finalizer。finalizer 的唯一公开成功语义是返回同一 witness identity 绑定的 sealed `EvidenceCommit`；authority module 只在接到该 capability 后从 publication transaction 正常返回。

但**唯一 PASS linearization point**不是 callback return，而是 finalizer 对同目录 exclusive `.pending` guard 的一次成功 `unlink`。这一步同时使 final evidence 可被 verifier 接受、使 sealed `EvidenceCommit` 可返回、并令 authority transaction committed。三层严格一致：

```text
accepted PASS visible  <=>  guard unlink succeeded
                        <=>  EvidenceCommit is returnable
                        <=>  publish_candidate preserves exact candidate refs
```

finalizer 必须按下列顺序执行，且只有第 7 步是 commit：

1. final evidence path 和 `.pending` guard path 均 fresh absent；以 `O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC` 创建 guard，file fsync、directory fsync；
2. 生成完整 PASS record 并以同目录 temp regular file 写全、file fsync；
3. atomic rename temp 到 fixed final path；
4. **guard 仍存在**时 fsync directory；
5. **guard 仍存在**时以单 FD re-read final file，验证 exact schema、digest、PASS terminal invariant以及两个 refs均为exact candidate；
6. **guard 仍存在**时预创建 opaque `EvidenceCommit`，但它不可被返回/使用；此前每一步及其异常均处于 pre-commit；
7. 仅执行 `unlink(guard)`。该调用成功即 commit，随后立即返回已创建 capability；guard unlink 后不得执行 fsync、read、validation、allocation、日志、诊断或任何可抛异常的动作。

guard 删除后不再额外 directory fsync：第4步已将 PASS record durable，guard 的残留只会产生 fail-closed false-negative（verifier拒绝），而不能产生无 guard 的 false PASS。若第7步失败，guard 必须仍存在；finalizer 作为 pre-commit exception 回到 authority rollback。若实现无法证明 guard 仍存在或无法清理 final/guard，必须以 `RollbackIncomplete` fail-stop；它不得让 accepted PASS 与 rollback 共存。

因此所有 writer file-fsync、rename、directory-fsync、re-read、validator、guard cleanup 故障都发生在第7步前并触发既有 remote→local conditional rollback。第7步成功后没有可由 callback 传播到 authority rollback 的操作。CPU/static tests必须在每一步前后注入异常，机械验证上式双向成立。

## 2. Failure object：保留首个失败与次级 rollback 失败

v0.3 `failure={phase,code}` 由下列 exact object 取代，禁止额外/缺失 key：

```text
primary_phase,primary_code,rollback_phase,rollback_code
```

- `primary_phase` 仅为`preflight,prepare,verify,pre_publication,local_cas,remote_cas,post_publication,binding_reverify,evidence_write`之一；PASS 时为 null。
- `primary_code` 是与 primary phase 对应的非空 stable ASCII code；PASS 时为 null。
- `rollback_phase` 仅为`rollback`或null；ordinary FAIL/PASS 时为 null。
- `rollback_code` 仅当`rollback_phase="rollback"`时为非空 stable ASCII code；否则为 null。

`ROLLBACK_INCOMPLETE` **永远保留实际 first-failure 的 primary phase/code**；rollback failure只是独立 secondary field，不能用`phase=rollback`覆盖 chronology。

## 3. Rollback-required exact reachability override

任何 `rollback.required=true` 的 record 都必须具有 concrete seven-key `authority`、verified `candidate`（revision、parents=`[formal_root_revision]`、tree OID、`verifier_pass=true`、binding SHA-256）以及 concrete pre-publication observations，且 `both_absent=true`。不允许 null authority、empty/prepared candidate、null pre-observations、或与已经到达的 CAS ownership bit 冲突。

generic `rollback` row 被下列按 primary origin 的四条取代：

| primary origin | publication 必然形状 | post-publication | rollback required / terminal |
|---|---|---|---|
| `remote_cas` | local attempted/succeeded/owned=true；remote attempted=true；remote succeeded/owned=false | null | required=true；remote delete bits=false；local delete按实；普通FAIL须local final absent/complete=true，次级失败为ROLLBACK_INCOMPLETE |
| `post_publication` | local三bit=true；remote attempted/succeeded/owned按实际（成功则三bit=true） | concrete observations，`both_candidate=false`，reverified=false | required=任一owned；remote→local delete bits仅覆盖owned端点；保留primary=`post_publication` |
| `binding_reverify` | local与remote三bit均=true | concrete exact-candidate observations，`both_candidate=true, committed_binding_reverified=false` | required=true；remote→local rollback；保留primary=`binding_reverify` |
| `evidence_write` | local与remote三bit均=true | concrete exact-candidate observations，`both_candidate=true, committed_binding_reverified=true` | 仅第1节第7步前可进入；required=true；remote→local rollback；保留primary=`evidence_write` |

这四条之外 `rollback.required=true` 一律无效。ordinary rolled-back FAIL 要求所有已owned端点经过 correct-order conditional delete、final local/remote均 concrete absent、`rollback.complete=true`且两个 rollback failure 字段均 null。`ROLLBACK_INCOMPLETE` 要求一条表内 primary origin、`rollback_phase="rollback"`、concrete `rollback_code`、`complete=false`，并明确保留已经到达的 ownership/pre/post facts；不得以 null 或 invented absent 掩盖无法观察的端点。

## 4. 额外 CPU/static 验收

四文件 stdlib tests新增以下强制负例：

1. 第7步前每个 writer/validator故障均只产生“no accepted PASS + complete rollback”的 ordinary FAIL；第7步成功后 refs恒为candidate且没有rollback调用；
2. `ROLLBACK_INCOMPLETE` 分别从 remote_cas、post_publication、binding_reverify、evidence_write 构造，validator拒绝 null authority、non-verified candidate、null pre-observation、错误 ownership/delete 顺序以及被覆盖的 primary phase；
3. failure object 的任何缺键、额外键、错误 nullability、`rollback_phase`/`rollback_code`不匹配都被拒绝；
4. accepted final evidence仅在 guard absent 时通过 verifier，并在所有 accepted case 与两个 exact candidate refs双向一致。

请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC
```

或`REQUEST_CHANGES(file:line)`。仅授权 v0.3 四文件的 temporary CPU/static implementation/tests；不授权真实 JSON/candidate/ref/origin/source/collection/GPU/训练。
