# Issue35 Text-KV hit 数值修复：作者证据

Formal Root `55b74ab461fda27e4ff6490023c828db0abc0a9f` / Child-Gitlink `bf707810f573e885f0966d65c232dc2a610d6a93`。作者 CPU 213/213 PASS；K1/source32、K16/source64 真实 H100 三路径最终 Action/Vision/raw15 及所有 30 步速度均严格相同。**不是独立审核结论或 V3 合并许可；没有性能结论。**

[完整增量审核申请](../../reviews/2026-11-10_Issue35_KVHit_PrefixNorm_55b74ab4_bf707810_Review_Request.md) 说明首差异、修复边界、旧失败及限制。

| 路径 | 内容 |
| --- | --- |
| `raw_cpu/author01/` | exact clean Pair 的原始 JUnit/log、命令、环境、1487 项前后指纹、gate.json |
| `raw_cpu/old_norm_red01.*` / `new_norm_green01.*` | 受控归一化舍入负例及新实现结果，旧 FAIL 不改写 |
| `raw_cpu/old_norm_red01_case.py` / `regression_provenance.json` | 旧受控测试完整文件与新旧相同测试函数 AST、原三生产文件 SHA 的静态绑定 |
| `raw_cpu/observer_*` | 为什么观察编译函数不能复制 Dynamo 原函数 metadata 的 CPU 复现，不是生产代码修复 |
| `probes/` | Codex 编写的诊断、回放、派生统计脚本；之前未完成版本一并保留 |
| `derived/server_derived_summary01.json` | 服务器上对私有原始证据计算的数值比较、哈希、源码身份及资源清理；不含张量值 |
| `derived/author_h100_commands.json` | 两次 H100 作者 Gate 的精确启动命令，第一次夹具失败仍保留 |
| `evidence_index.json` | 本目录发布文件的 SHA256/大小（不含索引自身） |

CPU：原201项加12项回归，213 PASS、0 failure/error/skip；1个历史 W0 assertion 仍 deselected，不计PASS。原3个 I001 例外保持。受控旧 RED 是仅测试增加的旧生产代码，不能称为 clean Formal Gate。

H100：三模式都是同一个 iter15000 Local-TTT 模型且 Prefix ON，不是 No-TTT；仅 KV/Pack 开关不同。每种模式恢复同一冻结完整请求与原生 prepared，不重新编码视觉或修改输入。先生成无包装输出，再从 `_get_velocity` 外部记录30步，并要求 observer 不改变最终输出。`author_h10002` PASS/Shell0/source+input unchanged；`author_h10001` K1通过后因 K16缺省K的外部夹具KeyError失败，未执行K16，原记录未覆盖。

原始服务器张量/PT、图像、checkpoint、FX/code、模型日志均仍在 `data` 私有目录；这里发布的是作者源码、本地合成 CPU 证据和派生哈希/统计。私有844文件索引 SHA256=`1833504e303cedcfd87a065e921845afb36c1ebbc5d5c68c260f715ce656d623`。

原始 RED 的 pytest 日志和 JUnit 内含 traceback 自带行尾空格，按原始字节保留。发布 whitespace 检查只排除这两份原始文件，其余文档和工具必须通过；生产代码检查范围不变。
