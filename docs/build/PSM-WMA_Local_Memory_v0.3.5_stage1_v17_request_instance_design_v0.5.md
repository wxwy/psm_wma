# Stage-1 v1.7 request-instance design v0.5

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`。
**状态**：docs-only v0.4/first-v0.2-request remediation；与 v0.1--v0.4 冲突时以本文为准。除本文件明确修订外，冻结依赖、two-query allowlist、zero-mutation、one-request/no-retry 和禁止边界不变。

## 修订原因与范围

v0.3 §Construction contract 要求 JSON “bind ... its own whole bytes/SHA”。把一份文件的完整字节 SHA-256 作为该同一字节串内的普通值没有可构造的有限解：变更字段本身会改变待哈希字节。v0.2 因而以 Markdown sidecar 绑定 whole identity，但未把这一非循环规则写入冻结设计，且其声明的compact canonical serialization与实际文件字节不一致。

本修订不删除 whole-file identity；只将其从不可能的自嵌字段改为请求对（Markdown + JSON）的明确、非循环且可机械验证的绑定。它不授权构造、materialization 或任何执行。

## Canonical JSON / Markdown sidecar binding

未来 exact request 的 JSON 必须是唯一 canonical byte representation：UTF-8、递归 sorted keys、`separators=(",", ":")`、无额外空白、末尾恰一 `\n`。JSON 内必须以 `canonicalization` 字段精确声明此规则；它不得包含其自身完整文件的长度或 SHA 字段。

同一 request 的 Markdown 必须在独立的 `JSON whole identity` 小节中绑定该 sibling JSON 的：

1. 相对文件名；
2. canonical raw byte length；
3. SHA-256；
4. canonicalization literal；
5. JSON formal Git blob OID（request formal tree 中的 blob）。

机械 verifier 必须先读取 JSON raw bytes，重新以该 JSON object 序列化为上述 canonical bytes，并要求 raw bytes逐字节相等；再比较 Markdown 的五项 sidecar identity。任一不等、缺项、extra self-identity字段、Markdown/JSON路径不唯一或formal-tree blob不符，均在任何 freshness/preflight或`os.execve`之前以`BLOCKED_AUTHORITY_NOT_CLOSED:request-identity`拒绝。

因此 request pair 同时绑定完整不可变 JSON 文件和其内容；Markdown 不是环境推断或可选说明，而是审核 formal tree 中唯一允许承载 JSON whole identity 的 detached identity record。

## 完整 closure 与 fresh snapshot 保持

本修订不缩小 v0.3/v0.4 的 JSON closure。未来替换 request 仍须在**新的一次同轮**、zero-mutation、已批准 allowlist 观察中，将下列原始事实完整写入 JSON：formal/base/replay identities；`.git` identity及`.git/config` raw bytes；local `V2`；两条exact remote query的command、timeout、return code、stdout/stderr raw bytes、length、SHA及V2 advertised raw value；local/remote authority-ref absence；designated path absences；selection/config/bootstrap/contract raw bytes、length、SHA；canonical parser argv及其length/SHA；six key/value environment；owner-FD insertion；replay output；cwd/index/evidence targets。

remote `V2` 仍仅是 construction provenance：其本轮 advertised commit 必须为未来 exact request formal root 的祖先，不得成为自然移动协作分支的runtime equality条件。fixed authority-ref 与指定absence仍是runtime freshness，且任一drift都必须在零写入阶段拒绝。v0.2 的历史观察不得以新时间戳复用。

## 构造与执行边界

只有本 v0.5 获同pair三方 `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` 后，才可按冻结 two-query allowlist 构造**一份**新的docs-only replacement request pair。该pair必须独立获得三方 exact-pair review；其批准至多授予该exact request的一次 Stage-1 attempt。任何pre-mutation drift零写入拒绝；成功只输出 authority tuple 后硬停；失败或消耗后永久禁止retry，必须重新设计、构造和批准。

本设计及其审核不授权 launcher/materializer、Stage-1 materialization/retry、source/checkpoint/manifest/data/cache/runtime I/O、collection/receipt/record/package/publication、child/runtime mutation、GPU/CUDA/torchrun、训练、评测、推理或LIBERO4IN1。

Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.
