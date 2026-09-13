# PSM-WMA Local Memory v0.3.5 单卡 Smoke Execution Request 设计 v0.1

**日期**：2026-09-13
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-EXECUTION-REQUEST-DESIGN`
**前置 formal pair**：root `5053ed40065bfa0b8e1d755756b0565bd2d5ef31` / child `93a89ba61306d840a008813f62f26a34d54850f4`

## 1. 目的与禁止范围

本文件只冻结 future receipt-bound single-GPU smoke execution request 的 canonical JSON
模板、填充时机、bind-before-read admission、审批边界和验证规则。它不创建 request，
不读取 receipt/source/checkpoint/manifest/data/cache，不探测 GPU，也不启动任何命令。

本 Gate 的批准只允许根据已闭合 source-evidence receipt 准备一份具体 request 并三方审核；
不授权该 request 的创建或执行、真实 I/O、child/runtime/config 修改、GPU/CUDA/torchrun、
训练、评测、推理、LIBERO4IN1、checkpoint 写入或 formal training。

## 2. Request 仅在 receipt 闭环后可被实例化

实例化前必须已完成 immutable collection/receipt、controlled write、source-evidence
record/receipt、publication materializer/verifier 和 read-only root audit。该闭环缺任一项，
唯一结果为 `BLOCKED_AUTHORITY_NOT_CLOSED`；不得预填、猜测或从工作树发现任何值。

future request 的 authority object 必须从已审 post-commit receipt 的 Git blob lookup 直接
导出，不接受 CLI、环境、路径、caller digest 或缓存副本：

```text
receipt_root_revision, receipt_path, receipt_blob_native_oid,
immutable_source_identifier, source_manifest_sha256, source_input_sha256,
checkpoint_source_descriptor_sha256, canonical_model_config_sha256,
root_revision, child_gitlink
```

所有十个值与 receipt canonical bytes、root tree 和 child Gitlink exact match 才可继续；
任何 mismatch 是 `AUTHORITY_DRIFT`，不可就地更新或重试。

## 3. Canonical request schema

request 的顶层 exact key set 为：

```text
schema_version, authority_tuple, request_id, request_sha256,
output_root, cuda_visible_device, max_steps, resolved_config_path,
command, environment_allowlist, fixed_runtime, expected_artifacts,
terminal_taxonomy, approvals
```

`fixed_runtime` 必须精确包含并固定：

```text
world_size=1, torchrun=false, num_workers=0,
resume=false, sidecar_resume=false, checkpoint_write=false,
evaluation=false, inference=false, B_stream=8, ttt_tbptt_steps=16,
K_local=1, local_state_feature=false, local_dt_feature=false,
local_age_feature=false, fast_state_dtype="fp32", inner_compute_dtype="fp32"
```

`max_steps` 必须为 1..100 的整数；`output_root` 必须在 admission 前不存在且显式标为
smoke-only；`cuda_visible_device` 只能标识一个设备。request 必须以 canonical JSON bytes
计算 `request_sha256`，其自身 hash 字段以 hash-excluding-self canonical projection 计算。

## 4. Command 与 preflight bind order

`command` 是 argv array，不是 shell string。其唯一 grammar 是：

```text
<approved-python> -m <approved-single-gpu-smoke-entrypoint>
--execution-request <absolute-request-json>
--authority-receipt-root <receipt_root_revision>
--authority-receipt-path <receipt_path>
--output-root <output_root>
```

interpreter、cwd、entrypoint、allowlisted environment 和 resolved config 只能由对应已审
root/child source audit 的 exact source identity 导出。含 shell、glob、命令替换、
`torchrun`、RANK、WORLD_SIZE 非 1、多 GPU、resume、sidecar、checkpoint save/load、eval 或
inference 的 request 必须在读取真实输入前 reject。

preflight 顺序固定为：receipt/root/child/blob binding → request canonical hash → output-root
nonexistence/write allowlist → fixed-runtime/config/inventory binding → one-GPU environment record →
才可授权后续独立 execution review。此 Gate 不允许走到最后一步。

## 5. 终态与验收

execution request 必须继承 runbook 的终态 ABI：`PASS|FAIL|BLOCKED|MANUAL_STOP`；后三者
必须对应 `failure.json`，并携带冻结 key set、request/authority digest 与最后 committed
transaction identity。expected artifacts 限于已批准 runbook 的七个 output-root 内路径。

本设计的 PASS 仅证明 future request 的字段、来源和 admission 顺序被充分冻结；它不证明
receipt 已存在、不证明 GPU 可用，也不授权任何执行。

## 6. 审核请求

请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_SINGLE_GPU_SMOKE_EXECUTION_REQUEST_INSTANCE
```

或 `REQUEST_CHANGES(file:line)`。批准只允许新建并审核一个 receipt-bound request instance；
不允许创建或执行该实例。
