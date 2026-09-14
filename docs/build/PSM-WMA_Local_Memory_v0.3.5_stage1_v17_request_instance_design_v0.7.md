# Stage-1 v1.7 request-instance design v0.7

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`。
**状态**：仅 docs-only v0.6 remediation；v0.6 不再提供 construction authority。除本文明确修订外，v0.5 的 non-circular request pair identity、two-query contracts、零写入及禁止范围保持。

## 唯一时序与 authority 消耗点

v0.6 的唯一 attempt 尚未开始。未来经本版批准后的流程严格为：

```text
P0 immutable input acquisition  (non-consuming)
  -> P1 pure replay + projection (non-consuming)
  -> C construction attempt begins (consuming, before first freshness observation)
  -> same-round snapshot / canonical pair write / verify / hard stop
```

`C` 的唯一、不可歧义消费点为：P1 成功返回并且构建者开始第一项同轮 `.git`、ref、remote、path-absence 或 environment observation **之前**。进入 C 即永久消耗该设计批准的唯一 construction authority；此后任一 observation、identity、write、verification 或异常失败均零输出或保留失败事实，但不得 retry、补跑或再构造。

P0/P1 的失败不进入 C，因而不消费 authority；它们只可在同一获批 authority 下重新执行以取得成功的、当前 formal object binding。P0/P1 不得写 request、创建目录/ref/record/receipt，也不得执行网络、materializer、child、GPU 或训练。

## P0：冻结对象取得与 replay binding

P0 是唯一允许取得 Phase-P 输入的 non-consuming read-only authority。它只允许从 future formal root/其冻结 parent 的 Git object database 读取并验证：launcher replay base bytes、outer payload source bytes、adapter source bytes、各自 Git blob OID、raw length、SHA-256，以及 formal tree/Gitlink identities。禁止读取 ambient worktree 文件、任何 source/checkpoint/manifest/data/cache路径、网络、ref mutation或输出路径。

P0 必须用已关闭的 `stage1_v17_launcher_replay` pure helper 对取得的 frozen base bytes执行 `replay_outer_payload(base_source, binding)`；binding、base raw/object identity、replay output raw/length/SHA与 parser identity都须成为 P0 result。该 helper调用只处理已取得的内存 bytes，不构成 Git/network/filesystem I/O，也不消耗 authority。

P0 仅在 replay output 与冻结 outer identity、adapter bytes 与冻结 adapter blob/raw identities全相等时成功。它将 verified outer bytes、verified adapter bytes及其完整 identity 作为 P1 唯一注入输入；不得从环境、历史结果或未验证工作树推断这些 bytes。

## P1：纯 projection

P1 仅调用 closed root `079167743685247d6aae62a671436e834411a3cb` 的 `project_request_closure(outer_bytes, adapter_bytes)`。P1 的输入必须逐字节来自本次 P0 result；返回的完整 `ProjectedRequestClosure`（包括 selection/config/parser/bootstrap/contract/outer/adapter fields）是 C 的唯一 closure 输入。P1 不得读取 Git、路径、网络、环境或写出文件；失败不产生 request且不消费 authority。

## C：同轮 freshness 与一份 request pair

进入 C 后才允许一次性执行 v0.5 frozen allowlist：local `.git`/config/local V2、两条 exact `git ls-remote`（V2与fixed authority ref，均记录 command/timeout/returncode/stdout/stderr raw identities）、local/remote ref absence、designated path absences、six environment values与owner-FD/cwd/index/evidence targets。所有结果与P0/P1 closure必须写入 canonical JSON，并由Markdown sidecar绑定其whole JSON identity。

任何 C observation失败立即 fail-close且不retry。成功只写一份docs-only Markdown/JSON request pair、机械核验其 detached identity、供独立 exact-pair review后硬停；仍不授权 materialization、launcher、payload访问、child、GPU或训练。

Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.
