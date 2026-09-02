# R09-B2 P4-v4 Execution-Preflight Materialization 设计 v0.5

**状态**：draft，替代未关闭 implementation 的 v0.4；仅申请 root static helper/stdlib CPU fixture。CLI 永远 hard-stop，禁止真实 request/preflight/materialize/P5/GPU/训练。

## 1. 固定前置与整改对象

v0.4 design=`dcb5b12` 已三方批准；implementation=`9bc78f1` 收到 ChatGPT=`8e1d019`、Kimi=`19:52` 的 REQUEST_CHANGES。v0.5 仅关闭：(a) capability 可直接伪造/重置；(b) pathname mkdir parent-symlink TOCTOU；(c) approved fixture matrix缺口。不改 closed execution-request nested/full validators、P5/P3 authority或 public main。

## 2. 不可伪造 admission capability

`_AdmittedRequest` 不公开 dataclass constructor：唯一 factory `_admit_execution_request(raw)` 先成功执行既有 `load_execution_request(raw)`，再将 canonical raw、SHA、已解析 immutable reservation plan 和 private unforgeable proof封装。admission fields及 proof不可赋值；仅 private one-shot state可从 `UNUSED` 单向变为 `CONSUMED`，不得复位。helper 只接受该 capability；bare raw/dict/reparse/deepcopy、伪造实例及 admission 后字段/状态 mutation均 fail-closed。fixture 必经真实 `_admit_execution_request()` 的完整 canonical request，而不是简化 JSON。

## 3. anchored nofollow dir-fd primitive

namespace 以 `O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC` 打开成 verified directory FD；每个 backend root/middle/leaf 均只以相对于已验证 parent FD 的 `os.mkdir(name, dir_fd=parent_fd)` 创建。创建后立即 `os.open(name, O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC, dir_fd=parent_fd)` 获得 child FD 并 `fstat` 验证 directory、非 symlink；下一层只使用该 child FD，绝不重新解析完整 pathname。所有 FD 用 finally 关闭。

precheck仍在 mutation前完成。fixture 在每个 precheck/parent替换窗口重定向路径为 symlink，证明写入仍只能落在原 namespace FD，外部 target零写入。

## 4. 状态和 fixture

成功 mkdir立即加入 `created_paths` mutation footprint；mkdir fail不加入，post-open/fstat fail保留刚创建 path。任意 terminal 消耗 capability，禁止 cleanup/retry/reuse。fixtures 必覆盖真实 admission、forge/mutation/reset、namespace/path/run/token/overlap precheck且零 mkdir、六 mkdir+六 post-create verification fault exact prefix/failed path/cause、parent retarget no escape、ambient/subprocess/P5/child poison、CLI hard-stop零 helper。

若批准仅改 P4 root helper/test并 CPU验证。请求 `APPROVE_TO_IMPLEMENT_P4_V4_PREFLIGHT_MATERIALIZATION_STATIC_TOOLS` 或 `REQUEST_CHANGES`（file:line）。
