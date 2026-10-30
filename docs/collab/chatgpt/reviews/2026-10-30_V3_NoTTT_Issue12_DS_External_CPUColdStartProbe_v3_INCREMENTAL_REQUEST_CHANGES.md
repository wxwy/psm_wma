# PSM-WMA V3 No-TTT Issue #12 — DS 仓库外 CPU Cold-Start Probe v3 增量复审

- 日期：2026-10-30。
- **本次增量脚本审核 verdict：`REQUEST_CHANGES`**；脚本只在DS服务器仓库外，**`REAL_DATA_CPU_PROBE=NOT_AUTHORIZED_TO_RUN`**。本Verdict不是冻结生产代码新Gate。
- **原 Formal Production Pair 不变**：Root `e0fe911dfb9fd34957234828195cf051713f6c3d` / Child-Gitlink `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`。该Pair既有`APPROVE_CODE`与Issue#11独立301CPU/6raw PASS均不重审、不变更。Issue#12真实GPU的B首包120s Timeout/0commit、性能INCONCLUSIVE状态保持。
- **审核对象**：Owner本轮上传`粘贴的文本 (1)(20261030-101828).txt`，内含DS自述`issue12_worker_coldstart_probe.py rev v3`、v2→v3 diff、说明文档。DS报告脚本SHA-256 `5eea42983a88ca823b2419e69a18fa6d0016cdc0bc252942488c3eeaca68d9c4`，Ruff/py_compile PASS。
- **字节一致性边界**：当前大粘贴文本本身的Python部分被Markdown格式化成`from **future** import annotations`、`description=**doc**`、嵌入 ``` 及取消缩进。GPT对**收到的大粘贴文本**程序化尝试`compile`在第51行SyntaxError；这说明**粘贴转码内容不可直接当独立可运行的原始.py**，并不证明DS原本的`.py`文件有SyntaxError。该粘贴不能独立验证DS报告的原`.py` SHA和py_compile结果。若要形成精确脚本Source Gate，DS需另交真正raw `.py`字节（如独立zip附件）及其同一SHA。**不能凭变形粘贴宣称字节级source PASS**。
- [上一轮同脚本 v2 复审](https://github.com/wxwy/psm_wma/blob/f60db0427d5fda6916ffaf0db4353586e6131f34/docs/collab/chatgpt/reviews/2026-10-30_V3_NoTTT_Issue12_DS_External_CPUColdStartProbe_v2_d54ef1b0_INCREMENTAL_REQUEST_CHANGES.md)。
- 审核范围：只检查v2→v3静态控制流和Frozen Child公开Loader行为，没有启动GPU、真实数据CPU、真实DCP、torchrun，未修改任何生产仓代码/临时脚本。

## 旧问题关闭/进展（仅新Delta）

1. **P1（torch模块作用域）`CLOSED`**：v3仍采用模块级torch import，`_require_cpu_only`的NameError不再存在（据修订文本）；要实际验证原始.py需新raw文件。
2. **P3（partial window调用finish与private API）`CLOSED`**：v3 `phase_real_worker():339-368`改公开`loader.begin(plan)` / `loader.materialize(request)`，partial window用`loader.close()`（finally），不调用`finish()`。
3. **P2的“漏掉begin-spawn计时”`CLOSED`**：`phase_real_worker():340-358`分别测`loader_construct_s`、`worker_startup_s`、`first_materialize_s`、`first_packet_total_s`。指标是**父进程观察的完整首次请求墙钟**，不是Worker内部`recipe.build()`分阶段观测。注意DataLoader120s deadline只施加在`next(iterator)`，不包括constructor/begin时长。
4. **P4的请求身份措辞 `MOSTLY_CLOSED`**：v3 `PARTIAL.request.scope`明确`representative_initial_frontier_request_rank0`不是正式iter9600 Frontier重放；但说明文档§3第5项仍含“identical to Arm B rank0”，应删除矛盾描述。固定config_digest仍无独立正式训练identity witness，定位为诊断用途不得称完全checkpoint parity。

## 本轮仍需修复的最小 Blockers

### P6 — HIGH：首次耗时构造被中断时仍拿不到分阶段证据

- **脚本位置**：`timed_worker_build():179-230`，`phase_in_process():233-322`，`phase_real_worker():325-369`，`main():382-438`。
- **根因**：`marks`在每个阶段函数返回后才更新，而且整个Scope A只在`phase_in_process()`完全返回后才写入全局`PARTIAL.phases`；Scope B同理。v3新增的SIGTERM Handler `_dump_partial()`只会写**已经加入PARTIAL的数据**。若恰在`RoboCasaExactWindowSourceReader`、Tokenizer初始化、`loader.begin`或`loader.materialize`里卡满外部1800s，Signal Handler并不能说明当时处于哪一个高成本阶段；“a timeout never loses the evidence”的声明并不成立。
- **冻结诊断目标违反点**：本探针需要定位120s首次Packet阻塞所在阶段，不能只知道大Scope未完成。
- **最小验收**：在高成本阶段**进入前+成功后**输出带`scope/stage/event(start|finish)/pid/UTC或monotonic timestamp`的单行JSON，`print(..., flush=True)`；至少包括parent dataset、scopeA source_reader、scopeA async_worker_state、scopeB begin、scopeB materialize；外部原始stdout/stderr须落地。遇到SIGTERM/异常可由最后一个stage_start定位卡点。无需新增监控框架、禁止改Frozen Child生产源码。

### P5 — HIGH：外部硬超时和日志隔离在提交命令中尚未完整落实

- **位置**：说明/命令 §4（粘贴行1325–1340），脚本 `main():382-385`，`_install_signal_dump():131-142`。
- **实况**：v3的启动命令已有`timeout 1800`，比v2进步，但没有`--kill-after`（父进程自定义SIGTERM处理通过`os._exit`直接退出，不保证finally清理独立spawn子进程）；提到“redirects stdout/stderr”但实际示例命令中没有`>log 2>&1`或`tee`；`--log-dir`、`--output`仍位于旧报告占用约99%的`/mnt/data1`同一卷（并非隔离可用`/tmp`）。仅创建子目录不等于新磁盘/有充足空间，也不能代替持续flush日志。
- **冻结风险边界违反点**：DS CPU诊断必须不会危害正在训练的正式进程、必须有有界退出与原始失败Evidence。
- **最小验收**：在已有`timeout 1800`旁加`--signal=TERM --kill-after=15s`或等价进程树保护；`LOG_DIR`/JSON/HF及joblib临时缓存使用经DS实测有空间的独立`/tmp`目录，事先`df -h`确认容量；输出日志真实执行`> "$LOG_DIR/probe.log" 2>&1`或`2>&1 | tee ...`，完整命令、退出码/worker存活检查设计明确；**不要**kill正式训练的任何PID。外部Probe脚本不得直接写入正式Checkpoint/DCP。
- `parent_peak_rss_mib`只是父进程后验观测，不是总宿主机/Worker硬上限；v3已正确降格，勿为此引入新RSS框架。

### P2 remaining — MEDIUM：真实Worker测试仍由Scope A提前预热

- **脚本位置**：`main():394-417`，`phase_in_process():300-307`。
- **根因**：`--end-to-end`仍强制先运行Scope A的完整Dataset重建、`AsyncWorkerState.prepare(request)`读取真实数据，再于同一解释器执行Scope B Worker spawn。Scope B Worker进程确实是新spawn，但模块导入/OS page cache/源数据文件已被Scope A预热，故其`first_packet_total_s`不可认定为与原B fresh 32Worker环境等价，也不能由单Worker成功推出32Worker“仅资源竞争”。
- **最小验收**：最好增`--scope {a,b}`只运行一个Scope的独立Python进程；Scope B仍需创建parent catalog/producer/planner，但应跳过Scope A的模拟worker build和first real prepare。若DS坚持不改，须明确标为`spawned_worker_after_parent_warmup`，**仅探索辅助，不作冷启动排除证据**。不会要求重做全4Rank实验。

## 非阻断/统计口径

- 全局`PARTIAL.status=ok`和`scope B.status=RuntimeError: DataLoader timeout`可以共存，需明示这是“探针已完成并记录超时”不是“Loader首次取数成功”，防止自动化读取误判；可改为`diagnostic_complete_loader_failed`但不要求新Gate。
- v3使用`initial_frontier()`取代表性请求，供单Worker冷启动诊断可接受，但不能以此声明正式iter9600数据/模型/RNG严格恢复一致。Digest硬编码只做本诊断参数来源声明，不对完整DCP/训练态给PASS。
- 仅有父进程构造分解+真实Worker首包墙钟时，仍不能严格确认真实Worker内部哪个constructor慢；报告要把Worker内部阶段写`NOT_MEASURED`而非推导成实测。

## 执行/角色边界

- **`SCRIPT_v3=REQUEST_CHANGES`，`REAL_DATA_CPU_EXECUTION=NOT_AUTHORIZED`**。DS可以修改自己机器上**仓库外**临时诊断脚本；仓库内代码只可Codex变更。修复以上最小问题后交**真正raw .py字节**、SHA、最小diff/静态检查和更新过的冻结**未执行**命令给GPT窄复审。
- 不重审旧Production Formal Pair和CPU301；不改源Loader timeout、不起4GPU A/B、不停正式NoTTT训练、不碰原DCP/Checkpoint/Cleaner，不触碰EvalV2。
