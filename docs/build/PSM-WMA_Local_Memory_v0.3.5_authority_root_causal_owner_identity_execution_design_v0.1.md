# PSM-WMA v0.3.5 Authority-root Causal Owner Identity Execution Design v0.1

**日期**：2026-09-13
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-EXECUTION-DESIGN`

## 1. 前序结论与范围

`145f0d4.../93a89ba...` 的三方 static-witness closure 已确认：native `git worktree add` 不返回其
创建目录的 inode，因此“Git 返回后才对 pathname `bind_owned()`”不能成为 owner authority。现有
v0.8 launcher 因而故意在成功 add 后 `ROLLBACK_INCOMPLETE`，不接受或删除任何 CLEAN。该行为是
正确的 fail-close，不是 materialization authority。

本设计只定义下一步如何让成功路径拥有**mutation 前已建立的 directory-FD identity**。不实现、
不运行 launcher、不给真实项目路径创建 worktree/backing/index/candidate/ref/evidence，不读取 source
或 checkpoint，也不改 child、GPU、训练、评测、推理或 LIBERO4IN1。

## 2. 冻结选择：executor 先创建空 CLEAN，再让 Git 填充同一 inode

不再要求证明“Git 创建了哪个 inode”。executor 在任何 native Git mutation 前按以下顺序建立唯一
owner capability：

1. 对 authority parent 取得 `O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC` FD，并重验其 `(st_dev, st_ino)`；
   parent 是本次 executor 新建的 mode `0700` 私有目录，且其所有后续 child 操作均使用此 FD 的
   `dir_fd` 形式，不重新由全局 pathname 取得 parent authority。
2. 仅以 `mkdir(..., mode=0o700, dir_fd=parent_fd)` 创建名称固定的空 CLEAN；以
   `open(..., O_DIRECTORY|O_NOFOLLOW, dir_fd=parent_fd)` 立即取得 `clean_fd`，并以 `fstat` 与
   `stat(..., dir_fd=parent_fd, follow_symlinks=False)` 绑定同一 `(dev, ino)`。此时它是 executor
   自己创建并持有的空目录，不依赖 Git 的返回值。
3. 把 `parent_fd` 作为唯一继承 FD（固定 FD number 和 `pass_fds`），使 native Git 的 target 使用
   `/proc/self/fd/<parent_fd>/CLEAN`。当前项目 Git `2.34.1` 的 temporary fixture 已验证：预创建的
   空目录可接受 `git worktree add --detach <existing-empty-dir> HEAD`。实现必须再次在测试中覆盖该
   事实；若任何受支持 Git 拒绝它，直接 FAIL，不回退到 post-add pathname bind。
4. Git 返回后，必须同时重验 `clean_fd` 与 `stat(CLEAN, dir_fd=parent_fd)` identity 相等、CLEAN 仍为
   directory 且 parent FD identity 未漂移；随后才允许 `rev-parse/status/worktree-list`，且 Git cwd
   也必须通过 `/proc/self/fd/<parent_fd>/CLEAN`。任一不等、symlink、missing、Git nonzero 或 route
   drift 都是 `ROLLBACK_INCOMPLETE`，禁止 backing handoff、FD 3/4/5 或 `execve`。

这个选择的因果链是：`executor mkdir -> clean_fd -> Git only populates held inode -> revalidation`，而
不是从 native Git 的无身份返回值倒推所有权。

## 3. 清理与失败语义

- 只有仍由 `clean_fd`/`parent_fd` 双重验证的 CLEAN 才可走 native `git worktree remove --force`；remove
  target 同样经 `/proc/self/fd/<parent_fd>/CLEAN` 表达。之后以 `unlink/rmdir` 的 `dir_fd` 形式重验空
  parent。不得以全局 CLEAN pathname 删除。
- 任何 replacement、parent drift、Git status/list 不一致、关闭前不为空，或 cleanup native failure 都是
  `ROLLBACK_INCOMPLETE`。不得删除 foreign inode，不得把失败降格为普通 PASS/FAIL。
- 因 Git add 在既有 executor-owned CLEAN 内失败时，只有 `clean_fd` identity 未漂移且目录仍为空的
  情况可移除 executor 自己的空目录；否则保留现场并 fail-stop。
- `/proc/self/fd/<parent_fd>` 是 Linux-only execution ABI；平台无该 procfs 合同或 fixed inherited FD
  不可用时，在任何 Git/source I/O 前 FAIL。不得添加 pathname fallback。

## 4. 后续 CPU/static implementation 的最小验收矩阵

全部只使用 `TemporaryDirectory`、local Git repo 和 bare fixture，绝不调用 production `main()`：

| 情形 | 必须证明 |
|---|---|
| 预创建空 CLEAN + native add | Git 填充的 `clean_fd` 与 parent-entry `(dev,ino)` 相同；HEAD/formal/list 均匹配 |
| add 前 CLEAN symlink、非空或 mode 错 | Git/source/backing 前拒绝 |
| add 后 parent-entry replacement | `clean_fd` 与 entry 不等，`ROLLBACK_INCOMPLETE`，foreign 不删除 |
| add 中 Git nonzero | 仅仍为空且 identity 未漂移的 executor CLEAN 可移除；否则 fail-stop |
| cleanup 前/中 replacement | 无 force remove foreign，`ROLLBACK_INCOMPLETE` |
| inherited FD/proc target 篡改 | 在 Git 前拒绝；没有 cwd/pathname fallback |
| raw/config/route 已有反例 | 全部保留，不因 owner mechanism 弱化 |

必须额外验证实际 Git invocation 的 argv、`pass_fds`、`close_fds`、fixed environment 以及 parent/clean
FD 的 `FD_CLOEXEC` 状态。任何 test 只能触碰 fixture，不能创建项目 authority artifacts。

## 5. 明确禁止与下一步

本文件请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC
```

或 `REQUEST_CHANGES(file:line)`。只有三方对同一 root/child 批准后，才允许 root-only stdlib
temporary-fixture CPU/static implementation 与 tests。该批准仍不等于真实 materialization、source/
checkpoint I/O、collection/receipt/publication、child/runtime、GPU 或训练授权。
