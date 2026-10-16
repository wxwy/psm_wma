# PSM-WMA V3 F1 — DS_PRO EVID-03 / EVID-05 独立 CPU Evidence-only Gate Closeout

**审核日期：**2026-10-17（DS_PRO 补证报告日期：2026-10-16）  
**角色：**GPT / Independent Code–Evidence–Gate Reviewer  
**Gate 名称：**`V3_F1_SYNC_LOCAL_DCP_STRICT_RNG_CPU_GATE`  
**正式裁决 literal：`APPROVE_TO_CLOSE` — STRICTLY F1 CPU GATE ONLY.**

**Frozen implementation Root：**`6ebf8998a7935f2ad690bb547c5db5e5a4322e6d`  
**Frozen implementation Child / Gitlink：**`2d128ed5a07601cdd424974f99b67832eafeeb41`  
**候选隔离分支：**`v3-f1-checkpoint-rng-20261016`，分支在审核开始时 docs HEAD `ccfd900bc35fcd39ca9953aa7aa55b85398300ad`；其文档 HEAD **不是** formal implementation Root。  
**V3 主分支在本轮审核前：**docs HEAD `b31984945a64e2dc6e85d6ede89aa9aec7429c50`，仍指向旧生产 Child `1d56320c08c56b0f8dd248919d152d81ae12ea7b`。F1 未并入 V3 主线。  
**合同：**`docs/build/PSM-WMA_V3_F1_sync_checkpoint_strict_rng_contract_2026-10-16.md`（提交时冻结 SHA256，据作者报告 `aa3f7c6db2bdf5a7c193de1398b7ff1aa81b59b08554552f6fa86fc3e2748185`）。  
**已有技术审核：**`docs/collab/chatgpt/reviews/2026-10-16_V3_F1_6ebf8998_2d128ed5_sync_checkpoint_strict_rng_pre_DS_incremental_review.md`，技术代码审读已完成。  
**上一轮 Evidence 审核：**`docs/collab/chatgpt/reviews/2026-10-16_V3_F1_6ebf8998_2d128ed5_DS_independent_CPU_evidence_review.md`，同一 pair 的 `REQUEST_CHANGES — EVIDENCE-ONLY`，只余 EVID-03 / EVID-05。  
**最新 DS_PRO Evidence：**Owner 本轮粘贴 `DS_PRO — V3 F1 EVID-03 / EVID-05 独立 CPU 证据 Addendum — 2026-10-16`；此前已提供 `DS_PRO — V3 F1 同步 Checkpoint / 严格 RNG 独立 CPU 验收报告 — 2026-10-16`。原始 XML/log 在远端 DS 服务器 `/tmp/psm_v3_f1_evid03_20261016/`、`/tmp/psm_v3_f1_evid05_20261016/`、`/tmp/psm_v3_f1_accept_20261016/`。GPT **未直接打开远端文件或重跑实验**，对这些结果明确归类为 DS 独立报告的事实；GitHub formal Root/Gitlink 与涉及CUDA边界的生产代码独立复核。

## 1. 新补证与两个剩余 Blocker

| Blocker / Contract | DS_PRO reported evidence, EXACT pair | Verdict |
|---|---|---|
| **F1-EVID-03** — 真实 Cosmos 完整配置解析 / Checkpointer 实际构造 | 使用真实 `load_experiment_from_toml → Pydantic → Hydra → attrs.Config`；官方 DROID base 路径仅作只读前检、已验收 verified-index open无全文扫描，9126 episodes；SafeLocal target `cosmos_framework.checkpoint.dcp.SafeLocalDistributedCheckpointer`、profile `psm_v3_sync_local_v1`、strict=true、async=false、本地存储；Configured 30000/500/100。Real `Config.freeze()` 与冻结拒改 PASS。真实 `config.pkl` 90,240B/ `config.yaml` 15,532B 成功序列化和回读。**真实生产 `instantiate(config.checkpoint.type,config.checkpoint,config.job,callbacks=None)` 在 2 个独立 CPU Gloo Rank 成功构造 Checkpointer**, safety group 非空。Fresh100与Resume500**语义**SHA相同 `22b17cc387453971554b4c31157affaf2f54ceb1078fc650a43ffa2b07c17e61`；无生产 DCP Resume 实测。 | **CLOSED for CPU-available authority**, with explicit CUDA-validate deferral (below) |
| **F1-EVID-05** — F1 当前代码受影响真实依赖回归 + Ruff/Syntax | V2 完整 Cosmos venv、F1 精确源码，既有受影响 Phase5 + Grouped Trainer + Grouped Resume + DCP Distill suite **128 PASS / 1 named legitimate optional-asset SKIP / 0 FAIL / 0 ERROR**, RC0，JUnit 129 tests、time36.46s。唯一跳过 `test_optional_real_strict_snapshot10_preflight` 因未提供可选真实资产；18警告均为未注册 pytest mark。六个受影响文件 `ruff check`、`ruff format --check`、`py_compile` 全部 RC0，Ruff0.12.7。 | **CLOSED** |

## 2. 明确的 `Config.validate()` CPU BLOCKED 与 GPU 硬门处理

DS_PRO 报告在 `CUDA_VISIBLE_DEVICES=""` 环境调用真实 `Config.validate()` 抛 `RuntimeError: No CUDA GPUs are available`，**不是配置逻辑已通过，也不当作通过**。

GPT 独立核对生产 Child `cosmos_framework/utils/config.py:529–546`：该方法首先 `distributed.ensure_world_communicator()`，随后创建 `torch.ByteTensor(...).cuda()` 并广播 job name。它从实现上依赖已初始化的 GPU/NCCL-world，不能在**明确禁止GPU**的 F1 CPU Gate 中端到端执行。当前 corrected Phase5 `preflight()` 是只读配置/数据 metadata 准备，真正训练入口 `main()` 初始化分布式后经 `_agree_preflight()` 调用 real `config.validate()`，在 Trainer、真实DCP训练前执行（`examples/psm_wma_robocasa_corrected_phase5.py:339–357,932–958`，按当前F1版本略有行号偏移）。

**Scope 判定（透明而非伪造 PASS）：** F1 CPU gate 可以关闭的，是实际CPU可运行的配置factory/serialization、DCP/Gloo失败/恢复与RNG行为。由于`Config.validate()`的GPU-collective设计，该 **CUDA-only subcheck明确 `BLOCKED_IN_CPU` 并强制转移为下一阶段Owner独立授权的8×H100 GPU启动前的 `HARD_P0`，不能由本 CPU approval 视作已测/自动豁免**。这不是旧 B1 numerical r2 阈值修改，也不是批准真实CUDA执行。若后续 GPU config.validate/World communicator失败：`STOP`，不得正式继续Fresh Job或向其写出成功证明。

除GPU validate外，新Pair实际 world8 FSDP/DTensor、真实DROID/Local、CUDA RNG恢复及正式DCP仍需后续**独立 GPU Gate**，不在本次CPU Gate acceptance内。

## 3. 原有 F1 核心 CPU Evidence 继续有效；未重复运行

保留 DS_PRO 2026-10-16 首轮独立验收结论：
- V2 & V3 venv F1专项各 **29/29 PASSED**（新增F1专项独立方法数，不应将JUnit子用例当独立新方法累加）。
- **14场景**真实双 Rank CPU Gloo/DCP：延迟rank、DCP/Sidecar/marker/latest写失败、首次失败、hard exit/stall bounded timeout、source/iteration disagreement、RNG rank/leaf/跨rank异常、双Rank成功恢复。目标 `/mnt/data` ext4的极小真实DCP合成fixture，独立 stdlib reader 验证complete/latest/四组件metadataSHA+extent和rank sidecar SHA，失败不发布半DCP。
- 18个rank RNG metadata leaf（2rank×9字段），双Rank保存/恢复model/optim/scheduler/local后 Python/NumPy/Torch next draw逐位一致；deterministic成功恢复后不reseed。
- 这不是GPU RNG验证，CUDA bytes是CPU stand-in，不能宣称8×H100或真实FSDP Optimizer恢复通过；DCP大分片验证只覆盖metadata SHA+shard存在/大小，不包含全部权重body的内容哈希。
- 上次GPT技术审核已确认新生产 `SafeLocalDistributedCheckpointer` 的发布流程与严格恢复机制没有新已证实 blocker。本轮 formal pair未变，只审核新DS Evidence，**没有重复新技术审核**。

## 4. Exact formal verdict 与剩余边界

**F1 CPU Gate = `APPROVE_TO_CLOSE` on exact Root `6ebf8998a7935f2ad690bb547c5db5e5a4322e6d` / Child `2d128ed5a07601cdd424974f99b67832eafeeb41`.** 现有同 pair Evidence-only `REQUEST_CHANGES`（EVID-03/05）由本次两项补证关闭；原先报错事实不被历史抹除。通过CPU Gate只能表明范围内的 DCP多Rank CPU故障/恢复、local存储写入与真实配置工厂/受影响回归满足验收，**不授权真实训练**。

严格不得将其解释为：
- 无条件`Config.validate()` PASS 或 NCCL/World communicator PASSED；
- 8×H100真实CUDA RNG、FSDP2 Local Fast/Slow/optimizer save→resume 连续性通过；
- 有权读取/改动原 iter1300、修改B1原数值FAIL或回溯迁移；
- 正式生产 `Fresh100`、`Resume500`、`Formal30k`、`Gate M`、RoboCasa仿真批量评测/有价资源调用获批；
- `V3` 主分支已经合入 F1（尚未）。

**紧接着的两项独立准备：**
1. **S0 存储门：**DS只读统计真实旧iter1300 DCP的组件文件大小元数据、真实输出卷可用空间，提出Owner批准的有界保留规则，避免将旧B1数值捕获 `rank*.pt` 误认真实DCP（不改任何原文件）。
2. **GPU Gate准备而非执行许可：**锁定一个将来实际要运行的Root/Child Full Pair、8Rank目标环境、正式Launcher/Index/Raw15/Action+Local FSDP梯度与full/terminal Loss/Mask、真实 `Config.validate()`、正式Fresh100全RankDCP完整保存和SameJob Resume100→500等验收策略；先给Owner明确精确授权再执行。旧Index8兼容性、新B1阈值、Prefetch/无关性能优化均不进入当前Fresh关键路径。

**Formal persistence requirement：**本 review 与 `docs/collab/chatgpt/CODEX_INBOX_2026-10-15_CONTINUATION.md` 的 append-only entry 必须同时提交并回读校验，才成为正式F1 CPU Gate关闭记录。
