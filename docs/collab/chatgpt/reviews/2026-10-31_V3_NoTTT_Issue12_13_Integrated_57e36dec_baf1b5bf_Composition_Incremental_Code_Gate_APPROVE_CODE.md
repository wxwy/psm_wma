# PSM-WMA V3 — Issue #12+13 No-TTT 组合 Formal Pair 增量 Code Gate

**日期：2026-10-31；正式 Verdict：`APPROVE_CODE`。** 本 Verdict **仅**绑定以下 Formal Implementation Pair：

- Root `57e36decbec0e00ecb94dc1c080fd8976afff25d`
- Child/Gitlink `baf1b5bf46853e9849a91518803b9738fc216235`

**范围：** 已批准的 Issue#13 Progress-only Root + Issue#12 Async Lazy Canonical Child 的原样组合、精确代码对象、6条仅合成CPU的 shell→console→profile→Trainer绑定证据。本审核不重开前两轮 APPROVE_CODE，也不替换历史性能 Gate。不意味着正式V3合并、真实Resume、GPU或正式30k启动许可。

## 1. Formal Pair 与差分核验

- 从GitHub实时读取当前Canonical V3 HEAD及 Formal Root Tree。此Formal Root的Gitlink mode160000 **精确指向** Child `baf1b5bf46853e9849a91518803b9738fc216235`；不是作者后续handoff/evidence HEAD `de276eae978fd8bdf9fc68607f21ed7ce9b6b727`。候选分支 `v3-nottt-integrated-20261031` 已发布，未据此认为Canonical已更新。
- Root 相对Canonical基线 `b260290ef09ef25a8a41259aef153df5efff3369` 仅1个实现提交、12个路径：3个No-TTT生产脚本（2 launcher+1 console）、5个tools/v3测试（4继承+1新增）、Child Gitlink、1设计文档与SESSION/TODO。新增唯一新逻辑为组合synthetic测试；没有修改其他生产功能。
- **Root独立Git blob匹配：** 从Formal Root直接读取3个生产文件及4个已批测试文件的SHA，**7/7与已审核donor完全一致**。Root新 `tools/v3/no_ttt_integrated_entry_test.py` blob为`8e9f9a8a32340b38ef0d854f9a0334a35f8b1548`。
- **Child独立Gitlink身份：** 组合直接使用已批移植Child `baf1b5bf46853e9849a91518803b9738fc216235` 整个commit，未创建新Child代码提交；已批该Child的13个donor等价对象不重新扫描。其Canonical EvalV2相关 `evaluation/inference/simulation`、`model/checkpoint/configs`等受保护Subtree已在原Port Gate校核，本轮直接锁死Child SHA，因而未引入任何额外Child修改。Root configs/third_party tree SHA与基线相同。
- 前轮精确审核引用：Issue13 `2026-10-31_V3_NoTTT_Issue13_DefaultProgressConsole_24dbb677_0ae313e3_Incremental_Code_Gate_APPROVE_CODE.md`；Issue12 `2026-10-31_V3_NoTTT_Issue12_LazySource_CanonicalPort_c66ade95_baf1b5bf_Incremental_Code_Gate_APPROVE_CODE.md`；两份Detailed Review已在Canonical V3并被本轮直接核对。**继承对象不等于自动继承新Pair Verdict，故本轮针对组合行为做Fresh增量审核。**

## 2. Contract → 实际行为 → Evidence

| Contract | 实际核查 | 直接 Evidence | 裁决 |
| --- | --- | --- | --- |
| 4GPU世界、workers=8确实执行Async而非旧RAW | 标准Root `train_v3_matched_no_ttt_4gpu.sh`经`no_ttt_console.py`调用原保留的torchrun参数；test使用CPU shim替代torchrun执行，但从真正 `profile_from_args`进入真实 `MatchedNoTTTTrainer.bind_grouped_stream`，`NoTTTAsyncLoader`类型、元数据构造次数与无RAW fallback被断言 | `world4, workers8, fresh/resume`两条测试及`receiver.json`、raw stdout | PASS（组合接线，非真实Worker spawn） |
| workers=0旧同步路径保留 | 4GPU `workers0/resume`、8GPU `workers0/fresh`及`workers0/resume`均确认loader=None、原`--ga`/`--world-size`/T/B及Profile语义 | JUnit对应3case，实际Root shell入口 | PASS |
| 默认屏幕仅Rank0 progress，完整日志不丢 | 复用先前已批Root console `subprocess.Popen`全量stdout/stderr合并→raw log先写→仅回显Progress；实际shell和wrapper为产品对象。新组合测试确认Rank1、Loader诊断仍在raw log，屏幕仅Progress+一次日志路径 | `cases/test_approved_launcher_console0`原始console.stdout、raw完整log | PASS |
| Post-bind失败不掩盖训练错误 | 4GPU workers8 Resume在真正Trainer绑定后通过合成shim注入退出7；包装器保持`exit=7`，完整Traceback在raw、失败摘要在console.stderr | `cases/test_approved_launcher_console5`console.stderr +原始raw文件 | PASS |
| 没有扩大到真实训练或破坏EvalV2 | Child完整采用已批port SHA；Shell只修改显示输出，训练argv/环境和已有Admission不变；原DCP、配置与模型不访问 | Formal Git Tree/Root Diff、7/7 donor blobs及Child SHA，JUnit/作者scope | PASS |

**重要边界：** 这6个测试中的Fresh/Resume是CLI及Trainer绑定模拟；真实 `torch.distributed.run`、actual dataset/worker pool、optimizer、DCP Save→Resume、GPU都没有运行。本轮不把它们误称为真实Resume验收。原donor真实独占GPU C12200 matched A/B的稳态1.61×收益仅属其历史已批Formal，不能声称这个新组合Pair另测一次GPU。

## 3. 独立 Evidence核验

- 作者Evidence在 `docs/collab/codex/evidence/2026-10-31_nottt_issue12_13_composition_author_cpu/`（发表docs commit `de276eae978fd8bdf9fc68607f21ed7ce9b6b727`，**非**Formal Root）。GPT直接读取`junit.xml`，**6个unique testcases PASS，0 failure/0 error/0 skip**；`gate.json`显示bash-n 2个入口、ShellCheck、Ruff check/format 6个Python文件、合成pytest均exit0，合成总40.269s。
- GPT读取全量新组合测试源码和真实原始`console.stdout`、`console.stderr`、`launch.log`，并独立SHA256核对`artifact_manifest.json`里 **7份关键证据**：JUnit、Gate、object_audit、首组成功console/raw、post-bind退出7时console/raw，**7/7一致**。
- 作者第一次**外部audit**因路径误指不存在的`tools/v3/eval_v2`在测试前停止，报告按原样保留`preflight_path_error/`；修正的是工作树外审计路径为实际`eval_v2_production_tests`，未改Formal代码/测试断言；verified目录的6case才是最终PASS。没有将失败审计冒充成功或与正式代码缺陷混淆。
- 直接看现场原始输出含CPU环境的pynvml过时和CPU affinity告警；归于mock test主机，不据此推真实GPU资源或性能结论。

## 4. Gate closure与后续

**正式技术结论：`APPROVE_CODE`；新组合Pair目前无确认的production或tests/Evidence blocker。** 此结论只覆盖已批NoTTT两项改动的源等价与Shell→Console→Trainer真实接线的合成CPU验证。历史Blocker（旧Worker 120s全量LeRobot初始化）已在已批donor及Port Gate关闭，本轮不再复制。

**尚未授权：**将候选发布/合并到Canonical V3，真实单/多Worker测量、GPU和torchrun、原正式30k训练恢复、任何原Checkpoint/Job/Cleaner操作。本次不要求重跑历史49/43/58/301或原匹配GPU A/B，不增加新Gate。

**建议下一步最短路线**：Owner决定是否将该组合Pair安全提升到V3时，遵循当前Canonical HEAD的非强推/非整树覆盖规则，由Codex做最小Promotion、保持EvalV2、形成准确的新Root/Child Gitlink并核验；正式30k只能在Owner明确授权及服务器资源检查后从**原正式完整iter_000012200 DCP**恢复，nw8/prefetch1/persistent1/timeout120，不能使用A/B实验产生的iter12220 DCP。

正式Review与Canonical `CODEX_INBOX.md`须同时成功落盘才视为正式Verdict；Review docs提交不等于实现Pair合并。