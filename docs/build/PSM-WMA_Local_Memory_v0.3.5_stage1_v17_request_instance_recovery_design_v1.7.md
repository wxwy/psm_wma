# Stage-1 v1.7 request-instance recovery design v1.7

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V17`。
**状态**：仅 docs-only recovery design。v0.3 pair 及其已消费 construction authority 绝不覆盖、补写、重跑或重试；本版仅修复 v1.6 三方同 pair final 的 closure finding。

## 唯一未来对象与消费边界

仅当本设计以同一 formal root/child 获三方 `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`，才授权一次 future C。唯一允许输出为：

```text
docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.4.json
docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.4.md
```

P0 只读取 v1.0 的三个 allowlisted Git object 与完整 literal `ReplayBinding`；P1 只对已关闭 projection helper 作 injected-byte projection；两者 non-consuming。C 必须紧接第一项 freshness observation 前开始，并永久消耗一次 authority。任何 precondition、snapshot、producer、consumer、identity 或 residue 失败均零写入（或保留 partial residue 作为终态证据）、永久 no-retry。PASS 只生成 v0.4 pair 并硬停等待独立 exact-pair review，绝不 materialize。

## C 的不可缩减继承闭包

v0.5 的 fresh same-round zero-mutation provenance closure 仍全部生效；v1.7 不得把它缩写为 query blob、ambient state、历史记录或事后 reconstruction。C 必须在**同一个 zero-mutation observation round**将以下完整原始事实及其 required identity 序列化进 canonical JSON：

1. `.git` object/directory identity；`.git/config` raw bytes、length、SHA-256；local `V2` raw value及其 length/SHA-256 identity。
2. 两条且仅两条允许 remote query 的完整 argv、timeout、return code、stdout/stderr raw bytes、各自 length/SHA-256；其中 V2 query 还必须独立绑定由 stdout 提取的 remote `V2` advertised raw value及其 length/SHA-256，不能仅以 query stdout 代替该 provenance field。
3. local fixed authority-ref absence 与 remote fixed authority-ref absence；每项均要有所观测的 path/ref、完整原始结果、length/SHA-256及明确 success/absence predicate。任一诊断、非零返回、非空/不合格结果、超时或 mismatch 均 fail-close，不能从 designated path absence、remote V2 query、旧 round 或环境推断 absence。
4. `selection`、`config`、`bootstrap`、`bootstrap_contract`、replay outer、canonical parser argv 的原始 bytes/完整 argv、length、SHA-256；v1.0 全量 P0 root/path/blob tuple、P1 injected-object identities及 owner-FD flag/value。
5. frozen targets：cwd、index、evidence、两条 designated output paths；以及 designated candidate、record、receipt、publication 路径的显式 absence observations 与 identities。
6. 唯一执行隔离环境，逐字逐值且无补充：`GIT_CONFIG_GLOBAL=/dev/null`、`GIT_CONFIG_NOSYSTEM=1`、`GIT_CONFIG_SYSTEM=/dev/null`、`GIT_NO_REPLACE_OBJECTS=1`、`LANG=C`、`LC_ALL=C`。`PWD`、`SHELL`、`TZ`、`USER` 等 ambient host metadata 不得替代或混入该字段。

任何字段、允许路径、query 数量/顺序、timeout、raw bytes、identity、authority absence、环境键/值或 designated absence 不符合，均在 producer 输出前 fail-close。remote `V2` 只是 construction provenance：其 advertised commit 必须为 future exact-request formal root 的祖先，绝不成为移动协作分支的 runtime equality 条件。

## Detached canonical identity 与唯一 consumer

JSON `canonicalization` 必须逐字声明 `utf-8; recursive sorted keys; compact separators; exactly one terminal LF`。producer 在内存构造 `json_raw` 与 `markdown_raw`；Markdown 必须绑定五项 sibling JSON identity：relative filename、whole raw byte length、SHA-256、同一 canonicalization literal、formal-tree Git blob OID。

两 raw 均严格 UTF-8、无 CR、仅一末尾 LF，沿用 v1.5 的 `patch_raw: bytes → strict UTF-8 patch_text → exactly one apply_patch(patch_text)` seam、byte/text 双 identity及 line encoder/inverse witness。consumer 前断言两条 v0.4 path 均不存在；consumer 后逐字回读，重序列化 JSON 并验证 byte equality、五字段 Markdown binding 和 Git-blob preimage。不得 shell redirection、Python write、临时文件、Git mutation、旧 v0.3内容或事后重建。

## 禁止项与验收

本设计不构造 v0.4，不开启 C，不授权 materialization/retry、launcher/materializer、真实 source/checkpoint/manifest/data/cache I/O、collection/receipt/record/publication、child/runtime/config mutation、GPU/CUDA/torchrun、训练、评测、推理或 LIBERO4IN1。

审阅验收：确认 v0.4 path 不与 v0.3 重叠；v0.5 继承的 `.git`/local V2/remote advertised V2/local+remote fixed authority-ref absence 全部在同轮闭包中逐项显式绑定；six-key环境、canonicalization/五字段identity、one-shot/no-retry和所有 terminal failure 不被削弱；批准范围仅 future docs-only v0.4 construction。

Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.
