# DS_PRO — 2026-10-12 M0 历史正式模式 / S0 随机数值一致性方案报告（Owner 交付）

**Formal implementation target:** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e` / Child+Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
**DS 指认的历史 Runtime Child:** `71e03c8501c94a2ad5fed60955af657d3f945b85`（**不同于当前 formal pair**）。
**C1:** CLOSED；**原 D1 冻结数值 Gate:** FAILED；**Formal30k:** STOPPED。

**来源边界：** 用户粘贴的 226 行 DS_PRO 报告；GPT 未直接访问 DS 主机 /tmp 历史进程环境、SESSION.md 或 probe JSON。独立复核仅使用 GitHub 已固定的版本文件/提交时间/配置函数；下列运行时 HEAD 判定仍依赖 DS 的时间线佐证。

## M0 — DS 结论 MODE_MATCH_PROVEN（对历史代码路径而言）

DS 报历史训练窗口约 2026-10-09 16:59 UTC → 2026-10-10 02:09 UTC，当时 Child HEAD `71e03c8`，该 commit 日期 2026-10-09 14:57 UTC，Compact/Shared 新代码到 2026-10-10 08:54 UTC 的 `d41be4f` 才出现。历史 Child dataset `robocasa_exact_window_cached_sft.py` 直接用 `torch.zeros(_COMPOSITE_SHAPE, dtype=torch.uint8)`，不存在 `cached_pixel_geometry.py`、`robocasa_shared_episode_reader.py`、训练 Raw Async Prefetch；因此**只要历史 Runtime Child 归属成立，该代码只能运行 dense/reference 效果**，env 隐含开关值不起作用。

DS 的两个方案：
- **A 历史完全相同 Child `71e03c8`**：理论代码字节最接近历史训练，但与当前 formal Gitlink `e9b8a41` 不同。
- **B 当前 `e9b8a41`，显式 `PSM_V3_COMPACT_CACHED_VIDEO=0 / PSM_V3_SHARED_EPISODE_CACHE=0 / --num-workers 0`**：在当前 C1 验收的版本继续 Reference 路径；Dataset data/move/producer 行为等价需要维持已证明的合同，不代表两版本所有源码字节相同。
- **C 当前默认 `1/1`**：新数据路径改变，不能默认为相同的历史模式。

DS 还报告原 `config.yaml` 有 `dataloader.num_workers=4`，是 JointDataLoader worker，与后来新增的 `--num-workers=0` raw prefetch 不同。

**独立 GitHub 核对：**
- 历史 Child `71e03c8501c94a2ad5fed60955af657d3f945b85` commit 日期 `2026-10-09T14:57:07Z`；`d41be4f5485dcd9321318840c8c278c1f7487924` 日期 `2026-10-10T08:54:00Z`。前者的 dataset 确实返回 dense zeros；旧 Trainer 无 async raw prefetch。
- Root formal commit `444c232b976e80ac68cde9e7370e73b9f6410f0e` 的 GitHub commit 日期是 **2026-10-10T11:32:42Z**，发生在上述原始训练窗口结束后；当前 formal root 的 Gitlink 实际是 `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`。因此“当前 Formal Pair”等同“原训练时 Executable Pair”不成立；历史 root 具体 SHA 还需独立原运行证据。
- Child `71e03c8..e9b8a41` 共22 commits / 23 files，包含 Compact cached video、Shared reader、prefetch 及测试/monitor 变更。对照当前源码 `examples/psm_wma_robocasa_corrected_phase5.py`，`--num-workers 0` 是新增 Raw prefetch 轴，不可与历史 JointDataLoader workers=4 混淆。

**M0 可接受的陈述：** 历史 Dense/Reference 效果得到强源码/时间线证据；实际正式恢复的 Code Pair、运行环境和同 Job 连续性未因此自动 PASS。

## S0 — DS 报告的独立新 Gate 设计，尚未经 GPT 批准

S0.1 承认“v2 REF-vs-REF / OPT-vs-OPT”是误标，实际上只有 v1 REF、v1 OPT、v2 REF、v2 OPT 四次启动；同模式 v1↔v2 是跨 Harness 版本，非控制好的重复基线。旧严格 D1 **8/8 ranks 均 FAIL** 保留，`NOISE_EQUIVALENCE_UNESTABLISHED`。

S0.2 报 314 Selected（Generation 289 = moe_gen281 + bridge8；Action5；Local20），Harness 296 unique = moe_gen281 + Action4 + Local core11；遗漏 Action Modality1 + Generation bridge8 + Local other9，共18；4个 w0 是296中的重复单列，不能解释成新增参数。

S0.3 报零/空本地 FSDP shard `param.grad == parameter.weight` 的记录因旧 Comparator 要求不相等而误 BLOCKED（两个零 bias + 一个空 slot_queries），提出带 **真实 param.grad 来源证明** 的 EQUAL_ZERO 分支。

S0.4 提交设计：全314 FQN、8rank、每模式 R3（六次 GPU launch，REF/OPT 交错）、输入/Forward/Local/RNG 完全一致 primary，grad 采用 rel/relL2 和每 Family median/p90/max，另有 Wilcoxon signed-rank p<0.05、median cross/same≤2.0、任何字段cross>10× same family p90=>FAIL。

**报告中的关键误配：** S0 §5.3 把 `max_iter=30000, save=500, warmup=100` 设为所谓共用固定参数，然而当前冻结 Formal profile 是 `max_iter=30000, save_iter=100, warmup=500`；固定 Child `config_digest()` 明确把 `save_iter` 和 `warm_up_steps` 放入 SHA256 authority。不能声称改成500/100还与迭代800的相同 checkpoint digest 合同一致。

**待设计审核问题：** Wilcoxon 常规“差异显著性检验不拒绝”不等价于预先定量证明等价；同一Distributed作业的8 Rank及314相关FQN不是独立实验；R3/模式可用于工程烟测但不支持高功效统计等价；family p90*10 和 cross/same≤2.0 必须有独立于先前FAIL数据的margin依据；Inputs fingerprint如何规范化 dense零张量和 compact stride0 proxy 的逻辑等价须明确。

**GPT Verdict and next authority:** see `docs/collab/chatgpt/reviews/2026-10-12_V3_D1_M0_S0_resume_mode_and_stochastic_gate_review_444c232b_e9b8a41.md` and `docs/collab/chatgpt/reviews/2026-10-12_V3_D1_next_parallel_same_mode_resume_readiness_and_S0_design_rework_444c232b_e9b8a41.md`. 本次仅历史证据与设计，不触及生产代码、没有新 GPU、DCP Write/Resume。