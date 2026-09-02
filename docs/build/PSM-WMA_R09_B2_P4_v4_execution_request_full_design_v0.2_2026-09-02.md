# R09-B2 P4-v4 Execution Request full admission 静态合同 v0.2

**状态**：draft；替代未批准的 v0.1。仅申请 future root request parser admission 与 stdlib CPU fixture；禁止真实 request、P4 preflight、materialize、P5、GPU 或训练。

前置八个 static section（`entry/source/interpreter/environment/authorities/run/candidates/backends`）已关闭。full admission 仅串联同一 canonical raw 的既有合同，不重定义任一 nested schema 或已关闭 `validate_source` 接口。

`load_execution_request(raw)` 固定检查 canonical JSON、exact `REQUEST_KEYS`、schema version 与 frozen `execution_contract`，并依序调用：`validate_entry` → `validate_host_git` 得 `git_path` → `validate_source(request["source"], request["entry"], git_path)`（接口/返回值不变）→ `validate_interpreter(..., git_path)` → `validate_run_pair` → `validate_candidates` → `validate_backends` → `validate_authorities_pair(request["authorities"], request, source_root, git_path)`。`git_path` 必为同一 invocation 的同一 `Path` object，fixture spy 证明 source/interpreter/authorities 三路复用；source root 不主张不可能的跨函数 object identity：source 验证返回后只从同一 parsed immutable `request["source"]["root"]` 构造一次 `source_root=Path(...)`，并以该字段的 exact canonical value、source validator 已成功及传给 authorities 的该唯一 object证明 binding。

authorities 是唯一 environment-D005 projection route；full layer 不调 `validate_environment_pair()` 或 D005 `verify_pair()`，不复制 allowlist/P3 mapping。成功仅返回内存 request，`main()` single-fd SHA binding及无条件 hard-stop 保持。

route-only fixture mock 已关闭 source/interpreter/authorities 的**底层** I/O，spy 正确 validator 的顺序/实参；full layer 不新增 subprocess。它不得把已有 source 固定 host-Git `subprocess` 或 authorities 固定 historical blob lookup 误报为禁止；仍永久禁止新增 bare Git/PATH/which/P5 exporter/verifier/child/torchrun/network/GPU 路径。fixture 覆盖 full valid route hard-stop、每 section reidentified mutation、git object identity、root canonical-value binding、authorities path、旧 environment/verify_pair 拒绝、hostile ambient及 future roots 未创建/未打开。

若批准，仅修改 `tools/g0/r09_b2_p4_v4_execution_preflight.py` 与其 stdlib CPU test，之后独立 implementation closure review。禁止真实 request/preflight/staging/P5/GPU/训练。请求 verdict：`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_FULL_STATIC_TOOLS` 或 `REQUEST_CHANGES`（附 `file:line`）。
