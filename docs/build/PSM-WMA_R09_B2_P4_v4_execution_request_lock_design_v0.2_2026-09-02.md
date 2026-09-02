# R09-B2 P4-v4 Execution-Request Lock 静态设计 v0.2

**状态**：draft，替代未获实现授权的 v0.1。仅申请 root static request-lock tooling 与 stdlib CPU fixture；禁止真实 P4 preflight、materialize/staging、candidate、record/refreeze、P5 export/compose、torchrun、GPU 与训练。

## 1. verifier-owned lock authority

工具内置 immutable `AUTHORIZED_P4_V4_LOCK_SPEC`；默认值为 `None`，此时所有 lock 请求必须 fail-closed，且零 output-file 写入。只有未来独立 reviewed root revision 才能把该常量填为 exact authority：`schema_version`、source Git commit/tree/Gitlink、tracked spec relative path、spec Git-blob SHA256/current-byte SHA256、canonical spec raw SHA256、output parent absolute lexical identity及唯一 output basename。此 reviewer-owned constant，而非 CLI、environment 或 caller dict，是 future execution values 的唯一 authority。

spec 必为 canonical `r09_b2_p4_v4_execution_lock_spec_v1` bytes，经 single-fd `O_NOFOLLOW` open/fstat/read 一次；同一 raw 同时用于 canonical parse、SHA 与 Git `show <commit>:<path>` byte equality。source/full-clean/Gitlink/submodule、tracked regular file、exact HEAD/commit/tree/blob/current-byte 任一不等即 FAIL。caller 只能请求工具读取 constant 指向的 spec，不能提供语义字段、路径、SHA或替代 spec。

## 2. deterministic final request and roster

spec 的 exact key-set 含已关闭 entry/source/interpreter/environment/authorities/backends identities、两 backend future run/candidate identity、attempt/token，及每 backend verifier-owned ordered `planned_roster` records。record key-set、canonical ordering、relative-path grammar、regular-file identity/SHA与 source/payload-manifest binding均精确冻结；工具从该 records 序列的 canonical bytes独立计算 `roster_sha256`，不得接受 caller digest。每个 request `run.<backend>.roster_sha256` 必等于该重算值，`candidates.<backend>.run` 必等于生成的 final run object；任一 mismatch 在 output create 前 FAIL。

future root 只可由 spec 导出，必须绝对、词法规范、pairwise non-reuse、与 source/submodule/evidence/output namespace 不重叠；existing-prefix nofollow/symlink 检查只读，最终 root、candidate、staging及 output target 均在锁定前不存在，绝不 mkdir/materialize。

## 3. output FD contract and terminal states

output parent 及 basename完全来自 `AUTHORIZED_P4_V4_LOCK_SPEC`，而非 caller。parent 通过 `/` anchored per-component `O_DIRECTORY|O_NOFOLLOW` openat/fstat 链获得 FD；basename以 `O_CREAT|O_EXCL|O_WRONLY|O_NOFOLLOW|O_CLOEXEC` 单 FD create。成功仅当：完整 raw 写入、`fsync(fd)` 成功、从同一 FD `lseek`/read-back 得到逐字节相同 canonical raw及同一 SHA、close 成功。只在全部条件满足时返回 `FROZEN_NOT_EXECUTABLE` raw/SHA。

create 前错误为 `NOT_LOCKED` 且零写；任何 create 后的 short-write/write/fsync/read-back/close错误为 terminal `POISONED_NOT_LOCKED`，保留该 path，不 cleanup、rename、overwrite、repair或retry。后续 lock 和 execution Gate 都要求 authority target为唯一成功 raw/SHA，单凭文件存在或 poison path 永不构成输入授权。

## 4. fixture、执行边界与后续 Gate

fixtures覆盖：默认 `None` authority零写；constant/spec commit/tree/blob/current-byte/SHA/schema drift；caller spec/path/dict injection；每个 roster record/order/path/SHA、run/candidate equality与digest mismatch；future lexical/root reuse；parent/target symlink/existing；create前零写；short-write/fsync/read-back/close poison；ambient PATH/PYTHONPATH/locale independence；禁止 subprocess/P5 child/torch；P4 public CLI hard-stop且不调用 materialization helper。

本设计只请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_LOCK_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 file:line）。即使 static implementation closure，真实 preflight仍必须针对由 future independently-reviewed lock authority 生成的 exact raw/SHA，另获三方 `APPROVE_TO_EXECUTE_P4_V4_PREFLIGHT_CPU_ONLY`；仍不授权 record/refreeze、P5 export/compose、GPU或训练。
