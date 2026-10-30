# PSM-WMA V3 — No-TTT Issue #12 仓库外 CPU 冷启动探针 v4 增量审核

- 日期：2026-10-30。
- **正式 Verdict：`REQUEST_CHANGES` — 仅剩 EXTERNAL_SCRIPT_SOURCE_EVIDENCE。** 从当前可审阅的v4控制流与设计看，上一轮阻断方案的P2/P3/P4/P5/P6已作充分整改；**未新发现需要 v5 代码重构的生产或探针逻辑 blocker**。但无法验证DS原始 `.py` 字节，故不能给出按精确SHA绑定的最终 `APPROVE_SCRIPT`。此外 **`REAL_DATA_CPU_EXECUTION=NOT_AUTHORIZED`**，无论脚本本身审到何种状态均不能擅自执行。
- **Frozen production Formal Root** `e0fe911dfb9fd34957234828195cf051713f6c3d` / **Child/Gitlink** `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7` 不变；其 `APPROVE_CODE` / Issue#11 DS独立301CPU+6raw `PASS` 保持，本轮**未重新做生产源技术审核**。Issue #12 真实 Arm B 120s Timeout/0 committed、性能 `INCONCLUSIVE` 亦未变。
- **新审对象**：用户这轮附 `粘贴的文本 (1)(20261030-112718).txt`，其中宣称的DS仓库外脚本 `cpu_diagnostic/issue12_worker_coldstart_probe.py` **rev v4**，报告SHA256 `9f1996b01d76f33ad8b15d19e47c15ef46471781f35599d591b55b8e5f016c67`、Ruff与PyCompile OK及**非真实数据**Smoke Test。
- GPT实际读取本次上传原文 **57,344 bytes**，文本SHA256 `844676456ea3a809ffc10c76a46d3838ec04891420931567f66e752e02f76d31`；第1-528行是经过聊天富文本处理的`Python-looking`内容，出现`from **future** import annotations`、`description=**doc**`、`if **name** == "**main**"`、插入代码围栏/缩进损失。直接`compile`在第63行SyntaxError。**这只证明聊天转码文本不是可运行原始.py，不证明DS本地脚本语法失败**。用户本轮未附真正`issue12_coldstart_probe_v4_review.zip`的原始字节；DS所称脚本SHA和静态测试均**尚未由GPT独立复核**。
- [上一轮 v3增量review](https://github.com/wxwy/psm_wma/blob/aba84dd96eea1444ecd3c45e2b47614f2facca22/docs/collab/chatgpt/reviews/2026-10-30_V3_NoTTT_Issue12_DS_External_CPUColdStartProbe_v3_INCREMENTAL_REQUEST_CHANGES.md)。

## 一、P2–P6增量结论（脚本方案/控制流层面）

| Finding | v4提交内容 | 增量判断 |
| --- | --- | --- |
| P1/P3 原作用域/finish/私有Loader API | 保留module-level torch；public `begin()/materialize()`；单Request用`finally:close`，不调用`finish` | **CLOSED**（v3已关，v4未见回归） |
| P2 计时范围 | `loader_construct_s` / `worker_startup_s`（含`begin`的iterator创建）/ `first_materialize_s` / `first_packet_total_s`分开；Scope B显式`prewarming.scope_a_ran_before=true` | **CLOSED_AS_DESIGN**；全部是Parent端墙钟，不是Worker内部逐阶段Timer；预热限制明确，不能据单Worker成功排除32Worker失败 |
| P4 请求来源 | `PARTIAL.request.scope=`representative initial rank0，不是9600恢复首请求 | **CLOSED_AS_DESIGN**；资料§3一个句子仍留有“identical to Arm B rank 0”后紧接否定注释，属文案不一致，非代码行为blocker |
| P5 外部超时/输出保护 | 明确`timeout -k 120 1800`；独立输出`/mnt/data/shenzhen/szrobot/logs/issue12_coldstart_diag`（据DS称238GiB空闲）；stdout/stderr用`>`、`2>`保存；SIGTERM Handler尝试own Loader关闭和进程收尾 | **CLOSED_AS_DESIGN**；空间数据与清理成功仍是DS现场报告，不能保证任何loky后代绝不残留。外部超时不意味着总Host RAM限制（报告已如实降格） |
| P6 中断可定位性 | `_stage_start/_stage_end`在ScopeA各`source_reader`等阶段、ScopeB`loader_construct/begin/materialize`前后及时`flush=True`，全局`PROGRESS.current`、部分失败JSON和独立日志保留 | **CLOSED_AS_DESIGN**；父进程Scope A的原始SFT Dataset预检阶段仍未统一START/DONE，但此轮要诊断的是随后Worker构造/首包，作为LOW可选加计时，不阻断本有界探针 |

### 关键边界

- *Stage Scope A* 是Parent内模仿Worker构造阶段，不能冒充真实Worker内`AsyncRecipe.build`分阶段时钟。*Stage Scope B* 测到实际spawn后单Worker首包的端到端Parent墙钟，但Scope A已预热OS cache；仅此仍**无法严格分解真实4rank×8worker失败中所耗具体环节**。
- 即使`--end-to-end`的Loader返回Timeout，脚本`PARTIAL.status=ok`也只代表诊断流程运行完成，须以`PARTIAL.phases.real_worker_first_packet.status`判定首包是否成功，不能将诊断完成误读成Loader PASS。
- 源/Cache/VerifiedIndex Digest校验不等于`iter_000009600`的模型、优化器、Frontier身份核对；本probe不加载DCP。源码里硬编码的`config_digest`如果没有原始正式Preflight witness，只能视为diagnostic parameter，不能据此称严格训练状态parity。
- 代码段审查时只涉及Frozen Child真实 `NoTTTAsyncLoader` / `AsyncRecipe.build()` / `NoTTTCpuLoader._shutdown` 的最小入口核对；GPT**没有运行任何CPU真实数据/GPU/模型/训练、没有改生产代码**。

## 二、当前唯一正式阻断：新原件字节审计缺件（EVIDENCE ONLY）

**EVIDENCE-12-PROBE-v4（MEDIUM）**；对象`issue12_worker_coldstart_probe.py:1–528`及 DS指出的 `issue12_coldstart_probe_v4_review.zip`：

- **根因**：所收“脚本原文”是格式变化的大粘贴，不是原始`.py`字节；用户未上传ZIP。文本在`__future__`/`__doc__`等Python语法处被破坏，原始文件SHA无法验证。
- **违反的验收要求**：本Gate需要绑定DS实际将执行的**精确脚本SHA**、可复核语法和最终启动命令；仅根据描述不能独立确认运行时的source对应性。
- **关闭条件**：Owner把DS已打包的 `cpu_diagnostic/issue12_coldstart_probe_v4_review.zip` **原件**作为文件附件上传本会话（不是复制其文本）或单独上传原始`.py`，并提供zip内文件的精确SHA256。GPT只对当前v4做**字节哈希、语法AST/compile、关键控制流和diff**最小复核，不要求写v5、不重复上一轮production源码/CPU301，也不要求重跑DS已报告的smoke。若原件可证对号，直接关闭此Evidence-only Gate。
- **权限**：`SCRIPT_SOURCE=NOT_VERIFIED`、`REAL_DATA_CPU=NOT_AUTHORIZED`。即便关闭源脚本Gate，仍需要Owner另行授权一次隔离、有外部timeout的真实CPU探针；不能自动开始Probe、GPU A/B、切换正式训练或更改原DCP。DS可继续维护其仓库外脚本；仓库内任何源码更改只由Codex负责。

**本轮明确不要求新的v5或无意义的其他测试；只补原始ZIP。**
