# Stage-1 v1.7 request projection preflight design v0.1

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-PROJECTION-PREFLIGHT-CPU-STATIC`。
**状态**：docs-only；提出一个与 request construction authority 完全隔离的纯 projection helper。它不恢复、替代或重试已经消费的 v0.5 construction authority。

## 背景与目标

v0.5 允许的唯一 construction probe 在 request emission 前，因将 replay outer payload 的 `RAW` 中 `base64.b64decode(...)` AST node 当作 literal 而失败。未来任何新的 construction authority 之前，必须先有一个可重复、纯输入输出的 pre-emission projection 核，证明它能从**注入且已验证**的 canonical outer bytes 中机械提取 complete closure。

该 preflight 不能读取 Git object、路径、`.git/config`、refs、remote、环境、source/checkpoint/manifest/data/cache，不能创建 request 或 artifact，不能执行 launcher/materializer。它只接收调用方已经验证为 `18875 / 658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8` 的 bytes。

## 最小 helper 合同

新增 root-only pure stdlib module（建议 `tools/psm_wma/stage1_v17_request_projection.py`）与 direct unittest。API：

```python
project_request_closure(outer_payload_bytes: bytes) -> ProjectedRequestClosure
```

它必须以 AST 而非执行 payload 的方式定位唯一顶层 `RAW` 三元组，并只接受：

1. `RAW[0]`/`RAW[1]` 为唯一 `base64.b64decode(<ASCII str 或 bytes literal>)` 调用；
2. `RAW[2]` 为唯一 bytes/string literal JSON argv；
3. outer 中唯一 `boot` 函数的末尾 return 为可静态拼接的常量 string/bytes expression，得到 bootstrap raw bytes；
4. bootstrap contract 必须由抽取的 canonical argv 与 bootstrap bytes按冻结 JSON sorted/compact 规则计算。

输出必须逐项提供 raw bytes、length、SHA-256：selection、config、canonical parser argv、bootstrap、bootstrap contract，以及 parser/outer replay identities。它还必须将 parser argv 解析为全量字符串数组，拒绝重复/非字符串/非canonical JSON；不允许默认值、环境推断、路径读取或吞掉 AST 例外。

任一缺失、重复、非literal、异常 call target、base64解码失败、UTF-8/JSON错误、hash/length drift、非法 boot return、额外 `RAW` 或 extra tuple element，必须抛出`AuthorityReplayError("BLOCKED_AUTHORITY_NOT_CLOSED:projection_<category>")`；不得返回部分结果。

## CPU/static 验收

测试只能嵌入 gzip/base64 的冻结 outer fixture，或显式注入 bytes；不得 `git show`、读工作树、network、subprocess、临时 Git 或启动 payload。至少覆盖：canonical positive；每项 raw/hash length；`base64.b64decode` 调用target/argument drift；RAW count/arity drift；nonliteral argv；malformed argv；duplicate argv item；boot return drift；contract drift；outer identity drift；partial-result failure。

`py_compile`、direct unittest 与`git diff --check`必须通过。formal implementation scope 仅该 module/test/coordination records；child Gitlink 不变。

## 与 future construction 的互锁

preflight 只有获得此设计的同pair三方 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_REQUEST_PROJECTION_PREFLIGHT_CPU_STATIC`、实现并再获独立close approval后，才可作为未来申请新 construction design 的前置证据。它永远不是 construction attempt：没有allowlisted remote query、freshness snapshot、request output或authority consumption。

即使 preflight 通过，也不授予新的 construction authority；仍须以独立 docs-only design 请求、三方批准、一次fresh zero-mutation snapshot与一份新 exact request review 才可能推进。禁止Stage-1 materialization/retry、launcher、source/checkpoint/manifest/data/cache/runtime I/O、child/runtime、GPU/CUDA/torchrun、训练、评测、推理及LIBERO4IN1。

Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_REQUEST_PROJECTION_PREFLIGHT_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
