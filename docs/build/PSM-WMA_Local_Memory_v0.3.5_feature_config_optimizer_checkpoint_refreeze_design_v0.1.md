# PSM-WMA Local Memory v0.3.5 Feature / Config / Optimizer / Checkpoint Refreeze Design v0.1

**日期**：2026-09-11

**状态**：docs-only design；待 ChatGPT、MM、Kimi 对同一 root/child SHA 审核。

**前置 Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-RUNTIME-CPU-STATIC-IMPLEMENTATION` 已关闭。

**当前技术基线**：root `35de2eceb1e93bed7e9b618b727f23edcbb420d5`；child `d96406e3b273d35e328c88142b36ef2eae895d2c`。

## 1. 目的、authority 与边界

本设计把 v0.3.5 的 canonical Local Memory 慢参数、配置 identity、optimizer membership 和 slow-only checkpoint 合同冻结为下一 CPU/static Gate 的唯一对象。数学/chronology 以 `PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md` §1、§2、§10--§13、§20 为准；canonical native runtime CPU/static closure 仅证明 typed scheduler/adapter/dispatcher contract，不代表下述生产配置或 checkpoint 已实现。

本设计显式 supersede `PSM-WMA_R09_B_TTT_v032_config_optimizer_checkpoint_design_v0.2_2026-09-04.md` 中的 `local_history_runtime.encoder/recurrent_backend` owner 与四 selector。它们是旧 recurrent backend 口径，不得作为 v0.3.5 TTT authority。

本 Gate 只允许后续创建 CPU/static implementation design。现在及下个实现 Gate 均不授权真实 data/cache/checkpoint I/O、CUDA/GPU、torchrun、active public runtime、optimizer step、sidecar、训练、评测、推理或 LIBERO4IN1。

## 2. v0.3.5 frozen config identity

首轮 identity 必须包含并 strict-validate：

| 字段 | 固定/允许值 | 语义 |
| --- | --- | --- |
| `ttt_tbptt_steps` | 正整数，默认 `16` | 单 microbatch 的 graph 上限，非 history horizon、非 GA。 |
| `ttt_inner_lr` | 有限正标量，默认 `0.1` | 每 step K/V write 的 inner update rate。 |
| `k_local` | 正整数，首轮固定 `1` | Memory Prefix token 数；`4/8` 必须独立增量 Gate。 |
| `local_evidence_feature_version` | 精确 `causal_visual96_executed_action10_v1` | 只启用 visual summary 96 + executed action 10；state/dt/age 均关闭。 |
| `local_fast_state_dtype` | 精确 `fp32` | runtime `W_fast` numeric carrier dtype。 |
| `local_runtime_resume_mode` | 精确 `slow_only_no_mid_episode_resume` | first smoke 不支持 exact mid-episode resume。 |

未知字段、bool 冒充数值、非有限/非正值、旧 `runtime_evidence_steps`、与上述固定值不符的 feature/dtype/resume 值均 fail closed。`k_local != 1` 不得由旧 `{1,4,8}` 宽放行而静默进入首轮 smoke。

identity 的 canonical serialization 必须是稳定、显式字段名/值的版本化 mapping；checkpoint 恢复时缺失、额外或任一值漂移一律 strict failure，不得默认、迁移或 warm-start。

## 3. 唯一 registered slow owner 与精确 inventory

实现必须只注册一个 Local root module（本设计称 `local_memory_runtime`）；它持有且 runtime adapter 实际引用同一 Python 对象：

```text
local_memory_runtime.evidence_encoder
local_memory_runtime.ttt_core
local_memory2llm
local_memory_modality_embed
```

`ttt_core` 必须拥有 learned `W_bar_0`、`theta_K`、`theta_V`、`theta_Q` 与 slot-query bank；任何别名、adapter copy、lazy second instance 或旧 `recurrent_backend` trainable 副本均 fail closed。`local_memory2llm` 的逐 token input width 必须精确为 `32`、输出 width 为 `2048`；`k_local` 个 readout 必须保留为 `k_local` 个 token，禁止拼成一个 `k_local * 32` token。modality embed 是一个 `2048`-width token bias。

canonical slow inventory 是该 root 的 `named_parameters()` 与 projector/modality 参数的逐名字典。验收必须证明：runtime references 与 registered objects 均 `is` 相同；键名唯一、无遗漏/额外；全部预期参数 `requires_grad=True`；所有 runtime-only `W_fast`、frontier、pending request/capability、scheduler queues、cursor/epoch、recovery receipt 不在 inventory。

## 4. Optimizer selector 与 slow/fast 生命周期

optimizer 只允许从 canonical inventory 精确选择以下四前缀：

```text
local_memory_runtime.evidence_encoder.
local_memory_runtime.ttt_core.
local_memory2llm.
local_memory_modality_embed
```

selector 必须 exact-cover inventory，交集为空；遗漏、重复、顺序交换导致的 parameter-object 差异、宽前缀捕获旧 Local module、或参数非 trainable均拒绝。`W_fast` 永远不能进入 optimizer group 或 `state_dict` slow parameter set。

仅 outer task loss 对这些 slow 参数产生梯度；inner loss 不加到 outer loss。每一个 canonical member 仅按已冻结的 `planned_n_valid/N_window * consumer_loss + auxiliary/GA_effective` 产生一次 scaler/backward；后续实际 runtime Gate 才能接触真实 optimizer step。step 更新 slow parameters 后，已存在的 numeric runtime `W_fast` 不得变化；fresh episode 才 clone 当时最新 `W_bar_0`。

## 5. Slow checkpoint / restore contract

slow checkpoint payload 必须包含：versioned config identity、exact canonical slow inventory tensors、optimizer state、scheduler state、global optimizer iteration，以及其对应 base-model checkpoint identity。实现 Gate 只允许 in-memory CPU serialization/round-trip fixture；不得触发 filesystem/DCP/remote checkpoint I/O。

恢复必须同时验证：payload key set、shape、dtype、config identity、base-model identity、optimizer group membership 和 iterator identity。任一缺失、额外、重复、shape/dtype/config drift、foreign owner、stale selector 或 runtime-state 键都 strict fail closed。成功恢复后 runtime adapter 仍必须指向被恢复的 exact registered objects。

以下不属于 slow checkpoint，且 first smoke 禁止声称恢复：`W_fast`、frontier、stream ownership、episode/category/cursor、queue RNG/permutation、pending capability、partial graph/grad、suffix recovery state。正式训练前若要求 exact mid-episode resume，必须另起 runtime-sidecar Gate，并且只允许在所有 member 已 backward、fast state 已 detach/commit 的安全边界保存。

## 6. 后续 CPU/static implementation design 的最小白名单与验收

下一 design 只能指定当前 config/checkpoint contract 与相邻测试、model config schema，以及 model registration/selector 的最小文件。不得以“refreeze”为名接通 public runtime hard-stop、packer、producer、trainer optimizer step、真实 checkpoint backend 或 dataset。

至少需要下列 synthetic CPU assertions：

1. 默认 identity 逐字段等于 §2，所有非法/旧/漂移值 fail closed；serialization deterministic。
2. `k_local=1` 的 core/encoder/projector/modality registered object identity 与 runtime adapter reference 完全相同，inventory 精确且无旧 recurrent owner。
3. selector exact-cover 四组；遗漏、重叠、foreign/duplicate/dormant parameter 均拒绝。
4. `W_bar_0/theta_K/V/Q/slot query` 在 inventory；`W_fast/frontier/pending` 不在 inventory 且不能加入 optimizer。
5. CPU memory round-trip 后 tensor、config、optimizer-group membership 和 runtime object identity一致；任一 key/shape/dtype/config/base identity drift strict reject。
6. `W_fast`/cursor/pending/recovery key 若试图写入 slow payload立即拒绝；没有 sidecar 不得伪造 mid-episode resume。

## 7. Verdict 请求与后续 Gate

请只对本 docs-only design 给出 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。批准仅允许新建并审核上述 CPU/static implementation design；真实 checkpoint I/O、GPU smoke、runtime sidecar、optimizer activation、训练或 LIBERO4IN1 必须由后续独立三方同 SHA Gate 授权。
