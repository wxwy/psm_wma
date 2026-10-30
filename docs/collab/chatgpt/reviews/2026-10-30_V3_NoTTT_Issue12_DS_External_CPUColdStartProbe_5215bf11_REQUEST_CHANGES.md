# Issue #12 — DS 独立 CPU-only 冷启动探针方案/外部脚本审核

**2026-10-30（Asia/Shanghai）**  
**VERDICT：`REQUEST_CHANGES` — 只针对外部诊断脚本与执行方案，**不批准本版运行**。  
**冻结 Production Formal Pair 未变：** Root `e0fe911dfb9fd34957234828195cf051713f6c3d` / Child+Gitlink `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`；原 `APPROVE_CODE` 与 Issue#11 独立301 CPU/6raw PASS 维持，不重新审核其生产代码/旧测试。真实 Issue#12 GPU/Resume Gate 继续 `REQUEST_CHANGES`（ArmA20 PASS、ArmB DCP load PASS但0 commit、120s 首包Timeout、性能 INCONCLUSIVE）。

**本次新审核对象：** 用户上传的 DS 外部脚本 `issue12_worker_coldstart_probe.py`，实际粘贴文件 `粘贴的文本 (1)(20261030-082855).txt`，**SHA-256 `5215bf115ea48b3cd05d833599b0c6f50fd38a31dbc62601be882ffdd1ce9167`**；以及 DS 书面 `Issue #12 — Deliverable 2: Minimal CPU Cold-Start Diagnostic (NOT YET AUTHORIZED TO RUN)`。脚本未成为新的 Formal Root/Child commit；审核 verdict 不冒充对新 production pair 的 verdict。

**GPT 已执行：** 只读 Python AST+symtable 静态分析（AST PASS，未导入脚本/项目模型/真实数据）与 GitHub 冻结 Child 实际入口核查：`no_ttt_async_loader.py:125–135,170–204,245–285,286–320,382–421`、`no_ttt_async_recipe.py:195–255,260–300`、`no_ttt_cpu_loader.py:437–448`、`robocasa_exact_window_cached_sft.py:172–214`、`robocasa_exact_window_source.py:247–258`、`robocasa_exact_window_local.py:178–181,244+`。未运行任何 probe、真实数据CPU、GPU、训练、DCP、CPU301回放。

## 审核结果：只改脚本的五项最小整改

### Probe-P1 — HIGH：确定性运行失败，`torch` 作用域

- **位置：外部探针 `issue12_worker_coldstart_probe.py:70–72,158–166`**。
- `_require_cpu_only()` 在模块全局作用域读 `torch.cuda.is_initialized()`；`torch` 只在 `main()` 内函数局部 `import torch`。Python词法作用域下全局 `torch` 未绑定。第一次 `timed_worker_build():100` → `_require_cpu_only()` 会 `NameError`，不可能获得 worker build/first packet 表。
- 静态 Python `ast` / `symtable` 独立确认：`_require_cpu_only.torch` 为 global reference、`main.torch` 为 local symbol、模块无 torch import。语法编译PASS不能证明运行入口可达。
- **验收：** 将 torch作为显式参数传入护栏函数或保证环境变量先设置、随后安全导入到模块全局；在任何真实数据构造前可静态/无数据验证护栏真正执行。不得让任何CUDA变可见。

### Probe-P2 — HIGH：并未测量真实 Worker 冷启动的全部阶段，可能错误归因

- **位置：外部脚本 `:75–154,230–238,269–283`**。
- Phase1在当前主进程手工重写 `AsyncRecipe.build`，并未调用真实 `recipe.build()`；其阶段计时从所有 import 结束后才开始，**遗漏Worker spawn/import耗时**，尤其本次已观察到loky/cpp_extension初始化噪音。最多是同一构造链的**in-process warm-path breakdown**，不能认定等价于真实Worker的 `build` 时延。
- Phase2 `started=_now()` 在 `loader._begin(plan)` 后：原始 `_begin()` 会执行 `iter(self.loader)` 启动 Worker，故 `first_packet_wall_s` **不包括 Iterator/Worker spawn**，与方案的“incl.spawn/transport”宣称矛盾。
- Phase2按当前逻辑在Phase1完整构造/数据读取之后才运行，同进程重复/预热模块及页缓存，不能把这次调用标记为全冷启动；若仍沿用这种形式，明确标注 `after_parent_build_warm_cache`。Phase2只有主进程等待耗时，**没有真实Worker内 `recipe.build` / SourceReader / first-packet阶段时钟**，不能据此严格判定120秒的具体组成。
- **验收：** 在冻结生产入口外围做最小、可审计的**外部诊断包装**，测真实 `recipe.build()` 调用和Worker内或一套可验证的入口时钟，并把 `begin() / iterator spawn` 与 `first materialize wait` **分别计时**。若只能保留Phase1复制的构造链，必须将它改名为仅供参考的进程内分解，报告 `actual worker-stage=NOT_MEASURED`，不能升级为根因证据。Phase1/Phase2分开新进程运行或清楚记录已有cache warm状态，禁止拿两者拼接成同一次真实Worker路径。

### Probe-P3 — MEDIUM：Loader API、部分窗口与错误清理不匹配

- **位置：外部脚本 `:272–290`；冻结Child `no_ttt_async_loader.py:382–393`**。
- 仅消费Window的 `plan.members[0][0]` 一个request后直接 `loader.finish()`，必触发 `RuntimeError('async loader cannot finish incomplete active Window')`，这不是本轮冷启动失败；会污染诊断的success/failure状态。
- 直接调用 `loader._begin` / `loader._materialize` 绕过生产公开的 `begin` / `materialize` 包装与异常关闭；`loader.close()` 不在 `finally`，若 `_begin` 本身异常则清理不保证执行。
- **验收：** 用公开 `loader.begin(plan)`、`loader.materialize(first_request)` 做单请求观测；**不调用`finish()`（未完成窗口）**；`try/finally: loader.close()` 对成功、timeout、异常均执行，记录已拥有子PID的cleanup、失败不伪造PASS。保留120s DataLoader超时用于对照，不自动增加deadline。

### Probe-P4 — MEDIUM：请求身份与源摘要“精确复现”表述不成立

- **位置：外部脚本 `:34–46,224–238`**。
- `planner.initial_frontier()` 是**iteration=0**的空frontier；真实ArmB是从 `iter_000009600` 恢复了rank0的持久Frontier。两者首个Request并非据证据相同；报告不得说“与Arm B rank0完全一致”。该脚本若不读取实际DCP sidecar（本轮禁止新DCP访问），可定位**代表性真实request**的构建/首包成本，不能称9601精确Consumer replay。
- `config_digest` 从外部字面常量传入，`AsyncRecipe.from_producer`拿它形成自身digest，随后比较source/cache/manifest并不独立证明该常量与正式训练的 `config_digest`相同。应引用已冻结原始Preflight/launch digest witness；没有就标 `UNVERIFIED_DIAGNOSTIC_DIGEST`，不要静默宣称complete identity parity。
- **验收：** 正确降格 scope（`representative rank0/GA4 request`）并记录episode/slot/segment；保留Source/Cache/Index身份校验，显式标记config digest来源与是否核验，无需为此读取24GiB DCP。

### Probe-P5 — MEDIUM：资源上限未在“拟执行命令”中落实

- **位置：DS方案第4–5节及外部脚本 `:60–63,158–166,269–295`**。
- 方案写“Phase1 1800s、shell timeout2000”但所给命令**没有`timeout`**且脚本自身未设置1800秒看门狗；`maxrss_kib`为事后观测而不是限制；`ulimit -v 12582912`仅为可选，不是已执行限制。首次LeRobotDataset初始化涉及loky等进程，不保证“Phase1实际只有一个OS进程”，`OMP_NUM_THREADS=1`也不能证明下游不会再派生进程。
- 当前方案将输出写入 `/mnt/data1/data_v2_0617/...`（与报告称盘99%满的source同卷），不符合前序明确要求的独立`/tmp`诊断缓存/输出边界，若无空间可能丢失耗时结果。
- **验收：** 提交真正带可验证外层`timeout --signal=TERM --kill-after=...`的完整命令，明确host RAM/子进程数预算、子进程树PID证据及只清理拥有的PID；使用与正式Job/数据集隔离且容量已确认的诊断输出+HF/joblib缓存目录（优先独立`/tmp`），stdout/stderr与阶段结果即使失败仍保存。**CPU探针未获Owner新执行授权，整改/静态语法检查仍不代表执行许可。**

## 重要边界、最终结论

1. 冻结生产代码被独立核查的真实事实：`PreparedDataset.__getitem__`首个请求重建 `AsyncRecipe.build()`，会构建 `RoboCasaExactWindowSourceReader`→LeRobotDataset；导致120秒可能来自worker初始化或机器资源竞争。但**现有/本轮外部脚本无真实时间样本**，不宣称已确证。
2. **当前本探针的 `REQUEST_CHANGES` 是 SCRIPT-ONLY**，不是宣布原 `f6a92d47` 生产源码出现新 blocker；Issue12真实GPU门仍 `REQUEST_CHANGES`，其余Code与CPU301 Gate保持已批准。
3. DS仅修改**仓库外诊断脚本/方案文本**，重新提交文件 SHA256、最小变更行、静态验证（不得执行真实数据/模型）。GPT对修订后的外部脚本做单次窄幅复审，**即使 `APPROVE_SCRIPT`也不自动代替Owner对新CPU真实数据执行的明确授权**。
4. 不得未经Owner许可启动Phase1/2、不重复4卡GPU A/B、不改Loader timeout/Worker数量试验矩阵、不操作生产Job/Checkpoints/Cleaner/V3/Gitlink、不开启仿真线。
