# Authority-root one-shot materialization execution request v0.4

**日期**：2026-09-13
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`
**状态**：docs-only replacement request；待独立同 pair 三方 `APPROVE_TO_MATERIALIZE`。

## 替代关系与批准对象

本文件替代 v0.3。唯一 runtime authority 是
`PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_execution_snapshot_annex_v0.4.md`：其继承的
v0.3 formal parent=`9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5`、Gitlink=
`93a89ba61306d840a008813f62f26a34d54850f4`、fixed ref、tools、inputs、FD、bootstrap、argv、environment
和 metadata，以及新增 canonical launcher procedure artifact，均逐字冻结。v0.3 request/annex 不能用于
执行；不得增加、替换、延后或由环境推导任何 authority。

唯一请求的单次事务仍只允许：以 frozen launcher 创建三个 canonical backing object、以 formal parent 为
唯一 parent 创建 authority candidate、独立 verifier PASS 后对 fixed ref 做一次 local/remote expected-zero
CAS，并写唯一 canonical evidence。canonical launcher procedure 的 exact Git worktree add/remove argv、
backing path/bytes/identity/fsync/re-read、FD 3/4/5 binding/offset/CLOEXEC/close set、final `execve` arrays
及 pre-adapter cleanup proof 已在 annex v0.4 §2--§4 完整冻结；不得使用 shell、PATH、stdin、remote alias、
caller mapping、ambient environment、credential/proxy 或额外 FD/argv。

执行前仍须重新验证 clean root/index/evidence/.pending freshness、formal tree/Gitlink、四模块/interpreter/
Git identity、selection/config/contract bytes、两种 environment、FD no-follow regular-file contract、routing
authority 及 local/remote ref expected-zero。任一漂移为零 mutation FAIL；launcher-owned cleanup 不能完整
证明则为 `ROLLBACK_INCOMPLETE`，不得 retry、换路径/ref/parent 或继续 collection/训练。

## 禁止范围与 verdict

本文件不执行命令；不授权 source/checkpoint I/O、collection/receipt/publication/root audit、child、GPU、
训练、评测、推理或 LIBERO4IN1。请求唯一 verdict：

```text
APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT
```

或 `REQUEST_CHANGES(file:line)`。
