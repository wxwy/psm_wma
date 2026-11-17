# G2-C 作者 CPU 证据索引

最终代码：Child `26243dae9be7a2ab7ef5d544f8759b398ce917f9`；固定依赖 `6d72d4d252c287fc8060bdc5a8db7f6cf959af1e`。Root V3/Gitlink 未改；不是 formal integrated pair。

| 目录/文件 | 含义 |
|---|---|
| `final02/` | 最终固定源码：405 PASS、1 SKIP、32 subtests PASS、22模块；唯一skip为旧真实资产预检无路径 |
| `final02/junit.xml` | 原始 JUnit，406 testcase节点；subtest不另行累加到405 |
| `final02/pytest.command`、`test_modules.txt` | 实际命令和精确模块清单 |
| `final02/runtime_and_protection.json` | 现有环境版本、固定来源、30个A/B/D保护blob |
| `final02/source_before.json`、`source_after.json` | 1149份tracked Python/config指纹相同，Child运行前后clean |
| `final02/actual_*parameter_inventory.json` | CPU fixture及A Reader＋tiny B的实际逐参数清单；不是完整Edge/FSDP |
| `final02/incomplete_recipe.log` | 未填正式值的模板拒绝，exit=2；没有补成正式参数 |
| `final01/` | 旧a911候选404 PASS/1 SKIP；之后增加显式配对LR horizon，不作最终结果 |
| `author_iterations/` | 保留早期失败、修复和开发测试；不与最终计数相加 |
| `c_after_B_6d72.patch` | 相对已集成首批C文本/adapter的B固定依赖，16文件最小C后继增量 |
| `c_owned_history.txt` | 四个C原创提交，依赖merge另见Git历史 |
| `run_cpu.sh` | 现有环境CPU复现；要求显式SHA、clean Child、新输出目录，不安装依赖 |

真实DATA_B/C、完整G1 checkpoint/Edge inventory、CUDA/BF16/FSDP、正式R1/R2、全量评测 **NOT_RUN**。CPU两rank使用Gloo，不是FSDP。A/B组件以CPU reference attention运行，数据/部分网络/损失边界明确使用fixture；详见[交接](../../reviews/2026-11-17_G2_Model_C_Training_Handoff.md)。

开发失败处置：text01/02为synthetic sample字段与mask collate wrapper问题；train01为旧入口source-string回归，恢复原判断结构，未改旧测试；dev02为新增组件误将B `(pack, metadata)`返回值当pack，修正测试调用。dev03是开发组合检查，不能替代固定源码证据。final01之后的显式horizon修正有新增R1/R2实际LR序列测试，最终仅采用final02。

`SHA256SUMS`覆盖本目录除自身外的全部证据文件；原始日志/XML复制保留字节，不重写历史失败记录。
