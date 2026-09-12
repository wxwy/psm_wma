# Authority-root execution snapshot annex v0.1

**日期**：2026-09-12  
**范围**：仅 `15e665576c8af37dbbbaf15cd05d2b4bf6af2f63` 三方批准的只读 annex；非执行请求。

## 冻结 authority

- candidate 唯一 parent：`9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5`；child Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`。
- fixed ref：`refs/heads/authority/r09-b-ttt-v035-immutable-source-v1`，local/remote 均 expected-zero。
- endpoint：`https://github.com/wxwy/psm_wma.git`；UTF-8 SHA-256：`8ddb34607979ff80a7b97732199b7c7a6439c81d1154eda97039bada69a02dae`。不得以 remote alias 替代。
- Python：`/opt/conda/bin/python3`，SHA-256=`f3e3f561b473976be55d937616915d6c507dedcb3950c3ca72df786b28e8efdc`，`Python 3.11.9`；Git：`/usr/bin/git`，SHA-256=`587ef21868c948b883993e23209b86a72a6ddc06aab1545c697ffc31075acd4a`，`git version 2.34.1`。
- clean worktree：`/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8`；index：其下`.authority-root.index`；evidence：`/disk/rl/psm_wma/artifacts/g0/r09/authority_root_materialization_evidence_v1.json`及`.pending`。本 annex 观测时三者均 absent；执行前须再次证明 fresh。

## 输入与模块

- selection：516 bytes，SHA-256=`8fe4585f366cb69ad9181e30c25b5f4e99040c83d8ffe66426897bfa9d331edd`，native OID=`9f03614b691bca3ba834e16e65ee983fe95af74c`。
- config：508 bytes，SHA-256=`43b3b77b5934107c54b8bee157b46d07cb17b85ca89305ad6fb7405237e42d1d`，native OID=`89b12047c50a3a924521200d1897b13bf30aacfe`。
- adapter：`da782754b8e8efa0f3cae973aa68602dcda1c237` / `091ea62d0a8b48429c67100c1395e62a300dc47a8d8f65c7046ba00f8205b5e9`；authority、collection、audit identity 逐字继承 v0.2 §2。

## ABI 与停止条件

唯一启动形态为冻结 Python 的 `-I -S -B -c` stdlib bootstrap；sanitized environment 仅包含
`GIT_NO_REPLACE_OBJECTS=1`、`GIT_CONFIG_NOSYSTEM=1`、`GIT_CONFIG_GLOBAL=/dev/null`、
`GIT_CONFIG_SYSTEM=/dev/null`、`LC_ALL=C`、`LANG=C`。两个输入仅以 fresh regular/non-symlink FD
传入；bootstrap contract FD 也必须 fresh regular。实际 FD numbers、bootstrap raw bytes、完整 argv
canonical bytes/SHA 与 commit metadata 必须在后续 execution request 中同本 annex 一起冻结并获新的
三方 `APPROVE_TO_MATERIALIZE`；本 annex 不创建任何 FD backing file、worktree、index、candidate、ref
或 evidence。

任一 identity、freshness、routing-authority、endpoint、input canonicality 或 expected-zero drift 都是
零 mutation FAIL。不得 source read、collection、child 修改、GPU、训练、评测或推理。
