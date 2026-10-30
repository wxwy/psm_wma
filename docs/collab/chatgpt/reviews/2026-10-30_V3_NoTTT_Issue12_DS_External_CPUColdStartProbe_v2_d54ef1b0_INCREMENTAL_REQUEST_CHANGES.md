# Issue#12 — DS 仓库外 CPU Cold-Start Probe v2 增量复审

- 日期：2026-10-30。**VERDICT：`REQUEST_CHANGES`（只针对本次仓库外 v2 临时诊断脚本；不授权实际运行）。**
- **Frozen 生产 Formal Root** `e0fe911dfb9fd34957234828195cf051713f6c3d`；**Child/Gitlink** `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7` 均**未变**。已通过的原生产 Code Gate `APPROVE_CODE`、Issue#11 CPU301/6raw `PASS`不重审。Issue#12 Real ArmB 120s Timeout / 0 commit、性能INCONCLUSIVE的真实Gate未关闭。
- **唯一此次审核目标**：DS 上传的 `issue12_worker_coldstart_probe.py` v2 （附 v1→v2 diff、PLAN ONLY说明）。对用户上传 `粘贴的文本 (1)(20261030-090714).txt` 直接逐字节提取 Python 内容，统一 LF、结尾一个LF得到 **18,378 bytes；SHA-256 `d54ef1b006bbf99bc4aedef633f8adf267b2d67334e993bcd1ac21526f096795`**，与DS宣称v2 hash匹配。Python AST/compile静态检查 `PASS`，**未导入项目、未执行真实数据CPU、GPU或训练**。
- [上一轮外部 v1 脚本审阅](https://github.com/wxwy/psm_wma/blob/41043ae973050a197244dd364ad8ebb340653ad2/docs/collab/chatgpt/reviews/2026-10-30_V3_NoTTT_Issue12_DS_External_CPUColdStartProbe_5215bf11_REQUEST_CHANGES.md)。本轮只看v1→v2整改及新发现，不重复已经冻结的生产源码技术Gate。
- Owner最新角色分工：**DS可修改其机器上仓库外的临时诊断脚本；仓库内任何代码修改仅Codex**；GPT给出审核指导。参见 [Issue#12角色修正](https://github.com/wxwy/psm_wma/issues/12#issuecomment-6518734306)。

## 已关闭的旧 Blocker

1. **P1 `CLOSED`（原HIGH：`torch` NameError）**。v2 `issue12_worker_coldstart_probe.py:47` 模块级 import torch，`_require_cpu_only():139-141`不再读不存在的模块变量。正式运行仍需外层shell先掩蔽CUDA。
2. **P3 的“无效 `finish()` + 无finally”部分 `CLOSED`**。v2 `:358-365` 仅在部分Window后 `loader.close()`，不再调用必须完整消费Window才能调用的`finish()`；finally对异常尝试清理。旧P3的**私有入口**`_begin/_materialize`仍未整改，见下项。
3. **P2 的“命名混淆”部分 `IMPROVED`**。输出明确区分`in_process_worker_approx`与`real_worker_first_packet`，但实际真实冷启动计时漏项仍在。

## 当前最低限度 Blocker（不要求新架构/重做旧CPU Gate）

### P2 — HIGH：PhaseB首包总耗时不包含Worker Spawn；Scope A预热Scope B

- **脚本 `:335-353,385-390`；实际冻结Child `cosmos_framework/trainer/no_ttt_async_loader.py:245-285`**。
- v2依旧先执行`loader._begin(plan)`（其中`iter(self.loader)`会实际启动worker），然后才`started=_now()`。所以`first_packet_wall_s`**不包含worker spawn/iterator startup**，与文件顶端和方案“including spawn+IPC”的声明冲突。真正复刻失败要至少分别测`construct_s`、`begin_spawn_s`、`materialize_wait_s`、`total_to_first_packet_s`；不要把`DataLoader timeout=120s`误解成覆盖全部启动阶段。
- **Scope B永远在同一进程的Scope A之后**；Scope A已完整构建SourceReader、LeRobotDataset并读一次真实Segment，可能预热Python import、磁盘页缓存与Tokenizer。将后续ScopeB结果认定为真正 cold-start将造成虚假阴性（单Worker在warm环境成功不能排除fresh nw8 timeout）。要么让B在**独立新Python进程**启动并跳过ScopeA的第二套模拟重建，要么明确标成`real_spawn_worker_after_parent_warmup`，从而仅作为有局限的辅助对照，不能用于最终“冷启动已排除”结论。
- **修复验收**：时间线分别捕获`loader construction`、`begin`、`first materialize`，有同一时钟域总耗时；ScopeB的冷热条件准确，不能以`first_packet_wall_s`冒充spawning cost。仅测parent replay不能推断Worker进程内`recipe.build()`分阶段耗时。

### P3-remnant — MEDIUM：仍绕开公开Loader API

- **脚本 `:344-349`** 使用 `loader._begin(plan)`、`loader._materialize(request)`；冻结Child公开`begin/materialize`包装负责在异常时关闭Worker。
- **修复验收**：替换为`loader.begin(plan)`、`loader.materialize(request)`（配合现有`finally close()`；不调用`finish()`），或者解释为何必须调用私有入口并验证失败清理效果。只要是外部probe改动，不需变更冻结Child。

### P4 — MEDIUM：真正的iter9600 frontier和config身份并未复现

- **脚本 `:56,316,345,395-409`，方案 §3/§6**。
- 仍使用 `planner.initial_frontier()` 的初始rank0 request，不是原ArmB从`iter_000009600`的持久Frontier恢复所消费的`C+1`请求；文档第855–857行仍称“identical to Arm B rank 0”。这对阶段成本的代表性测量并非致命，但**身份归因结论必须降级**。
- 固定输入 `config_digest=3b2b5a2d...` 未在v2提供同原正式Job的独立已冻结witness（`AsyncRecipe.from_producer`只是传递此字面值）；Source/Cache/Index digest检查不能证明和10月30日原运行完全同一训练状态。
- **修复验收**：说明`representative_initial_rank0_request_not_iter9601_replay`；标记digest的已验证原来源或`UNVERIFIED_DIAGNOSTIC_DIGEST`，不读取24GiB DCP、不强行做额外模型训练。

### P5 — HIGH：报告的1800s/RSS“强制上限”并非实际可靠硬保护

- **脚本 `:69-98,123-130,144-151,184-188,280-321,364-365`；方案§4命令第885–893行**。
- `Deadline.check()`仅在 **阻塞构造阶段结束之后**检查，无法中断卡在`RoboCasaExactWindowSourceReader`或`AsyncRecipe.build`中的调用；`RssMonitor`只读主进程 `RUSAGE_SELF.ru_maxrss`、也是阶段后检查，**不覆盖子进程RSS，也不是硬内存上限**。默认`RLIMIT_AS`关闭。
- v2命令仍**没有外部 `timeout`**、未落实对整个探针进程树的上限/清理规则；输出位于先前报告近满的 `/mnt/data1`、未落实独立可用空间/cache限制。
- **修复验收**：拟执行的完整命令真正包含外部 `timeout --signal=INT --kill-after=15s 2000s ...`（或等价安全有界机制），说明超时与自身子进程清理；真实CPU使用独立、经free-space核查的临时输出和HF/joblib缓存路径。把监控称`parent_RSS_observation`而非总RAM hard cap；如需要硬限制，由经过许可的OS/cgroup约束提供，不能把低风险的软监控谎报成强制资源限制。无需添加新框架。

### P6 — MEDIUM（新发现）：失败发生时无法输出最有价值的分阶段证据

- **脚本 `:184-188,199-201,280-321,429-432`**。
- `marks`只在函数成功返回后写入结果；整个JSON只在`main()`结束时输出。若诊断目标恰好出现某个阶段超时、Reader抛错、RSS检查失败或外层hard timeout，**已经完成的分阶段时间和正在执行的stage不会持久化，probe可能只剩一个Traceback**，导致不能回答“时间到底花在哪里”。
- **修复验收**：至少在每个高成本阶段**开始/完成**向独立stdout/stderr流输出带UTC时间、PID、scope、stage、单调耗时的轻量event（`flush=True`）并用`tee`保留到外部日志；出现异常时能确定最后开始但未完成的阶段。无需复杂仪表架构。

## 执行权限与职责

- **`SCRIPT_v2=REQUEST_CHANGES`；`REAL_DATA_CPU_EXECUTION=NOT_AUTHORIZED`。** 即使静态修完并经GPT批准，也仍需Owner对新真实数据CPU探针**另行明确授权**。无已授权GPU/torchrun/DCP/正式NoTTT job停切或数据写入。
- DS负责自己**仓库外临时脚本**的P2/P3/P4/P5/P6窄整改、返回新SHA/diff和静态检查、真正未执行的冻结命令；**不能**修改生产仓库代码、Gitlink、launcher、tests。GPT做新脚本SHA窄复审，不再重做旧Formal Pair源码或CPU301。
- 本次尽量只修**2个严重测量/资源Blocker + 3个小项**，不得转成多层性能框架或强推项目V3。若DS已有无Worker真实分阶段timing，保持`NOT_MEASURED`，不得编造。
