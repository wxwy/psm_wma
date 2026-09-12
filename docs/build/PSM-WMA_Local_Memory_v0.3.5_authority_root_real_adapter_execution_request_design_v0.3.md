# PSM-WMA v0.3.5 Authority Root Real Adapter / Execution Request 设计 v0.3

**日期**：2026-09-12
**状态**：docs-only；待三方复审。
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`

本文件 supersede v0.2 中的 real-adapter allowlist、publication/evidence finalization 与 evidence v1 ABI；v0.2 的 exact raw bytes/OID、single fixed-ref exact-old lease、两阶段路线以及所有未授权边界保持不变。

## 1. 本次整改与范围

ChatGPT 对 v0.2 的两个 HIGH 均在本 Gate 内关闭：

1. evidence writer 在 refs 已成功创建后失败，必须能调用同一 activation 的 ownership-aware rollback，不能让 adapter 复制或调用私有 `_rollback`；
2. evidence record 必须由独立 verifier 仅凭 record 本身机械复现 chronology，不能只固定顶层 key。

因此下一阶段 CPU/static implementation 的唯一 allowlist 扩展为四个 root 文件：

```text
tools/psm_wma/immutable_source_authority_root.py
tools/psm_wma/test_immutable_source_authority_root.py
tools/psm_wma/materialize_immutable_source_authority_root.py
tools/psm_wma/test_materialize_immutable_source_authority_root.py
```

前两者的改动只允许暴露下述 transaction-finalizer seam 与其 stdlib test，不得放宽 tree、binding、CAS、lease 或 rollback 条件；后两者仍只允许 temporary directory/local bare remote 的 CPU/static adapter 与 test。不得创建正式 JSON、candidate、live/local authority ref、origin ref，不得读 source/checkpoint/data/cache，不得运行 child、CUDA/GPU、训练、评测或推理。

## 2. 公开的一次性 publication-finalization seam

`publish_candidate` 的既有 prepare→verify→publish 主合同不改；扩展为带可选 keyword-only `finalizer` 的一次 transaction：

```python
def publish_candidate(request, candidate, binding, git, *, finalizer=None) -> PublicationWitness: ...
```

- authority module 在 local/remote exact CAS 都成功、fresh post-observation 都是 exact candidate、且 committed binding reverify 通过后，才创建 opaque `PublicationWitness` 并调用 `finalizer(witness)`；回调仍处于 `publish_candidate` 的既有 `try/except` 内。
- `PublicationWitness` 改为不可直接构造、不可复制/序列化的 opaque capability：仅 authority module 的 token 能创建；它绑定同一 request/candidate/binding identity、candidate revision、两个 owned-create bit 和未使用状态。finalizer 只能调用公开只读 accessors，不能构造、替换、重放或跨 activation 使用 witness。
- finalizer 正常返回即声明 evidence 已到达 §4 的 accepted commit point。任意异常（包括 writer、post-rename cleanup 或 record validator）均由 authority module 捕获，并以已有 remote→local、exact-candidate conditional delete、fresh two-endpoint observation 的 `_rollback` 执行；adapter 不得导入或复制 `_rollback`。
- rollback 完成后 authority module 仅在 finalizer 明确保证没有 accepted PASS 可见时，允许向 adapter 抛出 ordinary `AuthorityRootError`；任何 ref cleanup、evidence cleanup、final observation 或 accepted-evidence visibility 无法证明的情形，必须抛 `RollbackIncomplete`，最终记录 status=`ROLLBACK_INCOMPLETE`。
- `finalizer` 不可在失败后吞掉异常并返回；authority module 以 finalizer 回传的 sealed `EvidenceCommit` capability 交叉检查 witness identity 与 §4 commit state。callback 返回普通值、不同 witness 或二次使用 capability 一律失败并进入同一 rollback。

这把 final evidence commit 纳入既有 transaction 边界；不存在“publish 成功返回后再补救”的公开 rollback API，也不存在跨模块私有调用。

## 3. Evidence v1：exact nested ABI

顶层 exact keys 仍为：

```text
schema,status,execution,authority,candidate,pre_publication,
publication,post_publication,rollback,failure,evidence_sha256
```

所有 mapping 禁止额外/缺失 key；所有 JSON object key 按 UTF-8 byte order canonical JSON；bool 必须是 JSON boolean，整数必须是 non-negative JSON integer，digest/revision 只能为 64-char lowercase SHA-256 或 40-char lowercase Git SHA-1（分别按字段规定），禁止以 string/null 互换。

### 3.1 exact identity and observation objects

`execution` exact keys：

```text
formal_root_revision,child_gitlink,adapter,authority_module,interpreter,
git_executable,cwd,sanitized_env_sha256,argv_sha256,commit_metadata,
remote_identity_sha256,fixed_ref
```

- `formal_root_revision`、`child_gitlink`：Git SHA-1；`cwd`、`fixed_ref`：non-empty string；后三个 `*_sha256`：SHA-256。
- `adapter`、`authority_module` exact keys=`path,blob_native_oid,raw_sha256`；`path` 是 repo-relative non-empty string，OID/SHA 分别为 Git SHA-1/SHA-256。
- `interpreter`、`git_executable` exact keys=`path,raw_sha256,version`；均为 non-empty string（`raw_sha256`为 SHA-256）。
- `commit_metadata` exact keys=`author_name,author_email,author_date,committer_name,committer_email,committer_date,message`；每项均为 non-empty string，禁止环境默认值。

每个 `local_observation`/`remote_observation` 都是 exact object：

```text
state,revision,error
```

其中 `state` 仅可为`absent|revision|unreadable`：absent→`revision=null,error=null`；revision→`revision=<Git SHA-1>,error=null`；unreadable→`revision=null,error=<stable non-empty ASCII code>`。任何其他组合均无效。

`authority` 为 exact seven-key binding 或全 null mapping；七键固定为：

```text
root_revision,selection_path,selection_blob_native_oid,selection_raw_sha256,
config_path,config_blob_native_oid,config_raw_sha256
```

concrete 时 `root_revision`/两 OID 为 Git SHA-1、两 SHA 为 SHA-256、两 path 为 non-empty repo-relative string；null 时七值均 null。

`candidate` exact keys=`revision,parents,tree_native_oid,verifier_pass,binding_sha256`。空 candidate 必为`null,null,null,false,null`；prepared-but-unverified candidate 仅允许`revision=<Git SHA-1>,parents=null,tree_native_oid=null,verifier_pass=false,binding_sha256=null`；verified candidate 必须为 revision Git SHA-1、`parents=[formal_root_revision]`、tree Git SHA-1、`verifier_pass=true`、binding SHA-256。

`pre_publication` exact keys=`local_observation,remote_observation,both_absent`；`publication` exact keys=`local_create_attempted,local_create_succeeded,remote_create_attempted,remote_create_succeeded,local_owned,remote_owned`；`post_publication` exact keys=`local_observation,remote_observation,both_candidate,committed_binding_reverified`；`rollback` exact keys=`required,remote_delete_attempted,remote_delete_succeeded,local_delete_attempted,local_delete_succeeded,final_local_observation,final_remote_observation,complete`；`failure` exact keys=`phase,code`。

未到达的 observation field 必为 null（不是 absent object）；未到达 publication/rollback boolean 必为 false。`failure.phase` 只能是`preflight,prepare,verify,pre_publication,local_cas,remote_cas,post_publication,binding_reverify,evidence_write,rollback`，其 `code` 为稳定 non-empty ASCII；PASS 时二者均 null。

## 4. First-failure chronology / nullability table

以下表中的 C=concrete、N=all-null/unreached、F=exact all-false/未尝试、R=按端点已达成的真实 CAS/rollback bits；`A`是 concrete seven-key authority，`V`是 verified candidate，`P`是 prepared-but-unverified candidate。

| first failure / terminal | authority | candidate | pre | publication | post | rollback | failure | terminal rule |
|---|---|---|---|---|---|---|---|---|
| preflight | N | empty | N | F | N | `required=false`其余F/N | phase=preflight | `FAIL`；无 mutation |
| prepare | N | P 或 empty | N | F | N | `required=false`其余F/N | phase=prepare | `FAIL`；无 mutation |
| verify | N | P | N | F | N | `required=false`其余F/N | phase=verify | `FAIL`；无 mutation |
| pre_publication | A | V | C | F | N | `required=false`其余F/N | phase=pre_publication | `FAIL`；至少一端非 absent/unreadable |
| local_cas | A | V | C(both_absent=true) | local attempted=true、其余F | N | required=false其余F/N | phase=local_cas | `FAIL`；local 未 owned |
| remote_cas | A | V | C(true) | local attempted/succeeded/owned=true；remote attempted=true，其余按实 | N | required=true，remote F，local按R | phase=remote_cas | rollback complete 才 `FAIL` |
| post_publication / binding_reverify | A | V | C(true) | 两端 bits按实 | C | required=任一owned；按R | respective phase | rollback complete 才 `FAIL` |
| evidence_write | A | V | C(true) | 两端 create/owned=true | C(both_candidate=true、binding=true) | required=true，remote→local按R | phase=evidence_write | accepted PASS 不可见且 rollback complete 才 `FAIL` |
| rollback | A 或 N | V/P/empty按起点 | 已达部分C/N | 已达真实 bits | 已达C/N | required=true、按实、complete=false | phase=rollback | 唯一 `ROLLBACK_INCOMPLETE` |
| PASS | A | V | C(true) | 六 bits全 true | C(both_candidate=true、binding=true) | required=false其余F/N | null/null | accepted evidence 已 commit，两个 refs exact candidate |

`R` 的每个 delete attempted/succeeded bit 只能在对应 `*_owned=true` 后为 true；remote delete 必须先于 local delete。ordinary rolled-back FAIL 的两 final observations 均为 concrete absent，`rollback.complete=true`。`ROLLBACK_INCOMPLETE` 必须 `rollback.required=true,complete=false`，且至少一个 final observation 是 revision/unreadable/null或一个 required delete 不成功；不得伪称 absent。

## 5. Evidence commit point and writer ownership

writer 的固定 final evidence path 在 transaction 开始前必须 absent，并有同目录、同 basename 的 exclusive `.pending` guard。guard 由 finalizer 用`O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC`创建、file fsync 与 directory fsync；verifier 只有在 guard 不存在时才接受 final PASS。

finalizer 仅在 §4 PASS 行全部 refs/binding witness concrete 后构造 PASS bytes：temporary regular file（同目录、上述安全 flags）写全→file fsync→atomic rename 到 final path→directory fsync→single-FD re-read并验证 exact schema/digest→删除 guard→directory fsync→再次单-FD re-read。最后一步成功才产生 sealed `EvidenceCommit` 并允许 callback 正常返回。

- rename 前任何失败：final path 必须 absent，guard 清理并 fsync directory 后才允许 authority rollback；否则 `ROLLBACK_INCOMPLETE`。
- rename 后、guard 删除前：guard 令 visible final PASS 不被 verifier 接受；finalizer 必须尝试条件清理 final file与guard并 fsync directory，不能证明两者 absent即`ROLLBACK_INCOMPLETE`。
- guard 删除后：这是 accepted commit point。此后 authority 保留 exact candidate refs并把 record 视为 PASS；任何报告路径上的后续异常不得触发 ref rollback。实现必须在 guard 删除前完成所有可能失败的 record validation；测试必须证明 accepted PASS 与两个 candidate refs 同时存在。

ordinary `evidence_write` FAIL 因而只可能发生在 accepted commit point 前：final file不可接受/不可见且 refs 完整 rollback。任何 cleanup 失败不能产生 ordinary FAIL；必须 fail-stop 为`ROLLBACK_INCOMPLETE`。writer不覆盖既有 final、pending 或临时文件，且不接受 source raw bytes、绝对 source path、credential/secret URL。

## 6. CPU/static验收与唯一请求

除 v0.2 矩阵外，四文件 tests必须直接验证：callback只在 post-CAS+binding reverify 后执行；callback exception沿既有 remote→local rollback 且 adapter无法访问私有 rollback；opaque witness/commit capability 不可构造、复制、重放；每个 §4 representative row的 exact nullability/type mutation被 verifier拒绝；writer 的 partial/file-fsync/pre-rename/rename/post-rename/dir-fsync/guard-cleanup failure 与 accepted-commit cases保持“accepted PASS ↔ exact candidate refs”一致；foreign endpoint永不删除。

请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC
```

或`REQUEST_CHANGES(file:line)`。本请求仅授权上述四文件与 temporary CPU/static tests；不授权任何真实 materialization、source/remote/origin I/O、GPU 或训练。
