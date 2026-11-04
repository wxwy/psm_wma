# R04 Action 编码动态编译 — 独立窄整改 Code Gate 申请

日期：2026-11-04（Asia/Shanghai）。状态：**AUTHOR_TARGETED_CPU_PASS；GPT Code Gate PENDING**。本任务独立于Issue #17，不包含其尚未合并的streaming实现，也未重跑869项Gate。

| 对象 | 精确版本 |
|---|---|
| 新 Formal Root | `c9fa60b7134fda8fb848c29c148f25c7a8901892` |
| 新 Child / Gitlink | `4e9c8104ffd15a373b576bc35ee608de1b60eea1` |
| Root 基线（当前V3） | `9635cefe3208ab6320ba5fa70b0e0d68fd444790` |
| Child 基线（当前正式Gitlink） | `1069fe78841228cadbbfbe6afbd767eaed6225da` |
| 两仓隔离分支 | `v3-action-encode-dynamic-20261104` |

后续Evidence/ledger提交只作归档，不替代上述Formal Pair。任务认领与[最小设计](../designs/2026-11-04_VFM_Action_Dynamic_Compile_Narrow_Design.md)先于源文件编辑提交。

## 现场证据与可确认范围

Owner报告：R04 iter27700 M8/B8在648/900有效EP（416success/232failure）后停止，RSS预算256GiB；GPU7在`_encode_action`出现`FailOnRecompileLimitHit`，日志守卫为`len(packed_seq.action.domain_id)==1`，随后HTTP409/16invalid/36进程组关闭。**这是Owner转交的现场事实，Codex没有连接服务器或独立回读原始现场文件，不把这次CPU复现称为现场完整原因集重现。** 已提交Core不作任务失败重分类，不报告正式900EP SR。

当前公有基线的函数位置确为`cosmos3_vfm_network.py:1185`。`apply_compile`默认已经`fullgraph=True,dynamic=True`，而`pack_action`及噪声索引处理遍历Python列表；Tensor动态维度不能消除列表长度/结构守卫。这次控制RED在同一旧函数实际触发`FailOnRecompileLimitHit`，其last reason是`action.tokens`列表长度，确认同类机制可达。

## 最小生产变更

Child仅4个文件：

1. `model/generator/mot/cosmos3_vfm_network.py`：把原先连续三条语句（dtype cast → `action2llm` → optional modality embedding）逐句移入`_project_action_tokens`。`_encode_action`仍执行相同pack、timestep、噪声索引与scatter，顺序/精度不变。
2. `model/generator/mot/parallelize_vfm_network.py`：仅将原Action编译目标改为该Tensor-only helper。保留同一`compile_options`，其他四个head、MoT规则、默认recompile_limit8及CUDA graph scope选项均不改。普通默认scope继续fullgraph/dynamic编译；原whole-forward capture的静态策略保留。
3. 新`model/generator/mot/action_encode_compile_test.py`：19项真实CPU编译回归。
4. 原`parallelize_vfm_network_test.py`：stub编译目标名对应新helper，原scope断言全部保留；顺带修复该被修改文件原有import排序I001，无断言放宽。

Root仅Gitlink和任务文档/账本，Root生产代码不变。没有新Module/Parameter、参数树或checkpoint schema变更；不改模型算法、Local Memory更新、Session、Batch调度、Manifest/verify_source/Resume或M/B限制。不提高编译上限，不捕获错误伪装成功，不全局关闭compile。

[静态报告](../../../../artifacts/vfm_action_compile/2026-11-04_cpu/formal-static/static.json)核对了Child实际delta恰4文件、Root实际delta仅上述范围，并用AST证明：原三条投影语句与新helper完全相同；其余`_encode_action`流程除一次helper调用替换外完全相同；`compile_options`字典完全相同。四Python文件的Ruff0.12.7、format、AST均通过。

## CPU Evidence

测试直接import真实`Cosmos3VFMNetwork`、`PackedSequence/ModalityData`、projector及生产`apply_compile`，只构造小型CPU网络与合成Tensor；没有AST提取或替写生产运算。编译计数器只选择CPU backend，实际仍调用`torch.compile`和生产安装器。

| 证据 | 实际结果 |
|---|---|
| 原版受控RED | **4/4预期FAIL**；两local flag × FP32/BF16，8请求/8图后第9请求实际`FailOnRecompileLimitHit`，cap8 |
| 新版长序列 | 4组各**1024请求、1图**；交替B1–8，同时变化clean/noisy、ragged长度、scalar/framewise domain、single timestep元数据；序列内不reset，cap始终8 |
| 真实CPU Inductor | FP32/BF16各32交替请求、2图；输出与eager在约定精度阈值内一致 |
| 旧eager→新eager | 12组合（3projector×2embedding×2dtype）的输出、输入梯度、参数梯度及state-dict键**逐值完全一致** |
| AOT-eager梯度 | 12参数化用例通过；FP32阈值rtol1e-5/atol1e-6，BF16为2e-2 |
| 开发new-green | 51PASS、0fail/error/skip；8 GPU/L1显式deselect；source unchanged |
| **干净Formal Pair最终定向运行** | **51/51 PASS**，其中19新增+32已有；0fail/error/skip、8 GPU/L1显式deselect、exit0、source unchanged1227项；91.05s（pytest86.82s） |

最终运行开始/结束Root/Child均clean并匹配精确Pair；归档是在测试后进行。19新增全部实际执行，deselect只对应这次明确排除的硬件/L1范围。开发与最终运行是重复证据，不累加为102项；外部12组跨版本数值比较也不冒充新增JUnit用例。

同一RED/GREEN新测试字节SHA256：`81486c5ffd75b111a0980fcf9722db472e3e57cce5c438b2045632eb1a3cf34e`。旧production与Child1069 Git对象逐字节相同（SHA256`70fc494d9af8c6fd1b5f93c249781085937fe5471fb4e521bde284f868989df9`）；新production SHA256`ab24fe80768681e0865663442eafc770672b706b019073093b1b671cec0ab3f1`。RED当时有untracked新测试，不冒称整个旧工作树clean。旧eager合成参考Tensor文件SHA256`92759b23ad770c6e3341e2941ace177295592f50609ac5e7e981cc76a09c0941`，不是实际训练权重。

[机器摘要](../../../../artifacts/vfm_action_compile/2026-11-04_cpu/final_summary.json) · [最终JUnit](../../../../artifacts/vfm_action_compile/2026-11-04_cpu/formal-targeted/junit.xml) · [原RED](../../../../artifacts/vfm_action_compile/2026-11-04_cpu/old-red/junit.xml) · [跨版本比较](../../../../artifacts/vfm_action_compile/2026-11-04_cpu/formal-eager/summary.json) · [Child完整增量](../../../../artifacts/vfm_action_compile/2026-11-04_cpu/formal-static/child_delta.patch)。

证据包`artifacts/vfm_action_compile/2026-11-04_cpu/cpu_evidence.tar.gz`：**709061 bytes /81 entries**，SHA256 **`ca0b7bfe2f974ad4db03fe19af28f8969b4f84d2b4c1f1f33227bdbee574f45c`**。包含全部原始JUnit/log、命令/CPU环境、前后源码指纹、真实编译计数、旧源文件与合成数值参考、静态检查及透明外部记录脚本；只排除依赖/编译cache、bytecode和pytest current symlink。外部postprocessor首次误用空JUnit classname而失败，随后仅用实际file属性分类19新例；初版与纠正说明保留，无测试/源码改写或重跑。

## 独立只读核查及未完成事项

按AGENTS要求的另一Agent `review_requirements`只读源码/产物核查未发现可达HIGH/MED，确认数学/参数树/FSDP root ownership不变及RED/GREEN证据自洽；不等同GPT正式批准。必须保留这些边界：

- local_memory_enabled=True只验证该配置的Action head，不是完整Local scan/TTT轨迹或Session验收。
- CPU DomainAwareLinear走bmm；没有覆盖H100 BF16 grouped_mm、真实CUDA Inductor backward、FSDP实际unshard/reshard或CUDA graph capture/replay。原scope测试是编译选项spy。
- timestep/索引编排留在eager层可能影响kernel数量与延迟；CPU循环时间不是GPU性能证明。其他head的完整端到端重编译行为也未在硬件验证。
- 旧源码的控制RED说明同类可达风险，不替代R04全部原始guard历史或服务器Torch版本核对。

**请求GPT仅审核这个独立Pair的窄生产增量和CPU证据。** 通过后再决定匹配真实checkpoint/config的GPU数值、B1–8连续推理和性能验证；当前不派DS/GPU、不合V3/G2、不改Issue17或训练分支。

没有读取或改写服务器R04、648个结果或其冻结身份。新Root/Child是新的源码身份，**不能据此直接覆盖R04源码并Resume剩余252**；Manifest/verify_source限制保持，合法恢复方案需后续明确决定。现有648个有效Core保持为Owner报告的已提交结果，正式900EP SR仍不可报告。
