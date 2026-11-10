# Issue35 K16 首次慢段/长尾：诊断工具交接

2026-11-10 Asia/Shanghai。**本轮仅外部探针/CPU；根因UNKNOWN，稳定性Gate OPEN，没有新模型优化、GPU结果或V3合并。**

生产仍为 Formal Root `1b184204e301a51a7a20ed4dde1a11689589cf2d` / Child-Gitlink `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`。PR38/14继续Draft；此诊断分支/文档HEAD不构成新生产配对。

## 已同步的独立批准与开放项

本轮Root before74b48c6；fetch后advertised/tracking均e403fb8a，列出379f1856/e403fb8a、ancestor0并ff-only。完整读取正式 `2026-11-10_Issue35_K16_1b184204_d5c1ffc7_RequestLocalProjection_IndependentReview.md` 和Issue35评论6762151776，并记录于SESSION。

既有独立CPU314/11static/1487指纹、K16四路径原始Action/Vision/raw15及三路30步velocity exact已限域APPROVE_CODE，不重复其Gate。热态同进程30配对节省P50=33.853ms且29/30较快有效；首次约22次890–900ms慢段及50次复验最大1295.667ms不能删除。unique_graphs=8稳定不证明CUDA图、库调用、设备时钟或主机调度稳定。

## 本轮交付范围

新隔离Root分支 `v3-local-prefix-latency-issue35-20261110` 基于e403fb8a。Child继续d5c1且干净；既有1487源码指纹逐项与批准Pair的归档比对相同。只修改SESSION/TODO/append-only Inbox，新增自有外部诊断probe/测试、CPU证据与执行说明；没有生产路径或编译配置改动。

`latency_probe.py`在现有generate方法的编译外层观测，不额外执行模型或修改输入/RNG/输出。复用服务器现有 `benchmark_new_on_dynamo.py`、`benchmark_projection_paired_K16.py`；只查看了目录/CLI声明，没有复制它们或私有请求、DCP、Tensor、trace。

每请求关联Host wall、process/thread CPU、schedstat/page faults/context switches、GC、已有Dynamo计数、CUDA allocator及可选事件跨度。事件异步查询，不新增同步；失败显式记录，未就绪不补0，原异常优先保留并恢复method/GC callback。CLI要求clean精确Pair、工作树外工具/输出、显式K16/source64；不满足不启动runner。完整runner参数/哈希和前后身份保留在执行侧。

## 作者CPU与局限

- 最终 **34/34 PASS、0失败/错误/跳过、Shell0**，两文件Ruff E/F/I及format通过，无例外。测试覆盖原调用和输出身份、Torch/Python RNG/grad、异常/SystemExit/KeyboardInterrupt、无CUDA初始化/同步、异步事件关联、诊断写入/查询失败、GC及继承方法清理、原runner/argv复用和Source/K16/重复参数拒绝。
- 首轮26PASS与最终34有重叠；dev02两项样式失败保留，pytest未执行，不把不存在的测试算PASS。各自源文件/日志/JUnit均归档，不改失败历史。
- 测试使用CPU Tensor、模拟CUDA和模拟CLI身份；没有真实模型、CUDA context或新H100实验。当前硬件兼容性、观测扰动、能否复现及实际根因均未证明。
- Host调用时间不含原runner随后同步；CUDA event跨度含idle并非Kernel之和。插桩分配/回调/写日志可影响CPU/GC与原runner计时，不能把插桩结果代替未观测性能或精确相加减归因。

可再生命令、输出字段、完整边界、输入恢复及停止条件见[诊断执行说明](../evidence/2026-11-10_issue35_latency_diagnostics/README.md)；[CPU摘要](../evidence/2026-11-10_issue35_latency_diagnostics/cpu_summary.json)和原始日志/测试/来源索引一并保留。此前完整314项不重跑，不新增旧W0/I001例外。

## 下一步仅GPT真实K16诊断

先审核这个外部探针，按上轮原命令恢复实际解释器/iter15000/config/frozen/reference，保持BF16/compile模式/recompile_limit8、verify_source和设备校验。先启动所选GPU的聚合遥测，再在同一时间轴做一次4warmup+50连续ON；所有原严格Action/Vision断言保留。需要时才做既有同进程ON/OFF交错、无事件/未插桩控制，或有CUDA/OS runtime轨迹的单独复验；不盲目多轮重跑。

必须把慢/快样本与Host排队/GC、allocator、设备时钟/功率、CUDA图/库调用/Kernel时间线对上，才提出相应最小修复。Profiler和日志模式有扰动，单列不混入性能分布。无关联或不复现则INCONCLUSIVE，性能稳定性/P99保持OPEN；不得增加warmup隐藏慢段、删除离群或叠加Attention优化。

所有原始数据和新trace只在授权服务器；Codex仍不启动GPU、训练、K1/No-TTT、Sim/SR/900EP或管理其他任务。没有V3合并授权，旧Code/数值APPROVE_CODE原样保留。
