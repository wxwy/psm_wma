# PSM-WMA Local Memory v0.3.5 Canonical Segment Supersession Source Audit v0.1

**日期**：2026-09-10
**状态**：docs-only source audit；待三方审核；不授权代码、真实 I/O、GPU、训练、评测或推理
**任务/Gate**：`G0-R09-B-TTT-V035-CANONICAL-SEGMENT-SUPERSESSION-SOURCE-AUDIT`
**审计源码快照（非 canonical authority）**：root `ee07ca057afd203f8d58821051c0cfa6298e78ee` / child `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`

## 1. Authority 与结论

本文件仅将 `PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md` §20.2 的 A--H 未落地项映射到当前源码。v0.3.5 §12、§18 明确 supersede 旧 row-wise active-wiring 的生产训练语义；刚关闭的 active-wiring Gate 仍是 synthetic CPU/static contract，不是 v0.3.5 segment production authority。

历史 `PSM-WMA_Local_Memory_v0.3.5_supersession_migration_design_v0.1.md` 已被 ChatGPT review `2026-09-08_R09_B_TTT_v035_migration_design_a882b12_0fddc27f.md` 标记 superseded，禁止重开。唯一可继承的 canonical CPU/static authority 是以下不可变 formal chain：

| 阶段 | formal root | child/Gitlink | 唯一文档/结论 |
|---|---|---|---|
| canonical semantics design | `e4b2d2f980ce0f038ae1a44ed379d16bbf05b9d9` | `80aec090688e3c710c41e1dfd86b6500773db2c7` | v0.3.9 canonical training/runtime contract |
| canonical CPU/static implementation design | `1f6c0bad0faa4aabae1c71b01738ad95a4ea902c` | `80aec090688e3c710c41e1dfd86b6500773db2c7` | `docs/build/PSM-WMA_Local_Memory_v0.3.9_cpu_static_implementation_design_v0.3.md` |
| canonical CPU/static implementation closure | `d1f155d9a0cf0cf49055c065defa8119b0ac178f` | `333792e845fe3b15ba4d8af8f34f704de2a79fa2` | canonical synthetic core 已关闭 |

上方 `ee07ca0/f14a8d8` 仅是本 audit 核对旧/过渡源码的快照，绝不替代该 canonical chain。不得重新定义 `SegmentBatch`、`scan_segment_masked_many()`、feature-disable inventory、scheduler 或 GA retry 语义。

## 2. 当前源码事实

| 主题 | 当前事实 | 与 v0.3.5 的关系 |
|---|---|---|
| 旧生产入口 | `omni_mot_model.py::_ttt_local_memory_tokens` 逐 sample 调用 `TTTLifecycle.process_sample()` | 旧 `1 row/microbatch` 路线，不能作为新 segment production adapter 扩展 |
| active 入口 | `_run_active_local_memory_native_forward()` fail-closed | 正确阻止 test seam 误入生产；不能直接填入旧 row-wise adapter |
| canonical core | `local_memory_segment.py::SegmentBatch`、`local_evidence.py::scan_segment_masked_many()` | 是新路线唯一可继承的 synthetic core，仍未接真实 Cosmos consumer |
| feature disable | canonical `EvidenceFeatureConfig(state=False, dt=False, age=False)` 已有 CPU/static 语义 | production construction/config 尚未绑定，禁止以 zero tensor 代替 |
| loss/GA | `ImaginaireTrainer.training_step()` 仍按 native single-loss accumulation | 尚未有 planned valid-count 或 v0.3.5 weighted loss seam |
| checkpoint | slow-only contract存在；runtime stream ownership sidecar不存在 | 首轮 GPU smoke可声明 mid-episode resume unsupported；正式长训必须另起 sidecar Gate |

## 3. A--H 处置与后续 Gate

| v0.3.5 缺口 | 结论 | 必须由哪个新 Gate 冻结 |
|---|---|---|
| A variable valid gather | 当前 native packer 未证明可将 stream-major valid rows gather 成真实 variable consumer batch | `CANONICAL-SEGMENT-PRODUCTION-ADAPTER-DESIGN` |
| B native loss reduction | `_compute_losses()` 是 native reduction authority；必须取得 per-consumer/等价 valid mean 证据后才能 scale | 同上 |
| C planned `N_valid_window` | scheduler 必须在 tensor load 前产出 GA-window metadata；现有 owner未提供 | `SEGMENT-SCHEDULER-AND-GA-METADATA-DESIGN` |
| D weighted scheduler state | 需冻结 exposure、seed、queue epoch/permutation、slot/cursor/provenance | 同上 |
| E feature disable production binding | 只能 construction-time canonical encoder；需与 config/optimizer inventory单独绑定 | `CANONICAL-FEATURE-CONFIG-PRODUCTION-BINDING-DESIGN` |
| F old authority migration | 保留 identity/provenance/fail-close，不得保留 witness graph/row lifecycle | `CANONICAL-SEGMENT-PRODUCTION-ADAPTER-DESIGN` |
| G GPU budget | 只在 adapter + GA seam CPU/static closure后，单列显存/higher-order smoke design | `CANONICAL-SINGLE-GPU-SMOKE-DESIGN` |
| H runtime sidecar | 正式训练前独立保存 slot/cursor/W_fast/queue RNG/checkpoint identity | `RUNTIME-SIDECAR-RESUME-DESIGN` |

## 4. 强制顺序

1. 审核本 audit；只授权创建下一个 design，不授权 child 代码。
2. 冻结 scheduler/GA metadata 与 production adapter design；其 CPU/static implementation 必须先闭合 stream-major flatten/gather、valid-weight loss、per-stream scan、backward 后 commit、异常 fail-close。
3. 冻结并实现 feature-config production binding；不得混入 producer/packer 或真实 cache I/O。
4. 仅在上述 CPU/static closure 后，单独审核 single-GPU canonical smoke（`B_stream=8,T=16,K_local=1,no-state/no-dt/no-age,fp32 W_fast`）。
5. GPU smoke 通过后，单独审核 LIBERO4IN1 latent-cache matched smoke；正式训练另有命令/输入/停止条件 Gate。
6. runtime sidecar 是正式长训而非首轮 smoke前置条件；多卡与 exact resume均不得搭车进入单卡 Gate。

## 5. 审核请求与禁止范围

请求唯一 verdict：`APPROVE_TO_CREATE_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCTION_DESIGN` 或 `REQUEST_CHANGES(file:line)`。

本 audit 不授权修改 `cosmos-framework`、dataset/producer/packer/manifest/config/optimizer-selector/checkpoint，亦不授权真实数据/cache/checkpoint I/O、CUDA/GPU、torchrun、训练、评测、推理或 LIBERO4IN1。若上游 v0.3.5 被新版本 supersede，本 audit 必须新建版本并重新审核。
