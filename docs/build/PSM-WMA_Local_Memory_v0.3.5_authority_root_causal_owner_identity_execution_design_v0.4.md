# PSM-WMA v0.3.5 Authority-root Causal Owner Identity Execution Design v0.4

**日期**：2026-09-13
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-EXECUTION-DESIGN`

## 1. 版本关系与边界

本文件 replacement v0.3（formal `781824f...`）中仍阻断的两项 authority HIGH。v0.1--v0.3
不得作为实现依据；v0.3 已冻结的 pre-mutation FD3--9 reservation、FD7/9 owner lifecycle、
executor-only `ROOT`/`CLEAN` absolute names、backing `{3,4,5}` 内容 ABI、raw/config/route
authority、post-mutation fail-close 与禁止项，除本文件显式 refreeze 外全部继续生效。

只允许 docs-only。不得调用 production `main()`；不得创建项目 authority worktree/backing/index/
candidate/ref/evidence；不得读 source/checkpoint；不得改 child、GPU、训练、评测、推理或
LIBERO4IN1。未来获批实现也仅可为 root-only stdlib temporary-fixture CPU/static launcher/
adapter/tests。

`ROOT=/disk/rl/psm_wma` 与 executor-only frozen absolute `CLEAN` 只允许 executor 的 native Git
phase 使用。任何 post-exec argv、bootstrap、adapter、Git subprocess、Evidence observed argv 或
fallback 都不得出现 absolute CLEAN pathname。

## 2. 不变的 owner capability 与 final argv

final executor retained owners 仍严格为 `root_authority_fd=7` 与 `clean_owner_fd=9`。每个 mutation
前 FD3--9 必须全为 `EBADF`；temporary source-open 后必须 `dup2` 到固定 FD、`fstat` identity proof
再关闭 source。FD7/FD9 在 executor 为 `FD_CLOEXEC`，FD6仅 Git child lifetime，FD8仅 final
bootstrap/adapter及本文件第3节指定的 descendant lifetime。所有 owner-relative recheck 都以
FD7/FD9 的 `(dev, ino)` 与 non-symlink directory entry 为准，不能由 pathname replacement 补救。

final child inherited set 对 bootstrap/adapter process 仍精确为 `{3,4,5,8}`，final raw argv 精确为：

```text
--cwd                     /proc/self/fd/8
--index                   /proc/self/fd/8/.authority-root.index
--bootstrap-project-root  /proc/self/fd/8
--bootstrap-owner-root-fd 8
```

完整 final argv、`-I -S -B -c` payload bytes/SHA、argv digest、FD mapping 与本节 descendant policy
必须在同一未来 implementation SHA 冻结；没有该 SHA 的新三方批准不得执行。

## 3. FD8 到实际 Git consumer 的 descendant contract（关闭 HIGH-1）

### 3.1 精确继承集

任何 post-exec subprocess 只要会 dereference 以 `/proc/self/fd/8` 为前缀的 `cwd`、`GIT_INDEX_FILE`
或 repository path，都是 **FD8 consumer**。它包括 import-free bootstrap 的 `grun()` Git probes，以及
adapter `NativeAuthorityGit._run_bytes()`、`_mutation_succeeded()` 和其所有实际 Git invocation。

每一个 FD8 consumer 必须使用：

```text
close_fds=True
pass_fds=(8,)
```

并保持自身 FD8 未设置 `FD_CLOEXEC` 直到 consumer 返回。不得以默认 subprocess inheritance、
`close_fds=False`、隐式 `cwd` chdir、环境变量复制、重新打开 global CLEAN，或任何未记录 translation
替代此合同。FD3/4/5 **不得**通过这些 Git grandchildren 继承；其只属于 frozen final
bootstrap/adapter ABI，非 Git consumer ABI。executor Git population 继续仅以 FD6 contract执行，
不与 post-exec FD8 consumer混用。

### 3.2 consumer 前后 identity barrier

在每个 FD8 consumer 启动前，bootstrap/adapter 必须用 `fstat(8)` 得到 owner identity，并以
`fstatat`/FD8-relative no-follow check 证明 `.authority-root.index` 与需要的 owned path尚未被
foreign replacement。subprocess 返回后必须再次 `fstat(8)`，并由 owner-FD-relative identity check
证明同一 inode；任何 mismatch、FD8 close、procfs unavailable、index/path type不符或 Git return
无法重新证明，均在下一项 foreign worktree/index/module/config/Git consumption 前 fail-close。

若 failure 出现在Git已可能 mutation后，分类为 `ROLLBACK_INCOMPLETE`，保留 foreign entry 与现场；
否则为 pre-consumption `FAIL`。不得仅因 child `cwd` 曾成功而省略 Git consumer recheck。

### 3.3 强制 actual-Git seam witness

未来 temporary isolated interpreter witness 必须运行一次实际 temporary local/bare Git operation，
其 `GIT_INDEX_FILE` 精确为 `/proc/self/fd/8/.authority-root.index`。最后 executor pathname check后，
替换 global CLEAN entry为 foreign copy/rename；该 Git operation必须只消费 held FD8 inode，或在
foreign index/worktree/module/config consumption前 fail-close。witness必须断言 `close_fds=True`、
`pass_fds==(8,)`、Git child可解析FD8-derived index、FD3/4/5未泄露、foreign inode不被读取/删除。

## 4. Procfd-safe route/module/config identity replacement（关闭 HIGH-2）

### 4.1 禁止的 canonicalization 与允许的路径类别

对任一 post-exec FD8-derived value，禁止 `Path.resolve()`、`os.path.realpath()`、
`os.path.abspath()` 后再以 global CLEAN pathname作等价、边界或 ownership判断。受此禁止的 source
seams至少是 `bootstrap_payload()`、`_bootstrap_identity_from_runtime()`、`_verify_loaded_identity()`、
`NativeAuthorityGit._repository_directory()` 与 `verify_configuration_authority()`。

允许 global pathname 的仅是 Git administrative paths（frozen `.git` marker、gitdir、commondir及
common config）且必须走既有 no-follow FD/raw-byte/route revalidation authority；它们不得被用来
重新导出 CLEAN、adapter module、index或 owner root。CLEAN subtree、project modules、index、cwd和
repository boundary一律是 FD8 owner-anchored values。

### 4.2 冻结 replacement primitive

所有受影响 module/route/config check 使用同一 procfd-safe primitive：从 FD8 根开始，以
`dir_fd=8`、component-by-component `open(..., O_NOFOLLOW)`（目录使用 `O_DIRECTORY`）或等价的
no-follow dirfd traversal打开相对路径；对每个 component/leaf 的 `fstat` 检查目录或 regular
non-symlink type，hash已打开 leaf raw bytes，并与 formal-tree `100644 blob`/raw SHA比较。不得先
resolve procfd string再 `lstat`。

bootstrap module closure须以该 primitive检查 adapter、authority、collection、audit四模块；
`runpy` 前的 `sys.path` entry可以是 `/proc/self/fd/8`，但其可接受性由 FD8 fstat与上述 traversal
证明，不由 `realpath(path)==path` 判断。任一 component symlink、byte/blob mismatch、route drift、
FD8 mismatch或 procfs absence都在项目 import、Evidence/ref/Git consumption前 fail-close。

### 4.3 adapter and Git boundary refreeze

`_verify_loaded_identity()` 必须将 `__file__`/loaded-module paths映射回 FD8-relative component
sequence并以4.2 primitive复验；它不得接受解析后落在 global CLEAN的路径。`_repository_directory()`
与 `verify_configuration_authority()` 必须以 FD8-derived cwd的 retained FD8 identity加 no-follow
relative traversal确认 repository boundary，不能调用 `self.cwd.resolve()`。它们仍须保留现有
common-config FD/raw bytes/allowlist、Git routing marker/gitdir/commondir和 `config.worktree` absence
检查；这组 global administrative checks只验证 Git metadata，不能替换 owner-FD boundary proof。

implementation不得删除原 anti-symlink/route/config checks；只能用本节明确等价或更强的FD-anchored
algorithm替换它们。任何无法完成映射或重新证明的情况一律 fail-close。

### 4.4 replacement witnesses

未来 direct temporary witnesses至少覆盖：

| seam | required assertion |
|---|---|
| bootstrap module | final check后替换 global CLEAN/module entry；FD8 traversal只读held module或在`sys.path`/`runpy`前fail-close，foreign module不import |
| adapter loaded module | replacement/rename后`_verify_loaded_identity()`拒绝，foreign `__file__`或module bytes不接受 |
| config/repository | replacement/rename后的procfd cwd/config/repository check拒绝；common Git administrative route仍按existing FD/raw authority复验 |
| symlink | CLEAN subtree任一module/route component symlink立即拒绝，不能被`realpath`掩盖 |
| descendant Git | 第3.3 actual-Git index witness覆盖FD8存在、identity pre/post、无FD3/4/5 leakage和foreign non-consumption |

所有 witness仅在 `TemporaryDirectory`、temporary sentinel modules和 local/bare Git fixture运行；不得
运行 production main、创建项目 authority artifacts或读取项目 source/checkpoint。

## 5. 唯一请求

请求：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC
```

或 `REQUEST_CHANGES(file:line)`。仅当 ChatGPT、MM、Kimi 对同一新root/child批准后，才允许
root-only stdlib temporary-fixture launcher/adapter/tests implementation。生产/main、真实
materialization/source/checkpoint I/O、collection/receipt/publication、child、GPU、训练、评测、推理
和 LIBERO4IN1 继续禁止。
