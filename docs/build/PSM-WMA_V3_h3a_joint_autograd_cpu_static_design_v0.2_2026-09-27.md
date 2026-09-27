# PSM-WMA V3 H3-A — 联合 autograd CPU/static 设计 v0.2

- 日期：2026-09-27。
- 本版覆盖 `post_b2c_to_h100_gate_sequence_v0.1` 中已过时的“等待 run04”硬停点；B2-C 已依据 run06 实证关闭，见 `PSM-WMA_V3_stage_b2c_run06_closure_2026-09-27.md`。
- 责任：cx 为技术 owner、实现和 CPU 验证；ds 负责后续 GPU 执行验证；ChatGPT 为用户不定期激活的非在线审核者。本设计只授权 H3-A CPU/static 实现，不授权 H3-B/C/D/E、GPU 或正式训练。

## 目标与不变量

证明同一个 native policy outer loss 经 Local K/V-only Memory Prefix，以普通 autograd 同时更新 Edge generation/action host 参数和完整 Local slow 参数。冻结 T=16、K=4、local_dim=32、evidence_dim=256、ttt_dim=64、fast_hidden=256、inner_lr=0.1、raw15、chunk32/33-frame。Local inner loss 仅服务 fast-state candidate，不进入 outer objective。

4090 的 `SingleSegmentNativeGradientRelay` 保持独立，只用于 host 冻结的单卡 smoke；H100 路径禁止 prefix `detach()`、leaf 替代、手动梯度 relay、`no_grad` 或 `inference_mode` 截断。H3-A 不引入 optimizer step、sidecar commit 或 GA 二次缩放，这些属于 H3-C。

## 精确接线

1. 复用 `CanonicalLocalMemorySegmentAdapter.scan`，传入 production `model.net.local_memory_runtime.encoder/core` 同一实例，以及注册过的 `model.net.scan_local_memory`。B0 的 strict identity、S0 缺席、e(t-1) 和 pending transaction 保持权威。
2. 对一个单 slot、T16 `SegmentBatch`，按 `SegmentScanResult.payloads/locals` 的顺序调用 native callback；每次将原始 graph-connected prefix 作为 `OmniMoTModel.training_step(..., _local_memory_prefixes=(prefix,))` 私有输入。S0 传 `None`。`training_step` 经 `attach_local_prefixes`、`build_memory_prefix_context` 和 two-way attention 的 K/V seam 产生原生 flow outer loss。
3. H3-A 只构造一个单 member 平均 outer loss，调用方一次 `backward()`；不做 optimizer/GA/commit。发生回调异常或无效 loss，丢弃 pending candidate，live sidecar/frontier 不变。成功 backward 后同样先丢弃测试事务；生产发布顺序由 H3-C 实现。
4. host trainable inventory 为现有 Edge generation/action 范围：`moe_gen`、`time_embedder`、`vae2llm`、`llm2vae`、`action2llm`、`llm2action`、`action_modality_embed`，再加完整 `local_memory` namespace。reasoner 和其余 host 参数冻结。H3-A CPU 测试可用小型 representative host 模块检验梯度；正式完整 inventory、FSDP 和多 rank 数值由 H3-C/E 检验。

## 最小文件与验收

- child 仅新增 `cosmos_framework/model/generator/mot/local_memory_joint_segment.py` 与 `_test.py`；现有 B0、B2-A、B2-B 与 4090 harness 不改。若 private native seam 已满足，则不改 Cosmos 核心。
- CPU fixture 固定 T16/raw15：S0 prefix=None，其余 15 个 prefix 为同一未 detach 的 scan 图输出；对包含两路 host 参数与完整 Local 165312 slow 参数的 differentiable native attention loss，一次 backward 后 host 与 Local 代表梯度 finite/nonzero，全部 Local slow 参数都有 finite 梯度；fast state 不在 optimizer/named parameters。
- 与独立直接 scan + 原生注意力 outer loss 的数值梯度参考比较；现有 B2-B 测试已单独覆盖 host 冻结时的 relay 等价性。禁止 callback 自带的额外 inner/reconstruction loss、重复 `/GA`。异常路径证实 sidecar/frontier 不变。
- V3 venv targeted pytest、相关 Local CPU 回归、Ruff check/format、两仓 `git diff --check` PASS；不运行 GPU，不宣称正式 native Edge 全模型运行通过。

## 后续 Gate

H3-B 冻结 grouped persistent RoboCasa producer；H3-C 接入 trainer/optimizer/GA 和 commit-after-success；H3-D 做严格 checkpoint/resume；H3-E 由 ds 执行 8×H100 短跑、梯度/资源/恢复证据；H3-F 再冻结正式训练命令。没有 H3-E 的真实证据，不启动长训练。
