# Authority-root execution snapshot annex v0.2

**日期**：2026-09-12
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`
**状态**：docs-only remediation；仍待新的同 pair 三方审核。

## 1. v0.1 supersede 与不可变性

本文件完全替代 `...execution_snapshot_annex_v0.1.md`：v0.1 将部分 runtime
authority 延后至 execution request 的表述失效。本 annex 是 v0.2 request §4 枚举的**全部**
runtime 字段的唯一 authority；下列 canonical raw bytes、SHA、FD number、metadata、路径和
argv 均已冻结，后续 execution request 只能逐字复现/组装，不能加入、替换或推导新的运行时值。
执行时仍须重新观测 freshness、expected-zero 与 routing-authority；观测值漂移即零 mutation FAIL。

本文件不创建 FD backing file、JSON、worktree、index、candidate、ref 或 evidence；不读取
source/checkpoint，不进入 collection/receipt/publication，不改 child，不使用 GPU，不训练、评测或推理。

## 2. formal authority、路径与工具

- 唯一 candidate parent：`9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5`；child Gitlink：
  `93a89ba61306d840a008813f62f26a34d54850f4`；fixed ref：
  `refs/heads/authority/r09-b-ttt-v035-immutable-source-v1`，local/remote 必须 expected-zero。
- endpoint raw UTF-8：`https://github.com/wxwy/psm_wma.git`；SHA-256=
  `8ddb34607979ff80a7b97732199b7c7a6439c81d1154eda97039bada69a02dae`；不得使用 remote alias。
- clean root=`/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8`；index=
  `<clean-root>/.authority-root.index`；evidence=
  `/disk/rl/psm_wma/artifacts/g0/r09/authority_root_materialization_evidence_v1.json`
  和 `.pending`。每项执行前必须 absent。
- Python=`/opt/conda/bin/python3`，SHA-256=`f3e3f561b473976be55d937616915d6c507dedcb3950c3ca72df786b28e8efdc`，
  version=`Python 3.11.9`；Git=`/usr/bin/git`，SHA-256=`587ef21868c948b883993e23209b86a72a6ddc06aab1545c697ffc31075acd4a`，
  version=`git version 2.34.1`。

## 3. 完整 canonical input 与环境 bytes

selection raw UTF-8（516 bytes、无尾随换行、SHA-256=`8fe4585f366cb69ad9181e30c25b5f4e99040c83d8ffe66426897bfa9d331edd`、
native OID=`9f03614b691bca3ba834e16e65ee983fe95af74c`）：

```json
{"entries":[{"ordinal":0,"relative_path":"model/.metadata"},{"ordinal":1,"relative_path":"model/__0_0.distcp"},{"ordinal":2,"relative_path":"optim/.metadata"},{"ordinal":3,"relative_path":"optim/__0_0.distcp"},{"ordinal":4,"relative_path":"scheduler/.metadata"},{"ordinal":5,"relative_path":"scheduler/__0_0.distcp"},{"ordinal":6,"relative_path":"trainer/.metadata"},{"ordinal":7,"relative_path":"trainer/__0_0.distcp"}],"schema":"immutable_source_selection_request_v1","source_kind":"checkpoint_source_manifest_v1"}
```

config raw UTF-8（508 bytes、无尾随换行、SHA-256=`43b3b77b5934107c54b8bee157b46d07cb17b85ca89305ad6fb7405237e42d1d`、
native OID=`89b12047c50a3a924521200d1897b13bf30aacfe`）：

```json
{"enable_input_bias":false,"k_local":1,"local_evidence_feature_version":"causal_visual96_executed_action10_v1","local_fast_state_dtype":"fp32","local_history_backend":"ttt_fast_weight","local_history_enabled":true,"local_history_evidence_dim":106,"local_history_state_enabled":false,"local_memory_dim":32,"local_memory_enabled":true,"local_runtime_resume_mode":"slow_only_no_mid_episode_resume","local_ttt_enabled":true,"schema":"canonical_native_local_ttt_config_v2","ttt_inner_lr":0.1,"ttt_tbptt_steps":16}
```

sanitized launcher/bootstrap environment 的 canonical UTF-8 JSON（144 bytes、SHA-256=
`fbf082f8f77180514780ff3f838e311389ad0d0f44b71ec5cb3e472011a819cf`）唯一为：

```json
{"GIT_CONFIG_GLOBAL":"/dev/null","GIT_CONFIG_NOSYSTEM":"1","GIT_CONFIG_SYSTEM":"/dev/null","GIT_NO_REPLACE_OBJECTS":"1","LANG":"C","LC_ALL":"C"}
```

NativeAuthorityGit 的 commit-only environment 等于上述 mapping 加下节七个 metadata 键；不得继承
任何其它环境变量。

## 4. bootstrap、FD ABI 与 commit metadata

adapter identity 固定为 `tools/psm_wma/materialize_immutable_source_authority_root.py` /
blob `da782754b8e8efa0f3cae973aa68602dcda1c237` /
raw SHA-256 `091ea62d0a8b48429c67100c1395e62a300dc47a8d8f65c7046ba00f8205b5e9`；其余三模块 identity
逐字继承 v0.2 request §2。

bootstrap raw UTF-8 bytes 是该 exact adapter blob 中 `bootstrap_payload()` 的唯一 `return` expression
按 Python AST source-order 拼接所有 string constants 的值；该 extraction 不执行该 module、不得读
working tree，结果严格为 7,538 bytes，SHA-256=
`7e1c0ecc2161984a88ea0d0eae82f9f7ced709ca919f0302f74a3a068e08c9b8`。这一定义连同 blob/raw SHA
唯一确定每个 raw byte；任何 AST 形状、长度或 digest 不匹配均 FAIL。

FD 号固定且不得在 execution request 首次出现：selection=`3`、config=`4`、bootstrap contract=`5`。
三个 descriptor 均须由 launcher 在 `execve` 前以 `O_RDONLY|O_NOFOLLOW|O_CLOEXEC` 打开普通非
symlink 文件、复读精确 canonical bytes后清除仅这三个 FD 的 `FD_CLOEXEC`；其余 FD 必须关闭，
不得由 stdin、环境、path、shell 或 caller mapping 传入。bootstrap contract 的 canonical JSON 仅含
`bootstrap_raw_sha256` 与 `bootstrap_argv_sha256` 两键。

candidate metadata 固定为：author name=`wxwy`、author email=`1036648581@qq.com`、author date=
`2026-09-12T23:07:43+08:00`、committer name=`wxwy`、committer email=`1036648581@qq.com`、
committer date=`2026-09-12T23:07:43+08:00`、commit message=`chore: materialize immutable source authority root`。

## 5. complete parser argv authority

parser argv 为 JSON compact UTF-8 array；它按 `_parser()` 全字段的唯一顺序由以下 frozen tuple 组装：
`--selection-fd 3`、`--config-fd 4`、formal root/child、两 input SHA、clean root、endpoint、index、
evidence、Git/Python identity、`--bootstrap-contract-fd 5`、bootstrap project root/module、四模块
path/blob/raw-SHA，以及 §4 的七个 metadata 字段。其完整数组的 SHA-256 必须为
`72777bd7305c760c48c069eafd068f1a538383a6fdb8d40258acf3d8fc3b7ae2`，长度=2427 bytes；bootstrap
observes `json.dumps(sys.orig_argv[6:], sort_keys=True, separators=(',', ':'), ensure_ascii=False)`，
因此其 `bootstrap_argv_sha256` 必须等于此 digest。缺失、重排、追加或改变任一 argv element 均 FAIL。

后续 request 只可把本节 tuple 展开为 argv 和 contract JSON，不得增加任何 runtime authority；仍须在
mutation 前重新核验 fresh path、formal tree、routing authority、endpoint 与双端 expected-zero。

## 6. verdict

请求唯一 verdict：

```text
APPROVE_TO_PREPARE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_EXECUTION_REQUEST
```

或 `REQUEST_CHANGES(file:line)`。即使批准，仍不授权 materialization；完整 execution request 与
命令仍须新的同 pair 三方 `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT`。
