# Stage-1 authority-root materialization request v1.3

**状态**：docs-only remediation，待三方审核；绝不执行。

v1.3 替代 v1.2，仅关闭其三方已汇总的两个问题：同轮 freshness 与 parser/replay 内部一致性。candidate parent、child、ref、输入、FD ABI、closure、环境、metadata 和 Stage-1 tuple-only hard-stop 不变。

## 同轮 fresh binding

构造时重新观察：`.git`=`1048655:9223372050462812349:directory`（目录 size 会随合法 Git bookkeeping 变化，非身份字段）；`.git/config`=`1048655:3075283643:477:regular`，SHA-256=`f15e655f21ecf517b9074fbf99b6ebccd4aff99489735776769ecb510cb8b611`；fixed ref local rc=1、remote zero lines；clean/index/evidence/pending 全 absent。任何执行前漂移仍是 `BLOCKED_AUTHORITY_NOT_CLOSED`。

## 唯一 ordered replay

先解析 base `RAW[2]`，在 array 内同时写入 formal/FD8 和 adapter/collection 的 b359 值，插入 owner FD，再 canonical serialize 并 splice 一次；之后只替换 source-level formal/clean 和 bootstrap/parser/contract expected identities。唯一结果：parser `2336/51a82a6b2efb9aeee2cc2ecf057d5b7b16a6a841a1ed26c484e98b4a9f483e7d`、bootstrap argv `2341/3227a514b8bcfe4e557d7ea890964a97cd8a978f208ed36d4671c8d5e680bbb8`、contract `182/a434efd7eaa56d5217f88e0d0eee8697c523e38fb3fe625af4d0007f26ea1c5a`、payload `17389/4b85f226f3de63821fcaa922cc353d3917983bcf00adfeff1bade448914b599a`。

Canonical JSON=`7775 bytes`/`82f3103518ea953f6295e955f1d1f24e7945287dd19c1a47365647ca5fc22f7a`。请求 verdict：`APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT` 或 `REQUEST_CHANGES(file:line)`。未获新 exact pair 三方批准前，禁止 materialization、真实 I/O、child、GPU和训练。
