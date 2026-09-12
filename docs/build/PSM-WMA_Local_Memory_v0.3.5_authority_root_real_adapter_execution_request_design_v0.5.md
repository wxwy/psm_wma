# PSM-WMA v0.3.5 Authority Root Real Adapter / Execution Request 设计 v0.5

**日期**：2026-09-12
**状态**：docs-only；待三方复审。
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`

本文件 supersede v0.4 的 §1--§3；v0.3 的四文件 allowlist、opaque capability、exact raw bytes/OID、fixed-ref exact-old lease、其余 nested ABI 及全部禁止范围保持不变。本次只关闭 v0.4 exact-pair ChatGPT review 的两项 HIGH；不实现任何 adapter、authority module 或测试。

## 1. 单一跨模块 commit protocol

v0.4 的 guard unlink 仍是唯一 evidence/publication linearization point，但 authority 侧不得在它之后再作会进入 ownership rollback 的 capability 判断。未来四文件实现把原来的 callback-return contract 替换为下列 exact protocol：

```python
def publish_candidate(request, candidate, binding, git, *, finalizer=None) -> PublicationWitness: ...
def finalizer(witness: PublicationWitness, commit: EvidenceCommit) -> object: ...
```

1. authority 完成两个 exact CAS、fresh post-observation 和 committed binding reverify 后，在仍属于原有 `try/except` 的 pre-commit 阶段创建同一 activation 专属的 opaque `PublicationWitness` 和 `EvidenceCommit`；二者只由 authority token 构造，绑定同一 request/candidate/binding/witness identity、candidate revision 与单调 activation epoch。`EvidenceCommit` 初态为 `issued`，不可复制、序列化、重建或跨 activation 使用。
2. authority 在调用 finalizer **前**完成所有可拒绝的 capability 检查：witness 与 binding 的 object identity、activation epoch、commit object identity、`issued` state，以及一对一 witness--commit binding。finalizer 只能收到 authority 传入的这一对对象；不得接收或构造任意替代 capability。
3. finalizer 用传入的 exact `commit` 完成 guard 创建、PASS bytes 写入、file fsync、rename、directory fsync、single-FD re-read/schema/digest/ref invariant 验证，并在 guard 仍存在时调用唯一的 `commit.seal_for_guard(guard_identity, record_digest)`。该调用仅接受同一 witness 的 `issued` capability，且只能成功一次；wrong/unsealed/different-witness/replayed capability 一律在 guard 存在的 pre-commit 阶段抛异常。
4. `commit.consume_by_unlink()` 是唯一可调用 `unlink(guard)` 的操作。它只接受已 seal 的 expected commit；unlink 成功即原子地消费该 one-shot capability、使 guard absent、使 final evidence verifier-visible，并把 capability 置为不可再次调用的 committed state。unlink 失败时 capability 仍不可作为 committed 使用，guard 必须存在，异常回到既有 authority rollback。
5. finalizer 可返回任意 object；返回值不是提交 capability，也不参与 pre-commit validation。finalizer 返回后 authority 只作一个 total、non-throwing state dispatch：若 exact issued commit 仍未 committed，则此时 guard 必须存在，抛 `FINALIZER_DID_NOT_COMMIT` 并进入既有 rollback；若它已 committed，则 authority 不再验证 callback return、witness、digest、guard、refs 或 capability，也不得进入 rollback，直接保留候选 refs。
6. committed 后若外层发现 ordinary return value、different-witness capability、replayed capability 或 wrong/unsealed capability 的报告/包装违约，该错误是冻结的 `POST_COMMIT_CAPABILITY_VIOLATION` fail-stop：它可向 caller 报错，但必须在 authority `except` rollback boundary **之外**，不修改任何 ref、final evidence 或 commit state。该状态不是 ordinary FAIL，也不得伪造为 rollback success；accepted PASS 与两个 exact candidate refs 保持。

因此：`accepted PASS visible <=> guard unlink succeeded <=> exact EvidenceCommit 已 consumed <=> publication refs preserved`。所有可拒绝的 capability/type/identity/replay 状态都在 unlink 前发生；unlink 后唯一允许的控制流为 preserve-refs success 或 preserve-refs fail-stop。实现不得增加 guard unlink 后的 fsync、读取、验证、分配、日志或会抛异常操作。

## 2. `rollback` 语义与完整可达矩阵

`rollback.required` 严格表示“至少一个由本 activation 证明 owned 的 endpoint 需要 conditional delete”，而不是“恢复/终态证明 routine 已被进入”。为表达当前 `publish_candidate()` 的所有 `try/except` 路径，`rollback` exact keys 扩展为：

```text
entered,required,remote_delete_attempted,remote_delete_succeeded,
local_delete_attempted,local_delete_succeeded,final_local_observation,
final_remote_observation,complete
```

- `entered` 表示 authority 已进入 `_rollback`/fresh-final-observation routine；只要 first failure 在 publication `try` 内，它必须为 true，即使没有 owned ref。
- `required=true` 当且仅当 `local_owned or remote_owned`；每个 delete bit 仍只能属于已 owned endpoint，且顺序始终 remote→local。
- `complete=true` 仅当所有 required deletes 成功且 fresh final local/remote observations 都是 concrete absent。`entered=true,required=false,complete=true` 合法，表示无 owned ref 的终态证明成功。
- `ROLLBACK_INCOMPLETE` 保留 first failure，并允许 `entered=true,required=false`：它表示无权限删除 foreign/unproved state、但 fresh final observation 是 revision/unreadable 或不可获得，不得伪称 absent。

failure object 继续是 v0.4 的 exact 四键：

```text
primary_phase,primary_code,rollback_phase,rollback_code
```

其 nullability不变。`ROLLBACK_INCOMPLETE` 的 `primary_phase` 必须保留真实首失败；`rollback_phase="rollback"` 只表示 secondary recovery/final-proof failure，不能覆盖 chronology。

下表取代 v0.4 的“四条之外一律无效”规则。`A`=concrete authority，`V`=verified candidate，`C`=concrete observation，`F`=未尝试 all-false，`R`=真实已达到 bit。

| primary origin | pre / publication 必然形状 | rollback 必然形状 | ordinary FAIL / ROLLBACK_INCOMPLETE |
|---|---|---|---|
| `pre_publication` | A/V；pre 为 concrete foreign/unreadable 或 `both_absent=false`；publication=F | entered=true, required=false, delete bits=F；fresh final observations 必须记录 | 两端 final absent 则 ordinary FAIL；任一 foreign/unreadable/不可证明则 ROLLBACK_INCOMPLETE，且保留 foreign/unreadable |
| `local_cas` | A/V；pre concrete且both_absent=true；仅 local attempted=true，local succeeded/owned=false，其余F | entered=true, required=false, delete bits=F；fresh final observations 必须记录 | 两端 final absent则 ordinary FAIL；race/ambiguous/foreign/unreadable final则 ROLLBACK_INCOMPLETE |
| `remote_cas` | A/V；pre both absent；local attempted/succeeded/owned=true，remote attempted=true且succeeded/owned=false | entered=true, required=true；remote delete bits=false，local delete按实 | complete才 ordinary FAIL；否则 ROLLBACK_INCOMPLETE |
| `post_publication` | A/V；pre both absent；**local与remote six publication bits全 true**；post concrete且未满足允许的 post condition | entered=true, required=true；remote→local conditional delete按实 | complete才 ordinary FAIL；否则 ROLLBACK_INCOMPLETE |
| `binding_reverify` | A/V；pre both absent；six bits全 true；post concrete exact candidate且`both_candidate=true,committed_binding_reverified=false` | entered=true, required=true；remote→local conditional delete按实 | complete才 ordinary FAIL；否则 ROLLBACK_INCOMPLETE |
| `evidence_write`（仅 guard unlink 前） | A/V；pre both absent；six bits全 true；post concrete exact candidate且binding reverified=true | entered=true, required=true；remote→local conditional delete按实 | complete且accepted PASS不可见才 ordinary FAIL；否则 ROLLBACK_INCOMPLETE |

表外 `required=true`、`entered=false` 的 publication-try failure，或 `post_publication` remote not-owned 都无效。`preflight`/`prepare`/`verify` 保持未进入 publication try：`entered=false,required=false,complete=false`，无 final observations；PASS 保持 `entered=false,required=false` 且所有删除 bit false。

## 3. 强制 CPU/static 验收

四文件 temporary CPU/static tests 除 v0.4 全部矩阵外，必须新增：

1. finalizer ordinary return without `consume_by_unlink`、finalizer exception、wrong/unsealed/different-witness/replayed commit 都在 guard 存在阶段完成 rollback；accepted PASS 不可见且 refs 最终 absent；
2. unlink 成功后 callback return/type/report wrapping 的 ordinary、different-witness、replayed、wrong/unsealed四类违约均为 preserve-refs `POST_COMMIT_CAPABILITY_VIOLATION`，没有 `_rollback` 调用；accepted PASS 与两 candidate refs仍双向一致；
3. `pre_publication` foreign、pre-publication unreadable、`local_cas` lost-race/ambiguous且无 ownership witness，分别覆盖 final both-absent ordinary FAIL 与 final foreign/unreadable `ROLLBACK_INCOMPLETE`；foreign 永不删除；
4. validator拒绝：`entered`缺失/错值，`required`与owned不一致，未owned delete bit，pre/local-cas无owned却被误标`required=true`，不可能的`post_publication` remote未owned，及四键 failure object 的任何 key/nullability 漂移；
5. 对每一个 accepted PASS case，证明没有发生 post-unlink rollback；对每一个 rollback case，证明 guard 不存在的 accepted PASS 从未出现。

请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC
```

或`REQUEST_CHANGES(file:line)`。仅授权 v0.3 的四个 root 文件及 temporary directory/local bare-remote CPU/static tests；不授权真实 JSON/candidate/ref/origin/source/collection、child/runtime、checkpoint/data/cache、CUDA/GPU、训练、评测或推理。
