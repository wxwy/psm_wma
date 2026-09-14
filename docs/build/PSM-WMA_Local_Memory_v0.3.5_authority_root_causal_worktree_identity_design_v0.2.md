# Authority-root causal worktree identity execution design v0.2

**日期**：2026-09-14
**状态**：docs-only；待三方审核
**Gate**：`G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`

## 1. 版本关系与唯一目标

本文件 supersede `...causal_worktree_identity_design_v0.1.md`。v0.1 第 2 节第 3 步将 native
Git target 表达为可变的 `<absolute-clean-root>`；该表达无法把 Git 的 target resolution 绑定到
launcher 已持有的 inode，故不得作为实现依据。

本版本只关闭该 Git-target 因果 authority 缺口：让 native Git 实际消费 inherited directory
capability 派生的 target，而不是 global `CLEAN` pathname。它不创建 execution request、不调用
production launcher、不读 source/checkpoint，也不授权 materialization、collection、receipt、
publication、child、GPU、训练、评测、推理或 LIBERO4IN1。

## 2. Frozen Git-target capability contract

1. launcher 以绝对且 `O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC` 打开的受控 parent directory FD 为
   `parent_fd`；在 mutation 前冻结 parent pathname 与 `(st_dev, st_ino, S_IFMT)`。
2. 只通过 `mkdirat(parent_fd, clean_name, 0700)` 创建 clean root；随即用
   `openat(parent_fd, clean_name, O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC)` 取得 `clean_fd`，冻结其
   `(st_dev, st_ino, S_IFMT)`，并且仅经 `clean_fd` 验证为空。任何 pre-existing、symlink、非目录
   或非空结果均为 pre-Git `FAIL`，不得 rename、重建、换名或重试。
3. Git child 的唯一 target authority 为固定 inherited `git_parent_fd=6`：launcher 在 spawn 前以
   `dup2(parent_fd, 6)` 固定它，验证 FD 6 的 parent identity，清除 FD 6 的 `FD_CLOEXEC`，并使用
   `close_fds=True, pass_fds=(6,)`。Git argv 中 worktree target 必须逐字为
   `/proc/self/fd/6/<clean_name>`；禁止 global absolute CLEAN、`cwd` 替代、shell、PATH、ambient
   index、remote alias、额外 FD 或 fallback target。`clean_fd` 不继承给 Git，FD 6 只在此 Git child
   lifetime 存在，不得与 frozen backing ABI `{3,4,5}` 或 final owner descriptor 发生碰撞。
4. 调用前必须验证 `/proc/self/fd/6/<clean_name>` 由 retained FD 6 的 namespace 指向已冻结
   `clean_fd`；procfs 缺失、FD number/CLOEXEC/identity 不符、`pass_fds` 不能精确满足，或 Git
   拒绝 pre-created empty directory，均在 source/backing/adapter 前 `FAIL`，绝不退回 global path。
5. Git 返回后，以 `fstat(clean_fd)`、`fstatat(parent_fd, clean_name, AT_SYMLINK_NOFOLLOW)` 与
   `fstat(6)` 三重复验 parent/entry/owner identity；然后所有 Git validation 的 cwd/target 仍使用
   `/proc/self/fd/6/<clean_name>`，或等价的 retained-FD relative operation。任何 drift、missing、
   symlink、metadata 不一致或 Git nonzero 都 fail-close：已可能 mutation 时分类为
   `ROLLBACK_INCOMPLETE`，此前分类为 `FAIL`。

因果链唯一为：`launcher mkdirat -> retained clean_fd -> inherited parent FD6 -> Git consumes
/proc/self/fd/6/clean_name -> triple revalidation`。global pathname 仅可作为人类日志或最终 absence
补充检查，永远不是 Git 或后续 consumer 的 authority。

## 3. Descendant lifetime、cleanup 与行政 metadata

- FD 6 的继承边界冻结为上述单一 Git child；spawn 后立即以 child argv、`close_fds`、`pass_fds`、
  FD6 CLOEXEC state 和 parent identity 记录/验证。Git 返回后关闭 FD6；`clean_fd` 与 `parent_fd`
  继续作为 owner/cleanup capability，直到所有 cleanup/absence proof 完成。
- Git administrative worktree metadata 必须在 Git 返回后经 retained owner capability 和 existing
  no-follow/raw-byte/route checks 验证；不得因为 `/proc/self/fd/6/...` 是短寿命路径而回退至 global
  CLEAN 重新取得 repository authority。后续需要 Git consumer 时必须另行冻结其 inherited-FD
  contract；本 Gate 不授权隐式继承或 ambient reopen。
- cleanup 仅当 `clean_fd`、`parent_fd` entry 与创建 identity 三方一致时才有资格执行；native
  `git worktree remove --force` 的 target 同样只能是 FD6-derived path（若 FD6 已关则不执行此 cleanup，
  并 `ROLLBACK_INCOMPLETE`），随后仅以 `dir_fd=parent_fd` 删除已证明为空的自有 entry。foreign
  replacement 不读、不写、不删；无法证明 ownership/absence 一律保留现场并 `ROLLBACK_INCOMPLETE`。

## 4. CPU/static implementation acceptance

实现只允许既有 authority-root launcher/payload root allowlist 及 direct stdlib
`TemporaryDirectory`/local Git fixture tests。除既有 v0.8 legacy-route negative witness 外，新增：

| 场景 | 必须证明 |
|---|---|
| normal precreated owner | real temporary `git worktree add` 的 argv target 是 `/proc/self/fd/6/<clean_name>`；Git 填充的 inode 与 retained `clean_fd`/parent entry 一致 |
| target-resolution race | 在 Git child 解析 target 前 rename/replace global parent 或 clean entry 为 foreign empty directory；Git 只能填充 retained owner inode，或在写 foreign inode 前失败；foreign inode 不被 read/write/delete |
| inheritance seam | `close_fds=True`、`pass_fds==(6,)`、FD6 identity/CLOEXEC 与 argv 精确匹配；没有 FD3/4/5/clean_fd 泄漏 |
| post-Git drift | entry/parent replacement、symlink、nonempty、metadata drift 一律 fail-close，不能 handoff/exec |
| cleanup | 仅 identity-proven owner 可清理；FD6 不可用或 foreign replacement 时 `ROLLBACK_INCOMPLETE` 且 foreign 保留 |

fixture 只能使用 temporary local/bare Git repository；禁止访问项目 origin、真实 source/checkpoint、
cache、authority artifact、GPU 与训练。closure 后仍必须对新的 exact implementation root/child pair
取得三方 `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT`，才可提出任何真实
materialization request。

## 5. 审核请求

请求：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_WORKTREE_IDENTITY_CPU_STATIC
```

批准范围仅为上述 root-only、temporary-fixture CPU/static implementation/tests；明确禁止真实
worktree/materialization、source/checkpoint/manifest/data/cache I/O、collection/receipt/publication、
child 改动、GPU/CUDA/torchrun、训练、评测、推理和 LIBERO4IN1。
