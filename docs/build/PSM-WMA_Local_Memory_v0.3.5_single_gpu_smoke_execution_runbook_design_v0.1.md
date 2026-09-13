# PSM-WMA Local Memory v0.3.5 单卡 Smoke Execution Runbook 设计 v0.1

**日期**：2026-09-13
**状态**：docs-only；待三方审核。
**Gate**：`G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-EXECUTION-RUNBOOK-DESIGN`
**前置设计 formal pair**：root `e75c8c12c8573d445e91f2b9c9b4d95d98b1d5f8` / child `93a89ba61306d840a008813f62f26a34d54850f4`

## 1. 目的、唯一授权与禁止范围

本文件只冻结未来一次 canonical 单卡 Local Memory smoke 的 execution request/runbook
形状、准入、命令绑定、预检、产物、PASS/FAIL 与停止条件。它把已批准的
`PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_design_v0.1.md` 变成下一执行 Gate 可审核的
接口；它本身不执行命令，也不读取任何真实输入。

本 Gate 若获批准，只允许准备一份绑定真实 authority receipt 的 single-GPU smoke
execution request，并就该 request 另行三方审核。它不授权 source/checkpoint/manifest/data/cache
读取、immutable collection/receipt、source-evidence record/package/witness/publication、child 或
runtime/config 改动、GPU/CUDA、`torchrun`、训练、评测、推理、LIBERO4IN1 matched smoke、
runtime-sidecar、checkpoint 写入或正式训练。

## 2. 唯一前置 authority tuple

future execution request 必须逐字携带并在 launch 前从 Git object lookup 复验下列已审
source-evidence post-commit receipt tuple：

```text
receipt_root_revision
receipt_path
receipt_blob_native_oid
immutable_source_identifier
source_manifest_sha256
source_input_sha256
checkpoint_source_descriptor_sha256
canonical_model_config_sha256
root_revision
child_gitlink
```

request 中的 root tree、child Gitlink、receipt parent/tree/blob 与五项 digest 必须全部与
receipt 的 canonical bytes 相等。任一不同即 `AUTHORITY_DRIFT`，不得以当前工作树、路径重解、
caller digest、环境变量、软链接或“更新 receipt”修复。receipt 没有完成既有 immutable
collection → controlled write → source-evidence record/receipt → publication materializer/verifier →
read-only root audit 闭环时，本 request 只能给出 `BLOCKED_AUTHORITY_NOT_CLOSED`，不得启动 GPU。

## 3. 不可覆盖 smoke request schema

request 必须是 canonical JSON，精确 key set 如下；除 `max_steps`、`output_root`、
`cuda_visible_device` 与 authority tuple 的具体值外，任何值都不可覆盖：

```text
schema_version, authority_tuple, run_id, output_root, cuda_visible_device,
max_steps, world_size, launcher, num_workers, resume, sidecar_resume,
B_stream, ttt_tbptt_steps, K_local, local_state_feature,
local_dt_feature, local_age_feature, fast_state_dtype, inner_compute_dtype,
checkpoint_write, evaluation, inference, torchrun, resolved_config_path
```

固定值必须为：

```text
world_size=1; launcher="python"; torchrun=false; num_workers=0
resume=false; sidecar_resume=false; checkpoint_write=false
evaluation=false; inference=false
B_stream=8; ttt_tbptt_steps=16; K_local=1
local_state_feature=false; local_dt_feature=false; local_age_feature=false
fast_state_dtype="fp32"; inner_compute_dtype="fp32"
```

`max_steps` 是 `1 <= max_steps <= 100` 的整数；不得以配置 include、环境变量、CLI
override、resume sidecar 或 trainer default 改写以上字段。`output_root` 必须是此前不存在的
显式 smoke-only 目录，且每个允许写入的路径必须在其下。

## 4. 命令形状与环境约束

真实 execution request 必须将 interpreter、工作目录、完整 argv、环境 allowlist、authority
tuple 和 resolved config 的 SHA-256 逐字段写入 request；不得使用 shell、通配符、命令替换或
未记录的环境继承。命令的 frozen grammar 为：

```text
env -i <allowlisted-env>
<approved-python> -m <approved-single-gpu-smoke-entrypoint>
  --execution-request <absolute-request-json>
  --authority-receipt-root <receipt_root_revision>
  --authority-receipt-path <receipt_path>
  --output-root <new-output-root>
```

entrypoint、approved-python、工作目录和 allowlist 不在本设计猜测；它们只能由后续 request
从已审 current root/child source audit 的 exact native entrypoint 导出。request 必须拒绝含
`torchrun`、`RANK`、`WORLD_SIZE` 非 `1`、多 GPU 可见性、分布式初始化、resume、sidecar、
checkpoint save/load、eval 或 inference 的 argv/环境/config。CUDA 可见设备恰为一个，且
launch 前只读记录 driver、CUDA runtime、PyTorch、GPU name、总/空闲显存与 interpreter version；
设备缺失是 `BLOCKED_NO_SINGLE_GPU`，不得降级 CPU。

## 5. 预检与运行事务

启动前 preflight 的顺序不可改变：

1. 复验 §2 authority tuple、root/child identity、receipt blob 与 request JSON canonical digest；
2. 复验 output root 尚不存在，写入 allowlist 仅为 §6 的文件；
3. 解析 resolved config，逐项断言 §3 固定字段，且 strict checkpoint policy、Local parameter
   inventory、slow optimizer/scaler identity 均等于已审 native CPU/static contracts；
4. 只读记录 §4 single-GPU 环境，随后创建 output root；
5. 构造 immutable normal plan，先取得整个 GA window 的 `planned_N_valid`，再允许首次 backward。

运行必须采用 v0.3.5 canonical chronology：fresh `S0` 的 Local absent、`S_t` 只消费
`e_(t-1)` 更新后的 state、stream-major gather、`T=16` 仅为 TBPTT、segment 尾 detach 图而数值
carry、仅 episode done reset 至 learned `W_bar_0`、PAD 不更新不贡献 loss。每个 microbatch
backward 前必须断言 `planned_N_valid_mu == actual_gathered_consumer_count`。

若任一 microbatch/segment在 GA window 内发生 nonfinite、identity/count mismatch、OOM、CUDA error、
非法 Local/PAD token、跨 episode W leak、未声明写入、`world_size != 1`、resume 或超过批准步数，
立即停止：保留此前已提交 fast chronology/cursor/exposure，清空该 partial slow-gradient window，
不做该 window 的 optimizer/LR step，不重放/resample/重写已消费 chronology，也不得自动重跑。

## 6. 唯一允许产物及 schema

执行终态只可为 `PASS`、`FAIL`、`BLOCKED` 或 `MANUAL_STOP`；其中 `MANUAL_STOP` 是
独立的 non-PASS terminal status，不是未分类异常。执行成功或任一终态时只可在
`output_root` 写入：

```text
resolved_smoke_config.toml
authority_binding.json
environment.json
segment_chronology.jsonl
optimizer_scaler.jsonl
smoke_summary.json
failure.json                 # FAIL、BLOCKED 或 MANUAL_STOP 时必需
```

`failure.json` 的精确 key set 必须是 `schema_version`、`terminal_status`、`reason`、
`last_committed_transaction_identity`、`authority_tuple_sha256`、`request_sha256`；其
`terminal_status` 只能为 `FAIL`、`BLOCKED` 或 `MANUAL_STOP`，且与`smoke_summary.json.status`
一致。`authority_binding.json` 必须含 §2 全 tuple、request/config raw SHA-256、actual root/child/receipt
lookup 值和 exact command digest。`segment_chronology.jsonl` 每段必须含 stream/episode identity、
consumer index range、S0 status、evidence range、planned/actual valid count、PAD count、fast state
commit/disposition。`optimizer_scaler.jsonl` 必须含每个 GA window 的 planned denominator、actual
count、finite/GradScaler disposition、slow-step 是否发生及原因；没有 native scaler 时写
`not-applicable`，不得伪造 skip。各 JSON/JSONL schema 由 execution request 冻结并在启动前验证。

## 7. PASS、FAIL 与人工停止

`smoke_summary.json.status=PASS` 的必要充分条件是：authority、config、manifest、checkpoint binding
全一致；每个执行的 forward/inner update/native loss/backward/slow state 有限；fresh S0、shifted
evidence、stream-major gather、tail/PAD、commit 全满足 §5；planned/actual count 相等；发生至少一次
真实 slow optimizer boundary；没有 DDP/torchrun/sidecar/resume/eval/inference/checkpoint 写入；且所有
写入都在 output root。若 authority manifest 已证明无 tail，summary必须给出该证明引用；否则至少
记录一次 tail/PAD。

任一 FAIL 只保留最小 §6 证据，不扩大步数、不换输入、不改变配置、不自动恢复或重跑。PASS 不得声称
收敛、success rate、checkpoint reload、部署或正式训练完成；它只允许进入 runtime-sidecar
design/CPU-static/resume smoke Gate。操作者可在任何时刻人工停止；该终态必须令
`smoke_summary.json.status`和`failure.json.terminal_status`均为`MANUAL_STOP`，并写入最后已提交
transaction identity。它不得自动重跑、改写输入或被解释为 PASS、FAIL 或 BLOCKED。

## 8. 审核请求

本文件请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_SINGLE_GPU_SMOKE_EXECUTION_REQUEST
```

或 `REQUEST_CHANGES(file:line)`。批准只允许创建并审核绑定真实 receipt 的 execution request；
不授权其执行或任何 GPU/训练动作。
