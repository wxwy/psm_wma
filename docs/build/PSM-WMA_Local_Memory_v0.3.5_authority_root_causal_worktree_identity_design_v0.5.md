# Authority-root causal worktree identity execution design v0.5

**日期**：2026-09-14
**状态**：docs-only；待三方审核
**Gate**：`G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`

## 1. Supersession 与唯一整改目标

本文件 supersede v0.4 的 §2.4 cleanup contract；v0.4 的 add target
`/proc/self/fd/6/.`、leaf-FD authority、FD7/FD9 owner、FD6 only-child inheritance、
`close_fds=True, pass_fds=(6,)`、triple identity proof 与全部禁止范围原样继续生效。

v0.4 的 native cleanup operand `<clean>` 是 mutable global namespace，不能作为 destructive
Git authority。2026-09-14 的隔离 temporary local-Git fixture 进一步证明：在 Git 2.34.1，
`git worktree remove --force /proc/self/fd/6/.` 返回 128（`fatal: ... is not a working tree`）。
因此不存在已实证的 native-Git leaf-capability remove route；本版明确禁止 global fallback，而不是
把兼容性问题静默换成 foreign-B mutation 风险。

该 fixture 仅在 `/tmp/psm-wma-leaf-cleanup.*` 的新建 local repository 中运行，不访问项目仓、
origin、source/checkpoint/manifest/data/cache、authority artifact、child、GPU 或训练；它只决定
fail-closed cleanup 语义，不能构成 materialization authority。

## 2. Frozen add contract（不变）

1. launcher 只通过 `mkdirat(parent_fd, clean_name, 0700)` 创建 owner A，随即以
   `openat(..., O_DIRECTORY|O_NOFOLLOW)` 保有 `clean_fd`；所有初始/后续 owner proof 都使用
   retained FD、`fstat` 与 `fstatat(parent_fd, clean_name, AT_SYMLINK_NOFOLLOW)`，不得通过 global
   CLEAN 重获 authority。
2. `git worktree add --detach` 的唯一 target argv 逐字为 `/proc/self/fd/6/.`：仅在 Git child
   lifetime 将 `clean_fd` dup 到 FD6，验证 FD identity、清 CLOEXEC，精确
   `close_fds=True, pass_fds=(6,)`。不得附接 `clean_name`，不得使用 global CLEAN/parent pathname、
   cwd substitute、shell、PATH、ambient index/remote alias 或 fallback。
3. Git 返回后仍须通过 FD6、`clean_fd`、parent entry 三重 identity 验证 A；任何 entry/parent/
   metadata drift、Git nonzero、非空/symlink 或 metadata route 不可仅经 retained capability 验证，
   均不得 handoff。

## 3. Cleanup is non-destructive fail-close

1. 本 Gate 中的 launcher `cleanup` 不是 normal administrative deletion mechanism。只要 native
   `worktree add` 已被调用，任何后续 fail path 都不得执行 `git worktree remove`，不得执行
   `rmtree`/`unlink`/`rename`，不得以 `<clean>`、`CLEAN`、parent+name、canonical registration path、
   cwd 或 procfd string 作为 delete target。
2. cleanup 仅可重新验证 retained FD7/FD9/parent-entry identity 并关闭其自身可关闭的 descriptors；
   无论 A 仍可证明还是 entry 已变为 foreign B，结果统一为 `ROLLBACK_INCOMPLETE`。A、Git
   administrative metadata 与 B（如存在）全部保留，不能为“收尾干净”而作任何 namespace mutation。
3. 同一 retained parent 内 A 被 B 替换，或 global parent 被替换时，cleanup 在最后一次 owner proof
   后也绝不启动 native Git consumer；因此 B 不读、不写、不删。post-Git triple proof 不通过时同样
   fail-close，不能以“检测到后再清理”补救。
4. 未来若需要清理残留，只能由单独的 recovery-design Gate 冻结一个经 native fixture 证明、且在
   target resolution 到 mutation 全程保持 A authority 的机制；该 Gate 不在本申请范围。本版不授权
   recovery、真实 worktree/materialization 或任何项目路径 mutation。

## 4. Required temporary CPU/static witness matrix

实现只可改既有 authority-root launcher/payload root allowlist 和 direct stdlib
`TemporaryDirectory`/local-Git tests；不得访问项目 origin 或真实 source/data。除 v0.4 已有 add
witness 外，必须新增：

| seam | 断言 |
|---|---|
| unsupported leaf native remove | retained FD6 A 的 `git worktree remove --force /proc/self/fd/6/.` 若被 native Git 拒绝，返回受控 fail-close；不得改为 `<clean>` |
| cleanup-resolution race | 在最后一次 cleanup owner proof 后把 same-parent A 替换为 foreign B；cleanup 不启动 Git remove 或其他 namespace mutation，返回 `ROLLBACK_INCOMPLETE`，B marker 保留 |
| normal post-add failure | A 与 worktree metadata 均保留，并返回 `ROLLBACK_INCOMPLETE`；不得以全局路径 cleanup |
| capability hygiene | cleanup 不继承 FD6 给 Git child（因为不 spawn remove），FD6 close 后无 procfd/global fallback；FD7/FD9 proof 不泄漏 |

保留 v0.4 的 add argv、same-parent add replacement、global parent replacement、post-Git drift、
symlink/nonempty/metadata drift 与 v0.8 legacy negative witnesses。fixture 只能证明 fail-close；
不得把残留存在误报为 successful cleanup。

## 5. Request

请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_WORKTREE_IDENTITY_CPU_STATIC`，
仅覆盖 root-only launcher/payload 和 temporary-fixture CPU/static tests。明确禁止真实
worktree/materialization、source/checkpoint/manifest/data/cache I/O、collection/receipt/publication、
child 改动、GPU/CUDA/torchrun、训练、评测、推理和 LIBERO4IN1。
