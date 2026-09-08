# PSM-WMA Local Memory v0.3.9 CPU/static implementation design v0.2

**日期**：2026-09-08
**状态**：docs-only remediation；待三方同 SHA 审核；未授权代码、GPU、真实 I/O 或训练
**前置批准**：canonical contract v0.3.9，formal root `e4b2d2f980ce0f038ae1a44ed379d16bbf05b9d9` / Gitlink `80aec090688e3c710c41e1dfd86b6500773db2c7`
**取代范围**：本文件 supersede `PSM-WMA_Local_Memory_v0.3.9_cpu_static_implementation_design_v0.1.md`；v0.1 仅保留审核历史，不构成实现授权。

## 1. 唯一目标、授权 literal 与精确白名单

本 Gate 只把 v0.3.6--v0.3.9 的合同落实为**可隔离的 synthetic CPU core**。它不接入真实
`B2ManifestAwareIterableDataset`、Cosmos model forward、native payload adapter、trainer loop 或
checkpoint；这些接缝将在后续独立 design Gate 冻结。旧
`TTTLifecycle.process_sample()` 的 row-wise/closing-replay/materialize 路线不属于新 route。

仅在获得同一 formal root/Gitlink 三方 literal
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_STATIC` 后，才可修改下列 child 文件：

```text
cosmos_framework/model/generator/mot/local_memory_segment.py       # 新：本 Gate 所有新 public types/helpers
cosmos_framework/model/generator/mot/local_evidence.py             # 仅新增 masked core scan 与私有 row helpers
cosmos_framework/model/generator/mot/local_memory_segment_test.py  # 新：synthetic CPU tests
cosmos_framework/model/generator/mot/local_evidence_test.py        # masked scan tests
```

`local_memory_segment.py` 是 `SegmentBatch`、`SegmentProvenance`、`EvidenceFeatureConfig`、
`SegmentEvidenceEncoder`、`RankLocalSegmentScheduler`、`GAWindowPlan` 与 transaction helper 的唯一
承载文件；不得为它们另建未列名文件。不得修改 `LocalEvidenceEncoder`、
`action_sft_dataset.py`、`trainer/__init__.py`、`ttt_lifecycle.py`、production runtime adapter、
attention/model forward、config、optimizer/checkpoint、manifest builder/verifier 或
`local_memory2llm`。禁止真实 model/data/cache/checkpoint I/O、CUDA、torchrun、训练、评测和推理。

前置 semantics Gate 的 literal `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_DESIGN` 仅授权
创建本 implementation design；它绝不授权本节白名单代码。

## 2. `SegmentBatch`：shifted ABI、opaque payload 与共同 gather

新不可变 `SegmentBatch` 严格继承 v0.3.6 §2。`consumer_payload` 是 opaque 的 native condition/target
carrier，必须由未来 Cosmos adapter 保持其结构与所有权；本 Gate 的 synthetic double 使用带非平凡
identity/target 字段的不可变 payload，而不得以 action tensor 取代。其字段为：

```python
consumer_visual_summary: Tensor[B, T, 96]
consumer_payload: ConsumerPayloadGrid[B, T]  # opaque；每个 valid consumer 都有原位 payload
consumer_valid, evidence_valid: BoolTensor[B, T]
consumer_step, evidence_source_step: LongTensor[B, T]
evidence_visual_summary_prev: Tensor[B, T, 96]
evidence_executed_action_prev: Tensor[B, T, 10]
slot_id: LongTensor[B]
episode_id, category: tuple[str, ...]
segment_provenance: SegmentProvenance
```

`consumer_action` 不属于替代 ABI；若未来 native payload 含 action，它仍只由 payload authority 解释。
`validate()` fail-closes：`1 <= T <= ttt_tbptt_steps`；`evidence_source_step == -1` iff evidence invalid；
valid step0 必为 evidence absent；其余 valid row 必满足 source step 等于 consumer step 减一；PAD 的
payload/evidence storage 均不可读取。

canonical gather 先 stream-major flatten，再以同一个 `consumer_valid` index 同时 gather
`consumer_payload`、slot/episode/source identity 和 Local payload。S0 的 Local 为 Python `None`，其他
valid consumer 为 `[K_local, 32]`；PAD 从所有四个输出排除。synthetic round-trip 必须使用不同 payload
与 identity，证明 S0 保留、PAD 排除且 payload/Local/identity 不错位。

## 3. invalid-first masked core seam 与 feature-disable

现有 `ContinualTTTLocalMemoryCore.scan_segment_many()` 在 valid 判断前会对 dense batch 调用
`project_evidence()`，因此**不得**成为新 route 的调用入口。`local_evidence.py` 的唯一允许改动是新增
`scan_segment_masked_many()`，以及仅供它使用的私有 fast-state select/scatter row helpers。它在每个
timestep 按下列顺序运行：

1. 从 `valid[:, t]` 取得 valid row index；若为空，不访问 `evidence[:, t]`，不调用 encoder、有限性检查、
   K/Q/V projection、read 或 write，直接原样 carry fast state 并返回全 `False` present；
2. 若非空，仅 gather valid evidence 与其 fast-state rows；仅在这个紧凑子批上执行 finite check、
   `project_evidence()` 和 `step_projected_many(valid=True)`；
3. 仅 scatter valid rows 的 state/readout 回原 batch；invalid rows 的 committed fast-state bytes 必须逐字不变，
   输出 Local payload 为 absent，不得用零 token 代替。

旧 `scan_segment_many()`、`step_many()` 与其已有回归语义逐字不改。测试以 spy/counting core 或等价可观测
hook 直接观察 encoder、finite-check、K/Q/V projection、read/write 的参与 row；覆盖 mixed S0/PAD/valid 与
all-invalid timestep，并验证无效 payload 不访问且 state bytes 不变。

`EvidenceFeatureConfig(state=False, dt=False, age=False)` 与新的 `SegmentEvidenceEncoder` 都定义在
`local_memory_segment.py`；后者只注册 visual/action projection 与 LayerNorm，且 forward 不接受、读取或
合成 state/dt/age。既有 `LocalEvidenceEncoder` 完全不改，所有既有无参或单参调用继续走旧 route；因此本
Gate 的 feature-disable 只作用于新的 Local-Memory route，并由新 encoder parameter inventory 验证。

首轮仅 `K_local=1`。masked scan 输出 `[B,T,1,32]`，共同 gather 后再交给注入的
`PrefixProjector` protocol；测试可使用 synthetic `32 -> 2048` projector 并验证 `[N,1,2048]`，但本 Gate
不得修改或注册 production `local_memory2llm`，不得调用 model forward。

## 4. rank-local scheduler 与纯 Python transaction

`RankLocalSegmentScheduler` 仅消费 synthetic 已验证 metadata，不读取 dataset item；是 rank-local、
main-process、`num_workers=0` 语义的唯一 owner。它显式持有并在测试中序列化：rank、stable slot、
category/episode/cursor、target distribution、cumulative valid-consumer exposure、queue seed/epoch/
permutation、admission order、segment id 与 manifest/config/source digest。其 weighted-deficit admission
规则、target distribution 和 exposure 更新属于本 Gate；CPU fixture 必须验证 deterministic admission、
tail PAD、terminal/rebind、`training_stream_end` 与相同 snapshot 的重建一致性。

`GAWindowPlan` 与 transaction helper 同在该文件，且不接入 trainer。它冻结 members、planned counts、
`N_window`、`GA_effective`、attempt、plan-chain identity 与 suffix snapshot；只计算
`(N_valid/N_window) * L_consumer + (1/GA_effective) * L_aux`，并在任何 synthetic backward double 前断言
actual gathered count 等于 planned。此 Gate 不产生或缩放真实 trainer `loss`。

两类 scheduler 必须分离建模：successful backward 后的 episode scheduler fast chronology/cursor/exposure
commit 即使 GradScaler skip 也保留；`slow_lr_scheduler` 只在真实 slow optimizer step 成功时推进。synthetic
GradScaler-skip observation 必须确认：无 optimizer/LR step、slow grads 清除、且 episode chronology 不回滚。
failure 保留此前成功 fast commit、清 partial slow grads、无 optimizer/LR step、仅允许一次 suffix recovery；
attempt=1 任一 transient 都为 `LOCAL_MEM_RETRY_EXHAUSTED`，不执行余 member。

## 5. CPU acceptance 与后续接缝

必须 synthetic CPU PASS：shifted S0/previous-evidence ABI；mixed/all-invalid mask 的零 encoder/project/
read/write participation；PAD/no-token；payload/Local/identity gather round-trip；terminal reset 与
cross-segment carry；一次 write/K read；new-route feature-disabled parameter absence；multi-slot reject；
weighted-deficit snapshot/admission/exposure；planned==actual；full-valid objective parity；first/later
failure 与 A/B/C/D retry terminal；GradScaler-skip 两类 scheduler；`py_compile`、相关 pytest、child/root
`git diff --check`。

下一独立 Gate 才能设计 native payload adapter、dataset materialization、actual trainer pre-scaled loss seam、
production prefix projector/config/optimizer/checkpoint inventory 与 runtime sidecar。即使本 Gate 批准或 CPU
tests PASS，也不授权这些修改、真实 I/O、GPU 或 LIBERO4IN1 训练。
