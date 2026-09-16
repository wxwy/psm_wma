# Source-evidence closure request instance real-output execution design v0.1

**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-REQUEST-INSTANCE-REAL-OUTPUT-EXECUTION-DESIGN`

本 Gate 仅定义已批准的 memory-only constructor 如何在一次独立授权下写出 request instance pair；不授权本
次执行。输入必须是同轮冻结的 `ObservationBundle` 与已批准 CPU/static constructor，且 exact formal root/child
和 canonical instance SHA 在写入前重验。

## 固定输出与一次性事务

JSON 固定写入 `docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_closure_request_instance_v1.json`，
detached Markdown 固定写入同名 `.md`。preflight 必须证明两路径及 designated refs 均不存在、HEAD/index/worktree
snapshot 未变。构造器先在内存生成并验证 canonical JSON bytes，再以临时受控目录中的两个 staged bytes 完成
逐字节校验，最后以单次受控提交将 pair 发布到固定路径；不得覆盖、补写或 retry。

写后必须独立读取两个目标并验证：路径无 symlink、mode/owner 符合 allowlist、JSON canonical bytes 与 self-bound
SHA 一致、Markdown sibling 的 instance SHA 与 JSON 一致、目标仅包含本次 pair。任一失败保留 partial-residue
事实并进入 terminal `REAL_OUTPUT_WRITE_FAILED`，禁止清理性覆盖或重试。

## 边界

- 只允许修改构造模块、其 stdlib tests、TODO、SESSION 与本设计；source payload、record/publication、receipt-root、
  child/runtime、GPU/CUDA/torchrun、训练、评测和推理均不在本 Gate。
- real-output 执行必须另有 `APPROVE_TO_WRITE_SOURCE_EVIDENCE`；本设计审核只授权实现/审核执行方案，不授权写入。
- 成功写出 pair 后立即 hard stop，必须对 exact instance root/child/SHA 重新申请三方审核。

请求 verdict：`APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_REAL_OUTPUT_EXECUTION`
或 `REQUEST_CHANGES(file:line)`。
