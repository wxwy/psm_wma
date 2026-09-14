# Stage-1 authority-root materialization request v1.1

**Gate**：`G0-R09-B-TTT-V035-STAGE1-AUTHORITY-ROOT-MATERIALIZATION-REQUEST`
**状态**：docs-only exact-request replacement；待三方审核，绝不执行。
**替代关系**：本文件替代 v1.0（formal `d474849d7bf3bf556886f2887b2325aaab36a868`）的 HIGH-1。v1.0 仅可作历史草案；不得由其触发执行。

## 1. 已冻结的不可变 request instance

本 instance 的 candidate parent=`b3595395427114f73ff53a19a0c2b9180e39905f`，child Gitlink=
`93a89ba61306d840a008813f62f26a34d54850f4`，唯一 ref=
`refs/heads/authority/r09-b-ttt-v035-immutable-source-v1`，remote=
`https://github.com/wxwy/psm_wma.git`。它只可产生一个 authority tuple 后硬停；任何 review/ledger
commit 均不得成为 candidate parent 或 Stage-2 receipt。

选择与配置是下列**原始字节**，不是批准后才生成的配置：

| input | FD | bytes | SHA-256 | exact raw UTF-8 |
|---|---:|---:|---|---|
| selection | 3 | 516 | `8fe4585f366cb69ad9181e30c25b5f4e99040c83d8ffe66426897bfa9d331edd` | `{"entries":[{"ordinal":0,"relative_path":"model/.metadata"},{"ordinal":1,"relative_path":"model/__0_0.distcp"},{"ordinal":2,"relative_path":"optim/.metadata"},{"ordinal":3,"relative_path":"optim/__0_0.distcp"},{"ordinal":4,"relative_path":"scheduler/.metadata"},{"ordinal":5,"relative_path":"scheduler/__0_0.distcp"},{"ordinal":6,"relative_path":"trainer/.metadata"},{"ordinal":7,"relative_path":"trainer/__0_0.distcp"}],"schema":"immutable_source_selection_request_v1","source_kind":"checkpoint_source_manifest_v1"}` |
| config | 4 | 508 | `43b3b77b5934107c54b8bee157b46d07cb17b85ca89305ad6fb7405237e42d1d` | `{"enable_input_bias":false,"k_local":1,"local_evidence_feature_version":"causal_visual96_executed_action10_v1","local_fast_state_dtype":"fp32","local_history_backend":"ttt_fast_weight","local_history_enabled":true,"local_history_evidence_dim":106,"local_history_state_enabled":false,"local_memory_dim":32,"local_memory_enabled":true,"local_runtime_resume_mode":"slow_only_no_mid_episode_resume","local_ttt_enabled":true,"schema":"canonical_native_local_ttt_config_v2","ttt_inner_lr":0.1,"ttt_tbptt_steps":16}` |

FD5 is the exact 182-byte canonical bootstrap contract, SHA-256
`a434efd7eaa56d5217f88e0d0eee8697c523e38fb3fe625af4d0007f26ea1c5a`; FD8 is the clean-owner
directory capability. The executor must open these four inputs before the first mutation, require regular/no-follow
FD3/4/5 and directory/no-follow FD8, and record `fstat=(st_dev,st_ino,st_size,S_IFMT)` in the result. Any mismatch
against the byte identities above, FD number, type, or later retained-FD recheck is `BLOCKED_AUTHORITY_NOT_CLOSED`.
Those runtime inode values are verification outputs, not caller-controlled substitutions for this immutable instance.

## 2. Literal launcher contract

The outer interpreter is exactly `/opt/conda/bin/python3` (`Python 3.11.9`, raw SHA-256
`f3e3f561b473976be55d937616915d6c507dedcb3950c3ca72df786b28e8efdc`) with literal prefix
`["/opt/conda/bin/python3","-I","-S","-B","-c"]`. Its `-c` payload is the only v0.9 deterministic overlay:
base blob `615d6b117f810c4cb8c9459971caa32589352c93`, base raw SHA-256
`3a5b4cd99730ddb01098ed53d4278f1f7b8ef142bc234405095df54de4ec7ea5`, derived bytes=17,389,
derived SHA-256=`4b85f226f3de63821fcaa922cc353d3917983bcf00adfeff1bade448914b599a`.

Its literal sanitized environment is exactly:

```json
{"GIT_CONFIG_GLOBAL":"/dev/null","GIT_CONFIG_NOSYSTEM":"1","GIT_CONFIG_SYSTEM":"/dev/null","GIT_NO_REPLACE_OBJECTS":"1","LANG":"C","LC_ALL":"C"}
```

The inner parser argv is the canonical 2,336-byte JSON with SHA-256
`51a82a6b2efb9aeee2cc2ecf057d5b7b16a6a841a1ed26c484e98b4a9f483e7d`; it binds the parent/child above,
FD3/4/5/8, `/proc/self/fd/8`, `/proc/self/fd/8/.authority-root.index`, evidence path
`artifacts/g0/r09/authority_root_materialization_evidence_v1.json`, Git `/usr/bin/git` raw SHA-256
`587ef21868c948b883993e23209b86a72a6ddc06aab1545c697ffc31075acd4a`, and the fixed commit metadata
`wxwy <1036648581@qq.com>`, `2026-09-12T23:07:43+08:00`, message
`chore: materialize immutable source authority root`.

The isolated bootstrap is 8,351 bytes, SHA-256
`57266c12d011921614b66b8faaf20815bb83c37ff01e0aef5be7686598fbcb89`; its observed argv is 2,341 bytes,
SHA-256 `3227a514b8bcfe4e557d7ea890964a97cd8a978f208ed36d4671c8d5e680bbb8`. Before import it must exact-check
the four formal-tree modules: materializer `70b29267ea23dc4ca9d82d98ecd2b19423a9fc5e`/
`fc346d8133871c81ffba539d8a748c015b81e8428f1fa094ec352e6be42851be`; authority
`9937f74c49b14d489823c731aa2856b00c1a3d06`/`4ebf9fb8b0605bc30c45800bdfa7d367444ff97daee69926eba9aa5c9817f5d0`;
collection `4e9f51a52e822e7e57b67aa6ff5eaab8613566c1`/
`89eb3ee194f16665aea76ed4dcbaba803fc944d1e0b889d25be69d0831e68c67`; audit
`d0020f067badfe591152fafa6336e20b485eb5ba`/
`3db6376b35141d8ca5dc72c1bb38359943961db92545a88f320603121db4c39e`.

## 3. Fresh pre-mutation observations carried by this instance

At `2026-09-14 CST`, before this replacement was drafted: root `.git` identity was
`1048655:9223372050462812349:directory`; `.git/config` identity was
`1048655:3075283643:477:f15e655f21ecf517b9074fbf99b6ebccd4aff99489735776769ecb510cb8b611`.
`show-ref --verify refs/heads/authority/r09-b-ttt-v035-immutable-source-v1` returned rc=1 and exact remote
`ls-remote` returned zero lines. The clean root, its index, evidence, and pending evidence paths were absent.
The launcher must recheck every stated observation before mutation; a changed observation is fail-closed, not a new
request instance.

## 4. Canonical request bytes and stop condition

The reviewed immutable bytes are
`PSM-WMA_Local_Memory_v0.3.5_stage1_authority_root_materialization_request_v1.1.json` in this same formal tree:
**7,262 bytes** (the compact JSON plus one final LF), SHA-256
`7ba87345383657884024f9c0dd0c60489aac1ae7d6436df9340df8d3f08a95c1`. It is compact UTF-8 JSON with sorted
keys and contains the literal selection/config/bootstrap raw UTF-8 values, the full 2,336-byte parser argv array,
FD3/4/5/8 ABI, payload byte address, six-key environment, commit metadata, four-module closure, exact route
snapshot and all absence predicates. The payload `-c` source is byte-addressed by its closed v0.9 overlay digest;
the launcher must reconstruct it only by that frozen overlay, verify its bytes/digest, and execute no other string.

Before any mutation the launcher must recalculate the exact JSON bytes and SHA above, then recheck the retained-FD
and fresh-route predicates. Any byte-length or digest difference, identity drift, missing field or non-absent ref is
`BLOCKED_AUTHORITY_NOT_CLOSED`; runtime revalidation may only reject this reviewed instance, never construct a
different request.

PASS is only a committed authority tuple and hard stop. This request does not authorize collection, receipt,
source-evidence, record, package, publication, child/runtime changes, GPU/CUDA/torchrun, training, evaluation,
inference, LIBERO4IN1, or any downstream Stage-2 action.

## Verdict

Request exactly `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT` or
`REQUEST_CHANGES(file:line)`.
