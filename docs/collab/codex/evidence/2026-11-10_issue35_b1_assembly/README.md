# Issue35 B1 Prefix K/V 组装优化 — 作者 CPU Evidence

Formal Root `39f60da729a49c9f6514953bf801dcafb7493039` / Child-Gitlink `4be3d702f3008040b830ae09c200d80e273a201a`。

作者状态：**CPU 292/292 PASS；静态11文件；1487源码指纹不变；Shell0**。历史W0单独deselected，没有算作PASS；原3个I001例外保留，新两文件无例外。**独立代码审核、真实H100数值、实际性能和V3合并均未通过此作者结果自动获得。**

[完整窄增量审核申请](../../reviews/2026-11-10_Issue35_B1_Assembly_39f60da7_4be3d702_Review_Request.md)。

| 路径 | 内容 |
| --- | --- |
| `raw_cpu/author01/` | exact clean Pair 完整scoped Gate及两新文件静态检查，原始命令/环境/日志/JUnit/身份与指纹 |
| `raw_cpu/red01.log` / `red01.xml` | 旧生产代码的确定性预算负例，真实 cumsum1/repeat2/index_copy4，Shell1 |
| `raw_cpu/focused01.*` | 新实现整个memory_prefix_test.py 101项通过；与292项重叠，不累计 |
| `raw_cpu/red_identity.json` / `red_fixture.py` | 旧生产身份和当时完整测试文件；测试新增导致dirty，不称clean Formal Gate |
| `raw_cpu/regression_provenance.json` | 新旧测试文件byte-identical、原通用尾部byte-identical、生产模块移除单一快分支后AST相同 |
| `probes/baseline_memory_prefix.py` | parentbf707原公开生产源，用于静态provenance核查 |
| `probes/cpu_gate.py` | 作者CPU包装脚本：复用既有scoped Gate，加两文件严格静态检查 |
| `evidence_index.json` | 本目录所有发布文件大小/SHA256（不含索引自身） |

只有1个生产函数新增24行；原通用路径保留，梯度开启/非B1/不满足条件的布局回退。CPU对60组长度/padding/dtype/offset组合、当前Prefix、梯度、多样本、无Prefix、错误拒绝与fullgraph等完成验证。全部真实业务张量、模型、图像及Profiler仍仅在原服务器；本轮没有连接或读取服务器，没有新增真实GPU/NoTTT/Sim/SR实验，也不管理人工负载。

原始RED traceback的行尾空格按原始字节保留，发布whitespace检查只排除该日志和JUnit；其余文档与工具必须通过。
