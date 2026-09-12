# Authority-root execution snapshot annex v0.3

**日期**：2026-09-12
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`
**状态**：docs-only remediation；待同一三方新 pair 审核。

## 1. 唯一 authority 与继承

本文件完全 supersede `...execution_snapshot_annex_v0.2.md`。除本文件明确替换的 §4/§5 外，v0.2
§1–§4 的 formal parent/Gitlink/ref/endpoint、clean path、工具 identity、selection/config raw bytes、
六键 launcher environment、adapter/module identity、FD=3/4/5、bootstrap raw extraction（7,538 bytes，
SHA-256=`7e1c0ecc2161984a88ea0d0eae82f9f7ced709ca919f0302f74a3a068e08c9b8`）及 candidate metadata
均逐字继承且不得替换。本 annex 是全部 runtime authority 的唯一来源；后续 request 只可复现这些
bytes/字段，不能加入、替换或延后 authority。仍不创建/读取任何真实资产或执行 materialization。

## 2. parser argv canonical bytes

唯一 `actual_argv` raw UTF-8 是下列 compact JSON array（2,427 bytes，SHA-256=
`72777bd7305c760c48c069eafd068f1a538383a6fdb8d40258acf3d8fc3b7ae2`）：

```json
["--selection-fd","3","--config-fd","4","--formal-root","9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5","--child-gitlink","93a89ba61306d840a008813f62f26a34d54850f4","--selection-raw-sha256","8fe4585f366cb69ad9181e30c25b5f4e99040c83d8ffe66426897bfa9d331edd","--config-raw-sha256","43b3b77b5934107c54b8bee157b46d07cb17b85ca89305ad6fb7405237e42d1d","--cwd","/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8","--remote","https://github.com/wxwy/psm_wma.git","--index","/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8/.authority-root.index","--evidence-path","/disk/rl/psm_wma/artifacts/g0/r09/authority_root_materialization_evidence_v1.json","--git","/usr/bin/git","--git-raw-sha256","587ef21868c948b883993e23209b86a72a6ddc06aab1545c697ffc31075acd4a","--git-version","git version 2.34.1","--interpreter","/opt/conda/bin/python3","--interpreter-raw-sha256","f3e3f561b473976be55d937616915d6c507dedcb3950c3ca72df786b28e8efdc","--interpreter-version","Python 3.11.9","--bootstrap-contract-fd","5","--bootstrap-project-root","/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8","--bootstrap-module","tools.psm_wma.materialize_immutable_source_authority_root","--adapter-path","tools/psm_wma/materialize_immutable_source_authority_root.py","--adapter-blob-oid","da782754b8e8efa0f3cae973aa68602dcda1c237","--adapter-raw-sha256","091ea62d0a8b48429c67100c1395e62a300dc47a8d8f65c7046ba00f8205b5e9","--authority-module-path","tools/psm_wma/immutable_source_authority_root.py","--authority-module-blob-oid","9937f74c49b14d489823c731aa2856b00c1a3d06","--authority-module-raw-sha256","4ebf9fb8b0605bc30c45800bdfa7d367444ff97daee69926eba9aa5c9817f5d0","--collection-module-path","tools/psm_wma/immutable_source_collection.py","--collection-module-blob-oid","eefde4e5b5a0965bbdcaa5390b9286a4c77f2665","--collection-module-raw-sha256","1b3353b0bd1342f1685062f962a7cbc1ba0dbf699bdc72c099ca470cb09cc340","--audit-module-path","tools/g0/audit_r09_b_ttt_root_gitlink_authority.py","--audit-module-blob-oid","d0020f067badfe591152fafa6336e20b485eb5ba","--audit-module-raw-sha256","3db6376b35141d8ca5dc72c1bb38359943961db92545a88f320603121db4c39e","--author-name","wxwy","--author-email","1036648581@qq.com","--author-date","2026-09-12T23:07:43+08:00","--committer-name","wxwy","--committer-email","1036648581@qq.com","--committer-date","2026-09-12T23:07:43+08:00","--commit-message","chore: materialize immutable source authority root"]
```

这正是 adapter `argv_sha256` 的 authority。启动 fixed Python 的完整 `sys.orig_argv` 前缀固定为
`[python,"-I","-S","-B","-c",bootstrap,"--"]`；因此 bootstrap 所见 `sys.orig_argv[6:]`
是 compact JSON ` ["--", *actual_argv]`（2,432 bytes，SHA-256=
`aefa3a7d02be8ca5af6572e59eb125ced458b739d5f9ac2cc8fc3122018455a6`），不是上一段 digest。

bootstrap contract 唯一 canonical UTF-8 JSON（182 bytes，SHA-256=
`62a7bbf5fcb609e52931639001e6db01df81f0de2a33afd41c0080eb8e903f68`）为：

```json
{"bootstrap_argv_sha256":"aefa3a7d02be8ca5af6572e59eb125ced458b739d5f9ac2cc8fc3122018455a6","bootstrap_raw_sha256":"7e1c0ecc2161984a88ea0d0eae82f9f7ced709ca919f0302f74a3a068e08c9b8"}
```

## 3. transaction environment authority

v0.2 的 six-key JSON 是 launcher/bootstrap environment；production `NativeAuthorityGit.env` 是不同且
独立的 mapping。其唯一 canonical UTF-8 JSON 为（471 bytes，SHA-256=
`daf9e4bfb1740f5e94d038547619256b900eb16be7830bd37c7df8d4f6a0f235`）：

```json
{"GIT_AUTHOR_DATE":"2026-09-12T23:07:43+08:00","GIT_AUTHOR_EMAIL":"1036648581@qq.com","GIT_AUTHOR_NAME":"wxwy","GIT_COMMITTER_DATE":"2026-09-12T23:07:43+08:00","GIT_COMMITTER_EMAIL":"1036648581@qq.com","GIT_COMMITTER_NAME":"wxwy","GIT_CONFIG_GLOBAL":"/dev/null","GIT_CONFIG_NOSYSTEM":"1","GIT_CONFIG_SYSTEM":"/dev/null","GIT_INDEX_FILE":"/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8/.authority-root.index","GIT_NO_REPLACE_OBJECTS":"1","LANG":"C","LC_ALL":"C"}
```

`commit-message` 不是环境变量；它唯一作为 `git commit-tree` stdin UTF-8 payload
`chore: materialize immutable source authority root`。任何未列环境变量、argv item、FD 或 stdin
bytes 均 FAIL；execution request/evidence 必须逐字复现上述两种 environment、argv、contract 和
metadata，且仍在 mutation 前重观测所有 freshness/routing/expected-zero predicate。

## 4. 边界与 verdict

本文件不授权 materialization、source/checkpoint I/O、JSON/worktree/index/candidate/ref/evidence、
collection/receipt/publication、child、GPU、训练、评测、推理或 LIBERO4IN1。请求唯一 verdict：

```text
APPROVE_TO_PREPARE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_EXECUTION_REQUEST
```

或 `REQUEST_CHANGES(file:line)`；即使批准，完整 execution request 和命令仍需独立同 pair 三方
`APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT`。
