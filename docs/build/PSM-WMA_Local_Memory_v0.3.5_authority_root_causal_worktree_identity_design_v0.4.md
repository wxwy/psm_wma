# Authority-root causal worktree identity execution design v0.4

**日期**：2026-09-14
**状态**：docs-only；待三方审核
**Gate**：`G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`

## 1. Narrow v0.3 replacement

本文件只 supersede v0.3 中 Git target operand 的精确 spelling：从 `/proc/self/fd/6` 改为
`/proc/self/fd/6/.`。其它 leaf-FD authority、FD7/FD9 owner、FD6 only-child inheritance、无 global
fallback、triple identity proof 与禁止范围继续生效。

v0.3 的 leaf FD 已消除 `clean_name` lookup；但 direct temporary-Git probe 表明不带 `/.` 的 operand
不能可靠保留 Git administrative worktree registration/cleanup 语义。探针使用 `mktemp` 临时 local Git
repository，预创建 clean A、以 FD6 打开 A，执行 `git worktree add --detach /proc/self/fd/6/. HEAD`，
随后 `worktree list --porcelain` 注册真实 clean pathname，`worktree remove --force <clean>` exit 0。
该 probe 不是生产执行、不是 materialization authority，只是决定 exact target spelling 的 CPU fixture
事实。

## 2. Frozen target and cleanup contract

1. launcher 只通过 `mkdirat(parent_fd, clean_name,0700)` 创建 A，并保有 `clean_fd`；Git child 前只将
   `clean_fd` duplicate 到 fixed FD6，验证 identity、清 FD6 CLOEXEC，并精确使用
   `close_fds=True, pass_fds=(6,)`。
2. `git worktree add --detach` 的唯一 target argv 是 `/proc/self/fd/6/.`。尾部 `/.` 是 leaf capability
   内部的 current-directory component，不附接、解析或重查 `clean_name`；禁止 `/proc/self/fd/6/<name>`、
   global CLEAN/parent pathname、cwd substitute、PATH/shell/ambient index/remote alias及 fallback。
3. clean entry 被同一 retained parent 内 foreign B 替换时，该 child target 仍从 held leaf A 起始；全局
   parent replacement也不能重定向 FD6。Git不能安全接受该 spelling、procfs/FD proof不足或 metadata
   不能验证时必须 `FAIL`/`ROLLBACK_INCOMPLETE`，不得改回 v0.2/v0.3 spelling或 global route。
4. Git返回后仍要求 FD6/clean_fd/parent-entry triple identity；entry drift不得 handoff。正常 cleanup 仅在
   identity-proven A 时使用 frozen native `git worktree remove --force <clean>` administrative spelling，
   且 remove 前后再以 retained FDs验证 A；foreign B 永不读写删除。若 registration does not resolve to
   A 或 cleanup authority不可证明，`ROLLBACK_INCOMPLETE`。

## 3. Required temporary native witnesses

- exact add argv is `/proc/self/fd/6/.`, `pass_fds==(6,)`, `close_fds=True`，无 FD3/4/5/7/8/9 leakage；
- `worktree list --porcelain` reports canonical clean A and native remove `<clean>` succeeds only while the
  retained parent entry remains A;
- before target resolution replace same-parent `clean_name` A with B: Git fills A or fails before B write;
  B is never read/written/deleted, and any entry drift closes as `ROLLBACK_INCOMPLETE`;
- global parent replacement、post-Git drift、symlink/nonempty/metadata drift、legacy v0.8 route remain
  fail-closed negative witnesses.

## 4. Request

请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_WORKTREE_IDENTITY_CPU_STATIC`，仅覆盖
root-only launcher/payload 和 temporary-fixture CPU/static tests；仍禁止真实 worktree/materialization、
source/checkpoint/manifest/data/cache I/O、collection/receipt/publication、child、GPU、训练、评测、推理和
LIBERO4IN1。
