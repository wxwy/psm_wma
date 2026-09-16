# Source-evidence closure request instance real-output execution design v0.2

**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-REQUEST-INSTANCE-REAL-OUTPUT-EXECUTION-DESIGN`

本 amendment 版本化覆盖 v0.1 的机械语义，并引用已关闭 memory-only constructor formal root=
`e33c1c05013284039f82cd411a3398dceb45d781`、child=`93a89ba61306d840a008813f62f26a34d54850f4`。

1. “单次受控提交”明确为文件系统发布，不是 Git commit；HEAD/index/worktree 不变。两个 staged 文件在目标
  目录同一文件系统内创建，使用 `O_CREAT|O_EXCL|O_NOFOLLOW`、mode `0600`，写完 `fsync(fd)`；发布使用
   `os.replace` 前的 parent-directory `fsync`，禁止覆盖既有目标。
2. staging 目录固定为目标目录下 `.request_instance_stage`，必须事先不存在；目录 mode `0700`、owner 为当前
   uid/gid。两个 staged path 必须 regular non-symlink、mode `0600`，并以单独 no-follow fd readback 校验 bytes/size/SHA。
3. 目标 JSON/Markdown 仅在不存在时发布，mode `0644`、owner 当前 uid/gid；发布后以 no-follow fd、parent
   identity、mode/owner、byte equality 和 JSON self-bound SHA 验证。
4. 失败证据只写入 SESSION：记录 terminal=`REAL_OUTPUT_WRITE_FAILED`、stage/target 路径、各自存在性、size、
   raw SHA、published_side（`none|json|markdown|both`）和失败步骤；不清理、不覆盖、不 retry。该失败日志不写入
   request pair，避免产生第三个输出。
5. 执行白名单为 constructor module/test、real-output writer module/test、TODO、SESSION 与本 design；本 amendment
   仅授权继续设计审核，不授权真实写入。请求 verdict：
   `APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_REAL_OUTPUT_EXECUTION` 或
   `REQUEST_CHANGES(file:line)`。
