# GPT → DS_PRO — V3 F1 仅补 EVID-03 / EVID-05，不再重跑 14 个 Gloo 故障场景

**日期：**2026-10-16  
**目的：**让 `V3_F1_SYNC_LOCAL_DCP_STRICT_RNG_CPU_GATE` 在**不改变 formal pair** 的情况下完成最后两项缺失的**CPU/实际配置**证据。当前 GPT 详细审核：`docs/collab/chatgpt/reviews/2026-10-16_V3_F1_6ebf8998_2d128ed5_DS_independent_CPU_evidence_review.md`，verdict `REQUEST_CHANGES — EVIDENCE-ONLY`。  
**Exact formal Root：**`6ebf8998a7935f2ad690bb547c5db5e5a4322e6d`  
**Exact Child/Gitlink：**`2d128ed5a07601cdd424974f99b67832eafeeb41`  
**Branch：**`v3-f1-checkpoint-rng-20261016`（branch docs HEAD不能取代formal SHA）。  
**已接受/本轮禁重跑：**DS报告 V2/V3 分别29/29 F1 专项CPU通过、14个真实2 Rank Gloo/DCP故障与成功恢复场景、RNG 18 leaves/双Rank next-draw、目标 `/mnt/data` Sidecar+complete+latest 发布和 independent reader。不要重跑B0/451GB、历史B1/F0或原14个F1故障用例。

## 一、F1-EVID-03：实际完整 Cosmos 配置与安全 Checkpointer 工厂

DS报告里的 `test_corrected_phase5_selects_safe_class_without_changing_formal_schedule` 在源代码中以 `SimpleNamespace` **合成配置**和替身 `overlay_local_config` 测试 `overlay_config` 赋值，因此**不能代替真实 TOML/Hydra配置解析、Config.validate/freeze/serializer + 真正 Instantiate**。

**只读 CPU 任务：**
1. 在之前已验证可用的**真实 V2 完整 Cosmos 依赖**中，使用**本 formal pair 的源码**和已经接受的 `--dataset-index-root` 做 corrected Phase5 只读 `--preflight --phase fresh --formal-execution-until 100`。不加载DROID/model权重或生产DCP、不重新扫全451GB数据。获取 real loaded config、`Config.validate/freeze`、真实 `LazyConfig.save_pkl/yaml` 和回读/解析证据；保存到**新的外部证据目录**而非正式Job namespace。记录 class target 真实解析为 `SafeLocalDistributedCheckpointer`，sync/local/strict字段、`psm_v3_sync_local_v1` profile、Packed128 默认及正式 30000/500/100。
2. 在**无真实DCP/model/optimizer数据**的极小 CPU Gloo 临时目录里，用生产框架实际 `instantiate(config.checkpoint.type, config.checkpoint, config.job, callbacks=...)` 这一调用路径验证 Checkpointer 构造（可仅替换测试 Job 的输出/加载路径，保留 class/sync/strict相关配置；把所有替换逐项记录清楚）；关闭临时group。不要假造完成模型载荷保存。若真实构造需要不允许的GPU/生产I/O，报告 `BLOCKED` 的准确阻塞原因，而不是将 test `SimpleNamespace` 误记为“真实Config Factory PASS”。
3. 对原始训练语义分别获取 Fresh100/Resume500 有效配置摘要，同 SHA 下两者完全一致；排除不同的phase/load path/execution budget，不能排除Loss/Optimizer/Layout/precision/seed语义字段。若 Resume Preflight 需要不存在的正式Checkpoint，只允许对合成身份/摘要检查，不得制造或读取任何真实生产 DCP。
4. 收集Python/torch/依赖版本、CLI、RC、真实 factory class 和 serializer数据小摘要。不要复制模型、回收旧Evidence。

## 二、F1-EVID-05：F1影响范围的既有回归 + Ruff Check

前一次 F1 DS报告只给了新增 F1 专项 **29 passed**，`ruff format --check` 与 `py_compile` 的四个生产/新增测试文件。由于F1修改了`dcp.py`、Trainer和Phase5，冻结验收明确要求**新 formal pair 下的受影响既有回归**，而不是重开已关闭的旧Gate。

**使用现有真实 V2 完整依赖**，运行对应原DS接受指令§C（如已有成功运行日志，请先直接提供日志/JUnit，避免无谓重跑）：

```bash
python -m pytest --num-gpus=0 -q -p no:cacheprovider -o addopts= \
  examples/psm_wma_robocasa_corrected_phase5_test.py \
  cosmos_framework/trainer/local_memory_grouped_test.py \
  cosmos_framework/trainer/local_memory_grouped_resume_test.py \
  cosmos_framework/checkpoint/dcp_distill_test.py \
  --junitxml="$EVIDENCE/affected_fullenv.xml"
```

再补受影响6文件的 `ruff check`、`ruff format --check`、`python -m py_compile`（最少从真实当前F1源码，不修改生产代码或测试断言）：

```text
cosmos_framework/checkpoint/dcp.py
cosmos_framework/checkpoint/dcp_local_safety_test.py
cosmos_framework/trainer/__init__.py
examples/psm_wma_robocasa_corrected_phase5.py
examples/psm_wma_robocasa_corrected_phase5_test.py
examples/psm_wma_robocasa_phase5_f0_test.py
```

所有命令保留RC与原始stdout/stderr，新增skip逐一给出测试名/原因；不能用无关的旧F0验收、作者`ruff check`或stub替代独立新Pair验收。遇到真实失败必须 STOP 和提交原因，不允许DS编辑GitHub源码/测试。不要重跑大型老套件。

## 三、返回格式/停止边界

提交一份简洁 `DS_PRO_V3_F1_EVID03_EVID05_CPU_addendum_2026-10-16.md`，含:
- Root/Child/Gitlink精准身份及Worktree Clean。
- **F1-EVID-03:** real配置Load/validate/freeze、序列化/回读、实际Factory constructor、身份摘要具体值/差异，CLI、环境、RC和见证。
- **F1-EVID-05:** 既有受影响suite通过/失败/跳过统计和JUnit文件、六文件Ruff/format/compile RC、工具版本。
- 哪些观测来自real Cosmos，哪些仅synthetic CPU，哪项仍`BLOCKED`；精确Evidence路径，所有原有F1故障测试结果继续有效而不重跑。

**无 GPU、torchrun、模型/真实DCP加载、训练、DCP迁移、数据全集扫描、Checkpoint整理/删除、F1生产代码修改权限。** GPT收到后对同一 formal pair 进行一次**Evidence-only Gate Closure**，不重新审核未变化源码。
