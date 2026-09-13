# PSM-WMA v0.3.5 Authority-root Causal Owner Identity Execution Design v0.2

**日期**：2026-09-13
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-EXECUTION-DESIGN`

## 1. 版本关系、范围与不可变边界

本文件是对 v0.1（formal root `64b706b7b97451fd90cb6e9292100e512952f28a`）两项
`REQUEST_CHANGES` 的 replacement。v0.1 不再作为实现依据；除本文件显式 refreeze 的
owner/exec ABI 外，已冻结的 source identity、raw/config/route、post-mutation fail-close 与
backing `{3,4,5}` 合同继续生效。

本文件只定义 root docs-only 机制。它不实现、不调用 production `main()`，不创建项目路径
worktree/backing/index/candidate/ref/evidence，不读 source/checkpoint，也不改 child、GPU、训练、
评测、推理或 LIBERO4IN1。

冻结的目录名保持不变：

```text
ROOT  = /disk/rl/psm_wma
CLEAN = /disk/rl/psm_wma/.authority-root-materialization-9dd2fb8
```

既有 Git `--cwd`、`--index` 与其它 pre-exec absolute field 仅用于 executor 内的 frozen
Git transaction；它们不再允许成为 post-exec bootstrap 的 project-root source。

## 2. 三种 capability、固定编号与生命周期

实现不得再使用未定义的 `parent_fd`。下列名称、编号、继承方向与关闭点都是本设计的合同：

| capability | executor FD / lifetime | child inheritance | 唯一用途 |
|---|---|---|---|
| `root_authority_fd` | FD 7；executor 从 pre-mutation 到 child 退出及 cleanup 持有 | 不继承给 Git 或 bootstrap | `ROOT` 下 CLEAN entry 的 `dir_fd` lookup、identity revalidation 与 cleanup |
| `git_root_fd` | FD 6；仅 native Git child lifetime 的 duplicate | 仅 `pass_fds=(6,)` 给 Git | Git target `/proc/self/fd/6/.authority-root-materialization-9dd2fb8` |
| `clean_owner_fd` | executor 普通 FD，从 mkdir 到 child退出/cleanup持有 | 不直接继承 | executor 对 held CLEAN inode 的 owner-relative backing/handoff/cleanup |
| `bootstrap_clean_fd` | FD 8；从 exec admission 到 bootstrap consumer 结束 | 仅最终 bootstrap child 继承 | immutable consumer root `/proc/self/fd/8` |

`root_authority_fd` 以 `open(ROOT, O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC)` 获得，随后重绑到
FD 7。重绑后必须以 `fstat(7)` 与 `stat(ROOT, follow_symlinks=False)` 比较 `(st_dev,st_ino)`；
FD 7 在 executor 中保持 `FD_CLOEXEC`，不得靠 global pathname 重建。`git_root_fd` 必须由
FD 7 以 `dup2(7, 6)` 创建，并在 Git 之前证明 `fstat(6)==fstat(7)`；仅 FD 6 清除
`FD_CLOEXEC`，Git 以 `close_fds=True, pass_fds=(6,)` 接收它。Git 返回后立即关闭 executor
侧 FD 6；FD 7 始终不传递给 Git。

executor 以 `mkdir(name, 0o700, dir_fd=7)` 创建唯一空 CLEAN，以
`open(name, O_DIRECTORY|O_NOFOLLOW, dir_fd=7)` 取得 `clean_owner_fd`，并要求三者
`fstat(clean_owner_fd)`、`stat(name, dir_fd=7, follow_symlinks=False)`、创建时观察同一
`(dev,ino)`。Git 只允许填充已持有 inode；native Git 成功但任一身份不等一律
`ROLLBACK_INCOMPLETE`。

## 3. Git、handoff 与 cleanup 的因果闭包

Git target 固定为`/proc/self/fd/6/.authority-root-materialization-9dd2fb8`。仅 fixture 可验证
预创建空目录接受 `git worktree add --detach <target> HEAD`；任何支持环境拒绝时在 source
I/O 前 FAIL，不得退回 post-add pathname bind。

Git 后及每一次 owner-relative backing create/open/readback 前，executor 同时重验：FD 7 仍是
初始 ROOT、`stat(CLEAN, dir_fd=7)` 与 `fstat(clean_owner_fd)` 相等、entry 为非 symlink directory。
所有 backing 操作只可相对 `clean_owner_fd`；不得以 CLEAN absolute pathname 或 ROOT pathname
重开。FD duplication、Git invocation/inheritance、任何 identity recheck 的失败在 Git mutation
前为 FAIL，在 Git 已可能 mutation 后为 `ROLLBACK_INCOMPLETE`。

cleanup 从不“清空”或删除 ROOT。supervisor executor 在 child exit 后仍持 FD 7 与
`clean_owner_fd`：仅当二者与 `stat(CLEAN, dir_fd=7)` 仍是同一 inode，才可将 native
`git worktree remove --force` target 表达为`/proc/self/fd/6/CLEAN`（为此临时由 FD 7 重建
Git-only FD 6，重复上述 fstat/`pass_fds` 合同），随后仅删除该 owned CLEAN entry。若 entry
漂移、foreign、missing-with-uncertain-state、Git nonzero 或 close failure，保留现场并
`ROLLBACK_INCOMPLETE`；绝不删除 foreign inode。

## 4. 跨 exec/bootstrap 的 owner continuity（替代 v0.1 的 pre-exec 检查即充分说法）

最终 consumer 不能再从可替换的 absolute CLEAN pathname 解析项目根。executor 在最后一次
FD 7/`clean_owner_fd` 双重 revalidation 后，执行：

1. `dup2(clean_owner_fd, 8)`，清除 FD 8 的 `FD_CLOEXEC`；以 `fstat(8)==fstat(clean_owner_fd)`
   证明同一 inode；
2. final bootstrap child 的 inherited descriptor set **精确 refreeze 为 `{3,4,5,8}`**。FD 7、
   普通 `clean_owner_fd` 与 Git-only FD 6 不进入 child；supervisor 保留 FD 7 与
   `clean_owner_fd` 直至 child exit 和 cleanup；
3. refreeze bootstrap contract：`BOOTSTRAP_OWNER_ROOT_FD=8` 是唯一 root authority。bootstrap 从
   `sys.orig_argv` 验证该字段、FD 8 是 directory/non-symlink regular inherited FD、以及完整
   `-I -S -B -c ... --` framing，随后仅把`/proc/self/fd/8`作为 project root 用于 `.git`、
   formal modules、`sys.path`和`runpy`解析；禁止读取任何 absolute CLEAN root 参数，禁止
   pathname fallback；
4. 现有 raw bootstrap payload bytes/SHA、argv digest、final FD-set proof 与任何
   `--bootstrap-project-root=/disk/.../CLEAN` 字段因此被本节显式 supersede。后续实现必须把
   新 payload 的 exact bytes/SHA、完整 argv、FD mapping 及 verifier assertion 一并冻结；在
   未获得新 SHA 三方批准前不能执行。

因此在最后 executor pathname check 后，攻击者即使把 ROOT 下的 CLEAN entry 换为 foreign
inode，bootstrap consumer 仍只能使用 inherited FD 8 所指原 inode，或在 FD/proc contract失败时
于 module/code consumption 前 fail-close。supervisor 的 FD 7/`clean_owner_fd` 使后续 cleanup
仍具因果 owner authority；child 从不承担全局路径 cleanup。

## 5. 后续 temporary CPU/static implementation 的强制 witness

全部使用 `TemporaryDirectory`、local Git/bare fixture 和临时 sentinel module；禁止 project
authority artifacts、production `main()`、真实 source/checkpoint I/O。除既有 raw/config/route
反例外，必须新增：

| 情形 | 必须证明 |
|---|---|
| FD 7/6 construction | exact `dup2` direction、dev/inode equality、CLOEXEC、`pass_fds=(6,)`、`close_fds=True`，且 Git child无FD7 |
| CLEAN identity | precreated empty CLEAN 被Git填充后，FD7 entry与`clean_owner_fd`相同；stale name、symlink、nonempty、mode错误均在Git前拒绝 |
| root cleanup | ROOT 从不被删除/清空；只有仍同一 held CLEAN entry可remove；foreign replacement保持不动 |
| final seam | 在最后 executor pathname recheck后替换 global CLEAN entry；exec bootstrap仅从`/proc/self/fd/8`读原 sentinel module，或在消费前fail-close，绝不读取foreign sentinel |
| final ABI | child仅有`{3,4,5,8}`，FD8 identity/owner-root contract缺失、篡改或procfd不可用时在`sys.path/runpy`前拒绝 |
| lifecycle failures | FD duplicate/inheritance/recheck/close在Git前为FAIL；Git后为`ROLLBACK_INCOMPLETE`，foreign entry与证据现场保留 |

## 6. 唯一请求与禁止项

本文件请求：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC
```

或 `REQUEST_CHANGES(file:line)`。只有 ChatGPT、MM、Kimi 对同一新 root/child 三方批准后，才可
实现 root-only stdlib temporary-fixture CPU/static mechanism/tests。该批准不授权真实
materialization、source/checkpoint I/O、collection/receipt/publication、child/runtime、GPU、训练、
评测、推理或 LIBERO4IN1。
