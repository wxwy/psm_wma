# PSM-WMA Local Memory v0.3.9 CPU/static implementation design v0.1

**日期**：2026-09-08  
**状态**：待三方同 SHA 审核；仅 design，未授权代码、GPU、真实 I/O 或训练  
**前置批准**：canonical contract v0.3.9，root `e4b2d2f` / Gitlink `80aec09`

## 1. 范围与唯一目标

本设计把 v0.3.6--v0.3.9 转为下一步 CPU/static implementation 的最小白名单，且只允许
synthetic CPU doubles。它 supersede 旧 `TTTLifecycle.process_sample()` 的“一个 microbatch
一条 evidence + closing replay/materialize”生产路线；旧接口可保留给已关闭 Gate 的回归测试，
不得成为新 Local-Memory route 的 adapter。

本设计批准后才可实现以下文件：

```text
child/cosmos_framework/model/generator/mot/local_memory_segment.py       # 新
child/cosmos_framework/model/generator/mot/local_evidence.py              # feature-disable + batched scan seam
child/cosmos_framework/data/generator/action/datasets/action_sft_dataset.py # ordered source adapter only
child/cosmos_framework/trainer/__init__.py                                # explicit Local loss seam only
child/.../local_memory_segment_test.py                                    # 新 synthetic CPU tests
child/.../local_evidence_test.py, trainer/ttt_lifecycle_trainer_test.py   # 相邻 tests
```

不修改 `ttt_lifecycle.py`、production runtime adapter、Cosmos attention/model forward、config、
optimizer/checkpoint、manifest builder/verifier，且禁止真实 model/data/cache/checkpoint I/O、
CUDA、torchrun、训练/评测/推理。

## 2. SegmentBatch 与 source adapter

新 `local_memory_segment.py` 定义不可变 `SegmentBatch`，字段与 v0.3.6 §2 完全一致：

```python
consumer_visual_summary: Tensor[B,T,96]
consumer_action: Tensor[B,T,10]
consumer_valid, evidence_valid: BoolTensor[B,T]
consumer_step, evidence_source_step: LongTensor[B,T]
evidence_visual_summary_prev: Tensor[B,T,96]
evidence_executed_action_prev: Tensor[B,T,10]
slot_id: LongTensor[B]
episode_id, category: tuple[str, ...]
segment_provenance: SegmentProvenance
```

`SegmentBatch.validate()` fail-closes：`T in [1, ttt_tbptt_steps]`、`evidence_source_step==-1`
iff invalid、valid consumer step0 必为 evidence absent、其余 valid 必满足
`evidence_source_step=consumer_step-1`，PAD 不进入 evidence/read/loss。`B2ManifestAwareIterableDataset`
只提供已核验有序 source identity；新 `RankLocalSegmentScheduler(num_workers=0)` 是唯一 owner，
按 stable slot 生成 fresh step0、tail PAD、terminal/rebind 与 `training_stream_end`。旧
`_build_local_history()` 的 age/dt/history window 不得读取。

## 3. Core、feature 与 prefix seam

`EvidenceFeatureConfig(state=False, dt=False, age=False)` 使 `LocalEvidenceEncoder` 仅注册
visual/action projection 与 LayerNorm；disabled branches 的参数、forward arguments、optimizer
inventory 均不存在。新 segment seam 对 `evidence_valid` 行调用 encoder，按 `[B,T]` 调用现有
`ContinualTTTLocalMemoryCore.scan_segment_many()`，数值 fast state fp32；每 valid evidence
恰一次 K/V write，`K_local=1` 首轮。将 `[B,T,K,32]` gather 到 consumer rows；S0 为 Python
`None`，其余为 `[K,32]`，投影后才成为 `[N,K,2048]` Memory Prefix。不得伪造零 token。

graph 在 segment 末尾 detach，数值 state 跨同 episode segment carry；仅 terminal reset 到 learned
W0；没有 graph 跨 slow optimizer step。

## 4. Loss、GA transaction 与异常

新增 pure-Python `GAWindowPlan` / transaction helper（不接入 trainer loop）：冻结 ordered
identities、planned counts、`N_window`、`GA_effective`、attempt。它产出
`(N_valid/N_window)*L_consumer + (1/GA_effective)*L_aux`；actual gathered count 必须在 backward
前等于 planned。trainer 的未来 Local seam 接收已缩放 objective 并不得再 `/grad_accum_iter`；
disabled path 逐字保持当前 `loss/grad_accum_iter`。

helper 实现 v0.3.9：failure 保留已 commit fast chronology、清 partial slow grads、无 optimizer/
LR step、suffix-only recovery；一个 chain 仅一次 transient recovery，recovery 中任一 transient
为 `LOCAL_MEM_RETRY_EXHAUSTED`。本 Gate 仅测试 helper，绝不调用真实 `optimizer.step()`。

## 5. CPU acceptance

必须 synthetic CPU PASS：shifted S0/previous-evidence ABI、PAD/no-token、terminal reset 与
cross-segment carry、一次 write/K read、feature-disabled parameter absence、multi-slot reject
outside首轮、planned==actual、full-valid objective parity、first/later failure、A/B/C/D retry
terminal、GradScaler-skip modelled no-step、disabled path exact loss scaling。`py_compile`、相关
pytest、child/root `git diff --check` 必须通过。

## 6. 后续 Gate

本文件获三方同 SHA `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_DESIGN` 后，才允许
上述白名单的 CPU/static 实现；实现提交必须再次三方 closure 审核。真实 LIBERO4IN1、GPU 或
训练仍须独立 runtime/config/preflight/GPU Gate。
