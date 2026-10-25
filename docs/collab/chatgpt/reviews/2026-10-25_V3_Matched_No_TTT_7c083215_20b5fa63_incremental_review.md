# V3 Matched No-TTT Baseline — GPT 独立增量代码审核

日期：2026-10-25（CST）。
**FORMAL TECHNICAL VERDICT：`APPROVE` — 仅限精确 Root/Child 的 Matched No-TTT 生产代码及 CPU 作者 Evidence 增量审核。**
**DS_PRO 独立 CPU/S0 真实输入/GPU/真实训练/推理/Benchmark Gate 均未获本 verdict 关闭或运行授权。**

## 1. Formal target、来源、差异及 scope

- **Root formal implementation**：`7c083215e9f39ed4b5b3ff64010e415ad62dfdf4`（parent `48d1eb7f21f26be459bf78259d9678a8118e27c1`）。
- **Child/Gitlink formal**：`20b5fa639c405a515933da109529e3e2c04de88d`（parent `813a550dab5d6b5b5e3be90d38bb97527956b4dc`）。
- 上一经审核 Root/Child 基线：`fe9d537b4a5f82c8ea72a4f8ce182fdcefac6790` / `813a550dab5d6b5b5e3be90d38bb97527956b4dc`，原 Flexible Episode Resume Gate 的批准仅绑定旧 pair；本次新 Baseline 必须 fresh review。
- Author Evidence/docs HEAD `0f70fe8a6a58761b2d5c9c369627b001c08656a5`，**不是 formal implementation target**。取证时 V3 HEAD 为此 docs commit，无其他实现差异。
- Root source delta：新增 `scripts/train_v3_matched_no_ttt.sh`、`scripts/serve_v3_matched_no_ttt.py`、`configs/eval/robocasa_matched_no_ttt.example.yaml`、`tools/v3/matched_no_ttt_entry_test.py`、`docs/build/PSM-WMA_V3_Matched_No_TTT_training_runbook_v1.0_2026-10-25.md`；Root Gitlink更新，既有 G1 launcher、Unified Evaluation Queue、Vendor、模型/历史代码无修改。SESSION/TODO、后续 Evidence/Inbox 为 bookkeeping。
- Child delta：新增 `cosmos_framework/trainer/matched_no_ttt.py` +其测试、`examples/psm_wma_robocasa_matched_no_ttt.py` +其测试；对 `examples/psm_wma_robocasa_corrected_phase5.py`、`examples/psm_wma_robocasa_effective_config.py`、`cosmos_framework/utils/training_audit.py` 做受限 profile 接线。
- GitHub exact source tree 已直接核对 Root `cosmos-framework` Gitlink `20b5fa639c405a515933da109529e3e2c04de88d`，Child commit 为 `813a550dab5d6b5b5e3be90d38bb97527956b4dc` 的直接子提交。保护目录 `model/`、`data/`、`checkpoint/`、`inference/`、`simulation/`、第三方 Vendor、G1 standalone launcher 未改。

## 2. Matched 数据、Forward/Backward 与参数边界

### 2.1 Consumer / Source — PASS (code-level)

- `examples/psm_wma_robocasa_corrected_phase5.py` 的新 `--no-ttt` 路径仍调用相同 `VerifiedExactWindowIndex`、`RoboCasaExactWindowCacheCatalog`、`get_action_robocasa_exact_window_cached_sft_dataset`、`ExactWindowLocalCatalog`、`ExactWindowRankPlanner`、`ExactWindowSegmentProducer`。实际源必须仍满足 cache/source/index receipt 绑定。
- `cosmos_framework/trainer/matched_no_ttt.py:33-94,202-328`：逐GA member使用同一 Planner `members`、相同 Producer `produce(request)`、原生 `collate_grouped_native_batch` 与 `move_cached_native_batch`，保持 B=8、T=16、GA=2、world=8 和有效 Consumer 的 slot-major次序，拒绝非法 segment provenance/step/valid mask/Local token。终止部分窗口仍用真实有效数量，不伪造固定128。
- 唯一 intentionally removed step 是 Local `adapter.scan`、Inner Loss/Fast Weights/Prefix生成；其余产出 same native Consumer payload。没有把 `T=16` 错当为 No-TTT Inner-loop。
- `MatchedNoTTTTrainer.training_step` 调用 `model_ddp.training_step(batch,iteration)` 而非私有 `_local_memory_prefixes`；Outer loss 使用 `loss * len(payloads) / window.plan.n_window`，与 G1 的 rank-local valid-consumer归一化一致，无额外GA固定除法。原 action/vision/auxiliary native scalar由Model提供，不人工重算。
- 新 `matched_no_ttt_test.py:82-116` 使用实际 G1 `GroupedLocalMemoryWindow` 对照满量和末尾partial的Consumer顺序、weighted loss、Generation toy梯度及前沿提交；`:280-307` 验证随机Transform/source消费顺序。此为直接 CPU contract Evidence，**不是**同一次真实 GPU 训练中的数值/数据完全相等。

### 2.2 Model / Optimizer / LR — PASS (code-level)

- `examples/psm_wma_robocasa_corrected_phase5.py:750-798` 保留 G1 `overlay_local_config` 共有配置后，在模型实例化前将 `model.local_memory_enabled=False`、Trainer改为 `MatchedNoTTTTrainer`，Optimizer keys改为原七个 `GENERATION_KEYS`；Action头 LR multiplier=5.0、base LR=5e-5、schedule30000/warmup500/save100及 Grad Accum=2 不变。
- `cosmos_framework/trainer/matched_no_ttt.py:24-31` 强制不存在任何 `local_memory` 命名参数或 `net.local_memory_runtime/local_memory2llm/local_memory_modality_embed`；原训练入口在真实 optimizer 创建后验证 Generation-only参数选集、可训练性与没有未选择的参数在训练。
- 单独测试通过真实小型 Cosmos network 构造 `local_memory_enabled=False`，将 `LocalMemoryRuntime` 替换为一调用即失败的桩，证明不会构造 Local 模块，同时保留 action/vision投影。真实 Edge权重加载与world8 FSDP仍为后续 Gate。

### 2.3 Frontier / Checkpoint / Lifecycle — PASS (CPU contract，实际DCP未证明)

- `NoTTTFrontierCallback` 独占 `dataloader` checkpoint component；写入格式 `psm_v3_matched_no_ttt_frontier_v1`，保留真实 frontier、committed iteration、rank/world/seed/B/T/GA、cache/source/config hash。Resume只接受完全匹配schema、rank、source和下一segment counters；G1 Local sidecar/fast state无法当作No-TTT frontier。
- `MatchedNoTTTWindow.finish` 仅在GA2全部 backward和一次成功 optimizer step后提交前沿；非有限loss/gradient、optimizer-step skip、异常/中断会置失败状态，禁止下一次消费与 checkpoint假完成。CPU test覆盖指定错误注入及模型/Optimizer/Scheduler/Consumer toy roundtrip。
- 继续继承已审的 `JobLifecycle` 独立 output-root/job namespace、完整训练语义摘要校验、rank原状态/RNG、F0租约与F1已提交边界。新 `--no-ttt` 不允许命中 G1 命名空间、G1跨Pair例外不可用于No-TTT。缺真实 DCP Save/Load、GPU优化器及梯度一致性 **明确留到 S0/GPU Gate，不将 toy roundtrip等同已通过**。
- 旧G1缺失 `--no-ttt` 时依旧走 `GroupedLocalMemoryTrainer`、原Local overlay、原config digest/Source语义；此次共享审计更改只在 `local_memory_enabled=False` 下跳过 fast-state fingerprint。已审既有G1路径和测试未发现新 blocker。

## 3. Matched Off 推理接线 — APPROVE code-only，完整评测链路尚缺

- Root新增独立Server wrapper `scripts/serve_v3_matched_no_ttt.py`，检验专属 No-TTT `v3_job_identity.json`、canonical config hash、No-TTT语义摘要、独立checkpoint同job路径和model DCP元数据/分片存在性、raw15/state15/H16/left_wrist与Generation-only配置；构造原 `action_policy_server_robocasa` 参数 `--local-memory-mode off`、chunk16、采样步30与guidance1.0。
- `--dry-run` 只打印CLI不启动Server。原Child Server/Client的 `off` 是已存在通路，此次**没有**改变现有 `required` Queue 或历史 Episode Store。不能拿此 wrapper 当作「No-TTT统一18Task Queue、全仿真、SR已通过」的证明；后续需专门和G1的任务/随机化/官方horizon/媒体及F0评测协议对齐。
- 小型合成身份负例确认G1 checkpoint、不同source/job、Local on/chunk32等均不会误接。GPU服务器真实权重加载仍未执行。

## 4. 作者 CPU Evidence核对及局限

- Handoff：`docs/collab/codex/reviews/2026-10-25_V3_Matched_No_TTT_author_handoff.md`。
- Evidence：`docs/collab/codex/evidence/2026-10-25_matched_no_ttt_author_cpu/`，包含原始测试/静态检查命令、JUnit、日志、冻结Source SHA、收集节点、失败迭代和原始patch归档。
- 已独立打开 GitHub JUnit `junit.xml`：`tests=481` 中 **439个顶层 testcase 元素**，**434 passed +42 successful subtests +5 skipped**，0 failure/error，23.653s；新增82项在集合内执行且没有跳过。五项 Skip 为原有 optional real data/Edge DCP用例（仅缺外部真实资产），不得写作无skip/已通过。
- Ruff0.12.7 check/format（9 Python文件）、9文件语法、bash syntax、source SHA冻结、Git exact blob和保护路径差异记录均为PASS。前序缺CPU依赖的collection失败及candidate7failed/432passed的迭代保留，不加入最终成功结果。
- GPT直接审阅新旧精确diff、源码、测试断言、runbook和作者的最终JUnit；**未在真实训练主机运行该CPU套件，也未打开真实DROID/VAE/Cache/Verified Index、未运行torchrun、训练、DCP load/Save、实际Server或RoboCasa**。

## 5. Residual next Gates / 允许范围

**本轮 Formal GPT Implementation/Author CPU Source Evidence verdict：`APPROVE`。** 当前在已授权实现范围内未发现可证实的新生产 blocker；历史其他Gate结论不移植到这个训练Profile。

必需下一步依序：
1. **DS_PRO independent CPU Gate**：exact `7c083215e9f39ed4b5b3ff64010e415ad62dfdf4` / `20b5fa639c405a515933da109529e3e2c04de88d`，clean detached worktrees；相同16组 +明确5个optional Skip及82个新增case全部执行，静态验证和JUnit/命令/Source SHA归档。DS原始Evidence可以原位保存，不额外新增上传硬条件。
2. **S0真实资产和matched parity**（另外的只读授权）：比较G1真实 cache manifest/corpus/source-binding/index receipt、基础DROID/Edge/VAE身份、每rank seed/Producer/Consumer数据、Mask、Trainable Generation参数/Optimizer、LR和Loss scale；不得以形状一致替代相同原件。此时可发现真实ABI不一致并重开Gate。
3. **GPU实际能力**（Owner独立明确授权）：8×H100 `Config.validate`，Native Forward/Generation gradients、Local参数不存在、DCP Save和100→101→500 Resume无跳号、真实速度和显存。不能因CPU通过就执行正式30000步。
4. **同条件SR对照**：No-TTT server/client都off，split/task/seed/官方horizon/action horizon/prediction steps/guidance等与G1一致；独立评测输出，绝不复用G1带Local的旧Episode。

本 verdict **不允许**启动训练/模型服务/真实评测/GPU、修改活动G1或iter12000模型、覆盖已有Episode、将无TTT混入旧required Queue或将作者日志冒充DS独立CPU通过。
