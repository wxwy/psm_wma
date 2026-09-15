# Stage-1 v1.7 request-instance recovery design v1.9

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V19`。
**状态**：仅 docs-only recovery；v1.8 唯一 C 已消费，零 request pair 输出，禁止重试或补写。

## 不可复用的 v1.8 C 事实

在 v1.8 same-pair 三方批准后，P0/P1 纯内存复核通过，C 在第一项 freshness observation 前开始。全部冻结观察、canonical JSON/Markdown producer、line witness 和 `patch_raw -> strict UTF-8 patch_text` handoff 均在内存完成；唯一 consumer 以仅含六个冻结键的环境调用名称 `apply_patch` 时，系统返回 `FileNotFoundError: [Errno 2] No such file or directory: 'apply_patch'`。没有执行第二个 consumer、没有重试；两条 designated v0.4 输出路径随后均实测 absent。

因此 v1.8 C 已按 one-shot/no-retry 永久消费。该失败不是权限扩大理由，不得把宿主 PATH、未冻结可执行路径、工具 API 句柄或人工复制的 patch 内容当作补救 consumer。

## 唯一 future recovery 条件

未来若重新申请 construction authority，设计必须在 C 前把 consumer 作为显式、可验证的 injected capability，而不是由 shell PATH 名称解析：冻结 consumer 的 invocation ABI、输入为 producer 的同一 `patch_text` object、成功/失败 result schema、无额外 filesystem/network/Git 行为，以及不可用时的 P0/P1 前 fail-close probe。该 probe 必须在 C 开始前完成，且不能读取 future output paths、`.git`、environment、refs 或 remote。

新设计还必须明确：若项目治理要求只能使用 orchestration-level `apply_patch` 工具而非可执行文件，C 需要由同一受控 orchestration call 保持 opaque producer handoff；在该 handoff ABI 被静态证明前，禁止重新授权 construction。不得以 shell redirection、Python write、temporary file、stdout/context reconstruction 或 ambient PATH 替代。

本版不创建 v0.4 pair，不授权 materialization/retry、launcher/materializer、真实 source/checkpoint/manifest/data/cache I/O、collection/receipt/record/publication、child/runtime/config mutation、GPU/CUDA/torchrun、训练、评测、推理或 LIBERO4IN1。

Requested verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE_CONSUMER_RECOVERY` or `REQUEST_CHANGES(file:line)`.
