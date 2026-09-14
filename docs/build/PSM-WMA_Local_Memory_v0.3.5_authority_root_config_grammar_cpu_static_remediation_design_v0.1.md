# Authority-root config grammar CPU/static remediation design v0.1

**Gate**：`G0-R09-B-TTT-V035-AUTHORITY-ROOT-CONFIG-GRAMMAR-CPU-STATIC-REMEDIATION-DESIGN`
**状态**：proposal；仅供独立三方审核，不授权真实物化或重试。

## 1. 触发事实与边界

Stage-1 v1.3 的唯一获准执行尝试在 launcher `route_snapshot()` 的 config 预检处 fail-close，异常为 `Stop: config section`；该点早于 `add_and_capture()`，后验确认 clean root、ref、index、evidence、pending 均未创建。其冻结 `.git/config` 的合法 section 包含 `[remote "origin"]`、`[branch "main"]`、`[submodule "cosmos-framework"]`、`[branch "V2"]` 和 `[rerere]`，而现有 parser 无条件拒绝任意含引号或点的 section。

本 Gate 只修改 root authority tooling 的 config grammar/allowlist 与 temporary CPU/static tests；不得修改 `.git/config`、child/Gitlink、checkpoint/source/manifest/data/cache、collection/receipt/record/package/publication、GPU/CUDA/torchrun 或训练。v1.3 的单次 execution authority 已消费，修复后必须重新生成 fresh-bound exact request 并重新三方审核，绝不重试 v1.3 bytes。

## 2. 最小实现路线

同时收紧并统一以下两处 parser，禁止只修 launcher 造成 outer/bootstrap 语义分叉：

1. `docs/build/...authority_root_launcher_payload_v0.8.py` 的 frozen payload source；
2. `tools/psm_wma/materialize_immutable_source_authority_root.py` 的 `_parse_config_raw()`。

新增一个共享的、stdlib-only lexical contract（可作为同模块私有 helper；不新增依赖）：section header 仅接受无 subsection 的 `[name]` 或单一 ASCII quoted subsection 的 `[name "subsection"]`。`name` 只能是小写 ASCII 字母及 `-`；`subsection` 只能是 ASCII 字母、数字、`-`、`_`，不允许空串、转义、第二个引号、`.`、`/`、空白、控制字符或额外 token。键仍须为单个 ASCII key token；值保持 raw UTF-8 text，经 exact allowlist 比较，不做 unescape、插值或 include。

在此 lexical grammar 之上，allowlist 只接受本次绑定 route 的无副作用键值：

| canonical key | 允许值 |
| --- | --- |
| `core.repositoryformatversion` | `0` |
| `core.filemode` / `core.logallrefupdates` / `core.bare` / `extensions.worktreeconfig` | 既有安全 boolean/`false`约束 |
| `remote.origin.url` | canonical request remote `https://github.com/wxwy/psm_wma.git` |
| `remote.origin.fetch` | `+refs/heads/*:refs/remotes/origin/*` |
| `branch.main.remote` / `branch.main.merge` | `origin` / `refs/heads/main` |
| `branch.v2.remote` / `branch.v2.merge` / `branch.v2.vscode-merge-base` | `origin` / `refs/heads/V2` / `origin/main` |
| `submodule.cosmos-framework.active` / `.url` | `true` / frozen canonical URL |
| `rerere.enabled` | `true` |

任何未知 section、subsection、key、重复 canonical key、带引号/转义的 value grammar 变化、config.worktree/commondir、symlink、descriptor identity 或 raw digest 漂移仍必须 fail-close。现有 `.git/config` raw SHA binding 保留；allowlist 不是替代 digest，而是限制已绑定 config 的可执行 Git 语义。

## 3. CPU/static 验收

- real current frozen config 在 outer payload `route_snapshot()` 与 bootstrap parser 都可通过到其后的非 config precondition；
- temporary fixture 覆盖允许的 quoted subsection，及每种允许 section 的一项 exact value；
- 拒绝 unknown quoted subsection、空/escaped/dotted/path subsection、重复 key、remote URL/fetch 漂移、branch/submodule/rerere 值漂移、`include`/`includeIf`、hooks/filter/alias 等未知键；
- 保持现有 config.worktree、commondir、symlink、identity relocation 和 raw-digest drift 负例；
- 只运行 stdlib CPU/static tests、`py_compile` 与 `git diff --check`。任何测试不得访问真实 checkpoint/source/manifest/data/cache 或创建 production ref/evidence。

## 4. 后续 Gate

本设计获同 pair 三方 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CONFIG_GRAMMAR_CPU_STATIC` 后，才实现并测试上述两处。实现关闭后仍须独立审核；通过后重新观测 config/raw/ref/path freshness、构造新 payload/request，并对新 exact root/child 获取一次独立的 single-attempt materialization approval。
