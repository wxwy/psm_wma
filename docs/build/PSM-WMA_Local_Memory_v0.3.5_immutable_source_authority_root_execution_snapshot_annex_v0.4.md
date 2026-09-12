# Authority-root execution snapshot annex v0.4

**日期**：2026-09-13
**Gate**：`G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`
**状态**：docs-only remediation；待同一三方对新 formal pair 审核。

## 1. 替代关系与唯一 authority

本文件完全 supersede `...execution_snapshot_annex_v0.3.md`。v0.3 的 formal parent、Gitlink、fixed
ref、endpoint、clean root、index/evidence、Python/Git identity、selection/config/contract bytes、四模块
identity、parser argv、bootstrap raw、两种 environment 与 metadata 全部逐字继承；本文件唯一新增的是
§2 冻结 launcher artifact 及其 invocation。后续 execution request 只能逐字复现本文件和 v0.3 的
既有 bytes，不得由 operator、shell、PATH、ambient environment 或 caller 选择任何值。

本文件本身不执行 launcher，不创建 worktree、backing file、index、candidate、ref 或 evidence；不读取
source/checkpoint，不进入 collection/receipt/publication，不改 child，不使用 GPU，不训练、评测或推理。

## 2. Canonical launcher procedure v1

唯一 launcher 是以下 canonical compact UTF-8 JSON。其文件名不是运行时输入；运行时只可从本节 raw
bytes 以绝对 frozen Python 的 `-I -S -B -c` 直接执行 `payload`。该 JSON 中每一条 argv、path、FD、
mode、环境及清理证明均为 authority；不得扩展、缩写或以 shell 代替。

```json
{"artifact":"authority_root_launcher_v1","backing":[{"fd":3,"mode":"0600","path":"/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8/.authority-root.selection.json","raw_sha256":"8fe4585f366cb69ad9181e30c25b5f4e99040c83d8ffe66426897bfa9d331edd"},{"fd":4,"mode":"0600","path":"/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8/.authority-root.config.json","raw_sha256":"43b3b77b5934107c54b8bee157b46d07cb17b85ca89305ad6fb7405237e42d1d"},{"fd":5,"mode":"0600","path":"/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8/.authority-root.bootstrap-contract.json","raw_sha256":"62a7bbf5fcb609e52931639001e6db01df81f0de2a33afd41c0080eb8e903f68"}],"clean_root":"/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8","close_policy":{"after":"only_fd_3_4_5","before_exec":"enumerate_/proc/self/fd_then_close_every_fd_except_3_4_5"},"execve":{"argv":"v0.3.bootstrap_observation_json[1:]","env":"v0.3.sanitized_launcher_bootstrap_environment","path":"/opt/conda/bin/python3"},"formal_parent":"9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5","git":"/usr/bin/git","git_env":"v0.3.sanitized_launcher_bootstrap_environment","git_prefix":["--no-replace-objects","-c","core.hooksPath=/dev/null","-c","core.attributesFile=/dev/null","-c","filter.lfs.process=","-c","protocol.file.allow=never"],"launch":{"argv":["/opt/conda/bin/python3","-I","-S","-B","-c","payload","--"],"env":"v0.3.sanitized_launcher_bootstrap_environment","path":"/opt/conda/bin/python3"},"schema":"authority_root_launcher_v1","worktree_add_argv":["/usr/bin/git","--no-replace-objects","-c","core.hooksPath=/dev/null","-c","core.attributesFile=/dev/null","-c","filter.lfs.process=","-c","protocol.file.allow=never","-C","/disk/rl/psm_wma","worktree","add","--detach","/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8","9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5"],"worktree_remove_argv":["/usr/bin/git","--no-replace-objects","-c","core.hooksPath=/dev/null","-c","core.attributesFile=/dev/null","-c","filter.lfs.process=","-c","protocol.file.allow=never","-C","/disk/rl/psm_wma","worktree","remove","--force","/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8"]}
```

上述 raw JSON 是 2,144 bytes，SHA-256=`4de774a525b183261b7e89b7351ffe605e1fc21f0461897732e18a5bab0709c4`。
它是本 Gate 的 canonical launcher procedure artifact；`payload` 是下节规定的唯一标准库过程，不是可由
运行者替换的 runtime value。任何 descriptor byte、步骤或其到 final `execve` 的映射差异均使 new request
无效。

## 3. Payload 的精确执行语义

payload 必须仅使用 Python 标准库并实现以下不可省略的确定性过程；payload raw bytes、长度和 SHA-256
必须与 new request 一起审核。该过程的常量只能来自 §2 descriptor 和 v0.3 已冻结 raw bytes。

1. 先以 no-follow `lstat` 验证 clean root、三个 backing path、index、evidence、pending 均 absent；
   再验证 `/disk/rl/psm_wma` 的 `.git` 为 non-symlink directory。任何失败均在 mutation 前退出。
2. 以 §2 `worktree_add_argv`、完全等于 v0.3 six-key launcher environment 的 `env`、`cwd=/disk/rl/psm_wma`
   调用 native Git；禁止 shell、stdin、PATH、remote alias 与额外 environment。成功后以 no-follow
   directory FD 验证 clean root regular worktree、`HEAD==formal_parent`、状态 clean，且 Git worktree
   list 仅将该 absolute clean root 绑定为本次新建项。
3. 依 descriptor 顺序，以 `O_CREAT|O_EXCL|O_WRONLY|O_NOFOLLOW|O_CLOEXEC` 和固定 `0600` 建立 backing
   regular files；循环完整写入 v0.3 selection/config/bootstrap-contract raw bytes，`fsync`，以 retained FD
   `fstat` 验证 regular/non-symlink、mode `0600`、pathname `(st_dev,st_ino)` 相同，并 `pread` 回读全量
   bytes及 SHA-256。再以 `O_RDONLY|O_NOFOLLOW|O_CLOEXEC` 打开相同 pathname，重复 identity/raw/SHA
   验证；writer FD 关闭后仅保留此三个 reader FD。
4. descriptor 的 reader FD 按顺序 `dup2(reader,3)`、`dup2(reader,4)`、`dup2(reader,5)`；每次都先
   `lseek(target,0,SEEK_SET)`，再以 `fstat`、`pread` 验证 descriptor/path identity 和完整 bytes；随后
   仅对 3/4/5 清除 `FD_CLOEXEC`。从 `/proc/self/fd` 枚举所有实际打开的 non-directory descriptor，
   精确关闭除 3/4/5 外的每一个，并重新枚举，结果必须恰为 `{3,4,5}`。任何枚举、close、identity、
   offset 或 CLOEXEC 检查失败均进入 §4 cleanup，绝不 `execve`。
5. final 调用必须是 `os.execve('/opt/conda/bin/python3', argv, env)`，其中 `argv` 逐元素等于 v0.3
   bootstrap observation JSON 的 array（即 absolute Python、`-I -S -B -c`、v0.3 bootstrap raw、literal
   `--`、v0.3 actual argv），`env` 逐项等于 v0.3 six-key canonical mapping。不得保留、合并或派生任何
   父进程环境、FD、argv 或 stdin。

## 4. launcher-owned cleanup 与终态

在 adapter 取得控制权前，payload 是 clean root、其 Git admin entry 及三份 backing object 的唯一
owner。每一个 pre-adapter exception 都按以下唯一顺序处理：关闭仍保有的 FD；仅当 retained identity 与
pathname identity 均未漂移时调用 §2 `worktree_remove_argv`；重新 no-follow 验证 clean root 与三份
backing paths absent，并以 `git worktree list --porcelain`（同一 absolute Git/prefix/env）验证不存在
指向该 clean root 的 worktree entry。三项证明均成功才为 ordinary launcher FAIL；任一 ownership 或
absence 证明失败即终态 `ROLLBACK_INCOMPLETE`。两种终态都禁止 ref/materialization retry、换路径、
collection 或训练。adapter 接管后的 candidate/ref/evidence rollback 仍只由 frozen adapter state machine
负责。

## 5. 审核边界与 verdict

本 annex 只补齐 post-approval launcher authority，不改变 v0.3 的 source/collection/publication 或
runtime authority；仍不授权任何真实 materialization、source/checkpoint I/O、collection/receipt/
publication/root audit、child、GPU、训练、评测、推理或 LIBERO4IN1。它随 replacement execution request
请求唯一 verdict：

```text
APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT
```

或 `REQUEST_CHANGES(file:line)`。
