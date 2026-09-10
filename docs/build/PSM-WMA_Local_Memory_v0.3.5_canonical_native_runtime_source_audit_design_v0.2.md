# PSM-WMA Local Memory v0.3.5 Canonical Native Runtime Source-Audit 设计 v0.2

**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-RUNTIME-SOURCE-AUDIT-DESIGN`
**状态**：docs-only remediation；待新 SHA 三方审核；不授权实现或执行

本版 supersede v0.1 的 §3--§5，仅修复 ChatGPT review 的 HIGH-1/2；其余范围、formal child 基线
`c0e6e55cbab00b7d40eccacc0de1c4c91b66f9d9` 与禁止范围不变。

## 1. 不可变审计边界

审计只读当前 child source，保持 v0.3.5 的 S0/PAD/stream-major/past-only 合同，以及
v0.3.6--v0.3.9 的 immutable plan、suffix-only recovery、fast commit retain 与 partial slow-grad discard。
不改 child/config/checkpoint/data/cache；不运行项目代码、真实 I/O、GPU、torchrun、训练或推理。

## 2. 必答 source/ABI 地图

审计必须逐项记录 `file:line -> 唯一 owner -> fail-closed`：

1. model seam、legacy Local isolation、packer/flatten 的 payload order、多 vision/action/sound cardinality、`[B,K_local,2048]` prefix、S0 absent、PAD exclusion；
2. native loss 的 weighted population、sample scale、LBL auxiliary 与 `N/K_m` owner；
3. 每个 normal 或 suffix-recovery plan 的 `planned_N_valid[mu]`、`actual_N_valid[mu]`、其 pre-backward `actual==planned` 检查，及 `N_window=sum(planned_N_valid)`；
4. **primary** 的唯一系数 `planned_N_valid[mu] / N_window`，和 **auxiliary** 的唯一系数 `1 / GA_effective`；normal plan `GA_effective=GA`，recovery plan `GA_effective=len(recovery.members)`，两者不得合并为比值 shorthand；
5. 在上述 objective 形成后才发生的 GradScaler scale/unscale、optimizer/LR scheduler、zero-grad、DDP no-sync 边界；拒绝任何第二次 `/grad_accum_iter` 或第二次 GA scaling。full-valid normal case 必须还原 native `(L_consumer + L_aux)/GA`；
6. producer/cache 到 carrier 的 exact identity，含 LIBERO4IN1 manifest/config/source digest、episode/cursor/terminal、raw visual/action evidence；
7. feature flags/dims、exact canonical slow/trainable parameter inventory、optimizer membership、checkpoint config/manifest/source identity 与 old-checkpoint fail-closed owner；
8. checkpoint save/load、rank ownership、sidecar schema/restore seam。无 sidecar 时首轮 smoke 必须显式 mid-episode resume unsupported，不能声称 resume/distributed supported。

任一 owner 缺失、caller guessed、重复缩放、identity 缺失、legacy Local 不可隔离或 old checkpoint 非 fail-closed，均为 `REQUEST_CHANGES(file:line)`。

## 3. 唯一后续顺序

`APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_RUNTIME_IMPLEMENTATION` 只授权下一份 docs-only implementation design。继承的完整顺序不得弱化：

```text
runtime implementation design -> CPU/static implementation
-> feature/config/optimizer/checkpoint refreeze
-> single-GPU smoke design/approval -> single-GPU smoke
-> runtime-sidecar design -> CPU/static verification -> resume smoke
-> LIBERO4IN1 matched-smoke design/approval -> matched smoke
-> formal-training design/command approval -> formal training
```

若需不同顺序，必须先有独立 superseding contract。任何批准不授权 child、真实 I/O、GPU smoke、matched smoke 或训练。

## 4. 验收

仅验证 docs source-map 要求、明确 verdict 与 `file:line` fail-closed 分流及 root `git diff --check`；不执行项目代码。
