# Stage-1 v1.7 host-owned continuation boundary design v2.7

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-HOST-OWNED-CONTINUATION-BOUNDARY-DESIGN-V27`。
**状态**：draft；本版仅完成 V26 同 pair review 的三项 docs-only 整改，未授权 fake-host、real host/IPC、pre-C、C、request pair、materialization、child、GPU 或训练。

## 1. V24 → V27 明确继承与替代

V24 的以下语义继续严格生效：唯一 reviewed authority、从 non-consuming pre-C 到 verified resume 的同一 live authority、review record 非重构性、loss/restart terminal、exactly-once C、无 retry。

仅以如下 host-owned 等价物替代 V24/V25 中“同一 project-Python object/session/lease”措辞：独立低权限 `Stage1Host` 的同一 generation 内，唯一 `HostSessionV27`、唯一 `LivePlanEnvelopeV27` 和唯一 `HostLeaseV27` 构成同生共灭三元组。三者在 host 内创建一次，直到 terminal；project Python 永不接触其 raw plan、consumer、approval 或可变 binding。

`LivePlanEnvelopeV27` 只能由 host-owned non-consuming pre-C 一次创建。它保留 C 所需的 raw output/patch material、已解析 capability 与 sealed execution identities；它不是从 review 字段、日志、IPC payload 或 client object 重建。host restart/generation change、envelope/lease/session loss、identity mismatch 均 terminal；旧 approval、handle和record不能复活或创建替代 envelope。

`ReviewRecordV27` 是 detached、canonical、**non-reconstructive** identity witness：仅包含 hash/length、canonical identity/provenance、ordered field digest 和审计必要 non-secret literals；不包含 JSON/Markdown/patch raw bytes、callable/capability material、secret、envelope contents或任何可用于创建替代 plan 的 payload。它显式绑定 `host_generation_id`、`host_session_id`、`live_plan_id`、`live_plan_digest`、`host_lease_id` 和 `binding_digest`。

## 2. Session-bound approval attestation

只有独立 orchestration→host attestation channel 可 mint 并提交 canonical `ReviewApprovalV27`；project client IPC 没有 approval operation，也不能提交等价字段。attestation 必须精确覆盖：

`{gate, formal_root, child_gitlink, review_record_digest, host_generation_id, host_session_id, live_plan_id, live_plan_digest, host_lease_id, binding_digest, approval_nonce, approval_counter}`。

`approval_nonce` 由 host 对每个 newly-created live session 一次生成；`approval_counter` 固定为该 session 的唯一零到一 transition。host 只接受 exact current generation/session/envelope/lease/binding 的一份 attestation，并在 acceptance 时永久消费 nonce。任何 prior-session、prior-generation、different binding、duplicate nonce、counter mismatch、restart/loss或新 Create 均拒绝；新的 session 必须重新 non-consuming pre-C、重新审计、独立 review 与新的 attestation。

## 3. 原子 one-shot 状态机

host 为每个 session 持有单一串行 event loop/lock，状态唯一为：

`PENDING_REVIEW -> APPROVED -> CONSUMING -> TERMINAL`。

- 只有合法 `ReviewApprovalV27` 能作 `PENDING_REVIEW -> APPROVED`；
- 第一个 exact lease/handle 的 resume 在同一 host critical section 内原子完成 `APPROVED -> CONSUMING`，在任何 freshness、consumer或readback 前消耗 admission；
- 同时、pipelined、replayed、foreign或第二个 resume 只能观察 `CONSUMING`/`TERMINAL` 并零 freshness/consumer/apply 返回；
- 仅 `CONSUMING` 内执行 `freshness -> one host opaque apply -> host byte verify`；成功、STALE/UNKNOWN、consumer reject/throw、readback mismatch、IPC failure、host failure都直接进入 `TERMINAL`，绝无回到 APPROVED 或 retry。

状态转换与 terminal reason 仅保留在 host 私有状态中。client audit 只能得到 detached status/digest，不能借此制造 resume capability。

## 4. 许可的后续拆分

本设计获三方 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_HOST_OWNED_CONTINUATION_CPU_STATIC` 后，第一阶段仅可实现 stdlib fake-host protocol conformance：不得启动进程、socket、filesystem I/O、真实 consumer 或 apply_patch。测试必须覆盖每个 `ReviewRecordV27` 类别 drift、prior session/generation approval replay、duplicate/pipelined resume、每个 CONSUMING 失败分支，且总 apply 至多一、所有输家路径为零调用。

真实 Stage1Host OS identity、匿名继承 IPC、privileged attestation channel、real envelope/pre-C/consumer integration 需独立设计和新的三方 Gate；宿主隔离不可部署时 fail-close，不允许退回 V25 或同解释器模拟。

## 5. 禁止范围

本版本不修改 Local Memory 算法、Cosmos runtime、optimizer、data/cache或训练配置；不授权 host/IPC 实现、real pre-C/C、request pair、materialization/source-evidence、child、GPU、训练、评测或推理。

Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_HOST_OWNED_CONTINUATION_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
