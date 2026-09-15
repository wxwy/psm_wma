# Stage-1 v1.7 host-owned continuation boundary design v2.6

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-HOST-OWNED-CONTINUATION-BOUNDARY-DESIGN-V26`。
**状态**：draft；本文件仅冻结后续实现路线，不授权 real pre-C、C、request pair、materialization、source-evidence、child、GPU 或训练。

## 1. 决策与替代范围

用户于 2026-09-15 明确选择 host-owned capability boundary。该选择替代 V25 的“同一 Python interpreter 内以 module registry 保存 session/approval/binding authority”的实现前提。V25 的纯内存 `LivePlanSessionV1` 仅保留为历史 CPU fixture；它不得再被声称为抗任意 caller mutation 的执行边界。

目标是一次性关闭 V25 review 指出的同解释器 `_LIVE_PLANS`、`_LIVE_AUTHORITIES`、`_LIVE_BINDINGS` 可被任意 importer 改写的问题。不可通过改名、私有属性、frozen dataclass、`id()`、digest 或更多 module global 继续修补。

## 2. 信任边界

唯一 authority owner 为独立的 **Stage1Host** 进程，运行于 project Python 解释器之外，并使用专用低权限 OS identity。项目 Python 进程仅是 untrusted client：它不能读取、写入、枚举或重建 host 的 approval state、plan/lease binding、one-shot latch 或 review snapshot。

Stage1Host 启动时由受控 orchestration 创建一对匿名、仅继承给 host 与单个 client 的 IPC endpoints；禁止 pathname socket、环境变量、PATH/tool-name lookup、动态 import 和由 project process 自行发现 endpoint。host 私有状态目录权限必须为 owner-only；project identity 不得拥有该目录、host credential 或 host control channel。若部署环境不能提供独立 OS identity 与私有 endpoint，本 Gate 必须 fail-close，不能降级为同解释器模拟。

此边界不把“恶意拥有 host OS account/root 权限者”纳入保护承诺；其余 project-Python `object.__setattr__`、module-global mutation、monkey patch、copy/pickle、GC/id reuse 与任意公开函数调用均不得改变 host authority。

## 3. 生命周期与唯一协议

1. **Create（pre-C，non-consuming）**：host 接收已验证的 detached canonical `ReviewRecordV26`，生成不可预测 `session_id` 与仅 host 可读的 approval record；host 保存 sealed plan bytes/digest、lease identity、C01--C15、nine-entry freshness、consumer/guard/verifier provenance、paths/environment/query/absence/replay bindings。client 只收到不可解释的 request handle，不能得到 approval secret 或可写 state。
2. **Quiescent review**：host 只允许 `audit(handle)` 返回一份 detached、canonical、不可重建 payload 的 digest record。所有 client-side direct consume、rebind、replace、copy/serialize 或重复 create 都不能推进 host state。
3. **Approve**：host 仅接受由 orchestration review-attestation channel 写入的 exact root/child/review-record digest approval；client IPC 不能自行发送或伪造该 transition。attestation 与 session creation record 不完全相等即 terminal `INVALID`。
4. **Resume once**：client 提交 opaque handle；host 比较当前 host-owned record 与 creation-time reviewed record，检查 approval、freshness guard 和 terminal latch。仅 `FRESH` 时，host 在自身进程内调用唯一 registered add-only consumer，随后自身读取并逐字节验证两输出；client 从不拿到 consumer callable、patch bytes、write capability 或 readback capability。
5. **Terminal**：任何 malformed request、identity/drift、STALE/UNKNOWN、consumer rejection/partial result/readback mismatch、host restart/loss、IPC failure或一次调用完成，均把 session 置为不可恢复 terminal；没有 retry、repair、cleanup 或替代 session。

未来 C 的最小序列仍严格为：`host freshness snapshot comparison -> one host opaque write -> host byte-for-byte verify -> hard stop`。所有解析、路径推断、schema 补全、format generation、consumer discovery、dynamic import 和 review lookup 都只能在 Create 前完成，且不在 C 内发生。

## 4. 完整 ReviewRecordV26

host 仅接受 detached canonical primitives（UTF-8 strings、bytes SHA/length、ordered tuples、booleans、integers），不得保存 project dataclass/object reference 或 `repr()` digest。记录精确包含：

- formal root/child Gitlink、review-record digest与批准 attestation identity；
- canonical JSON/Markdown bytes、patch raw/strict-UTF-8 identity、ordered v0.5 output paths；
- consumer、freshness guard、post-write verifier 的 provider/module/path/source-blob/callable/ABI/transport identity；
- C01--C15 literal set、nine-entry freshness identities、six-key environment、`.git`/local V2/remote V2/authority-ref/query stdout+stderr+predicate、local/remote authority absences及四条 designated absences；
- P0/P1/replay binding、frozen targets、descriptor、ordered source/argv rows及 canonical identity digests。

host 比较的是 canonical byte serialization 的 exact equality；审计响应只披露已审核摘要与必要的 non-reconstructing identities。缺项、额外项、重排或任何 digest mismatch 一律 `INVALID`，且 freshness/consumer/apply 计数为零。

## 5. 实现拆分与验收

在获得本文件三方同 pair `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_HOST_OWNED_CONTINUATION_CPU_STATIC` 前，只允许为协议写 CPU/static fake-host tests；不得接入真实 host process、IPC、apply_patch 或路径 I/O。

获准后的第一实现阶段仅提供 stdlib fake host transport 和 protocol conformance tests，随后以新的 formal pair 单独审核。真实 OS identity、private inherited IPC、attestation injection 和 host consumer 的 integration design 必须再次三方审核，之后才可 real pre-C。

CPU/static fixtures必须证明：

- client 模块 global、session object、handle object和 monkey patch任意改写不影响 host admission；
- forged approval、cleared bookkeeping、binding replacement、foreign/replayed handle、host restart与重复 resume 全部在 freshness/consumer/apply 前 terminalize；
- ReviewRecordV26 的每个类别 drift（含 verifier provenance、C01--C15、absence target/predicate、replay binding）均零调用拒绝；
- 只有 host attestation 后的 exact handle 能走一次 FRESH -> apply -> readback；第二次恒为 terminal；
- fake host 不执行文件、Git、network、subprocess、真实 apply_patch、child、torch 或 GPU。

## 6. 明确禁止

本设计不改变 Local Memory v0.3.5 算法、Cosmos runtime、optimizer、配置、数据或 latent cache。它不授权真实 pre-C/C、request pair、materialization/source evidence、record/publication、submodule修改、GPU、torchrun、训练、评测或推理。

Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_HOST_OWNED_CONTINUATION_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
