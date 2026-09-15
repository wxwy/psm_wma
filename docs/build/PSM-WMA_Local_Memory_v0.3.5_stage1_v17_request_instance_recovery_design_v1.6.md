# Stage-1 v1.7 request-instance recovery design v1.6

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V16`。
**状态**：仅 docs-only recovery design；v0.3 pair 与其已消费 authority 不得覆盖、补写、重跑或重试。

## 唯一未来对象与消费边界

若且仅若本设计获得同一 formal root/child 的三方 `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`，才授权一次 future C。其新输出只能为：

```text
docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.4.json
docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.4.md
```

P0 只读取 v1.0 的三个 allowlisted Git object 和完整 literal `ReplayBinding`；P1 只对已关闭 projection helper 执行 injected-byte projection；二者均 non-consuming。C 紧接第一次 freshness observation 前开始并永久消耗一次 authority。任一 precondition、snapshot、producer、consumer、identity 或 residue 失败均零写入或保留 residue 作证据，永久 no-retry；PASS 只生成 v0.4 pair 并硬停等待独立 exact-pair review，绝不 materialize。

## C 的不可缩减闭包

C 必须将以下完整原始事实（不是仅 length/SHA 摘要）序列化进 canonical JSON：

1. `.git/config` raw bytes、length、SHA-256；两个远端 query 的 argv、timeout、return code、stdout/stderr raw bytes、各自 length/SHA-256。
2. `selection`、`config`、`bootstrap`、`bootstrap_contract`、replay outer 和 canonical parser argv 的原始 bytes/完整 argv、length、SHA-256，以及 v1.0 全量 P0 root/path/blob tuple、P1 injected-object identities、owner FD flag/value。
3. frozen targets：cwd、index、evidence、两条 designated output paths；以及 designated candidate、record、receipt、publication 路径的显式 absence observations 和 identities。
4. 唯一执行隔离环境，逐字、逐值、无环境补充：`GIT_CONFIG_GLOBAL=/dev/null`、`GIT_CONFIG_NOSYSTEM=1`、`GIT_CONFIG_SYSTEM=/dev/null`、`GIT_NO_REPLACE_OBJECTS=1`、`LANG=C`、`LC_ALL=C`。`PWD`、`SHELL`、`TZ`、`USER` 等 ambient host metadata 不得替代或混入该字段。

任何字段、允许路径、query 数量/顺序、timeout、raw bytes、identity、环境键/值或 absence 结果不符合上述闭包均在输出前 fail-close。

## detached canonical identity 与唯一 consumer

JSON `canonicalization` 必须逐字声明 `utf-8; recursive sorted keys; compact separators; exactly one terminal LF`。producer 在内存构造 `json_raw` 与 `markdown_raw`；Markdown 必须绑定五项 sibling JSON identity：relative filename、whole raw byte length、SHA-256、同一 canonicalization literal、formal-tree Git blob OID。

两 raw 均严格 UTF-8、无 CR、仅一末尾 LF，沿用 v1.5 的 `patch_raw: bytes → strict UTF-8 patch_text → exactly one apply_patch(patch_text)` seam 和 byte/text 双 identity、line encoder/inverse witness。consumer 前断言两条 v0.4 path 均不存在；consumer 后逐字回读两文件，重序列化 JSON 并验证 byte equality、五字段 Markdown binding 和 Git-blob preimage。不得用 shell redirection、Python write、临时文件、Git mutation、旧 v0.3 内容或事后重建代替。

## 禁止项与验收

本设计本身不构造 v0.4、不开启 C、不授权 materialization/retry、launcher/materializer、真实 source/checkpoint/manifest/data/cache I/O、collection/receipt/record/publication、child/runtime/config mutation、GPU/CUDA/torchrun、训练、评测、推理或 LIBERO4IN1。

审阅验收：确认新 pair 不与 v0.3 路径重叠；C 闭包没有缩减；six-key 环境精确；canonicalization/五字段完整；所有失败路径 terminal；批准范围仅 future docs-only v0.4 construction。

Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.
