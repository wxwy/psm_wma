# PSM-WMA v0.3.5 Authority-root Causal Owner Identity Execution Design v0.3

**日期**：2026-09-13
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-EXECUTION-DESIGN`

## 1. 版本关系与严格边界

本文件 replacement v0.2（formal `de1d12f...`）的两项 HIGH。v0.1/v0.2 不得作为实现
依据；未由本文件显式 refreeze 的 source/raw/config/route、post-mutation fail-close、backing
内容 ABI 与禁止项继续生效。

只允许 docs-only 设计。不得调用 production `main()`，不得创建项目路径 worktree/backing/index/
candidate/ref/evidence，不读 source/checkpoint，不改 child、GPU、训练、评测、推理或 LIBERO4IN1。

`ROOT=/disk/rl/psm_wma` 与
`CLEAN=/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8`保持 executor-only
frozen absolute names；**任何 post-exec child argv 不得含该 absolute CLEAN pathname**。

## 2. 预 mutation descriptor reservation 与无碰撞 owner capability

在 `mkdir(CLEAN)`、native Git 或任何 source/mutation 前，executor 必须以 `fcntl(F_GETFD)` 对
`{3,4,5,6,7,8,9}` 逐个检查；每个都必须为 `EBADF`。任一个已占用、`F_GETFD` 非预期失败、
`dup2`/`fcntl`/`fstat` 失败，均为 pre-mutation `FAIL`，不得关闭外来 FD、不得猜测复用、不得
继续。这条 reservation 使已有 backing ABI `{3,4,5}`、Git FD6、root FD7、bootstrap FD8 与 owner
FD9 在 mutation 前全部可证明无别名。

能力及固定编号如下：

| capability | bind chronology / executor lifetime | child inheritance | purpose |
|---|---|---|---|
| `root_authority_fd` | 以 temporary source-open FD 打开 ROOT，`dup2(source,7)`、`fstat` identity 相等后关闭 source；FD7 保存至 child exit/cleanup | 不继承 | ROOT entry lookup/revalidation/CLEAN-only cleanup |
| `git_root_fd` | 仅每次 Git child 前 `dup2(7,6)`，fstat等价，Git return即关闭6 | 仅 Git `pass_fds=(6,)` | `/proc/self/fd/6/CLEAN` Git target |
| `clean_owner_fd` | `mkdir`后以 temporary `clean_open_fd` 打开 CLEAN，`dup2(clean_open_fd,9)`，fstat/FD7-entry三方同一 inode后关闭 source；FD9 保存至 child exit/cleanup | 不继承 | 所有 owner-relative backing/handoff/cleanup authority |
| `bootstrap_clean_fd` | final admission 时 `dup2(9,8)`，fstat等价 | 仅 bootstrap/adapter child | actual consumer root `/proc/self/fd/8` |

FD7、FD9在 executor 为 `FD_CLOEXEC`；FD6只在 Git child 清除 CLOEXEC；FD8仅 final child 清除
CLOEXEC。FD9 在填充 backing `{3,4,5}`、创建/关闭FD6、创建FD8期间保持未变。不得把普通
open 返回的 `clean_open_fd` 当 owner capability；它在 rebind 至9并完成 identity proof后立即关闭。
child final inherited set 精确为 `{3,4,5,8}`；FD6/7/9及临时 source FDs 均不在 child。

Git 后每一 backing operation、child admission、child退出cleanup都重验：`fstat(7)`是初始
ROOT，`fstat(9)==stat(CLEAN,dir_fd=7,follow_symlinks=False)`且 entry 是 non-symlink directory。
Git may have mutated 后任一不确定性均 `ROLLBACK_INCOMPLETE`；ROOT 永不清空/删除，只能对仍由
FD7/FD9双验证的 CLEAN entry cleanup。

## 3. 从 FD8 到实际 adapter 的完整 child argv

v0.2 仅 refreeze bootstrap root 不够。本版冻结 final child 由 `sys.orig_argv` 观察的 CLEAN-derived
字段为以下精确 bytes（`FD8_ROOT=/proc/self/fd/8`）：

```text
--cwd                     /proc/self/fd/8
--index                   /proc/self/fd/8/.authority-root.index
--bootstrap-project-root  /proc/self/fd/8
--bootstrap-owner-root-fd 8
```

旧 `/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8` 值只能留在 executor Git phase，
不得出现在 final argv、bootstrap contract、adapter parser input、Evidence observed argv 或任何
post-exec fallback。完整 final argv、`-I -S -B -c` payload raw bytes/SHA、argv digest与FD mapping
须同一次实现冻结；未获该 implementation SHA 的三方批准前不得执行。

现有 adapter 不是被假定可直接兼容的黑盒。下一实现范围必须更新 root-only
`materialize_immutable_source_authority_root.py` 与其 direct temporary-fixture tests，使：

1. parser 增加必需 `--bootstrap-owner-root-fd`；
2. `_bootstrap_identity_from_runtime()` 核验 FD8 为 directory、将上述三个 raw argv 字段与 FD8
派生 canonical strings逐字节比较，且**不以 `Path.resolve()` 把 procfd 输入重新解释为全局
pathname**；
3. `NativeAuthorityGit` 仅接收 FD8-derived `cwd/index`；Git/config/module identity与Evidence
observed argv均来自同一 frozen procfd argv；
4. 任一字段缺失、不是 exact procfd derivation、FD8不匹配、procfs不可用或 adapter 尝试全局
CLEAN fallback，必须在 foreign module/worktree/index/Git consumption 前 fail-close。

这项 root adapter source refreeze 必须在未来 implementation commit 中以 formal-tree module raw
SHA/blob、bootstrap payload SHA与argv digest共同证明；禁止由运行时改写 `sys.orig_argv` 或未记录
的 argv translation 规避合同。

## 4. cleanup 与跨 exec 线性化

supervisor executor 保留 FD7/FD9，final child仅凭FD8消费原 CLEAN inode。最后 executor
pathname check后若攻击者替换 ROOT/CLEAN entry，child仍只能通过FD8使用原 inode，或在消费前
fail-close；supervisor待child exit后以FD7/FD9清理。foreign replacement绝不删除。

对 cleanup 的 Git target如需再次调用 Git，只临时 `dup2(7,6)`并按 Git-only contract传递；
不从 global CLEAN pathname重新取得 authority。child success/exit 后无法以双FD证明同一entry、
任何 close/recheck/Git remove不确定性都是`ROLLBACK_INCOMPLETE`。

## 5. 强制 temporary CPU/static witness

只用 `TemporaryDirectory`、local/bare Git repo、temporary sentinel modules；不跑 production
`main()`，不创建项目 authority artifacts。除原有 raw/config/route/cleanup 反例外，必须证明：

| witness | required assertion |
|---|---|
| low-FD baseline | 从仅0/1/2打开的子进程，root/clean source FD 可低号，但最终 retained owners恰为7/9；3/4/5/6/8操作不破坏FD9 |
| hostile preoccupation | 任一3--9占用在mkdir/Git前FAIL，外来FD不关闭/不修改 |
| rebind proof | source→7、clean source→9、7/9/entry dev-inode一致；所有source FD已关闭；CLOEXEC与child set精确 |
| argv/adapter | final raw argv只含FD8-derived cwd/index/bootstrap root及owner FD8；adapter拒绝旧absolute CLEAN、missing/mismatched FD8、resolve/global fallback |
| end-to-end seam | final check后替换 global CLEAN，真实 isolated bootstrap→adapter temporary seam只能读原 sentinel/cwd/index或消费前fail-close；foreign inode与module/index不被消费/删除 |
| post mutation failure | FD7/9/8或Git path不确定时为`ROLLBACK_INCOMPLETE`；foreign entry与现场保留 |

## 6. 唯一请求

请求：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC
```

或 `REQUEST_CHANGES(file:line)`。仅当 ChatGPT、MM、Kimi 对同一新root/child批准后，才允许
上述 root-only stdlib temporary-fixture adapter/launcher/tests 实现。仍不授权 production/main、
真实materialization/source/checkpoint I/O、collection/receipt/publication、child、GPU、训练、
评测、推理或 LIBERO4IN1。
