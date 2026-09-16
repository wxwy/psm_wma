# Source-evidence closure request instance real-output execution design v0.3

本 amendment 版本化覆盖 v0.2 的发布原语与权限矛盾。目标 JSON/Markdown 仍为固定 sibling 路径；发布不是
Git commit，HEAD/index/worktree 不变。staging 目录仍为目标目录下 `.request_instance_stage`，目录 `0700`、
当前 uid/gid；staged 文件创建使用 `O_CREAT|O_EXCL|O_NOFOLLOW`、mode `0644`，写完 `fsync(fd)`，再
`fsync(parent_fd)`。

每个目标的 no-overwrite 发布原语固定为 `os.link(staged_path, target_path, follow_symlinks=False)`：目标已存在
返回 `EEXIST`，立即终止为 `REAL_OUTPUT_WRITE_FAILED`，不得 fallback 到 `os.replace`、unlink 或 retry。link
成功后以 no-follow fd 校验 target/staged 的同一 inode、mode `0644`、当前 uid/gid、parent identity、size、raw
SHA；两个 sibling 按 JSON 后 Markdown 顺序分别 link，故 partial publish 只能记录 `none|json|markdown|both`。

失败时只向 SESSION 记录 terminal、stage/target 路径、存在性、size、raw SHA、published_side 与失败步骤；不
清理、不覆盖。构造器 formal root=`e33c1c05013284039f82cd411a3398dceb45d781`、child=`93a89ba61306d840a008813f62f26a34d54850f4`；
本 amendment 仅请求 design review，不授权真实写入、source I/O、GPU 或训练。

请求 verdict：`APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_REAL_OUTPUT_EXECUTION`
或 `REQUEST_CHANGES(file:line)`。
