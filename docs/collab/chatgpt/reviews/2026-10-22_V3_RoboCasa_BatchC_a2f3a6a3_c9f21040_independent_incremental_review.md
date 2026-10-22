# PSM-WMA V3 — Batch C Owner Manual RoboCasa Eval：独立增量源码/CPU Evidence Gate

日期：2026-10-22
对象：**Formal Root `a2f3a6a367395b2f2a6006cfc4e7c9effa606713` / Formal Child-Gitlink `c9f21040f462a114d597fc83773cb9b6a9e96214`**，不以docs-only HEAD `e8ebff8f3a8ad69c3b11c01caf1ec645755d5886`替代生产Pair。Vendor `1ac174585293ed998ffc9cf73e47439798cf6f6c` unchanged（robosuite1.5.2 + pinned patchset）。
**Verdict：`REQUEST_CHANGES` — 发现新 Batch C 生产证据完整性缺口；作者 CPU 结果 `AUTHOR_CPU_PASS` 实证计数正确，但不构成正式代码放行。**
未授权真实GPU、Action Server、Kitchen、vendor安装、G1训练/Checkpoint操作；不复审未变化的 G1/A/B 旧Formal实现，仅本次增量。

## 1. Pair / diff 范围

- GitHub V3 可解析 Root candidate SHA 和精确 mode160000 Child/Gitlink `c9f21040...`；与Base Root `9ae01344ffe82a3b403732aa61cce3dd7fb5055a` / Child `30db22a3586c0270611753dc2ca0deb10ec27833` incremental compare：
  - Root 生产增量：`scripts/eval_robocasa_18task_queue.py` (+290/-160)、新增`scripts/robocasa_eval_config.py` 301行、`scripts/robocasa_eval_results.py`418行、`scripts/run_robocasa_eval.sh`5行、YAML、Runbook、对应4个测试文件；SESSION/TODO和评审/证据归档属于文档变更。
  - Child：`cosmos_framework/simulation/robocasa/closed_loop_eval.py` (+113/-24)、新增`closed_loop_eval_manual_test.py`352行、`cosmos_framework/utils/rollout_evidence.py` (+9/-1)。
  - 保留G1跨版本Resume、A Task生命周期、B Vendor锁及算法/训练模型与真实G1 Frozen assets；Batch C已真实接线B runtime attestation于Queue及Child，但不能将旧版本模拟器成绩重新解释成正式benchmark。
- 正确实现部分：严格 YAML/CLI>config>defaults、18底层task与子集、oneGPU-oneSlot0、Checkpoint/Config/identity与严格required Local-TTT、无输出的metadata list/CPU dry-run、per-task全新Server和Task/Episode deadline，Generated视频none/first/all，PNG/rollout可关，action+prediction JSONL必选；新attempt独立目录、成功完整Task跳过、失败Task新attempt从ep0重试，日志和先前证据不覆盖。
- Runtime vendor Probe使用选定sim interpreter，在CPU preflight读取真实Git/source/native/registry，在Child创建Kitchen前独立复测digest，dataset generation0.5.1记录与Eval1.0.1分栏，后续真实安装/物理验收另Gate。
- CLI example与runbook的真实使用仍依赖独立vendor安装，作者云端没有完整RoboCasa运行时，尚未现场正向pass。

## 2. 作者 CPU Evidence 独立核对（结论为作者CPU可信但覆盖不足）

报告：`docs/collab/codex/reviews/2026-10-22_RoboCasa_Batch_C_manual_eval_author_handoff.md`，文件归档ref `e8ebff8f3a8ad69c3b11c01caf1ec645755d5886`。
已直接回读目录 `docs/collab/codex/evidence/2026-10-22_RoboCasa_Batch_C_manual_eval_author_cpu/` 中`gate.json`、`commands.json`、`source_checks.json`、4套最终原始JUnit与Ruff文本：
- Config/Task/Media/Process/Numba组 **148 testcases**，0failed/error/skipped；
- Child Media/Runtime/Lifecycle/Phase6/Contract等 **58 testcases**，0failed/error/skipped；
- Queue **29 testcase methods +65 subtests** (JUnit tests属性94)，0failed/error/skipped；
- 既有identity/media 回归 **20 testcases**，另50 deselected不计skips；
- 合计：**255顶层testcases +65 subtests**，共4套JUnit按tests属性计320，作者口径与原始记录一致。Ruff0.12.7 check+format、Python10改动文件syntax、bash -n据原始作者Evidence通过。
- 这些测试主要是真实轻量Git/Linux PGID/socket/FFmpeg/Pillow/MuJoCo接口与合成model/simulator边界；**GPT没有在DS服务器或本工具容器上重新运行255项**，不可写成独立DS CPU pass。最终Scope没有真实Vendor完整正向import、PandaOmron Kitchen create/reset/step、policy DCP/Local-TTT model推理或GPU仿真证据。

## 3. 阻断 Finding HIGH-C01：完成/Resume缺失Local清理和Episode进度证据

**文件和具体机制**：
- `scripts/robocasa_eval_results.py:240-383` — `validate_attempt()`验证了`process_cleanup.json`、`runtime_attestation.json`、`results.json`、`rolloutXX_episode.json`、每Episode action/prediction JSONL、媒体；**从未打开或检验`episode_progress.jsonl`，也未读取每Episode `rolloutXX_cleanup.json`**。
- `cosmos_framework/simulation/robocasa/closed_loop_eval.py:560-626` 实际已经发出`episode_progress.jsonl`逐Episode start/end及`evaluation_attempt_id`，也会通过`on_cleanup`写 `rolloutXX_cleanup.json`（Local-TTT End/Reset witness）。如果该两类证据被删除/截断/篡改，`finish_attempt()`仍可能将所有其它证据完整的Task写为`COMPLETE`，`find_completed_attempt()`在下一次`--resume`还会直接跳过它。
- **直接作者测试反证**：`tools/v3/robocasa_eval_results_test.py:38-140` 的`populate()`只创建`process_cleanup.json`、action/prediction JSONL、result/episode和选项媒体，**完全没有创建`episode_progress.jsonl`及`rolloutXX_cleanup.json`**；紧接的`test_complete_task_only_resume_requires_actual_decodable_artifacts`预期且实证`finish_attempt(...)`、`find_completed_attempt(...)`均PASS。这证明漏洞是实际源码合同，不是推测。
- `scripts/robocasa_processes.py:104-160` 的在线`EpisodeProgress.poll()`只比对Run Digest与Episode序号/order，却**未比对新增的`evaluation_attempt_id`**（Child已经写出）。这使在线进度协议没有达到本Batch C宣称的完整Task/Attempt绑定。

**违反冻结合同**：Manual Runbook `docs/eval/robocasa_manual_runbook.md` 的“Only entire COMPLETE tasks with matching identity, valid in-process runtime/cleanup witness and media/audits are skipped”、Batch C“异常恢复不丢证据、不将污染会话算正式成功”；尤其之前18任务发生过Local session-limit污染，不能忽略**每Episode**Local cleanup的证据。即使原主流程一般通过异常传播阻止成功，这些已提交的完结物仍必须让离线复查/重启具有一致Fail-closed语义。

**要求整改（不可无故扩大生产范围）**：
1. 在`validate_attempt()`/Resume入口验证每个`rolloutXX_cleanup.json`存在并且正确的Local-TTT清理语义：`reset_ok is True`、`cleanup_error is None`、`rollout_error is None`、`media_error is None`；required-mode还须有合法非空session ID或与Client End协议等价的硬证据。不能仅靠Server进程已退出代替Episode session清理成功。
2. 验证`episode_progress.jsonl`严格包含指定N Episode按序start/end、每条Run Digest与**Task/Attempt Identity**全部匹配，无缺失、截断、重复、尾部脏数据或额外Episode；在在线`EpisodeProgress`/Queue构造时传入expected attempt ID并严格检查新字段。完成/Resume复验执行同一严格条款。
3. 增加真实的负例CPU：缺失、改写`rollout00_cleanup.json`的`reset_ok/cleanup_error/session_id`，缺失/乱序/重复`episode_progress.jsonl`、错误run/attempt/episode字段；验证`finish_attempt`不能标COMPLETE，已COMPLETE的损坏文件`--resume`不能跳过。
4. 改写之前成功fixture需**生成完整且正确的**Local cleanup/进度证据，而不是为了保持旧绿而降低新验证；保证原有55+跨类型测试/路径仍通过。

## 4. Finding MEDIUM-C02：环境MP4与预测MP4结果混列

- `scripts/eval_robocasa_18task_queue.py:202-235` `task_result()`把`rollout_mp4s = sorted(str(path) for path in output_dir.glob("rollout*.mp4"))`用于Summary，且`:713-729`回退行也以`glob("rollout*.mp4")`构造。
- 在`save_generated_video=first/all`时，匹配`rollout00_generated.mp4`或`rollout00_generated_replan0000.mp4`。当`save_rollout_mp4=false`而仍生成预测视频时，Summary`rollout_mp4s`非空，被误称作**环境Rollout MP4**，与Owner明确要求环境实录和模型预测视频分开保存/呈现不符。此问题在`save_generated_video=none`的Synthetic Queue主测试中被隐藏（其默认关闭预测视频）。
- **整改**：`rollout_mp4s`仅匹配 `^rollout\d+\.mp4$` 的环境文件；预测视频显式另列`generated_mp4s`或依`generated_videos` perEpisode映射展示。添加禁用环境视频+启用generated first/all的Summary负例，防止误报。

## 5. Gate / 执行顺序

- **`REQUEST_CHANGES`**，Owner手动真实1x1 / 4x5 / 18x5仿真本Gate**不放行**，不是怀疑255作者CPU记录，而是新增完成证据与媒体归类两项生产缺口。
- Codex在**当前V3新Formal Pair之上**做最小Batch C r2 fix，不触碰G1冻结训练/模型、Local-TTT算法、Vendor patch与无关模块，提交新Root/Child/Gitlink完整SHA、精确Diff、针对上述负例及旧回归CPU JUnit/Ruff；单独通过GPT增量审核后交DS_PRO独立CPU（作者PASS!=DS验收）。
- Batch B真实Vendor目标解释器正向import和PandaOmron Kitchen物理Gate继续独立`BLOCKED`，不得将Batch C CPU Gate自动升级为正式benchmark可用。
- 不能因评审文件/Inbox造成的 docs-only HEAD 改变Formal Implementation Pair；当前Source仍以本Review开头固定SHA定位，后续r2源码变动另Gate。
