# Codex — V3 RoboCasa Batch C r2：仅修复完成证据与媒体分类（GPT REQUEST_CHANGES）

日期：2026-10-22
来源正式独立审核：`docs/collab/chatgpt/reviews/2026-10-22_V3_RoboCasa_BatchC_a2f3a6a3_c9f21040_independent_incremental_review.md`。
**CURRENT FORMAL Implementation Pair（不要用 docs-only HEAD 代替）**：
Root `a2f3a6a367395b2f2a6006cfc4e7c9effa606713`
Child/Gitlink `c9f21040f462a114d597fc83773cb9b6a9e96214`
Vendor `1ac174585293ed998ffc9cf73e47439798cf6f6c` unchanged。
**Gate：`REQUEST_CHANGES`**；这是精确 Batch C 增量整改，禁止跨功能扩大架构/训练/Local算法/第三方Vendor范围。Author 255 cases +65 subtests/Python/Ruff原始记录已审核计数正确，无需重做整套设计。

## Must fix HIGH-C01 — complete/skip must require real episode progress + Local-TTT cleanup witnesses

直接源码：`scripts/robocasa_eval_results.py:240–383`的`validate_attempt()`忽略 `episode_progress.jsonl` 和 `rollout{ep:02d}_cleanup.json`，但Child `cosmos_framework/simulation/robocasa/closed_loop_eval.py:558–630`会写这两类正式证据。作者测试`tools/v3/robocasa_eval_results_test.py:38–140`用完全缺失上述两类文件的`populate()`，依然`finish_attempt`+ `find_completed_attempt` PASS，已经直接构成真实负例。

**功能与验收条款**：
- 强制每个 Episode 的 Local cleanup witness 存在、是typed JSON、`reset_ok is True`、`cleanup_error/rollout_error/media_error is None`，对于required模式，必须有有效的真实session_id（按当前LocalClient.end实际返回类型，不凭猜测以字符串`"None"`冒充）。清理失败绝不算Task complete，即使 `process_cleanup.json`显示PID组已回收。
- 强制 `episode_progress.jsonl` 恰好按 Episode索引0…N−1包含 start/end 对，每条字段schema、digest、`evaluation_attempt_id=f"{task}/{attempt}"`、episode typed integer完整一致。拒绝缺失、空文件、尾行未换行、重复、跳序、外来Task/Attempt、错误Digest及额外记录。保留独立Process PID进度deadline监督；此离线校验需在`finish_attempt`和`find_completed_attempt`共用的`validate_attempt`中执行。
- 将`scripts/robocasa_processes.py:EpisodeProgress`和Queue构造连接到指定Attempt ID以同步在线监视的字段匹配，而非只比`evaluation_run_digest`；注意 Batch A此前CPU Process Fixture和其他Callers可能仍用旧signature，合理选择显式required参数或向后兼容并保证**正式Batch C路径必传**。
- 如果以 `_jsonl()`为解析基础，考虑该函数现要求每条 `"episode"`固定，progress包含跨Episode事件，要新增适配的严格解析器。不要用原始文本`str.contains`、只检查文件非空，或状态=COMPLETE时跳过某些文件。
- 修改Synthetic success fixtures，确实写出这两类正常见证；原有成功测试保持通过，新增至少：`missing_progress`、`duplicate_start/end`、`truncated_progress`、`wrong_attempt`、`wrong_digest`、`missing_cleanup`、`reset_ok_false`、`cleanup_error`、`missing_session`。先做baseline red，修后 green。模拟`attempt.json=COMPLETE`后损坏见证，`--resume`必须明确报错并**不跳过**；原始Attempt永不覆盖。
- 与生产Child先后顺序及日志写入边界保持一致：子程序成功后发end，主进程完成PID cleanup之后才能Commit COMPLETE；独立的Generated Manifest、raw15行动证据、Video decode不减配。

## Must fix MEDIUM-C02 — separate environment vs model-prediction MP4s

`scripts/eval_robocasa_18task_queue.py:202-235`以及`run_worker`错误回退，均以`glob("rollout*.mp4")`填 `rollout_mp4s`，会同时捞取 `rollout00_generated.mp4` 和`rollout00_generated_replan0000.mp4`。用户明确要求区分环境实录与预测生成片段。
- `rollout_mp4s` 仅允许 `^rollout\d+\.mp4$`，并把 `generated_mp4s` 单独成字段/可追溯映射；可以从每Episode `row.generated_videos`严格绑定聚合。缺环境MP4但有first/all model generated时 `rollout_mp4s=[]`，不能误报。
- Error/partial attempt也必须保留实有视频路径，但分类准确，不可丢掉失败样本片段。
- 加正反例：`save_rollout_mp4=false` +`save_generated_video=first/all`，行级与总Summary的MP4分类正确；`none`无generated files才可为空。

## Evidence / execution boundary

- 在**新的源码提交**上交付精确Root/Child/Gitlink Pair及diff、使用最新V3分支源码为开发基线；正式Pair不应变为评审 docs HEAD。按项目Gate仍可先在隔离工作树构建候选，再合入V3（目前Batch C已在V3，但不要改Owner活动G1训练Worktree）。
- 新增最窄完整CPU/Ruff/static Red/Green；保留当前4组作者结果 as baseline，确保已有 Config/Queue/Child/Results/Process/Numba/Media 测试持续绿。若目标CPU没装依赖，BLOCKED≠skip。不要自行启动GPU/ActionServer/真实Kitchen/机器人/训练。
- GPT收到新正式源码Pair后只进行**fresh incremental review of C01/C02 and adjacent source**, DS_PRO进行独立CPU验收。正式RoboCasa依赖真实runtime与Kitchen物理Gate仍需Owner独立批准；不以CPU pass发布18×5正式benchmark。
