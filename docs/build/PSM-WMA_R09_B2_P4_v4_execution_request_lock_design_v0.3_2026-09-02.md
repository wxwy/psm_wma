# R09-B2 P4-v4 Execution-Request Lock 静态设计 v0.3

**状态**：draft，替代未获实现授权的 v0.2。仅申请 root static planned-commitment tooling 与 stdlib CPU fixture；禁止真实 P4 preflight、materialize/staging、candidate、record/refreeze、P5 export/compose、torchrun、GPU 与训练。

## 1. 审核整改与唯一 authority

本版合并 ChatGPT review `e6593d5` 的 B1--B3；Kimi 对 v0.2 为 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_LOCK_STATIC_TOOLS`，MM 独立复核未发现额外结构性缺陷。P4-v4 full request static closure=`8535a8c`、P5 full-config static closure=`49e6ccf`、P5 evidence Git authority implementation=`3e3a853`（ChatGPT closure=`507a343`）及 materialization helper closure=`bda9737`/ChatGPT=`6910a72` 均只作为 static prerequisite；P5 evidence authority 仍默认未填充，真实 evidence 只能在独立 record/refreeze closure 后由新的 reviewed verifier revision 锚定。Gitlink 固定为 `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`。

工具内置 immutable `AUTHORIZED_P4_V4_LOCK_SPEC`；默认 `None`，此时任何调用必须 zero-write fail-closed。未来独立 reviewed root revision 才可填入 exact source commit/tree/Gitlink、tracked spec path、Git-blob/current-byte/canonical-raw SHA256、output parent lexical identity与唯一 basename。工具以 single-fd `O_NOFOLLOW` 一次读取该 spec，并以同一 raw 完成 canonical parse、SHA 与 `git show <commit>:<path>` byte equality；caller、CLI、cwd、environment 不得提供路径、dict、digest 或其他 semantic authority。

## 2. 两阶段 roster 生命周期

`preflight.json` 必含 P4 request/result/verification 的实际 SHA；其 result/verification SHA、P4 outcome 与最终 evidence authority 均不能由 pre-execution inputs 无循环地决定。因此本 Gate **不再输出** `r09_b2_p4_v4_execution_request_v1`，不向 `run.<backend>.roster_sha256` 写值，也不声称得到 final P5 roster SHA。

本 Gate 唯一输出 canonical `r09_b2_p4_v4_planned_roster_commitment_v1`。它只冻结两个 backend 的 lexical future identities、run token、candidate/attempt binding、已关闭 request-section identities，以及将来 final roster 的 P5-compatible deterministic **staging projection**。该 projection 是 ordered `entries` array；每行 key-set 精确为 `{path,type,mode,sha256}`，按 `path` byte lexical ascending 排序：

- `import_staging` 与 `import_staging/<run_token>` 是 `directory`，mode=`0555`、sha256=`""`；
- `payload_manifest.entries` 的每一 regular item映射为同 path 的 `regular` row，mode=`0444`、sha256 等于 manifest SHA；
- 禁止 `preflight.json`、任何未知路径、symlink、hardlink、或 caller supplied roster/digest。

该 projection 使用 P5 已有 canonical serializer `json.dumps(..., ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\\n"`，且只可由 verifier-owned spec 的 exact payload manifest/token 重建。它不计算也不携带名称为 `roster_sha256` 的 parallel/final digest；永久 fixture 以同一 serializer 重算并验证每个 row、排序、path-set、type、mode 与 file SHA。

后续独立 `P4 record/refreeze` 设计必须先生成实际 canonical `preflight.json`（精确 key-set `{request_relpath,request_sha256,result_relpath,result_sha256,verification_relpath,verification_sha256}`），再将其 `regular/0444/SHA` row 与本 commitment 的 projection 合并为**精确** P5 roster object `{entries,sha256}`，其中 `sha256=SHA256(canonical_bytes({"entries": entries}))`。该 Gate 才能把该 final digest 写入 immutable final request 的 `run.<backend>.roster_sha256`，并证明其与 P5 `_validate_roster` 的同一 object/hash definition byte-for-byte 一致。该后续 Gate 不属于本设计，仍不授权 record/refreeze 或真实执行。

## 3. 输出 FD 合同与终态

输出 parent/basename 完全来自 `AUTHORIZED_P4_V4_LOCK_SPEC`。parent 从 `/` 按 lexical component 用 `O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC` 的 openat/fstat 链锚定；target 以同一 FD 的 `O_RDWR|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC` 创建。创建后成功路径严格为：完整 write canonical raw、`fsync(fd)`、same-FD `lseek`/read-back 的逐字节与 SHA equality、`fchmod(fd, 0o444)`、`fstat(fd)` 确认 regular file 与 exact `0444`、close 成功；仅此时返回 `FROZEN_NOT_EXECUTABLE`。

create 前任一错误为 `NOT_LOCKED` 且 zero-write；create 后的 short-write/write/fsync/seek/read-back/fchmod/fstat/close 任一错误均为 `POISONED_NOT_LOCKED`，保留原 path，禁止 unlink、rename、repair、overwrite或 retry。poison path 或单纯文件存在均不构成后续 record/refreeze、execution 或 P5 authority。

## 4. fixture、边界与 re-review

永久 stdlib CPU fixtures 覆盖：default `None` zero-write；constant/spec commit/tree/blob/current/raw drift；caller injection；P5 staging-projection row/order/path/type/mode/SHA drift；token/pair reuse；禁止 premature `preflight.json` 和任何 `roster_sha256`；future lexical/reuse；parent/target symlink或existing；create-before 零写；short-write/write/fsync/seek/read-back/fchmod/fstat/close poison；ambient PATH/PYTHONPATH/locale independence；禁止 subprocess/P5 child/torch；P4 CLI hard-stop且不调用 materialization helper。

本设计仅请求 `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_LOCK_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 file:line）。即使 static closure，仍不得生成 real final request 或 preflight；真实 preflight仍须先经 record/refreeze Gate 固定 exact final request raw/SHA，再另获三方 `APPROVE_TO_EXECUTE_P4_V4_PREFLIGHT_CPU_ONLY`。record/refreeze、P5 export/compose、GPU、训练仍分别未授权。
