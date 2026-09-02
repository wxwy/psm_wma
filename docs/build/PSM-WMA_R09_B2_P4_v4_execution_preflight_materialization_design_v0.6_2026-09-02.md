# R09-B2 P4-v4 Execution-Preflight Materialization 设计 v0.6

**状态**：draft，替代未关闭 implementation 的 v0.5；仅申请 root static helper/stdlib CPU fixture。CLI 永远 hard-stop，禁止真实 request/preflight/materialize/P5/GPU/训练。

## 1. 固定前置与本次整改

v0.5 design=`d3b37e7` 获 Kimi/MM `APPROVE_TO_IMPLEMENT_P4_V4_PREFLIGHT_MATERIALIZATION_STATIC_TOOLS`，ChatGPT review=`8511bf0` 为唯一 `REQUEST_CHANGES`。v0.6 仅关闭 namespace anchor 获取晚于 pathname 预检的 race；v0.5 的不可伪造 capability、child `dir_fd` nofollow 链、poison 语义和 fixture 名册均不重开。不改 closed execution-request validators、P5/P3 authority 或 public main。

## 2. 不可伪造 admission capability

`_AdmittedRequest` 不公开 dataclass constructor：唯一 factory `_admit_execution_request(raw)` 先成功执行既有 `load_execution_request(raw)`，再将 canonical raw、SHA、已解析 immutable reservation plan 和 private unforgeable proof封装。admission fields及 proof不可赋值；仅 private one-shot state可从 `UNUSED` 单向变为 `CONSUMED`，不得复位。helper 只接受该 capability；bare raw/dict/reparse/deepcopy、伪造实例及 admission 后字段/状态 mutation均 fail-closed。fixture 必经真实 `_admit_execution_request()` 的完整 canonical request，而不是简化 JSON。

## 3. namespace 的先锚定 openat 链

所有 reservation precheck 之前，helper 必先取得 namespace directory FD；不得先以 pathname `stat`/`resolve`/`lstat` 检查 namespace 或其 ancestors，再用完整 pathname `os.open(namespace, ...)`。仅接受绝对、词法规范、非根的 namespace；拒绝空组件、`.`、`..` 及不符合既有 lexical 约束的值。

实现从 `os.open("/", O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC)` 获得 root anchor FD，再按 namespace 的每个 lexical component 顺序执行 `os.open(component, O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC, dir_fd=parent_fd)`，随后 `fstat` 验证 directory、非 symlink；仅以刚取得的 child FD 继续。前一 FD 在 child 已验证后关闭，失败时关闭全部已打开 FD并 fail-closed。除初始 `/` 外，不得以多组件或完整 namespace pathname 调用 `os.open`，也不得在 anchor 后为写入重新解析 namespace pathname。展示/错误中的 `Path` 仅来自已验证的 immutable lexical plan，绝不作为后续 filesystem authority。

namespace FD 锚定后，所有 filesystem precheck 均相对它进行。未来 run roots 必须由 immutable plan 的两个 direct-child backend 名给出；以 `os.stat(name, dir_fd=namespace_fd, follow_symlinks=False)` 仅接受 `ENOENT`，已有文件、目录或 symlink一律在零 mkdir 前拒绝。由于 direct child root 已证实不存在，禁止为了预检未来 `import_staging/<token>` 而作多组件 pathname traversal；其余 lexical token、backend overlap、plan identity check仍为纯内存 precheck。

## 4. anchored child mutation primitive

namespace FD 已锚定后，每个 backend root/middle/leaf 均只以相对于已验证 parent FD 的 `os.mkdir(name, dir_fd=parent_fd)` 创建。创建后立即 `os.open(name, O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC, dir_fd=parent_fd)` 获得 child FD并 `fstat`；下一层只使用 child FD，绝不重解析完整 pathname。所有 FD 用 finally 关闭。

成功 mkdir立即加入 `created_paths` mutation footprint；mkdir fail不加入，post-open/fstat fail保留刚创建 path。任意 terminal 消耗 capability，禁止 cleanup/retry/reuse。

## 5. 固定 fixture 和验收

fixtures 必覆盖真实 admission、forge/mutation/reset、全部 namespace lexical/anchor-acquisition/direct-child-absence/path/run/token/overlap precheck且零 mkdir、六 mkdir+六 post-create verification fault exact prefix/failed path/cause、ambient/subprocess/P5/child poison、CLI hard-stop零 helper。

新增的 namespace race fixture须在 component traversal 的 acquisition 窗口和 anchor 后的 mutation窗口将 namespace 或 ancestor lexical pathname替换/重定向为 symlink：前者必须 fail-closed 或获得原 component FD；后者必须继续绑定已锚定 namespace FD，外部 target零写入。fixture 不得以 pathname 重查替代 FD-anchored 断言。

若批准仅改 P4 root helper/test并 CPU验证。请求 `APPROVE_TO_IMPLEMENT_P4_V4_PREFLIGHT_MATERIALIZATION_STATIC_TOOLS` 或 `REQUEST_CHANGES`（file:line）。
