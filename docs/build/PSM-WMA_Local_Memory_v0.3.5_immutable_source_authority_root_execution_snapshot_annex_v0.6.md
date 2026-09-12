# Authority-root execution snapshot annex v0.6

**日期**：2026-09-13
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`
**状态**：docs-only remediation；待新 formal pair 三方审核。

## 替代与唯一 artifact

本文件完全 supersede v0.5 annex/request 对 launcher 的规定；v0.2/v0.3 的 formal parent、Gitlink、输入、
bootstrap、actual argv、环境、FD ABI、工具 identity、fixed ref 与禁止项不变。唯一可执行 artifact 为
`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.6.py`，其 formal-tree raw
length 与 SHA-256 必须由提交后静态核验回填；`launch.argv[5]` 唯一等于该 raw UTF-8，不可由 shell、PATH、
环境、文件读取或 operator 重建。

## v0.5 四项 HIGH 的闭合规则

1. payload 内联 v0.2 selection/config 与 v0.3 actual-argv 的 exact canonical bytes，分别以
   `516/8fe4585f...`、`508/43b3b77b...`、`2427/72777bd7...` 启动前复算。候选 parent 仍固定
   `9dd2fb8...`；只从其 tree 读取仍属于它的 adapter blob，不再错误地要求后置 annex 属于该 tree。
2. 每个 backing object 以 `O_EXCL|O_NOFOLLOW` 写入、完整循环 write、fsync、writer/reader/target
   `(dev,ino,size)` 与 raw bytes 比对；`rd==target` 时不 close target。三个 target 均 seek 到零、设
   inheritable，随后枚举并关闭除 `{3,4,5}` 外全部 FD，再枚举断言恰为该集合。
3. 首个 `git worktree add` 已纳入 transaction。成功后必须绑定 clean-root identity、detached
   `HEAD==FORMAL`、clean status 和 porcelain worktree entry。失败时仅当 retained clean-root identity
   未漂移才 remove；随后证明 clean root、index、evidence、pending 均 absent 且 worktree listing 无该路径。
   任何路径/route/cleanup 不确定都以唯一终态 `ROLLBACK_INCOMPLETE` 退出，保留现场且禁止 retry。
4. 当前正式 root 的普通 `.git` directory 是唯一接受 route：payload 保留 `O_DIRECTORY|O_NOFOLLOW`
   admin FD 与 `O_NOFOLLOW` config FD，所有 native Git 前后同时检查 pathname、retained-FD identity/raw
   bytes、`config.worktree` absence 及既有 allowlist。linked-worktree/`.git` file route 明确 fail-closed，
   因而不能无绑定地进入 common-dir authority。

## 验收与边界

静态验收必须包括：artifact `py_compile`；内联三段 bytes length/SHA；同号和异号 FD handoff、额外 inherited
FD、route/config replacement、post-add drift、foreign clean-root replacement、cleanup fail 与成功 cleanup 的
temporary-only causal witnesses。任何测试不得使用本项目真实 root、source/checkpoint 或 production 路径。

请求唯一 verdict：`APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT` 或
`REQUEST_CHANGES(file:line)`。本文件不授权 materialization、source/checkpoint I/O、JSON/worktree/index/
candidate/ref/evidence、collection/receipt/publication、child、GPU、训练、评测、推理或 LIBERO4IN1。
