# Authority-root one-shot materialization execution request v0.3

**日期**：2026-09-12
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`
**状态**：docs-only；待独立同 pair 三方 `APPROVE_TO_MATERIALIZE`。

## 唯一 authority

本文件替代此前 execution request 的运行时描述。唯一运行时 authority 是
`PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_execution_snapshot_annex_v0.3.md`：
formal parent=`9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5`、Gitlink=
`93a89ba61306d840a008813f62f26a34d54850f4`、fixed ref、工具、输入、FD、bootstrap、argv、
两种 environment 与 metadata 均逐字引用。后续不得加入、替换、延后或由环境推导任何 authority。

## 允许的单次事务

仅在所有 annex 预检通过后，允许在 fresh clean root 使用 FD 3/4/5、frozen Python 的
`-I -S -B -c` bootstrap 和 exact `actual_argv`：创建两个 canonical JSON、一个以 formal parent
为唯一 parent 的 candidate；独立 verifier PASS 后，对 fixed ref 做一次 local/remote expected-zero
CAS，并写唯一 canonical evidence。启动不得使用 shell、PATH、remote alias、stdin、caller mapping、
ambient environment、credential/proxy、额外 FD 或 argv。

执行前必须重新验证 clean root/index/evidence/.pending freshness、formal tree/Gitlink、四模块/
interpreter/Git identity、selection/config/contract bytes、两种 environment、FD no-follow regular-file
contract、routing authority及 local/remote ref expected-zero。任一漂移均为零 mutation FAIL。

## PASS、FAIL 与停止

PASS 要求：single-parent exact two-path candidate；独立 verifier 重算两 raw bytes、native OID、
full tree delta、Gitlink 与 seven-key `root_revision` binding；local/remote CAS 都精确指向 candidate；
evidence 可独立验证且不含 raw input/source path/URL/secret。

失败立即停止。已发生 mutation 时只能由 frozen adapter 作 ownership-aware rollback；无法证明恢复时
结果为 `ROLLBACK_INCOMPLETE`，不得重试、换路径/ref/parent，或继续 collection/训练。

## 禁止范围与 verdict

本文件不执行命令；不授权 source/checkpoint I/O、collection/receipt/publication/root audit、child、GPU、
训练、评测、推理或 LIBERO4IN1。请求唯一 verdict：

```text
APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT
```

或 `REQUEST_CHANGES(file:line)`。
