# PSM-WMA Local Memory v0.3.5 单卡 Smoke Execution Request 设计 v0.2

**日期**：2026-09-13
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-EXECUTION-REQUEST-DESIGN`
**前置 formal pair**：root `5053ed40065bfa0b8e1d755756b0565bd2d5ef31` / child `93a89ba61306d840a008813f62f26a34d54850f4`

## 1. 目的、版本关系与禁止范围

本文件是 v0.1 的整改版，只冻结 future receipt-bound single-GPU smoke execution
request 的 canonical JSON 模板、填充前置、bind-before-read admission、审批边界和验证规则。
它不创建 request，不读取 receipt/source/checkpoint/manifest/data/cache，不探测 GPU，也不启动命令。

本文件的 §3 以 `schema_version="psm-wma.single-gpu-smoke-request.v2"` **显式替代且仅替代**
`PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_execution_runbook_design_v0.1.md` §3 的
request 精确 key-set 条款；后者的 §1--2、§4--8（尤其 authority tuple、不可 shell 命令语义、
single-GPU/no-torchrun、1..100 步、write allowlist、terminal ABI 和 PASS/FAIL 语义）仍逐字控制。
因此 future instance 只有本文件 §3 所定义的一种 canonical request ABI；不得同时接受或生成
runbook v0.1 §3 的旧扁平 schema。

本 Gate 的批准仍是 **design-only**：它只授权后续独立
`INSTANCE-CONSTRUCTION-AND-REVIEW` Gate 在 source-evidence receipt 已闭环后创建且审核恰好一份
instance；不授权本 Gate 创建该文件，更不授权执行。任何阶段均不授权真实 I/O、child/runtime/config
修改、GPU/CUDA/torchrun、训练、评测、推理、LIBERO4IN1、checkpoint 写入或 formal training。

## 2. Request 仅在 receipt 闭环后可实例化

实例化前必须已完成 immutable collection/receipt、controlled write、source-evidence
record/receipt、publication materializer/verifier 和 read-only root audit。闭环缺任一项，
instance Gate 的唯一结果为 `BLOCKED_AUTHORITY_NOT_CLOSED`；不得预填、猜测或从工作树发现值。

`authority_tuple` 必须由已审 post-commit receipt 的 Git blob lookup 直接导出，精确 key set 为：

```text
receipt_root_revision, receipt_path, receipt_blob_native_oid,
immutable_source_identifier, source_manifest_sha256, source_input_sha256,
checkpoint_source_descriptor_sha256, canonical_model_config_sha256,
root_revision, child_gitlink
```

所有十个值必须与 receipt canonical bytes、root tree 和 child Gitlink exact match；任何 mismatch
为 `AUTHORITY_DRIFT`，不可用 CLI、环境、路径、caller digest、缓存或就地更新修复。

## 3. 唯一 canonical request ABI（v2）

request 是 canonical UTF-8 JSON object，顶层精确 key set 为：

```text
schema_version, authority_tuple, request_id, request_sha256,
output_root, cuda_visible_device, max_steps, resolved_config_path,
command, environment_allowlist, fixed_runtime, expected_artifacts,
terminal_taxonomy, approvals
```

不得有其他顶层键。`schema_version` 必须为
`"psm-wma.single-gpu-smoke-request.v2"`；`request_id` 是单次 instance 的稳定、非空字符串；
`request_sha256` 是删除该字段后，对其余 canonical JSON bytes 的 SHA-256。`output_root` 必须是
admission 前不存在的绝对 smoke-only 路径；`cuda_visible_device` 必须标识恰好一个设备；
`max_steps` 是 `1 <= max_steps <= 100` 的整数。

`fixed_runtime` 的精确 key set 与固定值为：

```text
world_size=1, launcher="python", torchrun=false, num_workers=0,
resume=false, sidecar_resume=false, checkpoint_write=false,
evaluation=false, inference=false, B_stream=8, ttt_tbptt_steps=16,
K_local=1, local_state_feature=false, local_dt_feature=false,
local_age_feature=false, fast_state_dtype="fp32", inner_compute_dtype="fp32"
```

`command` 是唯一 argv array：

```text
<approved-python> -m <approved-single-gpu-smoke-entrypoint>
--execution-request <absolute-request-json>
--authority-receipt-root <receipt_root_revision>
--authority-receipt-path <receipt_path>
--output-root <output_root>
```

它不是 shell string，不能含 shell、glob、命令替换、`torchrun`、RANK、非 1 的 WORLD_SIZE、
多 GPU、resume、sidecar、checkpoint save/load、eval 或 inference。`environment_allowlist` 仅列出
由已审 exact source identity 导出的键值；`command` 的 interpreter、cwd 与 entrypoint 同样只能由该
source identity 导出。

`expected_artifacts` 的精确集合为 runbook §6 的七个 output-root 相对路径；
`terminal_taxonomy` 的精确有序集合为 `PASS, FAIL, BLOCKED, MANUAL_STOP`；`approvals` 必须精确
携带本 instance Gate 的 formal root/child、三方 reviewer identity、同 pair final verdict 与 review
evidence locator。任一未知键、缺键、类型错误、固定值偏离或 canonical/self-hash 不匹配均在读取
任何真实输入前 reject。

## 4. Bind order、终态与下一 Gate

instance 的 preflight 顺序固定为：receipt/root/child/blob binding → request canonical hash →
output-root nonexistence/write allowlist → fixed-runtime/config/inventory binding → one-GPU environment
record → 才能请求独立 execution review。不得在本 Gate 或 instance 审核中走到最后一步。

终态 ABI 继续继承 runbook：`PASS|FAIL|BLOCKED|MANUAL_STOP`；后三者必须有同 status 的
`failure.json`，并带冻结 key set、request/authority digest 与最后 committed transaction identity。
本设计通过只证明 ABI/来源/准入的唯一性；它不证明 receipt 已存在、GPU 可用或可执行。

本文件获三方批准后，只可进入一个独立的 instance-construction-and-review Gate：该 Gate 在 receipt
闭环后创建一份且仅一份符合 §3 的 request，并对该 exact instance 重新三方审核；它仍不授权执行、
GPU、训练或读取 request 以外的真实输入。该 Gate 未批准前，禁止创建任何 request instance。

## 5. 审核请求

请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_SINGLE_GPU_SMOKE_EXECUTION_REQUEST_INSTANCE
```

或 `REQUEST_CHANGES(file:line)`。批准只允许上述后续 instance construction-and-review Gate，
不允许在本 Gate 创建或执行 instance。
