# PSM-WMA Local Memory v0.3.5 Feature / Config / Optimizer / Checkpoint CPU/static Implementation Design v0.1

**日期**：2026-09-11

**状态**：docs-only implementation design；待同 SHA 三方审核。

**前置 authority**：`PSM-WMA_Local_Memory_v0.3.5_feature_config_optimizer_checkpoint_refreeze_design_v0.1.md`，及其 v0.2 remediation；formal root=`ca08bebfaec0e63beee653fcbc3997ecee7fb476`、child/Gitlink=`d96406e3b273d35e328c88142b36ef2eae895d2c` 的 ChatGPT、MM、Kimi 一致 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_CPU_STATIC`。

## 1. 目的与不变边界

本文件只把已冻结的 v0.3.5 config identity、唯一 slow owner、selector/inventory 与 slow-only restore contract 落到一个**后续可审核**的 child CPU/static 实现白名单。它不实现或解除任何 production hard-stop；不读取/写入 checkpoint 文件，不连接 DCP/remote storage，不创建训练 dataloader，不进行 native forward/loss/backward、optimizer/scheduler step、CUDA/GPU、torchrun、sidecar、训练、评测、推理或 LIBERO4IN1。

第一实现只能使用构造在内存中的小型 `nn.Module`/tensor/optimizer/scheduler fixture。fixture 不是 `OmniMoTModel.training_step()`、不是 checkpoint backend，也不得借由 monkeypatch 将 public path 标为已实现。

## 2. 精确 child 白名单与迁移点

后续 implementation commit 只能修改以下六个 child 文件：

1. `cosmos_framework/model/generator/mot/config_checkpoint_contract.py`；
2. `cosmos_framework/model/generator/mot/config_checkpoint_contract_test.py`；
3. `cosmos_framework/configs/base/defaults/model_config.py`；
4. `cosmos_framework/model/generator/omni_mot_model.py`；
5. `cosmos_framework/model/generator/omni_mot_model_test.py`；
6. `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py`，仅用于既有 core concrete-key inventory 的静态交叉断言。

不得修改 `local_evidence.py`、runtime authority/adapter/scheduler、packer、producer、trainer、checkpoint backend、recipe、数据或测试基础设施。若第 4 项静态注册迁移需要修改白名单外文件，必须停止并新建设计 Gate，不能扩展本白名单。

`omni_mot_model.py:390-428` 的 active-TTT 静态注册在本 Gate 迁移为唯一 registered root `net.local_memory_runtime`，其精确 children 是 `evidence_encoder` 和 `ttt_core`；adapter 只可引用这两个同一对象。旧 `net.local_history_runtime`、`recurrent_backend` 和 `StatelessLocalReplayReadout` 不得作为 active-TTT 的 trainable owner、selector target 或 second Local copy。此变更不得触发 public canonical segment forward；现有 public hard-stop 与 disabled-first 行为保持不变。

## 3. Frozen config identity

`LocalMemoryConfig` 与 `OmniMoTModelConfig` 的 CPU/static identity 仅包含下列字段：

| field | required first-rollout value/validation |
| --- | --- |
| `ttt_tbptt_steps` | positive non-bool integer; default `16` |
| `ttt_inner_lr` | finite positive non-bool scalar; default `0.1` |
| `k_local` | exactly non-bool integer `1` |
| `local_evidence_feature_version` | exactly `causal_visual96_executed_action10_v1` |
| `local_fast_state_dtype` | exactly `fp32` |
| `local_runtime_resume_mode` | exactly `slow_only_no_mid_episode_resume` |

旧 `runtime_evidence_steps`、`k_local in {4,8}`、implicit defaults、unknown/missing keys、bool masquerading as numeric values，以及 noncanonical feature/dtype/resume values全部 fail closed。identity serialization 是带 version 的稳定 mapping；恢复时 exact key/value match，不作 migration/warm-start。

## 4. Canonical owner、inventory 与 selector

实现只允许一份 registered `local_memory_runtime`；其 evidence/core object 与 canonical adapter 持有者均必须 `is` 相同。slow inventory 的唯一键空间为：

```text
local_memory_runtime.evidence_encoder.*
local_memory_runtime.ttt_core.w0_fast_in_weight
local_memory_runtime.ttt_core.w0_fast_in_bias
local_memory_runtime.ttt_core.w0_fast_out_weight
local_memory_runtime.ttt_core.w0_fast_out_bias
local_memory_runtime.ttt_core.key_proj.weight
local_memory_runtime.ttt_core.key_proj.bias
local_memory_runtime.ttt_core.query_proj.weight
local_memory_runtime.ttt_core.query_proj.bias
local_memory_runtime.ttt_core.value_proj.weight
local_memory_runtime.ttt_core.value_proj.bias
local_memory_runtime.ttt_core.slot_queries
local_memory2llm.*
local_memory_modality_embed
```

`local_memory2llm` 必须保持逐 token `32 -> 2048`；K 个 readout 仍是 K 个 token。selector 仅按四个 frozen prefixes exact-cover 上述 inventory：`local_memory_runtime.evidence_encoder.`、`local_memory_runtime.ttt_core.`、`local_memory2llm.`、`local_memory_modality_embed`。任何遗漏、重叠、alias、non-trainable、foreign 或 legacy key 都拒绝。

`ContinualTTTFastState`、frontier、pending scan/native/commit/retry/suffix authority、transaction/receipt、cursor、queue/RNG、partial graph/grad 均不是 registered parameter、optimizer member 或 slow payload key。名字含 `fast` 的四个 `w0_fast_*` 相反是 slow seed parameter，必须存在于 inventory。

## 5. In-memory payload 与 preflight-first restore

payload 仅为 in-memory versioned mapping：config identity、base-model identity、ordered exact slow tensors、optimizer state/group schema、scheduler state/schema 和 global iteration/resume identity。严禁 filesystem、DCP、remote I/O 或 sidecar。

`strict_restore_into()` 的唯一允许顺序：

```text
decode/stage clone
  -> validate payload type/key set/config/base/inventory/tensor shape+dtype
  -> validate optimizer parameter-object/groups + staged state
  -> validate scheduler + iteration identity
  -> validate fresh/quiescent runtime admission
  -> copy into existing registered objects exactly once
```

所有 fallible checks 必须在第一项 live mutation 前完成；禁止创建/替换 root/module/parameter；禁止 post-mutation rollback 作为替代方案。reject 后 parameter bytes、optimizer group/state、scheduler、iteration、registered object identities 与 runtime authority 都必须不变。

admission 只接受 fresh/quiescent adapter：任何 committed `W_fast` frontier、pending scan/native/commit/retry/suffix capability、open transaction/recovery receipt 或 pre-restore nonterminal runtime authority，均在 mutation 前拒绝；不得 clear/rebind/destroy 以规避。成功时 adapter/frontier 为空，且仍 `is`-bound 到已恢复的 encoder/core；只有之后 fresh episode 才能 clone restored W-bar-0。

## 6. Direct CPU/static acceptance matrix

后续实现必须新增/替换以下直接 tests：

1. config defaults + deterministic serialization；每项 legacy/unknown/missing/drift/bool invalid input fail closed；
2. static active-TTT registration 的 root/children 与 canonical adapter exact object identity；无 legacy registered owner/readout alias；
3. concrete inventory 等于 §4，四 selector exact-cover；重复、遗漏、foreign、legacy、non-trainable 和 alias 均拒绝；
4. four `w0_fast_*`、K/Q/V、slot and evidence/projector/modality 都在 slow payload/selector，`ContinualTTTFastState`/frontier/pending 都不在；
5. valid in-memory round trip 保持 tensors、base/config identity、optimizer group/state、scheduler、iteration 与 object identities；
6. tensor/config 合法但**晚** optimizer/scheduler/owner defect 的 payload 在第一 mutation 前拒绝，并逐对象证明零 mutation；
7. 每类 live runtime authority 均使 restore pre-mutation reject、slow/runtime snapshots不变；fresh/quiescent success 后 adapter empty 且 binding exact；
8. payload 出现任何 runtime/sidecar key 立即拒绝，且没有 test 声称支持 mid-episode resume；
9. public canonical marker/hard-stop 的既有 disable-first test 保持通过；本 Gate 不调用 native forward/loss/backward 或 optimizer step。

必须运行仅这三个定向 CPU/static test 文件、改动文件 Ruff、目标 `py_compile`、child/root `git diff --check`。测试输出不得被描述为真实 checkpoint 或训练证据。

## 7. 提交、审核与停止条件

实现前，先提交本设计并取得 ChatGPT、MM、Kimi 对同一 formal root/child SHA 的 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_CPU_STATIC`。任一 `REQUEST_CHANGES`、SHA 不同或缺一方时停止在 `REVIEW`，不得修改 child。

即使随后 implementation closure 通过，仍只关闭 CPU/static refreeze；真实 checkpoint I/O、optimizer activation、GPU smoke、runtime sidecar 和 LIBERO4IN1 训练各需独立后续 Gate。
