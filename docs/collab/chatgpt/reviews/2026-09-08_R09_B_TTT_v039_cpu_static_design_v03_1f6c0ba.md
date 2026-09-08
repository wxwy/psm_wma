# ChatGPT 独立审核 — canonical CPU/static implementation design v0.3

日期：2026-09-08

## Verdict / formal target

**APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_STATIC**

- Gate：`G0-R09-B-TTT-V035-CANONICAL-CPU-IMPLEMENTATION-DESIGN`
- Formal root design SHA：`1f6c0bad0faa4aabae1c71b01738ad95a4ea902c`
- Verified child/Gitlink：`80aec090688e3c710c41e1dfd86b6500773db2c7`
- Review-start V2 HEAD：`a7d667af213f1d06570350bb565436c99de8d8a1`，为 request/bookkeeping；不改变 formal pair。
- Previous formal target：`3e63a0d74f10326b6c5d514f5cfca32a689303be` / same child。

## 增量结论

上一轮唯一 HIGH **CLOSED**。

v0.3 明确取消并禁止 `SegmentEvidenceEncoder`，将 canonical-route evidence encoder authority 收回既有 `LocalEvidenceEncoder`。`EvidenceFeatureConfig` 同样定义在 `local_evidence.py`；legacy 默认配置保持当前旧 route 的模块树、forward signature、参数/缓冲区、数值与错误行为，canonical `state=False/dt=False/age=False` construction 则物理不注册 disabled branches，并给出准确 trainable inventory。这与 frozen v0.3.6 §7 要求的 `LocalEvidenceEncoder` construction-time feature-disable authority 一致，不再存在 parallel encoder authority。

v0.3 同时冻结 canonical `encode_segment(visual_summary, executed_action)` 两输入路径；canonical instance 若经 legacy forward 收到 state/dt/age 任一 disabled tensor，须在读取/shape-check/projection 前 fail closed。CPU acceptance 直接验证 legacy regression、canonical inventory、disabled tensor 不创建/不传递/不读取以及 fail-closed 行为。

v0.2 已关闭事项继续有效且未被本版改写：invalid-first `scan_segment_masked_many()`、opaque `consumer_payload` common gather、current Gate exact literal、rank-local scheduler/GA/retry transaction 与 production boundary。当前 child 未变化；实际旧 `scan_segment_many()` 仍在 projection 后才依据 valid 分支，因此新 route 必须继续使用已冻结的 masked seam，不能回退旧入口。

当前 blockers：**none**。

## Scope

本 verdict 只授权 v0.3 §1 精确四文件白名单内的 synthetic CPU/static implementation：

- `cosmos_framework/model/generator/mot/local_memory_segment.py`
- `cosmos_framework/model/generator/mot/local_evidence.py`
- `cosmos_framework/model/generator/mot/local_memory_segment_test.py`
- `cosmos_framework/model/generator/mot/local_evidence_test.py`

不授权 dataset/trainer、production adapter/model forward、`local_memory2llm`、config/optimizer/checkpoint、manifest、`ttt_lifecycle.py`，也不授权真实 model/data/cache/checkpoint I/O、CUDA/GPU/torchrun、训练、评测、推理、preflight/staging/record/refreeze/export/compose、P4/P5、B2-T、LIBERO4IN1 或后续 Gate。

这是 implementation-design approval，不是 implementation closure。白名单实现形成新的 formal root/child pair 后必须 fresh review，旧 verdict 不继承。
