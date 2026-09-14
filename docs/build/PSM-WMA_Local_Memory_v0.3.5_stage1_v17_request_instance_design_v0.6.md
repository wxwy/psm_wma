# Stage-1 v1.7 request-instance design v0.6

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`。
**状态**：docs-only replacement construction-authority design；v0.5 的唯一构造权已在零写入 pre-emission AST failure 时消费，不能复用。与 v0.1--v0.5 冲突时以本文为准。

## 1. 目的、前置与唯一授权范围

此前 v0.5 获批后的一次构造 probe 在输出前因 outer `RAW` AST 投影错误失败；它没有创建 request，但依 one-request/no-retry 约束，原构造权永久消费。该失败不产生第二次尝试权。

新的前置已经独立关闭：

```text
projection implementation root: 079167743685247d6aae62a671436e834411a3cb
projection child/Gitlink:       93a89ba61306d840a008813f62f26a34d54850f4
verdict: APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_REQUEST_PROJECTION_PREFLIGHT_CPU_STATIC_IMPLEMENTATION
```

该 helper 是纯 stdlib、仅接受注入 outer/adapter bytes 的 pre-emission projection；它不读取 Git、路径、网络或输出文件，也不消耗 request-construction authority。其成功结果才可作为本设计未来构造的输入 closure。它不替代同轮 freshness snapshot，也不构成 request、materialization 或 runtime authorization。

本 v0.6 若获同 pair 三方
`APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`，仅授权**一次**按本文构造一份 docs-only replacement request Markdown/JSON pair。此设计不授权该 request 的 materialization、launcher 或任何执行；新 request 必须另获 exact-pair 三方审核。

## 2. 两阶段互锁：projection 在 authority attempt 之外

构造流程必须严格拆为两个阶段：

1. **Phase P — pre-emission projection**：向已关闭 helper 注入 formal-tree frozen outer bytes 和 adapter bytes，验证 outer/adapter identity、single-literal `RAW` grammar、selection/config/parser/bootstrap/contract closure。该阶段无网络、Git、filesystem/path、subprocess 或输出写入；任一失败仅为 `BLOCKED_AUTHORITY_NOT_CLOSED:projection_<category>`，不创建 request、也不消费下述 attempt。
2. **Phase C — one authority construction attempt**：仅当 Phase P 成功且所有下列同轮 zero-mutation observations 已完成，才开始。Phase C 的开始时刻即消耗本 v0.6 的唯一构造权；任何 pre-emission check 失败、写入失败、identity drift 或异常都不得 retry。

Phase P 不得在 Phase C 已开始后重新运行以补救失败。Phase C 不得直接重解 outer AST、绕过 `ProjectedRequestClosure`，或把历史 projection/result 当作当前输入。

## 3. Phase C 的同轮只读 allowlist

在 Phase P success 后、JSON/Markdown 输出前，Phase C 只允许读取下列项目；所有原始 bytes、命令、length、SHA-256 与结果必须写入 future JSON：

1. formal Git commit/tree/blob（含 frozen parent、projection helper root、outer/adapter/replay base bytes及其 object identities）；
2. local `.git` identity 与 `.git/config` raw bytes；
3. local `V2` ref；
4. 两条且仅两条受超时保护的 remote query：
   ```text
   git ls-remote origin refs/heads/V2
   git ls-remote origin refs/heads/authority/r09-b-ttt-v035-immutable-source-v1
   ```
   每条必须记录 return code、stdout/stderr raw bytes、length、SHA。authority ref absence 仅在第二条 return code=0、stdout/stderr 均为空时成立；
5. frozen local/remote authority-ref absence，以及 designated future output、candidate、record、receipt、publication 路径 absence；
6. six key/value environment、owner-FD insertion、cwd/index/evidence targets，以及 Phase P 的完整 `ProjectedRequestClosure` fields。

除上述 allowlist 外，禁止网络调用、Git mutation、source/checkpoint/manifest/data/cache content access、launcher/materializer、child/runtime、GPU 或训练。任何 allowlist observation 非预期、超时、缺项、identity 不一致或 absence 不成立，均在输出前 fail-close，且因 Phase C 已开始不得 retry。

## 4. Future request pair 的非循环 identity

future JSON 仍必须是唯一 canonical UTF-8 representation：recursive sorted keys、`separators=(",", ":")`、无额外空白、末尾恰一换行，并以 `canonicalization` 字段声明；JSON 不得自嵌自身 length/SHA。

future Markdown 作为 detached sidecar，必须绑定 JSON sibling 的相对文件名、raw byte length、SHA-256、canonicalization literal 与 formal-tree Git blob OID。verifier 必须重新序列化 JSON、比较 whole raw bytes，再比较五项 Markdown binding；任一差异、extra self-identity、路径不唯一或 blob 不符，在任何 freshness/FD/exec 前拒绝 `BLOCKED_AUTHORITY_NOT_CLOSED:request-identity`。

## 5. 输出、终止与禁止范围

Phase C 只可写一份 request Markdown/JSON pair 到冻结路径；写入后立即执行 canonical identity verification。成功只表示 request 已供独立审核，硬停：不运行 launcher/materializer，不创建 authority root/candidate/ref/record/package/publication，不访问 payload/source/checkpoint/manifest/data/cache，也不触及 child、GPU、训练、评测、推理或 LIBERO4IN1。

任何失败或成功都不允许在本 v0.6 authority 下重试、补写、覆盖或修改该 pair。未来再次构造必须新建 design、获得新的三方 exact-pair construction approval。

Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.
