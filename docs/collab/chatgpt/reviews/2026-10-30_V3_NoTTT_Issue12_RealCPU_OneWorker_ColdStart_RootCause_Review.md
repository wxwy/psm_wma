# No-TTT Issue #12 — 实际 CPU 冷启动定位 Evidence Review

2026-10-30。**结论：DIAGNOSTIC=PASS_REPORTED_STRONGLY_SUPPORTED；ASYNC_STARTUP_BOTTLENECK=HIGH_CONFIDENCE；GPU_PERFORMANCE=INCONCLUSIVE。**

冻结的生产 Formal Root e0fe911dfb9fd34957234828195cf051713f6c3d、Child/Gitlink f6a92d47b6dac7998ddc58b3da26ef93f8068dc7 不变；原 APPROVE_CODE 和 Issue#11 CPU301/六份Raw PASS保留。这次是对DS实测报告和冻结源码调用链的增量审核，不是新代码Gate，不触及仿真线。

**证据来源：** Owner转来的 DS_PRO 真实数据 CPU-only Scope A+B 执行报告。原始 probe_scopeA_plus_B.json、stdout、stderr在DS服务器，GPT未从该服务器取回文件字节，故实测数字均标记为 DS_REPORTED，不声称GPT现场重复测量；Owner已指出文件转运不可行，**不要求再复制ZIP/raw或再次运行Probe**。

| 阶段 | DS报告 | 证据语义 |
|---|---:|---|
| ScopeA：进程内模拟Worker完整构建 | 193652.7 ms | Parent进程近似、不是实际Worker内部定时 |
| SourceReader构建 | 192970.6 ms | 占完整构建约99.648% |
| LeRobotDataset init | 188782.1 ms | 占完整构建约97.484% |
| 首个Request的state.prepare | 224.5 ms | Parent近似、不是实际Worker |
| Transform pipeline构造 | 409.4 ms | 构造成本，非每条样本Transform |
| AsyncWorkerState构造 | 42.5 ms | 同一近似路径 |
| ScopeB：真实单Worker first_materialize | 120.249 s / Timeout | 已经过ScopeA预热，但仍没有首包返回 |
| ScopeB：constructor+begin+first_materialize | 120.266 s / Timeout | 超时退出所用Wall，不是数据Packet完成时间 |

**源码交叉核验：**
- cosmos_framework/trainer/no_ttt_async_loader.py:124-135：PreparedDataset在第一个__getitem__时调用self.recipe.build()；:245-295在PyTorch iterator发起请求并等待next；profile timeout120s。
- cosmos_framework/trainer/no_ttt_async_recipe.py:195-254：每Worker重开Index/Cache/SourceReader/Transformer/Tokenizer/Producer。
- cosmos_framework/data/generator/action/datasets/robocasa_exact_window_source.py:247-258：SourceReader构造函数立即初始化非视觉LeRobotDataset；:459-505通过官方dataset[relative]读取17帧delta数据并核严格identity。不能简单删掉Dataset而改变序列/文本语义。

**独立判断：** 真实单Worker复现Timeout，排除“必须32Worker同时启动才会导致Timeout”。SourceReader/LeRobot eager初始化是强烈支持的首要修复点，足够启动Codex窄修设计，不需新探针。但是ScopeA的193s并非ScopeB真实Worker内部逐阶段计时，也不能排除同期正式任务IO/CPU争用；不把DS口头“唯一根因100%证实”升级为绝对因果断言。

因persistent_workers=true，该昂贵构建发生于每Worker首次取样，并非每训练Step重复；修复首包Timeout不等于证明GPU steady-state加速。旧Issue12：A Compact1/nw0从9600连续20次optimizer commit PASS；B Compact1/nw8加载DCP后0 commits、性能INCONCLUSIVE，未改变。

**Verdict：READY_FOR_CODEX_NARROW_FIX_DESIGN；不授权立即停止正式30k任务、改现役Checkpoint、合并V3或执行GPU。** Codex设计交接见同日期 requests/2026-10-30_V3_NoTTT_Issue12_Codex_LeRobot_WorkerColdStart_NarrowFix_Handoff.md。
