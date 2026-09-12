# Authority-root execution snapshot annex v0.5

**日期**：2026-09-13
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`
**状态**：docs-only remediation；待新 formal pair 三方审核。

## 1. 替代关系

本文件完全 supersede annex v0.4 与其 replacement request。v0.2/v0.3 已冻结的 formal
parent、Gitlink、输入 raw bytes、bootstrap raw、actual argv、环境、FD ABI、工具 identity 与
fixed ref 逐字继承；本版只关闭 v0.4 遗留的 launcher payload、`execve` argv 和首次 Git
mutation 前 routing authority 三个缺口。本文件不执行 payload，不创建任何 worktree、backing
file、index、candidate、ref 或 evidence；不读取 source/checkpoint，不改 child，不使用 GPU。

## 2. 唯一 launcher artifact 与 `-c` bytes

唯一 payload 是 formal-tree regular file：

```text
path = docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.5.py
raw byte length = 8542
raw SHA-256 = cfbb67dc1583eaab433176ad44c16635c09907efda17bdf6167b23a37540461b
```

它是 UTF-8、无生成步骤的标准库 Python source；审批时必须以该 formal tree 的 blob raw bytes
与上述 length/SHA 同时核验。`launch.argv[5]` **就是该 exact raw byte sequence 解码后的 UTF-8
字符串**，不是 v0.4 的文字 placeholder，也不得由 shell、PATH、文件读取、环境或 operator
重建。唯一启动数组为：

```text
["/opt/conda/bin/python3", "-I", "-S", "-B", "-c", <payload raw UTF-8>, "--"]
```

其中 `<payload raw UTF-8>` 的 identity 仅由本节 path/length/SHA 规定；任何 blob、字节、编码或
argv 项差异均使 request 无效。payload 自身不接受额外 argv、环境、stdin 或 open FD；其唯一
常量均在 artifact 内，且只指向 v0.2/v0.3 已冻结的 formal blobs。

## 3. 唯一 final `execve` argv

payload 的 final argv 是下列无歧义的 exact derivation：

```text
["/opt/conda/bin/python3", "-I", "-S", "-B", "-c", bootstrap_raw,
 "--", *json.loads(v0.3.actual_argv_raw_utf8)]
```

`bootstrap_raw` 的 length=7538、SHA-256=
`7e1c0ecc2161984a88ea0d0eae82f9f7ced709ca919f0302f74a3a068e08c9b8`；
`v0.3.actual_argv_raw_utf8` 的 length=2427、SHA-256=
`72777bd7305c760c48c069eafd068f1a538383a6fdb8d40258acf3d8fc3b7ae2`。
payload 先从 formal parent 的 adapter blob 以 AST string-constant extraction 重构 bootstrap，并以
上述 length/SHA 拒绝；再从 formal-tree v0.3 annex blob 取得 actual argv JSON 并直接
`json.loads`。因此该 derivation 的输出唯一为完整 Python/flags/`-c`/bootstrap/`--`/actual argv，
不再存在 v0.4 的 `[1:]` 解释空间。final env 严格为 v0.3 six-key mapping，FD 仅为 3/4/5。

## 4. 首个 native Git 前后的 parent routing authority

payload 在每一条 native Git command 前后执行同一 `route_snapshot`/`check_route`：验证 absolute
Git executable raw SHA；`/disk/rl/psm_wma/.git` 为 non-symlink directory；common local `config`
为 non-symlink regular file，其 dev/inode/size/raw bytes 不变；`config.worktree` absent；并以已关闭
execution-authority allowlist 解析 `core.repositoryformatversion`、`core.filemode`、`core.bare`、
`core.logallrefupdates`、`core.worktree`、`extensions.worktreeconfig` 的唯一允许值。任何 route/config
drift 在 `git worktree add` 前即 FAIL；add 之后检测到 drift，只能执行 artifact 内 frozen cleanup 或
报告 `ROLLBACK_INCOMPLETE`，不得换路径、retry 或进入 adapter。

artifact 使用 frozen `/usr/bin/git --no-replace-objects -c core.hooksPath=/dev/null -c
core.attributesFile=/dev/null -c filter.lfs.process= -c protocol.file.allow=never -C /disk/rl/psm_wma`
及 v0.3 six-key env；无 remote alias、shell、PATH、ambient config、caller argv/FD authority。

## 5. 审核边界

请求唯一 `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT` 或
`REQUEST_CHANGES(file:line)`。批准前后均不授权 source/checkpoint I/O、collection/receipt/
publication、child、GPU、训练、评测、推理或 LIBERO4IN1。
