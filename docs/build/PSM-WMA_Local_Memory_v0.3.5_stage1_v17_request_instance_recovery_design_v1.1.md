# Stage-1 v1.7 request-instance recovery design v1.1

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN`。
**状态**：仅 docs-only recovery design；不构造 request，不授权 materialization 或任何执行。

## 已消费 authority 的不可复用事实

`9c8b4adc71b92caad5ecaf6fb044f5c01a4f9d9a` / `93a89ba61306d840a008813f62f26a34d54850f4`
的 v1.0 construct approval 只授权一次。其 P0/P1 已成功，但其后一次 output-path
enumeration 是 P1 后首次 designated-path freshness observation，故已进入 C；没有形成完整
C snapshot 或 request 输出。依 v0.7/v1.0 的 one-shot/no-retry 语义，该 authority 已永久耗尽，
不得重试、补跑或把它重新解释为 P0/P1。

本版不改变该事实，也不把它变成 materialization authority。

## Future request pair 的冻结路径

任何经本版后续独立批准而产生的**唯一** future request pair 必须使用下列固定 sibling 路径：

```text
docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.3.md
docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.3.json
```

这两个 pathname 是本设计的字面常量，不得由 worktree discovery、历史 request、环境、时间戳、
glob 或 C 内临时选择推导。既有 `v0.1`、`v0.2` request pair 是历史记录，不是新 request 的
候选、模板、输入或输出。future C 只检查上述 v0.3 pair 的 absence；不得把历史 pair 的存在
解释为 drift，也不得在 P1 后额外枚举其他 request 路径。

## Future construction 的阶段边界

future construct approval 必须另行由 ChatGPT、MM、DS 对新的 exact formal root/child 给出
`APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`。它至多允许下列一次序列：

```text
P0  frozen Git-object acquisition and identity checks       (non-consuming)
P1  injected-byte replay and project_request_closure        (non-consuming)
C   begins immediately before the first freshness observation (consuming)
```

- P0 only reads the v1.0 closed three-object allowlist and uses the v1.0 complete literal
  `ReplayBinding`; it must not read a test, worktree source, environment, history copy, request
  output path, or an alternate Git object.
- P1 only invokes frozen `079167743685247d6aae62a671436e834411a3cb`
  `project_request_closure` with P0-verified injected bytes. It performs no Git/path/network/
  environment/output I/O.
- C begins before its first `.git`/config/local-ref/remote-ref/designated-path/environment
  observation. C consumes its new one-shot authority even if any later observation, canonical
  serialization, write, verifier, or exception fails. No retry is permitted.

## C snapshot and output contract

C retains the v0.5--v1.0 closure contract without weakening it: one same-round zero-mutation
snapshot of formal/base/replay identities, `.git`/config raw identities, local `V2`, exactly two
timeout-protected remote queries (`refs/heads/V2` and fixed
`refs/heads/authority/r09-b-ttt-v035-immutable-source-v1`), fixed-local/remote authority-ref
absence, the exact v0.3 pair absence above, closure bytes, canonical parser argv, six environment
key/value pairs, owner-FD insertion, replay identities, and cwd/index/evidence targets.

Only after every required observation passes may C write exactly the v0.3 JSON/Markdown pair. JSON
is UTF-8, recursive sorted-key compact JSON with exactly one terminal newline and contains no
self length/SHA. Markdown is the detached sibling identity record and binds JSON relative name,
whole byte length, SHA-256, canonicalization literal and formal-tree blob OID. A mechanical
verifier must reserialize and compare exact bytes before any later freshness/preflight or exec.

The resulting request remains a docs-only review object. It must receive independent exact-pair
three-party review before it can authorize a separate single Stage-1 attempt.

## Prohibitions

This design and its review prohibit request construction, materialization, launcher/materializer
execution, source/checkpoint/manifest/data/cache I/O, collection/receipt/record/publication,
child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference and LIBERO4IN1.

Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or
`REQUEST_CHANGES(file:line)`.
