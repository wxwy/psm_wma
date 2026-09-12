# PSM-WMA v0.3.5 Authority Root Real Adapter / Execution Request 设计 v0.1

**日期**：2026-09-12
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`

## 1. 必要性与两阶段路线

synthetic authority-root implementation 已由三方关闭，但当前 production 只有 injected `AuthorityGitTransaction` protocol，没有真实 Git adapter、CLI、证据 writer 或可审核 argv。故不得直接声称可以执行真实 materialization。本 Gate 把剩余路径压缩为两个必要阶段，不插入其他 provenance Gate：

1. 按本设计实现并 CPU/static 审核一个 root-only real adapter/CLI；测试仅使用 temporary bare/local remotes，不连接项目 remote、不创建正式 JSON/ref。
2. adapter closure 后立即生成一次 exact execution request，冻结其 formal-root tree内工具 blob、解释器/Git identity、完整 argv 与下述 raw bytes；三方批准后执行一次 materialization。成功后直接提交 authority tuple 三方 binding，再进入已批准 controlled collection execution，不横向扩 Gate。

本设计仅申请第1阶段实现授权，不授权第2阶段真实执行。

## 2. Real adapter allowlist 与复用

仅允许新增：

```text
tools/psm_wma/materialize_immutable_source_authority_root.py
tools/psm_wma/test_materialize_immutable_source_authority_root.py
```

adapter 必须直接调用已关闭的 `prepare_candidate→verify_candidate→publish_candidate`，实现现有 typed protocol，不复制 schema/tree/ref/rollback算法。Git 调用只允许显式注入并经identity绑定的绝对 executable，以argv数组、`shell=False`、sanitized env、固定cwd运行；禁止bare Git、PATH lookup、shell、ambient HEAD/index/worktree、force、普通push覆盖或delete/recreate。所有object构造使用temporary index/plumbing；ref操作必须用expected-zero/expected-candidate CAS语义。

CLI 必须先以只读preflight验证两个input FD的regular/non-symlink/canonical bytes、formal root full tree、child Gitlink、工具/解释器/Git identity及local/remote ref absent，再允许candidate object创建；publication失败只走已关闭ownership-aware rollback。正式执行前另行冻结CLI exact argv，当前测试不得访问origin。

## 3. 已冻结 future raw-byte payload

selection exact 516 bytes（无尾随换行）：

```json
{"entries":[{"ordinal":0,"relative_path":"model/.metadata"},{"ordinal":1,"relative_path":"model/__0_0.distcp"},{"ordinal":2,"relative_path":"optim/.metadata"},{"ordinal":3,"relative_path":"optim/__0_0.distcp"},{"ordinal":4,"relative_path":"scheduler/.metadata"},{"ordinal":5,"relative_path":"scheduler/__0_0.distcp"},{"ordinal":6,"relative_path":"trainer/.metadata"},{"ordinal":7,"relative_path":"trainer/__0_0.distcp"}],"schema":"immutable_source_selection_request_v1","source_kind":"checkpoint_source_manifest_v1"}
```

- raw SHA-256=`8fe4585f366cb69ad9181e30c25b5f4e99040c83d8ffe66426897bfa9d331edd`
- native blob OID=`6c7d53c1f361dfec37257cabef8c31d8a27b0186`

config exact 508 bytes（无尾随换行）：

```json
{"enable_input_bias":false,"k_local":1,"local_evidence_feature_version":"causal_visual96_executed_action10_v1","local_fast_state_dtype":"fp32","local_history_backend":"ttt_fast_weight","local_history_enabled":true,"local_history_evidence_dim":106,"local_history_state_enabled":false,"local_memory_dim":32,"local_memory_enabled":true,"local_runtime_resume_mode":"slow_only_no_mid_episode_resume","local_ttt_enabled":true,"schema":"canonical_native_local_ttt_config_v2","ttt_inner_lr":0.1,"ttt_tbptt_steps":16}
```

- raw SHA-256=`43b3b77b5934107c54b8bee157b46d07cb17b85ca89305ad6fb7405237e42d1d`
- native blob OID=`d1b80b1c307c7dd729d92f794796d1fb4e51acfe`

这些bytes只批准future traversal选择与active config identity；本 Gate不打开8个source entry。future source root必须在controlled collection execution request另行绑定，不能写入authority JSON。

## 4. Future execution identity与提交合同

当前只读host观察为Python real executable `/opt/conda/bin/python3.11`、SHA-256=`f3e3f561b473976be55d937616915d6c507dedcb3950c3ca72df786b28e8efdc`、version=`Python 3.11.9`；Git `/usr/bin/git`、SHA-256=`587ef21868c948b883993e23209b86a72a6ddc06aab1545c697ffc31075acd4a`、version=`git version 2.34.1`。这些只是设计时observations，future execution request必须重新观察并精确冻结，drift即不执行。

execution request formal root将作为authority candidate唯一parent；不能预写为本设计SHA、ledger HEAD或运行时HEAD。它还必须冻结adapter与authority module的formal-tree Git blob OID/raw SHA、cwd `/disk/rl/psm_wma`、sanitized env allowlist、commit author/committer/message/timestamp、固定ref、remote URL identity、完整argv、evidence path及rollback判据。candidate commit不推进V2。

固定ref仍为：

```text
refs/heads/authority/r09-b-ttt-v035-immutable-source-v1
```

设计时只读观察local/remote均absent不能替代执行前双重fresh observation。

## 5. CPU/static acceptance与边界

temporary Git tests至少覆盖：exact CLI PASS、identity/raw-byte/formal-root/Gitlink/ref drift pre-mutation拒绝；zero/multi parent、parent fixed path、full-entry/inherited drift；local/remote CAS竞争及postcheck/rollback竞态；argv/env/cwd/PATH/shell污染拒绝；candidate不推进V2；evidence只含七键binding与必要identity，不含source raw bytes、绝对source path或secret。所有测试只用临时目录与本地temporary remote。

请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC
```

或 `REQUEST_CHANGES(file:line)`。不授权真实input文件、candidate/ref、origin mutation、source read、collection/publication、GPU或训练。
