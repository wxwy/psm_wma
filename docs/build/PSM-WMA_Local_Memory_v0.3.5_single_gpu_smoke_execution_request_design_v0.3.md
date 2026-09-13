# PSM-WMA Local Memory v0.3.5 单卡 Smoke Execution Request 设计 v0.3

**状态**：docs-only；待三方审核。  
**Gate**：`G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-EXECUTION-REQUEST-DESIGN`

本文件仅替代 v0.2 的 `approvals` 与后续 instance-construction 输入授权条款；v0.2 其余 ABI、
runbook §3 的 v2 supersession 范围、单卡限制、终态 ABI 和禁止范围继续有效。

## 1. 无环 request ABI

`approvals` 的精确 key set 改为 `design_authority_root, design_authority_child,
design_verdict`，且三值仅绑定本设计 Gate 已完成的前序设计 authority；它们在 instance 创建前已存在。
不得把 instance 的 reviewer identity、final verdict 或 review locator 写入 request。`request_sha256`
仍为删除自身字段后的 canonical JSON SHA-256。

instance 的三方最终 review receipt 必须是 request 外部的 append-only canonical review/ledger 条目，
精确键为 `request_sha256, formal_root, formal_child, reviewer, verdict, evidence_locator`；其只引用
immutable request SHA，绝不回写 request。因此 instance 先冻结 request/hash/formal pair，后审核，
无自引用循环。

## 2. 后续 construction Gate 的唯一读取授权

在 receipt 闭环已完成后，后续独立 `INSTANCE-CONSTRUCTION-AND-REVIEW` Gate 仅可只读 Git blob
lookup 该已发布 receipt，并只读核验 receipt blob、root tree 与 child Gitlink identity，以导出
`authority_tuple`。此授权不包括 source、checkpoint、manifest、data、cache payload 或任何运行时配置
读取；不允许 GPU/CUDA、torchrun、训练、评测、推理、instance 执行、child 修改或 checkpoint 写入。

## 3. 审核请求

请求 `APPROVE_TO_DESIGN_R09_B_TTT_V035_SINGLE_GPU_SMOKE_EXECUTION_REQUEST_INSTANCE`，或
`REQUEST_CHANGES(file:line)`。批准仅允许后续独立 construction-and-review Gate 依上述只读范围
创建一份 instance 并重新审核，仍不执行。
