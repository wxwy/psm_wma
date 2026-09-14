# Authority-root causal worktree identity execution design v0.3

**日期**：2026-09-14
**状态**：docs-only；待三方审核
**Gate**：`G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`

## 1. Supersession 与单一修复目标

本文件 supersede `...causal_worktree_identity_design_v0.1.md` 与 v0.2。v0.2 的 FD6 是
`parent_fd` duplicate，故 `/proc/self/fd/6/<clean_name>` 在 Git consume 时仍重新 lookup mutable
leaf entry；该 route 不得实现。本版只修复这一 leaf-authority 缺口，继续禁止 execution request、
真实 Git/worktree/materialization、source/checkpoint/manifest/data/cache I/O、collection、child、GPU
和训练。

## 2. 唯一 Git leaf-capability contract

1. retained parent authority 是 `parent_fd`，且使用既有 frozen final owner mapping：parent owner
   FD7、clean owner FD9。mutation 前冻结 parent 与 clean entry 的 `(st_dev, st_ino, S_IFMT)`；只以
   `mkdirat(parent_fd, clean_name, 0700)` 创建，并立即以 `openat(..., O_DIRECTORY|O_NOFOLLOW)` 取得
   `clean_fd`。任何 pre-existing/非空/symlink/非目录均为 pre-Git `FAIL`，没有 retry、rename 或换名。
2. Git target 是 leaf capability：仅为 Git child lifetime 以 `dup2(clean_fd, 6)` 生成
   `git_target_fd=6`，验证 `fstat(6)==fstat(clean_fd)`，清除 FD6 `FD_CLOEXEC`。parent FD7 与 clean
   owner FD9 不继承；FD6 不与 backing `{3,4,5}`、FD7、FD8 或 FD9 冲突。
3. native Git 的唯一 worktree target argv 逐字为 `/proc/self/fd/6`，不得附接 `clean_name`，不得
   传 global CLEAN/parent pathname、`cwd` 代替、shell、PATH、ambient index、remote alias 或 fallback。
   spawn 必须精确为 `close_fds=True, pass_fds=(6,)`；任何额外 inherited FD、FD number/CLOEXEC/
   identity 不符、procfs unavailable 或 Git 拒绝既有 empty leaf，均在 source/backing/adapter 前
   `FAIL`，绝不降级到 parent-derived 或 global pathname target。
4. 直接 leaf FD 的因果语义是：Git target resolution 只能 dereference retained inode A。若同一
   retained parent 内 `clean_name` 被 remove/rename/replaced 成 foreign B，`/proc/self/fd/6` 仍指向
   A（或 Git 在写 B 之前失败），绝不能被 B 重定向。global parent rename/replacement 同样不改变
   FD6 指向。该语义只以第 4 节的 actual temporary-Git witness 验证，未验证的平台 fail-close。
5. Git 返回前后都 `fstat(6)` 与 `fstat(clean_fd)`；返回后还以 `fstatat(parent_fd, clean_name,
   AT_SYMLINK_NOFOLLOW)` 判断 namespace entry 是否仍为 owner A。A 与 entry 不一致、Git nonzero、
   `.git`/HEAD/status/metadata route 不可仅经 retained capability 证明，均 fail-close；已可能 Git
   mutation 时为 `ROLLBACK_INCOMPLETE`，此前为 `FAIL`。后续 validation 不得使用 global CLEAN 重获
   authority。

## 3. FD lifetime、administrative metadata 与 cleanup

- 顺序冻结为：`clean_fd/FD9 open -> dup2 to FD6 -> pre-spawn proof -> Git returns -> post-Git
  fstat(6)/clean_fd/parent-entry triple proof -> close FD6`。FD6 关闭后，一切 owner operation 仅经
  retained FD7/FD9 相对路径进行；任何再次 Git consumer 必须另起显式 inherited leaf-FD contract，
  不能复用 closed procfd string 或 reopen global path。
- worktree administrative metadata 只能经 retained owner capability 及既有 no-follow/raw-byte/route
  checks验证；其验证不得把 global CLEAN、ephemeral procfd pathname 或 Git canonicalized path变为
  clean-root authority。若 Git 不支持此 metadata validation，route fail-close。
- cleanup 只在 FD7/FD9/parent entry 三方 identity 仍为创建 owner A 时允许。若需要 native Git remove，
  必须在 cleanup Git child 前重新把仍保有的 `clean_fd` duplicate 至 FD6、重新执行所有 FD6 identity/
  `close_fds/pass_fds` proof，并以 `/proc/self/fd/6` 为唯一 remove target；FD6 随后关闭。若 entry
  replacement、FD unavailable、metadata/absence proof 失败，`ROLLBACK_INCOMPLETE`，foreign B 不读、不写、
  不删。

## 4. Required CPU/static witness matrix

实现仅可改既有 authority-root launcher/payload root allowlist 和 direct stdlib
`TemporaryDirectory`/local-bare-Git tests。必须通过实际 temporary `git worktree add` 验证：

| seam | 断言 |
|---|---|
| normal leaf target | argv target 精确 `/proc/self/fd/6`；Git 填充 inode 等于 retained A（FD6/FD9），且 parent entry 仍为 A |
| same-parent leaf replacement | Git child resolve target 前，将 `parent_fd/clean_name` A 替换为 foreign empty B；Git 仅填充 A，或在写 B 前 fail；B 不被读取、写入或 cleanup 删除 |
| global parent replacement | replace/rename global parent path 后 target 仍只消费 A，foreign parent/leaf 不被写 |
| inheritance | `close_fds=True`、`pass_fds==(6,)`、FD6 identity/CLOEXEC/argv 精确；FD3/4/5/7/8/9 不泄漏给 Git child |
| post-Git / cleanup | entry/parent drift、symlink、metadata drift fail-close；cleanup 只删 identity-proven A，B 必保留；FD6 closure 后无 procfd/global fallback |

保留 v0.8 Git-self-created-root 的 legacy negative witness。fixture 不得访问项目 origin、真实
source/checkpoint/cache/authority artifact、GPU 或训练。实际 Git 不能安全接受 leaf procfd target 时，
该 route 必须关闭，不能改回 v0.2 parent+name 或任何 global target。

## 5. 审核请求与禁止范围

请求最终 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_WORKTREE_IDENTITY_CPU_STATIC
```

批准仅允许上述 root-only temporary-fixture CPU/static implementation/tests。明确禁止真实
worktree/materialization、source/checkpoint/manifest/data/cache I/O、collection/receipt/publication、
child 改动、GPU/CUDA/torchrun、训练、评测、推理和 LIBERO4IN1。
