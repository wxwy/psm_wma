# PSM-WMA v0.3.5 Authority Root Real Adapter / Execution Request 设计 v0.2

**日期**：2026-09-12
**状态**：docs-only；待三方复审。
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`

本文件逐项 supersede v0.1 的 blob OID、remote CAS 与 evidence 合同；其余范围、两阶段路线、两文件allowlist和禁止项全部继承。

## 1. Corrected exact raw-byte identity

v0.1 §3 所示两段无尾随换行 raw bytes、长度与 SHA-256 保持不变，native Git blob OID更正为：

```text
selection: len=516
sha256=8fe4585f366cb69ad9181e30c25b5f4e99040c83d8ffe66426897bfa9d331edd
blob_oid=9f03614b691bca3ba834e16e65ee983fe95af74c

config: len=508
sha256=43b3b77b5934107c54b8bee157b46d07cb17b85ca89305ad6fb7405237e42d1d
blob_oid=89b12047c50a3a924521200d1897b13bf30aacfe
```

adapter tests必须从exact raw bytes分别重算长度、SHA-256、native blob OID，并在temporary repository以absolute bound Git执行`hash-object --stdin`交叉核验；禁止信任复制常量。

## 2. Remote exact-old CAS primitive

禁止unconditional `--force`、wildcard/general force、普通overwrite push、delete/recreate、retry-to-win。唯一允许的remote mutation是对固定ref的exact-old atomic lease：

```text
create argv:
<git> push --porcelain --force-with-lease=<fixed-ref>: <credential-free-bound-remote> <candidate>:<fixed-ref>

rollback argv:
<git> push --porcelain --force-with-lease=<fixed-ref>:<candidate> <credential-free-bound-remote> :<fixed-ref>
```

creation lease冒号后为空，语义必须由temporary bare-remote tests证明为expected absent；rollback expected-old精确candidate。adapter不得接受caller提供lease/ref/refspec。每次mutation后均fresh `ls-remote <bound-remote> <fixed-ref>`：create只接受exact candidate；rollback只接受absent。lease失败、ambiguous output、remote不可读、foreign revision均fail-stop，foreign不覆盖/不删除且最终`ROLLBACK_INCOMPLETE`。测试必须构造foreign ref为candidate ancestor、普通push可fast-forward的情形，证明上述lease仍拒绝并完整保留foreign。

local create使用`update-ref <fixed-ref> <candidate> <zero-oid>`；local rollback使用`update-ref -d <fixed-ref> <candidate>`，均以fresh `rev-parse --verify`观察。所有argv通过absolute Git、`shell=False`、sanitized env和固定cwd执行。

## 3. Exact transaction evidence v1

canonical record顶层exact keys：

```text
schema,status,execution,authority,candidate,pre_publication,
publication,post_publication,rollback,failure,evidence_sha256
```

- `schema="immutable_source_authority_root_materialization_evidence_v1"`；`status`仅`PASS|FAIL|ROLLBACK_INCOMPLETE`。
- `execution` exact绑定`formal_root_revision,child_gitlink,adapter,authority_module,interpreter,git_executable,cwd,sanitized_env_sha256,argv_sha256,commit_metadata,remote_identity_sha256,fixed_ref`。tool/executable identity均为path、formal-tree/native blob或raw SHA、version中适用项；remote identity只存credential-free normalized identity的SHA-256，不存credential/secret URL。
- `authority`是exact seven-key mapping；pre-mutation失败时七键值全null，不得伪造candidate结果。
- `candidate` exact为`revision,parents,tree_native_oid,verifier_pass,binding_sha256`。
- `pre_publication` exact为`local_observation,remote_observation,both_absent`。
- `publication` exact为`local_create_attempted,local_create_succeeded,remote_create_attempted,remote_create_succeeded,local_owned,remote_owned`；owned只能由本activation成功CAS产生。
- `post_publication` exact为`local_observation,remote_observation,both_candidate,committed_binding_reverified`。
- `rollback` exact为`required,remote_delete_attempted,remote_delete_succeeded,local_delete_attempted,local_delete_succeeded,final_local_observation,final_remote_observation,complete`。
- `failure` exact为`phase,code`；PASS时二者null。稳定phase只取`preflight,prepare,verify,pre_publication,local_cas,remote_cas,post_publication,binding_reverify,evidence_write,rollback`；code为稳定ASCII标识。
- `evidence_sha256`是删除自身后的canonical JSON SHA-256；unknown/missing/type/order/status-reachability或digest drift全部拒绝。

PASS必须证明verifier PASS、pre两端absent、两端owned create成功、post两端candidate、committed binding reverified、rollback不需要。普通pre-mutation FAIL不得含CAS/rollback成功见证。mutation后FAIL必须有完整rollback；任一owned endpoint无法条件删除、任一final observation非absent/不可读，status唯一为`ROLLBACK_INCOMPLETE`。

evidence writer只接受完整verified record：同目录temporary regular file以`O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC`创建，写全、fsync file、atomic rename到预先absent固定path、fsync directory；正常返回表示唯一完整record可见。任一步失败必须清理未发布temp；final path已存在绝不覆盖。若rename后发生错误，必须重新单FD读取并验证exact digest；无法证明完整accepted record时fail-stop，不得返回PASS。测试覆盖partial write、before/after rename、fsync failure与stale PASS不可见。

## 4. CPU/static增量验收与边界

除v0.1矩阵外，temporary local/bare remote必须覆盖：exact bytes→SHA/OID→native `hash-object`；absent lease create；fast-forwardable foreign ancestor lease拒绝且保留；candidate→absent rollback lease；remote drift/unreadable/compare-delete failure；PASS、pre-mutation FAIL、一端成功另一端冲突、foreign drift、observation error与`ROLLBACK_INCOMPLETE`的exact evidence；atomic writer故障矩阵。不得接触origin或项目live ref。

请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC
```

或`REQUEST_CHANGES(file:line)`。只授权两文件adapter/CLI与temporary CPU/static tests，不授权真实JSON/candidate/ref/origin/source/GPU/训练。
