# Authority-root causal worktree identity execution design v0.1

**日期**：2026-09-14
**状态**：docs-only；待三方审核
**Gate**：`G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`

## 1. 问题与目标

v0.8 的 native-Git witness 已证明：`git worktree add` 若自行创建 clean-root，调用方无法从
Git 获得该目录的创建 identity；任何事后 pathname bind 都可能接纳替换目录。因此 v0.8 成功路径
必须 fail-close，不能作为真实 authority materialization 的 launcher。

本设计只恢复该一个缺口：将 clean-root 在 native Git 调用前作为 launcher 自有对象创建并保留
descriptor identity，使 Git 仅能填充已绑定的空目录。它不创建 execution request、不执行 Git、
不读取 source/checkpoint、也不授权 collection、receipt、publication、child、GPU 或训练。

## 2. 唯一 owner-continuity 协议

1. launcher 以绝对、no-follow 打开的受控 parent directory FD 为 capability；parent pathname、
   `(st_dev, st_ino, S_IFMT)` 在任何 mutation 前冻结。
2. 使用 `mkdirat(parent_fd, clean_name, 0700)` 创建唯一空 clean root；立刻以
   `openat(parent_fd, clean_name, O_DIRECTORY|O_NOFOLLOW)` 取得 `clean_fd`，并记录其
   `(st_dev, st_ino, S_IFMT)`。随后以该 retained FD 验证目录为空。
3. `git worktree add --detach <absolute-clean-root> <formal-parent>` 只可消费这一已存在空目录。
   Git invocation 仍逐字继承 v0.8 的 absolute executable、prefix、cwd 与 sanitized environment；
   不得传 PATH、shell、ambient index、remote alias 或新增 argv。
4. Git 返回后，先相对 retained `parent_fd` 以 `fstatat(..., AT_SYMLINK_NOFOLLOW)` 读取
   `clean_name`，再 `fstat(clean_fd)`；两者必须和创建时的 identity/type 精确相等。然后仅经
   retained `clean_fd` 验证 `HEAD==formal-parent`、clean status 与受限 worktree metadata。
5. 每一后续 backing/index/evidence 操作均只可相对 retained clean/parent FD 完成；其 pathname
   复核只是对 capability identity 的补充，不能替代 retained FD。

任何 `ENOENT`、symlink、非目录、identity mismatch、非空预存在目录、Git 拒绝已有目录、
worktree 元数据不一致或 parent drift 都是 pre-adapter FAIL；不得退回 pathname、重新创建目录、
换路径或重试。

## 3. Cleanup ownership

只有创建时 identity、retained `clean_fd`、以及 `parent_fd` 相互一致时，launcher 才拥有 cleanup
资格。普通失败时关闭 FD 后，只可通过 retained parent capability 删除已经证明为空的自有目录并使用
冻结 Git remove 流程清理 worktree metadata；清理后必须以 parent-FD 与 global pathname 双重证明
clean root 不存在。任一 owner/absence 证明失败均为 `ROLLBACK_INCOMPLETE`，保留现场且不得继续。

adapter 接管后 candidate/ref/evidence rollback 仍归既有 adapter state machine；本设计不改变其
CAS、authority tuple 或 source-input 语义。

## 4. 后续 CPU/static implementation acceptance

只允许在 authority-root launcher/payload 的既有 root allowlist 及其 direct stdlib temporary-Git
tests中实现。必须覆盖：

- 预创建空目录后 Git 正常填充时 parent/child FD identity 恒等；
- Git 返回后 parent rename/replacement、clean-root replacement、symlink、非空目录和 metadata drift
  全部 fail-close；
- cleanup 只能删除 identity-proven自有目录，foreign replacement 永不删除；
- 原 v0.8 "Git 自建目录无因果 identity" witness 保持为拒绝 legacy route 的负例；
- 不访问项目 origin、真实 source/checkpoint、cache 或 GPU；fixtures 仅 TemporaryDirectory/local Git。

实现 closure 后才可生成完整 one-shot materialization request，且仍须对 exact request/child pair
取得三方 `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT`；该批准前不得
执行任何真实 materialization。

## 5. 审核请求与禁止范围

请求最终 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_WORKTREE_IDENTITY_CPU_STATIC
```

批准仅允许既有 launcher/payload root 文件及其 direct temporary-fixture CPU/static tests 的最小实现。
明确禁止真实 worktree/materialization、source/checkpoint/manifest/data/cache I/O、collection/receipt/
publication、child 改动、GPU/CUDA/torchrun、训练、评测、推理和 LIBERO4IN1。
