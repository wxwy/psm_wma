# PSM-WMA V3 EvalV2 — R01-MEDIA-PROFILE-01 最小修复增量 Code Gate

- 日期：2026-11-03
- **Formal Source Code Verdict：`APPROVE_CODE`（仅本次 Root 代码、测试的窄范围增量）**
- 本次 Formal Root implementation：`2d1ad80f89ab4cc0e275ff4341f064954870abdd`
- 未变的 Formal Child/Gitlink：`c93f2abf4fb27d36176ff8db094379a853cec796`
- 候选分支：`v3-eval-v2-media-profile-20261103`；后续 docs/Inbox HEAD **不能代替**本次 Formal Pair。
- 上一已审正式 Root `e7ce99d7a0bbb7a81ea7afcee7253548687dc223` / Child `c93f2abf4fb27d36176ff8db094379a853cec796`；此前 RM-ALL-R01 代码 `APPROVE_CODE` 和 DS CPU122 独立 PASS 不变。
- 上一 R01 GPU Canary 真实结果：**历史 `R01_FRESH_EXIT=1` / `media_summary.status=MEDIA_INCOMPLETE` 不改**。DS report-supported Core/SR 1/1 valid/success，19 replans/19 Saved MP4/19 receipt/19 ACK，但媒体总体 Aggregator FAIL；此前仅一个 confirmed bug：根仓 Profile 误比对。本次代码 APPROVE **不自动改变 R01 原始 Hardware Gate FAIL**。
- 本轮通过 GitHub 插件直接读取了 Git commit、Formal Root 文件、Frozen Child contract、真实新增测试、作者 RED/JUnit、GREEN/JUnit/静态证据。**未在 DS 服务器独立运行 GPU/CPU 或访问真实 R01 out 目录**。

## 1. 实际 Formal Diff / 功能核对

**生产代码仅一个 Root 文件**：`scripts/robocasa_eval_v2/generated_media.py:34–38`，替换
`store.manifest.get("execution", {}).get("profile") == "phase_b"`
为与生产 `config.execution()` 和 Child `contract.build_manifest/validate_manifest` 严格一致的
`== "phase_b_native_batch_v1"`（格式导致2新增/1删除）。其他 `publish()` 的条件、`is not` 对布尔 `server_ack_required` 的精确检查、`count`、`missing=[]`、MP4 inventory、receipt Episode/attempt/generation identity、逐文件哈希核对均原样保留。科学 Core/SR `summary.json` 无更改。

新增 Root `tools/v3/eval_v2_replan_tests/media_profile_test.py`（221行）；Root `SESSION.md/TODO.md` 文档记录。**正式 Child SHA/Gitlink 未变**，Submodule 的 Cosmos/encoder/Action/Local/Session/ACK/训练等均未修改。对照本次 commit Diff、Gitlink tree 与作者 protected scope，未发现越界生产代码。

## 2. 原 Bug `R01-MEDIA-PROFILE-01`：**CLOSED（代码层面）**

真实 Phase B `manifest.execution.profile = "phase_b_native_batch_v1"`；应要求 `generated_media_completion.server_ack_required is True`。上一 Root 的 `== "phase_b"` 始终得到 false，导致合法 true 被拒、并让不合法 false 被接纳。

新比较：
- Phase B合法 true `publish().status=COMPLETE`，实际进入全部 MP4 与收据哈希校验；
- Phase B非法 false/None/int/string `MEDIA_INCOMPLETE`；
- Phase A / 无 `execution` 的合法 false 仍 `COMPLETE`，非法 true 拒绝；
- Child Contract 对未知 `phase_b` 或其他伪造的 native manifest value 仍 fail-closed。

没有放宽或跳过媒体身份校验，也没有篡改原 Canary 的 `media_summary`；**R01-MEDIA-PROFILE-01`CODE` blocker 可以关闭**。

## 3. 原始 RED/GREEN 与 Static 证据

作者证据目录：`docs/collab/codex/evidence/2026-11-03_eval_v2_media_profile_author_cpu/`（位于后续文档候选 HEAD）。

- `red/junit.xml`：旧 Root + 冻结测试，**2/2 expected RED**（0 errors，0 skipped）：(a) native Phase B true ACK 本应 COMPLETE 却得 INCOMPLETE；(b) native Phase B false ACK 本应拒绝却得 COMPLETE；读取真实 pytest stack 与 failure message，一一对应之前 bug。
- 冻结测试 SHA256 `d5f32f29936bebedc94301e7f7a528b8abdcd26d96fa10d5d9b3aa28ca8fab8a` 与旧 RED、新正式 Root 新 test 与 GREEN invocation 一致，未为通过修改断言。
- `final/junit.xml`：**42/42 author CPU PASS /0fail/0error/0skip**（15新增 profile +10既有 report+17 config，Python3.13.5）；并非 DS 独立验收或旧379/122的再次运行。
- 真实 `config.execution()` 构建原生 Phase B Manifest，并用 Child `build_manifest` + `validate_manifest`、Store Commit/Closed Episode、CPU合成MP4+实际 `write_generated`/Receipt 测试；每个合法分支重复 `publish` 两次，spy **delegates to real** `read_receipt` / SHA 实测分别访问索引0、1。负例覆盖缺 MP4/receipt、坏收据哈希及同大小内容改变，均拒绝。科学 `summary.json`、Core `result.json` 和 Manifest 字节不变。
- `static/gate.json`：Ruff0.12.7 check/format PASS、Root target source+test 语法通过、AST 表明唯一生产语义差为 Profile literal，正式 source 2项 Git Blob/SHA256 绑定，25项作者 artifact hashes 归档；Root/Child protected old379/122证据未改。以上均为作者证据，GPT已校对 GitHub 存档原文但本轮未自行重跑 Python。

## 4. Gate 状态与下一步

**正式增量 `APPROVE_CODE`**（Formal Root `2d1ad80f89ab4cc0e275ff4341f064954870abdd` / Child `c93f2abf4fb27d36176ff8db094379a853cec796`），单一代码问题 `R01-MEDIA-PROFILE-01 CODE CLOSED`；没有发现新生产 blocker。

**仍然 `PENDING` / not hardware PASS：** 原 R01 19个真实 MP4/Receipt 的完整库存与哈希核验、用新代码离线重新 `publish()` 的成功与否。原 R01 Run 在修复前以 exit1 结束，该历史 FAIL 不允许抹除。作者明示 `offline_reconciliation=PENDING_DS_ISOLATED_COPY_RECONCILIATION`。**只有真实 DS 独立验证在隔离副本上得到 `media_summary.status=COMPLETE, expected=saved=acknowledged=19, errors=[]` 且全部19文件/收据匹配，并保留原失败 provenance，才能将硬件成果归类为“原媒体 runtime PASS + 新代码离线重算成功”；原运行的 Exit1 永不改写成 Exit0。是否另外 rerun GPU 由 Owner 以后单独决定；优先不 rerun。

DS 的下一步明确为 **新 Root 独立 CPU42 + 仅 CPU/文件IO离线隔离副本 19媒体 recon**；详见
`docs/collab/chatgpt/reviews/2026-11-03_V3_EvalV2_R01_Media_Profile_DS_CPU42_and_Offline19_Handoff.md`。CPU 或离线有真实 FAIL 时按原始文件路径/校验异常反馈，不得自行改生产代码、改样例证明/手工改总结状态。验证完成停止，等待本审核者/Owner。

**范围严格隔离**：无官方 V3 merge，未启动真实 GPU、未重做900EP或历史379/122，不访问训练进程/GPU0–3、现有 out2/No-TTT/H2/H3、Checkpoint/DCP；不覆写旧 R01 out/ 的视频、日志和 exit1。
